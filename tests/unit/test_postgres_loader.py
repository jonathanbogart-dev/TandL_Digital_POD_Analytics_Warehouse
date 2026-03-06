"""Unit tests for PostgresLoader._flatten and upsert helper."""

from ingestion.loaders.postgres_loader import _flatten


class TestFlatten:
    def test_flat_dict_unchanged(self) -> None:
        result = _flatten({"a": 1, "b": "x"})
        assert result == {"a": 1, "b": "x"}

    def test_nested_dict_flattened(self) -> None:
        result = _flatten({"outer": {"inner": 42}})
        assert result == {"outer_inner": 42}

    def test_deeply_nested(self) -> None:
        result = _flatten({"a": {"b": {"c": "deep"}}})
        assert result == {"a_b_c": "deep"}

    def test_mixed_types_preserved(self) -> None:
        result = _flatten({"id": 1, "meta": {"flag": True, "score": 3.14}})
        assert result["meta_flag"] is True
        assert result["meta_score"] == pytest.approx(3.14)

    def test_list_values_not_expanded(self) -> None:
        result = _flatten({"tags": ["a", "b"]})
        assert result["tags"] == ["a", "b"]


import pytest
