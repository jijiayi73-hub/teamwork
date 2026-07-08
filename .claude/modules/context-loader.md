# Context Loader

## Responsibility

Selectively load context for an `/innergarden` task and report which files were read.

It also owns the mandatory progress truth audit: before trusting project progress claims, compare state docs, handoffs, Vibe Logs, `.docx` documents, source code, and tests.

## Required Inputs

- User task text.
- Current repository tree.
- `AGENTS.md`.
- Project facts, contracts, state files, and task-board.
- Handoffs and Vibe Logs that may describe current progress.
- `.docx` project, defense, status, or progress documents when present.
- Source files and tests directly related to the task.

## Source Priority

Use this priority unless an existing project rule says otherwise:

1. Accepted ADR.
2. Explicitly Frozen contract.
3. Automated tests.
4. Backend Schema and Router.
5. Frontend TypeScript types and API Client.
6. Handoffs and Vibe Logs with concrete file, command, commit, or test evidence.
7. Readable `.docx` progress documents.
8. General design docs.
9. Comments and chat history.

## Procedure

1. Detect whether the task is status, plan, implement, debug, review, contract, handoff, document, or release.
2. Discover likely progress sources: state docs, task-board, handoffs, Vibe Logs, ADRs, and `.docx` files.
3. Read only the docs and code needed for that mode.
4. Extract claims about completed work, current work, API contracts, database state, tests, and blockers.
5. Compare claims with stronger evidence such as code, tests, accepted ADRs, and frozen contracts.
6. Mark every major claim as `verified`, `unverified`, `conflict`, or `stale`.
7. Report context conflicts before edits.
8. Include a "read files" list and progress truth audit in the final result.

## Output

- Read file list.
- Fact sources.
- Contract sources.
- Possible stale documents.
- Conflicts and recommended precedence.
- Progress truth audit table.
