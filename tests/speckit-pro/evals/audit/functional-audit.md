# Layer 3 functional audit

Audit date: 2026-09-15

## Outcome

The legacy Layer 3 surface defines 211 skill-functional rows: 84 for Claude and 127 for Codex. Behavior-based reconciliation produces 127 canonical behaviors. The headless catalog contains 142 capture mappings (55 Claude and 87 Codex), leaving 69 definition-to-runner omissions (29 Claude and 40 Codex). These figures are deliberately separate: a headless mapping is not a graded functional pass.

The audit also found three executor-mode experiment cases. They are not skill-functional cases and are counted separately. Across functional definitions, headless mappings, and executor-mode cases, the machine inventory accounts for 356 legacy records.

The sole authored native catalog contains 206 cases overall, including 93 paired functional-layer cases: 65 response-only definitions and twenty-eight staged file/scenario/command-grounded definitions. One additional canonical functional behavior reuses the already-authored paired parity case `parity.02-scaffold-relocation-guidance`, giving 94 represented behaviors and 33 remaining gaps. This is authored, schema-valid coverage only, not native qualification. No held behavior was weakened into a response-only or invented-fixture test.

The selection ledger's `cross_layer_reuse` maps every expectation from Claude
scaffold case 1 and Codex scaffold case 8 to executable requirements in that
single parity case. Real reads, final artifact bytes, Git boundaries, suppression
classification, and forbidden operations are retained. The capability rubric
also requires that deferring relocation does not block later scaffolding under
normal prerequisites. The scoped prompt still stops before mutation; it does
not claim completion of the full scaffold workflow. No duplicate functional
case or extra subject launches are added, and both hosts must still qualify.

`functional-inventory.json` remains the exhaustive legacy/disposition inventory. Its embedded `native_catalog` summary now records the 75-represented/52-held checkpoint; this report, the sole catalog, and `legacy-selection.json` record the reviewed fourteen-case adoption delta. The legacy row counts, reconciliations, and dispositions in the frozen inventory remain unchanged.

The selection ledger separates 70 directly selected cases, seven `resolved_exclusions`, and two still-excluded candidates. Four resolved records were already represented: coach case 2 and status cases 2, 5, and 6. The other three cover autopilot Post-sequence case 7, Self-Review case 25, and status dashboard case 1. The new selected record for autopilot case 107 retains all five Codex legacy expectations and maps them to the executable binding and preservation requirements; its Claude arm is explicitly a parity addition, not fabricated legacy coverage. Their exact legacy boundaries and expectation-to-requirement mappings are retained. A regression check requires selected plus resolved IDs to equal the active functional catalog and forbids overlap with excluded IDs.
Twenty-four provider-free diagnostic behaviors are now authored. The latest batch adds the Claude same-session scaffold handoff and the archive-extension planning case. These are authored definitions only; no live qualification is claimed. The 94 represented / 33 held boundary includes these additions.

Status dashboard case 1 stages a real Git repository and registered descendant
worktree, with a roadmap and active workflow whose facts remain hidden from the
prompt. Five typed JSON checks cover totals, states, phases, next-active work,
and next-unstarted work. A separate semantic rubric covers sources, dependencies,
priority, and blockers. Both native hosts share all criteria. Ten wrong-field
controls fail independently of semantic verdicts; real fixture materialization
and controller-only expected-answer isolation also pass. The focused functional
suite passes 34/34; no native qualification is claimed.

Plan-repair cases 111/112 now map all 28 host expectations to fourteen shared
requirements. Their native evidence checks bind the supplied context, real
executor returns, and subsequent G3 reruns, with at most two repairs. Both
initial fixtures independently produce the real expected G3 failure without
writing state. Catalog contracts pass 141/141 and functional checks pass 24/24;
neither result is counted as live qualification.

The two explanation-only autopilot cases retain their original scope. Their shared response format exposes native sequence/count/mechanism fields to a strict JSON grader, bound to the actual client. The 12-row and 14-row lists are checked against the respective shipped canonical references; producing the other client's list fails. The shared semantic rubric still checks all explanation requirements. This adds no workflow execution claim. Provider-free functional checks pass 23/23; the two-case preview schedules four subject trials and up to four judges with runs=1. No native qualification occurred.

