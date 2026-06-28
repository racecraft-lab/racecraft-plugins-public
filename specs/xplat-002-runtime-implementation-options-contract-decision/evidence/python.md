# Evidence: Python Runtime Candidate

Candidate status: Selected by 2026-06-28 amendment
Captured: 2026-06-26; amended 2026-06-28

## Evidence Standard

This record uses the same XPLAT-001 gates and weights as the other candidates.
Evidence gaps are not counted as installed-cache probe passes.

## Official / Runtime Documentation

- Python `json` module: `https://docs.python.org/3/library/json.html`
- Python `subprocess` module: `https://docs.python.org/3/library/subprocess.html`
- Python `pathlib` module: `https://docs.python.org/3/library/pathlib.html`
- Python Windows usage/install documentation:
  `https://docs.python.org/3/using/windows.html`
- Official Spec Kit installation documentation:
  `https://github.com/github/spec-kit/blob/main/docs/installation.md`
- Official Spec Kit package metadata:
  `https://github.com/github/spec-kit/blob/main/pyproject.toml`
- OpenAI Codex plugin marketplace/cache documentation:
  `https://developers.openai.com/codex/plugins/build#how-codex-uses-marketplaces`
- Claude Code plugin marketplace documentation:
  `https://code.claude.com/docs/en/plugin-marketplaces`

## Repo-Local Evidence

- The active runtime problem is shell and `jq` dependency in installed skills,
  hooks, agents, helpers, and generated payloads, as recorded in
  `docs/ai/research/cross-platform-runtime-inventory.md`.
- SpecKit-Pro may require the official Spec Kit / `specify` prerequisite
  boundary. The official Spec Kit package metadata requires Python 3.11+, and
  the installed `specify` command is a product prerequisite for SpecKit-Pro.
- No repo-local Python runner exists yet in the XPLAT-002 worktree because this
  decision spike does not implement `speckit-pro-runner`.

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
| Windows/macOS/Linux Python launcher discovery from installed plugin caches | Installed plugin users | Runner is intentionally not implemented. | Official Spec Kit prerequisite boundary requires Python 3.11+; local probe proves stdlib behavior on this host. | Not selection-blocking; XPLAT-004 must prove launch and preflight behavior. | XPLAT-004. |

## Gate Results

| Gate | Result | Rationale |
|---|---|---|
| Installed-cache invocation | Viable with proof deferred | Official Spec Kit / `specify` is a product prerequisite and requires Python 3.11+; actual cache runner probe remains unavailable until XPLAT-004 implements the runner. |
| Native platform behavior | Pass with preflight | Python is portable across Windows, macOS, and Linux; XPLAT-004 must verify launcher discovery through `py -3.11`, `python3`, or `python`. |
| Filesystem and paths | Pass | `pathlib` and `ntpath` support typed path handling; local probe covered spaces and Windows basename parsing. |
| JSON handling | Pass | `json` avoids `jq`. |
| Subprocess behavior | Pass | `subprocess.run(..., shell=False)` supports argv execution and capture. |
| Packaging/update path | Pass with stdlib-only constraint | Runner source ships in the plugin payload; no `pip`, virtualenv, wheels, embedded Python, or plugin-only package restoration is allowed after install. |

## Weighted Score

| Criterion | Weight | Rating | Points |
|---|---:|---:|---:|
| Native platform behavior | 20 | 4 | 16 |
| Installed-cache invocation reliability | 15 | 4 | 12 |
| Dependency footprint and bootstrap burden | 15 | 4 | 12 |
| Packaging/distribution model | 15 | 4 | 12 |
| Offline behavior and update path | 10 | 4 | 8 |
| Diagnostics and error reporting | 10 | 4 | 8 |
| Maintainer ergonomics | 10 | 5 | 10 |
| Compatibility adapters and migration cost | 5 | 4 | 4 |
| **Total** | **100** |  | **82** |

## Supply-Chain Implications for XPLAT-003

- Evidence-backed: Python stdlib covers JSON, subprocess, and path operations.
- Selected boundary: SpecKit-Pro can require official Spec Kit / `specify`,
  which brings a Python 3.11+ prerequisite that must be verified by preflight.
- Required control: the runner stays stdlib-only for first release. `pip
  install`, virtualenv restoration, wheels, embedded Python, or plugin-only
  Python packages are out of scope unless XPLAT is reopened again.
- Risk: Windows launcher discovery and installed-cache invocation must be proven
  in XPLAT-004 before public support claims.
