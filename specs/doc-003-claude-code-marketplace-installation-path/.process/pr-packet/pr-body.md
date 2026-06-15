<!-- speckit-pro-review-packet-source: specs/doc-003-claude-code-marketplace-installation-path/.process/pr-packet/pr-packet.json -->

## Summary

<!-- speckit-pro-editable:summary:start -->
Adds the full DOC-003 Claude Code install route for Racecraft marketplace users, replacing the DOC-002 shell with source-backed install, verification, lifecycle, bounded recovery, and trust guidance.
<!-- speckit-pro-editable:summary:end -->

Source: feature specification defines reviewer-ready PR packet behavior.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Replaced `docs-site/src/content/docs/install/claude-code.md` with the canonical Claude-only path for marketplace add, SpecKit Pro install, `/reload-plugins`, `/plugin`, `/speckit-pro:speckit-status`, and `/speckit-pro:speckit-coach`.
- Added lifecycle and bounded recovery coverage for marketplace refresh, plugin uninstall, marketplace removal, clean reinstall, stale listings, failed visibility, and missing namespaced skills.
- Added source-backed trust inventory for marketplace metadata, plugin manifest, skills, agents, hooks, settings/MCP boundaries, managed marketplace boundaries, and generated Claude payload paths.
- Updated install-relevant wording in `README.md`, `AGENTS.md`, and `speckit-pro/README.md` to prefer current plugin skill language.
- Verification: `validate-gate.sh G7 ...` passed, `pnpm --dir docs-site validate` passed, DOC-003 quickstart checks passed, and no runtime/generated/release paths changed.
<!-- speckit-pro-editable:what_changed:end -->

Source: schema contract defines editable field markers.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
Claude Code users now have one reviewable route from marketplace setup to verified namespaced SpecKit Pro skills. Review first: `docs-site/src/content/docs/install/claude-code.md`; then supporting terminology in `README.md`, `AGENTS.md`, and `speckit-pro/README.md`; then process evidence under `specs/doc-003-claude-code-marketplace-installation-path/`. Non-goals: no Codex procedure, no runtime/payload/version/release change, and DOC-008 keeps full troubleshooting/rollback depth.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Inspect the generated packet JSON for mode, target, title, body path, and validation path.
2. Inspect this body for required reviewer headings, editable markers, and source evidence.

## How To UAT

Run the focused Layer 4 PR body generation test and confirm the packet metadata assertions pass.

## UAT Runbook

Manual UAT is not required for this packet metadata task. The compatibility heading remains present for downstream PR body checks.

## Verification

- Focused packet generation checks passed.
- Packet metadata and rendered body assertions passed.

Source: generated PR packet.

## Scope

- Source feature: recorded in packet metadata.
- Scope: this PR is limited to generated PR packet title and body behavior.
- Traceability: source feature, rendered body, validation, and changed-file scope are recorded in the packet metadata.
- Non-goals: split title generation and multi-PR emission behavior.

## Known Gaps

No known gaps for single-PR packet title metadata. Split packet title generation remains deferred.
