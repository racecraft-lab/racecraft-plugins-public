# Research: ART-004 Gallery Completion - Design & Prototyping

## Decisions

### R1. Runtime and packaging

**Decision**: Build each new artifact as one browser-native HTML file with inline CSS and JavaScript.

**Rationale**: The gallery contract requires direct `file://` use, offline readability, no sibling assets, no build step, and no runtime persistence. A local single-file implementation also keeps the user-facing behavior reviewable per artifact.

**Alternatives considered**:

- Shared JavaScript runtime: rejected because the single-file rule requires local behavior and the user explicitly required no new production helper.
- Framework build: rejected because it adds dependencies and a build step outside the gallery contract.

### R2. Source reproducibility

**Decision**: Use the pinned upstream commit `58c305be97f47b26b678f2c07dec01d4242268ec` for all six source templates.

**Rationale**: The recorded answer "Pin one commit" makes attribution, line-count evidence, and reproduction stable across all six ports.

**Alternatives considered**:

- Follow upstream `main`: rejected because review evidence could drift during implementation.
- Vendor upstream originals: rejected because the repository commits branded derivatives, not pristine upstream copies.

### R3. Fidelity rule

**Decision**: Use "Functional fidelity": preserve every distinct section, state, motion timing, decision surface, and interaction, while compacting only the repeated sample groups permitted by the spec.

**Rationale**: This keeps the user-visible value of each upstream template without forcing literal sample volume through an already blocked reviewability budget.

**Alternatives considered**:

- Literal fidelity: rejected because repeated sample rows would increase review size without adding distinct behavior.
- Minimal reinterpretation: rejected because it would drop required acceptance evidence.

### R4. Export semantics

**Decision**: `visual-designs` exports "One direction" plus rationale. `component-variants` exports "Base variant" plus rationale while still displaying every required state.

**Rationale**: These are the only two decision artifacts in ART-004. The copied payload must preserve the reader's live conclusion, rationale, and relevant control context.

**Alternatives considered**:

- Export all directions or every component state: rejected because the manifest value is the chosen decision, not a full page transcript.
- Freeform notes only: rejected because the result would not carry an actionable selected option.

### R5. ART-020 ownership

**Decision**: "Absorb ART-020" and "Mark superseded".

**Rationale**: ART-004 owns all five existing-container repairs, their accessible names, the global Layer 4 guard, the negative fixture, keyboard UAT, and generated artifacts. ART-020 remains a defect record without a duplicate execution path.

**Alternatives considered**:

- Run ART-020 separately first: rejected by the recorded ownership answer.
- Remove ART-020 from ART-004 to shrink scope: rejected because the fallback decision is "Stop and split", not scope reduction.

### R6. Review topology

**Decision**: Keep "One combined slice" only until the authoritative Plan evidence is evaluated.

**Rationale**: The setup interview selected one combined slice, but also selected "Stop and split" if the actual Plan evidence blocks. The combined slice is therefore a planning shape, not implementation permission.

**Alternatives considered**:

- Seven ordered slices: safest technical topology, but not the recorded setup answer.
- Three grouped slices: matches the advisory estimator's suggested slice count, but still needs human approval once G3 blocks.

### R7. Keyboard-scroll validation

**Decision**: Add a global Layer 4 guard over shipped manifest artifacts using `data-rc-keyboard-scroll="horizontal"`, `tabindex="0"`, `role="group"`, and a specific non-empty `aria-label`.

**Rationale**: The guard is markup-contract based, avoids CSS parsing, and makes both the ART-020 repair and new ports inherit the same keyboard-accessibility rule.

**Alternatives considered**:

- Hard-code only the five existing containers: rejected because new ports would not be protected.
- Infer overflow by selectors alone: rejected because the spec requires self-identifying intentional horizontal scroll regions.

### R8. Verification and release

**Decision**: Verify with Layer 1/Layer 4 tests, manual `file://` UAT, `scripts/refresh-release-artifacts.py`, `pnpm --dir docs-site reference:generate`, and generated-artifact consistency checks.

**Rationale**: Authored gallery bytes affect the Claude and Codex payloads, installed-cache mirrors, proof JSON, and docs reference pages. Generated files must be derived, not hand-edited.

**Alternatives considered**:

- Automated browser tests in the repository suite: rejected because repository validation remains Python standard library only.
- Skipping generated-reference refresh after test changes: rejected by the repository release contract.

## Source Inventory

| Artifact | Upstream source | Required fill regions | Export behavior |
|---|---|---|---|
| `visual-designs` | `02-exploration-visual-designs.html` | `feature-header`, `design-brief`, `background-toggle`, `directions` | Prompt and Markdown decision export |
| `design-system` | `05-design-system.html` | `feature-header`, `color`, `typography`, `spacing`, `shape`, `components` | Read-only |
| `component-variants` | `06-component-variants.html` | `feature-header`, `variant-controls`, `variants`, `snippet-preview` | Prompt and Markdown decision export |
| `animation-prototype` | `07-prototype-animation.html` | `feature-header`, `completion-stage`, `easing-controls`, `keyframes`, `css-snippet` | Read-only |
| `interaction-prototype` | `08-prototype-interaction.html` | `feature-header`, `views`, `interaction-notes`, `open-questions` | Read-only |
| `svg-illustrations` | `10-svg-illustrations.html` | `feature-header`, `illustrations`, `palette-rules` | Read-only |

## Reviewability Evidence

The fixed planning evidence records 3,098 upstream source lines and a forward estimate of 865 projected reviewable LOC. Local `wc -l` against the pinned cache reports 3,092 newline-terminated lines; this difference does not change the gate outcome because the accepted planning baseline and the forward estimate already exceed the block threshold.

