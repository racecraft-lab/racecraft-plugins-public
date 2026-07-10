# XPLAT-008 Release Readiness Packet

Status: Blocked for public native-platform release
Feature: XPLAT-008
Branch: `codex/xplat-008-claude-codex-cutover-universal-install-release-gate`

Archive note: preserved from
`specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/release-readiness.md`
after PRs #289-#292 merged. The active spec folder was removed during
post-merge archive cleanup, but this packet remains the durable record that
native platform release claims are still blocked by real operator UAT.

## Decision

XPLAT-008 is reviewable as a blocked release-readiness packet. The
deterministic runner gates, generated payload rebuild, public docs claim
alignment, and repair safety controls are implemented and verified. Public
native Windows/macOS/Linux Claude and Codex release claims remain blocked until
T035-T041 are filled with real native operator evidence.

Fixture-backed UAT gate proof demonstrates that the release gate blocks missing,
placeholder, smoke-only, failing, raw-HTML, missing-link, unsupported-claim,
unsafe-repair, broad-reinstall, and incomplete-update cases. It does not satisfy
the native UAT requirement by itself.

## Current Completion

| Area | Status | Evidence |
|---|---|---|
| Active runtime surface cutover | Complete | `specs/.../.process/active-runtime-inventory.md`, source skill/agent/hook updates, active-runtime guard request |
| Generated payload rebuild | Complete | `dist/claude/speckit-pro/**`, `dist/codex/speckit-pro/**`, payload completeness request |
| Public docs and README claim alignment | Complete | Root README, plugin README, docs-site install/first-run/troubleshooting/security/update/contribute pages |
| UAT matrix gate contract | Complete | `tests/speckit-pro/unit/fixtures/installed-plugin-release/uat-matrix-cases.json`, `requests/uat-matrix.json` |
| Install-health repair contract | Complete | `install-health-repair-cases.json`, `requests/install-health-repair.json`, `helpers/install.py` |
| Native UAT evidence | Blocked | T035-T041 remain incomplete; `docs/ai/specs/.process/XPLAT-008-uat-claude-macos.md` and `docs/ai/specs/.process/XPLAT-008-uat-codex-macos.md` record local macOS partial passes, and the matrix remains non-release-ready |
| Release decision | Blocked | Release-readiness gate must not be used to claim native support until real rows replace fixture evidence |

## Verification Evidence

