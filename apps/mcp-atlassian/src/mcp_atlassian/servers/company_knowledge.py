"""Company Knowledge-compatible `search` and `fetch` MCP tools.

ChatGPT "Company Knowledge" (and some connector flows) look for MCP tools named
exactly `search` and `fetch`. This repository historically exposes tools with
the naming scheme `{service}_{action}` (e.g. `jira_get_issue`) because the Jira
and Confluence servers are mounted under prefixes.

To support Company Knowledge without breaking existing tool names, we register
top-level `search` and `fetch` tools on the main server that wrap the existing
Jira/Confluence capabilities.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from pydantic import Field

from mcp_atlassian.servers.dependencies import get_confluence_fetcher, get_jira_fetcher

logger = logging.getLogger(__name__)

_JIRA_ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]+-\\d+$")
_CONFLUENCE_PAGE_ID_RE = re.compile(r"^\\d+$")


def _looks_like_jql(query: str) -> bool:
    q = query.strip()
    if not q:
        return False

    # Heuristic: treat queries containing typical JQL operators/clauses as JQL.
    jql_markers = ["=", "~", ">", "<", " AND ", " OR ", " ORDER BY ", "currentUser()"]
    q_upper = q.upper()
    return any(marker in q_upper for marker in jql_markers)


def _escape_jql_string(value: str) -> str:
    # JQL uses double-quoted strings; escape embedded quotes.
    return value.replace('"', '\\"')


def _jira_browse_url(base_url: str, issue_key: str) -> str:
    return f"{base_url.rstrip('/')}/browse/{issue_key}"


def _confluence_page_url(
    base_url: str, is_cloud: bool, page_id: str, space_key: str
) -> str:
    base = base_url.rstrip("/")
    if is_cloud:
        return f"{base}/spaces/{space_key}/pages/{page_id}"
    return f"{base}/pages/viewpage.action?pageId={page_id}"


def _format_jira_issue_text(issue: Any, *, browse_url: str) -> str:
    # Keep formatting simple and robust: rely on attribute access if present.
    key = getattr(issue, "key", "") or ""
    summary = getattr(issue, "summary", "") or ""
    status_obj = getattr(issue, "status", None)
    status_name = getattr(status_obj, "name", None) if status_obj else None
    description = getattr(issue, "description", "") or ""

    lines = [f"{key}: {summary}".strip(), f"URL: {browse_url}"]
    if status_name:
        lines.append(f"Status: {status_name}")

    if description:
        lines.extend(["", "Description:", description])

    return "\n".join(lines).strip()


def register_company_knowledge_tools(mcp: FastMCP[Any]) -> None:
    """Register top-level `search` and `fetch` tools on the provided server."""

    @mcp.tool(tags={"company-knowledge", "read"})
    async def search(
        query: Annotated[str, Field(description="Search query string.")],
        *,
        ctx: Context | None = None,
    ) -> str:
        """Search across Jira issues and Confluence pages.

        Returns a JSON-encoded object with a single `results` key, where each
        result contains: `id`, `title`, and `url`.
        """
        if not query or not query.strip():
            return json.dumps({"results": []}, ensure_ascii=False)

        if ctx is None:
            raise ValueError("Missing FastMCP context.")

        results: list[dict[str, str]] = []
        per_source_limit = 5

        # Confluence search (CQL or simple term).
        try:
            confluence = await get_confluence_fetcher(ctx)
            pages = confluence.search(query, limit=per_source_limit)
            for page in pages:
                page_id = getattr(page, "id", None)
                title = getattr(page, "title", None)
                if not page_id or not title:
                    continue

                url = getattr(page, "url", None)
                if not url:
                    space = getattr(page, "space", None)
                    space_key = getattr(space, "key", None) if space else None
                    if space_key:
                        url = _confluence_page_url(
                            confluence.config.url,
                            getattr(confluence.config, "is_cloud", False),
                            str(page_id),
                            str(space_key),
                        )
                if not url:
                    continue

                results.append(
                    {
                        "id": f"confluence:{page_id}",
                        "title": str(title),
                        "url": str(url),
                    }
                )
        except Exception:
            logger.debug("Company Knowledge Confluence search failed", exc_info=True)

        # Jira search (JQL or basic text search via JQL).
        try:
            jira = await get_jira_fetcher(ctx)
            if _looks_like_jql(query):
                jql = query
            else:
                escaped = _escape_jql_string(query.strip())
                jql = f'text ~ "{escaped}" ORDER BY updated DESC'

            search_result = jira.search_issues(
                jql=jql, fields=["summary"], limit=per_source_limit
            )
            for issue in getattr(search_result, "issues", []):
                issue_key = getattr(issue, "key", None)
                summary = getattr(issue, "summary", None)
                if not issue_key or not summary:
                    continue

                browse_url = _jira_browse_url(jira.config.url, str(issue_key))
                results.append(
                    {
                        "id": f"jira:{issue_key}",
                        "title": f"{issue_key}: {summary}",
                        "url": browse_url,
                    }
                )
        except Exception:
            logger.debug("Company Knowledge Jira search failed", exc_info=True)

        return json.dumps({"results": results}, ensure_ascii=False)

    @mcp.tool(tags={"company-knowledge", "read"})
    async def fetch(
        id: Annotated[str, Field(description="ID from `search` results.")],
        *,
        ctx: Context | None = None,
    ) -> str:
        """Fetch a single Jira issue or Confluence page by ID.

        Returns a JSON-encoded document with `id`, `title`, `text`, `url`, and
        optional `metadata`.
        """
        if not id or not id.strip():
            raise ValueError("Document id is required.")
        if ctx is None:
            raise ValueError("Missing FastMCP context.")

        raw_id = id.strip()

        source: str | None = None
        identifier: str | None = None
        if ":" in raw_id:
            candidate_source, candidate_identifier = raw_id.split(":", 1)
            if candidate_source in {"jira", "confluence"}:
                source = candidate_source
                identifier = candidate_identifier.strip()

        if source is None:
            if _JIRA_ISSUE_KEY_RE.match(raw_id):
                source = "jira"
                identifier = raw_id
            elif _CONFLUENCE_PAGE_ID_RE.match(raw_id):
                source = "confluence"
                identifier = raw_id

        if source is None or not identifier:
            raise ValueError(
                "Unrecognized id format. Expected 'jira:<ISSUE_KEY>' or 'confluence:<PAGE_ID>'."
            )

        if source == "jira":
            jira = await get_jira_fetcher(ctx)
            issue = jira.get_issue(
                issue_key=identifier,
                fields=["summary", "description", "status", "comment"],
                comment_limit=20,
                update_history=False,
            )
            browse_url = _jira_browse_url(jira.config.url, issue.key)
            title = f"{issue.key}: {issue.summary}"
            text = _format_jira_issue_text(issue, browse_url=browse_url)
            result: dict[str, Any] = {
                "id": f"jira:{issue.key}",
                "title": title,
                "text": text,
                "url": browse_url,
                "metadata": {"source": "jira", "issue_key": issue.key},
            }
            return json.dumps(result, ensure_ascii=False)

        confluence = await get_confluence_fetcher(ctx)
        page = confluence.get_page_content(identifier, convert_to_markdown=True)
        page_id = getattr(page, "id", identifier)
        title = getattr(page, "title", f"Confluence Page {page_id}")
        url = getattr(page, "url", None)
        if not url:
            space = getattr(page, "space", None)
            space_key = getattr(space, "key", None) if space else None
            if space_key:
                url = _confluence_page_url(
                    confluence.config.url,
                    getattr(confluence.config, "is_cloud", False),
                    str(page_id),
                    str(space_key),
                )
        if not url:
            url = confluence.config.url

        text = getattr(page, "content", "") or ""
        result = {
            "id": f"confluence:{page_id}",
            "title": str(title),
            "text": str(text),
            "url": str(url),
            "metadata": {"source": "confluence", "page_id": str(page_id)},
        }
        return json.dumps(result, ensure_ascii=False)
