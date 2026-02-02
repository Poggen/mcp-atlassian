# Environment and runtime paths

## Runtime paths
- Token file: `~/.config/drv/token`
- CLI config: `~/.config/drv`
- Kubeconfig: `~/.kube/config` (or `$KUBECONFIG`)
- Mise config: `~/.config/mise/conf.d`
- Git config: `~/.gitconfig`
- SSH config: `~/.ssh/config`

## Environment variables
Required:
- `GOPRIVATE` (for private Go modules)

Optional:
- `DRV_DEBUG`
- `DRV_ORG`
- `DRV_REPO`
- `KUBECONFIG`

## Org/repo precedence
1. CLI flags (`--org`, `--repo`)
2. Env vars (`DRV_ORG`, `DRV_REPO`)
3. Git repo auto-detection
