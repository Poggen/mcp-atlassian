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
MCP_ENDPOINT="https://mcp-atlassian.public.dev-euw1.d1db59e.drive-platform.com/mcp-atlassian/mcp" \
  ./scripts/mcp-oauth-e2e.sh
```

For Confluence:

```bash
MCP_ENDPOINT="https://mcp-atlassian.public.dev-euw1.d1db59e.drive-platform.com/mcp-atlassian-confluence/mcp" \
  ./scripts/mcp-oauth-e2e.sh
```

Notes:
- Scope defaults to the first `scopes_supported` value from resource metadata (currently `READ`).
- DCR payload lives at `scripts/mcp-register-payload.json`.
- Redirect URI is `http://127.0.0.1:8080/authorization-code/callback`.

## Consent with agent-browser

When the script prints the `AUTH_URL`, open and approve it with `agent-browser`:

```bash
agent-browser --cdp 9222 open "<AUTH_URL>"
agent-browser --cdp 9222 snapshot -i
# Click Allow/Allow Access (ref will be shown by snapshot)
agent-browser --cdp 9222 click <ref>
```

After consent, the browser redirects to `127.0.0.1` and shows a connection error. The auth `code` is still present in the page content:

```bash
agent-browser --cdp 9222 get text body | rg "authorization-code/callback"
```

Copy the `code` value from the URL and paste it into the script prompt.

## Expected output

- DCR succeeds
- Token exchange succeeds
- `initialize` returns `mcp-session-id`
- `ping` returns an `event: message` JSON payload

If `initialize` returns `text/event-stream`, that is expected.
