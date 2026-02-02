# Troubleshooting

- If login fails behind an ingress, try `--grpc-web-root-path` to match the server path.
- For SSO logins, complete the browser-based flow before retrying CLI commands.
- If you cannot reach the server, check DNS/VPN and confirm the endpoint is gated vs public.
