import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport
from mcp.types import TextContent

from mcp_atlassian.servers.main import main_mcp


@pytest.mark.asyncio
async def test_company_knowledge_tools_are_registered() -> None:
    tools = await main_mcp.get_tools()
    assert "search" in tools
    assert "fetch" in tools


@pytest.mark.asyncio
async def test_company_knowledge_search_returns_results_schema() -> None:
    # Confluence stub
    page = MagicMock()
    page.id = "123"
    page.title = "Test Page"
    page.url = "https://confluence.example/pages/viewpage.action?pageId=123"

    confluence_fetcher = MagicMock()
    confluence_fetcher.search.return_value = [page]
    confluence_fetcher.config.url = "https://confluence.example"
    confluence_fetcher.config.is_cloud = False

    # Jira stub
    issue = MagicMock()
    issue.key = "PROJ-1"
    issue.summary = "Test Issue"

    search_result = MagicMock()
    search_result.issues = [issue]

    jira_fetcher = MagicMock()
    jira_fetcher.search_issues.return_value = search_result
    jira_fetcher.config.url = "https://jira.example"

    with (
        patch(
            "mcp_atlassian.servers.company_knowledge.get_confluence_fetcher",
            new=AsyncMock(return_value=confluence_fetcher),
        ),
        patch(
            "mcp_atlassian.servers.company_knowledge.get_jira_fetcher",
            new=AsyncMock(return_value=jira_fetcher),
        ),
    ):
        transport = FastMCPTransport(main_mcp)
        client = Client(transport=transport)
        async with client as connected_client:
            result = await connected_client.call_tool("search", {"query": "test"})
            content = result.content if hasattr(result, "content") else result

    assert content and isinstance(content[0], TextContent)
    payload = json.loads(content[0].text)

    assert isinstance(payload, dict)
    assert "results" in payload
    assert isinstance(payload["results"], list)

    results = payload["results"]
    assert {"id", "title", "url"} <= set(results[0].keys())


@pytest.mark.asyncio
async def test_company_knowledge_search_falls_back_to_text_search() -> None:
    page = MagicMock()
    page.id = "123"
    page.title = "Test Page"
    page.url = "https://confluence.example/pages/viewpage.action?pageId=123"

    def search_side_effect(query: str, limit: int, spaces_filter: str | None = None):
        if query.startswith("siteSearch"):
            raise RuntimeError("siteSearch unsupported")
        return [page]

    confluence_fetcher = MagicMock()
    confluence_fetcher.search.side_effect = search_side_effect
    confluence_fetcher.config.url = "https://confluence.example"
    confluence_fetcher.config.is_cloud = False

    search_result = MagicMock()
    search_result.issues = []

    jira_fetcher = MagicMock()
    jira_fetcher.search_issues.return_value = search_result
    jira_fetcher.config.url = "https://jira.example"

    with (
        patch(
            "mcp_atlassian.servers.company_knowledge.get_confluence_fetcher",
            new=AsyncMock(return_value=confluence_fetcher),
        ),
        patch(
            "mcp_atlassian.servers.company_knowledge.get_jira_fetcher",
            new=AsyncMock(return_value=jira_fetcher),
        ),
    ):
        transport = FastMCPTransport(main_mcp)
        client = Client(transport=transport)
        async with client as connected_client:
            result = await connected_client.call_tool("search", {"query": "test"})
            content = result.content if hasattr(result, "content") else result

    assert content and isinstance(content[0], TextContent)
    payload = json.loads(content[0].text)
    assert payload["results"]
    assert confluence_fetcher.search.call_count == 2
    first_query = confluence_fetcher.search.call_args_list[0].args[0]
    second_query = confluence_fetcher.search.call_args_list[1].args[0]
    assert first_query.startswith("siteSearch")
    assert second_query.startswith("text")


@pytest.mark.asyncio
async def test_company_knowledge_fetch_returns_document_schema() -> None:
    issue = MagicMock()
    issue.key = "PROJ-1"
    issue.summary = "Test Issue"
    issue.description = "Body"
    issue.status = MagicMock()
    issue.status.name = "In Progress"

    jira_fetcher = MagicMock()
    jira_fetcher.get_issue.return_value = issue
    jira_fetcher.config.url = "https://jira.example"

    with patch(
        "mcp_atlassian.servers.company_knowledge.get_jira_fetcher",
        new=AsyncMock(return_value=jira_fetcher),
    ):
        transport = FastMCPTransport(main_mcp)
        client = Client(transport=transport)
        async with client as connected_client:
            result = await connected_client.call_tool("fetch", {"id": "jira:PROJ-1"})
            content = result.content if hasattr(result, "content") else result

    assert content and isinstance(content[0], TextContent)
    payload = json.loads(content[0].text)

    assert payload["id"] == "jira:PROJ-1"
    assert payload["title"] == "PROJ-1: Test Issue"
    assert payload["url"] == "https://jira.example/browse/PROJ-1"
    assert isinstance(payload["text"], str) and payload["text"]
    assert payload["metadata"]["source"] == "jira"
