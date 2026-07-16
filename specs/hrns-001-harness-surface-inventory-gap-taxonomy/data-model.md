# Data Model: Harness Surface Inventory and Gap Taxonomy

This is a conceptual Markdown data model. It is not a runtime schema, generated
registry, validator input, or install-facing payload.

## Entity: Harness Surface

Represents a repository surface that can affect long-running SpecKit Pro agent
behavior.

Fields:

- `surface_id`: short stable label for the surface section.
- `surface_type`: one of `skill`, `agent`, `command`, `helper`, `runner`,
  `generated payload`, `docs`, `workflow file`, `PR packet`, `test/eval`, or
  `release gate`.
- `source_paths`: repository source paths that establish the surface.
- `authority_status`: `authoritative`, `generated`, `fixture-like`, `derived`,
  `unreviewed`, or `excluded`.
- `notes`: concise review notes or exclusions.

Validation rules:

- Every required AC-1.1 surface type must appear at least once or be explicitly
  marked not applicable with rationale.
- Generated, cache, fixture, transcript, and derived-index paths cannot be
  factual authority.

## Entity: Retained Gap / Canonical Gap Row

Represents one reviewed harness observation that remains relevant after
duplicate, obsolete, and out-of-scope items are removed.

Fields:

- `gap_id`: stable `HRNS-GAP-###` identifier.
- `title`: short reviewer-readable name.
- `summary`: one- or two-sentence description.
- `surface_tags`: one or more Harness Surface tags.
- `taxonomy_type`: `context`, `tool contract`, `permission`, `sandbox`,
  `memory/state`, `orchestration`, `verification`, `observability`, `HITL`,
  `security`, `garbage collection`, or justified extension.
- `lifecycle_state`: `implemented`, `planned`, `deferred`, `duplicate`,
  `obsolete`, `unknown`, or `external-owner`.
- `authoritative_evidence`: repository path, commit, PR, issue, or approved
  external primary source reference.
- `owner_workflow`: HRNS/CAR/G56R/spec workflow that owns the next action.
- `cross_roadmap_owner`: `HRNS`, `CAR`, `G56R`, other roadmap label, or `none`.
- `dependency_posture`: `repo-local convention`, `runner/helper change`,
  `generated-doc/test evidence`, `future explicit dependency decision`,
  `deferred`, or `unknown`.
- `downstream_hrns_owner`: follow-up HRNS spec or `none`.
- `safety_closure`: `human-in-the-loop`, `human-on-the-loop`,
  `fully automated`, `disallowed`, or `unknown/non-promotable`.
- `closure_evidence`: source evidence or explicit `unknown`.
- `notes_as_of`: date and any bounded caveat.

Validation rules:

- Each retained gap has exactly one canonical row.
- IDs are zero-padded, stable, and never reused after publication.
- Gaps touching multiple surfaces use multiple `surface_tags`, not duplicate
  ownership rows.
- CAR/G56R-owned gaps stay visible but remain `planned` or `external-owner`
  when evidence is unmerged.

State transitions:

- `unknown` → `planned` when owner and next action are established.
- `planned` → `implemented` only when source evidence proves closure.
- `planned` → `external-owner` when CAR/G56R or another roadmap owns the work.
- `planned` or `unknown` → `deferred` when a reviewed deferment names the owner.
- Any state → `obsolete` only with evidence that the surface or need no longer
  exists.
- Any state → `duplicate` only when the canonical replacement row is named.

## Entity: Evidence Class

Represents authority and exclusion rules for evidence sources.

Fields:

- `class_name`: evidence category.
- `examples`: path or source examples.
- `authority_rule`: how the class may be used.
- `exclusion_reason`: required when non-authoritative.

Validation rules:

- Repository source, tests, agent guidance, constitution, PRDs, roadmaps, MOCs,
  workflow/process docs, ADRs, and approved issue/PR evidence can be authority
  when current and reviewed.
- Generated payloads, caches, fixtures, transcripts, derived indexes, and
  unreviewed chat are excluded as factual authority.

## Entity: External Candidate

Represents a third-party specification, framework, library, tool, or exemplar
used as reference evidence.

Fields:

- `candidate`: name.
- `category`: schema, orchestration, eval, trace/observability, guardrail,
  workflow runtime, coding-agent harness, or knowledge format.
- `mapped_hrns_surfaces`: downstream HRNS area(s) informed by the candidate.
- `local_first_fit`: fit summary or `unknown`.
- `runtime_dependency_posture`: `reference-only`, `future explicit dependency
  decision`, `optional adapter candidate`, `defer`, `reject`, or `unknown`.
- `telemetry_privacy_posture`: cited posture or `unknown`.
- `license_supply_chain_risk`: cited posture or `unknown`.
- `normative_reference_status`: normative, reference tooling,
  implementation example, product/tool, or `unknown`.
- `observed_version_or_commit`: version, commit, release, or `unknown`.
- `evidence_as_of`: date of review.
- `primary_evidence`: official specs, docs, source repo, release/maturity, or
  license source.
- `compatibility_gaps`: concise gap list or `none known`.
- `recommendation`: `reference pattern`, `future spike`,
  `optional adapter candidate`, `defer`, `reject`, or `unknown`.

Validation rules:

- No candidate recommendation can authorize required dependency adoption.
- Missing evidence stays `unknown`.
- The OKF row must record the pinned normative revision and reference-tooling
  compatibility posture.

## Entity: Self-Improvement Loop

Represents a workflow that can generate or influence future harness behavior.

Fields:

- `loop_id`: stable label.
- `surface_refs`: affected surfaces.
- `behavior`: generate, critique, refine, verify, trace, handoff, or other.
- `approval_boundary`: human-in-the-loop, human-on-the-loop, fully automated,
  disallowed, or unknown/non-promotable.
- `promotion_rule`: what evidence is required before output can affect
  harness-control files.
- `evidence`: source path or `unknown`.

Validation rules:

- Unknown approval boundaries are `unknown/non-promotable`.
- Open-ended recursive self-improvement and self-modifying harness-control
  loops are disallowed unless a later dedicated spec proves bounded controls.

## Entity: AC Crosswalk Row

Represents proof that each PRD acceptance criterion is covered.

Fields:

- `ac_id`: AC-1.1 through AC-1.10.
- `artifact_section`: target section in the taxonomy.
- `row_refs`: gap or candidate rows proving coverage.
- `verification_evidence`: command, review evidence, or manual proof.
- `status`: pass, deferred, or unknown.

Validation rules:

- AC-1.1 through AC-1.10 must each map to a section or row.
- Deferred items must name owning HRNS, CAR, G56R, or roadmap entry.
