## Clarify Question

**Spec:** SPEC-009 (search and database access)

**Question:** Should `list_tasks` requests that omit the `limit`
parameter return an unbounded result set, or should the server enforce
a default maximum even when the caller does not request one?

**Context from spec.md:**
> The system MUST expose a paginated `list_tasks` endpoint. The
> specification does not currently state whether `limit` is required or
> optional, nor whether the server enforces a ceiling on the returned
> page size.

The question is being routed to you as the spec context analyst because
this is a policy question — what the project's specifications and
constitution say about bounded responses — rather than a "look at how
the code does it today" question.

## What we need from you

Answer the question from the perspective of project decisions:
constitution, technical roadmap, prior spec clarifications, and
CLAUDE.md. If a constitutional principle or prior spec has already
resolved this kind of question, cite it; if not, propose an answer
grounded in the closest available principle. Propose exact spec text if
the spec needs a new sentence to close the gap.
