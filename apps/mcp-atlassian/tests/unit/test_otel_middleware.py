from types import SimpleNamespace

import pytest
from fastmcp.server.middleware import MiddlewareContext
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import StatusCode

from mcp_atlassian.utils.otel_middleware import OpenTelemetryMiddleware


@pytest.mark.asyncio
async def test_tool_call_span_created_without_arguments():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("test")

    middleware = OpenTelemetryMiddleware(
        enabled=True,
        tracer=tracer,
        include_arguments=False,
    )

    message = SimpleNamespace(name="my_tool", arguments={"token": "secret"})
    context = MiddlewareContext(
        message=message,
        method="tools/call",
        type="request",
        source="client",
    )

    async def call_next(ctx: MiddlewareContext):
        return {"ok": True}

    result = await middleware.on_call_tool(context, call_next)
    assert result == {"ok": True}

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "tool.my_tool"
    assert span.attributes["mcp.tool.name"] == "my_tool"
    assert "mcp.tool.arguments" not in span.attributes
    assert span.attributes["mcp.tool.success"] is True
    assert span.status.status_code == StatusCode.OK


@pytest.mark.asyncio
async def test_tool_call_span_records_error():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = provider.get_tracer("test")

    middleware = OpenTelemetryMiddleware(enabled=True, tracer=tracer)
    message = SimpleNamespace(name="boom_tool", arguments={})
    context = MiddlewareContext(
        message=message,
        method="tools/call",
        type="request",
        source="client",
    )

    async def call_next(ctx: MiddlewareContext):
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        await middleware.on_call_tool(context, call_next)

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    span = spans[0]
    assert span.name == "tool.boom_tool"
    assert span.attributes["mcp.tool.success"] is False
    assert span.status.status_code == StatusCode.ERROR
