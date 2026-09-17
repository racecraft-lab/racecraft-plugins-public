# Full-autopilot performance benchmark fixtures

These are frozen public workload inputs and acceptance references, **not completed
benchmarks**. No provider run is authorized by this directory. The manifest's
pending state is deliberate; a green fixture test proves byte integrity and
reference coverage, not runtime performance, behavioral equivalence, or UAT.

## Frozen inputs and separation

- Use the manifest's exact scaffold commit and tree for each workload checkout.
  Do not use the current, already-implemented repository as the workload.
- Install the baseline harness from `42f4afe5bd2a319f81ea4b28799ec13bfa8e6107`
  outside the workload checkout. Install the candidate from a separately frozen,
  qualified final commit outside its own matched workload checkout. Freeze both
  installed payload digests. Do not import runner modules or templates from the
  workload when intending to exercise the installed harness.
- This baseline is for **autopilot timing only**. The issue #573 trigger
  experiment has a different controlled comparison: both arms use the final
  trigger harness and differ only in the reviewed pre-#572 no-op description.
- `source/workflow.md` is byte-identical to the scaffold's original prepared
  workflow. Its main phase rows were already pending; no transformation was
  necessary. `source/spec.md`, `plan.md`, `tasks.md`, and required design,
  contract, research, data-model, and quickstart references are final
  pre-implementation planning evidence, not baseline implementation output.
- `prepared-tasks.md` resets only task-checkbox completion from the preserved
  source tasks. ART-007 resets T001–T005 (preflight work); the other two task
  references require no reset. This file is an acceptance reference: **never seed**
  it, the final plan, or historical completed workflow state into the active
  feature directory before generation. The actual Tasks phase must run.
- Provide `kickoff.md`, the original workflow/design concept, and the frozen
  approved specification as scope input. The final plan/tasks/supporting
  contracts are evaluator references. Regenerated artifacts may organize work
  differently, but must preserve every functional requirement, safety boundary,
  verification obligation, and declared exclusion. The reference counts
  14 / 54 / 40 are inventories, not sole correctness tests or required new task
  counts. Compare requirement-to-task-to-evidence coverage independently.

## Pre-implementation evidence

Scaffold-to-final-planning diffs contain planning/process changes, not target
implementation changes. ART-012 and ART-007 changed only their specification
and workflow/roadmap records. DOC-008 additionally appended two informational
technology lines to historical `CLAUDE.md`; that later change is not present in
the scaffold workload. No DOC-008 target docs-page implementation is present.
The manifest records the complete changed-path inventory and representative
absent implementation files. Reconfirm the pinned tree and absent files when
materializing a campaign; these observations do not qualify the environment.

## Provider-free preparation and campaign preflight

`COMMON-TASKS-INPUT.md` supplies one self-contained Tasks-production supplement
for both arms. It requires no candidate-only helper to calculate fingerprints.
Append its exact bytes to each original Tasks prompt in a separate prepared
workflow copy; do not modify the frozen original or seed generated artifacts.
Record the original workflow, scenario kickoff, common supplement, and resulting
prepared-workflow hash in the campaign manifest. Compare prepared copies across
matched arms before launch. The common input is prepared, not native-qualified:
actual baseline producer compatibility and candidate required-metadata validation
remain unproven until exercised through the installed native workflows.

`DEPENDENCY-PINS.json` binds each scaffold's exact docs-site package manifest and
complete lockfile using Git blob IDs, SHA-256, and byte counts. These are locally
verified source pins, **not an environment qualification**. The package-manager
declaration is `pnpm@10.25.0`; the lockfiles declare Astro's Node engine as
`>=22.12.0`, not an exact installed Node pin. ART-012 and ART-007 share identical
dependency input bytes; DOC-008 has an older, different dependency graph. Do not
replace either graph with today's package files or infer a missing dependency
from a newer scenario.

Before an authorized campaign, check out the exact manifest commit/tree and
compare both dependency files against all three recorded byte identities on
both arms. Independently record exact Python/Node/package-manager executables
and versions, OS/architecture, package installation and applicable browser
availability, and the outputs of every required automated prerequisite check.
The declared version constraints are only a lower bound; the complete locked
dependency graph and installed-arm checks may impose additional constraints.
Use each workload's frozen dependency inputs without updates, substitutions, or
skipped checks. Dependency installation is a separate authorized operation;
this provider-free preparation performs none. Missing Git objects, pin drift,
incompatible runtimes, unavailable locked packages, missing browsers, or an
unqualified historical command block the matched pair before launch. Attach
evidence to the campaign, not a success flag to these frozen reference files.

## Qualification before any native run

1. Review a separate campaign manifest and explicit launch budget. The paired
   minimum is **12 full workflow runs**: three scenarios × two native hosts
   (Claude and Codex) × baseline/candidate. Agent launches within a workflow are
   variable and need their own bounded provider budget; 12 is not that budget.
