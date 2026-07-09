# Database Workflow

## Scope

Use this module for SQLAlchemy models, migrations, seed data, table relationships, and persisted data contracts.

## Before Any Database Change

State:

- Current structure.
- Reason for change.
- Old vs new difference.
- Existing data impact.
- API impact.
- Whether migration or initialization is required.
- Rollback plan.

## Rules

- Model changes require Schema review.
- Model changes require Service review.
- Table changes require migration or initialization plan.
- Do not store plaintext passwords.
- Do not remove existing fields without data impact analysis.
- Do not write sensitive diary content to unnecessary logs.
