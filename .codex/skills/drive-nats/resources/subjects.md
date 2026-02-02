# Subject design

Subject design is critical for routing, fanout, and cross-account patterns.

Recommendations:
- Use clear hierarchical subjects (`domain.service.event`).
- Reserve wildcards for consumers, not publishers.
- Document subject ownership per system.

Reference: NATS subject best practices in the official docs.
