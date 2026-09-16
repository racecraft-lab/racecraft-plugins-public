
# Deterministic Layer 1/4/5 audit

## Verdict

The captured manifest contains 93 deterministic executables across Layers 1, 4, and 5. This report inventories every loaded case method, but it does not claim that file counts prove coverage: 1,674 executable case methods, 1,700 declared test-shaped functions, 9,071 all-file static assertion sites, runtime generated subtests, and house counted units are reported separately.

Layer 1 and Layer 5 received deep source review, the five approved replacements, and focused execution. Layer 4 remains the frozen breadth inventory; all 1,615 loaded Layer 4 case families are explicitly unreviewed in the JSON ledger. No Layer 4, Layer 6 integration, Layer 7 parity, live-provider, manifest, generated-artifact, commit, or push change was made in this lane.

## Exact coverage counts

| Layer | Registered executables | Declared test functions | Loaded case methods | Static assertion sites in file | Static subtest call sites | Runtime counted units | Runtime generated subtests |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 8 | 49 | 49 | 816 | 463 | 1692 | 1682 |
| 4 | 84 | 1641 | 1615 | 8220 | 696 | not run | unknown |
| 5 | 1 | 10 | 10 | 35 | 31 | 215 | 214 |

Totals: 93 registered executables; 1,700 declared test functions; 1,674 loaded case methods; 26 support-only test-shaped functions (plus two mixin declarations re-exposed under an executable subclass); 9,071 all-file static assertion sites; 1,190 all-file static subtest call sites; 141 static skipTest call sites; 31 skip-decorated declared test functions (30 loaded families); and 26 preview/dry-run-named families. Of the all-file sites, 8,373 assertions and 1,077 subtest calls are directly attributable to loaded case bodies; helper-owned sites account for the remainder. Layer 4 runtime generated-case and runtime-skip totals remain unknown because Layer 4 was not executed. Layer 1 plus Layer 5 produced 1,896 runtime subtests and 1,907 counted units.

Counting caveat: the house result counts each executed subtest as one unit and a method without subtests as one unit. It does not count each assertion expression. The JSON records all-file source sites separately from sites directly attributable to loaded case bodies; helper-owned sites are therefore visible without pretending they are independent generated cases.

## Actionable findings

### 1. Register or explicitly defer 35 post-baseline native-eval cases

3 executable unit files are not in the captured manifest: tests/speckit-pro/unit/test-native-eval-codex-rollouts.py (16 loaded cases), tests/speckit-pro/unit/test-native-eval-execution.py (9 loaded cases), and tests/speckit-pro/unit/test-native-eval-trigger.py (10 loaded cases). Their semantics were not reviewed in this lane. The seven earlier native-eval files are now registered and appear as unreviewed Layer 4 families in the ledger. Until the integration owner registers or explicitly defers the three post-baseline files, Layer 4 cannot claim to execute those 35 cases.

### 2. Codex agent-profile blind spot — remediated

The prior validator listed 10 Codex profiles while the shipped directory contained 12 TOML agents. Temporary-copy negative controls proved artifact-author and uat-runbook-author corruption passed.

Replacement proof: the validator now requires the directory, exact equality with a 12-role policy matrix, every expected file, all existing generic fields/cross-host checks, and exact model/effort/sandbox values per role. The new corruption, missing-directory, and unknown-role regressions pass; validate-agent-contracts reports 389/389 and test-structural-regressions reports 9/9.

### 3. Layer 5 exhaustive fail-closed matrix — remediated

artifact-author is absent from every Layer 5 role-specific tuple even though its Claude definition denies Skill, Agent, and SendMessage and its Codex definition declares workspace-write. An invalid artifact-author sandbox passed the Layer 5 Codex sandbox family in a temporary copy. Pointing the family at a missing Codex directory also passed.

Replacement proof: one exact 12-role matrix now checks directory existence, roster equality, every TOML file, and every sandbox value. artifact-author is covered on the Claude surface as a terminal mutating author that denies Skill, Agent, and SendMessage while retaining mutation tools. The missing-directory regression and the complete Layer 5 validator pass, 215/215.

### 4. Duplicate clarify-executor case — remediated

