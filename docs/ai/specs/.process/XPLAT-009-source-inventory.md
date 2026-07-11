# XPLAT-009 Source Inventory

Generated during the XPLAT-009 autopilot implementation run on 2026-07-07.

## Summary

- Source script inventory at scaffold time: 35 plugin-owned `.sh` files under
  `speckit-pro/`.
- Current source script inventory: `find speckit-pro -type f -name '*.sh'`
  returns zero files.
- Current generated payload script inventory:
  `find dist/claude/speckit-pro dist/codex/speckit-pro -type f -name '*.sh'`
  returns zero files.
- Final zero-Bash guard evidence:
  `docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json`.
- Final zero-Bash guard status: `pass`, `blocking_count: 0`,
  `script_file_count: 0`.
- Nonblocking findings are classified as `negative_policy` or
  `tool_declaration`; neither category is release-ready evidence.

## Deleted Source Scripts

| SHA-256 | Path |
|---|---|
| `057fff7f623cc943e2318af49668b54898219b3e9374fb7d6b4d2d37560d6b71` | `speckit-pro/codex-skills/install/scripts/install-codex-agents.sh` |
| `22186242857f61932b0caec95007ef9e7b012e20f5d794b0a776344189755e65` | `speckit-pro/scripts/install-curated-set.sh` |
| `9b99d5763708754a9cadededaa2d8de4b05dd22798dff48dfcbb824a5fbc3f73` | `speckit-pro/skills/speckit-autopilot/scripts/aggregate-crl.sh` |
| `a88d315912c71e98c4a76b0fb3782ffec9991e704b9bc7483be1244579b470fb` | `speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh` |
| `03a59b005e7e19762610dfe5e2b37e5a25b8d9f2993eb0c1057988bf52ba7864` | `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh` |
| `b9313e128cdb4f165cb876eda2cb306c999167ad036fdf786bfbd508ada7245f` | `speckit-pro/skills/speckit-autopilot/scripts/confidence-gate.sh` |
| `fc93457b3daf0461abc2026f7f0411bde7abcb4c2e0c2d9ab6d5b4fff041c3f3` | `speckit-pro/skills/speckit-autopilot/scripts/count-markers.sh` |
| `105207afc13d0780da8b4fd419ddbffca5e487332e4496db99bcf66cbb09f1df` | `speckit-pro/skills/speckit-autopilot/scripts/detect-commands.sh` |
| `defd8688d440b899c8118f58735770723cbbbe04720951c75a8c94db466d48b4` | `speckit-pro/skills/speckit-autopilot/scripts/detect-presets.sh` |
| `76b22a4d8e8bc0a31ef428a2a7e5b527d0ba74409f0898ef9a683e09c2d738f9` | `speckit-pro/skills/speckit-autopilot/scripts/detect-stack-manager.sh` |
| `2d15c9bdfce6c41c1b4899b6e0a757fec9824ddb7e6fab83132dfbd441bff9b1` | `speckit-pro/skills/speckit-autopilot/scripts/estimate-reviewable-loc.sh` |
| `9e2d9d049a4f815a34e26e6ef8d2a0a744bb2a9469f5420ac55fd04cb2f629fb` | `speckit-pro/skills/speckit-autopilot/scripts/final-reviewability-backstop.sh` |
| `021abdc95e7bede7a647f47e8ae6e877877583fa2485d2da88f506a6bf864f98` | `speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh` |
| `3971b8da9ddd7eefa7c4c02f9e9e68247c8e98d5b455ddab2402faa5efd1618d` | `speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh` |
| `97de74dccd7c6de8f634a79ea54d3ad97c5929d516e892e58a782d2681f1e10e` | `speckit-pro/skills/speckit-autopilot/scripts/generate-uat-skeleton.sh` |
| `46d90d6a401fdf0982a1204258af82c82fd770eb0a652fb76bcbfdbe0a7d4e9d` | `speckit-pro/skills/speckit-autopilot/scripts/lib/moc-frontmatter.sh` |
| `38d7d9658260fcbc69c91ab56b4cb337c372d8d6b477cef7314b6b62b1d66e30` | `speckit-pro/skills/speckit-autopilot/scripts/lib/moc-id-normalize.sh` |
| `e4852637984591abbf07818be8db9a8e5d556cc8d4bfb9e782360696e9c537b2` | `speckit-pro/skills/speckit-autopilot/scripts/lib/specify-cli.sh` |
| `96fe8dbe12f50389b47210f1151e132eec042d3bad5e64e6d6d35175c4180d3d` | `speckit-pro/skills/speckit-autopilot/scripts/migrate-structure.sh` |
| `b6640479c8e59ada5b8122fc65b60289c71adfb9d2de794722c5f316b60d94b1` | `speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh` |
| `c3b477010cea479f86a35a648cb9138e386e02a850b0731f0ce0463e4ca448b4` | `speckit-pro/skills/speckit-autopilot/scripts/o5-topology.sh` |
| `2d08384cef3752268b48b01ef341e283b7ca827eb2407056e79f6190c5ea26aa` | `speckit-pro/skills/speckit-autopilot/scripts/parse-consensus-categories.sh` |
| `36dba581521736c95e14700c457e721310da4bdfe9dc9333af301ae0a5ae6ad8` | `speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh` |
| `37846778edfd0d3e74bbebb76b52d5f223e2076bfe6d22ba305ffe94ead09262` | `speckit-pro/skills/speckit-autopilot/scripts/relocate-process-artifacts.sh` |
| `9764c4e5f96b058c17431775c3612df15fa7240beb4ef5646362fc72f9c86808` | `speckit-pro/skills/speckit-autopilot/scripts/resolve-confidence-mode.sh` |
| `3b838ae1d9d5954ee59b87b3a13c72ab1e3c08e016e1179540f83eabe5c563ec` | `speckit-pro/skills/speckit-autopilot/scripts/restack.sh` |
| `86f9e50d53affc2fffe04299c4688038137ac5ce58a7d98bd4f9a539a3a3e6b8` | `speckit-pro/skills/speckit-autopilot/scripts/reviewability-gate.sh` |
| `91413b579ac6b9d69e40450b7cbd654a5ba3f217511da5bdda45a61886dfa793` | `speckit-pro/skills/speckit-autopilot/scripts/validate-agent-install.sh` |
| `11ca38232c0021faa6fbedcf9087f33fcc2f46a3536e6985e63a6baa79da1fbe` | `speckit-pro/skills/speckit-autopilot/scripts/validate-gate.sh` |
| `b801b5015c44cea158e5906e40f6b540138229127996f11ac859da953b878cb4` | `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-packet.sh` |
| `c9b0f1bbacf63ef3f03da4cb1d068adb43477c438679afff5fe7b72509cd2d22` | `speckit-pro/skills/speckit-autopilot/scripts/validate-pr-workflow-contract.sh` |
| `a5fb8e96731b7e07204dfe744c1d7cf989f04a01fa44722843ddf7b4664ed71c` | `speckit-pro/skills/speckit-autopilot/scripts/validate-uat-runbook.sh` |
| `1c59084db2c92a910782f89e0028470c46a188d9756dd686107857277919f398` | `speckit-pro/skills/speckit-coach/scripts/ensure-reviewability-preset.sh` |
| `9f2b00b9c5e1ac3247203c55a349575098caef9384d92c47a05f8ea2649aad7c` | `speckit-pro/skills/speckit-coach/scripts/estimate-spec-size.sh` |
| `2dd754623bdfe19863c71e819d2b52bb1574ee4d4ae97acbecb2d02eaf78147c` | `speckit-pro/skills/speckit-coach/scripts/project-fixup.sh` |

