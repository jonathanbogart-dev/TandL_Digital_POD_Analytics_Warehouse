# Data Architecture

## Overview

The T&L Digital POD Analytics Warehouse follows a **medallion architecture** (raw → staging → intermediate → marts) implemented in dbt on top of PostgreSQL (dev) or BigQuery/Snowflake (prod).

```
┌─────────────────────────────────────────────────────────────┐
│  Source Systems                                              │
│  Printful · Printify · Etsy · Shopify · Stripe              │
└────────────────────┬────────────────────────────────────────┘
                     │  Python ingestion (ingestion/)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Raw / Bronze Layer  (PostgreSQL schemas: raw_*)             │
│  Append-only. Exact copies of API responses.                 │
│  _ingested_at timestamp added to every row.                  │
└────────────────────┬────────────────────────────────────────┘
                     │  dbt staging models (stg_*)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Staging Layer  (schema: staging)                            │
│  Cleaned, typed, and renamed. One model per source table.    │
│  Materialized as views.                                       │
└────────────────────┬────────────────────────────────────────┘
                     │  dbt intermediate models (int_*)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Intermediate Layer  (ephemeral — no table written)          │
│  Cross-source joins, business logic, unions.                 │
└────────────────────┬────────────────────────────────────────┘
                     │  dbt mart models (fct_*, dim_*)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Marts / Gold Layer  (schema: marts)                         │
│  Analytics-ready fact and dimension tables.                  │
│  Materialized as tables.                                      │
└────────────────────┬────────────────────────────────────────┘
                     │  FastAPI (api/)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Consumption Layer                                           │
│  - Static dashboard site (docs/ → GitHub Pages)             │
│  - BI tools (Metabase, Looker, etc.)                        │
│  - Ad-hoc analysis (analysis/notebooks/)                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow Detail

### Ingestion

- **Schedule:** Daily at 02:00 UTC via Airflow DAG `pod_daily_ingestion`
- **Parallelism:** All five sources run concurrently (separate Airflow tasks)
- **Incremental:** Each run fetches `yesterday → today` by default; full backfills supported via CLI
- **Idempotent:** Upsert on source primary key — safe to re-run
- **Raw layer:** Append-only. Records are never deleted; old snapshots remain for audit

### Transformation (dbt)

| Layer | Naming | Materialization | Description |
|---|---|---|---|
| Staging | `stg_<source>__<entity>` | View | Typing, renaming, deduplication |
| Intermediate | `int_<description>` | Ephemeral | Joins, unions, business logic |
| Marts | `fct_<entity>`, `dim_<entity>` | Table | Analytics-ready output |

### API

The FastAPI backend (`api/`) reads from `marts.*` tables and serves three endpoints:

| Endpoint | dbt Model | Dashboard Widget |
|---|---|---|
| `GET /api/kpis` | `fct_orders` | Business Overview KPI cards |
| `GET /api/orders/recent` | `fct_orders` | Recent Orders table |
| `GET /api/revenue/by-source` | `fct_revenue` | Revenue by Source chart |

When `API_BASE_URL` is empty in `docs/js/config.js`, the dashboard falls back to static JSON in `docs/data/`.

---

## Key Design Decisions

### Raw layer is append-only
We never update or delete raw records. If a source record changes, the new version is appended. This preserves a full audit trail and allows reprocessing history.

### Intermediate models are ephemeral
Intermediate models contain business logic that belongs in dbt lineage but doesn't need its own table. They compile inline into mart queries, reducing warehouse storage and query planning overhead.

### Source primary key upsert
The PostgreSQL loader uses `INSERT ... ON CONFLICT DO NOTHING` on the source PK. This means ingestion is idempotent — safe to re-run without creating duplicates.

### Static JSON fallback
The dashboard site can run without a live API by reading from `docs/data/*.json`. This makes the site deployable on GitHub Pages with zero backend infrastructure.

---

## Environment Topology

| Environment | Warehouse | Orchestration | Notes |
|---|---|---|---|
| Local dev | PostgreSQL (Docker) | Manual / Airflow local | `docker compose up` |
| Staging | PostgreSQL or BigQuery | Airflow (Cloud Composer) | PR deployments |
| Production | BigQuery or Snowflake | Airflow (Cloud Composer) | Main branch |
