# UAT Runbook: xplat-010-repository-bash-confinement

| Field | Value |
|-------|-------|
| Spec | `xplat-010-repository-bash-confinement` |
| Review stack | PRs #311 through #328 (18 open stacked PRs, fact-checked 2026-07-10) |
| Stack topology | #311 targets `main`; each later PR targets its predecessor; #328 is the integration tip |
| Current hosted state | Dynamic; inspect live checks and record their actual conclusions rather than freezing a transient result here |
| Generated packet set | 18/18 packet/body/validation triplets pass at frozen implementation head `a7b2d27b12fdc5051dfa4829c94f92752e2f5146` |
| Source | Current `spec.md`, `tasks.md`, `quickstart.md`, suite manifest, purpose-based fixtures, and live GitHub PR metadata |

Do not replace the hosted-state row with a green claim unless the live checks support it.
Recheck the stack at review time:

```console
gh pr view 311 --repo racecraft-lab/racecraft-plugins-public --json number,state,baseRefName,headRefName,url
gh pr view 328 --repo racecraft-lab/racecraft-plugins-public --json number,state,baseRefName,headRefName,mergeStateStatus,url
gh pr checks 328 --repo racecraft-lab/racecraft-plugins-public
```

`gh pr checks` returns nonzero while a check is failing. Record that result rather than
masking it.

## Environment setup

Use any checkout containing the integrated stack and run from its repository root. Keep
all evidence repository-relative; do not record an operator-specific absolute worktree
path. Local focused validation requires Python 3.11+ and Git. Hosted inspection requires
`gh` v2+ with repository access.

```console
git rev-parse --show-toplevel
python3 -c 'from pathlib import Path; required=(Path("tests/speckit-pro/suite-manifest.json"), Path("specs/xplat-010-repository-bash-confinement/quickstart.md")); missing=[str(p) for p in required if not p.is_file()]; assert not missing, missing; print("repository-relative UAT paths resolved")'
```

The parent integration owner runs `python3 tests/speckit-pro/run-all.py` and
`pnpm --dir docs-site validate`. This runbook's local UAT uses only the focused commands
below.

## Per-story acceptance tests

### User Story 1 - Python suite orchestration

1. Run the focused structural layer and orchestrator contract:

   ```console
   python3 tests/speckit-pro/run-all.py --layer 1
   python3 tests/speckit-pro/test-run-all.py
   ```

   Expected: both exit 0. Layer 1 prints the toolchain and structural headings, then
   equal passed/total values. The focused test covers manifest selection, flags,
   subprocess exit propagation, and invalid/missing manifest entries without relying on
   a hard-coded count.

2. Run the promoted toolchain request:

   ```console
   env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-toolchain-preflight.json
   ```

   Expected: top-level `status` is `ok`, `exit_code` is `0`, and the suite gate is
   promoted, passing, and non-blocking.

3. Inspect `tests/speckit-pro/suite-manifest.json`.

   Expected: executable entries use current Python paths and Python dispatch; no active
   test entry points at a retired repository-local Bash wrapper.

- [x] US1 accepted from fresh focused output: orchestrator 28/28 and promoted preflight request exit 0.

### User Story 2 - Per-port runtime parity

1. Run one complete purpose-based parity sample:

   ```console
   python3 tests/speckit-pro/unit/test-estimate-spec-size.py
   python3 -c 'from pathlib import Path; p=Path("tests/speckit-pro/parity/bash-to-python/test-estimate-spec-size-baseline.txt"); lines=p.read_text(encoding="utf-8").splitlines(); assert lines and lines[-1].startswith("TOTAL: "); print(f"{p}: {lines[-1]}")'
   ```

   Expected: the test exits 0 with equal passed/total values and no inventory-mismatch
   diagnostic. The baseline command prints its own `TOTAL:` line. The module validates
   ordered names against that committed baseline before its assertions run.

2. Inspect `docs/ai/specs/.process/XPLAT-010-count-ledger.md`.

   Expected: the estimator row points to the same module and baseline, and each port row
   records its historical-to-current disposition without checkout-specific paths.

3. Verify the current cumulative artifact:

   ```console
   python3 -c 'import json; from pathlib import Path; p=Path("docs/ai/specs/.process/XPLAT-010-suite-parity-result.json"); assert p.is_file(), "T131 parity artifact is missing"; data=json.loads(p.read_text(encoding="utf-8")); print(data.get("status", "<missing status>"))'
   ```

   Expected at final closeout: the file exists, parses, and records no undocumented count
   drop or silent rename. At the 2026-07-10 fact-check, it reported `status: passed`;
   cumulative US2 sign-off still requires parent review and task-state recording.

- [x] One per-port parity sample accepted: estimator 33/33.
- [x] T131 cumulative parity artifact accepted: status `passed`, 54 true-port rows, and no undocumented mismatch.

### User Story 3 - Repository Bash confinement

