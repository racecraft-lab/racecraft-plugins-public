---
name: speckit-scaffold-spec
description: "Use this skill when the user wants to set up, scaffold, bootstrap, prep, initialize, or prepare a SPEC-ID from the technical roadmap for autonomous execution. Triggers on: set up SPEC-XXX, scaffold SPEC-XXX, bootstrap SPEC-XXX for development, prep SPEC-XXX, initialize the workspace for SPEC-XXX, prepare SPEC-XXX for the autonomous run, create a spec branch and workflow for SPEC-XXX, generate the workflow file for SPEC-XXX, I need a workflow file generated for SPEC-XXX, fill the prompts from the roadmap, pre-fill the workflow template, start working on SPEC-XXX, populate the workflow file for SPEC-XXX. Opens with a blind-spot pass, creates the git worktree, spec branch, Design Concept doc, and populated workflow file, then hands off to planning. Strictly interactive — requires a human to answer the grill-me questions. Not for checking roadmap status (use /speckit-pro:speckit-status), running a populated workflow (use /speckit-pro:speckit-autopilot), or SDD coaching (use /speckit-pro:speckit-coach)."
---

# SpecKit Scaffold Spec

## Installed Runtime Contract

Installed Claude and Codex surfaces resolve Python 3.11 or newer, invoke
`[resolved_python, "-m", "speckit_pro_runner"]`, send one JSON request on
stdin, read one JSON response from stdout, and surface stderr diagnostics.
Do not add a shell fallback, `jq` parsing path, Git Bash, WSL, or
PowerShell-specific command-language requirement for installed workflows.

## Capability discovery & grounding

Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `speckit-pro/skills/speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it.

## Scope

Use this skill when the user wants a SPEC-ID prepared for
`$speckit-autopilot`. This skill is responsible for the mutation-heavy
bootstrap step: identify the roadmap entry, create or reuse the correct
worktree branch, generate the workflow file, and leave the repository in a
state where the autopilot can start immediately.

If the user is still figuring out how to decompose a feature, write a
technical roadmap, or understand the SDD process, redirect them to
`$speckit-coach`. Do not invent roadmap data or phase prompts from vague
requirements when the roadmap entry does not exist.

## Artifact tiering (CONTRACT vs EXHAUST)

speckit-pro artifacts are tiered. **CONTRACT** artifacts (`spec.md`, `plan.md`,
`tasks.md`, `research.md`, supporting design artifacts) are review-visible and stay
at their existing location — this skill does not relocate them. The three authored
**EXHAUST** artifacts (the design-concept doc, the workflow file, and the UAT
runbook) are scaffolding, so they are written under a `.process/` directory:
the design-concept doc and workflow file land under `docs/ai/specs/.process/`, and
the UAT runbook lands under the feature's own `specs/<NNN>/.process/`. Nothing is
deleted — every relocated file still exists and is readable at its `.process/` path.

## O5 monster-epic fallback

Normal PRSG-007/008/009 routing, layer planning, and split-PR emission remain
the default path for oversized work. Describe or scaffold O5 only when the
roadmap/design-concept evidence says ordinary O4 split planning cannot produce
reviewable, independently ordered slices.

O5 v1 uses a review-visible CONTRACT parent manifest at
`specs/<parent-branch>/o5-parent-manifest.json`. Child specs stay flat siblings
under `specs/<child-branch>`; never create nested
`specs/<parent>/<child>` directories. Child `SPEC-MOC.md` frontmatter keeps
`up:` pointed at the roadmap. Add only curated body links to the parent
manifest and shared design concept; add retrospective links only after the
retrospective exists. Do not create child branches or worktrees automatically
from the parent scaffold — each child is scaffolded independently.

Before presenting O5 as ready, validate the manifest with:

```text
Run runner helper o5-topology for specs/<parent-branch>.
```

If topology is invalid, report the JSON `problems[]` and keep the operator on
normal re-slicing until the manifest is fixed.

## Tier-2 Legacy PROCESS Relocation Suggestions

Scaffold may encounter thawed legacy specs that predate the `.process/`
layout. It must only give static operator guidance; it must not run the
relocation codemod.

When inspecting an existing target or nearby legacy candidate, suggest Tier-2
relocation only when all of these are true:

- The candidate is in scope: a current namespace whose first dash-delimited
  segment is `prsg` or `spec`, or a legacy numeric/spec candidate that joins to
  the roadmap spine. Suppress candidates whose first segment is all-alpha and
  not `prsg`/`spec` with reason `non_speckit_namespace`, and suppress
  date-first legacy names matching `YYYY`, `YYYY-MM`, or `YYYY-MM-DD` prefixes
  with reason `date_named_legacy_namespace`.
- The candidate is thawed: `.specify/feature.json` does not name it by exact
  path or spec ID match. If it is named there, report `frozen/in-flight` and do
  not suggest relocation. If active-feature state is invalid, report that state
  and do not suggest relocation.
- The candidate is legacy and not already current: its `SPEC-MOC.md` does not
  already carry `structureVersion: 1`, and PROCESS artifacts are not already
  normalized under `.process/`.
- A root PROCESS allow-list artifact or matching docs-side scaffold artifact is
  present. If none exists, report that no Tier-2 action is needed.

For the one eligible thawed candidate, report the candidate and the runtime gap
with the real `specs/<spec-dir>` value substituted:

```text
Tier-2 relocation candidate: specs/<spec-dir>.
Deferred: relocate-process-artifacts has no authoritative runner request and is unavailable.
```

Do not invoke the deferred operation, advertise either runner mode, or invent a
replacement command. Leave the PROCESS artifacts unchanged. This advisory gap
does not block the remaining scaffold workflow, but it must be recorded.

> **Codex implicit-trigger note (eval harness vs production):** Layer 2 trigger evals score this skill at 69% (11/16) on the Codex selector — but POS is a perfect 8/8 (every "scaffold SPEC-009" / "create a new spec branch" / "prep SPEC-022 for autopilot" query fires correctly). All 5 NEG misses are false-positives in single-skill staging where the harness loads only this skill, so the Codex selector has no alternative to route adjacent SDD queries to ("roadmap status" / "what's the progress on SPEC-009" → should go to `$speckit-status`, "run the fully populated workflow" → `$speckit-autopilot`, "resolve PR review comments" → `$speckit-resolve-pr`). In production all six speckit-pro skills are loaded together and Codex routes those queries to their proper destinations. The eval results under-report real-world accuracy; positive-trigger reliability is the operationally-relevant number. (This skill was renamed from `speckit-setup` in v1.12; the rename did not regress trigger behavior — same POS pass rate as before.)

## Input

Accept:

- a required `SPEC-ID` such as `SPEC-009`
- an optional technical roadmap path if the user already knows it
- an optional worktree root override if the repository uses a nonstandard
  location

If the request does not include a SPEC-ID, stop and ask for it. Everything
else should be derived from the repository.

## Hard Constraints

- Never commit or push `main`.
- Detect the actual git remote name before pushing.
- Create or reuse a dedicated worktree branch for the spec.
- After the worktree exists, perform all file edits inside the worktree, not in
  the main checkout.
- Use the shared workflow template shipped with this plugin. Locate it at
  `skills/speckit-coach/templates/workflow-template.md` relative to the
  speckit-pro plugin root directory.
- Do not leave placeholder tokens such as `SPEC_ID`, `SPEC_NAME`, or empty
  phase prompts in the generated workflow.
- Never run the autopilot at the end. Setup stops once the workflow is ready,
  committed, and pushed, and prints the hand-off command the `## Output` section
  defines. The operator runs it.
