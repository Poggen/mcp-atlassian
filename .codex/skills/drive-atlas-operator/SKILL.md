---
name: drive-atlas-operator
description: Use the Atlas Kubernetes Operator for declarative or versioned database schema management.
metadata:
  short-description: Atlas Operator schema workflows
---

# Atlas Operator (schemas)

Use this skill when managing database schemas declaratively in Kubernetes or when you need versioned migrations via Atlas Operator.

## Quick start
1. Choose declarative (`AtlasSchema`) or versioned (`AtlasMigration`) workflow.
2. Define schema source + database URL/secret.
3. Review the plan before applying changes.

## Read when
- **You need the operator overview and CRDs**: `resources/overview.md`
- **You need declarative schema flow**: `resources/declarative-workflow.md`
- **You need versioned migration flow**: `resources/versioned-workflow.md`
- **You need gotchas and safety tips**: `resources/gotchas.md`
