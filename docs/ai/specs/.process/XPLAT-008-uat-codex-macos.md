# XPLAT-008 UAT Evidence: Codex on macOS

Status: Partial pass for local Codex/macOS installed-cache checks and real
Codex status first use; not a release-ready native UAT row.

Archive note: preserved from
`specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/uat/codex-macos.md`
after PRs #289-#292 merged. This is partial local installed-cache evidence, not
complete native release UAT.

## Environment

| Field | Value |
|---|---|
| Product | Codex |
| Platform | macOS |
| Operator | Codex local UAT |
| Date | 2026-07-07T03:28:33Z |
| Host version | macOS 26.6 (25G5052e); arm64 |
| Codex host version | codex-cli 0.139.0 |
| Plugin version | 2.17.0 |
| Isolated local-path CODEX_HOME | `/private/tmp/xplat008-codex-macos-uat.1F8LdV` |
| Isolated Git CODEX_HOME | `/private/tmp/xplat008-codex-git-macos-uat.1kw5AR` |
| Installed cache path | `/private/tmp/xplat008-codex-macos-uat.1F8LdV/plugins/cache/racecraft-plugins-public/speckit-pro/2.17.0` |
| Git install cache path | `/private/tmp/xplat008-codex-git-macos-uat.1kw5AR/plugins/cache/racecraft-plugins-public/speckit-pro/2.17.0` |
| Real Codex installed source | `<real-codex-home>/.tmp/marketplaces/racecraft-plugins-public/dist/codex/speckit-pro` |
| SpecKit CLI | `<local-user-home>/.local/bin/specify`, `specify 0.11.8` |
| Python interpreter | `<local-user-home>/.pyenv/versions/3.11.0/bin/python3`, Python 3.11.0 |

## Steps And Results

| Step | Command | Result |
|---|---|---|
| Add local marketplace | `CODEX_HOME=<isolated-local-home> codex plugin marketplace add <repo-root> --json` | Pass; marketplace `racecraft-plugins-public` added from the local repo root. |
| Install plugin | `CODEX_HOME=<isolated-local-home> codex plugin add speckit-pro@racecraft-plugins-public --json` | Pass; installed `speckit-pro` 2.17.0 into the isolated cache path. |
| List installed plugin | `CODEX_HOME=<isolated-local-home> codex plugin list --json` | Pass; plugin is installed and enabled, sourced from `dist/codex/speckit-pro`. |
| Bundled agents | `find <installed-cache>/codex-agents -maxdepth 1 -type f -name '*.toml'` | Pass; 10 bundled Codex agents are present, including `phase-executor`, `implement-executor`, and `uat-runbook-author`. |
| Bundled skills | `find <installed-cache>/skills -maxdepth 2 -name SKILL.md` | Pass; installed Codex skills include autopilot, scaffold, status, install, upgrade, and resolve-pr. |
| Runner runtime-info | `PYTHONPATH=<installed-cache> python3 -m speckit_pro_runner` with request `xplat-008-codex-macos-20260707-runtime-info` | Pass; status `ok`, platform `darwin`, architecture `arm64`, Python 3.11.0, and `specify` 0.11.8 detected. |
| Runner preflight | `PYTHONPATH=<installed-cache> python3 -m speckit_pro_runner` with request `xplat-008-codex-macos-20260707-preflight` | Pass; status `ok`, runner metadata verified, source context reported as `installed_payload`. |
| Isolated first use | `CODEX_HOME=<isolated-local-home> codex exec --ephemeral ...` | Blocked by missing isolated Codex auth; after network access was allowed, the API returned `401 Unauthorized` because the temp CODEX_HOME had no bearer or basic authentication. |
| Real Codex first use | `codex exec --ephemeral --sandbox read-only --output-last-message /private/tmp/xplat008-uat-logs.CIxABs/codex-real-first-use.txt "Use the installed speckit-pro:speckit-status skill for xplat..."` | Pass; real authenticated Codex loaded the installed `speckit-status` skill from plugin cache and returned current XPLAT status without editing files. |
| Add Git marketplace | `CODEX_HOME=<isolated-git-home> codex plugin marketplace add racecraft-lab/racecraft-plugins-public --ref main --json` | Pass; Git marketplace source recorded as `https://github.com/racecraft-lab/racecraft-plugins-public.git`. |
| Install from Git marketplace | `CODEX_HOME=<isolated-git-home> codex plugin add speckit-pro@racecraft-plugins-public --json` | Pass; installed `speckit-pro` 2.17.0 into the isolated Git-backed cache. |
| Latest-tag update | `CODEX_HOME=<isolated-git-home> codex plugin marketplace upgrade racecraft-plugins-public --json` | Pass; upgrade completed for the isolated Git marketplace with no errors. |
| Install-health repair fixture | `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/.../requests/install-health-repair.json` | Fixture pass only; trusted missing runner artifact produces checksum-backed `autoheal_refresh` in read-only fixture mode. |

## Expected Result

Codex can install SpecKit Pro from the local marketplace payload into an
isolated cache, the installed payload contains the required skills and Codex
agent templates, the installed Python runner preflight succeeds when the
official SpecKit CLI is available, real authenticated Codex can invoke an
installed SpecKit status skill, and a Git-backed marketplace can update without
errors.

## Actual Result

The install, list, bundled skill/agent checks, runner runtime-info, runner
preflight, real authenticated Codex status first use, and isolated Git-backed
marketplace update behaved as expected. The isolated first-use probe could not
complete because the temporary CODEX_HOME had no Codex authentication. The
full scaffold/status and autopilot dry-run journey was not run.

## Release-Readiness Boundary

This file is durable local evidence for manual Codex/macOS installed-cache UAT.
It does not complete T039 or T041 by itself because it does not prove isolated
interactive auth, the full scaffold/status and autopilot dry-run journey,
native repair on a real installed cache, or all six Claude/Codex
Windows/macOS/Linux rows. The release-readiness gate must continue to block
native platform support claims until all required rows are filled with real
platform evidence.
