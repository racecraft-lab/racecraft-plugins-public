---
name: speckit-prd
description: >
  Collaboratively turn a product or technical idea into a lean PRD, a
  technical roadmap with a SPEC catalog, a canonical OKF roadmap map, and a
  generated MOC compatibility view, ready for $speckit-scaffold-spec and
  $speckit-autopilot. Use for "$speckit-prd", "write a PRD", "draft a PRD and
  roadmap", "plan a product", "decompose an idea into a SPEC catalog",
  "decompose this existing PRD", "--roadmap-only", or "right-size the
  catalog". Runs a recommendation-first, one-question-at-a-time interview.
  Normal mode accepts an idea, brief or transcript file, or empty input.
  Roadmap-only mode accepts a reviewed PRD path, preserves that PRD, and writes
  only downstream roadmap and knowledge surfaces. Not for per-spec scoping
  (use grill-me), worktree prep (use speckit-scaffold-spec), or SDD coaching
  (use speckit-coach). Requires an interactive session.
---

# SpecKit PRD — Collaborative PRD & Roadmap Authoring (Codex)

## Capability discovery & grounding

Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `speckit-pro/skills/speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it. (This governs your research-backed recommended answers, not the interview mechanics.)

## Durable knowledge

Follow [the shared knowledge lifecycle](../speckit-coach/references/knowledge-lifecycle.md).
If a bundle exists, run `knowledge-health` and a bounded `knowledge-search`
before the interview; verify selected sources and cite the resulting
`knowledge_use_receipt` in the PRD references. The technical roadmap remains the
catalog authority. Its reviewed grouping and rationale become the canonical OKF
roadmap concept; the roadmap-MOC is only a generated compatibility view.

You are a **collaborative product partner**. In normal mode, turn a raw idea
into three durable artifacts by thinking *with* the user, one question at a
time, then emit a canonical map and generated compatibility view. In
roadmap-only mode, consume the existing reviewed PRD as artifact 1 and produce
artifacts 2-4 without rewriting it:

1. A **lean PRD** (`docs/prd-<slug>.md`) — the WHAT and WHY.
2. A **technical roadmap with a SPEC catalog**
   (`docs/ai/specs/<slug>-technical-roadmap.md`) — the ordered specs the PRD
   decomposes into.
3. A canonical **OKF roadmap map**
   (`docs/ai/knowledge/projects/<slug>/roadmap.md`) — reviewed grouping and rationale.
4. A generated **roadmap-MOC compatibility view** (`docs/ai/specs/<slug>-roadmap-MOC.md`) — a single
   navigable map for the whole spec tree, derived from the roadmap (see step 6).

This is the **front door** of the speckit-pro chain. Downstream tools read the
PRD and roadmap:

```text
idea ──► PRD ──► Technical Roadmap (SPEC catalog)
                        └─► $speckit-scaffold-spec SPEC-NNN ──► $speckit-autopilot
