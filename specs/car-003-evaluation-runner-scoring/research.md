# Phase 0 Research: CAR-003 Evaluation Runner, Fixtures, Scoring, and Statistical Analysis

**Date**: 2026-07-24 | **Spec**: `specs/car-003-evaluation-runner-scoring/spec.md`

All open decisions in the Technical Context are resolved here; the plan carries no
unresolved-clarification markers. Four Clarify sessions already closed the specification-level
questions; this document records only the *implementation* decisions those
sessions left to planning, plus the codebase evidence each one rests on.

## Conventions

- Paths are repository-relative.
- "Shared contract" means a repo-level schema that is byte-identical across the
  Claude and Codex worktrees and MUST NOT be unilaterally extended.
- "Parity reference" means the Codex twin's spec-scoped schema, which CAR-003
  mirrors *logically* by authoring its own copy under this spec's `contracts/`.

---

## R-001: Where the canonical materializer lives and what it may depend on

**Decision**: One new module `speckit-pro/speckit_pro_runner/materializer.py`,
Python 3.11 standard library only, importing nothing from `tests/`. Layer 6
consumes it through an import inside
`tests/speckit-pro/layer6-efficiency/lib/claude_treatment_runner.py` rather than
a separate adapter file.

**Rationale**: Clarify fixed the location (design concept Q4) and forbade a
second implementation. The repository already settled the general rule after the
test relocation work: a library used by shipped code lives in the plugin, never
under `tests/`. `speckit_pro_runner` is the existing shipped Python package
(currently `__init__.py`, `__main__.py`, `envelope.py`, `merge_utils.py`,
`path_utils.py`, `runtime.py`, plus `gates/` and `helpers/` subpackages), so a
new sibling module is the smallest change that satisfies the constraint. The
"thin Layer 6 adapter" the design concept describes is genuinely thin — an
import plus a call — so giving it its own file would add a reviewable path
without adding reviewable behavior, which principle VI (YAGNI) rejects.

**Alternatives considered**:

- *Separate `lib/agent_materializer_adapter.py`*: matches the design concept's
  wording literally, but the adapter is a one-line delegation; a dedicated file
  is an abstraction for a single-use call.
- *Implement in Layer 6 first and relocate during CAR-006*: explicitly rejected
  in Clarify because relocating a payload-affecting module means running the
  generated-artifact regeneration ritual twice.

## R-002: How the shipped module is reached from the test tree

**Decision**: The Layer 6 consumer resolves the plugin root the same way the
existing smoke runner already does — via the `PLUGIN_ROOT` environment variable
with a repository-relative fallback — and loads the module with
`importlib.util.spec_from_file_location`, the loader idiom
`run-efficiency-benchmarks.py` already uses for its `lib/` modules.

**Rationale**: Reusing the established loader keeps the plugin-shaped
verification honest: a plugin-shaped run copies `speckit-pro/` alone, and the
resolver must still find the module. Inventing a second resolution mechanism
would create a path the plugin-shaped run does not exercise.

**Alternatives considered**: `sys.path` mutation (leaks global state into a test
process that also loads the CAR-002 module chain); a packaging install step
(the constitution forbids requiring package installation).

## R-003: Content-hash proof implementation

**Decision**: `sha256(destination_path.read_bytes())` after the write completes,
where the write itself used `write_bytes` on UTF-8-encoded content. The
destination path is verified as a separate assertion and never folded into the
digest preimage. No `newline=` translation, no re-serialization, no
`json.dumps` round trip, no trailing-newline insertion.

**Rationale**: FR-008 and Clarify session 2 fix this exactly. Reading back from
disk is what makes the proof see key order, whitespace, comments, unknown keys,
line endings, and encoding — the six classes of drift that parsed-field
equivalence is blind to. Computing from the in-memory render buffer would prove
only that the renderer is self-consistent.

**Alternatives considered**: hashing the render buffer (fails the stated
requirement); hashing a normalized form (defeats the purpose); including the
path in the preimage (would make an identical file at a different path hash
differently, conflating two independent checks).

