---
name: drive-argocd
description: Drive guidance for Argo CD CLI usage, login, and safe read-only workflows.
metadata:
  short-description: Drive Argo CD CLI usage
---

# Drive Argo CD

Use this skill when inspecting Argo CD apps, syncing status, or logging in via the CLI.

## Quick start
1. Log in to the Argo CD server (SSO for Drive environments).
2. Use read-only commands to inspect apps and resources.
3. Avoid write operations from the CLI; prefer GitOps changes.

## Read when
- **You need CLI login patterns**: `resources/cli-login.md`
- **You need safe usage guidance**: `resources/read-only-guidance.md`
- **You need troubleshooting tips**: `resources/troubleshooting.md`
