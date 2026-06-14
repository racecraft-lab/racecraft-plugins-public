# Data Model: Codex marketplace installation path

This feature is documentation-only. The "data model" below defines the content
objects the Codex install page and README alignment must present consistently.

## Entity: Documentation Entry Point

**Fields**

- `path`: repo-relative Markdown or MDX file path
- `role`: detailed guide or concise summary
- `audience`: Codex user, maintainer, or security-minded reader
- `required_invariants`: install facts that must match the other entry points

**Instances**

- `docs-site/src/content/docs/install/codex.md`: detailed Codex install guide
- `README.md`: repository-level marketplace summary
- `speckit-pro/README.md`: plugin-level install and workflow summary

**Validation rules**

- All three entry points must agree on marketplace surfaces, generated payload
  target, installed plugin cache behavior, `$install`, restart, verification,
  and bounded install-safety guidance.
- README surfaces may be concise, but they must not contradict the docs-site
  page.

## Entity: Install Path

**Fields**

- `name`: repo-scoped marketplace, personal/local marketplace, or CLI marketplace
- `source`: marketplace file or CLI source form
- `payload_target`: plugin directory Codex should install
- `success_signal`: what the user can observe after the step
- `source_evidence`: official docs, local CLI help, or checked-in source

**Validation rules**

- Repo-scoped marketplace must use `.agents/plugins/marketplace.json`.
- Personal marketplace examples must use `~/.agents/plugins/marketplace.json`.
- Personal/local plugin content must be copied or synced from
  `dist/codex/speckit-pro/`.
- Docs must not direct users to install Codex from `speckit-pro/`.
- CLI examples may include local path, `owner/repo[@ref]`, HTTP or HTTPS Git
  URL, SSH Git URL, `--ref`, repeatable `--sparse PATH`, and `--json` only.

## Entity: Codex Surface

**Fields**

- `surface_name`: marketplace file, source manifest, generated payload manifest,
  installed plugin cache, bundled skill, skill metadata sidecar, or custom-agent
  TOML file
- `path_pattern`: local path or official path pattern
- `role`: authoring, distribution, runtime cache, or registration target
- `editable_source_of_truth`: yes or no

**Validation rules**

- `dist/codex/speckit-pro/.codex-plugin/plugin.json` is generated payload
  evidence, not the authoring source of truth.
- `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/` is the
  installed plugin cache, not the source of truth.
- `speckit-pro/codex-agents/*.toml` is source/package evidence; installed
  verification follows the installer-copied set.

## Entity: Custom-Agent Checklist

**Fields**

- `trigger`: `@SpecKit Pro -> install` or `$install`
- `default_destination`: `~/.codex/agents/`
- `project_destination`: `.codex/agents/` when explicitly selected
- `expected_files`: installer-copied TOML list
- `restart_required`: true
- `verification`: observational checks only

**Expected files**

- `autopilot-fast-helper.toml`
- `phase-executor.toml`
- `clarify-executor.toml`
- `checklist-executor.toml`
- `analyze-executor.toml`
- `implement-executor.toml`
- `codebase-analyst.toml`
- `spec-context-analyst.toml`
- `domain-researcher.toml`

**Validation rules**

- Do not list `uat-runbook-author.toml` as expected installed output in DOC-004.
- Verification may check the installer report, destination directory, filenames,
  model lines, restart instruction, and preservation of unrelated user agents.
- Do not introduce a new doctor/list command.
- Do not tell users to edit installed cache or generated TOML files manually.

## Entity: Safety Notice

**Fields**

- `sandbox_expectation`: what local sandboxing may permit or block
- `approval_expectation`: when a user may see prompts
- `network_expectation`: when Git-backed setup may need network access
- `destination_expectation`: whether the write target is inside or outside the
  workspace
- `deferred_topics`: DOC-008 topics not covered here

**Validation rules**

- State that default `~/.codex/agents/` is outside most workspaces and may
  require approval.
- State that `$install` copies named local TOML files from the installed plugin
  bundle into the selected Codex agent directory.
- State that Git-backed marketplace setup or plugin installation may require
  network access or approval.
- Do not imply plugin install or `$install` bypasses sandbox or approval
  controls.
- Defer full trust model, managed policy, stale-cache diagnosis, permission
  troubleshooting, update/remove/rollback, and hook/MCP/agent security depth to
  DOC-008.

## Entity: Command Snippet

**Fields**

- `snippet`: exact command or path shown in docs
- `context`: when to use it
- `source`: official docs, local CLI help, or checked-in source
- `manual_review_status`: pending, reviewed, or rejected

**Validation rules**

- Every changed Codex command/path snippet must appear in the manual review
  checklist before PR readiness.
- Snippets must be labeled by install context so Claude Code commands do not
  leak into the Codex path.

## State Transitions

```text
Select install context
  -> Add/select marketplace
  -> Install SpecKit Pro plugin
  -> Run Codex install skill
  -> Approve only expected local TOML writes when prompted
  -> Restart Codex
  -> Verify nine custom-agent TOML files and expected skill access
```

Cache refresh guidance is state-aware:

```text
Edit source or generated payload
  -> Update marketplace source or copied payload
  -> Reinstall/refresh plugin
  -> Restart Codex when plugin or agent state changes
```
