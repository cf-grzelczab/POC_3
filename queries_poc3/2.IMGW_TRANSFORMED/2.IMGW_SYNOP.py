# Databricks notebook source
# MAGIC %run "../0.1Utils/merge_def"

# COMMAND ----------

from datetime import date   
dt = date.today()

# COMMAND ----------

folder_path = f'abfss://poc3@team1poc3dls.dfs.core.windows.net/bronze/'

# COMMAND ----------

from pyspark.sql.types import *

imgw_synop_schema = StructType([
    StructField('id_stacji', IntegerType(), True),
    StructField('stacja', StringType(), True),
    StructField('data_pomiaru', DateType(), True),
    StructField('godzina_pomiaru', IntegerType(), True),
    StructField('temperatura', FloatType(), True),
    StructField('predkosc_wiatru', IntegerType(), True),
    StructField('kierunek_wiatru', IntegerType(), True),
    StructField('wilgotnosc_wzgledna', FloatType(), True),
    StructField('suma_opadu', FloatType(), True),
    StructField('cisnienie', FloatType(), True),
])

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat, current_timestamp, lit, split, to_date
from delta import DeltaTable

imgw_synop_df = spark.read \
        .option("header", True) \
        .schema(imgw_synop_schema) \
        .json(f'abfss://poc3@team1poc3dls.dfs.core.windows.net/raw/synop/{dt}/{dt}.json')

imgw_synop_df = imgw_synop_df.withColumn("EXTRACTION_TS", current_timestamp())

if (DeltaTable.isDeltaTable(spark, 'abfss://poc3@team1poc3dls.dfs.core.windows.net/bronze/air_quality_data/')):
    pass
else:
    imgw_synop_df.write.mode("overwrite").format("delta").option("overwriteSchema", "true").saveAsTable("team1_poc3_bronze.imgw_synop_data")

imgw_synop_check_df = spark.read.format("delta").load('abfss://poc3@team1poc3dls.dfs.core.windows.net/bronze/imgw_synop_data/')

imgw_synop_check_df = imgw_synop_check_df.filter(to_date(col("EXTRACTION_TS")) == lit(dt))

if imgw_synop_check_df.count() == 0:
    imgw_synop_df.write.mode("append").format("delta").option("overwriteSchema", "true").saveAsTable("team1_poc3_bronze.imgw_synop_data")
else:
    dbutils.notebook.exit(f"Data from {dt} already fetched.")

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from team1_poc3_bronze.imgw_synop_data
