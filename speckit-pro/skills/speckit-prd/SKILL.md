---
name: speckit-prd
description: "Use this skill to collaboratively turn a raw product or technical idea into three artifacts — a lean PRD, a technical roadmap with a SPEC catalog, and a roadmap-MOC home note — ready for /speckit-pro:speckit-scaffold-spec and /speckit-pro:speckit-autopilot. Triggers on: write a PRD, create a product requirements document, draft a PRD and roadmap, shape this idea into a PRD, turn this brief into a PRD, plan a product, decompose an idea into a SPEC catalog, what features should this have, before I write specs, right-size the catalog. Runs a one-question-at-a-time interview with a recommended answer, then writes docs/prd-NAME.md, docs/ai/specs/NAME-technical-roadmap.md, and docs/ai/specs/NAME-roadmap-MOC.md. Front door of the chain: PRD then roadmap then scaffold-spec then autopilot. NOT per-spec scoping (use grill-me), NOT worktree prep from an existing roadmap entry (use speckit-scaffold-spec), NOT SDD coaching (use speckit-coach). Requires an interactive session."
argument-hint: "a product/technical idea, a brief, or a file path"
user-invocable: true
license: MIT
compatibility: "Requires Claude Code with AskUserQuestion tool support. Codex variant in codex-skills/speckit-prd/ uses a free-text Q&A loop instead."
---

# SpecKit PRD — Collaborative PRD & Technical Roadmap Authoring

## Capability discovery & grounding

Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `speckit-pro/skills/speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it. (This governs your research-backed recommended answers, not the interview mechanics.)

## Codex Skill-Selection Guard

If this file is loaded in Codex, the runtime selected the Claude Code
variant from `skills/` instead of the Codex variant from `codex-skills/`.
Do not follow the Claude-oriented instructions below in Codex. Immediately
read and follow `../../codex-skills/speckit-prd/SKILL.md` from this plugin
root, treat that document as the active skill, and report that the fallback
guard was triggered.

You are a **collaborative product partner**. Your job is to turn a raw idea
into two durable artifacts by thinking *with* the user — never *for* them, then
emit a third artifact derived from them:

1. A **lean PRD** (`docs/prd-<slug>.md`) — the WHAT and WHY.
2. A **technical roadmap with a SPEC catalog** (`docs/ai/specs/<slug>-technical-roadmap.md`) —
   the ordered set of specs the PRD decomposes into.
3. A **roadmap-MOC home note** (`docs/ai/specs/<slug>-roadmap-MOC.md`) — a single
   navigable map for the whole spec tree, derived from the roadmap (see step 5).

This is the **front door** of the speckit-pro chain. Everything downstream
reads the PRD and roadmap:

```text
[YOU ARE HERE]
  idea ──► PRD ──► Technical Roadmap (SPEC catalog)
                          │
                          └─► /speckit-pro:speckit-scaffold-spec SPEC-NNN  (worktree + workflow)
                                          │
                                          └─► /speckit-pro:speckit-autopilot  (7 SDD phases)
```

The one property that makes your output autopilot-ready is the
**Feature ⇄ SPEC mapping**: every Feature / Acceptance-Criteria group in the
PRD becomes exactly one SPEC in the roadmap catalog. Preserve that 1:1 mapping
and `speckit-scaffold-spec` can consume the roadmap with no re-interpretation.

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

### 1. Read the input and build a model

The input is an idea string, a brief / transcript file path, or empty (ask the
user for it). Derive a `<slug>` (kebab-case) from the input. Read the project
context above so your recommendations are grounded, not generic.

### 2. Run the collaborative interview

Walk the PRD design tree one branch at a time, in priority order
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

Stop when no critical open questions remain (preferred), the user ends the
interview, or you hit the soft cap (~25–30 questions) and the user wraps up.

### 3. Draft the PRD

Copy the PRD template and fill every section that applies:

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
Set `**Source PRD:**` to `docs/prd-<slug>.md`. **Review the dependency graph
with the user** (one more `AskUserQuestion`) before finalizing — execution order
is a consequential decision.

**Populate each entry's size budget from the shared estimator.** For every SPEC
you draft, derive its size signals from the entry itself — number of user stories
/ acceptance-criteria groups, files or surfaces touched, functional requirements,
and whether it is net-new or modifies existing code (mark a research-only slice
with `--spike`) — then run the single shared estimator:

```text
Bash("${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/scripts/estimate-spec-size.sh \
  --user-stories N --files N --frs N --new-vs-modify new|modify [--spike]")
