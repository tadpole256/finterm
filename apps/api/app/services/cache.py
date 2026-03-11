from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CacheResult:
    payload: dict[str, Any] | None
    source: str


class InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[datetime, str]] = {}

    def get(self, key: str) -> str | None:
        item = self._store.get(key)
        if item is None:
            return None
        expires_at, value = item
        if datetime.now(UTC) > expires_at:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        self._store[key] = (datetime.now(UTC) + timedelta(seconds=ttl_seconds), value)


class CacheService:
    def __init__(self) -> None:
        settings = get_settings()
        self._redis: Redis[str] | None
        try:
            self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
            self._redis.ping()
            self._backend = "redis"
        except RedisError:
            self._redis = None
            self._backend = "memory"
            logger.warning("Redis unavailable. Falling back to in-memory cache.")
        self._memory = InMemoryCache()

    @property
    def backend(self) -> str:
        return self._backend

    def get_json(self, key: str) -> CacheResult:
        raw: str | None = None
        source = self._backend

        if self._redis is not None:
            try:
                raw = self._redis.get(key)
            except RedisError:
                logger.warning("Redis get failed for key %s. Using in-memory cache.", key)
                source = "memory-degraded"

        if raw is None:
            raw = self._memory.get(key)
            if raw is not None and source == "redis":
                source = "memory-degraded"

        if raw is None:
            return CacheResult(payload=None, source=source)

        return CacheResult(payload=json.loads(raw), source=source)

    def set_json(self, key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        raw = json.dumps(payload)

        if self._redis is not None:
            try:
                self._redis.setex(key, ttl_seconds, raw)
                return
            except RedisError:
                logger.warning("Redis set failed for key %s. Mirroring in-memory cache.", key)

        self._memory.set(key, raw, ttl_seconds)
