# Databricks notebook source
# MAGIC %md
# MAGIC HYDRO_DATA

# COMMAND ----------

import requests
import pandas as pd
from pyspark.sql import SparkSession

response = requests.get('https://danepubliczne.imgw.pl/api/data/hydro/format/json')
data = response.json()

spark = SparkSession.builder.getOrCreate()
df = spark.createDataFrame(pd.DataFrame(data))
df = df.withColumnRenamed("Województwo", "Wojewodztwo")

df.createOrReplaceTempView("hydro_data")

spark.sql("""
CREATE OR REPLACE TABLE silver.hydro_data
    AS SELECT * FROM hydro_data
""")
spark.sql("""
DROP VIEW hydro_data
""")

# COMMAND ----------

# MAGIC %md
# MAGIC SYNOP DATA

# COMMAND ----------

import requests
import pandas as pd
from pyspark.sql import SparkSession

response = requests.get('https://danepubliczne.imgw.pl/api/data/synop/format/json')
data = response.json()

spark = SparkSession.builder.getOrCreate()
df = spark.createDataFrame(pd.DataFrame(data))

df.createOrReplaceTempView("synop_data")

spark.sql("""
CREATE OR REPLACE TABLE silver.synop_data
    AS SELECT * FROM synop_data
""")
spark.sql("""
DROP VIEW synop_data
""")

# COMMAND ----------

# MAGIC %md
# MAGIC TOWN/VOIVODESHIP DATA

# COMMAND ----------

import requests
import pandas as pd
from pyspark.sql.functions import col, concat, current_timestamp, lit, split
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.getOrCreate()

url = "https://api.dane.gov.pl/resources/39233,wykaz-urzedowych-nazw-miejscowosci-i-ich-czesci/csv"
c = pd.read_csv(url)

spark_df = spark.createDataFrame(c)

spark_df = spark_df.withColumnRenamed("Nazwa miejscowości", "Miejscowosc") \
       .withColumnRenamed("Województwo", "Wojewodztwo") \
           .withColumnRenamed("Identyfikator miejscowości z krajowego rejestru urzędowego podziału terytorialnego kraju TERYT", "TERYT_ID") \
               .withColumnRenamed("Dopełniacz", "Dopelniacz")

spark_df.createOrReplaceTempView("voivodeship_data")

