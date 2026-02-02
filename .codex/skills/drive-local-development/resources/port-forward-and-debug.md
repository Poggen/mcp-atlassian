# Port-forwarding and local inspection

## Inspect services
Once your cluster is running you can inspect resources with `kubectl` or `k9s`.

## Port-forward to an app
Use the helper task to open a local port to your app.

```sh
mise d:app:port-forward myapp
```

## Validate HTTP endpoints
The Drive templates include a Bruno collection at `/helpers/bruno/`.

- Select the `local` environment.
- Use the port-forwarded endpoints to test API calls.
