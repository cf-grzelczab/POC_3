# Databricks notebook source
# MAGIC %run "../Utils/merge_def"

# COMMAND ----------

from datetime import date   
dt = date.today()

# COMMAND ----------

folder_path = f'abfss://poc3@team1poc3dls.dfs.core.windows.net/bronze/'

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, IntegerType, TimestampType, FloatType

imgw_hydro_schema = StructType([
    StructField('id_stacji', IntegerType(), True),
    StructField('stacja', StringType(), True),
    StructField('rzeka', StringType(), True),
    StructField('województwo', StringType(), True),
    StructField('stan_wody', IntegerType(), True),
    StructField('stan_wody_data_pomiaru', TimestampType(), True),
    StructField('temperatura_wody', FloatType(), True),
    StructField('temperatura_wody_data_pomiaru', TimestampType(), True),
    StructField('zjawisko_lodowe', IntegerType(), True),
    StructField('zjawisko_lodowe_data_pomiaru', TimestampType(), True),
    StructField('zjawisko_zarastania', IntegerType(), True),
    StructField('zjawisko_zarastania_data_pomiaru', TimestampType(), True)
])

# COMMAND ----------

import requests
import pandas as pd
from pyspark.sql.functions import current_timestamp

imgw_hydro_df = spark.read \
        .option("header", True) \
        .schema(imgw_hydro_schema) \
        .json(f'abfss://poc3@team1poc3dls.dfs.core.windows.net/raw/hydro/{dt}/{dt}.json')

imgw_hydro_df = imgw_hydro_df.withColumnRenamed("Województwo", "Wojewodztwo")

imgw_hydro_df = imgw_hydro_df.withColumn("EXTRACTION_TS", current_timestamp())

merge_condition = "tgt.id_stacji = src.id_stacji"
merge_delta_data(imgw_hydro_df, 'team1_poc3_bronze', 'imgw_hydro_data', folder_path, merge_condition)

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from team1_poc3_bronze.imgw_hydro_data
