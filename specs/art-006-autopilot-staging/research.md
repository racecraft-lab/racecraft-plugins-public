# Phase 0 Research: Autopilot Staging

Every unknown in the Technical Context is resolved, and no clarification marker
remains anywhere in this feature's artifacts. The Clarify phase closed with 31
normative items and zero open markers; its Round 2 tiebreaks are recorded in
`docs/ai/specs/.process/ART-006-workflow.md:361-392`. This document records the
decisions the *plan* had to make on top of those, each with the alternative that
lost and why.

---

## D1 — Where stage resolution lives

**Decision.** A registered runner read-only operation named
`resolve-autopilot-stage`, implemented in
`speckit-pro/speckit_pro_runner/helpers/read_only.py` and registered in
`speckit-pro/speckit_pro_runner/helpers/registry.py:171-178`, reached by
operation identifier from both distributions at opening preparation.

**Rationale.** FR-012 settles this by Round 2 tiebreak (spec.md:281-297). The
model already exists one step away: `resolve-confidence-mode` is registered at
`registry.py:171`, implemented at `read_only.py:1081`, and invoked from the
Claude skill at `SKILL.md:328-336` and the Codex skill at
`codex-skills/speckit-autopilot/SKILL.md:572` — the same opening-preparation
step, the same argv-in/decision-out shape, the same fail-fast-on-conflict
behaviour. Copying a proven shape costs less review than inventing one.

**Alternatives considered.**

- *Inside the phase-coverage guard.* Rejected at the Round 2 tiebreak. The
  guard's `main()` accepts only `--workflow`, `--state`,
  `--expected-base-commit`, `--expected-head-commit`, and `--rule`
  (`validate-autopilot-phase-coverage.py:4004-4022`) — it is a consistency
  checker over two already-resolved inputs, with no argv input to resolve *from*.
- *Two prose descriptions, one per distribution.* This is the status quo the
  spec exists to end. Nothing in CI diffs the two `SKILL.md` bodies
  (spec.md:466-467), so prose parity is unverifiable by construction.
- *A new dedicated module under `helpers/`.* Rejected — see D2.

---

## D2 — How the guard consumes the resolver

**Decision.** `validate-autopilot-phase-coverage.py` inserts the plugin root on
`sys.path` and imports the resolver as a normal package import
(`from speckit_pro_runner.helpers.read_only import ...`). When the import fails,
the stage-mirror check returns an empty error list rather than a violation.

**Rationale.** The plugin root is `Path(__file__).resolve().parents[3]` from the
guard, which is `speckit-pro/` in the repository and `<plugin-root>/` in an
installed tree — the same relative position in both layouts, so one expression
works everywhere. A package import is required rather than the
`importlib.util.spec_from_file_location` trick used at
`tests/speckit-pro/layer1-structural/validate-workflow-status-evidence.py:270-280`,
because `read_only.py:20` uses the relative import `from ..envelope import ...`,
which file-location loading cannot satisfy without a parent package.

The graceful skip is not an invention: `validate_state_status`
(`validate-autopilot-phase-coverage.py:3930-3943`) already skips rather than
fails "whenever the validator is copied out of the repository", explicitly so an
extracted copy "cannot manufacture a false violation". The stage check adopts the
same posture for the same reason. Inside the repository and inside an installed
plugin the runner ships beside the guard, so the skip never fires in the paths
that matter, and the agent-independent Layer 1 gate covers the tree regardless of
whether any agent runs the guard at all.

**Alternatives considered.**

- *A new `helpers/autopilot_stage.py` module holding the pure functions.* Would
  give the guard a narrower import and a faster load. Rejected on constitution
  §VI: it adds a file and an indirection layer for a three-value decision, and
  §VI's YAGNI clause forbids "wrapper layers unless migration is planned and
  documented". The repository's established shape is that read-only helper logic
  lives in `read_only.py`; `resolve_confidence_mode`, `confidence_gate`, and
  `estimate_reviewable_loc` all sit there.
