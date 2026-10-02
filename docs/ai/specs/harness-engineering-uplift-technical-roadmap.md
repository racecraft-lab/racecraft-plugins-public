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
are retired. HRNS-015, HRNS-017 to HRNS-023, HRNS-039, and HRNS-040 are ready.
On 2026-09-24 this roadmap absorbed the Continuous Goal Verification roadmap,
whose `VRFY-###` identifiers are retired unscaffolded. On 2026-09-26 a
framework comparison added HRNS-039 to HRNS-041 and grew HRNS-018, HRNS-019,
HRNS-022, HRNS-025, and HRNS-026.

---

## Roadmap Overview

The active catalog holds **26 specifications** across **7 dependency tiers**.
HRNS-001 is complete, and HRNS-002 to HRNS-014 are retired with their
surviving criteria moved into the specs below. HRNS-016 is dropped: its
stop-on-first-failure rule contradicts ADR 0004 and ADR 0010, and one PR per
story contradicts the value unit in ADR 0009.

| Tier | Specs | Purpose | Parallelization |
|---|---|---|---|
| 1 | HRNS-015, HRNS-017, HRNS-018, HRNS-019, HRNS-020, HRNS-021, HRNS-022, HRNS-023, HRNS-039, HRNS-040 | Repair, host facts, typed state, registry contract, token baseline, guidance, eval ladder, drift scanner, consensus tally, test depth | Fully parallel; no dependencies |
| 2 | HRNS-024, HRNS-026, HRNS-028, HRNS-029, HRNS-037 | Decision contract, permission policy, context economy, progress page | Parallel, each after its one Tier 1 predecessor |
| 3 | HRNS-025, HRNS-030 | Run journal and obligation registry | Parallel after HRNS-024 |
| 4 | HRNS-027, HRNS-041 | Dual-host Jev adapter, the only slice that touches the wire; ledger formal model | Parallel; HRNS-041 after HRNS-025 and HRNS-040 |
| 5 | HRNS-031, HRNS-032, HRNS-033, HRNS-034 | Three shadow pilots and the phase-boundary verifier | Parallel after HRNS-027 |
| 6 | HRNS-035 | Change-triggered scheduler | Sequential after HRNS-034 |
| 7 | HRNS-036, HRNS-038 | Stop advice and trajectory calibration | Parallel after HRNS-035 |

**Execution Order:** Tier 1 in any order, HRNS-015 first when capacity is
short -> Tier 2 as each predecessor lands -> HRNS-025 + HRNS-030 -> HRNS-027 ->
HRNS-031 + HRNS-032 + HRNS-033 + HRNS-034 -> HRNS-035 -> HRNS-036 + HRNS-038.
HRNS-041 runs in parallel with that chain as soon as HRNS-025 and HRNS-040
land.

**Dependency Constraints:**

- HRNS-032 requires HRNS-015 for `speckit-resolve-pr` pagination and the
  pushed-SHA check, and HRNS-027 for the adapter.
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
- HRNS-031 and HRNS-033 each require only HRNS-027; HRNS-032 adds HRNS-015.
  They are consumers at existing handoffs and do not depend on each other.
- HRNS-034 requires HRNS-025, HRNS-027, and HRNS-030 because it reads frozen
  obligations, consumes adapter results, and records to the journal.
- HRNS-035 requires HRNS-034; HRNS-036 requires HRNS-035; HRNS-038 requires
  HRNS-025, the three pilots, and HRNS-035 because replay compares phase-end
  with change-triggered checking on stored journals.
- HRNS-041 requires HRNS-025 and HRNS-040 because the model describes the
  ledger after the journal changes, and its trace check runs in the
  dev-dependency layer.
