# Phase 0 Research: Candidate Route Baseline Planning Decisions

This document resolves planning and architecture choices for G56R-001. It does
not contain the implementation phase's current OpenAI platform findings, model
catalog, route conclusions, or final handoff decision. Those facts must be
collected during the recorded one-working-day spike from the evidence sources
defined below.

## Decision 1: Publish Markdown and JSON as separate authorities

**Decision**: Publish
`docs/ai/research/codex-agent-route-candidates.md` as the cited human review
record and `docs/ai/research/codex-agent-route-candidate-manifest.json` as the
versioned machine-readable projection. Neither artifact silently fills missing
fields from the other.

**Rationale**: The narrative is needed for evidence classification, source
conflicts, rationale, and review order. The JSON is needed for exact agent,
identity, route, candidate, provenance, fixture, unknown, and handoff checks.
Independent completeness plus normalized agreement satisfies AC-1.5 and
AC-1.6 without parsing arbitrary prose into policy.

**Alternatives considered**:

- Markdown only was rejected because G56R-002 would have to reconstruct
  structured identities and contracts from prose.
- JSON only was rejected because it is a poor primary surface for cited
  reasoning and source-conflict review.
- Generated Markdown from JSON was rejected because narrative evidence and
  judgment cannot be reduced to the manifest without a larger generator.

## Decision 2: Use split evidence authority and predeclared precedence

**Decision**: Current official OpenAI documentation is exclusive authority for
OpenAI platform facts. Tracked repository files at one recorded revision are
authority only for SpecKit Pro project facts. Cached content and sanitized
installed state remain separately classified environment observations and
never override tracked production definitions.

For competing official sources, prefer the source with the narrowest explicit
surface, version, and feature applicability. Recency alone is not a tiebreaker.
An equal-authority conflict remains unresolved and ends as
`blocking_no_go` or `nonblocking_deferred` under the ratified terminal rule.

**Rationale**: This is the final Q5 resolution and satisfies both the platform
source standard in AC-1.2 and the repository inventory required by AC-1.1,
AC-1.3, and AC-1.7.

**Alternatives considered**:

- Strict official-docs-only for every fact was rejected because OpenAI docs
  cannot establish repository routes, local source topology, or fixture gaps.
- Local observations as platform corroboration were rejected because one
  machine cannot establish general product behavior.
- Newest-source-wins was rejected because newer text may target a different
  client, version, or surface.

## Decision 3: Record four surfaces independently

**Decision**: Every platform claim has an independent applicability record for
`cli`, `desktop_app`, `app_server`, and `non_interactive` when relevant. Silence
is `undocumented`; `not_applicable` requires explicit official evidence; no
surface inherits another surface's fact.

**Rationale**: Surface isolation prevents a CLI fact from becoming an app,
app-server, or automation claim and makes applicability conflicts auditable.

**Alternatives considered**:

- A unified Codex record was rejected because it hides client differences.
- CLI-as-default was rejected because it leaves three required surfaces
  implicitly generalized.

## Decision 4: Keep one self-contained record per named agent

**Decision**: Use an agent-centric manifest. Every element of `agents` embeds
the named role's semantic contract, present/absent production route,
candidates, classified source observations, fixture contract, telemetry needs,
unknowns, provenance, and invalidation triggers. Root-level normalized route or
contract tables are not introduced.

**Rationale**: One explicit record per agent keeps the hard contract beside
every route hypothesis and avoids joins that could separate a candidate from
its authorization or safety constraints.

**Alternatives considered**:

- Normalized contract/route tables were rejected as unnecessary complexity for
  twelve records.
- Route-centric records were rejected because they fragment named-role
  obligations.

## Decision 5: Bind readable identities to canonical hashes

**Decision**: Use the ratified ID forms:

- `agent-contract/<agent-name>/v<N>`
- `candidate-route/<agent-name>/<model-slug>/<effort-slug>/<treatment-slug>/v<N>`

Hashes are lowercase `sha256:<64-hex>`. Normalize strings to Unicode NFC,
normalize CRLF/CR to LF, preserve all other whitespace, and encode UTF-8
without BOM. `instruction_hash` covers only the complete decoded instruction
body. `contract_hash` covers `agent_name` plus all FR-006 semantic fields after
recursive string normalization and deterministic Python JSON serialization
with `ensure_ascii=False`, `sort_keys=True`, compact separators, and
`allow_nan=False`.

**Rationale**: Readable IDs support review and stable references; hashes detect
content drift. Excluding transport/configuration syntax keeps the two Claude
semantic sources from masquerading as Codex route configuration.

**Alternatives considered**:

- Readable IDs without hashes were rejected because they cannot detect changed
  content under an old identity.
- Hash-only IDs were rejected because they are difficult to review and cite.
- Hashing whole TOML/frontmatter files was rejected because it binds semantic
  identity to transport-specific mechanics.

## Decision 6: Catalog all evidence-supported project candidates