- *Restating the resolution rule inside the guard.* This is exactly the drift
  FR-012 forbids.

---

## D3 — Registering an operation with no Bash ancestor

**Decision.** Add `resolve-autopilot-stage` to `EXPECTED_HELPERS` and to
`fixture-manifest.json`, add the authoritative request fixture at
`tests/speckit-pro/unit/fixtures/read-only-helpers/requests/resolve-autopilot-stage.json`,
and introduce a named carve-out set in
`tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` for operations
that were never Bash scripts.

**Rationale — this is the least obvious cost in the slice, so it is worth stating
plainly.** `test_fixture_manifests_cover_registered_helpers` asserts three
couplings (`test-speckit-pro-read-only-helpers.py:338-380`):

1. `fixture_ids == EXPECTED_HELPERS` — exact list equality, so a new operation
   without a fixture-manifest record fails the suite.
2. `bash_ids == [h for h in EXPECTED_HELPERS if h != "helper-registry-dispatch"]`
   — every operation except the registry dispatcher must have a Bash-reference
   record.
3. Each Bash-reference record's `source_script` must end in `.sh` (`:379`).

Every operation registered so far was a *port* of a deleted `.sh` script, so
assertion 2 held for free. `resolve-autopilot-stage` is new behaviour with no
predecessor, so satisfying assertion 2 would mean writing a `source_script` path
for a file that never existed — fabricated provenance in a manifest whose entire
purpose is recording provenance. A `NO_BASH_ANCESTOR` frozenset excluded from the
comprehension is one constant and one expression, and it states the truth.

Nothing executes `source_script`; the test only checks the suffix
(`:379`), which confirms the manifest is a provenance record rather than a live
comparison harness. `estimate-spec-size` already points at
`speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh`, a file the
repository deleted.

**Alternatives considered.**

- *Invent a plausible `.sh` path.* Rejected: it records a lie in the
  provenance manifest, and root `AGENTS.md` treats hand-edited generated payloads
  and false proof data as blocking.
- *Skip registration and call the resolver as a plain function.* Rejected:
  FR-012 requires reachability "by operation identifier from both
  distributions", which is what registration means.

---

## D4 — Resolver output shape

**Decision.** Structured JSON on stdout, not a bare token.

**Rationale.** `resolve-confidence-mode` returns bare text (`"strict\n"`,
`read_only.py:1087`) because its consumer needs one value. Stage resolution has
three consumers with three needs: the orchestrator needs the stage token, FR-006
requires reporting "the resolved stage **and its basis** before phase work
begins", and the mirror check needs the workflow file's recorded value
separately from the resolved one. Constitution §VI mandates a structured parser
over text munging, and every other multi-field operation in the registry —
`confidence-gate`, `estimate-reviewable-loc`, `reviewability-gate` — already
emits JSON.

**Alternatives considered.** *Bare token plus a second call for the basis.*
Rejected: two reads of the same file can disagree, which is the exact class of
bug this spec exists to close.

---

## D5 — Conflict rules and exit codes

**Decision.** Exit 0 with the envelope on success; exit 2 with a diagnostic on
any pre-flight rejection. Rejections are: an unrecognised `--stage` value; a
repeated `--stage` with differing values; and a `--from-phase` naming a phase
outside the explicitly named stage's range.

**Rationale.** FR-007 requires rejection "during opening preparation with a
non-zero exit … before any phase work begins". `resolve_confidence_mode` already
sets the precedent for exactly this shape: mutually exclusive flags return exit 2
with a one-line `error:` message (`read_only.py:1084-1085`), and the Claude skill
STOPs the run on that exit code before Phase 0 (`SKILL.md:331-333`). The
rationale is spelled out at `references/phase-execution.md:573-578` — resolve
once at start "so `--strict --advisory` conflicts fail fast before any phase
work happens, instead of surfacing 6 phases in". The same argument applies
verbatim to a stage conflict.