- HRNS-039 and HRNS-040 have no dependencies. HRNS-019's reference-validator
  check and HRNS-022's dev-only tools run in HRNS-040's dev-dependency layer;
  whichever spec lands first creates that layer under constitution II.
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
HRNS-015 Repair ─────────────────────► HRNS-032 Review-fix pilot (also needs HRNS-027)
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
HRNS-039 Consensus tally: independent
HRNS-040 Test depth ─┬─► HRNS-041 Ledger formal model
HRNS-025 Run journal ┘
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
| HRNS-015 | Autopilot, Gate, and PR-Emission Repair | ⏳ Ready | - | Specify |
| HRNS-016 | Per-story Autopilot Execution | Retired | - | Dropped |
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
| HRNS-032 | Pilot: Review-Fix Closure Verification | ⏳ Pending | - | HRNS-015, HRNS-027 |
| HRNS-033 | Pilot: Claim-to-Source Support Annotation | ⏳ Pending | - | HRNS-027 |
| HRNS-034 | Phase-Boundary Goal-Completion Verifier | ⏳ Pending | - | HRNS-025, HRNS-027, HRNS-030 |
| HRNS-035 | Change-Triggered Scheduler and Invalidation | ⏳ Pending | - | HRNS-034 |
| HRNS-036 | Premature-Stop and Redundant-Continuation Advice | ⏳ Pending | - | HRNS-035 |
| HRNS-037 | Live Run Progress Page | ⏳ Pending | - | HRNS-018 |
| HRNS-038 | Trajectory Calibration and Gated Live Evaluation | ⏳ Pending | - | HRNS-025, HRNS-031 to HRNS-033, HRNS-035 |
| HRNS-039 | Runner-Computed Consensus Tally | ⏳ Ready | - | Specify |
| HRNS-040 | State and Gate Test Depth | ⏳ Ready | - | Specify |
| HRNS-041 | Ledger Formal Model and Trace Check | ⏳ Pending | - | HRNS-025, HRNS-040 |

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

**Priority:** P1 | **Depends On:** none | **Enables:** HRNS-032

**Goal:** Fix the defects from live autopilot runs that main still has, each
with a failing-first fixture, so the documented happy path stops producing a
failing pull request or a silently wrong count.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 390 (estimate-spec-size: 3 story groups, 9 FRs, 6 files, modify; re-run at scaffold) |
Production files: 6 |
Total files: 24 |
Budget result: warn on total files as one PR; ships as three slices, each with at most four production files and ten total authored files. Regenerated `dist/` and runner trust files follow their sources and are not budgeted.

