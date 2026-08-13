# Phase 0 Research: Scaffold Integration — blind-spot pass and autopilot chain

**Feature**: ART-011 | **Branch**: `art-011-scaffold-integration` | **Date**: 2026-08-12

This spec adds no code, so Phase 0 is not technology selection. It is the
evidence pass that resolves the two questions the design concept explicitly
routed to `/speckit-plan`, recovers the normative contract that is not in the
working tree, and measures the caps the implementation has to land inside.
Every claim below is grounded in a file read or a command run in this worktree.

## R1. The ART-006 chain contract, recovered

**Decision**: Treat `contracts/scaffold-autopilot-chain.md` and
`contracts/stage-invocation.md` from the archived ART-006 spec as normative, read
from git history rather than the working tree.

**Recovery commands** (read-only, no checkout, no relocation):

```text
git show 5e184e33:specs/art-006-autopilot-staging/contracts/scaffold-autopilot-chain.md
git show 5e184e33:specs/art-006-autopilot-staging/contracts/stage-invocation.md
```

**Rationale**: spec.md names the first as normative and states it is not in the
tree. The second is reachable only from the first, which links it as holding
"full argv surface". Both were read in full during this phase. The design
concept's first Open Question deferred relocation as archive hygiene; nothing in
planning needed relocation, because the recovery command works from any checkout
sharing the object database.

**What the contract fixes, and where it lands in this plan**:

| Contract clause | Fixes | Consumed by |
|---|---|---|
| §1 Handoff artifact | The workflow file path is the **sole** token. Not a state file, branch name, feature directory, or environment variable | FR-014 |
| §2 Entry precondition | At scaffold time the `Stage` entry is absent; absence means "no run yet", is never an error, and is not a fourth value | Confirms the chain needs no `Stage` write |
| §3 Invocation form | Claude Code: `/speckit-pro:speckit-autopilot <workflow-file> --stage plan`. Codex CLI: `<workflow-file> --stage plan` | FR-014 |
| §3 Stage vocabulary | Closed at `plan`, `implement`, `full`. Literal lowercase, no aliases, no alternate casing | FR-014 |
| §4 Completion signal | Terminal status on every planning row **plus** a recorded `G6.5` verdict. The `Stage` row is corroborating, **not** the test | FR-019 |
| §4 Status ownership | The six terminal literals are owned by the shipped `WORKFLOW_TERMINAL_STATUSES` frozenset; every other appearance is a readability copy | FR-020 |

**Correction absorbed into this plan.** `stage-invocation.md` §1 states that the
leading `/speckit-pro:speckit-autopilot` token "has no Codex counterpart" and that
each distribution's argv begins at the workflow path. The Codex row of the §3
table therefore shows the argv, not a runnable line. The runnable Codex line is
the argv prefixed with the skill's own invocation form, which on Codex is
`$speckit-autopilot`. This is the form already used throughout the Codex skills
and is what the Codex variant must print and invoke. Reading the §3 table
literally would produce a Codex chain that invokes a bare path.

**Alternatives considered**: relocating the contract into
`docs/ai/specs/.process/` so downstream phases stop depending on a git object.
Rejected for this slice: it is the archive-hygiene change the design concept
already deferred, it adds a file to a budget fixed at two production files, and
the recovery command proved sufficient here. Carried forward as a named deferral
per the spec's PR Review Packet Requirements.

## R2. Is prompt-level framing of `codebase-analyst` sufficient? (design concept Open Question, routed to `/speckit-plan`)

**Decision**: Yes, with two mechanical conditions the plan makes explicit. No
agent definition is edited, so the Layer 6 sha256 corpus chain stays unstaled.

**Evidence read**: `speckit-pro/agents/codebase-analyst.md` (Claude) and
`speckit-pro/codex-agents/codebase-analyst.toml` (Codex), both in full.