clarify-executor appears in CODEX_READ_ONLY_ROLES and is checked again by a dedicated block. The runtime therefore counts the same sandbox requirement twice.

Replacement proof: clarify-executor now appears once in the exact sandbox matrix. The requirement remains and is checked as read-only; only the duplicate subcase was removed.

### 5. Successful no-op branches — remediated

Nine current skills enter assertTrue(True) when references are not required, and the local payload run enters another assertTrue(True) for the GitHub-only diff check. Those ten counted units do not probe behavior.

Replacement proof: non-required skill reference checks no longer create nine successful subtests, and the GitHub-only payload diff check no longer creates a local successful subtest. Required reference checks and the CI check remain. validate-skill-contracts reports 618/618; validate-payload-contracts reports the expected 324/325 with only the pre-existing fingerprint mismatch red.

### 6. Current Layer 1 failure belongs to the concurrent dirty tree

Focused results were Layer 1: 7/8 executables, with 1,691/1,692 counted units passing; Layer 5: 1/1 executable and 215/215 units passing. The only red unit is the isolated payload rebuild fingerprint versus committed payload. This remains consistent with concurrent payload-affecting source edits and was not weakened or attributed to these reports.

## Disposition summary

- Keep: 46 of 49 deeply reviewed Layer 1 families and 8 of 10 deeply reviewed Layer 5 families.
- Replace: 5 families listed in deterministic-inventory.json; all five replacements are implemented with proof attached to the family records. The `replace` disposition is retained as the audit decision rather than rewritten as historical `keep`.
- Merge: none recommended from current evidence.
- Remove: no executable or requirement recommended for removal. One duplicate clarify-executor subcase should disappear inside the Layer 5 replacement.
- Unreviewed: all 1,615 Layer 4 loaded families and all 35 currently unregistered native-eval families.

## Skips and preview modes

Layers 1 and 5 had zero runtime skips in the focused runs. Layer 4 contains 141 static skipTest call sites and 31 skip-decorated declared test functions, but runtime skip counts are intentionally unknown. The inventory separately flags 26 Layer 4 case names that explicitly mention preview or dry-run. Mere source mentions of words such as public_preview are not counted as preview-mode families.

## Registration and generated-reference follow-up

The audit JSON and Markdown are reports, not executables, so they do not need suite-manifest registration. However, tests/speckit-pro/AGENTS.md requires docs-site test-reference regeneration or checking after a Markdown change under this tree. That generated file is outside this worker's ownership and must be handled by the parent/integration owner.

## Reproduction evidence

- Layer 4 baseline: HEAD e1536a7a2f4b9b54fc88d357d01c4d8ea5fe46e6; suite manifest SHA-256 599aa951d91401951922214096fde4aac57389d1392694b5e25496bfc980dd4a; registered source-set SHA-256 d1eb9418f8d7b04e13a233f95eaa3f8db0025a2ded74e2b1983eef8bc74c7392; unregistered source-set SHA-256 9f6b88c2045e15317a8fe05a61f5c96796ef4e07ae72b90c654250fbd74cf2fa.
- Reviewed-layer remediation snapshot: 2026-09-15T17:19:28Z; Layer 1/5 source-set SHA-256 a8814e2c30c29dbc05486e2b0347f65bcc7541eb4a81ea5104a4030b642614e3 (sorted newline-delimited `path<TAB>source_sha256` rows, including the final newline).
- The baseline was frozen at 2026-09-15T17:00:57Z. Source bytes for test-native-eval-entrypoint.py, test-native-eval-codex-rollouts.py, and test-native-eval-trigger.py changed afterward and are recorded as post-snapshot observations instead of silently changing the counts.
- Focused commands: Python 3.12 run-layer-scripts.py for Layers 1 and 5.
- Focused temporary negative controls changed only copies under temporary directories.
- Layer 4 suite construction was inspected without running test bodies to identify the original 1,516 loaded case methods; the 99 subsequently registered native-eval methods were added by exact source enumeration and remain explicitly unreviewed. Across the frozen snapshot, 26 test-shaped support methods are not loaded.
- The full per-executable and per-case-family ledger, paths, symbols, lines, parameter sources, static assertions, subtest sites, skips, preview flags, dispositions, and replacement text is in deterministic-inventory.json.
