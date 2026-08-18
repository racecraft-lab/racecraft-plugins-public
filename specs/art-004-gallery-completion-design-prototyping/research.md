# Research: ART-004 Gallery Completion - Design & Prototyping

## Decisions

### R1. Runtime and packaging

**Decision**: Build each artifact as one browser-native HTML file with inline CSS and JavaScript.

**Rationale**: Direct `file://` use, offline readability, no sibling assets, no build step, and no persistence are required. Local behavior in each file keeps the review surface understandable inside each ordered slice.

**Alternatives considered**: Shared runtime and framework builds were rejected because they violate the single-file/offline contract and add nonessential dependency surface.

### R2. Source reproducibility

**Decision**: Use pinned upstream commit `58c305be97f47b26b678f2c07dec01d4242268ec` for all six new ports.

**Rationale**: The recorded answer "Pin one commit" keeps attribution, source-size evidence, and reproduction stable.

**Alternatives considered**: Tracking upstream `main` was rejected as drift-prone. Vendoring upstream originals was rejected because the repo ships branded derivatives only.

### R3. Fidelity rule

**Decision**: Use "Functional fidelity": keep every distinct section, state, motion timing, decision surface, and interaction; compact only repeated sample groups allowed by the spec.

**Rationale**: The user-visible behavior is preserved without forcing literal sample volume through review gates.

**Alternatives considered**: Literal fidelity was rejected for repeated sample overhead. Minimal reinterpretation was rejected because it would drop required acceptance evidence.

### R4. Approved review topology

**Decision**: Preserve the original "One combined slice" as historical evidence, then execute the user's 2026-08-17 recovery approval: "approve three slices".

**Rationale**: The combined Plan gate blocked at 865 reviewable LOC and 9 production files. The recorded fallback was "Stop and split", and the approved split keeps fidelity and ART-020 ownership intact.

**Alternatives considered**: Reducing fidelity or removing ART-020 from ART-004 was rejected because both contradict recorded decisions.

### R5. Slice boundaries

**Decision**: Use three serial slices: keyboard foundation, read-only ports, and decision ports.

**Rationale**: Slice 1 lands the keyboard-scroll repair and guard first. Slice 2 ships four read-only ports without export logic. Slice 3 ships the two exportable decision artifacts. Shared manifest, test, payload, proof, and generated-doc paths are assigned serially and are not parallel-safe.

**Alternatives considered**: Seven one-template slices were safer but not the approved topology. Three equal LOC slices were rejected because the split must follow actual capability boundaries.

### R6. Export semantics

**Decision**: `visual-designs` exports "One direction" plus rationale. `component-variants` exports "Base variant" plus rationale while still showing all required component states.

**Rationale**: These are the only two decision artifacts. The durable output is the chosen conclusion, rationale, and live context.

**Alternatives considered**: Exporting all options or freeform notes was rejected because it does not produce one actionable conclusion.

### R7. ART-020 ownership

**Decision**: "Absorb ART-020" and "Mark superseded".

**Rationale**: ART-004 owns the five existing-container repairs, accessible names, global guard, negative fixture, UAT, and generated-artifact updates. ART-020 stays as provenance, not an execution path.

**Alternatives considered**: Running ART-020 separately or removing it from ART-004 was rejected by the recorded ownership and fallback decisions.

### R8. Verification and release

**Decision**: Use Layer 1/Layer 4 validation, manual `file://` UAT, `scripts/refresh-release-artifacts.py`, `pnpm --dir docs-site reference:generate`, and generated-artifact consistency checks.

**Rationale**: Authored gallery bytes affect source, dist payloads, installed-cache mirrors, proof JSON, release-readiness evidence, and generated docs reference pages. Generated files must be derived, not edited.

**Alternatives considered**: Browser automation inside the repository suite was rejected because the suite remains Python standard library only.

## Source Inventory

| Artifact | Slice | Upstream source | Required fill regions | Export behavior |
|---|---:|---|---|---|
| `design-system` | 2 | `05-design-system.html` | `feature-header`, `color`, `typography`, `spacing`, `shape`, `components` | Read-only |
| `animation-prototype` | 2 | `07-prototype-animation.html` | `feature-header`, `completion-stage`, `easing-controls`, `keyframes`, `css-snippet` | Read-only |
| `interaction-prototype` | 2 | `08-prototype-interaction.html` | `feature-header`, `views`, `interaction-notes`, `open-questions` | Read-only |
| `svg-illustrations` | 2 | `10-svg-illustrations.html` | `feature-header`, `illustrations`, `palette-rules` | Read-only |
| `visual-designs` | 3 | `02-exploration-visual-designs.html` | `feature-header`, `design-brief`, `background-toggle`, `directions` | Prompt and Markdown decision export |
| `component-variants` | 3 | `06-component-variants.html` | `feature-header`, `variant-controls`, `variants`, `snippet-preview` | Prompt and Markdown decision export |

## Size Reconciliation

The six pinned sources total 3,098 planning lines. Local `wc -l` against the pinned cache reports 3,092 newline-terminated lines. The active Plan uses the required planning baseline and assigns review estimates by capability:

- Slice 1: 160 reviewable LOC, 3 production files, no new upstream source lines.
- Slice 2: 590 reviewable LOC, 4 production files, 1,976 required planning source lines.
- Slice 3: 520 reviewable LOC, 2 production files, 1,122 required planning source lines plus export behavior.

