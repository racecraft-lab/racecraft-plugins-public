# G56R-005 Manual UAT Runbook

**Result:** PASS after one artifact-generation finding was remediated  
**Date:** 2026-08-22  
**Baseline head:** `231270a16d02ff9cbeca350be27ede94b4f2970d`  
**Remediation commit:** `3d16d4aeb`
**Worktree:** `.worktrees/g56r-005-model-availability-fallback-recovery`

## Scope and setup

This UAT exercises the deterministic G56R-005 simulation and its four draft
review artifacts. It deliberately does not call a live model or service and
does not write to a real Codex home. Recovery scenarios use a temporary fake
home, as required by the feature specification.

Serve `specs/g56r-005-model-availability-fallback-recovery/artifacts/` from a
temporary localhost HTTP server, then open each page in the in-app browser.
Run the behavioral scenarios directly against
`tests/speckit-pro/layer6-efficiency/lib/codex_route_fallback.py` with
`PYTHONDONTWRITEBYTECODE=1`.

## Browser acceptance

1. Open `spec-explainer.html`, `implementation-plan.html`,
   `code-approaches.html`, and `module-map.html` at desktop width.
   - Expected: each page has the G56R-005 document title and H1, renders without
     horizontal overflow, and exposes the theme control.
   - Result: PASS.
2. Toggle the theme and open a collapsed disclosure.
   - Expected: the theme changes, `aria-pressed` follows the selected theme,
     and the disclosure opens.
   - Result: PASS.
3. Exercise Copy as Prompt and Copy as Markdown where offered.
   - Expected: each control reports a successful copy without exposing the
     fallback textarea.
   - Result: PASS.
4. Repeat all four pages at a 390 by 844 mobile viewport.
   - Expected: the title, H1, and controls remain visible and the document has
     no horizontal overflow.
   - Result: PASS.
5. Inspect the browser console after the desktop, interaction, and mobile runs.
   - Expected: no errors or warnings.
   - Result: PASS.

## Behavioral acceptance

1. Resolve an absent preferred model with an available fallback.
   - Expected: the preferred and fallback routes are attempted in order; the
     reason is `model_absent`; the fallback is selected with terminal outcome
     `qualified_route`.
   - Result: PASS.
2. Resolve a strict incompatible override.
   - Expected: no route is attempted and the terminal outcome is
     `strict_override_rejected`.
   - Result: PASS.
3. Compare approved service reroute attribution with an adjacent unapproved
   reroute.
   - Expected: both retain the plugin reason; only the approved reroute is
     scoring-eligible.
   - Result: PASS.
4. Inject a failure after the first fake-home write.
   - Expected: rollback reports `restored`, no writes remain, and the original
     file content is byte-identical.
   - Result: PASS.
5. Exercise retry, time, fan-out, context, cancellation, escalation,
   human-in-the-loop, and recursive/no-safe-route budget cases.
   - Expected: each case terminates with its documented bounded outcome and no
     recursive execution.
   - Result: PASS.
6. Replay the canonical scenarios three times.
   - Expected: the reports are byte-identical and contain no host-worktree path.
   - Result: PASS.

## Finding and remediation

### UAT-001: Generated artifacts used an unsafe dynamic document-title workaround

The four pages retained the template's static `NIMBUS-101` title and appended a
feature-specific `document.title` assignment inside a script. That caused stale
no-JavaScript metadata and violated the gallery contract that forbids inserting
repository-derived values into script bodies.

Remediation:

- Added a required `document-title` fill region to all four draft-stage
  templates.
- Added the slot to the fill-region contract test so templates cannot regress.
- Updated both Claude and Codex artifact-author instructions to require one
  static, HTML-escaped title and forbid the dynamic workaround.
- Regenerated shipped payloads and replaced all four G56R-005 artifact titles
  with static values.

Retest result: PASS. Every page now has exactly one static G56R-005 title, zero
scripts containing `document.title`, the correct visible H1, and no horizontal
overflow at desktop or mobile width.

## Final verification

- Manual browser acceptance: PASS.
- Deterministic behavioral acceptance: PASS.
- Static-title contract: 90/90 PASS.
- Artifact gallery validation: 587/587 PASS.
- Full repository suite: 7663/7663 PASS (L1 1469, L4 6002, L5 192).
- Live model/service reroute smoke: intentionally not run; the specification
  makes no live availability claim.
