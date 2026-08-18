# Implementation Plan: Draft-PR Emission

**Branch**: `art-007-draft-pr-emission` | **Date**: 2026-08-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/art-007-draft-pr-emission/spec.md`

## Summary

End the plan stage at a committed draft artifact set and an open draft pull
request whose body indexes those artifacts, then stop for human review.

Four surfaces carry it. A new `artifact-author` subagent fills the four
draft-stage gallery templates already shipped by ART-002 and writes the finished
pages into `specs/<branch>/artifacts/`. The pull-request packet contract gains a
third `draft` mode whose implementation-evidence requirements are conditionally
relaxed, copying the conditional pattern the schema already carries for
`split_slice`. The plan stage's terminal step gains an emission sequence —
generate, boundary-commit, push, create-or-refresh, record, bookkeeping-commit —
that leaves the shipped boundary-commit contract byte-identical and short-circuits
before generation on a strict-mode block. And stage auto-detect gains the
corroboration limb deferred from ART-006: the orchestrator takes one read-only
`gh` observation and hands it to the existing stage-resolution helper, which
classifies it into a closed six-status vocabulary and reports without ever
changing the resolved stage.

Everything fails open. A generation failure of any size still opens the pull
request, with the shortfall visible in the body's index, the stop report, and the
workflow file's record. The three corroboration discrepancies end the emission
attempt without creating, reopening, or rewriting anything, and without invoking
the strict-mode blocked-stop contract. No step of the emission sequence is
retried automatically either: a failed branch push stops the run before creation
with nothing on the remote, and a failed bookkeeping push leaves the pull request
standing with its record local-only. Both report through the stop report and are
recovered by the operator re-run, which the dual existence test keeps free of a
duplicate pull request.

## Technical Context

**Language/Version**: Python 3.11+, standard library only. Markdown for skills,
reference docs, and agent definitions. JSON for schemas and fixtures.

**Primary Dependencies**: None added. The runner is stdlib-only by constitution
II; the `gh` CLI is an orchestrator-side tool invoked as prose, never from a
helper.

**Storage**: Files in the repository. The workflow file's `### Basic Information`
table is the authoritative record of the pull request's identity; artifact pages
are ordinary tracked files under `specs/<branch>/artifacts/`; the packet is JSON
under `specs/<branch>/.process/pr-packets/`.

**Testing**: `python3 tests/speckit-pro/run-all.py` — Layers 1, 4, and 5, zero
failures. Layer 4 carries the helper unit tests and the packet golden fixtures;
Layer 1 carries structural and payload conformance.

**Target Platform**: Claude Code (`speckit-pro/skills/`, `speckit-pro/agents/`)
and Codex CLI (`speckit-pro/codex-skills/`, `speckit-pro/codex-agents/`).
Identical behavior on both.

**Project Type**: Coding-agent plugin. Skills and reference docs are the runtime;
Python helpers are the deterministic core.

**Performance Goals**: Not applicable. The stage is human-paced; the added work
is one `gh` query, one classification, and up to four template fills.

**Constraints**: No new Bash and no `jq` (constitution II). No edits to any of the
twelve governed Layer 6 corpus agent definitions. Plugin source changes must
account for the generated artifact contract before the work is called done.
Committed artifacts are not marked `merge=generated`.

**Scale/Scope**: 13 functional requirements, 3 user stories, 8 success criteria.
16 declared file operations across 4 surfaces.

**Reviewability Budget**: Primary surface harness/adapter, secondary docs/process;
projected reviewable LOC 335 by the advisory spec-size estimator (`ok`, 1 slice)
and 0 by `estimate-reviewable-loc`, which recognises no production file types in
this repository; 11 production files; 16 total files; budget result — within
budget on the machine gates, one file above the total-files warn line by hand
count, no split.

## Declared File Operations

