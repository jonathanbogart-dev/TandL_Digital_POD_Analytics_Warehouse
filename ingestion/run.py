"""
CLI entry point for running ingestion pipelines.

Usage:
    python -m ingestion.run --all
    python -m ingestion.run --source printful
    python -m ingestion.run --source shopify --start-date 2024-01-01
"""

import argparse
import logging
import os
import sys
from datetime import date, timedelta

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "")

SOURCES = ["printful", "printify", "etsy", "shopify", "stripe"]


def run_printful(start_date: date, end_date: date) -> None:
    from ingestion.loaders.postgres_loader import PostgresLoader
    from ingestion.sources.printful.client import PrintfulClient

    with PrintfulClient() as client:
        orders = client.get_orders(start_date=start_date, end_date=end_date)
        products = client.get_products()

    loader = PostgresLoader(DATABASE_URL)
    loader.load(orders, schema="raw_printful", table="orders", primary_key="id")
    loader.load(products, schema="raw_printful", table="products", primary_key="id")


def run_printify(start_date: date, end_date: date) -> None:
    from ingestion.loaders.postgres_loader import PostgresLoader
    from ingestion.sources.printify.client import PrintifyClient

    with PrintifyClient() as client:
        orders = client.get_orders()

    loader = PostgresLoader(DATABASE_URL)
    loader.load(orders, schema="raw_printify", table="orders", primary_key="id")


def run_etsy(start_date: date, end_date: date) -> None:
    from ingestion.loaders.postgres_loader import PostgresLoader
    from ingestion.sources.etsy.client import EtsyClient

    with EtsyClient() as client:
        receipts = client.get_receipts(start_date=start_date, end_date=end_date)

    loader = PostgresLoader(DATABASE_URL)
    loader.load(receipts, schema="raw_etsy", table="receipts", primary_key="receipt_id")


def run_shopify(start_date: date, end_date: date) -> None:
    from ingestion.loaders.postgres_loader import PostgresLoader
    from ingestion.sources.shopify.client import ShopifyClient

    with ShopifyClient() as client:
        orders = client.get_orders(start_date=start_date, end_date=end_date)
        products = client.get_products()

    loader = PostgresLoader(DATABASE_URL)
    loader.load(orders, schema="raw_shopify", table="orders", primary_key="id")
    loader.load(products, schema="raw_shopify", table="products", primary_key="id")


def run_stripe(start_date: date, end_date: date) -> None:
    from ingestion.loaders.postgres_loader import PostgresLoader
    from ingestion.sources.stripe.client import StripeClient

    with StripeClient() as client:
        charges = client.get_charges(start_date=start_date, end_date=end_date)
        refunds = client.get_refunds(start_date=start_date, end_date=end_date)

    loader = PostgresLoader(DATABASE_URL)
    loader.load(charges, schema="raw_stripe", table="charges", primary_key="id")
    loader.load(refunds, schema="raw_stripe", table="refunds", primary_key="id")


_RUNNERS = {
    "printful": run_printful,
    "printify": run_printify,
    "etsy":     run_etsy,
    "shopify":  run_shopify,
    "stripe":   run_stripe,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run POD ingestion pipelines.")
    parser.add_argument(
        "--source",
        choices=SOURCES,
        help="Run a single source. Omit together with --all to run all.",
    )
    parser.add_argument("--all", action="store_true", help="Run all sources.")
    parser.add_argument(
        "--start-date",
        type=date.fromisoformat,
        default=date.today() - timedelta(days=1),
        help="Start date (YYYY-MM-DD). Default: yesterday.",
    )
    parser.add_argument(
        "--end-date",
        type=date.fromisoformat,
        default=date.today(),
        help="End date (YYYY-MM-DD). Default: today.",
    )
    args = parser.parse_args()

    if not DATABASE_URL:
        logger.error("DATABASE_URL is not set. Check your .env file.")
        sys.exit(1)

    targets = SOURCES if args.all else ([args.source] if args.source else [])
    if not targets:
        parser.print_help()
        sys.exit(1)

    for source in targets:
        logger.info("Running ingestion: %s (%s → %s)", source, args.start_date, args.end_date)
        try:
            _RUNNERS[source](args.start_date, args.end_date)
            logger.info("✓ %s complete.", source)
        except Exception:
            logger.exception("✗ %s failed.", source)


if __name__ == "__main__":
    main()
