# Runtime Decision: XPLAT-002

Status: Amended 2026-06-28; runtime model selected
Date: 2026-06-26; amended 2026-06-28

## Decision

Select a Python standard-library runner aligned with the official Spec Kit /
`specify` prerequisite boundary. SpecKit-Pro may require a healthy official
Spec Kit installation, including Python 3.11+ and a working `specify` command,
because those are user prerequisites for the product. The runner must not
require Bash, Git Bash, WSL, `jq`, PowerShell scripts, Go, Rust, Zig, Node,
`pip install`, virtualenv restoration, network package restoration, or
plugin-only third-party Python packages after the plugin is installed.

The canonical command contract remains `speckit-pro-runner`. XPLAT-004 owns the
exact launcher shape, but the implementation target is a Python source runner
using the standard library. Launch may use a discovered Python interpreter,
`py -3.11`, `python3`, or `python`, as verified by preflight; helper logic must
live in Python, not in platform shell or PowerShell scripts.

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

## Amendment Rationale

The original 2026-06-26 decision selected Go because Python was evaluated only
against what Claude Code and Codex plugin platforms guarantee by themselves.
That was too narrow for SpecKit-Pro. SpecKit-Pro is an extension of official
Spec Kit workflows, and a working `specify` CLI is a product prerequisite. The
official Spec Kit prerequisite boundary gives XPLAT a documented Python 3.11+
floor that users already accept before using SpecKit-Pro.

This changes the least surprising user journey: users install Spec Kit once,
then SpecKit-Pro reuses that Python/specify environment instead of shipping
extra per-platform binaries or asking users to understand Go/Rust/Zig artifact
distribution.

The original Go-native evidence remains useful only as historical rejected
analysis explaining why the decision changed. Because SpecKit itself requires
Python, Go/Rust/Zig/native binaries are not XPLAT fallbacks, compatibility
adapters, or contingency plans.

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
| Python standard-library runner | Runtime model is viable because official Spec Kit / `specify` is a product prerequisite and requires Python 3.11+. Actual cache invocation remains an XPLAT-004 proof item because this spec does not build the runner. | 82/100 | Selected |
| Small per-platform native binary implemented in Go | Rejected for XPLAT because it creates a second implementation toolchain and artifact-distribution burden that the official Spec Kit Python prerequisite makes unnecessary. | 74/100 | Rejected historical candidate |

## Gate Results

| Gate | JavaScript/TypeScript | Python | Native binary (rejected evidence only) |
|---|---|---|---|
| Installed-cache invocation | Fail for source JS/TS: local Node exists, but plugin platform docs and manifests do not guarantee Node on every user host; cache probe cannot run because no runner exists. | Viable with prerequisite preflight: official Spec Kit / `specify` is a product prerequisite and requires Python 3.11+, but actual installed-cache runner proof remains deferred to XPLAT-004. | Rejected: packaged executable needs no post-cache runtime install, but adds a second distribution model XPLAT does not need. |
| Native platform behavior | Pass for Node runtime family, but selected package would still depend on Node availability or become a binary bundle. | Pass with preflight: Python standard-library path, JSON, and subprocess APIs cover Windows, macOS, and Linux; XPLAT-004 must verify Windows launcher discovery. | Rejected despite native capability because it duplicates the Python prerequisite path. |
| Filesystem and paths | Pass: Node `path` APIs and local probe handled spaces and Windows basename parsing. | Pass: Python `pathlib`/`ntpath` and local probe handled spaces and Windows basename parsing. | Historical evidence: Go `path/filepath` is standard-library path handling for native OS paths, but native binaries are rejected for XPLAT. |
| JSON handling | Pass: `JSON.parse`/`JSON.stringify`; local probe emitted JSON stdout. | Pass: Python `json`; local probe emitted JSON stdout. | Historical evidence: Go `encoding/json` is standard library, but native binaries are rejected for XPLAT. |
| Subprocess behavior | Pass: `child_process.spawnSync` with `shell:false`; local probe separated stdout/stderr. | Pass: `subprocess.run(..., shell=False)`; local probe separated stdout/stderr. | Historical evidence: Go `os/exec` uses argv-style execution, but no XPLAT spec may consume this as runner input. |
| Packaging/update path | Gap/fail for source JS/TS because `node_modules`, `npm install`, or bundled Node would add post-cache setup or binary supply-chain work. | Pass if stdlib-only: generated payload carries Python source; user prerequisite supplies Python/specify; no plugin runtime package restoration is allowed. | Rejected: generated payload would need platform artifacts, checksums, and binary release discipline that XPLAT avoids. |