- NEW speckit-pro/agents/artifact-author.md
- NEW speckit-pro/codex-agents/artifact-author.toml
- MODIFIED speckit-pro/speckit_pro_runner/helpers/install.py
- MODIFIED speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json
- MODIFIED speckit-pro/speckit_pro_runner/helpers/pr_emission.py
- MODIFIED speckit-pro/speckit_pro_runner/helpers/read_only.py
- MODIFIED speckit-pro/skills/speckit-autopilot/references/phase-execution.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md
- MODIFIED speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md
- MODIFIED speckit-pro/skills/speckit-autopilot/SKILL.md
- MODIFIED speckit-pro/codex-skills/speckit-autopilot/SKILL.md
- MODIFIED tests/speckit-pro/unit/test-autopilot-stage-resolution.py
- MODIFIED tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py
- MODIFIED tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py
- NEW tests/speckit-pro/unit/fixtures/pr-packet/valid-draft.json
- NEW tests/speckit-pro/unit/fixtures/pr-packet/bodies/valid-draft.md

Sixteen entries, and they are the whole change. The estimator reads only lines of
exactly that shape — a list marker, `NEW` or `MODIFIED`, one path, nothing after
it — so the obligations that attach to them are stated here as prose.

**What each surface carries.** The two agent definitions and the install-helper
edit are User Story 2. The schema, `pr_emission.py`, and the two packet test
files plus their fixtures are FR-005 and FR-008. `read_only.py` carries two
separate changes — the draft-mode evidence relaxation and the corroboration
classifier — and `test-autopilot-stage-resolution.py` covers the second. The five
prose files carry FR-006 through FR-013.

**Four surfaces were checked and did not need to change.** The scaffold workflow
template ships no `Draft PR` row, because it ships no `Stage` row either and
FR-009 forbids a placeholder. The Codex workflow-protocol mirror carries no
`Stage` entry section, so the Codex-side row rule rides
`phase-execution-codex.md` instead. `.gitattributes` needs no entry, because
`specs/*/artifacts/**` is not a generated path. And the duplicated packet-schema
test fixture stays as-is, because the test binding it compares only the title
regexes, which this change does not touch. Research D9 records the evidence for
each.

**One surface was discovered during planning and was not in the spec's
projection.** `speckit-pro/speckit_pro_runner/helpers/install.py` pins a closed
frozenset of Codex agent filenames and rejects a bundle containing an unexpected
one. Shipping `codex-agents/artifact-author.toml` without that edit makes every
Codex install refuse the bundle. This entry, plus the third unit-test file, is
why the count reads 11 production and 16 total against the spec's projected ~10
and ~14.

**That frozenset edit needs no test file of its own.** Checked rather than
assumed: `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py:424-441`
already covers the bundle loader, and it does so by copying the **real**
`speckit-pro/codex-agents/` directory, deleting one file, and asserting
`incomplete_agent_bundle`. It pins no literal filename list, so the new agent and
the frozenset move together and the assertion stays true. No test anywhere pins
an exact agent count — the payload gate asserts only
`bundled_agent_count >= 1` — and `install_inventory.json` does not enumerate
individual agent files. Constitution IV is satisfied through that existing
coverage, in a file this plan already declares.

**The generated-artifact contract applies.** Plugin source changes, so shipped
bytes change on both platforms. Before calling the work done:

```text
python3 scripts/refresh-release-artifacts.py
```

That rewrites `dist/claude/**` and `dist/codex/**`, the runner trust metadata
(`speckit-pro-runner.manifest.json` and `.sha256`, restaled by the two helper
`.py` edits), the installed-cache fixtures, and the payload evidence under
`docs/ai/specs/.process/`. Those paths are generated, are marked
`merge=generated`, and are excluded from the reviewability count by the gate's
own generated-path rule — which is why they are not entries above. CI's
`artifact-consistency` job fails the pull request if the regeneration is skipped.

**`--check` lies on an uncommitted tree.** `refresh-release-artifacts.py --check`
compares against the committed tree, so it exits 1 on a regeneration that is
correct but not yet committed. That exit is not a failure and resolves on commit.

**The docs reference regenerates too.** Three tracked `.py` files under
`tests/speckit-pro/` change, which restales the generated docs-site test
reference. `refresh-release-artifacts.py` does not cover it; run
`pnpm --dir docs-site reference:generate` after
`pnpm --dir docs-site install --frozen-lockfile` once per worktree.

