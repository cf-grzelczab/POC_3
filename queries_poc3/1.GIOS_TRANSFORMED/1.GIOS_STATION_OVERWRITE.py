# Databricks notebook source
# MAGIC %md
# MAGIC STATION DATA

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, DecimalType

commune_schema = StructType([
    StructField("communeName", StringType(), True),
    StructField("districtName", StringType(), True),
    StructField("provinceName", StringType(), True)
])

city_schema = StructType([
    StructField("id", IntegerType(), True),
    StructField("name", StringType(), True),
    StructField("commune", commune_schema, True)
])

station_data_schema = StructType([
    StructField("id", IntegerType(), True),
    StructField("stationName", StringType(), True),
    StructField("gegrLat", DecimalType(38,10), True),
    StructField("gegrLon", DecimalType(38,10), True),
    StructField("city", city_schema, True),
    StructField("addressStreet", StringType(), True)
])

# COMMAND ----------

import requests
import pandas as pd
from pyspark.sql.functions import col, concat, current_timestamp, lit, split
from pyspark.sql import SparkSession, functions as F

station_data_df = spark.read \
    .option("header", True) \
    .schema(station_data_schema) \
    .json('abfss://poc3@team1poc3dls.dfs.core.windows.net/raw/all_gios.json')

station_data_df = station_data_df.withColumn("commune", col("city.commune")) \
    .withColumn("city_id", col("city.id")) \
    .withColumn("name", col("city.name")) \
    .drop("city")


station_data_df = station_data_df.withColumn("communeName", col("commune.communeName")) \
    .withColumn("districtName", col("commune.districtName")) \
    .withColumn("proviceName", col("commune.provinceName")) \
    .drop("commune")

station_data_df = station_data_df.withColumn("EXTRACTION_TS", current_timestamp())

station_data_df.write.mode("overwrite").format("delta").option("overwriteSchema", "true").saveAsTable("team1_poc3_bronze.gios_station_data")

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE team1_poc3_bronze.gios_station_data

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from team1_poc3_bronze.gios_station_data
# MAGIC
