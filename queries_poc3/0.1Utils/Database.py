# Databricks notebook source
# MAGIC %sql
# MAGIC -- Databricks notebook source
# MAGIC -- DROP DATABASE IF EXISTS team1_poc3_bronze CASCADE;
# MAGIC
# MAGIC CREATE DATABASE IF NOT EXISTS team1_poc3_bronze
# MAGIC LOCATION "abfss://poc3@team1poc3dls.dfs.core.windows.net/bronze";
# MAGIC
# MAGIC -- DROP DATABASE IF EXISTS poland_fire_presentation CASCADE;
# MAGIC
# MAGIC CREATE DATABASE IF NOT EXISTS team1_poc3_silver 
# MAGIC LOCATION "abfss://poc3@team1poc3dls.dfs.core.windows.net/silver";
