# Enable NATS and JetStream

Enable NATS in your stage values, then opt apps into NATS env/secret injection.

```yaml
nats:
  enabled: true
  jetstream:
    enabled: true

apps:
  appName:
    nats: true
```

When enabled:
- `NATS_URL` is injected into the app.
- NAuth provisions a NATS account + user and writes credentials to a Kubernetes Secret.
