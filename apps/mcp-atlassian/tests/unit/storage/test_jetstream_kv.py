import pytest

from mcp_atlassian.storage.jetstream_kv import (
    BucketNotFoundError,
    JetStreamKVStore,
    KeyNotFoundError,
)


class FakeEntry:
    def __init__(self, value: bytes) -> None:
        self.value = value


class FakeBucket:
    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    async def get(self, key: str):
        if key not in self._data:
            raise KeyNotFoundError()
        return FakeEntry(self._data[key])

    async def put(self, key: str, value: bytes, **kwargs):
        self._data[key] = value

    async def delete(self, key: str):
        if key not in self._data:
            raise KeyNotFoundError()
        self._data.pop(key, None)


class FakeJS:
    def __init__(self) -> None:
        self._buckets: dict[str, FakeBucket] = {}

    async def key_value(self, name: str):
        if name not in self._buckets:
            raise BucketNotFoundError()
        return self._buckets[name]

    async def create_key_value(self, bucket: str):
        fb = FakeBucket()
        self._buckets[bucket] = fb
        return fb


@pytest.mark.anyio
async def test_put_get_delete_roundtrip():
    store = JetStreamKVStore(
        nats_url="nats://example",
        bucket_prefix="test-",
        default_collection="kv",
        js=FakeJS(),
    )

    await store.put("one", {"a": 1})
    value = await store.get("one")
    assert value == {"a": 1}

    await store.delete("one")
    assert await store.get("one") is None


@pytest.mark.anyio
async def test_get_many_and_ttl():
    store = JetStreamKVStore(
        nats_url="nats://example",
        bucket_prefix="",
        default_collection="kv",
        js=FakeJS(),
    )
    await store.put("first", {"x": "y"})
    results = await store.get_many(["first", "missing"])
    assert results[0] == {"x": "y"}
    assert results[1] is None

    value, ttl = await store.ttl("first")
    assert value == {"x": "y"}
    assert ttl is None


@pytest.mark.anyio
async def test_delete_many_counts_all():
    store = JetStreamKVStore(
        nats_url="nats://example",
        bucket_prefix="",
        default_collection="kv",
        js=FakeJS(),
    )
    await store.put("a", {"v": 1})
    await store.put("b", {"v": 2})

    deleted = await store.delete_many(["a", "b", "c"])
    assert deleted == 3
    assert await store.get("a") is None
    assert await store.get("b") is None
