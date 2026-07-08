# Backend Workflow

## Scope

Use this module for Python, FastAPI, Pydantic, SQLAlchemy, routers, schemas, services, models, and backend tests.

## Layer Rules

Router handles:

- HTTP parameters.
- Authentication and authorization boundary.
- Status codes.
- Calls into Service.

Schema handles:

- Request and response data constraints.
- Enums.
- Field validation.

Service handles:

- Business flow.
- AI Provider calls.
- Transaction boundary.
- Error translation.

Model handles:

- Persistence structure.
- Data relationships.

## Prohibited

- Complex business logic in Router.
- Returning SQLAlchemy Models directly as API responses.
- Swallowing exceptions.
- Printing secrets.
- Deleting tests to make tests pass.
- Fabricating AI success results.
- Changing public fields without a contract update.

## Validation

Prefer existing backend test, lint, type, and app startup checks. Record exact commands and results.
