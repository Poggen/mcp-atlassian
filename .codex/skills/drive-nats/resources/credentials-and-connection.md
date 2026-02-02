# Credentials and connection

## Runtime values
- `NATS_URL` environment variable
- Credentials file at `/var/run/secrets/nats/user.creds`

## Go client example
```go
natsURL := os.Getenv("NATS_URL")
credsPath := "/var/run/secrets/nats/user.creds"

nc, err := nats.Connect(natsURL, nats.UserCredentials(credsPath))
if err != nil {
    // handle error
}
defer nc.Close()
```
