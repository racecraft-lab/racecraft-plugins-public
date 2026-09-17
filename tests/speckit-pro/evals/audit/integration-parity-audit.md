# Layer 6/7 integration and parity audit

## Decision and qualification boundary

Layer 7 is the automated Claude/Codex parity gate. Each client must first pass
the same requirements independently. Cross-client comparison is additional
evidence and cannot turn two incorrect results into a pass.

Genuine interactive Claude agent-team verification is a separate manual
activity. It is not a pull-request blocker and is not an automated Layer 7
pass. Current Anthropic documentation says `TeamCreate` and `TeamDelete` were
removed in Claude Code v2.1.178, teammate spawning requires an interactive
session, and named agents in `claude -p` or Agent SDK sessions run as ordinary
subagents. Sources: [Anthropic agent teams](https://code.claude.com/docs/en/agent-teams)
and [Anthropic programmatic usage](https://code.claude.com/docs/en/headless).

OpenAI's skill-evaluation guide demonstrates native `codex exec --json` for
capturing execution evidence and a separate `codex exec --output-schema`
invocation for structured grading. This migration follows that native-client
approach, not the generic Evals API: validate inputs, retain native observations,
grade each host, then compare.
Source: [Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills).

This audit revision did not invoke Claude or Codex. That is a statement about
this audit action, not an authorization blocker: the user authorized
implementation and existing quota-backed runs. Read-only checks found Claude
Code 2.1.271 and codex-cli 0.154.0. Those version checks do not qualify
authentication, model identity, allowed-tool enforcement, output schemas, or
nested-agent behavior.

## Exact accounting

### Post integration reuse boundary

The active `parity.01-post-implementation-outcome` case already covers much of
legacy dispatch fixture 18: ordinary worker ownership, nonempty attributed
returns, waiting before the parent serial tail, current reviewability evidence,
and packet generation/validation. It deliberately checkpoints before external
PR creation. Legacy fixture 18 additionally requires explicit PR-creation
arguments and forbids a post-create repair fallback; its forbidden role set and
single-message parallel-dispatch boundary also need explicit replacement
coverage. Therefore the parity case is not recorded as a complete replacement
for `integration.dispatch-18-post-impl-parallel-subagents`.

The next migration should reuse compatible Post captures for the shared
requirements and retain separate executable evidence for those remaining
boundaries. A shared report or subject count alone cannot discharge them. This
audit identifies overlap without adding a duplicate live launch or falsely
closing the integration gap.

### Empty-comparison regression

The pair reducer previously accepted an already-compiled plan with no checks,
or a check with no comparison criteria, as a passing pair. The catalog compiler
already rejected empty authored plans, but the reducer boundary did not. A
negative-control regression demonstrated both false passes. The reducer now
classifies both shapes as invalid before comparing any arms. Its focused suite
passes 26/26. This is local reducer evidence, not a live parity qualification.

### Native return-case audit correction

The official Claude return-case run completed in 129.373 seconds with two
subjects and one shared judge: majority passed; disagreement failed; neither
capture was infrastructure-invalid. Both had verified native activation. The
disagreement parent skipped the required synthesis agent, even though its
decision was correct. That is a retained behavioral failure, not a reason to
relax the native mechanism requirement.

Its evidence rows used the known `speckit-pro:` analyst namespace. Both return
cases now explicitly accept the equivalent complete namespaced evidence arrays
alongside their bare-name forms. Exact source paths, order, recommendation
tokens, and types remain required; different namespaces and roles still fail.
No general prefix stripping or implicit name normalization is performed.
Negative controls passed 28/28 after first demonstrating both alias failures.
The original native failure receipt is preserved. Direct diagnostic grading of
that retained observation after the alias correction still fails the required
synthesis-agent check; it is not a new native execution or qualification pass.

The retained majority canary emitted `json` consistently in its decision, option
list, and evidence recommendations. Rejecting that output solely because the
fixture spells the format `JSON` tests capitalization rather than consensus
correctness. Those three checks now explicitly accept either complete value;
the original strict typed comparison remains the default everywhere else.
No implicit case folding is performed on paths, analyst names, object keys, or
arbitrary strings. Wrong choices, extra options, reordered evidence, incorrect
source paths, and type mismatches remain failures, with negative controls.
The original captured artifact and failed verdict remain unchanged.

Both return-case prompts now request independently observable tool calls for
each analyst file; parallel calls remain permitted. This supplies per-file
evidence without prescribing a shell command or revealing expected answers.
A proposed concatenated-output suffix observer was rejected: a preceding file
could supply matching bytes while the target file was empty. Its counterexample
is retained as a regression, and compound output is not accepted as complete
per-file proof. These are grading/protocol corrections, not live qualification;
new prompt identities require new subject evidence.

The inventory accounts for 46 legacy fixture/case paths:

| Surface | Legacy cases | Current evidence mode | Proposed disposition |
|---|---:|---|---|
| Dispatch | 21 | replay and Claude-only live | 21 paired native cases |
| Return format | 3 | replay and Claude-only live | 3 paired native cases |
| End to end | 2 | replay and Claude-only live | 2 paired native cases |
| Grounding | 6 | replay; accepted `--live` is ignored | 3 paired native cases, 3 replay controls |
| Parser helpers | 7 | replay only | 7 replay controls |
| Performance workloads | 3 | prepared historical inputs | 3 paired native workload cases |
| Parity | 4 | structural dry-run or dual-Claude live | 4 paired native cases |

That produces 36 paired cases from legacy positive/workload paths and preserves
10 replay/parser controls. The operator feedback-sweep isolation smoke adds one
paired case, for 37 catalog cases and 74 host trials at one Claude and one Codex
run per case. No legacy cases are merged.

## Four-case parity catalog slice

The four legacy parity candidates were rechecked against the shipped sources,
current native Git/capture contracts, and the real staged runner. Parity 02 now
has a non-vacuous composite definition: reuse the already-authored upgrade and
autopilot functional definitions, and add one paired scaffold definition for
the previously uncovered surface. Its real Git fixture and deterministic
Git-boundary grader are executable. Parity 01 and 02 are now authored once in
the sole active catalog; parity 03 and 04 remain held. The temporary held-case
catalog was removed rather than weakening the nonempty-catalog invariant.
Root-owned dashboard integration must require all reused arms plus the scaffold
pair before it may report parity 02 complete. No native subject, judge, or pair
qualification was run in this pass.

| Legacy row | Disposition | Evidence and minimum faithful contract |
|---|---|---|
| `parity-01-post-impl` | **Definition adopted in the active catalog; not live-qualified; three additional legacy scenarios remain uncovered** | The adopted definition preserves the installed Post contract's required local checkpoints and no-external-PR boundary; it does not restore the old contradictory no-commit rubric. Its real `baseline-feature-origin-main/v1` fixture places pre-existing workflow, constitution, and verification support in the baseline and leaves exactly two additive source/test increments in the feature diff. The authoritative runner now returns `split-PR` only when the existing `plan-layers-feature-dir` layer planner has a complete, warning-free, dependency-free multi-seam plan, the Git diff exactly matches newly added planned paths, and bounded static Python inspection finds no direct cross-seam import; guarded/release-held cutovers, shared paths, dependencies, modify-heavy/destructive changes, dynamic or aliased imports, invalid relative imports, unsupported languages, missing evidence, and ambiguous topology abstain or route atomically. The emitted `source-proof:direct-python-imports-only` signal expressly avoids claiming generalized dependency analysis. Provider-free tests pass 15/15 atomicity and 29/29 parity. Real preparation and the staged `check-prerequisites` boundary succeeded for both hosts at `.native-eval-output/post-binding-preflight-vm88tuf3`, including all nine Codex isolation probes. The typed `native_verification_pointer` check for `specs/parity-01/.process/emission/verification-pointer.json` binds the protected resolved-Python invocation, the authenticated immutable saved verification-record bytes, and the exact pointer schema/identity/digests/isolation fields; missing or malformed authoritative evidence is invalid, mismatches fail, and both-host mutate/remove replay controls reject persistence races. Execution, verification-pointer, and adapter suites pass 107/107, 27/27, and 94/94 respectively. The case remains unqualified until both native subjects, independent grading, and pair comparison run successfully. Missing/invalid-packet, post-create lifecycle, and split-PR partial-failure/resume coverage remain explicit gaps below and are not waived. |
| `parity-02-repository-migration-guidance` | **Definition adopted; composite not live-qualified** | Legacy behavior is static guidance across three real product surfaces, not an API implementation exercise. The upgrade surface is already represented by `functional.speckit-upgrade.case-5`: `legacy-01` proves `migrate-structure` is deferred with no authoritative request, `legacy-02` proves the same unavailable status for `relocate-process-artifacts`, `legacy-03` forbids `dry_run` and `apply`, `legacy-04` preserves repository and PROCESS state, and `legacy-05` reports the gap rather than inventing a command. The autopilot surface is already represented by `functional.speckit-autopilot.case-29`: its `legacy-01` through `legacy-08` bind the sole candidate and every suppression to successful reads of the neutral relocation fixture, while `legacy-09` rejects retired, deferred, and invented invocations using retained tool evidence. Re-running either behavior under a parity-only ID would duplicate four paid subject arms without adding a requirement. The active `parity.02-scaffold-relocation-guidance` case activates the real scaffold skill on each host, reuses the identical neutral topology, requires all ten exact fixture reads, stages those inputs in a real `baseline-feature-origin-main/v1` repository, checks the exact bytes of all ten final inputs, preserves absent relocation destinations, and compares the closed capability/classification/no-auto-run report fields only after both arms independently pass. Its direct forbidden-command regex recognizes only a command-position `relocate-process-artifacts[.sh]` invocation and does not reject benign `rg`/read calls that mention `dry_run`, `apply`, or the helper name; the semantic criterion remains responsible for deferred-runner and invented replacements. The controller-bound `native_git_final_state` check rejects an extra untracked output, modified inputs, and a deleted original on either host, while missing controller evidence is invalid. Its provenance is Claude scaffold eval 1 and Codex scaffold eval 8. The old `parity_migration_policy.py` exercise remains removed as a vacuous policy reimplementation. Composite completion still requires terminal passing results for both hosts of the two named functional cases plus the terminal scaffold pair; equal wrong scaffold reports fail at independent grading before comparison. This aggregation is reuse, not evidence substitution, and makes no live-qualification claim. |
| `parity-03-reviewability-backstop` | **Held** | The legacy row combines actual current-reviewability stopping, deferred-helper handling, O5 topology, flat sibling ownership, and contextual routing. The shipped backstop requires current committed evidence or a stop before PR effects (`gate-validation.md:503-512`), while scaffold and status independently require `o5-topology` and preserve flat siblings (`speckit-scaffold-spec/SKILL.md:48-71`, `speckit-status/SKILL.md:194-209`). The removed `parity_reviewability_policy.py` task did not execute any of these contracts and was a vacuous reimplementation. Minimum faithful coverage needs actual current-evidence and missing-evidence Git scenarios plus real `o5-topology` results across the involved skill surfaces; a standalone policy function is not evidence. |
| `parity-04-stack-manager-guidance` | **Held** | The shipped contract actively invokes `detect-stack-manager-plan` in `dry_run` (`stack-manager.md:3-13`; registry `helpers/registry.py:561-569`). Its supported path probes the installed gh-stack skill/CLI, repository permission and Stacks API, PR identities, and local branch topology (`helpers/stack_manager.py:110-189`); attempted or partial mutation must remain on same-manager recovery (`:80-107`). The removed `parity_stack_policy.py` task bypassed that helper and was a vacuous reimplementation. Minimum faithful coverage needs controlled, trustworthy read-only gh/gh-stack/repository/API probe evidence for supported, fallback, blocked, and recovery scenarios, then invokes the real helper. Current local fixtures can prove only a subset and cannot manufacture the supported profile. |

### Parity 02 deterministic Git-boundary evidence

The execution layer already attaches a strict
`native-eval-controller-git-observation/v1` record under
`native_metadata.controller_git_observation`. Its observation provides exact
tracked/untracked paths and status, commit records, the path union changed by
new commits, and a binding between current HEAD and the initial feature commit.
It does not provide worktree-file content digests. The ten existing `text`
checks therefore remain necessary for exact final bytes; the new check proves
the exhaustive final path boundary.

The active scaffold case uses this exact catalog/grader contract:

```json
{
  "id": "final-git-boundary",
  "requirement": "preservation",
  "type": "native_git_final_state",
  "head_equals_initial_feature": true,
  "branch": "feature",
  "commit_count": 0,
  "commits_added": [],
  "changed_tracked_paths_from_initial_feature": [],
  "status": {
    "clean": false,
    "tracked_dirty": false,
    "untracked_dirty": true,
    "tracked": [],
    "untracked": ["artifacts/parity-02-scaffold-guidance.md"]
  }
}
```

Validation requires those exact keys and strict JSON types. A missing,
malformed, unbound, or non-controller record is `invalid`; a well-formed
controller observation with any unequal value is a behavioral `fail`. The
grader must compare `observation.head` to
`observation.initial.feature_commit` when
`head_equals_initial_feature=true`, rather than accepting a catalog-supplied
object ID. No alternative path list or subset match is permitted. This proves
final repository state, not absence of transient side effects; attempted
operations still rely on retained native tool evidence and `include_failed`.

The provider-free native integration boundary is accepted: adapter runtime
exclusions are limited to exact protected runtime paths, and regressions prove
that an undeclared Claude-side `.agents/undeclared.txt` and other non-runtime
hidden outputs remain visible to the Git observer. This establishes executable
controller binding, not a passing native scaffold pair or composite parity-02
qualification.

Both authored pair designs compare only after each host independently passes.
For parity 02, the shared report comparison is intentionally limited to the
new scaffold surface; upgrade and autopilot reuse their canonical functional
definitions and semantic criteria rather than launching duplicate parity
subjects. The focused tests prove fixture/check wiring and demonstrate that a
same-wrong scaffold report is blocked by independent grading. Mock semantic
verdicts prove plumbing only, not native judge sensitivity or product
qualification. The rejected `speckit-pro:autopilot` identifier and legacy
team-management tools do not appear. Genuine interactive Claude teams remain
a separate, non-blocking verification surface.

`integration-parity-inventory.json` is the exact machine-readable ledger. Every
legacy row records its path, requirement, boundary, evidence, disposition,
replacement case, and required assertion families. The catalog proposal ties
every replacement requirement to at least one executable deterministic or
semantic check. A semantic check remains `needs_judge` until a typed verdict
cites retained evidence; descriptive expected-outcome prose cannot pass it.

## One-to-one replacement map

Every distinct positive routing, category, redelegation, phase, error,
ownership, return, end-to-end, grounding, performance, and parity case remains
distinct:

| Legacy case | Proposed native case | Required assertion family retained |
|---|---|---|
| dispatch-01-clarify-codebase-only | `integration.dispatch-01-clarify-codebase-only` | selection, count, exact/forbidden roles, parent ownership |
| dispatch-02-clarify-multi-category | `integration.dispatch-02-clarify-codebase-domain` | selection, count, exact/forbidden roles, parent ownership |
| dispatch-03-redelegation-chain | `integration.dispatch-03-redelegation-chain` | roles, order, parent-child attribution, forbidden roles |
| dispatch-04-clarify-domain-only | `integration.dispatch-04-clarify-domain-only` | selection, count, exact/forbidden roles, parent ownership |
| dispatch-05-clarify-spec-only | `integration.dispatch-05-clarify-spec-only` | selection, count, exact/forbidden roles, parent ownership |
| dispatch-06-clarify-security-fanout | `integration.dispatch-06-clarify-security-fanout` | count, exact roles, item ownership, result attribution, forbidden roles |
| dispatch-07-clarify-ambiguous-fanout | `integration.dispatch-07-clarify-ambiguous-fanout` | count, exact roles, item ownership, result attribution, forbidden roles |
| dispatch-08-clarify-codebase-spec | `integration.dispatch-08-clarify-codebase-spec` | selection, count, exact/forbidden roles, parent ownership |
| dispatch-09-clarify-domain-spec | `integration.dispatch-09-clarify-domain-spec` | selection, count, exact/forbidden roles, parent ownership |
| dispatch-10-clarify-all-three | `integration.dispatch-10-clarify-all-three` | count, exact roles, item ownership, result attribution, forbidden roles |
| dispatch-11-clarify-round2-escape | `integration.dispatch-11-clarify-round2-escape` | count, exact roles, escape causality, parent ownership, forbidden roles |
| dispatch-12-tasks-phase | `integration.dispatch-12-tasks-phase` | selection, count, exact/forbidden roles, fixture read |
| dispatch-13-implement-task | `integration.dispatch-13-implement-task` | selection, count, exact/forbidden roles, TDD boundary |
| dispatch-14-analyze-phase | `integration.dispatch-14-analyze-phase` | selection, count, exact/forbidden roles, parent ownership |
| dispatch-15-checklist-phase | `integration.dispatch-15-checklist-phase` | selection, count, exact/forbidden roles, parent ownership |
| dispatch-17-phase-error-handling | `integration.dispatch-17-phase-error-boundary` | failure recognition, bounded retry, forbidden roles, no later phase |
| dispatch-18-post-impl-parallel-subagents | `integration.dispatch-18-post-impl-parallel-subagents` | parallel count, ownership partition, attribution, wait/serial tail, packet boundary |
| dispatch-19-implement-parallel-p-tasks | `integration.dispatch-19-implement-parallel-p-tasks` | parallel count, exact role, task ownership, attribution, forbidden roles |
| dispatch-20-consensus-multi-item-batch | `integration.dispatch-20-consensus-multi-item-batch` | count, role/item Cartesian coverage, attribution, forbidden roles |
| dispatch-21-resolve-pr-parallel-files | `integration.dispatch-21-resolve-pr-parallel-files` | count, file ownership, comment coverage, attribution, forbidden roles |
| dispatch-22-stack-manager-replay | `integration.dispatch-22-stack-manager-replay` | exact roles, order, required fields, forbidden commands/roles |
| return-01-synthesizer-reads-analysts | `integration.return-01-synthesizer-disagreement` | exact role, option, agreement, confidence, no fabricated evidence |
| return-02-synthesizer-majority | `integration.return-02-synthesizer-majority` | exact role, decision, agreement, confidence, no fabricated evidence |
| return-03-checklist-output | `integration.return-03-checklist-output` | exact role, domain/gap fields, parent gate decision |
| e2e-01-autopilot-minimal-smoke | `integration.e2e-01-autopilot-minimal-smoke` | count, required/forbidden roles, phase stop, attribution |
| e2e-02-autopilot-extended-pipeline | `integration.e2e-02-autopilot-extended-pipeline` | count, exact roles, phase order, forbidden roles, attribution |
| grounding-01-grounded-research | `integration.grounding-01-grounded-research` | discovery/use, tool-before-claim, citation join/count |
| grounding-03-abstained-no-capability | `integration.grounding-03-abstained-no-capability` | zero lookups, abstention, zero citations, no unsupported claim |
| grounding-04-discovered-tool-used | `integration.grounding-04-discovered-tool-used` | discovery, non-curated use, tool-before-claim, citation join/count |
| performance-ART-012-implementation-notes | `integration.performance-art-012-implementation-notes` | fingerprint, completion evidence, elapsed time, matched comparison, truthful UAT |
| performance-ART-007-draft-pr-emission | `integration.performance-art-007-draft-pr-emission` | fingerprint, dependency order, automated/operator status, elapsed time, manual UAT |
| performance-DOC-008-troubleshooting-security | `integration.performance-doc-008-troubleshooting-security` | fingerprint, story ownership, grounding, elapsed time, matched comparison, manual UAT |
| parity-01-post-impl | `parity.01-post-implementation-outcome` | independent correctness, ownership/attribution, packet boundary, exact/tolerance/semantic parity |
| parity-02-repository-migration-guidance | `parity.02-repository-migration-guidance` | independent correctness, no mutation, forbidden tools, exact/semantic parity |
| parity-03-reviewability-backstop | `parity.03-reviewability-backstop` | independent correctness, stop boundary, forbidden provenance, no mutation, semantic parity |
| parity-04-stack-manager-guidance | `parity.04-stack-manager-guidance` | independent correctness, no mutation, forbidden tools, exact/semantic parity |

The additional operator path maps to
`integration.feedback-sweep-isolation`; it retains confinement, canary
non-disclosure, schema-valid receipt, and result-attribution requirements.

## Replay controls preserved separately

The following are not compressed into live positive cases:

| Legacy control | Required retained executable checks |
|---|---|
| grounding-02-fabricated-citation | replay parser, missing-call detection, citation count, negative verdict |
| grounding-05-errored-tool | replay parser, failed-call detection, citation join, negative verdict |
| grounding-06-malformed-citation | replay parser, malformed citation, successful-call presence, negative verdict |
| parser-forbidden-spawn | parent-child attribution and forbidden-spawn detection |
| parser-multi-dispatch | dispatch count, order, and call identity |
| parser-no-dispatch | zero dispatch |
| parser-redelegation-chain | order and parent-child attribution |
| parser-sidechain-noise | sidechain filtering and target attribution |
| parser-single-dispatch | single dispatch, call identity, and result attribution |
| parser-skill-invocations | skill activation and event-type separation |

These deterministic fixtures test parsers and graders, not current client
behavior. The fabricated, failed, and malformed citation cases remain negative
controls; a live prompt asking a model to fabricate evidence would test a
different and unsafe requirement.

## Current runner and grader findings

- `layer6-integration/lib/fixture_runner.py` launches only `claude -p`.
  Dispatch, return, and end-to-end live runs therefore provide no Codex result.
- The grounding runner accepts `--live` but still reads the replay transcript.
  A successful invocation is not live evidence.
- `layer7-parity/run-parity-fixtures.py` launches Claude twice and compares a
  teams environment against a fallback environment. It has no Codex adapter,
  and non-interactive Path A cannot prove genuine teammate execution.
- Layer 7 dry-run checks fixture schemas and authored invariants only. It is not
  native qualification.
- The current parity judge can mark semantic comparison skipped when bytes
  differ, while the runner fails only explicit failures. A skipped semantic arm
  cannot contribute to a parity pass.
- Reduced transcripts remain useful parser fixtures but omit native evidence
  needed for runtime identity, usage, errors, full call inputs, artifacts, and
  some parent/position joins.

The inventory also covers every current shared native-eval path used by this
migration: catalog, host adapters, capture, Codex rollout collection, fixture
staging, deterministic grading, typed semantic judging, bounded pooling,
immutable storage, trial execution, trigger qualification, and the
`run-native-evals.py` entry point. These modules remain parent-owned shared
infrastructure; this audit records their evidence boundaries without changing
them. Trigger qualification is lower-layer evidence and cannot substitute for
Layer 6/7 execution.

The target executor must preserve runtime identity, completion, usage,
successful and failed tool calls, full inputs, call and parent ids, positions,
artifacts, and errors. Missing or malformed evidence is `invalid`, not
`skipped` or `passed`. Provider tool names may be normalized only through
validated aliases, never inferred from final prose.

## Performance acceptance remains separately pending

Catalog migration does not complete the original performance goal and does not
make it automatically non-blocking. The committed performance manifest is a
historical PR state: `prepared-inputs-not-native-qualified`, zero completed
native workflow runs, and 12 planned runs. Its historical
`launch_authorized=false` and empty budget/model fields do not override the
current user authorization.

The remaining acceptance work is exactly 12 matched benchmark workflows:

- ART-012 baseline and candidate on Claude and Codex: 4 workflows.
- ART-007 baseline and candidate on Claude and Codex: 4 workflows.
- DOC-008 baseline and candidate on Claude and Codex: 4 workflows.

The applicable manual UAT state must also be completed and recorded. PR
readiness must report these workflows and manual UAT as outstanding or cite
their final evidence; completion of this migration may not be presented as
completion of the original performance objective.

The proposal retains each workload and its fingerprint, completion, timing,
matched-arm, and UAT assertion families, but the current catalog API has no
baseline/candidate experiment-arm field or cross-trial performance reducer.
Its six paired workload trials are therefore inputs to later performance
qualification, not the 12 matched acceptance workflows themselves.

## Obsolete expectations to remediate later

This inventory intentionally does not mutate existing runners, original legacy
fixtures, or product instructions. The new four-case shard already removes the
obsolete mechanisms from its own contract; later legacy-path remediation must
remove or reframe:

- Layer 7 `env-teams.json` claims that an environment variable forces genuine
  team execution in `claude -p`; no new case stages that file.
- Teams-versus-fallback wording as the automated parity target; the new pair
  arms are Claude plugin and Codex project, each graded independently first.
- Current expectations of `TeamCreate` or `TeamDelete`; occurrences in frozen
  performance source material remain historical provenance.
- Layer 6 prose that labels replay evidence as live Layer 7 qualification.
- The grounding runner's advertised-but-ignored live mode.
- Any statement that dry-run, reduced transcript, or descriptive expected
  outcome constitutes a native pass.

The underlying host-neutral requirements remain: exact role selection,
bounded and concurrent fanout, exclusive task/file ownership, parent control
between redelegation stages, child-result attribution, waiting before
synthesis or a serial tail, forbidden nested delegation, no autonomous
`grill-me`, grounded claims or explicit abstention, packet validation,
mutation boundaries, and truthful gate status.

## Bounded remediation sequence

1. Register the 10 replay/parser controls independently.
2. Review the remaining paired catalog without removing any distinct legacy
   assertion family. One Layer 7 candidate remains under executable fixture
   review; three invented-policy replacements were removed and their original
   requirements remain held, as detailed in the four-case audit above.
3. Use the implemented confined executor, exact runtime identities, and bounded
   timeouts. Finish the outstanding fixture and native-capability coverage.
4. Use retained hashed native traces; extend observation only for requirements
   that the current capture cannot prove.
5. Grade each host independently. Missing executables, authentication gaps,
   tool denial, timeout, malformed traces, and absent typed semantic verdicts
   remain `invalid` or `needs_judge`.
6. Compare hosts only after both independent results pass; apply deterministic
   checks first and evidence-backed semantic grading second.
7. Replace the old Layer 7 live path only after all four legacy requirements
   have faithful executable replacements and those replacements pass,
   and negative controls prove equal failures cannot be rubber-stamped.
8. Publish the separate interactive-team verification runbook without feeding
   its manual result into the automated parity gate.

## Remaining executable gaps

- Pair compilation and independent-host gating are implemented, including
  rejection of empty comparisons and equal wrong results. The adopted
  parity-01 definition plans two host trials but has no live qualification;
  its provider-free fixture, route, preparation, and typed verification-pointer
  contracts are accepted for execution.
- Confined real Git repositories and descendant registered worktrees are now
  supported. External worktrees and an initial nested-worktree actor directory
  are not thereby covered; each scenario must preserve its actual boundary.
- Host allowed-tool names and enforcement remain to be qualified.
- The grounding runner's `--live` path is replay-only.
- The old Layer 7 live runner has no Codex adapter.
- The shared typed judge is integrated. Each new scenario still needs adequate
  retained evidence; a semantic rubric cannot replace missing observations.
- Performance needs explicit baseline/candidate binding and a cross-trial
  reducer; six paired catalog workload trials do not satisfy the 12-workflow
  acceptance matrix.
- The original performance objective still needs the 12 matched workflows and
  applicable manual UAT record.
- Interactive Claude teammate evidence needs a separate manual interactive run.
- Generated manifest/reference/dist work remains outside this audit and is
  centrally owned.

## Current 12-to-14 Post checkpoint compatibility decision

The Claude 12-row and Codex 14-row Post plans perform the same underlying
operations. Claude currently performs the final reviewability backstop and PR
packet/body generation inside `Post: PR Body Generation`; Codex exposes them
as two separately durable checkpoints: `Post: Final Reviewability Backstop`
and `Post: PR Packet/Body Generation`. The parity gap is therefore separate
status, evidence, and resume visibility—not missing underlying operations.

Changing Claude to 14 checkpoints remains pending a safe compatibility rule
for existing 12-row workflow/state. A migration must neither append new
pending gates after a PR has already been created (silently rewinding a valid
resume) nor mark the new checkpoints complete without independent durable
evidence. The migration decision is deferred until the first verified fast
path; existing completed or partially post-PR 12-row state must remain valid
until that rule is established.

Candidate `parity.01-post-implementation-outcome` is pre-create coverage only.
It exercises parallel worker ownership, ordering and return consumption, final
reviewability, UAT preparation, packet/body generation and validation, then
stops before external PR creation. It is not an exhaustive replacement for
legacy `parity-01-post-impl`. Three legacy parity scenarios remain uncovered:

- Missing or invalid packet: prove no PR-create command, preserve exact
  validator diagnostics, and forbid invented repair or substituted body text.
- Post-create lifecycle: prove exact PR-create arguments and URL propagation,
  Review Remediation and Retrospective execution, and no post-create packet
  repair fallback.
- Split-PR partial failure and resume: prove three-slice order and base/head
  topology, durable schema-version-2 PRS/MOC/state persistence, no rewind of
  earlier opened PRs after a later failure, and correct resume reconciliation.

These are executable coverage gaps, not waived or non-blocking outcomes.
Parity 01 and 02 have executable authored definitions but no live qualification;
parity 03 and 04 remain held. Adopting the pre-create parity-01 case does not
waive the three additional legacy scenarios above.

## Return-case grading audit after native qualification

Disposition for `mechanism-evidence` in the two authored return cases: **keep**.
The `native_synthesis_mechanism` check already proves the expected host mechanism,
exact source-read ordering, successful native completion, and parent-owned
artifact materialization. For Claude it also verifies a nonempty child return
against retained tool-result bytes. These protections are implemented by
`_claude_synthesis_mechanism` and `_subagent_returns_before_parent_file_change`
in `tests/speckit-pro/lib/native_eval_grading.py`.

Those deterministic checks do not compare the meaning of the returned child
answer with the artifact the parent writes. A successful child returning an
unrelated recommendation could satisfy ordering and nonempty-result checks while
the parent independently emits the expected JSON. The shared semantic criterion
retains this otherwise-uncovered grounding requirement. Correct final JSON alone
does not demonstrate faithful consumption of the child result. Removing the
criterion as a duplicate is therefore not justified by the current evidence.

The latest Codex qualification executed both cases once, with two shared judge
calls and no retry: report
`integration-read-protocol-canary-20260916/reports/607aa4cdb8b747529a72b88df2d45942.json`.
Both passed in 153.651 seconds. This result qualifies neither Claude's counterpart
nor the remaining integration scenarios. Host-conditioned elimination of a judge
call is not implemented; it would require preserving the same logical grounding
criterion and proving the alternate deterministic check covers it.