**The Layer 6 corpus must not restale.** No governed agent definition is edited.
`artifact-author` is a thirteenth file under a new name, and the corpus is keyed
by explicit role bindings rather than a directory scan, so no digest in its chain
moves. A `source digest does not match role source bytes` failure would mean this
rule was broken.

**No script or test filename is coupled to the spec ID.** Every test entry above
is an existing file named for durable behavior; the two new fixtures follow the
shipped `valid-<mode>.json` convention.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against `.specify/memory/constitution.md` v1.2.0.

| Principle | Verdict | Evidence |
| --- | --- | --- |
| I. Plugin Structure Compliance | **Pass** | Two new agent definitions land in `speckit-pro/agents/` and `speckit-pro/codex-agents/`, the required layout. All tests stay under top-level `tests/speckit-pro/`, outside the install-facing directory. No manifest field changes. |
| II. Cross-Platform Runtime & Script Safety | **Pass** | Every code edit is Python 3.11+ stdlib. No Bash is added; the one `gh` invocation is orchestrator prose in a reference doc, which is where every existing `gh pr create` already lives. No `jq`: the observation is parsed with `--json` and handed to the helper as structured input. The `.specify/**` vendored allowlist is untouched. |
| III. Semantic Versioning | **Pass** | No manual version edit. Release-please owns the bump; the feature adds a plugin capability, which is a MINOR-class change it will infer from the conventional-commit type. |
| IV. Test Coverage Before Merge | **Pass** | Every new helper behavior gains Layer 4 unit coverage in an existing declared test file, so `suite-manifest.json` needs no new entry. The two new agent definitions are covered by the existing Layer 1 payload conformance sweep, which globs rather than pinning a literal list. |
| V. Conventional Commits | **Pass** | The stage-boundary commit keeps its shipped `chore(SPEC-XXX):` message. The bookkeeping commit and the pull-request title both use `<type>(<lowercase-scope>): <plain English description>`; research D4 records why the scope must be lowercase. |
| VI. KISS, Simplicity & YAGNI | **Pass** | The draft mode copies an existing conditional rather than inventing one. The `Draft PR` row reader is three near-duplicate lines beside the `Stage` reader rather than a premature generic row parser. No new template file, no new helper, no new stop-report renderer — the body is caller-supplied and the report is prose in the convention Step 0.6c already uses. |

**Reviewability, as the preset requires:**

- **Primary review surface**: harness/adapter — the autopilot terminal step and
  the runner helpers it calls. **Secondary**: docs/process — the two SKILL.md
  files and the reference docs. One primary surface, so the multi-surface rule
  is satisfied.
- **Within budget?** Yes on both machine gates. Run live during this phase
  against the block above, `estimate-reviewable-loc` returns:

  ```json
  {"tool":"estimate-reviewable-loc","status":"pass","projected":0,
   "declared_files":{"production":0,"new":4,"modified":12,"total_entries":16},
   "greenfield":false,
   "thresholds":{"warn":400,"block":800,"base_warn":400,"base_block":800}}
  ```

  It counts all sixteen entries and 0 production files, because
  `is_production_file` recognises only `src/`, `app/`, `lib/`, `scripts/` paths
  and JavaScript, TypeScript, or SQL extensions — none of which this repository's
  Markdown, Python, and JSON surface uses. The 0 is a property of the estimator,
  not a claim about this slice, so the advisory spec-size estimator carries the
  real sizing: run live against the final counts, it returns
  `{"estimated_loc":335,"suggested_slices":1,"status":"ok"}`, comfortably under
  the 400 warn ceiling. By hand count the change is 11 files under
  `speckit-pro/` and 5 under `tests/speckit-pro/`, 16 in all — one above the
  15-file warn line, well under the 25-file block line.
- **Split decision**: no split. The spec's ratified decision stands: this is one
  vertical slice, and every part is inert without the others — artifacts with no
  pull request reach no reviewer, a pull request with no index is not worth
  opening, and a corroboration limb has nothing to corroborate until a draft
  pull request exists. Both estimators return one suggested slice. The two-entry
  delta against the spec's projection is a planning-time refinement, itemised
  above, and does not change the verdict.