- Always run the `$grill-me` interview before writing the workflow file. The
  Design Concept doc is a required setup output, not optional. Setup must not
  attempt to fabricate design-concept content if grill-me aborts.

## Procedure

### -0.5 Verify Codex Agent Install

Before parsing or mutating the repository, resolve the plugin root and verify by
running the promoted `install-codex-agents` helper in `dry_run` mode against the
selected `.codex/agents/` or `~/.codex/agents/` destination and its installed
model choice. The plan must show every bundled TOML, including
`uat-runbook-author.toml`, as current. If any required file is missing or stale,
STOP, instruct the user to run `$install`, restart Codex, and then retry
scaffold. Do not apply the repair inside scaffold because this process cannot
reload changed custom agents safely.

### 0. Ensure SpecKit CLI

Before parsing or mutating the repository, verify the official SpecKit CLI is
available:

```text
PATH="${HOME:+$HOME/.local/bin:}/opt/homebrew/bin:/usr/local/bin:${PATH:-}"
command -v specify
```

If it is missing and `uv` is available, install it:

```text
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
```

If `uv` is unavailable or installation fails, stop and report the exact install
command for the operator to run. Do not continue with setup without the
`specify` command.

Do not run `specify init --here --force` automatically. Project initialization
and forced refreshes can overwrite managed files; setup may recommend the
command when `.specify/` is missing, but it must not run it without explicit
operator approval.

### 1. Locate the technical roadmap

Search for the roadmap before asking the user where it lives. Check likely
paths such as `docs/ai/`, `docs/ai/specs/`, and any file matching
`*technical-roadmap*` or `*roadmap*`. If no roadmap exists, stop with a short
message telling the user to create one with `$speckit-coach`.

### 2. Parse the requested roadmap entry

Read the section for the requested `SPEC-ID` and extract the data needed to
seed the workflow:

- spec name
- spec number
- short branch slug
- priority
- dependency information
- current status
- scope description and any constraints
- any tool count or tool names already recorded in the roadmap

If the spec is missing, stop and report the available pending specs. If the
spec is already complete, warn the user and stop. If the roadmap says the spec
is already in progress, prefer reusing the existing worktree branch rather than
creating a second setup.

Before creating the worktree, run the reviewability setup gate against the
roadmap or extracted spec entry:

```text
Run runner helper reviewability-gate in setup mode for <technical-roadmap-path>.
```

If the gate returns `block` without a ratified split exception, stop setup and
tell the user which threshold requires decomposition. Warnings may proceed only
when the generated workflow records the budget result and split decision.

### 3. Prepare the branch and worktree

Before `git worktree add` or any artifact or roadmap write, invoke the read-only
runner helper `resolve-scaffold-worktree-placement` with the deterministic
single-segment `branch_name` and, only when the user supplied one, the
`worktree_root_override`. Require `placement_status=resolved` and either
`relation=same` or `relation=descendant`. On `conflict` or `invalid`, report
`problems[]` and STOP. On `relation=external`, report the canonical registered or
proposed `worktree_root` and STOP before mutation; an explicit override is not
permission to escape the current task workspace.

Without an override, the helper derives exactly
`TASK_ROOT/.worktrees/<branch-name>`, where `TASK_ROOT` is the canonical current
Codex task checkout. Never derive worktree placement from
`git rev-parse --git-common-dir`, the primary checkout, or the first
`git worktree list` record. Use the helper's returned absolute `worktree_root`
unchanged for every create or reuse decision.