**Condition 1 — the dispatch must carry the whole framing, and it can.** Both
definitions frame the agent for consensus resolution: the input contract is
"Clarify Question | Checklist Gap | Analyze Finding", and the output contract is
a fixed `## Answer / ## Evidence / ## Confidence` block. Neither has a
blind-spot mode. FR-005's dispatch block substitutes a different task statement
and a different output shape, which is exactly the substitution the Codex
autopilot already performs on this same agent for three unrelated input types
(`speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md:244`).
The agent's `## Your Process` and `## Search Strategy` sections are task-agnostic
codebase-reading instructions and support the pass unchanged.

**Condition 2 — read-only reach covers the git-history chase, on both
platforms.** FR-004 requires chasing archived dependencies into git history, and
FR-005 asserts both platforms can. Verified directly:

- Claude: `disallowedTools: Write, Edit, MultiEdit, NotebookEdit, Skill, Agent, TeamCreate, SendMessage`. `Bash` is **not** in that list, so `git show` and `git log` are reachable. Write-class tools are all denied, so read-only is a tool restriction rather than a promise (design concept Q2).
- Codex: `sandbox_mode = "read-only"`, which permits reads including git object reads.

**Residual risk, recorded not closed.** The Codex definition pins
`model_reasoning_effort = "low"`, with a comment stating that setting was
Layer 6-validated at quality 1.0 **on consensus fixtures**. A blind-spot pass is
a different and harder task than consensus lookup, so that validation does not
transfer. FR-002 forbids editing the agent, so the effort setting cannot be
tuned inside this budget, and the design concept already fixed the remedy: if
framing proves insufficient, the fix is a new spec, not an agent edit. The
observable consequence is finding quality on Codex, not correctness: FR-007's
fail-open path already covers an unusable or absent reply, and FR-006's sentinel
makes "ran and raised nothing" a distinct, recordable outcome rather than a
silent failure. UAT is where this is measured.

## R3. Dispatch shape — the pass must await its result

**Decision**: Dispatch the analyst and **await its completed summary before the
interview begins**, mirroring the house consensus pattern on each platform.

**Rationale**: the Claude agent definition carries `background: true`
(`speckit-pro/agents/codebase-analyst.md` frontmatter). A background dispatch
returns an identifier, not an answer. FR-001 requires the pass to run
"immediately before the grill-me interview", FR-002 makes it the only channel,
and FR-011 requires the run to flow straight from the findings into the first
question. All three fail if the dispatch is fire-and-forget, because the findings
would arrive after the interview had already started. The spec does not state the
await, so the plan states it.

**House pattern, copied rather than invented**:

- Claude, `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md:200-206`: `Agent(subagent_type: <a>, run_in_background: true, ...)` followed by the literal instruction `Await ALL spawned analysts to complete.`
- Codex, `speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md:244-249`: `spawn_agent` → bounded `wait_agent` loop until the actual summary is delivered, with the explicit warning that "a status update or timeout alone is not the result", then `close_agent` only when that action is exposed.

**Agent name form**: `speckit-pro:codebase-analyst` on Claude, per
`consensus-protocol.md:82` and `:90`, which use the namespaced form throughout.
The bare name is not the dispatch identifier for a plugin-provided agent. On
Codex the agent is addressed by its installed name `codebase-analyst`
(`speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md:228`).

**Alternatives considered**: dispatching without awaiting and seeding findings
into the interview mid-flight. Rejected: it violates FR-011's "no confirmation,
curation step, or continue/abort prompt between the findings and the first
question" by making the ordering nondeterministic, and it gives the fail-open
branch no moment at which to decide the reply is absent.

## R4. FR-013a's predicate — the guard's own test, read verbatim

**Decision**: The pre-chain rooting test is "does the supplied workflow path
resolve inside the current checkout", taken from the guard rather than restated.

**Source**:
`speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md:21-45`,
"Workflow Worktree Binding". Steps 1 and 2 are the whole predicate:

1. Resolve the current checkout with `git rev-parse --show-toplevel`.
2. If the supplied workflow path exists inside that checkout, continue.

**Rationale**: FR-013a requires the same predicate, not an equivalent-looking
one. The failure mode the spec names is concrete: a stale same-named workflow
file sitting in the parent checkout passes a naive root comparison **and** passes
the guard, so the guard continues and planning phases commit into the parent
checkout, usually `main`. A root-equality test would disagree with the guard in
exactly that case. Testing path resolution rather than root identity is what
makes the two agree by construction.

