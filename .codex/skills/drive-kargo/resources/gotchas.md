# Gotchas

- **CRDs required**: Kargo resources are CRDs. Ensure the Kargo controllers and CRDs are installed before applying YAML.
- **Namespace scoping**: Projects, Warehouses, Stages, and Secrets usually live in the Project namespace.
- **Credential labels**: Git or registry credentials need the correct `kargo.akuity.io/cred-type` label (for example `git`).
- **Promotion flow**: Stages reference PromotionTasks that often update Git and then notify Argo CD; verify the repo credentials and Argo CD access paths.
- **Auth context**: The CLI requires a valid login; in Drive, prefer SSO over admin credentials.
