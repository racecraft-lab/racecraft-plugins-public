---
topic: "Gallery completion: design and prototyping"
slug: "art-004-gallery-completion-design-prototyping"
date: "2026-08-17"
mode: "setup"
spec_id: "ART-004"
source_input:
  type: "topic"
  ref: "docs/ai/specs/html-artifacts-technical-roadmap.md § ART-004: Gallery Completion — Design & Prototyping"
question_count: 9
stop_reason: "natural"
---

# Design Concept: Gallery completion — design and prototyping

> **Source:** `docs/ai/specs/html-artifacts-technical-roadmap.md` § ART-004
> **Date:** 2026-08-17
> **Questions asked:** 9
> **Stop reason:** natural — the product decisions, transferred scope, source revision, export meanings, and reviewability fallback are resolved
> **Blind-spot pass:** did not run — dispatch error: Full-history forked agents inherit the parent agent type; omit agent_type, or spawn without a full-history fork.

## Goals

- Port all six planned design and prototyping entries as branded, offline,
  single-file gallery artifacts: `visual-designs`, `design-system`,
  `component-variants`, `animation-prototype`, `interaction-prototype`, and
  `svg-illustrations`.
- Preserve **functional fidelity** with the pinned upstream sources: retain every
  distinct section and interaction, while compacting repeated sample data and
  rewriting markup where needed to satisfy the Racecraft contract and
  reviewability gate (Q1, Q3, Q6).
- Make `visual-designs` export exactly one selected direction plus the reader's
  rationale as both prompt and Markdown (Q7).
- Make `component-variants` display all required states while exporting one
  selected base variant plus the reader's rationale as both prompt and Markdown
  (Q2).
- Keep `design-system`, `animation-prototype`, `interaction-prototype`, and
  `svg-illustrations` read-only, matching their `exports: []` declarations.
- Absorb ART-020's complete defect repair into ART-004: add a keyboard route and
  accessible name to the five affected horizontal scroll containers across
  `code-approaches.html`, `implementation-plan.html`, and `module-map.html`;
  extend the Layer 4 assertion; add its negative fixture; and carry the repair
  through generated release artifacts (Q4, Q5).
- Mark ART-020 superseded by ART-004 so the same work cannot be executed twice
  (Q5).
- Preserve the original Q8 choice as historical evidence: the first Plan
  attempted **one combined slice**. When its authoritative gate blocked at 865
  reviewable LOC and 9 production files, Q9 fired. On 2026-08-17 the user
  approved three ordered slices without reducing fidelity or moving ART-020
  back out.

## Non-goals

- Workflow-stage routing. All six entries remain `ad-hoc`.
- The seven ART-005 knowledge, report, and editor ports.
- Vertical scroll containers or accessibility findings other than ART-020's
  named horizontal-scroll defect.
- Changes to gallery identifiers, categories, stages, triggers, sources,
  `when_to_use`, or export declarations. Each port flips only its own `status`
  from `planned` to `shipped`.
- A fidelity reduction as a budget escape hatch. A blocking plan gate returns
  the scope to HITL slicing instead.

## Source and size evidence carried into Plan

The six upstream sources are pinned to commit
`58c305be97f47b26b678f2c07dec01d4242268ec` in
`anthropics/html-effectiveness` (verified on 2026-08-17):

| Artifact | Upstream file | Lines |
|---|---|---:|
| `visual-designs` | `02-exploration-visual-designs.html` | 516 |
| `design-system` | `05-design-system.html` | 630 |
| `component-variants` | `06-component-variants.html` | 606 |
| `animation-prototype` | `07-prototype-animation.html` | 456 |
| `interaction-prototype` | `08-prototype-interaction.html` | 397 |
| `svg-illustrations` | `10-svg-illustrations.html` | 493 |
| **Total** | | **3,098** |

The shared forward estimator was run with seven capability groups, twelve
authored files or surfaces, fourteen functional requirements, and a net-new
classification. It returned:

```json
{"estimated_loc":865,"suggested_slices":3,"status":"warn"}
```

That estimate is advisory, not permission to bypass the authoritative
reviewability gate. It also does not account for the 3,098 upstream source
lines directly. Q8 deliberately keeps one combined slice despite this warning;
Q9 supplies the fail-closed response if Plan measures a block.

