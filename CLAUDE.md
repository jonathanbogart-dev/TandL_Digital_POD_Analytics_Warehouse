# CLAUDE.md — T&L Digital POD Analytics Warehouse

This file provides guidance for AI assistants (Claude and others) working in this repository. It covers project purpose, directory conventions, development workflows, and coding standards.

---

## Project Overview

**T&L Digital POD Analytics Warehouse** is a data analytics platform for T&L Digital's Print-on-Demand (POD) business. It aggregates, transforms, and exposes data from POD operations (orders, products, fulfillment, revenue) into a structured analytics warehouse for reporting and business intelligence.

### Core Goals
- Centralize POD data from multiple sources (storefronts, fulfillment partners, payment processors)
- Provide clean, documented data models for analysts and BI tools
- Automate data ingestion and transformation pipelines
- Support ad-hoc analysis via notebooks and SQL queries

---

## Repository Structure

```
TandL_Digital_POD_Analytics_Warehouse/
├── CLAUDE.md                  # This file
├── README.md                  # Project overview and quick-start
├── .env.example               # Required environment variables (no secrets)
├── .gitignore
├── docker-compose.yml         # Local development stack
├── Makefile                   # Common commands (setup, test, lint, run)
│
├── dbt/                       # dbt data transformation project
│   ├── dbt_project.yml
│   ├── profiles.yml.example
│   ├── models/
│   │   ├── staging/           # Raw source data cleaned and typed
│   │   ├── intermediate/      # Business logic, joins, aggregations
│   │   └── marts/             # Final analytics-ready tables
│   ├── seeds/                 # Static reference data (CSV)
│   ├── tests/                 # dbt data tests
│   ├── macros/                # Reusable SQL macros
│   └── docs/                  # dbt documentation
│
├── ingestion/                 # Data ingestion / EL scripts
│   ├── sources/               # One module per data source
│   │   ├── printful/
│   │   ├── printify/
│   │   ├── etsy/
│   │   ├── shopify/
│   │   └── stripe/
│   ├── loaders/               # Database loaders (raw layer writes)
│   └── utils/                 # Shared ingestion utilities
│
├── pipelines/                 # Orchestration (Airflow DAGs or similar)
│   ├── dags/
│   └── operators/
│
├── analysis/                  # Exploratory notebooks and one-off SQL
│   ├── notebooks/             # Jupyter notebooks
│   └── sql/                   # Ad-hoc SQL queries
│
├── tests/                     # Python unit + integration tests
│   ├── unit/
│   └── integration/
│
├── scripts/                   # Utility scripts (setup, backfill, etc.)
│
└── docs/                      # Project documentation
    ├── architecture.md
    ├── data_dictionary.md
    └── runbooks/
```

> **Note:** The repository is currently in initial setup. Add files following this structure as the project grows.

---

## Tech Stack

| Layer | Tool/Technology |
|---|---|
| Language | Python 3.11+ |
| Transformation | dbt (Data Build Tool) |
| Warehouse | PostgreSQL (dev) / BigQuery or Snowflake (prod) |
| Orchestration | Apache Airflow or Dagster |
| Containerization | Docker / Docker Compose |
| Testing | pytest, dbt tests |
| Linting | ruff (Python), sqlfluff (SQL) |
| Dependency Management | pip + `requirements.txt` or `pyproject.toml` |
| Notebooks | Jupyter |

---

## Development Setup

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- dbt CLI (`pip install dbt-postgres` or relevant adapter)
- A `.env` file copied from `.env.example` with real credentials

### Quick Start
```bash
# Clone and enter the repo
git clone <repo-url>
cd TandL_Digital_POD_Analytics_Warehouse

# Copy and fill in environment variables
cp .env.example .env
# Edit .env with your credentials

# Start local database and services
docker compose up -d

# Install Python dependencies
pip install -r requirements.txt

# Run dbt to build models
cd dbt && dbt deps && dbt run

# Run tests
make test
```

