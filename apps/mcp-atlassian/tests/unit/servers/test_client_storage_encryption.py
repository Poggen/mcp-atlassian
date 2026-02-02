import logging

import pytest
from cryptography.fernet import Fernet
from key_value.aio.stores.memory import MemoryStore
from key_value.aio.wrappers.encryption import FernetEncryptionWrapper

from mcp_atlassian.servers.main import _build_client_storage


def test_build_client_storage_wraps_when_key_present(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "memory")
    monkeypatch.setenv("STORAGE_ENCRYPTION_KEY", Fernet.generate_key().decode())

    store = _build_client_storage()

    assert isinstance(store, FernetEncryptionWrapper)


def test_build_client_storage_warns_when_key_missing(monkeypatch, caplog):
    monkeypatch.setenv("STORAGE_BACKEND", "memory")
    monkeypatch.delenv("STORAGE_ENCRYPTION_KEY", raising=False)

    with caplog.at_level(logging.WARNING):
        store = _build_client_storage()

    assert isinstance(store, MemoryStore)
    assert "STORAGE_ENCRYPTION_KEY not set" in caplog.text


def test_build_client_storage_raises_on_invalid_key(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "memory")
    monkeypatch.setenv("STORAGE_ENCRYPTION_KEY", "invalid-key")

    with pytest.raises(ValueError, match="Invalid STORAGE_ENCRYPTION_KEY"):
        _build_client_storage()
