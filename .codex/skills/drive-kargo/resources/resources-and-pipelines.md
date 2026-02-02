# Declarative setup (apply)

Kargo resources can be applied via the CLI:

```bash
cat <<EOF | kargo apply -f -
apiVersion: kargo.akuity.io/v1alpha1
kind: Project
metadata:
  name: kargo-demo
---
apiVersion: kargo.akuity.io/v1alpha1
kind: Warehouse
metadata:
  name: kargo-demo
  namespace: kargo-demo
spec:
  subscriptions:
  - image:
      repoURL: public.ecr.aws/nginx/nginx
      constraint: ^1.26.0
EOF
```

Add Stages that request Freight from the Warehouse and reference a PromotionTask for the promotion steps.
