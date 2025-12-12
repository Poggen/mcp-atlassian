"""OpenTelemetry spans for MCP operations.

FastMCP provides a middleware system that runs around MCP operations such as
tool calls. This module emits OpenTelemetry spans for those operations so we
can correlate user-visible MCP calls with outbound HTTP spans (requests).

Span names and attributes are intentionally aligned with the upstream FastMCP
draft OpenTelemetry middleware (jlowin/fastmcp#2001) to ease migration later.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext

from mcp_atlassian.utils.env import is_env_truthy

logger = logging.getLogger("mcp-atlassian.utils.otel_middleware")


def _otel_tracing_enabled() -> bool:
    if is_env_truthy("OTEL_SDK_DISABLED", "false"):
        return False
    exporter = os.getenv("OTEL_TRACES_EXPORTER", "").strip().lower()
    return bool(exporter and exporter != "none")


class OpenTelemetryMiddleware(Middleware):
    """Emit spans around MCP operations (tools/resources/prompts)."""

    def __init__(
        self,
        *,
        tracer_name: str = "fastmcp",
        enabled: bool | None = None,
        include_arguments: bool = False,
        max_argument_length: int = 500,
        tracer: Any | None = None,
    ) -> None:
        self._enabled = _otel_tracing_enabled() if enabled is None else enabled
        self._include_arguments = include_arguments
        self._max_argument_length = max_argument_length
        self._tracer = tracer
        self._tracer_name = tracer_name

        try:
            from opentelemetry import trace

            self._trace_api = trace
        except ImportError:
            self._trace_api = None
            if self._enabled:
                logger.info(
                    "OpenTelemetry is enabled but opentelemetry-api is not installed; disabling spans."
                )
                self._enabled = False

        if self._enabled and self._tracer is None and self._trace_api is not None:
            self._tracer = self._trace_api.get_tracer(self._tracer_name)

    def _truncate(self, value: Any) -> str:
        text = str(value)
        if len(text) > self._max_argument_length:
            return text[: self._max_argument_length] + "..."
        return text

    def _base_attributes(self, context: MiddlewareContext[Any]) -> dict[str, Any]:
        return {
            "mcp.method": context.method or "unknown",
            "mcp.source": context.source,
            "mcp.type": context.type,
        }

    async def on_call_tool(
        self, context: MiddlewareContext[Any], call_next: CallNext
    ) -> Any:
        if not self._enabled or self._tracer is None:
            return await call_next(context)

        tool_name = getattr(context.message, "name", "unknown")
        tool_arguments = getattr(context.message, "arguments", {})

        attributes = self._base_attributes(context)
        attributes["mcp.tool.name"] = tool_name
        if self._include_arguments:
            attributes["mcp.tool.arguments"] = self._truncate(tool_arguments)

        from opentelemetry.trace import Status, StatusCode

        with self._tracer.start_as_current_span(
            f"tool.{tool_name}",
            attributes=attributes,
        ) as span:
            try:
                result = await call_next(context)
                success = True
                span.set_attribute("mcp.tool.success", success)
                span.set_status(Status(StatusCode.OK))
                return result
            except Exception as e:
                success = False
                span.set_attribute("mcp.tool.success", success)
                span.set_attribute("mcp.tool.error", str(e))
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    async def on_read_resource(
        self, context: MiddlewareContext[Any], call_next: CallNext
    ) -> Any:
        if not self._enabled or self._tracer is None:
            return await call_next(context)

        resource_uri = getattr(context.message, "uri", "unknown")

        attributes = self._base_attributes(context)
        attributes["mcp.resource.uri"] = resource_uri

        from opentelemetry.trace import Status, StatusCode

        with self._tracer.start_as_current_span(
            "resource.read",
            attributes=attributes,
        ) as span:
            try:
                result = await call_next(context)
                span.set_status(Status(StatusCode.OK))
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    async def on_get_prompt(
        self, context: MiddlewareContext[Any], call_next: CallNext
    ) -> Any:
        if not self._enabled or self._tracer is None:
            return await call_next(context)

        prompt_name = getattr(context.message, "name", "unknown")
        prompt_arguments = getattr(context.message, "arguments", {})

        attributes = self._base_attributes(context)
        attributes["mcp.prompt.name"] = prompt_name
        if self._include_arguments:
            attributes["mcp.prompt.arguments"] = self._truncate(prompt_arguments)

        from opentelemetry.trace import Status, StatusCode

        with self._tracer.start_as_current_span(
            f"prompt.{prompt_name}",
            attributes=attributes,
        ) as span:
            try:
                result = await call_next(context)
                span.set_status(Status(StatusCode.OK))
                return result
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
