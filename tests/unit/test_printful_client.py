"""Unit tests for the Printful API client.

All HTTP calls are mocked — no network access required.
"""

import pytest
import httpx

from unittest.mock import MagicMock, patch


def _make_client(api_key: str = "test-key") -> "PrintfulClient":
    from ingestion.sources.printful.client import PrintfulClient
    return PrintfulClient(api_key=api_key)


class TestPrintfulClientInit:
    def test_raises_without_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PRINTFUL_API_KEY", raising=False)
        from ingestion.sources.printful.client import PrintfulClient
        with pytest.raises(ValueError, match="PRINTFUL_API_KEY"):
            PrintfulClient(api_key=None)

    def test_accepts_explicit_key(self) -> None:
        client = _make_client("my-key")
        assert client._api_key == "my-key"


class TestGetOrders:
    def test_returns_empty_on_empty_response(self, respx_mock) -> None:
        import respx

        respx_mock.get("https://api.printful.com/orders").mock(
            return_value=httpx.Response(
                200,
                json={"result": [], "paging": {"total": 0, "offset": 0, "limit": 100}},
            )
        )
        client = _make_client()
        orders = client.get_orders()
        assert orders == []

    def test_single_page(self, respx_mock) -> None:
        import respx

        fake_orders = [{"id": "1", "status": "fulfilled"}, {"id": "2", "status": "pending"}]
        respx_mock.get("https://api.printful.com/orders").mock(
            return_value=httpx.Response(
                200,
                json={"result": fake_orders, "paging": {"total": 2, "offset": 0, "limit": 100}},
            )
        )
        client = _make_client()
        orders = client.get_orders()
        assert len(orders) == 2
        assert orders[0]["id"] == "1"