## Tie-Breaker

Candidates are "otherwise close" only when they have no selection-blocking gate
failure and weighted totals differ by five points or less, or when the lead is
only maintainer ergonomics or adapter cost while reliability ties or favors
another option.

No tie-breaker is needed after the amendment. Python no longer has a
selection-blocking runtime-availability failure because SpecKit-Pro can require
the official Spec Kit / `specify` prerequisite boundary. Go is rejected for this
XPLAT lane because it adds artifact distribution burden without improving the
SpecKit-centered user journey.

## Rejections

JavaScript/TypeScript is rejected as the canonical runtime package because the
reliable installed-cache form would either require `node` on PATH after install
or require bundling a Node executable. The first violates the no per-user setup
gate; the second moves the candidate into native-binary packaging with a larger
embedded runtime and supply-chain burden. Local Node behavior remains useful
for tests, generators, and possible build tooling, not as the installed runner
runtime.

Python package restoration remains rejected. The selected model is not
`pip install`, virtualenv restoration, embedded Python, or a plugin-only Python
dependency graph. It is a Python standard-library runner launched through the
official Spec Kit prerequisite boundary and verified by preflight.

Go is rejected for the XPLAT lane because it requires a new maintainer build
toolchain, per-platform artifact matrix, and consumer-local artifact
verification story that is unnecessary once the Python/specify prerequisite is
accepted. Go/Rust/Zig/native binaries are not XPLAT fallbacks.

## Evidence Gaps

| Gap | Effect | Owner / expiry |
|---|---|---|
| No actual Python runner source or launcher exists in the local Claude cache at `~/.claude/plugins/cache/racecraft-public-plugins/speckit-pro/2.16.0/`. | Actual Claude installed-cache invocation cannot be marked as a probe pass in XPLAT-002. | XPLAT-004 must add the runner source/launcher and run the cache invocation probe before implementation acceptance. |
| No actual Python runner source or launcher exists in the local Codex cache at `~/.codex/plugins/cache/racecraft-plugins-public/speckit-pro/2.16.0/`. | Actual Codex installed-cache invocation cannot be marked as a probe pass in XPLAT-002. | XPLAT-004 must add the runner source/launcher and run the cache invocation probe before implementation acceptance. |
| Windows Python launcher and installed-cache invocation are not yet proven. | Python is selected by prerequisite boundary, but actual Claude/Codex installed-cache runner launch still needs platform proof. | XPLAT-004 must implement preflight discovery and prove `py -3.11`, `python3`, or `python` launch from installed caches on Windows, macOS, and Linux. |

No documentation/probe conflicts remain for the selected model. Local Python
availability alone was not enough evidence, but the official Spec Kit
prerequisite boundary changes Python from an incidental host runtime into an
explicit product prerequisite that XPLAT-004 must preflight.

## Downstream Handoff

- XPLAT-003: decide first-release and deferred controls for a Python
  standard-library runner, including source integrity, generated-payload
  integrity, prerequisite diagnostics, consumer-local verification, and truthful
  public claims.
- XPLAT-004: build the Python runner and launcher/preflight path, implement the
  JSON/stderr/exit/path/subprocess contract, verify Python 3.11+ and `specify`,
  avoid PowerShell/Bash helper logic, and prove installed Claude/Codex cache
  invocation on Windows, macOS, and Linux.
- XPLAT-005: port read-only/advisory helpers after the runner foundation exists.
- XPLAT-006: port mutation, install, apply, PR-emission, and rollback-safe
  helpers after the runner foundation exists.
- XPLAT-007: cut over generated Claude/Codex payloads and update public support
  claims only after native release-readiness validation passes.
