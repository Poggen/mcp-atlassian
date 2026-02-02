# Cross-account JetStream

JetStreams are account-scoped. To replicate across accounts, use **Sources** (or mirrors) rather than exporting a JetStream subject.

Notes:
- NATS creates an internal consumer to keep the destination stream synchronized.
- The Drive chart supports simplified configuration for account sourcing.
- Avoid `StorageType: memory` for cross-account streams to prevent replay storms on leader changes.
