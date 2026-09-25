# SpecKit Pro Harness Engineering Uplift Implementation Roadmap

**Repair observed harness defects, make workflow state typed and replayable,
cut the tokens autonomous runs spend finding things, and verify that work is
actually complete, on both hosts, without granting any new authority.**

This document defines the **SPEC catalog** for the harness-engineering uplift:
an ordered set of specifications derived from the source PRD. Each SPEC maps
1:1 to a Feature / Acceptance-Criteria group in the PRD (`AC-N.*`), preserving
traceability from PRD -> roadmap -> spec. Each specification is prepared for
autopilot with `/speckit-pro:speckit-scaffold-spec HRNS-###`, which reads this
roadmap as its input.

**Source PRD:** [../../prd-harness-engineering-uplift.md](../../prd-harness-engineering-uplift.md)
**Roadmap MOC:** [harness-engineering-uplift-roadmap-MOC.md](harness-engineering-uplift-roadmap-MOC.md)
**Typed-judgment catalog:** [harness-engineering-uplift-jev-catalog.md](harness-engineering-uplift-jev-catalog.md)
**Spec ID prefix:** `HRNS-###`
**Status:** Active. HRNS-001 is complete and archived. HRNS-002 to HRNS-014
are retired. HRNS-015 is in progress. HRNS-017 to HRNS-023 are ready. On 2026-09-24 this
roadmap absorbed the Continuous Goal Verification roadmap, whose `VRFY-###`
identifiers are retired unscaffolded.

---

## Roadmap Overview

The active catalog holds **24 specifications** across **7 dependency tiers**.
HRNS-001 is complete, and HRNS-002 to HRNS-014 are retired with their
surviving criteria moved into the specs below.

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | HRNS-015, HRNS-017, HRNS-018, HRNS-019, HRNS-020, HRNS-021, HRNS-022, HRNS-023 | Repair, host facts, typed state, registry contract, token baseline, guidance, eval ladder, drift scanner | Fully parallel; no dependencies |
| 2 | HRNS-016, HRNS-024, HRNS-026, HRNS-028, HRNS-029, HRNS-037 | Per-story autopilot, decision contract, permission policy, context economy, progress page | Parallel, each after its one Tier 1 predecessor |
| 3 | HRNS-025, HRNS-030 | Run journal and obligation registry | Parallel after HRNS-024 |
| 4 | HRNS-027 | Dual-host Jev adapter, the only slice that touches the wire | Sequential |
| 5 | HRNS-031, HRNS-032, HRNS-033, HRNS-034 | Three shadow pilots and the phase-boundary verifier | Parallel after HRNS-027 |
| 6 | HRNS-035 | Change-triggered scheduler | Sequential after HRNS-034 |
| 7 | HRNS-036, HRNS-038 | Stop advice and trajectory calibration | Parallel after HRNS-035 |

**Execution Order:** Tier 1 in any order, HRNS-015 first when capacity is
short -> Tier 2 as each predecessor lands -> HRNS-025 + HRNS-030 -> HRNS-027 ->
HRNS-031 + HRNS-032 + HRNS-033 + HRNS-034 -> HRNS-035 -> HRNS-036 + HRNS-038.

**Dependency Constraints:**

- HRNS-016 requires HRNS-015 because one PR per story repeats the packet
  release-note and untracked-packet failures on every story.
- HRNS-024 requires HRNS-017 because the contract binds to the result
  visibility and hook facts the spike observes on each host.
- HRNS-026 requires HRNS-019 because the command policy reads helper risk
  flags from the registry.
- HRNS-028 and HRNS-029 require HRNS-020 because their success is measured
  against the committed token baseline.
- HRNS-037 requires HRNS-018 because the page renders the typed record.
- HRNS-025 requires HRNS-019 and HRNS-024 because journal events carry helper
  identities and decision contract identities.
- HRNS-030 requires HRNS-018 and HRNS-024 because obligations live in the
  typed record and carry contract identities.
- HRNS-027 requires HRNS-017, HRNS-024, HRNS-025, and HRNS-026 because a
  journal admission failure must skip the call and every call passes the
  egress policy.
- HRNS-031, HRNS-032, and HRNS-033 each require only HRNS-027; they are
  consumers at existing handoffs and do not depend on each other.
- HRNS-034 requires HRNS-025, HRNS-027, and HRNS-030 because it reads frozen
  obligations, consumes adapter results, and records to the journal.
- HRNS-035 requires HRNS-034; HRNS-036 requires HRNS-035; HRNS-038 requires
  HRNS-025, the three pilots, and HRNS-035 because replay compares phase-end
  with change-triggered checking on stored journals.
- A spec with an optional Jev shadow check ships its deterministic core on the
  dependencies above. The Jev check is a later slice that waits for HRNS-027.

## Reviewability Contract

Every spec must fit a human review budget before setup and again before PR
creation. The size metric counts **production code only**; documentation,
tests, and config do not contribute to the reviewable-LOC count.

- Warn above 400 reviewable production LOC, 6 production files, or 15 total
  files. Touching more than one primary surface is also a warning, not a block.
- Block above 800 reviewable production LOC, 8 production files, or 25 total
  files, unless this roadmap records a typed exception pragma (below).
- A slice that adds only net-new files (no existing files modified) gets a 1.5x
  greenfield allowance on the production-LOC thresholds (warn 600, block 1200).
- Primary surfaces are schema/migration, API, UI, scheduler/runtime,
  harness/adapter, seed/config, and docs/process.
- A block-sized slice may be allowed only by a typed, auditable exception
  pragma on its own line, exactly: `Reviewability-Exception: <class>` where
  `<class>` is one of `refactor`, `infra`, or `upgrade`. The match is
  line-anchored and case-sensitive with no trailing content; an unknown class,
  a mis-cased class, or free-form prose is not honored (fail-closed).
- PR descriptions are review packets. They must include what changed, why,
  non-goals, review order, scope budget, traceability, verification evidence,
  known gaps, and rollback/flag notes.

Projected reviewable LOC below comes from the `estimate-spec-size` runner
operation run on 2026-09-24 with the size signals recorded in each entry. It
is a forward guess, not the authoritative count.

---

## Dependency Graph

