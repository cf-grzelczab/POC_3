# Databricks notebook source
# MAGIC %sql
# MAGIC -- Databricks notebook source
# MAGIC -- DROP DATABASE IF EXISTS poland_fire_processed CASCADE;
# MAGIC
# MAGIC -- COMMAND ----------
# MAGIC
# MAGIC CREATE DATABASE IF NOT EXISTS silver;
# MAGIC
# MAGIC -- COMMAND ----------
# MAGIC
# MAGIC -- DROP DATABASE IF EXISTS poland_fire_presentation CASCADE;
# MAGIC
# MAGIC -- COMMAND ----------
# MAGIC
# MAGIC CREATE DATABASE IF NOT EXISTS gold;
