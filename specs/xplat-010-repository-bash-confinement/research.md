# Phase 0 Research: Repository Bash Confinement and CI Dispatch Guard

The spec is final through Clarify (12 ratified Clarifications across 3 sessions) with zero
unresolved clarification markers. This document resolves the items the Clarify sessions and
the workflow's plan inputs **explicitly deferred to Plan**, and records the grounding
corrections surfaced by reading the actual runner code. Format: Decision / Rationale /
Alternatives considered.

---

## D1. FR-002 invocation vocabulary resolves to the literal `bash`/`jq` command-name pair

**Decision**: The confinement guard's active-invocation detection uses a **bash-scoped**
command-name set — `{"bash", "bash.exe", "jq", "jq.exe"}` — defined locally in
`active_path_guard.py` for the new operation. It does **not** reuse the module-level
`PROHIBITED_COMMAND_NAMES` (which also contains `wsl`/`powershell`/`pwsh` and their `.exe`
forms) nor `SHELL_RUNTIME_COMMAND_NAMES` (`sh`/`zsh`).

**Rationale**: Clarify S2-Q2 ratified bash-scoping and flagged this pairing for Plan. The
allowlist predicate already permits only `.specify/**/scripts/bash/**` paths, which
structurally cannot admit the sibling `.../scripts/powershell/**` tree; inheriting the
superset would flag the 4 vendored `.ps1` counterparts with no allowlist scope able to
admit them, contradicting FR-003's "exactly the 10." Scoping to `bash`/`jq` costs zero
false negatives for this repo's policy (Bash-family + `jq` only) while keeping the
allowlist at exactly 10.

**Alternatives considered**: (a) Reuse `PROHIBITED_COMMAND_NAMES` — rejected: forces
phantom `.ps1` allowlist entries and permanently contradicts FR-003. (b) A configurable
command set — rejected (YAGNI): one policy, one call site.

---

## D2. Bash-scoped suffix + shebang vocabulary (own set, not `PROHIBITED_SCRIPT_SUFFIXES`)

**Decision**: The new operation detects `.sh`/`.bash` suffixes plus a Bash-family shebang
(`bash` or POSIX `sh`, including bare `#!/bin/sh`), using its own suffix tuple
`(".sh", ".bash")` and a shebang normalizer that treats `#!/bin/sh` as in-scope. It does
**not** reuse `PROHIBITED_SCRIPT_SUFFIXES = (".sh", ".bash", ".zsh", ".ps1", ".bat",
".cmd")`.

**Rationale**: FR-001/SC-001 restrict the vocabulary to bash-family. `.ps1`/`.bat`/`.cmd`/
`.zsh` are explicitly out of scope; the 4 vendored `.ps1` are never in the detection set at
all (not merely excluded). `#!/bin/sh` is normalized alongside `bash` — a no-op today (all
10 vendored `.sh` use `#!/usr/bin/env bash`) that closes a future dodge at zero present cost.

**Alternatives considered**: Reuse the XPLAT-009 superset — rejected for the same
allowlist-arithmetic reason as D1.

---

## D3. Per-layer dispatch-kind assignment in the suite manifest

**Decision**: Manifest `dispatch` values per layer:

| Layer | dispatch | Notes |
|-------|----------|-------|
| toolchain | `internal-check` | `counted_in_total: false`; stays `check_toolchain` in-process |
| 1, 4 | `python-module` | dispatched via `run-layer-scripts.py` (now manifest-driven) |
| 5 | `internal-check` | `check_layer5` **body replaced** with the real tool-scoping validator (the current native check is vacuously true), then retired to a `python-module` at PR 5 if the ported `validate-tool-scoping` lives repo-side |
| 7 | `python-module` | replay harness (PRs 7a/7b); native `check_layer7` retired at PR 7b |
| 8 | `python-module` | parity runner (PR 8); native `check_layer8` retired at PR 8 |
| 2, 3, 6 | `python-module` + `live_only: true` | live-AI eval runners (PR 9); not in the default deterministic suite |
| — | `shell-legacy-transitional` | permitted ONLY between PR 2 and a layer's port-PR boundary; none remain after PR 10 |

