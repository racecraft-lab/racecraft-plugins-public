# Phase 0 Research: Draft-PR Emission (ART-007)

**Branch**: `art-007-draft-pr-emission` | **Date**: 2026-08-17

Every decision below was resolved by reading the tree, not from memory. File
references are repo-relative and carry the line numbers the reading came from.
The Technical Context in `plan.md` carries no unresolved-clarification markers
because every unknown listed here closed against in-tree evidence.

---

## D1 — Draft mode is a third value on the existing packet `mode`, not a new contract

**Decision**: Add `"draft"` to the packet's `mode` enum and relax the
implementation-evidence requirements conditionally for that value only. One
schema, one validator family, one packet that ART-010 later upgrades in place.

**Rationale**: The contract already models "this packet is a different shape of
the same thing" once, for `split`. Copying that shape costs no new abstraction
and keeps a single packet identity across the draft-to-ready lifecycle, which is
what FR-012 needs when the draft becomes the first slice of a stack.

**Where the enum lives — two sites, both required**:

- `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json:33-36` —
  `properties.mode`, `"enum": ["single", "split"]`
- `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json:442-445` —
  `$defs.validation_result.properties.mode`,
  `"enum": ["single", "split", null]`

**The conditional pattern to copy** (`pr-packet.schema.json:215-230`):

```json
"allOf": [
  {
    "if":   { "properties": { "mode": { "const": "split" } }, "required": ["mode"] },
    "then": { "required": ["split_slice"] },
    "else": { "not": { "required": ["split_slice"] } }
  }
]
```

The schema engine that evaluates it is generic and needs no change:
`speckit-pro/speckit_pro_runner/helpers/read_only.py:2374-2378` already handles
`if` / `then` / `else`.

**Alternatives considered**:

- *A separate draft-packet schema.* Rejected: two schemas means two validator
  families and a packet identity that changes when the PR flips to ready,
  breaking FR-012's "same PR, same thread" guarantee.
- *No packet at all for the draft PR.* Rejected: the shipped PR-creation
  protocol refuses to create a PR from anything but a validated packet
  (`speckit-pro/skills/speckit-autopilot/references/post-implementation.md:372-381`),
  and `generate-pr-body` is explicitly demoted to a body-only `golden_only`
  operation whose "output alone never authorizes PR creation"
  (`references/phase-execution.md:1315-1319`).

---

## D2 — Draft relaxations must land in TWO places, because one validator is not schema-driven

**Decision**: Implement each FR-005 relaxation twice — once as a schema
conditional, once in the hand-written check pair inside the read-only validator.

**Rationale**: `validate-pr-packet-read-only` carries evidence assertions that
never consult the schema and never branch on `mode`
(`speckit-pro/speckit_pro_runner/helpers/read_only.py:2872-2875`):

```python
if not data.get("verification_evidence"):
    failures.append({"rule": "evidence.verification", ...})
if not (scope_evidence or {}).get("changed_files"):
    failures.append({"rule": "evidence.scope.changed_files", ...})
```

Relaxing only the schema would leave a valid draft packet failing here. This is
the single highest-risk finding of Phase 0: a plan that touched only the schema
would have shipped a draft mode that cannot pass its own validator.

**Fields and their current unconditional requiredness**:

| Field | Schema location | Current rule |
| --- | --- | --- |
| `verification_evidence` | `pr-packet.schema.json:66-72` | top-level required, `minItems: 1` |
| `scope_evidence.changed_files` | `pr-packet.schema.json:94-101` | required inside a required object, `minItems: 1` |
| `uat.how_to_uat` | `pr-packet.schema.json:117-120` | required inside a required object, `minLength: 1` |

**Alternatives considered**: making the read-only validator fully schema-driven.
Rejected as out of scope — it would rewrite validation for the two shipped
modes, which FR-005 and SC-008 forbid changing.

---

## D3 — The draft body's two-block shape rides the packet's own `required_headings` field

**Decision**: Make `required_headings()` mode-aware. Draft mode returns the two
FR-008 blocks; every other mode returns today's eight, unchanged.

