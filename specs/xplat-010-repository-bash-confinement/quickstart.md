# Quickstart: Validating Repository Bash Confinement (XPLAT-010)

Runnable validation scenarios proving each user story end-to-end. Run all commands from the
repository root. Prerequisites: Python 3.11+, `git`; `gh` v2+ for the release paths;
`pnpm` for docs. No Bash and no `jq` are required to run the ported suite (that is the point).

Runner gate shorthand:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < <request.json>
```

---

## US1 — Cross-platform Python suite orchestrator

**Goal**: the full deterministic suite runs from Python with the bash runner's flags,
headline, and exit codes.

```text
python3 tests/speckit-pro/run-all.py --all
python3 tests/speckit-pro/run-all.py --layer 1
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-toolchain-preflight.json
```

**Expected**: `--all` ends with `speckit-pro test suite: X/Y passed` and exit 0 (matching the
recorded bash-runner behavior); `--layer 1` selects the same scope the bash `--layer 1` did;
the shipped suite gate resolves its layer roster from `tests/speckit-pro/suite-manifest.json`
(not by parsing any bash runner) with its envelope contract unchanged. Verify on a machine
with no Bash and no `jq` present (SC-002). See `contracts/suite-manifest.schema.json`.

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

**Expected**: the workflow triggers on runner/gate/workflow path changes (and manual dispatch)
but NOT on a docs-only PR that touches none of those paths; Linux amd64/arm64 container jobs
report as required (gating) checks; Windows x64/ARM64 smoke jobs run `continue-on-error` and
never block a merge; every job uploads an availability/smoke evidence artifact; an unavailable
or public-preview Windows label records its availability without blocking (SC-008).

---

## US5 — Public-readable GitHub Release Highlights

**Goal**: the composer rewrites the Release body with plain-English Highlights + a
conventional-commit appendix.

```text
python3 scripts/compose-release-notes.py --tag <new_tag> --prev-tag <prev_tag> --dry-run
```

**Expected**: the composed body opens with a plain-English Highlights section harvested from
PR `release-note` blocks (skip-labeled PRs omitted; missing-block feat/fix PRs degrade to
de-prefixed titles; zero blocks → all degrade gracefully), with the original conventional-commit
list preserved below as an appendix; deterministic stdlib only, no LLM, no new secret;
CHANGELOG.md is untouched. Re-running reproduces a byte-identical body (idempotent from the
`body` output). Fails loud on a Compare API error, a truncated/paginated response, or a commit
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
interpolation. It is a NEW required status check — PR 12 calls out the manual branch-protection
addition and creates the `release-note/skip` label (SC-006). See
`contracts/release-note-block.contract.md` §6.

---

## US7 — Restored spec-size estimator

**Goal**: `estimate-spec-size` returns a populated `{estimated_loc, suggested_slices, status}`.

```text
PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/estimate-spec-size/requests/typical-under.json
```

**Expected**: the size signals grill-me/speckit-prd send (`user_stories`/`files`/`frs`) return
a populated result matching the golden fixtures (`--files 20` → `{estimated_loc: 800,
suggested_slices: 2, status: "warn"}`; bad input coerces to `{0, 1, "ok"}`), restoring
pre-XPLAT-009 scoping behavior (SC-007). See `contracts/estimate-spec-size.schema.json`.

---

## Full-suite gate (before/after any change)

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/requests/run-default-suite.json
pnpm --dir docs-site validate
git ls-files '*.sh' | grep -v '^\.github/workflows/' | grep -v '^\.specify/'   # expect empty after PR 10
```

**Expected**: default-suite gate PASS; docs validation PASS; the final `git ls-files` check
returns nothing once the stack lands (every remaining `.sh` is either `.github/workflows/`
dispatch glue or one of the 10 allowlisted `.specify/**` vendored helpers). Shipped-runner
changes (PRs 2/10/13) additionally require the payload/proof regeneration ritual with
release-readiness evidence regenerated LAST and home-directory sanitization.
