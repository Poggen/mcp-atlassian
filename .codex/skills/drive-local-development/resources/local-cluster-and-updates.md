# Local cluster and update tasks

## Create the local cluster
Drive templates ship with mise tasks that create a local kind-based cluster and deploy the system.

```sh
mise task ls
mise d:kind:create
```

Notes:
- The first run pulls required images and can take a while.
- Subsequent runs are usually under a minute on a modern machine.

## Update your app
Rebuild and redeploy a single app in the local cluster.

```sh
# From repo root
mise d:app:update myapp

# Or from within the app directory
mise d:app:update
```

## Update the full system
Rebuild and redeploy all system images.

```sh
mise d:system:update
```
