# Runtime Decision: XPLAT-002

Status: In Review (PR #266 pending merge); runtime model selected
Date: 2026-06-26

## Decision

Select a small per-platform native binary runner implemented in Go with the Go
standard library. The canonical command contract is `speckit-pro-runner`,
resolved from the installed plugin payload at `scripts/speckit-pro-runner`.

XPLAT-002 does not implement the runner, port helpers, change active installed
invocation paths, rebuild generated payloads, or make public native-platform
support claims.

## Sources

- Runtime rubric: `docs/ai/research/cross-platform-runtime-inventory.md`
- Roadmap: `docs/ai/specs/cross-platform-plugin-runtime-technical-roadmap.md`
- Design concept: `docs/ai/specs/.process/XPLAT-002-design-concept.md`
- Contract: `specs/xplat-002-runtime-implementation-options-contract-decision/contracts/speckit-pro-runner-contract.md`
- Evidence records:
  - `evidence/javascript-typescript.md`
  - `evidence/python.md`
  - `evidence/small-per-platform-binary.md`

## Decision Boundaries

- No `speckit-pro-runner` implementation is added.
- No Bash helpers are ported.
- No active Claude or Codex invocation paths are changed.
- No broad generated payloads are rebuilt.
- No README, docs-site, marketplace metadata, changelog, release-note, or
  public native-support claim is changed.
- XPLAT-003 receives supply-chain implications only; no controls are selected.

## Rubric

Must-have gates from XPLAT-001:

| Gate | Required result |
|---|---|
| Installed-cache invocation | Runs from installed Claude and Codex plugin cache paths without a source checkout. |
| Native platform behavior | Runs on native Windows, macOS, and Linux without Bash, Git Bash, WSL, PowerShell-only behavior, or `jq`. |
| Filesystem and paths | Handles repo, plugin, cache, absolute, and temp paths, including spaces and Windows separators. |
| JSON handling | Parses and emits JSON without shelling to `jq`. |
| Subprocess behavior | Runs subprocesses with structured argv, captured stdout/stderr/exit, timeouts, and missing-command diagnostics. |
| Packaging and update path | Fits the public plugin payload/update path without post-cache dependency installation. |

Weighted criteria total 100 points: native platform behavior 20,
installed-cache reliability 15, dependency/bootstrap burden 15,
packaging/distribution 15, offline/update behavior 10, diagnostics 10,
maintainer ergonomics 10, compatibility/migration cost 5.

The accepted setup reviewability warning remains in force: two primary
surfaces (`docs/process`, `harness/adapter`), no blockers, one decision spike.

## Candidate Comparison

| Candidate | Gate result | Weighted score | Decision |
|---|---:|---:|---|
| JavaScript/TypeScript on Node.js | Fails selected-runtime gate unless Node or a bundled Node executable is guaranteed in the installed payload. | 68/100 | Rejected |
| Python | Fails selected-runtime gate unless Python or a bundled Python runtime is guaranteed in the installed payload. | 48/100 | Rejected |
| Small per-platform native binary implemented in Go | Runtime model is viable because the installed payload can ship the executable artifact with no user-side runtime install. Actual cache invocation remains an XPLAT-004 proof item because this spec does not build the runner. | 87/100 | Selected |

## Gate Results

| Gate | JavaScript/TypeScript | Python | Go native binary |
|---|---|---|---|
| Installed-cache invocation | Fail for source JS/TS: local Node exists, but plugin platform docs and manifests do not guarantee Node on every user host; cache probe cannot run because no runner exists. | Fail: local Python exists, but Python is not guaranteed by the plugin platforms; cache probe cannot run because no runner exists. | Runtime model viable: packaged executable needs no post-cache runtime install; actual installed-cache runner probe deferred to XPLAT-004 and not counted as passed in XPLAT-002. |
| Native platform behavior | Pass for Node runtime family, but selected package would still depend on Node availability or become a binary bundle. | Gap/fail for installed plugin default because Python availability varies by host and Windows install state. | Pass for per-platform native artifacts when XPLAT-004 builds the declared platform matrix. |
| Filesystem and paths | Pass: Node `path` APIs and local probe handled spaces and Windows basename parsing. | Pass: Python `pathlib`/`ntpath` and local probe handled spaces and Windows basename parsing. | Pass: Go `path/filepath` is standard-library path handling for native OS paths. |
| JSON handling | Pass: `JSON.parse`/`JSON.stringify`; local probe emitted JSON stdout. | Pass: Python `json`; local probe emitted JSON stdout. | Pass: Go `encoding/json` is standard library. |
| Subprocess behavior | Pass: `child_process.spawnSync` with `shell:false`; local probe separated stdout/stderr. | Pass: `subprocess.run(..., shell=False)`; local probe separated stdout/stderr. | Pass: Go `os/exec` uses argv-style execution; XPLAT-004 must fixture nonzero, timeout, and missing-command cases. |
| Packaging/update path | Gap/fail for source JS/TS because `node_modules`, `npm install`, or bundled Node would add post-cache setup or binary supply-chain work. | Fail/gap because `pip install`, virtualenv, or embedded Python would add setup or binary supply-chain work. | Runtime model viable: generated payload can carry platform artifacts; XPLAT-003 must decide checksums, SBOM, provenance, and vulnerability controls. |

## Tie-Breaker

Candidates are "otherwise close" only when they have no selection-blocking gate
failure and weighted totals differ by five points or less, or when the lead is
only maintainer ergonomics or adapter cost while reliability ties or favors
another option.

No tie-breaker is needed. JavaScript/TypeScript and Python both have
selection-blocking installed-cache/runtime-availability failures for a source
runtime package. The Go native binary candidate leads by more than five points
and is the only option whose runtime model satisfies the no-post-cache-install
constraint.

## Rejections

JavaScript/TypeScript is rejected as the canonical runtime package because the
reliable installed-cache form would either require `node` on PATH after install
or require bundling a Node executable. The first violates the no per-user setup
gate; the second moves the candidate into native-binary packaging with a larger
embedded runtime and supply-chain burden. Local Node behavior remains useful
for tests, generators, and possible build tooling, not as the installed runner
runtime.

Python is rejected because it has the same installed-cache runtime issue with a
weaker default host guarantee. A source Python runner would require Python on
PATH, `pip`/virtualenv assumptions, or an embedded runtime. Those assumptions
are not acceptable for installed plugin first-run reliability.

## Evidence Gaps

| Gap | Effect | Owner / expiry |
|---|---|---|
| No actual `scripts/speckit-pro-runner` exists in the local Claude cache at `~/.claude/plugins/cache/racecraft-public-plugins/speckit-pro/2.16.0/`. | Actual Claude installed-cache invocation cannot be marked as a probe pass in XPLAT-002. | XPLAT-004 must add the runner artifact and run the cache invocation probe before implementation acceptance. |
| No actual `scripts/speckit-pro-runner` exists in the local Codex cache at `~/.codex/plugins/cache/racecraft-plugins-public/speckit-pro/2.16.0/`. | Actual Codex installed-cache invocation cannot be marked as a probe pass in XPLAT-002. | XPLAT-004 must add the runner artifact and run the cache invocation probe before implementation acceptance. |
| Go toolchain is not installed on this host (`go version` failed with command not found). | Local Go build-tool probing is unavailable; this does not affect post-cache runtime because users will receive a built executable. | XPLAT-004 build environment must install/pin Go after XPLAT-003 chooses controls. |

No documentation/probe conflicts were found. The only conflicts are scope
boundaries: local runtime availability proves this host can run Node/Python, but
does not prove every installed plugin host can run Node/Python after cache
population.

## Downstream Handoff

- XPLAT-003: decide first-release and deferred controls for native executable
  artifacts, including checksums, signatures, SBOM/provenance, vulnerability
  scanning, generated-payload integrity, and consumer-local verification.
- XPLAT-004: build `scripts/speckit-pro-runner` as Go native artifacts for the
  supported platform matrix, implement the JSON/stderr/exit/path/subprocess
  contract, and prove installed Claude/Codex cache invocation.
- XPLAT-005: port read-only/advisory helpers after the runner foundation exists.
- XPLAT-006: port mutation, install, apply, PR-emission, and rollback-safe
  helpers after the runner foundation exists.
- XPLAT-007: cut over generated Claude/Codex payloads and update public support
  claims only after native release-readiness validation passes.
