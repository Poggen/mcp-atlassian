# Operations and refresh behavior

## Refresh interval
External Secrets syncs roughly every 30 minutes. Kubernetes updates the Secret object accordingly.

Check refresh times:
```sh
kubectl get es -o custom-columns='NAME:.metadata.name,LAST_REFRESH:.status.refreshTime,REFRESH_INTERVAL:.spec.refreshInterval'
```

## Deploy after updates
If your app reads secrets from env vars or does not watch files, restart the relevant Deployment so pods reload values.

## Access limitations
- You cannot read secret values directly outside the app.
- Secrets are not shareable across systems or stages.
- For local development, use local mechanisms; do not commit secret values.