Before any git mutation, inspect the actual remotes with `git remote -v`.
Never assume `origin`. Then honor the helper disposition:

1. On `disposition=reuse`, reuse the returned registered worktree. Do not move,
   recreate, duplicate, or prune it.
2. On `disposition=create`, check whether the intended branch exists locally
   and on every actual remote. If more than one remote carries the branch, STOP
   as ambiguous. If it exists locally, add the returned worktree for that local
   branch. If it exists on one remote only, create the local tracking branch in
   the returned worktree. If it exists nowhere, create it while adding the
   returned worktree.
3. Never substitute a different path because branch creation or remote lookup
   is inconvenient; rerun the resolver if live state changes.

Use a deterministic branch naming scheme based on the spec number and short
slug, for example `009-search-database`. Verify the active branch inside the
worktree before continuing. Re-run `resolve-scaffold-worktree-placement` after
worktree creation and again before bootstrap or Grill Me on either the create
or reuse path. Require `placement_status=resolved`, `disposition=reuse`, the
identical canonical `task_root`, `worktree_root`, and `branch_name`, and
`relation=same` or `relation=descendant`. STOP before bootstrap or Grill Me if
any field drifts.

### 3.5. Bootstrap the worktree (in the worktree)

A fresh worktree has only tracked files — no installed dependencies, no build
outputs, no code indexes. Checked-in agent config (for example a project-scoped
MCP server that runs a local build) can silently fail to start until the
worktree is bootstrapped, and the spec session then runs without the project's
code-intelligence tooling.

1. Check the project's AGENTS.md / CLAUDE.md for a worktree preflight or
   bootstrap section (for example "Spec-worktree preflight"). If it documents
   commands, display the exact commands and wait for explicit operator approval
   before running them. Do not treat the presence of AGENTS.md / CLAUDE.md as
   approval. Run only the approved commands from the worktree, in order.
2. If no explicit bootstrap/preflight commands are documented, do not infer an
   install/build/index sequence. Report that no bootstrap is documented and ask
   the operator before running any package install, build, or index command.
