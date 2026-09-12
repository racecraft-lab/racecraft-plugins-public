# Issue #571 Acceptance Fixture

This is a disposable evidence fixture for desktop artifact-review delivery.
**DO NOT MERGE.** It contains no production change and no claim of completed
manual acceptance.

## Initial checkpoint

- Planning record: `spec.md`, `plan.md`, and `tasks.md` are seeded test
  preconditions, not evidence that the full SpecKit phases ran.
- Generated pages: four shipped draft-PR templates are filled and fingerprinted
  in the workflow handoff.
- Planned gap: `architecture-viewer` has no shipped template in the active
  gallery, so no replacement HTML page is created.
- Browser observation: pending until the parent inspects each page through the
  permitted local preview route and supplies the actual rendered title, visible
  body text, locator, and timestamp.
- Human approval: pending; no approval is implied by generation.
- Manual UAT: pending; no UAT result is implied by browser rendering.

The parent may update this report with observed evidence after the draft PR
identity bookkeeping commit. The workflow's `Artifact Review Handoff` section
remains the sole machine-readable handoff record.

## Generation receipt

The fixture author ran a deterministic byte-level check over all four selected
pages. It passed the following checks for each page: output bytes differ from
the shipped template; every declared `FILL` marker appears once and in order;
every fill region differs from its shipped source region; and no rendered page
contains an element with `class="sample-notice"`, `class="notice"`, or
`class="note"`. A negative check confirmed that the untouched shipped
implementation-plan template still contains its sample banner and is rejected;
another confirmed that no architecture-viewer output exists.

The real resolver invocation was:

```text
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner <<'JSON'
{"schema_version":"1.0","request_id":"issue-571-resolve","helper_id":"resolve-autopilot-stage","operation":"resolve-autopilot-stage","mode":"read_only","inputs":{"workflow_file":"specs/desktop-review-acceptance/workflow.md","autopilot_args":["specs/desktop-review-acceptance/workflow.md"]}}
JSON
```

The request was supplied on stdin and not written to the feature directory. It
returned exit code 0 with `planning_complete: true`,
`stage: plan`, `artifact_review.status: pending`,
`artifact_review.resume_action: preview`, `generated: 4`,
`verified: 0`, and `generation_gaps: ["architecture-viewer"]`.

A second negative check copied the feature to a temporary fixture, removed the
required `implementation-plan.html`, and reran `review_handoff` against that
copy. It passed by classifying that required page as pending, setting
`reuse_artifacts: false`, and changing the resume action to `generate`; this is
distinct from the intentional `architecture-viewer` gap.

## Final acceptance matrix

This matrix covers the eleven issue-571 checks. `PASS (contract)` means a
deterministic repository or runner check; `PASS (desktop)` means the parent
actually inspected the rendered page in the permitted browser surface.

