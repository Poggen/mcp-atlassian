# Inject secrets into apps

## In values.yaml
Add secret names under `drive.secrets`, then reference them in your app.

```yaml
drive:
  secrets:
    - ENV_SECRET
    - MOUNTED_SECRET
  apps:
    appName:
      secretEnv:
        ENV_VARIABLE_NAME:
          secretName: SECRETS
          secretKey: SECRET_NAME
      volumeMounts:
        secrets:
          MOUNTED_SECRET:
            path: /run/secrets
            optional: false
```

## Env vars vs mounted files
- **Mounted files**: Kubernetes updates the secret files automatically. Best for most cases.
- **Environment variables**: simpler, but require a pod restart to pick up changes.

## Example access in Go
```go
apiKey := os.Getenv("ENV_VARIABLE_NAME")
value, err := os.ReadFile("/run/secrets/MOUNTED_SECRET/API_KEY")
```
