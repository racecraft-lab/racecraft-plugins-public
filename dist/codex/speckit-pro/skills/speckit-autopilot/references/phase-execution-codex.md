# Phase Execution for Codex

Codex autopilot orchestration runs in the parent session. Phase work runs in
installed custom subagents through `spawn_agent` and `wait_agent`.

## Contents

- [Canonical Order](#canonical-order) — `PHASES = [...]` + `--from-phase` semantics
- [Agent Mapping](#agent-mapping) — per-phase executor + prompt prefix table
- [Main Execution Loop](#main-execution-loop) — full 11-step per-phase pseudocode
- [Phase 3: Plan — Reviewability Budget](#phase-3-plan--reviewability-budget-advisory) — advisory plan-phase production-LOC estimate
- [Phase 7: Implement](#phase-7-implement) — task decomposition + placeholder replacement + reviewability gate
- [PR Body Generation](#pr-body-generation) — script invocation order pre-PR
- [Coverage Audit](#coverage-audit) — all-phase prefix audit run before/during/on-resume

## Canonical Order

```text
PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]
```

`--from-phase` changes the first phase to execute, not the required plan
coverage. `update_plan` and `autopilot-state.json` must still contain Phase 0,
all seven SDD phases, and Post before any subagent is spawned.

## Agent Mapping

| Phase | Agent | Prompt prefix |
| ----- | ----- | ------------- |
| Specify | `phase-executor` | `Run $speckit-specify with:` |
| Clarify | `clarify-executor` | `Prepare a Clarify Question Set for:` |
| Plan | `phase-executor` | `Run $speckit-plan with:` |
| Checklist | `checklist-executor` | `Run $speckit-checklist with:` |
| Tasks | `phase-executor` | `Run $speckit-tasks with:` |
| Analyze | `analyze-executor` | `Run $speckit-analyze with:` |
| Implement | `implement-executor` or project implementation agent | Task-specific TDD prompt |

Consensus uses `codebase-analyst`, `spec-context-analyst`, and
`domain-researcher`. `autopilot-fast-helper` is optional and never votes.

## Main Execution Loop

For each pending phase, spawn a subagent, collect the result, validate the
gate, and advance.

```text
for phase in PHASES starting from first_pending:
    0. Re-run the all-phase coverage audit against update_plan and
       autopilot-state.json. If Archive Sweep or any canonical phase family
       is missing, STOP and repair the plan before executing this phase.
    1. update_plan: mark the current phase item as "in_progress"
       and mirror the same status change into autopilot-state.json
    2. Check .specify/extensions.yml for before_<phase> hooks
       → run accepted hooks (non-destructive), skip duplicates
    3. Read the workflow file's prompt(s) for this phase
    4. For EACH prompt in the phase:
       a. Resolve <executor>:
          use the matching installed SpecKit custom agent
       b. spawn_agent the resolved <executor>:
          "Run $speckit-<phase> with: <prompt>"
       c. wait_agent for the summary, then close_agent the executor once its
          summary is recorded — frees its concurrent-thread slot; never leave
          a finished executor open
       d. update_plan: mark this prompt's item as "completed"
       e. Write the same transition to autopilot-state.json
    5. Run consensus in main session if needed:
       Parse executor's "Unresolved for consensus" section.
       For each item → spawn the category-routed analysts (codebase-analyst,
       spec-context-analyst, domain-researcher) per Rule 7 via
       spawn_agent → wait_agent → close_agent each, holding no more than
       agents.max_threads (default 6) open at once (dispatch in waves when
       items × analysts exceeds the cap) → apply consensus rules → edit
       artifacts → mark the corresponding Consensus item complete in both stores
    6. Check .specify/extensions.yml for after_<phase> hooks
       → run accepted hooks (non-destructive), skip duplicates
    7. Validate gate directly in the main session:
       Run '<SKILL_SCRIPTS>/validate-gate.sh' for gate G<N>
       against <feature_dir> from the orchestrator using the
       resolved scripts path for this skill.
       Parse the script output for PASS/FAIL status.
    8. If gate fails:
       a. Attempt auto-fix (max 2 attempts)
       b. If still failing and gate-failure == "stop": STOP
       c. If gate-failure == "skip-and-log": log, continue
    9. Update workflow file with results and print the current checklist summary
   10. If auto-commit == "per-phase":
       For phases 1–6: run: git add specs/ && git commit
       For phase 7 (implement): run: git add -A && git commit
       (implementation changes include src/, tests/, etc.)
   11. Advance to next phase (next iteration of loop) and write the new
       in_progress item to both update_plan and autopilot-state.json.
       Never mark the run complete while a later phase family still has
       pending items.
```

After all 7 phases complete, proceed to the post-implementation parallel
group (see [post-implementation-codex.md](./post-implementation-codex.md)).

## Static Tier-2 Relocation Suggestion

During pre-flight, the parent may inspect the active workflow target and nearby
legacy spec candidates for Tier-2 PROCESS relocation. This is static
inspection/reporting only. It does not run
`relocate-process-artifacts.sh`.

Suggest relocation only for thawed in-scope legacy specs with relocatable
PROCESS artifacts. For each eligible spec, print:

```text
speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --dry-run --spec specs/<spec-dir> --repo-root .
speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh --apply --spec specs/<spec-dir> --repo-root .
```

The `--apply` line is an operator follow-up after reviewing dry-run output and
cleaning the worktree. The parent must suppress the suggestion for
`frozen/in-flight`, invalid active-feature, already-current, already-normalized,
no-candidate, `non_speckit_namespace`, and `date_named_legacy_namespace`
cases. Record any surfaced suggestion or suppression note in the workflow log
before Phase 1 continues.

## Phase 3: Plan — Reviewability Budget (advisory)

After the Plan phase executor returns and `plan.md` exists (G3 pass), run the
standalone plan-phase estimator to project each slice's production-LOC footprint
from `plan.md`'s declared file structure. This is preventive sizing — it catches
an oversized slice at plan time, before any code is written. It is **advisory
only**: no outcome blocks, prompts mid-autonomous-run, or aborts the run (hard
blocking / re-slicing is PRSG-010, explicitly out of scope here).

Invoke the estimator from the parent session with `exec_command` and **capture
the exit code** rather than letting a non-zero exit propagate and abort the run:

```text
plan = "specs/<feature>/plan.md"
exec_command: bash -c 'code=0; out=$("<SKILL_SCRIPTS>/estimate-reviewable-loc.sh" "$1") || code=$?; printf "%s\n" "$out"; exit "$code"' _ "$plan"
```

The three budget statuses (`pass`, `over_budget`, `not_estimated`) all return
exit 0 with the verdict in the JSON `status` field; a non-zero exit (exit 2:
usage error or an absent/unreadable `plan.md`) is the only error path. Branch on
the JSON `status` when the exit code is 0, and on the exit code otherwise:

- **`pass`** → record "within budget" in the workflow/plan record and
  `autopilot-state.json` (silent — no prompt, no block).
- **`over_budget`, autonomous run** → record an over-budget note in the
  workflow/plan record and **CONTINUE** (advisory, non-blocking — FR-004,
  SC-002). Never block the run or trigger re-slicing.
- **`over_budget`, interactive use** → surface the over-budget result to the
  human as a decision (FR-005).
- **`not_estimated`** (`projected: null` — `plan.md` has no parseable declared
  production-file structure) → record "not estimated (no declared production
  files)" and continue. Never treat this as a within-budget pass.
- **non-zero exit** (exit 2) → record "estimator could not run (exit N)" and
  continue the autonomous run.

This mirrors the Codex gate-handling pattern (the G6.5 confidence-gate step reads
the script's exit code and branches on it rather than aborting).
Advisory-and-never-crash is the invariant for every outcome — under-budget,
over-budget, unmeasured, or errored — none may block, prompt
mid-autonomous-run, or crash the run. The estimator does not yet exist on older
plugin builds; when the script is absent the captured non-zero exit is recorded
as the error note and the run continues, same as any other error path.

## Phase-Gate: Spec-MOC Navigation Regeneration

At **every phase boundary** — for all seven phases — regenerate the spec map
navigation zones and fold any change into that phase's existing checkpoint
commit. This runs as an **idempotent** step **immediately before step 10's
commit** in the Main Execution Loop above (`git add specs/ && git commit` for
phases 1–6, `git add -A && git commit` for phase 7), so the rebuilt maps are
swept into that same commit. A boundary that changes nothing contributes
nothing — no extra `update_plan` item and no `autopilot-state.json` transition
are recorded for this step.

**Why before step 10:** step 10's `git add … && git commit` is what folds the
rebuilt maps into the one checkpoint commit. Running the rebuild *after* the
commit would force a second commit on every map-affecting boundary — the
failure this ordering avoids.

**Step (run at each boundary, before step 10):**

```bash
# Write mode (NO --check): regenerate over the autopilot's target repo.
# Pass "$PWD" explicitly — do NOT rely on the generator's default REPO_ROOT.
# In a cached-plugin run the default resolves to the plugin cache's parent, not
# the user's project, so the explicit arg is required (same path-prefix +
# "$PWD" convention as generate-pr-body.sh below).
skills/speckit-autopilot/scripts/generate-spec-index.sh "$PWD"
```

**Act on the result:**

- **Exit 2 (error)** → a map is malformed/unbalanced or a PRS manifest is
  unreadable. **Surface the actionable stderr line and STOP.** Do NOT commit a
  broken regen and do NOT advance the phase.
- **Exit 0 (clean)** → the generator wrote any stale maps and returned success.
  **The commit decision is diff-driven, not exit-code-driven** (write mode
  returns `0` whether or not it changed a file; the stale `exit 1` is
  `--check`-only and is never reached here). Inspect the working tree:
  - `git diff` (plus `git status` for newly-injected zones) is **empty** →
    nothing was regenerated. This is the idempotent no-op: contribute nothing,
    proceed to step 10's normal commit.
  - `git diff` is **non-empty** and the rebuild rides **alongside** other
    staged phase work → it is folded into that phase's existing checkpoint
    commit (`feat(SPEC-XXX): complete <phase> phase` / `feat(SPEC-XXX):
    implement phase`). No separate commit is made.
  - `git diff` is **non-empty** and the regenerated maps are the **only**
    staged change → make a standalone commit with this fixed, public-readable
    subject:

    ```text
    docs(speckit-pro): regenerate spec-MOC navigation zones
    ```

This subject is a fixed constant (it is NOT computed per run): `docs:` because
regenerating generated documentation zones is a docs-scope change and does not
trigger a release-please version bump. The regeneration is a pure function of
committed files, so re-running it on an unchanged tree yields a zero-byte diff
and no commit — exactly one rebuild contribution to the checkpoint commit on a
map-affecting boundary, and none on a no-op boundary.

## Phase 6.5: Pre-Implement Confidence Gate

After Phase 6 (Analyze) commits and before Phase 7 begins, run the optional
Pre-Implement Confidence Gate (G6.5). The synthesizer's final emit on the
workflow file (see [consensus-protocol.md §Pre-Implement Confidence Emit](consensus-protocol.md#pre-implement-confidence-emit-end-of-phase-6-analyze))
provides the data; the gate script reads it and decides whether to proceed,
surface a remediation hint, or stop.

```text
1. Read mode from `CONFIDENCE_GATE_MODE` (set at Step 0.6b in
   the autopilot SKILL.md by `resolve-confidence-mode.sh`). The
   resolver runs once at autopilot start so `--strict --advisory`
   conflicts and unknown values fail fast before any phase work
   begins, instead of surfacing 6 phases in.

2. Resolve threshold (`confidence_threshold: 0.90`). Default: 0.90.

3. On entry, print the /goal tip:
   - Codex interactive mode: "Tip: run `/goal achieve confidence ≥<T> on
     the pre-Implement gate` to get the goal-mode iteration."
     (Requires `features.goals = true` in `~/.codex/config.toml`.)
   - Codex `codex exec` headless: "/goal is not first-class in headless
     mode per openai/codex#21764 — the 3-iteration cap is your safety
     bound."

4. Run the gate:
     bash '<SKILL_SCRIPTS>/confidence-gate.sh' \
       <workflow-file> --threshold <T> --mode <M>

5. Parse exit code + JSON:
   - exit 0 (PASS): update_plan G6.5 → completed. Advance to Phase 7.
   - exit 1 (NO_DATA): log a warning, treat as plugin regression to
     report. update_plan G6.5 → completed with `no_data: true`.
     Advance to Phase 7.
   - exit 2 (FAIL):
       a. Read JSON `criteria` object; find the lowest-scoring criterion.
       b. If iteration_count < 3:
            - spawn_agent on the appropriate analyst for the lowest
              criterion (e.g., "task_understanding" lowest →
              clarify-executor re-pass on spec.md; "risk_assessment"
              → analyze-executor re-pass on open findings;
              "completeness" → verify artifact presence).
            - spawn_agent consensus-synthesizer to re-emit the
              pre-Implement Confidence block to the workflow file.
            - Re-run confidence-gate.sh.
            - Increment iteration_count.
       c. After max iterations OR exit 0:
            - mode=advisory: log + advance to Phase 7.
            - mode=strict: STOP. Operator may resume with
              --from-phase implement if they accept the lower score.
```

The iteration cap of 3 is the only safety bound in Codex `codex exec`
headless mode. In Codex interactive TUI with `features.goals = true`,
an operator-set `/goal` provides an additional turn-based check
layered on top of the cap.

**Why this gate is opt-in for blocking:** Clarify (G2) and Analyze
(G6) already filter most pre-Implement shakiness. Advisory mode
surfaces the score and a remediation hint without blocking; strict
opt-in via local config for operators who want a fail-closed posture.

**update_plan**: at autopilot start, after the G6 task, create a
G6.5 task `Confidence gate (pre-Implement)`. Transition through
`in_progress` → `completed` regardless of advisory vs strict outcome
(strict only differs in whether Phase 7 runs).

## Phase 7: Implement

Before `tasks.md` exists, the plan contains:

```text
Phase 7: Implement - Pending task decomposition
```

After Tasks completes, replace that placeholder with concrete task-group items
from `tasks.md`. Each implement item must include the task IDs, dependencies,
TDD protocol, `PROJECT_COMMANDS`, and `COMPLETED_TASKS` context accumulated from
earlier work.

After G5 passes, the placeholder is invalid. Before Analyze or Implement can
run, audit `update_plan` and `autopilot-state.json`, then run the
reviewability task gate:

```text
skills/speckit-autopilot/scripts/reviewability-gate.sh tasks specs/<feature>
```

If the gate returns `block` without a ratified split exception, stop before
implementation and split the spec.

- no `Phase 7: Implement - Pending task decomposition` item remains
- one or more concrete `Phase 7:` items exist
- each concrete item names one or more task IDs parsed from `tasks.md`

If any check fails, repair both state stores and print the corrected checklist
summary before continuing.

Use `implement-executor` for test and implementation tasks unless Step 0.11
found a more specific project implementation agent. The parent session dispatches
all workers directly; subagents do not spawn nested agents.

## PR Body Generation

Before creating or updating a PR after G7, the parent session runs:

```text
skills/speckit-autopilot/scripts/final-reviewability-backstop.sh --feature-dir specs/<feature> --feature-branch <branch> --diff-range origin/main...HEAD --state-output specs/<feature>/.process/final-reviewability/gate-state.json --packet-output specs/<feature>/.process/final-reviewability/reslicing-packet.json ...
skills/speckit-autopilot/scripts/generate-pr-body.sh "$PWD" specs/<feature> .git/speckit-pr-body.md origin/main...HEAD
```

Run `generate-pr-body.sh` only after the final backstop exits 0. Exit 1 is
`reslicing_required`: do not generate a PR body, invoke any `gh pr create`
variant, or run `multi-pr-emission.sh`; read the packet's `operator_steps` and
resume from the named PRSG-007/008/009 phase. Exit 2 is a gate error: state is
written, no packet is valid, and the run stops for operator repair.

`generate-pr-body.sh` uses the host repository's pull request template if it
exists, preserves unknown host-required sections, appends missing review-packet
sections, and falls back to the bundled template when the host has none. Use
`gh pr create --body-file .git/speckit-pr-body.md`, not an inline placeholder.

## Coverage Audit

Run the all-phase coverage audit before Phase 1, after every phase transition,
and on resume. If any of these prefixes is absent from either durable state
store, repair the plan before continuing:

```text
Phase 0:
Phase 1:
Phase 2:
Phase 3:
Phase 4:
Phase 5:
Phase 6:
Phase 7:
Post:
```
