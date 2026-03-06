"""Unit tests for the Shopify API client."""

import pytest
import httpx


def _make_client() -> "ShopifyClient":
    from ingestion.sources.shopify.client import ShopifyClient
    return ShopifyClient(
        store_url="test.myshopify.com",
        access_token="test-token",
    )


class TestShopifyClientInit:
    def test_raises_without_store_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SHOPIFY_STORE_URL", raising=False)
        monkeypatch.delenv("SHOPIFY_ACCESS_TOKEN", raising=False)
        from ingestion.sources.shopify.client import ShopifyClient
        with pytest.raises(ValueError, match="SHOPIFY_STORE_URL"):
            ShopifyClient(store_url=None, access_token="token")

    def test_raises_without_access_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SHOPIFY_ACCESS_TOKEN", raising=False)
        from ingestion.sources.shopify.client import ShopifyClient
        with pytest.raises(ValueError, match="SHOPIFY_ACCESS_TOKEN"):
            ShopifyClient(store_url="test.myshopify.com", access_token=None)


class TestExtractNextPageInfo:
    def test_returns_none_when_no_link_header(self) -> None:
        from ingestion.sources.shopify.client import _extract_next_page_info
        assert _extract_next_page_info("") is None

    def test_extracts_cursor_from_link_header(self) -> None:
        from ingestion.sources.shopify.client import _extract_next_page_info
        link = '<https://test.myshopify.com/admin/api/2024-01/orders.json?page_info=abc123&limit=250>; rel="next"'
        assert _extract_next_page_info(link) == "abc123"

    def test_returns_none_when_only_prev(self) -> None:
        from ingestion.sources.shopify.client import _extract_next_page_info
        link = '<https://test.myshopify.com/admin/api/2024-01/orders.json?page_info=abc123&limit=250>; rel="previous"'
        assert _extract_next_page_info(link) is None
