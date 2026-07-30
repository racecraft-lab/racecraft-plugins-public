# Phase 0 Research: CAR-005 Model Availability, Fallback, and Recovery Simulation

**Date**: 2026-07-29 | **Spec**: `specs/car-005-availability-fallback-recovery/spec.md`

The specification arrived clarified: 44 functional requirements, zero outstanding
clarification markers, and a binding set of decisions resolved across
two Clarify sessions and two consensus rounds. Phase 0 therefore had no open
questions to close. Its job was the inverse — **verify every load-bearing claim
the spec makes about this repository before the plan commits to it**, because
the spec's decisions are justified by cited precedent and a wrong citation would
silently propagate into the implementation.

Every claim below was checked against committed bytes. One decision (D1) was
genuinely open and is resolved here. Two findings (D2, D9) are constraints the
spec does not mention and the plan now carries.

---

## D1: The schema-validation engine is imported, not written

**Decision**: `claude_route_fallback.py` imports the fail-closed validation
engine and the document roots from `claude_policy_controls`, and the canonical
serializer from `claude_successor_freeze`. It writes neither.

**Rationale**: This was the one open design question, and the repository already
answered it. `claude_policy_controls.py:108` publishes
`validate_instance(instance, schema, *, path="")`, a fail-closed draft-2020-12
subset engine whose docstring states the invariant this feature depends on:
"every `$ref` is resolved against its own `#/$defs/` and a reference leaving the
document fails closed (SC-017)". That is FR-016's no-cross-document-`$ref` rule
enforced by the engine itself rather than by convention.

The reuse precedent is explicit and recent. `claude_control_comparison.py:37-48`
imports `CONTRACT_ROOT`, `FIXTURE_ROOT`, `ControlContractError`,
`load_contract`, `require_utc_timestamp`, `validate_instance`, and
`verify_car_003_bindings` from `claude_policy_controls` under the comment "The
shared fail-closed schema engine and the committed-document roots, imported
rather than restated (research D1)" — CAR-004 reached the same conclusion and
labelled it identically. `claude_policy_controls.py:37` in turn imports
`canonical_json` and `record_digest` from `claude_successor_freeze`.

