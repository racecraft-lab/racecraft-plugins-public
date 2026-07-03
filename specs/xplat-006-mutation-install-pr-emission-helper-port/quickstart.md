# Quickstart: XPLAT-006 Mutation, Install, and PR-Emission Helper Port

This guide describes source-checkout validation for the XPLAT-006 plan. It does
not perform active Claude/Codex cutover, generated-payload selection/cutover,
public documentation updates, native matrix UAT, or repo-local release-gate
migration. The only allowed skill/payload changes are the autopilot
phase-coverage hardening source and generated mirror.

## Prerequisites

- Worktree: `.worktrees/xplat-006-mutation-install-pr-emission-helper-port`
- Branch: `codex/xplat-006-mutation-install-pr-emission-helper-port`
- Python 3.11+
- No network requirement
- Fake repositories, fake `gh`, fake `specify`, fake Claude homes, fake Codex
  homes, and fake plugin caches for deterministic helper tests

## 1. Verify Autopilot Phase Coverage Hardening

Run:

```bash
python3 tests/speckit-pro/layer4-scripts/test-autopilot-phase-coverage.py
```

Expected outcome:
- One complete workflow/state fixture passes.
- Missing Phase 6.5 fails.
- Missing canonical Post items fail.
- Collapsed later phases fail.
- Semantically mislabeled phase numbers fail.
- Malformed `autopilot-state.json` returns deterministic `input_error`.

Run the validator against the active workflow/state when state exists:

```bash
python3 speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py \
  --workflow docs/ai/specs/.process/XPLAT-006-workflow.md \
  --state docs/ai/specs/.process/autopilot-state.json
```

Expected outcome:
- `status` is `pass` for a complete workflow/state pair.
- `status` is `fail` or `input_error` before a run advances if required phase
  or Post coverage is missing.

## 2. Run Mutation Helper Fixtures

Planned focused command:

```bash
python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-mutation-helpers.py
```

Expected outcome:
- Dry-run fixtures report planned operations and mutate no repo, home, cache,
  network, or GitHub state.
- Apply fixtures mutate only clean fake repositories or fixture fake-home roots.
- Dirty-worktree, unavailable git-status, path-escape, malformed JSON,
  write-failure, and partial-failure fixtures fail deterministically.
- Each promoted Bash-backed helper references accepted Bash comparison evidence.

## 3. Run Install and Doctor Fixture Proof

Planned fixture coverage:
- Complete fake Claude/Codex install
- Missing Codex agent
- Missing Claude package agent
- Stale plugin cache
- Downgrade refusal
- Missing runner file
- Checksum mismatch
- Missing generated payload file
- Malformed inventory
- Missing fake `gh` or `specify`
- Real-home refusal
- Safe repair
- Unsafe manual remediation
- Blocked repair

Expected outcome:
- Doctor/preflight remains read-only by default.
- Repair runs only as explicit apply mode inside fixture fake-home boundaries.
- Unrelated files are preserved.

## 4. Run PR-Emission and Restack Fixture Proof

Planned fixture coverage:
- PR body and UAT skeleton generation
- Final reviewability backstop
- PR packet and workflow-contract outputs
- Multi-PR emission command capture
- Fake restack apply
- Migration and relocation fake repo apply
- Live GitHub/repo command-plan apply rejection as deferred

Expected outcome:
- Candidate PR emission remains dry-run command capture.
- Command-plan apply returns a deterministic deferred-live-mutation failure in
  XPLAT-006.

## 5. Run Repository Gates

Run focused and deterministic layers:

```bash
bash tests/speckit-pro/run-all.sh --layer 4
bash tests/speckit-pro/run-all.sh --layer 1
bash tests/speckit-pro/run-all.sh
```

Expected outcome:
- Layer 4 proves helper behavior and fixture parity.
- Layer 1 proves plugin structure remains valid.
- Default suite passes before PR.

## 6. Run Scope Audit

Review changed files:

```bash
git diff --name-only origin/main...HEAD
```

Expected outcome:
- No active Claude/Codex invocation paths, hooks, generated-payload
  selection/cutover, install guidance, public docs claims, repo-local release
  gates, native UAT artifacts, or public platform support claims changed in
  XPLAT-006; allowed phase-coverage hardening source/mirror changes are listed
  separately.
- Runner manifest/checksum metadata is updated if runner-owned Python files
  changed.

## 7. PR Packet Traceability

The PR packet must cite:
- Slice 1 mutation primitive files, fixture ids, Bash-reference ids, promotion
  status, and rollback/manual remediation notes.
- Slice 2 install/doctor inventory records, fake-home fixture ids, safe-repair
  classifications, and no-real-home proof.
- Slice 3 PR/restack/migration/relocation fixture ids, fake `gh` proof,
  command-capture evidence, and live-coverage limits.
- Autopilot validator and test evidence for Phase 6.5 and Post coverage.
- Scope audit evidence for all deferred cutover surfaces.