spark.sql("""
CREATE OR REPLACE TABLE silver.voivodeship_data
    AS SELECT * FROM voivodeship_data
""")
spark.sql("""
DROP VIEW voivodeship_data
""")

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE
# MAGIC OR REPLACE TABLE silver.synop_data_adj AS
# MAGIC WITH
# MAGIC   voivodeship_data_ADJ AS (
# MAGIC     SELECT
# MAGIC       *,
# MAGIC       CASE
# MAGIC         WHEN Miejscowosc = 'Bielsko-Biała' THEN 'Bielsko Biała'
# MAGIC         ELSE Miejscowosc
# MAGIC       END AS Miejscowosc_adj,
# MAGIC       COUNT(1) OVER (
# MAGIC         PARTITION BY
# MAGIC           Miejscowosc
# MAGIC       ) AS CNT
# MAGIC     FROM
# MAGIC       silver.voivodeship_data
# MAGIC   ),
# MAGIC   ADJUSTED AS (
# MAGIC     SELECT
# MAGIC       SD.*,
# MAGIC       mv.Wojewodztwo
# MAGIC     FROM
# MAGIC       silver.synop_data SD
# MAGIC       LEFT JOIN voivodeship_data_ADJ mv ON SD.stacja = mv.Miejscowosc_adj
# MAGIC     WHERE
# MAGIC       mv.Rodzaj = 'miasto'
# MAGIC       OR CNT = 1
# MAGIC   )
# MAGIC SELECT
# MAGIC   *
# MAGIC FROM
# MAGIC   ADJUSTED
# MAGIC UNION
# MAGIC SELECT
# MAGIC   *,
# MAGIC   'N/A'
# MAGIC FROM
# MAGIC   SILVER.SYNOP_DATA
# MAGIC WHERE
# MAGIC   stacja IN ('Kasprowy Wierch', 'Platforma', 'Śnieżka')

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE
# MAGIC OR REPLACE TABLE silver.imgw_data AS
# MAGIC WITH
# MAGIC   SYNOP AS (
# MAGIC     SELECT DISTINCT
# MAGIC       Wojewodztwo AS VOIEVODESHIP_S,
# MAGIC       MAX(to_timestamp (data_pomiaru)) OVER (
# MAGIC         PARTITION BY
# MAGIC           Wojewodztwo
# MAGIC       ) as LATEST_MEASUREMENT_TIMESTAMP,
# MAGIC       CAST(
# MAGIC         AVG(temperatura) OVER (
# MAGIC           PARTITION BY
# MAGIC             Wojewodztwo
# MAGIC         ) AS DECIMAL(38, 2)
# MAGIC       ) AS AVG_TEMP_WOJ,
# MAGIC       CAST(
# MAGIC         AVG(predkosc_wiatru) OVER (
# MAGIC           PARTITION BY
# MAGIC             Wojewodztwo
# MAGIC         ) AS DECIMAL(38, 2)
# MAGIC       ) AS AVG_WIND_SPD_WOJ,
# MAGIC       CAST(
# MAGIC         AVG(wilgotnosc_wzgledna) OVER (
# MAGIC           PARTITION BY
# MAGIC             Wojewodztwo
# MAGIC         ) AS DECIMAL(38, 2)
# MAGIC       ) AS AVG_HUMIDITY_WOJ,
# MAGIC       CAST(
# MAGIC         AVG(suma_opadu) OVER (
# MAGIC           PARTITION BY
# MAGIC             Wojewodztwo
# MAGIC         ) AS DECIMAL(38, 2)
# MAGIC       ) AS AVG_RAIN_WOJ,
# MAGIC       CAST(
# MAGIC         AVG(cisnienie) OVER (
# MAGIC           PARTITION BY
# MAGIC             Wojewodztwo
# MAGIC         ) AS DECIMAL(38, 2)
# MAGIC       ) AS AVG_PRESSURE_WOJ
# MAGIC     FROM
# MAGIC       silver.SYNOP_DATA_ADJ
# MAGIC     WHERE
# MAGIC       Wojewodztwo != 'N/A'
# MAGIC   ),
# MAGIC   HYDRO AS (
# MAGIC     SELECT DISTINCT
# MAGIC       wojewodztwo AS VOIEVODESHIP_H,
# MAGIC       MAX(to_timestamp (temperatura_wody_data_pomiaru)) OVER (
# MAGIC         PARTITION BY
# MAGIC           Wojewodztwo
# MAGIC       ) as LATEST_MEASUREMENT_WATER_TIMESTAMP,
# MAGIC       CAST(
# MAGIC         AVG(stan_wody) OVER (
# MAGIC           PARTITION BY
# MAGIC             wojewodztwo
# MAGIC         ) AS DECIMAL(38, 2)
# MAGIC       ) AS AVG_WATER_WOJ,
# MAGIC       CAST(
# MAGIC         AVG(temperatura_wody) OVER (
# MAGIC           PARTITION BY
# MAGIC             wojewodztwo
# MAGIC         ) AS DECIMAL(38, 2)
# MAGIC       ) AS AVG_WATER_TEMP_WOJ,
# MAGIC       MAX(to_timestamp (zjawisko_lodowe_data_pomiaru)) OVER (
# MAGIC         PARTITION BY
# MAGIC           Wojewodztwo
# MAGIC       ) as LATEST_MEASUREMENT_ICE_TIMESTAMP,
# MAGIC       CAST(
# MAGIC         MAX(zjawisko_lodowe) OVER (
# MAGIC           PARTITION BY
# MAGIC             wojewodztwo
# MAGIC         ) AS DECIMAL(38, 2)
# MAGIC       ) AS MAX_ICE_OCCR_WOJ,
# MAGIC       MAX(to_timestamp (zjawisko_zarastania_data_pomiaru)) OVER (
# MAGIC         PARTITION BY
# MAGIC           Wojewodztwo
# MAGIC       ) as LATEST_MEASUREMENT_ENCHROACHING_TIMESTAMP,
# MAGIC       CAST(
# MAGIC         MAX(zjawisko_zarastania) OVER (
# MAGIC           PARTITION BY
# MAGIC             wojewodztwo
# MAGIC         ) AS DECIMAL(38, 2)
# MAGIC       ) AS MAX_ENCHROACHING_WOJ
# MAGIC     FROM
# MAGIC       silver.hydro_data
# MAGIC     where
# MAGIC       wojewodztwo != '-'
# MAGIC   )
# MAGIC SELECT
# MAGIC   UPPER(S.VOIEVODESHIP_S) AS VOIVODESHIP,
# MAGIC   LATEST_MEASUREMENT_TIMESTAMP,
# MAGIC   AVG_TEMP_WOJ,
# MAGIC   AVG_WIND_SPD_WOJ,
# MAGIC   AVG_HUMIDITY_WOJ,
# MAGIC   AVG_RAIN_WOJ,
# MAGIC   AVG_PRESSURE_WOJ,
# MAGIC   LATEST_MEASUREMENT_WATER_TIMESTAMP,
# MAGIC   AVG_WATER_WOJ,
# MAGIC   AVG_WATER_TEMP_WOJ,
# MAGIC   LATEST_MEASUREMENT_ICE_TIMESTAMP,
# MAGIC   MAX_ICE_OCCR_WOJ,
# MAGIC   LATEST_MEASUREMENT_ENCHROACHING_TIMESTAMP,
# MAGIC   MAX_ENCHROACHING_WOJ
# MAGIC FROM
# MAGIC   SYNOP S
# MAGIC   JOIN HYDRO H ON S.VOIEVODESHIP_S = H.VOIEVODESHIP_H

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM silver.imgw_data
