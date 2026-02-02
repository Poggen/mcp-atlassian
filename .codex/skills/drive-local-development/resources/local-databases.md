# Local databases

Drive templates include a Postgres cluster managed by the `cloudnative-pg` operator.

## Local behavior
- Local Postgres is ephemeral; stopping the cluster destroys its volume.
- Use this for development and testing only.

## Browse with pgweb
Start pgweb and open it in your browser.

```sh
mise d:db:port-forward
mise d:db:web
```

## Inspect in any environment
The same approach works for any environment as long as you set the correct Kubernetes context and namespace.
