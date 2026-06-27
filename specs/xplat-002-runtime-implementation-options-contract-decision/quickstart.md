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
- The Go runtime model is selected as viable for no post-cache setup; actual
  installed Claude/Codex cache invocation proof is deferred to XPLAT-004 because
  XPLAT-002 does not build `speckit-pro-runner`.
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

Expected: pass or warn with no blockers, or an honored named `infra` exception
whose overage is limited to XPLAT PR-packet tooling support plus synced payload
mirrors.

```bash
git diff --name-only
git diff --check
bash tests/speckit-pro/run-all.sh --layer 1
```

Expected: scope limited to XPLAT-002 feature artifacts and deterministic layer 1
passes.

## 5. Recorded Results

Reviewability-Exception: infra

The final PR includes a small PR-packet tooling fix so XPLAT-scoped specs can
generate and validate `feat(XPLAT-*)` pull request titles. This is infrastructure
support for the XPLAT-002 closeout path, not runtime implementation work.

Infra exception manual audit trail: source PR tooling
`speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh`, its
Claude/Codex generated payload mirrors, and
`tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh` are included only
to make XPLAT PR packet generation reviewable and reproducible. The gate's
`reviewable_loc=0` and `production_files=0` output is preserved as tool output;
this manual note names the script and test surfaces covered by the honored
`infra` exception.

| Check | Result |
|---|---|
| Marker count | Passed: `{"type":"gaps","total":0,"spec":0,"plan":0,"checklists":0,"details":[]}` |
| Spec index | Regenerated after adding decision artifacts, then passed: `spec-index: index current — all in-scope maps up to date.` |
| Reviewability gate | Exception/pass: `reviewable_loc=0`, `production_files=0`, `total_files=33`, `primary_surface_count=5`, `primary_surfaces=["API","docs/process","other","scheduler/runtime","seed/config"]`; infra exception honored for XPLAT PR packet tooling support and generated payload mirrors. |
| `git diff --name-only origin/main...HEAD` | Tracked diff includes XPLAT-002 workflow and feature artifacts, roadmap/spec-map refreshes, PR packet title tooling/tests, and Claude/Codex payload mirrors for XPLAT scope support. |
| Scope review | Passed with infra exception: no README, docs-site runtime, marketplace metadata, changelog, release notes, active installed runtime invocation paths, or public support-claim surfaces changed; generated payload changes are limited to the two synced PR tooling scripts. |
| `git diff --check` | Passed with no whitespace errors. |
| Layer 1 structural suite | Passed: `bash tests/speckit-pro/run-all.sh --layer 1` reported `1438/1438 passed`. |
| Focused PR tooling tests | Passed: `test-generate-pr-body` reported `97/97`; `test-validate-pr-workflow-contract` reported `17/17`. |
| Broader shell suite | Attempted: focused payload determinism now passes, but `bash tests/speckit-pro/run-all.sh` remains blocked by baseline DOC-014 privacy-scan terms already present on `origin/main`. |

Supplemental non-mutating probes recorded in evidence:

- `node --version` -> `v26.0.0`
- Node JSON/path/stderr/subprocess probe -> pass
- `python3 --version` -> `Python 3.11.0`
- Python JSON/path/stderr/subprocess probe -> pass
- `go version` -> unavailable on this host (`command not found`)
- Installed Claude and Codex cache roots exist for `speckit-pro/2.16.0`, but
  `scripts/speckit-pro-runner` is absent by design because XPLAT-002 does not
  implement the runner.
