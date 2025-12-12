# MCP-atlassian

This is a fork of [sooperset/mcp-atlassian](https://github.com/sooperset/mcp-atlassian), with a couple of features added:

- OAuth Dynamic Client Registration via FastMCP's [OAuth Proxy](https://gofastmcp.com/servers/auth/oauth-proxy)
- NATS JetStream KV implementation of [py-key-value](https://github.com/strawgate/py-key-value), creating a custom [Storage Backend](https://gofastmcp.com/servers/storage-backends) for storing encrypted user tokens.
- OpenTelemetry tracing (OTLP/HTTP) + Cilium NetworkPolicy config so we can derive minimal egress allow-lists before Drive enforces network policies.
