"""Token verifier for Atlassian Data Center opaque OAuth tokens.

FastMCP's OAuthProxy expects a TokenVerifier that can validate access tokens
presented by MCP clients. Atlassian DC issues opaque tokens without a JWKS
endpoint, so we accept any non-empty token and attach the required scopes.
This is intended for development/local use; replace with real introspection
when available.
"""

from __future__ import annotations

import time

from fastmcp.server.auth.auth import TokenVerifier
from fastmcp.server.auth.oauth_proxy import AccessToken


class AtlassianOpaqueTokenVerifier(TokenVerifier):
    """Accepts opaque Atlassian tokens and wraps them in AccessToken.

    For DC OAuth, tokens are opaque and there is no public JWKS. We treat any
    non-empty bearer token as valid and attach the required scopes passed at
    construction. Expiry is not asserted here; upstream expiry will still apply
    when Atlassian rejects expired tokens during API calls.
    """

    async def verify_token(self, token: str) -> AccessToken | None:  # noqa: D401
        if not token:
            return None

        scopes = self.required_scopes or []
        # No reliable expiry info; mark as long-lived and let upstream enforce.
        return AccessToken(
            token=token,
            client_id="atlassian",
            scopes=scopes,
            expires_at=int(time.time()) + 86400 * 30,
        )
