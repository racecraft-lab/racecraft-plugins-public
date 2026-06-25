# Quickstart: Runtime Inventory and Constraints

## Purpose

Use this guide during implementation to verify that the XPLAT-001 report covers
the planned scan universe and preserves the accepted static-only boundaries.

## Preflight

1. Confirm the worktree:

   ```bash
   git rev-parse --abbrev-ref HEAD
   git status --short
   ```

2. Re-read source truth:

   ```bash
   sed -n '1,220p' docs/ai/specs/.process/XPLAT-001-design-concept.md
   sed -n '1,260p' specs/xplat-001-runtime-inventory-constraints/spec.md
   sed -n '1,260p' docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md
   ```

## Report Target

Create one durable report:

```text
docs/ai/research/cross-platform-runtime-inventory.md
```

The report must include:

- Scan commands and scope.
- Exclusion rationale.
- Summary counts.
- Inventory table.
- Runtime rubric.
- Supply-chain rubric.
- Handoff notes for XPLAT-002 through XPLAT-007.

## Inventory Checks

For every inventory row:

- Fill `classification`.
- Fill `active_runtime_status`.
- Fill `runtime_relevance`.
- Fill `owner_bucket`.
- Fill `follow_up_spec`.
- Cite evidence.
- Cite `invocation_trace` for every `proven-active-runtime` row.
- Document the evidence gap for every `unproven-active-runtime` row.

Do not mark public docs, generated payloads, tests, fixtures, archive reports, or
repository-only tooling as active runtime without static invocation evidence.

## Static Verification

Run the checks required by the plan:

```bash
speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"
git diff --check
```

Also rerun the scan commands recorded in the report and confirm that every
result is represented or explicitly excluded.

## Out-of-Scope Guard

Stop and revise the artifact if XPLAT-001 starts to:

- Score, rank, or choose runtime candidates.
- Score, rank, or choose supply-chain controls.
- Port helpers.
- Change active Claude or Codex invocation paths.
- Rebuild generated payloads.
- Claim native Windows support in public docs.
