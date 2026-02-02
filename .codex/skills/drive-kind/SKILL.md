---
name: drive-kind
description: Use kind for local Kubernetes clusters in Drive development.
metadata:
  short-description: kind local clusters
---

# kind (local clusters)

Use this skill when creating or troubleshooting local kind clusters for Drive development.

## Quick start
1. `kind create cluster --name <name>`
2. `kubectl cluster-info --context kind-<name>`
3. `kind load docker-image <image>` to load local images

## Read when
- **You need cluster creation basics**: `resources/create-cluster.md`
- **You need kubeconfig/context tips**: `resources/kubeconfig-context.md`
- **You need to load images into kind**: `resources/load-images.md`