Coach case 7 closes the fixture-destination gap: the existing neutral workflow is staged at the exact path named by the user. The paired case requires coach activation without autopilot activation, rejects attempted delegated workflow execution, preserves the complete workflow bytes, and grades the requested redirection and brief guidance from retained actions and output. Four legacy expectations remain mapped. The Claude wording “correct command” and Codex wording “correct entrypoint” share the same routing requirement. Focused catalog checks pass 22/22; semantic mocks prove wiring, not native success or judge sensitivity.

## Count ledger

| Surface | Claude | Codex | Total |
|---|---:|---:|---:|
| Defined legacy functional cases | 84 | 127 | 211 |
| Headless capture mappings | 55 | 87 | 142 |
| Defined but absent from headless | 29 | 40 | 69 |
| Canonical behavior union | — | — | 127 |
| Authored native functional definitions | 77 paired cases | 77 paired cases | 154 planned one-run trials |
| Response-only authored subset | 58 paired cases | 58 paired cases | 116 planned one-run trials |
| File/scenario/command-grounded authored subset | 19 paired cases | 19 paired cases | 38 planned one-run trials |
| Additional functional behavior reused from parity | 1 existing arm | 1 existing arm | 0 additional trials |
| Represented canonical functional behaviors | — | — | 78 |
| Held canonical behaviors | — | — | 49 |
| Executor-mode comparative cases | — | — | 3 |

The 43 canonical behaviors without a Claude legacy definition break down as follows: `install` 3, `speckit-autopilot` 12, `speckit-coach` 2, `speckit-install` 1, `speckit-resolve-pr` 6, `speckit-scaffold-spec` 8, `speckit-status` 7, and `speckit-upgrade` 4. In particular, Claude is missing the entire status suite and the entire PR-resolution suite even though both Claude skills exist.

## Headless omissions

| Host | Legacy catalog | Defined | Headless | Missing eval ids |
|---|---|---:|---:|---|
| Claude | grill-me | 7 | 0 | 1-7 |
| Claude | speckit-autopilot | 43 | 33 | 1, 11, 12, 113-119 |
| Claude | speckit-coach | 21 | 19 | 11, 12 |
| Claude | speckit-install | 2 | 0 | 1, 2 |
| Claude | speckit-prd | 5 | 0 | 1-5 |
| Claude | speckit-scaffold-spec | 2 | 2 | none |
| Claude | speckit-upgrade | 1 | 1 | none |
| Claude | ubiquitous-language | 3 | 0 | 1-3 |
| Codex | grill-me | 7 | 0 | 1-7 |
| Codex | install | 3 | 0 | 1-3 |
| Codex | speckit-autopilot | 55 | 46 | 1, 16, 113-119 |
| Codex | speckit-coach | 23 | 21 | 13, 14 |
| Codex | speckit-install | 3 | 0 | 1-3 |
| Codex | speckit-prd | 5 | 0 | 1-5 |
| Codex | speckit-resolve-pr | 6 | 5 | 1 |
| Codex | speckit-scaffold-spec | 10 | 8 | 1, 7 |
| Codex | speckit-status | 7 | 5 | 1, 4 |
| Codex | speckit-upgrade | 5 | 2 | 1-3 |
| Codex | ubiquitous-language | 3 | 0 | 1-3 |

## What the current runners prove

- `run-functional-evals.py` and `run-functional-evals-codex.py` only locate a skill and print prompts plus expectations. They do not invoke a client, capture native evidence, grade a requirement, or inspect an artifact. These are preview helpers, not automated functional runners.
- `run-headless-evals.py` does invoke native CLIs and records lifecycle, selection, tool, and workspace hashes. It initializes `semantic_grade` as `not_performed` and its success state is `completed_ungraded`.
- The headless runner reclassifies any workspace change as `workspace_changed`. It therefore cannot prove a writable requirement. A completion saying “I wrote the file,” “I pushed,” or “I resolved the thread” remains only a response claim.
- Claude `speckit-autopilot` eval 2 now has an authored paired definition with actual command/artifact checks, but Claude live qualification remains blocked until the plugin-host Bash prerequisite is independently qualified. Catalog adoption is not equivalent to observed native execution.
- Ninety-three headless rows omit `expected_selection` and inherit `target`. That default is valid in the old loader, but it obscures whether selection was deliberately classified.
- The 142 headless rows reference existing fixture directories, but existence is not sufficiency. Most autopilot rows reuse `coach-installed-project`, which contains extension manifests and CLI observations, not the scenario-specific workflows, reviewability evidence, PR packets, worktree registrations, or preview records named by many prompts.

