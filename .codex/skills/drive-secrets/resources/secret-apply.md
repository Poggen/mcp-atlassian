# Create/update secrets with drv

Secrets must be provided via standard input (piped JSON).

```sh
# Inline JSON
echo '{"key1":"value1","key2":"value2"}' | drv secret apply --name my-secret --stage dev-euw1

# From file (compact JSON)
jq -c . <secretsFile>.json | drv secret apply --org <org> --repo <repo> --name <secret> --stage <stage>
```

Notes:
- Secret names and keys are case-sensitive.
- `--org` and `--repo` are optional when run inside the repo.

## List secrets and keys
```sh
drv secret list --repo <repo> --org <org>
drv secret list --repo <repo> --org <org> --keys
```
