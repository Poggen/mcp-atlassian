# JetStream configuration

Drive configures streams through the NACK operator. The Drive chart exposes simple defaults:
- `size` controls stream capacity.
- `criticality` controls replication + persistence.

## StorageType changes
NATS does not support updating `StorageType` in-place. You must recreate the stream.

Quick switch approach (downtime expected):
1. Remove the stream from `values.yaml`.
2. Deploy the change so the stream is removed.
3. Re-add the stream with the new config and deploy again.