```text
HRNS-015 Repair ─────────────────────► HRNS-016 Per-story autopilot
HRNS-017 Host spike ──► HRNS-024 Decision contract ─┬─► HRNS-025 Run journal ─┐
HRNS-018 Typed state ─┬─────────────────────────────┴─► HRNS-030 Obligations ─┤
                      └─► HRNS-037 Progress page                               │
HRNS-019 Registry ──► HRNS-026 Permission + egress ─┐                          │
                      (HRNS-019 also feeds HRNS-025)│                          │
                                                    ▼                          │
          HRNS-017 + HRNS-024 + HRNS-025 + HRNS-026 ─► HRNS-027 Jev adapter    │
                                                    │                          │
                     ┌──────────────┬───────────────┼───────────────┐          │
                     ▼              ▼               ▼               ▼          │
               HRNS-031       HRNS-032        HRNS-033        HRNS-034 ◄──────┘
               coverage       review-fix      claim support   verifier
                     │              │               │               │
                     │              │               │               ▼
                     │              │               │          HRNS-035 scheduler
                     │              │               │               │
                     │              │               │        ┌──────┴──────┐
                     │              │               │        ▼             ▼
                     └──────────────┴───────────────┴──► HRNS-038     HRNS-036
                                                         calibration  stop advice
HRNS-020 Token baseline ─┬─► HRNS-028 Shared retrieval packet
                         └─► HRNS-029 Visibility ladder + handoff
HRNS-021 Guidance, HRNS-022 Eval ladder, HRNS-023 Drift scanner: independent
```

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|---|---|---|---|---|
| HRNS-001 | Harness Surface Inventory and Gap Taxonomy | ✅ Complete / Archived | `.process/HRNS-001-workflow.md` | PR #357 merged |
| HRNS-002 | Progressive Context and Durable State Contract | Retired | - | Merged into HRNS-018 and HRNS-021 |
| HRNS-003 | Helper, Tool, and Capability Contract | Retired | - | Merged into HRNS-019 |
| HRNS-004 | Permission, Sandbox, and Pre-action Authorization Controls | Retired | - | Merged into HRNS-026 |
| HRNS-005 | Feedback Sensors and Eval Readiness Ladder | Retired | - | Merged into HRNS-022 |
| HRNS-006 | Trace, Debug, and Review Evidence Packets | Retired | - | Merged into HRNS-025 |
| HRNS-007 | Long-horizon Orchestration and Resumption Controls | Retired | - | Merged into HRNS-018, HRNS-026, HRNS-036 |
| HRNS-008 | Harness Drift, Garbage Collection, and Self-healing Remediation | Retired | - | Merged into HRNS-023 |
| HRNS-009 | Host Repository OKF Knowledge Contract and Initialization | Retired | - | Dropped |
| HRNS-010 | Incremental Evidence Ingest and Knowledge Synthesis | Retired | - | Dropped |
| HRNS-011 | Knowledge Query, Citation, and Compounding Capture | Retired | - | Dropped |
| HRNS-012 | Knowledge Conformance, Health, and Drift Maintenance | Retired | - | Dropped |
| HRNS-013 | Code-Intelligence and Vector-Index Interoperability | Retired | - | Dropped |
| HRNS-014 | External OKF Exchange and Reviewable Reconciliation | Retired | - | Dropped |
| HRNS-015 | Autopilot, Gate, and PR-Emission Repair | 🔄 In Progress | `.process/HRNS-015-workflow.md` | Specify |
| HRNS-016 | Per-story Autopilot Execution | ⏳ Pending | - | HRNS-015 |
| HRNS-017 | Host Capability Spike | ⏳ Ready | - | Specify |
| HRNS-018 | Typed Workflow State | ⏳ Ready | - | Specify |
| HRNS-019 | Helper Registry Contract and Tiered Disclosure | ⏳ Ready | - | Specify |
| HRNS-020 | Autopilot Token Baseline | ⏳ Ready | - | Specify |
| HRNS-021 | Condition-Bound Guidance and Lesson Promotion | ⏳ Ready | - | Specify |
| HRNS-022 | Eval Ladder and Model Refresh | ⏳ Ready | - | Specify |
| HRNS-023 | Harness Drift Scanner | ⏳ Ready | - | Specify |
| HRNS-024 | Shared Typed-Decision Contract | ⏳ Pending | - | HRNS-017 |
| HRNS-025 | Run Journal and PR Trace Summary | ⏳ Pending | - | HRNS-019, HRNS-024 |
| HRNS-026 | Autonomous-Run Permission and Egress Policy | ⏳ Pending | - | HRNS-019 |
| HRNS-027 | Dual-Host Jev Adapter | ⏳ Pending | - | HRNS-024, HRNS-025, HRNS-026 |
| HRNS-028 | Shared Retrieval Packet for Fan-Out Roles | ⏳ Pending | - | HRNS-020 |
| HRNS-029 | Visibility Ladder and Handoff Preservation | ⏳ Pending | - | HRNS-020 |
| HRNS-030 | Obligation and Subgoal Registry | ⏳ Pending | - | HRNS-018, HRNS-024 |
| HRNS-031 | Pilot: Requirement-to-Task Semantic Coverage | ⏳ Pending | - | HRNS-027 |
| HRNS-032 | Pilot: Review-Fix Closure Verification | ⏳ Pending | - | HRNS-027 |
| HRNS-033 | Pilot: Claim-to-Source Support Annotation | ⏳ Pending | - | HRNS-027 |
| HRNS-034 | Phase-Boundary Goal-Completion Verifier | ⏳ Pending | - | HRNS-025, HRNS-027, HRNS-030 |
| HRNS-035 | Change-Triggered Scheduler and Invalidation | ⏳ Pending | - | HRNS-034 |
| HRNS-036 | Premature-Stop and Redundant-Continuation Advice | ⏳ Pending | - | HRNS-035 |
| HRNS-037 | Live Run Progress Page | ⏳ Pending | - | HRNS-018 |
| HRNS-038 | Trajectory Calibration and Gated Live Evaluation | ⏳ Pending | - | HRNS-025, HRNS-031 to HRNS-033, HRNS-035 |

**Status Legend:** ⏳ Pending | ⏳ Ready | 🔄 In Progress | ✅ Complete | ⚠️ Blocked | Retired (identifier reserved, never reused)

---

## Specification Sections

### HRNS-001: Harness Surface Inventory and Gap Taxonomy

**Priority:** P1 | **Depends On:** none | **Enables:** the rest of this catalog

