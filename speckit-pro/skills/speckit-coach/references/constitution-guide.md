# Constitution Design Guide

How to create effective project constitutions using `/speckit.constitution`. A constitution establishes the architectural DNA that ensures consistency across all AI-generated implementations.

## What Makes a Good Constitution

### Testable, Not Aspirational

Every principle must be verifiable through specific commands or code review:

| Bad (aspirational) | Good (testable) |
|---|---|
| "Write clean code" | "All Python functions must have type annotations — verified by `pyright --strict`" |
| "Code should be well-tested" | "No implementation code before unit tests pass — TDD Red→Green→Refactor" |
| "Keep things simple" | "Maximum 3 projects initially; additional projects require documented justification" |
| "Use modern practices" | "Use framework features directly rather than wrapping them" |

### The Right Number of Principles

- **5-8 principles** is the sweet spot
- Fewer than 5: too vague, not enough guardrails
- More than 8: contradictions become likely, enforcement becomes impossible
- Each principle should be independent — if two principles often conflict, merge them

### Principle Categories

Good constitutions cover these dimensions:

| Category | Example Principles |
|----------|-------------------|
| **Code Quality** | Type safety, linting rules, line length limits |
| **Architecture** | Library-first, modularity, framework usage |
| **Testing** | TDD, integration-first, contract testing |
| **Styling** | CSS approach, component patterns |
| **State Management** | Approved patterns (Context, hooks, etc.) |
| **Simplicity** | YAGNI, anti-abstraction, complexity justification |

## The 9-Article Pattern

The official SpecKit spec-driven.md describes a constitutional pattern with these articles:

- **Article I**: Library-First — features begin as standalone libraries
- **Article II**: CLI Interface Mandate — text I/O, JSON support for all libraries
- **Article III**: Test-First — NON-NEGOTIABLE TDD
- **Article VII**: Simplicity — maximum 3 projects initially
- **Article VIII**: Anti-Abstraction — use frameworks directly
- **Article IX**: Integration-First Testing — real databases over mocks

You don't need all 9 articles. Choose principles that fit your project. A web API might skip Library-First and CLI Mandate but keep Test-First and Simplicity.

## Semantic Versioning

Constitutions use semantic versioning (MAJOR.MINOR.PATCH):

| Change Type | Version Bump | Example |
|-------------|-------------|---------|
| New principle added | MAJOR | Adding "Accessibility First" principle |
| Existing principle amended | MINOR | Allowing `useChat` hook alongside React Context |
| Clarification or typo fix | PATCH | Clarifying that "type safety" means Pyright strict mode |

Include governance metadata:

```markdown
**Version**: 1.2.0
**Ratified**: 2026-01-15
**Last Amended**: 2026-02-10
```

## Amendment Workflow

When a principle needs updating:

1. **Document the rationale** — why is the change needed?
2. **Assess backward compatibility** — does this break existing specs/plans?
3. **Get maintainer approval** — constitutions are team agreements
4. **Update version** — bump MAJOR/MINOR/PATCH appropriately
5. **Propagate changes** — update dependent templates if needed

## Constitutional Enforcement

### Phase Gates in plan.md

The plan template includes pre-implementation gates that check constitutional compliance:

- **Simplicity Gate**: Using minimal projects? No future-proofing?
- **Anti-Abstraction Gate**: Using framework directly? No unnecessary wrapping?
- **Integration-First Gate**: Contracts defined? Real test environments?

If a gate fails, the developer must either:
- Change the plan to comply, OR
- Document a justified exception in the **Complexity Tracking** table

### Complexity Tracking

When a principle violation is justified, document it:

```markdown
| Principle | Violation | Justification |
|-----------|-----------|---------------|
| Simplicity (≤3 projects) | 4 projects | ML pipeline requires separate project for GPU isolation |
| Anti-Abstraction | Custom ORM wrapper | Database migration requires abstraction layer during transition |
```

This creates accountability — violations are visible and must be defended.

## Anti-Patterns

### Principles That Don't Work

- **Too vague**: "Write good code" — not testable, not enforceable
- **Too many**: 15+ principles — contradictions guaranteed, nobody remembers them all
- **Technology-locked**: "Always use React 18" — prevents migration, dates quickly
- **Aspirational**: "Achieve 100% test coverage" — impractical, leads to bad tests
- **Contradictory**: "Move fast" + "Full test coverage" — which wins?

### Common Constitution Mistakes

1. Writing the constitution after implementation begins (should be first)
2. Not versioning the constitution (changes are invisible)
3. Not including quality gate commands (principles aren't enforced)
4. Making all principles absolute (some need escape hatches via Complexity Tracking)
5. Copying another project's constitution without adapting to your context

## Example: Minimal Effective Constitution

```markdown
# Project Constitution v1.0.0

## Core Principles

### I. Type Safety First
All code must pass strict type checking. Python: `pyright --strict`. TypeScript: `strict: true`.

### II. Test-First Development
No implementation code before tests are written and confirmed failing (TDD Red phase).
Quality gate: `pytest` (Python), `npm test` (TypeScript).

### III. Simplicity
YAGNI — no speculative features. Maximum 3 projects initially.
Additional projects require documented justification in Complexity Tracking.

### IV. Framework-Direct
Use framework features directly. No wrapping layers unless migration is planned.

## Governance
- **Version**: 1.0.0
- **Ratified**: [DATE]
- Amendments require: rationale, team review, version bump
```

This is 4 principles, all testable, with clear governance. Start here and add principles as your project matures.

## Protecting Your Constitution During Upgrades

**Critical:** Running `specify init --here --force` overwrites
`constitution.md` with the default template. Your customized
principles will be lost unless you back up first.

**Best practice:**

```bash
# Before upgrading
cp .specify/memory/constitution.md .specify/memory/constitution-backup.md

# After upgrading
git restore .specify/memory/constitution.md
# or: cp .specify/memory/constitution-backup.md .specify/memory/constitution.md
```

**Why this happens:** The SpecKit upgrade replaces all files in
`.specify/memory/` with fresh templates. The constitution is the
only file that's project-specific — all others are generic.

**Long-term solution:** Commit your constitution to git. Then
`git restore` will always recover it after an upgrade.
