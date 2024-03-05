# Databricks notebook source
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

gov_cities_schema = StructType([
    StructField("Nazwa miejscowości", StringType(), True),
    StructField("Rodzaj", StringType(), True),
    StructField("Gmina", StringType(), True),
    StructField("Powiat", StringType(), True),
    StructField("Województwo", StringType(), True),
    StructField("Identyfikator miejscowości z krajowego rejestru urzędowego podziału terytorialnego kraju TERYT", IntegerType(), True),
    StructField("Dopełniacz", StringType(), True),
    StructField("Przymiotnik", StringType(), True)
])

# COMMAND ----------

import requests
import pandas as pd
from pyspark.sql.functions import col, concat, current_timestamp, lit, split
from pyspark.sql import SparkSession, functions as F

gov_cities_df = spark.read \
    .option("header", True) \
    .schema(gov_cities_schema) \
    .csv('abfss://poc3@team1poc3dls.dfs.core.windows.net/raw/gov/cities.csv')


gov_cities_df = gov_cities_df.withColumnRenamed("Nazwa miejscowości", "Miejscowosc") \
       .withColumnRenamed("Województwo", "Wojewodztwo") \
           .withColumnRenamed("Identyfikator miejscowości z krajowego rejestru urzędowego podziału terytorialnego kraju TERYT", "TERYT_ID") \
               .withColumnRenamed("Dopełniacz", "Dopelniacz")

gov_cities_df = gov_cities_df.withColumn("EXTRACTION_TS", current_timestamp())

gov_cities_df.write.mode("overwrite").format("delta").option("mergeSchema", "true").saveAsTable("team1_poc3_bronze.gov_cities_data")

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from team1_poc3_bronze.gov_cities_data
