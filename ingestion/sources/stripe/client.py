"""
Stripe API client.

Docs: https://stripe.com/docs/api
Auth: Basic auth with STRIPE_SECRET_KEY as username (no password).
"""

import logging
import os
from datetime import date
from typing import Any

import httpx

from ingestion.utils.retry import with_retry

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.stripe.com/v1"
_DEFAULT_TIMEOUT = 30.0
_PAGE_LIMIT = 100


class StripeClient:
    """HTTP client for the Stripe API using cursor-based pagination."""

    def __init__(self, secret_key: str | None = None) -> None:
        """Initialise the client.

        Args:
            secret_key: Stripe secret key. Defaults to STRIPE_SECRET_KEY env var.

        Raises:
            ValueError: If secret_key is not provided or found in environment.
        """
        self._secret_key = secret_key or os.environ.get("STRIPE_SECRET_KEY")
        if not self._secret_key:
            raise ValueError("STRIPE_SECRET_KEY is not set.")

        self._client = httpx.Client(
            base_url=_BASE_URL,
            auth=(self._secret_key, ""),
            timeout=_DEFAULT_TIMEOUT,
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> "StripeClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    @with_retry()
    def _get(self, path: str, params: dict | None = None) -> Any:
        response = self._client.get(path, params=params or {})
        response.raise_for_status()
        return response.json()

    def _paginate(
        self,
        path: str,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Paginate through a Stripe list endpoint using cursor-based pagination.

        Args:
            path: API path (e.g. /charges).
            params: Initial query parameters.

        Returns:
            All records across all pages.
        """
        records: list[dict[str, Any]] = []
        starting_after: str | None = None

        while True:
            if starting_after:
                params["starting_after"] = starting_after

            body = self._get(path, params)
            data = body.get("data", [])
            records.extend(data)

            has_more = body.get("has_more", False)
            if not has_more or not data:
                break
            starting_after = data[-1]["id"]

        return records

    def get_charges(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all charges, optionally filtered by creation date.

        Args:
            start_date: Earliest charge date (inclusive).
            end_date: Latest charge date (inclusive).

        Returns:
            List of Stripe charge dicts.
        """
        import calendar

        params: dict[str, Any] = {"limit": _PAGE_LIMIT}
        if start_date:
            params["created[gte]"] = int(calendar.timegm(start_date.timetuple()))
        if end_date:
            params["created[lte]"] = int(calendar.timegm(end_date.timetuple()))

        charges = self._paginate("/charges", params)
        logger.info("Stripe: fetched %d charges.", len(charges))
        return charges

    def get_refunds(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all refunds, optionally filtered by creation date.

        Args:
            start_date: Earliest refund date (inclusive).
            end_date: Latest refund date (inclusive).

        Returns:
            List of Stripe refund dicts.
        """
        import calendar

        params: dict[str, Any] = {"limit": _PAGE_LIMIT}
        if start_date:
            params["created[gte]"] = int(calendar.timegm(start_date.timetuple()))
        if end_date:
            params["created[lte]"] = int(calendar.timegm(end_date.timetuple()))

        refunds = self._paginate("/refunds", params)
        logger.info("Stripe: fetched %d refunds.", len(refunds))
        return refunds
