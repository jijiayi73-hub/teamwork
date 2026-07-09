---
name: innergarden
description: Project-level Inner Garden AI orchestrator. Use when the user invokes /innergarden or asks to plan, implement, debug, review, document, hand off, or release Inner Garden work through the unified workflow.
---

# Inner Garden Orchestrator

## Purpose

`/innergarden` is the only public AI work entry for Inner Garden. Team members describe work in natural language, and this orchestrator loads project context, chooses the internal workflow modules, plans, executes or reviews, validates, updates state, and reports in one unified format.

Internal modules are implementation details. Do not ask users to call `/frontend`, `/backend`, `/api`, `/test`, or `/docs`.

## Invocation

Use:

```text
/innergarden <natural language task>
```

Examples:

```text
/innergarden 查看当前项目状态
/innergarden 规划聊天失败重试功能，不修改代码
/innergarden 实现聊天失败后的前端重试流程
/innergarden 检查当前分支能否提交 PR
/innergarden 调试日记接口返回 422 的问题
/innergarden 接手 TASK-021
```

Users do not need to memorize subcommands. Detect intent from the task text.

## Operating Modes

Recognize these internal modes:

- `status`: read current state only.
- `plan`: plan only, no code changes.
- `implement`: implement a feature or change.
- `debug`: reproduce and fix a defect.
- `review`: review code, branch, or proposed changes.
- `contract`: check API and data contracts.
- `handoff`: take over or hand off a task.
- `document`: update docs, ADRs, or Vibe Logs.
- `release`: pre-merge acceptance review.
- `deploy`: deploy to VPS production environment.

If the user does not specify a mode, infer it from wording. Before editing business code, explicitly state that the task is in `implement` or `debug` mode.

## Internal Modules

The orchestrator may call these internal modules. They are not public commands:

- `modules/context-loader.md`
- `modules/task-planner.md`
- `modules/frontend-workflow.md`
- `modules/backend-workflow.md`
- `modules/database-workflow.md`
- `modules/api-contract-guardian.md`
- `modules/test-debug-workflow.md`
- `modules/security-review.md`
- `modules/docs-vibe-workflow.md`
- `modules/release-review.md`
- `modules/deployment-workflow.md`

## Mandatory Workflow

### 1. Detect

Identify user goal, operating mode, likely affected layers, and whether the task is read-only.

### 2. Evidence Gate

Before planning or editing, verify project progress claims against durable evidence. This step is mandatory for every mode, including `status` and `plan`.

Read, when present:

- `docs/state/current-status.md`
- `docs/state/task-board.md`
- `docs/state/known-issues.md`
- relevant files under `docs/handoffs/`
- relevant files under `docs/vibe-logs/`
- relevant Accepted ADRs under `docs/decisions/`
- relevant `.docx` progress or project documents found in `docs/`, `defense/`, or other project documentation folders

If `.docx` files exist, extract and read their text with an available document reader before trusting progress claims. If the environment cannot read `.docx`, mark that as `WARNING` and do not treat the `.docx` contents as verified.

Produce a progress truth audit:

| Claim | Evidence read | Verdict |
| --- | --- | --- |

Verdict values:

- `verified`: supported by source code, tests, accepted docs, handoffs, Vibe Logs, or readable `.docx` evidence.
- `unverified`: mentioned but not supported by inspected evidence.
- `conflict`: durable sources disagree.
- `stale`: evidence exists but appears older than newer state, handoff, or implementation facts.

Do not continue as if a claim is true when the verdict is `unverified`, `conflict`, or `stale`; report the limitation and scope the task around confirmed facts.

### 3. Load Context

Read only relevant context:

- `AGENTS.md`
- `docs/project/`
- `docs/contracts/`
- `docs/state/current-status.md`
- `docs/state/task-board.md`
- `docs/state/known-issues.md`
- `docs/vibe-logs/`
- relevant `.docx` project or progress documents
- source code and tests directly related to the task
- relevant handoff files or ADRs

Do not read every large file indiscriminately.

### 4. Inspect Repository

Check:

- current Git branch
- `git status`
- uncommitted changes
- whether the task is already assigned
- whether planned files or APIs overlap with active tasks

If the worktree is dirty, do not delete or overwrite others' work.

### 5. Scope

Before changing files, state:

- current behavior
- target behavior
- change scope
- out of scope
- API impact
- database impact
- risks
- acceptance criteria

### 6. Register Task

For `implement`, `debug`, refactor, or contract-change tasks:

- create or confirm a Task ID
- record owner
- record branch
- record expected files
- update `docs/state/task-board.md`

If owner is unknown, use the current executor identity or `unassigned`. Do not invent names.

### 7. Route

Route automatically:

- frontend pages, components, state, API Client: `modules/frontend-workflow.md`
- FastAPI, Router, Schema, Service, Model: `modules/backend-workflow.md`
- tables, relations, migrations: `modules/database-workflow.md`
- fields, status codes, enums, errors: `modules/api-contract-guardian.md`
- failures, tests, integration debugging: `modules/test-debug-workflow.md`
- login, permissions, secrets, privacy: `modules/security-review.md`
- docs, Vibe Logs, README: `modules/docs-vibe-workflow.md`
- pre-merge checks: `modules/release-review.md`
- VPS deployment, code updates, container rebuilds: `modules/deployment-workflow.md`

One task may use multiple modules.

### 8. Plan Before Change

Provide the smallest workable plan before edits. Unless explicitly requested, do not:

- replace the tech stack
- move large file sets
- rename many public fields
- rewrite working modules
- change unrelated features together
- overdesign for speculative future needs

### 9. Execute

Apply changes according to selected module rules.

### 10. Validate

Run the relevant checks available in this repository. Distinguish:

- actually run
- static inspection only
- could not run because of environment limits
- recommended local follow-up

Never replace validation with guesses.

### 11. Contract Check

Run `modules/api-contract-guardian.md` whenever the task touches:

- API path
- request fields
- response fields
- enum values
- status codes
- permissions
- time format
- nullable behavior
- error structure
- frontend TypeScript API types

### 12. Document

When work completes or pauses:

- update `docs/state/current-status.md`
- update `docs/state/task-board.md`
- create or update a handoff
- update API, architecture, or data docs when needed
- create a Vibe Log draft when conditions in `modules/docs-vibe-workflow.md` are met
- if the task changed durable progress, implementation, contracts, debugging conclusions, or release readiness, record the evidence and verification result in a Vibe Log or handoff

Do not mark work complete unless the final report lists where the trace was written or explains why no Vibe Log was required.

### 13. Review Result

Final conclusion must be exactly one:

- `PASS`: can proceed.
- `WARNING`: can continue with explicit risk.
- `BLOCK`: do not recommend merge.

## Unified Result Format

Return this shape for `/innergarden` runs. Omit only sections that truly do not apply to `status` or `plan`; do not fabricate results.

```markdown
# Inner Garden Task Result

## 1. 执行模式

## 2. 任务理解

## 3. 已读取上下文

## 4. 仓库状态

## 4.5 进度真伪审查

| Claim | Evidence read | Verdict |

## 5. 修改前行为

## 6. 目标行为

## 7. 执行计划

## 8. 修改文件

| 文件 | 操作 | 原因 |

## 9. 数据流变化

## 10. API / 数据库影响

## 11. 实际验证

| 命令或检查 | 是否实际运行 | 结果 |

## 12. 尚未验证

## 13. 风险与已知限制

## 14. 文档与状态更新

## 15. 建议分支和 Commit

## 16. Handoff

## 17. 最终结论

PASS / WARNING / BLOCK
```
