# Presets & Extensions Guide

Comprehensive guide to SpecKit's extensibility system. Presets
customize how specs are generated; extensions add new capabilities.
Both are independently versioned, stackable, and upgrade-safe.

---

## Presets — Template Customization

Presets are **stackable, priority-ordered collections of template
and command overrides**. They change how specs, plans, tasks,
checklists, and constitutions are generated — without modifying
core files.

### When to Use Presets

| Use Case | Example |
|----------|---------|
| Methodology enforcement | Agile story points, DDD bounded contexts |
| Compliance formatting | Add regulatory sections, audit requirements |
| Localization | Translate template sections to other languages |
| Project conventions | Enforce TDD, architecture patterns, test mandates |
| Team standards | Standardize artifact structure across repos |

### Preset Commands

```text
# Discovery
specify preset search                         # browse available presets
specify preset search --tag <tag>             # filter by tag
specify preset search --author <author>       # filter by author
specify preset info <name>                     # detailed preset info

# Installation
specify preset add <name>                      # install from catalog
specify preset add --from <url>                # install from ZIP URL
specify preset add <name> --priority 5         # install with priority (lower wins)
specify preset add --dev ./my-preset           # install from local directory

# Management
specify preset list                            # show installed presets
specify preset resolve <template-name>         # show which file wins for a template
specify preset remove <name>                   # uninstall preset
specify preset enable <name>                   # re-enable a disabled preset
specify preset disable <name>                  # disable without removing
specify preset set-priority <name> <N>         # change resolution priority

# Catalog management
specify preset catalog list                    # list active preset catalogs
specify preset catalog add <url>               # add custom catalog
specify preset catalog remove <name>           # remove catalog
```

### Template Resolution Order

When a SpecKit skill needs a template, the system checks
these locations in order — first match wins:

```
1. .specify/templates/overrides/           ← project-local tweaks (highest priority)
2. .specify/presets/<id>/templates/         ← installed presets (sorted by priority number)
3. .specify/extensions/<id>/templates/      ← extension-provided templates
4. .specify/templates/                     ← core defaults (lowest priority)
```

**Lower priority numbers win.** A preset with priority 5 beats
one with priority 10 when both provide the same template.

**Presets override, they don't merge.** When two presets provide
`spec-template.md`, only the lower-priority one is used — they
are not combined.

### Preset Configuration

| Location | Scope |
|----------|-------|
| `.specify/preset-catalogs.yml` | Project-level custom catalogs |
| `~/.specify/preset-catalogs.yml` | User-level custom catalogs |
| `SPECKIT_PRESET_CATALOG_URL` env var | Environment override |

---

## Extensions — Adding Capabilities

Extensions are **modular packages** that add new commands, hooks,
and workflows. They're independently versioned, optionally
installed, and organized into 5 categories.

### Extension Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| **docs** | Read, validate, or generate spec artifacts | Archive, DocGuard, Retrospective |
| **code** | Review, validate, or modify source code | Cleanup, Review, Verify |
| **process** | Orchestrate workflow across phases | Conduct, Fleet Orchestrator |
| **integration** | Sync with external platforms | Azure DevOps, Jira |
| **visibility** | Report on project health or progress | Doctor, Project Status |

### Extension Commands

```text
# Discovery
specify extension search                       # browse all catalogs
specify extension search <keyword>             # search by keyword
specify extension search --tag <tag>           # filter by tag
specify extension search --author <name>       # filter by author
specify extension search --verified            # verified extensions only
specify extension info <name>                  # detailed info

# Installation
specify extension add <name>                   # install from approved catalog
specify extension add <name> --from <zip-url>         # install from GitHub release URL
specify extension add --dev <path>             # install from local directory

# Management
specify extension list                         # show installed extensions
specify extension list --available             # show available from catalogs
specify extension list --all                   # show all (installed + available)
specify extension update [name]                # check for / apply updates
specify extension disable <name>               # disable temporarily
specify extension enable <name>                # re-enable
specify extension remove <name>                # remove completely
specify extension remove <name> --force        # force removal without confirmation
specify extension remove <name> --keep-config  # remove but preserve config
specify extension remove <name> --force        # skip confirmation
specify extension set-priority <name> <N>     # change resolution priority

# Catalog management
specify extension catalog list                 # list active catalogs
specify extension catalog add <url> --name <n> --install-allowed
specify extension catalog remove <name>        # remove catalog
```

### Extensions speckit-pro's autopilot routes to by name

These are a stable contract between this plugin and a curated set of
extension ids. The autopilot's post-implementation workflow auto-dispatches
to them when they're present in `.specify/extensions/.registry`, and
gracefully skips them when they're not. The ids are bare (no `spec-kit-`
prefix) — they match what's published in the upstream
`extensions/catalog.community.json`.

| Extension | ID | Category | Used by autopilot for |
|-----------|----|----------|------------------------|
| Archive | `archive` | docs | Archive Sweep at startup |
| Project Health Check | `doctor` | visibility | Track A — post-impl health check |
| Review | `review` | code | Track B — post-impl code review |
| Verify | `verify` | code | Track C step 1 — implementation-vs-spec |
| Verify Tasks | `verify-tasks` | code | Track C step 2 — phantom task detector |
| Retrospective | `retrospective` | docs | Sequential after Cleanup — post-impl reflection |

