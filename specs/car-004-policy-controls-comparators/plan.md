# Implementation Plan: CAR-004 Policy Controls and Adaptive Comparators

**Branch**: `car-004-policy-controls-comparators` | **Date**: 2026-07-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/car-004-policy-controls-comparators/spec.md`

## Summary

Freeze the three AC-2.17 policy controls — unpinned, adaptive, and
orchestration-changing — and the rules CAR-011 will later apply to them, as two
new additive, content-addressed JSON Schema contracts with committed frozen
instances, standard-library validators, deterministic replay fixtures, a
reserved-partition guard, and a machine-verified twin-handoff record.

The technical approach is the schema + lib + replay-fixture pattern CAR-003
already established in `tests/speckit-pro/layer6-efficiency/`. Two new schema
documents land beside the frozen CAR-003 set in `contracts-claude/`; two new
`claude_*.py` validator modules land in `lib/`; four committed JSON instances land
in a new `fixtures-controls/`; three durable-named unit tests land in
`tests/speckit-pro/unit/` and are registered at Layer 4. Every reference to a
CAR-003 contract is a data-level `{id, digest}` binding, never a `$ref` — the
repository validator resolves only local `#/$defs/` and fails closed on anything
else, and FR-004/FR-005 require additive-only reference anyway. Nothing under
`speckit-pro/` changes, so no plugin runtime, payload, or shipped default moves.

## Technical Context

**Language/Version**: Python 3.11+, standard library only (constitution
principle II). No third-party `jsonschema`; contract validation is driven from
the schema document itself, as `lib/claude_trace_schema.py` already does.

**Primary Dependencies**: In-repo only. Read-only reuse of frozen CAR-003
modules — `canonical_json` and `record_digest` from `lib/claude_successor_freeze.py`
(one FR-033 preimage rule for every digest in the program), and
`build_partition_registry_entry` / `register_partitions` /
`objective_set_digest` from `lib/claude_experiment_policy.py`. Frozen enums are
read live from `contracts-claude/score-bundle.schema.json` rather than restated
in Python, so a mirrored enum and a CAR-004 check can never drift apart silently;
FR-010a makes that live read fail closed on a membership change instead of
absorbing it. The two frozen derivations FR-010c checks against — the
failure-code-to-plane mapping and the candidate-plane terminal-state pairing —
are likewise imported read-only from `lib/claude_score_bundle.py`, which already
derives the plane from the code rather than authoring it beside the code, so the
consistency check reads the same source the contract does instead of a second
transcription of it. `service_reroute` and its non-scorable disposition reason
(FR-015a) come from that module's frozen constants for the same reason.
Both partition entries are produced by the frozen builder and
registered through `register_partitions`, so FR-025a's closed type set and
FR-025b's disjointness are enforced by the machinery CAR-003 already uses rather
than by a parallel check. Every `{id, digest}` binding into a frozen CAR-003
document is re-verified by recomputing that document's digest from its committed
bytes (FR-005a), which is what turns FR-005 from a review convention into a
suite failure.

The live-integration requirements add no dependency but do pin four further
frozen surfaces, all read live from their committed schema documents rather than
restated in Python for the same anti-drift reason: the cache diagnostic's
`observed_cache_isolation` object and its closed status set (FR-032a), the
configured-route proof's served `model`, `effort`, and `candidate_route_id`
(FR-031a), the environment contract's pinned parent session and its
`claude_code_subagent_model_unset` observation (FR-031a), and the shared trace's
`raw_token_vector`, `wall_time_ms`, and `parent_child_graph` (FR-016d, FR-016e,
FR-031a). The `parent_child_graph` is a member of the shared treatment-record
contract that the frozen Claude-side CAR-003 runner already binds, not of the
CAR-002 Claude trace contract, which carries only a nullable parent-session
configuration string; FR-016d keeps the two apart and the CAR-004 unit boundary
is checked for agreement against the shared graph alone. Because `wall_time_ms`
is declared as a bare nullable integer, FR-031a's parallel observable does not
infer its meaning: the orchestration control's frozen child shape declares that
every unit member's wall time is its full elapsed window, and a null anywhere in
the compared set records the demonstration as not made rather than as passed.
The `authentication_mode` member is read from the Claude-side contract whose
enumeration is `subscription | api_key`, never from the shared environment
contract whose enumeration is `chatgpt_subscription | api_key`; FR-030c pins
which one, and the FR-010a set-equality discipline covers it.

