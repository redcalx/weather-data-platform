from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("check-bronze").getOrCreate()

df = spark.read.json("s3a://weather-bronze/openweathermap/")

df.printSchema()
print("rows:", df.count())
df.select("name", "main.temp", "dt", "date").show(truncate=False)

spark.stop()