# Secret rules and structure

## Policy requirements
- Create and update secrets only with `drv`.
- Manual `kubectl` edits are not allowed.

## Payload structure
- Secrets are flat JSON objects.
- Keys and values must be strings.
- Nested objects or lists are not allowed.

Valid example:
```json
{
  "API_KEY": "*apiKey*",
  "SECRET_NUMBER": "42"
}
```

Invalid example:
```json
{
  "COMPLEX_SECRET": { "API_KEY": "value" },
  "SECRET_LIST": ["value"]
}
```