`--from-phase` *inside* the resolved stage's range stays legal and only moves the
starting point, per the spec's edge case at spec.md:134-136 and the pinned Codex
sentence "`--from-phase` changes only the starting index"
(`validate-codex-skills.py:295`). Widening or narrowing the range would break
that pinned sentence.

---

## D6 — The `Stage` row, and why the workflow template is untouched

**Decision.** The `Stage` row is written into `### Basic Information` by the
autopilot at resolution time. `speckit-pro/skills/speckit-coach/templates/workflow-template.md`
is **not** modified.

**Rationale.** FR-016 fixes the entry precondition: "at scaffold time the stage
entry is absent, and absence means 'no run yet'". A template row would make every
scaffolded file carry the entry from birth, contradicting that precondition and
the FR-008a rule that absence resolves through ordinary auto-detection. It also
removes a file from the change set.

The carrier is right for a mechanical reason recorded during the re-grill: the
`### Basic Information` table is a scalar `| Field | Value |` table already
parsed for `Branch` by `speckit-pro/skills/speckit-status/SKILL.md:96`, whereas
the `## Workflow Overview` status table has two parsers reading its row shape —
`validate-workflow-status-evidence.py:238-261` and
`validate-autopilot-phase-coverage.py:3878-3921` — so adding a row there would
disturb both (`docs/ai/specs/.process/ART-006-workflow.md:130-136`).

**Alternatives considered.** *A commented-out template row as a hint.* Harmless
to parsers (both blank HTML comments before scanning), but it adds a file for
documentation value only, and the same explanation belongs in
`references/workflow-file-protocol.md`, which is already being edited.

---

## D7 — Codex word budget arithmetic

**Decision.** Two `SKILL.md` edits totalling ≈24 words; all stage prose in
`references/phase-execution-codex.md`.

**Measurement.** Re-measured 2026-08-04 against the current file:

```text
python3 -c "import sys,pathlib; sys.path.insert(0,'tests/speckit-pro/lib');
import structural_helpers as sh;
b=sh.body(pathlib.Path('speckit-pro/codex-skills/speckit-autopilot/SKILL.md').read_text().splitlines());
print(len(b.split()))"
→ 7671        # cap 8000, headroom 329
```

`structural_helpers.body` (`tests/speckit-pro/lib/structural_helpers.py:44-57`)
returns everything after the second `---` fence and does **not** strip code
fences, so a token added inside the argv fence counts. `[--stage plan|implement|full]`
has no internal whitespace, so it is one `.split()` token. The pointer sentence
is ≈23 words. Post-edit projection ≈7695 of 8000.

The cap applies to the body alone; referenced files are uncapped and are still
folded into `runtime_doc` at `validate-codex-skills.py:235-242`, which is what
the four string-pinned assertions read (`:292`, `:295`, `:306-310`, `:313-318`).
So moving prose into `phase-execution-codex.md` costs nothing in coverage and
everything in headroom.

---

## D8 — Test filename and the live-family rule

**Decision.** `tests/speckit-pro/unit/test-autopilot-stage-resolution.py`.

**Rationale.** The constraint is real but narrower than "no filename may contain
`art`". `_contains_repository_spec_id` at
`tests/speckit-pro/unit/test-unit-layout.py:143-148` searches for
`{family}[-_]\d{3}[a-z]?` — a family token followed by a separator and three
digits. `art-006` fails; a bare substring does not match. The chosen name
contains no `art` substring at all and no digits, so it is safe under both the
strict and the loose reading, and it names durable capability rather than a
temporary spec ID as root `AGENTS.md` requires.

---

## D9 — Reviewability re-estimate at G3

**Decision.** 430 projected reviewable LOC. **Warn, within budget, one slice.**

