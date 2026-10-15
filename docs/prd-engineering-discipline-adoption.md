# PRD: Engineering Discipline Adoption for SpecKit Pro

**Status**: Active - not yet implemented
**Source**: Interactive `speckit-coach` + `speckit-prd` session on 2026-09-25, reviewing every skill in `mattpocock/skills`
**Created**: 2026-09-25
**Last updated**: 2026-09-25
**Target window**: Tier 1 and Tier 2 in the next release train; the full catalog before the next minor release after that. Not release-blocking.
**Spec ID prefix**: `EDA-###` (Engineering Discipline Adoption)

---

## 1. Problem

> "How do SpecKit Pro users get Matt Pocock's engineering fundamentals (grilling, prototypes, deep modules, seams-first TDD, disciplined debugging, two-axis review) inside the SDD process, without his issue-tracker workflow?"

Matt Pocock's `mattpocock/skills` (MIT) encodes proven engineering discipline as small, composable agent skills. Its README names Spec-Kit as an approach that "owns the process" and takes away control. His published position (README, 2026-04-28; AI Engineer Europe talk, April 2026; issue #906, 2026-08-19) rejects three things: code regenerated from specs, frameworks that own the process, and the model deciding stage transitions. He still runs a spec-driven flow himself and treats CONTEXT.md and ADRs as the durable records.

SpecKit Pro users who install both plugins today get two overlapping `grill-me` interviews, two glossaries (`ubiquitous-language` and CONTEXT.md), and colliding trigger phrases for TDD, review, and debugging. Useful discipline (prototypes before specify, a debugging loop, deep-module vocabulary, two-axis review) is absent from SpecKit Pro. The gap is coherence: one SDD story where each of Matt's techniques lands at the phase that needs it, with his authorship credited.

## 2. Goals & Non-goals

### 2.1 Goals

- Every one of the 38 upstream skills (plugin, in-progress, and misc buckets at the pinned commit) has a recorded disposition: absorbed, new skill, or ignored with a reason.
- Absorbed discipline lives in the SpecKit Pro surface that owns that phase, so users meet it inside the normal flow rather than as parallel commands.
- Exactly three new skills exist where no surface does today: `speckit-prototype`, `speckit-diagnose`, and `speckit-architecture-review`.
- Attribution is complete and test-enforced: the MIT notice ships in both payloads and every derivative file credits its upstream source.
- SpecKit Pro answers Matt's critique by design: every skill stays runnable on its own, stage changes stay user-visible, and durable knowledge moves into ubiquitous-language and ADRs.

### 2.2 Non-goals (out of scope)

- Matt's issue-tracker workflow (`setup-matt-pocock-skills`, `to-spec` and `to-tickets` publishing, `implement`, `implement-spec`, `triage` labels, the `wayfinder` map, the `ask-matt` router). SpecKit's own specify, tasks, and autopilot own this; won't do.
- Skills that generate or require Bash or `jq` (`wizard`, `git-guardrails-claude-code`). They conflict with the Python-only tooling principle; won't do.
- Niche skills (`teach`, `wait-what`, `loop-me`, `writing-beats`, `writing-fragments`, `writing-shape`, `migrate-to-shoehorn`, `scaffold-exercises`) and the Claude-only `claude-handoff`; won't do.
- Edits in the `racecraft-lab/skills` fork. It stays a provenance anchor; all adaptation lives in SpecKit Pro.
- Automatic syncing with upstream. A future sync compares the fork against the pinned tag by hand.

## 3. Acceptance Criteria

### 3.1 Attribution Foundation *(-> EDA-001)*

- **AC-1.1**: `racecraft-lab/skills` is a fork of `mattpocock/skills` with tag `speckit-pro-baseline` at `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`.
- **AC-1.2**: An upstream notice under `speckit-pro/skills/` reproduces Matt Pocock's MIT license verbatim and names the upstream URL, fork URL, and pinned SHA.
- **AC-1.3**: The notice carries a disposition ledger with one row for each of the 38 upstream skills: upstream path, disposition, destination, status (`planned` or `landed`), and a reason for every IGNORE row.
- **AC-1.4**: An attribution test fails when a `landed` destination is missing, lacks its credit block, a row lacks a disposition, an IGNORE row lacks a reason, or the MIT text differs from upstream.
- **AC-1.5**: After a release-artifact refresh, the notice exists in both `dist/` payloads.
- **AC-1.6**: `speckit-pro/README.md` acknowledges Matt Pocock's skills and links the notice.

### 3.2 Frontier-Round Grilling *(-> EDA-002)*

