"""
POD Daily Ingestion DAG

Runs every night at 02:00 UTC:
  1. Ingests raw data from all source APIs (Printful, Printify, Etsy, Shopify, Stripe)
  2. Runs dbt to refresh staging, intermediate, and mart models

Schedule: 0 2 * * *  (02:00 UTC daily)
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# ---------------------------------------------------------------------------
# Default args
# ---------------------------------------------------------------------------
default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="pod_daily_ingestion",
    description="Ingest POD source data and run dbt transformations.",
    schedule="0 2 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["ingestion", "dbt", "daily"],
    doc_md=__doc__,
) as dag:

    # ── Ingestion tasks ────────────────────────────────────────────────────

    def _make_ingest_task(source: str) -> PythonOperator:
        """Create a PythonOperator that runs the ingestion for one source."""

        def _run(**context: dict) -> None:
            import sys

            sys.path.insert(0, "/opt/airflow")

            from ingestion.run import _RUNNERS

            logical_date = context["logical_date"].date()
            start_date = logical_date - timedelta(days=1)
            end_date = logical_date

            _RUNNERS[source](start_date=start_date, end_date=end_date)

        return PythonOperator(
            task_id=f"ingest_{source}",
            python_callable=_run,
        )

    ingest_printful  = _make_ingest_task("printful")
    ingest_printify  = _make_ingest_task("printify")
    ingest_etsy      = _make_ingest_task("etsy")
    ingest_shopify   = _make_ingest_task("shopify")
    ingest_stripe    = _make_ingest_task("stripe")

    # ── dbt tasks ──────────────────────────────────────────────────────────

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt && dbt run --profiles-dir /opt/airflow/dbt",
        env={**os.environ, "DBT_PROFILES_DIR": "/opt/airflow/dbt"},
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt && dbt test --profiles-dir /opt/airflow/dbt",
        env={**os.environ, "DBT_PROFILES_DIR": "/opt/airflow/dbt"},
    )

    # ── Dependencies ───────────────────────────────────────────────────────
    #
    # All ingestion runs in parallel, then dbt runs, then dbt tests.

    ingestion_tasks = [
        ingest_printful,
        ingest_printify,
        ingest_etsy,
        ingest_shopify,
        ingest_stripe,
    ]

    ingestion_tasks >> dbt_run >> dbt_test
