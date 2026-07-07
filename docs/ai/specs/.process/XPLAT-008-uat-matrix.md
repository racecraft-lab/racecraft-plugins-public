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
| Claude | macOS | `docs/ai/specs/.process/XPLAT-008-uat-claude-macos.md` | Partial |
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
| Claude | macOS | Codex local UAT | 2026-07-07 | macOS 26.6 (25G5052e), arm64; Claude Code 2.1.202 | 2.17.0 | `/private/tmp/xplat008-claude-macos-uat.gFoutU/.claude/plugins/cache/racecraft-plugins-public/speckit-pro/2.17.0` | Python 3.11.0 via `/Users/fredrickgabelmann/.pyenv/versions/3.11.0/bin/python3`; `specify` 0.11.8 via `/Users/fredrickgabelmann/.local/bin/specify` | `xplat-008-claude-macos-20260707-runtime-info`, `xplat-008-claude-macos-20260707-preflight` | Pass | Pass | Blocked | Not run | Not run | Pass | Fixture pass only | Installed cache should install, expose skills/agents/hook, run runner preflight, and update to latest when already current. | Isolated Claude install/list/details, bundled inventory, runner runtime-info, runner preflight, and plugin update passed; model-backed first use was blocked by external-service review policy. | `docs/ai/specs/.process/XPLAT-008-uat-claude-macos.md` | Local installed-cache proof only; does not complete the full model-backed journey or native repair proof. | Partial |
| Claude | Linux | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `docs/ai/specs/.process/XPLAT-008-uat-claude-linux.md` | PENDING: notes | Pending |
| Codex | Windows | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `docs/ai/specs/.process/XPLAT-008-uat-codex-windows.md` | PENDING: notes | Pending |
| Codex | macOS | Codex local UAT | 2026-07-07 | macOS 26.6 (25G5052e), arm64; codex-cli 0.139.0 | 2.17.0 | `/private/tmp/xplat008-codex-macos-uat.1F8LdV/plugins/cache/racecraft-plugins-public/speckit-pro/2.17.0`; Git update cache `/private/tmp/xplat008-codex-git-macos-uat.1kw5AR/plugins/cache/racecraft-plugins-public/speckit-pro/2.17.0` | Python 3.11.0 via `/Users/fredrickgabelmann/.pyenv/versions/3.11.0/bin/python3`; `specify` 0.11.8 via `/Users/fredrickgabelmann/.local/bin/specify` | `xplat-008-codex-macos-20260707-runtime-info`, `xplat-008-codex-macos-20260707-preflight`, real Codex first-use output `/private/tmp/xplat008-uat-logs.CIxABs/codex-real-first-use.txt` | Pass | Pass | Partial | Partial | Not run | Pass | Fixture pass only | Installed cache should install, expose Codex skills/agents, run runner preflight, support installed status first use, and update from a Git marketplace. | Isolated install/list, bundled inventory, runner runtime-info, runner preflight, real authenticated Codex status first use, and isolated Git-backed marketplace update passed; isolated first use was auth-blocked and full scaffold/autopilot was not run. | `docs/ai/specs/.process/XPLAT-008-uat-codex-macos.md` | Local installed-cache and real status proof only; does not complete isolated auth, scaffold/autopilot dry-run, or native repair proof. | Partial |
| Codex | Linux | PENDING: operator | PENDING: date | PENDING: host version | PENDING: plugin version/latest tag | PENDING: installed cache path | PENDING: interpreter resolution | PENDING: runner invocation IDs | Pending | Pending | Pending | Pending | Pending | Pending | Pending | PENDING: expected result | PENDING: actual result | `docs/ai/specs/.process/XPLAT-008-uat-codex-linux.md` | PENDING: notes | Pending |

## Completion Rule

The XPLAT-008 release gate must continue to block until all six rows have real
native evidence, non-placeholder operator/date/host/cache/interpreter details,
runner invocation IDs, evidence links, expected and actual results, notes, and
`pass` status across install, bundled-agent verification, first use,
scaffold/status, autopilot dry-run, latest-tag update, and incomplete-install
repair.
