# Getting Started with SpecKit & SDD

A guided walkthrough for developers new to Spec-Driven Development. This covers first-time setup, your first complete workflow, how to evaluate quality at each gate, and what to do when things go wrong.

---

## First-Time Setup

### 1. Install the SpecKit CLI

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

Verify it works:

```bash
specify check
```

### 2. Initialize SpecKit in Your Project

```bash
cd your-project
specify init --ai claude
```

**`specify init` options:**

| Flag | Description |
|------|-------------|
| `--ai <agent>` | Agent type (see table below) |
| `--ai-skills` | Install as agent skills (for Codex, Antigravity) |
| `--ai-commands-dir <path>` | Custom command directory (for `--ai generic`) |
| `--here` | Initialize in current directory (for upgrades) |
| `--force` | Overwrite without confirmation |
| `--no-git` | Skip git initialization |
| `--script sh\|ps` | Script type (bash or PowerShell) |
| `--skip-tls` | Disable SSL/TLS verification |
| `--debug` | Verbose troubleshooting output |
| `--ignore-agent-tools` | Skip agent availability checks |
| `--github-token` | Explicit GitHub credentials |

**Supported agents (25+):**

| Agent | CLI Name | Notes |
|-------|----------|-------|
| Claude Code | `claude` | |
| GitHub Copilot | `copilot` | IDE-based |
| Cursor | `cursor-agent` | IDE-based |
| Gemini CLI | `gemini` | |
| Codex CLI | `codex` | Requires `--ai-skills` |
| Windsurf | `windsurf` | IDE-based |
| Qwen Code | `qwen` | |
| opencode | `opencode` | |
| Junie | `junie` | |
| Kilo Code | `kilocode` | IDE-based |
| Auggie CLI | `auggie` | |
| Roo Code | `roo` | IDE-based |
| CodeBuddy | `codebuddy` | |
| Qoder CLI | `qodercli` | |
| Kiro CLI | `kiro` | Alias: `kiro-cli` |
| Amp | `amp` | |
| SHAI | `shai` | |
| Tabnine CLI | `tabnine` | |
| Antigravity | `agy` | IDE-based, requires `--ai-skills` |
| IBM Bob | `bob` | IDE-based |
| Mistral Vibe | `vibe` | |
| Kimi Code | `kimi` | |
| Trae | `trae` | IDE-based |
| Pi Coding Agent | `pi` | No MCP by default |
| iFlow CLI | `iflow` | |
| Generic | `generic` | Bring-your-own agent support |

This creates:

| Directory/File | Purpose |
|---|---|
| `.specify/templates/` | Templates that guide each SpecKit command |
| `.specify/scripts/bash/` | Helper scripts (prerequisites, branch creation, plan setup) |
| `.specify/memory/constitution.md` | Your project's constitution (starts as template) |
| `.claude/commands/speckit.*.md` | Slash commands for Claude Code (varies by `--ai`) |
| `.specify/init-options.json` | Persisted init options for upgrades |

### 3. Create Your Feature Branch

SpecKit auto-detects your feature from the current Git branch:

```bash
git checkout -b feature/my-new-feature
```

The branch name becomes the feature identifier. All spec artifacts go to `specs/<number>-<feature-name>/`.

### 4. Create Your Constitution (First Time Only)

Before writing any specs, establish your project's principles:

```bash
/speckit.constitution
```

Tell the agent about your project: tech stack, testing philosophy, code style preferences, and architectural constraints. The agent will help you craft testable principles.

**Tip:** Start with 4-5 principles. You can always amend later. See the [Constitution Guide](./constitution-guide.md) for detailed design guidance.

### 5. Customize with Presets (Optional)

Presets override templates to enforce methodology, compliance,
or project-specific patterns:

```bash
specify preset search                          # browse available
specify preset add <preset-name>               # install one
specify preset add --dev ./my-preset           # install local preset
specify preset resolve spec-template           # verify which template wins
```

See the [Presets & Extensions Guide](./presets-extensions-guide.md) for details.

### 6. Add Extensions (Optional)

Extensions add new commands and hooks — code review, verification,
integration with Jira/Azure DevOps, and more:

```bash
specify extension search                       # browse 26+ community extensions
specify extension add verify --from <zip-url>  # install from URL
specify extension list                         # show installed
```

See the [Presets & Extensions Guide](./presets-extensions-guide.md) for the full catalog.

### Upgrading an Existing Project

If you already have SpecKit installed and want the latest version:

