# Kubernetes events (kubectl / k9s)

Kyverno admission failures appear in Kubernetes events.

Example commands:
```sh
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl describe pod <pod-name>
```

Look for events that mention `validate.kyverno.svc-fail` and the violated policy names.
