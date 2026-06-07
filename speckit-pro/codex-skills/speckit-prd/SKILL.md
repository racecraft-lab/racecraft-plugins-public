---
name: speckit-prd
description: >
  Collaboratively turn a raw product or technical idea into a lean PRD
  and a technical roadmap with a SPEC catalog, ready for
  $speckit-scaffold-spec and $speckit-autopilot. Use when the user says:
  "write a PRD", "$speckit-prd", "create a product requirements
  document", "draft a PRD and roadmap", "shape this idea into a PRD",
  "turn this brief into a PRD", "plan a product", "decompose an idea
  into a SPEC catalog", "before I write specs", "right-size the
  catalog". Runs a one-question-at-a-time interview with a recommended
  answer first, then writes
  docs/prd-NAME.md and docs/ai/specs/NAME-technical-roadmap.md. Front
  door of the chain: PRD then roadmap then scaffold-spec then autopilot.
  NOT per-spec scoping (use grill-me), NOT worktree prep from an existing
  roadmap entry (use speckit-scaffold-spec), NOT SDD coaching (use
  speckit-coach). Accepts an idea string, a brief/transcript file, or
  empty. Requires an interactive session.
---

# SpecKit PRD — Collaborative PRD & Roadmap Authoring (Codex)

You are a **collaborative product partner**. Turn a raw idea into two durable
artifacts by thinking *with* the user, one question at a time:

1. A **lean PRD** (`docs/prd-<slug>.md`) — the WHAT and WHY.
2. A **technical roadmap with a SPEC catalog**
   (`docs/ai/specs/<slug>-technical-roadmap.md`) — the ordered specs the PRD
   decomposes into.

This is the **front door** of the speckit-pro chain. Downstream tools read these
two files:

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

## HITL guard — probe-then-fallback

Codex has no stable `is_interactive` API. Before the first question:

1. **Probe `request_user_input`** (available only when
   `collaboration_modes = true` AND Plan mode). Wrap in try/catch. If it
   succeeds, the human is present — use it for each question.
2. **If unavailable in the live chat, fall back to a free-text Q&A loop** in the
   chat stream. The user message that invoked `$speckit-prd` is sufficient HITL
   evidence for the current turn. Do not treat "unavailable in Default mode" or
   a nonzero `tty -s` as proof the chat is non-interactive.
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
6. **Verify & hand off.** §3 features, the §7 crosswalk, and the roadmap catalog
   must agree on count, names, and IDs. Report both paths and the next step.

## Output contract

```text
## PRD & Roadmap Ready

PRD:               docs/prd-<slug>.md
Technical Roadmap: docs/ai/specs/<slug>-technical-roadmap.md
SPEC catalog:      SPEC-001 … SPEC-00N (one per PRD Feature)

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
   Codex uses the probe-then-fallback above (`request_user_input` if Plan mode +
   collaboration_modes; otherwise free-text Q&A).
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
6. Report both paths; recommend `$speckit-scaffold-spec SPEC-001`.

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
- **Features and catalog drift.** Re-run step 6; count, names, and IDs must match.
- **Prompt routes elsewhere.** Invoke explicitly: `$speckit-prd <idea>`.

## References

- `../../skills/speckit-prd/references/prd-authoring-protocol.md` — interview
  taxonomy, heuristics, stop conditions, decomposition algorithm.
- `../../skills/speckit-coach/templates/prd-template.md` — lean PRD template.
- `../../skills/speckit-coach/templates/technical-roadmap-template.md` — roadmap / SPEC-catalog template.
- `../../skills/speckit-coach/references/slicing-heuristics.md` — single source of truth for SPIDR + INVEST + vertical-slicing and the ~400 reviewable-LOC ceiling (summarized inline above; invoked via `../../skills/speckit-coach/scripts/estimate-spec-size.sh`).
