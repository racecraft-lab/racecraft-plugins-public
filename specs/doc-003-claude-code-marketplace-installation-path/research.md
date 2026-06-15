# Research: Claude Code Marketplace Installation Path

## Decision: Use official Claude Code docs plus repository source/generated payload citations

**Decision**: Cite official Claude Code documentation for platform behavior and repository-controlled files for Racecraft/SpecKit Pro-specific claims.

**Rationale**: Claude Code owns marketplace, plugin install, reload, lifecycle, and managed-setting behavior. Racecraft owns the marketplace catalog, SpecKit Pro manifest, shipped skills, agents, hooks, settings, and generated Claude payload shape. The docs route needs both authorities so users can distinguish platform behavior from this plugin's exact installation surface.

**Sources**:

- Official plugin marketplace behavior: `https://code.claude.com/docs/en/discover-plugins`
- Official plugin structure and namespaced skill behavior: `https://code.claude.com/docs/en/plugins`
- Official settings, scopes, plugin settings, and managed marketplace controls: `https://code.claude.com/docs/en/settings`
- Racecraft marketplace catalog: `.claude-plugin/marketplace.json`
- SpecKit Pro source manifest: `speckit-pro/.claude-plugin/plugin.json`
- SpecKit Pro source trust surfaces: `speckit-pro/skills/`, `speckit-pro/agents/`, `speckit-pro/hooks/hooks.json`
- Generated Claude payload: `dist/claude/speckit-pro/`

**Alternatives considered**:

- Repo-only citations: rejected because platform commands and lifecycle behavior can change outside this repository.
- Official-only citations: rejected because official docs cannot prove SpecKit Pro's exact marketplace entry, skill names, source files, or generated payload paths.

## Decision: Make `docs-site/src/content/docs/install/claude-code.md` the canonical user route

**Decision**: Put the full ordered install path, verification path, lifecycle guidance, and trust/reference section in the docs-site Claude install page.

**Rationale**: The existing docs site route is the user-facing install surface from DOC-002. Keeping the full procedure in one page lets a Claude Code user add the marketplace, install SpecKit Pro, reload plugins, verify namespaced skills, update, uninstall, and remove the marketplace without jumping across README fragments.

**Alternatives considered**:

- README-first install guide: rejected because it would duplicate or demote the docs-site install route.
- Split lifecycle and trust into separate first-pass pages: rejected because the design concept keeps DOC-003 as one vertical Claude install slice.

## Decision: Use skills terminology for install-relevant surfaces

**Decision**: Normalize install-facing wording around plugin skills and namespaced skill invocation, especially `/speckit-pro:speckit-status` and `/speckit-pro:speckit-coach`.

**Rationale**: The user chose broad consolidation on skills terminology because command-folder language is deprecated for this install path. Claude Code's plugin docs describe plugin namespacing and the current `skills/` layout, while this repository's current SpecKit Pro surface ships skills rather than command files.

**Alternatives considered**:

- Flag inconsistencies only on the install page: rejected by the user's Q2 decision.
- Rewrite every repository mention of historical command files: rejected as too broad for a docs-only install route unless the wording is install-relevant.

## Decision: Document lifecycle coverage without absorbing DOC-008

**Decision**: Cover add marketplace, install, reload, verify, marketplace update, plugin uninstall, marketplace removal, and reinstall checks. Keep detailed troubleshooting and rollback matrix content out of DOC-003.

**Rationale**: Claude Code users need lifecycle commands on the install route, but the design concept reserves full failure-mode troubleshooting for DOC-008. The route should explain the safe sequence and decision points, not enumerate every possible cache, policy, network, or rollback failure.

**Alternatives considered**:

- Install-only page: rejected because it would not satisfy lifecycle requirements.
- Full operations playbook: rejected because it would overlap with DOC-008 and expand the review surface.

## Decision: Put trust guidance in a Claude-specific section, bounded by source inventory

**Decision**: Include a deeper trust section that covers marketplace trust, skills, agents, hooks, settings/MCP implications, generated payloads, and managed marketplace controls, with links to official docs and repository paths.

**Rationale**: Installing plugins carries meaningful trust implications. Official Claude Code docs warn that plugins and marketplaces are highly trusted components and expose inventories through the plugin manager. The Racecraft docs should give evaluators a source-backed map before they run plugin skills.

**Alternatives considered**:

- Minimal trust note: rejected by the user's Q7 decision.
- Full troubleshooting/security matrix: rejected because DOC-008 owns that matrix.

## Decision: Validate as docs-only

**Decision**: Use `pnpm --dir docs-site validate` as the required validation command. Add `bash tests/speckit-pro/run-all.sh --layer 1` only if implementation changes plugin manifests, hooks, agents, skills, or generated payloads.

**Rationale**: The planned implementation changes Markdown documentation. Docs-site validation directly proves the route builds and its internal content constraints hold. Plugin structural validation is unnecessary if no plugin runtime/source/payload files change.

**Alternatives considered**:

- Always run Layer 1: unnecessary for docs-only changes and explicitly conditional in the workflow prompt.
- No validation: rejected by FR-014 and SC-005.

## Decision: Omit contracts

**Decision**: Do not create `contracts/`.

**Rationale**: DOC-003 exposes no software API, endpoint, CLI grammar, schema, or parser interface. The user-facing behavior is documentation guidance, captured by `quickstart.md` validation scenarios and the changed docs page.

**Alternatives considered**:

- Create a Markdown contract for the install page: rejected because it would duplicate the spec and quickstart without adding a real interface contract.
