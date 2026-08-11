# Phase 0 Research: Implementation-Notes Capture (ART-012)

**Date**: 2026-08-10 | **Spec**: `specs/art-012-implementation-notes-capture/spec.md`

Every decision below was settled before planning, either by the Design Concept
interview (`docs/ai/specs/.process/ART-012-design-concept.md`, Q1-Q8) or by the
two Clarify consensus rounds recorded in
`docs/ai/specs/.process/ART-012-workflow.md`. This file records them in one
place with the tree evidence that backs them, plus the four questions planning
had to resolve on its own (R6, R8, R9, R11).

There are no unresolved unknowns. Technical Context in `plan.md` carries no
clarification markers.

---

## R1. The reporting contract has three authored homes, not one

**Decision**: Add the new field to all three authored copies of the
`## Task Result: <TASK_ID>` block. That is four touchpoints, because one file
states the contract twice.

| File | Touchpoint | Anchor |
|---|---|---|
| `speckit-pro/skills/speckit-autopilot/references/tdd-protocol.md` | Summary Format template | block at `:119-140`, `**Errors:**` at `:139` |
| `speckit-pro/agents/implement-executor.md` | Summary Format template | block at `:139-158`, `**Errors:**` at `:157` |
| `speckit-pro/agents/implement-executor.md` | Terminal Deliverable enumeration | `:164`, a hard `MUST` naming exactly four fields |
| `speckit-pro/codex-agents/implement-executor.toml` | Summary Format template | block at `:121-140`, `**Errors:**` at `:139` |

**Rationale**: `grep -rln "Task Result: <TASK_ID>" speckit-pro/` returns exactly
these three files. `tdd-protocol.md` is shared and injected into every
implementation dispatch prompt, but both agent definitions hard-code their own
duplicate of the same block, and an agent follows its own output template over
referenced contract prose. FR-001 requires *every* implementation task summary
to carry the field, so a partial fix violates the requirement. The Terminal
Deliverable line at `implement-executor.md:164` is a separate touchpoint because
it enumerates the four required fields in prose; patching the template alone
ships an agent that contradicts itself.

**Verified**: the Codex TOML carries no Terminal Deliverable enumeration, so it
is one touchpoint, not two. Confirmed by grep over that file.

**Alternatives rejected**: patch only the shared `tdd-protocol.md`. Rejected
because it leaves two agents emitting the old four-field block. No Layer 1 test
diffs Summary Format content across platforms, so this partial fix would pass
CI green and still break FR-001. Enforcement is FR-001 plus the G6 drift check,
not a red test.

**Precedent**: commit `bb01ef28` added a required line to this same Summary
Format contract in both agent definitions in one commit, for exactly this
reason.

---

## R2. The new field goes after `**Errors:**`

**Decision**: append `**Deviations/Edge cases/Surprises:**` as the last line of
the Task Result block in all three copies.

**Rationale**: `**Errors:**` is currently the terminal line in all three copies.
Appending after it leaves every existing line byte-stable and position-stable.
Inserting anywhere earlier shifts existing lines for no gain. No test anchors
the field order today, so the new Layer 4 test defines it.

**Alternatives rejected**: place the field next to `**Errors:**` but before it,
grouping "things that went wrong". Rejected: same semantics, larger diff.

---

## R3. Append cadence is per-arrival, on every dispatch shape

**Decision**: every attempt's entry is appended on the turn that attempt's own
result reaches the orchestrator, before further work is dispatched. This holds
for a singleton, a sequential run, and a member of a parallel run alike. A bare
idle or liveness signal carrying no task summary is never an append trigger.

**Rationale**: the platform delivers worker completions individually, not as a
batch. `code.claude.com/docs/en/sub-agents` states that "a background subagent's
results reach Claude as a completion notification in a later turn" — singular,
per subagent. `code.claude.com/docs/en/agent-teams` states that "when a teammate
finishes and stops, it automatically notifies the lead" and that "the lead
doesn't need to poll for updates". So the orchestrator does get a turn per
attempt, and per-attempt durability is achievable on both parallel paths.

