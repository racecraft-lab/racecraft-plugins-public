# Contract: Draft Mode on the Pull-Request Packet

**Owner surface**: `speckit-pro/skills/speckit-autopilot/contracts/pr-packet.schema.json`,
`speckit-pro/speckit_pro_runner/helpers/pr_emission.py`,
`speckit-pro/speckit_pro_runner/helpers/read_only.py`

Satisfies FR-005, FR-007 (title), FR-008 (body), SC-007, SC-008.

---

## 1. Schema edits

### 1.1 `mode` enum, two sites

`properties.mode` becomes:

```json
"enum": ["single", "split", "draft"]
```

`$defs.validation_result.properties.mode` becomes:

```json
"type": ["string", "null"],
"enum": ["single", "split", "draft", null]
```

Both are required. The validation-result copy is what the write-side validator
stamps onto persisted evidence; leaving it behind makes a valid draft packet's
own validation record unrepresentable.

### 1.2 Draft relaxations, as a second `allOf` branch

Added alongside the existing `split_slice` branch, not merged into it.

**Amended at implementation time, 2026-08-18. A `then` branch cannot relax a
constraint.** This section first specified the relaxation as a `then` arm
restating `minItems: 0`. That does not work, in this validator or in JSON Schema
generally: `allOf` branches are conjunctive, so a branch's `minItems: 0` is
intersected with the top-level `minItems: 1` rather than replacing it, and the
stricter bound wins. A draft packet with empty `verification_evidence` would
still have failed `min_items` — the exact defect this contract's own §3 warns
about, one level lower down.

Proof, run against the shipped `json_schema_failures` at
`speckit-pro/speckit_pro_runner/helpers/read_only.py:2369-2378`: the original
shape returns `packet.schema.min_items packet.verification_evidence` for
`{"mode": "draft", "verification_evidence": []}`; the shape below returns no
failures for that same document, and still returns `min_items` for
`{"mode": "single", "verification_evidence": []}`.

The relaxation therefore **inverts**: the strict bound moves off the top-level
property and into an `else` arm that binds every non-draft mode.

Top-level bounds become permissive on exactly three keys:

| Key | Was | Becomes |
| --- | --- | --- |
| `verification_evidence` | `minItems: 1` | `minItems: 0` |
| `scope_evidence.changed_files` | `minItems: 1` | `minItems: 0` |
| `uat.how_to_uat` | `minLength: 1` | `minLength: 0` |

And the strictness is restated for every other mode, in the `else` arm of the
same branch. The full branch is given in §1.2.2, because three further sites
join it.

`scope_evidence.non_goals` keeps `minItems: 1` and is **not** relaxed. A draft
packet states its non-goals; only evidence a plan stage cannot yet have produced
is relaxed.

### 1.2.1 Three further sites pin the single/split shape

Also found at implementation time, 2026-08-18. §1.2 named three keys. The schema
pins the reviewer-packet shape at **three more**, and each one rejects the draft
body this contract's own §4 mandates. Enumerated with the constraint that bites:

| Site | Today | Why a draft fails it | Draft value |
| --- | --- | --- | --- |
| `required_headings` | `prefixItems` of 8 consts, `minItems: 8`, `maxItems: 8` | §2.2 gives draft two headings, not eight | exactly `["Artifacts", "Resume"]` |
| `editable_fields` | `prefixItems` pinning `summary`/`what_changed`/`why_it_matters`, `minItems: 3`, `maxItems: 3` | a draft body has no Summary, What Changed, or Why It Matters section, and `$defs/editable_field` restricts `heading` to exactly those three | `[]` |
| `uat.uat_runbook_heading` | `const "## UAT Runbook"` | §4 forbids a UAT section in a draft body, and `packet_body_structure_failures` requires the declared heading to appear in the body exactly once | `""` |

The `uat_runbook_heading` resolution needs **no validator change**. The body
checker already guards on truthiness at
`speckit-pro/speckit_pro_runner/helpers/read_only.py:2669-2671`
(`if isinstance(uat_heading, str) and uat_heading:`), so an empty declared
heading is the designed escape rather than a special case bolted on for draft.

