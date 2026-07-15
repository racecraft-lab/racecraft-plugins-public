# Implementation Plan: CAR-001 Candidate Route Baseline and Role Contracts

**Branch**: `car-001-candidate-route-baseline` | **Date**: 2026-07-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/car-001-candidate-route-baseline/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

CAR-001 is a read-only documentation research spike that produces a dated, cited
baseline handoff so CAR-002 can freeze the project-eligible candidate set and
design the capability probes; the executable subset follows successful probing
and qualification. The deliverable is **two artifacts** under
`docs/ai/research/`: a human-readable Markdown research record
(`claude-agent-route-candidates.md`) and a separate machine-readable JSON
manifest (`claude-agent-route-candidate-manifest.json`). The record holds the
agent + route-policy surface inventory, the primary-source fact table (every row
carrying URL + access date + short verbatim quote and labeled fact / inference /
proposed policy / assumption), the requirements-level fixture backlog, the
stable-ID capability questions, and the go/no-go handoff. The manifest is the
machine contract that CAR-002/CAR-003/CAR-006 bind to programmatically: for each
of the twelve named agents it records the immutable production route (or its
recorded absence for the net-new `autopilot-fast-helper`), a role contract, the
alias-based candidate tuples with expected resolved model IDs and effort,
required capabilities, `agent_contract_id`, instruction and full-file hashes,
rationale, known incompatibilities, required qualification artifacts, and
invalidation triggers.

Technical approach: pin the immutable production comparator to the
latest-published-at-research-time release tag `speckit-pro-v2.19.1` (commit
`e343aa2e4ebcb2d48c501f285d7072cfd55722da`) per the binding FR-009 / Design Q3
rule — 2.19.0 was the 2026-07-13 scaffold-time snapshot, superseded by the
2.19.1 patch published later that day, and `speckit-pro/agents/*.md` and
`speckit-pro/codex-agents/` are byte-identical between the two tags (verified via
`git diff`), so every route tuple and hash is unchanged; compute instruction
identity as the sha256 over the
frontmatter-stripped agent body with the full-file sha256 recorded alongside
(FR-011 / Design Q4) using the Python 3.11+ standard library only (FR-025); cite
every platform fact from current official Anthropic documentation fetched live
(FR-004); and change zero shipped bytes (FR-024). All nine binding design
decisions (Q1–Q9) are already resolved in the design concept, so no planning
`NEEDS CLARIFICATION` remains; the only open items are execution-time doc facts,
which the spec already routes to the capability-question list by construction.

## Technical Context

**Language/Version**: Python 3.11+ standard library (`hashlib.sha256`, `json`),
invoked ad hoc during the spike for hash computation and JSON validity; any
helper snippet stays inside the research record or this spec directory, never in
shipped (`speckit-pro/`) or test (`tests/`) trees (FR-025). The deliverables
themselves are Markdown + JSON — there is no compiled language.

**Primary Dependencies**: None beyond the Python standard library. Official
Anthropic documentation is fetched live via the available web tools
(WebFetch / Tavily or equivalent) to source and quote platform facts; the docs
are an evidence source, not a runtime dependency.

**Storage**: Flat files. One Markdown record and one JSON manifest, both under
`docs/ai/research/`. No database, no generated payload, no installed-cache write.

**Testing**: `python3 tests/speckit-pro/run-all.py` (default deterministic
suite — must pass untouched, SC-006); JSON validity check on the manifest
(`python3 -m json.tool` / stdlib `json.load`); JSON Schema conformance against
`contracts/agent-route-candidate-manifest.schema.json`; a privacy scan for
absolute filesystem paths in both artifacts; and hash recomputation to
demonstrate SC-007 (a pure frontmatter route change leaves the instruction
sha256 unchanged).

**Target Platform**: Repository documentation. The artifacts are read by humans
(the record) and by downstream CAR-002/CAR-003/CAR-006 tooling (the manifest);
they are platform-agnostic.

**Project Type**: Documentation research spike — read-only with respect to the
plugin. No production code, no plugin components, no shipped-byte change.

**Performance Goals**: N/A. Research artifacts sized by timebox (one autopilot
run, Design Q9), not by throughput or latency.

**Constraints**: Zero shipped-byte change and nothing under `speckit-pro/`'s
allowlisted payload directories (FR-024, SC-006); no new Bash and Python stdlib
only for any hashing (FR-025, Constitution II); no absolute filesystem paths in
any authored artifact (privacy scan); one-autopilot-run timebox with unresolved
mandatory facts flowing to the go/no-go handoff as no-go items or capability
questions rather than extending the box (FR-023, Design Q9); every platform fact
cited with URL + access date + short verbatim quote (FR-004, Design Q5).

**Scale/Scope**: Twelve named agents (eleven current Claude agents plus the
net-new `autopilot-fast-helper`); two deliverable files; roughly 1,000–1,600
lines of prose and structured data across the two artifacts; zero
production-code LOC.

**Reviewability Budget**: Primary surface docs/process (one Markdown record +
one JSON manifest under `docs/ai/research/`); projected reviewable production
LOC 0 (estimator advisory `{estimated_loc: 0, suggested_slices: 1, status: ok}`,
spike flag); 0 production files; 2 total deliverable files; budget result within
budget.

## Declared File Operations

The plan-phase reviewability estimator parses this block to project the slice's
production-LOC footprint before `tasks.md` exists. Both deliverables are
documentation/data files (`.md` and `.json` under `docs/ai/research/`), so they
carry zero production-code LOC; the estimator degrades them to non-production and
returns `estimated_loc: 0`. The SDD process artifacts under
`specs/car-001-candidate-route-baseline/` (this plan plus `research.md`,
`data-model.md`, `contracts/`, `quickstart.md`) are workflow outputs, not
production files, and are intentionally omitted from this block.