**Rationale**: `required_headings` is already a first-class packet field
(`pr-packet.schema.json` top-level `required`, lines 7-23), and the body
structure checker *receives* it rather than deriving it — `normalize_packet_input`
passes `"required_headings": required_headings()` into
`packet_body_structure_failures`
(`speckit-pro/speckit_pro_runner/helpers/pr_emission.py:325-330`;
checker at `read_only.py:2537`). The extension point already exists; only the
producer is hardcoded:

```python
# speckit-pro/speckit_pro_runner/helpers/pr_emission.py:427-437
def required_headings() -> list[str]:
    return ["Summary", "What Changed", "Why It Matters", "How To Review",
            "How To UAT", "Verification", "Scope", "Known Gaps"]
```

FR-005 requires the two pre-existing modes to validate identically; keying the
heading set on `mode` satisfies that literally. FR-008 independently defines the
draft body as exactly two blocks, so a draft-specific heading set is required by
the specification, not a deviation from FR-005.

**The draft body is caller-supplied, so no new template file is needed.**
`normalize_packet_input` accepts a ready-made body: `body = inputs.get("body")`
and uses it verbatim when non-empty, falling back to `build_packet_body` only
when absent (`pr_emission.py:314-324`). The orchestrator composes the artifacts
index table and the resume/status block and passes them as `body`.

**Alternatives considered**:

- *Compose the draft body with `generate-pr-body`.* Rejected on evidence:
  `build_pr_body` emits `## <section>` followed by the literal `TBD`
  (`pr_emission.py:223-227`). It is a skeleton generator, not a body composer.
- *A new `draft-pr-description-template.md` alongside
  `templates/pr-description-template.md`.* Rejected: a template file buys
  nothing when the body is two generated blocks with no free-text prose, and it
  would add a shipped file to a budget already at its ceiling.

---

## D4 — Draft titles must use a lowercase scope, because two title regexes disagree today

**Decision**: Reuse `normalize_generated_title` unchanged and constrain the draft
title to a lowercase scope. Draft-mode validation checks the conventional shape
only.

**Rationale — a pre-existing, unsynchronised delta found in the tree**:

- The packet schema's pattern permits an uppercase ticket-style scope
  (`pr-packet.schema.json:254`):
  `^[a-z]+\((?:[a-z][a-z0-9-]*|[A-Z]+-[A-Z0-9][A-Z0-9-]*)\): [A-Za-z][A-Za-z0-9 ,.'()/-]+$`
- The release-readiness gate permits **lowercase scopes only**
  (`speckit-pro/speckit_pro_runner/gates/release.py:1242-1245`):
  `^(feat|fix|chore|docs|test|refactor)\([a-z0-9-]+\): .+`

A title such as `feat(ART-007): ...` passes the packet schema and **fails** the
release-readiness shape. SC-007 requires 100% of emitted titles to pass the
release-readiness check at creation time, so the draft title must be
`<type>(speckit-pro): <plain English description>` — a lowercase plugin-directory
scope, which is also what the repository agent contract requires.

**Non-goal**: reconciling the two regexes. That is pre-existing drift on a
surface this feature does not own, and changing the schema pattern would alter
validation for the two shipped modes.

---

## D5 — The orchestrator observes GitHub; the helper classifies

**Decision**: The orchestrator takes exactly one read-only observation,
`gh pr list --head <branch> --state all --json number,url,state,isDraft,headRefName`,
and passes the parsed result verbatim to `resolve-autopilot-stage` as a new
`inputs` key. The helper never shells out.

**Rationale**: No helper in `speckit-pro/speckit_pro_runner/` runs `gh` today —
every `gh` invocation in the plugin is orchestrator-run prose in SKILL.md and the
reference docs (`references/post-implementation.md:432-437`,
`references/phase-execution.md:1286-1310`). Preserving that boundary keeps the
runner deterministic, offline-testable, and inside the Python-3.11-stdlib rule
(constitution II). The established convention for caller-supplied evidence is
`inputs.<field>` on the stdin request envelope, not an argv flag — see
`normalize_scope_evidence` (`pr_emission.py:586-626`), which takes a
pre-computed `changed_files` / `reviewable_loc` object rather than running
`git diff`, and `normalize_evidence_list` (`pr_emission.py:628-651`).