**Method and why two numbers appear.** The workflow file directs a G3 re-estimate
with `estimate-reviewable-loc` (`ART-006-workflow.md:157-158`). Run against this
plan's Declared File Operations block, that helper returns
`projected: 0, production: 0, status: "pass"`. That is not a real zero: its
`is_production_file` heuristic (`read_only.py:3939-3940`) counts a path only if it
starts with `src/`, `app/`, `lib/`, or `scripts/`, or ends in a TypeScript,
JavaScript, or SQL extension. This repository's shipped surface is Python under
`speckit-pro/speckit_pro_runner/` and Markdown under `speckit-pro/skills/`, so
none of it registers. Reporting 0 would be dishonest by omission.

The ratified 382 came from a different instrument — the modify-weighted
`estimate-spec-size`, whose formula is
`user_stories*25 + files*40 + frs*15`, halved for `new_vs_modify: modify`
(`read_only.py:1065-1073`). It reproduces exactly from the workflow's declared
signals (`ART-006-workflow.md:146-149`): 3 stories, 12 files, 14 FRs →
`(75 + 480 + 210) // 2 = 382`. Re-running the *same* instrument with the G3-real
signals keeps the numbers comparable:

| Signals | Arithmetic | LOC | Slices |
|---|---|---|---|
| Ratified at scaffold (3 stories, 12 files, 14 FRs) | `(75 + 480 + 210) // 2` | 382 | 1 |
| **G3 actual (3 stories, 11 shipped-source files, 23 FRs)** | `(75 + 440 + 345) // 2` | **430** | 2 (advisory) |
| G3 with all 17 authored files counted | `(75 + 680 + 345) // 2` | 550 | 2 (advisory) |

**Why the number grew, and why it is still one slice.** Files fell from 12 to 11;
the growth is entirely the FR term, 14 → 23. All nine additions are lettered
sub-clauses the Clarify phase attached to requirements that already existed —
FR-008a, FR-008b, FR-009a, FR-010a, FR-012a, FR-014a, FR-015a, plus the carve-outs
inside FR-010 and FR-013. They *constrain* the same work rather than adding
capability, and the estimator's flat +15-per-FR term cannot see that distinction.
FR-010's carve-out is described in the spec itself as "costing zero implementation
lines" (spec.md:247-249).

Against the constitution's thresholds
(`reviewability_gate`, `read_only.py:966-980`):

| Dimension | Value | Warn | Block | Verdict |
|---|---|---|---|---|
| Reviewable LOC | 430 | 400 | 800 | warn |
| Production files | 0 (estimator classification) | 6 | 8 | pass |
| Total files | 17 | 15 | 25 | warn |
| Primary surfaces | 1 (harness/adapter) | 1 | 1 | pass |

Two warnings, no blockers — the same posture the setup gate recorded at scaffold
(`ART-006-workflow.md:139-141`). The primary-surface dimension, the one the
constitution treats as an unconditional blocker, stays at one.

