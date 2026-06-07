# PRD: {{FEATURE_NAME}}

<!--
  LEAN PRD TEMPLATE — universal across any project or domain.

  A PRD describes the WHAT and WHY, not the HOW. Keep it lean: capture
  validated decisions, do not re-litigate discovery. If a section does not
  reduce ambiguity for THIS effort, delete it — an empty heading is noise.

  This template is the FIRST artifact in the speckit-pro chain:

    PRD  ──►  Technical Roadmap (SPEC catalog)  ──►  speckit-scaffold-spec  ──►  speckit-autopilot

  The single property that makes a PRD "autopilot-ready" is the
  Feature ⇄ SPEC mapping (§3 + §7): every Feature / Acceptance-Criteria group
  becomes exactly ONE SPEC in the technical roadmap. Preserve that 1:1 mapping
  and the downstream tools can consume this document without re-interpretation.

  Authoring tip: generate this with `/speckit-pro:speckit-prd` (a collaborative,
  one-question-at-a-time interview), or fill it in by hand.
-->

**Status**: <!-- Draft | Active — not yet implemented | In progress | Shipped -->
**Source**: <!-- Originating idea, issue link, brief, or discovery doc -->
**Created**: {{DATE}}
**Last updated**: {{DATE}}
**Target window**: <!-- Milestone or date this targets, and how critical it is -->

---

## 1. Problem

<!--
  ONE or two paragraphs. State the problem in the user's terms, why it matters,
  and why now. Link to discovery / PR-FAQ / pitch instead of repeating it.
  Resist describing the solution here — that is §2/§3.
-->

> "<!-- The user-felt question or pain this PRD answers, in one sentence. -->"

<!-- Context: what exists today, where the gap is, what users do to work around it. -->

## 2. Goals & Non-goals

### 2.1 Goals

<!-- 3–6 outcomes. Each should be observable. Prefer outcomes over features. -->

- <!-- Goal: the change and the value it delivers -->
- <!-- Goal -->
- <!-- Goal -->

### 2.2 Non-goals (out of scope)

<!--
  Explicit scope cuts. For each, say WHERE it is handled instead (a later
  phase, a future PRD, "won't do"). Non-goals are what keep specs lean.
-->

- <!-- Item — deferred to {{LATER_SPEC_OR_PRD}} / out of scope because … -->
- <!-- Item -->

## 3. Acceptance Criteria

<!--
  THE KEYSTONE SECTION. Group criteria by Feature. Each Feature maps to exactly
  ONE SPEC in the technical roadmap (see §7 crosswalk). Number every criterion
  AC-<feature>.<n> so the roadmap, specs, and tasks can cite it.

  Write each criterion as an observable, testable statement (BDD-friendly:
  Given / When / Then is welcome but not required). A reviewer must be able to
  judge "did we meet this?" without asking you.
-->

### 3.1 {{FEATURE_1_NAME}} *(→ SPEC-001)*

- **AC-1.1**: <!-- Observable, testable statement -->
- **AC-1.2**: <!-- … -->

### 3.2 {{FEATURE_2_NAME}} *(→ SPEC-002)*

- **AC-2.1**: <!-- … -->
- **AC-2.2**: <!-- … -->

### 3.3 {{FEATURE_3_NAME}} *(→ SPEC-003)*

- **AC-3.1**: <!-- … -->

<!-- Add one subsection per Feature. Keep features small enough that each maps
     to a single reviewable SPEC. If a feature is too big for one SPEC, split
     it into two features here. -->

## 4. Migration Path (phased — one phase per SPEC)

<!--
  OPTIONAL but recommended for multi-spec efforts. One phase per Feature/SPEC,
  in dependency order. This is the narrative the roadmap's SPEC catalog
  formalizes. If the work is a single spec, delete this section.
-->

- **Phase 1 (SPEC-001) — {{FEATURE_1_NAME}}**: <!-- what ships, why first -->
- **Phase 2 (SPEC-002) — {{FEATURE_2_NAME}}**: <!-- depends on Phase 1 because … -->
- **Phase 3 (SPEC-003) — {{FEATURE_3_NAME}}**: <!-- … -->

## 5. Constraints

<!--
  Only constraints that genuinely bound the solution. Skip ceremony. Pull in
  project-governance constraints if a constitution exists
  (.specify/memory/constitution.md). Call out non-functional requirements ONLY
  where they are at risk (performance, security, accessibility, compatibility).
-->

- <!-- Governance / constitutional gate this work must satisfy -->
- <!-- Technical constraint (existing architecture, tech stack, integration) -->
- <!-- NFR at risk (latency budget, data residency, a11y, backward-compat) -->

## 6. Open Questions

<!--
  Unresolved decisions, tagged to the SPEC that will resolve them. These do not
  block PRD acceptance — they get answered in the per-spec grill-me interview or
  /speckit-clarify. Give each a recommendation if you have one.
-->

- **OQ-1 (SPEC-00N):** <!-- question — recommendation, if any -->
- **OQ-2 (SPEC-00N):** <!-- question -->

## 7. SPEC Catalog Crosswalk

<!--
  The handoff to the technical roadmap. Every Feature in §3 appears here as one
  SPEC. The roadmap (technical-roadmap-template.md) expands each row into a full
  SPEC section; speckit-scaffold-spec then reads the roadmap to build each spec.
  Keep this table 1:1 with §3 — it is the traceability spine of the whole chain.
-->

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| {{FEATURE_1_NAME}} | AC-1.* | SPEC-001 | — | P1 |
| {{FEATURE_2_NAME}} | AC-2.* | SPEC-002 | SPEC-001 | P1 |
| {{FEATURE_3_NAME}} | AC-3.* | SPEC-003 | SPEC-001 | P2 |

## 8. Success Criteria

<!-- How we know the PRD as a whole is delivered. Tie back to §2 Goals and §3 AC. -->

1. <!-- e.g., All acceptance criteria (AC-1.1 … AC-3.x) pass. -->
2. <!-- e.g., Each SPEC merged within its reviewability budget. -->
3. <!-- e.g., The originating user question (§1) is answerable in-product. -->

## 9. References

<!-- Links the downstream specs will need. Remove rows that don't apply. -->

- **Technical roadmap:** `docs/ai/specs/{{FEATURE_SLUG}}-technical-roadmap.md`
- **Constitution:** `.specify/memory/constitution.md`
- **Project standards:** <!-- AGENTS.md / CLAUDE.md / equivalent -->
- **Discovery / source:** <!-- brief, issue, PR-FAQ, design concept doc -->

---

## Appendix (optional — include only if it reduces ambiguity)

<!--
  Delete this whole appendix for simple efforts. Add only the pieces that make
  the WHAT clearer for reviewers and downstream specs:
    - Solution Overview — a short narrative of the approach (still the WHAT).
    - Information Architecture — navigation / layout sketch (ASCII is fine).
    - Data Flow — how data moves between components.
  These are aids, not required structure. A lean PRD often has none of them.
-->
