from pyspark.sql import SparkSession, functions as F

# Create Spark session
spark = (
    SparkSession.builder.appName("bronze-to-silver")
    .config("spark.sql.session.timeZone", "UTC")
    .getOrCreate()
)

# S3 paths
BRONZE = "s3a://weather-bronze/openweathermap/"
SILVER = "s3a://weather-silver/weather_observations/"

# Setting up spark to read the bronze data
bronze = spark.read.json(BRONZE)

# If there's a column named "rain" in the bronze DataFrame, extract the "1h" field; otherwise, set it to None
if "rain" in bronze.columns:
    rain_mm = F.col("rain").getField("1h")
else:
    rain_mm = F.lit(None)

# Transforming bronze to silver  
silver = (
    bronze
    .withColumn("source_file", F.input_file_name())
    .select(
        F.col("id").alias("city_id"),
        F.col("name").alias("city_name"),
        F.col("sys.country").alias("country"),
        F.col("coord.lat").alias("latitude"),
        F.col("coord.lon").alias("longitude"),
        F.timestamp_seconds("dt").alias("observed_at"),
        F.col("main.temp").alias("temp_c"),
        F.col("main.feels_like").alias("feels_like_c"),
        F.col("main.humidity").alias("humidity_pct"),
        F.col("main.pressure").alias("pressure_hpa"),
        F.col("wind.speed").alias("wind_speed_ms"),
        F.col("wind.deg").alias("wind_deg"),
        F.col("clouds.all").alias("clouds_pct"),
        F.coalesce(rain_mm, F.lit(0.0)).alias("rain_1h_mm"),
        F.col("weather")[0]["main"].alias("weather_main"),
        F.col("weather")[0]["description"].alias("weather_description"),
        F.to_timestamp(
            F.concat_ws(
                " ",
                F.col("date").cast("string"),
                F.regexp_extract("source_file", r"_(\d{6})\.json$", 1)
            ),
            "yyyy-MM-dd HHmmss",
        ).alias("ingested_at"),
    )
    .dropDuplicates(["city_id", "observed_at"])
    .withColumn("observed_date", F.to_date("observed_at"))
)

silver.printSchema()
silver.write.mode("overwrite").partitionBy("observed_date").parquet(SILVER)

print("silver rows:", spark.read.parquet(SILVER).count())
spark.read.parquet(SILVER).show(truncate=False)

spark.stop()