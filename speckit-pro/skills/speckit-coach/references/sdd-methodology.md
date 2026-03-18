# Spec-Driven Development (SDD) Methodology

This reference covers the SDD methodology as defined by the official [SpecKit](https://speckit.org) project and the [spec-driven.md](https://github.com/github/spec-kit/blob/main/spec-driven.md) methodology document.

## The Core Idea

SDD inverts the traditional relationship between specifications and code:

- **Traditional**: Code is truth; specifications are scaffolding discarded once coding begins.
- **SDD**: Specifications are the primary artifact; code is their expression in a particular language and framework.

"Maintaining software means evolving specifications; debugging means fixing specs and plans that generate incorrect code."

Specifications are "version control for your thinking" — capturing the "why" behind choices in formats that evolve with your project.

## Why SDD Matters Now

Three converging trends make SDD practical:

1. **AI Capability**: Natural language specifications now reliably generate working code. AI amplifies developer effectiveness and enables easy exploration and start-overs.

2. **Complexity Growth**: Modern systems integrate dozens of services and frameworks. SDD provides systematic alignment through specification-driven generation.

3. **Change Velocity**: Requirements change rapidly. SDD transforms pivots from disruptions into systematic regenerations — change a requirement in the spec, and affected plans update accordingly.

"If you don't decide what you're building and why you're building it ahead of time, the codebase becomes the de-facto specification."

## The 6 Core Principles

1. **Specifications as Lingua Franca** — Specifications are the primary artifact. Code expresses them in particular languages and frameworks. Teams align on specifications, not implementation details.

2. **Executable Specifications** — Must be precise, complete, and unambiguous enough to generate working systems. Not aspirational documents — working blueprints.

3. **Continuous Refinement** — Consistency validation happens ongoing, not as one-time gates. Each phase refines the artifacts from previous phases.

4. **Research-Driven Context** — Agents gather technical context throughout: library compatibility, performance benchmarks, security implications, organizational constraints.

5. **Bidirectional Feedback** — Production reality informs specification evolution. Performance bottlenecks become non-functional requirements. Security vulnerabilities affect all future generations.

6. **Branching for Exploration** — Generate multiple implementation approaches from the same specification to explore different optimization targets (e.g., Rust vs. Go implementations).

## The Two-Phase Workflow

### Phase 1: Foundation

| Step | Command | Focus |
|------|---------|-------|
| Constitution | `/speckit.constitution` | Establish immutable project principles |
| Specification | `/speckit.specify` | Define WHAT and WHY (user stories, requirements) |
| Clarification | `/speckit.clarify` | Resolve ambiguities through structured questioning |

### Phase 2: Implementation

| Step | Command | Focus |
|------|---------|-------|
| Planning | `/speckit.plan` | Define HOW (tech stack, architecture, contracts) |
| Validation | `/speckit.checklist` | Validate requirement quality across domains |
| Tasks | `/speckit.tasks` | Break plan into atomic, ordered implementation chunks |
| Analysis | `/speckit.analyze` | Cross-artifact consistency check |
| Implementation | `/speckit.implement` | Execute tasks with TDD approach |

## The 7 Template Quality Mechanisms

SpecKit templates constrain LLM behavior toward higher-quality output:

### 1. Preventing Premature Implementation Details
Templates explicitly instruct: "Focus on WHAT users need and WHY; avoid HOW to implement." No tech stack, APIs, or code structure in specs. This forces proper abstraction — the LLM stays focused on "users need real-time updates" rather than jumping to specific frameworks.

### 2. Forcing Explicit Uncertainty
Both templates mandate `[NEEDS CLARIFICATION: specific question]` markers. The LLM cannot guess — if the prompt doesn't specify an auth method, it must mark the ambiguity explicitly rather than making assumptions.

### 3. Structured Checklists
Templates include comprehensive checklists acting as "unit tests for specifications" — verifying completeness, measurability, and testability of requirements before any code is generated.

### 4. Constitutional Compliance Through Gates
The implementation plan template enforces architectural principles via phase gates:
- **Simplicity Gate**: Using minimal projects? No future-proofing?
- **Anti-Abstraction Gate**: Using framework directly? No unnecessary wrapping?
- **Integration-First Gate**: Contracts defined? Real test environments?

Gates force explicit justification for any complexity in a "Complexity Tracking" section.

### 5. Hierarchical Detail Management
"This implementation plan should remain high-level and readable. Any code samples, detailed algorithms, or extensive technical specifications must be placed in appropriate supporting files." Prevents specs from becoming unreadable code dumps.

### 6. Test-First Thinking
Templates enforce file creation order: (1) Create `contracts/` with API specs, (2) Create test files, (3) Create source files to make tests pass. Ensures testability is designed in, not bolted on.

### 7. Preventing Speculative Features
"No speculative or 'might need' features; all phases have clear prerequisites and deliverables." Every feature must trace to a concrete user story with clear acceptance criteria.

**Compound Effect**: These constraints combine to produce specifications that are complete (checklists), unambiguous (forced clarification), testable (test-first thinking), maintainable (proper abstraction), and implementable (clear phases with deliverables).

## The Constitutional Foundation

The constitution (`memory/constitution.md`) establishes architectural DNA ensuring consistency across all generated implementations.

### The 9-Article Pattern (SpecKit Default)

The official SpecKit spec-driven.md describes these constitutional articles:

- **Article I: Library-First** — Every feature begins as a standalone library. No feature is implemented directly in application code without first being abstracted into a reusable component.

- **Article II: CLI Interface Mandate** — Every library exposes functionality through a command-line interface with text I/O and JSON support. This enforces observability and testability.

- **Article III: Test-First Imperative** — "This is NON-NEGOTIABLE: All implementation MUST follow strict TDD. No implementation code shall be written before: (1) Unit tests are written, (2) Tests are validated and approved, (3) Tests are confirmed to FAIL (Red phase)."

- **Articles VII & VIII: Simplicity and Anti-Abstraction** — Maximum 3 projects initially (justify additions). Use framework features directly rather than wrapping them. Every abstraction layer requires explicit justification.

- **Article IX: Integration-First Testing** — Prefer real databases over mocks, actual service instances over stubs. Contract tests mandatory before implementation.

### Constitutional Enforcement

The plan template operationalizes articles through **Pre-Implementation Gates**: Simplicity Gate, Anti-Abstraction Gate, Integration-First Gate. The LLM cannot proceed without passing gates or documenting justified exceptions in the Complexity Tracking table.

### Constitutional Evolution

Amendments require: explicit documentation of change rationale, maintainer review and approval, and backwards compatibility assessment. The constitution uses semantic versioning (MAJOR.MINOR.PATCH).

## Evolving Specs Over Time

From SpecKit community discussions, four patterns have emerged for managing spec evolution:

1. **Multiple Specs + Periodic Rollup** — Create new specs per feature/change. Periodically consolidate into a snapshot reflecting current system state. Balances history with readability.

2. **Master/Consolidated Spec Model** — Maintain a single source-of-truth spec. After each feature completes, update the master. Provides humans a single readable reference.

3. **Target-State Approach** — Treat specs as desired end-state. Systems diff current vs. target to generate plans. More sophisticated but demands enhanced tooling.

4. **Modular/Capability-Based Structure** — For larger systems, split specs by domain or capability. Use a coordinating "master spec" binding modules together.

**Critical insight**: Specifications and code naturally diverge. The workflow should include explicit loops to fold code changes back into specs. Close feedback loops between implementation and specification throughout development.

## Key Takeaways for Developers

1. **Specs are executable** — They generate implementation plans and code, not just document intent
2. **Templates constrain LLMs productively** — Structure forces better quality than unconstrained generation
3. **Constitution provides stability** — Immutable principles ensure consistency across time and AI models
4. **Continuous feedback loops** — Production reality continuously refines specifications
5. **Test-first is mandatory** — No code before tests define behavior
6. **Simplicity is enforced** — Every abstraction requires explicit justification
7. **Living documents** — Update specs as understanding evolves, not as static artifacts

## Further Reading

- [speckit.org](https://speckit.org) — Official SpecKit homepage
- [github.com/github/spec-kit](https://github.com/github/spec-kit) — Source repository (MIT license)
- [spec-driven.md](https://github.com/github/spec-kit/blob/main/spec-driven.md) — Full methodology document
- [Microsoft Developer Blog: SDD with Spec Kit](https://developer.microsoft.com/blog/spec-driven-development-spec-kit) — Tutorial and overview
