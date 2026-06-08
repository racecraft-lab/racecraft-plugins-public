# PRD Authoring Protocol

Operational detail for `speckit-prd`. Read this before starting an interview.
The goal of the session is two consistent artifacts — a lean PRD and a technical
roadmap whose SPEC catalog is 1:1 with the PRD's Features.

## Principles

1. **WHAT before HOW.** The PRD describes the problem, the goals, and the
   observable behavior. Implementation detail belongs in the roadmap's per-SPEC
   scope, not the PRD.
2. **Lean by default.** Capture validated decisions; do not re-run discovery in
   the document. Delete any template section that does not reduce ambiguity.
3. **One decision per question.** Each `AskUserQuestion` resolves exactly one
   branch. Recommendation first, with a one-line rationale, then 1–2 plausible
   alternatives. Header ≤ 12 chars.
4. **Features are the unit of decomposition.** Every Feature becomes one SPEC.
   Keep features small enough to fit a single reviewable SPEC.

## Interview Branch Taxonomy

Walk branches in priority order — highest `uncertainty × impact` first. Skip a
branch when the input already answers it; confirm rather than re-ask.

| # | Branch | Question seed | Feeds |
| --- | --- | --- | --- |
| 1 | **Problem** | What user-felt pain does this solve, and why now? | §1 |
| 2 | **Users** | Who experiences it? Which segment matters most for v1? | §1 |
| 3 | **Goals** | What observable outcome means success? | §2.1 |
| 4 | **Non-goals** | What are we deliberately NOT doing in this effort? | §2.2 |
| 5 | **Feature breakdown** | What are the distinct capabilities? Where are the seams? | §3, §4, §7 |
| 6 | **Sequencing** | What must ship first? What can start in parallel (mock data)? | §4, §7 |
| 7 | **Acceptance criteria** | For feature X, what observable result proves it works? | §3 AC-N.* |
| 8 | **Constraints** | Which governance gates / tech limits / NFRs bind this? | §5 |
| 9 | **Open questions** | What is genuinely unresolved and can wait for clarify? | §6 |

### The feature-breakdown branch (most important)

This is where the SPEC catalog is born. Look for natural seams — the same
signals `speckit-coach` uses for roadmap decomposition:

| Boundary signal | How to split |
| --- | --- |
| Different system layers (API vs UI) | One feature/SPEC per layer |
| Different integrations (search, LLM, payments) | One per integration |
| Independently shippable user stories | One per story |
| A component others depend on (shared types, core service) | Foundation feature first |
| A "wire it all together" step | Integration feature last |

For each candidate feature, confirm with the user: does it have its own
acceptance criteria? Could it be reviewed as a single PR? If a feature is too
large for one reviewable SPEC, split it into two features **now** — the PRD is
the cheapest place to split.

## Question Heuristic

Ask the question that, if answered, eliminates the most uncertainty about the
WHAT. Cosmetic questions (naming, wording) are not worth a turn. If you cannot
form a grounded recommendation, say so in the option description (low
confidence) and lean on the alternatives.

## Stop Conditions

- **Preferred:** no critical open questions remain across all branches.
- **User-driven:** the user selects an "End interview / wrap up" option.
- **Soft cap:** ~25–30 questions. At the cap, checkpoint with the user and offer
  to wrap up with current answers; remaining unknowns become Open Questions.

## Decomposition Algorithm (PRD → Roadmap SPEC catalog)

After the PRD draft, expand each Feature into one SPEC. This mirrors
`speckit-coach`'s technical-roadmap algorithm — defer to it for depth.

1. **One SPEC per Feature.** SPEC-00N ⇄ Feature N ⇄ AC-N.*. Keep IDs stable.
2. **Resolve dependencies.** For each SPEC: can it be built and tested with no
   other SPEC complete? If not, which must finish first, and why? Can it start
   on mock data in parallel?
3. **Order the catalog.** Foundations (shared types, core services) first;
   integration SPEC last; prefer sequential over deeply nested dependencies.
4. **Write rich scope.** Each SPEC's scope must be detailed enough to drive
   `/speckit-specify` directly — name technologies, endpoints, data shapes.
   "Backend API" is too vague; "POST /alerts endpoint with schema X, persisted
   to table Y" is right.
5. **Set the reviewability budget.** Each SPEC must fit a human review budget
   (see `speckit-coach`'s reviewability contract). If projected scope exceeds it,
   go back and split the Feature.
6. **Status + graph.** Mark every SPEC `⏳ Pending`, draw the dependency graph,
   and confirm the execution order with the user before finalizing.

## Consistency Check (run before handoff)

The PRD §3 Features, the PRD §7 crosswalk, and the roadmap SPEC catalog must
agree on:

- **Count** — same number of features and SPECs.
- **Names** — same feature names.
- **IDs** — `AC-N.*` ⇄ `SPEC-00N` with no gaps or collisions.

Any drift means the chain will mis-route at `speckit-scaffold-spec`. Fix it
before reporting done.

## File Locations

- PRD: `docs/prd-<slug>.md`
- Roadmap: `docs/ai/specs/<slug>-technical-roadmap.md`

These match what `speckit-scaffold-spec` globs for (`**/*technical*roadmap*`,
`docs/ai/specs/*roadmap*.md`) and the house example layout, so the handoff works
with no extra configuration.
