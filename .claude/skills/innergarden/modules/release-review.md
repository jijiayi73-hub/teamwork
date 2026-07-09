# Release Review

## Definition Of Done

- [ ] Task goal is clear.
- [ ] Task ID, owner, and branch are clear.
- [ ] Change scope matches the task card.
- [ ] Core function can run.
- [ ] Happy path is verified.
- [ ] Exceptional input is verified.
- [ ] Permission flow is verified.
- [ ] API contract passes.
- [ ] Frontend typecheck passes.
- [ ] Backend related tests pass.
- [ ] Build passes.
- [ ] No real secrets.
- [ ] No unrelated large refactor.
- [ ] State docs are updated.
- [ ] Handoff is generated.
- [ ] Required Vibe Log is generated.
- [ ] At least one other member can understand the core logic.

## Rules

- Any blocking issue means final conclusion is `BLOCK`.
- A dirty worktree is not automatically blocking, but must be explained.
- Missing tests or unavailable build scripts are `WARNING` or `BLOCK` depending on risk.
- Never claim PR readiness without listing checks actually run.