Use the catalog's `id` value for native install commands; display names and
repository names are not installation IDs.

### The curated set

`speckit-pro/scripts/curated-set.json` is a manual recommendation catalog read
by the install and upgrade skills. They list missing entries and ask the
operator which ones to install. For each accepted entry, use the native
`specify extension add <id>` or `specify preset add <id>` command.

| ID | Kind | What speckit-pro uses it for |
|----|------|-----------------------------|
| `review` | extension | Post-impl Code Review track |
| `verify` | extension | Post-impl Verify chain — implementation-vs-spec |
| `verify-tasks` | extension | Post-impl Verify chain — phantom-task detector |
| `cleanup` | extension | Sequential after the parallel group — scout-rule cleanup |
| `retrospective` | extension | Sequential after Cleanup — post-impl reflection |
| `claude-ask-questions` | preset | Upgrades `/speckit-clarify` and `/speckit-checklist` to use the native AskUserQuestion picker on Claude Code |

**Carve-out — the archive extension stays pinned.** The Racecraft
archive extension (`racecraft-lab/spec-kit-archive`) is **not** in the
curated set and keeps its existing pinned-tag rule documented in the
Archive Extension section below. Different trust model (Racecraft-
owned), different install discipline (vendored or pinned by the
operator), different provenance bar (full recovery commands).

### Browsing the live catalog — three plays

The full community catalog has grown to 100+ extensions and changes
frequently upstream. Rather than mirroring it here (and going stale on
every upstream merge), the coach reaches the authoritative sources on
demand. Three plays cover the common interactions.

#### Play 1 — Discovery ("what's available?", "find an extension for X")

The user wants to browse or search the catalog. Run `specify extension
search` against the user's local catalog stack (which respects custom
catalogs and `SPECKIT_CATALOG_URL` env overrides):

```text
specify extension search                       # browse everything
specify extension search <keyword>             # filter by keyword
specify extension search --tag <tag>           # filter by tag
specify extension search --author <author>     # filter by author
specify extension search --verified            # verified extensions only
```

Parse the output and render it as a markdown table grouped by category.

If `specify` is unavailable, fall back to the GitHub API against the
authoritative catalog file and parse the returned JSON with a
standard-library JSON reader:

```text
gh api /repos/github/spec-kit/contents/extensions/catalog.community.json
decode the content field and filter extensions by keyword
```

If neither CLI is available, WebFetch the raw URL:
`https://raw.githubusercontent.com/github/spec-kit/main/extensions/catalog.community.json`

#### Play 2 — Deep dive ("tell me about the X extension")

The user wants details on one extension. Run `specify extension info <id>`
to get the full manifest, then surface the salient fields (commands
provided, hook events, `requires.speckit_version`, tags, repository URL):

```text
specify extension info <id>
```

If `specify` doesn't know about the extension (e.g., the user is asking
about something they read on a blog), fetch the extension's own
`extension.yml` from its repository. The `repository` field in the catalog
entry gives the URL; the manifest path is typically
`<repo>/blob/main/extension.yml`:

```text
gh api /repos/<owner>/<repo>/contents/extension.yml
decode the content field and read extension.yml
```

Read out: `provides.commands` (what slash commands the extension adds),
`hooks` (which phase boundaries it fires on), `requires.speckit_version`
(compatibility), and `tags`. Cross-reference against the user's installed
SpecKit version (`specify --version`) before recommending install.

#### Play 3 — Install, configure, remove

The user wants to change extension state. **Always confirm with the user
before running any mutation.** Once confirmed:

```text
# Install (community extensions are "discovery only" — must use --from)
specify extension add <id> --from https://github.com/<owner>/<repo>/archive/refs/tags/<tag>.zip

# Lifecycle
specify extension remove <id>
specify extension enable <id>
specify extension disable <id>
specify extension set-priority <id> <N>
```

**End every install / configure / hook-wiring response with this
two-line block, verbatim. Do not skip it,
even if the rest of the response is long. The closing block is non-negotiable
because long install walkthroughs reliably bury these two facts.**

Closing block (copy verbatim, substituting `<id>` with the real extension id):

```
**No plugin update or restart needed** — the autopilot re-reads
`.specify/extensions.yml` at every phase boundary, so any hook you wire
here fires on the next autopilot run. No `claude` / `codex` restart,
no `/plugin marketplace update`, no session reload.

**Two config files to know:** `.specify/extensions/<id>/<id>-config.yml`
(shared, commit to git) and `.specify/extensions/<id>/<id>-config.local.yml`
(personal, gitignored).
```

The 4-tier configuration resolution (defaults → project config → local
override → env var) is documented in the "Extension Configuration Layers"
section below.

If the new extension should fire automatically at a phase boundary,
register a hook in `.specify/extensions.yml`:

