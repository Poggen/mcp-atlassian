# kubectl basics

Common commands:
```bash
kubectl get pods -n <namespace>
kubectl describe pod <pod> -n <namespace>
kubectl logs <pod> -n <namespace>
```

Port-forward a service:
```bash
kubectl port-forward svc/<service> 8080:80 -n <namespace>
```
