---
name: speckit-prd
description: "Collaboratively turns a raw product or technical idea into a lean PRD, technical roadmap and SPEC catalog, canonical OKF roadmap map, and generated roadmap-MOC compatibility view; roadmap-only mode turns an existing reviewed PRD into the roadmap and knowledge surfaces without rewriting the PRD. Use for: write or draft a PRD and roadmap; shape an idea or brief into a PRD; plan a product; decompose an existing PRD into a SPEC catalog; decide what features it needs; right-size the catalog before writing specs. Runs a one-question-at-a-time interview with recommended answers, then writes the applicable artifacts for speckit-scaffold-spec and speckit-autopilot. Not for per-spec scoping (use grill-me), worktree prep from an existing roadmap entry (use speckit-scaffold-spec), or SDD coaching (use speckit-coach). Requires an interactive session."
argument-hint: "a product/technical idea, a brief/file path, or --roadmap-only <existing-prd-path>"
user-invocable: true
license: MIT
compatibility: "Requires Claude Code with AskUserQuestion tool support. Codex variant in codex-skills/speckit-prd/ uses a free-text Q&A loop instead."
---

# SpecKit PRD — Collaborative PRD & Technical Roadmap Authoring

## Capability discovery & grounding

Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `speckit-pro/skills/speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it. (This governs your research-backed recommended answers, not the interview mechanics.)

## Durable knowledge

Follow [the shared knowledge lifecycle](../speckit-coach/references/knowledge-lifecycle.md).
If a bundle exists, run `knowledge-health` and a bounded `knowledge-search`
before the interview; verify selected sources and cite the resulting
`knowledge_use_receipt` in the PRD references. The technical roadmap remains the
catalog authority. Its reviewed grouping and rationale become the canonical OKF
roadmap concept; the roadmap-MOC is only a generated compatibility view.

## The collaboration contract

<hard_constraints>

- **One question at a time.** Use `AskUserQuestion`. Never batch a wall of
  questions. Walk the design tree branch by branch.
- **Always recommend.** Every question carries your recommended answer as the
  first option, marked `(Recommended)`, with a one-line rationale. The user
  agrees, course-corrects, or picks an alternative — they stay in the loop on
  every consequential decision.
- **Human-in-the-loop only.** This skill requires a real user answering in real
  time. If `AskUserQuestion` is unavailable (subagent, automation, CI), do not
  fabricate answers — draft from the supplied material only and mark every
  unconfirmed decision as an Open Question, or abort and ask the user to run it
  interactively.
- **Lean is the goal.** A PRD captures *validated decisions*; it does not
  replace discovery. Cut any section that does not reduce ambiguity. Resist
  turning the PRD into a design doc — it states the WHAT, not the HOW.

</hard_constraints>

## Prerequisites

PRDs and roadmaps are plain Markdown — this skill does **not** require the
SpecKit CLI to run. But the roadmap it produces feeds the SpecKit workflow, so
ground your recommendations in the project's existing decisions when they
exist:

```text
Read CLAUDE.md / AGENTS.md (tech stack, conventions)
Read .specify/memory/constitution.md if present (governance gates)
Glob docs/**/*roadmap*.md (is there an existing roadmap to extend?)
```

If a constitution exists, its principles become Constraints (§5) in the PRD and
must be honored by the SPEC catalog.

## What to Do

Full branch taxonomy, question-generation heuristics, and the decomposition
algorithm live in [`references/prd-authoring-protocol.md`](./references/prd-authoring-protocol.md) —
read it before starting. High-level loop:

### Mode selection

- **Normal mode:** accept an idea, brief, transcript, or empty input; interview
  the user and author both the PRD and roadmap.
- **Roadmap-only mode:** require `--roadmap-only <existing-prd-path>`. Read the
  reviewed PRD, derive its slug, and treat its goals, non-goals, acceptance
  criteria, and SPEC crosswalk as binding inputs. Skip PRD drafting and do not
  rewrite the PRD unless the user explicitly approves a correction. Interview
  only for unresolved decomposition, dependency, priority, or reviewability
  decisions, then author the roadmap and its knowledge surfaces.

### 1. Read the input and build a model

In normal mode, the input is an idea string, a brief / transcript file path, or
empty (ask the user for it). In roadmap-only mode, the input is the required
existing PRD path. Derive a `<slug>` (kebab-case) from the input. Read the
project context above so your recommendations are grounded, not generic.

### 2. Run the collaborative interview

In normal mode, walk the PRD design tree one branch at a time, in priority order
(uncertainty × impact). The branches map directly to PRD sections:

| Branch | Resolves PRD section |
| --- | --- |
| Problem & why-now | §1 Problem |
| Who it's for (users / segments) | §1 Problem, §3 audience framing |
| Outcomes / goals | §2.1 Goals |
| Scope cuts | §2.2 Non-goals |
| **Feature breakdown** (boundaries, sequence, dependencies) | §3 Features, §4 Migration, §7 SPEC Catalog |
| Acceptance criteria per feature | §3 AC-N.* |
| Constraints (governance, tech, NFRs at risk) | §5 Constraints |
| Unknowns | §6 Open Questions |

For each branch: generate the single highest-uncertainty question, determine
your recommended answer (consult code, constitution, and best practices), call
`AskUserQuestion` with the recommendation first, record the answer, update your
model. **The feature-breakdown branch is the most important** — it is where the
SPEC catalog is born. Drive features small enough that each maps to one
reviewable SPEC; if a feature is too big, split it into two features here.

In roadmap-only mode, skip branches already resolved by the PRD and ask only
questions needed to make the SPEC catalog executable.

Stop when no critical open questions remain (preferred), the user ends the
interview, or you hit the soft cap (~25–30 questions) and the user wraps up.

### 3. Draft the PRD

In normal mode, copy the PRD template and fill every section that applies. In
roadmap-only mode, skip this step and preserve the existing PRD bytes:

```text
Read("${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/prd-template.md")
Write("docs/prd-<slug>.md", <filled template>)
```

Number acceptance criteria `AC-<feature>.<n>`. Each Feature subsection in §3
carries its `(→ SPEC-00N)` tag. Fill the §7 SPEC Catalog Crosswalk so it is 1:1
with §3. Delete the optional appendix unless a sketch genuinely reduces
ambiguity.

### 4. Decompose into the technical roadmap (SPEC catalog)

Apply the decomposition algorithm (see `references/prd-authoring-protocol.md`
and `speckit-coach`'s technical-roadmap guidance). Copy the roadmap template and
expand each PRD Feature into one SPEC section:

```text
Read("${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/technical-roadmap-template.md")
Write("docs/ai/specs/<slug>-technical-roadmap.md", <filled template>)
```

**Right-size the catalog by construction.** Use SPIDR (split along a Spike,
Path, Interface, Data, or Rule seam) and vertical slicing so every SPEC is a
*thin, end-to-end slice* — cutting through all its layers to deliver one small
working capability — that clears the INVEST bar (Independent, Negotiable,
Valuable, Estimable, Small, Testable). Decompose into many thin vertical slices,
not a few fat horizontal specs (a SPEC that is "all the models" then "all the
UI" is a re-slicing signal). The canonical SPIDR + INVEST + vertical-slicing
guidance, the ~400 reviewable-LOC ceiling, and the spike escape hatch live in one
shared reference — read it, do not restate it:
[`speckit-coach/references/slicing-heuristics.md`](../speckit-coach/references/slicing-heuristics.md).

For each SPEC: scope (detailed enough to drive `/speckit-specify`), depends-on /
enables, priority, status (`⏳ Pending`), reviewability budget, and key files.
Set `**Source PRD:**` to `docs/prd-<slug>.md` and set `**Knowledge Map:**` to the
relative link `[Canonical project knowledge](../knowledge/projects/<slug>/index.md)`.
**Review the dependency graph with the user** (one more `AskUserQuestion`)
before finalizing — execution order is a consequential decision.

**Populate each entry's size budget from the shared estimator.** For every SPEC
you draft, derive its size signals from the entry itself — number of user stories
/ acceptance-criteria groups, files or surfaces touched, functional requirements,
and whether it is net-new or modifies existing code (mark a research-only slice
with `--spike`) — then run runner operation `estimate-spec-size`.

Populate that entry's existing **`Projected reviewable LOC`** field in its
`**Reviewability Budget:**` line with the returned `estimated_loc` (this is the
roadmap template's per-SPEC budget line — reuse it; do **not** add a new
`Budget` field or otherwise change the template schema), and add a one-line
INVEST/vertical-slice rationale to the entry's scope (e.g. "one vertical slice:
endpoint → handler → store; Independent and Small"). If the estimator returns
`status: "warn"` (the entry is over the documented ceiling), surface that as an
**advisory** note — record the size signal, optionally suggest the
`suggested_slices` count as a split the user may take, and continue the
interview. Nothing is blocked or rejected; the estimate is a forward guess that
shapes decomposition early, never a gate (see the shared reference's
"forward guess, not the authoritative count" caveat).

If the estimator cannot produce a usable result for any reason — the operation is
unavailable, it exits non-zero, or it prints empty/unparseable
output — treat it as an **absent estimate**: leave that entry's
`Projected reviewable LOC` field unpopulated (or note it as unavailable), add a
short advisory note, and continue the interview. Never read the script's exit
code as a gate and never let an unavailable estimate become a hard stop — the
catalog is still authored, just without the forward size signal on that entry.

Finish every accepted edit to the PRD and technical roadmap now, including the
Knowledge Map link, and persist both files. Reread their final bytes before
building source evidence. Do not edit either source after hashing it; if either
changes, discard the pending knowledge plan and recompute the source hashes.

### 5. Build the canonical knowledge map and compatibility MOC

Use the roadmap's reviewed phase/tier grouping and the rationale already
captured during decomposition; ask no new questions. Do not hand-author a MOC.

1. Inventory pre-existing legacy MOCs and `.specify/memory`, but do not run
   `init` or `migrate` yet.
2. From the finalized source bytes, build a candidate that matches
   `knowledge-candidate.schema.json`: `type: speckit-project-map`,
   `concept_path: projects/<slug>/roadmap.md`, stable `id`, project `<slug>`,
   non-empty `title`, `description`, and curated `body`, `state: reviewed`,
   `reviewed: true`, and `producer.skill: speckit-prd`. Every PRD/roadmap source
   carries its exact path, section, line evidence when available, and SHA-256.
   Set `legacy_view: docs/ai/specs/<slug>-roadmap-MOC.md`. If no canonical map
   exists, plan/apply `promote` with scope `projects/<slug>` **before
   migration**; promotion can initialize an absent bundle. If a canonical map
   already exists and the finalized PRD or roadmap bytes changed, plan/apply a
   reviewed same-path `supersede` replacement instead. Never use `rebuild` to
   refresh authoritative source hashes.
3. If the inventory found pre-existing legacy MOCs or memory, plan and apply
   `migrate` with `reviewed: true` and `legacy_memory_reviewed: true` only after
   promotion. Review the plan and require it to
   preserve the existing `projects/<slug>/roadmap.md`; migration may add other
   legacy records and projections, but must not overwrite the promoted concept.
4. Run `knowledge-health`. Plan and apply action `rebuild` with scope
   `projects/<slug>` only when the canonical map and source hashes are current
   but a generated project index, manifest, log, or MOC projection has drifted.
5. For every mutation, apply with `repo_root`, the complete returned `plan`,
   `plan_hash`, and `expected_snapshot`. A source edit or stale snapshot requires
   a new plan; never reuse the old hash.
6. If there are more than about ten epics, warn but do not block or regroup
   automatically.

The canonical roadmap concept owns curated grouping and rationale. Generated
indexes, status, links, and compatibility views are never hand-edited.

### 6. Verify and hand off

- Confirm §3 features, the §7 crosswalk, and the roadmap SPEC catalog are
  mutually consistent (same count, same names, same SPEC IDs).
- Confirm every SPEC's scope is detailed enough to seed `/speckit-specify`.
- Run `knowledge-health` and confirm the canonical roadmap concept, generated
  indexes, and compatibility MOC are current.
- Report the PRD, roadmap, canonical knowledge path, compatibility path, and the
  recommended next step.

## Output Contract

Committed source artifacts plus generated knowledge projections:

- `docs/prd-<slug>.md` — lean PRD (template sections, optional appendix dropped).
- `docs/ai/specs/<slug>-technical-roadmap.md` — roadmap whose **SPEC catalog**
  (Progress Tracking table + Specification Sections) is 1:1 with the PRD's
  Features, carrying the reciprocal link to the home note.
- `docs/ai/knowledge/projects/<slug>/roadmap.md` — canonical reviewed grouping
  and rationale, with generated project/spec indexes.
- `docs/ai/specs/<slug>-roadmap-MOC.md` — generated compatibility view; never
  hand-edit it.

Closing report:

```text
## PRD & Roadmap Ready

