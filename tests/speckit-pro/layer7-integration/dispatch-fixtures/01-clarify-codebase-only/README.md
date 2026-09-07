# Fixture 01 — Clarify, codebase-only category

## What this fixture proves

When the orchestrator encounters a `[codebase]`-tagged unresolved item from
a clarify session, the Tier A category-routed dispatch protocol fires
exactly one analyst — `codebase-analyst` — and not the other two.

This is the simplest single-category routing case. If the orchestrator
fans out to all 3 analysts on a single-category tag, this fixture fails
and signals dispatch protocol drift.