- **AC-2.1**: `grill-me` asks each round as up to four independent questions whose prerequisites are settled, each with a recommended answer first; a question that depends on an open one waits for a later round.
- **AC-2.2**: Before asking, `grill-me` looks up facts it can find itself with read-only tools and asks the user only for decisions.
- **AC-2.3**: When only an absent stakeholder can answer, `grill-me` writes an async questionnaire (recipient, what is needed back, questions ordered by importance, answer stubs) and records the deferral in the Design Concept.
- **AC-2.4**: When all three consensus analysts disagree, autopilot's human-review escalation can emit the same questionnaire shape.
- **AC-2.5**: The Codex mirror uses its own question mechanism, or a numbered round when none exists, with the same round rules.

### 3.3 Domain Model and ADRs *(-> EDA-003)*

- **AC-3.1**: A documented ADR convention exists at `docs/adr/NNNN-slug.md`, with Matt's three-gate test (hard to reverse, surprising without context, a real trade-off) and a short format.
- **AC-3.2**: `ubiquitous-language` records `Avoid` aliases, offers a challenge mode that tests terms against the glossary and the code, and keeps the document to terms only.
- **AC-3.3**: `grill-me` writes new or sharpened terms and qualifying ADRs inline as decisions land, not in a batch at the end.
- **AC-3.4**: `spec-context-analyst` and `codebase-analyst` read `docs/adr/` when it exists and flag a conflicting recommendation by ADR number.

### 3.4 Prototype Skill *(-> EDA-004)*

- **AC-4.1**: `speckit-prototype` exists on Claude and Codex, with a logic branch (one self-contained HTML file with a visible state panel and guided walkthroughs) and a UI branch (several structurally different variants behind a switcher).
- **AC-4.2**: Prototype code is marked throwaway and preserved on a `prototype/<name>` branch; the Design Concept records it under `Prototype evidence`.
- **AC-4.3**: `grill-me`, `speckit-scaffold-spec`, and `speckit-coach` route a question that only a prototype can answer to `speckit-prototype`.
- **AC-4.4**: Layer 1 contracts pass and Layer 2 trigger files hold at least three positive and three negative queries on each surface.

### 3.5 Deep-Module Planning and Slicing *(-> EDA-005)*

- **AC-5.1**: A coach reference defines the deep-module vocabulary (module, interface, depth, seam, adapter, leverage, locality), the deletion test, and design-it-twice.
- **AC-5.2**: The Plan phase prompt asks for test seams first, preferring the highest existing seam, and states that the spec records decisions already made.
- **AC-5.3**: Module and Interface Deltas guidance uses the deep-module vocabulary.
- **AC-5.4**: `slicing-heuristics.md` and the Tasks prompt cover tracer-bullet vertical slices, refactoring first, expand then migrate then contract for wide refactors, and explicit blocking edges.
- **AC-5.5**: `speckit-prd` applies the fog-versus-spike test and records each rejected concept once, matched by concept.

### 3.6 Seams-First TDD *(-> EDA-006)*

- **AC-6.1**: `tdd-protocol.md` requires tests only at seams agreed in the plan, bans tautological expected values, and limits mocks to system boundaries.
- **AC-6.2**: `implement-executor` on Claude and Codex carries the same rules and reports the seam each test exercises.

### 3.7 Diagnose Skill *(-> EDA-007)*

- **AC-7.1**: `speckit-diagnose` exists on Claude and Codex with six gated phases: feedback loop, reproduce and minimise, ranked falsifiable hypotheses, instrument, fix with a regression test, clean up.
- **AC-7.2**: Phase 2 cannot start until one named, already-run command goes red on the reported symptom.
- **AC-7.3**: Debug instrumentation carries a unique tag, and cleanup proves zero remaining tags; secrets appear only as a redaction marker.
- **AC-7.4**: Autopilot error recovery and `speckit-resolve-pr` route an unexpected red test or CI failure to `speckit-diagnose`.
- **AC-7.5**: No shipped file contains Bash; the upstream shell template does not ship.

### 3.8 Post-Implementation Discipline *(-> EDA-008)*

- **AC-8.1**: The Code Review step runs two parallel reviews, Standards and Spec, and reports them side by side without merging or reranking.
- **AC-8.2**: The draft-PR body gains a smallest-view summary, before-and-after evidence, and a merge-danger line (one-way or two-way door, blast radius), within the existing body contract; Dex Horthy's `show-me` is credited.
- **AC-8.3**: A merge-conflict reference resolves each hunk by the intent of both sides, never aborts, and regenerates generated paths instead of hand-resolving them; autopilot main sync and `speckit-resolve-pr` use it.
- **AC-8.4**: The retrospective step reports each mechanical violation as a candidate deterministic check and a missing guardrail as a finding.

