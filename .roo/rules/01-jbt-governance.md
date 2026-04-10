# JBT Governance Rules

## Source Of Truth

- Read these files before major work: ATLAS_PROMPT.md, docs/plans/ATLAS_MASTER_PLAN.md, PROJECT_CONTEXT.md, docs/prompts/总项目经理调度提示词.md, and docs/prompts/公共项目提示词.md.
- JBT is the only active project management source. J_BotQuant is legacy and stays read-only unless an approved task explicitly says otherwise.
- Do not create or copy a second business prompt family. Business meaning must come from ATLAS_PROMPT.md and docs/prompts only.

## Gatekeeping

- Atlas is the only business interface and gatekeeper.
- No write is allowed without a matching task, review, lock record, and active file-level token.
- Normal Roo-implemented batches require token agent Roo. Do not assume an Atlas token covers Roo implementation.
- White lists are file-level. If one more file is needed, stop and return the exact supplemental whitelist request to Atlas.

## Read-Only Inspection

- Read-only bug finding, vulnerability review, and diagnostics are allowed before code changes.
- The moment you conclude that a write is required, stop and hand Atlas the minimum file scope, service boundary, and validation plan.
- Do not turn a read-only inspection into an implementation batch by momentum.

## Protected Areas

- Do not touch services, shared contracts, workflow, GitHub governance files, compose files, env examples, runtime directories, logs, or real env files unless the current batch white list explicitly includes them.
- Do not modify governance/jbt_lockctl.py in Roo bootstrap or future Roo batches unless a dedicated task explicitly unlocks it.

## Batch Closeout

- After each Roo batch, if ATLAS_PROMPT.md is whitelisted, use the jbt-governance MCP tool append_atlas_log with signature Roo.
- Then stop for Atlas review, architect final review, lockback, commit, and sync.
- Keep summaries in Chinese and make them concrete enough for audit.