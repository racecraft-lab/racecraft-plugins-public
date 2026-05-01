# Fixture E2E-02 — Extended autopilot pipeline (G1–G7)

## What this fixture proves

Where fixture E2E-01 covers G0–G3 (the "easy half"), this fixture
exercises the **entire phase-agent set** in the canonical SpecKit
order (G1 → G7):

  Specify → Clarify → Plan → Checklist → Tasks → Analyze → Implement

That order maps to:

- `phase-executor` (Specify, Plan, Tasks — 3 of the 7 phases)
- `clarify-executor` (Clarify)
- `checklist-executor` (Checklist)
- `analyze-executor` (Analyze)
- `implement-executor` (Implement)

The fixture uses **manual dispatch** (the prompt explicitly tells the
orchestrator which agent to dispatch for each phase) rather than
invoking `/speckit-pro:autopilot` end-to-end. This avoids the autopilot
skill's Step 0 preflight, which expects a workflow file and writes
real artifacts. The dispatch-graph properties under test are
identical either way.

Order constraints assert the canonical pipeline order, including
the easy-to-mistake **Analyze before Implement** boundary (G6 → G7).

## Cost

`--live` mode dispatches all five phase agents in sequence. Each
subagent is asked for a brief, non-binding summary; the prompt
explicitly instructs **"Do NOT write artifacts to disk."** Real LLM
behavior may still produce side effects (e.g., implement-executor
sometimes writes a TDD test file even when asked not to — see the
"Live-mode side effects" section in the parent L7 README). The
`--max-budget-usd` cost guard caps total spend regardless.

Default budget cap: **$10.00** (`E2E_FIXTURE_BUDGET_USD`). This is
the most expensive fixture in the suite — run sparingly. The
captured transcript on disk shows the actual cost was ~$1.27 in the
canonical run, so the $10 default leaves substantial headroom for
the LLM to take a longer path on rerun.

## Required setup

The fixture is self-contained. The minimal spec (`sample-spec.md`) is
committed alongside this README; `prompt.txt` references it by an
in-repo path.