## R-004: Reusing the CAR-002 module chain instead of re-implementing

**Decision**: CAR-003's harness modules import the existing chain rather than
re-deriving canonical JSON, digesting, sanitization, or schema validation.
Specifically: `treatment_trace_io.canonical_bytes` for the canonical JSON
serialization (sorted keys, minimal separators, UTF-8, no NaN);
`claude_trace_schema.validate_exact_treatment_replay` for the frozen trace
contract; `claude_capabilities.sanitize_home_paths` / `payload_sha256` for the
sanitization boundary; `treatment_trace_bundle` and `treatment_trace_authority`
for bundle-graph validation and route ownership.

**Rationale**: These modules are consume-don't-modify by constraint, and they
already implement every primitive CAR-003 needs. `claude_trace_schema.py`
validates the entire CAR-002 contract in 240 lines by driving every check *from*
the JSON Schema rather than hardcoding rules. CAR-003 adopts the same posture:
the contracts carry the rules, and Python carries only what a schema cannot
express.

**What a schema cannot express, and therefore stays in Python**:

1. Set intersection admission (official-source ledger x pinned-runtime support).
2. Byte-level read-back hashing.
3. Disposition-bucket precedence over a co-firing reason set.
4. The ordered decision ladder (floors, then non-inferiority, then Pareto).
5. Cross-record digest recomputation and dangling-reference detection.
6. Objective-level partition disjointness across registry entries.

**Alternatives considered**: a standalone CAR-003 validator stack (duplicates
240 lines of proven schema-driven validation and creates a second source of
truth for canonicalization, which would silently break digest equality).

## R-005: Effort ladder divergence from the Codex twin

**Decision**: CAR-003's `successor-capability-freeze.schema.json` uses the
closed ordered ladder `low` < `medium` < `high` < `xhigh` < `max`. The Codex
twin's schema uses `none`, `minimal`, `low`, `medium`, `high`, `xhigh`. The two
schemas are otherwise structurally identical.

**Rationale**: This is a *value* difference, not a logical one, and the parity
alignment section of the design concept explicitly contemplates it: "platform
differences remain values, not schemas". FR-003 names CAR-003's ladder
literally, and the design concept records that `max` is a Claude Code effort
level while `none`/`minimal` are Codex reasoning-effort levels. Forcing a single
union enum would admit efforts neither platform supports.

**Alternatives considered**: a shared union enum (admits unsupported tuples on
both platforms); a free-form string (loses the closed-set guarantee FR-003
requires).

## R-006: Exclusion-reason taxonomy divergence

**Decision**: CAR-003's freeze schema carries the nine reasons FR-029 names:
`source_not_admitted`, `effort_not_source_admitted`,
`effort_source_not_admitted`, `canonical_effort_unknown`,
`surface_evidence_incomplete`, `surface_disagreement`, `alias_repoint_unresolved`,
`availability_not_proven`, `topology_control_not_candidate_effort`. The twin
carries `hidden_state_disagreement` where CAR-003 carries
`alias_repoint_unresolved`; the other eight are identical.

**Rationale**: Both are capability-plane codes for "a surface-level observation
could not be reconciled", and each names the platform's actual failure mode.
Codex exposes hidden reasoning state; Claude Code exposes alias re-pointing.
FR-039 makes `alias_repoint_unresolved` load-bearing on the Claude side (it is
the code that blocks admission when override proof is incomplete or the client
version changed), so it cannot be omitted. FR-034 separately pins
`alias_repoint_unresolved` to the capability plane and forbids repurposing it in
the score plane.

**Alternatives considered**: carrying both codes on both platforms (one would be
permanently unreachable on each side, which is dead enum surface).

## R-007: `sandbox` versus mutation contract in the role corpus

**Decision**: CAR-003's `role-corpus.schema.json` uses `mutation_contract` where
the twin uses `sandbox`. Both are required, non-empty strings in the same
position with the same cardinality.

