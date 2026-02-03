#!/usr/bin/env bash
# OAuth 2.1 + MCP E2E test helper.
# Usage: MCP_ENDPOINT=... ./scripts/mcp-oauth-e2e.sh
set -euo pipefail

MCP_ENDPOINT="${MCP_ENDPOINT:-}"
REDIRECT_URI="${REDIRECT_URI:-http://127.0.0.1:8080/authorization-code/callback}"
SCOPE="${SCOPE:-}"
REGISTER_PAYLOAD="${REGISTER_PAYLOAD:-scripts/mcp-register-payload.json}"

if [[ -z "${MCP_ENDPOINT}" ]]; then
  echo "MCP_ENDPOINT is required" >&2
  exit 1
fi

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== MCP OAuth 2.1 E2E ===${NC}"

echo -e "${BLUE}Step 1: Discovering OAuth configuration...${NC}"
MCP_RESPONSE=$(curl -s -i -X POST "${MCP_ENDPOINT}" \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":"1","method":"ping"}')

RESOURCE_METADATA_URL=$(echo "${MCP_RESPONSE}" | grep -i "resource_metadata=" | \
  sed 's/.*resource_metadata=\([^[:space:]]*\).*/\1/' | tr -d '\r\n"')

if [[ -z "${RESOURCE_METADATA_URL}" ]]; then
  echo -e "${RED}Failed to discover resource metadata URL${NC}" >&2
  exit 1
fi

echo "Resource metadata URL: ${RESOURCE_METADATA_URL}"
RESOURCE_METADATA=$(curl -s "${RESOURCE_METADATA_URL}")
AUTH_SERVER_URL=$(echo "${RESOURCE_METADATA}" | jq -r '.authorization_servers[0]')
if [[ -z "${SCOPE}" ]]; then
  SCOPE=$(echo "${RESOURCE_METADATA}" | jq -r '.scopes_supported[0] // empty')
fi

echo "Authorization Server: ${AUTH_SERVER_URL}"

echo -e "${BLUE}Step 2: Fetching OAuth endpoints...${NC}"
OAUTH_METADATA=$(curl -s "${AUTH_SERVER_URL}/.well-known/oauth-authorization-server")
AUTH_ENDPOINT=$(echo "${OAUTH_METADATA}" | jq -r '.authorization_endpoint')
TOKEN_ENDPOINT=$(echo "${OAUTH_METADATA}" | jq -r '.token_endpoint')
REGISTRATION_ENDPOINT=$(echo "${OAUTH_METADATA}" | jq -r '.registration_endpoint // empty')

CLIENT_ID=""
CLIENT_SECRET=""
TOKEN_AUTH_METHOD=""

if [[ -n "${REGISTRATION_ENDPOINT}" && -f "${REGISTER_PAYLOAD}" ]]; then
  echo -e "${BLUE}Step 3: Registering client...${NC}"
  REG_RESPONSE=$(curl -s -X POST "${REGISTRATION_ENDPOINT}" \
    -H "Content-Type: application/json" \
    -d @"${REGISTER_PAYLOAD}")
  CLIENT_ID=$(echo "${REG_RESPONSE}" | jq -r '.client_id')
  CLIENT_SECRET=$(echo "${REG_RESPONSE}" | jq -r '.client_secret // empty')
  TOKEN_AUTH_METHOD=$(echo "${REG_RESPONSE}" | jq -r '.token_endpoint_auth_method // empty')
  if [[ -z "${CLIENT_ID}" || "${CLIENT_ID}" == "null" ]]; then
    echo -e "${RED}Client registration failed:${NC}" >&2
    echo "${REG_RESPONSE}" | jq .
    exit 1
  fi
  echo -e "${GREEN}✓ Client registered${NC}"
else
  echo -e "${RED}Missing registration endpoint or payload; DCR skipped${NC}" >&2
  exit 1
fi

CODE_VERIFIER=$(openssl rand -base64 32 | tr '/+' '_-' | tr -d '=')
CODE_CHALLENGE=$(echo -n "${CODE_VERIFIER}" | openssl dgst -sha256 -binary | openssl base64 | tr '/+' '_-' | tr -d '=')
STATE=$(openssl rand -hex 16)

AUTH_URL="${AUTH_ENDPOINT}?response_type=code&client_id=${CLIENT_ID}&redirect_uri=${REDIRECT_URI}&scope=${SCOPE}&state=${STATE}&code_challenge=${CODE_CHALLENGE}&code_challenge_method=S256"

echo -e "${YELLOW}Open this URL in your browser:${NC}"
echo "${AUTH_URL}"
echo

echo -e "${YELLOW}After login, copy the authorization code from the callback URL${NC}"
read -p "Enter the authorization code: " AUTH_CODE

if [[ "${TOKEN_AUTH_METHOD}" == "client_secret_post" ]]; then
  TOKEN_RESPONSE=$(curl -s -X POST "${TOKEN_ENDPOINT}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=authorization_code&code=${AUTH_CODE}&redirect_uri=${REDIRECT_URI}&code_verifier=${CODE_VERIFIER}&client_id=${CLIENT_ID}&client_secret=${CLIENT_SECRET}")
else
  TOKEN_RESPONSE=$(curl -s -X POST "${TOKEN_ENDPOINT}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -u "${CLIENT_ID}:${CLIENT_SECRET}" \
    -d "grant_type=authorization_code&code=${AUTH_CODE}&redirect_uri=${REDIRECT_URI}&code_verifier=${CODE_VERIFIER}&client_id=${CLIENT_ID}")
fi

ACCESS_TOKEN=$(echo "${TOKEN_RESPONSE}" | jq -r '.access_token')
if [[ -z "${ACCESS_TOKEN}" || "${ACCESS_TOKEN}" == "null" ]]; then
  echo -e "${RED}Token exchange failed:${NC}" >&2
  echo "${TOKEN_RESPONSE}" | jq .
  exit 1
fi

echo -e "${GREEN}✓ Access token obtained${NC}"

echo -e "${BLUE}Step 4: Initialize MCP session...${NC}"
INIT_RESPONSE=$(curl -s -i -X POST "${MCP_ENDPOINT}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"oauth-test","version":"0.1"}}}')
SESSION_ID=$(echo "${INIT_RESPONSE}" | awk -F': ' 'tolower($1)=="mcp-session-id"{print $2}' | tr -d '\r')
if [[ -z "${SESSION_ID}" ]]; then
  echo -e "${RED}Missing MCP session id${NC}" >&2
  echo "${INIT_RESPONSE}"
  exit 1
fi

echo -e "${GREEN}✓ MCP session initialized (${SESSION_ID})${NC}"

echo -e "${BLUE}Step 5: Ping MCP...${NC}"
PING_RESPONSE=$(curl -s -X POST "${MCP_ENDPOINT}" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: ${SESSION_ID}" \
  -d '{"jsonrpc":"2.0","id":"1","method":"ping"}')

echo -e "${GREEN}✓ MCP ping:${NC}"
echo "${PING_RESPONSE}"

if [[ "${RUN_TOOLS_LIST:-}" == "1" ]]; then
  echo -e "${BLUE}Step 6: Tools list...${NC}"
  TOOLS_RESPONSE=$(curl -s -X POST "${MCP_ENDPOINT}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -H "mcp-session-id: ${SESSION_ID}" \
    -d '{"jsonrpc":"2.0","id":"tools","method":"tools/list"}')
  echo "${TOOLS_RESPONSE}"
fi

if [[ -n "${TOOL_NAME:-}" ]]; then
  echo -e "${BLUE}Step 7: Tool call (${TOOL_NAME})...${NC}"
  if [[ -n "${TOOL_ARGS_JSON:-}" ]]; then
    TOOL_ARGS="${TOOL_ARGS_JSON}"
  else
    TOOL_ARGS=$(jq -nc --arg q "${TOOL_QUERY:-}" '{query:$q}')
  fi
  TOOL_PAYLOAD=$(jq -nc --arg name "${TOOL_NAME}" --argjson args "${TOOL_ARGS}" \
    '{jsonrpc:"2.0",id:"tool",method:"tools/call",params:{name:$name,arguments:$args}}')
  TOOL_RESPONSE=$(curl -s -X POST "${MCP_ENDPOINT}" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -H "mcp-session-id: ${SESSION_ID}" \
    -d "${TOOL_PAYLOAD}")
  echo "${TOOL_RESPONSE}"
fi

echo -e "${GREEN}=== OAuth flow test complete ===${NC}"
