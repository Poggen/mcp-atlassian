# ArgoCD policy visibility

When Kyverno blocks a resource, ArgoCD shows the validation failure in the resource details.

Suggested flow:
1. Open the ArgoCD app and select the failed resource.
2. Read the policy error details in the resource view.
3. Fix the manifest to comply with Drive golden paths (e.g., pod security settings).