- **PR review packet source**: the draft pull request opens from a packet in the
  new `draft` mode. Its body carries the two FR-008 blocks only. The full
  reviewer packet — what changed, why, non-goals, review order, scope budget,
  traceability, verification, known gaps, rollback — is ART-010's job at the
  ready flip, filling this same packet in place rather than replacing it. The
  spec's PR Review Packet Requirements therefore bind the implementation pull
  request for this feature, which is a finished-implementation `single`-mode
  packet, and not the draft pull requests the feature emits.

**Post-Design re-check**: unchanged. Phase 1 introduced no new dependency, no new
abstraction, and no new file beyond the sixteen declared. Every design artifact
is documentation under `specs/`, which ships nothing. Complexity Tracking stays
empty.

## Project Structure

### Documentation (this feature)

```text
specs/art-007-draft-pr-emission/
├── plan.md                          # This file (/speckit-plan output)
├── spec.md                          # Input, post-clarify, 13 FRs, 0 markers
├── research.md                      # Phase 0 output — 15 decisions
├── data-model.md                    # Phase 1 output — 6 entities
├── quickstart.md                    # Phase 1 output — 7 validation scenarios
├── contracts/                       # Phase 1 output
│   ├── draft-packet-mode.md         # The third packet mode
│   ├── stage-corroboration.md       # The six-status classifier
│   ├── draft-pr-row.md              # The workflow-file row grammar
│   └── artifact-author-agent.md     # The authoring subagent
├── checklists/                      # Pre-existing
├── SPEC-MOC.md                      # Pre-existing
└── tasks.md                         # Phase 2 output (/speckit-tasks — NOT created here)
```

This run produces no `specs/art-007-draft-pr-emission/artifacts/` directory. The
feature builds the emission; it does not yet run it. The plan stage that closes
this spec uses the pre-ART-007 terminal step.

### Source Code (repository root)

```text
speckit-pro/                                     # the installed plugin
├── agents/
│   └── artifact-author.md                       # NEW — Claude authoring subagent
├── codex-agents/
│   └── artifact-author.toml                     # NEW — Codex mirror
├── artifact-gallery/                            # read-only input, ART-002, unchanged
│   ├── manifest.json                            #   stage + trigger routing
│   └── templates/                               #   4 draft-pr pages, FILL markers
├── skills/speckit-autopilot/
│   ├── SKILL.md                                 # Step 0.6c corroboration line
│   ├── contracts/pr-packet.schema.json          # mode enum + draft conditional
│   └── references/
│       ├── phase-execution.md                   # terminal step: emission sequence
│       └── workflow-file-protocol.md            # the `Draft PR` entry
├── codex-skills/speckit-autopilot/
│   ├── SKILL.md                                 # Step 0.6c corroboration line
│   └── references/
│       └── phase-execution-codex.md             # terminal step + `Draft PR` row
├── skills/speckit-coach/templates/
│   └── workflow-template.md                     # unchanged — no placeholder row
└── speckit_pro_runner/helpers/
    ├── pr_emission.py                           # mode gate, mode-aware headings
    ├── read_only.py                             # draft relaxation + corroboration
    └── install.py                               # Codex agent bundle registration

tests/speckit-pro/
├── unit/
│   ├── test-autopilot-stage-resolution.py       # six statuses, precedence, row parsing
│   ├── test-speckit-pro-read-only-helpers.py    # draft packet validation
│   ├── test-speckit-pro-mutation-helpers.py     # draft packet emission
│   └── fixtures/pr-packet/
│       ├── valid-draft.json                     # NEW
│       └── bodies/valid-draft.md                # NEW
└── suite-manifest.json                          # unchanged — no new test file

dist/claude/**, dist/codex/**                     # generated, regenerate, do not edit
```

**Structure Decision**: Single project, existing layout, no new directories under
`speckit-pro/`. The feature extends four surfaces that already exist and adds two
files to two directories that already exist. The one structural fact worth stating
is the asymmetry in the Codex mirror: reference docs are not uniformly duplicated.
Seven Claude reference docs are single-copy and linked from Codex by relative
path; six exist as independently written `-codex.md` mirrors, and
`phase-execution` is one of those pairs. The terminal-step change therefore costs
two files, and no test compares their prose, so keeping them in step is the
author's obligation rather than CI's.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Every principle passes on its own terms, and the table is
intentionally empty.