## Specific evidence gaps

### Preview-only behavior

Autopilot cases 113-119 are not rendered-preview tests. The legacy rows ask the model to describe preview decisions; they do not supply rendered observations or assert a durable preview record. The generic fixture cannot distinguish a real rendered page from a queued/open receipt, blank page, error page, title-only page, or stale artifact. These seven behaviors remain pending until an adapter can retain rendered observation evidence and checks can grade it.

### Response claims instead of actual files

The current catalogs frequently phrase expected behavior as “writes,” “creates,” “commits,” “pushes,” “installs,” or “resolves,” but neither preview runner observes any outcome and the headless runner forbids workspace changes. Artifact-producing PRD, scaffold, install, upgrade, autopilot post-phase, and the remaining interactive ubiquitous-language requirements therefore need writable disposable fixtures plus `file_exists`, `json_field`, content, tool-order, and Git-state evidence as applicable. Ubiquitous-language case 3 is now represented separately by an actual lint command and complete retained JSON report. Semantic prose alone must not substitute for those checks.

### Missing or insufficient fixtures

- The `coach-workflow-project` fixture contains `SPEC-025-workflow.md` at its root, while the prompt names `docs/ai/specs/.process/SPEC-025-workflow.md` and no `fixture_destination` repairs that path.
- Status cases 1-3 and 5-7 have usable frozen scenario files. Status case 4 needs a real registered external-worktree topology, which the flat file fixture contract cannot create by itself.
- Autopilot migration, layer-plan, reviewability, PR-packet, archive-sweep, worktree-binding, grounding-repair, and preview cases reference state absent from the generic fixture.
- The executor-mode catalog names `src/queue/...` and `src/report/...` subjects that do not exist under its test tree. Its scorer consumes externally supplied result JSON and does not launch either client.

### Writable and external operations

Install, upgrade, scaffold, full autopilot, PR creation, and PR resolution require disposable mutation targets and, where applicable, fake or replayed GitHub operations. The audit does not turn them into read-only explanation tests. External catalog discovery also needs a frozen replay for deterministic automation. Requirement answers, grading rubrics, and judge verdicts must stay outside the staged agent workspace.

### Cross-client capability versus mechanics

The Codex-only `install` skill installs bundled Codex agent TOML files. Claude has no equivalent native installer skill and one must not be fabricated. The canonical replacement must test the shared capability—required agents are available—while allowing legitimate mechanics: Claude plugin materialization versus Codex installation/refresh. Similarly, native edit tools may normalize to a shared edit capability, while literal provider tool names remain adapter details.

Claude autopilot legacy case 106 and Codex case 34 are not equivalent merely because both discuss a descendant worktree: the Claude case requires an operator `/cd` handoff, while the Codex case permits same-task execution with all work rooted at `WORKFLOW_ROOT`. This stays pending until the shared safety invariant and host-specific mechanics are expressed without contradictory executable checks.

## Behavior reconciliation

Counterparts were matched by requirement, not numeric id. Important shifted matches include:

- Claude autopilot 13-22 map to Codex autopilot 17-27 by behavior; Claude 23-26 map to Codex 29, 31-33.
- Claude coach 10-12 map to Codex coach 12-14.
- Claude scaffold 1 maps to Codex scaffold 8; Claude scaffold 2 maps to Codex scaffold 9.
- Claude upgrade 1 maps to Codex upgrade 5.
- Claude autopilot 5 is absorbed by the broader Codex autopilot 5 contract because that case includes the same mandatory consensus-task requirements plus durable plan state.

The inventory uses four dispositions:

- `keep`: retain a distinct requirement and add the missing host entry.
- `merge`: collapse behavior-equivalent host rows into one paired case.
- `replace`: retain the requirement but redesign its fixture, checks, interaction boundary, or host-neutral contract.
- `remove`: retire a legacy automation row only after its replacement is executable; no product requirement is removed.