**Rationale**: Clarify S1-Q3 deferred the `internal-check` vs `python-module` split to Plan.
Grounding: `suite.py` today runs toolchain/5/7/8 **in-process** (`run_internal_suite_check`)
and dispatches 1/4 to `run-layer-scripts.py`. The manifest must express both dispatch kinds
so the fail-closed drift-guard test (FR-007) can assert the gate's advertised roster and
dispatch kinds match the manifest exactly. Layer 5 stays `internal-check` transitionally
because retiring `check_layer5` (PR 5) can either replace its body in-process or point at a
ported repo-side module; the manifest records whichever the PR lands.

**Alternatives considered**: All layers `python-module` — rejected: the toolchain preflight
and (transitionally) Layer 5 have no external dispatcher and are cheapest in-process; forcing
external dispatch adds subprocess churn for no benefit.

---

## D4. Suite gate reads the manifest — grounding correction on "regex-parses run-all.sh"

**Decision**: PR 2 makes the manifest the single source both readers consume:
(a) `suite.py` derives `DEFAULT_SUITE`/`EXTENDED_SUITE`/`ALLOWED_LAYERS` from the manifest,
failing closed when it is absent/unreadable (today these are **hardcoded tuples**, not a
run-all.sh parse); (b) `run-layer-scripts.py` reads the manifest's per-layer `scripts[]`
instead of text-parsing `run-all.sh` via `re.findall(r'"\$TESTS_DIR/([^"]+)"')` (today it
**does** parse run-all.sh as text — that is the real "regex-parses the bash runner" surface,
in the layer dispatcher, not in `suite.py`). A deterministic drift-guard test asserts the
gate roster + dispatch kinds equal the manifest.

**Rationale**: The design concept's "suite gate regex-parses run-all.sh" is imprecise about
which module. Reading the code: the coupling lives in `run-layer-scripts.py`; `suite.py`
hardcodes the roster. Both must move to the manifest for FR-007 to hold. `run-all.sh`
survives only as inactive `prior_gate` provenance strings in `gates/registry.py` (lines 78,
91) — those are metadata, not executed.

**Alternatives considered**: Point `suite.py` at `run-all.py` — rejected (design-concept Q2):
recreates the parse-a-script coupling the manifest removes.

---

## D5. `run-all.py` preserves the exact bash UX

**Decision**: `run-all.py` reproduces `run-all.sh` (455 lines) behavior: flags `--live`,
`--layer N`, `--integration` (= layer 7), `--all` (= all + live), `--verbose`
(`VERBOSE=true`); default run = Layers 1, 4, 5 + toolchain (skips 2/3/6/7); headline
`speckit-pro test suite: X/Y passed` (and `X/Y passed (Z failed)` on failure); exit 0 iff
no failures, 1 on failure, 2 on unknown flag. It parses each child module's `X/Y passed`
line (the same contract the shipped gate and `run-layer-scripts.py` rely on).

**Rationale**: FR-006/SC-002 require the prior runner's flags, headline, and exit codes 1:1
on any OS with Python 3.11+ and no Bash/`jq`.

**Alternatives considered**: A new CLI surface — rejected (breaks operator habits; violates
the 1:1 UX requirement).

---

## D6. Count-parity capture tooling + shared `TestResult` subclass live under `tests/speckit-pro/lib/`

