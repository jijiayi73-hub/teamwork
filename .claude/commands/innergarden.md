# `/innergarden`

Use the shared Inner Garden orchestrator. Do not maintain separate Claude Code rules here.

Task:

```text
$ARGUMENTS
```

Workflow:

1. Read `AGENTS.md`.
2. Read `skills/innergarden/SKILL.md`.
3. Treat `$ARGUMENTS` as the natural language task.
4. Load project facts, contracts, state, and task-board according to the Skill.
5. Route to the internal modules named by the Skill.
6. Validate the work that can actually be validated.
7. Return the unified `Inner Garden Task Result` format.

If this command file is copied into a project as `.claude/commands/innergarden.md`, Claude Code can use it as the thin project command adapter.
