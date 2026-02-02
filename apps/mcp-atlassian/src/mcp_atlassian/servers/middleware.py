"""HTTP middleware utilities for MCP Atlassian."""

from __future__ import annotations

import logging
from typing import Any, Optional

from cachetools import TTLCache
from fastmcp import settings as fastmcp_settings
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_atlassian.utils.logging import mask_sensitive

logger = logging.getLogger("mcp-atlassian.server.middleware")

token_validation_cache: TTLCache[
    int, tuple[bool, str | None, Any | None, Any | None]
] = TTLCache(maxsize=100, ttl=300)


class UserTokenMiddleware(BaseHTTPMiddleware):
    """Middleware to extract Atlassian user tokens/credentials from Authorization headers."""

    def __init__(
        self, app: Any, mcp_server_ref: Optional[Any] = None
    ) -> None:
        super().__init__(app)
        self.mcp_server_ref = mcp_server_ref
        if not self.mcp_server_ref:
            logger.warning(
                "UserTokenMiddleware initialized without mcp_server_ref. "
                "Path matching for MCP endpoint might fail if settings are needed."
            )

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> JSONResponse:
        logger.debug(
            "UserTokenMiddleware.dispatch: ENTERED for request path='%s', method='%s'",
            request.url.path,
            request.method,
        )
        mcp_server_instance = self.mcp_server_ref
        if mcp_server_instance is None:
            logger.debug(
                "UserTokenMiddleware.dispatch: self.mcp_server_ref is None. "
                "Skipping MCP auth logic."
            )
            return await call_next(request)

        mcp_path = (fastmcp_settings.streamable_http_path or "/mcp").rstrip("/")
        request_path = request.url.path.rstrip("/")
        logger.debug(
            "UserTokenMiddleware.dispatch: Comparing request_path='%s' with "
            "mcp_path='%s'. Request method='%s'",
            request_path,
            mcp_path,
            request.method,
        )
        if request_path == mcp_path and request.method == "POST":
            auth_header = request.headers.get("Authorization")
            cloud_id_header = request.headers.get("X-Atlassian-Cloud-Id")

            token_for_log = mask_sensitive(
                auth_header.split(" ", 1)[1].strip()
                if auth_header and " " in auth_header
                else auth_header
            )
            logger.debug(
                "UserTokenMiddleware: Path='%s', AuthHeader='%s', "
                "ParsedToken(masked)='%s', CloudId='%s'",
                request.url.path,
                mask_sensitive(auth_header),
                token_for_log,
                cloud_id_header,
            )

            # Extract and save cloudId if provided
            if cloud_id_header and cloud_id_header.strip():
                request.state.user_atlassian_cloud_id = cloud_id_header.strip()
                logger.debug(
                    "UserTokenMiddleware: Extracted cloudId from header: %s",
                    cloud_id_header.strip(),
                )
            else:
                request.state.user_atlassian_cloud_id = None
                logger.debug(
                    "UserTokenMiddleware: No cloudId header provided, will use global config"
                )

            # Check for mcp-session-id header for debugging
            mcp_session_id = request.headers.get("mcp-session-id")
            if mcp_session_id:
                logger.debug(
                    "UserTokenMiddleware: MCP-Session-ID header found: %s",
                    mcp_session_id,
                )
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()
                if not token:
                    return JSONResponse(
                        {"error": "Unauthorized: Empty Bearer token"},
                        status_code=401,
                    )
                logger.debug(
                    "UserTokenMiddleware.dispatch: Bearer token extracted (masked): ...%s",
                    mask_sensitive(token, 8),
                )
                request.state.user_atlassian_token = token
                request.state.user_atlassian_auth_type = "oauth"
                request.state.user_atlassian_email = None
                logger.debug(
                    "UserTokenMiddleware.dispatch: Set request.state (pre-validation): "
                    "auth_type='%s', token_present=%s",
                    getattr(request.state, "user_atlassian_auth_type", "N/A"),
                    bool(getattr(request.state, "user_atlassian_token", None)),
                )
            elif auth_header and auth_header.startswith("Token "):
                token = auth_header.split(" ", 1)[1].strip()
                if not token:
                    return JSONResponse(
                        {"error": "Unauthorized: Empty Token (PAT)"},
                        status_code=401,
                    )
                logger.debug(
                    "UserTokenMiddleware.dispatch: PAT (Token scheme) extracted (masked): ...%s",
                    mask_sensitive(token, 8),
                )
                request.state.user_atlassian_token = token
                request.state.user_atlassian_auth_type = "pat"
                request.state.user_atlassian_email = (
                    None  # PATs don't carry email in the token itself
                )
                logger.debug(
                    "UserTokenMiddleware.dispatch: Set request.state for PAT auth."
                )
            elif auth_header:
                logger.warning(
                    "Unsupported Authorization type for %s: %s",
                    request.url.path,
                    auth_header.split(" ", 1)[0]
                    if " " in auth_header
                    else "UnknownType",
                )
                return JSONResponse(
                    {
                        "error": "Unauthorized: Only 'Bearer <OAuthToken>' or 'Token <PAT>' types are supported."
                    },
                    status_code=401,
                )
            else:
                logger.debug(
                    "No Authorization header provided for %s. Will proceed with "
                    "global/fallback server configuration if applicable.",
                    request.url.path,
                )
        response = await call_next(request)
        logger.debug(
            "UserTokenMiddleware.dispatch: EXITED for request path='%s'",
            request.url.path,
        )
        return response


__all__ = ["UserTokenMiddleware", "token_validation_cache"]