**Second half of the check**: `git status --porcelain` clean in that checkout.
This command already runs in Step 3.5 of both variants
(`speckit-pro/skills/speckit-scaffold-spec/SKILL.md:249` and
`speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md:254`), so FR-023's
no-new-machinery constraint holds: the check reuses two commands the skills
already run.

**Explicitly not tested**: the most recent commit. After Step 8 the newest commit
is the roadmap status flip, not the workflow-file commit, so a last-commit test
would fail on every correct run. FR-013a states this; the shipped Step 8 confirms
it (`skills/.../SKILL.md:491-493`, `codex-skills/.../SKILL.md:425-430`).

## R5. Caps, measured before and projected after

| Cap | Enforced at | Current | Constraint |
|---|---|---|---|
| Description ≤ 1024 chars | `tests/speckit-pro/layer1-structural/validate-skills.py:121-122` | 975, both platforms | Reword lands at **1015**, 9 chars headroom |
| Description has no angle brackets | `tests/speckit-pro/layer1-structural/validate-skills.py:124-125` | passes | Replacement sentence contains none |
| Codex body 500–8000 words | `tests/speckit-pro/layer1-structural/validate-codex-skills.py:168-171` | 3250 words | Additions must keep it under 8000; no `references/` may be added (FR-022) |
| Claude body | no word cap in Layer 1 | 2859 words | Tracked for symmetry only |

**Verification of the 1015 figure** (run in this worktree, not assumed): the
current description was read from the file, sentence 3 was replaced with FR-021's
replacement text, and the result measured at 1015 characters with no angle
brackets. The replacement is a pure sentence-3 substitution; sentences 1, 2, 4,
and 5 are untouched, which is what FR-021 requires.

**Headroom for the Codex body**: 4750 words. The planned additions are on the
order of 700–900 words, so the cap is not a binding constraint on this change.
The binding constraint is the 9-character description headroom.

## R6. Which pinned Codex sentences the FR-022 amendments must not break

**Decision**: All three FR-022 amendment sites are safe. None of the three
sentences is string-pinned by a validator.

**Evidence**: `tests/speckit-pro/layer1-structural/validate-codex-skills.py` pins
these scaffold-specific strings, checked by reading every `skill ==
"speckit-scaffold-spec"` branch in the file:

- picker metadata and heading naming (`:147-164`)
- the Grill Me native-picker guard: `picker-first HITL guard`, `request_user_input`, `default_mode_request_user_input`, `Do not ask the Grill Me question as a normal assistant`, `` If `request_user_input` is absent `` (`:173-183`)
- the referenced workflow template exists (`:212-214`)
- `allow_implicit_invocation: true` (`:398-402`)

`Do not run the autopilot at the end` is **not** pinned. Neither are the two
Output-section sentences forbidding hand-off from the parent checkout. FR-022
requires the latter two to survive verbatim anyway, prefaced rather than rewritten.

**Consequence for the plan**: the Step 4 Codex seeding edit must not disturb the
five pinned Grill Me strings, all of which live in the same step. The edit adds a
sentence about the scope input; it does not touch the picker guard.

## R7. Byte-identity of the two descriptions is unenforced

**Decision**: FR-021a's byte-identity must be verified by hand after both edits.
No automated test compares the two description strings.

**Evidence**: `tests/speckit-pro/layer1-structural/validate-codex-parity.py`
asserts version and marketplace parity, agent parity in both directions, skill
directory coverage, Codex metadata sidecars, and that every `../../skills/**.md`
reference in a Codex `SKILL.md` resolves. It does not read or compare frontmatter
description values. `validate-skills.py` and `validate-codex-skills.py` each
validate their own platform in isolation.

**Method**: the two files carry byte-identical descriptions today (both measured
at 975 characters and confirmed equal). The reword is one identical substitution
applied to both, so identity is preserved by construction — but FR-021a requires
re-verification rather than assumption, so the plan carries it as an explicit
verification step, not an inference.

## R8. Generated-artifact propagation

