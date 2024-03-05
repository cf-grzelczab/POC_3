# Databricks notebook source
# MAGIC %sql
# MAGIC CREATE OR REPLACE TEMP VIEW gios_transformed_upd
# MAGIC AS
# MAGIC WITH
# MAGIC   TEST AS (
# MAGIC     SELECT
# MAGIC       gf.proviceName,
# MAGIC       TO_TIMESTAMP(gaq.stCalcDate) AS AIR_QUALITY_CHECK_TS,
# MAGIC       gaq.indexLevelName_st as OVERALL_MARK,
# MAGIC       gf.EXTRACTION_TS AS STATION_EXT_TS,
# MAGIC       gsd.EXTRACTION_TS AS SENSOR_EXT_TS,
# MAGIC       gaq.EXTRACTION_TS AS AIR_QUALITY_EXT_TS
# MAGIC     FROM
# MAGIC       team1_poc3_bronze.gios_station_data gf
# MAGIC       LEFT JOIN team1_poc3_bronze.gios_sensor_data gsd ON gf.id = gsd.stationId
# MAGIC       LEFT jOIN team1_poc3_bronze.air_quality_data gaq ON gf.id = gaq.id
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
# MAGIC       END AS OVERALL_RANK,
# MAGIC       STATION_EXT_TS,
# MAGIC       SENSOR_EXT_TS,
# MAGIC       AIR_QUALITY_EXT_TS
# MAGIC     from
# MAGIC       test
# MAGIC   ),
# MAGIC   AVG_RANK AS (
# MAGIC     SELECT
# MAGIC       VOIVODESHIP,
# MAGIC       AIR_QUALITY_CHECK_TS,
# MAGIC       CAST(
# MAGIC         AVG(OVERALL_RANK) OVER (
# MAGIC           PARTITION BY
# MAGIC             VOIVODESHIP
# MAGIC         ) AS INT
# MAGIC       ) AS AVG_RANK,
# MAGIC       STATION_EXT_TS,
# MAGIC       SENSOR_EXT_TS,
# MAGIC       AIR_QUALITY_EXT_TS,
# MAGIC       ROW_NUMBER() OVER (PARTITION BY VOIVODESHIP ORDER BY AIR_QUALITY_CHECK_TS DESC) AS R_NUM
# MAGIC     FROM
# MAGIC       TEST_RANK tr
# MAGIC   )
# MAGIC SELECT
# MAGIC   VOIVODESHIP,
# MAGIC   AIR_QUALITY_CHECK_TS,
# MAGIC   AVG_RANK,
# MAGIC   CASE
# MAGIC     WHEN AVG_RANK = 1 THEN 'Bardzo zły'
# MAGIC     WHEN AVG_RANK = 2 THEN 'Zły'
# MAGIC     WHEN AVG_RANK = 3 THEN 'Dostateczny'
# MAGIC     WHEN AVG_RANK = 4 THEN 'Umiarkowany'
# MAGIC     WHEN AVG_RANK = 5 THEN 'Dobry'
# MAGIC     WHEN AVG_RANK = 6 THEN 'Bardzo dobry'
# MAGIC     ELSE NULL
# MAGIC   END AS MARK,
# MAGIC   STATION_EXT_TS,
# MAGIC   SENSOR_EXT_TS,
# MAGIC   AIR_QUALITY_EXT_TS,
# MAGIC   current_timestamp() as MODIFIED_TS
# MAGIC FROM
# MAGIC   AVG_RANK
# MAGIC       WHERE R_NUM = 1

# COMMAND ----------

# MAGIC %sql
# MAGIC MERGE INTO team1_poc3_silver.gios_transformed tgt
# MAGIC USING gios_transformed_upd upd
# MAGIC ON (tgt.VOIVODESHIP = upd.VOIVODESHIP AND tgt.AIR_QUALITY_CHECK_TS = upd.AIR_QUALITY_CHECK_TS)
# MAGIC WHEN MATCHED THEN
# MAGIC   UPDATE SET tgt.AVG_RANK = upd.AVG_RANK,
# MAGIC              tgt.MARK = upd.MARK,
# MAGIC              tgt.MODIFIED_TS = current_timestamp()
# MAGIC WHEN NOT MATCHED
# MAGIC   THEN INSERT (VOIVODESHIP, AIR_QUALITY_CHECK_TS, AVG_RANK, MARK, STATION_EXT_TS, SENSOR_EXT_TS, AIR_QUALITY_EXT_TS, MODIFIED_TS) 
# MAGIC        VALUES (VOIVODESHIP, AIR_QUALITY_CHECK_TS, AVG_RANK, MARK, STATION_EXT_TS, SENSOR_EXT_TS, AIR_QUALITY_EXT_TS, MODIFIED_TS)

# COMMAND ----------

# MAGIC %sql
# MAGIC --drop table team1_poc3_silver.gios_transformed

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM team1_poc3_silver.gios_transformed
