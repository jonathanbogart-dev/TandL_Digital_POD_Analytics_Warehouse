"""
Shopify Admin REST API client.

Docs: https://shopify.dev/docs/api/admin-rest
Auth: X-Shopify-Access-Token header via SHOPIFY_ACCESS_TOKEN env var.
"""

import logging
import os
from datetime import date
from typing import Any
from urllib.parse import urlencode

import httpx

from ingestion.utils.retry import with_retry

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 30.0
_PAGE_LIMIT = 250  # Shopify max


class ShopifyClient:
    """HTTP client for the Shopify Admin REST API."""

    def __init__(
        self,
        store_url: str | None = None,
        access_token: str | None = None,
    ) -> None:
        """Initialise the client.

        Args:
            store_url: Shopify store domain (e.g. mystore.myshopify.com).
                       Defaults to SHOPIFY_STORE_URL env var.
            access_token: Admin API access token.
                          Defaults to SHOPIFY_ACCESS_TOKEN env var.

        Raises:
            ValueError: If store URL or access token are missing.
        """
        self._store_url = store_url or os.environ.get("SHOPIFY_STORE_URL")
        self._access_token = access_token or os.environ.get("SHOPIFY_ACCESS_TOKEN")

        if not self._store_url:
            raise ValueError("SHOPIFY_STORE_URL is not set.")
        if not self._access_token:
            raise ValueError("SHOPIFY_ACCESS_TOKEN is not set.")

        self._base_url = f"https://{self._store_url}/admin/api/2024-01"
        self._client = httpx.Client(
            headers={
                "X-Shopify-Access-Token": self._access_token,
                "Content-Type": "application/json",
            },
            timeout=_DEFAULT_TIMEOUT,
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> "ShopifyClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    @with_retry()
    def _get(self, path: str, params: dict | None = None) -> Any:
        url = f"{self._base_url}{path}"
        response = self._client.get(url, params=params or {})
        response.raise_for_status()
        return response.json(), response.headers

    def get_orders(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        status: str = "any",
    ) -> list[dict[str, Any]]:
        """Fetch all orders with cursor-based pagination.

        Args:
            start_date: Fetch orders created on or after this date.
            end_date: Fetch orders created on or before this date.
            status: Shopify order status filter (open, closed, cancelled, any).

        Returns:
            List of Shopify order dicts.
        """
        orders: list[dict[str, Any]] = []
        params: dict[str, Any] = {"limit": _PAGE_LIMIT, "status": status}
        if start_date:
            params["created_at_min"] = f"{start_date.isoformat()}T00:00:00Z"
        if end_date:
            params["created_at_max"] = f"{end_date.isoformat()}T23:59:59Z"

        page_info: str | None = None

        while True:
            if page_info:
                # Cursor pagination: subsequent pages use page_info only
                body, headers = self._get("/orders.json", {"page_info": page_info, "limit": _PAGE_LIMIT})
            else:
                body, headers = self._get("/orders.json", params)

            page_orders = body.get("orders", [])
            orders.extend(page_orders)
            logger.debug("Shopify orders: fetched page of %d", len(page_orders))

            # Parse Link header for next cursor
            link_header = headers.get("link", "")
            page_info = _extract_next_page_info(link_header)
            if not page_info:
                break

        logger.info("Shopify: fetched %d orders.", len(orders))
        return orders

    def get_products(self) -> list[dict[str, Any]]:
        """Fetch all Shopify products.

        Returns:
            List of Shopify product dicts.
        """
        products: list[dict[str, Any]] = []
        page_info: str | None = None

        while True:
            if page_info:
                body, headers = self._get("/products.json", {"page_info": page_info, "limit": _PAGE_LIMIT})
            else:
                body, headers = self._get("/products.json", {"limit": _PAGE_LIMIT})

            page_products = body.get("products", [])
            products.extend(page_products)

            link_header = headers.get("link", "")
            page_info = _extract_next_page_info(link_header)
            if not page_info:
                break

        logger.info("Shopify: fetched %d products.", len(products))
        return products


def _extract_next_page_info(link_header: str) -> str | None:
    """Parse the Shopify Link header and return the next page_info cursor, if any."""
    for part in link_header.split(","):
        part = part.strip()
        if 'rel="next"' in part:
            url_part = part.split(";")[0].strip().strip("<>")
            for segment in url_part.split("&"):
                if segment.startswith("page_info="):
                    return segment.split("=", 1)[1]
    return None