`protected_body_fingerprint.elided_fields` needs no schema change — it carries no
`minItems` — but its truthful draft value is `[]`, because a draft body encloses
no editable prose.

An empty `editable_fields` array satisfies `prefixItems`, which constrains only
the positions that exist. Dropping `minItems`/`maxItems` from the top level and
restoring them in the `else` arm is therefore sufficient; the `prefixItems`
entries stay where they are and keep binding `single` and `split`.

### 1.2.2 The whole branch, both arms

Draft mode is not the mere absence of constraints — it has a shape of its own —
so the branch carries **both** arms: `then` pins the draft shape, `else` restores
the reviewer-packet shape for `single` and `split`.

```json
{
  "if":   { "properties": { "mode": { "const": "draft" } }, "required": ["mode"] },
  "then": {
    "properties": {
      "required_headings": {
        "prefixItems": [{ "const": "Artifacts" }, { "const": "Resume" }],
        "minItems": 2,
        "maxItems": 2
      },
      "editable_fields": { "maxItems": 0 },
      "uat": { "properties": { "uat_runbook_heading": { "const": "" } } }
    }
  },
  "else": {
    "properties": {
      "verification_evidence": { "minItems": 1 },
      "scope_evidence": {
        "properties": { "changed_files": { "minItems": 1 } }
      },
      "uat": {
        "properties": {
          "how_to_uat": { "minLength": 1 },
          "uat_runbook_heading": { "const": "## UAT Runbook" }
        }
      },
      "required_headings": {
        "prefixItems": [
          { "const": "Summary" }, { "const": "What Changed" },
          { "const": "Why It Matters" }, { "const": "How To Review" },
          { "const": "How To UAT" }, { "const": "Verification" },
          { "const": "Scope" }, { "const": "Known Gaps" }
        ],
        "minItems": 8,
        "maxItems": 8
      },
      "editable_fields": { "minItems": 3, "maxItems": 3 }
    }
  }
}
```

The matching top-level loosening is: drop `minItems`/`maxItems` and the eight
`prefixItems` consts from `required_headings`, leaving
`{"type": "array", "items": {"type": "string", "minLength": 1}}`; drop
`minItems`/`maxItems` from `editable_fields`, leaving its `prefixItems`; and
change `uat.uat_runbook_heading` from a `const` to
`{"type": "string"}`.

Neither arm declares `additionalProperties`, so the root's
`additionalProperties: false` is unaffected.

**Requiredness is relaxed, presence is not.** The three keys stay in their
`required` lists so `additionalProperties: false` and the object shapes are
untouched; draft mode permits them to be empty. This keeps one packet shape
across the draft-to-ready upgrade, which is what lets ART-010 fill the same
packet rather than replace it.

SC-008 is what proves the inversion is behaviour-preserving: every existing
`single` and `split` fixture must keep its exact outcome, and the `else` arm is
what holds that line.

The existing `split_slice` branch is unchanged, including its `else` arm — a
draft packet carries no `split_slice`, and the `else` arm already forbids it for
any non-`split` mode.

### 1.3 What must NOT change

`generated_title.value`'s pattern, `protected_body_fingerprint`, `editable_fields`,
`source_markers`, `body_file` / `validation_result_path` canonical-path rules,
and every rule that applies when `mode` is `single` or `split`. SC-008 is the
acceptance test for this line.

---

## 2. Producer edits (`pr_emission.py`)

### 2.1 The mode gate

```python
elif mode not in {"single", "split", "draft"}:
    return invalid_packet_input("mode must be single, split, or draft when provided", field="mode")
```

The default when `mode` is absent stays `"single"`. Draft mode is never implicit.

### 2.2 Mode-aware heading set

`required_headings()` gains a `mode` parameter. Draft mode returns the two FR-008
blocks; every other value returns today's eight, in today's order:

| Mode | Headings |
| --- | --- |
| `draft` | `Artifacts`, `Resume` |
| `single`, `split` | `Summary`, `What Changed`, `Why It Matters`, `How To Review`, `How To UAT`, `Verification`, `Scope`, `Known Gaps` |

