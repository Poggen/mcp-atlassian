# Custom domains

## High-level flow
1. Add desired domains/subdomains to the Drive platform config (PR).
2. Create DNS records (CNAME) that point to the Drive technical hostname.
3. Add a custom `HTTPRoute` that lists the custom hostname.

## Example `HTTPRoute`
```yaml
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: my-custom-route
spec:
  hostnames:
    - myservice.mycustomdomain.com
  parentRefs:
    - name: gated-gw
      namespace: gateway-system
      sectionName: mycustomdomain.com
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: myapp
          port: 80
```

## Certificate management (DNS validation)
When Drive manages certificates for your custom domains:
- Create an AWS role with a restricted trust policy for cert-manager DNS challenges.
- Limit permissions to Route53 TXT record changes for your domain.
- Share the role ARN with the Drive platform team for setup.

Keep the policy scoped to the exact domain(s) that need certificates.
