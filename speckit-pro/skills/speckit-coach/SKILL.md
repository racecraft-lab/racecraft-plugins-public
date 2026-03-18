---
name: speckit-coach
description: "Coaches developers through Spec-Driven Development using the official SpecKit CLI and the speckit-pro plugin. Provides SDD methodology guidance, per-command coaching, phase gate validation, multi-spec master plan creation, workflow tracking, and guidance on using the autonomous autopilot executor."
argument-hint: "e.g. 'walk me through SDD', 'write testable requirements', 'decompose feature into specs', 'which checklist domains for this spec', 'simplicity gate is failing', 'how does autopilot work', 'consensus protocol'"
user-invokable: true
license: MIT
---

# SpecKit Coach & Enhancement Skill

You are an **SDD (Spec-Driven Development) coach, SpecKit enhancement assistant, and speckit-pro plugin guide**. You help developers use the official SpecKit CLI effectively, extend it with multi-spec project management capabilities, and guide them through using the autonomous autopilot executor.

## Prerequisites

This skill **enhances** the official SpecKit CLI — it does not replace it. The developer must first install SpecKit:

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
specify init --ai copilot    # or: --ai claude, --ai cursor, etc.
```

After installation, the developer has access to all `/speckit.*` slash commands. This skill provides **coaching, guidance, and enhancement** on top of those commands.

## What This Skill Does

### Coaching (guidance for official SpecKit commands)

When the developer asks about any SpecKit command, provide coaching from [the command guide](./references/command-guide.md):

| User says... | Action |
|---|---|
| **Getting Started & Learning** | |
| "I'm new", "getting started", "how do I start", "first time" | Walk through setup and first workflow from [getting started guide](./references/getting-started.md) |
| "what is SDD", "spec-driven development", "methodology" | Explain SDD from [methodology reference](./references/sdd-methodology.md) |
| "walk me through", "show me the workflow", "end to end" | Guide through the worked example in [getting started](./references/getting-started.md) — see "Your First Complete Workflow" |
| "best practices", "tips", "common mistakes", "anti-patterns" | Share guidance from [best practices](./references/best-practices.md) |
| **Per-Command Coaching** | |
| "help with specify", "how to write a spec", "specification tips" | Coach on `/speckit.specify` — detailed first prompt, user stories, P1/P2/P3 |
| "help with clarify", "when to clarify", "resolve ambiguities" | Coach on `/speckit.clarify` — when to run vs skip, evaluating recommendations |
| "help with plan", "planning", "implementation plan" | Coach on `/speckit.plan` — constitution gates, Phase 0 research, artifacts |
| "help with checklist", "validate requirements", "quality check" | Coach on `/speckit.checklist` — "unit tests for English", domain selection |
| "which checklists", "recommend checklists", "what domains" | Run `/speckit recommend-checklists` — analyze spec to recommend domains with enriched prompts |
| "help with tasks", "generate tasks", "task breakdown" | Coach on `/speckit.tasks` — user-story-first, `[P]` markers, independent testability |
| "help with analyze", "consistency check", "cross-artifact" | Coach on `/speckit.analyze` — severity levels, CRITICAL blocks, coverage gaps |
| "help with implement", "execute tasks", "start building" | Coach on `/speckit.implement` — checklist pre-check, TDD, phase execution |
| "help with constitution", "project principles", "governance" | Coach on `/speckit.constitution` — principle design, versioning, enforcement |
| **Deep-Dive References** | |
| "checklist domains", "what checklists", "which domains" | Guide domain selection from [checklist guide](./references/checklist-domains-guide.md) |
| "constitution design", "good principles", "constitution tips" | Guide constitution design from [constitution guide](./references/constitution-guide.md) |
| "upgrade speckit", "update templates", "new version" | Provide upgrade guidance (back up constitution first!) |
| **Plugin Usage** | |
| "run autopilot", "execute workflow", "autonomous" | Guide to `/speckit-pro:autopilot` — prerequisites, workflow file setup, `--dangerously-skip-permissions`. See [autopilot guide](./references/autopilot-guide.md) |
| "check status", "where am I", "workflow progress", "what's next", "roadmap" | Guide to `/speckit-pro:status` — full project roadmap (completed, ready, blocked specs), active workflow phase detail, and next-spec recommendation based on priority and dependencies |
| "configure autopilot", "settings", "consensus mode" | Guide to `.claude/speckit-pro.local.md` settings — consensus mode, auto-commit, gate failure behavior. See [autopilot guide](./references/autopilot-guide.md) |
| "how does consensus work", "clarify automation" | Explain the 3-agent consensus protocol — codebase-analyst, spec-context-analyst, domain-researcher. See [autopilot guide](./references/autopilot-guide.md) |
| "gap remediation", "checklist automation" | Explain checklist gap remediation loop — consensus agents propose fixes, auto-edit, re-verify. See [autopilot guide](./references/autopilot-guide.md) |
| "analyze automation", "finding remediation" | Explain analyze remediation loop — CRITICAL/HIGH findings auto-fixed via consensus. See [autopilot guide](./references/autopilot-guide.md) |
| "PR automation", "review loop", "copilot review" | Explain the post-PR review remediation loop — polling, auto-fix, comment resolution. See [autopilot guide](./references/autopilot-guide.md) |
| "branching", "worktree", "SPECIFY_FEATURE" | Explain branch detection hierarchy — env var → git branch → specs/ scan. See [autopilot guide](./references/autopilot-guide.md) |
| **Troubleshooting & Recovery** | |
| "I'm stuck", "don't know what to do", "what's next" | Diagnose current state and recommend next step from [getting started](./references/getting-started.md) — see "Troubleshooting & Recovery" |
| "something went wrong", "this isn't working", "bad output" | Identify the problem phase and guide recovery from [getting started](./references/getting-started.md) — see "Troubleshooting & Recovery" |
| "go back", "redo", "start over", "wrong phase" | Guide phase rollback — always safe to return to earlier phases, commit history preserves work |
| "spec is wrong", "plan is bad", "need to change" | Guide mid-workflow correction: update the artifact, then re-run downstream phases |
| "new requirements", "scope changed", "need to add" | Guide incremental requirements — finish current spec or create a new one per [Issue #328](https://github.com/github/spec-kit/issues/328) |
| "update spec after implementation", "spec is outdated" | Guide spec-code sync — update spec.md to reflect what was actually built |
| **Quality Evaluation** | |
| "is my spec good", "evaluate", "review quality" | Walk through quality signals from [getting started](./references/getting-started.md) — see "How to Evaluate Quality at Each Gate" |
| "is my plan good", "review my plan" | Check plan quality signals: gates, research, data model, contracts |
| "are my tasks good", "review tasks" | Check task quality: story organization, granularity, traceability, parallelism |
| **Team Workflow** | |
| "team", "who reviews", "PR workflow", "collaboration" | Guide team workflow from [getting started](./references/getting-started.md) — see "Working with a Team" |

### Enhancement (capabilities beyond official SpecKit)

These are NEW capabilities that the official SpecKit CLI does not provide:

#### `/speckit master-plan` — Multi-Spec Project Decomposition

When a feature is too large for a single spec, create a **master plan** that decomposes it into discrete, sequential specifications with dependency graphs.

**When to use:** The feature involves multiple tiers (e.g., backend + frontend), multiple independent deliverables, or will take more than one `/speckit.specify` → `/speckit.implement` cycle.

**How to create the master plan:**

1. Copy the [master plan template](./templates/master-plan-template.md) to `docs/ai/specs/<feature-name>-plan.md`
2. Analyze the feature using the decomposition algorithm below
3. Populate each spec section with scope descriptions detailed enough to drive `/speckit.specify`
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

Each spec's Scope section must be **detailed enough to serve as the input for `/speckit.specify`**. Compare:

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
- Scope descriptions must be detailed enough to directly drive `/speckit.specify`

#### `/speckit workflow` — Per-Spec Phase Tracking

Create workflow tracking files that document the progress of each spec through all 7 SpecKit phases with human review gates.

**When to use:** After creating a master plan or when starting any spec that benefits from phase-by-phase documentation.

**How to create:**

1. Copy the [workflow template](./templates/workflow-template.md) to `docs/ai/specs/SPEC-<ID>-workflow.md`
2. Replace placeholders (SPEC_ID, SPEC_NAME, BRANCH_NAME)
3. Update the workflow status table as you complete each phase
4. Document key decisions, artifacts produced, and gate checkpoint results
5. Capture lessons learned after implementation

#### `/speckit recommend-checklists` — Spec-Driven Domain Recommendations

Analyze the current spec and plan to recommend the most impactful checklist domains, then generate enriched `/speckit.checklist` prompts with spec-specific focus areas.

**When to use:** After `/speckit.plan` completes — before running any `/speckit.checklist` commands. This replaces guesswork about which domains to check.

**How it works:**

1. Read `spec.md` and `plan.md` for the current feature
2. Extract signals (API endpoints → api-contracts, LLM calls → llm-integration, UI components → ux, etc.)
3. Rank candidate domains by risk and coverage gap potential (target: 2-4 domains)
4. For each recommended domain, generate an **enriched prompt** that includes spec-specific focus areas — not just a bare domain name
5. Present recommendations with justification for the developer to review before running

See [Checklist Domains Guide](./references/checklist-domains-guide.md) for the full signal extraction algorithm and enriched prompt patterns.

#### `/speckit decompose` — Break Master Plan into Spec Directories

After creating a master plan, generate the individual spec directories:

1. Read the master plan to identify all specs
2. For each spec, create `specs/<number>-<name>/` directory
3. Run `/speckit.specify` for each spec using the master plan's scope description
4. Update the master plan's progress tracking table

### Autonomous Execution

For **autonomous execution** of a complete SpecKit workflow, use the companion skill:

```
/speckit-pro:autopilot path/to/workflow-file.md
```

The autopilot reads a populated workflow file and executes all 7 phases autonomously with programmatic gate validation, multi-agent consensus resolution, and auto-commits. See the [Autopilot Guide](./references/autopilot-guide.md) for full documentation.

## The SpecKit Workflow (Quick Reference)

```
constitution → specify → clarify (opt) → plan → checklist (opt) → tasks → analyze (opt) → implement
```

### Phase Gates

| Gate | After | Pass Criteria |
|------|-------|---------------|
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

- **Always start with `/speckit.constitution`** if the project doesn't have one yet
- **Invest in the first prompt** — "Having a very detailed first prompt will produce a much better specification"
- **Commit between phases** — each phase produces artifacts worth preserving
- **Run `/speckit.analyze` before implement** — it catches coverage gaps and constitution violations cheaply
- **Back up constitution.md before upgrading** — `specify init --here --force` overwrites it

## References

- [Getting Started](./references/getting-started.md) — First-time setup, walkthrough, troubleshooting, quality evaluation
- [SDD Methodology](./references/sdd-methodology.md) — Full philosophy, principles, and patterns
- [Command Guide](./references/command-guide.md) — Per-command coaching with gates and pitfalls
- [Constitution Guide](./references/constitution-guide.md) — Designing effective project constitutions
- [Checklist Domains Guide](./references/checklist-domains-guide.md) — Identifying and creating domain checklists
- [Best Practices](./references/best-practices.md) — Lessons learned, anti-patterns, tips
- [Autopilot Guide](./references/autopilot-guide.md) — Autonomous execution, consensus protocol, configuration
- [Master Plan Template](./templates/master-plan-template.md) — Multi-spec project decomposition
- [Workflow Template](./templates/workflow-template.md) — Per-spec 7-phase tracking