There is no `--observation-json`-style flag precedent to copy, because helpers
take no argv at all: `python -m speckit_pro_runner` reserves argv for `--help`
and `--version` and reads one JSON request from stdin
(`speckit-pro/speckit_pro_runner/__main__.py:14-24`).

**Why classification belongs in `resolve-autopilot-stage`**: FR-011 requires the
draft-PR record to be parsed in exactly one place. That helper already owns
workflow-file parsing (D6), so the classifier reads the recorded identity from
the same parse that resolves the stage.

**Provenance**: this division of labour is not a planning invention. It is the
consensus resolution recorded in the Consensus Resolution Log of
`docs/ai/specs/.process/ART-007-workflow.md` during Clarify session 2, which also
fixed the closed six-status vocabulary, its precedence order, and the rule that
only an exit-0 parseable observation may yield a discrepancy. The "why" behind
the storage decision it builds on — workflow-file row only, no state-file mirror
— is the design concept's Q4 resolution in
`docs/ai/specs/.process/ART-007-design-concept.md`, which rejected a
row-plus-mirror alternative because two sinks must stay in sync and the mirror is
non-authoritative under the inherited OQ-4 decision anyway. Phase 0 changed
neither; it verified that the tree can carry them.

**Alternatives considered**:

- *A new dedicated corroboration helper.* Rejected: it would need its own copy
  of the workflow-file parser, which is the duplication FR-011 forbids.
- *Let the helper run `gh` itself.* Rejected: breaks the offline-determinism
  boundary and would make the 38 existing stage-resolution tests
  network-dependent.

---

## D6 — The `Draft PR` row parser is a near-clone of the shipped `Stage` row parser

**Decision**: Add `workflow_draft_pr_row(lines)` next to `workflow_recorded_stage`,
reading the same table with the same cell handling.

**Rationale**: The shipped reader is already exactly the right shape
(`speckit-pro/speckit_pro_runner/helpers/read_only.py:1258-1263`):

```python
def workflow_recorded_stage(lines: list[str]) -> str | None:
    for cells in workflow_table_rows(lines, AUTOPILOT_BASIC_INFO_HEADING):
        if len(cells) >= 2 and cells[0].strip("*` ").casefold() == "stage":
            return cells[1].strip("*` ") or None
    return None
```

The generic table reader `workflow_table_rows` (`read_only.py:1196-1209`) and the
heading constant `AUTOPILOT_BASIC_INFO_HEADING = "### Basic Information"`
(`read_only.py:1192`) are reused as-is. HTML comments are blanked before parsing
(`read_only.py:1193,1222`), so a commented-out example row is never evidence —
which is why FR-009's "no placeholder row in the template" rule is enforceable
rather than merely stylistic.

Absent row returns `None`, which is the legal empty state FR-009 requires and
matches the `Stage` row's own "no run yet" semantics
(`references/workflow-file-protocol.md:41-45`).

**Three near-duplicate lines beat an abstraction here** (constitution VI): the
two readers differ only in the key they match, and folding them into a generic
`workflow_scalar_row(lines, key)` is the better shape only if a third caller
appears. It has not.

---

## D7 — Corroboration rides the existing stage envelope as one nested object

**Decision**: `resolve-autopilot-stage`'s success payload gains a
`corroboration` object. The eight existing keys are untouched.

Today's payload (`read_only.py:1314-1323`):

```python
make_result(json_text({
    "tool": "resolve-autopilot-stage", "stage": stage, "source": source,
    "basis": basis, "recorded_stage": signals["recorded_stage"],
    "planning_complete": signals["planning_complete"],
    "confidence_gate_status": signals["confidence_gate_status"],
    "from_phase": parsed["from_phase"],
}))
```

The new object carries `status` (one of the closed six), `recorded` (number and
URL from the row, or null), `observed` (number and URL from the observation, or
null), `merged` (only meaningful under `pr_closed`), and `reason` (populated only
under `skipped`). It is always present, so a run that could not check is
distinguishable from a run that checked and agreed — FR-011's explicit
requirement.

**Rationale**: The envelope is additive-friendly. The outer runner envelope
(`speckit-pro/speckit_pro_runner/envelope.py:78-91`) nests helper stdout as
`data.stdout_json`, so callers that ignore the new key keep working, and
`resolve-autopilot-stage` never changes the resolved stage — corroboration is
reported, never acted on.

**Classification precedence** is fixed and first-match-wins, exactly as FR-011
orders it; only an exit-0, parseable observation may produce a discrepancy.
Everything else — tool absent, unauthenticated, cancelled, rate-limited,
unparseable — resolves to `skipped` with its reason. The full table is in
`contracts/stage-corroboration.md`.

---

## D8 — Emission order, and the boundary commit stays byte-identical

**Decision**: Implement FR-013's order literally, and change nothing about the
stage-boundary commit.

**The shipped contract that must not move**
(`speckit-pro/skills/speckit-autopilot/references/phase-execution.md:761-786`):

```text
git add specs/ <workflow-file-path> <workflow-dir>/autopilot-state.json \
  && git commit -m "chore(SPEC-XXX): close the plan stage boundary"
