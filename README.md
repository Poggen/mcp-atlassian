# Drive - Jumpstart Go Service

This is an example of how an application which demonstrates multiple patterns to be used in services:

- Simple REST api
- Database storage using Cloudnative Postgres
- Messaging, pub-sub and key-value store using NATS
- OpenTelemetry for logging, metrics & tracing

## Getting Started

### Prerequisites

Before you begin, check out the [Quickstart Guide](https://backstage.drive-platform.com/docs/wirelesscar-wdp/component/drive/quickstart/) for an overview.

You need to have a working development setup with git with ssh, Docker and Enablers CLI aka we.
And just a reminder, if you are using Windows, you also need to install PowerShell 7.x

### Tooling

This project uses [mise](https://mise.jdx.dev/) as the tool manager. All required tools and their versions are managed via mise. To install the necessary tools, follow the [installation instructions](https://backstage.drive-platform.com/docs/wirelesscar-wdp/component/drive/quickstart/part-02-installation/).


To set a specific version of a tool (e.g., Go), run:

```sh
mise use go@1.22.5
```

### Tasks

Development tasks are automated using [mise tasks](https://mise.jdx.dev/tasks/).

To setup mise with all tasks provided by Drive, run:

```sh
drv mise setup
```

To see all available tasks, run:

```sh
mise task ls
```

To get started with local development you create a kind cluster with all dependencies and your apps:

```sh
mise kind:create
```

If you make changes in both infrastructure and code, and want to update your local cluster:

```sh
mise system:update
```

You might only want to rebuild and deploy your app:

```sh
mise app:update myapp
```

Or update all of your apps:

```sh
mise app:update:all
```

If you did a `mise task ls` you already now there are several more task, some of them is listed below.

#### Building

Build a Go app:

```sh
# From any directory, specify the app name
mise go:build myapp

# From within the app directory
mise go:build
```

Build all Go apps:

```sh
mise go:build:all
```

#### Testing

Run unit tests:

```sh
mise go:test myapp
# or, from within the app directory
mise go:test
```

Test all Go apps:

```sh
mise go:test:all
```

Run tests with coverage:

```sh
mise go:test:coverage myapp
# or, from within the app directory
mise go:test:coverage
```

#### Dependency Management

Update Go dependencies:

```sh
mise go:update:dependencies myapp
# or, from within the app directory
mise go:update:dependencies
```

#### Static Analysis

Run `go vet` for static analysis:

```sh
mise go:vet myapp
# or, from within the app directory
mise go:vet
```

### Docker

Build a Docker image:

```sh
mise docker:build myapp
# or, from within the app directory
mise docker:build
```

Build all Docker images:

```sh
mise docker:build:all
```

### Local Development

To spin up a local Kubernetes cluster with all dependencies using [kind](https://kind.sigs.k8s.io/):

```sh
mise kind:create
```

- The cluster uses the context `kind-mcp-atlassian`.
- Infrastructure manifests are in `infrastructure/local`, with dependencies in `infrastructure/local/dependencies`.
- Dependencies are installed via [Helm](https://helm.sh/).
- The initial setup may take a few minutes as images are downloaded and preloaded into kind.

### Inspecting Your Service

Once running, interact with your service using [kubectl](https://kubernetes.io/docs/reference/kubectl/) or [k9s](https://k9scli.io/).

## Deploying stuff

### CI/CD

### Infrastructure
This template uses [Helm](https://helm.sh/) to create different infrastructure setup for different environments.

Folder `infrastructure` contains infratructure setup for each [stage](https://backstage.drive-platform.com/docs/wirelesscar-wdp/component/drive/architecture/terminology/#stage).
For local development stage `local` is used. Local stage folder also conatins the needed dependencies to be able to deploy locally to kind.

#### CI
This template uses [`GitHub Actions`](./.github/workflows/container.yaml) to build the container for the service. It's
still rudimentary with no testing and security scanning.

#### Promotions to stages
[`Kargo`](https://kargo.akuity.io/) is currently being used to subscribe to either container changes in ECR, as well as tracking updates to changes
to the git repository for infrastructure updates.

These changes are combined and promoted to the different stages by pushing the combined changes to environment branches.

#### CD
[ArgoCD](https://argo-cd.readthedocs.io/en/stable/) is used for the deployment of the service.

Currently, `Kargo` is updating the environment branches of the repository with this configuration.