**Decision**: Two net-new repo-side utilities land in PR 2 under `tests/speckit-pro/lib/`:
(1) `test_result.py` — a `unittest.TestResult` subclass overriding `addSubTest` so
`{passed}/{total}` counts every executed assertion (loop-generated **and** non-loop grouped),
reconciling names 1:1 via `subTest(msg=...)`; (2) `capture_baseline.py` — the baseline capture
tool that runs a bash script under `VERBOSE=true`, parses only lines matching
`^\s*(.+?)\s\.\.\.\s(PASS|FAIL)$`, and writes `tests/speckit-pro/parity/bash-to-python/<script>-baseline.txt`
in the frozen format (`NNN <name>` per outcome + `TOTAL: <N>`), failing loudly on an
empty/stale name.

**Rationale**: Clarify S1-Q3/S1-Q4 pinned both. Grounding: `tests/speckit-pro/lib/` currently
holds only `assertions.sh`; **no** Python module overrides `addSubTest` (all 5 pre-existing
Python modules print bare `result.testsRun`), so this is genuinely net-new — and the 5
`testsRun` modules are the ratified exemption (do not retrofit; new ports must not copy the
pattern). `tests/speckit-pro/parity/` does not exist yet and is created here. The 20+ port
consumers put the shared subclass well past the KISS three-use bar.

**Alternatives considered**: Per-module ad-hoc counting — rejected: 20+ divergent
implementations, and bare `result.testsRun` silently under-counts subTests.

---

## D7. Estimator restoration lands as a read-only helper against existing golden fixtures

**Decision**: PR 13 registers `estimate-spec-size` as a new `HelperEntry` in
`helpers/registry.py` (`{helper_id, operation, script=None-or-historical, promotion_status,
comparison_mode, authoritative_command}`) implemented via `read_only.py`
(`run_registered_helper`). Inputs carry the size signals the grill-me/speckit-prd skills send
(`user_stories`, `files`, `frs`); output is `{estimated_loc, suggested_slices, status}`.
Golden fixtures already exist at `tests/speckit-pro/unit/fixtures/estimate-spec-size/`
(`--files 20` → 800/2/warn; `--files 11` → 440/2/warn; bad input coerced to 0/1/ok) and pin
the exact formula and thresholds. Distinct from the existing `estimate-reviewable-loc` helper.

**Rationale**: FR-025/US7 and the operator directive require remediating the dogfood defect in
this spec. The runner is the shipped surface, so PR 13 also runs the payload/proof regen ritual.

**Alternatives considered**: A new gate op — rejected: the estimator is a read-only helper,
matching the callers' request shape and the existing helper registry.

---

## D8. PR 13 also fixes the manifest-version staleness (confirmed latent defect)

**Decision**: PR 13 (already a shipped-runner fix carrying the regen ritual) additionally:
(a) adds `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` to
`release-please-config.json` `extra-files` with jsonpath `$.plugin_version` (and the
matching manifest key alignment) so releases bump it; (b) replaces
`test-speckit-pro-runner.py:307` `self.assertEqual(manifest["plugin_version"], "2.17.0")`
with a version-agnostic check — assert the value matches the semver pattern **and** equals
`speckit-pro/.claude-plugin/plugin.json` `$.version`.

**Rationale**: Confirmed latent defect in the workflow's dogfood log: the manifest
self-describes `2.17.0` while the released plugin is 2.18.0 (release-please never bumps it),
and the test hardcodes the stale value — the same version-pinning anti-pattern as the
dependabot SHA-pin lesson. Functionally benign today (the release gate validates the version
*pattern*, not the value), but drifts indefinitely.

**Alternatives considered**: Chase the current value (bump to 2.18.0 by hand) — rejected:
re-introduces the same hardcode; the fix is to remove the hardcode and automate the bump.

---

## D9. Capture/composer wiring: immutable artifact, own jobs, minimal permissions