**Decision**: One `python3 scripts/refresh-release-artifacts.py` run covers every
generated copy. The Layer 6 digest chain is untouched.

**Measured copies of the description string** (tree-wide search, `.git` excluded):

```text
speckit-pro/skills/speckit-scaffold-spec/SKILL.md                                              (source, hand-edited)
speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md                                        (source, hand-edited)
dist/claude/speckit-pro/skills/speckit-scaffold-spec/SKILL.md                                  (generated)
dist/codex/speckit-pro/skills/speckit-scaffold-spec/SKILL.md                                   (generated)
tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/skills/speckit-scaffold-spec/SKILL.md   (generated)
tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-scaffold-spec/SKILL.md    (generated)
```

Exactly the four generated copies spec.md's Assumptions name, and no others.
`scripts/refresh-release-artifacts.py` rebuilds both payloads, content-syncs the
installed-cache fixtures, refreshes the proof-tree hashes, and regenerates the
payload-completeness, zero-Bash, and release-readiness evidence, per its own
module docstring.

**Payload path mapping, confirmed by diff**: the Codex payload **flattens**
`codex-skills/` into `skills/`. `dist/codex/speckit-pro/skills/speckit-scaffold-spec/SKILL.md`
is byte-identical to the Codex source. Both source edits therefore propagate
through the same generator run; neither needs separate handling.

**Layer 6 is not affected.** The corpus in
`tests/speckit-pro/layer6-efficiency/fixtures-codex/` binds a sha256 chain over
**agent** source bytes. FR-002 forbids adding or editing any agent definition, so
no agent byte changes and the chain stays valid. This is the specific reason Q2
chose reuse over a dedicated blind-spot agent.

## R9. A payload transform that constrains where Claude text may go

**Finding**: the Claude payload build strips a region of the Claude `SKILL.md`.
Text placed there ships to nobody.

**Evidence**: `speckit-pro/speckit_pro_runner/gates/payloads.py:379-391`,
`strip_codex_guard`, deletes every line from the `## Codex Skill-Selection Guard`
heading up to but not including the next `## ` heading. Confirmed by diffing the
source against `dist/claude/speckit-pro/skills/speckit-scaffold-spec/SKILL.md`:
lines 24-36 of the source are absent from the payload.

**Consequence**: the two summary lines currently living inside that region —
"Prepare a spec from the technical roadmap for autonomous execution." and
"Creates the worktree, branch, and workflow file — ready for
`/speckit-pro:speckit-autopilot`." — are **not** in the shipped Claude payload.
An implementer updating that summary to mention the pass and the chain would be
editing text the Claude runtime never sees.

**Planning rule derived**: every Claude edit site in this plan sits under
`## What to Do` or in the frontmatter. None is inside the stripped region. This
is recorded so the constraint is checkable rather than accidental.

## R10. Layer 2 fixture shape and the ASCII rule

**Decision**: Add three cases per platform to the two scaffold fixtures only,
in the existing `{query, should_trigger}` shape, ASCII-only.

**Measured**: both fixtures hold 16 entries, 8 positive and 8 negative, with
exactly two keys per entry. The two files differ **only** in em-dash encoding:
`tests/speckit-pro/layer2-trigger/evals/speckit-scaffold-spec-trigger.json` uses
the `—` escape at entries 15 and 31 of the pretty-printed file, while
`tests/speckit-pro/layer2-trigger/codex-evals/speckit-scaffold-spec-trigger.json`
uses the literal character. Nothing else differs.

**Why ASCII-only matters concretely**: FR-021b requires it, and the measurement
explains why. A new query containing an em dash would have to be written
differently in each file to preserve each file's convention, or would silently
change one file's convention. An ASCII query is written identically in both and
leaves the existing divergence exactly as it is. Post-change: 20 entries each,
10 positive and 10 negative. *(Originally 19 with a single negative. A fourth
case was added after implementation, on an independent review's finding that the
one negative stated its precondition explicitly and so tested the easy form of
the misroute rather than the likely one.)*

