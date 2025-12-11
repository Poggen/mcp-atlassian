import inspect

import pytest

from mcp_atlassian.servers.confluence import confluence_mcp
from mcp_atlassian.servers.jira import jira_mcp


async def _collect_tools():
    jira_tools = await jira_mcp.get_tools()
    confluence_tools = await confluence_mcp.get_tools()
    return list(jira_tools.values()) + list(confluence_tools.values())


@pytest.mark.asyncio
async def test_ctx_kwonly_and_default():
    tools = await _collect_tools()
    for tool in tools:
        sig = inspect.signature(tool.fn)
        ctx_param = sig.parameters.get("ctx")
        if ctx_param is None:
            continue
        assert ctx_param.kind == inspect.Parameter.KEYWORD_ONLY
        assert ctx_param.default is not inspect.Parameter.empty
