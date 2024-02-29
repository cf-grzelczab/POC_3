# Databricks notebook source
# MAGIC %md
# MAGIC STATION DATA

# COMMAND ----------

import requests
import pandas as pd
from pyspark.sql.functions import col, concat, current_timestamp, lit, split
from pyspark.sql import SparkSession, functions as F

response = requests.get('https://api.gios.gov.pl/pjp-api/rest/station/findAll')
data = response.json()

spark = SparkSession.builder.getOrCreate()
df = spark.createDataFrame(pd.DataFrame(data))

df = df.withColumn("commune", col("city.commune")) \
    .withColumn("city_id", col("city.id")) \
    .withColumn("name", col("city.name")) \
    .drop("city")

df = df.withColumn("communeName", col("commune.communeName")) \
    .withColumn("districtName", col("commune.districtName")) \
    .withColumn("proviceName", col("commune.provinceName")) \
    .drop("commune")

df.createOrReplaceTempView("gios_findall")

spark.sql("""
CREATE OR REPLACE TABLE silver.gios_findall
    AS SELECT * FROM gios_findall
""")
spark.sql("""
DROP VIEW gios_findall
""")

# COMMAND ----------

# MAGIC %md
# MAGIC SENSOR DATA

# COMMAND ----------

import requests
import pandas as pd
from pyspark.sql import SparkSession

ids = [114, 117, 129, 52, 109, 11, 16, 38, 70, 74, 9153, 11254, 11934, 12055, 12056, 17780, 156, 158, 16237, 16613, 295, 296, 314, 355, 10058, 291, 319, 322, 331, 562, 9913, 11358, 16271, 17160, 590, 10374, 568, 584, 600, 8976, 10018, 16181, 16413, 671, 10125, 17159, 17179, 631, 638, 646, 659, 665, 678, 684, 870, 882, 10005, 10030, 17741, 944, 16493, 952, 902, 920, 946, 950, 9218, 10834, 16495, 17438, 986, 987, 989, 16270, 805, 809, 813, 814, 837, 841, 17880, 834, 10554, 11855, 789, 10158, 798, 800, 842, 845, 853, 856, 9000, 11278, 11455, 11457, 11794, 16406, 11195, 16196, 16497, 769, 778, 785, 10794, 11754, 12138, 17758, 877, 861, 11554, 11616, 400, 401, 402, 10123, 10139, 10447, 11303, 444, 10120, 426, 9173, 9175, 10414, 10438, 12057, 609, 11174, 11814, 17658, 612, 618, 9994, 11154, 11916, 731, 732, 736, 16242, 725, 740, 741, 742, 743, 750, 437, 443, 449, 455, 459, 9179, 10119, 10124, 10446, 10814, 11301, 11434, 16753, 16894, 17118, 17138, 530, 538, 550, 552, 10955, 10956, 16533, 497, 501, 515, 460, 466, 471, 485, 488, 517, 9798, 12038, 266, 236, 248, 275, 282, 285, 10874, 11360, 12100, 361, 387, 11294, 374, 376, 379, 382, 11576, 145, 206, 208, 225, 9791, 142, 143, 164, 190, 232, 966, 11336, 961, 983, 10934, 17158]

df_combined = pd.DataFrame()

for id in ids:
    response = requests.get(f'https://api.gios.gov.pl/pjp-api/rest/station/sensors/{id}')

    data = response.json()

    df = pd.DataFrame(data)

    df_combined = df_combined.append(df, ignore_index=True)

df_combined[['paramName', 'paramCode', 'paramFormula', 'paramID']] = df_combined['param'].apply(pd.Series)

df_combined.drop('param', axis=1, inplace=True)

spark = SparkSession.builder.getOrCreate()
df_spark = spark.createDataFrame(df_combined)

df_spark.createOrReplaceTempView("gios_sensor_data")

spark.sql("""
CREATE OR REPLACE TABLE silver.gios_sensor_data
    AS SELECT * FROM gios_sensor_data
""")
spark.sql("""
DROP VIEW gios_sensor_data
""")

# COMMAND ----------

# MAGIC %md
# MAGIC AIR QUALITY DATA

# COMMAND ----------

import requests
from pyspark.sql import SparkSession
from pyspark.sql import SQLContext
from pyspark.sql.types import StructType
import json

ids = [114, 117, 129, 52, 109, 11, 16, 38, 70, 74, 9153, 11254, 11934, 12055, 12056, 17780, 156, 158, 16237, 16613, 295, 296, 314, 355, 10058, 291, 319, 322, 331, 562, 9913, 11358, 16271, 17160, 590, 10374, 568, 584, 600, 8976, 10018, 16181, 16413, 671, 10125, 17159, 17179, 631, 638, 646, 659, 665, 678, 684, 870, 882, 10005, 10030, 17741, 944, 16493, 952, 902, 920, 946, 950, 9218, 10834, 16495, 17438, 986, 987, 989, 16270, 805, 809, 813, 814, 837, 841, 17880, 834, 10554, 11855, 789, 10158, 798, 800, 842, 845, 853, 856, 9000, 11278, 11455, 11457, 11794, 16406, 11195, 16196, 16497, 769, 778, 785, 10794, 11754, 12138, 17758, 877, 861, 11554, 11616, 400, 401, 402, 10123, 10139, 10447, 11303, 444, 10120, 426, 9173, 9175, 10414, 10438, 12057, 609, 11174, 11814, 17658, 612, 618, 9994, 11154, 11916, 731, 732, 736, 16242, 725, 740, 741, 742, 743, 750, 437, 443, 449, 455, 459, 9179, 10119, 10124, 10446, 10814, 11301, 11434, 16753, 16894, 17118, 17138, 530, 538, 550, 552, 10955, 10956, 16533, 497, 501, 515, 460, 466, 471, 485, 488, 517, 9798, 12038, 266, 236, 248, 275, 282, 285, 10874, 11360, 12100, 361, 387, 11294, 374, 376, 379, 382, 11576, 145, 206, 208, 225, 9791, 142, 143, 164, 190, 232, 966, 11336, 961, 983, 10934, 17158]

