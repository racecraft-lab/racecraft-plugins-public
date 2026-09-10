# Selected formal checkpoints

This contract is shared by Claude and Codex. Formal methods are independent of
PROJECT_COMMANDS and its three quality slots. Use the existing runner envelope
and the bound WORKFLOW_ROOT for every request, path, agent, and commit.

## Selection and preflight

Read the workflow's single `## Formal Methods` JSON block. `none`, `deferred`,
and absent legacy selection activate no checks or runtime prerequisites. Keep
the rationale. A malformed explicit selection blocks; never replace it with none.
The `.specify/formal-methods.json` catalog alone does not activate a model.

Invoke `formal-doctor` in `read_only` mode with `repo_root: WORKFLOW_ROOT` and
`workflow_file: WORKFLOW_FILE`. It inspects selected tools and files only.
`pending_authoring` for a new model may continue through Specify/Clarify/Plan;
missing existing inputs, invalid configuration, or missing tools are setup gaps.
Explain the precise gap using the [coach guide](../../speckit-coach/references/formal-methods-guide.md)
and stop at a resumable checkpoint. Installation requires operator authorization.
Do not run Grill Me in autopilot; use its existing Clarify/consensus flow.

When an explicitly selected catalog model uses `language: quint`, the same
preflight, authoring, freshness, resume, and final/Post checkpoints apply. Read
the [Quint guide](../../speckit-coach/references/quint-guide.md), reuse its pinned
upstream authoring guidance on demand, and inspect both the compiler and Apalache.
The parent supplies scoped guidance to the bounded author; do not activate a
second upstream orchestrator or infer selection from installed skills.

## Plan authoring checkpoint

After the ordinary Plan executor returns, keep Plan/G3 incomplete while selection
is enabled. The phase executor retains its single-command contract. The parent:

1. Revalidates workflow binding and loads spec.md, plan.md, the approved selection,
   existing selected models, and catalog settings.
2. Dispatches `formal-model-author` for each selected behavior, with explicit
   permitted outputs: new `formal/<id>/` model/configuration/contract files or
   declared existing inputs, plus that model's catalog entry. Supply the approved
   requirements, assumptions, property mapping, and requested evidence level.
   Claude uses its installed `speckit-pro:formal-model-author` agent; Codex uses
   the installed custom `formal-model-author` role with `spawn_agent`. Wait for
   its completed result. If unavailable, stop and repair the agent installation.
3. Reviews the returned paths and requirement mapping, refreshes `formal-doctor`,
   then previews and executes `formal-check`. Both distributions use this request:

   ```json
   {
     "schema_version": "1.0",
     "helper_id": "formal-check",
     "operation": "formal-check",
     "mode": "dry_run",
     "inputs": {
       "repo_root": "<WORKFLOW_ROOT>",
       "workflow_file": "<WORKFLOW_FILE>",
       "spec_file": "specs/<feature>/spec.md",
       "plan_file": "specs/<feature>/plan.md",
       "checkpoint": "plan",
       "state_file": "<workflow-directory>/autopilot-state.json"
     }
   }
   ```

   Review `data.commands`, then repeat with `mode: apply`. Neither mode installs
   tools. `data.verdict: pass` is required; `ready`, `preview`, type-check success,
   partial induction, missing tools, and inconclusive results are not passes.
4. On an authoring error, give the diagnostic to the author for a bounded repair.
   On a design violation, reconcile through the approved requirements and existing
   consensus flow. Never silently weaken properties, strengthen assumptions,
   reduce bounds/coverage, or add a waiver to get green. After two unsuccessful
   repair attempts, stop with the counterexample and the unresolved decision.
5. Pass `workflow_file` to `validate-gate` G3 so its read-only check verifies the
   current record. Only then mark Plan/G3 complete in the workflow and state.
   Supply the existing `state_file` beside the workflow. The helper mirrors the
   selection and checkpoint verdict, fingerprint, and evidence path under
   `formal_checkpoints`; the workflow is authoritative. A failed or interrupted
   state write remains incomplete until the check and coverage validation rerun.

## Commit and resume

`formal-check` writes compact records under `.specify/formal-evidence/` and
updates the workflow's Formal Checkpoints table. It emits `data.commit_paths`.
Stage those exact declared paths in addition to the normal planning commit paths,
after checking ownership; include the model, native config, imports, property
contract, catalog and compact evidence. Do not use broad `git add -A` to collect
planning changes. Raw `.specify/formal-runs/` output is ignored automatically.

On resume, use `resolve-autopilot-stage` before phase work. It verifies the
selection and current evidence from WORKFLOW_ROOT. A missing or stale selected
checkpoint resolves to Plan; explicit implementation or later-phase entry stops
with `--stage plan --from-phase plan`. Resume unfinished authoring/check work
without repeating a normal Plan prompt whose completed result is already durable.
Never treat a completed table row alone as current evidence.

Confidence overrides and generic `skip-and-log` cannot waive a formal checkpoint.
An operator waiver must be explicit and recorded separately; it is not a pass.
After Checklist, Analyze, or review changes to spec/plan/model inputs, reconcile
and renew evidence before Tasks or the planning boundary. See the lifecycle
checks in this release's acceptance record for the qualified resume cases.

