from pyspark.sql import SparkSession

spark = (
    SparkSession.builder.appName("check-silver")
    .config("spark.sql.session.timeZone", "UTC")
    .getOrCreate()
)

df = spark.read.parquet("s3a://weather-silver/weather_observations/")

df.printSchema()
print("rows:", df.count())
df.show(truncate=False) 

spark.stop()