### 3.9 Context Hygiene and Agent Writing *(-> EDA-009)*

- **AC-9.1**: A context-hygiene reference orders the phase-boundary moves (continue, clear, hand off, delegate, compact) and is cited by coach and autopilot.
- **AC-9.2**: `speckit-status` can print a handoff brief that points to artifacts by path and names the next command, while staying read-only.
- **AC-9.3**: The constitution guide and the repository `scaffold-skill` helper apply the writing-for-agents rules.
- **AC-9.4**: The quality-gates guide carries worked examples for module-boundary enforcement and pre-commit checks.
- **AC-9.5**: `grounding.md` requires tracing each external claim to the source that owns it.

### 3.10 Architecture Review Skill *(-> EDA-010)*

- **AC-10.1**: `speckit-architecture-review` exists on Claude and Codex as a user-invoked skill that never edits code.
- **AC-10.2**: It scopes the survey from the user's direction or recent change hot spots, uses the read-only `codebase-analyst`, and applies the deletion test.
- **AC-10.3**: It writes a self-contained HTML report (no CDN) with candidate cards, before-and-after diagrams, and a strength rating.
- **AC-10.4**: A chosen candidate is grilled and leaves as a roadmap entry proposal or an ADR.

### 3.11 Adoption Close-out *(-> EDA-011)*

- **AC-11.1**: Every ledger row is `landed` or IGNORE with a reason, and the attribution test passes.
- **AC-11.2**: The Layer 2 inventory is revised to include the three new trigger corpora under the qualification protocol.
- **AC-11.3**: Generated reference pages and README skill tables list the three new skills.

## 4. Migration Path

- **Phase 1 (EDA-001) - Attribution Foundation**: the notice and test exist before any derivative content lands.
- **Phase 2 (EDA-002, EDA-007, EDA-008, EDA-009)**: independent absorptions and the diagnose skill; each needs only the ledger.
- **Phase 3 (EDA-003, EDA-004)**: ADRs and the prototype skill build on the round-based interview.
- **Phase 4 (EDA-005)**: planning vocabulary builds on the ADR and glossary conventions.
- **Phase 5 (EDA-006, EDA-010)**: TDD uses plan seams; architecture review uses ADRs and the vocabulary.
- **Phase 6 (EDA-011)**: close-out after every other spec merges.

## 5. Module and Interface Deltas

| Feature (§3) | Module or interface | Delta | Note |
|---|---|---|---|
| Attribution Foundation | `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/` | new | MIT notice and disposition ledger |
| Attribution Foundation | `tests/speckit-pro/unit/test-upstream-skill-attribution.py` | new | enforces notice, ledger, and credit blocks |
| Frontier-Round Grilling | `skills/grill-me` interview protocol (Claude and Codex) | changed | rounds of up to four questions; stakeholder questionnaire output |
| Frontier-Round Grilling | autopilot consensus human-review escalation | changed | can emit a questionnaire |
| Domain Model and ADRs | `docs/adr/NNNN-slug.md` convention | new | consumer projects gain an ADR home |
| Domain Model and ADRs | `skills/ubiquitous-language` document format | changed | adds `Avoid` aliases and challenge mode |
| Domain Model and ADRs | `spec-context-analyst`, `codebase-analyst` inputs | changed | read ADRs |
| Prototype Skill | `speckit-prototype` skill | new | model-invoked on both surfaces |
| Prototype Skill | Design Concept format | changed | adds `Prototype evidence` |
| Deep-Module Planning and Slicing | coach deep-module reference; plan and tasks prompts; `slicing-heuristics.md`; `speckit-prd` protocol | changed | vocabulary, seams-first, slicing and fog rules |
| Seams-First TDD | `tdd-protocol.md`; `implement-executor` (Claude and Codex) | changed | seam, tautology, and mocking rules; seam in evidence |
| Diagnose Skill | `speckit-diagnose` skill | new | model-invoked on both surfaces |
| Diagnose Skill | autopilot error recovery; `speckit-resolve-pr` | changed | route to diagnose |
| Post-Implementation Discipline | post-implementation Code Review step | changed | two parallel review axes |
| Post-Implementation Discipline | draft-PR body sections | changed | summary view, evidence, merge danger |
| Post-Implementation Discipline | autopilot merge-conflict reference | new | used by main sync and resolve-pr |
| Context Hygiene and Agent Writing | coach and autopilot context-hygiene reference | new | phase-boundary moves |
| Context Hygiene and Agent Writing | `speckit-status` output | changed | optional handoff brief |
| Architecture Review Skill | `speckit-architecture-review` skill | new | user-invoked on both surfaces |
| Adoption Close-out | Layer 2 trigger inventory | changed | three new corpora |

