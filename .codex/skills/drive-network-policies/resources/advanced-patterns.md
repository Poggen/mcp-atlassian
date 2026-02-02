# Advanced network policy patterns

## Subject matching
- `matchPattern` supports `*` wildcards in subdomains.
- Use as few wildcards as possible.

## Port ranges and protocols
`toPorts.port` with `endPort` enables ranges.
`protocol` can be `TCP`, `UDP`, or `ANY`.

```yaml
apps:
  probe:
    extraEgress:
      - toFQDNs:
          - matchPattern: "*.github.com"
        toPorts:
          - ports:
              - port: "8000"
                endPort: 9000
                protocol: ANY
```