### Makefile Targets
```bash
make setup        # Install all dependencies
make test         # Run all tests (pytest + dbt tests)
make lint         # Run ruff and sqlfluff
make format       # Auto-format Python (ruff --fix) and SQL
make ingest       # Run all ingestion pipelines
make dbt-run      # Run dbt models
make dbt-test     # Run dbt data tests
make dbt-docs     # Generate and serve dbt docs
make clean        # Remove build artifacts and caches
```

---

## Coding Conventions

### Python

- **Style**: Follow PEP 8. Use `ruff` for linting and formatting.
- **Type hints**: Required on all public functions and class methods.
- **Docstrings**: Use Google-style docstrings for all public functions and classes.
- **Imports**: Standard library → third-party → local, separated by blank lines.
- **Environment variables**: Never hardcode credentials. Use `os.environ` or `python-dotenv`. Load from `.env`.
- **Error handling**: Raise specific exceptions. Log errors before re-raising in pipelines.
- **Logging**: Use Python's `logging` module, not `print()`. Configure at the top of each module.

```python
# Good
import logging

logger = logging.getLogger(__name__)

def fetch_orders(start_date: str, end_date: str) -> list[dict]:
    """Fetch orders from Printful API within a date range.

    Args:
        start_date: ISO 8601 date string (YYYY-MM-DD).
        end_date: ISO 8601 date string (YYYY-MM-DD).

    Returns:
        List of order dicts from the API response.

    Raises:
        APIError: If the API request fails.
    """
    ...
```

### SQL / dbt

- **Naming**: Use `snake_case` for all model names, column names, and schema names.
- **Model prefixes**:
  - `stg_` — staging models (one per source table, minimal transformation)
  - `int_` — intermediate models (joins, business logic)
  - `fct_` — fact tables (events, transactions)
  - `dim_` — dimension tables (entities: products, customers, etc.)
- **CTEs**: Prefer CTEs over nested subqueries. Name CTEs descriptively.
- **Column ordering**: Keys first, then dates, then attributes, then metrics.
- **Tests**: Every model must have at minimum `not_null` and `unique` tests on primary keys.
- **Documentation**: Every model and column in `schema.yml` must have a `description`.
- **Ref over direct table**: Always use `{{ ref('model_name') }}` or `{{ source('source', 'table') }}` — never raw table names.

```sql
-- Good dbt model: stg_printful__orders.sql
with source as (
    select * from {{ source('printful', 'orders') }}
),

renamed as (
    select
        id                          as order_id,
        external_id                 as external_order_id,
        status                      as order_status,
        created                     as created_at,
        updated                     as updated_at,
        total_retail_costs_total    as order_total_usd

    from source
)

select * from renamed
```

### Git

- **Branch naming**: `feature/<short-description>`, `fix/<short-description>`, `chore/<short-description>`
- **Commit messages**: Use the imperative mood. Be specific.
  - Good: `Add Printful order ingestion pipeline`
  - Bad: `updates`, `WIP`, `fix stuff`
- **PR size**: Keep PRs focused. One logical change per PR.
- **No secrets in git**: Never commit `.env`, credentials, API keys, or tokens. They belong in `.gitignore` and secret management.

---

## Data Architecture

### Layers

```
Sources (APIs, databases, files)
    ↓
Raw / Bronze Layer    — exact copies of source data, append-only
    ↓
Staging Layer         — cleaned, typed, renamed (stg_ models)
    ↓
Intermediate Layer    — business logic, joins (int_ models)
    ↓
Marts / Gold Layer    — analytics-ready facts and dims (fct_, dim_ models)
```

### Key Data Domains

- **Orders**: POD order lifecycle from placement to fulfillment
- **Products**: SKUs, variants, catalog metadata
- **Fulfillment**: Partner performance, shipping, returns
- **Revenue**: Sales, refunds, fees, payouts
- **Marketing**: Channel attribution, campaign performance

### Source Systems

