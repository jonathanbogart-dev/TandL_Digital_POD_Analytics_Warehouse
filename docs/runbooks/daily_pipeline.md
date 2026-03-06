# Runbook: Daily Ingestion Pipeline

## Overview

The daily ingestion pipeline runs automatically at **02:00 UTC** via the Airflow DAG `pod_daily_ingestion`. It fetches the previous day's data from all source APIs, loads it into the raw layer, and triggers dbt to refresh the staging and mart models.

---

## Normal Operating Procedure

The pipeline requires no manual intervention under normal conditions. Monitor it via:

- **Airflow UI:** `http://localhost:8080` (local) or your hosted Airflow instance
- **DAG:** `pod_daily_ingestion`
- **Expected runtime:** 10–20 minutes total

---

## Alerting

Airflow sends task-level failure notifications when email alerts are configured. Check `default_args` in `pipelines/dags/pod_daily_ingestion.py` to update the email list.

---

## Manual Trigger (Backfill)

To re-run for a specific date range:

```bash
# Single day
python -m ingestion.run --all --start-date 2024-03-01 --end-date 2024-03-01

# Single source
python -m ingestion.run --source shopify --start-date 2024-01-01 --end-date 2024-03-01
```

Or via Airflow CLI:
```bash
airflow dags backfill pod_daily_ingestion --start-date 2024-03-01 --end-date 2024-03-07
```

---

## Common Failures

### Task: `ingest_<source>` fails

**Symptoms:** Airflow task shows red; logs contain `HTTPStatusError` or `ValueError`.

**Checks:**
1. Verify the API key is set: `echo $PRINTFUL_API_KEY` (or relevant key)
2. Check the source API status page for outages
3. Look for rate-limit errors (HTTP 429) — the client retries automatically up to 4 times

**Resolution:**
- If the API was down, re-trigger the failed task from Airflow UI
- If credentials expired, update `.env` and restart the Airflow scheduler

### Task: `dbt_run` fails

**Symptoms:** dbt compilation or model execution error.

**Checks:**
```bash
cd dbt && dbt run --select <failing_model> --debug
```

**Common causes:**
- Raw table schema changed (new/removed column from source API)
- Database connection issue

**Resolution:**
- Schema change: update the staging model and `schema.yml`
- Connection issue: verify `DATABASE_URL` and Postgres health

### Task: `dbt_test` fails

**Symptoms:** Data quality test failures (uniqueness, not_null, accepted_values).

**Checks:**
```bash
cd dbt && dbt test --select <failing_model>
```

**Resolution:**
- Duplicate PKs: investigate upstream ingestion for double-loading
- Null violations: check if source API changed a previously required field
- Accepted values failure: add new status value to the `accepted_values` list in `schema.yml`

---

## Data Freshness Check

```bash
cd dbt && dbt source freshness
```

Expected output: all sources GREEN (< 24h stale). WARN at 24h, ERROR at 48h.

---

## Full Reset (Emergency)

> **Warning:** This deletes all raw data. Only use as a last resort.

```bash
# Drop and recreate all raw schemas
psql $DATABASE_URL -c "
  DROP SCHEMA IF EXISTS raw_printful CASCADE;
  DROP SCHEMA IF EXISTS raw_printify CASCADE;
  DROP SCHEMA IF EXISTS raw_etsy CASCADE;
  DROP SCHEMA IF EXISTS raw_shopify CASCADE;
  DROP SCHEMA IF EXISTS raw_stripe CASCADE;
"
psql $DATABASE_URL -f scripts/init_db.sql

# Full backfill from start date
python -m ingestion.run --all --start-date 2024-01-01 --end-date $(date +%Y-%m-%d)

# Rebuild dbt models
cd dbt && dbt run && dbt test
```
