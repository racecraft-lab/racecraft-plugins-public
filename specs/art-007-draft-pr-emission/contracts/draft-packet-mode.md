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

Added alongside the existing `split_slice` branch, not merged into it:

```json
{
  "if":   { "properties": { "mode": { "const": "draft" } }, "required": ["mode"] },
  "then": {
    "properties": {
      "verification_evidence": { "type": "array", "minItems": 0 },
      "scope_evidence": {
        "properties": { "changed_files": { "type": "array", "minItems": 0 } }
      },
      "uat": { "properties": { "how_to_uat": { "type": "string" } } }
    }
  }
}
```

**Requiredness is relaxed, presence is not.** The three keys stay in their
`required` lists so `additionalProperties: false` and the object shapes are
untouched; draft mode permits them to be empty. This keeps one packet shape
across the draft-to-ready upgrade, which is what lets ART-010 fill the same
packet rather than replace it.

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

---

## 6. Test obligations

| Obligation | Where |
| --- | --- |
| A valid draft packet passes read-only validation with no verification, changed-file, or UAT evidence | `tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` |
| A draft packet carrying `split_slice` fails | same |
| A draft body missing either required heading fails | same |
| An unknown mode value is still rejected | same |
| `pr-packet-output` emits a draft packet and its body | `tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` |
| Every existing `single` and `split` fixture keeps its exact outcome | both, unchanged assertions (SC-008) |

New fixtures follow the shipped naming convention:
`fixtures/pr-packet/valid-draft.json` with its paired
`fixtures/pr-packet/bodies/valid-draft.md`. The packet's
`protected_body_fingerprint.value` is a sha256 over the normalised body, so the
two must be generated together — there is no digest manifest for this fixture
directory, the binding is pairwise.
