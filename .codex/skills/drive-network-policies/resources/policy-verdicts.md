# Using policy verdicts

Drive logs network policy verdicts and exposes them in Grafana.

## Suggested workflow
1. Open Grafana dashboard **Drive / System Overview**.
2. Inspect **Network Policy Verdicts** for unexpected blocks.
3. Translate valid traffic into `extraEgress` rules.

Example translation:
```yaml
apps:
  netshoot-restricted:
    extraEgress:
      - toFQDNs:
          - matchName: "github.com"
        toPorts:
          - ports:
              - port: "80"
                protocol: TCP
      - toSystems:
          - matchName: drive-canary
```
