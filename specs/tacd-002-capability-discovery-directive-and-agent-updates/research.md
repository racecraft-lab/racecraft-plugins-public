# Phase 0 Research: TACD-002 Capability Discovery Directive and Agent Updates

## Decision: Use One Shared Directive As The Source Of Truth

**Decision**: Create or update `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` as the shared directive for capability-first research and context selection.

**Rationale**: The TACD-002 design concept chooses **"Shared reference"** and records the directive-home decision as a shared capability-discovery reference plus runtime-specific pointers or approved equivalents. The TACD-001 spike recommends the same structure to reduce semantic drift while allowing Claude and Codex loading differences.

**Alternatives considered**:

- Runtime-specific directive copies: rejected for TACD-002 because it increases drift risk before TACD-004 adds checks.
- Inline-only agent guidance: rejected because six Claude and six Codex agents would duplicate the behavior contract.

## Decision: Scope Active Behavior Guidance Only

**Decision**: Limit implementation to the six active Claude Markdown agents, six matching Codex TOML agents, narrow active references in `consensus-protocol.md` and `gate-validation.md`, and source-derived generated payloads.

**Rationale**: The design concept says TACD-002 prioritizes agent guidance and leaves prerequisite messaging, plugin limitation wording, and public docs advisory language to TACD-003 unless an agent reference needs a narrow behavior pointer.

**Alternatives considered**:

- Include prerequisite checks and user-facing docs now: rejected because TACD-003 owns that slice.
- Include deterministic checks and functional eval updates now: rejected because TACD-004 owns enforcement after final behavior and messaging settle.

## Decision: Allow Runtime-Specific Pointers And Approved Equivalents

**Decision**: Claude agents and shared skill references should point to `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`. Codex skill payload references may use payload-builder-rewritten paths. Installed Codex TOML agents may embed compact equivalents with source-note markers when a direct Markdown pointer would break after install.

**Rationale**: Clarify resolved this runtime policy, and TACD-001's platform mechanics matrix records that Claude and Codex have different loading and dependency models. The shared behavior must remain aligned even when pointer mechanics differ.

**Alternatives considered**:

- Force direct Markdown pointers everywhere: rejected because installed Codex TOML agents may not resolve source-tree paths.
- Embed the full directive everywhere: rejected because it undermines the shared-reference design and increases review surface.

## Decision: Preserve Schema-Required Metadata IDs

**Decision**: Preserve metadata IDs such as Codex dependency values in `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml` and Claude frontmatter `tools:` allowlist IDs, while rewriting body prose and Codex TOML developer instructions that express active preferred-tool behavior.

**Rationale**: The design concept chooses **"Preserve metadata"** where schemas require concrete identifiers, and Clarify classifies metadata fields separately from behavior surfaces. The TACD-001 allowlist recommends reviewing metadata rather than blocking exact IDs blindly.

**Alternatives considered**:

- Replace all exact IDs with generic categories: rejected because some runtime schemas and allowlists require concrete identifiers.
- Keep all named-tool references: rejected because active behavior wording must stop privileging named optional MCPs.

## Decision: Require Compact Evidence Wording

**Decision**: Discovery-informed answers must use:

`Capability path: <need> -> <selected capability/source>; Evidence: <citations or local file refs>; Confidence: <high|medium|low> (<brief reason>)`

Fallback wording must disclose missing or unusable installed capabilities and lower confidence:

`No installed <capability> was available/usable; used <local/native/repo-local fallback>; confidence is <medium|low> because <reason>.`

**Rationale**: Clarify selected the exact evidence wording, and the design concept chooses **"Capability path plus confidence"**. This gives reviewers behavior-observable output without dumping full installed-tool inventories.

**Alternatives considered**:

- Full inventory reports: rejected for normal answers because they add noise and may expose environment-specific tool lists.
- Citations only: rejected because fallback confidence and capability selection would remain implicit.

## Decision: Regenerate Generated Payloads From Source

**Decision**: Edit source guidance under `speckit-pro/` and refresh generated payloads with `bash scripts/build-plugin-payloads.sh`. Record paired source and `dist/**` diffs, run `bash tests/speckit-pro/run-all.sh`, and run a second rebuild to check for unintended additional changes.

**Rationale**: The design concept chooses **"Regenerate from source"**, and Clarify names `bash scripts/build-plugin-payloads.sh` as the refresh command. Generated payloads are install-facing copies, not durable source.

**Alternatives considered**:

- Patch generated payloads directly: rejected because it breaks source-of-truth traceability.
- Skip generated payloads until release automation: rejected because TACD-002 acceptance requires source and generated install surfaces to match.

## Decision: Keep TACD-004 Enforcement Deferred

**Decision**: TACD-002 will record ad hoc evidence only: directive file exists, payload refresh runs, source and generated payload surfaces contain the pointer or equivalent marker, and the default suite passes.

**Rationale**: The spec explicitly states TACD-004 owns final deterministic checks and eval coverage. TACD-002 must not add the final enforcement layer.

**Alternatives considered**:

- Add static pointer checks now: rejected because TACD-004 is sequenced after TACD-003 so checks can lock the final contract.
- Update Layer 3 evals now: rejected because prerequisite/user-facing messaging is still pending in TACD-003.
