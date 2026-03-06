"""
Printful API client.

Docs: https://developers.printful.com/docs/
Auth: Bearer token via PRINTFUL_API_KEY environment variable.
"""

import logging
import os
from datetime import date, datetime
from typing import Any

import httpx

from ingestion.utils.retry import with_retry

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.printful.com"
_DEFAULT_TIMEOUT = 30.0
_PAGE_LIMIT = 100


class PrintfulClient:
    """HTTP client for the Printful REST API."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialise the client.

        Args:
            api_key: Printful API key. Defaults to PRINTFUL_API_KEY env var.

        Raises:
            ValueError: If no API key is provided or found in the environment.
        """
        self._api_key = api_key or os.environ.get("PRINTFUL_API_KEY")
        if not self._api_key:
            raise ValueError("PRINTFUL_API_KEY is not set.")

        self._client = httpx.Client(
            base_url=_BASE_URL,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=_DEFAULT_TIMEOUT,
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> "PrintfulClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    @with_retry()
    def _get(self, path: str, params: dict | None = None) -> Any:
        """Make an authenticated GET request.

        Args:
            path: API path (relative to base URL).
            params: Optional query parameters.

        Returns:
            Parsed JSON response body.

        Raises:
            httpx.HTTPStatusError: On non-2xx responses.
        """
        response = self._client.get(path, params=params or {})
        response.raise_for_status()
        return response.json()

    def get_orders(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all orders, optionally filtered by date range.

        Handles pagination automatically.

        Args:
            start_date: Earliest order creation date (inclusive).
            end_date: Latest order creation date (inclusive).

        Returns:
            List of order dicts as returned by the Printful API.
        """
        orders: list[dict[str, Any]] = []
        offset = 0

        while True:
            params: dict[str, Any] = {"limit": _PAGE_LIMIT, "offset": offset}
            if start_date:
                params["from_date"] = start_date.isoformat()
            if end_date:
                params["to_date"] = end_date.isoformat()

            body = self._get("/orders", params=params)
            page = body.get("result", [])
            orders.extend(page)

            paging = body.get("paging", {})
            total = paging.get("total", 0)
            offset += len(page)

            logger.debug("Printful orders: fetched %d / %d", offset, total)

            if offset >= total or not page:
                break

        logger.info("Printful: fetched %d orders total.", len(orders))
        return orders

    def get_products(self) -> list[dict[str, Any]]:
        """Fetch the Printful sync product catalog.

        Returns:
            List of sync product dicts.
        """
        products: list[dict[str, Any]] = []
        offset = 0

        while True:
            body = self._get("/store/products", params={"limit": _PAGE_LIMIT, "offset": offset})
            page = body.get("result", [])
            products.extend(page)

            paging = body.get("paging", {})
            total = paging.get("total", 0)
            offset += len(page)

            if offset >= total or not page:
                break

        logger.info("Printful: fetched %d products.", len(products))
        return products
