# Constitution Design Guide

Use this reference to help a project define testable governance. The current
constitution at `.specify/memory/constitution.md` is the authority; templates
and commands resolve it at runtime.

## Write enforceable principles

Each principle should name an observable rule and how it is reviewed. Prefer
"all public API changes have contract tests" over "write high-quality code".
Keep the set small enough to apply consistently, and record a justified
exception in the plan rather than silently weakening a principle.

Useful dimensions include code quality, architecture, testing, security,
accessibility, and simplicity. Choose the dimensions that govern this project;
there is no mandatory article catalog.

## Amendments and versions

Record the rationale, assess existing artifacts, obtain maintainer approval,
and update the version with the amendment.

| Change | Version bump |
|---|---|
| Backward-incompatible governance, or removal/redefinition of a principle | MAJOR |
| A new principle or section, or materially expanded guidance | MINOR |
| Clarification or non-semantic refinement | PATCH |

This follows the current official Spec Kit constitution template. Do not copy a
constitution into plan or command templates: `plan`, `tasks`, and `analyze`
read the live constitution when they run.

## Use it in a workflow

Before planning, read the live constitution and identify the principles that
shape the design. A plan that needs an exception should state the principle,
the deviation, and its justification. On review, resolve violations by changing
the artifact or recording a justified exception rather than diluting the rule.

## Lifecycle boundary

For an installation upgrade, route to the maintained upgrade skill for the
active host. Treat the constitution as project-owned content and do not copy its
prose into command or plan templates by hand.

## Further reference

- [Official Spec Kit constitution command](https://github.com/github/spec-kit/blob/main/templates/commands/constitution.md)
