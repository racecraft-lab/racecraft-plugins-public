# Quickstart: HRNS-001 Validation Guide

Use this guide to verify the HRNS-001 taxonomy without adding runtime code or a
new validator.

## Prerequisites

- Work from the HRNS-001 feature worktree:
  `racecraft-plugins-public/.worktrees/hrns-001-harness-surface-inventory-gap-taxonomy`
- Do not install or prototype external candidates for HRNS-001.
- Treat docs outside `docs-site/` as docs-only; docs-site validation is not
  required unless `docs-site/**` changes.

## Scenario 1: Placeholder and clarification sweep

```bash
rg -n "\\[NEEDS CLARIFICATION\\]|ACTION REQUIRED|\\[FEATURE\\]|\\[DATE\\]|\\[###-feature-name\\]" \
  specs/hrns-001-harness-surface-inventory-gap-taxonomy \
  docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md
```

Expected result: no matches.

## Scenario 2: Generated spec index is current

```bash
PYTHONPATH=/Users/fredrickgabelmann/.codex/plugins/cache/racecraft-plugins-public/speckit-pro/2.19.2 \
python3 -m speckit_pro_runner <<'JSON'
{
  "schema_version": "1.0",
  "request_id": "hrns-001-generate-spec-index-check-final",
  "helper_id": "generate-spec-index-check",
  "operation": "generate-spec-index-check",
  "mode": "read_only",
  "inputs": {
    "repo_root": "."
  }
}
JSON
```

Expected result: `spec-index: index current`.

## Scenario 3: Markdown diff hygiene

```bash
git diff --check
```

Expected result: exit code 0 with no whitespace errors.

## Scenario 4: AC-1.* crosswalk review

Review `docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md` and confirm:

- AC-1.1 maps to the surface inventory.
- AC-1.2 through AC-1.5 map to the canonical gap register.
- AC-1.6 and AC-1.10 map to the external-candidate matrix.
- AC-1.7 maps to the self-improvement loop register.
- AC-1.8 maps to evidence authority and exclusions.
- AC-1.9 maps to knowledge lifecycle gap/ownership rows.

Expected result: every AC has a named section or row and no unowned deferment.

## Scenario 5: Link and evidence review

Inspect Markdown links in the taxonomy:

```bash
rg -n "\\[[^\\]]+\\]\\([^)]*\\)" docs/ai/specs/harness-engineering-uplift-gap-taxonomy.md
```

Expected result: repository-relative links resolve in the worktree; external
candidate rows cite dated official primary sources or mark unsupported fields
`unknown`.

## Scenario 6: Applicable structural validation

Run Layer 1 when final changed paths warrant repository structural validation
or before PR publication:

```bash
python3 tests/speckit-pro/run-all.py --layer 1
```

Expected result: Layer 1 passes. If HRNS-001 remains strictly docs/process and
the final diff does not touch plugin source, generated payloads, docs-site, or
validation code, record why heavier runtime/docs-site validation is not
applicable in the PR packet.
