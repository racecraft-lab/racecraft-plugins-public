# Quickstart: Review XPLAT-002

This guide validates the completed runtime decision spike. It does not run or
implement `speckit-pro-runner`.

## 1. Review Order

1. `runtime-decision.md`
2. `evidence/javascript-typescript.md`
3. `evidence/python.md`
4. `evidence/small-per-platform-binary.md`
5. `contracts/speckit-pro-runner-contract.md`
6. `handoff.md`
7. `SPEC-MOC.md`
8. `tasks.md`

## 2. Decision Checklist

- Exactly one runtime is selected: Go-backed small per-platform native binary.
- JavaScript/TypeScript, Python, and small per-platform binary candidates are
  evaluated against the same XPLAT-001 gates and weights.
- Rejected candidates include gate and score rationale.
- Installed-cache probe gaps are recorded without being counted as probe
  passes.
- Contract still defines `speckit-pro-runner` at
  `scripts/speckit-pro-runner`.
- The contract includes JSON stdin/stdout, line-delimited JSON stderr,
  exit-code map, path rules, shell-disabled subprocess rules, prerequisite
  reporting, runtime-info/preflight, and fixture expectations.
- XPLAT-003 receives implications only, not selected controls.
- XPLAT-004 receives the selected runtime, command contract, fixture
  expectations, XPLAT-001 row-derived inputs, and temporary adapter records.
- README, docs-site, marketplace metadata, changelog, release notes, public
  support claims, active installed invocation paths, and broad generated
  payloads remain unchanged.

## 3. Evidence Gaps

| Gap | Fallback |
|---|---|
| Local Claude cache has no `scripts/speckit-pro-runner` because XPLAT-002 cannot implement it. | XPLAT-004 must add the runner artifact and run installed Claude cache invocation. |
| Local Codex cache has no `scripts/speckit-pro-runner` because XPLAT-002 cannot implement it. | XPLAT-004 must add the runner artifact and run installed Codex cache invocation. |
| `go version` is unavailable on this host. | XPLAT-004/XPLAT-003 must establish the build environment and controls; users receive built artifacts, not a Go toolchain requirement. |

## 4. Validation Commands

Run from the XPLAT-002 worktree:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh gaps specs/xplat-002-runtime-implementation-options-contract-decision
```

Expected: `"total":0`.

```bash
speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh --check "$PWD"
```

Expected: `spec-index: index current`.

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh diff origin/main...HEAD
```

Expected: pass or warn with no blockers.

```bash
git diff --name-only
git diff --check
bash tests/speckit-pro/run-all.sh --layer 1
```

Expected: scope limited to XPLAT-002 feature artifacts and deterministic layer 1
passes.

## 5. Recorded Results

| Check | Result |
|---|---|
| Marker count | Passed: `{"type":"gaps","total":0,"spec":0,"plan":0,"checklists":0,"details":[]}` |
| Spec index | Regenerated after adding decision artifacts, then passed: `spec-index: index current — all in-scope maps up to date.` |
| Reviewability gate | Warn/pass: `reviewable_loc=0`, `production_files=0`, `total_files=21`, `primary_surface_count=4`, `primary_surfaces=["API","docs/process","scheduler/runtime","seed/config"]`, warnings for total files and primary surfaces, no blockers. |
| `git diff --name-only` | Tracked diff limited to `SPEC-MOC.md`, `contracts/speckit-pro-runner-contract.md`, `quickstart.md`, and `tasks.md`. `git status --short` also shows new XPLAT-002 `evidence/`, `handoff.md`, and `runtime-decision.md` files. |
| Scope review | Passed: all changed/untracked paths are under `specs/xplat-002-runtime-implementation-options-contract-decision/`; no README, docs-site, marketplace metadata, changelog, release notes, active installed invocation paths, or broad generated payloads changed. |
| `git diff --check` | Passed with no whitespace errors. |
| Layer 1 structural suite | Passed: `bash tests/speckit-pro/run-all.sh --layer 1` reported `1438/1438 passed`. |
| Broader shell suite | Not run intentionally: no source, generator script, durable probe script, installed invocation path, or generated payload changed unexpectedly. |

Supplemental non-mutating probes recorded in evidence:

- `node --version` -> `v26.0.0`
- Node JSON/path/stderr/subprocess probe -> pass
- `python3 --version` -> `Python 3.11.0`
- Python JSON/path/stderr/subprocess probe -> pass
- `go version` -> unavailable on this host (`command not found`)
- Installed Claude and Codex cache roots exist for `speckit-pro/2.16.0`, but
  `scripts/speckit-pro-runner` is absent by design because XPLAT-002 does not
  implement the runner.
