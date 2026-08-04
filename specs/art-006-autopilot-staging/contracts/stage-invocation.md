# Contract: Stage Invocation and `resolve-autopilot-stage`

The `--stage` argument is a public invocation surface consumed by six downstream
specifications and mirrored across two distributions whose argv contracts have
already silently diverged. Nothing in CI diffs the two `SKILL.md` bodies, so
anything specified only in prose is unverifiable. This document is the single
statement of the surface; both distributions restate the argv line and nothing
else.

## 1. Argv surface — identical on both distributions

### Claude Code

```text
/speckit-pro:speckit-autopilot path/to/workflow-file.md
    [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement]
    [--spec SPEC-ID]
    [--stage plan|implement|full]
    [--strict | --advisory]
```

Current line: `speckit-pro/skills/speckit-autopilot/SKILL.md:293`. Two additions:
`--stage`, and the `[--strict | --advisory]` pair the Codex synopsis already
advertises. The second is a stale-documentation repair, not new capability — the
Claude side already resolves those flags from the invocation argv at
`SKILL.md:327-336` — and it changes no gate behaviour (FR-002).

The leading `/speckit-pro:speckit-autopilot` token is **not** a third addition to
that line. Each distribution's `## Input` block documents the argv the skill
*receives*, which on both sides begins at the workflow path; the command token
shown here is the user-facing Claude invocation, and it is what the scaffold-chain
contract's invocation table shows for the same reason. Parity is over the flag
set, its values, and its precedence — never over the leading token, which has no
Codex counterpart.

### Codex CLI

```text
path/to/workflow-file.md
    [--from-phase specify|clarify|plan|checklist|tasks|analyze|implement]
    [--spec SPEC-ID]
    [--strict | --advisory]
    [--stage plan|implement|full]
```

Current line: `speckit-pro/codex-skills/speckit-autopilot/SKILL.md:544`. One
addition. Argument order in the synopsis is presentation only; the resolver reads
argv by name, not by position.

### Stage vocabulary

