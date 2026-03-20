# SpecKit Command Guide

Per-command coaching for the official SpecKit slash commands. This is NOT the command logic itself (that's installed by `specify init` in `.specify/` and your agent's command directory). This guide covers **when to use each command, how to get the best results, common mistakes, and phase gates**.

## Command Chaining (The Official Workflow)

```
constitution → specify → clarify (opt) → plan → checklist (opt) → tasks → analyze (opt) → implement
```

- **Required**: constitution, specify, plan, tasks, implement
- **Recommended**: clarify, analyze (always run before implement)
- **Optional**: checklist (skip for trivial features)

Each command depends on artifacts from previous commands. You cannot skip required commands.

---

## `/speckit.constitution` — Project Governance

### When to Run
- **First** — before any specs. Run this when initializing a new project or when project principles need updating.
- Re-run when adding new architectural principles or amending existing ones.

### How to Get the Best Results
- Define **testable** principles, not aspirational statements. "All functions must have type annotations" is testable. "Code should be clean" is not.
- Keep to 5-8 principles maximum. Too many principles create contradictions.
- Use semantic versioning: MAJOR (new principles), MINOR (amendments), PATCH (clarifications).
- Include quality gates — specific commands that verify principle compliance (e.g., `pyright .`, `npm run build`).

### Common Mistakes
- Writing principles that are too vague to enforce ("write good code")
- Technology-locked principles that prevent future migration
- Too many principles that create contradictions
- **Known issue**: Codex may modify templates during constitution creation ([Issue #1229](https://github.com/github/spec-kit/issues/1229))

### What It Produces
- `.specify/memory/constitution.md` — the project's governing principles

### Next Command
→ `/speckit.specify` to start creating feature specifications

---

## `/speckit.specify` — Create Feature Specification

### When to Run
- When starting a new feature. Focus on WHAT and WHY, never HOW.

### How to Get the Best Results

**The most important tip**: "Having a very detailed first prompt will produce a much better specification." Think through what you want and don't want before invoking `/specify`.

- Write **independently testable user stories** — each story should be deliverable as a standalone MVP slice
- Prioritize stories: P1 (must-have), P2 (should-have), P3 (nice-to-have)
- Use Given/When/Then format for acceptance scenarios
- Use `[NEEDS CLARIFICATION: specific question]` markers for any ambiguity — don't guess
- Define **measurable** success criteria, not vague outcomes
- Include explicit "Out of Scope" section to prevent scope creep
- SpecKit auto-detects your feature from the current Git branch

### Common Mistakes
- Too vague initial prompt — cascading quality issues through all downstream commands
- Including implementation details (tech stack, APIs, code structure) — keep it business-level
- Writing untestable requirements ("the system should be fast")
- Not defining Out of Scope — leads to unbounded features
- Forgetting to commit spec.md before moving to the next phase

### Gate G1
- [ ] No `[NEEDS CLARIFICATION]` markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] User stories are independently testable

### What It Produces
- `specs/<number>-<feature-name>/spec.md`
- `specs/<number>-<feature-name>/checklists/requirements.md`

### Next Command
→ `/speckit.clarify` (if spec has `[NEEDS CLARIFICATION]` markers) or `/speckit.plan` (if spec is clean)

---

## `/speckit.clarify` — Resolve Ambiguities

### When to Run
- When spec has `[NEEDS CLARIFICATION]` markers
- When areas could be interpreted multiple ways
- "10-20 minutes here saves hours of rework later"

### When to Skip
- Spec has zero `[NEEDS CLARIFICATION]` markers
- All requirements are clearly testable and unambiguous
- You're working on a trivial feature

### How to Get the Best Results
- Focus each clarify session on a specific domain (e.g., "Focus on UX" or "Focus on API contracts")
- Evaluate AI recommendations critically — they're suggestions, not mandates
- Maximum 5 questions per session
- Each accepted answer is immediately integrated into spec.md
- You can say "recommended" or "suggested" to accept the AI's recommendation

### When Enough is Enough
- All `[NEEDS CLARIFICATION]` markers are resolved
- No remaining ambiguities in acceptance scenarios
- You've done 2-3 sessions without surfacing new issues

### Common Mistakes
- Running too many sessions on a simple feature
- Accepting all AI recommendations without thinking critically
- Not reviewing the updated spec after clarification

### Gate G2
- [ ] All `[NEEDS CLARIFICATION]` markers resolved
- [ ] All decisions documented in `## Clarifications` section
- [ ] Updated spec reviewed and approved

### What It Produces
- Updated `spec.md` with clarifications integrated
- `## Clarifications` section with dated session logs

### Next Command
→ `/speckit.plan`

---

## `/speckit.plan` — Implementation Planning

### When to Run
- After spec is finalized (G1/G2 gates passed). Now you define HOW.

### How to Get the Best Results
- Provide your tech stack and architecture preferences — the plan needs this context
- Constitution gates run automatically — review the Simplicity, Anti-Abstraction, and Integration-First gates
- Phase 0 generates `research.md` to resolve technical unknowns
- Phase 1 generates supporting artifacts: `data-model.md`, `contracts/`, `quickstart.md`
- File creation order matters: contracts → tests → implementation
- Keep the plan high-level and readable — detailed algorithms go in supporting files

### Common Mistakes
- Skipping constitution gate pre-check — violations surface late and are expensive to fix
- Not reviewing research.md — it contains critical technical decisions
- Including too much implementation detail in plan.md — use supporting files
- Forgetting to review generated data models and contracts

### Gate G3
- [ ] Architecture approved
- [ ] Constitution gates pass (Simplicity, Anti-Abstraction, Integration-First)
- [ ] Dependencies identified
- [ ] No unresolved technical unknowns in research.md

### What It Produces
- `plan.md` — technical implementation plan
- `research.md` — decision rationales (Phase 0)
- `data-model.md` — entities and types (Phase 1)
- `contracts/` — API specifications (Phase 1)
- `quickstart.md` — developer onboarding (Phase 1)

### Next Command
→ `/speckit.checklist` (recommended) or `/speckit.tasks`

---

## `/speckit.checklist` — Validate Requirement Quality

### When to Run
- After plan is complete. Validates both spec AND plan together.
- Run multiple times for different domains.

### The Key Concept: "Unit Tests for English"
Checklists validate **requirement quality**, NOT implementation correctness.

- WRONG: "Verify button clicks correctly" (testing implementation)
- CORRECT: "Are visual hierarchy requirements defined with measurable criteria?" (testing requirement quality)

### How to Get the Best Results
- **Analyze the spec first** — don't pick domains from a generic list. Read `spec.md` and `plan.md` to identify which domains have the highest risk and most ambiguity.
- **Use enriched prompts** — don't just run `/speckit.checklist security`. Add spec-specific focus areas: "Focus on JWT validation for the auth middleware, input sanitization for the search field, and Bedrock API key management."
- Each run creates a NEW checklist file (never overwrites previous)
- Items should include traceability references: `[Spec §X.Y]`, `[Gap]`, `[Ambiguity]`
- Minimum 80% of items should include traceability to spec sections
- Address all `[Gap]` markers by updating spec.md or plan.md
- See [Checklist Domains Guide](./checklist-domains-guide.md) for the full signal extraction algorithm and enriched prompt patterns

### Common Mistakes
- **Running bare domain prompts** — `/speckit.checklist security` without focus areas produces generic items that don't test YOUR spec's specific requirements
- Writing checklist items that test implementation instead of requirements
- Using generic checklists instead of domain-specific ones
- Not addressing `[Gap]` items — they represent missing requirements
- Choosing domains based on project type alone instead of analyzing what's actually in the spec

### Gate G4
- [ ] All `[Gap]` markers addressed (spec/plan updated)
- [ ] Traceability ≥80% across all checklists
- [ ] No unaddressed ambiguities

### What It Produces
- `checklists/<domain>.md` — per-domain validation checklists

### Next Command
→ `/speckit.tasks`

---

## `/speckit.tasks` — Generate Task Breakdown

### When to Run
- After checklist gaps are resolved. Generates atomic, ordered implementation tasks.

### How to Get the Best Results
- Tasks are organized **by user story** (P1, P2, P3...), NOT by technical layer
- Each user story phase should be **independently testable**
- Task format: `- [ ] [T001] [P] [US1] Description with exact file path`
- `[P]` marks tasks safe for parallel execution
- Foundational phase blocks ALL user stories — it's critical shared infrastructure
- Tests are OPTIONAL — only if explicitly requested in spec or by user

### Phase Structure
1. **Phase 1: Setup** — Project initialization, shared infrastructure
2. **Phase 2: Foundational** — MUST complete before ANY user story
3. **Phase 3+: User Story phases** — One phase per story (P1, P2, P3...)
4. **Final Phase: Polish** — Cross-cutting concerns

### Common Mistakes
- Organizing by tech layer (all backend, then all frontend) — breaks independent delivery
- Tasks that touch too many files (keep to 2-3 files max)
- Missing exact file paths — tasks should be precise enough to execute
- Not marking parallel-safe tasks with `[P]`
- Forgetting the foundational phase

### Gate G5
- [ ] Coverage verified — every FR and user story has tasks
- [ ] Dependencies ordered correctly
- [ ] Parallel opportunities identified with `[P]`
- [ ] Each user story phase independently testable

### What It Produces
- `tasks.md` — dependency-ordered task list

### Next Command
→ `/speckit.analyze` (recommended — always run before implement)

---

## `/speckit.analyze` — Cross-Artifact Consistency

### When to Run
- **Always** run after generating tasks, before implementing. It catches issues cheaply.

### How to Get the Best Results
- This is STRICTLY read-only — it only produces a report, never modifies files
- Maximum 50 findings to stay actionable
- Constitution alignment violations are automatically marked CRITICAL
- Review the coverage summary table — unmapped requirements are gaps

### How to Interpret Results

| Severity | Meaning | Action |
|----------|---------|--------|
| CRITICAL | Blocks implementation, violates constitution | **Must fix before implementing** |
| HIGH | Significant gap in coverage or consistency | Should fix |
| MEDIUM | Quality improvement opportunity | Review and decide |
| LOW | Minor inconsistency or optimization | Note for future |

### Common Mistakes
- Ignoring CRITICAL findings — they will cause implementation failures
- Running analyze without tasks.md (it needs all three: spec, plan, tasks)
- Not re-running after fixing issues from the report

### Gate G6
- [ ] No CRITICAL issues
- [ ] HIGH issues reviewed and either fixed or justified
- [ ] Coverage summary shows no unmapped requirements

### What It Produces
- Analysis report with findings table, coverage summary, and recommendations

### Next Command
→ `/speckit.implement`

---

## `/speckit.implement` — Execute Tasks

### When to Run
- After all gates passed. This is the code generation phase.

### How to Get the Best Results
- Implementation checks checklists first — if incomplete, it will ask whether to proceed
- Execution is phase-by-phase, respecting task dependencies
- Tasks marked `[P]` can run in parallel within a phase
- TDD approach: Red (write failing test) → Green (make it pass) → Refactor
- Completed tasks are marked `[X]` in tasks.md

### Common Mistakes
- Skipping the checklist pre-check prompt ("Do you want to proceed anyway?")
- Not committing after each phase — makes rollback impossible
- Trying to implement everything at once instead of phase-by-phase

### Gate G7
- [ ] All tasks marked complete in tasks.md
- [ ] Tests pass
- [ ] Manual verification complete
- [ ] Code review done

### What It Produces
- Working code implementing all tasks
- Updated tasks.md with completed task markers

---

## `/speckit.taskstoissues` — Export to GitHub Issues

### When to Run
- After tasks.md is finalized and you want to track tasks as GitHub Issues.

### What It Does
- Converts tasks.md entries into dependency-ordered GitHub Issues
- Requires GitHub MCP server connection

### What It Produces
- GitHub Issues for each task with labels, dependencies, and descriptions

---

## Extension Commands (Installed)

These commands are provided by installed SpecKit extensions.
They extend the core workflow with post-implementation quality
gates, code review, and project diagnostics.

### Verify Extension — `/speckit.verify` / `/speckit.verify.run`

**Purpose:** Post-implementation verification gate. Validates
that the implementation matches spec.md, plan.md, tasks.md,
and constitution.md.

**When to run:** After `/speckit.implement`, before PR creation.
Non-destructive (read-only report).

**What it checks:** Spec adherence, plan conformance, task
completion, constitution alignment.

### Verify Tasks — `/speckit.verify-tasks` / `/speckit.verify-tasks.run`

**Purpose:** Detect phantom completions — tasks marked `[X]`
in tasks.md that have no real implementation behind them
(missing files, dead code, or empty stubs).

**When to run:** After implementation, especially if tasks were
marked complete programmatically.

**What it checks:** Five-layer verification cascade against
every completed task.

### Review Extension — `/speckit.review` / `/speckit.review.run`

**Purpose:** Comprehensive code review using 6 specialized
agents. Orchestrates all sub-reviews sequentially.

**Sub-commands** (can be run individually):

| Command | Focus |
|---------|-------|
| `/speckit.review.code` | Project guideline compliance, bug detection, code quality |
| `/speckit.review.comments` | Comment accuracy, documentation completeness, comment rot |
| `/speckit.review.tests` | Behavioral coverage, critical gaps, test resilience |
| `/speckit.review.errors` | Silent failure detection, catch block analysis, error logging |
| `/speckit.review.types` | Encapsulation, invariant expression, usefulness, enforcement |
| `/speckit.review.simplify` | Clarity, unnecessary complexity, redundant abstractions (advisory) |

**When to run:** After implementation, as part of code review
workflow. Can run full suite (`/speckit.review`) or individual
agents for focused review.

### Retrospective — `/speckit.retrospective.analyze`

**Purpose:** Post-implementation retrospective measuring spec
adherence, implementation deviations, and lessons learned.
Generates a `retrospective.md` with adherence scoring and
drift analysis.

**When to run:** After implementation is complete and PR is
merged. Human-gated spec updates based on findings.

### Cleanup — `/speckit.cleanup` / `/speckit.cleanup.run`

**Purpose:** Post-implementation quality gate following the
scout rule — fix small issues immediately, create tasks for
medium issues, generate analysis for large issues.

**When to run:** After implementation. Can fix small issues
(formatting, naming, dead code) and flag larger concerns.

### Doctor — `/speckit.doctor` / `/speckit.doctor.check`

**Purpose:** Full project health diagnostic. Checks structure,
agents, features, scripts, extensions, and git status.

**When to run:** Anytime. Useful for:
- Verifying project setup after `specify init`
- Diagnosing issues with extensions or commands
- Health check before starting a new spec

---

## CLI Commands (v0.3.2)

Beyond the slash commands above, the `specify` CLI provides
project management commands for presets, extensions, and
project health.

### `specify check` — Installation Health

Verifies all required tools are installed and operational.

```bash
specify check
```

Shows which AI agents are detected (25+ supported), Git status, and CLI readiness.

### `specify version` — Version Information

```bash
specify version
```

Shows CLI version, template version, platform, and architecture.

---

## Presets — Customizing Workflows

Presets are **stackable, priority-ordered collections of template
and command overrides**. They customize how specs, plans, tasks,
checklists, and constitutions are generated without modifying
core files.

### When to Use Presets

- **Methodology adaptation** — enforce Agile, Kanban, DDD, or custom methodology patterns in templates
- **Compliance formatting** — add required sections, disclaimers, or formatting to artifacts
- **Localization** — translate template sections to other languages
- **Project-specific patterns** — encode TDD enforcement, architecture conventions, or testing mandates

### Preset Commands

| Command | Description |
|---------|-------------|
| `specify preset search` | Browse available presets in catalogs |
| `specify preset add <name>` | Install preset from catalog |
| `specify preset add --dev <path>` | Install from local directory (development) |
| `specify preset add <name> --priority N` | Install with specific priority (lower wins) |
| `specify preset list` | Show installed presets |
| `specify preset resolve <template>` | Show which file wins for a template name |
| `specify preset info <name>` | Get detailed preset information |
| `specify preset remove <name>` | Uninstall preset |
| `specify preset catalog list` | List active preset catalogs |
| `specify preset catalog add <url>` | Add custom preset catalog |
| `specify preset catalog remove <name>` | Remove preset catalog |

### Template Resolution Order

When a `/speckit.*` command needs a template, resolution checks
these locations in order (first match wins):

1. **Project overrides** — `.specify/templates/overrides/`
2. **Installed presets** — `.specify/presets/<id>/templates/` (sorted by priority, lower number wins)
3. **Extension templates** — `.specify/extensions/<id>/templates/`
4. **Core templates** — `.specify/templates/`

Use `specify preset resolve <template-name>` to debug which
file is actually being used.

### Stacking Presets

Multiple presets can be installed simultaneously. Lower priority
numbers win when templates conflict:

```bash
specify preset add compliance --priority 5    # wins over...
specify preset add agile --priority 10        # ...this one
```

**Presets override, they don't merge.** When two presets provide
the same template, the lower priority number's version is used
entirely.

### Creating Custom Presets

1. Copy the `scaffold/` directory from the spec-kit repo
2. Edit `preset.yml` with your metadata (id, name, version, priority)
3. Add/modify templates in `templates/`
4. Test locally: `specify preset add --dev .`
5. Verify: `specify preset resolve spec-template`

### Configuration

| Location | Scope |
|----------|-------|
| `.specify/preset-catalogs.yml` | Project-level custom catalogs |
| `~/.specify/preset-catalogs.yml` | User-level custom catalogs |
| `SPECKIT_PRESET_CATALOG_URL` env var | Environment override |

---

## Extensions — Adding Capabilities

Extensions are **modular packages** that add new commands, hooks,
and workflows to SpecKit without modifying the core framework.
They're independently versioned and optionally installed.

### Extension Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| **docs** | Read, validate, or generate spec artifacts | Archive, DocGuard, Retrospective, Spec Sync |
| **code** | Review, validate, or modify source code | Cleanup, Review, Verify, Verify Tasks |
| **process** | Orchestrate workflow across phases | Conduct, Fleet Orchestrator, SDD Utilities |
| **integration** | Sync with external platforms | Azure DevOps, Jira |
| **visibility** | Report on project health or progress | Project Health Check, Project Status |

### Extension Commands

| Command | Description |
|---------|-------------|
| `specify extension search` | Browse all extension catalogs |
| `specify extension search <keyword>` | Search by keyword |
| `specify extension search --tag <tag>` | Filter by tag |
| `specify extension search --author <name>` | Filter by author |
| `specify extension search --verified` | Show verified only |
| `specify extension info <name>` | Detailed extension info |
| `specify extension add <name>` | Install from approved catalog |
| `specify extension add --from <url>` | Install from ZIP URL |
| `specify extension add --dev <path>` | Install from local directory |
| `specify extension list` | Show installed extensions |
| `specify extension update [name]` | Check for / apply updates |
| `specify extension disable <name>` | Disable temporarily |
| `specify extension enable <name>` | Re-enable |
| `specify extension remove <name>` | Remove completely |
| `specify extension remove <name> --keep-config` | Remove but preserve config |
| `specify extension catalog list` | List active extension catalogs |
| `specify extension catalog add <url>` | Add custom catalog |
| `specify extension catalog remove <name>` | Remove catalog |

### Community Extensions (26 available)

| Extension | Category | Purpose |
|-----------|----------|---------|
| Archive | docs | Archive merged features into project memory |
| Cognitive Squad | docs | Multi-agent system with Triadic Model |
| DocGuard | docs | Documentation validation and scoring |
| Iterate | docs | Two-phase refine-and-apply for spec docs |
| Learning | docs | Generate educational guides from implementations |
| Reconcile | docs | Update artifacts to address implementation drift |
| Retrospective | docs | Post-implementation review with spec adherence scoring |
| Spec Sync | docs | Detect and resolve drift between specs and code |
| Understanding | docs | Quality analysis using 31 metrics (IEEE/ISO) |
| V-Model | docs | Paired generation of development and test specs |
| Cleanup | code | Quality gate — fix small issues, create tasks for medium |
| Ralph Loop | code | Autonomous implementation using AI agent CLI |
| Review | code | Comprehensive code review with 6 specialized agents |
| Verify | code | Post-implementation verification against spec artifacts |
| Verify Tasks | code | Detect phantom completions (tasks marked done but not implemented) |
| Conduct | process | Orchestrate phases via sub-agent delegation |
| Fleet Orchestrator | process | Full feature lifecycle with human-in-the-loop gates |
| SDD Utilities | process | Resume workflows, validate health, verify traceability |
| Azure DevOps | integration | Sync user stories and tasks to Azure DevOps work items |
| Jira | integration | Create Epics, Stories, and Issues from specifications |
| Project Health Check | visibility | Diagnose project across multiple dimensions |
| Project Status | visibility | Show current SDD workflow progress |

### Hook Events

Extensions can register hooks that fire before or after core
commands. Available hook events:

| Event | Fires | Example Use |
|-------|-------|-------------|
| `before_specify` | Before `/speckit.specify` | Pre-flight checks |
| `after_specify` | After `/speckit.specify` | Auto-sync to external tools |
| `before_plan` | Before `/speckit.plan` | Validate prerequisites |
| `after_plan` | After `/speckit.plan` | Generate additional artifacts |
| `before_tasks` | Before `/speckit.tasks` | Verify plan completeness |
| `after_tasks` | After `/speckit.tasks` | Verify tasks, create issues |
| `before_implement` | Before `/speckit.implement` | Checklist pre-check |
| `after_implement` | After `/speckit.implement` | Code review, retrospective |

Configure hooks in `.specify/extensions.yml`:

```yaml
hooks:
  after_tasks:
    - extension: verify-tasks
      command: speckit.verify-tasks.run
      enabled: true
      optional: true
      prompt: "Verify all tasks are properly specified?"
  after_implement:
    - extension: verify
      command: speckit.verify.run
      enabled: true
      optional: true
      prompt: "Verify implementation against spec?"
```

### Extension Configuration Layers

Configuration resolves in priority order (higher overrides lower):

1. **Extension defaults** — built into the extension
2. **Project config** — `.specify/extensions/<ext>/<ext>-config.yml` (committed to git)
3. **Local overrides** — `.specify/extensions/<ext>/<ext>-config.local.yml` (gitignored)
4. **Environment variables** — `SPECKIT_<EXT_ID>_*` (e.g., `SPECKIT_JIRA_PROJECT_KEY`)

### Catalog Management

SpecKit searches a **catalog stack** — multiple catalogs
checked simultaneously:

| Priority | Catalog | Installable? | Purpose |
|----------|---------|-------------|---------|
| 1 | `catalog.json` (default) | Yes | Curated, installable extensions |
| 2 | `catalog.community.json` | No | Discovery-only community extensions |

Add custom catalogs for your organization:

```bash
specify extension catalog add \
  --name "internal" \
  --install-allowed \
  https://internal.company.com/spec-kit/catalog.json
```

Or configure in `.specify/extension-catalogs.yml`:

```yaml
catalogs:
  - name: "internal"
    url: "https://internal.company.com/catalog.json"
    priority: 2
    install_allowed: true
```

### Version Control for Extensions

**Commit to git:**
- `.specify/extensions.yml` (installed extension list + hooks)
- `.specify/extensions/*/<ext>-config.yml` (shared config)

**Gitignore:**
- `.specify/extensions/.cache/`
- `.specify/extensions/.backup/`
- `.specify/extensions/*/*.local.yml`
- `.specify/extensions/.registry`

---

## Upgrade Guidance

### Upgrading the CLI

```bash
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git
```

Verify: `specify version` → should show latest version.

### Upgrading Project Files

```bash
# 1. Back up constitution (WILL be overwritten)
cp .specify/memory/constitution.md .specify/memory/constitution-backup.md

# 2. Back up custom templates
cp -r .specify/templates .specify/templates-backup

# 3. Run upgrade
specify init --here --force --ai claude

# 4. Restore constitution
git restore .specify/memory/constitution.md
# or: cp .specify/memory/constitution-backup.md .specify/memory/constitution.md

# 5. Verify
specify check
```

### What's Safe

- **`specs/` directory** — completely excluded from template packages, never modified
- **Extension configurations** — not touched by `specify init`
- **Preset configurations** — not touched by `specify init`

### What's Overwritten

- **Constitution** (`constitution.md`) — always back up first
- **Templates** (`.specify/templates/`) — custom modifications lost
- **Scripts** (`.specify/scripts/`) — replaced with latest hardened versions
- **Commands** (`.claude/commands/speckit.*`) — replaced with latest versions

### Version Compatibility

| Feature | Minimum Version |
|---------|----------------|
| Core commands (specify, plan, tasks, etc.) | Any version |
| Presets (`specify preset *`) | v0.3.0+ |
| Extensions (`specify extension *`) | v0.2.0+ |
| Hook events (before/after) | v0.3.1+ |
| Enable/disable toggle | v0.3.2+ |
| `init-options.json` persistence | v0.3.0+ |

Check your version: `specify version`

### Common Issues

- **Duplicate slash commands** in IDE agents — delete old files, restart IDE
- **`SPECIFY_FEATURE` env var** for non-git repos: `export SPECIFY_FEATURE="001-my-feature"`
- **Custom templates lost** — use presets instead of modifying core templates (presets survive upgrades)