1. Run the live tracked-file guard, release-readiness composition fixture, and focused
   negative-path contract:

   ```console
   env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/repository-bash-confinement/requests/repo-bash-confinement.json
   env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/release-readiness.json
   python3 tests/speckit-pro/unit/test-repo-bash-confinement.py
   ```

   Expected: the guard returns top-level `status: "ok"`, `data.status: "pass"`, no
   blockers, and `enumeration.source: "git ls-files -z"`. Its allowlist count matches
   `tests/speckit-pro/unit/fixtures/repository-bash-confinement/allowlist.json`; all
   vendored `.specify/**` findings are release-readiness excluded. Release readiness has
   no active-path blockers. The focused test exits 0 and exercises both pass and fail
   cases.

- [x] US3 accepted from fresh guard JSON and focused test output: 47/47, 0 blockers, and 10 release-excluded vendored findings.

### User Story 4 - Container and runner preflight (T108)

1. Prove the local structure/helper contract:

   ```console
   python3 tests/speckit-pro/unit/test-hosted-windows-preflight.py
   python3 tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.py
   ```

   Expected locally: the helper prints `33/33 passed` and the sentinel prints
   `49/49 passed`. This proves workflow
   syntax and routing contracts only. It does not prove GitHub triggers, hosted runner
   availability, uploaded artifacts, or branch-protection contexts.

2. Inspect the available pre-merge hosted `pull_request` evidence:

   ```console
   gh pr checks 325 --repo racecraft-lab/racecraft-plugins-public
   gh pr checks 328 --repo racecraft-lab/racecraft-plugins-public
   ```

   Expected now: actual conclusions are printed, including failures or skips. Do not
   mark T108 complete from local tests or from a partially green hosted run.

3. Apply the official `workflow_dispatch` boundary.

   GitHub documents that `workflow_dispatch` runs only when the workflow file exists on
   the default branch. See
   [`workflow_dispatch`](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch).
   `.github/workflows/container-preflight.yml` is not yet on default branch `main`, so
   pre-merge hosted evidence is `pull_request` only. Manual dispatch is deferred until
   after merge; a branch `--ref` cannot bypass the default-branch requirement.

4. After the stack merges and the workflow exists on `main`, run the deferred manual
   acceptance:

   ```console
   gh workflow run container-preflight.yml --repo racecraft-lab/racecraft-plugins-public --ref main -f windows_x64_enabled=true -f windows_arm64_enabled=false
   gh run list --repo racecraft-lab/racecraft-plugins-public --workflow container-preflight.yml --event workflow_dispatch --limit 1
   ```

   Expected post-merge: a manual run appears. Its artifacts show Linux role outcomes,
   Windows x64 advisory behavior, and ARM64-disabled control evidence without queueing
   the ARM64 label.

5. T108 is complete only when hosted evidence includes all of these observations:
   relevant changes run both Linux heavy jobs; docs-only changes skip heavy jobs while
   both Linux sentinels succeed; Linux failures propagate to sentinels; Windows roles do
   not block; each executed role uploads evidence; ARM64-disabled control evidence is
   present; the configured `opened`, `reopened`, `synchronize`, and `ready_for_review`
   PR triggers behave as declared; and post-merge manual dispatch is recorded.

- [x] Local US4 structure/helper contract accepted: 33/33 helper and 49/49 sentinel checks passed.
- [ ] Pre-merge relevant-change `pull_request` evidence accepted.
- [ ] Pre-merge docs-only `pull_request` evidence accepted.
- [ ] Post-merge `workflow_dispatch` and artifact evidence accepted (T108).

### User Story 5 - Public release highlights

```console
python3 tests/speckit-pro/unit/test-compose-release-notes.py
python3 scripts/compose-release-notes.py --tag speckit-pro-v2.19.0 --dry-run --fixture tests/speckit-pro/unit/fixtures/release-notes/quickstart.json
python3 tests/speckit-pro/layer1-structural/validate-release-workflow.py
```

Expected: composition prints `46/46 passed`, workflow validation prints `41/41 passed`,
and the dry run exits 0. It performs no network mutation and prints a release body
starting with `## Highlights`, preserving `## Commit appendix`, and ending with snapshot
audit metadata. The tests cover fail-loud Compare, pagination, integrity, and unresolved
PR-number paths. Workflow validation also executes failed capture, failed snapshot
download, and snapshot-digest mismatch; each path writes canonical
`release-note-audit.json`, emits `release_note_composition_failed`, and preserves the
always-run immutable audit upload.

- [x] US5 accepted from 46/46 composition, 41/41 release workflow, and dry-run output.

### User Story 6 - Release-note enforcement (T117)

