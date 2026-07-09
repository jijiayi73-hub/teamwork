# Docs And Vibe Workflow

## Scope

Use this module for README updates, project docs, contracts, handoffs, ADRs, and Vibe Logs.

## Mandatory Trace Rule

Every `/innergarden` run must decide whether a Vibe Log is required and state that decision in the final result.

Create or update a durable trace when a task changes or verifies:

- Project progress.
- Implementation status.
- API or data contracts.
- Debugging conclusions.
- Release readiness.
- A claim that was previously unverified, stale, or conflicting.

If no Vibe Log is required, the handoff or final result must say why.

## Create A Vibe Log Draft When

- A core API is added.
- An API contract changes.
- Database structure changes.
- An AI Provider is integrated.
- A complex bug is solved.
- Frontend and backend integration completes.
- Permission or security logic changes.
- There is an important failed approach and second iteration.
- A meaningful architecture decision is made.

Do not force Vibe Logs for low-value visual-only edits.

## Vibe Log Required Sections

- Log ID and date.
- Goal.
- Existing context.
- Progress truth audit summary.
- Key prompts.
- AI proposed plan.
- Human checks and validation.
- Problems encountered.
- Iterations.
- Final result.
- Team understanding and reflection.
- Related files.
- Related Task.
- Related Commit or PR.