```yaml
hooks:
  after_implement:
    - extension: <id>
      command: speckit.<id>.run
      enabled: true
      optional: true
      prompt: "Run <extension-name> after implementation?"
```

### Hook Events

Extensions can register hooks that fire before or after core SpecKit commands.
The install flow above supplies the focused hook block; inspect the installed
extension manifest before changing it.

**Available hook events:**

| Event | When It Fires |
|-------|---------------|
| `before_specify` | Before `/speckit-specify` runs |
| `after_specify` | After `/speckit-specify` completes |
| `before_plan` | Before `/speckit-plan` runs |
| `after_plan` | After `/speckit-plan` completes |
| `before_tasks` | Before `/speckit-tasks` runs |
| `after_tasks` | After `/speckit-tasks` completes |
| `before_implement` | Before `/speckit-implement` runs |
| `after_implement` | After `/speckit-implement` completes |

When `optional: true`, the hook prompts before running. When
`optional: false`, it runs automatically.

### Extension Configuration Layers

Configuration resolves in priority order (higher overrides lower):

```
1. Extension defaults                          ← built into the extension
2. Project config  (<ext>-config.yml)          ← committed to git, shared
3. Local overrides (<ext>-config.local.yml)    ← gitignored, per-developer
4. Environment vars (SPECKIT_<EXT_ID>_*)       ← runtime overrides
```

Example for the Jira extension:

```yaml
# .specify/extensions/jira/jira-config.yml (shared)
project:
  key: "MSATS"
defaults:
  epic:
    labels: ["spec-driven"]

# .specify/extensions/jira/jira-config.local.yml (personal)
project:
  key: "MYTEST"    # local development override
```

### Catalog Management

SpecKit searches a **catalog stack** — multiple catalogs
checked simultaneously:

| Priority | Catalog | Installable? |
|----------|---------|-------------|
| 1 | `catalog.json` (default) | Yes |
| 2 | `catalog.community.json` | No (discovery only) |

Add organizational catalogs:

```text
# Via CLI
specify extension catalog add \
  --name "internal" \
  --install-allowed \
  https://internal.company.com/spec-kit/catalog.json

# Via config file (.specify/extension-catalogs.yml)
catalogs:
  - name: "internal"
    url: "https://internal.company.com/catalog.json"
    priority: 2
    install_allowed: true
```

Environment override: `SPECKIT_CATALOG_URL`

### The Extension Registry

The CLI maintains a structured registry at `.specify/extensions/.registry`
(JSON). This is the **most authoritative** source for extension status:

```json
{
  "schema_version": "1.0",
  "extensions": {
    "verify": {
      "version": "1.0.0",
      "source": "local",
      "manifest_hash": "sha256:...",
      "enabled": true,
      "priority": 10,
      "registered_commands": {
        "claude": ["speckit.verify.run", "speckit.verify"],
        "gemini": ["speckit.verify.run", "speckit.verify"]
      },
      "installed_at": "2026-03-20T02:25:31Z"
    }
  }
}
```

**Key fields:**
- `enabled` — whether the extension is active (true/false)
- `registered_commands` — which command files were created per platform
- `priority` — resolution order (lower = higher precedence)
- `source` — "catalog" or "local" (from `--dev` flag)

**Detection priority for automation:**
1. `.registry` (most authoritative — has enabled/disabled status)
2. Glob for `.specify/extensions/*/extension.yml` (fallback)
3. NEVER rely solely on `installed` field in `.specify/extensions.yml`

### Version Control

**Commit to git:**
- `.specify/extensions.yml` — hook configuration
- `.specify/extensions/*/<ext>-config.yml` — shared config

**Gitignore:**
- `.specify/extensions/.cache/`
- `.specify/extensions/.backup/`
- `.specify/extensions/*/*.local.yml`
- `.specify/extensions/.registry`

Note: `.registry` is gitignored because it contains machine-specific
install timestamps and manifest hashes. Extension presence is determined
from the extension directories and `extensions.yml` hooks config. The
`installed` field in `extensions.yml` SHOULD list installed extensions
but may be empty if extensions were installed with older CLI versions.

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|---------|
| Extension not found | Misspelling or not in catalog | `specify extension search <keyword>` |
| Can't install from community | Community catalog is discovery-only | Use `--from <zip-url>` to install |
| Template not resolving | Wrong priority or missing file | `specify preset resolve <template>` |
| Hook not firing | Not configured in extensions.yml | Check `.specify/extensions.yml` hooks section |
| Extension command missing | Extension disabled or IDE needs restart | `specify extension list`, restart IDE |
| Config not applied | Wrong config layer or file name | Check 4-tier config priority |
| Preset lost after upgrade | Presets survive `specify integration upgrade`, including a `--force` escalation | Presets are safe — only core templates reset |
| Extension lost after upgrade | Extensions survive upgrades | Extensions are safe — check with `specify extension list` |
| `installed: []` but extensions exist | CLI didn't update field or older version | Check `.registry` or Glob for directories — those are authoritative |
| Autopilot skips extension tasks | Wrong detection — not reading `.registry` | Ensure Step 0.11 checks `.registry` first, then Glob fallback |
