# T&L Digital POD Analytics Warehouse

A data analytics platform for T&L Digital's Print-on-Demand business. Aggregates data from POD storefronts and fulfillment partners into a structured analytics warehouse for reporting and BI.

**Live dashboard:** [GitHub Pages site](https://jonathanbogart-dev.github.io/TandL_Digital_POD_Analytics_Warehouse/)

---

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- dbt CLI (`pip install dbt-postgres`)

### Setup

```bash
# 1. Clone
git clone <repo-url>
cd TandL_Digital_POD_Analytics_Warehouse

# 2. Configure environment
cp .env.example .env
# Fill in API keys and database credentials

# 3. Install Python dependencies
make setup

# 4. Start local stack (Postgres + API + Airflow)
make up

# 5. Seed dbt and run models
make dbt-seed
make dbt-run

# 6. Verify with tests
make test
```

---

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Transformation | dbt (postgres adapter) |
| Warehouse | PostgreSQL (dev) / BigQuery or Snowflake (prod) |
| Orchestration | Apache Airflow 2.9 |
| API | FastAPI |
| Containerization | Docker Compose |
| Testing | pytest, dbt tests |
| Linting | ruff (Python), sqlfluff (SQL) |

---

## Architecture

```
POD Sources (Printful, Printify, Etsy, Shopify, Stripe)
    ↓  ingestion/
Raw Layer (PostgreSQL — append-only)
    ↓  dbt staging models (stg_*)
Staging Layer (typed, renamed, deduped)
    ↓  dbt intermediate models (int_*)
Intermediate Layer (joins, business logic)
    ↓  dbt mart models (fct_*, dim_*)
Analytics Marts
    ↓  FastAPI (api/)
Dashboard / BI Tools (docs/ static site + GitHub Pages)
```

See [`docs/architecture.md`](docs/architecture.md) for the full diagram.

---

## Repository Structure

```
├── api/              FastAPI backend (serves /kpis, /orders, /revenue)
├── dbt/              dbt transformation project
│   ├── models/
│   │   ├── staging/      stg_* models — one per source table
│   │   ├── intermediate/ int_* models — joins and business logic
│   │   └── marts/        fct_* and dim_* analytics-ready tables
│   └── seeds/            static reference CSVs
├── docs/             Static website (GitHub Pages)
│   ├── index.html    Dashboard hub
│   ├── js/           config, api, data, charts, main modules
│   └── data/         static JSON fallback data
├── ingestion/        Source API clients and raw loaders
│   ├── sources/      one module per source (printful, shopify, …)
│   └── loaders/      raw-layer database writers
├── pipelines/        Airflow DAGs
├── analysis/         Jupyter notebooks and ad-hoc SQL
├── tests/            pytest unit and integration tests
└── scripts/          Utility scripts (db init, backfill, etc.)
```

---

## Common Commands

```bash
make help           # list all targets
make up / down      # start / stop Docker stack
make dbt-run        # run all dbt models
make dbt-test       # run dbt data quality tests
make test           # run pytest
make lint           # ruff + sqlfluff
make api-dev        # start FastAPI at localhost:8000
make ingest         # run all ingestion pipelines
```

---

## Data Sources

| Source | Type | Data |
|---|---|---|
| Printful | REST API | Orders, fulfillment, shipping |
| Printify | REST API | Orders, products, variants |
| Etsy | REST API | Listings, orders, revenue |
| Shopify | REST API | Orders, customers, products |
| Stripe | REST API | Payments, refunds, payouts |

---

## Development

See [`CLAUDE.md`](CLAUDE.md) for full coding conventions, data architecture decisions, and AI assistant instructions.

### Running tests

```bash
make test-unit          # fast, no DB required
make test-integration   # requires running Docker stack
make dbt-test           # dbt data quality tests
```

### Adding a new data source

1. Create `ingestion/sources/<source>/client.py`
2. Add source definition to `dbt/models/staging/sources.yml`
3. Create `stg_<source>__<entity>.sql` staging models
4. Add to `pipelines/dags/pod_daily_ingestion.py`
5. Update `.env.example` with new credentials
