# Phase 1 Data Model: Repository Bash Confinement and CI Dispatch Guard

Eight entities, all repository files (no database). Schemas frozen by the spec's Key
Entities section + Clarifications; JSON/format contracts live under `contracts/`.

---

## 1. Suite Manifest

- **File**: `tests/speckit-pro/suite-manifest.json` (NEW, PR 2). **Contract**:
  `contracts/suite-manifest.schema.json`.
- **Purpose**: Single per-layer source of truth for suite composition, read by both
  `run-all.py` and the shipped suite gate (`gates/suite.py` + `run-layer-scripts.py`).
- **Fields**: top-level `{schema_version, layers[]}`. Per layer `{id, label, default,
  execution ("execute"|"print-commands"), live_only, integration, counted_in_total,
  dispatch ("python-module"|"internal-check"|"shell-legacy-transitional"), scripts[]}`.
  Per script `{path, label, baseline}` where `baseline` is a repo-relative pointer to the
  committed count-parity baseline file (the single count of record — **no** inline
  expected-count integers) or `null`.
- **Validation rules**: toolchain layer carries `counted_in_total: false`. Post-PR-2 the
  shipped gate's `DEFAULT_SUITE`/`EXTENDED_SUITE`/`ALLOWED_LAYERS` derive solely from this
  file, failing closed when it is absent/unreadable. A deterministic drift-guard test asserts
  the gate's advertised roster and dispatch kinds equal the manifest exactly (FR-007).
  `shell-legacy-transitional` is valid only between PR 2 and a layer's port-PR boundary; none
  remain after PR 10.
- **State transitions**: composition changes are manifest-only edits (no shipped-runner byte
  change) except when a layer's `dispatch` kind changes (that touches `suite.py` →
  regen ritual).

## 2. Confinement Guard Allowlist

- **File**: `tests/speckit-pro/unit/fixtures/repository-bash-confinement/allowlist.json`
  (NEW, PR 10). **Contract**: `contracts/confinement-allowlist.schema.json` (rhymes with the
  XPLAT-009 `historical-allowlist-entry.schema.json`).
- **Purpose**: Fail-closed list of exactly the 10 vendored `.specify/**` upstream Spec Kit
  helper `.sh` files, each `release_readiness_excluded: true`.
- **Fields**: `{schema_version, feature_id: "XPLAT-010", entries[]}`; per entry `{path,
  categories[], reason, scope: "vendored_specify_helper", release_readiness_excluded: true}`
  with `additionalProperties: false` and `release_readiness_excluded` required on every entry.
- **The 10 pinned paths (no globs)**:
  - `.specify/extensions/git/scripts/bash/{auto-commit,create-new-feature,git-common,initialize-repo}.sh`
  - `.specify/scripts/bash/{check-prerequisites,common,create-new-feature,setup-plan,setup-tasks,update-agent-context}.sh`
- **Validation rules**: the loader accepts only the `vendored_specify_helper` path scope
  (`.specify/scripts/bash/**` and `.specify/extensions/**/scripts/bash/**`). Any `.sh` or
  Bash-shebang file under `.specify/**` not on the list is a fail-closed blocking finding. The
  4 vendored `.specify/extensions/git/scripts/powershell/*.ps1` are outside the bash-scoped
  detection vocabulary and require no entry (the count stays exactly 10).

## 3. Count-Parity Baseline

- **Files**: `tests/speckit-pro/parity/bash-to-python/<script>-baseline.txt` (NEW, PR 2+; one per
  `(script, invocation-mode)` pair). **Contract**: `contracts/count-parity-baseline.contract.md`.
- **Purpose**: Committed per-script capture of the ordered check-name inventory + runtime
  count, proving 1:1 preservation on each port.
- **Format**: one line per executed `_pass`/`_fail` call in execution order,
  `NNN <canonical-name>` (grouped checks legitimately repeat the same name on consecutive
  lines), then a trailing `TOTAL: <N>` line where `N = PASS_COUNT + FAIL_COUNT`.
- **Validation rules**: names captured **verbatim** from runtime `VERBOSE=true` PASS/FAIL
  output (parse only `^\s*(.+?)\s\.\.\.\s(PASS|FAIL)$`), never from source literals. Capture
  environment pinned/recorded (non-root, matching CI). Runtime count granularity = per
  assertion execution (loop-generated + non-loop grouped), computed in the Python port via the
  shared `addSubTest` `TestResult` subclass. Regeneration triggers include the data files the
  script reads at runtime, not just source. Fail loud on an empty/stale name (no positional
  fallback).

