# CLI login

## Standard login
```bash
argocd login <host>
```

If the server is behind a non-root gRPC-Web path:
```bash
argocd login <host>:<port> --grpc-web-root-path /argo-cd
```

## Drive SSO example
```bash
argocd login argocd.gated.euw1.d1db59e.drive-platform.com --sso
```

## Local port-forward (dev only)
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
argocd login localhost:8080
```