**Storage**: JSON documents on disk. Schemas in
`tests/speckit-pro/layer6-efficiency/contracts-claude/`; frozen instances and
replay fixtures in `tests/speckit-pro/layer6-efficiency/fixtures-controls/`.
Per-run live-smoke output is written under
`tests/speckit-pro/layer6-efficiency/results/`, which the existing layer6
`.gitignore` already excludes wholesale (`results/*`, with a single named
allow-rule for the CAR-003 consolidated baseline). CAR-004 commits no smoke
output at all, so that `.gitignore` needs no edit.

**Testing**: `unittest`, dispatched as `python-module` at Layer 4 through
`tests/speckit-pro/suite-manifest.json`. Iteration check:
`python3 tests/speckit-pro/run-all.py --layer 4`. Structural check:
`python3 tests/speckit-pro/run-all.py --layer 1`. Full gate before PR:
`python3 tests/speckit-pro/run-all.py`.

**Target Platform**: Developer and CI workstations running the repository test
suite (macOS and Linux). The three live smoke runs are developer-local and
operator-invoked, never CI.

**Project Type**: Repository-only validation assets for an evaluation harness.
No application, service, or user-facing surface.

**Performance Goals**: The Layer 4 additions stay deterministic and fast — no
network, no subprocess, no live model call. Replay fixtures are bounded to a
small closed case set following the CAR-003 precedent (six cases), so suite cost
does not scale with accumulated evidence.

**Constraints**: Additive-only against the frozen CAR-003 contract set; no new
telemetry field; no `$ref` outside a document's own `#/$defs/`; no script or test
filename coupled to the spec ID; no new Bash or `jq` dependency; live smoke must
run on the subscription authentication path, must never require an API key, and
is refused as evidence when the observed mode is `api_key` rather than merely
noted and kept — the observed mode is still recorded on the refused record, so
a refusal stays auditable and the remedy is a re-run rather than a relabel
(FR-030c).
One preimage rule governs every digest this feature records — the frozen
`record_digest` over canonical JSON with the record's own digest member excluded
(FR-002a) — and no second rule may be coined. Every value inside a hash-relevant
object is frozen in the spec, so Implement chooses no numeric (FR-030a). The
error-handling decision semantics are frozen in the spec for the same reason,
because two conforming implementations must fold identical evidence to the same
verdict: the row-resolution precedence and the two map-consistency rules
(FR-010b, FR-010c), the clean-pass streak accounting (FR-012a), the bound scope
and the terminal state each bound breach records (FR-014a), the reroute
observable (FR-015a), and the aggregation unit's membership (FR-016d). Implement
serializes them; it decides none of them, and each is an FR-034 category 7
handoff entry.

The live-integration decision semantics are frozen on the same terms, because
they decide what counts as evidence that a control ran at all: the raw-token
member set and the parent-plus-children rule for the reasoning member and the
two cache-diagnostic quantities, with the unobserved-rather-than-zero
disposition (FR-016e); the scope each smoke bound is counted over, the
elapsed-versus-additive reading of the wall clock, and the rule that a child
dispatch consumes no attempt (FR-030b); the identified frozen
`authentication_mode` member and its constraining reading (FR-030c); the
read-back rule and the three exact-treatment observables, plus the frozen
no-subagent-override precondition (FR-031a); and the frozen cache-isolation
observable with its pairwise scope and three dispositions (FR-032a). Each is
likewise an FR-034 category 7 entry, and none of them adds a member to a frozen
CAR-003 document.

**Scale/Scope**: Two contract documents, three frozen controls, one comparison
contract, two partition registry entries, one replay fixture set, three unit
test modules, one operator smoke script, one twin-handoff record.

**Reviewability Budget**: Primary surface: harness/fixtures.
Projected reviewable LOC 250; production files 0; total files 15; result pass.

## Declared File Operations

