# Contract: Capability Discovery Guidance

## Scope

This contract defines the required behavior for TACD-002 active runtime guidance. It applies to:

- Six active Claude Markdown agents: `codebase-analyst`, `domain-researcher`, `clarify-executor`, `checklist-executor`, `analyze-executor`, and `implement-executor`.
- Six matching Codex TOML agents under `speckit-pro/codex-agents/`.
- Narrow active autopilot references in `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md` and `speckit-pro/skills/speckit-autopilot/references/gate-validation.md`.
- Generated payload copies under `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/` after source refresh.

## Directive Binding

Source guidance must use `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` as the shared directive path.

Acceptable runtime-specific forms:

- Claude agents and shared skill references point to the shared directive.
- Generated Codex skill payloads may use payload-builder-rewritten paths.
- Installed Codex TOML agents may embed a compact equivalent when direct Markdown pointer resolution would break.

Compact Codex TOML equivalents must include this exact source-note marker inside
`developer_instructions`:

`Capability discovery equivalent: mirrors speckit-pro/skills/speckit-autopilot/references/capability-discovery.md for installed Codex TOML runtime.`

## Capability Selection

Runtime guidance must instruct agents to:

1. Identify the needed capability category.
2. Select the best installed capability for that need using task fit, source authority/directness, freshness needs, expected evidence quality, and minimal necessary inventory disclosure.
3. Use formerly named tools only when discovery selects them as the best available capability.
4. Fall back to local files, native platform context, or repo-local helpers when optional capabilities are unavailable or unusable.

Capability categories are a taxonomy, not an ordered fallback chain. Guidance
must not replace a named-tool preference with a fixed vendor-neutral capability
order.

Required capability categories:

- codebase context
- spec context
- library documentation
- web or domain research
- source extraction
- installed skills/plugins
- repo-local helpers

## Required Evidence Output

Discovery-informed answers must include:

`Capability path: <need> -> <selected capability/source>; Evidence: <citations or local file refs>; Confidence: <high|medium|low> (<brief reason>)`

Fallback answers must include:

`No installed <capability> was available/usable; used <local/native/repo-local fallback>; confidence is <medium|low> because <reason>.`

## Inventory Disclosure

Normal answers must report only the selected capability path and any material fallback gap.

Full installed-capability inventories are allowed only when:

- directly requested,
- needed for troubleshooting, or
- required as PR evidence, such as the preserved-ID review table.

## Metadata Preservation

Exact IDs may remain when they are schema-required metadata rather than active preferred behavior.

Metadata examples:

- Codex dependency values in `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml`.
- Claude frontmatter `tools:` allowlist IDs such as `mcp__RepoPrompt__*`, `mcp__tavily-mcp__*`, and `mcp__context7__*`.
- Generated manifest or path rewrite metadata.

Behavior surfaces:

- Agent body text.
- Codex TOML `developer_instructions`.
- Shared reference prose.

The PR packet must include a preserved-ID table with file, field, classification, and behavior-scan result.

## Generated Payload Refresh

Generated payloads must be refreshed from source using:

```bash
bash scripts/build-plugin-payloads.sh
```

Required evidence:

- builder invocation,
- both payload roots present after generation,
- paired source and generated `dist/**` diff review,
- default verification with `bash tests/speckit-pro/run-all.sh`, and
- second rebuild with no unintended additional payload changes.

## Out Of Scope For This Contract

- TACD-003 prerequisite checks, user-facing setup messaging, public docs advisory language, and plugin limitation docs except for narrow active behavior pointers.
- TACD-004 deterministic checks, static pointer enforcement, Layer 3 eval changes, or final tool-scoping enforcement.
