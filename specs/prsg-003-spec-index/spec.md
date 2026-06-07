# Feature Specification: Generated index/PRs/backlinks + status integration + phase-gate regen

**Feature Branch**: `prsg-003-spec-index`

**Created**: 2026-06-06

**Status**: Draft

**Input**: User description: "Generated index/PRs/backlinks + status integration + phase-gate regen (PRSG-003)"

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
-->

### User Story 1 - Trustworthy generated navigation zones (Priority: P1)

The navigation maps shipped earlier are static Markdown shapes with no engine
behind them: any "generated" block can silently fall out of sync with the source
tree and present stale links as if they were current — the top risk in the
PR-size-governance roadmap. A maintainer needs a deterministic generator that
rebuilds three clearly-bounded zones inside each spec's map-of-content note from
the committed source tree, so the maps cannot silently lie. The three zones are:
an **index** (roadmap → spec maps), a **pull-requests** zone (slice → PR number →
merged commit), and a **backlinks** zone (a per-spec reachability list of that
spec's own artifacts). Rebuilding always replaces the whole zone between its
markers; partial in-place edits are forbidden because a half-updated zone is the
exact failure mode being eliminated.

**Why this priority**: This is the core engine. Without it there is nothing to
wire into status or the autopilot, and the earlier deferral ("non-map documents
become reachable from the map once this lands") stays open. It delivers value on
its own: running the generator produces real, correct reachability content for
the repository's existing version-marked spec maps.

**Independent Test**: Run the generator against the repository's spec maps and
confirm each zone is rebuilt between its marker pair, the content is correct and
ordered canonically, and a second run with no source change produces a
byte-identical file (zero diff). Fully testable without any status or autopilot
wiring.

**Acceptance Scenarios**:

1. **Given** a version-marked spec map that already contains the three empty
   marker-bounded zones, **When** the generator runs in write mode, **Then** each
   zone's body is replaced with content derived from that spec's tree and the
   bytes outside every marker pair are unchanged.
2. **Given** the generator has just produced a spec map, **When** the generator
   runs again with no change to any source file, **Then** the output is
   byte-identical to the prior run (zero diff).
3. **Given** a spec map that is missing one or more of the marker-bounded zones,
   **When** the generator runs, **Then** the missing zones are inserted exactly
   once at the fixed anchor and then filled, and a spec map that lacks the
   version marker is left untouched.
4. **Given** a spec map missing one marker pair (for example, only the index
   markers are absent), **When** the generator runs, **Then** that one zone is
   skipped and the other present zones are still rebuilt.
5. **Given** two specs with map notes, **When** any cross-spec list is rendered,
   **Then** entries appear in canonical normalized-identifier order and a spec's
   own reachability list follows the fixed artifact precedence
   (spec → plan → tasks → data-model → research → contracts → checklists →
   process exhaust) then path order, independent of filesystem enumeration order.

---

### User Story 2 - Staleness is caught read-only; freshness is enforced at phase gates (Priority: P1)

A maintainer reading the status dashboard must be able to trust that the
committed maps are current, and the autonomous workflow must keep them current as
it advances. The status dashboard invokes the generator in a read-only check
mode: it rebuilds the zones in memory, diffs them against what is committed, and
reports "index stale" when they differ — writing nothing, preserving its
read-only contract. The autonomous workflow is the single authoritative writer:
at every phase boundary it rebuilds the zones and folds the result into its
existing checkpoint commit, but only when the diff is non-empty.

**Why this priority**: Wiring is what makes the engine matter day to day. The
read-only check closes the silent-stale-index risk for anyone running status
outside a workflow cycle; the phase-gate rebuild guarantees the committed maps
are never stale by the time work merges. Both are needed for the engine to be
trustworthy in practice.

**Independent Test**: Hand-edit a source artifact so the committed map goes
stale, run the status check, and confirm it reports staleness and writes nothing;
then run a phase boundary and confirm the maps are rebuilt and committed only
because the diff was non-empty. A no-op phase boundary (nothing changed) produces
no commit.

**Acceptance Scenarios**:

1. **Given** a committed map that matches the current source tree, **When** the
   status check runs, **Then** it reports the index as current and no file on
   disk is modified.
2. **Given** a source artifact was changed so the committed map is now stale,
   **When** the status check runs, **Then** it reports the index as stale with an
   actionable "run regen" message and still writes nothing.
3. **Given** the autonomous workflow reaches a phase boundary and the rebuild
   yields a non-empty diff, **When** the phase-gate step runs, **Then** the
   rebuilt maps are committed as part of the checkpoint with a fixed commit
   message.
4. **Given** the autonomous workflow reaches a phase boundary and the rebuild
   yields no diff, **When** the phase-gate step runs, **Then** nothing is
   committed for the rebuild.

---

### Edge Cases

- A spec directory whose map note carries no version marker and no zones is
  skipped silently (consistent with "no marker → exempt").
- The pull-requests source data is absent or empty: the zone renders as an
  empty-but-valid zone, not an error.
- The pull-requests source data is present but malformed or unreadable (distinct
  from absent/empty): the generator fails safe with an actionable message and a
  non-success result, and MUST NOT partially write or corrupt the target — the
  same fail-safe contract as a malformed map note, never conflated with the
  absent/empty empty-but-valid case.
- A source map note is malformed or unreadable: the generator fails safe with an
  actionable message and a non-zero exit, and the check mode never writes even on
  this error path.
- A target that is not a regular file (for example, a directory or symlink where
  a map note is expected) is rejected rather than written through.
- A zone's marker pair is unbalanced or ill-formed (a start marker without its
  matching end marker, or the reverse, or a duplicated or out-of-order pair within
  one map note): this is the malformed-target fail-safe case (actionable message,
  non-success result, no partial write — FR-022/FR-016), distinct from an
  *entirely missing* (absent) marker pair, which simply skips that one zone while
  other present zones are still rebuilt (FR-009).
- An unexpected internal or operational failure mid-run (one the generator did
  not explicitly anticipate) surfaces as the error result, never as the benign
  "stale" / content-difference result, so a real failure is never mistaken for "the
  maps merely need a regen" (FR-021).
- No in-scope (version-marked) specs are discovered at all (an empty tree, or a
  repository with only legacy non-marked specs): this is a clean no-op success, not
  an error — the generator reports nothing to do, modifies zero files, and succeeds
  offline.
- The roadmap-level index zone has no home note in this repository yet: the index
  path is exercised by fixtures but renders nothing live here (dormant until a
  later spec supplies the home note).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a single generator that rebuilds three
  independently-bounded generated zones — an index zone, a pull-requests zone, and
  a backlinks zone — each delimited by its own start/end marker pair inside a
  spec's map-of-content note.
- **FR-002**: The generator MUST always replace the entire body between a zone's
  start and end markers and MUST NOT perform partial in-place patching of zone
  content.
- **FR-003**: The generator MUST be deterministic: given the same committed
  repository inputs it MUST produce byte-identical output, and re-running it with
  no source change MUST produce a zero-byte diff.
- **FR-004**: The generator MUST reuse the project's existing canonical
  identifier-normalization join for every cross-spec identifier match; it MUST NOT
  introduce a second normalization implementation.
- **FR-005**: Cross-spec lists MUST be ordered by the normalized identifier
  ascending, and a spec's own reachability list MUST follow a fixed artifact
  precedence (spec, then plan, then tasks, then data-model, then research, then
  contracts, then checklists, then the spec's process exhaust) followed by
  path order, so ordering is independent of filesystem enumeration order.
- **FR-006**: The backlinks zone MUST render, for each in-scope spec, a
  reachability list of that spec's own artifacts as relative links covering the
  files within that spec's directory tree (including its process subtree), so
  every non-map document in the spec is reachable from the spec's map note.
- **FR-007**: The generator MUST discover only specs whose directory already
  contains a version-marked map note; specs lacking such a map note MUST be
  skipped and left unmodified.
- **FR-008**: The generator MUST insert the three empty generated zones at a
  fixed anchor into any in-scope version-marked map note that is missing them, do
  so exactly once, and then fill them; this injection MUST be idempotent across
  repeated runs. The injection MUST use the same fixed anchor and the same zone
  order used by the template (FR-017), so a template-born map and an
  injection-migrated map are byte-identical.
- **FR-009**: A map note that is missing an individual zone's marker pair MUST
  have that single zone skipped while any other present zones are still rebuilt.
- **FR-010**: The pull-requests zone MUST be rendered only from a repository-local
  committed data source; the generator MUST NOT contact any external service or
  network at generation time to populate it.
- **FR-011**: When the repository-local pull-requests data is absent or empty, the
  generator MUST render an empty-but-valid pull-requests zone rather than failing.
- **FR-012**: The system MUST expose a read-only check mode that rebuilds the
  zones in memory, compares them against the committed map notes, reports whether
  each is current or stale, and writes nothing to disk — including on error paths.
- **FR-013**: The status dashboard MUST invoke the generator in read-only check
  mode and surface an actionable "index stale — run regen" indication when the
  committed maps differ from a fresh rebuild, while making no file modifications.
- **FR-014**: The autonomous workflow MUST run the rebuild as an idempotent
  step at every phase boundary and MUST commit the rebuilt maps — folded into its
  existing checkpoint commit with a fixed commit message — only when the rebuild
  diff is non-empty.
- **FR-015**: The generator MUST expose a distinguishable result for each of the
  three outcomes — current, stale, and error — so the status dashboard and the
  workflow phase-gate step can act on them unambiguously.
- **FR-016**: On a malformed or unreadable target, the generator MUST fail safe
  with an actionable message and a non-success result, and MUST NOT partially
  write or corrupt the target. The no-partial-write guarantee MUST hold even when
  a write fails partway through: a write that cannot complete MUST leave the
  target either fully updated or wholly unchanged — never a half-written or
  corrupted map note (a half-updated zone is the exact failure mode being
  eliminated, FR-002). This atomicity MUST hold per target across a multi-map
  run, so a failure writing one spec's map note cannot leave any other spec's map
  note half-written. The "actionable message" MUST name the offending file and
  the failure class so the outcome is objectively diagnosable, not a bare adjective.
- **FR-017**: The spec map template used to scaffold new specs MUST include the
  three empty generated zones at the fixed anchor, so newly created specs are born
  with the zones present. The template MUST place them at the same fixed anchor and
  in the same zone order used by FR-008's inject-if-missing path, so template-born
  and injection-migrated spec maps are byte-identical.
- **FR-018**: The generator's per-spec reachability enumeration MUST be bounded to
  that spec's own directory tree (including its process subtree) and MUST NOT reach
  into any other tree.
- **FR-019**: The roadmap-level index path MUST be present and exercised by
  fixtures but remain dormant in this repository — rendering nothing live until a
  separate, later deliverable supplies the roadmap home note that carries the
  index markers; no change to this feature is required for that activation.
- **FR-020**: Any change made to a skill's behavior description that has a mirrored
  counterpart for the alternate coding-agent runtime MUST be reflected in that
  mirror so the two stay in parity, while the generator itself remains a single
  shared implementation referenced by path rather than duplicated.
- **FR-021**: An unexpected internal or operational failure during a run (a fault
  the generator did not explicitly anticipate) MUST surface as the error result
  (the same non-success outcome as a malformed target, FR-016) and MUST NOT be
  reported as the benign "stale" / content-difference result. The error outcome
  and the stale outcome are never conflated: a real failure must never be
  mistaken for "the committed maps merely need a regen", because the status
  dashboard and the workflow phase gate act differently on each (FR-013/FR-014).
- **FR-022**: A zone whose marker pair is unbalanced or ill-formed — a start
  marker present without its matching end marker (or the reverse), or a
  duplicated or out-of-order pair within one map note — MUST be treated as the
  malformed-target fail-safe case (FR-016): the generator stops with an
  actionable message and a non-success result and MUST NOT partially write or
  corrupt the target. This is distinct from FR-009's *missing* (entirely absent)
  marker pair, where neither marker is present and that one zone is simply
  skipped while other present zones are still rebuilt.

### Reviewability Budget *(mandatory)*

<!--
  ACTION REQUIRED: Declare the expected review surface before planning.
-->

- **Primary surface**: harness/adapter (a shell generator script plus its
  determinism and unit fixtures)
- **Secondary surfaces, if any**: docs/process (the spec-map template's added
  zones and the two skill behavior descriptions, with their alternate-runtime
  mirrors)
- **Projected reviewable LOC**: ~350 production lines (shell + jq), plus test
  fixtures
- **Projected production files**: ~5 (one new generator script; edits to the
  spec-map template, two skill descriptions, and their mirrors)
- **Projected total files**: ~10 (production files plus the determinism fixture
  and unit tests)
- **Budget result**: within budget
- **Split decision**: Remains one spec. The generator and its two consumers form
  a single cohesive engine; the index and pull-requests population paths that
  would enlarge this are explicitly deferred to separate downstream specs, keeping
  this slice bounded.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope
  budget, traceability, verification evidence, known gaps, and rollback or
  feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue (roadmap-level index
  population; live pull-request/commit population; legacy-spec backfill).

### Key Entities *(include if feature involves data)*

- **Generated zone**: A region inside a spec's map note bounded by a dedicated
  start/end marker pair. Three kinds exist — index, pull-requests, backlinks —
  each independently positioned and wholly replaced on each rebuild.
- **Spec map note**: The per-spec map-of-content note that hosts the generated
  zones. Only version-marked map notes are in scope; the generator may inject the
  empty zones into one that lacks them.
- **Reachability entry**: A relative link from a spec's map note to one of that
  spec's own artifacts (its specification, plan, tasks, data-model, research,
  contracts, checklists, or process exhaust).
- **Pull-requests record**: A repository-local committed datum mapping a slice to
  a pull-request number and a merged commit, rendered into the pull-requests zone.
  Who writes this datum is out of scope here.
- **Normalized identifier**: The canonical (namespace, number) key produced by the
  reused normalization join, used to order and match specs across the repository.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running the generator twice in a row with no intervening source
  change yields a zero-byte difference on every spec map note (idempotent).
- **SC-002**: For every in-scope spec, 100% of that spec's own artifacts (its
  specification, plan, tasks, data-model, research, contracts, checklists, and
  process exhaust) are reachable as links from its map note's backlinks zone.
