# Agent Routing Evidence and Structural Parity Contract

**Applies to:** `CAR-001` and `G56R-001` candidate-route baselines
**Schema:**
[`agent-route-candidate-manifest.schema.json`](../research/agent-route-candidate-manifest.schema.json)
**Status:** Active foundation for CAR-002 and G56R-002

## Purpose

The Claude Code and Codex routing programs implement the same product contract
for the same twelve named agents. Their PRDs, roadmaps, research reports, and
machine manifests use one structure. Content differs only where Anthropic and
OpenAI document different coding-agent surfaces, model catalogs, controls, or
runtime evidence.

This contract does not assert that the platforms expose identical features. It
requires identical evidence handling when a feature is documented, absent,
surface-specific, or unresolved.

## Vendor Documentation Authority

Only current documentation on the following canonical domains may establish a
platform fact or admit a candidate:

| Platform | Authoritative documentation |
|---|---|
| Claude Code | `code.claude.com/docs/**`, `platform.claude.com/docs/**` |
| Codex | `learn.chatgpt.com/docs/**`, `developers.openai.com/codex/**`, `developers.openai.com/api/docs/**`, `platform.openai.com/docs/**` |

Redirected legacy URLs may be retained as `requested_url`, but the final
`canonical_url` must match the platform allowlist. OpenAI Apps SDK documentation
may support an explicitly Apps-SDK-scoped boundary; it cannot establish Codex
custom-agent support.

Vendor support articles, marketing pages, news posts, release announcements,
third-party research, repository observations, runtime discovery, and
successful probes are not platform-fact authority. They may be preserved as
historical context or classified under another evidence class.

## Evidence Classes

Both platforms use exactly these classes:

| Class | Meaning |
|---|---|
| `official_documentation` | Current allowlisted vendor documentation establishes a platform fact for the stated surface. |
| `project_input` | Repository, release, payload, installed-cache, or maintainer evidence establishes the current SpecKit Pro contract only. |
| `runtime_verification_needed` | A documented candidate requires availability, binding, or exact-treatment verification in a pinned environment. |
| `qualification_needed` | A documented and executable route still requires controlled project evaluation. |
| `undocumented` | Official documentation does not establish the fact; dependent claims and routes fail closed. |

Runtime discovery and probes may narrow availability for a documented
candidate. They cannot add a model, effort value, configuration field,
telemetry field, or native behavior to the official catalog. Evaluation may
qualify or rank routes but cannot establish platform behavior.

## Shared Research Matrix

Each platform ledger covers the same source families. A family with no
documented platform surface is recorded as `not_documented` or
`not_applicable`; it is never silently omitted.

1. Documentation discovery and canonical URLs.
2. Model catalog, identifiers, positioning, lifecycle, deprecations, and
   replacements.
3. Agent or subagent configuration, supported fields, inheritance, and model
   resolution precedence.
4. Reasoning or effort controls, values, defaults, scope, and model support.
5. Skills, durable instructions, delegation, and role invocation.
6. Tools, MCP or app extensions, permissions, sandboxing, and mutation
   boundaries.
7. Hooks, lifecycle events, effective-route evidence, and service reroutes.
8. Noninteractive and programmatic interfaces, structured output, and errors.
9. Usage, token, cost, latency, and agent-attribution telemetry.
10. Authentication, provider boundaries, product surfaces, and feature
    availability.
11. Pricing, cost categories, administrative analytics, and diagnostic-only
    usage surfaces.

Every platform claim binds at least one source-ledger record. Every candidate
binds coding-agent documentation plus any API or lifecycle documentation needed
for the model. API documentation alone does not prove coding-client or account
availability.

## Source Ledger Contract

An official source record includes the vendor, source family, document class,
requested and canonical URLs, UTC retrieval timestamp, HTTP status, body byte
count and SHA-256, page or surface, locator, supported surfaces, exact facts,
bounded normalized extracts and hashes, claim bindings, access and conflict
status, known gaps, and invalidation triggers.

If official sources conflict, preserve both records and scope each claim to its
documented surface. The dependent claim or candidate remains blocked until the
documentation resolves the conflict. Runtime behavior cannot settle a
documentation-authority conflict.

## Manifest Contract

The Claude and Codex manifests validate against schema `2.0.0` and expose the
same top-level and record-level fields. Unsupported platform values use an
explicit status, `null`, or an empty array. Platform-only top-level keys are
forbidden.

The twelve shared agent names are:

1. `analyze-executor`
2. `checklist-executor`
3. `clarify-executor`
4. `codebase-analyst`
5. `consensus-synthesizer`
6. `domain-researcher`
7. `gate-validator`
8. `implement-executor`
9. `phase-executor`
10. `spec-context-analyst`
11. `uat-runbook-author`
12. `autopilot-fast-helper`

Agent contracts have the same role, safety, grounding, mutation, tool, skill,
MCP, output, capability, source, hash, production-route, field-mapping,
divergence, fixture, and invalidation fields. Candidate routes use generic
model and effort selectors so platform differences remain values, not schemas.

## Historical Integrity

The CAR `1.0.0` manifest and original CAR-001 report remain recoverable from
merge commit `725be949b856724a073622900bd168d29b2f4603`. The canonical manifest
moves to `2.0.0` because the shape is incompatible. Stable legacy fact IDs are
never deleted or renumbered; the new snapshot assigns each one a disposition
and replacement source binding where applicable.

Original workflow, design-interview, archive, and completed-spec records are
historical execution evidence. Later parity decisions are recorded in new
amendments or explicit dated supersession notes.

## Consumption Gates

- CAR-002 and G56R-002 must not consume a manifest until its schema, source
  ledger, cross-references, and historical dispositions pass validation.
- Revalidate official sources before each consuming scaffold and before
  release. A changed or withdrawn source invalidates bound claims and routes.
- No candidate in either baseline is executable or preferred. Capability
  verification and qualification remain later-spec responsibilities.
- Changes under this contract do not alter plugin runtime behavior, shipped
  model defaults, payloads, installed caches, or release versions.
