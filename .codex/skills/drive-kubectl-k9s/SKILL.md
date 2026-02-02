---
name: drive-kubectl-k9s
description: Inspect Drive clusters with kubectl and k9s for debugging and verification.
metadata:
  short-description: kubectl + k9s workflows
---

# kubectl and k9s

Use this skill when inspecting pods, events, logs, or port-forwarding during Drive development or operations.

## Quick start
1. `kubectl config get-contexts` to confirm the target cluster.
2. `kubectl get pods -n <namespace>` to see workload status.
3. Use k9s for interactive resource navigation.

## Read when
- **You need kubectl basics**: `resources/kubectl-basics.md`
- **You need context/namespace switches**: `resources/context-and-namespace.md`
- **You need k9s workflow tips**: `resources/k9s-workflow.md`
