# XPLAT-008 Native UAT Matrix

Status: Pending native operator evidence
Feature: XPLAT-008

Archive note: preserved from
`docs/ai/specs/.process/XPLAT-008-uat-matrix.md`
after PRs #289-#292 merged. The active spec folder was removed during
post-merge archive cleanup, but this matrix remains the durable public-release
blocker until all native operator rows pass.

This matrix defines the six required Claude/Codex native UAT rows for the
release gate. Rows remain non-release-ready until each platform operator
replaces every `PENDING:` field with real evidence from a native host.

## Required Rows

| Product | Platform | Detail file | Status |
|---|---|---|---|
| Claude | Windows | `docs/ai/specs/.process/XPLAT-008-uat-claude-windows.md` | Pending |
| Claude | macOS | `docs/ai/specs/.process/XPLAT-008-uat-claude-macos.md` | Pending |
| Claude | Linux | `docs/ai/specs/.process/XPLAT-008-uat-claude-linux.md` | Pending |
| Codex | Windows | `docs/ai/specs/.process/XPLAT-008-uat-codex-windows.md` | Pending |
| Codex | macOS | `docs/ai/specs/.process/XPLAT-008-uat-codex-macos.md` | Partial |
| Codex | Linux | `docs/ai/specs/.process/XPLAT-008-uat-codex-linux.md` | Pending |

## Row Template

Copy this block once per row into the matching detail file, then summarize the
completed row back into the matrix below.

```text
Product:
Platform:
Operator:
Date:
Host version:
Plugin version or latest tag:
Installed cache path:
Interpreter resolution:
Runner invocation IDs:
- install:
- first use:
- scaffold/status:
- autopilot dry-run:
- latest-tag update:
- incomplete-install repair:
Install result:
Bundled agent verification:
First use:
Scaffold/status:
Autopilot dry-run:
Latest-tag update:
Incomplete-install repair:
Expected result:
Actual result:
Evidence link:
Operator notes:
Status:
```

## Matrix

| Product | Platform | Operator | Date | Host version | Plugin version or latest tag | Installed cache path | Interpreter resolution | Runner invocation IDs | Install | Bundled agents | First use | Scaffold/status | Autopilot dry-run | Latest-tag update | Incomplete-install repair | Expected result | Actual result | Evidence link | Notes | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Claude | Windows | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `docs/ai/specs/.process/XPLAT-008-uat-claude-windows.md` | PENDING: notes | Pending |
| Claude | macOS | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `docs/ai/specs/.process/XPLAT-008-uat-claude-macos.md` | PENDING: notes | Pending |
| Claude | Linux | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `docs/ai/specs/.process/XPLAT-008-uat-claude-linux.md` | PENDING: notes | Pending |
| Codex | Windows | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `docs/ai/specs/.process/XPLAT-008-uat-codex-windows.md` | PENDING: notes | Pending |
| Codex | macOS | Codex autopilot local UAT | 2026-07-06 | macOS 26.6 (25G5052e); codex-cli 0.139.0 | 2.17.0 | `/private/tmp/xplat008-codex-uat-home/plugins/cache/racecraft-plugins-public/speckit-pro/2.17.0` | Python 3.14.6 via Homebrew Python; `specify` 0.11.8 via `<local-user-bin>/specify` when PATH is set | `xplat-008-codex-macos-installed-runtime-info`, `xplat-008-codex-macos-installed-preflight-with-specify-path`, `xplat-008-codex-macos-installed-install-health-repair` | Pass | Pass | Partial | Partial | Not run | Not run | Fixture pass only | Installed cache should install and preflight through the Python runner when official SpecKit is on PATH. | Isolated Codex plugin install/list, bundled skills/agents, runner runtime-info, and runner preflight passed; default PATH correctly failed with `specify_missing` until existing SpecKit CLI path was exposed. | `docs/ai/specs/.process/XPLAT-008-uat-codex-macos.md` | Local installed-cache proof only; does not complete the full native interactive journey. | Partial |
| Codex | Linux | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `docs/ai/specs/.process/XPLAT-008-uat-codex-linux.md` | PENDING: notes | Pending |

## Completion Rule

The XPLAT-008 release gate must continue to block until all six rows have real
native evidence, non-placeholder operator/date/host/cache/interpreter details,
runner invocation IDs, evidence links, expected and actual results, notes, and
`pass` status across install, bundled-agent verification, first use,
scaffold/status, autopilot dry-run, latest-tag update, and incomplete-install
repair.
