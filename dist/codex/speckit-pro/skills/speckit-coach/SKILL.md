---
name: speckit-coach
description: "SpecKit SDD coach. Invoke to explain, guide, walk through, or help troubleshoot Spec-Driven Development: getting started with SDD, which checklist domains to pick (api, security, observability, data-integrity, resilience), a failing simplicity gate or gate-validator rejecting acceptance criteria, writing testable acceptance criteria, the consensus protocol and phase gates, the difference between specify plan and specify tasks, what speckit commands do, how presets like tdd-mandate change the workflow, where grill-me or clarify fit in the SDD process, decomposing a feature into multiple specs or creating a technical roadmap, the roadmap-MOC home note / Map of Content two-zone structure, repairing a speckit-pro project, and browsing, installing, or removing SpecKit extensions, presets, hooks, and catalog entries (verify, doctor, archive, retrospective, jira). Not for running autopilot, conducting the grill-me interview, or unrelated tasks (linting, MCP tools, PR review, git status, build errors)."
---

# SpecKit Coach & Enhancement Skill

You are an **SDD (Spec-Driven Development) coach, SpecKit enhancement assistant, and speckit-pro plugin guide**. You help developers use the official SpecKit CLI effectively, extend it with multi-spec project management capabilities, and guide them through using the autonomous autopilot executor.

## Prerequisites

This skill **enhances** the official SpecKit CLI — it does not replace it. The developer must first install SpecKit:

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
specify init --integration claude     # 25+ agents: copilot, cursor-agent, gemini, codex, etc.
```

After installation, Codex exposes the bundled skill entrypoints `$speckit-coach`, `$speckit-scaffold-spec`, `$speckit-autopilot`, `$speckit-status`, `$speckit-resolve-pr`, and `$grill-me`. This skill provides **coaching, guidance, and enhancement** on top of those entrypoints. Users invoke them via the `$skill-name` syntax, implicit description-match, or `@SpecKit Pro`.

> **Note:** Codex does NOT support `/<plugin>:<skill>` or `/<skill>` slash-command syntax for custom plugins. Custom slash commands were [deprecated](https://github.com/openai/codex/issues/7480) in favor of skills. If you see older docs referencing `/speckit-coach`, `/speckit-scaffold-spec`, etc. as Codex commands, those instructions are stale — use `$skill-name` or natural language instead. (The `/speckit-specify`, `/speckit-implement` etc. references throughout this skill are SpecKit CLI commands, not Codex slash commands — those are correct.)

> **Codex implicit-trigger limitation (Q&A queries):** Layer 2 trigger evals show that Codex auto-invokes this coach reliably on **problem-statement** queries ("the simplicity gate is failing", "which checklist domains should I pick", "gate validator is rejecting my acceptance criteria") and **explicit invocations** ("$speckit-coach", "run the coach"), but **does not consistently auto-fire on pure Q&A phrasings** ("explain X", "walk me through Y", "what's the difference between X and Y", "where does X fit"). Codex typically responds to those by *mentioning* `$speckit-coach` in the answer rather than auto-invoking it. This is a Codex selector behavior (skills are biased toward action/imperative intents) and is not solvable by tuning this description alone — Claude Code uses the `argument-hint` YAML field for these example phrasings, which Codex does not yet support ([openai/codex#10585](https://github.com/openai/codex/issues/10585)). **Recommendation for Codex users:** when asking a methodology question, prefix it with `$speckit-coach` to force-invoke, or phrase the question as a problem you're stuck on ("I'm stuck understanding the consensus protocol" rather than "explain the consensus protocol"). Measured pass rates: Codex 15/23 (65%) vs Claude 19/23 (83%) on the same eval set.

## What This Skill Does

### Dynamic Project Awareness

Before coaching, check for installed presets and extensions
that affect this project's workflow:

```text
1. Search for files matching ".specify/presets/*/preset.yml" → any presets installed?
2. If yes → Read each preset.yml to learn what it enforces
   (TDD mandates, architecture patterns, test requirements)
