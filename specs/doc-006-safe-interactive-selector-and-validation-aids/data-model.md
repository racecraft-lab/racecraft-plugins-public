# Data Model: Safe Interactive Selector and Validation Aids

## SelectorPath

Represents one supported platform and install-scope path shown on `choose-your-path`.

Fields:

- `id`: Stable kebab-case identifier for filtering and tests.
- `platform`: `claude-code` or `codex`.
- `scope`: Install scope label such as repository, user, marketplace, or not applicable.
- `label`: Human-readable path label.
- `prerequisites`: Static prerequisite notes.
- `commands`: Ordered `CommandGuidance` records.
- `successSignals`: Observable platform-specific success text.
- `nextLinks`: Links to existing install, first-run, lifecycle, troubleshooting, or contribute/release docs.
- `manifestRefs`: Manifest-backed values used in the path, such as plugin name, version, or marketplace source/path.

Rules:

- Every selector path must include platform, scope, prerequisites, commands, success signals, and at least one next link.
- Claude Code paths may show `/plugin`, `/reload-plugins`, and `/speckit-pro:<skill>` style guidance.
- Codex paths may show Codex app or CLI guidance such as `codex`, `/plugins`, `@SpecKit Pro`, `$install`, and `$speckit-*`.
- A selected path must not render the other platform's selected command sequence as copyable guidance.

## CommandGuidance

Represents visible copyable guidance, not executable browser behavior.

Fields:

- `id`: Stable command identifier.
- `platform`: Platform discriminator matching the parent selector path.
- `label`: Visible command label.
- `command`: Visible command text or sequence.
- `expectedSignal`: Observable success signal.
- `copyable`: Boolean for optional progressive copy affordance.

Rules:

- Commands remain visible/selectable in static markup.
- Copy buttons, if present, use native buttons and show failure/status text.
- Browser code must not execute commands, read local files, write config, install plugins, or invoke plugin workflows.

## ManifestSource

Represents one checked-in JSON/manifest input.

Required sources:

- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`
- `speckit-pro/.claude-plugin/plugin.json`
- `speckit-pro/.codex-plugin/plugin.json`
- `dist/claude/speckit-pro/.claude-plugin/plugin.json`
- `dist/codex/speckit-pro/.codex-plugin/plugin.json`

Rules:

- These files are read at docs build or focused-test time only.
- No installed cache, user home-directory config, pasted JSON, browser-local config, or install Markdown is a data source.

## ManifestConsistencyComparison

Represents one repository-only checker row.

Fields:

- `id`: Stable comparison identifier.
- `label`: Human-readable comparison label.
- `rule`: Expected consistency rule.
- `leftSource`: Source manifest path and JSON pointer or field label.
- `rightSource`: Counterpart manifest path and JSON pointer or field label.
- `leftValue`: Displayed value or unavailable marker.
- `rightValue`: Displayed value or unavailable marker.
- `state`: `pass`, `mismatch`, or `unavailable`.
- `severity`: `pass`, `caution`, or `info`.
- `handoff`: Lightweight troubleshooting or maintainer link.

Rules:

- Equality checks are limited to stable repository consistency fields such as plugin name, version, marketplace source/path, and counterpart presence.
- Intentional platform packaging differences, such as Codex source-vs-dist skills path rewrites, are informational and must not create false mismatch states.
- Each row must show compared values and the rule used to evaluate them.

## GeneratedPayloadDiagramNode

Represents one accessible payload-flow node.

Fields:

- `id`: Stable node identifier.
- `label`: Visible node label.
- `kind`: `source-tree`, `claude-dist`, `codex-dist`, `marketplace-entry`, or `codex-cache`.
- `description`: Static explanatory text.
- `inputs`: Source node ids.
- `outputs`: Destination node ids.

Rules:

- All diagram content must also exist as text-backed headings, rows, or list items.
- No required information may depend on hover, drag, zoom, click, or pointer-only interaction.

## FirstRunCheckpoint

Represents one compact safe readiness checkpoint.

Fields:

- `id`: Stable checkpoint identifier.
- `label`: Visible checkpoint label.
- `description`: Static review text.
- `category`: Platform route, prerequisite, repository state, scaffold output, or validation.
- `handoff`: Optional next docs link.

Required checkpoint coverage:

- Platform install route.
- Spec Kit CLI exists/version.
- Constitution.
- Roadmap or SPEC-ID selection.
- GitHub CLI.
- `jq`.
- Branch or worktree and clean-state review.
- Scaffold output artifacts.
- Docs validation evidence.

## TroubleshootingHandoff

Represents a safe next-link from mismatch, unavailable, or caution states.

Fields:

- `id`: Stable link identifier.
- `label`: Visible link text.
- `href`: Existing or future docs URL.
- `audience`: Installer, maintainer, or evaluator.
- `scope`: Lightweight orientation, not a full troubleshooting matrix.

Rules:

- Handoffs must not become a cache diagnosis, update procedure, rollback guide, or security/trust model.
- Future DOC-008 ownership should be named when the target content is not yet detailed.
