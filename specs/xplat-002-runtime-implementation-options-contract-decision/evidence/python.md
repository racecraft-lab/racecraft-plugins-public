# Evidence: Python Runtime Candidate

Candidate status: Rejected
Captured: 2026-06-26

## Evidence Standard

This record uses the same XPLAT-001 gates and weights as the other candidates.
Evidence gaps are not counted as installed-cache probe passes.

## Official / Runtime Documentation

- Python `json` module: `https://docs.python.org/3/library/json.html`
- Python `subprocess` module: `https://docs.python.org/3/library/subprocess.html`
- Python `pathlib` module: `https://docs.python.org/3/library/pathlib.html`
- Python Windows usage/install documentation:
  `https://docs.python.org/3/using/windows.html`
- OpenAI Codex plugin marketplace/cache documentation:
  `https://developers.openai.com/codex/plugins/build#how-codex-uses-marketplaces`
- Claude Code plugin marketplace documentation:
  `https://code.claude.com/docs/en/plugin-marketplaces`

## Repo-Local Evidence

- The active runtime problem is shell and `jq` dependency in installed skills,
  hooks, agents, helpers, and generated payloads, as recorded in
  `docs/ai/research/cross-platform-runtime-inventory.md`.
- No repo-local Python runner package, lockfile, or embedded runtime exists in
  the XPLAT-002 worktree.

## Probe Evidence

| Probe | Command | Result | Scoring effect |
|---|---|---|---|
| Runtime availability | `python3 --version` | Passed on this host: `Python 3.11.0`. | Host-local availability only; not an installed-cache guarantee. |
| JSON, stderr separation, paths, subprocess | `python3 -c '...'` supplemental probe | Passed: JSON stdout parsed, line-delimited JSON stderr preserved, path with spaces retained, Windows basename parsed with `ntpath`, child process exited 0 with `shell=False`. | Supports JSON/path/subprocess criteria. |
| Claude installed-cache runner | `ls -la ~/.claude/plugins/cache/racecraft-public-plugins/speckit-pro/2.16.0/scripts/speckit-pro-runner` | Gap: file missing because XPLAT-002 must not implement the runner. | Cannot count as installed-cache probe pass. |
| Codex installed-cache runner | `ls -la ~/.codex/plugins/cache/racecraft-plugins-public/speckit-pro/2.16.0/scripts/speckit-pro-runner` | Gap: file missing because XPLAT-002 must not implement the runner. | Cannot count as installed-cache probe pass. |

## Evidence Gaps

| Missing probe | Scope | Reason unavailable | Substitute evidence | Effect | Owner / expiry |
|---|---|---|---|---|---|
| Installed Claude cache invocation of Python `speckit-pro-runner` | Claude cache on this macOS host | Runner is intentionally not implemented. | Cache directory exists for `speckit-pro/2.16.0`; contract path is documented. | Installed-cache gate is not a pass. | XPLAT-004 must run after adding runner. |
| Installed Codex cache invocation of Python `speckit-pro-runner` | Codex cache on this macOS host | Runner is intentionally not implemented. | Cache directory exists for `speckit-pro/2.16.0`; OpenAI docs define cache install path. | Installed-cache gate is not a pass. | XPLAT-004 must run after adding runner. |
| Cross-host Python availability from plugin platforms | Windows/macOS/Linux installed plugin users | Plugin docs do not guarantee Python for payload execution; Windows Python installation is user-managed. | Local `python3 --version` only proves this host. | Selection-blocking for source Python package. | Would require platform proof or embedded runtime, which moves supply-chain burden to XPLAT-003. |

## Gate Results

| Gate | Result | Rationale |
|---|---|---|
| Installed-cache invocation | Fail | Source Python requires Python on PATH or an embedded runtime; actual cache runner probe is unavailable. |
| Native platform behavior | Gap/fail | Python is portable, but installed plugin hosts do not guarantee it. |
| Filesystem and paths | Pass | `pathlib` and `ntpath` support typed path handling; local probe covered spaces and Windows basename parsing. |
| JSON handling | Pass | `json` avoids `jq`. |
| Subprocess behavior | Pass | `subprocess.run(..., shell=False)` supports argv execution and capture. |
| Packaging/update path | Fail/gap | `pip`, virtualenv, wheels, or embedded Python would add post-cache setup or binary artifact controls. |

## Weighted Score

| Criterion | Weight | Rating | Points |
|---|---:|---:|---:|
| Native platform behavior | 20 | 3 | 12 |
| Installed-cache invocation reliability | 15 | 1 | 3 |
| Dependency footprint and bootstrap burden | 15 | 2 | 6 |
| Packaging/distribution model | 15 | 2 | 6 |
| Offline behavior and update path | 10 | 2 | 4 |
| Diagnostics and error reporting | 10 | 4 | 8 |
| Maintainer ergonomics | 10 | 3 | 6 |
| Compatibility adapters and migration cost | 5 | 3 | 3 |
| **Total** | **100** |  | **48** |

## Supply-Chain Implications for XPLAT-003

- Evidence-backed: Python stdlib covers JSON, subprocess, and path operations.
- Unverified: packaging a Python app with no user runtime dependency would
  require an embedded runtime or platform artifacts.
- Risk: `pip install`, virtualenv, wheel restoration, or embedded-runtime
  controls would need explicit XPLAT-003 decisions before implementation.