**Rationale**: FR-012 enumerates the bound fields and names "mutation contract",
not sandbox. Codex exposes a sandbox mode as its containment primitive; Claude
Code expresses the same containment through the agent's permitted-tools and
mutation contract. The shared treatment-record contract already carries *both*
`sandbox` and `mutation_class` as separate fields, which confirms the two are
distinct concepts rather than synonyms, and confirms the Claude-side name.

**Alternatives considered**: keeping the field named `sandbox` on the Claude side
for byte-level parity (would name a concept Claude Code does not expose, and the
spec-scoped schemas are explicitly a parity *reference*, not shared files).

## R-008: Role identifiers

**Decision**: The twelve `role_id` values are adopted from the twin verbatim:
`analyze-executor`, `autopilot-fast-helper`, `checklist-executor`,
`clarify-executor`, `codebase-analyst`, `consensus-synthesizer`,
`domain-researcher`, `gate-validator`, `implement-executor`, `phase-executor`,
`spec-context-analyst`, `uat-runbook-author`.

**Rationale**: Verified against the shipped Claude agent definitions: `agents/`
inside the plugin holds exactly eleven `.md` files whose stems match eleven of
the twelve names. `autopilot-fast-helper` has no shipped definition, which is
precisely the contract-only role FR-011 and FR-012 describe and CAR-011 will
author. The twin's enum and the Claude-side agent inventory agree exactly, so no
divergence is needed here.

## R-009: `failure_code` for platform alias re-pointing

**Decision**: In the score-bundle contract, alias re-pointing uses the twin's
existing `service_reroute` code verbatim. In the shared treatment-record
contract's `disposition_reasons` array it uses the existing
`service_reroute_requested_route_non_scorable` member. Neither enum gains a
Claude-only member.

**Rationale**: These are two different fields in two different contracts, and
both are already closed. The shared treatment-record schema was read directly
and confirmed to contain `service_reroute_requested_route_non_scorable` in
`disposition_reasons` and the four-member `treatment_disposition` set
(`proven`, `unknown`, `non_scorable_rerouted`, `hard_fail`). FR-034 requires the
score-plane taxonomies be adopted verbatim from the twin, and the twin's
`failure_code` enum contains `service_reroute`. Coining `platform_route_change`
would fragment a category downstream analysis treats as mutually exclusive.

**Alternatives considered**: a Claude-only synonym (validates on one platform,
fails on the other, because both enclosing enums are closed under
`additionalProperties: false`).

## R-010: Where the additive records live

**Decision**: Three CAR-003 record classes that the frozen CAR-002 contract
cannot carry are grouped into one additive schema authored as a `oneOf`:

1. **Mandatory observation manifest** (FR-009) — the versioned closed list of
   required telemetry fields the frozen CAR-002 profile never enumerated.
2. **Alias re-point attribution record** (FR-045) — the platform-attribution
   label, because the frozen `record_class` enum is closed to
   `success`, `null`, `unavailable`, `misdelivery`.
3. **Cache diagnostic record** (FR-018) — cache-write-by-TTL-class and
   cache-read breakdowns, because the shared `rawTokenVector` is closed under
   `additionalProperties: false` and carries only `input_tokens`,
   `output_tokens`, `cached_input_tokens`, and `reasoning_output_tokens`.

