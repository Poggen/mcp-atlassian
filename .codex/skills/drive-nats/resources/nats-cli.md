# NATS CLI basics

## Contexts
Contexts store connection settings (server URL, creds, etc.).

```bash
nats context create my-context
nats context edit my-context
nats context save local --server nats://localhost:4222 --select
nats context ls
nats context select
```

## Pub/Sub
```bash
nats pub <subject> <message>
nats sub <subject>
```

## JetStream streams and consumers
```bash
nats stream add ORDERS --subjects "ORDERS.*" --storage file
nats consumer add ORDERS NEW --filter ORDERS.received --ack explicit --pull
```