**Decision**: Include the immutable production baseline and every
evidence-supported project-level model/effort candidate eligible for each role.
Include a prompt/context treatment only with a cited bounded-overhead hypothesis
and retain the unchanged treatment as its attribution control. A hard-contract
incompatibility, contract failure, or applicable predeclared dominance evidence
may exclude a candidate; local installation absence may not.

All preferred/fallback signals remain hypotheses. Presentation order is
lexical by stable ID and carries no preference or fallback meaning.

**Rationale**: G56R-001 defines project eligibility; G56R-002 determines
installation executability and G56R-003 owns scored qualification and ordering.

**Alternatives considered**:

- A curated shortlist was rejected because it pre-filters without downstream
  capability or outcome evidence.
- Broad prompt exploration was rejected because it exceeds the research
  timebox and loses attribution.
- Excluding unavailable local models was rejected because it conflates project
  policy with one environment.

## Decision 7: Use one feature-local focused checker

**Decision**: Create
`specs/g56r-001-candidate-route-baseline/check-artifacts.py` as a fixed-path,
offline, read-only Python 3.11+ checker. It validates JSON structure, version,
exact 12/10/2 coverage, required fields, IDs, canonical hashes, evidence and
surface completeness, fixture inventory, sanitization, cross-artifact
agreement, classified unknowns, and reproducible terminal state. Run it twice
for repeatability, then run Layer 4 and the default deterministic suite.

**Rationale**: A direct checker gives objective evidence while keeping exactly
three research delivery files and avoiding a schema package, generic helper,
fixture framework, or dependency. Because it is a checked-in repository tool,
Constitution Principle IV requires one focused Layer 4 unit file and its entry
in the existing suite manifest.

**Alternatives considered**:

- Manual review only was rejected because identity, hash, and agreement checks
  would not be reproducible.
- JSON Schema plus a reusable validator was rejected as unnecessary and
  incomplete for cross-artifact semantic rules.
- A reusable repository validation framework was rejected; the existing Layer
  4 manifest receives only the constitution-required focused test entry.

## Decision 8: Make fixture and unknown ownership explicit

**Decision**: Record exactly three current fixtures (`codebase-analyst`,
`domain-researcher`, `spec-context-analyst`) and nine missing fixtures
(`phase-executor`, `implement-executor`, `analyze-executor`,
`checklist-executor`, `uat-runbook-author`, `clarify-executor`,
`consensus-synthesizer`, `gate-validator`, `autopilot-fast-helper`). Every
agent gets a fixture contract with status, nullable repository-relative path,
representative task/input, expected behavior/output, and hard-contract
assertions. Historical prompt emulation is `non_release_evidence`.

Documentation and source-inventory questions belong to G56R-001. Executable
capability and installation availability belong to G56R-002. Fixture execution,
exact-treatment replay, scoring, qualification, and route ordering belong to
G56R-003. Every deferred unknown records class, impact, owner spec, and required
follow-up.

**Rationale**: Named ownership keeps a classified unknown from silently
becoming either a false conclusion or a generic future-work bucket.

**Alternatives considered**:

- A fixture name list was rejected because it is not actionable for later
  exact-treatment qualification.
- Implementing fixtures now was rejected because it crosses the research-only
  boundary.
- Leaving capability questions unowned was rejected because it makes the
  handoff irreproducible.

## Decision 9: Use a terminal objective gate at the workday boundary

**Decision**: Record `started_at` and `deadline_at` before any checker or
evidence work and `stopped_at` at the terminal boundary no later than the
deadline. Emit `go` only when the declared
artifact, coverage, contract, candidate, provenance, agreement, fixture,
telemetry, unknown-classification, and sanitization checks all pass and no
blocking conflict remains.

Otherwise emit `no_go` containing `started_at`, `deadline_at`, `stopped_at`,
`completed_artifacts`, and `unmet_conditions`. Each unmet condition records
`gate_id`, `requirement_refs`, `condition`, `available_evidence_ids`, `impact`,
`owner_spec`, and `required_follow_up`.

**Rationale**: The spike is bounded by one workday, but its result is bounded by
objective completeness. A no-go packet is a valid terminal result; extending
time or reducing deliverables is not.

**Alternatives considered**:

- Maintainer-confidence-only completion was rejected because it is not
  reproducible.
- Automatic go at the deadline was rejected because it could pass missing
  contracts or evidence to G56R-002.
- Extending until complete was rejected because it breaks the ratified spike
  size.

## Resolved planning unknowns

All plan-level technology, structure, identity, validation, evidence, and
terminal-behavior decisions are resolved. The remaining questions are
deliberately implementation evidence tasks, not Plan clarifications:

- Current documented model IDs and effort values must be collected from
  current official OpenAI sources during the spike.
- Installation-specific executability remains G56R-002 work. G56R-001 records
  only the capability-snapshot requirement; G56R-002 creates or selects and
  binds the versioned runtime snapshot during admission.
- Preferred routes and ordered fallbacks remain G56R-003 qualification work.

No `NEEDS CLARIFICATION` item remains in the Plan artifacts.
