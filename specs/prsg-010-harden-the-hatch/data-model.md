# Data Model: PRSG-010 Harden the Hatch + O5 Monster Epics

## Final Gate Result

Fields:

- `status`: `pass`, `warn`, `exception`, `block`, or `error`
- `gate_result`: raw reviewability decision name
- `gate_reason`: stable human-readable reason
- `metrics`: review surface counts, threshold values, and projected/actual LOC
- `exception`: exception evaluation summary
- `blocked_operations`: ordered list of operations that did not run
- `timestamp`: UTC ISO-8601 timestamp
- `pr_created`: always `false` on unexcepted block or gate error
- `pr`: always `null` on unexcepted block or gate error
- `reslicing_packet_path`: repo-relative path to the recovery packet, or `null`
  for pass/warn/exception/error states

Validation rules:

- `block` without honored exception must set `pr_created: false`, `pr: null`,
  `exception.honored: false`, all skipped PR operations in `blocked_operations`,
  and a non-null `reslicing_packet_path`.
- `error` must set `pr_created: false`, `pr: null`, `exception.honored: false`,
  and must not create a re-slicing packet.
- `exception` must set `exception.honored: true`, record the accepted class and
  line-anchored evidence, and may proceed to PR preparation.
- `pass` and `warn` may proceed to PR preparation without exception evidence.

State transitions:

`verification_complete -> final_gate_running -> pass_or_warn_or_exception -> pr_preparation`

`verification_complete -> final_gate_running -> block -> reslicing_required`

`verification_complete -> final_gate_running -> error -> gate_error`

## Reviewability Exception

Fields:

- `class`: `refactor`, `infra`, or `upgrade`
- `path`: repo-relative Markdown artifact path
- `line`: 1-based line number
- `provenance`: `contract`, `generated`, `process`, `template`,
  `pr-description`, `commit-message`, `code-fence`, or `unknown`
- `branch_added`: boolean
- `honored`: boolean
- `reason`: accepted or rejected reason

Validation rules:

- Honored exceptions must be branch-added, line-anchored, case-sensitive, and
  located in committed review-visible non-generated CONTRACT Markdown.
- Generated, process, template, PR-description, commit-message, code-fence, or
  mutable provenance is rejected.
- Invalid class, mixed casing, and trailing prose are rejected.

## Re-slicing Packet

Fields:

- `schemaVersion`: `1`
- `kind`: `final_reviewability_reslicing_packet`
- `feature`: branch, feature directory, spec ID, and title
- `diff`: base/head refs, changed file counts, and gate input summary
- `gate`: raw gate status, reason, thresholds, and metrics
- `exceptions`: accepted and rejected exception evidence arrays
- `blocked_operations`: no-PR assertions and skipped operation names
- `sizing`: PRSG-007 routing and sizing source, route, thresholds, and summary
- `layer_plan`: PRSG-008 layer-plan availability, status, path, and slice count
- `handoff`: PRSG-009 command template and concrete required input paths
- `suggested_slice_boundaries`: ordered slice suggestions
- `operator_steps`: ordered concrete steps for the blocked operator, each with
  PRSG phase, command template, required paths, when to use it, and expected
  unblock condition
- `resume`: human-readable and machine-readable next action fields

Validation rules:

- `blocked_operations` must include PR body generation, single PR creation, and
  multi-PR emission when those operations were skipped.
- `no_pr_assertions` must keep `pr_created`, PR body generation, all
  `gh pr create` variants, and multi-PR emission false.
- `sizing`, `layer_plan`, and `handoff` must contain enough machine-readable
  PRSG-007/008/009 context to resume at re-routing or layer-plan regeneration
  without reconstructing prior workflow state from prose.
- `operator_steps` must give a concrete command/path sequence and must make the
  `resume.resume_from` choice understandable from packet evidence: rerun
  PRSG-007 when route or sizing evidence is missing/stale, regenerate PRSG-008
  when the layer plan is missing/invalid/stale, and hand off to PRSG-009 when
  route and layer-plan evidence are valid but PR emission remains blocked.
- Packet must be valid JSON and stable enough for status/resume reads.

## O5 Parent Manifest

Fields:

