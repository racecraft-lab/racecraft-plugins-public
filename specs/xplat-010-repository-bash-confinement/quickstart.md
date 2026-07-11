# Quickstart: Validating Repository Bash Confinement (XPLAT-010)

Run commands from the repository root. Keep evidence paths repository-relative; do not
record an operator's checkout or temporary worktree path. Local prerequisites are Python
3.11+ and Git. Hosted checks additionally require `gh` v2+ with repository access. The
final frozen-stack evidence is recorded below; T108 and T117 remain separate hosted and
operator acceptance gaps.

Confirm the working directory before starting:

```console
git rev-parse --show-toplevel
python3 -c 'from pathlib import Path; p=Path("tests/speckit-pro/suite-manifest.json"); assert p.is_file(), p; print(p)'
```

The current review stack is PRs #311 through #328. As fact-checked on 2026-07-10,
all 18 PRs are open; #311 targets `main`, and each later PR targets its predecessor.
The tip is #328. Hosted conclusions are intentionally not frozen in this document; inspect
live state instead of copying a transient check snapshot into acceptance evidence:

```console
gh pr view 311 --repo racecraft-lab/racecraft-plugins-public --json number,state,baseRefName,headRefName,url
gh pr view 328 --repo racecraft-lab/racecraft-plugins-public --json number,state,baseRefName,headRefName,mergeStateStatus,url
gh pr checks 328 --repo racecraft-lab/racecraft-plugins-public
```

`gh pr checks` returns a nonzero exit status while any check is failing. That is an
observable hosted result, not a reason to report the stack as green.

## US1 - Python suite orchestration

```console
python3 tests/speckit-pro/run-all.py --layer 1
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-toolchain-preflight.json
python3 tests/speckit-pro/test-run-all.py
```

**Expected:** each command exits 0. Layer 1 prints `Toolchain Preflight`, then
`Layer 1: Structural Validation`, and finishes with equal passed/total values without
hard-coding a count in this runbook. The runner response has top-level `status: "ok"`,
`exit_code: 0`, and a non-blocking promoted suite gate. The focused orchestrator test
passes its manifest-selection, flag, exit-code, and fail-closed cases.

The authoritative roster is `tests/speckit-pro/suite-manifest.json`. Do not use `--all`
as deterministic acceptance evidence: it opts into live behavior and prints plans for
manual-only layers. The parent integration run executes the no-flag default suite.

## US2 - Per-port runtime parity

The historical Bash captures are frozen. Validate the current Python inventory against
its committed baseline; do not attempt to execute a deleted Bash predecessor.

```console
python3 tests/speckit-pro/unit/test-estimate-spec-size.py
python3 -c 'from pathlib import Path; p=Path("tests/speckit-pro/parity/bash-to-python/test-estimate-spec-size-baseline.txt"); lines=p.read_text(encoding="utf-8").splitlines(); assert lines and lines[-1].startswith("TOTAL: "); assert all(line[:3].isdigit() and line[3:4] == " " for line in lines[:-1]); print(f"{p}: {lines[-1]}")'
```

**Expected:** the test exits 0 with equal passed/total values and no inventory-mismatch
diagnostic. The second command prints the baseline's own `TOTAL:` line. The test module
checks its ordered names against that baseline before running its assertions.

The running ledger is
`docs/ai/specs/.process/XPLAT-010-count-ledger.md`. The cumulative closeout artifact is
`docs/ai/specs/.process/XPLAT-010-suite-parity-result.json`. At the 2026-07-10
fact-check, the current artifact parsed with `status: passed` at frozen implementation head
`a7b2d27b12fdc5051dfa4829c94f92752e2f5146`; T131 is complete. Verify the artifact without copying its mutable totals
into this runbook:

```console
python3 -c 'import json; from pathlib import Path; p=Path("docs/ai/specs/.process/XPLAT-010-suite-parity-result.json"); assert p.is_file(), "T131 parity artifact is missing"; data=json.loads(p.read_text(encoding="utf-8")); print(data.get("status", "<missing status>"))'
```