**PRD:** docs/prd-<slug>.md
**Technical Roadmap:** docs/ai/specs/<slug>-technical-roadmap.md
**Roadmap-MOC home note:** docs/ai/specs/<slug>-roadmap-MOC.md
**Canonical knowledge map:** docs/ai/knowledge/projects/<slug>/roadmap.md
**SPEC catalog:** SPEC-001 … SPEC-00N (one per PRD Feature)

**Next:**
/speckit-pro:speckit-status                       # see the catalog and what's ready
/speckit-pro:speckit-scaffold-spec SPEC-001       # prepare the first spec for autopilot
```

## Boundaries — what this skill does NOT do

- It does **not** scope a single spec that already exists in the roadmap. That
  is `/speckit-pro:grill-me` (per-spec, produces a design-concept doc).
- It does **not** create the worktree, branch, or workflow file. That is
  `/speckit-pro:speckit-scaffold-spec`.
- It does **not** teach SDD methodology. That is `/speckit-pro:speckit-coach`.
- It does **not** run autonomously. See the collaboration contract.

If the user already has a reviewed PRD and only needs the roadmap, use
`/speckit-pro:speckit-prd --roadmap-only <existing-prd-path>`. The coach may
explain decomposition, but this skill owns roadmap mutation and the coherent
OKF/MOC lifecycle.

## Examples

### Example 1 — idea to PRD + roadmap

User: *"Help me write a PRD for adding saved searches with email alerts to our app."*

1. Read CLAUDE.md / constitution for stack and gates.
2. Interview: problem → users → goals → non-goals → features (saved-search CRUD,
   alert scheduler, notification delivery, settings UI) → AC per feature →
   constraints → opens. Recommendation first on every question.
3. Draft `docs/prd-saved-searches.md` with four Features (§3), AC-1.* … AC-4.*,
   and a 1:1 §7 crosswalk to SPEC-001 … SPEC-004.
4. Decompose into `docs/ai/specs/saved-searches-technical-roadmap.md`; confirm
   the dependency graph and finalize its canonical knowledge link.
5. Reread and hash the finalized PRD and roadmap, promote
   `docs/ai/knowledge/projects/saved-searches/roadmap.md` first, migrate any
   pre-existing legacy MOCs or memory without replacing it, then rebuild its
   indexes and `docs/ai/specs/saved-searches-roadmap-MOC.md` compatibility view.
6. Report the source and knowledge paths; recommend `/speckit-pro:speckit-scaffold-spec SPEC-001`.

### Example 2 — brief file as input

User: *"Turn notes/discovery-call.md into a PRD."*

Read the file, treat it as discovery input, interview only on the gaps it leaves
open, then produce the same three artifacts.

### Example 3 — refusing a non-interactive run

A background agent invokes this skill. `AskUserQuestion` is unavailable. Draft a
best-effort PRD strictly from the supplied material, mark every unvalidated
decision as an Open Question (§6), and tell the caller the PRD needs an
interactive pass before it is roadmap-ready. Do not invent user intent.

## Troubleshooting

- **The PRD is ballooning into a design doc.** You are answering HOW. Move
  implementation detail to the roadmap's per-SPEC scope or to the optional
  appendix, and only if it reduces ambiguity. The PRD states WHAT and WHY.
- **A feature won't fit one reviewable SPEC.** Split it into two features in §3
  during the interview — the catalog should never contain a SPEC that blows the
  reviewability budget (see `speckit-coach`'s reviewability contract).
- **Features and SPEC catalog drift apart.** Re-run step 6. The §3 features, the
  §7 crosswalk, and the roadmap catalog must always have the same count, names,
  and IDs — that 1:1 mapping is the contract scaffold-spec relies on.
- **Natural-language prompts route elsewhere.** If "write a PRD" lands on a
  different skill, invoke explicitly: `/speckit-pro:speckit-prd <idea>`.

## References

- [`references/prd-authoring-protocol.md`](./references/prd-authoring-protocol.md) —
  full interview branch taxonomy, question heuristics, stop conditions, and the
  PRD→roadmap decomposition algorithm (read before starting).
- `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/prd-template.md` — the lean PRD template.
- `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/technical-roadmap-template.md` — the roadmap / SPEC-catalog template.
- `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/roadmap-moc-template.md` — generated legacy MOC compatibility-view template.
- Runner operations `knowledge-update-plan` and `knowledge-update-apply` — promote the canonical roadmap concept and rebuild projections.
- [`speckit-coach/references/slicing-heuristics.md`](../speckit-coach/references/slicing-heuristics.md) — the single source of truth for SPIDR + INVEST + vertical-slicing and the ~400 reviewable-LOC ceiling (summarized inline above; invoked via runner operation `estimate-spec-size`).
- `/speckit-pro:speckit-coach` — decomposition algorithm and SDD methodology depth.
- `/speckit-pro:grill-me` — the downstream per-spec interview that mirrors this skill's one-question-at-a-time machinery.
