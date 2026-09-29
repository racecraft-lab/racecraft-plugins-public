Priority: major

## Summary

Several dated records state things that are no longer true: roadmap and PRD status, spec plan checklists, runbook job ownership, and eval audit notes that claim current agreement with changed sources. native-runner-progress.md is a 1126-line session log sitting beside the evals README as if it were a contract, and it is cited by the generated test reference.

## Evidence

- **docs-008** (minor): The roadmap describes the staging guard as a robots.txt disallow plus noindex meta, and lists switching robots.txt to allow indexing as a DOC-012 launch step. DOC-014 (row at line 75, robots.txt.ts) already ships an allow-all robots.txt and only the noindex meta remains. The roadmap contradicts itself and the shipped endpoint.
  - `docs/ai/specs/interactive-documentation-technical-roadmap.md:25`, `docs/ai/specs/interactive-documentation-technical-roadmap.md:425`, `docs/ai/specs/interactive-documentation-technical-roadmap.md:455`, `docs/ai/specs/interactive-documentation-technical-roadmap.md:75`, `docs-site/src/pages/robots.txt.ts:73-98`
- **docs-014** (minor): Six completed workflow and design-concept records sit at the docs/ai/specs root in the pre-.process layout, mixed with live roadmaps, MOCs and decision docs. They reference deleted .sh scripts (doc-drift evidence) and are candidates for the Tier-2 .process relocation the scaffold skill describes.
  - `docs/ai/specs/SPEC-001-workflow.md:1`, `docs/ai/specs/SPEC-004-workflow.md:1`, `docs/ai/specs/SPEC-006a-workflow.md:1`, `docs/ai/specs/PRSG-001-workflow.md:1`, `docs/ai/specs/PRSG-001-design-concept.md:1`, `docs/ai/specs/SPEC-006a-design-concept.md:1`
- **artifact-gallery-010** (minor): ART-018 to ART-021 sit after the Decomposition Principles and Environment sections, so they fall outside the Specification Sections H2. The overview says 13 of 21 specs are in tiers and the table of contents lists four of the ten H2 sections. ART-013 still says it requires everything.
  - `docs/ai/specs/html-artifacts-technical-roadmap.md:35-37`, `docs/ai/specs/html-artifacts-technical-roadmap.md:1248-1289`, `docs/ai/specs/html-artifacts-technical-roadmap.md:26-31`
- **artifact-gallery-011** (minor): The PRD header says 'Active, not yet implemented' with last updated 2026-07-28. The body mentions ART-021 added 2026-09-25, and the roadmap records 15 of 21 specs complete or archived.
  - `docs/prd-html-artifacts.md:3-6`, `docs/prd-html-artifacts.md:279`, `docs/ai/specs/html-artifacts-technical-roadmap.md:125-145`
- **runner-core-010** (minor): The spike cites files that no longer exist (check-prerequisites.sh, layer5 validate-tool-scoping.sh) and line ranges past the end of speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml (7 lines, cited 9-16). The governance research cites scripts/generate-spec-index.sh, also gone. Doc-drift counts 16 drifted anchors in the spike.
  - `docs/ai/research/tool-agnostic-capability-discovery-spike.md:73`, `docs/ai/research/tool-agnostic-capability-discovery-spike.md:77`, `docs/ai/research/tool-agnostic-capability-discovery-spike.md:194`, `docs/ai/research/tool-agnostic-capability-discovery-spike.md:75`, `docs/ai/research/spec-pr-size-governance-research.md:165`
- **coach-and-formal-004** (minor): The trace-layer evidence says native TLC trace qualification passed 26/26. The acceptance table (A4) and the delivery row for PR 563 both record TLC 27/27 on the same hosted run.
  - `specs/formal-001-selective-formal-methods/acceptance.md:140`, `specs/formal-001-selective-formal-methods/acceptance.md:14`, `specs/formal-001-selective-formal-methods/acceptance.md:30`
- **coach-and-formal-005** (minor): plan.md still has four unchecked items (T5, T6, T6, and the full-harness review) for work that tasks.md marks complete (T5, T5a, T6, T6a, T6b) and acceptance.md A7 records as finished.
  - `specs/formal-001-selective-formal-methods/plan.md:54`, `specs/formal-001-selective-formal-methods/plan.md:56`, `specs/formal-001-selective-formal-methods/plan.md:85`, `specs/formal-001-selective-formal-methods/plan.md:117`, `specs/formal-001-selective-formal-methods/tasks.md:26`
- **release-tooling-004** (major): The runbook says pr-checks.yml exposes validate-pr-title. That job lives in pr-metadata.yml, which also owns validate-release-note; the runbook lists neither workflow split.
  - `docs/ai/specs/cicd-release-pipeline-verification.md:8`