## Python Ownership Mapping

| Prior script group | Current owner |
|---|---|
| Read-only helper operations | `speckit-pro/speckit_pro_runner/helpers/read_only.py` plus `helpers/registry.py` expose Python operation IDs and no runnable shell paths |
| Mutation/install/PR-emission operations | `speckit-pro/speckit_pro_runner/helpers/install.py`, `helpers/pr_emission.py`, `helpers/mutation.py`, and `helpers/registry.py`; obsolete live shell behavior is delete-only or deferred command-plan provenance |
| Active source and payload guard | `speckit-pro/speckit_pro_runner/gates/active_path_guard.py` and `gates/registry.py` implement `active-path-guard` / `zero-bash-guard` |
| Payload completeness | `speckit-pro/speckit_pro_runner/gates/payloads.py` records source roots, transform records, tree hashes, path leaks, and `script_file_count` |
| Release readiness | `speckit-pro/speckit_pro_runner/gates/release.py` projects payload and active-runtime evidence through the release-readiness gate |
| Runner metadata | `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json` and `.sha256` record Python runner source hashes |
| MOC structural validators | `tests/speckit-pro/layer1-structural/validate-moc-orphan.sh` and `validate-moc-stale-index.sh` are now self-contained test validators and no longer source deleted plugin Bash libraries |
| Spec-index active contract | `tests/speckit-pro/layer1-structural/validate-spec-index-determinism.sh` now verifies Python runner `generate-spec-index-check` and deferred write-mode registry state |

## Verification

- `python3 -m py_compile speckit-pro/speckit_pro_runner/gates/active_path_guard.py speckit-pro/speckit_pro_runner/gates/release.py`
- `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py` -> `33/33 passed`
- `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py` -> `17/17 passed`
- `PYTHONPATH=speckit-pro python3 tests/speckit-pro/unit/test-speckit-pro-gates.py` -> `48/48 passed`
- `bash tests/speckit-pro/unit/test-privacy-scan.sh` -> `10/10 passed`
- `bash tests/speckit-pro/run-all.sh --layer 1` -> `1326/1326 passed`
- `bash tests/speckit-pro/run-all.sh` -> `2021/2021 passed`

## Evidence Files

- Payload completeness:
  `docs/ai/specs/.process/XPLAT-009-payload-completeness-result.json`
- Installed-cache proof:
  `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json`
- Zero-Bash guard:
  `docs/ai/specs/.process/XPLAT-009-zero-bash-guard-result.json`
- Release readiness:
  `docs/ai/specs/.process/XPLAT-009-release-readiness-result.json`
