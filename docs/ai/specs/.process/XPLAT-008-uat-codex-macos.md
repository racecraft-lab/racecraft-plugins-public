# XPLAT-008 UAT Evidence: Codex on macOS

Status: Partial pass for local Codex/macOS installed-cache checks; not a
release-ready native UAT row.

Archive note: preserved from
`specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/uat/codex-macos.md`
after PRs #289-#292 merged. This is partial local installed-cache evidence, not
complete native release UAT.

## Environment

| Field | Value |
|---|---|
| Product | Codex |
| Platform | macOS |
| Operator | Codex autopilot local UAT |
| Date | 2026-07-06T03:08:36Z |
| Host version | macOS 26.6 (25G5052e) |
| Codex host version | codex-cli 0.139.0 |
| Plugin version | 2.17.0 |
| Isolated CODEX_HOME | `/tmp/xplat008-codex-uat-home` |
| Installed cache path | `/private/tmp/xplat008-codex-uat-home/plugins/cache/racecraft-plugins-public/speckit-pro/2.17.0` |
| SpecKit CLI | `<local-user-bin>/specify`, `specify 0.11.8` |
| Python interpreter | `/opt/homebrew/opt/python@3.14/bin/python3.14`, Python 3.14.6 |

## Steps And Results

| Step | Command | Result |
|---|---|---|
| Add local marketplace | `CODEX_HOME=/tmp/xplat008-codex-uat-home codex plugin marketplace add <repo-root> --json` | Pass; marketplace `racecraft-plugins-public` added from the local repo root. |
| Install plugin | `CODEX_HOME=/tmp/xplat008-codex-uat-home codex plugin add speckit-pro@racecraft-plugins-public --json` | Pass; installed `speckit-pro` 2.17.0 into the isolated cache path. |
| List installed plugin | `CODEX_HOME=/tmp/xplat008-codex-uat-home codex plugin list --json` | Pass; plugin is installed and enabled, sourced from `dist/codex/speckit-pro`. |
| Bundled agents | `find <installed-cache>/codex-agents -maxdepth 1 -type f -name '*.toml'` | Pass; 10 bundled Codex agents are present, including `phase-executor`, `implement-executor`, and `uat-runbook-author`. |
| Bundled skills | `find <installed-cache>/skills -maxdepth 2 -name SKILL.md` | Pass; installed Codex skills include autopilot, scaffold, status, install, upgrade, and resolve-pr. |
| Runner runtime-info | `python3 -m speckit_pro_runner` with `runtime-info` request from the installed cache | Pass; status `ok`, platform `darwin`, architecture `arm64`, Python `3.11.0` in the default shell path. |
| Runner preflight without SpecKit PATH | `python3 -m speckit_pro_runner` with `preflight` request from the installed cache | Expected fail; status `missing_prerequisite`, diagnostic `specify_missing`, runner metadata verified. |
| Runner preflight with SpecKit PATH | `env PATH=<local-user-bin>:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin PYTHONPATH=<installed-cache> python3 -m speckit_pro_runner` with `preflight` request | Pass; status `ok`, runner metadata verified, Python `3.14.6`, and `specify` found at `<local-user-bin>/specify`. |
| Install-health repair fixture | `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/.../requests/install-health-repair.json` | Pass; trusted missing runner artifact produces checksum-backed `autoheal_refresh` in read-only fixture mode. |

## Expected Result

Codex can install SpecKit Pro from the local marketplace payload into an
isolated cache, the installed payload contains the required skills and Codex
agent templates, and the installed Python runner preflight succeeds when the
official SpecKit CLI is available on PATH.

## Actual Result

The install, list, bundled skill/agent checks, runner runtime-info, and runner
preflight all behaved as expected. The default shell PATH did not expose
`specify`, and the runner correctly failed with `specify_missing`; adding the
existing local SpecKit CLI path made preflight pass without changing plugin
code or installing new software.

## Release-Readiness Boundary

This file is durable local evidence for manual Codex/macOS installed-cache UAT.
It does not complete T039 or T041 by itself because it does not prove the full
interactive scaffold/status/autopilot journey, latest-tag update, or all six
Claude/Codex Windows/macOS/Linux native rows. The release-readiness gate must
continue to block native platform support claims until all required rows are
filled with real platform evidence.
