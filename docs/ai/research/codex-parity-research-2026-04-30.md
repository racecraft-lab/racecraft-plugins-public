# Codex Parity Research — 2026-04-30

Author: Claude Code research agent
Audience: speckit-pro maintainer (Fredrick Gabelmann)
Scope: Validate every speckit-pro Codex-side assumption against primary OpenAI sources before shipping the new `grill-me` skill on the Codex side.

## Summary

Codex skills are real and converged. The canonical model is: a plugin lives under `<plugin>/.codex-plugin/plugin.json`, ships skills under `<plugin>/skills/<name>/SKILL.md`, optional MCP/app integrations via `.mcp.json` / `.app.json`, optional bundled hooks at `hooks/hooks.json` (NOT `codex-hooks.json` and NOT `hooks.json` at the plugin root unless the manifest's `hooks` key overrides the path), optional `commands/` directory of plain Markdown command files (no frontmatter required, format mirrors Figma's official plugin), and an optional `agents/openai.yaml` plugin-level skill metadata sidecar. **User-defined slash commands are deprecated in favor of skills** (per OpenAI staff comment closing issue #7480), so the only stable invocation surface for `grill-me` is the skill's own description-match (implicit) or explicit `$grill-me` mention. Skills are triggered explicitly via `$skill-name` or implicitly when Codex matches the task to the `description` frontmatter (default `allow_implicit_invocation: true`). Custom subagents are TOML files in `~/.codex/agents/` or `.codex/agents/` and are NOT directly bundle-loaded by the plugin loader — speckit-pro's `install` skill that copies TOML templates into those paths is the correct workaround. The interactive `ask_user_question` / `request_user_input` tool is gated by collaboration mode in current Codex, is NOT a stable always-on tool, and is removed entirely under `codex exec` (`SessionSource::Exec`); a Codex `grill-me` therefore must NOT depend on it and should fall back to a free-text Q&A loop with TTY/exec-mode detection.

The biggest divergences between the local repo and OpenAI canon:

1. **`codex-hooks.json` at plugin root is non-canonical.** Codex looks for `hooks/hooks.json` by default. The repo's `validate-codex-hooks.sh` enforces a filename Codex's loader will not find (Q6).
2. **Custom slash commands are deprecated** (per OpenAI staff). `/speckit-pro:setup` is not a real Codex affordance; users invoke skills as `$speckit-setup`, never `/<plugin>:<command>`. The repo's docstrings that say `/speckit-coach`, `/speckit-setup`, etc. are wrong for the Codex surface (Q3, Q10).
3. **Subagents in `~/.codex/agents/` are TOML, but plugin-bundled `agents/*.md` files exist in OpenAI plugins** (Figma) — they are different things. The local repo's TOML-as-bundled-template approach is consistent with how user-scoped agents work, just not auto-loaded; the `install` skill is required (Q5).
4. **The `model_reasoning_effort` enum `xhigh` is officially documented but model-dependent**, and the `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.3-codex-spark` model names that local validation enforces do not all appear in the public docs — only `gpt-5.5` is named explicitly in the configuration reference and changelog (Q5 caveat).
5. **`marketplace.json` lives at `.agents/plugins/marketplace.json`** at the *repo* root (not under `speckit-pro/`). The local check enforces this correctly (Q8).

## Findings

### Q1 — Codex plugin manifest format

**Answer:** The canonical manifest is `<plugin>/.codex-plugin/plugin.json`. Required fields are `name` (kebab-case), `version` (semver), and `description`. Optional top-level fields include `author`, `homepage`, `repository`, `license`, `keywords`, `skills` (path), `mcpServers` (path to `.mcp.json`), `apps` (path to `.app.json`), and `interface` (display metadata for the marketplace). Plugins may also declare a `hooks` field that overrides the default `hooks/hooks.json` path. The `interface` object holds `displayName`, `shortDescription`, `longDescription`, `developerName`, `category` (e.g. `"Coding"`, `"Productivity"`, `"Design"`), `capabilities` (e.g. `["Interactive", "Read", "Write"]`), `websiteURL`, `privacyPolicyURL`, `termsOfServiceURL`, `defaultPrompt` (array), `brandColor`, `composerIcon`, `logo`, `screenshots`.

**Primary source(s):**
- https://developers.openai.com/codex/plugins/build (accessed 2026-04-30)
- https://github.com/openai/plugins/blob/main/plugins/build-web-apps/.codex-plugin/plugin.json (accessed 2026-04-30, OpenAI-shipped reference plugin)
- https://github.com/openai/plugins/blob/main/plugins/figma/.codex-plugin/plugin.json (accessed 2026-04-30)

**Quoted snippet (OpenAI build-web-apps reference):**
```json
{
  "name": "build-web-apps",
  "version": "0.1.0",
  "description": "Build web apps with frontend asset design...",
  "author": {"name": "OpenAI", "email": "support@openai.com", "url": "https://openai.com/"},
  "homepage": "https://openai.com/",
  "repository": "https://github.com/openai/plugins",
  "license": "MIT",
  "keywords": ["build-web-apps", "frontend", "image-generation", ...],
  "skills": "./skills/",
  "interface": {
    "displayName": "Build Web Apps",
    "shortDescription": "Build frontend-focused web apps...",
    "longDescription": "...",
    "developerName": "OpenAI",
    "category": "Coding",
    "capabilities": ["Interactive", "Read", "Write"],
    "websiteURL": "https://openai.com/",
    "privacyPolicyURL": "...",
    "termsOfServiceURL": "...",
    "defaultPrompt": ["Design a new landing page for my new SaaS product."],
    "brandColor": "#111111",
    "composerIcon": "./assets/build-web-apps-small.svg",
    "logo": "./assets/app-icon.png",
    "screenshots": []
  }
}
```

**Comparison with local `speckit-pro/.codex-plugin/plugin.json` (v1.9.1):** The shape matches. `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `skills`, and `interface.{displayName, shortDescription, longDescription, developerName, category, capabilities, websiteURL, defaultPrompt, brandColor}` are all present and follow the OpenAI reference. **No changes needed.** Local manifest is missing optional `composerIcon`/`logo`/`screenshots`/`privacyPolicyURL`/`termsOfServiceURL`, but those are optional polish items.

---

### Q2 — Codex SKILL.md / skill format

**Answer:** A skill is a directory containing `SKILL.md`. The file must begin with YAML frontmatter (`---` … `---`). Required frontmatter fields are `name` and `description`. Optional subdirectories: `scripts/`, `references/`, `assets/`. An optional `agents/openai.yaml` sidecar provides UI metadata (`interface.display_name`, `interface.short_description`, `interface.icon_small`, `interface.icon_large`, `interface.brand_color`, `interface.default_prompt`) and policy (`policy.allow_implicit_invocation`, default **`true`**) and `dependencies.tools`. Skills are triggered two ways: (a) **explicit** invocation via `$skill-name` (or via `/skills` browser), and (b) **implicit** invocation when Codex matches the task to the skill's `description` (only when `allow_implicit_invocation` is true). Codex caps the initial skills list at "**roughly 2% of the model's context window, or 8,000 characters when the context window is unknown**". Skill discovery paths (in priority order): `$CWD/.agents/skills`, `$CWD/../.agents/skills` (walking up to repo root), `$REPO_ROOT/.agents/skills`, `$HOME/.agents/skills`, `/etc/codex/skills`, plus skills bundled in installed plugins under `<plugin>/skills/`.

**Primary source(s):**
- https://developers.openai.com/codex/skills (accessed 2026-04-30)
- https://github.com/openai/codex/blob/main/codex-rs/core-skills/src/loader.rs (accessed 2026-04-30) — `SKILLS_FILENAME = "SKILL.md"`, `extract_frontmatter` requires `---` delimiters, parses `name`, `description`, optional `display_name`, `short_description`, `allow_implicit_invocation`.
- https://github.com/openai/plugins/blob/main/plugins/build-web-apps/skills/frontend-app-builder/SKILL.md (accessed 2026-04-30) — minimal real example with only `name` + `description`.

**Quoted snippets:**
- "this list is capped at roughly 2% of the model's context window, or 8,000 characters when the context window is unknown."
- "allow_implicit_invocation (default: true)"
- "In CLI/IDE, run /skills or type $ to mention a skill."
- "Implicit invocation: Codex can choose a skill when your task matches the skill description."
- OpenAI reference SKILL.md (frontend-app-builder):
  ```yaml
  ---
  name: frontend-app-builder
  description: Use for new frontend applications, dashboards, games, ...
  ---
  ```
- Loader Rust constant: `const SKILLS_FILENAME: &str = "SKILL.md";`

**Comparison with local skills:** The local SKILL.md frontmatter shape (`name`, `description`) is correct. The local validation forbids Claude-only keys (`user-invokable`, `license`, `argument-hint`) which is correct. Local skill body word-count bound (500–8000) is a self-imposed convention, not a Codex requirement; the only Codex-side limit is the **~8,000-character / ~2% context cap on the *aggregate* skill-description list** (not per skill, not on the body). With speckit-pro shipping 6 skills today + grill-me = 7 skills, the aggregate cap leaves roughly 1.1 KB per `description` on average (8000 / 7 ≈ 1143 chars). The body itself loads in full only when the skill is selected. **The `templates/` subdirectory pattern (used in the speckit-coach Claude side) is NOT documented for Codex skills** — only `scripts/`, `references/`, `assets/` are. Codex's loader treats other subdirs as opaque (no special semantics), so nothing breaks if you put `templates/` there, but Codex won't auto-resolve a template path the way Claude would.

---

### Q3 — Codex command files

**Answer:** Codex **does not have an officially supported "custom slash command" surface for plugins** the way Claude Code's `commands/` directory does. The historical `~/.codex/prompts/*.md` (custom prompts, invoked via `/prompts:name`) feature has been **deprecated**. The official replacement is **skills**. Plugins MAY ship a `commands/` directory of plain-Markdown files (Figma's official plugin does), but Codex's plugin loader (`codex-rs/core-plugins/src/loader.rs`) defines NO `commands/` constant — it loads only `skills/`, `hooks/hooks.json`, `.mcp.json`, `.app.json`, and `plugin.json`. Files placed in a plugin's `commands/` directory are documentary references to be loaded by the plugin's own skills, not auto-registered slash commands. Therefore the local docstring claim that Codex exposes `/speckit-coach`, `/speckit-setup`, `/speckit-autopilot`, `/speckit-status`, `/speckit-resolve-pr` after install is **factually incorrect for Codex**. Users invoke skills by typing `$speckit-coach` (or `@speckit-pro` to mention the plugin), or by writing a task that matches the description (implicit invocation). For `grill-me`, the canonical Codex affordance is `$grill-me` mention or implicit-trigger via a well-tuned `description`.

**Primary source(s):**
- https://developers.openai.com/codex/custom-prompts (accessed 2026-04-30): "Custom prompts are deprecated. Use skills for reusable instructions that Codex can invoke explicitly or implicitly."
- https://github.com/openai/codex/issues/7480 (accessed 2026-04-30) — closed by `etraut-openai` (collaborator): **"This feature request hasn't received enough upvotes, so I'm going to close it. We have deprecated custom slash commands in favor of skills."**
- https://github.com/openai/codex/issues/13893 (accessed 2026-04-30) — original ask for SKILL.md-as-slash-command was redirected: skills replaced custom slash commands.
- https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/loader.rs (accessed 2026-04-30): only `DEFAULT_SKILLS_DIR_NAME`, `DEFAULT_HOOKS_CONFIG_FILE`, `DEFAULT_MCP_CONFIG_FILE`, `DEFAULT_APP_CONFIG_FILE`, `CONFIG_TOML_FILE` constants; no commands constant.
- https://github.com/openai/plugins/blob/main/plugins/figma/commands/implement-from-figma.md (accessed 2026-04-30) — example: plain Markdown body, no YAML frontmatter, used as a documentary skill reference.

**Quoted snippets:**
- OpenAI staff (issue 7480): "We have deprecated custom slash commands in favor of skills."
- Figma plugin command file (no frontmatter, just body): `# /implement-from-figma\n\nImplement a Figma frame or component into project code.\n...`

---

### Q4 — Codex tool affordances

**Answer:** Codex's primary first-party tools (per the prompting guides and CLI features) include `read_file`, `apply_patch`, `update_plan` / `todo_write`, `list_dir`, `glob_file_search`, `rg`, `git`, plus `exec_command` / shell escalation, MCP tools registered by enabled servers, and the agent orchestration primitives `spawn_agent` / `wait_agent` / `send_input` (used by parent agents to manage subagents). There is NO Codex equivalent to Claude Code's `AskUserQuestion` that's always available: the closest is `ask_user_question` / `request_user_input`, currently only available behind `collaboration_modes` (Plan, Code; Plan only by default), and **explicitly stripped out under `codex exec` (`SessionSource::Exec`)** so non-interactive runs cannot hang. There is no Codex equivalent to Claude Code's `Skill` tool (skills are loaded by the runtime, not invoked through a tool). Subagents are the closest analog to Claude's `Agent` tool. Local skills today that depend on `AskUserQuestion`, the `Skill` tool, or `Agent(subagent_type=...)` will not directly translate — they must use `spawn_agent` against a TOML-defined subagent (which the `install` skill provisions) and a free-text Q&A pattern (or no Q&A in non-interactive mode).

**Primary source(s):**
- https://cookbook.openai.com/examples/gpt-5/gpt-5-1-codex-max_prompting_guide (accessed 2026-04-30) — names default solver tools `read_file`, `apply_patch`, `update_plan`/`todo_write`.
- https://github.com/openai/codex/issues/9926 (accessed 2026-04-30) — feature request for `ask_user_question`; community testing confirms `request_user_input` exists today only behind `collaboration_modes = true` and is **"`request_user_input is unavailable in code mode`"** (i.e., gated by Plan mode).
- Implementation note (issue 9926, proposed exec-mode handling): *"human-input tools (`ask_user_question`, `request_user_input`) [be removed] from the toolset when `SessionSource::Exec` is used"*.
- https://developers.openai.com/codex/subagents (accessed 2026-04-30) — orchestration via `spawn_agent`/`wait_agent` is documented but mostly described in prose.

---

### Q5 — Codex agent / subagent model

**Answer:** Codex supports a multi-agent orchestration model. Custom subagents are defined as **standalone TOML files** placed in `~/.codex/agents/` (personal) or `.codex/agents/` (project-scoped). Required fields: `name`, `description`, `developer_instructions`. Optional: `model`, `model_reasoning_effort`, `sandbox_mode`, `nickname_candidates`, `mcp_servers`, `skills.config`. Supported `sandbox_mode`: `read-only`, `workspace-write`, `danger-full-access`. Supported `model_reasoning_effort`: `minimal | low | medium | high | xhigh` (xhigh is "model-dependent"). Codex orchestrates via `spawn_agent` (start subagent), `wait_agent` (collect result), `send_input` (route follow-up). Concurrency caps live under `[agents]` in `config.toml`: `agents.max_threads` (default 6), `agents.max_depth` (default 1), `agents.job_max_runtime_seconds` (default 1800). **Plugin-bundled agents are a separate concept**: OpenAI's official plugins ship `agents/<name>.md` (Markdown agent personas, e.g. Figma's `figma-implementation-agent.md`) plus an `agents/openai.yaml` plugin-level skill-metadata sidecar — **NOT TOML**. The plugin loader (per `codex-rs/core-plugins/src/loader.rs`) does NOT auto-register TOML files from a plugin's `agents/` directory as runtime subagents; it only looks for `skills/`, `hooks/hooks.json`, `.mcp.json`, `.app.json`. So bundling TOML templates in the plugin is correct, but **users must run an installer (the speckit-pro `install` skill is the right pattern) to copy them into `~/.codex/agents/`**. After install, Codex picks them up automatically on next start.

**Primary source(s):**
- https://developers.openai.com/codex/subagents (accessed 2026-04-30): *"To define your own custom agents, add standalone TOML files under `~/.codex/agents/` for personal agents or `.codex/agents/` for project-scoped agents."*
- https://developers.openai.com/codex/config-reference (accessed 2026-04-30): `[agents]` block, `agents.max_threads = 6`, `agents.max_depth = 1`, `agents.job_max_runtime_seconds = 1800`. Sandbox `read-only | workspace-write | danger-full-access`. Reasoning effort `minimal | low | medium | high | xhigh` (with note "`xhigh` is model-dependent").
- https://github.com/openai/plugins/blob/main/plugins/figma/agents/figma-implementation-agent.md (accessed 2026-04-30) — example plugin-bundled Markdown agent.
- https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/loader.rs (accessed 2026-04-30) — confirms no `agents` directory loading in the plugin loader.

**Quoted TOML example (from Codex subagents docs):**
```toml
name = "pr_explorer"
description = "Read-only codebase explorer for gathering evidence before changes are proposed."
model = "gpt-5.3-codex-spark"
model_reasoning_effort = "medium"
sandbox_mode = "read-only"
developer_instructions = """
Stay in exploration mode.
Trace the real execution path, cite files and symbols, and avoid proposing fixes unless the parent agent asks for them.
"""
```

**Caveat on model names:** The local `validate-codex-agents.sh` script enforces `^(gpt-5\.5|gpt-5\.4|gpt-5\.4-mini|gpt-5\.3-codex|gpt-5\.3-codex-spark)$`. Of these, only **`gpt-5.5`** is explicitly named in OpenAI's public Codex changelog (2026-04-23 release entry) and config reference. `gpt-5.3-codex-spark` appears in the official subagents documentation example. `gpt-5.4` and `gpt-5.4-mini` appear in changelog references to "previous default" but are not in a canonical "supported models" table I could find on developers.openai.com. The local enum is plausible but partly under-documented — see Open issues.

---

### Q6 — Codex hooks

**Answer:** Codex's canonical user/repo hook locations are `~/.codex/hooks.json`, `<repo>/.codex/hooks.json`, or inline `[hooks]` tables inside the matching `config.toml`. **Codex's plugin loader looks for plugin-bundled hooks at `<plugin>/hooks/hooks.json` by default** (constant `DEFAULT_HOOKS_CONFIG_FILE = "hooks/hooks.json"` in `codex-rs/core-plugins/src/loader.rs`). The plugin manifest may set a `hooks` field that overrides the default — accepting a path, an array of paths, an inline object, or an array of inline objects. Supported events: `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `Stop`. Hook entry shape: `{ matcher, hooks: [{ type: "command", command, statusMessage?, timeout? }] }`. **Default timeout is 600 seconds.** **The filename `codex-hooks.json` is not a documented Codex filename** — neither in user, repo, nor plugin scope.

**Primary source(s):**
- https://developers.openai.com/codex/hooks (accessed 2026-04-30): *"Codex discovers hooks next to active config layers in either of these forms: `hooks.json` [or] inline `[hooks]` tables inside `config.toml`"*
- https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/loader.rs (accessed 2026-04-30): `const DEFAULT_HOOKS_CONFIG_FILE: &str = "hooks/hooks.json";`. The `load_plugin_hooks` function: *"Discover plugin-bundled hooks from manifest `hooks` entries when present (path, paths, inline object, or inline objects), otherwise from the default `hooks/hooks.json` file."*
- Codex changelog 2026-04-20: *"Hooks are now stable, can be configured inline in `config.toml` and managed `requirements.toml`, and can observe MCP tools"*.

**Implication for speckit-pro:** The current `speckit-pro/codex-hooks.json` file at the plugin root is **not loaded by Codex** as written. It is invisible to the runtime. Either (a) rename to `speckit-pro/hooks/hooks.json`, or (b) keep at root with a different name and add a `"hooks": "./codex-hooks.json"` field in `.codex-plugin/plugin.json` (the loader supports the `Path`, `Paths`, `Inline`, and `InlineList` forms — see `RawPluginManifestHooks` enum in `manifest.rs`). Option (a) is the lower-risk default. The local `validate-codex-hooks.sh` script enforces the wrong canonical filename (`codex-hooks.json`) and must be updated.

**Cross-check against OpenAI's Figma plugin:** The Figma plugin (https://github.com/openai/plugins/tree/main/plugins/figma) ships a `hooks.json` at the plugin root and its README claims it's "an example hook bundle". However, the figma plugin's `.codex-plugin/plugin.json` has NO `hooks` key, and the loader's `None` arm in `load_plugin_hooks` only checks `<plugin>/hooks/hooks.json`. The default-arm code is verbatim:
```rust
None => {
    let default_path = plugin_root.join(DEFAULT_HOOKS_CONFIG_FILE); // "hooks/hooks.json"
    if default_path.as_path().is_file() {
        append_plugin_hook_file(...);
    }
}
```
There is no fallback to a root-level `hooks.json`. So Figma's `hooks.json` is genuinely orphaned — likely a documentation/example artifact rather than a wired hook. This confirms the local `codex-hooks.json` placement will not work either; the rename to `hooks/hooks.json` (or manifest `hooks` field) is the correct fix.

---

### Q7 — Interactive vs non-interactive detection

**Answer:** Codex distinguishes a user-facing interactive TUI session from a non-interactive `codex exec` run via `SessionSource` (an internal enum: `Interactive` vs `Exec`). Skills do **not** have a documented public API to read this directly. The canonical signal is **tool availability**: `ask_user_question` / `request_user_input` is only registered when `collaboration_modes = true` AND the session is interactive (Plan mode). Under `codex exec`, those tools are explicitly removed from the toolset (per the closing implementation in issue #9926). Practical detection patterns for a `grill-me` skill:

1. **Tool-presence probe** (recommended). Attempt to call `request_user_input` with a small, harmless probe payload; if the runtime returns "tool unavailable" or the call fails, fall back to free-text mode. Document this as the canonical guard.
2. **Environment heuristic**: read `CODEX_SESSION_SOURCE` if exposed, or check `tty -s` via a `bash` tool (Codex `exec` does not allocate a TTY by default).
3. **AGENTS.md / preamble flag**: have the human user explicitly say "interactive mode" / "exec mode" at start of session and persist that to a tiny state file.

There is **no documented `is_interactive` flag**. The skill must therefore degrade gracefully — produce a coherent free-text Q&A when tools are missing.

**Primary source(s):**
- https://developers.openai.com/codex/cli/reference (accessed 2026-04-30): *"For scripted/CI-style runs, these flags are essential: `--json`/`--experimental-json`, `--output-last-message`, `--ephemeral`, `--full-auto`, `--dangerously-bypass-approvals-and-sandbox`"* — `codex exec` is by definition non-interactive.
- https://github.com/openai/codex/issues/9926 (accessed 2026-04-30): proposed fix removes `ask_user_question` / `request_user_input` from the toolset when `SessionSource::Exec` is set.
- Community confirmation in issue 9926: *"`request_user_input is unavailable in code mode`"* — the tool is gated by mode even within interactive sessions.

---

### Q8 — Marketplace and installation flow

**Answer:** Codex installs plugins from a **marketplace** registered via the CLI: `codex plugin marketplace add <source>` where `<source>` can be GitHub shorthand (`owner/repo`), a Git URL (https/ssh), or a **local marketplace root directory**. Marketplace files live at `<repo>/.agents/plugins/marketplace.json` (repo-scoped) or `~/.agents/plugins/marketplace.json` (personal-scoped). The marketplace.json shape is `{ "name": ..., "interface": { "displayName": ... }, "plugins": [ { "name", "source": { "source": "local" | "git", "path" or url ... }, "policy": { "installation", "authentication" }, "category" } ] }`. Path references must be relative, start with `./`, and resolve inside the marketplace root. **This is NOT the same flow as Claude Code's `/plugin marketplace add racecraft-lab/racecraft-plugins-public`.** Codex's CLI is a separate binary (`codex plugin marketplace add ...`) and reads the marketplace.json at the canonical `.agents/plugins/marketplace.json` path. After registration, users browse and install via the in-app `/plugins` browser.

**Primary source(s):**
- https://developers.openai.com/codex/cli/reference (accessed 2026-04-30): *"The `codex plugin marketplace` subcommand manages plugin sources."* with `add`, `remove`, `upgrade` syntax.
- https://github.com/openai/plugins/blob/main/.agents/plugins/marketplace.json (accessed 2026-04-30) — OpenAI's reference marketplace, structurally identical to the local repo's.
- https://github.com/openai/codex/blob/main/codex-rs/core/src/plugins/manager.rs (accessed 2026-04-30) — references `".agents/plugins/marketplace.json"` literal.

**Comparison with local `.agents/plugins/marketplace.json`:** The local file matches OpenAI's reference shape exactly — `name`, `interface.displayName`, `plugins[]` with `name`, `source.{source: "local", path: "./speckit-pro"}`, `policy.{installation: "AVAILABLE", authentication: "ON_INSTALL"}`, `category: "Coding"`. **No changes needed.**

---

### Q9 — Versioning and release semantics

**Answer:** Codex enforces semver `X.Y.Z` in plugin manifests but does NOT prescribe a specific automation tool. release-please's behavior of bumping `.codex-plugin/plugin.json:$.version` and syncing `marketplace.json` is fine — Codex doesn't care how the version got there, only that it's valid semver. Codex's plugin cache invalidation on Git-source marketplaces uses the version field plus the marketplace ref/SHA (per `marketplace_upgrade.rs`). Tracing the local validation rules: `validate-codex-marketplace.sh` enforces (a) `name` is non-empty (matches OpenAI shape — required); (b) `interface.displayName` exists (matches — required for browser); (c) `plugins` is a non-empty array (matches); (d) `plugins[0].name == "speckit-pro"` (project-specific — fine); (e) `source.source == "local"` (matches OpenAI shape for local-checked-in marketplaces); (f) `source.path` starts with `./` (matches OpenAI shape and Rust loader's path-validation logic that requires staying inside repo root); (g) `policy.installation` and `policy.authentication` are present (matches the OpenAI reference manifest); (h) `category` is present (matches). **All assertions trace to documented OpenAI conventions.** No drift.

**Primary source(s):**
- https://developers.openai.com/codex/plugins/build (accessed 2026-04-30) — `version` is required semver.
- https://github.com/openai/plugins/blob/main/.agents/plugins/marketplace.json (accessed 2026-04-30) — reference structure confirms every assertion in `validate-codex-marketplace.sh`.
- https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/marketplace.rs (file exists; confirmed handling of local & git sources).

---

### Q10 — Naming conventions / Claude-Code divergences

**Answer:**
- **Skill names are kebab-case lowercase**, used as the literal `$skill-name` invocation token. The Codex skills loader matches the directory name plus the `name:` frontmatter (must agree). They are case-sensitive in display but the matcher is documented as treating the description as a natural-language match, not the name.
- **Plugin names are kebab-case lowercase** (e.g. `speckit-pro`, `build-web-apps`, `figma`). Used as the namespace prefix in marketplace listings.
- **The `/<plugin>:<command>` pattern from Claude Code does NOT exist in Codex.** Plugins do not register slash commands. Users invoke skills via `$skill-name` or natural-language description-matching, or mention the plugin via `@plugin-name`. The deprecated custom-prompts feature used `/prompts:<name>` (single namespace), not `/<plugin>:<name>`.
- **Reserved/restricted names:** No public list. Avoid built-in slash command names (`/copy`, `/diff`, `/plugins`, `/model`, `/permissions`, `/status`, `/clear`, `/exit`, `/fork`, `/review`, `/theme`, `/auto-context`, `/cloud`, `/feedback`, `/local`, `/mention`) for any user-facing skill name to be safe.
- **`description` triggers ARE supported the same way Claude Code does** for implicit invocation, with one difference: Codex caps the initial skills-list payload at ~2% context window or 8KB, so descriptions across all installed skills compete for that budget. Tight, decisive descriptions matter even more on Codex than on Claude Code.

**Primary source(s):**
- https://developers.openai.com/codex/skills (accessed 2026-04-30) — `$skill-name` and implicit description-matching.
- https://github.com/openai/codex/issues/7480 (accessed 2026-04-30) — confirmed: custom slash commands deprecated.
- https://developers.openai.com/codex/cli/slash-commands (accessed 2026-04-30) — built-in command list.

---

## Plan reconciliation

For each plan element, mark CONFIRMED / INVALIDATED / CHANGE NEEDED.

- **`speckit-pro/codex-skills/grill-me/SKILL.md` frontmatter shape**
  → **CONFIRMED** (with three sub-actions). Required keys: `name: grill-me`, `description: <when to trigger>`. Strip the Claude-side `argument-hint`, `user-invokable`, `license` keys (the local `validate-codex-skills.sh` enforces this — they are Claude-Code-only). The current Claude-side `description` field is ~720 characters and is well within budget: with 7 installed skills sharing the ~8KB skill-list cap, each skill has roughly **1.1 KB of headroom for `description`**, so the existing description fits and the budget is not the binding constraint. The binding constraint is **trigger clarity** — keep the description action-oriented and front-load the negative constraint ("NEVER invoke this skill from inside autopilot or any of its phase agents") so Codex's implicit-trigger logic respects it.
  → **`agents/openai.yaml` policy:** set `policy.allow_implicit_invocation: false` for grill-me. It is human-in-the-loop ONLY, must never auto-trigger from autopilot or phase agents, and must require an explicit `$grill-me` mention. This places it in the same `false` bucket as `speckit-setup`, `speckit-autopilot`, `speckit-resolve-pr`, `install` per `validate-codex-skills.sh`.
  → **Update `validate-codex-skills.sh`:** add `grill-me` to the `SKILLS=(...)` array AND add a case branch for it in BOTH the implicit-invocation policy block (use the `mutation-heavy` bucket so `allow_implicit_invocation: false` is required) AND the source-artifact mapping block (`grill-me) if [ -f "$PLUGIN_ROOT/skills/grill-me/SKILL.md" ]; then _pass; fi`).
  → **Update `validate-codex-plugin.sh`:** add `grill-me` to its `REQUIRED_SKILLS=(...)` array.

- **`speckit-pro/codex-skills/grill-me/references/` subdirectory pattern**
  → **CONFIRMED.** Codex skill spec officially supports `references/`, `scripts/`, `assets/`. `references/` is appropriate for long-form supplementary docs and matches both the Codex skills doc and OpenAI's own plugin examples.

- **Codex `/speckit-pro:grill-me` command invocation (does this need a corresponding command file? where?)**
  → **INVALIDATED.** Codex does NOT have `/<plugin>:<command>` namespace syntax. Custom slash commands are deprecated. Users invoke as `$grill-me` (explicit) or via description-matching (implicit). Do NOT create a `commands/grill-me.md` — even Figma's `commands/*.md` are documentary references, not auto-registered commands. **Action:** drop any `/speckit-pro:grill-me` mention from Codex-facing docs; document `$grill-me` as the canonical invocation. Also: update existing wording in `codex-skills/speckit-coach/SKILL.md` that claims `/speckit-coach`, `/speckit-setup`, etc. work — replace with `$speckit-coach`, `$speckit-setup`, etc.

- **Codex hooks placement (`codex-hooks.json` at root vs other location)**
  → **CHANGE NEEDED.** Canonical default is `<plugin>/hooks/hooks.json`. The local `speckit-pro/codex-hooks.json` will not be loaded by Codex's plugin loader. **Action:** either (a) move to `speckit-pro/hooks/hooks.json` (low risk, recommended), or (b) keep at root and add `"hooks": "./codex-hooks.json"` to `.codex-plugin/plugin.json`. Update `tests/layer1-structural/validate-codex-hooks.sh` to enforce the chosen layout. Note: even after fix, hooks only fire when the plugin/project `.codex/` config layer is trusted (for repo hooks) or the plugin is installed and trusted.

- **Codex subagent model for autopilot's negative constraints (where do constraints live?)**
  → **CONFIRMED with required workflow.** Subagents are TOML files in `~/.codex/agents/` (or `.codex/agents/` project-scoped). Required fields `name`, `description`, `developer_instructions`. Plugin-bundled TOML templates under `codex-agents/*.toml` are NOT auto-loaded by Codex's plugin loader; the speckit-pro `install` skill correctly handles copying them into `~/.codex/agents/` then prompts the user to restart Codex. Negative constraints should live in `developer_instructions` of the relevant subagent (e.g., `clarify-executor.toml`, `phase-executor.toml`). Local validate-codex-agents.sh model-name regex includes `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.3-codex` which are not all in public docs — see Open issues.

- **Codex eval file format/locations**
  → **CONFIRMED-BY-CONVENTION.** No OpenAI doc prescribes eval file shape — `tests/layer2-trigger/codex-evals/*.json` and `tests/layer3-functional/codex-evals/*.json` are local conventions and the new `grill-me-trigger.json` and `grill-me-evals.json` should mirror the existing schema used by `speckit-coach-trigger.json` etc. Layer 2 and 3 evals require `claude -p` (per CLAUDE.md), so they are developer-local.

- **Tool-availability assumptions (no `AskUserQuestion`, free-text loop)**
  → **CONFIRMED.** No always-on AskUserQuestion in Codex. `request_user_input` exists today only behind `collaboration_modes = true` AND only in Plan mode AND not under `codex exec`. The grill-me Codex variant must default to a free-text Q&A loop and treat any structured-input tool as opportunistic. Document this guard explicitly in the skill body.

- **Interactive-detection mechanism for grill-me's HITL guard**
  → **CHANGE NEEDED — adopt a probe pattern.** No public `is_interactive` flag exists. Recommended pattern in priority order: (1) attempt a probe `request_user_input` call wrapped in try/catch — if unavailable, fall through; (2) check `tty -s` via `exec_command`; (3) require the human to confirm interactive mode at session start. Document the chosen guard at the top of `codex-skills/grill-me/SKILL.md` so the guard is durable across rewrites.

---

## Open issues

1. **Authoritative list of supported `model` values for subagent TOML.** The public docs name `gpt-5.5` (current), reference `gpt-5.4` / `gpt-5.4-mini` (older) and `gpt-5.3-codex-spark` (in the subagent example), but I could not find a single canonical "supported models" table on developers.openai.com. The local `validate-codex-agents.sh` regex `^(gpt-5\.5|gpt-5\.4|gpt-5\.4-mini|gpt-5\.3-codex|gpt-5\.3-codex-spark)$` is plausible but partly under-documented. **Resolution path:** file an issue against `openai/codex` asking for a stable supported-model list in the Subagents doc. In the meantime, keep the local regex but add a comment marking each value's source URL.

2. **Whether plugin-bundled TOML subagents will ever auto-load.** Today the plugin loader does NOT load `<plugin>/agents/*.toml`. The speckit-pro `install` skill workaround is correct and likely durable, but if Codex ever adds plugin-bundled subagent loading, the install step becomes redundant. **Resolution path:** track the `openai/codex` repo for changes to `codex-rs/core-plugins/src/loader.rs` constants; if a new constant like `DEFAULT_AGENTS_DIR_NAME` appears, revisit.

3. **Stable `is_interactive` API.** No documented way for a skill body or sub-agent to detect interactive vs `codex exec` mode without probing. **Resolution path:** file an OpenAI feature request: "expose session source (Interactive / Exec) to skills via env var (e.g., `CODEX_SESSION_SOURCE`) so skills can decide HITL vs autonomous flows." Until then, use the probe pattern.

4. **Whether plugins can declare `commands` in the manifest.** Figma's official OpenAI plugin ships a `commands/` directory but Codex's plugin loader does not load it. Are these meant to be skill references only, or is there an unreleased command-loading feature? **Resolution path:** read the figma plugin's SKILL.md files to see how `commands/*.md` are referenced; consult plugin-creator skill output. Until clarified, treat `commands/` as documentary.

5. **`agents/openai.yaml` `dependencies.tools` schema.** The Codex skills doc shows an example `mcp` tool dependency but doesn't enumerate all `type` values (mcp, ?), `transport` values (`streamable_http`, ?), or describe how Codex enforces dependencies. **Resolution path:** examine `codex-rs/core-skills/src/loader.rs` more deeply, or skip declaring dependencies for grill-me (it has no MCP needs).

6. **Whether `templates/` subdirectory under a Codex skill has any documented semantics.** Codex's spec lists `scripts/`, `references/`, `assets/` only. The Claude Code side uses `templates/` (e.g., `skills/speckit-coach/templates/workflow-template.md`). On Codex, files placed in `templates/` are silent — not loaded, not advertised. **Resolution path:** if grill-me ships templates, place them under `references/` for Codex parity, or duplicate into both `templates/` (Claude) and `references/` (Codex).

---

## References (consolidated, accessed 2026-04-30)

Primary OpenAI documentation:
- Skills: https://developers.openai.com/codex/skills
- Plugins overview: https://developers.openai.com/codex/plugins
- Build plugins: https://developers.openai.com/codex/plugins/build
- Subagents: https://developers.openai.com/codex/subagents
- Hooks: https://developers.openai.com/codex/hooks
- Custom Prompts (deprecated): https://developers.openai.com/codex/custom-prompts
- CLI features: https://developers.openai.com/codex/cli/features
- CLI reference: https://developers.openai.com/codex/cli/reference
- CLI slash commands: https://developers.openai.com/codex/cli/slash-commands
- IDE slash commands: https://developers.openai.com/codex/ide/slash-commands
- Configuration reference: https://developers.openai.com/codex/config-reference
- Changelog: https://developers.openai.com/codex/changelog

OpenAI source code (codex-rs):
- Plugin loader (constants): https://github.com/openai/codex/blob/main/codex-rs/core-plugins/src/loader.rs
- Plugin manager: https://github.com/openai/codex/blob/main/codex-rs/core/src/plugins/manager.rs
- Skills loader: https://github.com/openai/codex/blob/main/codex-rs/core-skills/src/loader.rs

OpenAI plugin reference repo (https://github.com/openai/plugins):
- Marketplace example: https://github.com/openai/plugins/blob/main/.agents/plugins/marketplace.json
- Build Web Apps plugin: https://github.com/openai/plugins/tree/main/plugins/build-web-apps
- Figma plugin: https://github.com/openai/plugins/tree/main/plugins/figma
- Vercel plugin: https://github.com/openai/plugins/tree/main/plugins/vercel
- Superpowers plugin: https://github.com/openai/plugins/tree/main/plugins/superpowers
- Cloudflare plugin: https://github.com/openai/plugins/tree/main/plugins/cloudflare

OpenAI GitHub issues (decisive context):
- Custom slash commands deprecated: https://github.com/openai/codex/issues/7480
- SKILL.md as slash commands (closed via skills): https://github.com/openai/codex/issues/13893
- ask_user_question feature/status: https://github.com/openai/codex/issues/9926
