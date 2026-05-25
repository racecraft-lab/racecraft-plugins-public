## Clarify Question

**Spec:** SPEC-009 (search and database access)

**Question:** When a list endpoint receives a request without an explicit
`limit` parameter, what default page size should the implementation use,
and where should that default be defined?

**Context from spec.md:**
> The system MUST expose a paginated `list_tasks` endpoint that returns
> cursor-based results. The default page size is not specified in the
> spec.

The question is being routed to you as the codebase analyst because the
codebase likely already has an established pagination default that the
new endpoint should match.

## What we need from you

Answer the question from the perspective of established code patterns in
this repository. Look for existing list endpoints, default constants,
shared pagination helpers, or precedent set by SPEC-006 (notifications)
or SPEC-007 (repetition). Cite the specific file/line where the default
is defined today, or report low confidence if no precedent exists.
