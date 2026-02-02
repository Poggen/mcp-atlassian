---
name: drive-api-gateway
description: Expose Drive services with Gateway API, HttpRoutes, and custom domains.
metadata:
  short-description: Drive API gateway and routing
---

# Drive API Gateway

Use this skill when exposing endpoints, selecting `public` vs `gated` gateways, or configuring custom domains.

## Quick start
1. Enable the HttpRoute for your app in Drive chart values.
2. Verify the generated hostname and path for the stage.
3. Add custom domains only after the platform team has enabled them for your vertical.

## Read when
- **You need to expose an app endpoint**: `resources/exposing-endpoints.md`
- **You need custom domains and cert management**: `resources/custom-domains.md`
