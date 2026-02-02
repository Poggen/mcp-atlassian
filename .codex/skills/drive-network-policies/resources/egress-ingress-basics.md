# Egress and ingress basics

## Egress example
```yaml
apps:
  probe:
    extraEgress:
      - toFQDNs:
          - matchName: "github.com"
        toPorts:
          - ports:
              - port: "443"
                protocol: TCP
      - toSystems:
          - matchName: outpost
```

### Warning: list structure matters
A missing hyphen before `toPorts` changes evaluation order. Keep each rule in its own list item unless you intentionally want to broaden access.

## Ingress example
Only `fromSystems` is allowed for ingress.

```yaml
apps:
  outpost:
    extraIngress:
      - toSystems:
          - matchName: drive-sentinel
```