**Status:** ✅ Complete and archived (PR #357). The taxonomy at
[harness-engineering-uplift-gap-taxonomy.md](harness-engineering-uplift-gap-taxonomy.md)
is a 2026-07-15 snapshot; its surface counts are historical, and the
2026-09-24 completion audit that re-shaped this roadmap supersedes its
gap-to-spec mapping.

---

### HRNS-015: Autopilot, Gate, and PR-Emission Repair

**Priority:** P1 | **Depends On:** none | **Enables:** HRNS-016

**Goal:** Fix every open defect observed in live autopilot runs, each with a
failing-first fixture, so the documented happy path stops producing a failing
pull request or a silently wrong artifact.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 292 (estimate-spec-size: 3 story groups, 10 FRs, 9 files, modify) |
Production files: 9 |
Total files: 20 |
Budget result: over the 8-file block line as one PR; ships as three slices of at most four production files each

Two of the original eight defects are already repaired: the correct-but-halted
turn (#531, "Never Yield With Nothing In Flight") and the spec-index walk over
git-ignored files (#568). The rest were recorded while running ART-001 and
ART-007 (`docs/ai/specs/.process/ART-001-workflow.md`,
`docs/ai/specs/.process/ART-007-manual-uat.md`) or reported by operators
running this workflow on other repositories.

**Scope:**

- **Slice A, PR emission.**
  - The generated packet body cannot satisfy a host repository's release-note
    gate: `build_packet_body` emits eight fixed headings and no fence, while
    this repository requires one non-empty ` ```release-note ` fence on `feat`
    and `fix` bodies. Add a consumer-facing release-note field, or document and
    exercise the existing `inputs.body` override as the host-body hook.
  - `validate-pr-packet-write` apply mode refuses on a dirty worktree, and a
    freshly emitted packet is untracked in any repository that never commits
    packets. State which outcome is success for that case.
  - Carry the confidence-gate verdict into the generated body only if HRNS-025
    has not landed; otherwise leave it to HRNS-025.
- **Slice B, gates and counters.**
  - The gap counter matches `[Gap]` literally, so `[Gap, <ref>]` markers (the
    checklist skill's own example form) under-report.
  - The spec-index walk still selects untracked, non-ignored files, and no CI
    check runs the index against the real tree (`AGENTS.md` says "freshness:
    no PR check"). Add the exclusion and the real-tree check together.
  - Reviewability-gate setup mode checks only the last roadmap entry and
    ignores `Reviewability-Exception` (#637).
  - `estimate-spec-size` has no signal for required refactors, so a roadmap
    budget goes stale after the interview.
- **Slice C, workflow behavior.**
  - The Post list is not self-verifying, and its size is stated three ways (11
    on Claude, 13 on Codex, "12" in prose). State it once and add a
    deterministic check that refuses completion while any entry is pending.
  - Executors that keep the `Agent` tool can form teams with no teardown
    obligation; one teammate outlived its parent by about 1.75 hours.
  - `speckit-resolve-pr` must fetch every thread and comment page and must
    reply and resolve only after final verification and a confirmed pushed
    SHA. Re-verify current behavior first.
  - The scaffold blind-spot pass can expire its wait and silently skip; report
    the expiry as a finding. A detected quality-gate command must honor the
    host repository's documented test command rather than a raw default.
  - The roadmap template links workflow files where scaffold never writes them
    (#638).
  - Skills that tell the agent to call a runner helper must show the complete
    request envelope; `speckit-status` names `generate-spec-index-check`
    without one, which cost three failed calls in a live run.

**Out of Scope:**

- Redesigning the PR-packet schema or the post-implementation sequence.
- Changing any host repository's release-note policy; the gate is correct.
- Removing autopilot's wall-clock budgets, which #642 already did.

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` — changed: release-note field or body hook; untracked-packet outcome.
- `speckit-pro/speckit_pro_runner/helpers/read_only.py` — changed: `[Gap` matching; untracked-file exclusion; refactor signal for spec-size estimation.
- `speckit-pro/skills/speckit-autopilot/` and the Codex mirror — changed: self-verifying Post list; team teardown.
- `speckit-pro/skills/speckit-resolve-pr/SKILL.md` — changed: full pagination; verify, push, then reply and resolve.
- `speckit-pro/skills/speckit-scaffold-spec/SKILL.md`, the reviewability gate helper, and the roadmap template — changed: blind-spot expiry finding; #637; #638.
- `.github/workflows/pr-checks.yml` — changed: real-tree spec-index check.

**Key Files:**

- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` — `required_headings()`, `build_packet_body`, and the write-validation guard.
- `speckit-pro/speckit_pro_runner/helpers/mutation.py` — the `--untracked-files=all` dirty-worktree check.
- `speckit-pro/speckit_pro_runner/helpers/read_only.py` — the gap counter, the spec-index walk, and `estimate_spec_size`.
- `speckit-pro/skills/speckit-autopilot/SKILL.md` and `references/post-implementation.md` — the Post list and its audit prose.
- `speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md` — team formation.
- `tests/speckit-pro/layer1-structural/validate-spec-lifecycle-contracts.py` — the fixture-root spec-index contract.

**Done When:**

- A packet emitted by the documented path passes a host release-note gate,
  proven by a fixture, or the body hook is documented and exercised.
- The untracked-packet outcome is stated and covered by a fixture.
- A `[Gap, <ref>]` fixture counts correctly.
- The real-tree spec-index check fails on the pre-fix ART-007 `SPEC-MOC.md`
  and passes with an untracked file present.
- #637 and #638 each have a failing-first fixture.
- A fixture proves the Post sequence refuses completion with any entry
  pending, on both hosts, and one constant states the entry count.
- A structural check proves every executor that can form a team tears it down.
- `speckit-resolve-pr` pagination and ordering are covered by fixtures.

---

### HRNS-016: Per-story Autopilot Execution

**Priority:** P2 | **Depends On:** HRNS-015 (packet release-note and untracked-packet repairs), plus live `multi-pr-emission` apply | **Enables:** none

**Goal:** Make the user story the unit of autopilot execution, verification,
and review: Setup and Foundational once, then per story in priority order
implement, gates, hardener, architecture check, checkpoint, and pull request,
continuing while green and stopping on the first failing check.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 182 (estimate-spec-size: 3 stories, 6 FRs, 5 files, modify) |
Production files: 5 |
Total files: 12 |
Budget result: within budget

The "Quality Gauntlet" prerequisites are merged (#536, #537, #542). This entry
records the accepted direction; it goes through `speckit-scaffold-spec` and a
grill-me interview, where the design tree is walked branch by branch.

**Scope:**

- Phase 7 restructured around the story phases `tasks.md` already carries:
  Setup and Foundational run once, then each user story in the recorded
  priority order, never the next before the previous checkpoint is recorded.
- Per-story sequence: implement the story's tasks with the existing TDD
  executors; run the automated checks and every populated quality-gate slot
  with `{paths}` = the story's diff; run the hardener when MUTATION is
  populated; run an architecture check that compares the story's diff against
  the plan's Module and Interface Deltas and the `DEPENDENCY_RULES` slot;
  record the checkpoint with the story's `**Independent Test**` and evidence
  paths.
- One pull request per story. With `gh-stack` installed, the spec is one stack
  rooted on trunk with one layer per story; otherwise each story is an
  independent branch. The selected mode and reason are recorded before the
  first story PR.
- Stop rule: continue while every check is green; stop on the first failing
  check, naming the story, the check, and the evidence path. Resume from the
  last recorded checkpoint.
- Review overhead is accepted and stated in each PR body. Batching small
  stories or auto-merging green layers is a recorded follow-on.
- Both distributions run the same loop, checkpoint record, PR-per-story rule,
  and stop rule.

**Out of Scope:**

- Changing how `spec.md` defines stories or how `tasks.md` groups them.
- Reducing review overhead by batching or auto-merge (follow-on).
- Changing the gate slots, thresholds file, or hardener; this spec calls them
  per story instead of once per spec.

**Module and Interface Deltas:**

- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` and the Codex mirror — changed: task-group loop becomes a story loop with per-story verification and checkpoint.
- `speckit-pro/skills/speckit-autopilot/references/post-implementation.md` and the Codex mirror — changed: per-story PR emission, stack or independent-branch mode.
- `speckit-pro/skills/speckit-coach/templates/workflow-template.md` — changed: per-story checkpoint table.

**Key Files:**

- `.specify/templates/spec-template.md` and `.specify/templates/tasks-template.md` — the story and checkpoint structure this spec consumes.
- `speckit-pro/speckit_pro_runner/helpers/stack_manager.py` — splits by marker slice today.
- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` — `multi-pr-emission` apply is deferred today.

**Done When:**

- A spec with three stories runs Setup and Foundational once and then three
  story iterations, each with its own gate run, checkpoint, and PR, on both
  distributions.
- With `gh-stack` the three PRs form one stack; without it, three branches;
  the workflow file names the mode.
- A failing check in story 2 stops the run with the story, check, and evidence
  named, and a resume continues from story 2.

---

### HRNS-017: Host Capability Spike

**Priority:** P1 | **Depends On:** none | **Enables:** HRNS-024, HRNS-027, HRNS-029, HRNS-036

**Goal:** Observe, on both hosts, the facts every later slice depends on,
before any shipped source changes.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 0 (spike; timeboxed to two working days) |
Production files: 0 |
Total files: 1 |
Budget result: within budget

**Scope:**

- Record HEAD, the `agent_inventory.json` role set, the helper registry
  envelope, and the prepare, invoke, consume, and record integration points
  on Claude Code and Codex.
- Observe whether a native `evaluate` result is visible to the live parent
  before decisions seal, and classify each host's posture as
  `isolated_shadow`, `retrospective_shadow`, or `advisory_not_authorized`.
- Observe whether each host lets a hook replace a built-in tool's output,
  whether Codex exposes a prompt-time hook, how two plugins' Stop hooks
  interact when one continues the turn, and how per-turn hook text from
  several plugins shares the lead's context.
- Re-check the Jev model version, token budgets, and backends the installed
  `typesafe-jev` plugin actually uses.
- Classify each inherited finding in the typed-judgment catalog as open,
  resolved, or unverified.

**Out of Scope:**

- Any shipped source change, registry write, or paid provider call.

**Module and Interface Deltas:**

- `docs/ai/specs/harness-engineering-uplift-host-capability-spike.md` — new: report only.

**Done When:**

- The report answers every question above per host, each answer labeled as
  native observation or documentation, and names the qualification gaps.

---

### HRNS-018: Typed Workflow State

**Priority:** P1 | **Depends On:** none | **Enables:** HRNS-030, HRNS-037

**Goal:** Make workflow status typed data with rendered prose, so a status
report can never disagree with what actually ran.

**Reviewability Budget:** Primary surface: scheduler/runtime |
Projected reviewable LOC: 190 (estimate-spec-size: 3 stories, 7 FRs, 5 files, modify) |
Production files: 5 |
Total files: 12 |
Budget result: within budget

**Scope:**

- A typed JSON record per workflow holds phase, gate, and Post status; the
  workflow file's status tables are rendered from it, and a check fails when
  they disagree.
- `speckit-status` reads the record. The 2026-09-24 status sweep found
  archived specs whose tables still showed implementation or Post in
  progress; this class of drift disappears.
- PRD authoring, scaffold, resolve-pr, and archive record resumable
  next-action state, not only autopilot.
- Freshness checks cover roadmap and archive pointers beside the existing
  workflow binding and stage mirror.
- Resume gives the user's latest instruction precedence and reports a
  conflicting live run under a documented policy.
- Resume reloads only the recorded chunks the next step needs, by stable id.

**Out of Scope:**

- Time-based run budgets; autopilot stops only for exceptional conditions.
- Journal and trace events (HRNS-025).

**Key Decisions:**

**Mirror Decision (open):** whether the typed record replaces the one-slot
`autopilot-state.json` mirror or sits beside it is decided at scaffold from
the stage-resolution tests (PRD OQ-8).

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/contracts/workflow-state.schema.json` — new: typed phase, gate, and Post record.
- Workflow-file rendering helper in `speckit-pro/speckit_pro_runner/helpers/` — new: renders status tables from the record.
- `speckit-pro/skills/speckit-status/SKILL.md` — changed: reads the typed record.

**Key Files:**

- `speckit-pro/skills/speckit-autopilot/SKILL.md` — workflow file authority and the state mirror.
- `speckit-pro/speckit_pro_runner/execution_control.py` — the durable run ledger this record sits beside.

**Done When:**

- A fixture archived spec with a stale table fails the consistency check.
- Status on a fixture repository reports from the record on both hosts.
- A resume fixture proves latest-instruction precedence and partial reload.

---

### HRNS-019: Helper Registry Contract and Tiered Disclosure

**Priority:** P2 | **Depends On:** none | **Enables:** HRNS-025, HRNS-026

**Goal:** Make the helper registry the single source for what each helper does,
what it risks, and how to call it, disclosed in tiers.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 142 (estimate-spec-size: 2 stories, 5 FRs, 4 files, modify) |
Production files: 4 |
Total files: 10 |
Budget result: within budget

**Scope:**

- Add purpose, owner workflow, linked input and output schemas, and risk flags
  to each registry entry. The record shape has not changed since the HRNS-001
  baseline, and 57 entries now exist.
- Generate helper reference pages and skill-facing request examples from the
  registry, with a drift check.
- Close the mutation fixture-manifest gap (17 dispatchable helpers, 14 in the
  manifest: `detect-stack-manager-plan`, `formal-check`, and
  `generate-spec-index-write` are missing).
- Disclose helpers in tiers: one-line index, schema on request, documentation
  on request.
- Resolve a stated intent to a helper and a validated envelope; a wrong
  argument is a validation error with remediation.

**Out of Scope:**

- Adopting a schema library; stdlib JSON Schema stays.

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/helpers/registry.py` — changed: purpose, owner, schema links, risk flags.
- `docs-site/scripts/generate-reference-pages.mjs` — changed: helper pages generated from the registry.

**Key Files:**

- `speckit-pro/speckit_pro_runner/contracts/` — existing per-surface schemas the registry will link.
- `tests/speckit-pro/unit/fixtures/mutation-helpers/fixture-manifest.json` — the manifest gap.

**Done When:**

- Every entry carries the new fields, and a check fails on a missing one.
- Generated pages and examples match the registry, and a drift check guards
  them.
- The fixture manifest covers every dispatchable mutation helper.

---

### HRNS-020: Autopilot Token Baseline

**Priority:** P1 | **Depends On:** none | **Enables:** HRNS-028, HRNS-029

**Goal:** Measure where an autopilot run's tokens go, per host and per role,
and commit a baseline that later context work must beat.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 245 (estimate-spec-size: 2 stories, 5 FRs, 3 files, new; greenfield allowance applies) |
Production files: 3 |
Total files: 8 |
Budget result: within budget

**Scope:**

- A committed harness reads documented host transcripts or usage records and
  reports processed-token share by activity: file reads, search, command
  output, reasoning, editing, and fixed prompt overhead.
- Attribution to the lead and each subagent role, naming the largest repeated
  read.
- Intervals on every share; an insufficient sample never passes; pass, fail,
  insufficient, and error get distinct exit codes.
- A committed baseline for the current release on both hosts.

**Out of Scope:**

- Changing any dispatch or context behavior (HRNS-028, HRNS-029).
- Estimating unknown usage; unknown stays unknown.

**Module and Interface Deltas:**

- `tests/speckit-pro/evals/` token-share harness — new: measurement and committed baseline.

**Done When:**

- The baseline report exists for both hosts with intervals, and the harness
  exits distinctly for insufficient data.

---

### HRNS-021: Condition-Bound Guidance and Lesson Promotion

**Priority:** P2 | **Depends On:** none | **Enables:** none

**Goal:** Load guidance only when a task touches the path it governs, and give
lessons a reviewed path from memory to scoped guidance to `AGENTS.md`.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 162 (estimate-spec-size: 3 stories, 6 FRs, 4 files, modify) |
Production files: 4 |
Total files: 10 |
Budget result: within budget

**Scope:**

- Per-directory guidance ("footguns") files selected deterministically from a
  task's owned paths and included in its dispatch.
- Re-supply condition-bound guidance at every dispatch whose condition holds,
  so compaction of an earlier turn cannot drop it.
- Keep entrypoints as short maps with references; report entrypoints that grow
  past a documented size without references (`speckit-scaffold-spec`
  `SKILL.md` grew from 497 to 1021 lines with no `references/`).
- A reviewable proposal path for lessons with provenance, secret screening,
  and a size bound.
- Optional scaffold of the guidance layout in a host repository on request;
  never a write on install.
- Later slice, after HRNS-027: shadow checks JEV-045 (lesson durability) and
  JEV-046 (relevant-lesson retrieval).

**Out of Scope:**

- A committed knowledge bundle or wiki; the OKF lane is dropped.

**Module and Interface Deltas:**

- Autopilot dispatch references and the Codex mirror — changed: path-conditional guidance in dispatch prompts.
- `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` — changed: optional guidance layout for host repositories.

**Done When:**

- A fixture task under a directory with a guidance file receives it at
  dispatch; a task elsewhere does not.
- A lesson promotion fixture shows provenance, screening, and review.

---

### HRNS-022: Eval Ladder and Model Refresh

**Priority:** P1 | **Depends On:** none | **Enables:** HRNS-038

**Goal:** Write down how SpecKit Pro verifies itself, calibrate its judge, and
make every model or effort change follow one evidence-backed procedure.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 150 (estimate-spec-size: 3 stories, 7 FRs, 3 files, modify) |
Production files: 3 |
Total files: 10 |
Budget result: within budget

**Scope:**

- A written ladder of verification rungs with blocking or advisory status, and
  the evaluator hierarchy.
- The native eval judge gains `insufficient_evidence` and is calibrated on
  labeled known-good and known-bad cases (today it returns a boolean only).
- A failure-derived fixture rule, with a discard rationale when a change adds
  no fixture.
- The model-refresh procedure for `agent_inventory.json`: a pre-registered
  comparison on the native evals with cost, tokens, and new failures, and the
  evidence committed with the change. The comparison harness behind the
  measured effort change (#641) is committed rather than living in a PR body.
- Eval reports name model, plugin version, runner version, allowed tools, and
  permission mode.
- Long inspection and eval jobs record cost and scope caps with a continuation
  plan.

**Out of Scope:**

- Comparing external eval products; the native runners (#578) are chosen.
- Live qualification runs themselves; they follow the procedure.

**Module and Interface Deltas:**

- `tests/speckit-pro/lib/native_eval_judge.py` — changed: `insufficient_evidence` verdict and calibration.
- `tests/speckit-pro/evals/README.md` — changed: written ladder, hierarchy, and model-refresh procedure.

**Done When:**

- The ladder and procedure are written and linked from `AGENTS.md`.
- Judge calibration results are committed with the labeled cases.
- A dry-run model refresh produces the committed evidence shape.

---

### HRNS-023: Harness Drift Scanner

**Priority:** P2 | **Depends On:** none | **Enables:** none

**Goal:** Find stale skill prose, status drift, dead references, and orphaned
process files with cited evidence, in bounded batches.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 205 (estimate-spec-size: 2 stories, 5 FRs, 2 files, new; greenfield allowance applies) |
Production files: 2 |
Total files: 7 |
Budget result: within budget

**Scope:**

- Report stale counts, paths, and line references in skill and reference
  prose; status drift between roadmaps and workflow records; dead helper
  references; orphaned process files.
- Cite repository evidence per finding and classify it as remediation or
  no-op.
- Bound output into reviewable batches and report coverage.
- Mark downstream plans, fixtures, and docs stale when planning inputs
  change.

**Out of Scope:**

- Automatic rewrites of harness-control files; remediation is a reviewable
  diff.

**Module and Interface Deltas:**

- `scripts/` drift scanner — new: bounded, evidence-cited report.

**Done When:**

- The scanner reports the live drift the 2026-09-24 audit found (for example
  the Post-list count stated three ways) and a clean tree reports none.

---

### HRNS-024: Shared Typed-Decision Contract

**Priority:** P1 | **Depends On:** HRNS-017 | **Enables:** HRNS-025, HRNS-027, HRNS-030

**Goal:** Give every Jev consumer one versioned contract whose schema and
conformance fixtures live in the `typesafe-jev` plugin.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 197 (estimate-spec-size: 3 stories, 8 FRs, 5 files, modify) |
Production files: 5 |
Total files: 14 |
Budget result: within budget

**Scope:**

- A language-neutral JSON contract: decision identity and version; projection,
  rubric, normalizer, and policy identities with hashes; preconditions;
  `authority_owner`. Schema and fixtures in `typesafe-jev`, consumed by
  speckit-pro and by the delegation runtime.
- Runner operations `prepare-semantic-check` and `assess-semantic-check`,
  registered with fixtures before any skill uses them.
- A wire projection limited to `state`, `questions`, and selected model
  fields, proven by test.
- Separate normalization for Noul, Choice, and Score; every malformed or
  missing answer is an explicit non-success; a malformed answer is rejected,
  never repaired; a security decision fails closed; an absent confidence
  stays absent.
- Versioned canonicalization with measured UTF-8 size and a labeled token
  estimate against the provider's documented budgets.
- String-only questions, the form both backends accept; requested and
  reported model identities recorded.
- Migrate the research broker's existing Jev screening onto the contract as
  the first consumer, with unchanged outcomes on its fixtures.

**Out of Scope:**

- Any provider client; transport stays in `typesafe-jev`.
- Enabling any new consumer (HRNS-027 and later).

**Module and Interface Deltas:**

- `typesafe-jev/` contract schema and conformance fixtures — new: shared by every consumer.
- `speckit-pro/speckit_pro_runner/semantic_checks.py` — new: prepare, normalize, assess, canonicalize.
- `speckit-pro/speckit_pro_runner/helpers/registry.py` — changed: registers the two operations.
- `speckit-pro/speckit_pro_runner/research_broker.py` — changed: screening moves onto the contract.

**Done When:**

- The conformance fixtures pass in speckit-pro, and the research broker's
  screening fixtures are unchanged.
- Every malformed-answer fixture yields a non-success state.

---

### HRNS-025: Run Journal and PR Trace Summary

**Priority:** P1 | **Depends On:** HRNS-019, HRNS-024 | **Enables:** HRNS-027, HRNS-034, HRNS-038

**Goal:** Record what ran, what was authorized, why a run stopped, and every
semantic decision in one additive, replayable journal, and summarize it in
the PR.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 177 (estimate-spec-size: 3 stories, 8 FRs, 4 files, modify) |
Production files: 4 |
Total files: 12 |
Budget result: within budget

**Scope:**

- One JSON-lines journal per run with helper runs, authorization decisions,
  safe-stop reasons, subagent lineage, and decision events, with per-run
  sequence, correlation and causation ids, and source revision.
- One failure-layer classification.
- Duplicate delivery, interrupted appends, and partial records handled
  explicitly; worker-authored JSON never becomes an observed result.
- A separate, bounded evidence store referenced by digest.
- Offline replay: deterministic decisions reproduce; stored Jev answers are
  re-thresholded without a call; non-replayable rows carry a cause.
  Counterfactual policy simulation edits nothing. Zero provider, dispatch,
  apply, push, or resolve calls, proven by test.
- A crash after send and before record leaves the request unknown.
- A compact, secret-screened trace summary and the confidence-gate verdict in
  the PR body.
- The journal stays local.

**Out of Scope:**

- External telemetry sinks or OpenTelemetry mapping.
- Replacing the existing ledgers; they stay authoritative.

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/run_journal.py` — new: append, replay, simulate; evidence-store reference.
- `speckit-pro/speckit_pro_runner/helpers/pr_emission.py` — changed: trace summary and confidence verdict in the body.

**Key Files:**

- `speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json` — `authorization_granted` is a constant `false` today, with no producer.

**Done When:**

- Replay and simulation fixtures run with zero side-effecting calls.
- A generated PR body carries the trace summary and verdict, and a planted
  secret is screened out.

---

### HRNS-026: Autonomous-Run Permission and Egress Policy

**Priority:** P1 | **Depends On:** HRNS-019 | **Enables:** HRNS-027

**Goal:** Give autonomous runs one deterministic command and egress policy
that inspects what a command will do and protects harness-control files.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 197 (estimate-spec-size: 3 stories, 8 FRs, 5 files, modify) |
Production files: 5 |
Total files: 14 |
Budget result: within budget

**Scope:**

- A command policy for autonomous runs: deny credential stores and
  environment secrets; deny network egress from scripts unless the task scope
  allows it; ask before writes outside the worktree; allow a declared
  read-only set; inspect script contents before execution.
- Protect harness-control files (plugin manifests, hooks, MCP config, helper
  registry, runner manifest, quality-gates file, policy files) from
  autonomous modification without a reviewable diff.
- Stop on repeated denials, workspace escape attempts, and harness-policy
  mutation attempts.
- A Claude Code equivalent of the Codex pre-implementation write-root and
  authorization boundary.
- One data-sensitivity classification governing every egress; a
  classification only narrows.
- Untrusted MCP tool annotations stay advisory; `SECURITY.md` matches actual
  allowlist behavior.
- A decision record for the research broker's Jev screening dependency.
- Later slice, after HRNS-027: shadow checks JEV-074 (ambiguous-command
  advice, which can only escalate to "ask") and JEV-075 (sensitivity label,
  which can only restrict).

**Out of Scope:**

- Changing the host's own permission modes.
- Authorizing the delegation runtime's worker actions; it keeps its own
  sandbox and apply boundary.

**Module and Interface Deltas:**

- `speckit-pro/scripts/workflow-guard-hook.py` and a policy file — changed: command policy, content inspection, protected files.
- `SECURITY.md` — changed: allowlist wording matches behavior.

**Done When:**

- Fixtures prove each deny, ask, and allow rule, including a script whose
  contents open a network connection.
- A fixture autonomous edit to a harness-control file is refused.

---

### HRNS-027: Dual-Host Jev Adapter

**Priority:** P1 | **Depends On:** HRNS-017, HRNS-024, HRNS-025, HRNS-026 | **Enables:** HRNS-031, HRNS-032, HRNS-033, HRNS-034, and every optional shadow slice

**Goal:** Let the trusted parent on each host call `evaluate` behind consent,
data classification, and budget checks, disabled by default.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 190 (estimate-spec-size: 3 stories, 7 FRs, 5 files, modify) |
Production files: 5 |
Total files: 14 |
Budget result: within budget

**Scope:**

- Capability discovery lists an optional typed-judgment capability with no
  hardcoded vendor preference.
- Per-project enablement defaults off; disabled output is byte-identical to
  today, proven on existing fixtures.
- Before each call: consent, provider and model pairing, HRNS-026
  classification, and the remaining call, input, and spend budget, with a
  per-call timeout; a failure records `DecisionSkipped`.
- Requested and reported model identities recorded; a mismatch is
  `unqualified`.
- Sweep roles gain nothing; the agent inventory and role allowlists stay
  unchanged, proven by test.
- Both hosts pass the same fixtures; the named `consensus-synthesizer` binding
  and all gates, budgets, and permissions are preserved.
- Key values never appear in output, journal entries, or logs.

**Out of Scope:**

- Any provider client or credential handling beyond what `typesafe-jev`
  already does.

**Module and Interface Deltas:**

- `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` — changed: optional typed-judgment capability.
- Project semantic-check configuration — new: enablement, consent, caps; default off.

**Done When:**

- Byte comparison proves the disabled path unchanged on both hosts.
- A parity test proves the synthesizer binding and role allowlists unchanged.

---

### HRNS-028: Shared Retrieval Packet for Fan-Out Roles

**Priority:** P2 | **Depends On:** HRNS-020 | **Enables:** none

**Goal:** Stop each fan-out role from re-deriving the same evidence: one
immutable packet per consensus item or checklist domain.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 142 (estimate-spec-size: 2 stories, 5 FRs, 4 files, modify) |
Production files: 4 |
Total files: 10 |
Budget result: within budget

**Scope:**

- A snapshot-bound, digest-checked evidence packet per consensus item and
  checklist domain, read by every analyst in the fan-out, with fetch on
  demand. The sweep broker's immutable snapshot is the pattern to generalize.
- A per-role projection; analyst opinions never become shared evidence.
- Read or write intent declared per task and fan-out role; read-only work runs
  in parallel, writers keep ownership locks.
- An HRNS-020 comparison against the baseline with no loss on the native
  evals.
- Later slice, after HRNS-027: shadow checks JEV-003 (code ranking), JEV-004
  (research passages), and JEV-029 (coupling warnings), which never remove
  evidence a check requires.

**Out of Scope:**

- The delegation runtime's worker-side packets and shared retrieval.

**Module and Interface Deltas:**

- Consensus and checklist dispatch references — changed: shared packet per item or domain.
- Retrieval-packet builder in `speckit-pro/speckit_pro_runner/` — new: snapshot-bound, digest-checked packet.

**Done When:**

- An HRNS-020 run shows fewer repeated reads and total tokens per consensus
  round, with native eval outcomes unchanged or better.

---

### HRNS-029: Visibility Ladder and Handoff Preservation

**Priority:** P2 | **Depends On:** HRNS-020 | **Enables:** none

**Goal:** Hand each subagent only the view of evidence its question needs, and
never let a handoff summary drop an open obligation.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 162 (estimate-spec-size: 3 stories, 6 FRs, 4 files, modify) |
Production files: 4 |
Total files: 10 |
Budget result: within budget

**Scope:**

- View levels (hide, short, long, full) at dispatch and return boundaries;
  required evidence and unresolved errors are never hidden; every lower view
  keeps a raw handle.
- Index-first subagent returns with fetch on demand.
- Long command and test output reduced to the failing trace and cause, on
  hosts where HRNS-017 found a supported hook; elsewhere the limitation is
  documented.
- A deterministic check that phase-handoff and resume packets keep every open
  obligation, unresolved failure, and constraint, with recovery from source.
- A documented rule for continuing an existing subagent versus starting fresh.
- Later slice, after HRNS-027: shadow checks JEV-002, JEV-072, JEV-073, and
  JEV-068.

**Out of Scope:**

- The lead session's own context and compaction, which the host owns.

**Module and Interface Deltas:**

- Dispatch and return contracts in the autopilot references — changed: view levels and index-first returns.
- Handoff check helper — new: deterministic obligation-preservation check.

**Done When:**

- A handoff fixture that omits an open obligation is caught and recovered.
- An HRNS-020 run shows the effect on tokens with no native eval loss.

---

### HRNS-030: Obligation and Subgoal Registry

**Priority:** P1 | **Depends On:** HRNS-018, HRNS-024 | **Enables:** HRNS-034

**Goal:** Turn approved goals into frozen, versioned obligations, and never
dispatch the same subtask twice.

**Reviewability Budget:** Primary surface: scheduler/runtime |
Projected reviewable LOC: 130 (estimate-spec-size: 2 stories, 6 FRs, 3 files, modify) |
Production files: 3 |
Total files: 8 |
Budget result: within budget

**Scope:**

- Versioned obligations from approved goals with stable ids, provenance,
  owning phase or task, applicability, required observations, semantic
  predicates, and dependencies, reusing FR and task ids.
- `invalid_goal` for an empty applicable required set; stage-relative
  obligations; rewording keeps identity; goal changes are versioned events;
  the model cannot add, drop, or weaken an obligation.
- Subtask registration before dispatch with exact-key dedup against completed
  and in-flight work, extending the execution-control reservations.
- Later slice, after HRNS-027: shadow check JEV-030 (repair-family
  recognition).

**Out of Scope:**

- Any new scheduler or repair budget.

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/goal_obligations.py` — new: frozen obligations and subgoal keys.
- `speckit-pro/speckit_pro_runner/execution_control.py` — changed: subgoal registration before dispatch.

**Done When:**

- Fixtures prove identity stability under rewording, the `invalid_goal`
  rejection, and that a duplicate subtask is not dispatched.

---

### HRNS-031: Pilot: Requirement-to-Task Semantic Coverage

**Priority:** P1 | **Depends On:** HRNS-027 | **Enables:** HRNS-038

**Goal:** Annotate each requirement with whether the task set really plans it,
without changing any gate result.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 110 (estimate-spec-size: 1 story, 5 FRs, 3 files, modify) |
Production files: 3 |
Total files: 8 |
Budget result: within budget

**Scope:**

- After Tasks (G5), one Noul per atomic requirement over the linked task set,
  with planned behavior, failure cases, and required evidence recorded
  separately (JEV-023).
- The structural G5 helper stays authoritative; the annotation changes no gate
  outcome, task count, or reservation.
- One uncovered required obligation is always reported; relevant edits mark
  judgments stale.
- Fixtures: a task that only repeats the FR id, a paraphrased plan, a missing
  sub-obligation, and planning coverage presented as implementation.

**Module and Interface Deltas:**

- Tasks G5 handoff — changed: shadow annotation beside the structural result.

**Done When:**

- The four fixtures classify correctly in shadow on both hosts.

---

### HRNS-032: Pilot: Review-Fix Closure Verification

**Priority:** P1 | **Depends On:** HRNS-027 | **Enables:** HRNS-038

**Goal:** Annotate each review thread with whether the concern was actually
addressed, after verification and push, without replying from a model result.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 102 (estimate-spec-size: 1 story, 4 FRs, 3 files, modify) |
Production files: 3 |
Total files: 8 |
Budget result: within budget

**Scope:**

- A closure judgment per thread over the concern, full thread, before and
  after source, acceptance condition, verification observations, and pushed
  SHA (JEV-038). The pagination and ordering prerequisite is HRNS-015.
- Annotation only; missing verification cannot become resolved; later edits
  invalidate the judgment.
- Fixtures: wrong-path fix, superficially similar edit, correct fix without
  execution evidence, supported false-positive rebuttal, omitted comment, and
  new regression.

**Module and Interface Deltas:**

- `speckit-pro/skills/speckit-resolve-pr/SKILL.md` and its review helper — changed: closure annotation record.

**Done When:**

- The six fixtures classify correctly in shadow, and no reply or resolution
  is made from a judgment.

---

### HRNS-033: Pilot: Claim-to-Source Support Annotation

**Priority:** P2 | **Depends On:** HRNS-027 | **Enables:** HRNS-038

**Goal:** Annotate analyst findings with whether their cited source actually
supports them.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 102 (estimate-spec-size: 1 story, 4 FRs, 3 files, modify) |
Production files: 3 |
Total files: 8 |
Budget result: within budget

**Scope:**

- Mechanical citation resolution first, then one Choice over `supports`,
  `contradicts`, `does_not_address`, and `insufficient_context` (JEV-005).
- Annotation linked to the finding, which is never rewritten; the full
  distribution is kept; later source edits mark judgments stale.
- Fixtures: real but irrelevant citation, paraphrased support, opposite
  behavior, missing branch context, missing source, and instruction-like text
  in evidence.

**Module and Interface Deltas:**

- Shared grounding boundary reference — changed: support annotation queue.

**Done When:**

- The six fixtures classify correctly in shadow.

---

### HRNS-034: Phase-Boundary Goal-Completion Verifier

**Priority:** P1 | **Depends On:** HRNS-025, HRNS-027, HRNS-030 | **Enables:** HRNS-035, HRNS-037 (semantic health)

**Goal:** At every phase handoff and proposed terminal summary, reconcile the
complete obligation set and report exactly what is unmet.

**Reviewability Budget:** Primary surface: scheduler/runtime |
Projected reviewable LOC: 130 (estimate-spec-size: 2 stories, 6 FRs, 3 files, modify) |
Production files: 3 |
Total files: 8 |
Budget result: within budget

**Scope:**

- Reconcile the complete applicable obligation set at handoffs and proposed
  terminal summaries (JEV-062).
- The aggregation vector (`invalid_goal`, unmet, missing-evidence,
  uncertain, stale, unresolved effects, pending mandatory work,
  `completion_suggestion_eligible`), with no field hiding another.
- Eligibility is a suggestion, never a gate result; expected TDD RED is not
  corrective work.
- G6.5 and the named synthesizer are unchanged; a readiness vector beside G6.5
  shows the weakest evidenced obligations (JEV-028).
- A host where the result reaches the live parent is labeled
  `advisory_mode_required`.

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/goal_verifier.py` — new: reconciliation and aggregation vector.
- Autopilot phase-handoff and terminal-summary references — changed: consume the vector as advisory.

**Done When:**

- Fixtures prove each vector field independently and that eligibility never
  alters a gate result.

---

### HRNS-035: Change-Triggered Scheduler and Invalidation

**Priority:** P1 | **Depends On:** HRNS-034 | **Enables:** HRNS-036, HRNS-038

**Goal:** Re-check only affected obligations when something relevant changes,
at parent-observed boundaries.

**Reviewability Budget:** Primary surface: scheduler/runtime |
Projected reviewable LOC: 102 (estimate-spec-size: 2 stories, 5 FRs, 2 files, modify) |
Production files: 2 |
Total files: 6 |
Budget result: within budget

**Scope:**

- Schedule only at parent-observed boundaries (JEV-063).
- No extra evaluation for an unchanged state; cache keys exclude timestamps
  and attempt ids.
- Unknown dependency coverage invalidates the larger scope; late responses
  after cancellation or supersession are kept stale.
- One in-flight check per decision, projection, and run; no recursive
  scheduling.
- User cancellation and repair budgets dominate; an exhausted Jev call budget
  never becomes success.

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/goal_verifier.py` — changed: dirty tracking, coalescing, single-flight, invalidation.

**Done When:**

- Fixtures prove coalescing, single-flight, and stale handling of a late
  response.

---

### HRNS-036: Premature-Stop and Redundant-Continuation Advice

**Priority:** P1 | **Depends On:** HRNS-035 | **Enables:** none

**Goal:** Before a run claims to be done, name what is still unmet; when it
keeps working past a satisfied goal, say so.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 122 (estimate-spec-size: 2 stories, 5 FRs, 3 files, modify) |
Production files: 3 |
Total files: 8 |
Budget result: within budget

**Scope:**

- Premature-done and redundant-continuation advisories naming obligation ids
  and missing evidence (JEV-064).
- Reconcile completion claims such as "all tests pass" against the cited
  producer evidence (JEV-036).
- Advice never ends a session, loops a worker, switches models, resets a
  budget, skips a gate, or bypasses approval; user cancellation always wins.
- Explicit stop conditions for exceptional cases only: blocked
  infrastructure, missing user decisions, repeated denials, repeated test
  failures, and impossible branch or worktree state.
- Provider outage never traps a stop path; the advisory coexists with other
  plugins' Stop hooks as HRNS-017 recorded.

**Out of Scope:**

- Wall-clock stop limits; autopilot runs to completion unless an exceptional
  condition occurs.

**Module and Interface Deltas:**

- Autopilot pre-terminal summary reference — changed: advisory block with obligation ids.

**Done When:**

- A fixture run that claims completion with an unmet obligation produces the
  advisory naming it, and no stop path changes.

---

### HRNS-037: Live Run Progress Page

**Priority:** P2 | **Depends On:** HRNS-018 | **Enables:** none

**Goal:** Let an operator check a long run's progress from anywhere, without
touching the run.

**Reviewability Budget:** Primary surface: UI |
Projected reviewable LOC: 165 (estimate-spec-size: 1 story, 4 FRs, 2 files, new; greenfield allowance applies) |
Production files: 2 |
Total files: 6 |
Budget result: within budget

**Scope:**

- An opt-in, read-only page rendered from the HRNS-018 typed record at phase
  boundaries: phase, gates, open tasks, checkpoints.
- No secrets, local paths, or transcript text; published only when enabled.
- After HRNS-034: semantic health shown separately from progress (JEV-048).
- A missing or failed page never blocks or slows the run.

**Module and Interface Deltas:**

- Progress-page renderer — new: read-only page from the typed record.

**Done When:**

- A fixture record renders a page with no secrets or paths, and a failing
  publish leaves the run unaffected.

---

### HRNS-038: Trajectory Calibration and Gated Live Evaluation

**Priority:** P1 | **Depends On:** HRNS-025, HRNS-031, HRNS-032, HRNS-033, HRNS-035 | **Enables:** promotion of any check beyond shadow

**Goal:** Produce the evidence required before any semantic check moves from
shadow to advisory.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 245 (estimate-spec-size: 2 stories, 5 FRs, 3 files, new; greenfield allowance applies) |
Production files: 3 |
Total files: 12 |
Budget result: within budget

**Scope:**

- A frozen, human-labeled trajectory corpus with development and holdout
  splits and labels stored apart from model outputs (JEV-053, JEV-070).
- Offline replay comparing phase-end with change-triggered verification at
  equal permitted work, with uncertainty on every rate.
- Every attempt kept; score shopping rejected; the holdout never tunes
  thresholds.
- A live-evaluation manifest whose default caps authorize zero requests; CI
  denies provider egress.
- Promotion beyond shadow is a reviewed decision citing the report.

**Module and Interface Deltas:**

- `tests/speckit-pro/trajectories/` — new: frozen corpus, holdout, replay report.
- Live-evaluation manifest schema — new: zero-default caps.

**Done When:**

- A calibration report exists for at least one frozen holdout.

---

## Environment & Deployment Context

| Resource | Detail |
|---|---|
| Runtime substrate | Python 3.11+ standard-library runner for installed-plugin helper behavior. |
| Test suite | `python3 tests/speckit-pro/run-all.py` for the quick layers; the CI suite request in `AGENTS.md` for the full set; native eval runners (#578) for behavioral layers. |
| Typed judgments | The `typesafe-jev` plugin in this repository ships `evaluate` for both hosts and owns the shared decision contract fixtures. |
| Model inventory | `speckit-pro/speckit_pro_runner/agent_inventory.json` is the only per-agent model and effort table. |
| Delegated work | The delegation runtime owns worker-side context, routing, escalation, and spend for delegated tasks; this roadmap never duplicates it. |

## Scaffold Notes

- Start Tier 1 in parallel; take HRNS-015 first when capacity is short,
  because every other slice's PRs pass through its repaired gates.
- Scaffold HRNS-016 only after HRNS-015 lands and live `multi-pr-emission`
  apply exists, and take it through grill-me first.
- Do not scaffold HRNS-027 or any shadow slice before HRNS-024, HRNS-025, and
  HRNS-026 have merged.
- Every shadow check starts disabled and records a baseline for its measure
  before any promotion; promotion needs the HRNS-038 report.
- Autopilot runs to completion; no spec adds a wall-clock stop.
- Preserve the `specs/` archive hygiene pattern: active spec folders are
  temporary and are archived after merge.
