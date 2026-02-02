---
name: drive-kyverno-policies
description: Understand Kyverno policy enforcement in Drive and how to diagnose blocked resources.
metadata:
  short-description: Drive Kyverno policy troubleshooting
---

# Drive Kyverno policies

Use this skill when a deployment is blocked by policy or when you need to locate the reason in ArgoCD or Kubernetes events.

## Quick start
1. Check the ArgoCD app/resource details for policy errors.
2. Inspect Kubernetes events (`kubectl` or `k9s`) for Kyverno violations.
3. Fix the resource using Drive golden paths; exemptions are rare.

## Read when
- **You need ArgoCD visibility**: `resources/argocd-visibility.md`
- **You need kubectl/k9s examples**: `resources/kubectl-events.md`
- **You need the exemption flow**: `resources/exemptions.md`
