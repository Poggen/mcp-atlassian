# Declarative workflow (AtlasSchema)

Use `AtlasSchema` to keep the database aligned with a declared schema.

Typical flow:
1. Define the desired schema source (file, URL, or dev database).
2. Provide a connection URL/secret for the target database.
3. Operator runs `atlas schema plan` and `atlas schema apply` to converge.