**Measured, not asserted.** All three helpers were run against this plan on
2026-08-04; commands are in [quickstart.md §2](./quickstart.md#2--reviewability-re-check-g3).

```json
{"tool":"estimate-reviewable-loc","status":"pass","projected":0,
 "declared_files":{"production":0,"new":2,"modified":15,"total_entries":17},
 "greenfield":false}

{"estimated_loc":430,"suggested_slices":2,"status":"warn"}

{"mode":"setup","status":"warn","pass":true,"reviewable_loc":430,
 "production_files":0,"total_files":17,"primary_surface_count":1,
 "primary_surfaces":["harness/adapter"],
 "warnings":["reviewable LOC 430 exceeds warn threshold 400",
             "total files 17 exceeds warn threshold 15"],
 "blockers":[]}
```

`suggested_slices: 2` is advisory output from a formula that cannot distinguish a
requirement that adds work from one that forbids it. The split decision is the
paragraph above, not the integer.

Splitting is rejected for the reason spec.md:369-375 already gives and which the
real file list confirms: the vertical is argv → resolution → phase-loop bounds →
durable state → both distributions, and every cut produces a PR whose behaviour
cannot be reviewed without the other half. The three test-registry files
(D3) are a fixed toll on registering *any* operation and would be paid by
whichever slice carried the resolver.

---

## D10 — Out-of-stage task marking

**Decision.** `skipped: <reason>` in the entry's **status** field, entry name
byte-identical, applied by a planning-stage run to the implementation phase and
every post-implementation entry.

**Rationale.** Three of the four constraints were verified against the shipped
validator during Clarify (spec.md:265-280) and none is negotiable:

- The status field, not the name — the coverage guard matches
  post-implementation checkpoints by exact name equality, so a prefixed name
  reads as a *missing* checkpoint and would fail every planning-stage run at the
  pre-final audit.
- No `pending` substring in any casing — the guard flags any string value
  containing it case-insensitively.
- The `skipped: <reason>` shape is already the established spelling for absent
  extensions (`references/task-list-canonical.md:3` and `:56`, and Codex
  `SKILL.md:627`), so one search finds both kinds of skip.

The canonical list is never truncated (spec.md:265-266); every entry stays
visible with an honest status.

---

## D11 — Terminal commit identity

**Decision.** A distinct commit taken after G6.5 resolves, staging the same
enumerated path set as the per-phase commits, with a message naming the stage
boundary rather than a phase.

**Rationale.** G6.5 runs "After Phase 6 commits and before Phase 7 begins"
(`references/phase-execution.md:563-565`), so the analyze-phase commit is already
taken by the time the gate produces a verdict. Renaming that commit would leave
the verdict uncommitted. Emptiness is not a risk: the confidence-gate row always
advances off its pending state, so the commit has content whether or not the
`Stage` value changed (spec.md:217-220) — which is why the conditional second
`Stage` write needs no empty-commit escape hatch.

The staged path set is the explicit trio already used at
`speckit-pro/skills/speckit-autopilot/SKILL.md:436`
(`git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json`) and
never the workflow *directory*, which also holds untracked run byproducts — a
failure that passes locally and fails only on a clean checkout
(spec.md:230-235).

---

## Carried forward, not re-derived

These were settled before planning and are recorded here only so the plan is
self-contained.

| Item | Resolution | Source |
|---|---|---|
| Durable stage store | Workflow file `Stage` row; state file mirrors for one run | Re-grill Q9; `contracts/autopilot-state-status.schema.json` |
| Codex stage prose location | `references/phase-execution-codex.md` | Re-grill Q10 |
| Verification surfaces | Extend the shipped Layer 1 validator + one new unit test | Re-grill Q11 |
| Resolver substrate | Registered runner operation, not the guard | Clarify S2/R1 Round 2 |
| Argument-parity assertion | The new unit test, not the parity validator | Clarify S2/R2 Round 2 |
| Claude usage-synopsis repair | Fix in this slice; one line, no gate change | Clarify S2/R3 Round 2 |

## Known defect, deliberately not fixed here

The store-precedence documentation at
`speckit-pro/skills/speckit-autopilot/SKILL.md:672-676` names
`autopilot-state.json.workflow_file` as authoritative and quotes a failure
message for a mismatch. That check is inert under every invocation the phase loop
issues: its error key appears in no tuple of `RULE_PROBLEM_KEYS`
(`validate-autopilot-phase-coverage.py:238-247`), and `main()` computes the exit
code only from the selected rule's keys (`:4040-4042`). Verified during Clarify by
direct execution against a state file naming a different specification — the
guard exits 0 and reports `pass`, with and without the scoping flag
(`ART-006-workflow.md:383-392`).

This slice does **not** fix it; it is out of scope and deserves its own issue
against the plugin. FR-014a exists so this feature's own check does not reproduce
the defect, which is why the plan registers `stage_mirror_errors` inside the
`status-evidence` tuple rather than merely computing it.
