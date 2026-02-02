---
name: drive-secrets
description: Create, inject, and operate secrets in Drive using the drv CLI and External Secrets.
metadata:
  short-description: Drive secrets management
---

# Drive secrets management

Use this skill when creating or updating secrets, wiring them into apps, or troubleshooting refresh behavior.

## Quick start
1. Prepare a compact JSON map of string key/value pairs.
2. Pipe the JSON into `drv secret apply` for the target stage.
3. Inject secrets via env vars or mounted files in `values.yaml`.

## Read when
- **You need rules and payload structure**: `resources/secret-constraints.md`
- **You need apply/list commands**: `resources/secret-apply.md`
- **You need to inject secrets into apps**: `resources/secret-injection.md`
- **You need operations/refresh guidance**: `resources/secret-ops.md`
