---
name: speckit-prd
description: "Use this skill to collaboratively turn a raw product or technical idea into two artifacts — a lean PRD and a technical roadmap with a SPEC catalog — ready for /speckit-pro:speckit-scaffold-spec and /speckit-pro:speckit-autopilot. Triggers on: write a PRD, create a product requirements document, draft a PRD and roadmap, shape this idea into a PRD, turn this brief into a PRD, plan a product, decompose an idea into a SPEC catalog, what features should this have, before I write specs. Runs a one-question-at-a-time interview with a recommended answer on every question, then writes docs/prd-NAME.md and docs/ai/specs/NAME-technical-roadmap.md. This is the front door of the chain: PRD then roadmap then scaffold-spec then autopilot. NOT per-spec scoping for a single spec already in the roadmap (use grill-me), NOT preparing a worktree from an existing roadmap entry (use speckit-scaffold-spec), NOT SDD methodology coaching (use speckit-coach). Requires an interactive session."
argument-hint: "a product/technical idea, a brief, or a file path"
user-invocable: true
license: MIT
compatibility: "Requires Claude Code with AskUserQuestion tool support. Codex variant in codex-skills/speckit-prd/ uses a free-text Q&A loop instead."
---

# SpecKit PRD — Collaborative PRD & Technical Roadmap Authoring

## Codex Skill-Selection Guard

If this file is loaded in Codex, the runtime selected the Claude Code
variant from `skills/` instead of the Codex variant from `codex-skills/`.
Do not follow the Claude-oriented instructions below in Codex. Immediately
read and follow `../../codex-skills/speckit-prd/SKILL.md` from this plugin
root, treat that document as the active skill, and report that the fallback
guard was triggered.

You are a **collaborative product partner**. Your job is to turn a raw idea
into two durable artifacts by thinking *with* the user — never *for* them:

1. A **lean PRD** (`docs/prd-<slug>.md`) — the WHAT and WHY.
2. A **technical roadmap with a SPEC catalog** (`docs/ai/specs/<slug>-technical-roadmap.md`) —
   the ordered set of specs the PRD decomposes into.

This is the **front door** of the speckit-pro chain. Everything downstream
reads these two files:

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

For each SPEC: scope (detailed enough to drive `/speckit-specify`), depends-on /
enables, priority, status (`⏳ Pending`), reviewability budget, and key files.
Set `**Source PRD:**` to `docs/prd-<slug>.md`. **Review the dependency graph
with the user** (one more `AskUserQuestion`) before finalizing — execution order
is a consequential decision.

### 5. Verify and hand off

- Confirm §3 features, the §7 crosswalk, and the roadmap SPEC catalog are
  mutually consistent (same count, same names, same SPEC IDs).
- Confirm every SPEC's scope is detailed enough to seed `/speckit-specify`.
- Report the two file paths and the recommended next step.

## Output Contract

Two committed Markdown files:

- `docs/prd-<slug>.md` — lean PRD (template sections, optional appendix dropped).
- `docs/ai/specs/<slug>-technical-roadmap.md` — roadmap whose **SPEC catalog**
  (Progress Tracking table + Specification Sections) is 1:1 with the PRD's
  Features.

Closing report:

```text
## PRD & Roadmap Ready

**PRD:** docs/prd-<slug>.md
**Technical Roadmap:** docs/ai/specs/<slug>-technical-roadmap.md
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
5. Report both paths; recommend `/speckit-pro:speckit-scaffold-spec SPEC-001`.

### Example 2 — brief file as input

User: *"Turn notes/discovery-call.md into a PRD."*

Read the file, treat it as discovery input, interview only on the gaps it leaves
open, then produce the same two artifacts.

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
- **Features and SPEC catalog drift apart.** Re-run step 5. The §3 features, the
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
- `/speckit-pro:speckit-coach` — decomposition algorithm and SDD methodology depth.
- `/speckit-pro:grill-me` — the downstream per-spec interview that mirrors this skill's one-question-at-a-time machinery.
