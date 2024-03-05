# Databricks notebook source
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

param_schema = StructType([
    StructField("paramName", StringType(), True),
    StructField("paramFormula", StringType(), True),
    StructField("paramCode", StringType(), True),
    StructField("idParam", IntegerType(), True)
])

sensor_data_schema = StructType([
    StructField("id", IntegerType(), True),
    StructField("stationId", IntegerType(), True),
    StructField("param", param_schema, True)
])

# COMMAND ----------

from pyspark.sql.functions import col, concat, current_timestamp, lit, split


sensor_data_df = spark.read \
        .option("header", True) \
        .schema(sensor_data_schema) \
        .json(f'abfss://poc3@team1poc3dls.dfs.core.windows.net/raw/stations/')


sensor_data_df = sensor_data_df.withColumn("idParam", col("param.idParam")) \
    .withColumn("paramCode", col("param.paramCode")) \
    .withColumn("paramFormula", col("param.paramFormula")) \
    .withColumn("paramName", col("param.paramName")) \
    .drop("param")

sensor_data_df = sensor_data_df.withColumn("EXTRACTION_TS", current_timestamp())

sensor_data_df.write.mode("overwrite").format("delta").option("overwriteSchema", "true").saveAsTable("team1_poc3_bronze.gios_sensor_data")

# COMMAND ----------

# MAGIC %sql
# MAGIC DROP TABLE team1_poc3_bronze.gios_sensor_data

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from team1_poc3_bronze.gios_sensor_data
