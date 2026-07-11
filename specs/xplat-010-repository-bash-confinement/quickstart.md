# Quickstart: Validating Repository Bash Confinement (XPLAT-010)

Runnable validation scenarios proving each user story end-to-end. Run all commands from the
repository root. Prerequisites: Python 3.11+, `git`; `gh` v2+ for the release paths;
`pnpm` for docs. No repository-local Bash or `jq` runtime is required to run the ported suite
(that is the point); hosted workflows may still invoke bounded shell glue inside `.github/workflows/`.

Runner gate shorthand:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < <request.json>
```

---

## US1 — Cross-platform Python suite orchestrator

**Goal**: the full deterministic suite runs from Python with the bash runner's flags,
headline, and exit codes.

```text
python3 tests/speckit-pro/run-all.py
python3 tests/speckit-pro/run-all.py --layer 1
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-toolchain-preflight.json
```

**Expected**: the no-flag command runs the deterministic default layers and ends with
`speckit-pro test suite: X/Y passed` and exit 0; current integrated evidence is
`2442/2442` by composed coverage: the aggregate run isolated four stale-proof gate
failures and the refreshed exact gate module passed `60/60`. `--layer 1` selects the same structural scope the bash `--layer 1` did. The
shipped suite gate resolves its layer roster from `tests/speckit-pro/suite-manifest.json`
(not by parsing any bash runner) with its envelope contract unchanged. Verify the no-flag
command on a machine with no Bash and no `jq` present (SC-002).

Do not use `--all` as deterministic acceptance evidence. `--all` implies live mode: with
the current manifest it executes Layers 1, 4, and 5 plus live Layer 7, prints the manual
command plans for Layers 2, 3, and 6, and does not select gate-only Layer 8. Use it only for
an intentional live run. See `contracts/suite-manifest.schema.json`.

---

## US2 — Runtime count-parity proof per port

**Goal**: each port PR shows a runtime name-and-count diff proving 1:1 preservation.

```text
# capture the bash baseline for a script (pinned non-root env):
python3 tests/speckit-pro/lib/capture_baseline.py <script>.sh \
  > tests/speckit-pro/parity/xplat-010/<script>-baseline.txt
