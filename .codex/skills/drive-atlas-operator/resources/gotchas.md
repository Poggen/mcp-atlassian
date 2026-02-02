# Gotchas and safety tips

- **Connection secrets**: Store database URLs in Kubernetes Secrets and reference them from the CRD.
- **Plan review**: Inspect planned changes before applying, especially in shared environments.
- **Concurrent controllers**: Avoid multiple controllers applying to the same database.
- **Migration discipline**: Keep migration history consistent and avoid editing applied migrations.
