from __future__ import annotations

import pytest
from mcp.shared.auth import OAuthClientInformationFull

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


def test_build_auth_provider_allows_chatgpt_oauth_redirect(monkeypatch):
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("ATLASSIAN_OAUTH_INSTANCE_URL", raising=False)
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    _set_required_oauth_env(
        monkeypatch, redirect_uri="https://mcp.example.com/mcp-atlassian/callback"
    )

    provider = _build_auth_provider()

    assert provider is not None
    assert (
        "https://chatgpt.com/connector_platform_oauth_redirect"
        in provider._allowed_client_redirect_uris
    )


def test_build_auth_provider_uses_env_redirect_uris(monkeypatch):
    monkeypatch.setenv(
        "ATLASSIAN_OAUTH_ALLOWED_CLIENT_REDIRECT_URIS", "https://example.com/callback"
    )
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("ATLASSIAN_OAUTH_INSTANCE_URL", raising=False)
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    _set_required_oauth_env(
        monkeypatch, redirect_uri="https://mcp.example.com/mcp-atlassian/callback"
    )

    provider = _build_auth_provider()

    assert provider is not None
    assert provider._allowed_client_redirect_uris == ["https://example.com/callback"]


def test_build_auth_provider_can_disable_consent(monkeypatch):
    monkeypatch.setenv("ATLASSIAN_OAUTH_REQUIRE_CONSENT", "false")
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("ATLASSIAN_OAUTH_INSTANCE_URL", raising=False)
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    _set_required_oauth_env(
        monkeypatch, redirect_uri="https://mcp.example.com/mcp-atlassian/callback"
    )

    provider = _build_auth_provider()

    assert provider is not None
    assert provider._require_authorization_consent is False


@pytest.mark.anyio
async def test_register_client_hardens_grant_types_and_scopes(monkeypatch):
    monkeypatch.setenv("ATLASSIAN_OAUTH_SCOPE", "read:jira-work")
    monkeypatch.setenv("ATLASSIAN_OAUTH_ALLOWED_GRANT_TYPES", "authorization_code")
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    monkeypatch.delenv("ATLASSIAN_OAUTH_INSTANCE_URL", raising=False)
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    _set_required_oauth_env(
        monkeypatch, redirect_uri="https://mcp.example.com/mcp-atlassian/callback"
    )

    provider = _build_auth_provider()

    assert provider is not None
    client = OAuthClientInformationFull(
        client_id="client-123",
        client_secret="secret",
        redirect_uris=["http://localhost:1234/callback"],
        grant_types=[
            "refresh_token",
            "authorization_code",
            "urn:ietf:params:oauth:grant-type:jwt-bearer",
        ],
        scope="read:jira-work write:jira-work",
    )

    await provider.register_client(client)
    stored = await provider._client_store.get(key="client-123")

    assert stored is not None
    assert stored.grant_types == ["authorization_code"]
    assert stored.scope == "read:jira-work"