# run the ported module and compare ordered names + total:
python3 tests/speckit-pro/layer4-scripts/<module>.py
```

**Expected**: the committed baseline lists one `NNN <name>` line per executed `_pass`/`_fail`
plus `TOTAL: <N>`; the ported module's `{passed}/{total}` and ordered subTest names match 1:1
(`bash: N == python: N`; unified diff empty or `no differences — 1:1 preserved`). A silent
rename/drop yields a non-empty diff and flags the PR as a regression (SC-003). The running
ledger `docs/ai/specs/.process/XPLAT-010-count-ledger.md` and the final
`XPLAT-010-suite-parity-result.json` record cumulative preservation. See
`contracts/count-parity-baseline.contract.md`.

**Deletion reconciliation**: FR-016 authoritatively covers 33 deletions: 31 true
orphans plus 2 redundant wrappers. The estimator test is excluded from that set;
PR 13 restores its subject and ports the active test to Python.

---

## US3 — Repository Bash confinement guard

**Goal**: the guard fails any new `.sh`/Bash-shebang/active `bash`/`jq` invocation outside
`.github/workflows/`, with the fail-closed 10-file `.specify/**` allowlist.

```text
# live repo-wide scan (default-suite case) + release-readiness composition:
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-010-confinement/requests/repo-bash-confinement.json
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/release-readiness.json
```

**Expected**: a clean tree passes; a tree with a stray new `.sh` outside the workflow boundary
or a non-allowlisted Bash file under `.specify/**` fails closed (`status: fail`,
`blocking_count > 0`). Each of the 10 allowlisted vendored files is accepted and marked
`release_readiness_excluded: true`, excluded from the positive Bash-free evidence set. The
guard enumerates live via `git ls-files -z` (never a fixed list) and is composed into both the
default suite and the release-readiness gate (`repo_bash_confinement` check), riding the
existing `validate-plugins` sentinel + release-readiness leg with zero new required checks or
branch-protection changes. A prose mention of `bash`/`jq` in Markdown/fixtures does NOT fail;
a `hooks.json` `command` or `package.json` `scripts` value that invokes them does (SC-001,
SC-004). See `contracts/{confinement-allowlist,repo-bash-confinement-result}.schema.json`.

---

## US4 — Container and runner preflight CI

**Goal**: Linux preflight gates, Windows smoke is advisory, evidence is uploaded.

```text
gh workflow run container-preflight.yml           # manual dispatch
# or push a change touching speckit-pro/speckit_pro_runner/** or the suite manifest
```

**Expected**: the workflow starts on every PR and manual dispatch so the
`container-preflight-linux-amd64` and `container-preflight-linux-arm64` required contexts always
report. Runner/gate/workflow changes and manual dispatch run the heavy jobs; a docs-only PR skips
them and both sentinels report an explicit successful no-op. Linux gates; Windows x64/ARM64 smoke
is `continue-on-error`, requires Python 3.11+, and never blocks. The runner-independent control job
records stable Windows x64 and public-preview Windows ARM64 status plus configured enablement;
x64 defaults on, ARM64 defaults off until explicitly enabled. Every executed role uploads evidence
that is explicitly not native installed-plugin UAT (SC-008).

**Hosted boundary**: PR 11 / T108 remains pending until an actual PR URL, hosted relevant-change
and docs-only runs, manual-dispatch artifacts, and configured-runner results exist. Add the two
Linux contexts to branch protection only after the workflow is merged and both contexts have
reported. Local `49/49` sentinel validation does not prove that hosted or post-merge behavior.

---

## US5 — Public-readable GitHub Release Highlights

**Goal**: the composer rewrites the Release body with plain-English Highlights + a
conventional-commit appendix.

```text
python3 scripts/compose-release-notes.py \
  --tag speckit-pro-v2.19.0 \
  --dry-run \
  --fixture tests/speckit-pro/layer4-scripts/fixtures/release-notes/quickstart.json
```

**Expected**: the composed body opens with a plain-English Highlights section harvested from
PR `release-note` blocks (skip-labeled PRs omitted; missing-block feat/fix PRs degrade to
de-prefixed titles; zero blocks → all degrade gracefully), with the original conventional-commit
list preserved below as an appendix; deterministic stdlib only, no LLM, no new secret;
CHANGELOG.md is untouched. The live workflow captures mutable API inputs once as an immutable,
SHA-256-audited artifact, and composition reruns consume that same snapshot. Fails loud on a
Compare API error, a truncated/paginated response, a snapshot-integrity failure, or a commit
subject with no resolvable trailing `(#N)` (SC-005). See `contracts/release-note-block.contract.md`.

---

## US6 — Release-note enforcement check

**Goal**: `validate-release-note` fails a feat/fix PR missing the block; the skip label exempts.

```text
# open a feat PR with no release-note block  -> check fails
# add the ```release-note``` block           -> check passes
# label another PR 'release-note/skip'        -> check passes without a block
```

**Expected**: the check runs on `opened, reopened, synchronize, edited, labeled, unlabeled,
ready_for_review`; scopes to releasable types only (`feat`/`fix` incl. scoped and `!` forms);
skips drafts and release-please's own PRs; handles the PR body via env vars, never shell
interpolation. It is a NEW required status check — PR 12b calls out the manual, post-merge
branch-protection addition and creates the `release-note/skip` label (SC-006). The actual PR URL,
hosted event behavior, and required-check registration remain pending. See
`contracts/release-note-block.contract.md` §6.

---

## US7 — Restored spec-size estimator

**Goal**: `estimate-spec-size` returns a populated `{estimated_loc, suggested_slices, status}`.

```text
python3 tests/speckit-pro/layer4-scripts/test-estimate-spec-size.py
python3 -c 'import json,shlex,sys; t=shlex.split(open("tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/typical-under.args", encoding="utf-8").read()); m={"--user-stories":"user_stories","--files":"files","--frs":"frs"}; inputs={m[t[i]]:int(t[i+1]) for i in range(0,len(t),2)}; json.dump({"schema_version":"1.0","request_id":"quickstart-typical-under","helper_id":"estimate-spec-size","operation":"estimate-spec-size","mode":"read_only","inputs":inputs},sys.stdout)' \
  | env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner
```

**Expected**: the fixture suite ends `test-estimate-spec-size: 33/33 passed`. The second
command parses the committed `typical-under.args` signals (`--user-stories 2 --files 3
--frs 4`), constructs the runner request envelope, and returns `status: ok` with
`data.stdout_json` equal to the committed `typical-under.json` golden result:
`{estimated_loc: 230, suggested_slices: 1, status: "ok"}`. Other golden fixtures retain
the pinned boundaries (`--files 20` → `{800, 2, "warn"}`; bad input → `{0, 1, "ok"}`).
The committed `.args`/`.json` pair is the fixture contract; no request file is
assumed. See `contracts/estimate-spec-size.schema.json`.

---

## Full-suite gate (before/after any change)

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-default-suite.json
pnpm --dir docs-site validate
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-010-confinement/requests/repo-bash-confinement.json
```

**Expected**: default-suite gate PASS; docs validation PASS; the confinement gate
returns `status: ok` once the stack lands (every remaining in-scope Bash surface is either
confined workflow dispatch glue or one of the 10 allowlisted `.specify/**` vendored helpers).
Shipped-runner
changes (PRs 2/7b/8/9/10/13) additionally require the payload/proof regeneration ritual with
release-readiness evidence regenerated LAST and home-directory sanitization.