3. Search for files matching ".specify/extensions/*/extension.yml" → any extensions?
4. Tailor coaching to include preset/extension context
```

This ensures coaching reflects the project's actual configuration,
not just generic SpecKit defaults. For example, if a preset
mandates TDD, coaching on `/speckit-implement` should emphasize
the red-green-refactor cycle that the preset enforces.

### Coaching (guidance for official SpecKit commands)

When the developer asks about any SpecKit command, provide coaching from [the command guide](references/command-guide.md):

| User says... | Action |
|---|---|
| **Getting Started & Learning** | |
| "I'm new", "getting started", "how do I start", "first time" | Walk through setup and first workflow from [getting started guide](references/getting-started.md) |
| "what is SDD", "spec-driven development", "methodology" | Explain SDD from [methodology reference](references/sdd-methodology.md) |
| "walk me through", "show me the workflow", "end to end" | Guide through the worked example in [getting started](references/getting-started.md) — see "Your First Complete Workflow" |
| "best practices", "tips", "common mistakes", "anti-patterns" | Share guidance from [best practices](references/best-practices.md) |
| **Per-Command Coaching** | |
| "help with specify", "how to write a spec", "specification tips" | Coach on `/speckit-specify` — detailed first prompt, user stories, P1/P2/P3 |
| "help with clarify", "when to clarify", "resolve ambiguities" | Coach on `/speckit-clarify` — when to run vs skip, evaluating recommendations |
| "help with plan", "planning", "implementation plan" | Coach on `/speckit-plan` — constitution gates, Phase 0 research, artifacts |
| "help with checklist", "validate requirements", "quality check" | Coach on `/speckit-checklist` — "unit tests for English", domain selection |
| "which checklists", "recommend checklists", "what domains" | Run `/speckit recommend-checklists` — analyze spec to recommend domains with enriched prompts |
| "help with tasks", "generate tasks", "task breakdown" | Coach on `/speckit-tasks` — user-story-first, `[P]` markers, independent testability |
| "help with analyze", "consistency check", "cross-artifact" | Coach on `/speckit-analyze` — severity levels, CRITICAL blocks, coverage gaps |
| "help with implement", "execute tasks", "start building" | Coach on `/speckit-implement` — checklist pre-check, TDD, phase execution |
| "help with constitution", "project principles", "governance" | Coach on `/speckit-constitution` — principle design, versioning, enforcement |
| **Deep-Dive References** | |
| "checklist domains", "what checklists", "which domains" | Guide domain selection from [checklist guide](references/checklist-domains-guide.md) |
| "constitution design", "good principles", "constitution tips" | Guide constitution design from [constitution guide](references/constitution-guide.md) |
| "upgrade speckit", "update templates" | Provide upgrade guidance from [command guide](references/command-guide.md) — see "Upgrade Guidance" |
| **Plugin Usage** | |
| "install codex agents", "subagents missing", "repair codex install", "refresh codex agents" | Route to the SpecKit Pro Codex `install` skill. Explain that `speckit-autopilot` and `speckit-coach` still own skill-local `agents/openai.yaml` metadata sidecars, but real custom agents register from `.codex/agents/*.toml` or `~/.codex/agents/*.toml`, so the install skill copies the bundled `codex-agents/*.toml` templates into place and the user must restart Codex afterward. |
| "run autopilot", "execute workflow", "autonomous" | Guide to `$speckit-autopilot` — prerequisites, workflow file setup, and autonomous execution. See [autopilot guide](references/autopilot-guide.md) |
| "check status", "where am I", "workflow progress", "what's next", "roadmap", "project health" | Guide to `$speckit-status` for technical roadmap progress (completed, ready, blocked specs), or `$speckit-doctor` for project health diagnostics (`$speckit-doctor` requires the doctor extension — install via `specify extension add doctor`) |
| "roadmap map", "home note", "Map of Content", "roadmap-MOC", "navigation", "how is the home note structured", "curated vs generated zone", "two-zone", "can I edit the INDEX", "cap epics" | Explain the roadmap-MOC home note's two-zone structure from [roadmap-MOC guide](references/roadmap-moc-guide.md) — the curated epics zone is hand-authored/editable, the GENERATED INDEX zone is machine-regenerated by `generate-spec-index.sh` and never hand-edited, and the cap-epics-below-~10 guardrail is advisory (warns, never blocks) |
| "fix up this speckit-pro project", "repair existing SpecKit project", "make template edits durable", "template customizations got overwritten", "upgrade-safe templates", "reviewability preset repair" | Run the Project Fixup workflow below. Audit `.specify`, migrate reviewability-related direct core template edits into a project-local preset, verify `specify preset resolve`, preserve host PR templates, and restore core templates only from a reviewed source. |
| "configure autopilot", "settings", "consensus mode" | Guide to `.claude/speckit-pro.local.md` settings (project-relative path, works on both Claude Code and Codex) — consensus mode, auto-commit, gate failure behavior. See [autopilot guide](references/autopilot-guide.md) |
| "how does consensus work", "clarify automation" | Explain the 3-agent consensus protocol — codebase-analyst, spec-context-analyst, domain-researcher. See [autopilot guide](references/autopilot-guide.md) |
| "gap remediation", "checklist automation" | Explain checklist gap remediation loop — consensus agents propose fixes, auto-edit, re-verify. See [autopilot guide](references/autopilot-guide.md) |
| "analyze automation", "finding remediation" | Explain analyze remediation loop — CRITICAL/HIGH findings auto-fixed via consensus. See [autopilot guide](references/autopilot-guide.md) |
| "PR automation", "review loop", "copilot review" | Explain the post-PR review remediation loop — polling, auto-fix, comment resolution. See [autopilot guide](references/autopilot-guide.md) |
| "branching", "worktree", "SPECIFY_FEATURE" | Explain branch detection hierarchy — env var → git branch → specs/ scan. See [autopilot guide](references/autopilot-guide.md) |
| **Presets & Extensions (v0.8.x)** | |
| "preset", "customize templates", "override templates", "methodology" | Explain presets — stackable template overrides, resolution order, commands. See [presets & extensions guide](references/presets-extensions-guide.md) |
| "extension", "add extension", "install extension", "community catalog" | Explain extensions and use the live catalog playbook. See [presets & extensions guide](references/presets-extensions-guide.md) — "Browsing the live catalog" section. |
| "what extensions are available", "search extensions", "find an extension for X", "browse extensions", "list community extensions" | Run **Play 1 — Discovery**: `specify extension search [keyword]` (fallback to `gh api` against `catalog.community.json`, then WebFetch the raw URL). Render results grouped by category. See [presets & extensions guide](references/presets-extensions-guide.md) — "Browsing the live catalog". |
| "tell me about the X extension", "info on X extension", "what does X extension do", "details on X extension" | Run **Play 2 — Deep dive**: `specify extension info <id>`. Fallback: fetch the extension's own `extension.yml` from its repo via `gh api` or WebFetch and read out `provides.commands`, `hooks`, `requires.speckit_version`, `tags`. Cross-reference against `specify --version`. |
| "install X extension", "add the X extension", "remove X extension", "disable an extension", "enable an extension", "configure an extension" | Run **Play 3 — Install / configure / remove**. Always confirm with the user before mutating. Use `specify extension add/remove/enable/disable/set-priority`. **Every install / configure / hook-wiring response MUST end with a two-line closing block, verbatim** — do not paraphrase, do not skip, even if the rest of the response is long: <br>`**No plugin update or restart needed** — the autopilot re-reads `.specify/extensions.yml` at every phase boundary, so any hook you wire here fires on the next autopilot run. No `claude` / `codex` restart, no `/plugin marketplace update`, no session reload.`<br>`**Two config files to know:** `.specify/extensions/<id>/<id>-config.yml` (shared, commit to git) and `.specify/extensions/<id>/<id>-config.local.yml` (personal, gitignored).`<br>If the extension should fire automatically at a phase boundary, register it in `.specify/extensions.yml`. |
| "archive extension", "Archive Sweep", "archive cleanup", "spec graveyard", "remove merged specs", "provenance" | Explain the Racecraft archive extension path: install or vendor `racecraft-lab/spec-kit-archive` from a pinned tag/commit, run Archive Sweep at autopilot startup, exclude the current target spec, keep unsafe checkouts dry-run-only, and clean active `specs/**` only after archive success plus recovery commands. |
| "hook events", "after_implement", "before_specify" | Explain the 8 hook events and how extensions use them. See [presets & extensions guide](references/presets-extensions-guide.md) |
| "template resolution", "which template", "preset resolve" | Explain 4-tier resolution: overrides > presets > extensions > core. See [presets & extensions guide](references/presets-extensions-guide.md) |
| "catalog", "custom catalog", "extension catalog", "preset catalog" | Explain multi-catalog stacks, custom catalogs, env vars. See [presets & extensions guide](references/presets-extensions-guide.md) |
| "doctor", "project diagnostics", "health check" | If the doctor extension is installed, run `$speckit-doctor` for full project diagnostic (structure, agents, features, scripts, extensions, git); install via `specify extension add doctor`. See [presets & extensions guide](references/presets-extensions-guide.md) |
| "upgrade speckit", "update speckit", "new version", "latest version" | Guide full upgrade: backup constitution → upgrade CLI → init --here --force → restore. See [command guide](references/command-guide.md) upgrade section |
| "verify extension", "verify-tasks", "review extension", "cleanup extension" | Explain installed extensions and their commands. See [presets & extensions guide](references/presets-extensions-guide.md) |
| **Troubleshooting & Recovery** | |
| "I'm stuck", "don't know what to do", "what's next" | Diagnose current state and recommend next step from [getting started](references/getting-started.md) — see "Troubleshooting & Recovery" |
| "something went wrong", "this isn't working", "bad output" | Identify the problem phase and guide recovery from [getting started](references/getting-started.md) — see "Troubleshooting & Recovery" |
| "go back", "redo", "start over", "wrong phase" | Guide phase rollback — always safe to return to earlier phases, commit history preserves work |
| "spec is wrong", "plan is bad", "need to change" | Guide mid-workflow correction: update the artifact, then re-run downstream phases |
| "new requirements", "scope changed", "need to add" | Guide incremental requirements — finish current spec or create a new one per [Issue #328](https://github.com/github/spec-kit/issues/328) |
| "update spec after implementation", "spec is outdated" | Guide spec-code sync — update spec.md to reflect what was actually built |
| **Quality Evaluation** | |
| "is my spec good", "evaluate", "review quality" | Walk through quality signals from [getting started](references/getting-started.md) — see "How to Evaluate Quality at Each Gate" |
| "is my plan good", "review my plan" | Check plan quality signals: gates, research, data model, contracts |
| "are my tasks good", "review tasks" | Check task quality: story organization, granularity, traceability, parallelism |
| **Enhancement Commands (speckit-pro plugin)** | |
| "scope this idea", "pre-spec scoping", "interview me on this brief", "walk every branch of the design tree", "produce a Design Concept doc", "before /speckit-specify", "before I write the spec" | Guide to `$grill-me` — relentless one-question-at-a-time interview that produces a Design Concept doc (Goals, Non-goals, Q&A log, Open Questions). Strictly human-in-the-loop. The output enriches `$speckit-scaffold-spec`'s workflow file phase prompts. Use it standalone for raw briefs / transcripts, or rely on `$speckit-scaffold-spec` to invoke it automatically per spec. |
| "write a PRD", "create a product requirements document", "draft a PRD and roadmap", "shape this idea into a PRD", "turn this brief into a PRD", "plan a product", "decompose an idea into a SPEC catalog", "before I write specs" | Guide to `$speckit-prd` — a collaborative, one-question-at-a-time interview that authors a lean PRD **and** the technical roadmap (SPEC catalog) from a raw idea. This is the front door of the chain (PRD → roadmap → scaffold-spec → autopilot). Use it when the PRD does not exist yet; if a PRD already exists and you only need decomposition, use the technical-roadmap path below. |
| "technical roadmap", "decompose feature", "multi-spec", "too large for one spec" | Guide technical roadmap creation — decompose large features into sequential specs. See Enhancement section below. **Tip:** if no PRD exists yet, author it and the roadmap together with `$speckit-prd`. To sharpen an existing PRD before decomposing, run `$grill-me docs/prd.md` first to lock in the scope envelope. |
| "workflow tracking", "track phases", "workflow file" | Guide workflow file creation — per-spec 7-phase tracking. See Enhancement section below |
| "recommend checklists", "which checklists", "what domains to check" | Run spec-driven domain recommendation — analyze spec to suggest enriched checklist prompts. See Enhancement section below |
| "decompose", "create spec directories", "break into specs" | Guide spec decomposition — generate individual spec directories from technical roadmap. See Enhancement section below |
| "setup spec", "create worktree", "prepare for autopilot" | Guide to `$speckit-scaffold-spec` — creates worktree, branch, workflow file |
| "resolve PR", "fix review comments", "address copilot comments" | Guide to `$speckit-resolve-pr` — addresses review comments, fixes code, resolves threads |
| **Team Workflow** | |
| "team", "who reviews", "PR workflow", "collaboration" | Guide team workflow from [getting started](references/getting-started.md) — see "Working with a Team" |

### Enhancement (capabilities beyond official SpecKit)

These are NEW capabilities that the official SpecKit CLI does not provide:

#### Project Fixup — Repair an Existing SpecKit Pro Project

When the developer asks the coach to fix or harden an existing SpecKit Pro
project, operate on the current project root unless they name another path.
This is a repair workflow, not just advice.

**When to use:** Existing `.specify` projects with fragile direct edits to
`.specify/templates/*.md`, missing or stale preset registration, missing PR
template integration, or reviewability gates that should survive Spec Kit
CLI upgrades.

**Workflow:**

1. Confirm you are in the intended repository root and inspect `git status`
   before edits. Do not overwrite unrelated user changes.
2. Ensure the generic speckit-pro reviewability preset exists:
   `scripts/ensure-reviewability-preset.sh "$PWD"`
   This generates `.specify/presets/speckit-pro-reviewability/` from the
   project's current core templates, then adds reviewability budget and PR
   review packet sections.
3. Run the audit helper:
   `scripts/project-fixup.sh audit "$PWD"`
4. If the audit reports reviewability-related direct core template edits that
   are not covered by the generic preset, preserve those project-specific
   customizations in a repo-specific preset id instead of overwriting the
   generic `speckit-pro-reviewability` preset.
5. Verify template resolution:
   `specify preset resolve spec-template`,
   `specify preset resolve plan-template`, and
   `specify preset resolve tasks-template` must point at the preset or an
   intentional project override, not core `.specify/templates/*.md`.
6. Restore affected core `.specify/templates/*.md` only from a reviewed source:
   version control, a known-good Spec Kit re-init/upgrade backup, or an
   official core template. Do not guess at core content.
7. Ensure generated PR bodies preserve the host repository PR template if one
   exists. If absent, recommend adding `.github/pull_request_template.md`.
8. Run the project/unit checks that match the changed files, then report:
   preset path, resolved templates, core-template restore status, PR template
   status, and any manual follow-up.

#### `/speckit technical-roadmap` — Multi-Spec Project Decomposition

When a feature is too large for a single spec, create a **technical roadmap** that decomposes it into discrete, sequential specifications with dependency graphs.

**When to use:** The feature involves multiple tiers (e.g., backend + frontend), multiple independent deliverables, or will take more than one `/speckit-specify` → `/speckit-implement` cycle.

**How to create the technical roadmap:**

1. Copy the [technical roadmap template](templates/technical-roadmap-template.md) to `docs/ai/specs/<feature-name>-technical-roadmap.md`
2. Analyze the feature using the decomposition algorithm below
3. Populate each spec section with scope descriptions detailed enough to drive `/speckit-specify`
4. Review the dependency graph with the developer before proceeding

**Step 1: Analyze the Feature Request**

Before decomposing, understand the full scope by discussing with the developer:

- What is the end-to-end user journey? (entry point → value delivered)
- What are the major system layers involved? (API, database, frontend, external services, AI/ML)
- What are the hard constraints? (existing infrastructure, tech stack decisions, timeline, team size)
- What decisions have already been made vs what needs research?
- Are there existing components to reuse? (branches, libraries, prototypes)

**Step 2: Identify Natural Spec Boundaries**

Look for natural seams where the feature splits into independent deliverables:

| Boundary Signal | How to Split |
|---|---|
| Different system layers (backend API vs frontend UI) | Separate specs per layer |
| Different external integrations (LLM, search, database) | Separate spec per integration |
| Independent user stories that can be delivered alone | One spec per story |
| A component others depend on (shared types, core service) | Foundation spec first |
| A "wire everything together" step | Integration spec last |

**Step 3: Define Dependencies and Execution Order**

For each candidate spec, ask:
- Can this spec be implemented and tested without any other spec being complete?
- If not, which specific specs must complete first, and why?
- Can any specs use mock data to start in parallel with their dependencies?

**Dependency patterns:**
- **Sequential chain:** A → B → C (each spec requires the previous)
- **Fan-out:** A → B, A → C (foundation enables multiple parallel specs)
- **Fan-in:** B → D, C → D (integration spec requires all predecessors)
- **Mock-parallel:** B can start with mock data while A is in progress, but needs A's real output before implementation

**Step 4: Write Rich Scope Descriptions**

Each spec's Scope section must be **detailed enough to serve as the input for `/speckit-specify`**. Compare:

| Too Vague (useless for /specify) | Detailed Enough (drives /specify) |
|---|---|
| "Backend API endpoint" | "FastAPI `POST /chat` endpoint with SSE streaming, Pydantic v2 request/response models, conversation state management (in-memory for MVP)" |
| "Search integration" | "Wrap existing combined-search pipeline (imagery + change detection) as an agent tool using `@tool` decorator, register via `create_sdk_mcp_server()`" |
| "Frontend components" | "Install UI component library for core chat interface, reuse existing domain-specific components from feature branch, apply project theming from design tokens" |

**Step 5: Document Key Decisions**

For each significant technical decision, add a decision block to the relevant spec section:

```markdown
**[Decision Name] Decision ([Date]):** [What was decided and why.]
Alternatives considered: [Brief list of alternatives that were rejected and why.]
```

**Decomposition principles:**
- Each spec should be independently executable through the full SpecKit workflow
- Minimize cross-spec dependencies — prefer sequential over deeply nested
- Backend foundations before frontend integrations
- Mock data for specs that depend on unfinished backend work
- Integration spec last — wire everything together as the final spec
- Each spec gets its own `specs/<number>-<name>/` directory
- Scope descriptions must be detailed enough to directly drive `/speckit-specify`

#### `/speckit workflow` — Per-Spec Phase Tracking

Create workflow tracking files that document the progress of each spec through all 7 SpecKit phases with human review gates.

**When to use:** After creating a technical roadmap or when starting any spec that benefits from phase-by-phase documentation.

**How to create:**

1. Copy the [workflow template](templates/workflow-template.md) to `docs/ai/specs/SPEC-<ID>-workflow.md`
2. Replace placeholders (SPEC_ID, SPEC_NAME, BRANCH_NAME)
3. Update the workflow status table as you complete each phase
4. Document key decisions, artifacts produced, and gate checkpoint results
5. Capture lessons learned after implementation

#### Archive Extension And Archive Sweep

For projects that want to avoid an active `specs/**` graveyard while retaining
provenance, coach the user toward the Racecraft archive extension:

1. Install or vendor `racecraft-lab/spec-kit-archive` from a pinned tag or
   commit, and record the source URL, ref, commit, and manifest hash.
2. Treat the archive command as provenance-first: record PR URL, merge/tree
   reference, CI/Argos URLs, metadata gates, artifact manifests, and recovery
   commands such as `git show <merge-sha>:specs/<feature>/spec.md`.
3. Run Archive Sweep at the start of autopilot before the requested spec's
   Phase 0. The sweep considers previously merged specs only.
4. Always exclude the current target spec. It becomes eligible only in a later
   autopilot run after its PR has merged.
5. Keep dirty worktrees or unsafe branches dry-run-only or stopped. Do not mix
   prior-spec cleanup into an unrelated feature branch.
6. Remove active `specs/**` folders only as an explicit reviewed forward change
   after archive success, merge/tree references, recovery commands, and
   `safeToApplyCleanup=true` are recorded. Never rewrite history and never rely
   on post-merge CI mutating `main`.

#### `/speckit recommend-checklists` — Spec-Driven Domain Recommendations

Analyze the current spec and plan to recommend the most impactful checklist domains, then generate enriched `/speckit-checklist` prompts with spec-specific focus areas.

**When to use:** After `/speckit-plan` completes — before running any `/speckit-checklist` commands. This replaces guesswork about which domains to check.

**How it works:**

1. Read `spec.md` and `plan.md` for the current feature
2. Extract signals (API endpoints → api-contracts, LLM calls → llm-integration, UI components → ux, etc.)
3. Rank candidate domains by risk and coverage gap potential (target: 2-4 domains)
4. For each recommended domain, generate an **enriched prompt** that includes spec-specific focus areas — not just a bare domain name
5. Present recommendations with justification for the developer to review before running

See [Checklist Domains Guide](references/checklist-domains-guide.md) for the full signal extraction algorithm and enriched prompt patterns.

#### `/speckit decompose` — Break Technical Roadmap into Spec Directories

After creating a technical roadmap, generate the individual spec directories:

1. Read the technical roadmap to identify all specs
2. For each spec, create `specs/<number>-<name>/` directory
3. Run `/speckit-specify` for each spec using the technical roadmap's scope description
4. Update the technical roadmap's progress tracking table

### Autonomous Execution

For **autonomous execution** of a complete SpecKit workflow, use the companion skill:

```
$speckit-autopilot path/to/workflow-file.md
```

The autopilot reads a populated workflow file and executes all 7 phases autonomously with programmatic gate validation, multi-agent consensus resolution, and auto-commits. See the [Autopilot Guide](references/autopilot-guide.md) for full documentation.

## The SpecKit Workflow (Quick Reference)

```
constitution → specify → clarify (opt) → plan → checklist (opt) → tasks → analyze (opt) → implement
```

### Phase Gates

| Gate | After | Pass Criteria |
|------|-------|---------------|
| G0 | Prerequisites | Build, typecheck, lint, tests all pass |
| G1 | Specify | No `[NEEDS CLARIFICATION]` markers remain |
| G2 | Clarify | All decisions documented in spec |
| G3 | Plan | Architecture approved, constitution gates pass |
| G4 | Checklist | All `[Gap]` markers addressed |
| G5 | Tasks | Coverage verified, dependencies ordered |
| G6 | Analyze | No CRITICAL issues |
| G7 | Implement | Tests pass, manual verification complete |

### Traceability Markers

| Marker | Purpose |
|--------|---------|
| `[US1]`, `[US2]` | User story reference |
| `[FR-001]` | Functional requirement |
| `[NEEDS CLARIFICATION]` | Flag for Clarify phase |
| `[P]` | Parallel-safe task |
| `[Gap]` | Missing checklist coverage |

### File Layout Convention

```
specs/<number>-<feature-name>/
├── spec.md          # Phase 1: Specify
├── plan.md          # Phase 3: Plan
├── research.md      # Phase 3: Plan (research notes)
├── data-model.md    # Phase 3: Plan (entities/types)
├── quickstart.md    # Phase 3: Plan (dev onboarding)
├── contracts/       # Phase 3: Plan (API contracts)
├── tasks.md         # Phase 5: Tasks
└── checklists/      # Phase 4: Checklist (per domain)
```

### Command Chaining Tips

- **Always start with `/speckit-constitution`** if the project doesn't have one yet
- **Invest in the first prompt** — "Having a very detailed first prompt will produce a much better specification"
- **Commit between phases** — each phase produces artifacts worth preserving
- **Run `/speckit-analyze` before implement** — it catches coverage gaps and constitution violations cheaply
- **Back up constitution.md before upgrading** — `specify init --here --force` overwrites it

## References

- [Getting Started](references/getting-started.md) — First-time setup, walkthrough, troubleshooting, quality evaluation
- [SDD Methodology](references/sdd-methodology.md) — Full philosophy, principles, and patterns
- [Command Guide](references/command-guide.md) — Per-command coaching with gates and pitfalls
- [Constitution Guide](references/constitution-guide.md) — Designing effective project constitutions
- [Checklist Domains Guide](references/checklist-domains-guide.md) — Identifying and creating domain checklists
- [Best Practices](references/best-practices.md) — Lessons learned, anti-patterns, tips
- [Presets & Extensions Guide](references/presets-extensions-guide.md) — Presets, extensions, hooks, catalogs, custom presets
- [Autopilot Guide](references/autopilot-guide.md) — Autonomous execution, consensus protocol, configuration
- [Roadmap-MOC Guide](references/roadmap-moc-guide.md) — The home note's curated-vs-generated two-zone structure and the advisory epic cap
- [PRD Template](templates/prd-template.md) — Lean, universal PRD; author it with `$speckit-prd`
- [Technical Roadmap Template](templates/technical-roadmap-template.md) — Multi-spec project decomposition (SPEC catalog derived from the PRD)
- [Workflow Template](templates/workflow-template.md) — Per-spec 7-phase tracking