```bash
# 1. Upgrade CLI
uv tool install specify-cli --force --from git+https://github.com/github/spec-kit.git

# 2. Back up constitution (will be overwritten)
cp .specify/memory/constitution.md .specify/memory/constitution-backup.md

# 3. Update project files
specify init --here --force --ai claude

# 4. Restore constitution
git restore .specify/memory/constitution.md

# 5. Verify
specify check
```

**Safe:** `specs/` is never modified by upgrades.

### Non-Git Repos

For projects without Git, set the `SPECIFY_FEATURE` environment
variable to tell SpecKit which feature directory to use:

```bash
export SPECIFY_FEATURE="001-my-feature"
```

This replaces the auto-detection from Git branch names.

---

## Your First Complete Workflow

Here's what the full process looks like for a single feature, from idea to working code. Each phase produces artifacts that feed into the next.

### Phase 1: Specify — Define WHAT and WHY

```bash
/speckit.specify

I need a user authentication system. Users should be able to:
- Register with email and password
- Log in and receive a session token
- Reset their password via email
- View and update their profile

Constraints:
- Passwords must meet OWASP strength requirements
- Sessions expire after 24 hours of inactivity
- All auth endpoints must be rate-limited

Out of Scope:
- OAuth/social login (future feature)
- Two-factor authentication (future feature)
- Admin user management
```

**What happens:** The agent generates `spec.md` with user stories, functional requirements (FR-001, FR-002...), acceptance criteria, and a requirements checklist.