The `Wait for ALL to complete.` line at
`speckit-pro/skills/speckit-autopilot/references/phase-execution.md:888`, and
`Wait for all teammates to complete.` at `:875`, remain accurate as *site
collection policy* for the verification barrier. They were never platform
constraints. The barrier stays; only the notes append moves earlier.

**Superseded reasoning, preserved.** An earlier revision of this decision held
that per-attempt append inside a parallel run was unachievable, citing those two
lines plus
`speckit-pro/skills/speckit-autopilot/references/agent-teams-integration.md:75-76`
("The next user message returns all N results together"). That third citation is
factually wrong and is corrected by this spec. The earlier analysis checked
`Monitor` and `TaskStop` and was right that no *polling* primitive exists; it
missed that the platform *pushes*. The narrowed cadence it produced is reversed
by operator decision, recorded in the Design Concept's Q2 revision note 2.

**Design Principle #2 now cuts the other way.**
`agent-teams-integration.md:325-328` requires the parallel-subagents fallback to
deliver the same contract as the Agent Teams path. When the fallback was thought
to be the weaker path, that argued for narrowing both. Since both can deliver
per-arrival, the same principle requires both to do so.

**Cost**: one genuine addition, on the Agent Teams path only. Teammates are
independent sessions whose output never returns to the caller, so their idle
notification is a signal without a payload. FR-006 therefore requires teammates
to be told at dispatch to send their task summary to the lead on completion, and
the append triggers on that message. Without it, the Teams path would write
structurally empty entries while looking identical in the instructions.

**Alternatives rejected**: trigger the append on the teammate idle notification
itself. Rejected on two counts — it carries no task summary, so entries would
record nothing; and idle is not completion, so a teammate that goes idle after a
coordination message and is later woken would be recorded as two attempts,
breaking SC-002's exact count and FR-003's ordering rule.

**Serial re-run**: the fallback after a parallel-run regression
(`phase-execution.md:894-898`) is per-task by construction and needs no special
handling.

---

## R4. There are three append call sites in the routing, not one

**Decision**: append an entry for every dispatched attempt on all three routing
branches.

**Rationale**: the Phase 7 routing table (`phase-execution.md:972-984`) sends
research tasks to `domain-researcher` and verification tasks to
orchestrator-direct execution. Neither branch carries the TDD protocol and
neither emits a `## Task Result: <TASK_ID>` block. FR-003 defines "each task
attempt" as every attempt the orchestrator dispatched, whichever agent or direct
command executed it, so those attempts still get entries.

**Alternatives rejected**: append only on the executor branch. Rejected: SC-001
counts every dispatched attempt, and silently missing research and verification
tasks is the failure the edge case names.

---

## R5. The record is create-if-absent, never truncate

**Decision**: at the start of Phase 7 the orchestrator ensures the record
exists. Absent, it creates it with the header. Present, it leaves the file
exactly as found and appends after the existing content.

**Rationale**: Phase 7 is resumable. `--from-phase implement` re-enters Phase 7
against a feature directory that may already hold a partial record. A plain
"create with header" step would truncate it and write a second header, losing
everything the earlier run recorded. FR-002 states the create-if-absent rule and
forbids both truncation and a second header.

**Alternatives rejected**: detect already-recorded tasks on resume and skip
them. Rejected explicitly by spec.md's Assumptions: a re-executed task appends
another entry, which is the same accurate-history behavior a retry produces.

---

## R6. One literal value covers both empty cases: `None`

**Decision**: the entry field reads exactly `None` both when an executor
reported "None" and when the attempt produced no reporting field at all.