Already fixed or owned elsewhere, so out of scope: #637 (PR #694), #638
(PR #699), the correct-but-halted turn (#531), git-ignored spec-index files
(#568), the "12-row" Post prose (#896), and the scaffold blind-spot deadline
(#994, PR #996).

**Scope:**

- **Slice A, PR emission** (`helpers/pr_packet.py`, `pr-packet.schema.json`,
  `helpers/mutation.py`, `helpers/pr_contract.py`).
  - Add an optional `release_note` input to final (single and split) packets.
    `build_packet_body` renders it as one ` ```release-note ` fence after
    Known Gaps. Drafts never carry one. The note is protected body content,
    not a new editable field.
  - `pr-packet-output` and `validate-pr-packet-write` apply succeed when the
    only untracked paths are the current packet's three canonical files. A
    second packet, an unrelated file, a tracked edit, or a `git status` failure
    still refuses. State this outcome in the autopilot packet guidance.
  - The final body shows the current Phase 6.5 verdict under Verification, read
    from the workflow file inside `pr_packet.py`. A missing verdict blocks
    finalization. HRNS-025 then drops the verdict from its scope. If the
    scaffold estimate exceeds 400 LOC, move this item back to HRNS-025 first.
- **Slice B, gates and counters** (`helpers/read_only.py`,
  `scripts/refresh-release-artifacts.py`).
  - G1-G4 and `count-markers` count `[Gap]` and `[Gap, <ref>]` alike with one
    shared pattern. Code-span and fence exclusion is out of scope.
  - The spec-index walk uses tracked paths only (`git ls-files --cached`).
    `refresh-release-artifacts.py` refreshes and `--check`s the spec index, so
    the existing `artifact-consistency` job catches a stale tracked map. Update
    the `AGENTS.md` freshness row.
  - `estimate-spec-size` accepts `required_refactor_files` and adds 40 LOC per
    distinct file. A missing or invalid value adds nothing.
  - `detect-commands` honors the host repository's documented test command
    (`UNIT_TEST`, or `FULL_VERIFY`) before marker-based detection. Scaffold
    chooses where a repository declares it; `.specify/quality-gates.json`
    holds thresholds only. Thresholds and the four quality slots are unchanged.
- **Slice C, workflow behavior** (no production files).
  - `speckit-resolve-pr` pages through every review thread and every thread's
    comments with `pageInfo` and cursors, and blocks mutation on a failed page.
    After verify and push, it compares the PR's fresh `headRefOid` with the
    pushed SHA before any reply or resolve.
  - phase-, analyze-, checklist-, and implement-executor (both hosts) state a
    teardown obligation for any team they form: collect each teammate result,
    request graceful shutdown, and report unconfirmed cleanup as unresolved.
    One Layer 1 structural test covers all eight definitions. Runtime child
    lifetime stays with HRNS-017.
  - `speckit-status` shows the complete request envelope for
    `generate-spec-index-check` and `o5-topology`, each matched by a passing
    fixture. HRNS-019 owns the broader envelope sweep.

**Out of Scope:**

- Post-list completion refusal and a single Post count (moved to HRNS-018,
  whose typed record owns Post status).
- Slice-row budget parsing and greenfield aggregation in the setup gate.
- Markdown-visibility rules for markers.
- Legacy roadmap-link repair; #699 fixed the template.
- Redesigning the PR-packet schema or the post-implementation sequence.
- Changing any host repository's release-note policy.

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/helpers/pr_packet.py`: changed. Optional
  release-note fence; current Phase 6.5 verdict.
- `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`:
  changed, only if the packet records the note.
- `speckit-pro/speckit_pro_runner/helpers/mutation.py`: changed. Current-packet
  untracked exemption.
- `speckit-pro/speckit_pro_runner/helpers/pr_contract.py`: new. Canonical
  packet paths shared by `pr_packet.py` and `mutation.py`.
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`: changed. Gap pattern;
  tracked-only spec index; refactor signal; declared test command.
- `scripts/refresh-release-artifacts.py`: changed. Spec-index refresh and check.
- `speckit-pro/skills/speckit-resolve-pr/SKILL.md`,
  `speckit-pro/skills/speckit-status/SKILL.md`, and four executor definitions
  in `speckit-pro/agents/` with their generated Codex TOML: changed.

**Key Files:**

- `speckit-pro/speckit_pro_runner/helpers/pr_packet.py`: `build_packet_body`,
  `required_headings`, `packet_path_parts`, `canonical_packet_paths`.
- `speckit-pro/speckit_pro_runner/helpers/mutation.py`:
  `git_worktree_status` and `dirty_worktree_diagnostic`.
- `speckit-pro/speckit_pro_runner/helpers/read_only.py`: the G1-G4 counters,
  `_spec_index_walk_regular_files`, `estimate_spec_size`, and `detect_commands`.
- `scripts/release_note_policy.py`: the gate the packet must satisfy.
- `docs/ai/specs/.process/ART-007-manual-uat.md`: the stale-index provenance.

**Done When:**

- A final packet built with `release_note` passes `scripts/release_note_policy.py`
  for a `feat` and a `fix` title. Without the input the body is byte-identical
  to today, and a draft still has no fence.
- Packet apply succeeds with only the current packet's three files untracked,
  and refuses for each blocked case above, each proven by a fixture.
- The final body carries the current Phase 6.5 verdict, and a missing verdict
  blocks (unless moved to HRNS-025).
- A fixture with `[Gap]` and `[Gap, <ref>]` counts both in G1-G4 and
  `count-markers`.
- `refresh-release-artifacts.py --check` fails on a frozen pre-fix stale
  `SPEC-MOC.md` fixture and passes with an untracked file present in the tree.
- `estimate-spec-size` fixtures cover a refactor count, a missing value, and
  an invalid value.
- A declared test command wins over detection in a `detect-commands` fixture.
- `speckit-resolve-pr` fixtures cover more than 100 threads, more than one
  comment page, a failed page, and a pushed-SHA mismatch that leaves threads
  unresolved.
- The structural test fails when any of the eight executor definitions loses
  its teardown obligation.
- Each documented `speckit-status` envelope matches a passing fixture.

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
- Observe how each host lets a teammate or child process outlive its parent,
  and what ends it. HRNS-015 states only a teardown obligation for executors;
  runtime child lifetime belongs here.
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
Projected reviewable LOC: 237 (estimate-spec-size: 4 stories, 9 FRs, 6 files, modify) |
Production files: 6 |
Total files: 14 |
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
- The runner owns phase sequencing: a read-only next-step helper reads the
  record and the execution ledger and returns the next phase and its allowed
  transitions. Autopilot executes what it returns and records the outcome;
  the model stops reconciling the workflow file, the state mirror, and the
  ledger by hand.
- Reading resumable state never writes; only a recorded transition changes
  the record.
- A deterministic check refuses completion while any Post row is pending, read
  from the record's Post status on both hosts. One constant states the Post
  row count per host (11 on Claude; 13 on Codex, two of them supporting rows);
  `validate-autopilot-phase-coverage.py` checks only row presence today.

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
- Next-step fixtures cover every phase transition, and the autopilot
  sequencing prose reduces to calling it.
- A fixture proves completion is refused while any Post row is pending, on both
  hosts, and one constant states each host's Post row count.

---

### HRNS-019: Helper Registry Contract and Tiered Disclosure

**Priority:** P2 | **Depends On:** none | **Enables:** HRNS-025, HRNS-026

**Goal:** Make the helper registry the single source for what each helper does,
what it risks, and how to call it, disclosed in tiers.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 197 (estimate-spec-size: 3 stories, 8 FRs, 5 files, modify) |
Production files: 5 |
Total files: 13 |
Budget result: within budget

**Scope:**

- Add purpose, owner workflow, linked input and output schemas, and risk flags
  to each registry entry. The record shape has not changed since the HRNS-001
  baseline, and 62 entries now exist (39 read-only helpers, 23 mutation
  helpers).
- Generate helper reference pages and skill-facing request examples from the
  registry, with a drift check. This covers the envelope sweep beyond
  `speckit-status` (HRNS-015 fixes that one skill).
- Close the mutation fixture-manifest gap (17 dispatchable helpers, 14 in the
  manifest: `detect-stack-manager-plan`, `formal-check`, and
  `generate-spec-index-write` are missing).
- Disclose helpers in tiers: one-line index, schema on request, documentation
  on request.
- Resolve a stated intent to a helper and a validated envelope; a wrong
  argument is a validation error with remediation.
- Make each shipped schema the single source for its contract: a CI
  differential test runs every documented example and generated invalid
  variants through the runner's validator and a pinned jsonschema, which must
  agree; a schema without fixtures fails. Generating the request examples from
  the schemas removes the prose drift behind #650, #651, and #654.
- A 2020-12 meta-schema check on every shipped schema, and the runner
  integrity hash extended to cover them.

**Out of Scope:**

- Adopting a schema library in the runner; stdlib JSON Schema stays at run
  time. A pinned jsonschema may check the runner's validator in CI under
  constitution II.

**Key Decisions:**

**Schema Authoring (open):** whether schemas are hand-written or generated by
a pinned dev-only model library such as Pydantic is decided at scaffold; the
committed schema stays the source either way.

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/helpers/registry.py` — changed: purpose, owner, schema links, risk flags.
- `speckit-pro/speckit_pro_runner/runtime.py` — changed: integrity hash covers contract schemas.
- `docs-site/scripts/generate-reference-pages.mjs` — changed: helper pages generated from the registry.

**Key Files:**

- `speckit-pro/speckit_pro_runner/contracts/` — existing per-surface schemas the registry will link.
- `tests/speckit-pro/unit/fixtures/mutation-helpers/fixture-manifest.json` — the manifest gap.

**Done When:**

- Every entry carries the new fields, and a check fails on a missing one.
- Generated pages and examples match the registry, and a drift check guards
  them.
- The fixture manifest covers every dispatchable mutation helper.
- The differential and meta-schema checks pass on all shipped schemas, and a
  planted disagreement fails.

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
  `SKILL.md` grew from 497 to 1,274 lines with no `references/`).
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
Projected reviewable LOC: 165 (estimate-spec-size: 3 stories, 9 FRs, 3 files, modify) |
Production files: 3 |
Total files: 12 |
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
- Dev-only tuning: `claude plugin eval` and skill-creator's train/test
  description loop first, then standalone GEPA (zero required dependencies,
  a host-CLI wrapper as its reflection model) with a held-out split, scoring
  on both hosts, no regression in any other skill, and human review of each
  committed diff.
- An Inspect AI and inspect_swe spike with a recorded keep-or-drop decision.

**Out of Scope:**

- Replacing the native runners (#578). Dev-only eval tools (`claude plugin
  eval`, skill-creator's description loop, standalone GEPA, an Inspect AI
  spike) may supplement them under constitution II.
- Live qualification runs themselves; they follow the procedure.

**Module and Interface Deltas:**

- `tests/speckit-pro/lib/native_eval_judge.py` — changed: `insufficient_evidence` verdict and calibration.
- `tests/speckit-pro/evals/README.md` — changed: written ladder, hierarchy, and model-refresh procedure.

**Done When:**

- The ladder and procedure are written and linked from `AGENTS.md`.
- Judge calibration results are committed with the labeled cases.
- A dry-run model refresh produces the committed evidence shape.
- One description change lands through the tuning loop with its held-out
  evidence, and the Inspect AI decision is recorded.

---

### HRNS-023: Harness Drift Scanner

**Priority:** P2 | **Depends On:** none | **Enables:** none

**Goal:** Find roadmap-to-workflow status drift and orphaned process files with
cited evidence, in bounded batches.

**Reviewability Budget:** Primary surface: docs/process |
Projected reviewable LOC: 205 (estimate-spec-size: 2 stories, 5 FRs, 2 files, new; greenfield allowance applies; re-run at scaffold) |
Production files: 2 |
Total files: 7 |
Budget result: within budget

**Scope:**

- Report status drift between roadmaps and workflow records, and orphaned
  process files.
- Cite repository evidence per finding and classify it as remediation or
  no-op.
- Bound output into reviewable batches and report coverage.
- Mark downstream plans, fixtures, and docs stale when planning inputs
  change.

**Out of Scope:**

- Stale counts, paths, and doc drift in skill and reference prose: the
  `ripwire-advisory` workflow reports doc drift on pull requests (#841).
- Automatic rewrites of harness-control files; remediation is a reviewable
  diff.

**Module and Interface Deltas:**

- `scripts/` drift scanner — new: bounded, evidence-cited report.

**Done When:**

- The scanner reports a fixture roadmap whose status disagrees with its
  workflow record and an orphaned `.process` file, and a clean tree reports
  none.

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
Projected reviewable LOC: 227 (estimate-spec-size: 3 stories, 12 FRs, 5 files, modify) |
Production files: 5 |
Total files: 14 |
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
- A compact, secret-screened trace summary in the PR body. The confidence-gate
  verdict ships with HRNS-015 unless that spec moves it here.
- The journal stays local.
- Compare stdlib `sqlite3` with JSON lines against the duplicate, torn-append,
  and partial-read rules, and record the choice. The ledger lock is released
  when its owner dies; a live owner's lock is never taken over.
- Intent-then-outcome records around runner file mutations, each declaring
  whether it must reach disk before the next step.
- Format versions with upcasting, so a run started under an older plugin
  release replays after a cache update.
- Replay fails when current gate logic would decide differently from the
  record; one journal writer per spec; a host `TRACEPARENT` recorded when
  present, never required.

**Out of Scope:**

- External telemetry sinks or OpenTelemetry mapping.
- Replacing the existing ledgers; they stay authoritative.

**Module and Interface Deltas:**

- `speckit-pro/speckit_pro_runner/run_journal.py` — new: append, replay, simulate; evidence-store reference.
- `speckit-pro/speckit_pro_runner/helpers/pr_packet.py`: changed. Trace summary in the body (and the confidence verdict if HRNS-015 does not ship it).

**Key Files:**

- `speckit-pro/speckit_pro_runner/contracts/execution-control.schema.json` — `authorization_granted` is a constant `false` today, with no producer.

**Done When:**

- Replay and simulation fixtures run with zero side-effecting calls.
- A generated PR body carries the trace summary, and a planted secret is
  screened out.
- A killed process leaves no lock that blocks the next run, an old-format
  ledger replays, and a changed gate decision fails replay.

---

### HRNS-026: Autonomous-Run Permission and Egress Policy

**Priority:** P1 | **Depends On:** HRNS-019 | **Enables:** HRNS-027

**Goal:** Give autonomous runs one deterministic command and egress policy
that inspects what a command will do and protects harness-control files.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 225 (estimate-spec-size: 3 stories, 9 FRs, 6 files, modify) |
Production files: 6 |
Total files: 15 |
Budget result: within budget

Landed on main and not repeated here: Codex egress authorization
(`helpers/egress_authorization.py`), the `check-gate-preflight-coverage`
helper, and run-start permission and egress settlement (#748, #755, #805,
#833). What remains is the Claude-side command policy, content inspection, and
harness-control file protection.

**Scope:**

- One verdict shape (allow, deny, or ask, with a reason) from runner gates and
  hook policies to both hosts' hooks.
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

**Priority:** P1 | **Depends On:** HRNS-015, HRNS-027 | **Enables:** HRNS-038

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
  SHA (JEV-038). HRNS-015 owns the pagination and the pushed-SHA check this
  judgment reads.
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

### HRNS-039: Runner-Computed Consensus Tally

**Priority:** P1 | **Depends On:** none | **Enables:** fewer consensus routing defects

**Goal:** Move vote counting and routing out of the synthesizer prompt into
runner code, so consensus follows its rules exactly on both hosts.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 170 (estimate-spec-size: 3 stories, 7 FRs, 4 files, modify) |
Production files: 4 |
Total files: 14 |
Budget result: within budget

**Scope:**

- Analysts return schema-typed positions (position key, security relevance,
  escape hatch, evidence) through the schema-constrained output the
  feedback-sweep launcher already uses on both hosts.
- The runner computes agreement (2-of-3 and the N<3 rules), applies the
  security override, and routes human review.
- The model step only judges whether two positions match and writes the
  artifact edit; a missing or malformed position is an explicit unknown.
- Red-first fixtures for every routing rule, including #661, #718, and #726,
  and for Round 3 tiebreak routing to the `consensus-tiebreaker` agent (#827).
  PR #982 (#883) dropped the consensus settings nothing read.

**Out of Scope:**

- Changing the consensus rules themselves; this moves where they run.
- Adopting DSPy or another LLM framework; the host CLIs stay the model path.

**Module and Interface Deltas:**

- Consensus tally in `speckit-pro/speckit_pro_runner/` — new: agreement, security override, human-review routing.
- Analyst position schema in `speckit-pro/speckit_pro_runner/contracts/` — new.
- `speckit-pro/agents/consensus-synthesizer.md`, analyst agents, and the Codex TOML mirrors — changed: typed positions; no vote counting.
- `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md` — changed: describes the split.

**Key Files:**

- `speckit-pro/speckit_pro_runner/sweep_launcher.py` — the existing schema-constrained, two-host model path.
- `speckit-pro/speckit_pro_runner/sweep_isolation.py` — typed result records the tally can follow.

**Done When:**

- Every consensus routing fixture passes on both hosts, and no prompt counts
  votes.

---

### HRNS-040: State and Gate Test Depth

**Priority:** P2 | **Depends On:** none | **Enables:** HRNS-041

**Goal:** Find ledger, state, path, gate, and broker defects with generated
and adversarial tests instead of waiting for live runs to hit them.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 300 (estimate-spec-size: 3 stories, 7 FRs, 3 files, new; greenfield allowance applies) |
Production files: 3 |
Total files: 15 |
Budget result: within budget

**Scope:**

- A pinned dev-dependency source, a repository installer, and a named suite
  layer and CI job, under constitution II; a missing package fails the layer.
- Stateful property tests (Hypothesis) over the execution-control ledger and
  workflow-state resolution: start, reserve, authorize, repeated event ids,
  clock regression, resume; path shapes with symlinks, worktrees, and a
  doubled `.process`. Deterministic in CI.
- A mutation-testing pilot over `gates/` with in-process tests; each survivor
  gets a test or a recorded equivalence reason.
- Per-module mypy strict for the ledger, workflow-state, and path modules.
- The MCP Python SDK as a CI conformance client for the three stdio brokers.
- A check that flags a runner mutation before an operator gate unless it is
  declared idempotent.

**Out of Scope:**

- Adding any package to shipped code.
- Making the new CI job a required check; that is a ruleset decision.

**Module and Interface Deltas:**

- Dev-dependency installer in `scripts/` and a pinned requirements source — new.
- `tests/speckit-pro/suite-manifest.json` — changed: the dev-dependency layer.
- `.github/workflows/pr-checks.yml` — changed: the dev-dependency job.

**Done When:**

- The layer runs in CI and fails when a pinned package is missing.
- Stateful tests cover the ledger actions and path shapes above, and every
  survivor of the mutation pilot is triaged.

---

### HRNS-041: Ledger Formal Model and Trace Check

**Priority:** P3 | **Depends On:** HRNS-025, HRNS-040 | **Enables:** formal regression coverage of the ledger

**Goal:** Check the execution-control ledger against a formal model, using
the trace checker the runner already ships.

**Reviewability Budget:** Primary surface: harness/adapter |
Projected reviewable LOC: 205 (estimate-spec-size: 2 stories, 5 FRs, 2 files, new; greenfield allowance applies) |
Production files: 2 |
Total files: 10 |
Budget result: within budget

**Scope:**

- A TLA+ or Quint model of reservations, corrective-cycle budgets, native
  event-id replay protection, and resume, with stated invariants.
- Ledger tests emit ITF traces that `formal/traces.py` checks against the
  model in CI.

**Out of Scope:**

- Modeling the whole workflow; only the ledger.

**Module and Interface Deltas:**

- Ledger model and trace fixtures under `tests/speckit-pro/` — new.

**Key Files:**

- `speckit-pro/speckit_pro_runner/formal/traces.py` — the existing ITF trace checker.
- `speckit-pro/speckit_pro_runner/execution_control.py` — the ledger being modeled.

**Done When:**

- The invariants hold at documented bounds, and a planted divergence between
  the traces and the model fails.

---

## Environment & Deployment Context

| Resource | Detail |
|---|---|
| Runtime substrate | Python 3.11+ standard-library runner for installed-plugin helper behavior; pinned dev-only packages for checks, under constitution II. |
| Test suite | `python3 tests/speckit-pro/run-all.py` for the quick layers; the CI suite request in `AGENTS.md` for the full set; native eval runners (#578) for behavioral layers. |
| Typed judgments | The `typesafe-jev` plugin in this repository ships `evaluate` for both hosts and owns the shared decision contract fixtures. |
| Model inventory | `speckit-pro/speckit_pro_runner/agent_inventory.json` is the only per-agent model and effort table. |
| Delegated work | The delegation runtime owns worker-side context, routing, escalation, and spend for delegated tasks; this roadmap never duplicates it. |

## Scaffold Notes

- Start Tier 1 in parallel; take HRNS-015 first when capacity is short,
  because every other slice's PRs pass through its repaired gates.
- Do not scaffold HRNS-027 or any shadow slice before HRNS-024, HRNS-025, and
  HRNS-026 have merged.
- Every shadow check starts disabled and records a baseline for its measure
  before any promotion; promotion needs the HRNS-038 report.
- Autopilot runs to completion; no spec adds a wall-clock stop.
- Preserve the `specs/` archive hygiene pattern: active spec folders are
  temporary and are archived after merge.
