# Databricks notebook source
# MAGIC %sql
# MAGIC CREATE OR REPLACE TEMP VIEW gov_imgw_transformed_upd
# MAGIC AS
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
# MAGIC       team1_poc3_bronze.gov_cities_data
# MAGIC   ),
# MAGIC   ADJUSTED AS (
# MAGIC     SELECT
# MAGIC       SD.*,
# MAGIC       mv.Wojewodztwo
# MAGIC     FROM
# MAGIC       team1_poc3_bronze.imgw_synop_data SD
# MAGIC       LEFT JOIN voivodeship_data_ADJ mv ON SD.stacja = mv.Miejscowosc_adj
# MAGIC     WHERE
# MAGIC       mv.Rodzaj = 'miasto'
# MAGIC       OR CNT = 1
# MAGIC   ),
# MAGIC synop_data_adj AS (
# MAGIC SELECT
# MAGIC   *
# MAGIC FROM
# MAGIC   ADJUSTED
# MAGIC UNION
# MAGIC SELECT
# MAGIC   *,
# MAGIC   'N/A'
# MAGIC FROM
# MAGIC   team1_poc3_bronze.imgw_synop_data
# MAGIC WHERE
# MAGIC   stacja IN ('Kasprowy Wierch', 'Platforma', 'Śnieżka')
# MAGIC ),
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
# MAGIC       ) AS AVG_PRESSURE_WOJ,
# MAGIC       EXTRACTION_TS AS SYNOP_EXT_TS
# MAGIC     FROM
# MAGIC       synop_data_adj
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
# MAGIC       ) AS MAX_ENCHROACHING_WOJ,
# MAGIC       EXTRACTION_DATE AS HYDRO_EXT_TS
# MAGIC     FROM
# MAGIC       team1_poc3_bronze.imgw_hydro_data
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
# MAGIC   MAX_ENCHROACHING_WOJ,
# MAGIC   SYNOP_EXT_TS,
# MAGIC   HYDRO_EXT_TS,
# MAGIC   current_timestamp() as MODIFIED_TS
# MAGIC FROM
# MAGIC   SYNOP S
# MAGIC   JOIN HYDRO H ON S.VOIEVODESHIP_S = H.VOIEVODESHIP_H

# COMMAND ----------

# MAGIC %sql
# MAGIC MERGE INTO team1_poc3_silver.imgw_transformed tgt
# MAGIC USING gov_imgw_transformed_upd upd
# MAGIC ON (tgt.VOIVODESHIP = upd.VOIVODESHIP)
# MAGIC WHEN MATCHED THEN
# MAGIC   UPDATE SET tgt.LATEST_MEASUREMENT_TIMESTAMP = upd.LATEST_MEASUREMENT_TIMESTAMP,
# MAGIC              tgt.AVG_TEMP_WOJ = upd.AVG_TEMP_WOJ,
# MAGIC              tgt.AVG_WIND_SPD_WOJ = upd.AVG_WIND_SPD_WOJ,
# MAGIC              tgt.AVG_HUMIDITY_WOJ = upd.AVG_HUMIDITY_WOJ,
# MAGIC              tgt.AVG_RAIN_WOJ = upd.AVG_RAIN_WOJ,
# MAGIC              tgt.AVG_PRESSURE_WOJ = upd.AVG_PRESSURE_WOJ,
# MAGIC              tgt.LATEST_MEASUREMENT_WATER_TIMESTAMP = upd.LATEST_MEASUREMENT_WATER_TIMESTAMP,
# MAGIC              tgt.AVG_WATER_WOJ = upd.AVG_WATER_WOJ,
# MAGIC              tgt.AVG_WATER_TEMP_WOJ = upd.AVG_WATER_TEMP_WOJ,
# MAGIC              tgt.LATEST_MEASUREMENT_ICE_TIMESTAMP = upd.LATEST_MEASUREMENT_ICE_TIMESTAMP,
# MAGIC              tgt.MAX_ICE_OCCR_WOJ = upd.MAX_ICE_OCCR_WOJ,
# MAGIC              tgt.LATEST_MEASUREMENT_ENCHROACHING_TIMESTAMP = upd.LATEST_MEASUREMENT_ENCHROACHING_TIMESTAMP,
# MAGIC              tgt.MAX_ENCHROACHING_WOJ = upd.MAX_ENCHROACHING_WOJ,
# MAGIC              tgt.MODIFIED_TS = current_timestamp()
# MAGIC WHEN NOT MATCHED
# MAGIC   THEN INSERT (VOIVODESHIP, LATEST_MEASUREMENT_TIMESTAMP, AVG_TEMP_WOJ, AVG_WIND_SPD_WOJ, AVG_RAIN_WOJ, AVG_PRESSURE_WOJ, LATEST_MEASUREMENT_WATER_TIMESTAMP,
# MAGIC   AVG_WATER_WOJ, AVG_WATER_TEMP_WOJ, LATEST_MEASUREMENT_ICE_TIMESTAMP, MAX_ICE_OCCR_WOJ, LATEST_MEASUREMENT_ENCHROACHING_TIMESTAMP, MAX_ENCHROACHING_WOJ,
# MAGIC   SYNOP_EXT_TS, HYDRO_EXT_TS, MODIFIED_TS) 
# MAGIC        VALUES (VOIVODESHIP, LATEST_MEASUREMENT_TIMESTAMP, AVG_TEMP_WOJ, AVG_WIND_SPD_WOJ, AVG_RAIN_WOJ, AVG_PRESSURE_WOJ, LATEST_MEASUREMENT_WATER_TIMESTAMP,
# MAGIC   AVG_WATER_WOJ, AVG_WATER_TEMP_WOJ, LATEST_MEASUREMENT_ICE_TIMESTAMP, MAX_ICE_OCCR_WOJ, LATEST_MEASUREMENT_ENCHROACHING_TIMESTAMP, MAX_ENCHROACHING_WOJ,
# MAGIC   SYNOP_EXT_TS, HYDRO_EXT_TS, MODIFIED_TS)

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from team1_poc3_silver.imgw_transformed