**Rationale**: All three were verified against the actual schemas: the frozen
trace contract's `recordClass` is `{"enum": ["success", "null", "unavailable",
"misdelivery"]}` and `exactTreatmentReplay.outcome` is exactly
`{status, telemetry_ref, notes}`; the shared `rawTokenVector` has no TTL fields.
Grouping three additive record classes into one `oneOf` document mirrors the
CAR-002 trace contract itself, which is a `oneOf` over four record classes in a
single file — the established repository idiom.

**Alternatives considered**: three separate schema files (three more reviewable
paths for three records that share one versioning and invalidation lifecycle);
extending the frozen enums (explicitly forbidden).

## R-011: The circular dependency between calibration pairs and the analysis plan

**Decision**: A fourth CAR-003 schema, `experiment-assignment.schema.json`,
carries three related pre-execution binding records as a `oneOf`: the Partition
Registry Entry (FR-013), the Calibration Protocol (FR-037), and the Comparison
Set / Assignment (FR-037). A qualification-eligible assignment binds
`analysis_plan_binding`; a calibration assignment binds
`calibration_protocol_binding` instead, and the frozen analysis plan references
the protocol through its own `calibration_binding` field.

**Rationale**: Clarify session 4 resolved the circularity at the specification
level. The twin's `analysis-plan.schema.json` already has a required
`calibration_binding` field, which is the receiving end of the same rule, so
CAR-003 mirrors it exactly. The twin publishes no assignment schema, so the
Claude side authors one; making it schema-enforced (rather than code-only) is
what lets the "bindings exist before execution" invariant be checked by
validation rather than by convention.

**Note on the twin's `experiment-policy` schema**: it makes
`analysis_plan_binding` unconditionally required. CAR-003 mirrors that shape
unchanged — the *policy* is a campaign-level document that always references a
plan version, while the *assignment* is the per-pair record where FR-037's
calibration substitution applies. The two are different records and the
substitution belongs only to the latter.

## R-012: Blindness leak check without a model call

**Decision**: The pre-ballot leak check is a mechanical scan of the blinded
artifact for the freeze-bound model identities, aliases, effort values, agent
frontmatter keys, and route identifiers, driven from the published successor
freeze rather than a hardcoded list. Failure records the existing
`ballot_non_blind` code and blocks scoring. No paraphrase or style
normalization is performed.

**Rationale**: FR-035 and FR-047. Paraphrase normalization requires an
additional non-frozen model call, which breaks bit-exact replay and changes what
is being scored. Driving the identifier list from the freeze means the check
cannot go stale relative to the admitted candidate set.

**Alternatives considered**: an LLM-based leak detector (non-deterministic, adds
a live call to the default suite, which SC-019 forbids).

## R-013: Family exclusion as static policy

**Decision**: Scorer/adjudicator family exclusion is a static declaration in the
frozen experiment policy — a mapping from each candidate route to the model
families barred from scoring it — checked at ballot-collection time by set
membership.

**Rationale**: FR-047 requires it be static and carry no replay cost. A static
declaration is verifiable by reading the frozen policy, replays for free, and
cannot drift between the calibration pilot and later cohorts.

## R-014: Cache isolation between paired arms

**Decision**: Each arm executes with its own ephemeral working directory and its
own cache root, created and destroyed per arm. The isolation claim is recorded
in the trace as a checked property, not asserted in prose.

**Rationale**: US2 acceptance scenario 5 and FR-049's cache-state isolation
policy. The existing smoke runner already uses `tempfile` for per-run isolation,
so the mechanism is established; CAR-003 adds the *recorded proof* that the two
arms did not share a root.

## R-015: The generated-artifact contract

**Decision**: Adding `materializer.py` to the shipped runner triggers the
repository's existing six-step refresh, run through
`scripts/refresh-release-artifacts.py`, followed by a plugin-shaped
verification that copies `speckit-pro/` alone (no `tests/`) and confirms the
module resolves and the hashes match.

**Rationale**: The refresh script's own docstring enumerates the six steps:
recompute runner trust metadata (manifest sha256 entries plus `.sha256`),
rebuild the Claude and Codex install payloads, sync marketplace registries,
content-sync the installed-cache fixtures, refresh the installed-cache proof
tree hashes, and regenerate the payload-completeness, zero-Bash guard, and
release-readiness evidence. It is idempotent. `AGENTS.md` forbids hand-editing
any of these outputs, so the script is the only sanctioned mutator.

**Regenerated path set for one new runner module** (all machine-produced):

- `speckit-pro/speckit_pro_runner/speckit-pro-runner.manifest.json`
- `speckit-pro/speckit_pro_runner/speckit-pro-runner.sha256`
- `speckit-pro/speckit_pro_runner/install_inventory.json`
- `dist/claude/speckit-pro/speckit_pro_runner/` — module plus the same three
  metadata files
- `dist/codex/speckit-pro/speckit_pro_runner/` — module plus the same three
  metadata files
- `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache-proof.json`
- gate evidence under `docs/ai/specs/.process/`

**Known trap**: the file copy underlying the payload rebuild compares by
modification time by default; a checksum-based comparison is required or an
identical-mtime change is silently skipped. Verified previously in this
repository; the refresh script is the correct entry point precisely because it
already handles this.

## R-016: Shared smoke-runner coordination

**Decision**: Sync from the default branch immediately before editing
`tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py`, keep the
edit confined to results metadata and the smoke labelling (the demotion FR-007
requires), and resolve any overlap with the Codex twin branch by `git merge`,
never rebase.

**Rationale**: FR-043 and design concept Q5. The file is a single 495-line
dual-platform script serving both `claude -p` and `codex exec` off a `--codex`
flag. Checked at planning time: neither the default branch nor the twin branch
has modified it yet, so the conflict is latent rather than active — which makes
the sync-before-edit discipline the cheap prevention rather than an after-the-fact
repair. This repository resolves shared-infrastructure conflicts by merge because
rebase rewrites the other branch's ancestry.

## R-017: Reviewability estimator behavior on this repository's layout

**Decision**: The plan declares its reviewability figures explicitly and treats
the setup-mode `reviewability-gate` as the authoritative check. The
`estimate-reviewable-loc` helper's `Declared File Operations` block is filled in
truthfully, but its projection is expected to read low.

**Rationale**: The helper classifies a production file as one whose path starts
with `src/`, `app/`, `lib/`, or `scripts/`, or whose extension is `.ts`, `.tsx`,
`.js`, `.jsx`, `.mjs`, `.cjs`, or `.sql`. This repository's Python lives under
`speckit-pro/` and `tests/speckit-pro/`, so almost nothing matches and the
`production * 40` projection collapses toward zero. Recording this openly is
better than letting a reviewer read `projected: 0` as evidence of a trivial
change. The gate that actually governs — `reviewability-gate` in setup mode —
reads the declared numbers from this plan, which are derived by hand below.

## R-018: Verification strategy

**Decision**: Layer 4 unit coverage under `tests/speckit-pro/unit/` for every
new module, registered in `tests/speckit-pro/suite-manifest.json`, verified with
`python3 tests/speckit-pro/run-all.py`. Zero live calls in the default suite.
Live collection and the calibration pilot are operator-only commands.

**Rationale**: Constitution principle IV requires Layer 4 coverage for all new
Python helpers and gates, and principle I requires repository-only tests live
under the top-level test tree. The suite manifest is the declared source of
truth for layer membership and dispatch. Baseline is green at 3251/3251; the
completion bar is that number plus the new tests, still green, still zero live
calls (SC-019).

---

## Resolved Technical Context

| Item | Resolution |
|---|---|
| Language/Version | Python 3.11+, standard library only |
| Primary dependencies | None added. Consumes the existing CAR-002 module chain |
| Storage | JSON documents on disk, digest-addressed; operator-only retention store for raw captures |
| Testing | `python3 tests/speckit-pro/run-all.py` (Layers 1, 4, 5), zero live calls |
| Target platform | Claude Code CLI on macOS/Linux/Windows; CI on Linux |
| Project type | Plugin source plus repository-only validation harness |
| Performance goals | None. Determinism and replayability are the operative properties |
| Constraints | No Bash, no `jq`, no external evaluation framework, no second materializer, no API-key requirement |
| Scale/Scope | 12 governed roles, 8 Pareto dimensions, 5-rung effort ladder, 3 review slices |