## US3 - Repository Bash confinement

```console
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/repository-bash-confinement/requests/repo-bash-confinement.json
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/release-readiness.json
python3 tests/speckit-pro/unit/test-repo-bash-confinement.py
```

**Expected:** the confinement response has top-level `status: "ok"`,
`data.status: "pass"`, `data.blocking_count: 0`, and
`data.enumeration.source: "git ls-files -z"`. Its allowlist count matches
`tests/speckit-pro/unit/fixtures/repository-bash-confinement/allowlist.json`; every
reported vendored `.specify/**` finding has `release_readiness_excluded: true`.
The release-readiness response has `status: "ok"` and an active-path guard summary with
no blockers. The focused test exits 0 and covers stray scripts, non-allowlisted vendored
scripts, prose-only mentions, executable config values, allowlist exclusion, and gate
composition.

## US4 - Container and runner preflight (T108 hosted boundary)

Local validation proves structure and helper behavior only:

```console
python3 tests/speckit-pro/unit/test-hosted-windows-preflight.py
python3 tests/speckit-pro/layer1-structural/validate-pr-checks-sentinel.py
```

**Expected locally:** the helper prints `33/33 passed` and the sentinel prints
`49/49 passed`. They validate
the `pull_request` and `workflow_dispatch` declarations, relevant-change routing,
docs-only sentinel behavior, Linux gating roles, advisory Windows roles, and evidence
upload contracts. They do not prove a hosted runner, trigger, artifact, or branch rule.

**Official GitHub limitation:** a `workflow_dispatch` event can run only when the workflow
file exists on the repository's default branch. See GitHub's
[`workflow_dispatch` documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_dispatch).
Because `.github/workflows/container-preflight.yml` is not yet on default branch `main`,
manual dispatch cannot provide pre-merge evidence. Before merge, hosted evidence is
limited to the workflow's `pull_request` runs. Manual dispatch is deferred until after
the stack merges to `main`.

Inspect the current pre-merge `pull_request` evidence without assuming success:

```console
gh pr checks 325 --repo racecraft-lab/racecraft-plugins-public
gh pr checks 328 --repo racecraft-lab/racecraft-plugins-public
```

After `.github/workflows/container-preflight.yml` exists on `main`, an authorized operator
can perform the deferred manual run:

```console
gh workflow run container-preflight.yml --repo racecraft-lab/racecraft-plugins-public --ref main -f windows_x64_enabled=true -f windows_arm64_enabled=false
gh run list --repo racecraft-lab/racecraft-plugins-public --workflow container-preflight.yml --event workflow_dispatch --limit 1
```

**T108 remains open** until hosted evidence shows: a relevant-change PR run executes both
Linux heavy jobs; a docs-only PR run skips heavy jobs while both Linux sentinels succeed;
Windows x64/ARM64 remain advisory; configured ARM64-disabled evidence is uploaded without
queueing that label; every executed role uploads evidence; the configured `opened`,
`reopened`, `synchronize`, and `ready_for_review` PR triggers behave as declared; and the
post-merge manual dispatch is observed. Current failing or skipped jobs must be recorded
as such.

## US5 - Public release highlights

```console
python3 tests/speckit-pro/unit/test-compose-release-notes.py
python3 scripts/compose-release-notes.py --tag speckit-pro-v2.19.0 --dry-run --fixture tests/speckit-pro/unit/fixtures/release-notes/quickstart.json
python3 tests/speckit-pro/layer1-structural/validate-release-workflow.py
```

**Expected:** composition prints `46/46 passed` and workflow validation prints
`41/41 passed`. The dry run exits 0, performs no network mutation, and
prints a body beginning with `## Highlights`, followed by the preserved
`## Commit appendix`, plus deterministic snapshot audit metadata. Fail-loud Compare,
pagination, digest, and unresolved-PR cases are covered by the focused test. The workflow
validator also executes capture failure, snapshot-download failure, and snapshot-digest
mismatch; every path writes canonical `release-note-audit.json`, emits
`release_note_composition_failed`, and leaves the immutable audit upload on `always()`.