- NEW tests/speckit-pro/layer6-efficiency/contracts-claude/policy-control-registry.schema.json
- NEW tests/speckit-pro/layer6-efficiency/contracts-claude/control-comparison.schema.json
- NEW tests/speckit-pro/layer6-efficiency/lib/claude_policy_controls.py
- NEW tests/speckit-pro/layer6-efficiency/lib/claude_control_comparison.py
- NEW tests/speckit-pro/layer6-efficiency/fixtures-controls/policy-control-registry.json
- NEW tests/speckit-pro/layer6-efficiency/fixtures-controls/control-comparison.json
- NEW tests/speckit-pro/layer6-efficiency/fixtures-controls/partition-registry-entries.json
- NEW tests/speckit-pro/layer6-efficiency/fixtures-controls/control-replay.json
- NEW tests/speckit-pro/layer6-efficiency/run-control-smoke.py
- NEW tests/speckit-pro/unit/test-policy-control-contracts.py
- NEW tests/speckit-pro/unit/test-control-comparison-dominance.py
- NEW tests/speckit-pro/unit/test-twin-handoff-completeness.py
- MODIFIED tests/speckit-pro/suite-manifest.json
- NEW docs/ai/specs/.process/CAR-004-twin-handoff.md
- MODIFIED docs-site/src/content/docs/reference/tests.md

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | How this plan satisfies it | Status |
|-----------|-------------|----------------------------|--------|
| I. Plugin Structure Compliance | Repository-only tests live under top-level `tests/<plugin>/`, outside the install-facing plugin directory | Every delivered asset lands under `tests/speckit-pro/` except the twin-handoff record, which is cross-platform coordination and lands in `docs/ai/specs/.process/`. Nothing under `speckit-pro/` is touched. | Pass |
| II. Cross-Platform Runtime & Script Safety | Python 3.11+ standard library, structured parsers, no new Bash or `jq` | Two validator modules and three unit tests use `json`, `hashlib`, `re`, `pathlib`, `datetime`, `unittest` only. JSON is parsed with the `json` module. No shell is invoked. No file under `.github/workflows/` changes. | Pass |
| III. Semantic Versioning | `plugin.json` is the single source of truth; manual version edits prohibited | No plugin manifest or version field is touched. The new contracts carry their own `schema_version` constant, which is contract versioning, not plugin versioning. | Pass (not engaged) |
| IV. Test Coverage Before Merge | New Python helpers have Layer 4 unit coverage; layer membership declared in `suite-manifest.json` | Three new Layer 4 modules cover both validators, the replay fixtures, the partition guard, and the twin-handoff derivation. All three are registered in `suite-manifest.json`. | Pass |
| V. Conventional Commits | `type(scope): description`; PR title is the squash commit | Commits and the PR title use the `speckit-pro` scope with a plain-English description, validated against the release-readiness gate before the PR is marked ready. | Pass |
| VI. KISS, Simplicity & YAGNI | Simplest approach; no speculative abstraction; structured JSON parsing | The control set is closed at three with no fourth arm. One fail-closed schema engine is shared between the two validator modules rather than duplicated, following the precedent by which `claude_experiment_policy.py` imports its digest primitives from `claude_successor_freeze.py`. No new lib module exists solely to be shared. Replay cases are bounded. | Pass |

**Post-Phase-1 re-check**: Pass. The Phase 1 design added no new dependency, no
new runtime surface, and no module beyond the two validators already declared.
The reserved partition reuses the frozen CAR-003 partition-registry builder
rather than coining a parallel registry, which removed a file rather than adding
one.

### Review surfaces

- **Primary surface: harness/fixtures** — `tests/speckit-pro/layer6-efficiency/`
  and `tests/speckit-pro/unit/`.
- Secondary review area: `docs/ai/specs/.process/CAR-004-twin-handoff.md`,
  cross-platform coordination rather than repository validation, and excluded
  from the estimator by the `.process/` generated-path rule.

### Budget position and split decision

The plan-phase estimator projects from declared **production** files, and this
slice declares zero: nothing lands under `src/`, `app/`, `lib/`, or `scripts/`,
and nothing carries a `.ts`, `.js`, or `.sql` suffix. Fifteen declared entries
sit at the 15-file warn threshold without crossing it, and far below the 25-file
block threshold. The ratified setup-gate reading of 2026-07-27 stands unchanged.

**Split decision: no split.** This is one vertical slice and the spec's single
user story. The three controls, the comparison rule, the reserved partition, and
the twin-handoff record are one freeze: shipping half of it would publish a
comparator set that CAR-011 could not apply and would leave the un-frozen half
authorable after the static core's results are visible, which is the exact
failure this feature exists to prevent. No follow-up spec IDs or deferred issue
IDs are created.

### Review load (informational, not a budget figure)