## Authored native catalog status

`tests/speckit-pro/evals/catalog.json` is the sole authored `native-eval-catalog/v1` corpus. It contains 74 paired functional definitions in addition to the separately counted trigger cases. Each functional definition has:

- exactly `claude` and `codex` host entries;
- required `timeout_seconds: 300` and `resource_class: ordinary`;
- one shared prompt and one shared check list;
- normalized selection checks plus deterministic or semantic checks appropriate to the requirement;
- no staged fixtures for the 58 response-only cases;
- exact successful file-access evidence plus fixture-specific semantic grounding for the four staged coach/status cases;
- one staged missing-roadmap scaffold case with a deterministic absent-workflow check and semantic grading for truthful recovery;
- only existing fixture source files under the evaluation test tree;
- three scenario-grounded autopilot definitions for relocation classification, the four-branch layer-plan gate, and broken-archive fail-closed behavior;
- one command-grounded G7 definition that executes the authoritative runner, retains the full envelope, and proves the sole staged feature file remains byte-for-byte unchanged;
- one command-grounded ubiquitous-language definition that executes the shipped lint against a real staged `origin/main` history and grades the complete ordered unmapped list;
- one registered-worktree ambiguity definition that binds the exact protected runner request and complete expected-failure envelope, grades both canonical candidates and the hard-stop response, and preserves the root checkout plus registered child worktree;
- provenance back to every merged legacy catalog;
- native differences limited to activation/tool mechanics, not weaker behavior.

With the user-selected one-trial default, `plan_trials(..., runs=1)` produces 148 planned functional trials: 74 Claude plugin-mode trials and 74 Codex project-mode trials. Semantic checks intentionally return `needs_judge` until a typed verdict with retained evidence is supplied; the rubric is not part of actor input. Schema validation, mocked semantic verdict tests, trial expansion, and provider-free preparation do not establish that either native subject or judge passed the case.

The 58 response-only and sixteen staged file/scenario/command-grounded cases are audited definitions ready for native execution, not claims that either host has passed them. `functional.speckit-scaffold-spec.case-3` preserves Codex legacy eval 3 as an actual missing-roadmap execution request: its subject prompt provides no rubric, the controller stages a neutral adjacent SPEC-030 roadmap entry alongside the fixed Git baseline, and grading requires both no invented SPEC-031 workflow artifact and typed semantic verdicts. The layer-plan subject prompt names only the four independent inputs and receipt keys; it does not disclose the expected branch values or actions. Autopilot case 107 uses a real registered descendant worktree and exact protected runner-result plus final-Git-state checks; the accepted provider-free `prepare_trial` evidence for both hosts at `.native-eval-output/worktree-bound-preflight-044p2byp` is preparation evidence only, not native subject qualification. The private proposal remains planning material; archive case 35 is held below rather than registered in the active catalog.

## Interactive requirement correction

The 13 Grill Me, PRD, and terminology behaviors are completion blockers. The user's non-blocking interactive-verification decision applies only to genuine Claude Teams behavior; it does not waive these retained functional requirements. A non-interactive PR gate cannot call these cases passed merely because it cannot exercise them.