- `schemaVersion`: `1`
- `kind`: `o5_parent_manifest`
- `parent`: identifier, branch, path, title
- `children`: ordered child entries
- `sharedDesignConcept`: repo-relative path
- `sharedRetrospective`: repo-relative path or `null`
- `declaredRollupStatus`: optional declared status

Child entry fields:

- `id`: child identifier such as `PRSG-010A`
- `branch`: child branch name
- `path`: flat `specs/<child-branch>` path
- `title`: child title
- `dependsOn`: array of child IDs that must appear earlier in the manifest

Validation rules:

- Parent manifest lives at `specs/<parent-branch>/o5-parent-manifest.json`.
- Parent `path` must equal `specs/<parent.branch>`.
- Child `path` must equal `specs/<child.branch>`.
- Branch/path equality is enforced by the topology validator because the JSON
  Schema contract can only enforce the flat path shape.
- Child paths must be flat siblings under `specs/`, not nested below the parent.
- Child IDs are unique.
- Dependencies must refer to known earlier children and must not form cycles.
- Zero-child manifests are invalid.

## O5 Child Spec

Fields:

- `id`: child identifier
- `path`: flat spec directory
- `parentManifest`: link to the parent manifest
- `sharedDesignConcept`: inherited or explicit link
- `sharedRetrospective`: inherited or explicit nullable link
- `up`: existing roadmap/MOC pointer

Validation rules:

- Child `SPEC-MOC.md` body links must include the parent manifest.
- `up:` remains pointed at the roadmap, not the parent directory.
- Generated `SPEC-MOC.md` zones remain owned by `generate-spec-index.sh`; O5
  scaffold and status logic may update curated links, but must not hand-patch
  generated backlink or index zones.
- Child specs proceed through normal SpecKit phases.

## O5 Status Rollup

Fields:

- `topologyStatus`: `valid` or `invalid`
- `computedStatus`: `invalid_topology`, `blocked`, `failed`, `in_progress`,
  `pending`, or `complete`
- `children`: ordered child state rows
- `declaredStatusDrift`: boolean
- `problems`: actionable topology or drift diagnostics

Validation rules:

- Topology is validated before child status computation.
- Child state is computed in manifest child order.
- The `children` array must contain exactly one row for every declared child,
  including failed, pending, blocked, archived, and missing-state children.
- Optional declared rollup status is drift-checked only; it is never the source
  of truth.

## Contextual Probe Evidence

Fields:

- `probe`: `flag-system`, `release-cadence`, or `consumer-locality`
- `strength`: `high`, `weak`, or `conflict`
- `evidence`: deterministic file/task observations
- `decisiveSignal`: nullable signal token
- `hint`: nullable hint token
- `reason`: stable explanation

Validation rules:

- Flag-system evidence is high confidence only with a repo-local flag or
  evaluation mechanism plus current guard and test tasks.
- Release-cadence evidence is high confidence only for no-flag release-held
  cutovers with concrete release-cadence and release-hold evidence.
- Consumer-locality evidence can emit branch-by-abstraction only when all
  affected consumers are in-tree, old and new behavior can coexist, migration
  and contract tasks are complete, and no hard-atomic or release risk applies.
- Branch-by-abstraction emits `context:consumer-locality:all-in-tree` and
  `strategy:branch-by-abstraction`; proven out-of-tree consumers emit
  `context:consumer-locality:out-of-tree` and keep the router conservative.
- Weak, stale, ambiguous, fixture-only, code-fence-only, or conflicting
  evidence never enters `signals[]`.

## Routing Decision

Fields:

- `route`: `split-PR`, `one-navigable-PR`, `single-atomic-PR`,
  `out-of-scope`, or `branch-by-abstraction`
- `releasable`: boolean
- `signals`: closed enum decisive tokens
- `hints`: closed enum advisory tokens
- `warnings`: closed enum warning strings

Validation rules:

- Hard-atomic and releasability precedence remains above contextual probes.
- `context:flag-system:guarded-cutover` routes non-hard-atomic guarded cutovers
  to `one-navigable-PR` unless independent additive multi-seam evidence proves
  `split-PR`.
- `context:release-cadence:release-held-cutover` routes no-flag release-held
  cutovers to `single-atomic-PR` without automatically setting
  `releasable: false`.
- Weak contextual evidence appears only as a closed-enum hint.