```

The property that makes the output autopilot-ready is the **Feature ⇄ SPEC
mapping**: every Feature / Acceptance-Criteria group in the PRD becomes exactly
one SPEC in the roadmap catalog. Preserve that 1:1 mapping.

## The collaboration contract

- **One question at a time.** Walk the design tree branch by branch; never batch.
- **Always recommend.** Each question presents your recommended answer first,
  marked `(Recommended)`, with a one-line rationale, then 1–2 alternatives.
- **Human-in-the-loop only.** A real user must answer in real time.
- **Lean is the goal.** Capture validated decisions, not discovery. Cut any
  section that does not reduce ambiguity. State the WHAT, not the HOW.

## HITL guard — native picker required

Before the first question, verify Codex exposes the native ask-user-question
surface:

1. **Call `request_user_input`** for every question. In Codex Default mode this
   requires `codex features enable default_mode_request_user_input` before the
   thread starts or resumes.
2. **If `request_user_input` is unavailable, stop instead of asking in
   Markdown/free-text.** Tell the user to enable
   `default_mode_request_user_input`, restart Codex or open a new thread, then
   rerun `$speckit-prd`. The user message that invoked `$speckit-prd` is HITL
   evidence, but it is not a substitute for the native picker UI.
3. **Abort only for autonomous/background invocations** (`codex exec`, CI, cron,
   autopilot agents/subagents). Draft from supplied material only and mark every
   unvalidated decision as an Open Question, or abort and ask for an interactive
   pass. Never fabricate user intent.

## Prerequisites

PRDs and roadmaps are plain Markdown — no SpecKit CLI required to run. Ground
recommendations in existing decisions when present:

```text
Read CLAUDE.md / AGENTS.md          (tech stack, conventions)
Read .specify/memory/constitution.md if present  (governance gates → Constraints)
Glob docs/**/*roadmap*.md           (existing roadmap to extend?)
```

## How to run

Full branch taxonomy, question heuristics, stop conditions, and the
PRD→roadmap decomposition algorithm live in
`references/prd-authoring-protocol.md` — read it before
starting. High-level loop:

**Select the mode first.** Normal mode accepts an idea, brief, transcript, or
empty input and authors both PRD and roadmap. Roadmap-only mode requires
`--roadmap-only <existing-prd-path>`; treat that reviewed PRD's goals,
non-goals, acceptance criteria, and SPEC crosswalk as binding. Do not rewrite
it unless the user explicitly approves a correction. Ask only questions needed
for unresolved decomposition, dependency, priority, or reviewability decisions.

1. **Read the input** (idea string, brief/transcript file, existing PRD in
   roadmap-only mode, or ask the user). Derive a kebab-case `<slug>`.
2. **Build a model** from the project context above.
3. **Interview** one branch at a time, recommendation first. In normal mode:
   Problem → Users → Goals → Non-goals → **Feature breakdown** → Sequencing →
   Acceptance criteria per feature → Constraints → Open questions. The
   feature-breakdown branch is the most important — it births the SPEC catalog.
   Keep features small enough that each maps to one reviewable SPEC.
   In roadmap-only mode, skip branches already resolved by the PRD.
4. **Draft the PRD in normal mode only** from
   `../speckit-coach/templates/prd-template.md`; number `AC-N.*`, tag
   each Feature `(→ SPEC-00N)`, fill the §7 SPEC Catalog Crosswalk 1:1 with §3.
   Write `docs/prd-<slug>.md`. In roadmap-only mode preserve the existing PRD
   bytes and skip this write.
5. **Decompose into the roadmap** from
   `../speckit-coach/templates/technical-roadmap-template.md` — one
   SPEC per Feature, with scope detailed enough to drive `/speckit-specify`,
   dependencies, priority, status `⏳ Pending`, reviewability budget. Set
   `Source PRD` to `docs/prd-<slug>.md` and `Knowledge Map` to the relative link
   `[Canonical project knowledge](../knowledge/projects/<slug>/index.md)`.
   Confirm the dependency graph with the user. Write
   `docs/ai/specs/<slug>-technical-roadmap.md`.

   **Right-size the catalog by construction.** Use SPIDR (split along a Spike,
   Path, Interface, Data, or Rule seam) and vertical slicing so every SPEC is a
   *thin, end-to-end slice* — cutting through all its layers to deliver one
   small working capability — that clears the INVEST bar (Independent,
   Negotiable, Valuable, Estimable, Small, Testable). Emit many thin vertical
   slices, not a few fat horizontal specs (an "all the models, then all the UI"
   SPEC is a re-slicing signal). The canonical SPIDR + INVEST + vertical-slicing
   guidance, the ~400 reviewable-LOC ceiling, and the spike escape hatch live in
   one shared reference — read it, do not restate it:
   `../speckit-coach/references/slicing-heuristics.md`.

   **Populate each entry's size budget from the shared estimator.** For every
   SPEC you draft, derive its size signals from the entry itself — number of
   user stories / acceptance-criteria groups, files or surfaces touched,
   functional requirements, and whether it is net-new or modifies existing code
   (mark a research-only slice with `--spike`) — then run runner operation
   `estimate-spec-size` with those signals.
   Populate that entry's existing `Projected reviewable LOC` field in its
   `Reviewability Budget` line with the returned `estimated_loc` (reuse the
   roadmap template's per-SPEC budget line; do **not** add a new `Budget` field
   or change the template schema), and add a one-line INVEST/vertical-slice
   rationale to the entry's scope. If the estimator returns `status: "warn"`
   (over the documented ceiling), surface it as an **advisory** note — record the
   size signal, optionally suggest the `suggested_slices` count as a split the
   user may take, and continue the interview. Nothing is blocked or rejected; the
   estimate is a forward guess that shapes decomposition early, never a gate.

   If the estimator cannot produce a usable result for any reason — the operation is
   unavailable, it exits non-zero, or it prints empty/unparseable
   output — treat it as an **absent estimate**: leave that entry's
   `Projected reviewable LOC` field unpopulated (or note it as unavailable), add a
   short advisory note, and continue. Never read the script's exit code as a gate
   and never let an unavailable estimate become a hard stop.
   Finish every accepted edit to the PRD and roadmap now, including the
   Knowledge Map link, and persist both. Reread the final bytes before building
   source evidence. If either source changes after hashing, discard the pending
   knowledge plan and recompute its hashes.
6. **Build the canonical knowledge map and compatibility MOC.** Use the reviewed
   roadmap grouping and rationale; ask no new questions and do not hand-author a
   MOC. Inventory pre-existing legacy MOCs and `.specify/memory`, but do not run
   `init` or `migrate` yet. From the finalized source bytes, build a candidate
   matching `knowledge-candidate.schema.json`: `type: speckit-project-map`,
   `concept_path: projects/<slug>/roadmap.md`, stable `id`, project `<slug>`,
   non-empty `title`, `description`, and curated `body`, `state: reviewed`,
   `reviewed: true`, and `producer.skill: speckit-prd`. Every PRD/roadmap source
   carries its exact path, section, line evidence when available, and SHA-256.
   Set `legacy_view: docs/ai/specs/<slug>-roadmap-MOC.md`. If no canonical map
   exists, plan/apply `promote` with scope `projects/<slug>` **first**;
   promotion can initialize an absent bundle. If a canonical map exists and
   finalized PRD or roadmap bytes changed, build a reviewed same-path
   replacement and plan/apply `supersede`; never use `rebuild` to refresh a
   source hash. If the inventory found legacy
   MOCs or memory, plan and apply `migrate` with `reviewed: true` and
   `legacy_memory_reviewed: true` after promotion, and
   require its plan to preserve the existing `projects/<slug>/roadmap.md` rather
   than overwrite it. Then run `knowledge-health`; plan/apply `rebuild` with
   scope `projects/<slug>` only when canonical sources are current but a
   generated index, manifest, log, or compatibility view drifted. Every apply carries `repo_root`, the complete returned
   `plan`, `plan_hash`, and `expected_snapshot`. A source edit or stale snapshot
   requires a new plan and hash. Review the canonical roadmap, generated
   indexes, and generated compatibility view. Warn, but do not block, when the
   roadmap has more than about ten epics.

7. **Verify & hand off.** §3 features, the §7 crosswalk, and the roadmap catalog
   must agree on count, names, and IDs. Run `knowledge-health` and confirm the
   canonical roadmap concept, generated indexes, and compatibility MOC are
   current. Report all paths and the next step.

## Output contract

Committed source artifacts plus the canonical roadmap concept, generated
indexes, and generated roadmap-MOC compatibility view.

```text
## PRD & Roadmap Ready

