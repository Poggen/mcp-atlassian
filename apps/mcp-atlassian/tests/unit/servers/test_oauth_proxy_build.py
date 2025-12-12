from __future__ import annotations

from mcp_atlassian.servers.main import _build_auth_provider


def _set_required_oauth_env(monkeypatch, *, redirect_uri: str) -> None:
    monkeypatch.setenv("ATLASSIAN_OAUTH_CLIENT_ID", "client-id")
    monkeypatch.setenv("ATLASSIAN_OAUTH_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("ATLASSIAN_OAUTH_REDIRECT_URI", redirect_uri)


def test_build_auth_provider_falls_back_to_jira_url(monkeypatch):
    monkeypatch.delenv("ATLASSIAN_OAUTH_INSTANCE_URL", raising=False)
    monkeypatch.delenv("CONFLUENCE_URL", raising=False)
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    _set_required_oauth_env(
        monkeypatch, redirect_uri="https://mcp.example.com/mcp-atlassian/callback"
    )

    provider = _build_auth_provider()

    assert provider is not None


def test_build_auth_provider_infers_base_url_from_redirect_uri(monkeypatch):
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("ATLASSIAN_OAUTH_INSTANCE_URL", raising=False)
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    _set_required_oauth_env(
        monkeypatch, redirect_uri="https://mcp.example.com/mcp-atlassian/callback"
    )

    provider = _build_auth_provider()

    assert provider is not None
    assert str(provider.base_url) == "https://mcp.example.com/mcp-atlassian"
    assert provider._redirect_path == "/callback"


def test_build_auth_provider_prefers_public_base_url(monkeypatch):
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://mcp.example.com/mcp-atlassian")
    monkeypatch.delenv("ATLASSIAN_OAUTH_INSTANCE_URL", raising=False)
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    _set_required_oauth_env(
        monkeypatch, redirect_uri="https://mcp.example.com/mcp-atlassian/callback"
    )

    provider = _build_auth_provider()

    assert provider is not None
    assert str(provider.base_url) == "https://mcp.example.com/mcp-atlassian"
    assert provider._redirect_path == "/callback"


def test_build_auth_provider_supports_root_redirect_uri(monkeypatch):
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("ATLASSIAN_OAUTH_INSTANCE_URL", raising=False)
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    _set_required_oauth_env(monkeypatch, redirect_uri="http://localhost:3000/callback")

    provider = _build_auth_provider()

    assert provider is not None
    assert str(provider.base_url).rstrip("/") == "http://localhost:3000"
    assert provider._redirect_path == "/callback"
