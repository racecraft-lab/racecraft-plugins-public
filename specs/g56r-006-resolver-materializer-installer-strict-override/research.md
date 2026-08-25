# Research: Capability-aware Resolver, Materializer, Installer, and Strict Override

## Decision: Explicit Trusted Manifest Activates Route-aware Mode

Route-aware installation activates only when the request supplies a path that the existing trusted-file boundary resolves to a non-symlink regular file inside the current repository. The closed `1.0.0` manifest recomputes its manifest identity, binds the current strict 13-TOML source roster by canonical filename/original-byte digests, and declares exactly 12 required policies plus the optional helper/no-helper state.

**Rationale**: The Design Concept says route-aware activation is an ["Explicit policy manifest"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) and the spec requires no-manifest requests to preserve the existing static response. A path-based manifest keeps provenance inspectable and avoids widening the runner input to inline policy objects.

**Alternatives considered**:

- Inline policy object: rejected because it widens the public input surface and weakens provenance.
- Inferred bundled defaults: rejected because G56R-006 must not qualify production routes or infer model/effort from source TOMLs.
- Always route-aware: rejected because downstream final policies and default activation belong to later specs.

## Decision: One Runner-owned Observation Adapter and One Batch Snapshot

`helpers/install.py` owns an injectable capability-observation adapter. Route-aware execution captures one fresh snapshot at invocation start; any bounded availability probe is recorded as child evidence of that same snapshot.

**Rationale**: The Design Concept requires ["One injectable runner-owned adapter"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions) and ["One fresh batch snapshot"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions). This keeps production discovery behind a real boundary while allowing deterministic test injection.

**Alternatives considered**:

- Caller-supplied snapshots: rejected because freshness and probe responsibility move outside the installer.
- Per-agent snapshots: rejected because one atomic install decision could depend on inconsistent availability states.
- Fixture booleans in production: rejected because G56R-005 was only a simulator.

## Decision: Extend Canonical Materializer

`agent_materialization.py` will render the selected explicit model and reasoning effort into destination bytes while preserving original source-byte binding and proving non-route fields unchanged.

**Rationale**: The Design Concept says ["Extend canonical materializer to render and prove the selected route"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions). This keeps G56R-003 source identity authoritative and avoids treating rewritten destination bytes as source.

**Alternatives considered**:

- Separate renderer before materialization: rejected because identity boundaries become ambiguous.
- Regex-only install rewrite: rejected because it lacks resolved-policy identity and non-route drift proof.

## Decision: Complete Required Diagnostics Before Mutation

Normal mode evaluates preferred route then ordered fallbacks for all 12 required agents in stable roster order. Strict override mode evaluates exactly one override-derived tuple per required agent. Any required miss empties planned writes and removals but still returns all read-only diagnostics.

**Rationale**: The Design Concept requires ["Resolve all required agents, return all attempts, zero writes on any required miss"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions). This prevents one failed run from hiding the rest of the incompatibility set.

**Alternatives considered**:

- Stop at first required miss: rejected because it makes retries less reproducible.
- Continue into partial writes: rejected because required-agent installation must be atomic.

## Decision: Strict Override Does Not Fall Back

When `strict_model_override` is present, required agents evaluate only the override model with each agent's explicit effort and non-route contract. The helper uses the override only when compatible; otherwise validated no-helper wins.

**Rationale**: The Design Concept says ["Required agents are strict; matching helper override installs, incompatible helper uses no-helper"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions). This preserves strictness for required agents without letting optional helper failure block a fully resolved required roster.

**Alternatives considered**:

- Preferred/fallback after override miss: rejected because it silently weakens the override.
- Helper miss fails required batch: rejected because helper optionality is destination-only.
- Arbitrary effort map: rejected as out of scope.

## Decision: Managed Helper Removal Requires Byte or Provenance Proof

Route-aware apply may remove an existing optional helper only when trusted runner-owned provenance binds the installed file, or when the current bytes exactly match a known rendered helper digest from the trusted source and manifest.

**Rationale**: The Design Concept requires ["Provenance or known-byte proof required"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions). Helper removal is destructive and must not delete a user-modified same-named file.

**Alternatives considered**:

- Filename match: rejected because it can delete user-owned files.
- Parsed TOML equivalence: rejected because normalization can hide byte-level user edits.
- Never remove: rejected because a stale plugin-managed helper would weaken a validated no-helper state.

## Decision: One Rollback-backed Mutation Batch

After route-aware resolution and materialization succeed, apply writes and managed-helper removal execute as one rollback-backed batch. Prior bytes and file modes are captured before mutation, and rollback verifies final state against pre-state identities.

**Rationale**: The Design Concept says ["Complete plan first, rollback-backed batch apply"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions). The existing installer already has rollback-oriented helpers, so the simplest safe path is to extend them.

**Alternatives considered**:

- Directory swap: rejected because the destination can contain unrelated user-owned agents.
- Per-file commits: rejected because partial installation violates required-batch semantics.

## Decision: Deterministic Fake-home Acceptance Only

All acceptance evidence uses injected capability/probe fixtures and fake-home destination state. Live model calls, real user-home writes, and installed-runtime UAT are deferred.

**Rationale**: The Design Concept requires ["Deterministic fixtures and fake homes only"](../../docs/ai/specs/.process/G56R-006-design-concept.md#decisions). This makes CI proof stable and leaves live route UAT to G56R-011.

**Alternatives considered**:

- Live discovery smoke: rejected for G56R-006 because it makes the framework slice environment-dependent.
- Real-home install: rejected because user-home mutation belongs outside this acceptance boundary.

## Decision: Generated Payload and Docs Refresh Are Follow-through, Not New Architecture

Production runner and Codex skill changes require regenerated `dist/` mirrors, installed-cache fixture mirrors, and docs reference output. These outputs are declared in the plan but should be refreshed by repository tooling, not hand-edited as primary design surfaces.

**Rationale**: Repository rules require generated payloads and docs references to be refreshed after source/test/doc inputs change. G56R-006 must account for them without treating generated outputs as independent implementation logic.

**Alternatives considered**:

- Hand-edit generated payloads: rejected because generated artifacts are a function of source.
- Skip generated/reference refresh: rejected because Layer 1 and docs reference checks can fail on stale outputs.