The setup `reviewability-gate` invocation against the full roadmap reported the
last reviewability declaration in that file rather than ART-004's entry. Its
result is not ART-004 evidence and must not be used to claim this expanded scope
fits. Plan must declare the actual file operations and run the authoritative
gate against the feature plan.

## Design Tree (Q&A log)

### Q1. How closely should the six ports follow their upstream templates?

**Branch:** Porting fidelity

**Recommended answer:** Mechanism-first port.

> Preserve each template's decision mechanism and distinguishing interaction,
> then shape the content to the Racecraft contract and budget.

**Alternatives offered:**
- Full-fidelity port: preserve all meaningful sections and behavior.
- Minimal reinterpretation: use upstream only as visual inspiration.

**User's answer:** Full-fidelity port.

**Resolution:** Q6 narrows this to functional rather than literal fidelity.

---

### Q2. What should `component-variants` treat as the exportable decision?

**Branch:** Component-variant export semantics

**Recommended answer:** Base variant.

> The manifest promises a sheet showing every state and declares prompt and
> Markdown exports. Choosing a base variant preserves the complete state sheet
> while producing one actionable conclusion.

**Alternatives offered:**
- Individual state: export one selected state.
- Per-state review: collect and export a conclusion for every state.

**User's answer:** Base variant (Recommended).

---

### Q3. Which upstream revision policy governs the six ports?

**Branch:** Upstream reproducibility

**Recommended answer:** Pin one commit.

> One immutable revision lets attribution, line measurements, review, and later
> reproduction refer to the same bytes across all six sibling ports.

**Alternatives offered:**
- Follow the latest `main` revision at implementation time.
- Vendor the original upstream files into this repository.

**User's answer:** Pin one commit (Recommended).

**Recorded revision:**
`58c305be97f47b26b678f2c07dec01d4242268ec`.

---

### Q4. How should ART-004 coordinate with the unstarted ART-020 repair?

**Branch:** Cross-spec ownership

**Recommended answer:** Proceed separately.

> ART-020 was independently reviewable and would let its assertion land before
> the new ports, without expanding ART-004.

**Alternatives offered:**
- Wait for ART-020 before starting ART-004.
- Absorb ART-020 into ART-004.

**User's answer:** Absorb ART-020.

**Consequence:** ART-004 owns all five existing-container fixes, their
accessible names, the global Layer 4 assertion, the negative fixture, keyboard
UAT, and generated-artifact updates.

---

### Q5. What happens to ART-020 after its work moves into ART-004?

**Branch:** Roadmap disposition

**Recommended answer:** Mark superseded.

> A superseded status preserves the defect record and its provenance while
> closing the duplicate execution path.

**Alternatives offered:**
- Keep ART-020 active with the original scope.
- Keep both entries active and reconcile them later.

**User's answer:** Mark superseded (Recommended).

---

### Q6. What does full fidelity mean when a port approaches the reviewability block?

**Branch:** Fidelity versus reviewability

**Recommended answer:** Functional fidelity.

> Preserve every distinct section and interaction, but compact repeated sample
> data and rewrite markup as needed. No behavior or decision surface is dropped.

**Alternatives offered:**
- Literal fidelity: preserve upstream structure and sample volume closely.
- Per-template rule: choose a different fidelity rule for each port.

**User's answer:** Functional fidelity (Recommended).

---

### Q7. What should `visual-designs` carry into its exports?

**Branch:** Visual-direction export semantics

**Recommended answer:** One direction plus rationale.

> The roadmap says the durable result is the choice and its reason. One selected
> direction gives prompt and Markdown consumers an unambiguous conclusion.

**Alternatives offered:**
- A ranked shortlist with rationale for every direction.
- Freeform notes without a required selection.

**User's answer:** One direction (Recommended).

---

### Q8. How should expanded ART-004 be divided for planning and review?

**Branch:** Review topology

**Recommended answer:** Seven ordered slices.

> Land the ART-020 repair and global guard first, then port one template per
> slice. This is the safest shape given the 865-LOC advisory warning and 3,098
> upstream source lines.

**Alternatives offered:**
- Three grouped slices, following the estimator's coarse count.
- One combined slice, preserving the original bundle despite the expansion.

**User's answer:** One combined slice.

---

### Q9. What happens if the authoritative planning gate blocks that slice?

