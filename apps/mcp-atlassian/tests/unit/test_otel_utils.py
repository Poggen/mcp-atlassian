from types import SimpleNamespace
from unittest.mock import MagicMock

from mcp_atlassian.utils.otel import (
    _get_sanitized_url,
    _parse_resource_attributes,
    _requests_request_hook,
)


def test_parse_resource_attributes_empty():
    assert _parse_resource_attributes(None) == {}
    assert _parse_resource_attributes("") == {}
    assert _parse_resource_attributes("   ") == {}


def test_parse_resource_attributes_parses_key_value_pairs():
    assert _parse_resource_attributes("a=b,c=d") == {"a": "b", "c": "d"}
    assert _parse_resource_attributes("a=b, invalid, c= d ") == {"a": "b", "c": "d"}


def test_get_sanitized_url_removes_query_and_fragment_and_extracts_host_port():
    sanitized, host, port = _get_sanitized_url(
        "https://example.com/some/path?token=secret#frag"
    )
    assert host == "example.com"
    assert port == 443
    assert sanitized == "https://example.com:443/some/path"
    assert "token=" not in sanitized
    assert "#" not in sanitized


def test_get_sanitized_url_defaults_path_and_port():
    sanitized, host, port = _get_sanitized_url("http://example.com")
    assert host == "example.com"
    assert port == 80
    assert sanitized == "http://example.com:80/"


def test_get_sanitized_url_keeps_explicit_port():
    sanitized, host, port = _get_sanitized_url("https://example.com:8443/foo")
    assert host == "example.com"
    assert port == 8443
    assert sanitized == "https://example.com:8443/foo"


def test_requests_request_hook_sets_sanitized_url_attributes():
    span = MagicMock()
    request = SimpleNamespace(url="https://example.com/path?token=secret")

    _requests_request_hook(span, request)

    set_calls = {(args[0], args[1]) for args, _ in span.set_attribute.call_args_list}

    assert ("http.url", "https://example.com:443/path") in set_calls
    assert ("url.full", "https://example.com:443/path") in set_calls
    assert ("net.peer.name", "example.com") in set_calls
    assert ("net.peer.port", 443) in set_calls
