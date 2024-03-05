# Databricks notebook source
# MAGIC %run "../0.1Utils/merge_def"

# COMMAND ----------

from datetime import date   
dt = date.today()

# COMMAND ----------

folder_path = f'abfss://poc3@team1poc3dls.dfs.core.windows.net/bronze/'

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, IntegerType, BooleanType, TimestampType

index_level_schema = StructType([
    StructField("id", IntegerType(), True),
    StructField("indexLevelName", StringType(), True),
])

air_quality_schema = StructType([
    StructField("id", IntegerType(), True),
    StructField("stCalcDate", TimestampType(), True),
    StructField("stIndexLevel", index_level_schema, True),
    StructField("stSourceDataDate", TimestampType(), True),
    StructField("so2CalcDate", TimestampType(), True),
    StructField("so2IndexLevel", index_level_schema, True),
    StructField("so2SourceDataDate", TimestampType(), True),
    StructField("no2CalcDate", TimestampType(), True),
    StructField("no2IndexLevel", index_level_schema, True),
    StructField("no2SourceDataDate", TimestampType(), True),
    StructField("pm10CalcDate", TimestampType(), True),
    StructField("pm10IndexLevel", index_level_schema, True),
    StructField("pm10SourceDataDate", TimestampType(), True),
    StructField("pm25CalcDate", TimestampType(), True),
    StructField("pm25IndexLevel", index_level_schema, True),
    StructField("pm25SourceDataDate", TimestampType(), True),
    StructField("o3CalcDate", TimestampType(), True),
    StructField("o3IndexLevel", index_level_schema, True),
    StructField("o3SourceDataDate", TimestampType(), True),
    StructField("stIndexStatus", BooleanType(), True),
    StructField("stIndexCrParam", StringType(), True),
])

# COMMAND ----------

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat, current_timestamp, lit, split, to_date
from delta import DeltaTable

air_quality_df = spark.read \
        .option("header", True) \
        .schema(air_quality_schema) \
        .json(f'abfss://poc3@team1poc3dls.dfs.core.windows.net/raw/pollutions/{dt}/')

air_quality_df = air_quality_df.withColumn("id_no2", col("no2IndexLevel.id")) \
    .withColumn("indexLevelName_no2", col("no2IndexLevel.indexLevelName")) \
    .drop("no2IndexLevel")

air_quality_df = air_quality_df.withColumn("id_o3", col("o3IndexLevel.id")) \
    .withColumn("indexLevelName_o3", col("o3IndexLevel.indexLevelName")) \
    .drop("o3IndexLevel")

air_quality_df = air_quality_df.withColumn("id_pm10", col("pm10IndexLevel.id")) \
    .withColumn("indexLevelName_pm10", col("pm10IndexLevel.indexLevelName")) \
    .drop("pm10IndexLevel")

air_quality_df = air_quality_df.withColumn("id_pm25", col("pm25IndexLevel.id")) \
    .withColumn("indexLevelName_pm25", col("pm25IndexLevel.indexLevelName")) \
    .drop("pm25IndexLevel")

air_quality_df = air_quality_df.withColumn("id_so2", col("so2IndexLevel.id")) \
    .withColumn("indexLevelName_so2", col("so2IndexLevel.indexLevelName")) \
    .drop("so2IndexLevel")

air_quality_df = air_quality_df.withColumn("id_st", col("stIndexLevel.id")) \
    .withColumn("indexLevelName_st", col("stIndexLevel.indexLevelName")) \
    .drop("stIndexLevel")

air_quality_df = air_quality_df.withColumn("EXTRACTION_TS", current_timestamp())

if (DeltaTable.isDeltaTable(spark, 'abfss://poc3@team1poc3dls.dfs.core.windows.net/bronze/air_quality_data/')):
    pass
else:
    air_quality_df.write.mode("overwrite").format("delta").option("overwriteSchema", "true").saveAsTable("team1_poc3_bronze.air_quality_data")

air_quality_check_df = spark.read.format("delta").load('abfss://poc3@team1poc3dls.dfs.core.windows.net/bronze/air_quality_data/')

air_quality_check_df = air_quality_check_df.filter(to_date(col("EXTRACTION_TS")) == lit(dt))

if air_quality_check_df.count() == 0:
    air_quality_df.write.mode("append").format("delta").option("overwriteSchema", "true").saveAsTable("team1_poc3_bronze.air_quality_data")
else:
    dbutils.notebook.exit(f"Data from {dt} already fetched.")

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE team1_poc3_bronze.air_quality_data

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM team1_poc3_bronze.air_quality_data