**This does not violate FR-033d.** FR-033d requires the *route-resolution
capability* to be one module. Importing a general-purpose validator that already
has two in-tree callers is not splitting the capability; writing a third copy of
a JSON Schema engine would violate constitution principle VI (YAGNI, "no wrapper
layers unless migration is planned").

**Canonical serialization** is therefore not this feature's invention:
`claude_successor_freeze.py:169-173` defines
`canonical_json(record) -> json.dumps(record, sort_keys=True,
separators=(",", ":"), ensure_ascii=False, allow_nan=False)`. FR-014's
byte-identity assertion runs over this function's output. The spec's assumption
that "canonical JSON serialization means sorted keys and a fixed separator
convention, consistent with the existing pinned-report precedent" resolves to
this exact call.

**Alternatives rejected**: a local validator (duplicates 2,800 lines of proven
fail-closed logic, and would diverge on the very `$ref` containment rule FR-016
depends on); third-party `jsonschema` (forbidden — constitution principle II,
standard library only).

---

## D2: Adding schemas to `contracts-claude/` opts them into an existing CAR-004 test

**Finding not stated in the spec.** `test-policy-control-contracts.py:5204`
runs `for path in sorted(CONTRACT_ROOT.glob("*.schema.json")): walk(...)` inside
`SchemaEngineKeywordCoverageTests`, asserting that **every** committed document
in `contracts-claude/` uses only keywords in
`claude_policy_controls.SUPPORTED_KEYWORDS`. The test's own docstring explains
why: "A keyword the engine quietly skips is indistinguishable from one the
instance satisfied."

**Consequence**: the three new schemas fall under a pre-existing CAR-004 test the
moment they land. A schema using an unsupported keyword fails
`test-policy-control-contracts.py`, not the new module's own test — a failure
that would look unrelated to this feature's diff.

**Verified safe.** `claude_policy_controls.py:290-308` supports every keyword the
spec's binding decisions require:

| Requirement | Keyword | Supported |
| --- | --- | --- |
| FR-013a conditional requiredness | `allOf`, `if`, `then`, `not`, `required` | yes |
| FR-016a two-`$defs` union | `oneOf` | yes |
| FR-012a action-list bounds | `minItems`, `maxItems` | yes |
| FR-027 budget maxima | `maximum`, `minimum` | yes |
| closed enums, discriminator | `enum`, `const` | yes |
| shape closure | `additionalProperties`, `propertyNames` | yes |
| local helpers | `$ref` | yes (local only) |

No new keyword needs teaching. `multipleOf` is the documented example of a
refused keyword (`test-policy-control-contracts.py:5208-5211`) and is not needed.

**Plan consequence**: the slice-1 verification step is `--layer 4` over the whole
unit tree, not just the new module, and the plan records this coupling so a
reviewer seeing a CAR-004 test in the run output understands why.

---

## D3: The report is one shape — root `oneOf` is impossible, not merely worse

**Verified**: the `allOf` + `if`/`then` + `not: {required: [...]}` idiom is the
directory's established mechanism for conditional requiredness, at all three
cited locations:

- `control-comparison.schema.json:204-213` — two branches on a `class`
  discriminator, each pairing `required` with `not: {required: [...]}`.
- `role-corpus.schema.json:90-93` — `if` on `executable: false`, `then`
  forbidding `candidate_route_bindings`.
- `experiment-policy.schema.json:22-31` — two branches on a nested
  `qualification_eligible` const.

**Verified**: root-level `oneOf` appears in exactly two of the eleven documents —
`car-003-additive-records.schema.json` (4 variants) and
`experiment-assignment.schema.json` (3 variants). Both are unions of distinct
*record classes*, confirming the spec's claim that root `oneOf` is reserved for
that case and is not the idiom for an outcome partition.

The spec's stronger claim — that a root `oneOf` partition is *impossible* here —
holds independently of style: FR-024 requires the override path to emit a
`no_safe_route` report that still carries `effective_dispatch_tuple`, so
"resolved" and "no_safe_route" do not partition the field space. A two-variant
`oneOf` would have to admit `effective_dispatch_tuple` in the failure variant,
at which point it discriminates nothing.

---

## D4: Enums are inline; no bare-enum `$defs` exists

**Verified by exhaustive scan** of all eleven documents in `contracts-claude/`:

- **Bare-enum `$defs` members: 0.** No `$defs` member is a naked enum.
- **Enum locations**: every one of the 125 enum occurrences sits at a point of
  use. The two most common shapes are
  `/$defs/<objectShape>/properties/<field>/enum` (81 occurrences) and
  `/properties/<field>/enum` (8).

The 81-occurrence shape is exactly what FR-016a mandates for the two diagnostic
`$defs`. So `$defs/resolutionDiagnostic/properties/code/enum` is not a
concession to a stylistic rule — it is the directory's dominant pattern, and it
is what gives FR-017a a stable JSON pointer.

---

## D5: No cross-document `$ref`; shared helpers are re-declared locally

**Verified by exhaustive scan**: 173 `$ref` occurrences across 38 distinct
targets, and **every one** begins `#/$defs/`. Zero cross-document references.

**Verified**: `digest` and `binding` are each declared locally in **11 of 11**
documents. The spec's justification for refusing a fourth shared-definitions
schema is therefore accurate — local re-declaration of shared helpers is
universal here, and the engine would fail closed on a cross-document `$ref`
anyway (D1).

---

## D6: Declaring an unexercised closed enum is house style

**Verified**: `score-bundle.schema.json:88` declares `failure_plane` with 12
members; `:89` declares `failure_code` with 36. Both are inline
`/properties/<field>/enum`. This is the precedent FR-019 leans on for declaring
the five-member policy-violation enum in slice 1 while no slice-1 corpus case can
emit one.

FR-019a is what makes that safe, and its technique is also established:
`SchemaEngineKeywordCoverageTests` (`test-policy-control-contracts.py:5160+`)
constructs instances and schemas **inline** via an
`accepts(instance, schema) -> bool` helper, precisely to prove behavior no
shipped fixture exercises. Slice 1's negative-validation test follows that shape.

---

## D7: The diagnostics envelope mirrors the runner; the trap is real

**Verified against the installed runner**, `envelope.py:43-66`. The `diagnostic()`
factory unconditionally emits five fields — `severity`, `source`, `code`,
`message`, `remediation` — and adds `details` only under `if details:`. That is
the required/optional split FR-012 pins, read off the constructor rather than
inferred.

- `remediation` is built by `envelope.py:36-40`: `{"summary": ..., "actions":
  actions[:3]}`. The `[:3]` slice is the origin of FR-012a's `maxItems: 3`; the
  `or [...]` default at `:60` supplies at least one action, giving `minItems: 1`.
  A fourth action would be silently discarded by the real runner.
- `severity` is closed to `{"info", "warning", "error"}` by the runner's own
  diagnostic validator, `gates/release.py:823`.
- `remediation` is a field **of the diagnostic**, never top-level.

**The trap is confirmed and must not be copied.**
`speckit-pro/skills/speckit-autopilot/contracts/final-reviewability-gate-state.schema.json:347-364`
defines `markerWarning` with
`"required": ["code", "severity", "message", "source", "details"]` and **no
`remediation` property at all** — `details` mandatory, `remediation` absent. That
is the exact inverse of the runner. FR-012 binds to the runner.

---

## D8: The corpus template already exists

**Verified**: `fixtures-controls/control-replay.json` is the pinned-replay
precedent, and its shape maps one-to-one onto FR-015:

- Top level: `schema_version`, `fixture_kind`, `description`, `cases`.
- `cases` is a list of 9 self-contained entries, each carrying `case_id`,
  `expected`, `proves`, and `requirements`.
- **Order is declaration order, not sorted** — confirmed by comparing the
  extracted `case_id` list against its own sorted form (they differ). This is the
  precedent FR-015 cites for appending slice-2 cases at the tail without
  perturbing any existing case's pinned bytes.

The `proves` and `requirements` per-case fields are what satisfy SC-007 (a reader
opens one case and understands it without opening another file), so the new
corpus carries them too.

A second, closer analogue exists: `fixtures/car-003-alias-repoint-replay.json`
(`fixture_kind: "alias_repoint_replay"`) already pins alias-repoint cases and
already uses the `case_id` `platform_route_change`, corroborating FR-006's
sub-reason vocabulary as continuous with prior work rather than newly invented.

**Naming caveat**: that file is spec-ID-named, which FR-032 now forbids (see
D9). The new corpus is `fallback-scenario-corpus.json` — capability-named.

---

## D9: Durable naming is automatically enforced

**Finding not stated in the spec.** FR-032's durable-name rule is not
convention — `test-unit-layout.py` enforces it mechanically:

- `_repository_spec_families()` (`:122-141`) derives live spec families by
  scanning `docs/ai/specs/**/*.md` and every directory under `specs/`. Because
  this feature's directory is `specs/car-005-availability-fallback-recovery`,
  **`car` is a live family**, so `car-005` in a filename would be detected.
- `test_tracked_authored_script_files_are_behavior_named` (`:273-294`) walks
  `git ls-files --stage` and fails on any authored script whose stem contains a
  live spec ID.
- `test_unit_test_method_names_are_behavior_named` (`:197-206`) applies the same
  rule to **test method names**, parsed via `ast`.

**Plan consequences**, all satisfiable:

| Artifact | Status |
| --- | --- |
| `claude_route_fallback.py` | clean |
| `test-route-fallback-simulation.py` | clean |
| `fallback-scenario-corpus.json` | clean |
| the three `*.schema.json` names | clean |
| test **method** names | must be behavior-named — no `test_car_005_*` |

The `$id` values *do* contain `car-005`, and that is correct: the check inspects
path stems, not file contents, and the existing convention already embeds
`car-003`/`car-004` in every `$id` (verified across all eleven documents). The
roadmap's own proposed Key Files
(`docs/ai/specs/claude-agent-routing-technical-roadmap.md:552-554`) independently
name `fixtures-fallback/` and `test-route-fallback-simulation.py`, matching this
plan.

---

## D10: The roadmap parity source is verified verbatim

**Verified** the five codes the Claude roadmap pins, at
`docs/ai/specs/claude-agent-routing-technical-roadmap.md:527-529`:
`preferred_model_unavailable`, `effort_unsupported`,
`capability_probe_unavailable`, `treatment_probe_failed`, `no_safe_route`.
Exactly five — a whole-file scan for backticked reason-code tokens returns only
these, all within `:527-529`.

**Verified** the Codex counterpart at
`docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md:535-538`, whose
third member is `capability_discovery_unavailable`. The other four are
byte-identical and each appears exactly once per file. The divergence is the
single third member, exactly as FR-017b states.

**Reading roadmap markdown from a test is established practice**:
`test-agent-route-research-parity.py:434-444` opens both roadmap files by path
and asserts on their text. FR-017a's "read live, never transcribe" discipline has
its own precedent at `test-policy-control-contracts.py:400-413`, whose comment
states the rule: "a case that restated an enum would absorb the very drift it
exists to catch." Both sides of the FR-017a comparison are therefore derived —
the enum by JSON pointer from the committed schema, the roadmap members by
parsing the roadmap.

**FR-012a's verbatim rollback string is grounded.** The roadmap states the
guidance twice in indicative mood — CAR-005 scope: "consumer recovery is the
previous plugin release" (`:536-537`); CAR-011 live-UAT scope: "rollback to the
previous plugin release" (`:902-903`). `Roll back to the previous plugin
release.` is the imperative rendering FR-012a pins, consistent with both.

**FR-017c's permanence evidence is confirmed**: the Claude roadmap bounds three
budget dimensions ("bound probe attempts, retries, and fan-out", `:532-533`) and
names four rejections (`:531-533`), while Codex bounds six and names six
(`:539-545`), and Codex carries an approved/unapproved service-reroute
distinction with no Claude analogue. The vocabularies describe different
mechanisms; reconciliation would force one platform onto a term that misdescribes
its own behavior.

**G56R-005 confirmed silent on mirroring**: its entry
(`codex-gpt-5-6-agent-routing-technical-roadmap.md:513-545`) contains zero
occurrences of "mirror" or "CAR-005", and carries neither an `Out of Scope` nor a
`Key Files` block. The spec's named-follow-up assumption is accurate: the
mirroring obligation is recorded in CAR-005's spec, not in G56R-005's scope text.

---

## D11: The synthetic vocabulary reuses frozen values where one exists

**Decision**: fixture efforts are drawn from the frozen Claude ladder
`low | medium | high | xhigh | max`; model IDs and alias names are synthetic.

**Rationale**: `successor-capability-freeze.schema.json` `$defs/tuple` pins the
effort enum to exactly those five with the description "FR-003: the closed
ordered Claude ladder." Inventing a parallel effort vocabulary would make
FR-007's `effort_unsupported` case untranslatable when CAR-006 adopts the corpus.
Agent names and model IDs are the opposite case — FR-018 and SC-006 require the
cast to be synthetic and forbid naming any of the twelve shipped agents, so those
are invented per the three role classes the spec's assumptions fix (required
executor, bounded analyst, optional helper).

FR-002's prohibition is respected: the snapshot projection is authored from the
five fields resolution actually consumes and does **not** reuse the CAR-002
runtime-capability capture-record shape, which carries capture provenance,
digests, and retention metadata resolution never reads.

---

## D12: No directory-level registration is required

**Verified**: nothing enumerates fixture directories as a registry. Grepping the
tree for `contracts-claude` and `fixtures-controls` returns only library modules
and unit tests that reference specific paths — no manifest section, no Layer 1
validator that scans the directory for expected membership. `fixtures-fallback/`
therefore needs no registration beyond existing on disk.

The **only** registration surface is `suite-manifest.json`. Layer 4's `scripts[]`
array holds 62 entries of shape `{"path": ..., "label": ..., "baseline": null}`,
with `tests/speckit-pro/unit/test-twin-handoff-completeness.py` currently at the
tail. Slice 1 appends one entry, which becomes the new tail. FR-033a's
single-module reasoning checks out: a second slice-2 entry would have to add a
comma to slice 1's final line, so registering one module keeps the manifest
entirely out of slice 2's diff.

**Also verified**: `docs-site/src/content/docs/reference/tests.md` is generated
from the test tree and lists unit-test paths, so both slices must run
`pnpm --dir docs-site reference:generate`. That worktree already has
`docs-site/node_modules` installed.

---

## Baseline

`python3 tests/speckit-pro/run-all.py --layer 1` → **1428/1428 passed** on the
branch before any change. The starting tree is green, so any failure during
implementation is attributable to this feature.

---

## Open questions

**None.** No clarification marker existed in the spec, and every claim
the plan relies on is verified above. Two constraints the spec did not state
(D2, D9) are now carried by the plan; neither required a spec change, because
both are satisfied by the file names and keyword choices the spec had already
fixed.
