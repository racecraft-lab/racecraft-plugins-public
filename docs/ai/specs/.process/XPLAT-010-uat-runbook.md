# UAT Runbook: Repository Bash Confinement and CI Dispatch Guard

| Field | Value |
|-------|-------|
| Spec | `XPLAT-010` (archived) |
| Review stack | PRs #311 through #328, all merged on 2026-07-11 |
| Stack topology | #311-#313 were squash-merged; #314-#328 form a contiguous bottom-to-top merge chain ending at `ad89f4531ce33021c3c722ba5f0a0ae73bd5aa29` |
| Current hosted state | T108 and T117 complete; durable evidence is recorded below and in the post-merge archive report |
| Generated packet set | 18/18 packet/body/validation triplets pass at frozen implementation head `a7b2d27b12fdc5051dfa4829c94f92752e2f5146` |
| Source | Preserved XPLAT-010 process evidence, suite manifest, purpose-based fixtures, immutable merge provenance, and GitHub run metadata |

Recheck immutable merge and hosted evidence when auditing this runbook:

```console
gh pr view 311 --repo racecraft-lab/racecraft-plugins-public --json number,state,mergedAt,mergeCommit,url
gh pr view 328 --repo racecraft-lab/racecraft-plugins-public --json number,state,mergedAt,mergeCommit,url
gh run view 29161090549 --repo racecraft-lab/racecraft-plugins-public --json status,conclusion,headSha,jobs,url
gh api repos/racecraft-lab/racecraft-plugins-public/branches/main/protection/required_status_checks
```

The recorded acceptance requires the exact run and branch-rule facts below; a future
failure does not rewrite this historical result.

## Environment setup

Use any checkout containing the integrated stack and run from its repository root. Keep
all evidence repository-relative; do not record an operator-specific absolute worktree
path. Local focused validation requires Python 3.11+ and Git. Hosted inspection requires
`gh` v2+ with repository access.

```console
git rev-parse --show-toplevel
python3 -c 'from pathlib import Path; required=(Path("tests/speckit-pro/suite-manifest.json"), Path("docs/ai/specs/.process/XPLAT-010-workflow.md")); missing=[str(p) for p in required if not p.is_file()]; assert not missing, missing; print("repository-relative UAT paths resolved")'
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

2. Inspect the accepted hosted `pull_request` evidence:

   ```console
   gh run view 29159969108 --repo racecraft-lab/racecraft-plugins-public
   gh run view 29161055742 --repo racecraft-lab/racecraft-plugins-public
   gh run view 29159559914 --repo racecraft-lab/racecraft-plugins-public
   ```

   Expected: the relevant-path run executes both Linux heavy jobs and Windows x64;
   the docs-only run skips heavy execution while both sentinels pass; and the failure
   run propagates detector failure to both sentinels while retaining evidence.

3. Inspect the completed post-merge manual acceptance:

   ```console
   gh run view 29161090549 --repo racecraft-lab/racecraft-plugins-public --json status,conclusion,headSha,jobs,url
   gh api repos/racecraft-lab/racecraft-plugins-public/actions/runs/29161090549/artifacts --jq '.artifacts[] | [.name,.expired,.expires_at] | @tsv'
   ```

   Expected: success at `main@ad89f453`, eight artifacts, both Linux heavy jobs and
   sentinels passing, native Windows x64 smoke passing, and Windows ARM64 recorded as
   available but explicitly disabled without queueing its label.

4. Inspect PR #331 trigger canaries: `opened` run `29161598122`, `synchronize`
   run `29161613608`, `ready_for_review` run `29161619193`, and `reopened` run
   `29161647866`. Each passed both Linux sentinels and retained five artifacts.

- [x] Local US4 structure/helper contract accepted: 33/33 helper and 49/49 sentinel checks passed.
- [x] Relevant-change and docs-only `pull_request` evidence accepted.
- [x] Failure propagation and Windows advisory behavior accepted.
- [x] All four declared PR trigger actions accepted through PR #331 canaries.
- [x] Post-merge `workflow_dispatch` and artifact evidence accepted (T108).

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

   Expected: `validate-release-note` appears and passes on the accepted hosted runs.

3. After merge, inspect `main` branch protection:

   ```console
   gh api repos/racecraft-lab/racecraft-plugins-public/branches/main/protection/required_status_checks
   ```

   Expected: non-strict protection requires exactly `validate-plugins`,
   `validate-pr-title`, `validate-release-note`,
   `container-preflight-linux-amd64`, and
   `container-preflight-linux-arm64`, all from GitHub Actions.

- [x] Local US6 policy/template contract accepted: release-note policy 30/30.
- [x] Hosted `validate-release-note` behavior accepted.
- [x] Post-merge five-check branch-protection rule recorded (T117).

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

No XPLAT-010 acceptance blocker remains. Public native-platform release claims remain
separately blocked by the preserved XPLAT-008 operator UAT matrix; XPLAT-010 hosted
preflight evidence does not substitute for that native installed-plugin UAT.

## Sign-off

- [x] All seven local user-story contracts are accepted from the focused evidence above.
- [x] T131 parity and T134 18-packet evidence are complete for frozen implementation head `a7b2d27b12fdc5051dfa4829c94f92752e2f5146`.
- [x] T133 final neutral-PATH Bash-absent, `jq`-absent Python 3.11+ evidence is complete at frozen implementation head `a7b2d27b12fdc5051dfa4829c94f92752e2f5146` (tree `a1c42735d35619bbd0a4a90a42c57ab9e578848e`): read-only helpers 42/42 and ARM64 exact pinned-container overlay with hydrated `tasks.md` 42/42.
- [x] T135 final neutral-PATH deterministic suite and docs evidence is complete at the same frozen implementation head: 2512/2512 total, Layer 1 1373/1373, Layer 4 953/953, Layer 5 186/186; `pnpm --dir docs-site validate` passed.
- [x] T108 and T117 hosted/post-merge evidence is complete.

## Rollback

Use the immutable recovery commands in
`.specify/memory/archive-reports/2026-07-11-xplat-010-post-merge-hygiene.md`, then rerun
the focused commands, default suite, and docs validation. There is no database, browser
storage, or external service state to migrate.
