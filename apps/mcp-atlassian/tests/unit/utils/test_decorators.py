from unittest.mock import MagicMock

import pytest

from mcp_atlassian.utils.decorators import ensure_write_access


class DummyContext:
    def __init__(self, read_only):
        self.request_context = MagicMock()
        self.request_context.lifespan_context = {
            "app_lifespan_context": MagicMock(read_only=read_only)
        }


def test_ensure_write_access_blocks_in_read_only():
    ctx = DummyContext(read_only=True)
    with pytest.raises(ValueError) as exc:
        ensure_write_access(ctx)
    assert "read-only mode" in str(exc.value)


def test_ensure_write_access_allows_in_writable():
    ctx = DummyContext(read_only=False)
    ensure_write_access(ctx)