The call site already threads the result through as packet data
(`"required_headings": required_headings()`), so the body structure checker needs
no change at all — it validates the body against whichever set the packet
carries.

### 2.3 No `split_slice` analogue for draft

Draft mode adds no new required sub-object, so the `mode == "split"` branch that
demands `split_slice` gains no sibling. Nothing extra is attached to the packet.

### 2.4 The producer surface is six sites and an ordering fix

Amended at implementation time, 2026-08-18. §2.1 and §2.2 named two producer
edits. There are **six**, and the two this section originally omitted are the
ones that fire first — a draft packet dies in input normalisation before the mode
gate at §2.1 is ever reached. Demonstrated by the T013 RED run, whose emission
test fails at `scope_evidence.changed_files must be a non-empty string array`.

| # | Site | Today | Draft behaviour |
| --- | --- | --- | --- |
| 1 | mode gate, `pr_emission.py:298-301` | rejects anything but `single`/`split` | accepts `draft`; unknown values still rejected with `field="mode"` |
| 2 | `required_headings()`, ~427 | returns the eight reviewer headings | takes `mode`; draft returns `["Artifacts", "Resume"]` |
| 3 | `editable_fields()`, ~729 | returns the three reviewer fields | takes `mode`; draft returns `[]` |
| 4 | `uat` assembly, ~305-308 | hardcodes `uat_runbook_heading` **and** a `how_to_uat` fallback string | draft emits `""` for both; `uat_source` keeps its default |
| 5 | `normalize_scope_evidence()`, ~586-625 | rejects an empty `changed_files` in **both** the dict and the non-dict branch | draft permits `changed_files: []`; `non_goals` stays non-empty in every mode |
| 6 | `normalize_evidence_list()`, ~629-641 | `isinstance(raw, list) and raw` is false for `[]`, so it falls through to "must contain at least one item" | draft permits `verification_evidence: []` |

Site 4 is worth calling out: the heading is not the only hardcode in that object.
`how_to_uat` carries fallback prose (`"No manual UAT runbook was provided; …"`)
that a draft packet must not emit, because §1.2.2's `then` arm permits an empty
string but the schema still forbids a draft body from carrying a UAT section for
the prose to describe.

**The ordering fix.** `mode` is read at line 298, *after* `normalize_scope_evidence`
(281) and `normalize_evidence_list` (285) have already run and returned their
diagnostics. Neither receives `mode`, so sites 5 and 6 cannot become mode-aware
where they stand. Hoist the mode resolution above both calls, then thread the
resolved `mode` into them. Hoisting is safe: nothing between the target check and
line 298 consults `mode`, and none of `normalize_generated_title`,
`normalize_scope_evidence`, `normalize_evidence_list`, or
`normalize_source_markers` takes it today.

Skipping any one of the six ships a producer whose output its own schema rejects
— the same failure §3 warns about, one layer up. The acceptance test is the
round trip: emit a draft packet, feed it straight back through
`validate-pr-packet-read-only`, and require `status=passed` with
`pr_blocked=false`. A heading spot-check passes while the packet is still
unusable.

---

## 3. Validator edits (`read_only.py`)

The read-only validator's two hand-written evidence assertions are not
schema-driven and must become mode-aware:

```python
if data.get("mode") != "draft":
    if not data.get("verification_evidence"):
        failures.append({"rule": "evidence.verification", ...})
    if not (scope_evidence or {}).get("changed_files"):
        failures.append({"rule": "evidence.scope.changed_files", ...})
```

Missing this is the failure mode that would ship a draft mode incapable of
passing its own validator. There are exactly two such assertions; no others in
the validator consult evidence contents.

---

## 4. Body contract (FR-008)

The draft body contains exactly two blocks and nothing else.

```markdown
# <generated title>

## Artifacts

| Artifact | Purpose | Open |
| --- | --- | --- |
| Implementation Plan | Lay out the phases of a planned change... | `open specs/<branch>/artifacts/implementation-plan.html` |
| Spec Explainer | Explain what a feature does and why... | `open specs/<branch>/artifacts/spec-explainer.html` |

## Resume

Stage: plan — stopped at the plan-stage boundary for review.
Resume with: `/speckit-pro:speckit-autopilot <workflow-file> --stage implement`
```