- **SC-003**: When a source artifact is changed without regenerating, the status
  dashboard reports the index as stale and modifies zero files on disk.
- **SC-004**: When the maps are current, the status dashboard reports the index as
  current and modifies zero files on disk.
- **SC-005**: A phase boundary with no map-affecting change produces no rebuild
  commit; a phase boundary with a map-affecting change produces exactly one
  rebuild contribution to the checkpoint commit.
- **SC-006**: The generator renders the backlinks zone with real content for the
  repository's existing version-marked spec maps (demonstrated on at least two
  specs), confirming the engine works on this repository and not only on fixtures.
- **SC-007**: Specs lacking a version-marked map note are unchanged by any run
  (zero modifications), and a map note missing only one zone's markers still has
  its other zones rebuilt.
- **SC-008**: The generator completes with no external-service or network access
  during generation, so it succeeds offline.
- **SC-009**: Zone ordering is identical when the generator runs on two machines
  with different filesystem enumeration orders (byte-identical output).
- **SC-010**: The two mirrored skill behavior descriptions remain in parity after
  the change (their parity check passes). Parity is verified by the structural
  Codex-skill checks (`validate-codex-skills.sh` + `validate-codex-parity.sh`) —
  presence/structure, not byte-identity: each Codex mirror describes the same new
  behavior in Codex-native framing and MUST NOT carry Claude-only frontmatter keys
  (`argument-hint`, `user-invocable`, `license`, `disable-model-invocation`).