## Later planning, implementation, and closeout

Before Tasks and again after Analyze or planning review remediation, use the
same author/review/check sequence with `checkpoint: planning`. Do this even if
the original Plan row passed. The newest Plan or planning record controls resume;
an interrupted newer record cannot fall back to an older success. Retain the
seven-phase order and the ordinary executors' command contracts.

Tasks must map selected properties to implementation obligations. During Plan,
declare the exact relevant source, tests, configuration, and adapter paths in
each model's `implementation_inputs`, including planned files. Review that scope
against the implementation before closeout. A planned file may be absent during
planning; every declared file must exist for final and Post verification.
Planning fingerprints exclude implementation file contents. Final/Post
fingerprints include them, so relevant implementation edits invalidate results.

For G5 and G6, supply `workflow_file` to `validate-gate`. Before implementation
entry and the planning-stage commit, run the existing coverage validator; it
checks current formal evidence and its durable state mirror. No confidence or
generic failure override can bypass this requirement.

After final implementation tests, run `formal-check` with `checkpoint: final`,
then `validate-gate` G7 with `workflow_file`. After the Post Integration Suite's
tests finish, run `checkpoint: post` before that item can complete. Both calls
include `state_file`. A selected formal failure is blocking even when other
Post extension failures are advisory. Repeat affected checks after review fixes;
reconcile planning evidence first if a requirement, plan, model, or catalog
changed. Preserve every returned `commit_paths` alongside normal bookkeeping.

For `model_and_trace`, Tasks must include a tested ITF emitter and action/state
projection, capture before/after source bindings, and run its producing tests
before each final/Post check. Follow
[implementation-traces.md](../../speckit-coach/references/implementation-traces.md).
Review the preview's `trace_checks` as well as native model commands. Missing,
stale, malformed, mismatched, and illegal-transition traces block closeout.
Report observed conformance separately from model and implementation test results.

## Explicit operator waiver

An operator may explicitly waive one current checkpoint. Record their actual
decision and its chat/issue reference; never invent approval. Add this object
to the same preview/apply `formal-check` request:

```json
"waiver": {
  "operator_confirmed": true,
  "approved_by": "<operator>",
  "reason": "<accepted limitation and why>",
  "approval_reference": "<actual decision reference>"
}
```

The helper stores `<checkpoint>-waiver.json` separately from checker results,
reports `waived`, and binds it to the current selection, engine, catalog and
inputs. It can waive a missing runtime after the catalog and selected files are
complete. Changed inputs invalidate it. A new check supersedes an older waiver;
use a fresh explicit decision if the operator intends to waive that new result.
Include waivers as limitations in handoff and PR evidence; never count them as
successful model checks. Other checkpoints remain independently required.

## Model catalog

The [catalog schema](../../../speckit_pro_runner/contracts/formal-methods.schema.json)
owns the format. Each selected model declares its module/configuration/imports,
property-to-requirement mapping, assumptions, native Init/Next, search mode and
bounds, and time/output budget. Use local TLA+ operator names; define a local
alias when a property originates in an instantiated module.

Apalache `bounded` and `temporal` use an explicit `bounds.length`. `inductive`
uses `bounds.inductive_invariant` and runs all three obligations: initial states
satisfy the strengthening predicate; one Next step preserves it; the predicate
implies every requested safety property. Report these obligations and assumptions
explicitly. The strengthening must initialize every state variable using supported
assignments, commonly `TypeOK /\ IndInv`; a bare inequality is insufficient as Init.
Apalache configuration must use explicit `INIT` and `NEXT` matching
the catalog. Its `SPECIFICATION` handling can override induction initialization
and ignore fairness, so this integration rejects it. Put all selected properties
in the catalog; any native property list must agree. Unsupported configuration
directives are setup gaps, never silently dropped options.

Apalache checks the explicitly selected Next relation. Include stuttering in
that relation when intended. Its temporal mode searches bounded lassos; it does
not establish an unbounded liveness proof. Native `WF_`/`SF_` and `ENABLED` are
unsupported in the qualified profile; use TLC for those models. Encode only
approved assumptions using supported formulas, and explain their limits.
No mode substitutes type checking for a completed model check.

TLC `finite` and `temporal` use `bounds.max_set_size` and explore the complete
configured finite state space within the time/memory budgets. Catalog
`specification` replaces `init`/`next` when native SPECIFICATION is selected;
fairness remains in the original TLA+ definition. Native property lists must
exactly match the catalog. Temporal symmetry reduction is outside the qualified
profile. Simulation and zero-initial-state runs cannot pass. Follow the coach's
`references/tlc-guide.md` for a first progress check and its interpretation.

The catalog's tool entry pins the jar SHA256 and exact version, names Java, and
sets its heap budget. Official distributions are preferred. Inputs are copied
into an isolated run directory before checking; undeclared local modules are
unavailable there. Keep model behavior pure and all imported/data files declared.

Final and Post checks run after implementation tests. Use `checkpoint: final`
and `checkpoint: post`; when `model_and_trace` is selected, model success alone
cannot satisfy these checkpoints. Tasks must include the selected model's
implementation obligations and, when requested, trace emitters and adapters.