**Rationale**: this is the one place FR-003 and SC-003 could be read as pulling
apart. FR-003 says entries for attempts with no reporting field "record that
nothing was reported"; SC-003 says that in a run where every executor reports
nothing, 100% of entries read "None". A distinct marker such as "Not reported"
would make SC-003 fail the moment a run contains one research task. A single
literal `None` satisfies both clauses: it records that nothing was reported, and
it keeps SC-003 measurable. It also matches Design Concept Q1/Q3 verbatim, which
say the per-task entry "literally reads 'None'".

Nothing in the spec requires distinguishing "executor said None" from "no field
returned". The task ID and the record's ordering already tell a reader which
route ran.

**Alternatives rejected**: a second field naming the dispatch route. Rejected
under constitution principle VI (YAGNI) and Design Concept Q7's flat-entry
decision. No consumer asked for it.

---

## R7. Fail-open, and the gap lands in the workflow file

**Decision**: any failure to create the record or append an entry is recorded as
a gap in the run's workflow file under
`docs/ai/specs/.process/<SPEC_ID>-workflow.md`, and the task and phase outcomes
are unchanged.

**Rationale**: Design Concept Q4 chose fail-open because the roadmap classifies
this record as exhaust, not load-bearing output. FR-004 requires the failure to
be readable afterwards in "the run's durable, operator-visible record of the
run". In this workflow that record is the workflow file, which the orchestrator
already writes gap notes into and which an operator already reads to find out
what the run did.

**Alternatives rejected**: fail-closed. Rejected: it makes a formatting glitch
in one task's summary able to stop the implement phase, which the Design Concept
rules out.

---

## R8. Verification is one new Layer 4 unit test plus a manifest entry

**Decision**: add `tests/speckit-pro/unit/test-implementation-notes-record.py`
and register it in `tests/speckit-pro/suite-manifest.json` under layer `4`.

**Rationale**: constitution principle IV requires Layer 4 coverage under
`tests/speckit-pro/unit/` and requires layer membership to stay declared in the
suite manifest. Layer 4 is the suite's "Unit Tests" layer; there is no
`layer4-*` directory. The manifest lists every Layer 4 script explicitly, so a
new file is invisible to the runner until it is registered.

`tests/speckit-pro/unit/test-reviewability-marker-guidance.py` is the working
precedent for this exact shape: a Layer 4 test that asserts reference-document
prose across both platform copies of `phase-execution*.md`. The new test follows
it and needs no baseline file (many Layer 4 entries carry `baseline: null`).

**Alternatives rejected**: extend
`tests/speckit-pro/unit/test-autopilot-phase-coverage.py`. Rejected: that file
is 3,499 lines testing a Python validator script, not reference prose. Wrong
home, and it would bury the new assertions.

**Naming**: the filename describes durable behavior and carries no spec ID, per
the repository's editing boundaries.

---

## R9. Editing plugin source pulls two generated surfaces with it

**Decision**: after editing the five plugin files, run
`python3 scripts/refresh-release-artifacts.py`, which covers both surfaces in
one idempotent pass. Never hand-edit either.

`python3 scripts/build-plugin-payloads.py` on its own is **not** sufficient: its
whole body is the `build_xplat008_payloads` call, so it rebuilds `dist/` and
leaves the installed-cache fixtures and the proof hashes stale, which fails
Layer 4. `refresh-release-artifacts.py` calls the same builder as step 2 of six
and then content-syncs the fixtures and refreshes the proof tree hashes. Its
docstring states both the six steps and the idempotence, and states that it does
**not** regenerate the docs reference — that surface keeps its own command,
below.

**Rationale**: two generated surfaces mirror these files.

1. **Install payloads.** `dist/claude/speckit-pro/` and
   `dist/codex/speckit-pro/` carry all five files. The Codex payload keeps the
   agent at `dist/codex/speckit-pro/codex-agents/implement-executor.toml` and
   flattens `codex-skills/.../references/*` into
   `dist/codex/speckit-pro/skills/speckit-autopilot/references/`. Layer 1
   enforces them through `validate-plugin-payload`,
   `validate-payload-completeness`, and `validate-payload-conformance`.
