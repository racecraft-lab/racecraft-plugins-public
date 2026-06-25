---
name: speckit-prd
description: >
  Collaboratively turn a raw product or technical idea into three
  artifacts — a lean PRD, a technical roadmap with a SPEC catalog,
  and a roadmap-MOC home note — ready for $speckit-scaffold-spec and
  $speckit-autopilot. Use when the user says: "write a PRD",
  "$speckit-prd", "create a product requirements document",
  "draft a PRD and roadmap", "shape this idea into a PRD",
  "turn this brief into a PRD", "plan a product",
  "decompose an idea into a SPEC catalog", "before I write specs",
  "right-size the catalog". Runs a one-question-at-a-time interview
  with a recommended answer first, then writes docs/prd-NAME.md,
  docs/ai/specs/NAME-technical-roadmap.md, and
  docs/ai/specs/NAME-roadmap-MOC.md. Front door of the chain: PRD
  then roadmap then scaffold-spec then autopilot. NOT per-spec scoping
  (use grill-me), NOT worktree prep (use speckit-scaffold-spec), NOT
  SDD coaching (use speckit-coach). Accepts an idea string, a
  brief/transcript file, or empty. Requires an interactive session.
---

# SpecKit PRD — Collaborative PRD & Roadmap Authoring (Codex)

## Capability discovery & grounding

Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `speckit-pro/skills/speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it. (This governs your research-backed recommended answers, not the interview mechanics.)

You are a **collaborative product partner**. Turn a raw idea into two durable
artifacts by thinking *with* the user, one question at a time, then emit a third
derived from them:

1. A **lean PRD** (`docs/prd-<slug>.md`) — the WHAT and WHY.
2. A **technical roadmap with a SPEC catalog**
   (`docs/ai/specs/<slug>-technical-roadmap.md`) — the ordered specs the PRD
   decomposes into.
3. A **roadmap-MOC home note** (`docs/ai/specs/<slug>-roadmap-MOC.md`) — a single
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
`../../skills/speckit-prd/references/prd-authoring-protocol.md` — read it before
starting. High-level loop:

1. **Read the input** (idea string, brief/transcript file, or ask the user).
   Derive a kebab-case `<slug>`.
2. **Build a model** from the project context above.
3. **Interview** one branch at a time, recommendation first:
   Problem → Users → Goals → Non-goals → **Feature breakdown** → Sequencing →
   Acceptance criteria per feature → Constraints → Open questions. The
   feature-breakdown branch is the most important — it births the SPEC catalog.
   Keep features small enough that each maps to one reviewable SPEC.
4. **Draft the PRD** from
   `../../skills/speckit-coach/templates/prd-template.md`; number `AC-N.*`, tag
   each Feature `(→ SPEC-00N)`, fill the §7 SPEC Catalog Crosswalk 1:1 with §3.
   Write `docs/prd-<slug>.md`.
5. **Decompose into the roadmap** from
   `../../skills/speckit-coach/templates/technical-roadmap-template.md` — one
   SPEC per Feature, with scope detailed enough to drive `/speckit-specify`,
   dependencies, priority, status `⏳ Pending`, reviewability budget. Set
   `Source PRD` to `docs/prd-<slug>.md`. Confirm the dependency graph with the
   user. Write `docs/ai/specs/<slug>-technical-roadmap.md`.

   **Right-size the catalog by construction.** Use SPIDR (split along a Spike,
   Path, Interface, Data, or Rule seam) and vertical slicing so every SPEC is a
   *thin, end-to-end slice* — cutting through all its layers to deliver one
   small working capability — that clears the INVEST bar (Independent,
   Negotiable, Valuable, Estimable, Small, Testable). Emit many thin vertical
   slices, not a few fat horizontal specs (an "all the models, then all the UI"
   SPEC is a re-slicing signal). The canonical SPIDR + INVEST + vertical-slicing
   guidance, the ~400 reviewable-LOC ceiling, and the spike escape hatch live in
   one shared reference — read it, do not restate it:
   `../../skills/speckit-coach/references/slicing-heuristics.md`.

   **Populate each entry's size budget from the shared estimator.** For every
   SPEC you draft, derive its size signals from the entry itself — number of
   user stories / acceptance-criteria groups, files or surfaces touched,
   functional requirements, and whether it is net-new or modifies existing code
   (mark a research-only slice with `--spike`) — then run the single shared
   estimator:
   `bash "../../skills/speckit-coach/scripts/estimate-spec-size.sh" --user-stories N --files N --frs N --new-vs-modify new|modify [--spike]`.
   Populate that entry's existing `Projected reviewable LOC` field in its
   `Reviewability Budget` line with the returned `estimated_loc` (reuse the
   roadmap template's per-SPEC budget line; do **not** add a new `Budget` field
   or change the template schema), and add a one-line INVEST/vertical-slice
   rationale to the entry's scope. If the estimator returns `status: "warn"`
   (over the documented ceiling), surface it as an **advisory** note — record the
   size signal, optionally suggest the `suggested_slices` count as a split the
   user may take, and continue the interview. Nothing is blocked or rejected; the
   estimate is a forward guess that shapes decomposition early, never a gate.

   If the estimator cannot produce a usable result for any reason — the script is
   missing, `jq` is missing, it exits non-zero, or it prints empty/unparseable
   output — treat it as an **absent estimate**: leave that entry's
   `Projected reviewable LOC` field unpopulated (or note it as unavailable), add a
   short advisory note, and continue. Never read the script's exit code as a gate
   and never let an unavailable estimate become a hard stop.
6. **Emit the roadmap-MOC home note (third artifact).** When — and only when —
   you have just authored a fresh PRD + technical-roadmap, also write a
   roadmap-MOC **home note** at `docs/ai/specs/<slug>-roadmap-MOC.md`: one
   navigable map for the whole spec tree, carrying two zones. This is
   **new-roadmaps-only** — never backfill a home note onto an existing/legacy
   roadmap (a later spec owns retro-migration).

   **6a. Derive the curated epics zone (ZERO new interview questions).** The
   roadmap's phase/tier grouping IS the epic structure — reuse it; ask the user
   nothing new for this (the decomposition already happened in step 5). For each
   phase/tier scaffold one epic: an epic title (the phase name), the phase's
   member SPEC-MOC links as relative `[]()` links, and a one-line advisory
   **"Why:"** placeholder the author refines by hand. If the roadmap has **no
   phase grouping** (a flat catalog), emit a single **"Specs"** epic listing all
   specs plus a one-line advisory note to group them. The curated zone is an
   editable scaffold; the generator never touches it.

   **6b. Write from the template, then fill the INDEX.** Copy the shared template
   so the file carries **only** the empty `GENERATED:INDEX` sentinel pair (the
   template ships exactly that pair — not PRS or BACKLINKS — so the generator's
   whole-zone-rewrite path fills only the INDEX). Set the home note's frontmatter
   `up:` to a relative `[]()` link to `<slug>-technical-roadmap.md`, fill the
   curated epics zone around the sentinels, and write
   `docs/ai/specs/<slug>-roadmap-MOC.md` from
   `../../skills/speckit-coach/templates/roadmap-moc-template.md`. Then invoke the
   generator to fill the INDEX — **passing the consumer's repo root positionally**.
   The generator's default repo root is the plugin's parent, correct in the
   plugin-source repo but **wrong in a consumer install** (the plugin lives in the
   plugin cache, not under the user's repo), so always pass the user's project root
   (the directory holding `docs/` and `specs/`) explicitly:
   `bash "../../skills/speckit-autopilot/scripts/generate-spec-index.sh" "$REPO_ROOT"`.
   The generator fills one `- [<spec_id>](../../../specs/<dir>/SPEC-MOC.md) · <status>`
   row per gated spec, normalized-ID ascending. Do not author the sentinel bytes or
   the INDEX rows by hand — the template carries the sentinels and the generator owns
   the rows.

   **6c. Add the reciprocal roadmap link.** Add one line to the technical-roadmap
   linking back to the home note (a relative `[]()` link to
   `<slug>-roadmap-MOC.md`), so the two top-level documents are mutually reachable.
   Do **not** change any spec-MOC's `up:`, the spec-MOC template, or
   scaffold-spec — the home note is a downward index + curated layer, leaving the
   per-spec upward-navigation contract untouched.

   **6d. Epic-count advisory (warn, never block).** If the derived scaffold yields
   more than ~10 epics, print a single one-line advisory (e.g. "11 epics — consider
   consolidating; >~10 strains navigability") and **still write the home note**.
   The cap is advisory only — never a block, never a CI lint.

7. **Verify & hand off.** §3 features, the §7 crosswalk, and the roadmap catalog
   must agree on count, names, and IDs. Confirm the home note exists with both
   zones (curated epics + a filled GENERATED INDEX) and that the roadmap carries
   the reciprocal link. Report the three paths and the next step.

## Output contract

Three committed Markdown files: the lean PRD, the technical-roadmap (carrying the
reciprocal link to the home note), and the roadmap-MOC home note (curated epics
zone + generator-filled GENERATED INDEX zone, `up:` linking back to the roadmap).

```text
## PRD & Roadmap Ready

