# API Contract Guardian

## Scope

Use this module for any API path, request field, response field, enum, status code, permission, error structure, nullable behavior, time format, or frontend API type change.

## Sources To Compare

- API documentation.
- FastAPI Router.
- Pydantic Schema.
- Frontend TypeScript types.
- API Client.
- Automated tests.

## Checklist

- HTTP method.
- URL.
- Request fields.
- Response fields.
- Enum values.
- Status codes.
- Permissions.
- Nullable behavior.
- Time format.
- Error structure.

## Required Output

| 检查项 | 契约文档 | 后端 | 前端 | 测试 | 结论 |
| --- | --- | --- | --- | --- | --- |

Conclusion values:

- `PASS`
- `WARNING`
- `BLOCK`

If any blocking conflict exists, do not recommend PR merge.
