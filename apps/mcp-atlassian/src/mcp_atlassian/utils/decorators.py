import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

import requests
from requests.exceptions import HTTPError

from mcp_atlassian.exceptions import MCPAtlassianAuthenticationError

logger = logging.getLogger(__name__)


F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def ensure_write_access(ctx: Any) -> None:
    """
    Shared guard for write-capable tools. Raises if the service is running in read-only mode.

    Args:
        ctx: FastMCP context injected into tool functions.
    """
    request_ctx = getattr(ctx, "request_context", None)
    lifespan_ctx_dict = getattr(request_ctx, "lifespan_context", None)
    if not isinstance(lifespan_ctx_dict, dict):
        return

    app_lifespan_ctx = (
        lifespan_ctx_dict.get("app_lifespan_context")
        if isinstance(lifespan_ctx_dict, dict)
        else None
    )  # type: ignore

    if app_lifespan_ctx is not None and app_lifespan_ctx.read_only:
        logger.warning("Attempted to call write tool in read-only mode.")
        raise ValueError("Cannot perform write operations in read-only mode.")


def check_write_access(func: F) -> F:  # pragma: no cover - kept for backward compat
    """
    Backward-compatible decorator for legacy code.

    Prefer calling ensure_write_access(ctx) at the top of write tools.
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        ctx = kwargs.get("ctx")
        if ctx is None and args:
            ctx = args[0]
        ensure_write_access(ctx)
        return await func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


def handle_atlassian_api_errors(service_name: str = "Atlassian API") -> Callable:
    """
    Decorator to handle common Atlassian API exceptions (Jira, Confluence, etc.).

    Args:
        service_name: Name of the service for error logging (e.g., "Jira API").
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                return func(self, *args, **kwargs)
            except HTTPError as http_err:
                if http_err.response is not None and http_err.response.status_code in [
                    401,
                    403,
                ]:
                    error_msg = (
                        f"Authentication failed for {service_name} "
                        f"({http_err.response.status_code}). "
                        "Token may be expired or invalid. Please verify credentials."
                    )
                    logger.error(error_msg)
                    raise MCPAtlassianAuthenticationError(error_msg) from http_err
                else:
                    operation_name = getattr(func, "__name__", "API operation")
                    logger.error(
                        f"HTTP error during {operation_name}: {http_err}",
                        exc_info=False,
                    )
                    raise http_err
            except KeyError as e:
                operation_name = getattr(func, "__name__", "API operation")
                logger.error(f"Missing key in {operation_name} results: {str(e)}")
                return []
            except requests.RequestException as e:
                operation_name = getattr(func, "__name__", "API operation")
                logger.error(f"Network error during {operation_name}: {str(e)}")
                return []
            except (ValueError, TypeError) as e:
                operation_name = getattr(func, "__name__", "API operation")
                logger.error(f"Error processing {operation_name} results: {str(e)}")
                return []
            except Exception as e:  # noqa: BLE001 - Intentional fallback with logging
                operation_name = getattr(func, "__name__", "API operation")
                logger.error(f"Unexpected error during {operation_name}: {str(e)}")
                logger.debug(
                    f"Full exception details for {operation_name}:", exc_info=True
                )
                return []

        return wrapper

    return decorator
