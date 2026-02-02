# Versioned workflow (AtlasMigration)

Use `AtlasMigration` to apply a versioned migration directory.

Typical flow:
1. Maintain migration files in a repo or volume.
2. Point `AtlasMigration` to the migration source and target DB.
3. Operator runs Atlas migration plan/apply to advance the schema.
