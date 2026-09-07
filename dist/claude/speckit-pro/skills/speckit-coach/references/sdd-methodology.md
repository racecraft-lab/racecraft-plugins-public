# Spec-Driven Development (SDD) Methodology

SDD treats specifications as the durable description of what and why to build;
plans and code express that intent. Keep requirements testable, state
uncertainty explicitly, and preserve traceability as the work moves from a
specification to implementation.

## Workflow and boundaries

The normal flow is `constitution → specify → clarify (as needed) → plan →
checklist (as needed) → tasks → analyze (as needed) → implement`.

- The constitution establishes project-specific, testable governance.
- Specify records user outcomes and acceptance criteria without implementation
  design; clarify resolves ambiguity instead of guessing.
- Plan makes technical decisions and contracts visible; tasks make the work
  dependency-ordered and independently verifiable.
- Analyze tests cross-artifact consistency; implementation follows the accepted
  artifacts and returns evidence to them.

Grill Me is a separate human-in-the-loop scoping interview before a workflow is
written. It is not an autopilot phase or a substitute for in-workflow
clarification.

## Evolving a specification

When understanding changes, update the source artifact first and re-evaluate
its downstream artifacts. A small change may need only a clarified acceptance
criterion; a changed capability boundary can require a new specification,
revised plan, and regenerated tasks. Keep dependencies, non-goals, and
verification evidence explicit so a reviewer can tell what remains true.

For a larger product, split by independently deliverable user outcomes, not by
technical layer. Use real dependency edges only; a contract or mock is useful
only when it makes a separately testable slice possible.

## Further reference

- [Official Spec Kit repository](https://github.com/github/spec-kit)
- [Command guide](./command-guide.md) for phase-specific coaching
- [Slicing heuristics](./slicing-heuristics.md) for roadmap decomposition