**Forbidden in a draft body**: a ```release-note fence, any verification section,
any scope or UAT section, and any placeholder final-writeup content. The draft PR
is in draft state, so the repository's PR checks do not run against it and no
release-note fence is needed or wanted.

**Composition**: the orchestrator builds both blocks and passes the finished
Markdown as `inputs.body`, which the packet producer uses verbatim. The
`build_packet_body` fallback is never reached in draft mode.

---

## 5. Title contract (FR-007, SC-007)

Shape: `<type>(<lowercase-scope>): <plain English description>`.

- `type` from `feat`, `fix`, `chore`, `docs`, `refactor`, `test`.
- Scope must be lowercase. The packet schema would accept an uppercase
  ticket-style scope; the release-readiness gate would not. SC-007 binds the
  stricter of the two.
- The title is final-shape at creation. It is not re-derived at the ready flip.

Draft-mode title validation checks the conventional shape only — it does not
require the description to reference verification or evidence that a draft has
not produced.

**Self-validation before creation**: the terminal step validates the packet title
through the release-readiness title check and refuses to create the pull request
on failure, reporting through the fail-open stop-report path rather than
proceeding with a title that would need a human edit.

**Which check, named — amended 2026-08-18.** "The release-readiness title check"
is the release gate's **`validate-pr-title`** operation, at
`speckit-pro/speckit_pro_runner/gates/release.py:1242-1245`:

```
^(feat|fix|chore|docs|test|refactor)\([a-z0-9-]+\): .+
```

It is **not** `validate-pr-workflow-contract`, even though that is what the
shipped `## PR Creation Protocol` uses for the implementation pull request's own
title. Using it here would make draft emission **structurally impossible** on four
spec families. Its `title.spec_scope` rule
(`read_only.py:2269-2287`) derives an expected scope from the changed spec paths
through `spec_scope_from_changed_path` (`read_only.py:2310-2327`), which
upper-cases the slug for `prsg-`, `spec-`, `doc-`, and `xplat-` prefixes. On a
`spec-006-…` feature the draft pull request's changed files include
`specs/spec-006-…/artifacts/`, so that rule would demand the scope `SPEC-006`
while this section demands lowercase. No title satisfies both, and every such run
would refuse to create.

ART-007's own slug matches none of those four prefixes, so the helper returns an
empty scope and the conflict does not arise for this feature's own pull request.
That is exactly why the wrong choice would have shipped undetected: the spec that
introduces the rule is not one of the specs the rule breaks.

---

## 6. Test obligations

| Obligation | Where |
| --- | --- |
| A valid draft packet passes read-only validation with no verification, changed-file, or UAT evidence | `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` |
| A draft packet carrying `split_slice` fails | same |
| A draft body missing either required heading fails | same |
| A draft body whose `Artifacts` table carries only gap rows still passes — the zero-artifact case FR-008 requires to remain a valid, openable draft | same |
| An unknown mode value is still rejected | same |

The zero-artifact obligation is the deterministic half of FR-004's fail-open
mandate. The rest of that mandate is orchestrator prose whose only check is the
operator-gated quickstart run, but the body itself is machine-checkable here:
`required_headings` for draft is `["Artifacts", "Resume"]`, so a body whose
`Artifacts` heading is present and whose table holds gap rows instead of
artifact rows must validate exactly as a fully-populated one does. Build that
body variant in memory in the existing test file — the fixture pair stays the
populated case, so no fixture is added and the declared file set does not grow.
| `pr-packet-output` emits a draft packet and its body | `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` |
| Every existing `single` and `split` fixture keeps its exact outcome | both, unchanged assertions (SC-008) |

New fixtures follow the shipped naming convention:
`fixtures/pr-packet/valid-draft.json` with its paired
`fixtures/pr-packet/bodies/valid-draft.md`. The packet's
`protected_body_fingerprint.value` is a sha256 over the normalised body, so the
two must be generated together — there is no digest manifest for this fixture
directory, the binding is pairwise.
