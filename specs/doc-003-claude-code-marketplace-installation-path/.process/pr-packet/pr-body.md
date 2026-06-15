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

1. Review `docs-site/src/content/docs/install/claude-code.md` first for the full Claude Code marketplace install path.
2. Review `README.md`, `AGENTS.md`, and `speckit-pro/README.md` for install-relevant terminology alignment.
3. Review DOC-003 process evidence under `specs/doc-003-claude-code-marketplace-installation-path/` for traceability and validation.

## How To UAT

Read the Claude Code install route as a first-time Racecraft marketplace user and confirm the documented flow is coherent from marketplace setup through verified namespaced SpecKit Pro skills.

## UAT Runbook

Manual UAT is documentation review only. Confirm the page clearly covers marketplace add, SpecKit Pro install, `/reload-plugins`, `/plugin` verification, namespaced skill checks, update, uninstall, marketplace removal, clean reinstall, bounded recovery, and trust boundaries without adding Codex procedure.

## Verification

- `validate-gate.sh G7` passed with all 39 tasks complete.
- `pnpm --dir docs-site validate` passed.
- DOC-003 quickstart checks passed for planning artifacts, route content, lifecycle coverage, Codex boundary, trust inventory, terminology, and runtime-surface scope.
- Scope review confirmed no `dist/`, runtime, generated payload, release automation, or GitHub workflow changes.

Source: quickstart and workflow validation evidence.

## Scope

- Source feature: DOC-003 Claude Code marketplace installation path.
- Scope: Claude Code install docs route, install-relevant README and AGENTS wording, and SDD/process artifacts.
- Traceability: DOC-003 spec, tasks, quickstart, workflow evidence, and generated packet metadata record the review scope and validation.
- Non-goals: no Codex install procedure, plugin runtime behavior, generated payload, manifest, hook, agent, version, release automation, or GitHub workflow change.

## Known Gaps

No known DOC-003 implementation gaps. Full troubleshooting, rollback, incident response, policy design, network debugging, permission repair, and deeper cache forensics remain deferred to DOC-008.
