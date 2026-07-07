# XPLAT-008 UAT Evidence: Claude on macOS

Status: Partial pass for local Claude/macOS installed-cache checks; not a
release-ready native UAT row.

Archive note: created after the XPLAT-008 active spec was archived. This file
preserves the 2026-07-07 local macOS Claude UAT attempt against the installed
plugin payload.

## Environment

| Field | Value |
|---|---|
| Product | Claude |
| Platform | macOS |
| Operator | Codex local UAT |
| Date | 2026-07-07T03:28:33Z |
| Host version | macOS 26.6 (25G5052e); arm64 |
| Claude host version | Claude Code 2.1.202 |
| Plugin version | 2.17.0 |
| Isolated HOME | `/private/tmp/xplat008-claude-macos-uat.gFoutU` |
| Installed cache path | `/private/tmp/xplat008-claude-macos-uat.gFoutU/.claude/plugins/cache/racecraft-plugins-public/speckit-pro/2.17.0` |
| SpecKit CLI | `<local-user-home>/.local/bin/specify`, `specify 0.11.8` |
| Python interpreter | `<local-user-home>/.pyenv/versions/3.11.0/bin/python3`, Python 3.11.0 |

## Steps And Results

| Step | Command | Result |
|---|---|---|
| Add local marketplace | `HOME=<isolated-home> claude plugin marketplace add <repo-root>` | Pass; marketplace `racecraft-plugins-public` added from the local repo root. |
| Install plugin | `HOME=<isolated-home> claude plugin install speckit-pro@racecraft-plugins-public --scope user` | Pass; installed `speckit-pro@racecraft-plugins-public` for the isolated user scope. |
| List installed plugin | `HOME=<isolated-home> claude plugin list` | Pass; plugin version 2.17.0 is installed, enabled, and user-scoped. |
| Plugin details | `HOME=<isolated-home> claude plugin details speckit-pro@racecraft-plugins-public` | Pass; 10 skills, 11 agents, and the UserPromptExpansion hook are registered. |
| Bundled runner files | `find <installed-cache>/speckit_pro_runner -maxdepth 1 -type f` | Pass; runner entry point, manifest, and checksum metadata are present. |
| Runner runtime-info | `PYTHONPATH=<installed-cache> python3 -m speckit_pro_runner` with request `xplat-008-claude-macos-20260707-runtime-info` | Pass; status `ok`, platform `darwin`, architecture `arm64`, Python 3.11.0, and `specify` 0.11.8 detected. |
| Runner preflight | `PYTHONPATH=<installed-cache> python3 -m speckit_pro_runner` with request `xplat-008-claude-macos-20260707-preflight` | Pass; status `ok`, runner metadata verified, source context reported as `installed_payload`. |
| Latest-tag update | `HOME=<isolated-home> claude plugin update speckit-pro@racecraft-plugins-public` | Pass; Claude reported the plugin was already latest at 2.17.0. |
| Model-backed first use | `HOME=<isolated-home> claude --print ...` using the installed plugin | Blocked before execution by external-service review policy because the command would send workspace-derived repo content to Claude. |
| Install-health repair fixture | `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/.../requests/install-health-repair.json` | Fixture pass only; trusted missing runner artifact produces checksum-backed `autoheal_refresh` in read-only fixture mode. |

## Expected Result

Claude can install SpecKit Pro from the local marketplace payload into an
isolated user home, expose the expected skills, agents, hook, and runner files,
and run installed-payload Python runner preflight with the official SpecKit CLI
available.

## Actual Result

The local install, list, bundled inventory, runner runtime-info, runner
preflight, and update check behaved as expected. The model-backed first-use
probe was not executed because the approval reviewer rejected sending
workspace-derived repository context to the external Claude service.

## Release-Readiness Boundary

This file is durable local evidence for manual Claude/macOS installed-cache UAT.
It does not complete T036 or T041 by itself because it does not prove the full
model-backed first-use journey, scaffold/status, autopilot dry-run, native
repair on a real installed cache, or all six Claude/Codex Windows/macOS/Linux
rows. The release-readiness gate must continue to block native platform support
claims until all required rows are filled with real platform evidence.
