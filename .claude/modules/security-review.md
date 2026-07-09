# Security Review

## Scope

Use this module for login, JWT, roles, permissions, secrets, privacy, microphone or voice data, and user diary or emotion data exposure.

## Checklist

- API Keys are not committed.
- API Keys are not logged.
- Passwords are hashed.
- Normal users can access only their own data.
- Admin authority is verified by backend.
- Client cannot forge user ID for protected data access.
- No unauthorized diary reads.
- AI output is validated and not blindly trusted.
- Error responses do not leak internal stack traces.
- Emotion and diary data are not unnecessarily exposed.
- Microphone or voice data usage is documented.

Frontend-hidden buttons are not permission control.

## Output

Return findings as `PASS`, `WARNING`, or `BLOCK`, with file evidence and remediation.
