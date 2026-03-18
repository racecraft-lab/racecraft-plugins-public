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

### Phase Gate G1
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

### Phase Gate G2
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

### Phase Gate G3
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

### Phase Gate G4
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

### Phase Gate G5
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

### Phase Gate G6
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

### Phase Gate G7
- [ ] All tasks marked complete in tasks.md
- [ ] Tests pass
- [ ] Manual verification complete
- [ ] Code review done

### What It Produces
- Working code implementing all tasks
- Updated tasks.md with completed task markers

---

## Upgrade Guidance

When upgrading SpecKit (`specify init --here --force --ai copilot`):

1. **Always back up constitution.md first** — `specify init --here --force` overwrites it with the default template
2. **Back up custom templates** — `.specify/templates/` will be overwritten
3. **`specs/` is safe** — never included in upgrade packages, never overwritten
4. **Restore after upgrade**: `git restore .specify/memory/constitution.md`
5. **Use `specify check`** to verify CLI installation
6. **`SPECIFY_FEATURE` env var** for non-git repos: `export SPECIFY_FEATURE="001-my-feature"`
7. **Duplicate slash commands** in IDE agents — manually delete old files and restart IDE