PRD:                     docs/prd-<slug>.md
Technical Roadmap:       docs/ai/specs/<slug>-technical-roadmap.md
Roadmap-MOC home note:   docs/ai/specs/<slug>-roadmap-MOC.md
Canonical knowledge map: docs/ai/knowledge/projects/<slug>/roadmap.md
SPEC catalog:            SPEC-001 … SPEC-00N (one per PRD Feature)

Next:
$speckit-status                       # see the catalog and what's ready
$speckit-scaffold-spec SPEC-001       # prepare the first spec for autopilot
```

## Boundaries — what this skill does NOT do

- Not per-spec scoping of a roadmap entry — that is `$grill-me`.
- Not worktree/branch/workflow prep — that is `$speckit-scaffold-spec`.
- Not SDD methodology coaching — that is `$speckit-coach`.
- Not autonomous. See the HITL guard.

If the user already has a reviewed PRD and only needs the roadmap, use
`$speckit-prd --roadmap-only <existing-prd-path>`. The coach may explain
decomposition, but this skill owns roadmap mutation and the coherent OKF/MOC
lifecycle.

## Codex-specific notes

This Codex variant differs from the Claude Code variant
(`speckit-pro/skills/speckit-prd/`) in three ways:

1. **Interview tool.** Claude Code uses `AskUserQuestion` (always available);
   Codex uses `request_user_input`. In Default mode, enable
   `default_mode_request_user_input` before starting the thread; otherwise stop
   instead of rendering Markdown questions.
2. **Invocation syntax.** Claude Code: `/speckit-pro:speckit-prd`. Codex:
   `$speckit-prd`. Custom slash commands are deprecated in Codex.
3. **No `commands/` directory.** Ships only as a skill.

## Examples

### Example 1 — idea to PRD + roadmap

User: *"$speckit-prd — write a PRD for saved searches with email alerts."*

1. HITL probe (succeeds in interactive session).
2. Read CLAUDE.md / constitution for stack and gates.
3. Interview: problem → users → goals → non-goals → features (search CRUD, alert
   scheduler, delivery, settings UI) → AC per feature → constraints → opens.
4. Draft `docs/prd-saved-searches.md` (Features §3, AC-1.* … AC-4.*, §7 crosswalk
   to SPEC-001 … SPEC-004).
5. Decompose into `docs/ai/specs/saved-searches-technical-roadmap.md`; confirm the
   dependency graph and finalize its canonical knowledge link.
6. Reread and hash the finalized PRD and roadmap, promote
   `docs/ai/knowledge/projects/saved-searches/roadmap.md` first, migrate any
   pre-existing legacy MOCs or memory without replacing it, then rebuild its
   indexes and `docs/ai/specs/saved-searches-roadmap-MOC.md` compatibility view.
7. Report the source and knowledge paths; recommend `$speckit-scaffold-spec SPEC-001`.

### Example 2 — existing PRD to roadmap only

User: *"$speckit-prd --roadmap-only docs/prd-saved-searches.md"*

Read and preserve the reviewed PRD, interview only on unresolved catalog
decisions, write the technical roadmap, then promote or same-path supersede the
canonical project map and regenerate projections through the runner.

### Example 3 — refusing a non-interactive run

A background `codex exec` job invokes this skill. The HITL probe cannot confirm a
live user. Draft a best-effort PRD strictly from supplied material, mark every
unvalidated decision as an Open Question, and tell the caller the PRD needs an
interactive pass before it is roadmap-ready.

## Troubleshooting

- **PRD ballooning into a design doc.** You are answering HOW. Push detail into
  the roadmap's per-SPEC scope; keep the PRD on WHAT and WHY.
- **A feature won't fit one reviewable SPEC.** Split it into two features during
  the interview — the PRD is the cheapest place to split.
- **Features and catalog drift.** Re-run step 7; count, names, and IDs must match.
- **Prompt routes elsewhere.** Invoke explicitly: `$speckit-prd <idea>`.

## References

- `references/prd-authoring-protocol.md` — interview
  taxonomy, heuristics, stop conditions, decomposition algorithm.
- `../speckit-coach/templates/prd-template.md` — lean PRD template.
- `../speckit-coach/templates/technical-roadmap-template.md` — roadmap / SPEC-catalog template.
- `../speckit-coach/templates/roadmap-moc-template.md` — generated legacy MOC compatibility-view template.
- Runner operations `knowledge-update-plan` and `knowledge-update-apply` — promote the canonical roadmap concept and rebuild projections.
- `../speckit-coach/references/slicing-heuristics.md` — single source of truth for SPIDR + INVEST + vertical-slicing and the ~400 reviewable-LOC ceiling (summarized inline above; invoked via runner operation `estimate-spec-size`).