```

Three properties are load-bearing and stay: the message names the stage boundary
(not a phase); the staged path set is the same enumeration the per-phase
bookkeeping commits use, never the workflow *directory*; and the commit is
non-empty regardless of whether the `Stage` row changed, because the
`Confidence Gate` row always advances off pending.

**The push belongs to the terminal step.** Grepping the shipped skills for push
sites returns only `references/post-implementation.md:503,619` and
`references/phase-execution.md:1293` — all implement-stage or post-implementation.
Nothing in the plan stage pushes today, which confirms the spec's assumption and
makes the terminal step's own push the step that makes PR creation possible.

**The strict-mode short-circuit** is a return before generation, not a wrapper
around it. The blocked contract at `phase-execution.md:751-759` — non-terminal
`Confidence Gate` row, boundary commit still taken, STOP — is preserved
byte-for-byte, and no artifacts are generated and no PR is opened.

---

## D9 — Four surface trims, each verified in-tree rather than assumed

The workflow prompt asked for legitimate trims and told us to verify rather than
assume. Four held:

1. **`speckit-pro/skills/speckit-coach/templates/workflow-template.md` needs no
   edit.** The `Stage` row does not appear in that template at all (grep returns
   nothing), which is the shipped precedent for a protocol-only row. FR-009
   forbids a placeholder `Draft PR` row for the same reason.
2. **`speckit-pro/codex-skills/speckit-autopilot/references/workflow-file-protocol-codex.md`
   needs no edit.** Its headings are `Per-Phase Section Updates`,
   `Constitution + Consensus Log`, and `workflow_file State Authority` — it
   carries no `Stage` entry section. Codex documents the `Stage` row inside
   `references/phase-execution-codex.md:177-178` instead, so the Codex-side
   `Draft PR` row rule rides the same file as the Codex terminal-step change.
3. **`.gitattributes` needs no edit.** `specs/*/artifacts/**` is absent from the
   `merge=generated` list; only `specs/*/SPEC-MOC.md` is marked there
   (`.gitattributes:53`). Committed artifacts are ordinary tracked files, which
   is what the spec assumes.
4. **The duplicated schema fixture needs no edit.**
   `tests/speckit-pro/unit/fixtures/pr-packet-feature/specs/prsg-012-reviewer-ready-pr-packet-contract/contracts/pr-packet.schema.json`
   is hand-synced, but the test that binds it compares only the
   `generated_title.scope` and `.value` regex patterns
   (`tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py:901-926`).
   Adding a `mode` enum value leaves those patterns untouched.

**One trim did not hold.** Reference docs are not uniformly shared. Seven Claude
reference docs are genuinely single-copy and linked from Codex by relative path;
six exist as independently written `-codex.md` mirrors. `phase-execution.md`
(1395 lines) and `phase-execution-codex.md` (737 lines) are one of those pairs
and are not line-for-line equivalents, so the terminal-step change costs two
files, not one. No test compares their prose, so the parity is the author's
obligation.

---

## D10 — A new Codex agent file is rejected at install time unless a frozen set is updated

**Decision**: Add `"artifact-author.toml"` to `REQUIRED_CODEX_AGENT_NAMES`.

**Rationale**: `speckit-pro/speckit_pro_runner/helpers/install.py:31-44` pins a
closed frozenset of the ten Codex agent filenames, and
`load_codex_agent_bundle` (`install.py:284-307`) diffs the source directory
against it, failing with `incomplete_agent_bundle` on a **missing file or an
unexpected one**. Shipping `codex-agents/artifact-author.toml` without this edit
makes every install refuse the bundle.

This surface was not in the spec's projected file list. It is the reason the
plan's declared production count is eleven rather than the spec's projected ten.

The Claude side needs no registration: agents are discovered by directory
convention, and the generic payload sweep
(`tests/speckit-pro/layer1-structural/validate-payload-conformance.py:221,287`)
covers any newly added file without a literal-list edit.

---

## D11 — `artifact-author` frontmatter mirrors `uat-runbook-author`, read from disk

**Decision**: Mirror the shipped analogue's frontmatter shape on both platforms.

**Rationale**: The spec's Assumptions section requires confirming the pattern by
reading the file during planning rather than from memory. Read directly from
`speckit-pro/agents/uat-runbook-author.md:1-18`:

```yaml
---
name: uat-runbook-author
description: >
  ... Fail-open — on any trouble it leaves the skeleton untouched
  and never blocks PR creation.