- **SC-011**: After the generator writes the dogfooded version-marked spec maps,
  the project's existing orphan and stale-index map-note lints pass on those real
  maps (zero new lint failures introduced by the generated zones) — confirming the
  generated content keeps the navigation layer's integrity guarantees green, not
  only on fixtures.
- **SC-012**: Running the generator against a tree with no in-scope (version-marked)
  specs — an empty tree, or one holding only legacy non-marked specs — succeeds as
  a clean no-op: it returns the success result, modifies zero files on disk, and
  completes offline. A malformed or unreadable input, by contrast, returns the
  error result with a non-success exit and still writes zero files; the success
  no-op and the error outcome are never conflated.

## Assumptions

<!--
  Reasonable defaults and design-concept-routed deferrals recorded here so no
  open clarification markers remain. The three items the design concept routed
  to later phases (rather than to clarification) are documented as deferrals
  below with their routing, so the after-Specify gate stays clean.
-->

- **Zone markers are invisible in the rendered document.** The three zones are
  bounded by start/end marker pairs that do not show up when the Markdown is
  rendered, are independently positionable, and are easy to search for. The exact
  marker text is a settled design choice defined in one place; its precise
  spelling is finalized during planning.
- **Zone anchor position (default; finalized in Plan).** There is one canonical
  anchor and one fixed zone order, used identically by the template (FR-017) and
  the generator's inject-if-missing path (FR-008) — this shared placement is what
  keeps template-born and injection-migrated maps byte-identical (SC-001/SC-009).
  The default position is the end of the map note body, immediately after the
  introductory paragraph; the exact byte position is finalized during planning.
