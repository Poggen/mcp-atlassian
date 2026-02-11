# Temporary sourceImage workaround (wrapper images)

Drive currently resolves deployment image names from app keys. Until native
`sourceImage` reuse lands platform-wide, this repo uses thin wrapper images:

- `apps/mcp-jira/Dockerfile`
- `apps/mcp-confluence/Dockerfile`

Both wrappers only `FROM` the base `mcp-atlassian` image. In hosted stages,
this keeps `mcp-jira` and `mcp-confluence` as distinct published image names
while still reusing the same runtime bits.

## Why this exists

- `drive-service-infra` renders image refs as
  `<registry>/<vertical>/<system>/images/<app-name>:<tag>`.
- We run two app names (`mcp-jira`, `mcp-confluence`) with one shared runtime.
- Wrapper images are a temporary compatibility layer until native source-image
  reuse is available in Drive.

## Two-step release flow (temporary)

1. Merge app/runtime changes that affect `apps/mcp-atlassian`.
2. Wait for the base image tag to be published.
3. Pin wrappers to the new base digest:

```bash
./scripts/update-wrapper-base-image.sh \
  891377205362.dkr.ecr.eu-west-1.amazonaws.com/d1db59e/mcp-atlassian/images/mcp-atlassian:<new-tag>
```

4. Commit the wrapper Dockerfile updates in a follow-up PR.

Notes:
- The helper script requires `docker buildx`, `jq`, and registry access.
- If no argument is provided, the script resolves digest from `:latest`.
- Wrapper Dockerfiles are intentionally pinned via `@sha256:...`; if a
  placeholder digest is present, run the helper script before promotion.

## Local development flow

`mise d:app:update` contains local wrapper plumbing:

- `mise d:app:update mcp-atlassian`
  - builds/loads `mcp-atlassian:latest`
  - rebuilds `mcp-jira:latest` and `mcp-confluence:latest` with
    `BASE_IMAGE_REF=.../mcp-atlassian:latest`
  - restarts local deployments for both wrappers
- `mise d:app:update mcp-jira` or `mise d:app:update mcp-confluence`
  - rebuilds just that wrapper from local `mcp-atlassian:latest`

This keeps day-to-day local loops fast without editing digest pins.

## Rollback / removal

When Drive supports native source-image reuse:

1. Remove `apps/mcp-jira/` and `apps/mcp-confluence/`.
2. Set stage values back to `sourceImage: mcp-atlassian`.
3. Shrink `.drv.yaml` app list to only the true app artifact model.
4. Remove temporary local wrapper logic from `mise.toml`.
5. Remove this document.
