# Databricks notebook source
# MAGIC %sql
# MAGIC SELECT DISTINCT
# MAGIC   IMGW.VOIVODESHIP,
# MAGIC   IMGW.LATEST_MEASUREMENT_TIMESTAMP,
# MAGIC   IMGW.AVG_TEMP_WOJ,
# MAGIC   IMGW.AVG_WIND_SPD_WOJ,
# MAGIC   IMGW.AVG_HUMIDITY_WOJ,
# MAGIC   IMGW.AVG_RAIN_WOJ,
# MAGIC   IMGW.AVG_PRESSURE_WOJ,
# MAGIC   IMGW.LATEST_MEASUREMENT_WATER_TIMESTAMP,
# MAGIC   IMGW.AVG_WATER_WOJ,
# MAGIC   IMGW.AVG_WATER_TEMP_WOJ,
# MAGIC   IMGW.LATEST_MEASUREMENT_ICE_TIMESTAMP,
# MAGIC   IMGW.MAX_ICE_OCCR_WOJ,
# MAGIC   IMGW.LATEST_MEASUREMENT_ENCHROACHING_TIMESTAMP,
# MAGIC   IMGW.MAX_ENCHROACHING_WOJ,
# MAGIC   IMGW.EXTRACTION_TS AS IMGW_EXT_TS,
# MAGIC   GIOS.AIR_QUALITY_CHECK_TS,
# MAGIC   GIOS.AVG_RANK AS AVG_AIR_QUALITY_RANK,
# MAGIC   GIOS.MARK AS AIR_QUALITY_MARK,
# MAGIC   GIOS.EXTRACTION_TS AS GIOS_EXT_TS
# MAGIC FROM team1_poc3_silver.imgw_transformed IMGW
# MAGIC LEFT JOIN team1_poc3_silver.gios_transformed GIOS
# MAGIC ON IMGW.VOIVODESHIP = GIOS.VOIVODESHIP

# COMMAND ----------

              MERGE INTO f1_presentation.calculated_race_results tgt
              USING race_result_updated upd
              ON (tgt.driver_id = upd.driver_id AND tgt.race_id = upd.race_id)
              WHEN MATCHED THEN
                UPDATE SET tgt.position = upd.position,
                           tgt.points = upd.points,
                           tgt.calculated_points = upd.calculated_points,
                           tgt.updated_date = current_timestamp
              WHEN NOT MATCHED
                THEN INSERT (race_year, team_name, driver_id, driver_name,race_id, position, points, calculated_points, created_date ) 
                     VALUES (race_year, team_name, driver_id, driver_name,race_id, position, points, calculated_points, current_timestamp)
