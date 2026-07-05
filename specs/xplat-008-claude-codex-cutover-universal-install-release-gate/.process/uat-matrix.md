# XPLAT-008 Native UAT Matrix

Status: Pending native operator evidence
Feature: XPLAT-008

This matrix defines the six required Claude/Codex native UAT rows for the
release gate. Rows remain non-release-ready until each platform operator
replaces every `PENDING:` field with real evidence from a native host.

## Required Rows

| Product | Platform | Detail file | Status |
|---|---|---|---|
| Claude | Windows | `.process/uat/claude-windows.md` | Pending |
| Claude | macOS | `.process/uat/claude-macos.md` | Pending |
| Claude | Linux | `.process/uat/claude-linux.md` | Pending |
| Codex | Windows | `.process/uat/codex-windows.md` | Pending |
| Codex | macOS | `.process/uat/codex-macos.md` | Pending |
| Codex | Linux | `.process/uat/codex-linux.md` | Pending |

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
| Claude | Windows | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `.process/uat/claude-windows.md` | PENDING: notes | Pending |
| Claude | macOS | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `.process/uat/claude-macos.md` | PENDING: notes | Pending |
| Claude | Linux | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `.process/uat/claude-linux.md` | PENDING: notes | Pending |
| Codex | Windows | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `.process/uat/codex-windows.md` | PENDING: notes | Pending |
| Codex | macOS | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `.process/uat/codex-macos.md` | PENDING: notes | Pending |
| Codex | Linux | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `.process/uat/codex-linux.md` | PENDING: notes | Pending |

## Completion Rule

The XPLAT-008 release gate must continue to block until all six rows have real
native evidence, non-placeholder operator/date/host/cache/interpreter details,
runner invocation IDs, evidence links, expected and actual results, notes, and
`pass` status across install, bundled-agent verification, first use,
scaffold/status, autopilot dry-run, latest-tag update, and incomplete-install
repair.