data_list = []

for id in ids:
    response = requests.get(f'https://api.gios.gov.pl/pjp-api/rest/aqindex/getIndex/{id}')
    data = response.json()
    
    data_list.append(data)

spark = SparkSession.builder.getOrCreate()
sqlContext = SQLContext(spark)

df = sqlContext.read.json(spark.sparkContext.parallelize([json.dumps(d) for d in data_list]))

df = df.withColumn("id_no2", col("no2IndexLevel.id")) \
    .withColumn("indexLevelName_no2", col("no2IndexLevel.indexLevelName")) \
    .drop("no2IndexLevel")


df = df.withColumn("id_o3", col("o3IndexLevel.id")) \
    .withColumn("indexLevelName_o3", col("o3IndexLevel.indexLevelName")) \
        .drop("o3IndexLevel")


df = df.withColumn("id_pm10", col("pm10IndexLevel.id")) \
    .withColumn("indexLevelName_pm10", col("pm10IndexLevel.indexLevelName")) \
        .drop("pm10IndexLevel")


df = df.withColumn("id_pm25", col("pm25IndexLevel.id")) \
    .withColumn("indexLevelName_pm25", col("pm25IndexLevel.indexLevelName")) \
        .drop("pm25IndexLevel")


df = df.withColumn("id_so2", col("so2IndexLevel.id")) \
    .withColumn("indexLevelName_so2", col("so2IndexLevel.indexLevelName")) \
        .drop("so2IndexLevel")


df = df.withColumn("id_st", col("stIndexLevel.id")) \
    .withColumn("indexLevelName_st", col("stIndexLevel.indexLevelName")) \
        .drop("stIndexLevel")

df.createOrReplaceTempView("gios_air_quality")

spark.sql("""
CREATE OR REPLACE TABLE silver.gios_air_quality
AS SELECT * FROM gios_air_quality
""")

spark.sql("""
DROP VIEW gios_air_quality
""")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM silver.gios_findall

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM silver.gios_air_quality

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM silver.gios_sensor_data

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE silver.gios_data AS
# MAGIC WITH
# MAGIC   TEST AS (
# MAGIC     SELECT
# MAGIC       gf.proviceName,
# MAGIC       TO_TIMESTAMP(gaq.stCalcDate) AS AIR_QUALITY_CHECK_TS,
# MAGIC       gaq.indexLevelName_st as OVERALL_MARK
# MAGIC     FROM
# MAGIC       silver.gios_findall gf
# MAGIC       LEFT JOIN silver.gios_sensor_data gsd ON gf.id = gsd.stationId
# MAGIC       LEFT jOIN silver.gios_air_quality gaq ON gf.id = gaq.id
# MAGIC   ),
# MAGIC   TEST_RANK AS (
# MAGIC     select
# MAGIC       proviceName as VOIVODESHIP,
# MAGIC       AIR_QUALITY_CHECK_TS,
# MAGIC       CASE
# MAGIC         WHEN OVERALL_MARK = 'Bardzo zły' THEN 1
# MAGIC         WHEN OVERALL_MARK = 'Zły' THEN 2
# MAGIC         WHEN OVERALL_MARK = 'Dostateczny' THEN 3
# MAGIC         WHEN OVERALL_MARK = 'Umiarkowany' THEN 4
# MAGIC         WHEN OVERALL_MARK = 'Dobry' THEN 5
# MAGIC         WHEN OVERALL_MARK = 'Bardzo dobry' THEN 6
# MAGIC         ELSE NULL
# MAGIC       END AS OVERALL_RANK
# MAGIC     from
# MAGIC       test
# MAGIC   ),
# MAGIC   AVG_RANK AS (
# MAGIC     SELECT DISTINCT
# MAGIC       VOIVODESHIP,
# MAGIC       AIR_QUALITY_CHECK_TS,
# MAGIC       CAST(
# MAGIC         AVG(OVERALL_RANK) OVER (
# MAGIC           PARTITION BY
# MAGIC             VOIVODESHIP
# MAGIC         ) AS INT
# MAGIC       ) AS AVG_RANK
# MAGIC     FROM
# MAGIC       TEST_RANK tr
# MAGIC   )
# MAGIC SELECT
# MAGIC   *,
# MAGIC   CASE
# MAGIC     WHEN AVG_RANK = 1 THEN 'Bardzo zły'
# MAGIC     WHEN AVG_RANK = 2 THEN 'Zły'
# MAGIC     WHEN AVG_RANK = 3 THEN 'Dostateczny'
# MAGIC     WHEN AVG_RANK = 4 THEN 'Umiarkowany'
# MAGIC     WHEN AVG_RANK = 5 THEN 'Dobry'
# MAGIC     WHEN AVG_RANK = 6 THEN 'Bardzo dobry'
# MAGIC     ELSE NULL
# MAGIC   END AS MARK
# MAGIC FROM
# MAGIC   AVG_RANK

# COMMAND ----------

# MAGIC %md
# MAGIC CAN PULL MORE SPECIFIC DATA FOR EACH INDEX, PULLED THE AVERAGE INDEX FOR SHOWCASE PURPOSES

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM silver.gios_data
