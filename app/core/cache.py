"""Cache Redis — simpan dan ambil hasil transkrip biar ga proses ulang."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_TTL = 86400 * 30  # 30 hari


def _get_redis_client() -> Any | None:
    """Buat Redis client dari environment variable.

    Returns:
        Redis client instance, atau None jika env tidak diset / koneksi gagal.
    """
    host = os.environ.get("REDIS_HOST")
    if not host:
        logger.info("REDIS_HOST tidak diset, cache Redis dinonaktifkan (fallback mode).")
        return None

    try:
        import redis

        port = int(os.environ.get("REDIS_PORT", "6379"))
        username = os.environ.get("REDIS_USER", None)
        password = os.environ.get("REDIS_PASSWORD", None)
        db = int(os.environ.get("REDIS_DB", "0"))

        client = redis.Redis(
            host=host,
            port=port,
            username=username,
            password=password,
            db=db,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        client.ping()
        logger.info("Koneksi Redis berhasil ke %s:%s", host, port)
        return client
    except Exception as e:
        logger.warning("Gagal konek Redis: %s — fallback ke no-cache mode.", e)
        return None


# Singleton client
_client: Any | None = None
_client_initialized = False


def get_client() -> Any | None:
    """Ambil singleton Redis client."""
    global _client, _client_initialized
    if not _client_initialized:
        _client = _get_redis_client()
        _client_initialized = True
    return _client


def reset_client() -> None:
    """Reset singleton (untuk testing)."""
    global _client, _client_initialized
    _client = None
    _client_initialized = False


def get_cache(key: str) -> dict[str, Any] | None:
    """Ambil hasil transkrip dari cache.

    Args:
        key: Cache key (dari hashing.cache_key).

    Returns:
        Dict hasil transkrip, atau None jika tidak ada / Redis mati.
    """
    client = get_client()
    if client is None:
        return None

    try:
        data = client.get(f"transkrip:{key}")
        if data:
            logger.info("Cache HIT untuk key %s", key[:16])
            return json.loads(data)
        logger.info("Cache MISS untuk key %s", key[:16])
        return None
    except Exception as e:
        logger.warning("Error baca cache: %s", e)
        return None


def set_cache(key: str, result: dict[str, Any], ttl: int | None = None) -> bool:
    """Simpan hasil transkrip ke cache.

    Args:
        key: Cache key.
        result: Dict hasil transkrip (segments, metadata, dll).
        ttl: Time-to-live dalam detik. Default dari env CACHE_TTL_SECONDS atau 30 hari.

    Returns:
        True jika berhasil, False jika gagal / Redis mati.
    """
    client = get_client()
    if client is None:
        return False

    if ttl is None:
        ttl = int(os.environ.get("CACHE_TTL_SECONDS", str(DEFAULT_TTL)))

    try:
        payload = result.copy()
        payload["_cached_at"] = time.time()
        client.setex(f"transkrip:{key}", ttl, json.dumps(payload, ensure_ascii=False))
        logger.info("Cache SET untuk key %s (TTL=%ds)", key[:16], ttl)
        return True
    except Exception as e:
        logger.warning("Error tulis cache: %s", e)
        return False


def delete_cache(key: str) -> bool:
    """Hapus cache entry."""
    client = get_client()
    if client is None:
        return False
    try:
        client.delete(f"transkrip:{key}")
        return True
    except Exception:
        return False
