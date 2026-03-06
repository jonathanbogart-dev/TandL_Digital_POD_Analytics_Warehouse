"""
Etsy Open API v3 client.

Docs: https://developer.etsy.com/documentation/
Auth: x-api-key header for public endpoints; OAuth2 for shop-level data.
"""

import logging
import os
from datetime import date
from typing import Any

import httpx

from ingestion.utils.retry import with_retry

logger = logging.getLogger(__name__)

_BASE_URL = "https://openapi.etsy.com/v3"
_DEFAULT_TIMEOUT = 30.0
_PAGE_LIMIT = 100


class EtsyClient:
    """HTTP client for the Etsy Open API v3."""

    def __init__(
        self,
        api_key: str | None = None,
        shop_id: str | None = None,
        access_token: str | None = None,
    ) -> None:
        """Initialise the client.

        Args:
            api_key: Etsy API key (keystring). Defaults to ETSY_API_KEY env var.
            shop_id: Etsy shop ID. Defaults to ETSY_SHOP_ID env var.
            access_token: OAuth2 access token for authenticated endpoints.
                          Defaults to ETSY_ACCESS_TOKEN env var.

        Raises:
            ValueError: If api_key or shop_id are not provided.
        """
        self._api_key = api_key or os.environ.get("ETSY_API_KEY")
        self._shop_id = shop_id or os.environ.get("ETSY_SHOP_ID")
        self._access_token = access_token or os.environ.get("ETSY_ACCESS_TOKEN")

        if not self._api_key:
            raise ValueError("ETSY_API_KEY is not set.")
        if not self._shop_id:
            raise ValueError("ETSY_SHOP_ID is not set.")

        headers: dict[str, str] = {"x-api-key": self._api_key}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        self._client = httpx.Client(
            base_url=_BASE_URL,
            headers=headers,
            timeout=_DEFAULT_TIMEOUT,
        )

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> "EtsyClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    @with_retry()
    def _get(self, path: str, params: dict | None = None) -> Any:
        response = self._client.get(path, params=params or {})
        response.raise_for_status()
        return response.json()

    def get_receipts(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
        was_paid: bool = True,
    ) -> list[dict[str, Any]]:
        """Fetch shop receipts (orders), with optional date filtering.

        Args:
            start_date: Fetch receipts created on or after this date.
            end_date: Fetch receipts created on or before this date.
            was_paid: If True, only return paid receipts.

        Returns:
            List of receipt dicts from the Etsy API.
        """
        receipts: list[dict[str, Any]] = []
        offset = 0

        params: dict[str, Any] = {
            "limit": _PAGE_LIMIT,
            "was_paid": str(was_paid).lower(),
        }
        if start_date:
            params["min_created"] = int(
                date.fromisoformat(start_date.isoformat()).strftime("%s")
                if hasattr(date, "strftime")
                else start_date.toordinal()
            )
        if end_date:
            params["max_created"] = int(
                date.fromisoformat(end_date.isoformat()).strftime("%s")
                if hasattr(date, "strftime")
                else end_date.toordinal()
            )

        while True:
            params["offset"] = offset
            body = self._get(f"/application/shops/{self._shop_id}/receipts", params)
            page = body.get("results", [])
            receipts.extend(page)
            count = body.get("count", 0)
            offset += len(page)

            logger.debug("Etsy receipts: fetched %d / %d", offset, count)

            if offset >= count or not page:
                break

        logger.info("Etsy: fetched %d receipts.", len(receipts))
        return receipts