| Requirement-level class | Cases | Exact retained behavior | Feasible fixture or harness option |
|---|---|---|---|
| Live multi-turn design decisions | Grill Me 1-6 | The source skill requires an active user, one question and one answer at a time, then synthesis from the chosen answers. Case 4 specifically grades structured question calls; cases 1-3 and 5-6 require the resulting decision record or artifact. | A live interactive harness can exercise the whole behavior. A saved answer set or transcript can test only a later replay/synthesis companion; it cannot replace the question/answer path. |
| Live PRD validation and decomposition | PRD 1-3 | The source protocol requires one decision axis per turn, no invented decisions, and user confirmation of the dependency graph. The legacy cases additionally require gap-only questioning or interview-time feature splitting. | Exercise with a live interactive harness. A supplied brief can reduce the questions, but pre-filled answers would remove the acceptance evidence that these cases explicitly require. |
| Protocol-required PRD interview, not explicit in the short prompt | PRD 4 | Although the legacy expectations emphasize leanness, the active source still requires the shared interview and dependency-graph confirmation. The current prompt is not a complete validated decision record. | A fully answered brief could be a separate draft-quality case. Under the current source, non-interactive execution may produce only a best-effort PRD and must not create the roadmap, so it cannot replace this full case without an explicit product-contract change. |
| Continuation after a completed PRD interview | PRD 5 | The case forbids *new* questions beyond the pre-existing interview, but still depends on validated earlier answers before producing the PRD, roadmap, and MOC. No such history fixture exists today. | Claude plugin eval can seed a prior JSONL conversation and make the case prompt the next user turn. That can test continuation only. The decision-acquisition requirement still needs its own passing interactive case, and the source must explicitly permit validated-history continuation before this can be automated as written. |
| Explicit terminology confirmation | Ubiquitous Language 1-2 | Case 1 requires confirmation before writing; case 2 requires the user to choose the winning term. | Seeded history can test write-after-confirmation as a companion. Static answers cannot prove that the skill asked for confirmation or let the user choose, so the interaction requirement remains blocking. |

This distinction also preserves the already-proposed Grill Me case 7: its exact requirement is to abort before asking a question in autopilot/subagent execution, so it is legitimately non-interactive and is not one of the 13 gaps.

### Official Claude plugin-eval capability

