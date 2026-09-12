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
| C1. Missing files and unmodified samples fail generation validation | PASS (contract) | The byte-level receipt rejects an untouched sample template and a temporary fixture with required `implementation-plan.html` removed; the latter becomes `pending` with `resume_action=generate`. |
| C2. Queued or generic open success is not verification | PASS (contract) | `test-artifact-review.py:123-129` covers the distinction; HTTP 200, file existence, tab URL, generic open success, and queued delivery are not rendered evidence. |
| C3. Wrong, blank, error, or title-only pages remain unverified | PASS (contract) | `test-artifact-review.py:131-141` keeps these states pending with a blocker; verification requires rendered title and feature-specific visible body text. |
| C4. Partial delivery is recorded per page | PASS (contract) | Workflow checkpoint `77b5f261` recorded 2 verified and 2 pending pages after the first two observations; no unrelated pages were promoted. |
| C5. Policy denial is retained without workaround | PASS (contract) | `test-artifact-review.py:143-150,177-180` and `artifact-review.md` preserve denial semantics. This run has no live browser-denial claim: the initial socket permission was newly user-authorized through normal escalation. |
| C6. Task/worktree mismatch cannot redirect delivery | PASS (contract) | Canonical path and current-task binding checks are covered by the referenced contract lines 66-77. The parent task stayed the destination while the server/resolver used the isolated canonical worktree; no other task was opened. |
| C7. Headless mode reports unavailable evidence and supplies manual links | PASS (contract) | `artifact-review.md:91-100,132-138` and `test-artifact-review.py:143-150` define deterministic unavailable/manual-link behavior; this is not a live headless-run claim. |
| C8. Interrupted delivery reuses valid pages without duplicate PR or regeneration | PASS (contract) | After pushed `77b5f261`, the resolver returned `plan`, `preview`, `reuse_artifacts=true`, PR `match`, exactly one open draft PR #577, unchanged page/input hashes; final checkpoint is `cab5884f`. |
| C9. Real macOS desktop renders all four pages with visible expected content | PASS (desktop) | Parent visually reviewed all four retained browser2 captures and visible text; exact routes, references, timestamps, and observed bodies are listed below. |
| C10. Missing template is a separate generation gap | PASS (contract) | `architecture-viewer` remains `generation=gap` because its planned manifest row has no shipped template; resolver reports it separately and no replacement page exists. |
| C11. Preview verification is not approval or UAT | PASS (contract) / PENDING (approval, UAT) | All four previews are verified rendered observations, but human approval and manual UAT have not occurred and remain pending. |

## Fixture provenance and scope

- Approved base: `42f4afe5bd2a319f81ea4b28799ec13bfa8e6107`; branch
  `codex/issue-571-desktop-acceptance`.
- The pinned runner manifest covers all 42 files and the analyst reports all
  hashes matching. Key hashes: `artifact_review.py`
  `22f81e489ae5687625ab74289e1bfbd8ad1d83d7e643adda27f7c4789adcdbed`,
  `read_only.py`
  `c9fa0e19d37b63d5f56ddda28b9b8b89956b2460bc0922b807c52f3c739fbea7`,
  `artifact-review.md`
  `4bd305657bd9cf84aeac86f62c34e354c8053cf45948e0ea131455b4b7bcaa4b`, and
  gallery manifest
  `af9a4944ff96ab0dcaf99909f5298edd6c8ea25c627ce97029084c17bb83d06a`.
- Focused analyst evidence is 708/708 assertions (41 + 44 + 23 + 257 + 343).
- Checkpoint chain: `144cf857` → `26e174e9` → `468710f9` → `77b5f261` →
  `cab5884f` → `2387247e`.
- The screenshots remain in the parent task transcript, not public image
  files. The report retains the observed visible text and transcript refs.

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

The post-checkpoint analyst audit passed 13/13 checks: 12 expected hash matches
(three planning inputs, manifest, four templates, and four generated pages) plus
the absent planned architecture-viewer template/output check. GitHub lists exactly one open draft
PR for the head. Source-pinned CI is green separately; the fixture PR's latest
CodeQL/container-arm64 jobs were still running at report time, while the
completed jobs were success or skipped. That current CI run is not relabeled as
complete here.
