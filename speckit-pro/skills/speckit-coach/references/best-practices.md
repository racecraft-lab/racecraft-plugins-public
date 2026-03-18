# SpecKit Best Practices

Lessons learned from real-world multi-spec projects, official SpecKit guidance, and community discussions. All examples are generic and project-agnostic.

## Getting Started Right

### Invest in the First Prompt

"Having a very detailed first prompt will produce a much better specification." — [Microsoft Developer Blog](https://developer.microsoft.com/blog/spec-driven-development-spec-kit)

Before running `/speckit.specify`, spend 5-10 minutes thinking through:
- What problem does this solve and for whom?
- What are the key user stories?
- What is explicitly OUT of scope?
- What constraints exist (performance, accessibility, compatibility)?

A vague prompt produces a vague spec, which cascades quality issues through all downstream commands.

### Constitution First

Run `/speckit.constitution` before any `/speckit.specify` calls. Without a constitution:
- AI agents have no guardrails for generated code
- Plan phase has no gates to validate against
- Each spec may adopt different architectural patterns
- There's no mechanism to enforce consistency

### Living Documents

"Specs become living documents that evolve alongside your code, not dusty artifacts that you write once and forget."

Update specs when:
- Implementation reveals incorrect assumptions
- Production metrics change requirements
- New user feedback contradicts original stories
- External dependencies change capabilities

## Early Ambiguity Resolution

The Clarify phase is cheap. Rework is expensive.

- "10-20 minutes in Clarify saves hours of rework later"
- Protocol mismatches, API incompatibilities, and design assumptions caught during Clarify cost keystrokes to fix
- The same issues caught during implementation cost entire sprints

### When to Run Clarify

| Scenario | Action |
|----------|--------|
| Spec has `[NEEDS CLARIFICATION]` markers | Run `/speckit.clarify` |
| Multiple valid interpretations of a requirement | Run `/speckit.clarify` |
| You're unsure about acceptance criteria | Run `/speckit.clarify` |
| Spec has 0 markers and all requirements are clear | Skip — go to `/speckit.plan` |
| Trivial feature with obvious requirements | Skip |

## Constitution as Guardrail

### Pre-Plan Gates

The plan template includes three constitutional gates:

1. **Simplicity Gate**: Using minimal projects? No future-proofing? No speculative features?
2. **Anti-Abstraction Gate**: Using framework features directly? No unnecessary wrapping?
3. **Integration-First Gate**: Contracts defined? Real test environments?

If a gate fails, either change the plan or document a justified exception in the Complexity Tracking table.

### Complexity Tracking

When you need to violate a principle, don't just do it — document it:

```markdown
| Principle | Violation | Justification |
|-----------|-----------|---------------|
| Simplicity | 4 projects | GPU isolation requires separate project |
```

This creates accountability and helps future developers understand why decisions were made.

## User Story Organization

### By Story, Not By Layer

Tasks should be organized by **user story** (P1, P2, P3), not by **technical layer** (all backend, then all frontend).

| Bad (by layer) | Good (by story) |
|---|---|
| Phase 1: All backend models | Phase 1: Setup (shared infrastructure) |
| Phase 2: All API endpoints | Phase 2: Foundational (blocks everything) |
| Phase 3: All frontend components | Phase 3: [US1] User searches imagery (P1) |
| Phase 4: All tests | Phase 4: [US2] User views results on map (P1) |

### Why Story-First Matters

- Each story phase is **independently testable** — you can demo and validate incrementally
- Each story is a **standalone MVP slice** — delivers value on its own
- Enables **parallel work** — different developers can work on different stories
- Better **risk management** — P1 stories complete before P2/P3

### The Foundational Phase

The foundational phase (Phase 2) is special:
- It blocks ALL user stories — nothing can start until it completes
- Contains critical shared infrastructure (types, base components, configuration)
- Keep it as small as possible to unblock story work quickly

## Incremental Commits

### Commit Between Phases

Every SpecKit phase produces artifacts worth preserving:
- After `/speckit.specify` → commit spec.md
- After `/speckit.clarify` → commit updated spec.md
- After `/speckit.plan` → commit plan.md, research.md, data-model.md, contracts/
- After `/speckit.tasks` → commit tasks.md
- After each implementation phase → commit working code

### Why This Matters

- **Rollback capability**: If implementation goes wrong, you can return to a known-good state
- **Review points**: Teammates can review artifacts before implementation starts
- **Git branch detection**: SpecKit auto-detects your feature from the current branch

## Cross-Artifact Traceability

### The Traceability Chain

Every task should trace back to a requirement:

```
[US1] User story → [FR-001] Functional requirement → [T003] Implementation task
```

This chain catches:
- **Orphaned requirements**: FRs with no tasks → coverage gap
- **Orphaned tasks**: Tasks with no FR → potential scope creep
- **Missing stories**: Requirements not covered by any user story

### Parallel Markers

`[P]` markers identify tasks safe for parallel execution:

```markdown
- [ ] [T005] [P] [US1] Create search input component `src/components/SearchInput.tsx`
- [ ] [T006] [P] [US1] Create results grid component `src/components/ResultsGrid.tsx`
```

Tasks without `[P]` must be executed sequentially.

## When to Skip Optional Phases

| Phase | Skip When | Always Run When |
|-------|-----------|-----------------|
| Clarify | Zero `[NEEDS CLARIFICATION]` markers, trivial feature | Multiple ambiguities, complex domain |
| Checklist | Trivial feature, well-understood domain | New domain, multiple stakeholders, compliance requirements |
| Analyze | **Never skip** | Always — it catches coverage gaps cheaply |

**Always run `/speckit.analyze` before `/speckit.implement`**. It's the cheapest quality gate in the workflow.

## Evolving Specs Over Time

From [community discussions](https://github.com/github/spec-kit/discussions/152):

### Specs and Code Naturally Diverge

Implementation rarely matches the original spec exactly. Follow-up changes, bug fixes, and production feedback accumulate. Close the feedback loop by updating specs to reflect reality.

### Patterns for Spec Evolution

1. **Multiple Specs + Periodic Rollup**: Create new specs per feature. Periodically consolidate into a snapshot reflecting current state.

2. **Modular/Capability-Based Structure**: For larger systems, split specs by domain or capability rather than creating monolithic specs.

3. **Anti-pattern**: Treating feature-specific specs as permanent project artifacts. They should evolve or be consolidated.

### Incremental Requirements

From [Issue #328](https://github.com/github/spec-kit/issues/328):

When new requirements emerge after planning:
- Use `/speckit.specify` on a feature branch for the new requirements
- Merge spec branches to integrate with existing work
- New specs are contextually informed by previous specs and the constitution

## Multi-Variant Implementations

From the [Microsoft Developer Blog](https://developer.microsoft.com/blog/spec-driven-development-spec-kit):

Since specs are decoupled from code, you can request AI agents to generate competing implementations from the same spec:
- Different languages (Rust vs. Go for performance comparison)
- Different frameworks (Express vs. Fastify for Node.js)
- Different design approaches (monolith vs. microservices)

This enables rapid exploration without rewriting requirements.

## Anti-Patterns

| Anti-Pattern | Why It's Bad | Fix |
|---|---|---|
| Implementing before planning | Misaligned assumptions waste sprints | Always run constitution → specify → plan first |
| Skipping constitution | No guardrails for AI-generated code | Run `/speckit.constitution` before first spec |
| Implementation details in specs | Premature technology lock-in | Focus on WHAT/WHY, not HOW |
| Ignoring CRITICAL analyze findings | Broken implementation, missed requirements | Fix all CRITICAL issues before `/speckit.implement` |
| Too vague initial prompt | Cascading quality issues through all phases | Invest 5-10 minutes in a detailed first prompt |
| Not committing between phases | No rollback capability | Commit after each phase |
| Spec-code drift | Specs become outdated documentation | Update specs after implementation changes |
| Organizing tasks by tech layer | Non-independent delivery, no incremental value | Organize by user story with priority |
| Giant foundational phase | Blocks all stories for too long | Minimize foundation; move specifics to story phases |