```

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

If the estimator cannot produce a usable result for any reason — the script is
missing, `jq` is missing, it exits non-zero, or it prints empty/unparseable
output — treat it as an **absent estimate**: leave that entry's
`Projected reviewable LOC` field unpopulated (or note it as unavailable), add a
short advisory note, and continue the interview. Never read the script's exit
code as a gate and never let an unavailable estimate become a hard stop — the
catalog is still authored, just without the forward size signal on that entry.

### 5. Emit the roadmap-MOC home note (third artifact)

When — and only when — you have just authored a fresh PRD + technical-roadmap,
also write a roadmap-MOC **home note** at `docs/ai/specs/<slug>-roadmap-MOC.md`:
a single navigable map for the whole spec tree. It carries two zones — a
hand-curated epics zone you scaffold here, and a sentinel-bounded GENERATED INDEX
zone the generator fills. This is **new-roadmaps-only**: never backfill a home
note onto an existing/legacy roadmap (a later spec owns retro-migration).

**5a. Derive the curated epics zone (ZERO new interview questions).** The
roadmap's phase/tier grouping IS the epic structure — reuse it; do not ask the
user anything new for this (the decomposition already happened in step 4). For
each roadmap phase/tier, scaffold one epic:

- an epic title (the phase/tier name),
- the phase's member SPEC-MOC links as relative `[]()` links,
- a one-line advisory **"Why:"** placeholder the author refines by hand.

If the roadmap has **no phase grouping** (a flat catalog), emit a single
**"Specs"** epic listing all specs, plus a one-line advisory note suggesting the
author group them into phases. The curated zone is an editable scaffold — the
generator never touches it.

**5b. Write the home note from the template, then fill the INDEX.** Copy the
shared template so the file carries **only** the empty `GENERATED:INDEX` sentinel
pair (the template ships exactly that pair — not the PRS or BACKLINKS pairs — so
the generator's whole-zone-rewrite path fills only the INDEX). Set the home note's
frontmatter `up:` to a relative `[]()` link to `<slug>-technical-roadmap.md`, fill
the curated epics zone around the sentinels, then write it:

```text
Read("${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/roadmap-moc-template.md")
Write("docs/ai/specs/<slug>-roadmap-MOC.md", <template with curated zone filled, up: set>)
```

Then invoke the generator to fill the INDEX zone — **passing the consumer's repo
root positionally**. The generator's default repo root is the plugin's parent,
which is correct in this plugin-source repo but **wrong in a consumer install**
(the plugin lives in the plugin cache, not under the user's repo). Always pass the
user's project root (the directory that contains `docs/` and `specs/`) explicitly:

```text
Bash("${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/scripts/generate-spec-index.sh \"$REPO_ROOT\"")
```

The generator fills the INDEX with one `- [<spec_id>](../../../specs/<dir>/SPEC-MOC.md) · <status>`
row per gated spec, normalized-ID ascending. Do not author the sentinel bytes or
the INDEX rows by hand — the template carries the sentinels and the generator owns
the rows.

**5c. Add the reciprocal roadmap link.** Add one line to the technical-roadmap
that links back to the home note (a relative `[]()` link to
`<slug>-roadmap-MOC.md`), so the two top-level documents are mutually reachable.
Do **not** change any spec-MOC's `up:`, the spec-MOC template, or scaffold-spec —
the home note is a downward index + curated layer that cross-links with the
roadmap, leaving the existing per-spec upward-navigation contract untouched.

**5d. Epic-count advisory (warn, never block).** If the derived scaffold yields
more than ~10 epics, print a single one-line advisory (e.g. "11 epics — consider
consolidating; >~10 strains navigability") and **still write the home note**. The
cap is advisory only — never a block, never a CI lint.

### 6. Verify and hand off

- Confirm §3 features, the §7 crosswalk, and the roadmap SPEC catalog are
  mutually consistent (same count, same names, same SPEC IDs).
- Confirm every SPEC's scope is detailed enough to seed `/speckit-specify`.
- Confirm the home note exists with both zones (curated epics + a filled
  GENERATED INDEX) and that the roadmap carries the reciprocal link.
- Report the three file paths and the recommended next step.

## Output Contract

Three committed Markdown files:

- `docs/prd-<slug>.md` — lean PRD (template sections, optional appendix dropped).
- `docs/ai/specs/<slug>-technical-roadmap.md` — roadmap whose **SPEC catalog**
  (Progress Tracking table + Specification Sections) is 1:1 with the PRD's
  Features, carrying the reciprocal link to the home note.
- `docs/ai/specs/<slug>-roadmap-MOC.md` — the roadmap-MOC **home note** (a curated
  epics zone scaffolded from the roadmap's phases + a generator-filled GENERATED
  INDEX zone), with `up:` linking back to the technical-roadmap.

Closing report:

```text
## PRD & Roadmap Ready

**PRD:** docs/prd-<slug>.md
**Technical Roadmap:** docs/ai/specs/<slug>-technical-roadmap.md
**Roadmap-MOC home note:** docs/ai/specs/<slug>-roadmap-MOC.md
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

If the user already has a PRD and only needs the roadmap, hand off to
`/speckit-pro:speckit-coach help me create a technical roadmap` — that path is
PRD-in, roadmap-out. This skill is for when the PRD itself does not exist yet.

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
   the dependency graph (scheduler depends on CRUD; UI can mock).
5. Emit `docs/ai/specs/saved-searches-roadmap-MOC.md` (curated epics zone from the
   roadmap's phases + a generator-filled GENERATED INDEX); add the reciprocal link.
6. Report all three paths; recommend `/speckit-pro:speckit-scaffold-spec SPEC-001`.

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
- `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/roadmap-moc-template.md` — the roadmap-MOC home-note template (carries the empty GENERATED INDEX sentinel pair the generator fills).
- `${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/scripts/generate-spec-index.sh` — the generator that fills the home note's GENERATED INDEX zone (invoke with the consumer repo root positionally).
- [`speckit-coach/references/slicing-heuristics.md`](../speckit-coach/references/slicing-heuristics.md) — the single source of truth for SPIDR + INVEST + vertical-slicing and the ~400 reviewable-LOC ceiling (summarized inline above; invoked via `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/scripts/estimate-spec-size.sh`).
- `/speckit-pro:speckit-coach` — decomposition algorithm and SDD methodology depth.
- `/speckit-pro:grill-me` — the downstream per-spec interview that mirrors this skill's one-question-at-a-time machinery.
