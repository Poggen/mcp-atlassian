---
name: drive-local-development
description: Run and iterate on Drive services locally with kind clusters, mise tasks, and dev tooling.
metadata:
  short-description: Drive local dev workflows
---

# Drive local development

Use this skill when you need to spin up a local Drive cluster, update apps or system components, and validate endpoints locally.

## Quick start
1. `mise task ls` to see available tasks.
2. `mise d:kind:create` to create the local cluster (first run pulls images).
3. `mise d:app:update <app>` to rebuild and redeploy a single app.

## Read when
- **You need local cluster setup + updates**: `resources/local-cluster-and-updates.md`
- **You need port-forwarding and inspection**: `resources/port-forward-and-debug.md`
- **You need local Postgres access**: `resources/local-databases.md`
- **You need tool/version management**: `resources/tooling-mise.md`