- NEW docs/ai/research/claude-agent-route-candidates.md
- NEW docs/ai/research/claude-agent-route-candidate-manifest.json

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Evaluated against the Racecraft Plugins Public Constitution v1.2.0.

| Principle | Verdict | Basis |
|-----------|---------|-------|
| I. Plugin Structure Compliance | PASS (N/A change) | No plugin directory, command, agent, skill, hook, or manifest is added or modified. Deliverables live under `docs/ai/research/`; nothing lands under `speckit-pro/`. Layer 1 structural validation is unaffected. |
| II. Cross-Platform Runtime & Script Safety | PASS | Any hash / JSON computation uses the Python 3.11+ standard library only (`hashlib`, `json`), run ad hoc; no new Bash, `jq`, or PowerShell. Helper snippets stay inside the research record or this spec dir, never in shipped or test trees (FR-025). |
| III. Semantic Versioning | PASS (N/A change) | No version bump; `speckit-pro/.claude-plugin/plugin.json` is untouched. The comparator only reads the published `2.19.1` tag identity; it does not mutate version state. |
| IV. Test Coverage Before Merge | PASS | No new Python helper, gate, or repository tool is added to shipped or test trees (the ad hoc hashing snippet is transient, not a committed deliverable), so no Layer 4 coverage obligation is triggered. The default suite (Layers 1, 4, 5) must still pass with zero failures (SC-006). |
| V. Conventional Commits | PASS (planning-level) | The implementation PR title and commits will follow `type(scope): description` (a `docs(...)`-class change); enforced by CI `validate-pr-title`. |
| VI. KISS, Simplicity & YAGNI | PASS | Exactly two artifacts. JSON is produced and validated with Python's stdlib `json`, not `jq`. The manifest is the single source of machine data and the record the single source of evidence — cross-referenced by `agent_name` + `agent_contract_id`, never duplicated (Constitution VI single-source-of-truth). This is a research spike, not a new plugin; its purpose is documented in the master plan at `docs/ai/specs/claude-agent-routing-technical-roadmap.md`. |

**Required plan additions (all specs):**

- **Primary review surface**: docs/process — one Markdown research record plus
  one JSON research manifest, both under `docs/ai/research/`. **Secondary
  surfaces**: none. The spike is read-only to the plugin.
- **Reviewability budget**: within budget. Projected 0 production LOC
  (estimator `{estimated_loc: 0, suggested_slices: 1, status: ok}`, spike flag),
  0 production files, 2 total files, 1 primary surface — all below the warn
  thresholds (400 reviewable LOC, 6 production files, 15 total files, >1 primary
  surface) and the block thresholds (800 reviewable LOC, 8 production files, 25
  total files, >1 primary surface). The ~1,000–1,600 prose-and-data lines are
  research content sized by timebox under the spike escape hatch, not production
  LOC subject to the 800-LOC block; no split exception is required.
- **Split decision**: remains one spec (`suggested_slices: 1`). The deliverable
  is a single coherent baseline-and-handoff whose go/no-go section would be
  fractured by a split; downstream work is already sliced as CAR-002 through
  CAR-011.
- **PR review packet source**: the spec's *PR Review Packet Requirements*
  section supplies what changed, why, non-goals, review order, scope budget,
  traceability, verification evidence, known gaps, and rollback notes; this
  plan's traceability (below) maps each major requirement to its artifact and
  verification.

**Post-Design re-check (after Phase 1):** PASS — unchanged. The Phase 1 design
adds only documentation artifacts (`data-model.md`, one JSON Schema under
`contracts/`, `quickstart.md`) under the feature spec directory; it introduces
no plugin component, no shipped-byte change, no new Bash, and no new runtime
dependency. All six principles remain satisfied and no Complexity Tracking entry
is required.

## Project Structure

### Documentation (this feature)

```text
specs/car-001-candidate-route-baseline/
├── spec.md              # Feature specification (already written)
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 output — resolved decisions + research method
├── data-model.md        # Phase 1 output — full manifest JSON schema (field set)
├── quickstart.md        # Phase 1 output — validation guide
├── contracts/           # Phase 1 output — machine contract downstream binds to
│   └── agent-route-candidate-manifest.schema.json
├── checklists/          # Pre-existing checklist artifacts
└── SPEC-MOC.md          # Pre-existing spec map-of-content
```

### Deliverables (repository root)

```text
docs/ai/research/
├── claude-agent-route-candidates.md              # NEW — the Markdown research record
└── claude-agent-route-candidate-manifest.json    # NEW — the JSON candidate-route manifest
```

Read-only inventory sources consumed (never modified) during implementation:

```text
speckit-pro/agents/*.md                                 # 11 current Claude agents (frontmatter route tuples + bodies)
speckit-pro/codex-agents/autopilot-fast-helper.toml     # source contract for the net-new 12th agent
tests/speckit-pro/layer6-efficiency/fixtures/           # current Claude Layer 6 fixtures: consensus-synthesizer, gate-validator
speckit-pro/skills/**, references/**, validators, dist/**, installed-cache mirrors  # AC-1.1 route-policy surface inventory
```

**Structure Decision**: Documentation research spike. The two committed
deliverables live under `docs/ai/research/` (matching the repo's existing
research-spike convention — e.g. `cross-platform-runtime-inventory.md`,
`tool-agnostic-capability-discovery-spike.md`). The SDD process artifacts stay
under `specs/car-001-candidate-route-baseline/`. Nothing is written under
`speckit-pro/`, `dist/`, or `tests/`; the inventory sources there are read-only.

## Complexity Tracking

> No Constitution Check violations. This section is intentionally empty — no
> principle is violated, so no justification is required.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | (none) | (none) |
