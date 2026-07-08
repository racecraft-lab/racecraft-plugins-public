# Quickstart: XPLAT-009 Plan Verification

This quickstart defines the intended maintainer flow after implementation tasks
are generated. It uses Python runner operations as the source of truth.

## 1. Verify Slice 1 Source Cleanup

1. Confirm the source inventory evidence exists at
   `docs/ai/specs/.process/XPLAT-009-source-inventory.md`.
2. Confirm every active source script record is either Python-owned or
   delete-only obsolete.
3. Run the focused read-only helper, mutation helper, and gate tests that Tasks
   assigns to Slice 1.
4. Confirm `speckit-pro/` contains zero `.sh` files.
5. Run the zero-Bash guard request for `speckit-pro/` and confirm
   `blocking_count` is `0`.

Expected Slice 1 result: active plugin source no longer depends on Bash,
`.sh`, `jq`, shell interpolation, Git Bash, WSL, PowerShell-specific command
language, or Unix-only guidance.

## 2. Rebuild Payloads From Source

1. Run `payload-gate/payload-completeness` in apply mode using the XPLAT-009
   request fixture.
2. Confirm the apply result writes both generated payload roots from source.
3. Run the read-only payload-completeness check after apply mode.
4. Confirm the evidence records source roots, output roots, transform records,
   file-tree hashes, and zero missing/extra/mismatched/path-leaking files.
5. Confirm both generated payload roots contain zero `.sh` files.

Expected payload result: `dist/claude/speckit-pro/` and
`dist/codex/speckit-pro/` are source-derived and Bash-free.

## 3. Produce Bounded Installed-Cache Proof

1. Create the installed-cache proof from rebuilt payloads into a bounded fixture
   or temporary proof root.
2. Do not use a mutable real user cache as the required proof.
3. Confirm the proof includes product, installed root, source payload root,
   source payload hash, file inventory, `.sh` count, active-guidance finding
   counts, `source_derived: true`, and allowlist exclusion state.
4. Run the zero-Bash guard across source, generated payloads, and installed
   cache proof.

Expected proof result: installed-cache proof reports zero `.sh` files, zero
blocking active Bash guidance, and zero active `jq` requirements.

## 4. Verify Release Readiness Integration

1. Run the release-readiness fixture or live request assigned by Tasks.
2. Confirm release readiness blocks when scan roots are missing, installed-cache
   proof is missing, blocking findings exist, or allowlist entries are counted
   as release-ready proof.
3. Confirm historical/archive allowlist entries include path, reason, scope,
   category, and release-readiness exclusion.
4. Preserve XPLAT-008 native UAT rows as known release context and do not claim
   XPLAT-009 completes public native-platform readiness.

Expected release result: zero-Bash proof is required for XPLAT-009 readiness,
while XPLAT-008 native UAT remains a separate blocker.
