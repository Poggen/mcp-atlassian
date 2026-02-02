# CLI authentication

## Login (admin credentials)
```bash
kargo login https://kargo.example.com \
  --admin \
  --password "${ADMIN_PASSWORD}"
```

Verify connection:
```bash
kargo version
```

## Drive SSO example
Use SSO for Drive-hosted Kargo instances:
```bash
kargo login --sso https://kargo.gated.euw1.d1db59e.drive-platform.com/
```

Notes:
- The SSO flag and URL are Drive-specific.
- Admin login is typically for local or bootstrap scenarios.