| Criterion | Result | Evidence |
| --- | --- | --- |
| C1. Worktree is pinned to the approved base | PASS (contract) | Canonical root is `/Users/fredrickgabelmann/Documents/Business_Documents/RSE_Documents/Projects/racecraft-plugins-public/.worktrees/issue-571-desktop-acceptance`; branch `codex/issue-571-desktop-acceptance`, base `42f4afe5bd2a319f81ea4b28799ec13bfa8e6107`. |
| C2. Runner source is complete and hash-stable | PASS (contract) | Pinned runner manifest covers all 42 files; analyst reports all hashes match. Key sources: `artifact_review.py` `22f81e489ae5687625ab74289e1bfbd8ad1d83d7e643adda27f7c4789adcdbed`, `read_only.py` `c9fa0e19d37b63d5f56ddda28b9b8b89956b2460bc0922b807c52f3c739fbea7`. |
| C3. The shared artifact-review contract is the source of truth | PASS (contract) | Contract reference hash `4bd305657bd9cf84aeac86f62c34e354c8053cf45948e0ea131455b4b7bcaa4`; workflow contains one handoff section and no state-file mirror. |
| C4. Manifest routing selects the intended pages | PASS (contract) | Manifest hash `af9a4944ff96ab0dcaf99909f5298edd6c8ea25c627ce97029084c17bb83d06a`; two always-on pages plus `competing_approaches` and `brownfield_change` pages selected. |
| C5. Four pages are real filled shipped templates | PASS (contract) | `implementation-plan`, `spec-explainer`, `code-approaches`, and `module-map` are present, differ from their shipped templates, retain ordered markers, and carry current page hashes in `workflow.md`. |
| C6. Generation provenance is byte-accurate | PASS (contract) | `spec.md` `b0369e0b512ae12e4aad0a8c62de7f7de0bfe9845268be6595dfa8b0d427db70`; `plan.md` `a54deacb21f818cafc70356351c1223a8e9cdeb89fa609fc6cc398d43a80dad6`; `tasks.md` `8bd2ff1cc135f4576822cf8e7a7128b4587fcc71528d4bc4782e8cf15f4d8de0`; template and output hashes are retained in the handoff. |
| C7. Fail-closed generation guards work | PASS (contract) | Checks rejected an untouched sample banner and a missing required `implementation-plan.html` (resume changed to `generate`); no architecture-viewer output was fabricated. |
| C8. Focused automated evidence is complete | PASS (contract) | Analyst ran the focused five-test set: 708/708 assertions passed (41 + 44 + 23 + 257 + 343). No fresh source edits or regeneration were needed after that audit. |
| C9. Draft PR identity is canonical and corroborated | PASS (contract) | PR [#577](https://github.com/racecraft-lab/racecraft-plugins-public/pull/577) is the single verified open draft for the head branch. Identity commit `468710f9`; resolver corroboration returned `match`. |
| C10. All four pages render with expected visible content | PASS (desktop) | Parent visually reviewed screenshots and visible text in browser2/Codex session `01a0963e-207b-70c1-b138-51853cee8573`; refs and timestamps are recorded in the workflow handoff. Screenshots remain in the parent task transcript, not public image files. |
| C11. Resume/closeout boundaries remain honest | PASS (contract) / PENDING (approval, UAT) | Complete checkpoint commit `cab5884f`; resolver returns `stage=implement`, `artifact_review=verified`, `resume_action=none`, `generated=4`, `verified=4`. Human approval and manual UAT have not occurred and remain pending. |

## Complete desktop observations

The four observations were made against the permitted loopback artifact-only
route, with one retained review tab per page and no alternate task destination:

1. `implementation-plan.html` — title `Implementation Plan — Desktop Artifact Review Acceptance`; visible body “Four rendered pages share one durable handoff so reviewers can resume artifact delivery without mistaking planning for UAT.” Route `http://127.0.0.1:8765/implementation-plan.html`; reference `codex-task:01a0963e-207b-70c1-b138-51853cee8573/observation/571-plan-1`; observed `2026-09-12T17:03:19.263Z`.
2. `spec-explainer.html` — title `Spec Explainer — Desktop Artifact Review Acceptance`; visible body “A disposable evidence fixture that separates generated gallery pages from rendered observation, approval, and UAT.” Route `http://127.0.0.1:8765/spec-explainer.html`; reference `codex-task:01a0963e-207b-70c1-b138-51853cee8573/observation/571-spec-1`; observed `2026-09-12T17:03:31.998Z`.
3. `code-approaches.html` — title `Code Approaches — Desktop Artifact Review Acceptance`; visible body “Two ways to carry artifact evidence: a report-only snapshot or one durable workflow handoff that the resolver can resume.” Route `http://127.0.0.1:8765/code-approaches.html`; reference `codex-task:01a0963e-207b-70c1-b138-51853cee8573/observation/571-approaches-1`; observed `2026-09-12T17:05:23.661Z`.
4. `module-map.html` — title `Module Map — Desktop Artifact Review Acceptance`; visible body “The existing resolver and artifact-review module meet at one workflow handoff; this fixture reads those boundaries without modifying production code.” Route `http://127.0.0.1:8765/module-map.html`; reference `codex-task:01a0963e-207b-70c1-b138-51853cee8573/observation/571-module-1`; observed `2026-09-12T17:05:35.470Z`.

The parent task was the current destination (`browser2`, Codex session
`01a0963e-207b-70c1-b138-51853cee8573`). The loopback server and read-only
resolver were deliberately bound to the isolated canonical worktree above;
no other task destination was opened. The checkpoint chain is
`144cf857` → `26e174e9` → `468710f9` → `77b5f261` → `cab5884f`, preserving the
initial fixture, negative receipt, PR identity, partial checkpoint, and final
checkpoint respectively.

The `architecture-viewer` entry remains a planned generation gap because the
active manifest has no shipped template. Human approval and manual UAT remain
pending; this report does not imply either.

The post-checkpoint analyst audit found all 13 expected hashes current (three
planning inputs, manifest, four templates, and four generated pages, with the
planned architecture-viewer output absent). GitHub lists exactly one open draft
PR for the head. Source-pinned CI is green separately; the fixture PR's latest
CodeQL/container-arm64 jobs were still running at report time, while the
completed jobs were success or skipped. That current CI run is not relabeled as
complete here.