| Command | Result | Notes |
|---|---|---|
| `python3 -m json.tool` on XPLAT-008 fixture/request JSON | Pass | UAT matrix, install-health repair, release-readiness, and request fixtures parse |
| `python3 -m py_compile speckit-pro/speckit_pro_runner/gates/release.py speckit-pro/speckit_pro_runner/helpers/install.py speckit-pro/speckit_pro_runner/gates/registry.py speckit-pro/speckit_pro_runner/helpers/registry.py tests/speckit-pro/unit/test-speckit-pro-gates.py` | Pass | Runner gate/helper code compiles |
| `bash tests/speckit-pro/run-all.sh --layer 1` | Pass | 1439/1439 structural checks passed |
| `python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` | Pass | 47/47 focused Layer 4 gate tests |
| `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/active-runtime-guard.json` | Pass | Active runtime no-shell/no-jq guard |
| `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/payload-completeness.json` | Pass | Generated payload completeness for Claude and Codex payloads |
| `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/uat-matrix.json` | Pass | Fixture UAT matrix validates the positive gate case only |
| `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/install-health-repair.json` | Pass | Trusted missing artifact autoheal fixture passes |
| `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/installed-plugin-release/requests/release-readiness.json` | Pass | Promoted ready fixture validates the passing release-readiness contract |
| Direct `release-readiness-xplat008` request for case `current-native-uat-pending` | Expected failure | Current native UAT pending case blocks with `release_readiness.gate_status: fail`, `status: expected_failure`, and `uat-matrix rows=0` |
| Isolated Claude/macOS installed-cache UAT | Partial pass | `HOME=/private/tmp/xplat008-claude-macos-uat.gFoutU` install/list/details, bundled skills/agents/hook, runner runtime-info, runner preflight, and plugin update passed; model-backed first use was policy-blocked; see `docs/ai/specs/.process/XPLAT-008-uat-claude-macos.md` |
| Isolated Codex/macOS installed-cache UAT | Partial pass | `CODEX_HOME=/private/tmp/xplat008-codex-macos-uat.1F8LdV` install/list, bundled skills/agents, runner runtime-info, and preflight passed; isolated first use was auth-blocked; see `docs/ai/specs/.process/XPLAT-008-uat-codex-macos.md` |
| Real Codex/macOS status first use | Partial pass | Authenticated real Codex loaded installed `speckit-status` from plugin cache and returned the current XPLAT status without edits; output at `/private/tmp/xplat008-uat-logs.CIxABs/codex-real-first-use.txt` |
| Isolated Codex/macOS Git marketplace update | Pass | `CODEX_HOME=/private/tmp/xplat008-codex-git-macos-uat.1kw5AR` added the Git marketplace, installed `speckit-pro` 2.17.0, and `codex plugin marketplace upgrade racecraft-plugins-public --json` completed with no errors |
| `npx --yes pnpm@10.25.0 --dir docs-site validate` | Pass | Docs validation and 88 Playwright smoke checks passed |
| `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/pr/speckit-pr-packet.json` | Pass | Packet validation wrote a fresh `status: "passed"` result |
| `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-workflow-contract.sh --title "feat(XPLAT-008): Add Claude/Codex cutover and universal install release gate" --changed-files specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/pr/changed-files.txt` | Pass | Single-PR workflow contract passed |

## Functional Requirement Traceability

| Requirement | Changed files | Verification |
|---|---|---|
| FR-001 | `.process/active-runtime-inventory.md`, `active_path_guard.py` | Active-runtime guard request; inventory review |
| FR-002 | `helpers/install.py`, Claude/Codex skills and hooks | Runner invocation fixtures and focused Layer 4 tests |
| FR-003 | Claude/Codex skills, agents, hooks, docs guidance | Active-runtime no-shell/no-jq guard |
| FR-004 | `gates/active_path_guard.py`, `gates/registry.py` | Active-runtime guard seeded blocker tests |
| FR-005 | `active-runtime-guard-cases.json` | Allow-list fixture cases for archive/provenance, tests, CI glue, upstream helpers |
| FR-006 | `gates/payloads.py`, generated `dist/**` | Payload completeness apply/read-only requests |
| FR-007 | `payload-completeness-cases.json`, generated payload runner files and metadata | Payload completeness request |
| FR-008 | `release.py`, `release-readiness-cases.json` | Release-readiness blocker cases |
| FR-009 | `README.md`, `speckit-pro/README.md`, docs-site install pages | Docs validation; public-claim release-readiness cases |
| FR-010 | Docs-site install/first-run/troubleshooting/security pages | Docs validation; public-claim review |
| FR-011 | Docs-site security/trust/update guidance and READMEs | Public-claim release-readiness cases |
| FR-012 | `.process/uat-matrix.md`, `uat-matrix-cases.json` | UAT matrix gate contract; real native rows pending |
| FR-013 | `.process/uat-matrix.md`, UAT fixture rows | UAT matrix gate contract; real native rows pending |
| FR-014 | `gates/release.py`, UAT and release-readiness fixtures | Missing/placeholder/smoke/failing UAT blocker tests |
| FR-015 | `helpers/install.py`, install-health fixtures | Install-health repair helper request |
| FR-016 | `helpers/install.py`, install-health fixtures | Trusted missing/stale autoheal cases |
| FR-017 | `helpers/install.py`, install-health fixtures | Unsafe drift manual remediation and broad reinstall blocker cases |
| FR-018 | UAT matrix contract and release-readiness cases | Incomplete update proof blocker; real native update proof pending |
| FR-019 | `gates/release.py`, release-readiness fixtures | Aggregate release-readiness request and seeded blockers |
| FR-020 | This packet, workflow, tasks, PR packet draft | Traceability tables and verification commands |
| FR-021 | Manifest/checksum metadata, release docs | Diff audit; no manual release-process version bump |
| FR-022 | Runner gate/helper registry and XPLAT-006/XPLAT-007 substrates | Registry tests; generated payload metadata refresh |