## 6. Constraints

- Constitution II: no Bash, `jq`, `$(`, shell scripts, or grep and sed pipes in shipped prose; upstream shell templates do not ship.
- Constitution IV: every new test and helper passes Layers 1, 4, and 5; generated artifacts are committed with their source.
- Constitution VI: absorb before adding; a new skill needs a trigger boundary no sibling covers.
- Web research stays behind the research broker; no ported prose may instruct open web fetching.
- The privacy scan forbids home paths, temp paths, and raw UUIDs in committed files.
- Each new skill needs a Codex mirror with `agents/openai.yaml`, a policy-map entry, capability and grounding pointers, the Codex Skill-Selection Guard, entries in the four hard-coded skill lists, and Layer 2 trigger files.
- Layer 2 runs require the upstream `mattpocock-skills` plugin to be disabled, or the results measure collisions with it.
- Credit is both machine-readable (`metadata.credits` frontmatter) and human-readable (credit block and notice), following the artifact-gallery precedent.

## 7. Open Questions

- **OQ-1 (EDA-002):** Does the installed Codex CLI expose a structured multi-question tool? Recommendation: verify during Clarify and fall back to a numbered round.
- **OQ-2 (EDA-003):** Should `ubiquitous-language` add an `Avoid` column or keep aliases in the Meaning cell? Recommendation: a column, with the advisory lint updated.
- **OQ-3 (EDA-008):** Can the new PR-body sections sit inside the protected fingerprint markers without changing the packet contract? Recommendation: resolve in Plan against the current contract.
- **OQ-4 (EDA-010):** How does the architecture review relate to the planned ART-021 architecture viewer? Recommendation: the review produces candidates; the viewer renders structure; share diagram conventions only.
- **OQ-5 (EDA-011):** Does adding three corpora need a new qualification campaign or an inventory amendment? Recommendation: an amendment under the existing protocol.

## 8. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Attribution Foundation | AC-1.* | EDA-001 | - | P1 |
| Frontier-Round Grilling | AC-2.* | EDA-002 | EDA-001 | P1 |
| Domain Model and ADRs | AC-3.* | EDA-003 | EDA-002 | P1 |
| Prototype Skill | AC-4.* | EDA-004 | EDA-002 | P1 |
| Deep-Module Planning and Slicing | AC-5.* | EDA-005 | EDA-003 | P2 |
| Seams-First TDD | AC-6.* | EDA-006 | EDA-005 | P2 |
| Diagnose Skill | AC-7.* | EDA-007 | EDA-001 | P1 |
| Post-Implementation Discipline | AC-8.* | EDA-008 | EDA-001 | P2 |
| Context Hygiene and Agent Writing | AC-9.* | EDA-009 | EDA-001 | P3 |
| Architecture Review Skill | AC-10.* | EDA-010 | EDA-003, EDA-005 | P2 |
| Adoption Close-out | AC-11.* | EDA-011 | EDA-001 through EDA-010 | P3 |

## 9. Success Criteria

1. All acceptance criteria AC-1.1 through AC-11.3 pass.
2. Each EDA spec merges within its reviewability budget.
3. A SpecKit Pro user can run grill-me, prototype, specify, plan, tasks, implement, and review without installing `mattpocock-skills`, and meets each absorbed technique at its phase.
4. The attribution test passes with every ledger row resolved.

## 10. References

- **Technical roadmap:** [`docs/ai/specs/engineering-discipline-adoption-technical-roadmap.md`](ai/specs/engineering-discipline-adoption-technical-roadmap.md)
- **Roadmap MOC:** [`docs/ai/specs/engineering-discipline-adoption-roadmap-MOC.md`](ai/specs/engineering-discipline-adoption-roadmap-MOC.md)
- **Constitution:** `.specify/memory/constitution.md`
- **Project standards:** `AGENTS.md`, `speckit-pro/AGENTS.md`, `tests/speckit-pro/AGENTS.md`
- **Upstream:** https://github.com/mattpocock/skills (MIT); fork https://github.com/racecraft-lab/skills, tag `speckit-pro-baseline`
- **Attribution precedent:** `speckit-pro/artifact-gallery/UPSTREAM-NOTICE.md`
- **Matt Pocock's stated position:** README (2026-04-28); "Software Fundamentals Matter More Than Ever", AI Engineer Europe (April 2026); https://www.aihero.dev/skills-to-spec; mattpocock/skills issue #906
