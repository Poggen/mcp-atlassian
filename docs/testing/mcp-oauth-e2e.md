# MCP OAuth E2E (Jira + Confluence)

This is a repeatable OAuth + MCP session validation flow using DCR, PKCE, and a minimal MCP handshake (`initialize` + `ping`).

## Prereqs

- `jq`, `curl`, `openssl`
- `agent-browser` (for consent flow automation)
- A running Chrome with CDP enabled

Start Chrome with CDP enabled (macOS):

```bash
open -na "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir=/tmp/agent-browser-chrome
```

## Script

Use the helper script:

```bash
MCP_ENDPOINT="https://mcp-atlassian.public.dev-euw1.d1db59e.drive-platform.com/mcp-jira/mcp" \
  ./scripts/mcp-oauth-e2e.sh
```

For Confluence:

```bash
MCP_ENDPOINT="https://mcp-atlassian.public.dev-euw1.d1db59e.drive-platform.com/mcp-confluence/mcp" \
  ./scripts/mcp-oauth-e2e.sh
```

Notes:
- Scope defaults to the first `scopes_supported` value from resource metadata (currently `READ`).
- DCR payload lives at `scripts/mcp-register-payload.json`.
- Redirect URI is `http://127.0.0.1:8080/authorization-code/callback`.

## Consent with agent-browser (headless/default)

When the script prints the `AUTH_URL`, open and approve it with `agent-browser`:

```bash
agent-browser open "<AUTH_URL>"
agent-browser snapshot -i
# Click Allow/Allow Access (ref will be shown by snapshot)
agent-browser click <ref>
```

After consent, the browser redirects to `127.0.0.1` and shows a connection error. The auth `code` is still present in the page content:

```bash
agent-browser get text body | rg -n "reloadUrl" -m 1
```

Copy the `code` value from the URL and paste it into the script prompt.

Tip: the error page stores the redirect URL in `loadTimeDataRaw.reloadUrl`.

## Consent with agent-browser (headed/manual)

If SSO requires manual login/consent, run in headed mode so a human can complete the flow:

```bash
agent-browser --headed open "<AUTH_URL>"
```

After completing login + consent in the UI, the browser lands on the 127.0.0.1 error page. Extract the `code` the same way:

```bash
agent-browser get text body | rg -n "reloadUrl" -m 1
```

## CDP fallback (optional)

If you prefer to reuse a local Chrome profile or the agent-browser daemon is blocked, start Chrome with CDP enabled and point agent-browser at it:

```bash
open -na "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir=/tmp/agent-browser-chrome
agent-browser --cdp 9222 open "<AUTH_URL>"
agent-browser --cdp 9222 get text body | rg -n "reloadUrl" -m 1
```

## JQL/CQL + fetch examples

Jira JQL search:

```bash
MCP_ENDPOINT="https://mcp-atlassian.public.dev-euw1.d1db59e.drive-platform.com/mcp-jira/mcp" \
  TOOL_NAME=search \
  TOOL_QUERY='project = WCAR ORDER BY updated DESC' \
  ./scripts/mcp-oauth-e2e.sh
```

Jira fetch:

```bash
MCP_ENDPOINT="https://mcp-atlassian.public.dev-euw1.d1db59e.drive-platform.com/mcp-jira/mcp" \
  TOOL_NAME=fetch \
  TOOL_ARGS_JSON='{"id":"jira:WCAR-81881"}' \
  ./scripts/mcp-oauth-e2e.sh
```

Confluence CQL search:

```bash
MCP_ENDPOINT="https://mcp-atlassian.public.dev-euw1.d1db59e.drive-platform.com/mcp-confluence/mcp" \
  TOOL_NAME=search \
  TOOL_QUERY='type=page AND text ~ "onboarding"' \
  ./scripts/mcp-oauth-e2e.sh
```

Confluence fetch:

```bash
MCP_ENDPOINT="https://mcp-atlassian.public.dev-euw1.d1db59e.drive-platform.com/mcp-confluence/mcp" \
  TOOL_NAME=fetch \
  TOOL_ARGS_JSON='{"id":"confluence:44593488"}' \
  ./scripts/mcp-oauth-e2e.sh
```

## Expected output

- DCR succeeds
- Token exchange succeeds
- `initialize` returns `mcp-session-id`
- `ping` returns an `event: message` JSON payload

If `initialize` returns `text/event-stream`, that is expected.
