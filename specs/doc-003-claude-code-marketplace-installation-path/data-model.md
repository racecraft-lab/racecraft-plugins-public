# Data Model: Claude Code Marketplace Installation Path

DOC-003 is documentation-only. These entities describe the planned documentation concepts and validation relationships; they do not create runtime data storage.

## Claude Install Route

**Purpose**: Canonical docs-site page for Claude Code users installing and managing SpecKit Pro from the Racecraft marketplace.

**Fields**:

- `path`: `docs-site/src/content/docs/install/claude-code.md`
- `audience`: Claude Code users and evaluators
- `sections`: trust overview, prerequisites, sequential install procedure, verification, lifecycle maintenance, source/reference inventory, Codex cross-link
- `non_goals`: Codex install instructions, full DOC-008 troubleshooting matrix, runtime behavior changes, generated payload regeneration
- `validation`: `pnpm --dir docs-site validate`

**Relationships**:

- Contains one Lifecycle Command Set.
- Contains one Trust Surface Inventory.
- Contains one Source and Generated Path Map.
- Links to the separate Codex install route at `/install/codex/`.

## Lifecycle Command Set

**Purpose**: User-facing command sequence for adding the marketplace, installing SpecKit Pro, reloading, verifying, updating, uninstalling, marketplace removal, and reinstalling.

**Fields**:

- `command`: exact command shown to the user
- `action`: add marketplace, install plugin, reload plugins, verify plugin UI, verify status skill, verify coach skill, update marketplace, uninstall plugin, remove marketplace, reinstall
- `sequence_position`: install and lifecycle order
- `source_authority`: official Claude Code docs for platform behavior, repository files for SpecKit Pro plugin name and marketplace name
- `expected_signal`: plain-language result that indicates success
- `scope_note`: user/project/local/managed scope caveat where relevant

**Validation Rules**:

- Every command shown on the Claude route must have source backing.
- Install commands must appear in one sequential procedure section before lifecycle maintenance.
- Verification must include `/plugin`, `/speckit-pro:speckit-status`, and `/speckit-pro:speckit-coach`.
- Lifecycle guidance must distinguish plugin uninstall from marketplace removal.

## Trust Surface Inventory

**Purpose**: Source-backed review map for evaluators deciding whether to install or run SpecKit Pro skills.

**Fields**:

- `surface_type`: marketplace catalog, plugin manifest, skills, agents, hooks, settings/MCP implications, generated Claude payload
- `source_paths`: repository authoring paths
- `generated_paths`: generated Claude payload paths, where applicable
- `review_question`: what an evaluator should inspect before running plugin skills
- `risk_note`: plain-language trust implication
- `authority_link`: official Claude Code docs or repository path

**Validation Rules**:

- Skills, agents, hooks, settings implications, and generated payload files must be identified.
- Source paths and generated payload paths must not be conflated.
- Trust guidance must be Claude-specific and must not expand into the full DOC-008 troubleshooting matrix.

## Source and Generated Path Map

**Purpose**: Maintainer-facing distinction between Racecraft authoring files and the generated Claude install payload.

**Fields**:

- `source_path`: authoring file or directory in the repository
- `generated_path`: generated Claude payload file or directory when present
- `purpose`: marketplace catalog, manifest, skill body, agent definition, hook configuration, shipped README, generated scripts
- `citation_role`: install authority, trust inventory, verification evidence, or generated-shape reference

**Validation Rules**:

- `.claude-plugin/marketplace.json` must be treated as the marketplace catalog source.
- `speckit-pro/.claude-plugin/plugin.json` must be treated as source manifest authority.
- `dist/claude/speckit-pro/` must be labeled generated payload, not authoring source.
- No implementation task may regenerate `dist/**`.

## Terminology Consistency Patch

**Purpose**: Install-relevant README/AGENTS wording corrections that remove command-vs-skill confusion.

**Fields**:

- `file`: `README.md`, `AGENTS.md`, `speckit-pro/README.md`, or the Claude install page
- `current_term`: deprecated or confusing install-relevant wording
- `replacement_term`: skills-based wording
- `rationale`: why the wording affects Claude install users
- `verification`: search or review evidence that no install-relevant contradiction remains

**Validation Rules**:

- Patch only install-relevant wording.
- Do not rewrite unrelated maintainer guidance.
- Preserve Codex scope for DOC-004.

## Lifecycle State Transitions

```text
not configured
  -> marketplace added
  -> plugin installed
  -> plugins reloaded
  -> installed surface verified
  -> marketplace/plugin updated
  -> plugin uninstalled
  -> marketplace removed, only if no longer needed
  -> reinstalled, if user chooses a clean reinstall
```

These transitions are documentation states, not application state.