model: sonnet
color: cyan
disallowedTools: Skill, Agent, TeamCreate, SendMessage
maxTurns: 30
effort: max
---
```

And `speckit-pro/codex-agents/uat-runbook-author.toml:1-6` — a flat TOML
document, no frontmatter fence, prompt body inside `developer_instructions`:

```toml
name = "uat-runbook-author"
description = "..."
model = "gpt-5.5"
model_reasoning_effort = "xhigh"
sandbox_mode = "workspace-write"
developer_instructions = """
```

The analogue is exact: both roles are fail-open content authors dispatched at
PR time, both edit files in place, both must never block PR creation. The
Claude-only fields (`color`, `maxTurns`, `effort`, `disallowedTools`) are
forbidden in the TOML by `validate-codex-agents.py:42,132-134`; Codex expresses
the equivalent constraint through `sandbox_mode`.

---

## D12 — Shipping outside the governed corpus restales no digest

**Decision**: Ship `artifact-author` outside the twelve-role Layer 6 corpus, as
the spec's Out of Scope section requires.

**Rationale**: The corpus is a hand-committed JSON document keyed by explicit
`role_id` to `source_path` bindings
(`tests/speckit-pro/layer6-efficiency/fixtures-codex/corpus-manifest.json`,
pinned at twelve by `tests/speckit-pro/unit/test-role-corpus-governance.py:57-75,200-207`).
It is **not** derived by scanning the agent directories, so a thirteenth file
under a new name is invisible to it and touches no `source_digest`,
`fixture_digest`, or `corpus_digest`. Registering a thirteenth role is
explicitly refused by `test_a_thirteenth_role_is_refused`.

Note that `uat-runbook-author` *is* inside the corpus. Copying its frontmatter
shape is safe; editing its file is not, and this feature does not.

---

## D13 — Selection routing is manifest-driven; the templates are consumed as-is

**Decision**: Route by the shipped manifest's `stage` and `trigger` fields. Do
not touch the gallery.

**Evidence** (`speckit-pro/artifact-gallery/manifest.json`):

| Entry | `stage` | `trigger` |
| --- | --- | --- |
| `implementation-plan` (:16-26) | `draft-pr` | `{"always": true}` |
| `spec-explainer` (:27-36) | `draft-pr` | `{"always": true}` |
| `code-approaches` (:38-47) | `draft-pr` | `{"any_of": ["competing_approaches"]}` |
| `module-map` (:49-58) | `draft-pr` | `{"any_of": ["brownfield_change"]}` |

The two trait names in the workflow prompt are **confirmed exactly**, and are two
members of a closed five-signal vocabulary declared at `manifest.json:3-9`
(the other three route final-PR artifacts). Artifact paths are derived as
`templates/<id>.html`; the entry's `source.file` names the upstream original and
is not a path to the shipped file.

**Fill regions are paired HTML comments**, `<!-- FILL:<slot>:START -->` through
`<!-- FILL:<slot>:END -->` — verified at
`speckit-pro/artifact-gallery/templates/spec-explainer.html:668,676` and
`.../module-map.html:956,1009`. Each template also carries a slot inventory
comment naming each slot's source document. Two shipped validators already
enforce all of this (`tests/speckit-pro/unit/test-artifact-gallery.py` groups
B and C; `tests/speckit-pro/unit/test-artifact-fill-regions.py` checks R1-R7),
which is why the feature can consume the contract without re-validating it.

**Trait producers**: `competing_approaches` reads from the design concept's
"Alternatives offered" blocks — present in this feature's own design concept at
`docs/ai/specs/.process/ART-007-design-concept.md`, one per Q block.
`brownfield_change` reads from the spec's declared primary surface.

---

## D14 — Fail-open has three sinks and no shared renderer to extend

**Decision**: Compose the stop report as orchestrator prose, consistent with the
one-line convention Step 0.6c already uses.

**Rationale**: There is no stop-report or run-report renderer anywhere in the
runner — no module defines one, and STOP output is composed ad hoc at each check
point. The nearest shipped convention is the single line Step 0.6c prints,
`Stage: <stage> (<source>) — <basis>`
(`speckit-pro/skills/speckit-autopilot/SKILL.md:344-363`; the Codex twin at
`speckit-pro/codex-skills/speckit-autopilot/SKILL.md:585-586`). FR-011's
"run report" line is that same convention extended by one line.

The three fail-open sinks FR-004 names are a gap row in the PR body's artifacts
index, a note in the stop report, and a note appended after the link in the
workflow file's `Draft PR` cell. Zero artifacts still opens the PR.

---

## D15 — The reviewable-LOC estimator scores this repository zero by construction

**Decision**: Report the estimator's real output, and carry `estimate-spec-size`
as the sizing evidence.

**Rationale**: `estimate-reviewable-loc` derives its projection as
`production_files * 40`, and `is_production_file`
(`speckit-pro/speckit_pro_runner/helpers/read_only.py:4185-4186`) recognises
only paths under `src/`, `app/`, `lib/`, `scripts/`, or files ending `.ts`,
`.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs`, `.sql`. This feature's surface is
Markdown, Python, and JSON under `speckit-pro/` and `tests/`, so it scores zero
production files and a projected zero LOC regardless of its real size. That is a
property of the estimator, not a claim about this slice.

The authoritative sizing is the advisory spec-size estimator, run live during
this phase against the spec's projected counts (three user stories, ten
production files, thirteen functional requirements, modify-weighted):

```json
{"estimated_loc":335,"suggested_slices":1,"status":"ok"}
```

This reproduces the figure `spec.md` records and confirms one slice.

D10 raises the production-file count to eleven, so the same estimator was run
again at that input to check the verdict survived it:

```json
{"estimated_loc":355,"suggested_slices":1,"status":"ok"}
```

The formula is `user_stories * 25 + files * 40 + frs * 15`, halved for a
modify-weighted profile
(`speckit-pro/speckit_pro_runner/helpers/read_only.py`, `estimate_spec_size`),
so one more file is worth twenty reviewable lines here. Status `ok` and one
suggested slice hold at both inputs, and both sit under the 400 warn ceiling.
The 335 stays the figure of record because it is what `spec.md` and the workflow
file cite; the 355 is the same verdict re-derived at the plan's own count.

---

## Resolved unknowns summary

| Unknown carried into Phase 0 | Resolved by |
| --- | --- |
| Where the draft mode plugs into the packet contract | D1, D2, D3 |
| Whether title validation differs by mode | D4 |
| How the `gh` observation reaches the classifier | D5 |
| How the `Draft PR` row is parsed | D6 |
| What the corroboration output looks like | D7 |
| Whether the boundary commit changes | D8 |
| Which files the change actually costs | D9, D10 |
| The authoring agent's frontmatter | D11 |
| Whether the new agent restales the Layer 6 digests | D12 |
| Template selection routing and fill-region format | D13 |
| Whether a stop-report renderer exists to extend | D14 |
| What the reviewability estimator will report | D15 |

Every unknown above is closed. No unresolved-clarification markers remain.
