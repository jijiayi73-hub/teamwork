# Test And Debug Workflow

## Required Order

1. Reproduce.
2. Collect evidence.
3. Identify error layer.
4. Propose minimum hypothesis.
5. Apply minimum fix.
6. Rerun original test.
7. Run regression test.

## Error Layers

- Browser or UI.
- API Client.
- Network and CORS.
- Router.
- Schema validation.
- Service.
- Database.
- AI Provider.
- Environment configuration.

## Required Output

- Reproduction steps.
- Actual error.
- Expected behavior.
- Error layer.
- Root cause.
- Changes made.
- Commands actually run.
- Test results.
- Not yet verified.
- Regression risk.

## Guardrails

- Do not hide 422 errors by loosening every type.
- Do not change public contracts without running the API Contract Guardian.
- Do not delete tests to pass a run.
- Do not fabricate assistant messages after AI Provider failure.
