# Data Model: Command, workflow, manifest, and file-layout reference

## Entity: ReferencePage

- **Fields**: `slug`, `title`, `description`, `publicPath`, `outputPath`, `records`, `generatedNotice`, `sources`
- **Validation rules**:
  - `slug` is one of `skills`, `agents`, `manifests`, `hooks`, `scripts`, `tests`, `source-vs-dist`.
  - `publicPath` uses `/racecraft-plugins-public/reference/<slug>/`.
  - `outputPath` is under `docs-site/src/content/docs/reference/`.
  - `generatedNotice` is non-empty and rendered visibly on every generated page.
  - `sources` contains page-level source citations for the inventory inputs used by the page.
  - Records are sorted deterministically.
- **Relationships**: Owns many `ReferenceRecord` objects and has page-level `SourceCitation` values.

## Entity: ReferenceRecord

- **Fields**: `id`, `heading`, `purpose`, `platformMapping`, `commandSkillReference`, `manifestFieldSets`, `sourceFacts`, `sources`, `inferredNotes`, `classification`
- **Validation rules**:
  - `id` is stable and unique within the page.
  - A record that states source facts has at least one visible `SourceCitation`.
  - `sourceFacts` and `inferredNotes` are separate arrays.
  - Markdown rendering uses stable ordered labels, including visible `Sources` and `Inferred notes` fields.
- **Relationships**: Belongs to one `ReferencePage`; may have many `SourceFact` and `InferredNote` objects.

## Entity: SourceFact

- **Fields**: `text`, `sourceRefs`
- **Validation rules**:
  - Text is derived from checked-in allowlisted files.
  - Each `sourceRefs` entry points to an existing local repo-relative path.
  - Facts do not use generated reference output as evidence.
- **Relationships**: References one or more `SourceCitation` objects.

## Entity: SourceCitation

- **Fields**: `path`, `fragment`, `label`, `githubUrl`
- **Validation rules**:
  - `path` is repo-relative and exists locally during generation/check.
  - `path` matches an allowlisted source file or directory.
  - `githubUrl` uses `https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/<path>`.
- **Relationships**: Supports `SourceFact` and `InferredNote` records.

## Entity: InferredNote

- **Fields**: `text`, `basedOn`
- **Validation rules**:
  - Rendered only under `Inferred notes`.
  - Uses a visible `Based on:` source-path list.
  - Does not appear in `sourceFacts`.
- **Relationships**: References one or more `SourceCitation` objects.

## Entity: PlatformMapping

- **Fields**: `concept`, `claudeCode`, `codex`, `runtimeDifference`
- **Validation rules**:
  - Claude Code and Codex entries appear in parallel when both exist.
  - Runtime-specific differences are not collapsed into a generic description.
  - Missing optional surfaces are labeled absent or omitted without invented facts.
- **Relationships**: Used by skill, agent, hook, manifest, and source-vs-dist records.

## Entity: CommandSkillReference

- **Fields**: `claudeInvocation`, `codexInvocation`, `purpose`, `prerequisites`, `expectedOutputArtifact`, `sourceRefs`
- **Validation rules**:
  - Present on command or skill records that describe invocable surfaces.
  - Claude Code and Codex invocation fields are both rendered; unavailable or not-applicable runtime values are labeled explicitly.
  - Prerequisites and expected output artifacts are supported by checked-in source paths or labeled as inferred notes with `Based on:` paths.
- **Relationships**: Belongs to a `ReferenceRecord` and references one or more `SourceCitation` values.

## Entity: ManifestFieldSet

- **Fields**: `runtime`, `manifestKind`, `requiredFields`, `optionalFields`, `sourceRefs`
- **Validation rules**:
  - `runtime` is either `claude-code` or `codex`.
  - Required and optional fields are listed separately for each runtime-specific plugin manifest record.
  - Field classifications are reference metadata only; they do not change manifest semantics or generated payload content.
- **Relationships**: Belongs to a manifest `ReferenceRecord` and references one or more `SourceCitation` values.

## Entity: FileClassification

- **Fields**: `path`, `role`, `platform`, `editability`, `reason`
- **Validation rules**:
  - `role` is one of `source`, `generated-payload`, `test-only`, `release-infrastructure`, `documentation-infrastructure`, or `other`.
  - Generated payload paths are classified separately from authoring source paths.
  - Plugin behavior and release semantics remain read-only for DOC-007.
- **Relationships**: Supports `source-vs-dist`, `manifests`, `scripts`, and `tests` pages.

## Entity: SourceAllowlist

- **Fields**: `exactPaths`, `prefixes`, `excludedPrefixes`
- **Validation rules**:
  - Includes repo manifests, `speckit-pro/`, `dist/claude/`, `dist/codex/`, root scripts, `tests/speckit-pro/`, and docs-site config/content needed for navigation.
  - Excludes `.git`, `.worktrees`, `node_modules`, user home/cache installs, network sources, user-pasted JSON, and generated reference output as evidence.
- **Relationships**: Validates every `SourceCitation`.

## Entity: FreshnessCheck

- **Fields**: `mode`, `expectedFiles`, `staleFiles`, `exitCode`, `message`, `errorCategory`, `affectedPath`, `phase`, `recoveryAction`
- **Validation rules**:
  - `mode=generate` writes generated Markdown files.
  - `mode=check` does not write files.
  - Exit code `0` means current, `1` means stale generated output, and `2` means source/parsing/internal error.
  - `errorCategory` is one of `source`, `parse`, `output-write`, or `internal` when `exitCode=2`.
  - `affectedPath` is a repo-relative source or output path when one path caused the failure.
  - `phase` is present when no single source or output path explains the failure.
  - `recoveryAction` is bounded to local generate/check recovery and must not expand into DOC-008 troubleshooting or DOC-010 CI hardening.
- **State transitions**:
  - `missing-or-stale -> current` after `reference:generate`.
  - `current -> stale` when source facts or generated output diverge.
  - `any -> error` when required source files are missing or malformed.
