-- init_db.sql — run once by docker-entrypoint-initdb.d on first container start
-- Creates the Airflow database and all raw-layer schemas.

CREATE DATABASE airflow;

-- Raw layer schemas (one per source)
CREATE SCHEMA IF NOT EXISTS raw_printful;
CREATE SCHEMA IF NOT EXISTS raw_printify;
CREATE SCHEMA IF NOT EXISTS raw_etsy;
CREATE SCHEMA IF NOT EXISTS raw_shopify;
CREATE SCHEMA IF NOT EXISTS raw_stripe;

-- dbt output schemas
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