**Decision**: PR 12 adds separate `capture-release-note-inputs` and
`compose-release-notes` jobs. Both are gated on the publishing job's mapped
`speckit-pro--release_created` output; composer `needs:` publishing plus capture. Capture reads
the component tag/body outputs, Compare response, and PR bodies/labels, serializes canonical
JSON, computes its SHA-256, and uploads it once through a SHA-pinned `actions/upload-artifact`
release with v4-or-later immutable semantics. Its artifact digest and identity become composer
inputs. Composer downloads and verifies that
artifact, resolves the release by tag, and PATCHes the deterministic body without Compare/PR
re-fetches. Shallow checkouts load the stdlib script with persisted credentials disabled.

The workflow-level default is `permissions: {}`. Publishing retains the exact
`{actions: write, contents: write, pull-requests: write}` map; capture gets only
`contents: read`; composer gets only `contents: write`; PR validation independently gets only
`contents: read`. Artifact upload/download uses the Actions runtime token and adds no repository
grant.

**Rationale**: `contents: read` covers capture-time Compare and PR reads;
`contents: write` covers composer-time release lookup/update and is its complete map. All
unspecified grants remain `none`. Job-level maps do not merge with another job's permissions,
so capture/composer cannot inherit `actions: write` or `pull-requests: write`. FR-024 also
forbids `RELEASE_PLEASE_TOKEN`.
**Guard-rail:** the appendix derives only from the mapped `body` output and discovery is
Compare-API-only, so the composer does **not** depend on release-please's
`changelog-notes-type`.

**Alternatives considered**: Add capture/composition as steps in the existing `release:` job —
rejected: they would inherit `actions`/`pull-requests: write`, violating FR-024's ceiling.

---

## D10. Composer discovery, immutable replay, fallback, and audit evidence

**Decision**: Discovery walks immutable GitHub Compare API commit subjects for trailing
`(#N)` (never rendered release-body links), fetches every discovered PR, and runs one shared
extract/sanitize/non-empty pipeline over every body. A block that becomes empty after raw HTML
and image removal fails validation and defensive composition. Genuinely missing feat/fix notes,
and all non-skipped entries when no usable blocks exist, fall back to the de-prefixed Compare
commit subject — never mutable PR title — capped at 250 characters (249 and 250 unchanged;
251 truncates to 247 plus `...`).

The capture job freezes canonical Compare/PR/raw-body JSON before composition and records both
its own SHA-256 and the immutable artifact digest. A failed composer-job rerun in the same
workflow run downloads those exact bytes, never re-fetches mutable PR metadata, and PATCHes the
same body bytes. Missing, malformed, or digest-mismatched snapshots fail loud. Structured
success output and the job summary record artifact identity/digest, snapshot digest,
composed-body digest and byte count, tag range, release id, commit/PR count, and run attempt,
without logging raw PR bodies. The immutable artifact preserves the exact source/body evidence;
the published release can be re-hashed against the recorded composed-body digest.

The unpaginated Compare contract also pins GitHub's 250-commit boundary: exactly 250 is accepted
only when `total_commits` agrees; 251, a larger advertised total, or a pagination link fails
loud. Implementation assumptions remain: (a) **first-release** (no previous tag) is out of
scope; (b) previous-tag resolution assumes today's **single release component**; (c)
capture-time Compare/PR reads and composer-time release lookup/PATCH use only the built-in token
and the D9 per-job permission maps.

**Rationale**: FR-023 and the Session-3 Clarifications pin Compare discovery. The implementation
review closed four determinism gaps: raw non-empty text can sanitize to empty; PR titles and
bodies remain mutable after merge; deriving only the appendix from a stable body does not make
the whole composition idempotent; and a log that omits exact body bytes cannot audit a release
edit. Verified live in-repo: 22/22 recent merged commits carry a trailing `(#N)`.

**Alternatives considered**: Parse rendered release-body links — rejected as lossy. Use PR
titles for fallback — rejected because titles remain mutable. Re-fetch API metadata during a
failed-job retry — rejected because the same run could produce different bytes. Persist only a
digest — rejected because a digest detects drift but cannot replay the original inputs.

---

