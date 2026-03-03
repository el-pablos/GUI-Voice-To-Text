"""Test cache Redis — pastikan fallback aman dan key beda config beda."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.core import cache


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset singleton sebelum setiap test."""
    cache.reset_client()
    yield
    cache.reset_client()


class TestFallbackMode:
    def test_no_redis_env_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Tanpa REDIS_HOST, get_client harus return None."""
        monkeypatch.delenv("REDIS_HOST", raising=False)
        assert cache.get_client() is None

    def test_get_cache_returns_none_without_redis(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Tanpa Redis, get_cache harus return None (bukan crash)."""
        monkeypatch.delenv("REDIS_HOST", raising=False)
        assert cache.get_cache("somekey") is None

    def test_set_cache_returns_false_without_redis(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Tanpa Redis, set_cache harus return False (bukan crash)."""
        monkeypatch.delenv("REDIS_HOST", raising=False)
        assert cache.set_cache("somekey", {"text": "hello"}) is False

    def test_delete_cache_returns_false_without_redis(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("REDIS_HOST", raising=False)
        assert cache.delete_cache("somekey") is False


class TestWithMockRedis:
    @pytest.fixture()
    def mock_redis(self, monkeypatch: pytest.MonkeyPatch):
        """Setup mock Redis client."""
        monkeypatch.setenv("REDIS_HOST", "mock-host")
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        with patch("app.core.cache._get_redis_client", return_value=mock_client):
            cache.reset_client()
            cache._client = mock_client
            cache._client_initialized = True
            yield mock_client

    def test_set_and_get_cache(self, mock_redis: MagicMock) -> None:
        """Set lalu get harus konsisten."""
        test_data = {"segments": [{"text": "halo"}], "duration": 10.5}

        # Mock get untuk return data yang di-set
        mock_redis.get.return_value = json.dumps(test_data)

        result = cache.set_cache("testkey", test_data, ttl=60)
        assert result is True

        cached = cache.get_cache("testkey")
        assert cached is not None
        assert cached["segments"][0]["text"] == "halo"

    def test_cache_miss(self, mock_redis: MagicMock) -> None:
        """Cache miss harus return None."""
        mock_redis.get.return_value = None
        assert cache.get_cache("nonexistent") is None

    def test_delete_cache(self, mock_redis: MagicMock) -> None:
        """Delete harus berhasil."""
        assert cache.delete_cache("testkey") is True
        mock_redis.delete.assert_called_once()


class TestCacheKeyIntegration:
    def test_different_config_different_result(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Cache dengan config beda harus miss (bukan hit palsu)."""
        from app.core.hashing import cache_key

        key_id = cache_key("filehash", language="id")
        key_en = cache_key("filehash", language="en")
        assert key_id != key_en

        # Tanpa Redis: keduanya return None (no false positive)
        monkeypatch.delenv("REDIS_HOST", raising=False)
        assert cache.get_cache(key_id) is None
        assert cache.get_cache(key_en) is None
