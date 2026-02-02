# Exposing endpoints

## Gateway types
Drive provides two gateways:
- `public`: open internet exposure.
- `gated`: public exposure with IP allowlisting (Drive defaults).

## How routing works
Teams bind hostnames to services using Gateway API `HTTPRoute` resources.
The Drive chart can configure routes for you and will generate hostnames like:

```
<system>.[gated|public].<stage>.<vertical>.drive-platform.com/<app>
```

Example:
```
drive-canary.gated.dev-euw1.drive.drive-platform.com/canary
```

## Drive-managed TLS
Drive handles certificates and TLS termination for both technical hostnames and approved custom domains.