Current official documentation says each `claude plugin eval` run starts one fresh isolated **non-interactive** session, sends the case prompt, and grades the final reply, transcript, or created files. The supported context mechanism is `context.history_file`: it loads a saved `.jsonl` transcript and treats the case prompt as the next user turn. The documented case schema exposes one prompt and optional prior history; it does not document a scripted stream of new human replies inside one eval run. [Anthropic plugin evals](https://code.claude.com/docs/en/plugin-evals)

Claude Code generally supports resuming conversations in non-interactive mode, but that is session continuation, not proof that `claude plugin eval` can conduct a live one-question/one-answer interview. [Anthropic programmatic usage](https://code.claude.com/docs/en/headless) Therefore, saved history is a valid option for continuation cases, not a basis for declaring the interview requirements passed. This is an inference from the documented runner and schema boundaries, and remains fail-closed until Anthropic documents or a retained canary proves reply injection.

The proposed alternative of chaining real evaluation turns was also checked.
OpenAI documents `codex exec resume <SESSION_ID>` with a follow-up prompt, and
the installed CLI help confirms that interface. [OpenAI non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode#resume-a-non-interactive-session)
However, the product's Codex PRD interaction adapter explicitly prohibits the
question fallback in `codex exec` and restricts its output to a best-effort draft
with unvalidated decisions; it forbids roadmap/MOC completion in that context
(`speckit-pro/codex-skills/speckit-prd/SKILL.md:31-37`). Chaining native turns or
providing history does not remove this product contract. No paid canary is
needed to justify overriding an explicit prohibition, and no such override was
made. The user has been asked whether all thirteen requirements should remain
mandatory but be verified separately through the real interactive native
clients, an explicit exception to the non-interactive-runner-only migration.
Until that decision and actual evidence exist, all thirteen remain held.

## Pending canonical gaps

| Gap | Canonical behaviors | Required remediation |
|---|---:|---|
| Interactive requirement | 13 | Keep completion blocked until the exact live interaction is implemented and passes, or the user explicitly changes the requirement. Seeded history may cover only an explicitly separated continuation half. Genuine Claude Teams verification remains separate and non-blocking. |
| Rendered preview observer | 7 | Keep completion blocked until actual rendered-page observations and durable preview records are retained; queued/open receipts are insufficient. Retire a case only with evidence that its requirement is obsolete. |
| Writable scaffold fixture | 4 | Add disposable roadmap, branch, worktree, push-failure, and placeholder fixtures with file/Git checks. Scaffold relocation guidance reuses the parity case. |
| Writable autopilot fixture | 5 | Add phase/post fixtures, fake PR operations, and artifact/Git checks. |
| Registered-worktree fixture | 2 | Materialize the remaining registered nested/external/revalidation topologies. The ambiguous descendant-worktree behavior is now authored as autopilot case 107. |
| Scenario fixture | 1 | Add host-conditioned native command evidence for archive case 35: qualified Claude registered project-command invocation and Codex manifest-relative execution without equating their mechanics. |
| Writable upgrade fixture | 4 | Add isolated pre/post trees and backup/restore assertions. |
| Writable install fixture | 3 | Add isolated CLI/integration roots and artifact checks. |
| Cross-client install capability | 3 | Test agent availability postcondition; do not invent a Claude installer skill. |
| Other single gaps | 6 | Add cross-host worktree contract, external-catalog replay, forbidden-access observation, Git-history fixture, PR-review replay, and writable extension fixture. |

The table above accounts for 33 later-discovered gaps. No early migration candidate remains as an unrepresented catalog gap, leaving 33 held behaviors. Plan-repair cases 111/112, status dashboard case 1, and registered-worktree ambiguity case 107 now have executable definitions and are no longer missing-catalog gaps. The remaining scenario-fixture row is autopilot case 35; it is not one of the four early candidates. The earlier two adopted command-grounded definitions remain blocked from Claude live qualification by the separate Bash-host prerequisite, but they are no longer missing functional definitions and therefore are not counted among the 52 held behaviors.

| Held early candidate | Gap | Why it remains held |
|---|---|---|
| Coach 8 | Active installed CLI/host evidence | Frozen settings and help captures are replay evidence, not observation of the active installed CLI and host. |

The three executor-mode cases additionally need real subject fixtures and native capture integration. Their historical three-repeat comparison is an explicit experiment policy, not the default trial count for the canonical functional suite.

## Concrete migration plan

1. Keep this inventory as the accounting source and add a contract test requiring every legacy definition and headless row to retain a disposition and replacement.
2. Keep the 93 functional-layer definitions and the reused parity definition in the sole catalog, but make no qualification claim until grading, permission profiles, capture canaries, and native subject execution pass. Preserve the 33 held requirements in the audit ledger until their fixtures or contracts are faithful.
3. Implement two native adapters: official Claude plugin eval in non-interactive mode and `codex exec` for Codex. Normalize activation/tool aliases while retaining raw evidence and runtime identity.
4. Run one trial per host by default. Treat process success, equal outputs, and `completed_ungraded` as non-passes until all deterministic checks and semantic verdicts pass.
5. Add the missing Claude status and PR-resolution coverage from the shared canonical cases; do not clone Codex wording or assume matching ids imply matching behavior.
6. Remediate pending fixture/check gaps in bounded groups. Any new check type must be added to the canonical library and grader before a case depends on it.
7. Implement and run the 13 retained interactive behaviors with human input. They remain completion blockers even when they cannot run in the non-interactive PR job. If a case is split into decision acquisition and deterministic continuation, require both halves to pass. Do not use removed `TeamCreate`/`TeamDelete` assumptions; only genuine Claude Teams verification is separate and non-blocking.
8. Retire the preview helpers and individual headless rows only after replacement coverage, replay tests, and both native hosts are verified. Preserve the executor-mode comparison as a separate opt-in experiment.

## Verification performed in this audit lane

- Parsed every legacy JSON definition and every headless mapping.
- Verified all 142 headless references resolve to exactly one legacy definition.
- Verified all declared headless fixture roots exist, while separately auditing whether their contents satisfy the prompt.
- Validated all 93 functional definitions structurally with `load_catalog`; this is not native qualification.
- Confirmed one-run trial planning yields 138 functional host rows; this is scheduling evidence, not execution evidence.
- Verified the four file-read-grounded additions retain exact successful file-access checks and fixture-specific semantic criteria; this still does not prove a model observed every byte or that either native host passed.
- Executed the two new neutral fixtures provider-free against the shipped helpers: G7 returned exit 1 with `pass=false`, `total=85`, `done=84`, and one marker without changing `tasks.md`; the lint exited zero and returned exactly one unmapped `reindex_all` record at `src/billing.py:6`.
- Made no provider calls, no product/manifest/generated changes, and no claims of native qualification.

The required docs reference check was run and reported `stale: docs-site/src/content/docs/reference/tests.md`. This lane did not regenerate that generated page because generated-artifact edits were explicitly out of scope; the integration owner must regenerate after all concurrent audit files are present.