3. If the project documents a code index or MCP prerequisite (for example:
   build, then the project's documented index-init command), run only the
   documented commands after explicit approval and verify the documented health
   check passes.
4. After any bootstrap command, run `git status --porcelain` in the worktree. If
   unexpected tracked changes appear, stop and report them before continuing.

Report what was bootstrapped — or that the project documents nothing — in the
scaffold summary. Never skip this silently: an unbootstrapped worktree is how
spec sessions end up running without the project's tooling.

### 3.6 Blind-spot pass (in the worktree)

**This step is mandatory.** Every `$speckit-scaffold-spec` invocation runs the
blind-spot pass from the worktree, immediately before the grill-me interview.
There is no skip flag, no skip argument, and no documented path that reaches the
interview without attempting the pass. Mandatory to **attempt**, not to succeed:
the pass fails open, as the end of this step sets out.

**Engine.** The pass runs on the already-shipped read-only `codebase-analyst`,
consumed unmodified. Do not add or edit an agent definition on either platform.
Never add Grep, Glob, or Bash to this skill's tool surface: this step needs
**no new tool grant**.

**Dispatch, then await.** Dispatch with `spawn_agent`, using
`agent_type: "codebase-analyst"` and `fork_turns: "none"`, then poll
`wait_agent` in a bounded loop until the actual summary is delivered. The Seed
below is a self-contained task package, so the analyst does not need inherited
turns. Never omit `fork_turns` and never use `fork_turns: "all"` while selecting
this custom agent: a full-history fork inherits the parent agent type and Codex
rejects the incompatible override. A status update, an unrelated mailbox wake,
or a terminal status without a delivered result is **not** the result. Call
`close_agent` only when that action is exposed. The await completes BEFORE the
interview starts.

**The bound. A single expired poll is not the deadline.** Abandonment is governed
by one execution deadline for the whole pass:

| Bound | Value | On expiry |
| ----- | ----- | --------- |
| Per-poll timeout | whatever the surface provides | keep waiting; **not** a verdict |
| Pass execution deadline | **5 minutes from dispatch** | abandon the wait and record the `did not run` outcome with reason `wait deadline expired` |

Consecutive expired polls are the loop's **cue to check the five-minute
execution deadline**, not a second independently-triggering bound, and this cue
has no Claude-side counterpart. "No reply at
all" has one observation point: the loop ended without a summary, or the deadline
expired. Never infer it from a dispatch still running. A summary arriving
**after** the deadline does not change the recorded outcome.

**Seed.** Read three things from the roadmap entry step 2 already parsed:

| Seed element | Status | When absent |
| ------------ | ------ | ----------- |
| The entry's Scope text | **required** | The `**Scope:**` label is not universal, so read the scope text rather than matching a heading |
| The entry's dependency chain | **required when the entry declares one, under any heading** | Read a renamed variant such as `**Deps:**` as the chain. Only when no declaration exists in any spelling, append the label with the literal `none`. Never skip, never report a gap, never infer a chain |
| The `Key Files` section | **optional hint** | Omit the label entirely and continue. Never report a gap, never skip |

**The two absent-field behaviours differ on purpose. Do not collapse them.**
`Key Files` is a hint whose absence carries no information, so its label is
dropped. A missing `Depends On` **is** information, so the literal `none` is
written instead: reading a renamed `**Deps:**` as absent would put `none` in the
payload for an entry that names several — a false statement rather than a
missing one.

**Payload assembly.** Two parts, in this order: the dispatch block, then the
appended seed material under these literal labels:

```text
Scope:
<the roadmap entry's Scope text>

Depends On:
<the entry's dependency chain, read under whatever heading it carries — the literal `none` only when the entry declares no dependencies under any heading>

Key Files:
<the Key Files section — this label and its text are omitted entirely when the entry has none>
```

The block's own words "the Scope text below" refer to exactly this appended
material, so the order is fixed. **Nothing else is appended**: no operator
commentary, no prior findings, no spec text. Each `Depends On` spec whose
artifacts are not in the working tree is chased into git history rather than
reported absent — an archive sweep removes files, not history.

**The dispatch block, carried verbatim.** It is byte-identical to the Claude
copy: the shipped `codebase-analyst` description frames the agent for autopilot
consensus resolution, so this block carries the whole framing. Send it first,
then the appended material. Do not paraphrase it, and do not normalise the
one-word `blindspot pass` or `unknown unknowns`. Never ask the operator about
their familiarity: their structural position is stated as fact, not asked.

```text
You are running a blindspot pass for <SPEC-ID>: surface the unknown unknowns
in this roadmap entry before its scoping interview.

The operator has read this roadmap entry and its scope. They have not
necessarily read the affected code area, or the archived artifacts of its
dependencies.

Seed (required): the Scope text below, and each spec named in Depends On.
Seed (optional hint, may be absent): the Key Files section.
For each Depends On spec whose artifacts are not in the working tree, chase
it into git history rather than reporting it absent.

Return at most 5 findings, ranked by impact then surprise. Each finding:
N. **<Title>** - 1-3 sentences, plus a repo-relative file or path pointer.
   Impact: <what requirement or design decision this would change if true>
   Surprise: <why the roadmap entry's own text does not already say this>
Then state how many findings you set aside, including when that number is 0.
If you find nothing, reply exactly: The blindspot pass raised no unknown unknowns.
```

**Classify the reply. Three disjoint outcomes, no judgement call.** A reply is
**usable** when it carries at least one finding in the fixed shape, **or** the
literal sentence `The blindspot pass raised no unknown unknowns.`

| Outcome | Test |
| ------- | ---- |
| **Ran** | a finding in the fixed shape **or** the sentinel came back |
| **Returned nothing usable** | a reply came back carrying neither |
| **Did not run** | no reply at all — dispatch error, empty return, or the execution deadline expiring |

**"A finding in the fixed shape"** means a numbered item carrying a title and at
least one of the two rationale lines; a numbered title with neither fails the
test. **A single expired poll is not the third outcome** — only the pass
execution deadline expiring abandons the wait.

**Cap, ranking, and the set-aside count.** At most five findings, and the cap is
**not operator-configurable**. **Scaffold enforces the cap on what it renders**,
because the reply is model output and cannot be relied on to obey: when more than
five come back, show the first five **in the analyst's own order**, count the
remainder, and state that count through the truncation string below. Never
re-rank, merge, or rewrite findings to fit — the ranking is the analyst's,
ordered by impact with surprise as the tiebreak. **No numeric score** is
assigned.

**Always state the set-aside count, including when it is zero**, in one of these
three shapes:

```text
Showing the 5 highest-impact findings; N more were set aside
Showing all N findings; none were set aside
The blindspot pass raised no unknown unknowns.
```

When five or fewer findings come back and the analyst still names a non-zero
set-aside count, the second shape carries that count in place of `none`:
`Showing all N findings; M more were set aside`. Without it the printed line
would claim none were set aside while the design-concept record below states
`M`, which is exactly the drift one vocabulary exists to prevent.

The third is the **sentinel echoed verbatim** — one string doing two jobs, the
analyst's signal and scaffold's line to the operator — so no second wording for
"found nothing" can be invented.

**The two degraded outcomes get one status line each:**

```text
The blind-spot pass returned nothing usable; continuing without findings. Reason: <reason>
The blind-spot pass did not run; continuing without findings. Reason: <reason>
```

`<reason>` is one short clause naming what was observed, drawn from this
vocabulary: `reply carried neither a finding nor the sentinel`,
`dispatch error: <message>`, `empty return`, or `wait deadline expired`.
**Exactly one of the five status lines above is emitted per run**, and the same
`<reason>` clause is reused verbatim in the design-concept header line below, so
the printed record and the durable record cannot give different reasons.

**The one-word spelling inside the sentinel is deliberate. Do not normalise it.**
Where scaffold speaks in its own voice — the two degraded lines above and the
`**Blind-spot pass:**` header key below — the term is hyphenated, so one run can
show both spellings. It reads as a typo and is not. The sentinel is matched
**literally**: normalising it to `blind-spot` breaks the usable-reply test
silently, on exactly the runs where the pass worked.

**Fail open.** Do **not** treat the dispatch outcome as a gate, and do **not**
retry-then-halt. If the dispatch fails or returns nothing usable, continue into
the interview with nothing seeded, and record the gap and its reason in **both**
sinks: the operator status line above, which scaffold prints, and the
design-concept header line below, which step 4 verifies and repairs.

**"Nothing seeded" means no findings are seeded. It does not mean the labelled
block is omitted.** The block still travels in all three outcomes, carrying only
its status line in the degraded two; omitting it there would leave the "did not
run" record with no mechanism to be written at all.

**The seeded block — one shape, two appearances.** Findings reach the interview
as a labelled block appended to the scope input step 4 **already** passes. The
block uses one shape in both places it appears — the operator output and the
seeded scope string — so the two records cannot drift:

```text
--- BLIND-SPOT PASS FINDINGS ---
<the numbered findings, or the status line for the outcome>
<the set-aside line, present only when findings are shown>
Record the Blind-spot pass line in the design concept's header blockquote.
Treat each finding as a candidate question; any finding not reached becomes an Open Question.
--- END BLIND-SPOT PASS FINDINGS ---
```

**The second line is the only conditional one.** It is present in the two shapes
that show findings, and omitted when the sentinel came back (that sentinel is
already the line above it) and in the two degraded outcomes, which have no
set-aside count. The delimiters and the two closing instructions **never vary**,
which is what lets the block keep one shape in all three outcomes.

**Two of the block's lines address the interview, and the operator sees them.**
That cost is accepted rather than overlooked. **Do not resolve it by forking the
two copies**, softening the imperatives in one, or dropping them from the printed
half: any of those is the drift one shape exists to prevent. The second closing
instruction is how no finding is dropped silently — one the interview resolves
becomes an entry in the existing question-and-answer record, and one it does not
reach becomes an Open Question.

**The design-concept record.** One line in the design concept's **existing**
header blockquote, under the key `**Blind-spot pass:**` — hyphenated, because
that is scaffold's own voice — recording exactly one of the three outcomes:

```text
> **Blind-spot pass:** ran — N findings surfaced, M set aside
> **Blind-spot pass:** returned nothing usable — <reason>
> **Blind-spot pass:** did not run — <reason>
```

The word immediately after the key is the discriminator, drawn from the closed
set `ran`, `returned nothing usable`, `did not run`. `<reason>` is the **same
clause** the status line above carried. A pass that ran and raised nothing is the
first shape with `N` and `M` both zero, which is what distinguishes it from one
that never ran. This key needs no schema change. Do **not** add a section to the
design concept, do **not** write a separate findings artifact — specifically not
`.process/<SPEC-ID>-blind-spots.md` — and do **not** change what the interview
produces.

**Presentation is informational.** The run flows straight from the findings into
the first interview question. **No confirmation, no curation step, no
continue/abort prompt** between the two.

### 4. Run the Grill Me interview (in the worktree)

Before writing the workflow file, run an iterative scoping interview so the
Specify and Clarify prompts can be enriched from human-validated answers. Use
the spec scope description from the technical roadmap (and any constraints,
dependencies, or stated tools) as the input, with the step 3.6 BLIND-SPOT PASS
FINDINGS block appended below it.

Invoke `$grill-me` from inside the worktree with a setup-mode marker so it
knows to:

- Write its Design Concept doc to
  `docs/ai/specs/.process/SPEC-<ID>-design-concept.md` inside the worktree
- Surface the key answers (Goals, Non-goals, major design decisions) back to
  this skill so step 6 can fold them into the workflow prompts

The labelled block is the **only** channel the pass uses into the interview, and
it travels in all three step 3.6 outcomes — carrying only its status line in the
degraded two. Do not add a new interview argument, do not change what the
interview produces, and never edit any file under the grill-me skill on either
platform. The scope input already exists; this appends to it.

Codex grill-me uses a picker-first HITL guard: it must call
`request_user_input` for each Grill Me question. In Codex Default mode this
requires the `default_mode_request_user_input` feature to be enabled before the
thread starts or resumes. Do not ask the Grill Me question as a normal assistant
message, progress update, or final response. If `request_user_input` is absent
or unavailable, stop setup and tell the user to run
`codex features enable default_mode_request_user_input`, restart Codex or open a
new thread, then rerun `$speckit-scaffold-spec <SPEC-ID>`. A nonzero shell
`tty -s` result is not enough to stop a live Codex conversation, but a missing
native picker is a config prerequisite failure. Do not try to drive grill-me from
`codex exec` or any non-interactive runner — it will refuse and write nothing.

If grill-me aborts (no interactive runtime), stop setup and report the
condition. Do not synthesize design-concept content yourself.

After the interview returns, verify the durable record and repair it when
absent:

1. Read `docs/ai/specs/.process/SPEC-<ID>-design-concept.md` in the worktree —
   `<ID>` being the roadmap identity in full, including whatever namespace prefix
   it carries — and confirm it carries the `**Blind-spot pass:**` key in its
   header blockquote. Reading a path the run never wrote would report the key
   absent and repair a file that does not exist.
2. If the key is missing, edit the step 3.6 header line into that existing header
   blockquote from the values already held at the moment the status line was
   rendered — the outcome, the `<reason>` clause, and N and M for the `ran`
   outcome. Nothing is derived a second time.

The interview is the writer of first resort, but the request is one sentence
inside a prose block handed to another skill, so verify rather than assume. Read
to check and edit to repair: no new tool grant, no new machinery, no new section,
no separate findings artifact, and no grill-me edit. When the interview does not
return, nothing is owed — the run stops, so no design concept exists to carry a
record and the step 3.6 status line is the only one.

### 5. Copy the workflow template into the worktree

Before copying the workflow template, require the generic
`speckit-pro-reviewability` preset to already exist inside the worktree.
`ensure-reviewability-preset` is deferred and unavailable; do not invoke it or
claim setup generated preset files. If the preset is absent, STOP and report the
deferred capability gap.

After confirming the preset is present, verify template resolution from the
worktree:

```text
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

Each command should resolve to `.specify/presets/speckit-pro-reviewability/`
or to a project-specific higher-priority override that intentionally includes
the reviewability sections.

Create the destination directory inside the worktree, typically
`docs/ai/specs/.process/` (created when absent so the first exhaust artifact
lands correctly), then load the shared workflow template from the plugin. Do
not author a new template from scratch. The generated file should live at a
path like `docs/ai/specs/.process/SPEC-009-workflow.md` inside the worktree.

### 5.5. Write the SPEC-MOC marker (in the worktree)

Write a minimal `SPEC-MOC.md` navigation marker into the spec's CONTRACT
directory on EVERY new spec, regardless of how many slices it will ultimately
have (single-slice specs get the marker too — it is the version-gate carrier).

This marker is a CONTRACT artifact: write it to `specs/<branch-name>/SPEC-MOC.md`
— NOT redirected to `.process/`, and NOT written to `docs/ai/specs/`. Create the
contract directory if it is absent (`mkdir -p specs/<branch-name>/`); scaffold
owns this early creation. Name the directory from the branch (NOT auto-numbered)
so the `spec_id` namespace-matches the directory.

Load the shared spec-MOC template from the plugin at
`skills/speckit-coach/templates/spec-moc-template.md` (the template is a single
shared, runtime-agnostic copy — do NOT duplicate it under `codex-skills/`).
Token-substitute it with the same `{{TOKEN}}` mechanism used for the workflow
template:

- `{{ROADMAP_TITLE}}` — a short link text for the roadmap (e.g., the spec series
  name + " roadmap")
- `{{ROADMAP_FILENAME}}` — the existing `*-technical-roadmap.md` filename without
  the `.md` extension
- `{{SPEC_ID}}` — the roadmap identity, e.g., `PRSG-002` (must namespace-match
  `<branch-name>`)

The written marker MUST carry a non-empty, quoted relative `up:` markdown link
pointing at the existing `*-technical-roadmap.md` — from `specs/<branch-name>/`
this resolves as `../../docs/ai/specs/<roadmap-filename>.md` (the
`../../docs/ai/specs/` prefix is hardcoded in the template; only the filename is
tokenized), NEVER a `[[wikilink]]` — plus `structureVersion: 1` (carried verbatim
from the template, with its "keep in sync with the lint scripts' hardcoded
literal" comment) and a `spec_id` that namespace-matches the contract directory.

### 6. Populate the workflow file

Replace all placeholders using the roadmap data. At minimum populate:

- `SPEC_ID`
- `SPEC_NAME`
- `BRANCH_NAME`
- tool count and tool names if the roadmap provides them

Then seed each phase prompt with concrete, spec-specific context rather than a
generic placeholder. Use **both** the roadmap scope/dependencies and the
Design Concept doc produced in step 4 (`SPEC-<ID>-design-concept.md`) to fill:

- Specify prompt — fold in Goals, Non-goals, and the user-validated design
  decisions from the Q&A log
- Clarify session focus areas — pull from the Open Questions section of the
  design concept
- Plan prompt — combine CLAUDE.md tech stack, constitution, roadmap scope,
  AND architecture/data-model/constraint decisions extracted from the design
  concept Q&A log. Quote the chosen answer for any decision driving a
  planning choice. Reference the design concept doc path as well.
- Checklist domain suggestions — based on roadmap scope plus the design tree
  branches the grill-me interview walked
- Tasks prompt — reference spec.md, plan.md, AND the design concept doc.
  Use Non-goals to bound task generation; use Q&A "why" context to inform
  task ordering and TDD test specifications.
- Analyze prompt — cross-artifact consistency check across spec.md, plan.md,
  tasks.md, AND the design concept doc. Flag drift between Goals / Non-goals /
  decisions and downstream artifacts. The design concept is the source of
  truth for scoping decisions captured during grill-me.
- Implement prompt — reference tasks.md, plan.md, AND the design concept
  doc. Consult the Q&A log for the "why" behind decisions; this informs
  test specifications, edge-case handling, and refactor choices.

The prompts should be strong enough that `$speckit-autopilot` can execute
without the user hand-editing obvious missing context. The design concept is
the primary enrichment layer; the roadmap scope is the seed. If a critical
detail cannot be derived from either, stop and report the gap rather than
filling it with fiction.

### 7. Commit and push from the worktree

Stage the generated/updated preset files when present, plus the design concept
doc, the workflow file, AND the SPEC-MOC marker in the worktree branch (the
marker is a review-visible CONTRACT artifact — if it is written but left
untracked it never reaches the PR). Create a focused setup commit and push that
branch to the detected remote:

```
git add .specify/presets/speckit-pro-reviewability \
        .specify/presets/.registry \
        docs/ai/specs/.process/SPEC-<ID>-design-concept.md \
        docs/ai/specs/.process/SPEC-<ID>-workflow.md \
        specs/<branch-name>/SPEC-MOC.md
git commit -m 'chore(SPEC-XXX): add design concept and workflow for autopilot'
```

If the preset was already present and unchanged, the add command may include
only the design concept, the workflow, and the marker:

```
git add docs/ai/specs/.process/SPEC-<ID>-design-concept.md \
        docs/ai/specs/.process/SPEC-<ID>-workflow.md \
        specs/<branch-name>/SPEC-MOC.md
git commit -m 'chore(SPEC-XXX): add design concept and workflow for autopilot'
```

Then verify:

- both files exist in the worktree
- placeholders are gone from the workflow file
- `git rev-parse --abbrev-ref HEAD` shows the spec branch
- `git log --oneline -1` shows the setup commit

### 8. Update roadmap status in the worktree

Update the technical roadmap copy inside the worktree to mark the spec as in
progress. Commit and push that roadmap status change on the same spec branch.
Do not touch the main checkout. The roadmap change reaches the default branch
only when the spec branch is merged.

## Output

Finish with a concise scaffold report that includes:

- the spec name and ID
- branch name
- worktree path
- design concept path
- workflow path
- remote branch that was pushed
- bootstrap result from step 3.5, including commands run and health check, or
  `no documented bootstrap`
- the absolute worktree root from `git rev-parse --show-toplevel` run inside
  the worktree
- the exact next step: continue in this same Codex task by running the hand-off
  command below with the absolute workflow path

Never hand off only the inner workflow path from the parent checkout. The
absolute workflow path identifies the generated spec worktree; autopilot binds
all execution there and never treats main, a detached checkout, or the parent
checkout as its mutation root.

**The hand-off to the planning stage.** It extends this section rather than
becoming a new numbered step, and it sits after step 8, once the design concept,
the workflow file, the SPEC-MOC marker, and the roadmap status flip are all
committed and pushed. Placing it earlier is rejected for a stated reason: a
planning stage that fails or is interrupted must never leave the roadmap
claiming the spec is still Ready.

**Scaffold never invokes the autopilot. It prints the command; the operator runs
it as the next message in the same task.** A skill body invoking a sibling skill
mid-session is unverified on Codex, and on Claude Code the
autopilot skill carries `disable-model-invocation: true`, documented as "Only
you can invoke the skill" — a deliberate setting, because a seven-phase
autonomous run that commits as it goes is exactly the kind of side effect an
operator must trigger themselves. Printing a command that always works beats
shipping an invocation that may not. **Never state that accepting silently runs
the planning phases; the operator explicitly starts them with the printed
command.**

**Run the hand-off check first. Two read-only tests.** They do not gate the
hand-off — one is always printed. They select its form and decide whether a
warning travels with it.

```text
1. Invoke the read-only `resolve-workflow-binding` runner helper with the
   canonical absolute generated workflow path. Require `binding_status=resolved`,
   the generated worktree as `workflow_root`, and `relation=descendant` (or
   `same` only when scaffold was already running from that worktree).
2. Confirm `git status --porcelain` is clean in the returned `workflow_root`.
```

Step 1 uses the same authoritative helper as autopilot. The absolute path is
required even when the same relative path exists in the parent checkout: a
stale parent copy must not win resolution and redirect planning commits to
main.

**What the check must NOT test: the most recent commit.** After step 8 the newest
commit is the roadmap status flip rather than the workflow-file commit, so a
last-commit test would fail on every correct run. Both commands are read-only, so
this check adds no machinery.

**What each result selects:**

| Check result | Effect on the hand-off |
| ------------ | ---------------------- |
| Step 1 passes | print the same-task absolute command below |
| Step 1 fails | print the new-task recovery; never claim same-task execution is safe |
| Step 2 fails | add one line naming the uncommitted changes as something to resolve first |

**Print one line before asking.** The question and both option labels name
"planning", a term the operator has not been shown the meaning of. State three
facts and no more: the planning stage runs the six SDD phases and commits as it
goes; scaffold prints the command rather than running it, so the operator starts
it themselves; and declining leaves everything already pushed exactly as it is.
It is printed rather than asked, carries no options, and does not count against
the budget below.

**Then ask exactly one confirmation, structured.** It records whether the
operator is continuing now. It does not decide whether anything runs, because
nothing does. Use `request_user_input` when it is present:

```text
Question: Scaffold is complete and pushed. Are you continuing into planning now?
Options, two, mutually exclusive, in this order:
  1. Continue now (Recommended)
  2. Stop here
```

The recommended answer comes first, per house convention. Both answers are fully
non-destructive, and both print the same command; the answer selects only how the
closing report frames it. Never fall back to parsing a free-text reply. When the
session exposes no structured confirmation mechanism, skip the question and print
the report — the hand-off does not depend on it. **The budget counts what this
step adds**: exactly one confirmation. Step 3.5's bootstrap approval and the
grill-me questions are pre-existing, are not counted, and are not removed.

**The hand-off command has one fixed form:**

| Platform | Hand-off command |
| -------- | ---------------- |
| Claude Code | `/cd <absolute-worktree-root>`, then `/speckit-pro:speckit-autopilot <relative-workflow-file> --stage plan` |
| Codex CLI | `$speckit-autopilot <absolute-workflow-file> --stage plan` |

The Codex form is the ordinary same-task outcome. OpenAI documents worktrees as
separate checkouts and Handoff as movement between Local and a task's associated
worktree, including returning that task to the same associated worktree; it is
not an arbitrary filesystem-path selector:
<https://learn.chatgpt.com/docs/environments/git-worktrees>. This hand-off does
not pretend to move the task or change its checkout. Autopilot instead binds
every operation and agent explicitly to the registered nested `WORKFLOW_ROOT`.
If Step 1 cannot prove that binding, print this recovery instruction instead:

```text
Open a new Codex task rooted at <worktree>, then run $speckit-autopilot <absolute-workflow-file> --stage plan.
```

The leading `$speckit-autopilot` token is the invocation form this skill set
uses: Codex skills are invoked via `$skill-name`, never via a
`/<plugin>:<skill>` slash command. The Claude Code row above is recorded for
cross-platform parity only; never print it from this variant.

The stage token is the literal lowercase `plan`, from the closed vocabulary
`plan`, `implement`, `full`. No aliases, no alternate casing, no long-form
spellings. The workflow file path is the **sole** hand-off token and is absolute
in the Codex form: never pass a state file, branch name, feature directory, or
environment variable across the boundary.

**Nothing is rolled back on any path.** Everything scaffold owns is committed and
pushed before this step runs, so the operator who stops here loses one command
and no work.

### The closing report

**One report, rendered on every ending the run can reach.** Since scaffold never
invokes the autopilot, every run ends here, and the report is always owed:

```text
1. The operator is continuing into planning now.
2. The operator stopped here.
3. No structured confirmation mechanism was available, so nothing was asked.
```

The report is **printed, not written to a file.**

**Contents, closed at four elements, in this order:**

```text
## <heading>

**Outcome:** <one line>
**Draft PR:** none, because draft-PR creation is not part of this release

**Artifacts:**
- <repo-relative path>     (one line each; only paths that exist)

**Next step:** <one command>
```

**The heading is one fixed string, `## Ready for Planning`.** It is true on all
three endings: scaffold's own work is finished and pushed, and the planning stage
is the next command whether the operator runs it now or later. It leads with what
is finished rather than with a negation, because none of the three endings is a
failure and none is the operator's fault.

**Fixed, conditional, and derived.** The heading and the draft-PR line are fixed,
except that the draft-PR line is conditional on a URL existing. The outcome line,
the artifact index, and the next step are **derived** — each has its own rule
below. `<one command>` denotes one fixed string, not a bare invocation: it is the
hand-off command in the form the check selected, so its Codex form carries the
rooting precondition. The slot stays one line.

**The set-aside findings count MUST NOT appear here.** The list is closed at four
elements; that count lives in the design concept's header record and in the
seeded block, and the artifact index points at the file carrying it.

**The two reports must not restate the same fields**: no worktree path, no remote
line, and no bootstrap result here — the scaffold report above already gave all
three, and the closed list admits none of them. The pushed branch appears once,
as an index entry, never as a repeated header field.

**The outcome line, one per ending.** One heading covers all three, so the
outcome line is where they are told apart. The index and the next step are the
same on all three, because no planning stage ran in any of them:

| Ending | Outcome line states |
| ------ | ------------------- |
| The operator is continuing now | everything scaffold owns is committed and pushed, and the planning stage is the next command |
| The operator stopped here | the run stopped at the operator's request, everything scaffold owns is committed and pushed, and nothing was rolled back |
| No structured confirmation mechanism was available | the question was not asked because the session exposes none, everything scaffold owns is committed and pushed, and nothing was rolled back |

Every line closes on **everything scaffold owns is committed and pushed**, the
fact the operator most needs.

**When the cleanliness test failed, the outcome line carries one added clause**
naming the uncommitted changes as something to resolve before running the next
command. It is a clause on an existing element rather than a fifth element, and
it is the only check result that reaches this report as text — the rooting result
reaches it inside the next-step command instead.

**The draft-PR line.** Show the URL when the run produced one. Otherwise state
plainly that there is none:

```text
**Draft PR:** none, because draft-PR creation is not part of this release
```

Never omit the line silently, and never fabricate or guess a URL. For every run in
this release "none" is the expected value, because draft-PR creation belongs to a
later spec.

**The artifact index enumerates what the run actually produced.** It **must not
print a path that does not exist, and must not omit an artifact that does.** The
set genuinely varies per spec, so a derived index stays true where a fixed list
would not.

**Derived from a closed candidate set.** Exactness in both directions is
unverifiable against an open set, so the candidates are fixed here:

| Group | Candidates |
| ----- | ---------- |
| Scaffold-owned | `docs/ai/specs/.process/SPEC-<ID>-design-concept.md`, `docs/ai/specs/.process/SPEC-<ID>-workflow.md`, `specs/<feature>/SPEC-MOC.md`, the pushed branch name |

Nothing outside this set is listed, so an unexpected file is a change to this list
rather than a silent omission. The planning-stage artifacts are **not**
candidates: no planning stage runs before this report, so none of them exists yet.

**The `SPEC-<ID>` token above is the roadmap identity in full, including whatever
namespace prefix it carries — it is not a literal `SPEC-` joined to an
identifier.** An `ART-011` run tests `ART-011-design-concept.md`. The candidates
above must be the filenames Steps 4 and 5 actually wrote. Never test a literally
`SPEC-`-prefixed name for a spec whose identity does not begin with `SPEC-`: that
path was never written, the read fails, and the report silently omits its own
primary artifact — the one omission this index may never make.

**The existence test is a read of the candidate path, and nothing more.** A path
that reads is listed; a path that does not read is omitted. This is the only
existence test inside this skill's declared grant, and it adds no machinery.
Never add Grep, Glob, or Bash to widen that grant. Never infer a path from
convention, and never list a path that was not tested. The pushed branch name is
the one candidate that is not a path: it is listed from the branch step 7 pushed
and needs no read, so the test above never applies to it.

**The next step is the hand-off command**, in the form the check selected. There
is one rule because there is one heading. Scaffold names the planning stage as the
operator's next command, never as its own next action, and never asks a second
confirmation to offer it.

## Failure Handling

Stop instead of improvising when any of the following are true:

- no technical roadmap exists
- the SPEC-ID is not in the roadmap
- the branch or worktree state is ambiguous and cannot be safely reused
- git push fails
- the workflow still contains unresolved placeholders after population
- `$grill-me` aborts because no interactive runtime is available (e.g.,
  invoked from `codex exec` or a CI runner). Scaffolding is HITL-gated by design.

If scaffolding partially succeeds before a failure, report exactly what was created
and what remains unfinished so the user can resume without duplicating work.
