# Quickstart: Claude/Codex Cutover and Universal Install Release Gate

This quickstart is for maintainers implementing XPLAT-008 after Plan approval. It follows the accepted three-slice strategy and keeps implementation code changes out of the Plan phase.

## 1. Confirm the planning baseline

```bash
git status --short
sed -n '1,220p' specs/xplat-008-claude-codex-cutover-universal-install-release-gate/spec.md
sed -n '1,220p' specs/xplat-008-claude-codex-cutover-universal-install-release-gate/plan.md
```

Expected result:

- `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, and `contracts/` exist.
- No unresolved clarification marker remains.
- The reviewability warning is accepted with three internal slices.

## 2. Slice 1 - Cut over active installed-runtime surfaces

Implementation focus:

- Classify Claude and Codex skills, agents, hooks, install guidance, generated runtime payloads, release gates, archive/provenance text, CI dispatch glue, tests/fixtures, docs prose, and upstream Spec Kit generated helpers.
- Update active installed-runtime surfaces to resolve Python `>=3.11` and invoke `[resolved_python, "-m", "speckit_pro_runner"]`.
- Add or update active-runtime no-shell/no-jq guard fixtures so prohibited shell-only behavior fails in active runtime scope.

Verification focus:

```bash
python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/active-runtime-request.json
bash tests/speckit-pro/run-all.sh --layer 1
python3 tests/speckit-pro/layer4-scripts/test-speckit-pro-gates.py
```

Expected result:

- Active runtime surfaces use the Python runner path.
- Archive/provenance, CI dispatch glue, tests/fixtures, docs prose, and upstream generated helpers are not false positives.
- No active installed-runtime path requires Bash, Git Bash, WSL, PowerShell-specific command language, shell interpolation, redirection, Unix-only paths, or `jq`.

## 3. Slice 2 - Rebuild payloads and gate public claims

Implementation focus:

- Rebuild Claude and Codex generated payloads from source.
- Add payload completeness checks for manifests, skills, bundled agents, hooks, runner package files, runner manifest/checksum records, version metadata, and XPLAT-003 trust records.
- Add release-readiness blockers for stale payloads, missing payload items, path leaks, non-deterministic output, version mismatches, unsafe public claims, and missing trust evidence.
- Update public install, first-run, troubleshooting, trust, and release wording to describe implemented controls only.

Verification focus:

```bash
python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/payload-completeness-request.json
python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/release-readiness-request.json
pnpm --dir docs-site validate
```

Expected result:

- Claude and Codex payload gates pass for complete, current, source-derived payloads.
- Seeded missing/stale/unsafe claim cases fail with blocking diagnostics.
- Public docs do not claim unimplemented cryptographic guarantees or unproven native support.

## 4. Slice 3 - Fill native UAT, update, and repair evidence

Implementation focus:

- Create `specs/xplat-008-claude-codex-cutover-universal-install-release-gate/.process/uat-matrix.md`.
- Fill six rows: Claude on Windows, Claude on macOS, Claude on Linux, Codex on Windows, Codex on macOS, and Codex on Linux.
- Prove install, bundled-agent verification, first use, scaffold/status, autopilot dry-run, latest-tag update, and incomplete-install repair.
- Add doctor/autoheal evidence for trusted missing/stale artifacts and manual remediation evidence for unsafe drift.

Verification focus:

```bash
python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/uat-matrix-request.json
python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/install-health-request.json
python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/release-readiness-request.json
```

Expected result:

- Release-readiness fails while any required UAT row is missing, placeholder-only, smoke-only, or failing.
- Trusted missing/stale cache artifacts are repaired only when path, source identity, release channel/latest tag, and digest verify.
- Unsafe drift produces exact manual remediation and does not trigger broad reinstall behavior.

## 5. Final release-readiness review

Run the narrowest source-backed checks first, then the broader suite:

```bash
python3 -m speckit_pro_runner < tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release/release-readiness-request.json
bash tests/speckit-pro/run-all.sh --layer 1
bash tests/speckit-pro/run-all.sh --layer 4
bash tests/speckit-pro/run-all.sh
```

PR packet must include:

- What changed and why.
- Non-goals.
- Review order.
- Scope budget and accepted warning.
- Traceability from each major requirement and success criterion to changed files and verification evidence.
- Native UAT evidence links.
- Known gaps and rollback or feature-flag notes.

Release remains blocked until the release-readiness aggregate passes with zero blocking checks.
