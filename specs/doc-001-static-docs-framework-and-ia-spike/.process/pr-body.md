<!-- speckit-pro-review-packet-source: specs/doc-001-static-docs-framework-and-ia-spike/.process/pr-packets/pr-163.json -->

## Summary

<!-- speckit-pro-editable:summary:start -->
This PR selects Astro with Starlight as the default static docs stack and records the route-level IA handoff for the next docs-site implementation.
<!-- speckit-pro-editable:summary:end -->

Source: DOC-001 specification and framework spike report define the selected stack and IA handoff.

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- Updated the source-backed framework spike to recommend Astro with Starlight for the future docs site.
- Added the Racecraft Systems and Focusengine Astro portfolio context to the framework decision.
- Recorded Starlight community plugin paths for versioning and internal link validation.
- Added the route-level IA skeleton and command handoff that the next implementation PR can use.
- Kept this phase research-only, with no docs-site package, site config, workflow, marketplace, generated payload, or plugin behavior change.
<!-- speckit-pro-editable:what_changed:end -->

Source: framework spike report and DOC-001 planning artifacts define the changed review surface.

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
The docs-site shell can now be scaffolded from an approved Astro-aligned stack and information architecture without mixing framework selection into the implementation PR.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

1. Start with `docs/ai/research/interactive-documentation-framework-spike.md` for the framework recommendation and IA skeleton.
2. Check `specs/doc-001-static-docs-framework-and-ia-spike/` for the requirements, plan, checklist, and task evidence.
3. Confirm the diff stays research-only and does not add package files, lockfiles, site config, CI, marketplace files, generated payloads, or plugin behavior changes.

## How To UAT

No browser UAT applies because this PR does not scaffold a docs site. Review the research artifact, confirm the forbidden implementation surfaces are untouched, and rely on the deterministic repository checks.

## UAT Runbook

Manual browser UAT is not required for this research-only spike. The reviewer acceptance path is document review plus the automated checks listed below.

## Verification

- PR packet validation passed for this rendered title and body.
- The deterministic SpecKit Pro suite was rerun after the main merge and packet refresh.
- The 2026-06-13 decision update passed Layer 1 structural validation, research-report default-stack scan, and `git diff --check`.

Source: packet validation result and local verification output.

## Scope

- Source feature: DOC-001 static docs framework and IA spike.
- Scope: this PR is limited to the interactive documentation PRD/roadmap scaffold, the DOC-001 research report, and SpecKit planning evidence.
- Traceability: the PRD and roadmap point to this spike, the spike report records the framework decision, and the spec artifacts record acceptance and scope evidence.
- Non-goals: no docs-site scaffold, package or lockfile, site config, CI workflow, README migration, marketplace update, generated payload, or plugin behavior change.

## Known Gaps

The next docs-site implementation PR must refresh current Astro, Starlight, selected Starlight plugin, and GitHub Pages documentation before scaffolding. Later validation work still owns accessibility, deep links, docs quality gates, and the decision to add `starlight-links-validator` immediately or defer link validation to DOC-010.
