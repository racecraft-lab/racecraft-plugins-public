# Canonical Task List Reference

The complete, prescribed checklist the autopilot materializes at Step 1.1 in
`update_plan` and `autopilot-state.json`. Every entry below MUST appear in both
stores before Phase 1 starts. Do NOT omit, collapse, or defer entries — when a
required extension is absent, the item still appears, marked as
`skipped: <extension> not installed`.

## Contents

- [Task Naming Pattern](#task-naming-pattern) — phase + post-impl naming conventions
- [Canonical Post-Implementation Task List](#canonical-post-implementation-task-list) — 13-row combined durable Post plan + missing-extension behavior
- [Extension Detection Rule](#extension-detection-rule) — `.specify/extensions.yml` / `.registry` / Glob fallback
- [Out-Of-Stage Entries](#out-of-stage-entries) — how a staged run marks entries outside the resolved stage
- [Consensus Tasks Are Mandatory](#consensus-tasks-are-mandatory) — every Clarify session, Checklist domain, and Analyze gets a paired Consensus task
- [Other Rules](#other-rules) — Phase 7 group decomposition, item naming, completion order, completeness verification
- [Reference `autopilot-state.json` Schema](#reference-autopilot-statejson-schema) — full example JSON document

## Task Naming Pattern

Parsed from the workflow file:

```text
  "Archive Sweep: previously merged specs dry-run/apply eligibility"
  "Phase 0: Prerequisites"
  "Phase 1: Specify"
  "Phase 2: Clarify - <Session Name>"           ← one per session
  "Phase 2: Clarify - <Session Name> Consensus" ← MANDATORY after each session
  "Phase 2: Clarify - Pending session discovery" ← only if no sessions parsed yet
  "Phase 3: Plan"
  "Phase 4: Checklist - <Domain>"               ← one per domain
  "Phase 4: Checklist - <Domain> Consensus"     ← MANDATORY after each domain
  "Phase 4: Checklist - Pending domain discovery" ← only if no domains parsed yet
  "Phase 5: Tasks"
  "Phase 6: Analyze"
  "Phase 6: Analyze - Consensus"                ← MANDATORY after analyze
  "Phase 6.5: Confidence Gate"                  ← MANDATORY after analyze consensus
  "Phase 7: Implement - Pending task decomposition" ← before tasks.md exists
  "Phase 7: <Group> (<task IDs>)"               ← parsed from tasks.md
  "Post: <task name>"                           ← from the canonical list below
```

## Canonical Post-Implementation Task List

Every item below MUST appear in `update_plan` and `autopilot-state.json`
unless its required extension is provably absent. **Do NOT omit any of
these, do NOT collapse them, do NOT defer them** — the user expects to
see all of them in the plan panel before Phase 1 starts. When an
extension is missing, still create the item but mark it
`skipped: <extension> not installed`.

This is the combined Codex plan: the numbered 10-19 gates from
[post-implementation.md](./post-implementation.md#canonical-post-items-10-19)
plus the supporting tasks that remain independently visible for resume
safety. `Final Reviewability Backstop` owns the diff-gate/UAT boundary, and
`PR Packet/Body Generation` owns the body-generation boundary; the supporting
rows are evidence-producing steps, not substitutes for those numbered gates.

```text
  "Post: Doctor Extension Check"        ← doctor / speckit-utils ext
  "Post: Verify Implementation"         ← verify ext
  "Post: Verify Tasks Phantom Check"    ← verify-tasks ext
  "Post: Code Review"                   ← built-in independent review (no ext)
  "Post: Integration Suite"             ← always required (no ext)
  "Post: Reviewability Diff Gate"       ← always required (no ext)
  "Post: UAT Runbook Generation"        ← always required (no ext, skeleton script + author agent)
  "Post: Final Reviewability Backstop"  ← numbered Post 15 gate
  "Post: PR Packet/Body Generation"     ← numbered Post 16 gate
  "Post: PR Body Generation"            ← always required (no ext)
  "Post: PR Creation"                   ← always required (no ext)
  "Post: Review Remediation"            ← always required (no ext)
  "Post: Retrospective"                 ← retrospective ext (FINAL STEP)
```

Claude shows 11 rows. Codex shows the same 11 rows plus two supporting rows
after `Post: UAT Runbook Generation`: `Post: Final Reviewability Backstop` and
`Post: PR Packet/Body Generation`. Claude runs that work inside
`Post: PR Body Generation` and `Post: PR Creation`
([post-implementation.md §3.2](./post-implementation.md#32-pr-creation)).
The difference is in plan visibility only; both hosts run the same steps.

## Extension Detection Rule

For each extension-dependent task: check `.specify/extensions.yml`
(or `.specify/extensions/.registry`) for the extension's `enabled: true` flag,
OR confirm the extension directory exists. If neither, the task
still appears in the task list with status `skipped: <ext-name> not installed`.
Never silently drop a task.

## Out-Of-Stage Entries

The canonical list is **never truncated** per stage. A staged run
(`--stage plan` or `--stage implement`) still creates every entry above; entries
outside the resolved stage take
`skipped: <reason>` in the **status** field — the same shape used just above for
an absent extension, so one search finds both kinds of skip.

- **Status field only.** The marker goes in the status field and
  the entry name never changes. The coverage guard matches post-implementation
  checkpoints by exact name equality, so a `skipped:`-prefixed *name* is read as
  a *missing* checkpoint and fails the run at the pre-final audit.
- **No `pending` substring.** The marker text
  MUST NOT contain the substring `pending` in any casing — the guard flags any
  string value containing it case-insensitively.
- **What each stage marks.** A planning-stage run marks the
  `Phase 7: Implement` entry and every `Post:` entry; the post-implementation
  family is where the audit actually blocks. An implementation-stage run marks
  the six planning phase entries instead.

The pre-final completion audit treats a `skipped: <reason>` status as
**satisfied**, not as an incomplete item, or a planning-stage run could never
return a final response.

## Consensus Tasks Are Mandatory

Every Clarify session, every Checklist domain, and the Analyze phase MUST
have a corresponding Consensus task immediately after it. The consensus task
runs the two-layer resolution process (Rule 6 in SKILL.md / `references/consensus-protocol.md`).
A Consensus task may be skipped ONLY if the executor reports zero unresolved
items. Never omit consensus tasks from the task list at creation time.

## Other Rules

- Replace `Phase 7: Implement - Pending task decomposition` with concrete
  task-group items immediately after `tasks.md` is created. Do not leave Phase 7
  as a single placeholder once tasks can be parsed.
- Phase 7 decomposes into groups after `tasks.md` is created
  (test / impl / verify per phase — see [`phase-execution.md`](./phase-execution.md))
- Mark completed phases immediately; first pending phase as `in_progress`
- Use EXACTLY the same item names in `update_plan` and `autopilot-state.json`
- Preserve one or more pending items for every later canonical phase when
  resuming from a middle phase
- Print a checklist summary immediately after writing both copies
- **Verify task-list completeness before starting Phase 1**: count the
  prescribed entries (every Phase, every Consensus, every `Post:` task) and
  confirm each is present in both stores. If the count differs, ADD the
  missing entries before advancing. Then run the coverage guard below and do
  not advance unless it exits 0.

```text
<resolved_python> "<plugin-root>/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py" --workflow <workflow> --state <workflow-dir>/autopilot-state.json --require-autonomy-boundary --current-execution-environment "<live-execution-environment>" --current-sandbox-mode "<live-sandbox-mode>" --current-approval-reviewer "<live-approval-reviewer>" --current-writable-root "<live-writable-root>" --rule status-evidence
```

Replace every `<live-...>` value from the current system/developer execution
context, never from the workflow, state, repository, or a prior run; repeat
`--current-writable-root` for every current writable root. When v2 state
declares a changed-file manifest, also pass
`--expected-base-commit <live-baseRefOid> --expected-head-commit <live-headRefOid>`
from freshly fetched live PR metadata, never from the state or manifest.

`<resolved_python>` is the Python 3.11+ interpreter resolved by the Installed
Runtime Contract, never a literal `python3`. `--rule status-evidence` gates the
exit code on the nine workflow/state status-evidence checks
(`workflow_status_evidence_errors`, `state_status_errors`,
`autonomy_boundary_errors`, `stage_mirror_errors`, `workflow_authority_errors`,
`state_privacy_errors`, `marker_evidence_privacy_errors`,
`formal_checkpoint_errors`, `artifact_review_errors`) and the three current-run
state-plan invariants (`in_progress_errors`, `duplicate_state_steps`,
`state_order_errors`); other checks are printed but never block, so a spec that
predates the structural coverage checks stays resumable.

## Reference `autopilot-state.json` Schema

```json
{
  "workflow_file": "docs/ai/specs/SPEC-013-workflow.md",
  "updated_at": "2026-04-10T18:00:00Z",
  "active_step": "Phase 1: Specify",
  "plan": [
    {"step": "Archive Sweep: previously merged specs dry-run/apply eligibility", "status": "completed"},
    {"step": "Phase 0: Prerequisites", "status": "completed"},
    {"step": "Phase 1: Specify", "status": "in_progress"},
    {"step": "Phase 2: Clarify - UX Focus", "status": "pending"},
    {"step": "Phase 2: Clarify - UX Focus Consensus", "status": "pending"},
    {"step": "Phase 3: Plan", "status": "pending"},
    {"step": "Phase 4: Checklist - Pending domain discovery", "status": "pending"},
    {"step": "Phase 5: Tasks", "status": "pending"},
    {"step": "Phase 6: Analyze", "status": "pending"},
    {"step": "Phase 6: Analyze - Consensus", "status": "pending"},
    {"step": "Phase 6.5: Confidence Gate", "status": "pending"},
    {"step": "Phase 7: Implement - Pending task decomposition", "status": "pending"},
    {"step": "Post: Doctor Extension Check", "status": "pending"},
    {"step": "Post: Verify Implementation", "status": "pending"},
    {"step": "Post: Verify Tasks Phantom Check", "status": "pending"},
    {"step": "Post: Code Review", "status": "pending"},
    {"step": "Post: Integration Suite", "status": "pending"},
    {"step": "Post: Reviewability Diff Gate", "status": "pending"},
    {"step": "Post: UAT Runbook Generation", "status": "pending"},
    {"step": "Post: Final Reviewability Backstop", "status": "pending"},
    {"step": "Post: PR Packet/Body Generation", "status": "pending"},
    {"step": "Post: PR Body Generation", "status": "pending"},
    {"step": "Post: PR Creation", "status": "pending"},
    {"step": "Post: Review Remediation", "status": "pending"},
    {"step": "Post: Retrospective", "status": "pending"}
  ]
}
```

After Phase 6.5 starts, the same top-level object also carries
`autonomy_boundary`: the portable `autonomy-boundary-receipt.v1` public
receipt. The complete `autonomy-boundary.v1` record it is projected from stays
private at `<git-common-dir>/speckit-pro/autonomy-boundary/<run-id>.json`
(see [Phase Execution](./phase-execution.md#autonomy-boundary-preflight)).
Both shapes are in
[`autonomy-boundary.schema.json`](../contracts/autonomy-boundary.schema.json).
Before Phase 7, `--rule status-evidence` validates the receipt's schema and
planning bytes, replays its execution-boundary digest against the current
`--current-*` values, and checks each action's boundary binding,
authorization scope, and disposition consistency. It also reads the private
file named by the state's `execution_control.run_id` and fails unless its
canonical digest equals `private_record_sha256`:

```json
{
  "autonomy_boundary": {
    "schema_version": "autonomy-boundary-receipt.v1",
    "status": "ready",
    "planning_fingerprints": {
      "plan_md": {
        "path": "docs/ai/specs/SPEC-013/plan.md",
        "sha256": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "size_bytes": 4096
      },
      "tasks_md": {
        "path": "docs/ai/specs/SPEC-013/tasks.md",
        "sha256": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "size_bytes": 8192
      }
    },
    "execution_boundary": {
      "execution_environment": "local",
      "sandbox_mode": "workspace-write",
      "approval_reviewer": "auto_review",
      "sha256": "sha256:08060a2bdcd7ff0f4b22702a3648f47fb9ba3a8d84d7d6f9aab7f970f50c6b16"
    },
    "actions": [
      {
        "action_id": "install-runtime",
        "category": "privileged_command",
        "execution_boundary_sha256": "sha256:08060a2bdcd7ff0f4b22702a3648f47fb9ba3a8d84d7d6f9aab7f970f50c6b16",
        "scope_sha256": "sha256:d5c9445477f5b8bad43850f80d0c784a72c19aeea27c62075360f7dce9db71cf",
        "disposition": "ready",
        "authorization": {
          "status": "explicit_user",
          "scope_sha256": "sha256:d5c9445477f5b8bad43850f80d0c784a72c19aeea27c62075360f7dce9db71cf"
        }
      }
    ],
    "private_record_sha256": "sha256:130abe30df3dcf9efc3c8d95d0587445be550e8f42a2621a002f12d8467d6e83"
  }
}
```

The private file behind that receipt holds the complete v1 object under the
`autonomy_boundary` key below, without the key. That object's canonical JSON
digest is the receipt's `private_record_sha256`:

```json
{
  "autonomy_boundary": {
    "schema_version": "autonomy-boundary.v1",
    "status": "ready",
    "planning_fingerprints": {
      "plan_md": {
        "path": "docs/ai/specs/SPEC-013/plan.md",
        "sha256": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "size_bytes": 4096
      },
      "tasks_md": {
        "path": "docs/ai/specs/SPEC-013/tasks.md",
        "sha256": "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "size_bytes": 8192
      }
    },
    "execution_boundary": {
      "execution_environment": "local",
      "sandbox_mode": "workspace-write",
      "approval_reviewer": "auto_review",
      "writable_roots": ["/workspace"],
      "summary": "Repository writes are direct; system writes require approval.",
      "sha256": "sha256:08060a2bdcd7ff0f4b22702a3648f47fb9ba3a8d84d7d6f9aab7f970f50c6b16"
    },
    "actions": [
      {
        "action_id": "install-runtime",
        "category": "privileged_command",
        "command_or_tool": "sudo install reviewed payload",
        "target": "/opt/redline",
        "effect": "persistent system-wide runtime installation",
        "execution_boundary_sha256": "sha256:08060a2bdcd7ff0f4b22702a3648f47fb9ba3a8d84d7d6f9aab7f970f50c6b16",
        "scope_sha256": "sha256:d5c9445477f5b8bad43850f80d0c784a72c19aeea27c62075360f7dce9db71cf",
        "disposition": "ready",
        "authorization": {
          "status": "explicit_user",
          "evidence": "user approved the exact target and lasting effect",
          "scope_sha256": "sha256:d5c9445477f5b8bad43850f80d0c784a72c19aeea27c62075360f7dce9db71cf"
        }
      }
    ]
  }
}
```