**What to look for in the output:**
- Are all your user stories captured?
- Are there `[NEEDS CLARIFICATION]` markers? (If yes, you'll need the Clarify phase)
- Are success criteria measurable? ("User receives token within 200ms" vs "Login is fast")
- Is the Out of Scope section explicit?

**Artifact produced:** `specs/<number>-<feature-name>/spec.md`

### Gate G1: Review the Spec

Before moving on, verify:

- [ ] No `[NEEDS CLARIFICATION]` markers remain unresolved
- [ ] Every user story has acceptance criteria
- [ ] Success criteria are measurable (numbers, not adjectives)
- [ ] Out of Scope is defined
- [ ] You could explain each requirement to a teammate and they'd understand it the same way

**Commit:** `git add specs/ && git commit -m "feat: add auth spec"`

### Phase 2: Clarify (If Needed) — Resolve Ambiguities

Only run this if the spec has `[NEEDS CLARIFICATION]` markers or areas you're unsure about.

```bash
/speckit.clarify Focus on API: session token format, rate limiting thresholds, password reset flow
```

**What happens:** The agent asks up to 5 targeted questions. Your answers are integrated directly into `spec.md`.

**Tip:** 10-20 minutes here saves hours of rework later. Focus each session on one domain (UX, API, security, etc.).

**Commit:** `git add specs/ && git commit -m "feat: clarify auth spec"`

### Phase 3: Plan — Define HOW

```bash
/speckit.plan

Tech Stack:
- Backend: Express.js with TypeScript
- Database: PostgreSQL
- Auth: bcrypt for passwords, JWT for sessions
- Testing: Jest + Supertest
```

**What happens:** The agent generates:

| Artifact | Contains |
|---|---|
| `plan.md` | Technical architecture, execution flow, constitutional gate checks |
| `research.md` | Decision rationales for technical choices |
| `data-model.md` | Database schemas, TypeScript interfaces |
| `contracts/` | API endpoint specifications (OpenAPI or similar) |
| `quickstart.md` | Developer setup instructions |

**What to look for:**
- Do the constitutional gates pass? (Simplicity, Anti-Abstraction, Integration-First)
- Does `research.md` address technical unknowns?
- Are the data models complete and consistent with the spec?
- Do the API contracts match the functional requirements?

### Gate G3: Review the Plan

- [ ] Architecture makes sense for the requirements
- [ ] Constitutional gates pass (or violations are documented with justification)
- [ ] No unresolved technical unknowns in research.md
- [ ] Data model is consistent with spec requirements
- [ ] API contracts cover all endpoints from the spec

**Commit:** `git add specs/ && git commit -m "feat: add auth plan"`

### Phase 4: Checklist — Validate Requirement Quality

Don't guess which domains to check. Analyze what's in your spec:

- Auth spec mentions passwords, tokens, rate limiting → **security** domain
- Auth spec defines API endpoints → **api-contracts** domain
- Auth spec has session management → **state-management** domain

Run enriched prompts for each domain:

```bash
/speckit.checklist security

Focus on user authentication requirements:
- Password strength validation rules (OWASP compliance)
- Session token generation and storage security
- Rate limiting thresholds for auth endpoints
- Password reset token expiration and single-use requirements
- Pay special attention to: secrets management and credential storage
```

```bash
/speckit.checklist api-contracts

Focus on auth endpoint requirements:
- Request/response schemas for register, login, reset, profile
- Error response consistency across all auth endpoints
- Rate limit headers and 429 response format
- Pay special attention to: token refresh flow and session expiration behavior
```

**What happens:** Each run creates a checklist file in `checklists/`. Items marked `[Gap]` identify missing requirements.

**What to do with gaps:** Update `spec.md` or `plan.md` to address each `[Gap]`, then re-run the checklist to verify.

**Commit:** `git add specs/ && git commit -m "feat: add auth checklists"`

### Phase 5: Tasks — Break Into Implementable Chunks

```bash
/speckit.tasks

Task structure:
- Small, testable chunks (1-2 hours each)
- Organized by user story, not by technical layer
- Mark parallel-safe tasks with [P]
- Foundation phase first, then one phase per user story
```

**What happens:** The agent generates `tasks.md` with dependency-ordered tasks like:

```markdown
## Phase 1: Foundation
- [ ] [T001] Create User model and migration `src/models/user.ts`
- [ ] [T002] Create auth middleware `src/middleware/auth.ts`

## Phase 2: [US1] Registration (P1)
- [ ] [T003] [P] Create register endpoint `src/routes/auth.ts`
- [ ] [T004] [P] Create password validation `src/utils/password.ts`
- [ ] [T005] Create registration tests `tests/auth/register.test.ts`
```

**What to look for:**
- Does every FR have at least one task?
- Are tasks small enough (2-3 files max)?
- Is the dependency order correct?
- Are parallel opportunities marked with `[P]`?

**Commit:** `git add specs/ && git commit -m "feat: add auth tasks"`

### Phase 6: Analyze — Catch Issues Before Coding

```bash
/speckit.analyze

Focus on:
1. Constitution alignment
2. Coverage gaps — all FRs and user stories have tasks
3. Consistency between task file paths and project structure
```

**What happens:** A read-only report with findings sorted by severity:

| Severity | What It Means | What To Do |
|---|---|---|
| CRITICAL | Blocks implementation, violates constitution | **Must fix** — update spec/plan/tasks |
| HIGH | Significant gap | Should fix |
| MEDIUM | Improvement opportunity | Review and decide |
| LOW | Minor inconsistency | Note for later |

**Rule:** Fix all CRITICAL issues before proceeding. Re-run analyze to verify.

**Commit:** `git add specs/ && git commit -m "feat: resolve auth analysis findings"`

### Phase 7: Implement — Write the Code

```bash
/speckit.implement
```

**What happens:** The agent executes tasks phase-by-phase, following TDD:

1. **Red:** Write failing test
2. **Green:** Implement minimum code to pass
3. **Refactor:** Clean up while tests pass

Tasks are marked `[X]` in `tasks.md` as they complete.

**Tip:** Commit after each phase completes. Don't try to implement everything at once.

### Gate G7: Final Review

- [ ] All tasks marked complete in tasks.md
- [ ] All tests pass
- [ ] Linting passes
- [ ] Build succeeds
- [ ] Manual verification of key user flows
- [ ] PR created and reviewed

---

## How to Evaluate Quality at Each Gate

### Is My Spec Good?

| Quality Signal | Good | Bad |
|---|---|---|
| **User stories** | "As a user, I can reset my password via a time-limited email link" | "Password reset feature" |
| **Requirements** | "Session tokens expire after 24h of inactivity" | "Sessions should timeout" |
| **Acceptance criteria** | "Given an expired token, when user makes a request, then return 401 with `token_expired` error code" | "Handle expired tokens" |
| **Out of scope** | "OAuth/social login (planned for Q3)" | No out-of-scope section |
| **Ambiguity markers** | `[NEEDS CLARIFICATION: Should failed login attempts lock the account?]` | Assumes account locking without asking |

### Is My Plan Good?

| Quality Signal | Good | Bad |
|---|---|---|
| **Constitutional gates** | All pass, or violations documented with justification | Gates not mentioned |
| **Research** | "Chose JWT over opaque tokens because: stateless, standard libraries, and session revocation handled via allowlist" | No research.md |
| **Data model** | All entities typed, relationships defined, constraints specified | Vague "User table" |
| **Contracts** | Full request/response schemas with error cases | Just endpoint paths |
| **Complexity tracking** | Empty (simple) or justified violations | Many unjustified violations |

### Are My Tasks Good?

| Quality Signal | Good | Bad |
|---|---|---|
| **Organization** | By user story (US1 tasks, US2 tasks...) | By tech layer (all models, all routes...) |
| **Granularity** | Each task touches 1-3 files, takes 1-2 hours | Tasks that touch 10 files |
| **Traceability** | `[T003] [US1] [FR-001]` — traces to story and requirement | No FR references |
| **Dependencies** | Foundation → Stories → Polish, clear ordering | No dependency structure |
| **Parallelism** | `[P]` markers on independent tasks | Everything sequential |

### Are My Checklists Good?

| Quality Signal | Good | Bad |
|---|---|---|
| **Tests requirements, not implementation** | "Are rate limiting thresholds specified per endpoint?" | "Verify rate limiting works" |
| **Traceability** | `[Spec §4.1]` or `[Gap]` markers on 80%+ items | No spec references |
| **Actionable gaps** | `[Gap]` items lead to spec/plan updates | Gaps ignored |
| **Domain-specific** | Enriched prompts with spec-specific focus areas | Bare `/speckit.checklist security` |

---

## Troubleshooting & Recovery

### "My spec is too vague and I'm already at the plan phase"

**Go back.** SpecKit is iterative — you can always return to an earlier phase.

1. Identify which requirements are vague (check for unmeasurable criteria, missing acceptance scenarios)
2. Run `/speckit.clarify` focused on the vague areas
3. Update `spec.md` with the clarifications
4. Re-run `/speckit.plan` — the plan will be better with a better spec

**Key insight:** A bad spec cascades into a bad plan, bad tasks, and bad code. It's always cheaper to fix the spec than to fix the implementation.

### "The plan fails constitutional gates"

This means your proposed architecture violates project principles. You have two options:

1. **Change the plan** to comply with the constitution — simplify, remove abstractions, use framework features directly
2. **Document a justified exception** in the Complexity Tracking table — this is valid when the violation is genuinely necessary

```markdown
| Principle | Violation | Justification |
|-----------|-----------|---------------|
| Simplicity (≤3 projects) | 4 projects | Auth service requires isolated secrets management |
```

Never silently violate the constitution. The gates exist to prevent architectural drift.

### "Analyze found CRITICAL issues"

CRITICAL means "this will break implementation." Common causes and fixes:

| CRITICAL Issue | Typical Cause | Fix |
|---|---|---|
| Unmapped requirements | FR has no task | Add tasks for the missing FR in tasks.md |
| Constitution violation | Task contradicts a principle | Restructure the task or document exception |
| Inconsistent file paths | Task references files that conflict with plan | Align task paths with plan's project structure |
| Missing dependencies | Task A needs Task B but B isn't listed first | Reorder tasks or add dependency markers |

After fixing: **re-run `/speckit.analyze`** to verify the fixes resolved the issues.

### "Implementation diverges from the plan"

This is normal — implementation always reveals things the plan didn't anticipate. The question is how far the divergence goes:

| Divergence Level | Action |
|---|---|
| **Minor** (different variable names, slightly different API) | Note it but keep going. Update spec after implementation. |
| **Moderate** (new endpoint needed, changed data model) | Update `plan.md` and `data-model.md` during implementation. |
| **Major** (fundamental architecture change) | Stop. Update `spec.md` and `plan.md`. Re-run `/speckit.tasks` and `/speckit.analyze`. |

**After implementation completes**, always update specs to match what was actually built. Specs are living documents — they should reflect reality, not just the original plan.

### "New requirements emerged mid-implementation"

Don't shoehorn them into the current spec. Instead:

1. **Finish the current spec's implementation** if possible
2. **Create a new spec** for the new requirements: run `/speckit.specify` on a new branch or append to the current feature
3. The new spec is contextually informed by the existing spec and constitution
4. If the new requirements fundamentally change the current spec, stop and re-plan

From [SpecKit Issue #328](https://github.com/github/spec-kit/issues/328): "Use `/speckit.specify` on a feature branch for the new requirements. Merge spec branches to integrate with existing work."

### "I need to redo a phase"

You can always go back. The typical recovery paths:

| Current Phase | Go Back To | When |
|---|---|---|
| Plan | Specify or Clarify | Spec was too vague for a good plan |
| Checklist | Plan or Specify | Major gaps found that require architectural changes |
| Tasks | Plan | Task structure doesn't make sense with the plan |
| Analyze | Tasks | Coverage gaps require new tasks |
| Implement | Tasks or Plan | Implementation reveals plan was wrong |

**Tip:** This is why you commit after each phase — you can always `git diff` to see what changed and `git restore` to go back to a known-good state.

### "I'm stuck and don't know what to do next"

Check where you are in the workflow:

```
constitution → specify → clarify (opt) → plan → checklist (opt) → tasks → analyze (opt) → implement
```

1. **What artifacts exist?** Check `specs/<feature>/` for spec.md, plan.md, tasks.md
2. **What's the last completed gate?** Look at git history for phase commits
3. **What's blocking you?**
   - No spec yet → Run `/speckit.specify` with a detailed prompt
   - Spec has ambiguities → Run `/speckit.clarify`
   - No plan yet → Run `/speckit.plan` with your tech stack
   - Plan looks wrong → Fix the spec first, then re-plan
   - Tasks don't make sense → Re-run `/speckit.tasks`
   - Not sure if tasks are complete → Run `/speckit.analyze`
   - Ready to code → Run `/speckit.implement`

---

## Working with a Team

### Who Reviews What

| Gate | Reviewer | What They Check |
|---|---|---|
| G1 (Specify) | Product owner / tech lead | User stories match intent, requirements are complete |
| G2 (Clarify) | Same as G1 | Decisions are sound, no remaining ambiguities |
| G3 (Plan) | Tech lead / architect | Architecture is sound, gates pass, no over-engineering |
| G4 (Checklist) | Domain expert | Gaps are genuine, coverage is adequate |
| G5 (Tasks) | Implementing developer | Tasks are doable, dependencies are correct |
| G6 (Analyze) | Tech lead | CRITICAL issues are resolved |
| G7 (Implement) | Code reviewer | Code matches spec, tests pass, quality standards met |

### PR Workflow with Specs

Include spec artifacts in your PR:

```
PR: Add user authentication

Files:
  specs/001-auth/spec.md        ← What and why
  specs/001-auth/plan.md        ← How
  specs/001-auth/tasks.md       ← Implementation plan
  specs/001-auth/checklists/    ← Quality validation
  src/routes/auth.ts            ← Implementation
  tests/auth/                   ← Tests
```

Reviewers can read the spec to understand intent, the plan to understand architecture, and the code to verify correctness.

### Spec-Code Drift

After implementation, specs and code naturally diverge as bugs are fixed and requirements evolve. Manage this by:

1. **Updating specs after implementation** — fold code changes back into spec.md
2. **Periodic rollup** — for long-running features, consolidate multiple specs into a current-state snapshot
3. **Treating specs as living documents** — they reflect the system as it IS, not just as it was planned

---

## Quick Reference Card

```
INSTALL:    uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
INIT:       specify init --ai claude     # 25+ agents supported
UPGRADE:    specify init --here --force --ai claude
CHECK:      specify check
DOCTOR:     /speckit.doctor         # project health diagnostics
PRESETS:    specify preset search         # browse presets
EXTENSIONS: specify extension search      # browse extensions
BRANCH:     git checkout -b feature/my-feature

WORKFLOW:   constitution → specify → clarify → plan → checklist → tasks → analyze → implement
REQUIRED:   constitution, specify, plan, tasks, implement
OPTIONAL:   clarify, checklist, analyze (but always recommended)

COMMIT AFTER EACH PHASE.

ARTIFACTS:
  .specify/memory/constitution.md     Project principles
  specs/<feature>/spec.md             What and why
  specs/<feature>/plan.md             How (architecture)
  specs/<feature>/research.md         Decision rationales
  specs/<feature>/data-model.md       Schemas and types
  specs/<feature>/contracts/          API specifications
  specs/<feature>/tasks.md            Implementation tasks
  specs/<feature>/checklists/         Quality validation

MARKERS:
  [US1]                 User story reference
  [FR-001]              Functional requirement
  [NEEDS CLARIFICATION] Ambiguity — address in Clarify
  [P]                   Parallel-safe task
  [Gap]                 Missing requirement — address before Tasks

GATES:
  G0 (Prereqs)    Build, typecheck, lint, tests pass
  G1 (Specify)    No [NEEDS CLARIFICATION] markers
  G2 (Clarify)    All decisions documented
  G3 (Plan)       Architecture approved, gates pass
  G4 (Checklist)  All [Gap] markers resolved
  G5 (Tasks)      Coverage verified
  G6 (Analyze)    No CRITICAL issues
  G7 (Implement)  Tests pass, manual verification done
```
