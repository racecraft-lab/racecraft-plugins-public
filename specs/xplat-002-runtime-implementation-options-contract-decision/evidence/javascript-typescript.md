# Evidence: JavaScript/TypeScript Runtime Candidate

Candidate status: Rejected
Captured: 2026-06-26

## Evidence Standard

This record uses the XPLAT-001 gates and weights. Installed-cache evidence is a
pass only when it proves installed Claude and Codex plugin-cache invocation.
Repo-local and generated-payload evidence is supplemental.

Evidence gaps record missing probe, scope, reason unavailable, substitute
evidence, gate/scoring effect, owner, and expiry.

## Official / Runtime Documentation

- Node.js `child_process` documentation:
  `https://nodejs.org/api/child_process.html`
- Node.js `path` documentation: `https://nodejs.org/api/path.html`
- Node.js single executable applications:
  `https://nodejs.org/api/single-executable-applications.html`
- OpenAI Codex plugin marketplace/cache documentation:
  `https://developers.openai.com/codex/plugins/build#how-codex-uses-marketplaces`
- Claude Code plugin marketplace documentation:
  `https://code.claude.com/docs/en/plugin-marketplaces`

## Repo-Local Evidence

- `.agents/plugins/marketplace.json` points Codex at
  `./dist/codex/speckit-pro`.
- `.claude-plugin/marketplace.json` points Claude at
  `./dist/claude/speckit-pro`.
- `docs/ai/research/cross-platform-runtime-inventory.md` records active source
  and generated payload rows that must stop depending on Bash, `.sh`, `jq`,
  shell quoting, and Unix paths.

## Probe Evidence

| Probe | Command | Result | Scoring effect |
|---|---|---|---|
| Runtime availability | `node --version` | Passed on this host: `v26.0.0`. | Host-local availability only; not an installed-cache guarantee. |
| JSON, stderr separation, paths, subprocess | `node -e '...'` supplemental probe | Passed: JSON stdout parsed, line-delimited JSON stderr preserved, path with spaces retained, Windows basename parsed, child process exited 0 with `shell:false`. | Supports JSON/path/subprocess criteria. |
| Claude installed-cache runner | `ls -la ~/.claude/plugins/cache/racecraft-public-plugins/speckit-pro/2.16.0/scripts/speckit-pro-runner` | Gap: file missing because XPLAT-002 must not implement the runner. | Cannot count as installed-cache probe pass. |
| Codex installed-cache runner | `ls -la ~/.codex/plugins/cache/racecraft-plugins-public/speckit-pro/2.16.0/scripts/speckit-pro-runner` | Gap: file missing because XPLAT-002 must not implement the runner. | Cannot count as installed-cache probe pass. |

## Evidence Gaps

| Missing probe | Scope | Reason unavailable | Substitute evidence | Effect | Owner / expiry |
|---|---|---|---|---|---|
| Installed Claude cache invocation of JS/TS `speckit-pro-runner` | Claude cache on this macOS host | Runner is intentionally not implemented. | Cache directory exists for `speckit-pro/2.16.0`; contract path is documented. | Installed-cache gate is not a pass. | XPLAT-004 must run after adding runner. |
| Installed Codex cache invocation of JS/TS `speckit-pro-runner` | Codex cache on this macOS host | Runner is intentionally not implemented. | Cache directory exists for `speckit-pro/2.16.0`; OpenAI docs define cache install path. | Installed-cache gate is not a pass. | XPLAT-004 must run after adding runner. |
| Cross-host Node availability from plugin platforms | Windows/macOS/Linux installed plugin users | Plugin docs do not guarantee a Node runtime for plugin payload execution. | Local `node --version` only proves this host. | Selection-blocking for source JS/TS package. | Would require XPLAT-004/XPLAT-007 platform proof or bundling Node. |

## Gate Results

| Gate | Result | Rationale |
|---|---|---|
| Installed-cache invocation | Fail | Source JS/TS requires Node on PATH or a bundled runtime; actual cache runner probe is unavailable. |
| Native platform behavior | Pass/gap | Node is cross-platform, but plugin host availability is not guaranteed. |
| Filesystem and paths | Pass | Node path APIs and local probe cover spaces and Windows basename parsing. |
| JSON handling | Pass | Native JSON APIs avoid `jq`. |
| Subprocess behavior | Pass | `child_process` supports argv execution with shell disabled. |
| Packaging/update path | Gap/fail | A source package risks `node_modules`/`npm install`; bundling Node becomes a larger binary artifact strategy. |

## Weighted Score

| Criterion | Weight | Rating | Points |
|---|---:|---:|---:|
| Native platform behavior | 20 | 4 | 16 |
| Installed-cache invocation reliability | 15 | 2 | 6 |
| Dependency footprint and bootstrap burden | 15 | 3 | 9 |
| Packaging/distribution model | 15 | 3 | 9 |
| Offline behavior and update path | 10 | 3 | 6 |
| Diagnostics and error reporting | 10 | 4 | 8 |
| Maintainer ergonomics | 10 | 5 | 10 |
| Compatibility adapters and migration cost | 5 | 4 | 4 |
| **Total** | **100** |  | **68** |

## Supply-Chain Implications for XPLAT-003

- Evidence-backed: JS source can use built-in JSON/path/subprocess APIs; repo
  already has Node-based docs-site tooling but no installed runner package.
- Unverified: whether a bundled Node/SEA artifact is acceptable for payload
  size, scanning, checksums, signatures, SBOM/provenance, and updates.
- Risk: `node_modules`, package-manager lockfiles, and runtime bundling would
  require controls not selected in XPLAT-002.
