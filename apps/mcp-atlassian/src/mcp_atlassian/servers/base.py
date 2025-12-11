from __future__ import annotations

from fastmcp import FastMCP


class AtlassianFastMCP(FastMCP):
    """FastMCP subclass that always excludes the injected ctx arg from tool inputs."""

    def tool(self, *args, **kwargs):  # type: ignore[override]
        exclude = set(kwargs.get("exclude_args") or [])
        exclude.add("ctx")
        kwargs["exclude_args"] = list(exclude)
        return super().tool(*args, **kwargs)

    def mount(self, path: str, app: "FastMCP"):
        """Ensure mounted apps also exclude ctx by wrapping their tools."""
        for name, tool in app.tools.items():
            tool.exclude_args = list(set(tool.exclude_args or []) | {"ctx"})
        return super().mount(path, app)


__all__ = ["AtlassianFastMCP"]
