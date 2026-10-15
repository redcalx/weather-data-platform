from pyspark.sql import SparkSession, functions as F

spark = (
    SparkSession.builder.appName("history-to-silver")
    .config("spark.sql.session.timeZone", "UTC")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

BRONZE = "s3a://weather-bronze/open-meteo/archive/"
SILVER = "s3a://weather-silver/daily_temperatures/"

bronze = spark.read.json(BRONZE)

# Zips the daily columns into a single array of structs for easier processing 
zipped = F.arrays_zip(
    F.col("daily.time").alias("date"),
    F.col("daily.temperature_2m_max").alias("temp_max_c"),
    F.col("daily.temperature_2m_min").alias("temp_min_c"),
    F.col("daily.temperature_2m_mean").alias("temp_mean_c"),
    F.col("daily.apparent_temperature_max").alias("apparent_max_c"),
    F.col("daily.apparent_temperature_min").alias("apparent_min_c"),
    F.col("daily.apparent_temperature_mean").alias("apparent_mean_c"),
)

silver = (
    bronze
    # Expanding the zipped array into individual rows for each date
    .select("uf", F.explode(zipped).alias("d"))
    .select(
        "uf",
        F.to_date("d.date").alias("date"),
        F.col("d.temp_max_c").alias("temp_max_c"),
        F.col("d.temp_min_c").alias("temp_min_c"),
        F.col("d.temp_mean_c").alias("temp_mean_c"),
        F.col("d.apparent_max_c").alias("apparent_max_c"),
        F.col("d.apparent_min_c").alias("apparent_min_c"),
        F.col("d.apparent_mean_c").alias("apparent_mean_c"),
    )
    .dropDuplicates(["uf", "date"])
    .withColumn("year", F.year("date"))

)
# Writes the silver table and partitions it by year for efficient querying and storage
silver.repartition("year").write.mode("overwrite").partitionBy("year").parquet(SILVER)

saved = spark.read.parquet(SILVER)
print("total rows",saved.count())
print("states loaded:", saved.select("uf").distinct().count())

gaps = (
    saved.groupBy("uf", "year")
    .agg(
        F.count("*").alias("days"),
        (F.datediff(F.max("date"), F.min("date")) + 1).alias("expected_days"),
    )
    .filter(F.col("days") != F.col("expected_days"))
)
print("uf/year groups with missing days:", gaps.count())
gaps.show(20, truncate=False)

null_temps = saved.filter(
    F.col("temp_max_c").isNull() | F.col("apparent_max_c").isNull()
).count()
print("rows with null temperatures:", null_temps)

START_YEAR = 1991
last_year = saved.agg(F.max("year")).first()[0]
expected_years = last_year - START_YEAR + 1

coverage = saved.groupBy("uf").agg(
    F.min("year").alias("first_year"),
    F.max("year").alias("last_year"),
    F.countDistinct("year").alias("years"),
)
incomplete = coverage.filter(F.col("years") < expected_years)
print(f"states with fewer than {expected_years} years of data:", incomplete.count())
incomplete.show(truncate=False)

saved.orderBy("uf", "date").show(10, truncate=False)
spark.stop()