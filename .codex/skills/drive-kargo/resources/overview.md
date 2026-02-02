# Kargo concepts (quick map)

Kargo is a GitOps-oriented delivery orchestrator for Kubernetes.

Core resources:
- **Project**: logical tenant boundary (usually a namespace).
- **Warehouse**: defines artifact sources (Git or container images).
- **Stage**: promotion target that requests Freight from a Warehouse or upstream Stage.
- **PromotionTask**: reusable step template that updates Git/Helm/Kustomize and notifies Argo CD.

A typical pipeline is Warehouse -> Stage (test) -> Stage (uat) -> Stage (prod).