Normatively stated once, in [data-model.md §Stage](../data-model.md#stage):
exactly `plan`, `implement`, `full` — literal lowercase, no aliases, no alternate
casing, no long-form spellings. Every other appearance is a readability copy, not
a second source of truth — the two synopsis blocks above, the two rejection
messages below, and the scaffold-chain restatement. No copy is per-platform in
meaning: the two synopses carry the same value set by construction, and neither
distribution owns a vocabulary the other does not.

The copies are held to the source by **execution, not review**. The FR-015a unit
test covers every rejection case (plan.md §6), and those messages enumerate the
accepted values; the status-evidence validator separately asserts that any
recorded `Stage` row is one of the three literals. A token added to the source and
not to a copy therefore fails a test rather than shipping as documentation drift —
which matters because nothing in CI diffs the two skill bodies.

## 2. Precedence

| Rank | Source | Notes |
|---|---|---|
| 1 | explicit `--stage <token>` | Always wins, including when it disagrees with what auto-detection would have chosen. |
| 2 | auto-detection from the workflow file's `## Workflow Overview` table | Every row in the FR-006a predicate set terminal → `implement`; otherwise `plan`. |

The predicate set is the six planning rows plus `Confidence Gate`. An absent
`Confidence Gate` row does not block; a present non-terminal one does (FR-006a).

`--from-phase` is **not** a competing source of the stage. It moves the starting
point *within* the resolved stage and never widens or narrows the range
(spec.md:134-136). This preserves the string-pinned Codex sentence
"`--from-phase` changes only the starting index"
(`tests/speckit-pro/layer1-structural/validate-codex-skills.py:295`), which must
survive verbatim.

The absence of a `Stage` entry in the workflow file means "no run yet". It is not
a fourth value, it is not an error, and it resolves through rank 2.

## 3. Runner operation

**Operation identifier**: `resolve-autopilot-stage`
**Mode**: `read_only`
**Registered at**: `speckit-pro/speckit_pro_runner/helpers/registry.py`, beside
`resolve-confidence-mode` (`:171-178`)
**Implemented at**: `speckit-pro/speckit_pro_runner/helpers/read_only.py`, beside
`resolve_confidence_mode` (`:1081-1096`)

Both distributions reach it by operation identifier at opening preparation — the
Claude side at a new Step 0.6c after the 0.6b confidence-mode resolver
(`skills/speckit-autopilot/SKILL.md:327-336`), the Codex side at a matching
Step 0.6c bullet beside its own 0.6b, which lives in the skill body's pre-flight
summary at `codex-skills/speckit-autopilot/SKILL.md:570-578`.

The Codex step is **not** sited in `references/phase-execution-codex.md`. That
document opens at the main execution loop and carries no opening-preparation
section, so a rejection sited there would run *after* phase work began and could
not satisfy FR-007's "before any phase work" or SC-005's no-partial-output
guarantee. This is the one place stage prose must enter the word-capped Codex
body rather than an uncapped reference; at roughly thirty words it is well inside
the headroom FR-013 protects, and it is additive, so no pinned sentence moves.

### Request

```json
{
  "schema_version": "1.0",
  "helper_id": "resolve-autopilot-stage",
  "operation": "resolve-autopilot-stage",
  "mode": "read_only",
  "inputs": {
    "workflow_file": "docs/ai/specs/.process/ART-006-workflow.md",
    "autopilot_args": ["--stage", "plan", "docs/ai/specs/.process/ART-006-workflow.md"]
  }
}
```

| Input | Type | Required | Meaning |
|---|---|---|---|
| `workflow_file` | string, repo-relative | yes | The workflow file. Path-canonicalised like every other path input; must stay inside the repo/plugin trust boundary (`read_only.py:281-292`). |
| `autopilot_args` | array of strings | no | The invocation argv. Must be an array of strings or the operation returns an invalid-arguments diagnostic, matching `resolve-confidence-mode` (`read_only.py:337-339`). Omitted or empty means "no explicit stage". |

### Response — exit 0

Structured JSON on stdout. Multi-field output, so JSON rather than the bare token
`resolve-confidence-mode` returns; constitution §VI requires a structured parser.

```json
{
  "tool": "resolve-autopilot-stage",
  "stage": "plan",
  "source": "argv",
  "basis": "explicit --stage plan",
  "recorded_stage": null,
  "planning_complete": false,
  "confidence_gate_status": null,
  "from_phase": null
}
```

| Field | Type | Meaning |
|---|---|---|
| `stage` | `"plan" \| "implement" \| "full"` | The resolved stage. |
| `source` | `"argv" \| "auto-detect"` | Which precedence rank decided. |
| `basis` | string | Plain-English reason the orchestrator prints before phase work begins, satisfying FR-006's report requirement. For auto-detection it names the first non-terminal planning phase and its status. |
| `recorded_stage` | Stage token or `null` | The workflow file's `Stage` row as read. `null` means the row is absent — "no run yet", never an error. |
| `planning_complete` | boolean | Whether every row in the FR-006a predicate set — the six planning rows plus `Confidence Gate` — is terminal. The auto-detection input, surfaced so the guard and the tests can assert on it without re-parsing. |
| `confidence_gate_status` | status string or `null` | The `Confidence Gate` row as read; `null` when the row is absent. This is the recorded verdict an implementation-stage run reads instead of re-running the gate (FR-010a). |
| `from_phase` | phase name or `null` | The `--from-phase` value, echoed after range validation. |

### Response — exit 2, pre-flight rejection

One-line diagnostic on stderr, following `resolve_confidence_mode`'s shape at
`read_only.py:1085`. The autopilot STOPs before Phase 0 on this exit code, the
same way it already does for `--strict --advisory` (`SKILL.md:331-333`).

| Condition | Message |
|---|---|
| Unrecognised value | `error: unrecognized stage 'planning' — accepted values: plan, implement, full` |
| `--stage` repeated with differing values | `error: --stage given more than once with different values: plan, implement` |
| `--from-phase` outside the named stage's range | `error: --stage plan and --from-phase implement are mutually exclusive` |
| `--stage` present with no value | `error: --stage requires a value — accepted values: plan, implement, full` |

Rejection happens during opening preparation, before any phase work, so a
rejected run leaves no partial phase output (SC-005). `--from-phase` naming a
phase *inside* the resolved stage's range is accepted and is not a conflict.

**The range conflict is tested only against an explicitly named stage** (FR-007).
When the stage was auto-detected, `--from-phase` never conflicts with it. The
reason is concrete: after a strict-mode gate stop, auto-detection resolves `plan`
because the `Confidence Gate` row is non-terminal, and the shipped stop guidance
tells the operator to resume at the implementation phase. Testing the conflict
against the auto-detected stage would reject exactly that documented resume and
strand the operator at the only boundary the argument exists to cross. An
operator who means to cross states it — `--stage implement` — and gets the FR-010a
diagnostic naming the refused verdict they are proceeding past.

That shipped stop guidance currently names `--from-phase implement`. Because this
change makes `--stage implement` the direct way to express the same intent, the
guidance is updated to name the stage argument; the `--from-phase` form keeps
working under the rule above, so no operator following older guidance is stranded.

### Exit codes

Two layers reject, and conflating them is how the golden fixtures would be
written against the wrong surface. The runner validates the *request* before the
operation runs and returns a **diagnostic envelope, not an exit code**: a
malformed `autopilot_args` yields `invalid_input` and a path outside the trust
boundary yields `unsupported_path` (`read_only.py:392-399`, `:275-291`).
`unsupported_path` is not an exit code at all — it has no entry in the runner's
exit-code map. Only the operation's own rejections below are exit codes.

| Code | Meaning |
|---|---|
| 0 | Resolved. Envelope on stdout. |
| 2 | Input error — invalid or conflicting stage arguments, a workflow file that cannot be read, or a `## Workflow Overview` table that cannot be parsed. |

Exit 1 is not used: there is no "expected failure" for this operation. Exit 2 is
the only non-zero code, and the runner already maps it to `invalid_input`
(`read_only.py:42-47`), so this operation introduces no new diagnostic code.

Two cases that look alike are deliberately split, because collapsing them is how
this operation would produce the flagship silent failure:

- A **readable** workflow file carrying **no `Stage` row** is not a failure. It
  degrades to `recorded_stage: null` and resolves through auto-detection (FR-008a).
  This is the common case — nearly every workflow file in the tree predates the
  entry.
- A workflow file that **cannot be read**, or whose status table **cannot be
  parsed**, is exit 2. Auto-detection has no input in that case, and every
  degraded default resolves the planning stage — which would re-run finished work
  whenever the file is merely transiently unreadable. Rejecting is the only answer
  that cannot be silently wrong (FR-007). The at-rest validator already treats an
  unparseable overview table as its own violation class rather than as an empty
  table, so this operation matches a distinction the suite already draws.

## 4. Reporting obligation

Before phase work begins, the orchestrator prints the resolved stage and its
basis (FR-006). On an implementation-stage invocation that accepts a
confidence-mode flag, it additionally emits the FR-010a diagnostic stating that
the confidence gate is not run in this stage and that the recorded verdict is
read instead — so an accepted flag never silently does nothing.

## 5. Parity obligation

Parity is asserted by execution, not by prose comparison. The new unit test at
`tests/speckit-pro/unit/test-autopilot-stage-resolution.py` feeds both
distributions' documented argv forms through the one operation and asserts
identical resolution across the full fixture set (FR-015a, SC-007).

The assertion does **not** go in
`tests/speckit-pro/layer1-structural/validate-codex-parity.py`: its checks are
existence-only by design, its counted baseline would need regenerating, and this
specification's own record already names it as unable to catch this class of
divergence (spec.md:335-340).
