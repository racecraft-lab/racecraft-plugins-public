# Evidence: Small Per-Platform Binary Runtime Candidate

Candidate status: Selected runtime model; installed-cache invocation proof deferred to XPLAT-004
Selected implementation runtime: Go native executable using the Go standard
library
Captured: 2026-06-26

## Evidence Standard

This record evaluates the binary candidate as a small native CLI artifact
packaged into the installed plugin payload. XPLAT-002 selects the runtime model
and command contract; XPLAT-004 must build the executable and prove actual
installed-cache invocation.

## Official / Runtime Documentation

- Go installation/source environment and target controls:
  `https://go.dev/doc/install/source#environment`
- Go `encoding/json`: `https://pkg.go.dev/encoding/json`
- Go `os/exec`: `https://pkg.go.dev/os/exec`
- Go `path/filepath`: `https://pkg.go.dev/path/filepath`
- Go `runtime`: `https://pkg.go.dev/runtime`
- OpenAI Codex plugin marketplace/cache documentation:
  `https://developers.openai.com/codex/plugins/build#how-codex-uses-marketplaces`
- Claude Code plugin marketplace documentation:
  `https://code.claude.com/docs/en/plugin-marketplaces`

## Repo-Local Evidence

- `.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json`
  prove generated payloads are the install source for Codex and Claude.
- Local installed caches exist:
  - `~/.claude/plugins/cache/racecraft-public-plugins/speckit-pro/2.16.0/`
  - `~/.codex/plugins/cache/racecraft-plugins-public/speckit-pro/2.16.0/`
- XPLAT-001 rows `SRC-READ-001`, `SRC-MUT-001`, and `GEN-ACT-001` define the
  active runtime surfaces that later specs must port or cut over.

## Probe Evidence

| Probe | Command | Result | Scoring effect |
|---|---|---|---|
| Build-tool availability | `go version` | Gap on this host: `command not found`. | Does not block selected installed runtime; XPLAT-004 build environment must pin/install Go after XPLAT-003 controls. |
| Claude installed-cache root | `ls -la ~/.claude/plugins/cache/racecraft-public-plugins/speckit-pro/2.16.0` | Passed: cache root exists with payload directories. | Confirms target cache shape, not runner invocation. |
| Codex installed-cache root | `ls -la ~/.codex/plugins/cache/racecraft-plugins-public/speckit-pro/2.16.0` | Passed: cache root exists with payload directories. | Confirms target cache shape, not runner invocation. |
| Claude installed-cache runner | `ls -la ~/.claude/plugins/cache/racecraft-public-plugins/speckit-pro/2.16.0/scripts/speckit-pro-runner` | Gap: file missing because XPLAT-002 must not implement the runner. | XPLAT-004 must prove actual invocation. |
| Codex installed-cache runner | `ls -la ~/.codex/plugins/cache/racecraft-plugins-public/speckit-pro/2.16.0/scripts/speckit-pro-runner` | Gap: file missing because XPLAT-002 must not implement the runner. | XPLAT-004 must prove actual invocation. |

## Evidence Gaps

| Missing probe | Scope | Reason unavailable | Substitute evidence | Effect | Owner / expiry |
|---|---|---|---|---|---|
| Installed Claude cache invocation of native `speckit-pro-runner` | Claude cache on this macOS host | Runner is intentionally not implemented. | Cache root exists; contract path is `scripts/speckit-pro-runner`; runtime model has no post-cache interpreter dependency. | Runtime model viable; actual invocation proof deferred and not counted as a probe pass. | XPLAT-004 must run after adding runner. |
| Installed Codex cache invocation of native `speckit-pro-runner` | Codex cache on this macOS host | Runner is intentionally not implemented. | Cache root exists; OpenAI docs define installed cache path; runtime model has no post-cache interpreter dependency. | Runtime model viable; actual invocation proof deferred and not counted as a probe pass. | XPLAT-004 must run after adding runner. |
| Go build toolchain on this host | Maintainer/build environment | `go` is not installed locally. | Official Go docs cover build target environment; XPLAT-004 can establish build environment. | Reduces maintainer ergonomics score only. | XPLAT-004/XPLAT-003. |

## Gate Results

| Gate | Result | Rationale |
|---|---|---|
| Installed-cache invocation | Runtime model viable; invocation proof deferred | A compiled executable in the payload can run without user-side `npm`, `pip`, `uv`, `brew`, Node, Python, Bash, or `jq`. Actual cache invocation requires the XPLAT-004 artifact and is not counted as passed in XPLAT-002. |
| Native platform behavior | Pass | Per-platform artifacts can target Windows, macOS, and Linux. |
| Filesystem and paths | Pass | Go `path/filepath` and `os` APIs support native path semantics. |
| JSON handling | Pass | Go `encoding/json` is standard library. |
| Subprocess behavior | Pass | Go `os/exec` supports structured argv-style process execution without shell contract fallback. |
| Packaging/update path | Pass with XPLAT-003 controls pending | Payload can carry executable artifacts; XPLAT-003 must choose integrity and provenance controls before XPLAT-004 ships them. |

## Weighted Score

The installed-cache invocation reliability score reflects no-post-cache-install
runtime-model viability only. XPLAT-004 must replace that model score with
actual Claude and Codex installed-cache invocation proof before implementation
acceptance.

| Criterion | Weight | Rating | Points |
|---|---:|---:|---:|
| Native platform behavior | 20 | 5 | 20 |
| Installed-cache invocation reliability | 15 | 4 | 12 |
| Dependency footprint and bootstrap burden | 15 | 5 | 15 |
| Packaging/distribution model | 15 | 4 | 12 |
| Offline behavior and update path | 10 | 5 | 10 |
| Diagnostics and error reporting | 10 | 4 | 8 |
| Maintainer ergonomics | 10 | 3 | 6 |
| Compatibility adapters and migration cost | 5 | 4 | 4 |
| **Total** | **100** |  | **87** |

## Supply-Chain Implications for XPLAT-003

- Evidence-backed: Go standard library can cover JSON, path, subprocess, and
  runtime-info needs without third-party runtime dependencies.
- Unverified: exact build matrix, checksum/signature publication, SBOM,
  provenance/attestation, vulnerability-scan command, and generated-payload
  integrity policy.
- Risk: native executables increase artifact verification responsibility even
  though they remove user-side runtime bootstrap risk.