**Runner constraints, from spec.md Assumptions and confirmed against
`tests/speckit-pro/suite-manifest.json`**: Layer 2 is declared `"default": false`,
so `python3 tests/speckit-pro/run-all.py` prints its commands rather than running
them. Layer 2 is a scheduled manual gate, not part of FULL_VERIFY. The Claude
runner moves the operator's installed skill directory aside and restores it in a
`finally` block, so it must never run from a read-only or background agent.

## R11. The incidental citation defect

**Finding**: `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md:449` cites
`openai/codex#7480` as support for the `$skill-name` invocation form.

**Scope decision**: fix this file only, because it is the file being edited.
The same citation appears at `speckit-pro/codex-skills/grill-me/SKILL.md:289` and
`speckit-pro/codex-skills/speckit-coach/SKILL.md:25`. Both are named as follow-up
and left untouched — editing either would add a production file to a surface
FR-022 fixes at two, and grill-me is a file the design concept's Q3 and Q19
explicitly rule out changing.

**The miscitation is confirmed against the primary source, not assumed.**
`openai/codex#7480` is titled "Support for custom commands (custom slash
commands)", filed against the VS Code extension v0.4.46, and its body reads "the
extension only support general slash commands - but no custom commands". It is a
VS Code feature request. It does not discuss `$` versus slash syntax and cannot
support the sentence citing it.

**Correct support, also verified**:

- Official documentation, canonical at `https://learn.chatgpt.com/docs/build-skills` ("Build skills"). `https://developers.openai.com/codex/skills` returns HTTP 308 to it, and the page's own `<link rel="canonical">` names it. It states: "In Codex CLI or the IDE extension, run `/skills` or type `$` to mention a skill", and shows the worked form "In Codex, invoke it as: `$skill-creator`".
- `openai/codex#11817`, titled "CLI: `/<skill>` unrecognized while `$<skill>` invocation works", filed against Codex CLI 0.101.0, reproducing the exact contrast: `$prd` works, `/prd` returns "Unrecognized command".

**Correction chosen**: cite the documentation as the primary reference and
`openai/codex#11817` as corroboration. Documentation is the normative statement
of an invocation form and does not go stale when an issue is closed or
relabelled; the issue is retained because it demonstrates the negative half of
the claim, which the documentation states only implicitly. The corrected sentence
keeps the surrounding claim verbatim and changes only what it points at.

**One precision note carried into implementation**: the literal placeholder
`$skill-name` does not appear in the documentation, which writes `$skill` and
concrete examples. The existing sentence's use of `$skill-name` as a placeholder
is accurate as a pattern, so it stays; only the citation changes. Codex does
expose a generic `/skills` picker, but no per-skill `/<plugin>:<skill>` command,
so the contrast the sentence draws holds.

## Summary of decisions

| # | Decision | Drives |
|---|---|---|
| R1 | ART-006 contract read from git history; Codex runnable line is `$speckit-autopilot` + argv | FR-014, FR-019, FR-020 |
| R2 | Prompt-level framing is sufficient; Codex low-effort setting is a recorded residual risk | FR-002, FR-005, design concept Open Question |
| R3 | Dispatch then **await** the summary, per the house consensus pattern | FR-001, FR-002, FR-011 |
| R4 | Pre-chain rooting test is the guard's path-resolution predicate, plus a clean `git status --porcelain` | FR-013a |
| R5 | Description lands at 1015/1024; Codex body has 4750 words of headroom | FR-021 |
| R6 | No FR-022 amendment site is string-pinned; five Grill Me strings nearby are | FR-022 |
| R7 | Description byte-identity is unenforced and must be hand-verified | FR-021a |
| R8 | One `refresh-release-artifacts.py` run covers all four generated copies; Layer 6 unaffected | spec Assumptions |
| R9 | Claude payload strips the Codex-guard region; no edit site may sit there | FR-022 |
| R10 | Three ASCII-only cases per platform, in the two scaffold fixtures only | FR-021b |
| R11 | Fix the citation in the scaffold file only; name the other two as follow-up | incidental defect |

**No open clarification markers remain.** spec.md carried zero into this phase,
and the two questions the design concept routed to `/speckit-plan` are resolved
at R2 and R4.
