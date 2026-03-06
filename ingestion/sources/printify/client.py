"""
Printify API client.

Docs: https://printify.com/app/developer/docs
Auth: Bearer token via PRINTIFY_API_KEY environment variable.
"""

import logging
import os
from datetime import date
from typing import Any

import httpx

from ingestion.utils.retry import with_retry

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.printify.com/v1"
_DEFAULT_TIMEOUT = 30.0
_PAGE_LIMIT = 100


class PrintifyClient:
    """HTTP client for the Printify REST API."""

    def __init__(
        self,
        api_key: str | None = None,
        shop_id: str | None = None,
    ) -> None:
        """Initialise the client.

        Args:
            api_key: Printify API key. Defaults to PRINTIFY_API_KEY env var.
            shop_id: Printify shop ID. Defaults to PRINTIFY_SHOP_ID env var.

        Raises:
            ValueError: If api_key or shop_id are missing.
        """
        self._api_key = api_key or os.environ.get("PRINTIFY_API_KEY")
        self._shop_id = shop_id or os.environ.get("PRINTIFY_SHOP_ID")

        if not self._api_key:
            raise ValueError("PRINTIFY_API_KEY is not set.")
        if not self._shop_id:
            raise ValueError("PRINTIFY_SHOP_ID is not set.")

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

    def __enter__(self) -> "PrintifyClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    @with_retry()
    def _get(self, path: str, params: dict | None = None) -> Any:
        response = self._client.get(path, params=params or {})
        response.raise_for_status()
        return response.json()

    def get_orders(self) -> list[dict[str, Any]]:
        """Fetch all orders for the configured shop, handling pagination.

        Returns:
            List of order dicts from the Printify API.
        """
        orders: list[dict[str, Any]] = []
        page = 1

        while True:
            body = self._get(
                f"/shops/{self._shop_id}/orders.json",
                {"page": page, "limit": _PAGE_LIMIT},
            )
            page_data = body.get("data", [])
            orders.extend(page_data)

            last_page = body.get("last_page", page)
            logger.debug("Printify orders: page %d / %d (%d records)", page, last_page, len(page_data))

            if page >= last_page or not page_data:
                break
            page += 1

        logger.info("Printify: fetched %d orders.", len(orders))
        return orders
