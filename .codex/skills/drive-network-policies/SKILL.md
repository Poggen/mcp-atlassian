---
name: drive-network-policies
description: Configure Drive network policies (egress/ingress), with examples and troubleshooting tips.
metadata:
  short-description: Drive network policy patterns
---

# Drive network policies

Use this skill when adding or adjusting `extraEgress` / `extraIngress` rules, or when investigating blocked traffic.

## Quick start
1. Start with the basic egress/ingress examples.
2. Keep rules minimal and explicit (ports + protocols).
3. Use policy verdicts in Grafana to verify needed traffic.

## Read when
- **You need egress/ingress examples**: `resources/egress-ingress-basics.md`
- **You need advanced patterns**: `resources/advanced-patterns.md`
- **You need to derive rules from traffic**: `resources/policy-verdicts.md`
