# Secret commands

## Apply
```bash
echo '{"key":"value"}' | drv secret apply --stage dev --name my-secret
```

## List
```bash
drv secret list --stage dev
```

## Template
```bash
drv secret template --stage dev --name my-secret
```
