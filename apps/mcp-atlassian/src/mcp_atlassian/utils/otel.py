"""OpenTelemetry bootstrap utilities for MCP Atlassian.

Drive can provide OTEL-related environment variables and network policy rules,
but Python applications still need to initialize the OpenTelemetry SDK and
instrument outbound clients (e.g. requests) to actually emit traces.

This module provides a small, safe bootstrap that:
- only enables tracing when OTEL export is configured via env vars
- configures OTLP/HTTP export (Drive uses port 4318)
- instruments the requests library for outbound HTTP spans
- avoids leaking query strings or headers into span attributes
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from mcp_atlassian.utils.env import is_env_truthy

if TYPE_CHECKING:
    from opentelemetry.sdk.trace import TracerProvider

logger = logging.getLogger("mcp-atlassian.utils.otel")

_otel_configured: bool = False
_requests_instrumented: bool = False
_tracer_provider: TracerProvider | None = None


def _parse_resource_attributes(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}

    attributes: dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        attributes[key] = value
    return attributes


def _get_sanitized_url(url: str) -> tuple[str, str | None, int | None]:
    """Return a sanitized URL and extracted host/port.

    Sanitization removes query string and fragment to reduce PII risk.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname
    port: int | None = parsed.port
    scheme = parsed.scheme or "http"
    path = parsed.path or "/"

    if port is None and hostname:
        if scheme == "https":
            port = 443
        elif scheme == "http":
            port = 80

    if not hostname:
        # If parsing fails, return the original string but without crashing.
        return url, None, None

    netloc = f"{hostname}:{port}" if port else hostname
    sanitized = f"{scheme}://{netloc}{path}"
    return sanitized, hostname, port


def _instrument_requests() -> None:
    global _requests_instrumented

    if _requests_instrumented:
        return

    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
    except ImportError:
        logger.info(
            "OpenTelemetry requests instrumentation not installed; outbound HTTP spans disabled."
        )
        return

    # Avoid recording headers or bodies. The requests instrumentor does not
    # capture bodies by default, and we intentionally don't add any header attrs.
    RequestsInstrumentor().instrument(request_hook=_requests_request_hook)
    _requests_instrumented = True


def _requests_request_hook(span: Any, request: Any) -> None:
    # request is typically requests.PreparedRequest, but keep this flexible.
    if span is None:
        return

    url = getattr(request, "url", None)
    if not isinstance(url, str) or not url:
        return

    sanitized_url, hostname, port = _get_sanitized_url(url)

    # Overwrite common attributes with sanitized values.
    span.set_attribute("http.url", sanitized_url)
    span.set_attribute("url.full", sanitized_url)
    span.set_attribute("http.target", urlparse(sanitized_url).path or "/")

    if hostname:
        span.set_attribute("net.peer.name", hostname)
    if port:
        span.set_attribute("net.peer.port", port)


def setup_otel() -> None:
    """Initialize OpenTelemetry tracing if configured via environment variables.

    This function is intentionally idempotent and safe to call multiple times.
    """
    global _otel_configured
    global _tracer_provider

    if _otel_configured:
        return

    if is_env_truthy("OTEL_SDK_DISABLED", "false"):
        logger.debug("OTEL_SDK_DISABLED=true; skipping OpenTelemetry setup.")
        return

    traces_exporter = os.getenv("OTEL_TRACES_EXPORTER", "").strip().lower()
    if not traces_exporter or traces_exporter == "none":
        logger.debug(
            "OTEL_TRACES_EXPORTER not set or 'none'; skipping OpenTelemetry setup."
        )
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )
    except ImportError:
        logger.warning(
            "OpenTelemetry SDK not installed but OTEL_TRACES_EXPORTER=%s; skipping.",
            traces_exporter,
        )
        return

    resource_attributes = _parse_resource_attributes(
        os.getenv("OTEL_RESOURCE_ATTRIBUTES")
    )
    service_name = os.getenv("OTEL_SERVICE_NAME") or "mcp-atlassian"
    resource_attributes.setdefault("service.name", service_name)

    resource = Resource.create(resource_attributes)
    tracer_provider = TracerProvider(resource=resource)

    match traces_exporter:
        case "console":
            exporter = ConsoleSpanExporter()
        case "otlp":
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                    OTLPSpanExporter,
                )
            except ImportError:
                logger.warning(
                    "OTLP HTTP exporter not installed but OTEL_TRACES_EXPORTER=otlp; skipping."
                )
                return
            exporter = OTLPSpanExporter()
        case _:
            logger.warning(
                "Unsupported OTEL_TRACES_EXPORTER=%s; skipping OpenTelemetry setup.",
                traces_exporter,
            )
            return

    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(tracer_provider)

    _tracer_provider = tracer_provider
    _otel_configured = True

    _instrument_requests()
    logger.info("OpenTelemetry tracing enabled (exporter=%s).", traces_exporter)


def shutdown_otel() -> None:
    """Flush and shutdown OpenTelemetry providers (best effort)."""
    global _otel_configured
    global _tracer_provider

    if not _otel_configured or _tracer_provider is None:
        return

    try:
        _tracer_provider.force_flush()
    except Exception:
        # Best effort shutdown; do not block process exit.
        logger.debug("OpenTelemetry force_flush failed.", exc_info=True)

    try:
        _tracer_provider.shutdown()
    except Exception:
        logger.debug("OpenTelemetry shutdown failed.", exc_info=True)
    finally:
        _otel_configured = False
        _tracer_provider = None
