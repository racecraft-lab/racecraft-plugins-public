## Answer

The server MUST enforce a default maximum page size even when the caller
omits `limit`. This is non-negotiable under the project's constitution:
Article IV ("Bounded Responses") states that "every API response with
collection semantics must be bounded by an explicit maximum, regardless
of whether the caller requested a bound." SPEC-006 (notifications) and
SPEC-007 (repetition) both resolved an identical clarify question by
capping unbounded requests at `DEFAULT_PAGE_SIZE`. SPEC-009 should
follow the same precedent.

Proposed spec edit, to be inserted under "Functional Requirements" in
`specs/009-search-database/spec.md`:

> When `limit` is omitted, the server MUST apply `DEFAULT_PAGE_SIZE` as
> the ceiling. The server MUST also reject any `limit` value greater
> than `MAX_PAGE_SIZE` with a `400 Bad Request` response that includes
> the configured maximum in the error body.

## References

- **Artifact**: `.specify/memory/constitution.md`
  **Section**: Article IV — Bounded Responses
  **Relevance**: Directly mandates that collection endpoints enforce a
  ceiling regardless of caller intent. This is constitutional, not a
  recommendation.

- **Artifact**: `specs/006-notifications/spec.md`
  **Section**: "Clarifications" — Q3 (default page size)
  **Relevance**: Sets the precedent that omitted `limit` falls back to
  `DEFAULT_PAGE_SIZE` rather than being treated as unbounded.

- **Artifact**: `specs/007-repetition/spec.md`
  **Section**: "Clarifications" — Q2 (max page size)
  **Relevance**: Sets the precedent that `MAX_PAGE_SIZE` is the hard
  ceiling and that requests exceeding it return `400 Bad Request` with
  the configured maximum in the error body.

- **Artifact**: `CLAUDE.md`
  **Section**: "API Conventions"
  **Relevance**: Reinforces the constitutional rule with a project-wide
  convention that no list endpoint may return an unbounded result set.

## Confidence

high

**Rationale**: The constitution settles this question directly, and two
prior specs have already resolved the same clarification with the same
answer. There is no ambiguity to resolve — only spec text to add.