## US6 - Release-note enforcement (T117 hosted boundary)

```console
python3 tests/speckit-pro/unit/test-release-note-policy.py
python3 -c 'from pathlib import Path; p=Path(".github/pull_request_template.md"); text=p.read_text(encoding="utf-8"); assert text.count("```release-note") == 1; print(f"{p}: one release-note fence")'
gh pr checks 326 --repo racecraft-lab/racecraft-plugins-public
gh pr checks 328 --repo racecraft-lab/racecraft-plugins-public
```

**Expected locally:** the policy test and template assertion exit 0. The GitHub command
reports show whether `validate-release-note` is present and its actual conclusion. A
missing check is missing evidence, not a pass. Either command may return nonzero when
other PR checks fail and must not be summarized as green without inspecting the output.

`validate-release-note` is a new required status-check name. T117 remains open until an
operator adds it to `main` branch protection after the workflow has merged and reported,
then records the actual rule state. Inspect without mutating the rule:

```console
gh api repos/racecraft-lab/racecraft-plugins-public/branches/main/protection/required_status_checks
```

A JSON response containing `validate-release-note` is positive evidence. A missing
context, `null`, HTTP 404, or authorization error is not evidence that configuration is
complete. The 2026-07-10 fact-check returned only `validate-plugins` and
`validate-pr-title`, so T117 is currently open.

## US7 - Restored spec-size estimator

```console
python3 tests/speckit-pro/unit/test-estimate-spec-size.py
python3 -c 'import json,shlex,sys; t=shlex.split(open("tests/speckit-pro/unit/fixtures/estimate-spec-size/typical-under.args", encoding="utf-8").read()); m={"--user-stories":"user_stories","--files":"files","--frs":"frs"}; inputs={m[t[i]]:int(t[i+1]) for i in range(0,len(t),2)}; json.dump({"schema_version":"1.0","request_id":"quickstart-typical-under","helper_id":"estimate-spec-size","operation":"estimate-spec-size","mode":"read_only","inputs":inputs},sys.stdout)' | env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner
```

**Expected:** the test exits 0 with equal passed/total values. The runner response has
`status: "ok"`; `data.stdout_json` exactly matches
`tests/speckit-pro/unit/fixtures/estimate-spec-size/typical-under.json`. The focused test
also checks the other purpose-based fixtures under
`tests/speckit-pro/unit/fixtures/estimate-spec-size/`, including bad input.

## Parent-owned final gates

The closeout packet set currently contains 18 purpose-mapped directories under
`specs/xplat-010-repository-bash-confinement/.process/pr-packets/`; each has
`body.md`, `packet.json`, and a passing `validation.json`. T134 is complete for the frozen
implementation head `a7b2d27b12fdc5051dfa4829c94f92752e2f5146`. Regenerate any affected triplet if a final branch OID changes.

The final parent integration evidence was recorded on frozen implementation head
`a7b2d27b12fdc5051dfa4829c94f92752e2f5146` (tree
`a1c42735d35619bbd0a4a90a42c57ab9e578848e`):

```console
python3 tests/speckit-pro/run-all.py
pnpm --dir docs-site validate
```

The neutral-PATH deterministic default suite passed 2512/2512: Layer 1 1373/1373, Layer 4
953/953, and Layer 5 186/186. `pnpm --dir docs-site validate` passed. In the Bash-absent,
`jq`-absent Python 3.11+ environment, the read-only helpers passed 42/42 and the ARM64
exact pinned-container overlay with hydrated `tasks.md` passed 42/42.

Do not publish a final hosted-green claim from this evidence. Only T108 hosted evidence and
T117 branch-protection evidence remain open.