## D11. Layer-8 fixture `.sh` files convert before the guard's final deletion

**Decision**: PR 8 (Layer-8 parity port) converts the per-case `env-fallback.sh` and
`env-teams.sh` fixture scripts (8 files across 4 case dirs — the environment-selection scripts
the real validator requires) and the `jq`-dependent `run-parity-fixtures.sh` +
`lib/{extractors,judge}.sh` to Python/data, so that by PR 10 the confinement guard's live
`git ls-files -z` enumeration finds zero non-allowlisted `.sh` outside `.github/workflows/`.

**Rationale**: These fixture `.sh` live under `tests/speckit-pro/layer8-parity/**`, outside
`.github/workflows/` and off the `.specify` allowlist, so they would be blocking findings.
The atomic-swap discipline (Q3) plus PR-10-after-3–9 ordering guarantees the guard only turns
on once every surface it scans is clean.

**Alternatives considered**: Allowlist the fixture `.sh` — rejected: broadens the allowlist
beyond the ratified 10 and weakens the confinement claim for portable files.

---

## D12. Hooks and `scripts/**` port targets

**Decision**: PR 6 ports `.claude/hooks/guard-version-triplet.sh` (PreToolUse) and
`validate-structural.sh` (PostToolUse) to `.py`, preserving the stdin-JSON intake and the
exit-0 (allow/pass) / exit-2 (block) contract, replacing `jq` extraction with stdlib `json`
and — for `validate-structural` — replacing its `bash tests/run-all.sh --layer 1` shell-out
with a Python Layer-1 dispatch. Same PR ports `scripts/refresh-local-plugin.sh` (bash, no jq,
already calls `python3 build-plugin-payloads.py`) and `scripts/sync-marketplace-versions.sh`
(the 12-call `jq` holdout) to `.py`.

**Rationale**: FR-009/FR-014. The hooks are unwired today (no `.claude/settings*.json`), so the
port is zero-CI-risk and removes the `jq` dependency while keeping the guard capability ready.

**Alternatives considered**: Delete the hooks (design-concept Q4 alt) — rejected: loses the
documented version-triplet guard intent for two trivially portable files.

---

## D13. PR-stack ordering is fixed and each PR is independently CI-green

**Decision**: Encode the ratified 15-PR order and dependencies (13 numbered slices, with PR 3
and PR 7 each split into a/b review units; workflow file §Scope Budget):
PR 1 (orphan deletion + ledger) anytime; PR 2 (manifest + run-all.py + manifest-reading gate)
before 3–10; PRs 3a/3b (20 mechanical L1) and 4 (MOC + codex/payload) after 2; PR 5 (L5 +
toolchain + `pr-checks.yml:289` swap + `validate-pr-checks-sentinel` update + branch-protection
note) after 2; PR 6 (scripts + hooks) after 2; PRs 7a/7b (L7 transcript lib then runners) after
2; PR 8 (L8 parity) after 2; PR 9 (live-eval runners) after 2; PR 10 (confinement guard + final
bash deletion + release.py composition) after 3–9; PR 11 (container preflight; new required
Linux checks + branch-protection note) last among confinement PRs; PR 12 (composer + new
`validate-release-note` required check + `release-note/skip` label + PR template + composer job
+ `validate-release-workflow` update + branch-protection note) independent; PR 13 (estimator +
manifest-version fix) independent, land early.

**Rationale**: Every port swaps atomically so no layer runs with zero coverage; the guard turns
on only after every scanned surface is clean; workflow-changing PRs (5, 11, 12) update their
self-referential validators in the same PR and call out branch-protection follow-ups (PR 5
renames the docs-dispatch step; PR 11 adds required Linux preflight checks; PR 12 adds the new
required `validate-release-note` check).

**Alternatives considered**: 2–3 separate specs or fewer/larger PRs — rejected in design-concept
Q9 (scaffold overhead vs. blowing the 800-LOC block threshold).
