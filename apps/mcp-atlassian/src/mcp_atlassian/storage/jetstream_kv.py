"""JetStream-backed AsyncKeyValue implementation for FastMCP client storage.

We store MCP OAuth client registrations in NATS JetStream KeyValue buckets.
Each collection maps to a bucket (prefixed). Values are JSON-encoded.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import timedelta
from typing import Any, Mapping, Sequence, SupportsFloat

from key_value.aio.protocols.key_value import AsyncKeyValue

logger = logging.getLogger(__name__)

try:  # Optional dependency
    import nats  # type: ignore
    from nats.js.errors import BucketNotFoundError, KeyNotFoundError  # type: ignore
except Exception:  # pragma: no cover - import guard only
    nats = None  # type: ignore

    class BucketNotFoundError(Exception):
        ...

    class KeyNotFoundError(Exception):
        ...


class JetStreamKVStore(AsyncKeyValue):
    """AsyncKeyValue adapter backed by JetStream KeyValue buckets."""

    def __init__(
        self,
        *,
        nats_url: str,
        creds_path: str | None = None,
        bucket_prefix: str = "mcp-client-",
        default_collection: str = "registrations",
        js=None,
        connect_timeout: float = 5.0,
    ) -> None:
        self.nats_url = nats_url
        self.creds_path = creds_path
        self.bucket_prefix = bucket_prefix
        self.default_collection = default_collection
        self._js = js
        self._nc = None
        self._bucket_cache: dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self.connect_timeout = connect_timeout
        self._inmem_user_jwt: str | None = None
        self._inmem_sig_cb = None

    def _build_auth_kwargs(self, path: str) -> dict[str, Any]:
        """Return kwargs for nats.connect based on creds content.

        Drive may mount creds base64-encoded; we prefer in-memory auth to avoid writes.
        """
        try:
            with open(path, "rb") as f:
                raw = f.read()
        except Exception:
            logger.warning("Unable to read NATS creds at %s", path, exc_info=True)
            return {}

        # Heuristic: base64-encoded creds start with LS0t...
        if raw.strip().startswith(b"LS0tLS1CRUdJTiBOQVRTIFVTRVIgSldU"):
            import base64
            decoded = base64.b64decode(raw)
            text = decoded.decode()
        else:
            try:
                text = raw.decode()
            except Exception:
                return {"user_credentials": path}

        # Parse JWT and seed
        user_jwt = None
        user_seed = None
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("eyJ") and "." in line:
                user_jwt = line
            if line.startswith("SU") and len(line) > 10:
                user_seed = line
        if not user_jwt or not user_seed:
            # fallback to file-based auth
            return {"user_credentials": path}

        try:
            import nkeys  # type: ignore
        except Exception:
            logger.error("nkeys module missing; cannot perform in-memory NATS auth")
            return {"user_credentials": path}

        try:
            kp = nkeys.from_seed(user_seed.encode())
        except Exception:
            logger.warning("Failed to parse NATS seed from creds; falling back to file")
            return {"user_credentials": path}

        def sig_cb(nonce: str) -> bytes:
            # nats.py expects signature bytes decodable to utf-8; base64-encode to be safe.
            import base64
            return base64.b64encode(kp.sign(nonce.encode()))

        def jwt_cb() -> bytes:
            return user_jwt.encode()

        self._inmem_user_jwt = user_jwt
        self._inmem_sig_cb = sig_cb
        return {"user_jwt_cb": jwt_cb, "signature_cb": sig_cb}

    async def _ensure_connection(self):
        if self._js:
            return
        if nats is None:
            raise RuntimeError(
                "nats-py is required for JetStream storage. Install mcp-atlassian[jetstream]."
            )
        connect_kwargs: dict[str, Any] = {"servers": self.nats_url}
        # Always prefer the provided creds_path (expected to be user.creds with JS perms).
        if self.creds_path and os.path.exists(self.creds_path):
            connect_kwargs.update(self._build_auth_kwargs(self.creds_path))
        try:
            self._nc = await nats.connect(**connect_kwargs, connect_timeout=self.connect_timeout)
            self._js = self._nc.jetstream()
        except Exception as exc:  # pragma: no cover - connection failures
            raise RuntimeError(f"Failed to connect to NATS at {self.nats_url}: {exc}") from exc

    def _bucket_name(self, collection: str | None) -> str:
        name = collection or self.default_collection
        safe = re.sub(r"[^A-Za-z0-9_-]", "-", name)
        return f"{self.bucket_prefix}{safe}" if self.bucket_prefix else safe

    async def _get_bucket(self, collection: str | None):
        await self._ensure_connection()
        bucket_name = self._bucket_name(collection)
        async with self._lock:
            if bucket_name in self._bucket_cache:
                return self._bucket_cache[bucket_name]
            try:
                bucket = await self._js.key_value(bucket_name)
            except BucketNotFoundError:
                bucket = await self._js.create_key_value(bucket=bucket_name)
            self._bucket_cache[bucket_name] = bucket
            return bucket

    @staticmethod
    def _encode(value: Mapping[str, Any]) -> bytes:
        return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()

    @staticmethod
    def _decode(raw: bytes) -> dict[str, Any]:
        return json.loads(raw.decode())

    async def get(self, key: str, *, collection: str | None = None, raise_on_missing=False):
        bucket = await self._get_bucket(collection)
        try:
            entry = await bucket.get(key)
        except KeyNotFoundError:
            if raise_on_missing:
                raise
            return None
        value = self._decode(entry.value)
        return value

    async def get_many(
        self,
        keys: Sequence[str],
        *,
        collection: str | None = None,
        raise_on_missing: bool = False,
    ) -> list[dict[str, Any] | None]:
        results: list[dict[str, Any] | None] = []
        for key in keys:
            try:
                results.append(await self.get(key, collection=collection, raise_on_missing=raise_on_missing))
            except KeyNotFoundError:
                if raise_on_missing:
                    raise
                results.append(None)
        return results

    async def put(
        self,
        key: str,
        value: Mapping[str, Any],
        *,
        collection: str | None = None,
        ttl: SupportsFloat | None = None,
    ) -> None:
        bucket = await self._get_bucket(collection)
        data = self._encode(value)
        # nats-py KV API does not support per-entry ttl; bucket-level ttl can
        # be set at creation time. Ignore per-call ttl to avoid API errors.
        if ttl is not None:
            logger.debug("Ignoring per-entry ttl=%s for JetStream KV put", ttl)
        await bucket.put(key, data)

    async def put_many(
        self,
        keys: Sequence[str],
        values: Sequence[Mapping[str, Any]],
        *,
        collection: str | None = None,
        ttl: SupportsFloat | None = None,
    ) -> None:
        for key, value in zip(keys, values):
            await self.put(key, value, collection=collection, ttl=ttl)

    async def delete(self, key: str, *, collection: str | None = None) -> None:
        bucket = await self._get_bucket(collection)
        try:
            await bucket.delete(key)
            return True
        except KeyNotFoundError:
            return False

    async def delete_many(self, keys: Sequence[str], *, collection: str | None = None) -> int:
        # Align with FastMCP client storage expectations: return number of
        # processed keys (not only the ones that previously existed). This
        # matches earlier in-memory behaviour and keeps tests consistent.
        for key in keys:
            await self.delete(key, collection=collection)
        return len(keys)

    async def ttl(
        self,
        key: str,
        *,
        collection: str | None = None,
        raise_on_missing: bool = False,
    ) -> tuple[dict[str, Any] | None, float | None]:
        value = await self.get(key, collection=collection, raise_on_missing=raise_on_missing)
        return value, None

    async def ttl_many(
        self,
        keys: Sequence[str],
        *,
        collection: str | None = None,
        raise_on_missing: bool = False,
    ) -> list[tuple[dict[str, Any] | None, float | None]]:
        results: list[tuple[dict[str, Any] | None, float | None]] = []
        for key in keys:
            val, ttl = await self.ttl(key, collection=collection, raise_on_missing=raise_on_missing)
            results.append((val, ttl))
        return results

    async def close(self) -> None:
        if self._nc:
            await self._nc.close()
            self._nc = None
            self._js = None
            self._bucket_cache.clear()
        self._inmem_user_jwt = None
        self._inmem_sig_cb = None


__all__ = ["JetStreamKVStore", "BucketNotFoundError", "KeyNotFoundError"]
