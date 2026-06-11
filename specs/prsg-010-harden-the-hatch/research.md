# Research: PRSG-010 Harden the Hatch + O5 Monster Epics

## Decision: Stop-before-PR handling lives in autopilot orchestration

Rationale: The final reviewability gate already has a useful exit contract:
content results are distinguishable from usage or execution errors. PRSG-010
should preserve that contract and add the missing orchestration boundary before
PR body generation, single `gh pr create`, or `multi-pr-emission.sh`.

Alternatives considered:

- Change `reviewability-gate.sh` exit meanings: rejected because downstream
  scripts and tests already depend on the current pass/warn/block/error shape.
- Let PR body generation happen before blocking: rejected because FR-001 and
  FR-007 require no PR body or PR record for an unexcepted block.

## Decision: Re-slicing packet is a first-class JSON recovery artifact

Rationale: Operators need a durable packet that both humans and resume/status
flows can read. The packet records gate metrics, exception evidence, blocked
operations, sizing and layer-planning context, PRSG-009 handoff command shape,
and suggested slice boundaries.

Alternatives considered:

- Store only a Markdown status note: rejected because resume/status automation
  needs stable fields.
- Store only raw gate output: rejected because it does not capture no-PR
  assertions, rejected exception provenance, or re-slicing guidance.

## Decision: Remove generated live exception boilerplate but preserve typed exceptions

Rationale: Valid typed exceptions remain necessary for rare refactor, infra,
and upgrade work. The risk is generated copy-paste boilerplate, not the typed
exception mechanism itself. Generated roadmap and template content must avoid
live lines that match `Reviewability-Exception: refactor`, `infra`, or
`upgrade`.

Alternatives considered:

- Disable all exceptions: rejected because legitimate oversized work would lose
  the operator-owned escape hatch designed in earlier PRSG work.
- Keep live examples near users: rejected because generated examples can be
  mistaken for approved operator evidence.

## Decision: O5 uses a parent manifest and flat sibling child specs

Rationale: A manifest at `specs/<parent-branch>/o5-parent-manifest.json` gives
status and scaffold deterministic topology while preserving current flat
`specs/*` scanners. Child specs remain normal feature directories such as
`specs/prsg-010a-<slug>`.

Alternatives considered:

- Nested `specs/<parent>/<child>` directories: rejected because v1 must not
  broaden every MOC, index, and stale-spec scanner.
- Docs-only convention: rejected because status rollup and topology validation
  would remain interpretive.

## Decision: O5 status validates topology before rollup

Rationale: Missing children, duplicate IDs, later-child dependencies, unknown
dependencies, and cycles can make a rollup misleading. Status should first
validate topology, then compute child state in manifest order with precedence
`invalid topology > blocked/failed > in_progress > pending > complete`.

Alternatives considered:

- Infer parent/child hierarchy from directory names: rejected because flat
  sibling directories are required and names alone cannot represent dependency
  order or shared links.
- Trust optional declared status: rejected because declared status is useful
  only as a drift check against computed read-only status.

## Decision: Contextual probes are decisive only with deterministic high-confidence evidence

Rationale: The router should promote flag-system, release-cadence, and
consumer-locality evidence only when evidence is tied to current tasks and
meets explicit criteria. Weak hits remain closed-enum hints and never enter
`signals[]`.

Alternatives considered:

- Treat keyword hits as decisive: rejected because code fences, fixtures,
  historical specs, and comments can misroute work.
- Keep all contextual probes advisory forever: rejected because PRSG-010
  explicitly requires high-confidence evidence to improve routing.

## Decision: Promote a production routing schema

Rationale: The existing dogfood fixture schema documents the router shape but
is not a production contract. PRSG-010 should add or promote
`routing-decision.schema.json` under the plugin contracts directory, preserve
the flat `route`, `releasable`, `signals`, `hints`, and `warnings` shape,
extend the signal enum, and close `hints[]`.

Alternatives considered:

- Keep schema only under fixtures: rejected because production behavior needs a
  durable contract outside a historical dogfood fixture.
- Replace the output shape: rejected because PRSG-007/008/009 consumers already
  rely on the flat object.

## Decision: PRSG-010 ships as an ordered split stack

Rationale: The feature crosses scripts, skill mirrors, templates, status, and
tests. A four-slice stack keeps reviewable surfaces small while dogfooding the
PRSG-009 split-PR path.

Alternatives considered:

- One PR: rejected because the spec projects roughly 1,700 reviewable LOC and
  multiple surfaces.
- Defer O5: rejected because O5 is part of the accepted PRSG-010 scope.
