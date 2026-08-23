# UAT Runbook: ART-017

| Field | Value |
|-------|-------|
| Spec | ART-017 — Arm The Accidentally-Advisory State Bookkeeping Checks |
| Branch | `art-017-state-bookkeeping-checks` |
| PR | [#490](https://github.com/racecraft-lab/racecraft-plugins-public/pull/490) |
| Executed | 2026-08-22 |
| Result | PASS — 9/9 acceptance scenarios |

## Env Setup

Run from the ART-017 worktree with Python 3.11 or newer. The product surface is
the shipped `validate-autopilot-phase-coverage.py` command. Temporary
workflow/state pairs may be discarded after each case; no repository file is
part of a negative fixture.

The exact scoped invocation is:

```text
python3 speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py \
  --workflow <temporary-workflow> \
  --state <temporary-state> \
  --rule status-evidence
```

## Per-Story Acceptance Tests

1. Start with a clean workflow/state pair, set two plan entries to
   `in_progress`, and run the scoped command. It exits 1, reports only
   `in_progress_errors`, and leaves the other two ART-017 lists empty. PASS.
2. Start clean, append a copy of one plan entry, and run the command. It exits
   1, reports only `duplicate_state_steps`, and leaves the other two lists
   empty. PASS.
3. Start clean, swap the first two canonical plan entries, and run the command.
   It exits 1, reports only `state_order_errors`, and leaves the other two lists
   empty. PASS.
4. Run the unchanged clean pair. It exits 0, reports `status: pass`, preserves
   the complete JSON report shape, and leaves all three ART-017 lists empty.
   PASS.
5. Inspect `RULE_PROBLEM_KEYS["status-evidence"]` and `PROBLEM_KEY_INTENT`.
   Exactly the three ART-017 keys are newly selected, every verdict is `gated`,
   and every reason describes the current run invariant it protects. PASS.
6. Reduce the clean state to one plan entry to create legacy coverage debt.
   The report still exposes `missing_state_prefixes` and
   `missing_state_post_items`, but the scoped command exits 0 and all three
   ART-017 blocking lists remain empty. PASS.
7. Enumerate tracked workflow/state paths from the Git index and run every
   adjacent authority-matched pair. The ART-017 pair is eligible, exits 0, and
   reports `status: pass`; workflows without an eligible adjacent state remain
   explicitly excluded rather than synthesized. PASS.
8. Open PR #490 and follow its review order. The packet identifies the authored
   validator and client guidance, isolated controls, generated Claude/Codex
   copies, artifact refreshes, and final verification evidence. PASS.
9. Inspect both authored client guidance paragraphs and the generated
   validator copies. Claude Code and Codex both say legacy debt is visible but
   nonblocking, all three current-run invariants stop the run, all keys are
   named, and both generated validators are byte-identical to source. PASS.

## FR Coverage Matrix

| Acceptance evidence | Requirements covered |
|---------------------|----------------------|
| Cases 1–4 | FR-001–FR-003, FR-007–FR-011, FR-019 |
| Cases 5–6 | FR-004–FR-006, FR-008, FR-017–FR-018 |
| Case 7 | FR-012–FR-015 |
| Case 8 | FR-016, FR-020 |
| Case 9 | FR-016–FR-018, FR-020 |

All 20 functional requirements have manual acceptance coverage.

## Negative-Path Tests

- Multiple active steps, a duplicate step, and reordered checkpoints were each
  planted alone. Every case failed closed with exit 1 and only its expected
  ART-017 key populated.
- Legacy structural coverage debt remained visible while the scoped command
  exited 0, confirming that ART-017 did not arm unrelated advisory keys.

## Self-Review Findings

Two initial UAT-oracle findings were remediated before sign-off:

- A wording check required the literal hyphenated phrase `current-run` and
  rejected the equally clear `current run`. The oracle now evaluates the
  documented invariant meaning instead of punctuation.
- A parity check required Claude and Codex guidance paragraphs to be
  byte-identical even though each client has legitimate platform-specific
  setup wording. The oracle now compares the required behavior: legacy debt is
  visible and nonblocking, the three named invariants stop the run, and the
  generated validator bytes match the shared source.

The corrected run passed 9/9. No product defect or unremediated UAT finding
remains.

## Sign-off

- [x] Every acceptance scenario was executed and its observable result matched.
- [x] Every negative-path case failed or remained advisory exactly as specified.
- [x] Claude Code and Codex behavior and generated distribution parity passed.
- [x] PR reviewer traceability passed.

## Rollback

Revert the atomic three-key rule-membership and intent-verdict change together,
then regenerate both client distributions and proofs. Do not revert only one
client or only the rule tuple.