## 4. Count Ledger / Suite-Parity Result

- **Files**: `docs/ai/specs/.process/XPLAT-010-count-ledger.md` (running; one delta line per
  port PR) and `docs/ai/specs/.process/XPLAT-010-suite-parity-result.json` (final cumulative).
- **Purpose**: Cumulative name-and-count parity evidence across the PR stack (FR-013).
- **Fields (result JSON)**: per-script `{script, mode, bash_count, python_count, names_equal,
  intentional_change}` rows + a suite-level roll-up asserting zero drops/renames (SC-003).
- **Validation rules**: each port PR appends its delta line; the final result asserts
  `bash_count == python_count` and `names_equal == true` for every ported script.

## 5. Disposition Ledger

- **File**: `docs/ai/specs/.process/XPLAT-010-deleted-tests-ledger.md` (NEW, PR 1).
- **Purpose**: Committed record of the 34 removed orphan Bash tests + rationale for deleting
  rather than porting each (FR-016).
- **Fields**: per file `{path, kind ("orphan-target-deleted"|"redundant-wrapper"), rationale}`.
- **Content**: 32 target-deleted orphans (Layer-4 `test-*.sh` whose target under
  `speckit-pro/**` was already ported+deleted by XPLAT-009) + 2 redundant wrappers
  (`test-speckit-pro-runner.sh`, `test-speckit-pro-read-only-helpers.sh` — pure `python3 …`
  shims around shipped `.py`). Git history preserves content; the 12 genuinely active Layer-4
  `.sh` are ported, not deleted.

## 6. Release Note Block

- **Home**: authored in each feat/fix PR body; seeded by `.github/pull_request_template.md`
  (NEW, PR 12). **Contract**: `contracts/release-note-block.contract.md`.
- **Purpose**: Consumer-facing block harvested by the composer at release time.
- **Grammar**: exactly one fenced code block, info-string `release-note`, identified by
  CommonMark-nesting-aware fence matching; multiline plain-English prose; inline markdown
  limited to emphasis, plain inline links, and `-` bullets; raw HTML + image markdown stripped
  at composition; leading structural chars (`-`, `*`, `#`) neutralized; capped 2,000 chars
  (truncate-and-mark, not a failure); empty/whitespace-only = missing; skip only via the
  `release-note/skip` label.
- **Validation rules**: `validate-release-note` fails feat/fix PRs missing the block (zero or
  >1 block fails); the composer harvests defensively from every merged PR since the last tag.

## 7. Container-Preflight Evidence Artifact

- **Home**: uploaded by the preflight jobs in `.github/workflows/container-preflight.yml`
  (NEW, PR 11); not a repository source file.
- **Purpose**: Per-platform availability + smoke-result evidence (FR-020).
- **Fields**: per job `{platform (linux/amd64|linux/arm64|windows-x64|windows-arm64),
  runner_label, available (bool), gate_role ("required"|"advisory"), smoke_result, entrypoints}`.
- **Validation rules**: Linux amd64/arm64 jobs are required (gating) on the paths they trigger;
  Windows jobs are `continue-on-error` advisory with runner availability recorded per label; an
  unavailable/public-preview Windows label records availability and blocks no merge. Never
  treated as native installed-plugin UAT evidence (XPLAT-008 remains the release-claim gate).

## 8. Spec-Size Estimate

- **Runner op**: `estimate-spec-size` read-only helper (NEW, PR 13; `helpers/registry.py` +
  `read_only.py`). **Contract**: `contracts/estimate-spec-size.schema.json`. **Golden
  fixtures**: `tests/speckit-pro/unit/fixtures/estimate-spec-size/` (already present).
- **Purpose**: Restore the scoping estimator the grill-me/speckit-prd skills call (FR-025/US7).
- **Fields**: inputs = size signals `{user_stories, files, frs}` (lenient coercion of
  non-numeric/negative); result = `{estimated_loc (int ≥ 0), suggested_slices (int ≥ 1),
  status ("ok"|"warn")}`.
- **Validation rules**: matches the pre-XPLAT-009 contract the callers expect; the golden
  fixtures pin the formula and warn threshold (`--files 20` → 800/2/warn; bad input →
  0/1/ok). Distinct from the existing `estimate-reviewable-loc` helper.