**Branch:** Reviewability fallback

**Recommended answer:** Stop and split.

> Preserve the chosen scope for scaffold, but require a new human-approved
> topology if real plan evidence exceeds the contract. This keeps fidelity and
> ownership decisions intact without treating a warning as an override.

**Alternatives offered:**
- Reduce fidelity until the combined slice fits.
- Remove ART-020 from ART-004 and reactivate it separately.

**User's answer:** Stop and split (Recommended).

## Post-interview human decision: Three-slice recovery

The first Plan attempt measured the Q8 combined topology at 865 reviewable LOC
and 9 production files. Both values exceeded the repository's block thresholds,
so G3 stopped before Checklist and Tasks. The user then answered **"approve
three slices"** on 2026-08-17.

The approved topology is:

1. **Keyboard foundation:** ART-020's five horizontal-scroll repairs, the
   manifest-wide Layer 4 guard, its negative fixture, and keyboard UAT.
2. **Read-only ports:** `design-system`, `animation-prototype`,
   `interaction-prototype`, and `svg-illustrations`.
3. **Decision ports:** `visual-designs` and `component-variants`, including
   their live-state prompt/Markdown exports and clipboard-refusal fallback.

This is a review-topology decision only. `Functional fidelity`, the pinned
commit, ART-020 ownership and supersession, the exact export contracts, and the
single-file/offline constraints remain unchanged. Shared manifest, test,
payload, proof, and generated-doc changes must be serialized in slice order.
The resumed Plan must gate each slice separately and stop again if any one is
still blocked.

## Decisions recorded without a question

- **Single-file contract.** Each new artifact embeds the canonical brand and
  gallery-head blocks byte for byte, works over `file://` without a build step,
  loads no sibling resources, and flips only its own manifest `status`.
- **Export contract.** `visual-designs` and `component-variants` expose exact
  controls labelled `Copy as prompt` and `Copy as Markdown`; exports serialize
  live reader state and include enough context to act without reopening the
  page. Clipboard refusal reveals the payload in a selectable fallback.
- **Read-only entries.** The other four ports carry no export affordance because
  their manifest entries declare `exports: []`.
- **Keyboard-scroll pattern.** Every horizontal scroll container, including
  those introduced by the six ports, must be sequentially focusable and named.
  Follow the shipped `annotated-diff` / `flowchart` form: `tabindex="0"`, a
  suitable group role where semantically appropriate, and a specific
  `aria-label`.
- **Upstream handling.** Retrieve the pinned sources read-only into session
  scratch space during implementation. Do not vendor or stage the upstream
  originals; commit only the branded derivatives with the required attribution
  header.
- **Generated artifacts.** Template bytes affect the released payload and
  installed-cache proofs. Regenerate from authoritative source; never hand-edit
  generated mirrors.
- **Shared integration.** Manifest status flips, Layer 4 assertions, payloads,
  proofs, and generated documentation are shared integration surfaces. The
  approved slices own these changes serially in order; later slices build on
  the prior slice rather than editing the same integration surface in parallel.

## Open Questions

- **What:** The exact fill-region slot inventory and source artifact for each of
  the six templates.
  **Why deferred:** The interview fixed product behavior and export semantics;
  slot names must follow the pinned upstream structure and the gallery fill
  grammar rather than be invented here.
  **Suggested next step:** Resolve in Clarify after Plan records each pinned
  source's distinct sections.

- **What:** The exact prompt and Markdown serialization headings and field order
  for the two decision artifacts.
  **Why deferred:** Q2 and Q7 fix the conclusion, rationale, and live-state
  requirements; serialization is a design detail.
  **Suggested next step:** Reuse the shipped `code-approaches` export pattern in
  Plan, then pin exact strings in the specification.

- **What:** The negative fixture shape for the global keyboard-scroll assertion.
  **Why deferred:** ART-020 fixes the behavior and required proof, but the
  existing Layer 4 test architecture determines the smallest fixture form.
  **Suggested next step:** Plan from
  `tests/speckit-pro/unit/test-artifact-gallery.py` and its neighboring fixtures.

## Recommended Next Step

Resume Plan from the committed blocked checkpoint, encode the approved three
slices in every planning artifact, and run the authoritative reviewability gate
for each slice. Continue to Checklist and Tasks only if all three results are
non-blocking.
