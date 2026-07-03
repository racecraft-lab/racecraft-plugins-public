# Research: XPLAT-005 Read-Only Helper Port

## Decision 1: Reuse The XPLAT-004 Runner Envelope

**Decision**: Add helper dispatch behind the existing `speckit-pro/speckit_pro_runner/` package and preserve the XPLAT-004 JSON envelope shape.

**Rationale**: The runner already owns stdin request parsing, JSON stdout response emission, diagnostics, runtime-info, preflight, and typed path primitives. Reusing it avoids a second helper runtime and keeps promoted helpers on Python 3.11+ standard library only.

**Alternatives considered**: A standalone helper CLI was rejected because it would duplicate envelope and diagnostic behavior. A Bash wrapper around Python was rejected because promoted helpers must not require Bash.

## Decision 2: Use A Small Explicit Registry

**Decision**: Add an explicit registry mapping helper ids to read-only callable targets and accepted operation metadata.

**Rationale**: XPLAT-006 needs a stable extension point, but XPLAT-005 should not introduce a generic plugin framework. A small table keeps dispatch reviewable and makes out-of-scope helpers obvious.

**Alternatives considered**: Dynamic module discovery was rejected because it obscures the review surface and could accidentally expose mutation helpers. One file per helper was rejected for XPLAT-005 because the accepted reviewability plan limits production-file growth.

## Decision 3: Promote Helpers Only After Golden And Bash-Reference Parity

**Decision**: Every promoted Bash-backed helper must pass deterministic golden fixture parity and source-checkout Bash-reference comparison before its Python test is marked authoritative.

**Rationale**: Golden fixtures catch expected behavior drift, while Bash-reference comparisons prove migration parity against the current helper implementation. Both are required to preserve stdout JSON schemas, stderr diagnostics, and exit-code semantics.

**Alternatives considered**: Golden-only promotion was rejected for Bash-backed helpers because it could encode the wrong expected behavior. Live Bash-only comparison was rejected because it would not prove deterministic no-Bash behavior for synthetic Windows/no-Bash/path cases.

## Decision 4: Limit Golden-Only Fixtures To Runner And Synthetic Safety Cases

**Decision**: Golden-only fixtures are allowed only for runner envelope/registry dispatch, typed-path and subprocess safety, malformed runner requests, synthetic Windows/no-Bash/path cases, and normalization unit tests.

**Rationale**: These cases either do not have a Bash reference or intentionally model environments where Bash cannot run. All Bash-backed helper behavior still needs Bash-reference comparison.

**Alternatives considered**: Requiring Bash comparison for synthetic no-Bash fixtures was rejected because the fixture purpose is to prove behavior without Bash. Allowing golden-only helper promotion was rejected because it weakens migration proof.

## Decision 5: Normalize Only Environment-Sensitive Fields

**Decision**: Normalize repo/worktree absolute paths to repo-relative paths, temp paths to stable placeholders, executable paths or versions when not fixture-controlled, platform/runtime identity fields, and branch/worktree metadata only when a test intentionally uses live git state.

**Rationale**: These fields vary across source checkouts and platforms. Counts, booleans, statuses, diagnostic codes, route/status enums, public text, stderr diagnostics, and exit codes remain exact unless a helper-specific rule lists the field as normalized.

**Alternatives considered**: Raw byte-for-byte JSON comparison was rejected because absolute paths and runtime metadata would create false failures. Broad normalization was rejected because it could hide behavior drift.

## Decision 6: Keep One Workflow With Two Internal Slices

**Decision**: Keep XPLAT-005 as one workflow with Slice 1 for registry/prereq/status helpers and Slice 2 for index/topology/planning validators plus late read-only PR-packet validation.

**Rationale**: The setup reviewability gate warned but passed. The plan keeps the implementation to four production files and twelve total planned files after runner source metadata updates, with helper evidence organized by matrix rows.

**Alternatives considered**: Child specs were rejected because planning does not prove a split is required. A single undifferentiated implementation slice was rejected because reviewers need to inspect foundational helper parity before later planning and PR-packet validation ports.

## Decision 7: Preserve Bash Helpers As Temporary References

**Decision**: Current Bash helpers stay in place through XPLAT-005, both for unported/out-of-scope behavior and as temporary reference implementations for ported helpers until XPLAT-007 cutover.

**Rationale**: XPLAT-005 proves parity but does not change active invocation paths. Keeping Bash references reduces release risk and prevents public support claims before installed-cache and native matrix proof.

**Alternatives considered**: Removing Bash helpers was rejected because active cutover belongs to XPLAT-007. Updating active Claude/Codex command surfaces was rejected because the accepted scope is ports and tests only.

## Decision 8: Source-Checkout Smoke Is Runtime-Info Only

**Decision**: The local smoke command is limited to the source-checkout `runtime-info` request through `PYTHONPATH=speckit-pro python3 -m speckit_pro_runner`.

**Rationale**: This proves the local runner launches, accepts the JSON envelope through stdin, emits JSON stdout, reports `status: ok`, reports `source_vs_installed_context: source_checkout`, and exposes runtime metadata. It does not claim installed-cache launch or full native matrix support.

**Alternatives considered**: Installed-cache launch proof and Windows/macOS/Linux native matrix UAT were rejected because they are XPLAT-007 responsibilities.
