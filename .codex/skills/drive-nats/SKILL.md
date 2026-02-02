---
name: drive-nats
description: Enable and use NATS (JetStream) on Drive, including credentials and stream configuration patterns.
metadata:
  short-description: Drive NATS + JetStream
---

# Drive NATS (JetStream)

Use this skill when enabling NATS in Drive, connecting clients, or defining JetStream streams and cross-account patterns.

## Quick start
1. Enable NATS + JetStream in your stage values and set `nats: true` for apps that need access.
2. Read `NATS_URL` and the mounted creds file in your app.
3. Use Drive-provided JetStream defaults (size + criticality) unless you need custom config.

## Read when
- **You need Drive-specific enablement**: `resources/enable-and-configure.md`
- **You need credentials and connection details**: `resources/credentials-and-connection.md`
- **You need JetStream configuration patterns**: `resources/jetstream-config.md`
- **You need subject design guidance**: `resources/subjects.md`
- **You need cross-account JetStream notes**: `resources/cross-account.md`
- **You need NATS CLI basics**: `resources/nats-cli.md`
