# Read-only usage guidance (Drive)

In Drive environments, treat the Argo CD CLI as **read-only**.

Recommended commands:
- `argocd app list`
- `argocd app get <app>`
- `argocd app diff <app>`

Avoid write operations (for example `argocd app sync`, `argocd app set`, or direct resource edits). Use GitOps changes instead so state stays traceable and reviewable.