2. **Installed-cache proof.** `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/{claude,codex}/speckit-pro/`
   holds a copy of the payload tree, including all five files. Its provenance is
   pinned by `source_payload_tree_hash` in
   `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`, mirrored at
   `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json`.
   The active-path guard recomputes the hash from `dist/<product>/speckit-pro`
   and reports `source_payload_tree_hash is stale` when the pin no longer
   matches, and `tests/speckit-pro/unit/test-speckit-pro-gates.py` asserts the
   two proof files are byte-identical JSON.

`docs-site/src/content/docs/reference/source-vs-dist.md` documents the
source-versus-payload contract. `AGENTS.md` forbids hand-editing generated
payloads and installed-cache proofs.

**Verification that catches a miss**: `python3 tests/speckit-pro/run-all.py`.
Skipping the rebuild fails Layer 1; skipping the fixture and hash refresh fails
Layer 4.

**Also triggered**: `AGENTS.md` requires
`pnpm --dir docs-site reference:generate` after a tracked `.py` change under the
test tree, which refreshes `docs-site/src/content/docs/reference/tests.md`. That
surface needs `pnpm --dir docs-site install --frozen-lockfile` once per worktree.

---

## R10. Codex parity is owed on the record, not on the wording

**Decision**: both platforms produce the same header, the same entry format, and
the same additive-only and fail-open behavior. The instruction text may differ
where dispatch mechanics differ.

**Rationale**: FR-005 states this directly. Codex's `implement-executor`
already records each result as it arrives
(`speckit-pro/codex-skills/speckit-autopilot/SKILL.md:322`), so its document
needs the append instruction but no cadence change. Claude's document gains the
same per-arrival instruction on both parallel paths. The platforms now agree on
timing as well as on the record, so parity holds in the strong direction rather
than by capping the faster platform to the slower one.

**Alternatives rejected**: leave Claude at a barrier cadence and rely on
FR-005's older "the moment of append MAY differ" escape hatch. Rejected: the
escape hatch existed only to absorb a limitation that turned out not to exist,
and keeping it would have left the two platforms producing measurably different
records from the same run.

---

## R11. The plan-phase estimator projects 0 for this slice, and that is a heuristic gap

**Decision**: use 162 projected reviewable LOC, from `estimate-spec-size`, as
the authoritative budget figure. Read the plan-phase estimator's `projected`
value as not applicable to this surface rather than as a measurement.

**Rationale**: the plan-phase estimator counts a declared file as production
only when its path starts with `src/`, `app/`, `lib/`, or `scripts/`, or ends in
`.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`, or `.sql`, and it projects
`production_files x 40`. None of this repository's plugin surface matches that
heuristic: the five production files are Markdown and TOML under
`speckit-pro/`. The estimator will therefore report `production: 0` and
`projected: 0` with `status: pass` and `greenfield: false`.

This is a known shape mismatch between a JavaScript-oriented heuristic and a
Markdown plugin repository. It cannot produce a false pass that matters here,
because the real figure (162) is already far under the 400 warn line and the
diff-mode reviewability gate re-measures the actual diff at PR time.

**Alternatives rejected**: inflate the declared list with generated payload
paths so the number moves. Rejected on two counts: the estimator excludes
`dist/` as generated anyway, and padding a declared-operations block to move a
metric is dishonest.

---

## Sources

- `docs/ai/specs/.process/ART-012-design-concept.md` (Q1-Q8, including the dated
  revision note under Q2)
- `docs/ai/specs/.process/ART-012-workflow.md` (Verified Repository Facts,
  Consensus Resolution Log, Architecture Notes)
- `specs/art-012-implementation-notes-capture/spec.md` (FR-001 to FR-005,
  SC-001 to SC-006)
- `.specify/memory/constitution.md` v1.2.0 (principles II, IV, VI)
- `AGENTS.md` (Editing Boundaries, Worktree Preflight, Source Of Truth)