- **Pull-requests data source shape (deferred to Plan).** The exact shape of the
  repository-local committed source for slice → PR number → merged commit (a
  dedicated process-tree manifest versus data carried in the map note body) is a
  deliberate deferral, not an open question: this feature only needs a
  deterministic, fixture-testable input contract, and the writer that populates it
  belongs to a separate downstream spec. The minimal input contract is pinned
  during planning.
- **Roadmap index activation timing (deferred to a downstream spec).** Whether and
  when the roadmap-level index zone renders live is deferred by design: the
  roadmap home note that would carry the index markers is a separate downstream
  deliverable. Here the index path is built and fixture-tested but dormant, and no
  change to this feature is needed for it to begin filling later.
- **Fixed commit message wording (deferred to Plan).** The exact fixed commit
  message used by the workflow's commit-on-diff rebuild step is cosmetic and is
  finalized during planning against the existing checkpoint-commit convention, so
  it reads cleanly as a public commit subject.
- **Single shared generator.** The generator is one shared implementation
  referenced by absolute path from both consumers (the status dashboard and the
  autonomous workflow) and their alternate-runtime mirrors; only the skill
  behavior descriptions are mirrored, never the script.
- **Alternate-runtime parity bar is the structural skill check, not the
  teams-vs-subagents parity harness.** The PR-size-governance roadmap's per-spec
  coverage table lists the multi-path parity harness for this spec, but that
  harness verifies Agent-Teams-vs-parallel-subagents runtime equivalence for the
  post-implementation parallel group — a concern introduced by a later spec, not
  touched here. This feature's alternate-runtime surface is prose-only (the two
  mirrored skill descriptions), verified by the structural skill checks named in
  SC-010; because the generator is one shared script referenced by path, there is
  no second execution path to compare. The roadmap's parity-harness entry for this
  spec does not apply; any such work is deferred to the multi-path spec.
- **Scope is plugin behavior and a shared script only.** No end-user product code
  is involved; this feature changes plugin-skill behavior plus one shared script
  and its tests.
- **The "no marker → exempt" contract is authoritative.** Legacy specs without a
  version-marked map note are intentionally out of scope and are never reached
  into or modified.
- **This spec's own directory will gain a version-marked map note in a later
  phase.** Because this run creates a brand-new spec directory and the generator
  must dogfood on the repository's real spec maps, this spec's own directory is
  expected to carry a version-marked map note (with a valid relative upward link
  and a spec identifier matching the directory) created in a later phase. This is
  an expected outcome of the feature, not out of scope, and the map note is not
  created during specification.