- **native-eval-harness-007** (major): A 1126-line append-only session log sits beside the README as a contract doc. It holds contradictory point-in-time claims (a section titled 'Hosted suite gate: current red state', 'pending' adoptions, 8,436/8,436 totals) and orchestration-agent paths, while the README says it does not hard-code totals. It is also cited by the generated docs-site test reference as a source.
  - `tests/speckit-pro/evals/native-runner-progress.md:1`, `tests/speckit-pro/evals/native-runner-progress.md:853`, `tests/speckit-pro/evals/native-runner-progress.md:49`
- **native-eval-harness-008** (minor): README sends readers to the audit directory for 'current coverage and gaps', but those reports are frozen snapshots: the inventory cites a 102-entry manifest (now about 140 scripts) and trigger-audit proposes four bootstrap tests in test-native-agent-bootstrap-contracts.py that do not exist, though the same ids are in trigger-inventory.json.
  - `tests/speckit-pro/evals/README.md:373`, `tests/speckit-pro/evals/audit/execution-surface-inventory.md:6-15`, `tests/speckit-pro/evals/audit/trigger-audit.md:88-93`
- **native-eval-harness-009** (minor): README lists 'supported checks and parameters' but omits native_synthesis_mechanism, native_subagent_dispatch, native_plan_repair_context, native_verification_pointer, native_runner_result and subagent_returns_before_parent_file_change, and the case fields git_fixture, required_tools, pairing and git_metadata_access. Catalog.json uses all of these except the last check type.
  - `tests/speckit-pro/evals/README.md:103-135`, `tests/speckit-pro/lib/native_eval_catalog.py:41-46`, `tests/speckit-pro/lib/native_eval_catalog.py:467-475`
- **brokers-and-verification-013** (minor): The audit record cites test-execution-control.py:619-623 for the custom loader and says it loads 45 families. The loader is now at lines 3142-3154 and lists 20 classes on main. Its drift is reported by --doc-drift.
  - `tests/speckit-pro/evals/audit/unit-execution-contract-audit.md:28`, `tests/speckit-pro/unit/test-execution-control.py:3142-3154`
- **coach-and-formal-007** (minor): The audit says all current source hashes match its frozen inventory and source_drift_at_review is false. Eight of the eleven listed test scripts (including test-formal-checkers, -setup and -traces) no longer hash to their recorded frozen_sha256, and the counted-unit totals are stale with them.
  - `tests/speckit-pro/evals/audit/unit-quality-formal-audit.md:10`, `tests/speckit-pro/evals/audit/unit-quality-formal-audit.json:9`

## Proposed fix

- docs-008: Update lines 25, 425 and 455 to say robots.txt already allows crawling and DOC-012 only removes the noindex meta.
- docs-014: Relocate them under docs/ai/specs/.process/ (or archive them) so the root holds only live planning documents.
- artifact-gallery-010: Move ART-018 to ART-021 into Specification Sections and refresh the overview, tier table and table of contents.
- artifact-gallery-011: Update the PRD status and last-updated date, or mark the PRD as historical.
- runner-core-010: Add a dated-record banner stating the citations describe the tree at spike time, or re-point them to current paths.
- coach-and-formal-004: Reconcile the count to the hosted run, or label 26/26 as the earlier layer-5 figure.
- coach-and-formal-005: Check the plan items or drop the duplicated checklist from plan.md so tasks.md is the only status record.
- release-tooling-004: Name pr-metadata.yml as the owner of validate-pr-title and validate-release-note in baseline check 2.
- native-eval-harness-007: Move dated checkpoints to an archive or delete them, and keep only durable, current statements (or none) in evals/.
- native-eval-harness-008: Label the audit directory as dated history in the README, and drop or resolve the proposed-test ids that never landed.
- native-eval-harness-009: Document each check type and optional case field, or generate the table from CHECK_TYPES and the validator field sets.
- brokers-and-verification-013: Refresh the citation and the family count, or cite the loader by symbol instead of line.
- coach-and-formal-007: Mark the record as a dated snapshot, or refresh hashes and counts. Do not let the wording claim current-state agreement.

## Acceptance

- [ ] Each record is updated, or marked as a dated snapshot so it no longer claims current state.
- [ ] native-runner-progress.md is archived or reduced to durable statements, and the generated reference no longer cites it as a source.
- [ ] The evals README lists every supported check type and case field, or generates the table from the code.
- [ ] Workflow and spec-index MOC files stay consistent (spec-index check, if touched).

## Related

- None.

Found by the 2026-09 coherence audit.
