.PHONY: help setup test lint format ingest dbt-run dbt-test dbt-docs api-dev clean

# Default target
help:
	@echo ""
	@echo "T&L Digital POD Analytics Warehouse"
	@echo "====================================="
	@echo ""
	@echo "  make setup        Install all Python dependencies"
	@echo "  make up           Start local Docker stack (Postgres + API + Airflow)"
	@echo "  make down         Stop Docker stack"
	@echo "  make test         Run all tests (pytest + dbt tests)"
	@echo "  make lint         Run ruff and sqlfluff"
	@echo "  make format       Auto-format Python (ruff) and SQL (sqlfluff)"
	@echo "  make ingest       Run all ingestion pipelines (dry-run safe)"
	@echo "  make dbt-run      Run dbt models"
	@echo "  make dbt-test     Run dbt data tests"
	@echo "  make dbt-docs     Generate and serve dbt docs at localhost:8888"
	@echo "  make api-dev      Start FastAPI dev server at localhost:8000"
	@echo "  make clean        Remove build artifacts and caches"
	@echo ""

# ── Environment ─────────────────────────────────────────────────────────────

setup:
	pip install -e ".[dev]"
	@echo "✓ Dependencies installed. Copy .env.example → .env and fill in credentials."

# ── Docker ──────────────────────────────────────────────────────────────────

up:
	docker compose up -d
	@echo "✓ Stack started. Postgres: localhost:5432 | API: localhost:8000 | Airflow: localhost:8080"

down:
	docker compose down

# ── Testing ─────────────────────────────────────────────────────────────────

test: test-unit dbt-test

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# ── Linting & Formatting ─────────────────────────────────────────────────────

lint:
	ruff check .
	sqlfluff lint dbt/models/ --dialect postgres

lint-fix:
	ruff check . --fix

format:
	ruff format .
	sqlfluff fix dbt/models/ --dialect postgres

# ── dbt ─────────────────────────────────────────────────────────────────────

DBT_DIR = dbt

dbt-deps:
	cd $(DBT_DIR) && dbt deps

dbt-run:
	cd $(DBT_DIR) && dbt run

dbt-test:
	cd $(DBT_DIR) && dbt test

dbt-compile:
	cd $(DBT_DIR) && dbt compile

dbt-docs:
	cd $(DBT_DIR) && dbt docs generate && dbt docs serve --port 8888

dbt-seed:
	cd $(DBT_DIR) && dbt seed

dbt-freshness:
	cd $(DBT_DIR) && dbt source freshness

# ── Ingestion ────────────────────────────────────────────────────────────────

ingest:
	python -m ingestion.run --all

ingest-printful:
	python -m ingestion.run --source printful

ingest-shopify:
	python -m ingestion.run --source shopify

ingest-etsy:
	python -m ingestion.run --source etsy

ingest-stripe:
	python -m ingestion.run --source stripe

# ── API ──────────────────────────────────────────────────────────────────────

api-dev:
	uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# ── Cleanup ──────────────────────────────────────────────────────────────────

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache"   -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info"    -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleaned."
