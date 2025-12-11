from __future__ import annotations

from fastmcp import FastMCP


class AtlassianFastMCP(FastMCP):
    """FastMCP subclass that always excludes the injected ctx arg from tool inputs."""

    def tool(self, *args, **kwargs):  # type: ignore[override]
        exclude = set(kwargs.get("exclude_args") or [])
        exclude.add("ctx")
        kwargs["exclude_args"] = list(exclude)
        return super().tool(*args, **kwargs)


__all__ = ["AtlassianFastMCP"]