1. Run local policy and template checks:

   ```console
   python3 tests/speckit-pro/unit/test-release-note-policy.py
   python3 -c 'from pathlib import Path; p=Path(".github/pull_request_template.md"); text=p.read_text(encoding="utf-8"); assert text.count("```release-note") == 1; print(f"{p}: one release-note fence")'
   ```

   Expected: both exit 0. The policy test covers releasable titles, valid/invalid fenced
   blocks, skip-label behavior, draft behavior, sanitization, and workflow contract.

2. Inspect the hosted check without assuming its conclusion:

   ```console
   gh pr checks 326 --repo racecraft-lab/racecraft-plugins-public
   gh pr checks 328 --repo racecraft-lab/racecraft-plugins-public
   ```

   Expected for acceptance: `validate-release-note` appears with its actual conclusion.
   A missing check is missing evidence, not a pass. Other failed PR checks may make either
   command return nonzero.

3. After merge, inspect `main` branch protection:

   ```console
   gh api repos/racecraft-lab/racecraft-plugins-public/branches/main/protection/required_status_checks
   ```

   Expected for T117 completion: the returned required contexts include
   `validate-release-note`, and the operator records the response. Missing context,
   `null`, HTTP 404, or insufficient authorization does not prove configuration.
   The 2026-07-10 fact-check returned only `validate-plugins` and `validate-pr-title`;
   therefore T117 is open. This runbook does not claim the new required check is already
   configured.

- [x] Local US6 policy/template contract accepted: release-note policy 30/30.
- [ ] Hosted `validate-release-note` behavior accepted.
- [ ] Post-merge branch-protection context recorded (T117).

### User Story 7 - Restored spec-size estimator

```console
python3 tests/speckit-pro/unit/test-estimate-spec-size.py
python3 -c 'import json,shlex,sys; t=shlex.split(open("tests/speckit-pro/unit/fixtures/estimate-spec-size/typical-under.args", encoding="utf-8").read()); m={"--user-stories":"user_stories","--files":"files","--frs":"frs"}; inputs={m[t[i]]:int(t[i+1]) for i in range(0,len(t),2)}; json.dump({"schema_version":"1.0","request_id":"uat-typical-under","helper_id":"estimate-spec-size","operation":"estimate-spec-size","mode":"read_only","inputs":inputs},sys.stdout)' | env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner
```

Expected: the test exits 0 with equal passed/total values. The runner returns top-level
`status: "ok"`, and `data.stdout_json` exactly matches
`tests/speckit-pro/unit/fixtures/estimate-spec-size/typical-under.json`. The unit test also
validates the other purpose-based estimator fixtures, including bad input.

- [x] US7 accepted from estimator 33/33 and runner JSON exit 0.

## FR coverage matrix

| Behavior | Acceptance evidence |
|----------|---------------------|
| Manifest-driven Python orchestration and fail-closed dispatch | US1 focused layer, runner request, and `test-run-all.py` |
| Per-port ordered-name/count preservation and cumulative closeout | US2 baseline sample, ledger, and T131 artifact |
| Live tracked-file confinement and release-readiness exclusion | US3 guard JSON and focused negative-path test |
| Linux gating, Windows advisory preflight, evidence uploads, and trigger boundaries | US4 local contracts plus T108 hosted evidence |
| Deterministic consumer-facing release highlights | US5 focused test and offline fixture run |
| Release-note policy plus required-check registration | US6 local/hosted evidence and T117 branch rule |
| Restored estimator operation and committed caller fixtures | US7 focused test and runner JSON |

## Negative-path checks

These deterministic modules exercise mutations in isolated fixtures; do not edit the live
review tree to recreate them.

```console
python3 tests/speckit-pro/test-run-all.py
python3 tests/speckit-pro/unit/test-repo-bash-confinement.py
python3 tests/speckit-pro/unit/test-release-note-policy.py
python3 tests/speckit-pro/unit/test-compose-release-notes.py
python3 tests/speckit-pro/unit/test-hosted-windows-preflight.py
python3 tests/speckit-pro/unit/test-estimate-spec-size.py
```

Expected: every module exits 0. Together they cover missing/invalid manifest entries,
stray Bash and active config invocation, allowlist fail-closed behavior, invalid release
notes, incomplete release API/snapshot inputs, disabled Windows ARM64 routing, and bad
estimator input. Equal passed/total output is the acceptance signal; this runbook does not
pin totals that will drift as coverage grows.

## Sign-off blockers

The only remaining integrated-stack blockers are:

- T108 lacks relevant-change, docs-only, and post-merge manual-dispatch hosted evidence.
- T117 lacks recorded `main` branch-protection evidence for `validate-release-note`.

## Sign-off

- [x] All seven local user-story contracts are accepted from the focused evidence above.
- [x] T131 parity and T134 18-packet evidence are complete for frozen implementation head `a7b2d27b12fdc5051dfa4829c94f92752e2f5146`.
- [x] T133 final neutral-PATH Bash-absent, `jq`-absent Python 3.11+ evidence is complete at frozen implementation head `a7b2d27b12fdc5051dfa4829c94f92752e2f5146` (tree `a1c42735d35619bbd0a4a90a42c57ab9e578848e`): read-only helpers 42/42 and ARM64 exact pinned-container overlay with hydrated `tasks.md` 42/42.
- [x] T135 final neutral-PATH deterministic suite and docs evidence is complete at the same frozen implementation head: 2512/2512 total, Layer 1 1373/1373, Layer 4 953/953, Layer 5 186/186; `pnpm --dir docs-site validate` passed.
- [ ] T108 and T117 hosted/post-merge evidence is complete.

## Rollback

Revert the affected stack slice rather than editing unrelated files, then rerun its focused
commands from this runbook. The parent integration owner reruns the default suite and docs
validation after the stack is restacked. There is no database, browser storage, or external
service state to migrate.