2. Bind candidate commit/payload hashes, baseline payload hashes, exact CLI and
   model/effort pins per host, native dispatcher configuration, credentials
   source identity without secret values, host capacity, installed extensions,
   dependency lockfiles, runtime versions, and allowed tools. Keep these
   identical across matched arms except the reviewed harness change.
3. Qualify each historical workload's prerequisites on both arms. Historical
   commands in references are evidence, not an instruction to add dependencies
   to today's repository. Do not silently modernize a workload, substitute a
   scenario, change effort, skip an unavailable check, or use current source to
   make a historical baseline pass. An unresolved compatibility issue blocks
   that pair and must be reported before launch.
4. Verify clean isolated workload/config/temp/output roots, restore points,
   owned-process cleanup, and permission to perform each external write. A
   campaign involving GitHub must name a disposable approved fork and its
   bounded PR/branch cleanup scope. Never copy authentication files or secrets
   into fixtures or evidence. Do not mutate the public project's PRs while
   qualifying these workloads.
5. Freeze the requirement-coverage rubric before observing candidate results.
   ART-012's FR-006/T014 scope amendment is mandatory at kickoff. ART-007 T052
   remains operator-only and pending; scenarios 1–4 and all other automated
   obligations remain required. General human UAT is also pending until
   actually performed. No human work is relabeled automated to meet a target.
6. Qualify a reviewed **common metadata-producing kickoff input** before
   claiming batching performance. These historical workflows do not request
   `task-execution.v1`; the candidate template does, and the candidate runtime
   preserves legacy behavior when it is absent. Therefore the frozen original
   workflow alone is not a qualified batching benchmark. Freeze identical
   scope-preserving Tasks-production instructions for both arms, prove that the
   baseline can process them without a missing candidate-only helper, and
   require the candidate's actual Tasks output to produce validated metadata
   with `task_execution_required=true`. Preserve the original bytes and record
   every common input normalization and hash in the reviewed campaign. Never
   preseed metadata or silently benchmark candidate legacy dispatches as the
   optimized path. The shared supplement above is the explicit common input
   normalization; its producer/input compatibility qualification is currently
   pending. Preparing its bytes does not establish native qualification.

## Run and record through the existing native autopilot

- Use each host's installed native autopilot and normal dispatch primitives.
  Do not replace the workflow with Python orchestration, direct task execution,
  cached generated planning, or a manually prepared batch dispatch. Exercise
  Specify, Clarify, Plan, Checklist, actual Tasks generation, Analyze,
  implementation, repair, all applicable automated gates, and Post closeout.
- Apply the installed arm's process policy to historical scope: the candidate
  may eliminate redundant checks or test-count-growth incentives only as
  authorized by the approved optimization contract. Functional acceptance,
  security, authorization, final-suite coverage, and artifact checks do not
  disappear because an old workflow or reference omits a newer Post row.
- Start the timer immediately before prepared-workflow kickoff. Use a
  monotonic clock for elapsed intervals plus UTC timestamps for audit. Stop
  only after all required automated phases and final checks complete. Include
  startup, model/tool waits, implementation, repair, tests, generation,
  automated review, and cleanup required by the workflow. Exclude only recorded
  human UAT and external approval wait intervals, with exact start/end evidence.
  A checkpoint, timeout, exhausted budget, invalid result, or skipped required
  work is an incomplete run, never a successful elapsed-time sample.
- Preserve raw event records with run/scenario/host/arm identities, workload and
  harness pins, UTC and monotonic timestamps, phase/task/batch/dispatch IDs,
  event type, outcome, command or tool identity, input/evidence digests, worker
  launches, repair reservations, repeated-check counts, cleanup outcome, and
  available token usage (null when unavailable, never estimated as fact).
  Preserve raw native transcripts and command outputs under the approved
  private evidence root, with an index of containment-safe paths and hashes.
- Produce every reference obligation's result/evidence mapping, not just a
  task-count or `passed: true`. Record partially completed work and operator
  exclusions separately. Freeze publication atomically; interrupted evidence
  publication cannot produce a qualified result.

## Acceptance and reporting

- Report raw elapsed time and completion for all 12 planned runs, including
  failures. Every completed candidate must finish the full automated scope
  below **7200 seconds**. No early-stop result satisfies this target.
- Compute baseline and candidate medians separately for each native host over
  the three completed matched scenarios. The candidate/baseline median ratio
  must be at most **0.5**. An incomplete baseline leaves the relative-speed
  target unmet; do not drop its scenario or use a timeout as completed runtime.
  Three scenarios establish neither percentile reliability nor zero regressions.
- Routine PR feedback below **900 seconds** needs its own declared selection
  scope and measured campaign. A scoped quick result is **not full qualification**
  and these workflow fixtures do not substitute for the dual-host trigger
  matrix or its separate 48-launch concurrency pilot.
- Report dispatches, native launches, repairs, repeated checks, token usage,
  and cleanup beside time. Lower launch counts are not automatically equal
  reductions in token use or billing. Keep remaining UAT, T052, dependency,
  evidence, and acceptance gaps explicit. Leave the fixture manifest pending;
  publish campaign-specific qualification separately instead of rewriting
  reference history into a success claim.