| Source | Type | Description |
|---|---|---|
| Printful | API | POD fulfillment partner |
| Printify | API | POD fulfillment partner |
| Etsy | API | Storefront / marketplace |
| Shopify | API | Storefront |
| Stripe | API | Payment processing |

---

## Environment Variables

All secrets and environment-specific settings live in `.env` (gitignored). Copy `.env.example` to get started.

Key variables expected:
```
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/pod_warehouse

# Printful
PRINTFUL_API_KEY=

# Printify
PRINTIFY_API_KEY=
PRINTIFY_SHOP_ID=

# Etsy
ETSY_API_KEY=
ETSY_API_SECRET=
ETSY_SHOP_ID=

# Shopify
SHOPIFY_STORE_URL=
SHOPIFY_ACCESS_TOKEN=

# Stripe
STRIPE_SECRET_KEY=

# Airflow (if used)
AIRFLOW__CORE__FERNET_KEY=
AIRFLOW__CORE__SQL_ALCHEMY_CONN=
```

---

## Testing

### Python Tests
- Located in `tests/`
- Run with `pytest`
- Unit tests mock external API calls; do not make real network requests in tests
- Integration tests use a local test database (spun up via Docker Compose)

### dbt Tests
- Data quality tests defined in `schema.yml` files alongside models
- Run with `dbt test`
- Every model's primary key must be `not_null` + `unique`
- Critical business metrics should have `accepted_values` or custom tests

### CI Checks (when configured)
- Linting: `ruff check .`
- Type checking: `mypy .` (if configured)
- SQL linting: `sqlfluff lint dbt/models/`
- Unit tests: `pytest tests/unit/`
- dbt compile: `dbt compile`

---

## Common Tasks for AI Assistants

### Adding a New Data Source
1. Create `ingestion/sources/<source_name>/` with a client module and extractor
2. Add `raw` table definitions and a source definition in `dbt/models/staging/sources.yml`
3. Create `stg_<source>__<entity>.sql` staging models
4. Add `not_null` and `unique` tests in `schema.yml`
5. Update `.env.example` with any new required variables
6. Document the source in `docs/data_dictionary.md`

### Adding a dbt Model
1. Place the file in the appropriate layer (`staging/`, `intermediate/`, `marts/`)
2. Follow the naming convention (`stg_`, `int_`, `fct_`, `dim_`)
3. Add the model to the corresponding `schema.yml` with a description and column docs
4. Add primary key tests (`not_null`, `unique`)
5. Run `dbt run --select <model_name>` to verify
6. Run `dbt test --select <model_name>` to validate

### Modifying Ingestion Scripts
1. Read the existing source client before making changes
2. Maintain backwards compatibility with existing raw table schemas when possible
3. If schema changes are needed, create a migration and update downstream dbt models
4. Add or update unit tests for any changed logic

---

## What NOT to Do

- **Never commit secrets or credentials** to git, even in test files
- **Never query raw tables directly** in marts — always go through staging models
- **Never use `SELECT *`** in dbt models (except in the `source` CTE at the top of staging models)
- **Never bypass linting** — fix linting errors rather than suppressing them
- **Never hardcode dates or IDs** in transformation logic — use variables/macros
- **Never delete raw data** — the raw layer is append-only for auditability
- **Never push directly to `main`** — all changes go through PRs

---

## Useful References

- [dbt Documentation](https://docs.getdbt.com/)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [Printful API Docs](https://developers.printful.com/docs/)
- [Printify API Docs](https://printify.com/app/developer/docs)
- [Etsy API Docs](https://developer.etsy.com/documentation/)
- [Shopify API Docs](https://shopify.dev/docs/api)
- [Stripe API Docs](https://stripe.com/docs/api)
- [SQLFluff](https://docs.sqlfluff.com/)
- [Ruff](https://docs.astral.sh/ruff/)

---

*Last updated: 2026-03-06. Update this file whenever project structure, conventions, or tooling changes.*
