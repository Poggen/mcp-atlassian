# Context and namespace

List contexts:
```bash
kubectl config get-contexts
```

Switch context:
```bash
kubectl config use-context <context-name>
```

Set a default namespace for the current context:
```bash
kubectl config set-context --current --namespace=<namespace>
```