PRD:                     docs/prd-<slug>.md
Technical Roadmap:       docs/ai/specs/<slug>-technical-roadmap.md
Roadmap-MOC home note:   docs/ai/specs/<slug>-roadmap-MOC.md
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

If the user already has a PRD and only needs the roadmap, hand off to
`$speckit-coach help me create a technical roadmap` (PRD-in, roadmap-out). This
skill is for when the PRD does not exist yet.

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
   dependency graph.
6. Emit `docs/ai/specs/saved-searches-roadmap-MOC.md` (curated epics zone from the
   roadmap's phases + a generator-filled GENERATED INDEX); add the reciprocal link.
7. Report all three paths; recommend `$speckit-scaffold-spec SPEC-001`.

### Example 2 — refusing a non-interactive run

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

- `../../skills/speckit-prd/references/prd-authoring-protocol.md` — interview
  taxonomy, heuristics, stop conditions, decomposition algorithm.
- `../../skills/speckit-coach/templates/prd-template.md` — lean PRD template.
- `../../skills/speckit-coach/templates/technical-roadmap-template.md` — roadmap / SPEC-catalog template.
- `../../skills/speckit-coach/templates/roadmap-moc-template.md` — roadmap-MOC home-note template (carries the empty GENERATED INDEX sentinel pair the generator fills).
- `../../skills/speckit-autopilot/scripts/generate-spec-index.sh` — the generator that fills the home note's GENERATED INDEX zone (invoke with the consumer repo root positionally).
- `../../skills/speckit-coach/references/slicing-heuristics.md` — single source of truth for SPIDR + INVEST + vertical-slicing and the ~400 reviewable-LOC ceiling (summarized inline above; invoked via `../../skills/speckit-coach/scripts/estimate-spec-size.sh`).