## Success Criteria Traceability

| Criterion | Status | Evidence |
|---|---|---|
| SC-001 | Blocked | Requires real native Claude/Codex Windows/macOS/Linux first-use journeys; macOS has partial evidence only and T035-T040 remain incomplete |
| SC-002 | Complete | Active-runtime no-shell/no-jq guard passes |
| SC-003 | Complete | Payload completeness request passes for Claude and Codex generated payloads |
| SC-004 | Blocked | `.process/uat-matrix.md` has partial Claude/macOS and Codex/macOS local rows plus four pending rows; T041 pending |
| SC-005 | Complete | Release-readiness seeded blocker cases cover active shell, incomplete payload, missing bundled agent, stale metadata, unsafe public claim, and incomplete UAT |
| SC-006 | Complete for deterministic contract | Trusted stale/missing and unsafe/manual/broad-reinstall fixtures covered; real native repair proof pending under T035-T041 |
| SC-007 | Complete for current public docs | Docs and public-claim gates avoid unsupported native support and cryptographic trust-chain claims |
| SC-008 | Complete for packet structure | Requirement and success criteria traceability recorded here; PR packet should reuse this ordering |

## Non-goal Audit

| Non-goal | Result | Evidence |
|---|---|---|
| No child specs during setup | Preserved | Only the XPLAT-008 feature directory is active |
| No installed-runtime shell wrapper transition path | Preserved | Installed runtime surfaces route through Python runner invocation |
| No repo-wide historical shell-word purge | Preserved | Guard scope excludes archive/provenance and upstream helper text |
| No future-facing public claims before evidence | Preserved | Native support remains blocked pending real UAT |
| No smoke-only UAT support claim | Preserved | UAT gate blocks smoke-only rows |
| No broad reinstall or wipe-copy repair | Preserved | Install-health repair gate rejects broad reinstall action |
| No manual plugin version edits outside release-please | Preserved | Version handling remains release-process aligned; no manual version bump is required by this feature |

## Known Gaps

- T035: Claude on Windows native UAT evidence is not filled.
- T036: Claude on macOS local installed-cache UAT evidence is partially filled
  in `docs/ai/specs/.process/XPLAT-008-uat-claude-macos.md`; model-backed
  first use, scaffold/status, autopilot dry-run, native repair proof, and
  release-row completion remain pending.
- T037: Claude on Linux native UAT evidence is not filled.
- T038: Codex on Windows native UAT evidence is not filled.
- T039: Codex on macOS local installed-cache UAT evidence is partially filled
  in `docs/ai/specs/.process/XPLAT-008-uat-codex-macos.md`; real authenticated
  status first use and isolated Git marketplace update pass, while isolated
  auth, full scaffold/status, autopilot dry-run, native repair proof, and
  release-row completion remain pending.
- T040: Codex on Linux native UAT evidence is not filled.
- T041: The six native evidence files have not been consolidated into a
  passing `.process/uat-matrix.md`; two macOS rows are partial and four rows
  remain pending.

## Reviewer Order

1. Review source runner/gate/helper changes under `speckit-pro/speckit_pro_runner/`.
2. Review active Claude/Codex skill, hook, README, and docs claim wording.
3. Review fixture contracts and focused Layer 4 coverage.
4. Review generated `dist/**` payloads after source changes.
5. Review this blocked release-readiness packet and pending UAT matrix rows.

## Release Rule

Do not publish native Windows/macOS/Linux Claude or Codex support claims from
this PR until real platform operators replace the pending UAT matrix rows with
passing evidence and the release-readiness gate is rerun against that evidence.