A reviewer should expect roughly 2,200–2,700 changed lines across the fifteen
entries, dominated by declarative JSON — two schema documents and four frozen
instances — plus three unit test modules. The upper end moved after the
llm-integration checklist closed its gaps into FR-016e, FR-030b, FR-030c,
FR-031a, and FR-032a: those add validator branches and smoke-record members but
no new file, so the declared file operations and the zero-production-file
estimator reading are unchanged. That volume is genuine and is called
out here so nobody is surprised at PR time; it is not reviewable production LOC
under this repository's convention, and the PR-time diff-mode reviewability gate
is the authoritative check on it. The recommended review order is in the PR
review packet source below.

### PR review packet source

| Packet section | Source |
|----------------|--------|
| What changed | This plan's Summary and Declared File Operations |
| Why | `spec.md` User Story 1 and `docs/ai/specs/.process/CAR-004-design-concept.md` |
| Non-goals | `spec.md` Out of Scope |
| Review order | 1. the two schema documents, 2. their frozen instances, 3. `claude_policy_controls.py`, 4. `claude_control_comparison.py`, 5. the replay and partition fixtures, 6. the three unit tests, 7. the twin-handoff record |
| Scope budget | This section and the Reviewability Budget line above |
| Traceability | `spec.md` FR-001 through FR-037a, mapped per artifact in [data-model.md](./data-model.md) |
| Verification | [quickstart.md](./quickstart.md) |
| Known gaps | [research.md](./research.md) Open Risks |
| Rollback / flags | No flag. The change is additive validation assets; reverting the commit removes them with no migration and no effect on any shipped default. |

## Project Structure

### Documentation (this feature)

```text
specs/car-004-policy-controls-comparators/
├── plan.md              # This file
├── research.md          # Phase 0 output — decisions and rationale
├── data-model.md        # Phase 1 output — entities, fields, validation rules
├── quickstart.md        # Phase 1 output — how to validate the feature
├── contracts/           # Phase 1 output — contract specifications
│   ├── policy-control-registry.md
│   ├── control-comparison.md
│   └── validator-api.md
├── checklists/          # Phase 4 output (/speckit-checklist)
├── SPEC-MOC.md          # Navigation marker
└── tasks.md             # Phase 5 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
tests/speckit-pro/
├── layer6-efficiency/
│   ├── contracts-claude/
│   │   ├── policy-control-registry.schema.json   # NEW — closed-at-three control set
│   │   ├── control-comparison.schema.json        # NEW — CAR-011-facing comparison rules
│   │   └── <nine frozen CAR-003 schemas>         # READ ONLY — never edited
│   ├── fixtures-controls/                        # NEW directory
│   │   ├── policy-control-registry.json          # NEW — frozen registry instance
│   │   ├── control-comparison.json               # NEW — frozen comparison instance
│   │   ├── partition-registry-entries.json       # NEW — reserved CAR-011 + CAR-004 smoke entries
│   │   └── control-replay.json                   # NEW — deterministic replay cases
│   ├── lib/
│   │   ├── claude_policy_controls.py             # NEW — schema engine + registry/control rules
│   │   ├── claude_control_comparison.py          # NEW — eligibility, Pareto, margin, verdict, claims
│   │   └── claude_successor_freeze.py            # READ ONLY — digest primitives imported
│   ├── results/                                  # git-ignored; per-run smoke output only
│   └── run-control-smoke.py                      # NEW — operator-only bounded live smoke
├── unit/
│   ├── test-policy-control-contracts.py          # NEW — Layer 4
│   ├── test-control-comparison-dominance.py      # NEW — Layer 4
│   └── test-twin-handoff-completeness.py         # NEW — Layer 4
└── suite-manifest.json                           # MODIFIED — three Layer 4 registrations

docs/ai/specs/.process/
└── CAR-004-twin-handoff.md                       # NEW — mirror-membership record for G56R-004
```

**Structure Decision**: The feature extends the existing CAR-003 evaluation
harness in place rather than creating a parallel tree. Schemas sit beside the
schemas they reference, validators sit beside the validators whose primitives
they import, and fixtures get their own `fixtures-controls/` directory so control
replay evidence is never confused with the CAR-003 corpus and calibration
fixtures in `fixtures/`. The three unit tests are split by concern — control
identity and replay, comparison and dominance, twin-handoff completeness — so a
failure names the concern it broke.

## Complexity Tracking

> No constitution violations. This table is intentionally empty.
