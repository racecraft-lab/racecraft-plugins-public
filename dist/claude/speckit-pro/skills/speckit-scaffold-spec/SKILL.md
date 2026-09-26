---
name: speckit-scaffold-spec
description: "Use this skill when the user wants to set up, scaffold, bootstrap, prep, initialize, or prepare a SPEC-ID from the technical roadmap for autonomous execution. Triggers on: set up SPEC-XXX, scaffold SPEC-XXX, bootstrap SPEC-XXX for development, prep SPEC-XXX, initialize the workspace for SPEC-XXX, prepare SPEC-XXX for the autonomous run, create a spec branch and workflow for SPEC-XXX, generate the workflow file for SPEC-XXX, I need a workflow file generated for SPEC-XXX, fill the prompts from the roadmap, pre-fill the workflow template, start working on SPEC-XXX, populate the workflow file for SPEC-XXX. Opens with a blind-spot pass, creates the git worktree, spec branch, Design Concept doc, and populated workflow file, then hands off to planning. Strictly interactive — requires a human to answer the grill-me questions. Not for checking roadmap status (use /speckit-pro:speckit-status), running a populated workflow (use /speckit-pro:speckit-autopilot), or SDD coaching (use /speckit-pro:speckit-coach)."
argument-hint: "SPEC-ID (e.g., SPEC-009)"
user-invocable: true
allowed-tools: Read Edit Write Skill Agent ToolSearch
license: MIT
---

# SpecKit Scaffold Spec

## Installed Runtime Contract

Installed Claude and Codex surfaces resolve Python 3.11 or newer, invoke
`[resolved_python, "-m", "speckit_pro_runner"]`, send one JSON request on
stdin, read one JSON response from stdout, and surface stderr diagnostics.
Do not add a shell fallback, `jq` parsing path, Git Bash, WSL, or
PowerShell-specific command-language requirement for installed workflows.

## Capability discovery & grounding

Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it.

## Artifact tiering (CONTRACT vs EXHAUST)

speckit-pro artifacts are tiered. **CONTRACT** artifacts (`spec.md`, `plan.md`,
`tasks.md`, `research.md`, supporting design artifacts) are review-visible and
live at their normal locations. The three authored **EXHAUST** artifacts (the
design-concept doc, the workflow file, and the UAT runbook) are scaffolding, so
they are written under a `.process/` directory: the design-concept doc and
workflow file land under `docs/ai/specs/.process/`, and the UAT runbook lands
under the feature's own `specs/<NNN>/.process/`. EXHAUST artifacts are kept, not
discarded: each one stays readable at its `.process/` path.

## O5 monster-epic fallback

Normal reviewability re-slicing routing, layer planning, and split-PR emission remain
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

## Invocation

```text
/speckit-pro:speckit-scaffold-spec SPEC-009
/speckit-pro:speckit-scaffold-spec SPEC-008
```

## Canonical Scaffold Identity

Derive one deterministic `<branch-name>` from the roadmap's spec number and
short slug, then use that exact verified value everywhere. The authored paths,
relative to the resolved worktree root, are:

- `docs/ai/specs/.process/SPEC-<ID>-design-concept.md`
- `docs/ai/specs/.process/SPEC-<ID>-workflow.md`
- `specs/<branch-name>/SPEC-MOC.md`

The generated workflow's `Branch` field is the actual dedicated branch
returned by `resolve-scaffold-worktree-placement` and verified inside the
worktree. Never write `main`, a guessed branch, or a display label into that
field.

## What to Do

### -0.5 Verify Claude Agent Package Completeness

Before parsing or mutating the repository, resolve the plugin root from this
skill location and verify by filesystem reads that every bundled Claude Code
`agents/*.md` file is present, including `uat-runbook-author.md`.
Do not use `install-codex-agents` as a Claude-side repair: Claude Code loads
plugin agents from the plugin cache, so scaffold cannot safely self-heal a
missing Claude agent file. If the file inventory is incomplete, STOP and
tell the user to update/reinstall `speckit-pro`, run `/reload-plugins`, and
retry.

### 0. Ensure SpecKit CLI

Check for the official SpecKit CLI before parsing or mutating the repository:

Use command execution to confirm the official `specify` CLI is available after
including common user-local binary directories on PATH.

If missing and `uv` exists, install it:

Run `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`.

If `uv` is unavailable or install fails, STOP and tell the operator to install
SpecKit with that command. Do not run `specify init --here --force`
automatically; recommend it only when `.specify/` is absent and the operator
explicitly approves project initialization.

### 1. Find the Technical Roadmap

```text
Glob("**/*technical*roadmap*" or "**/*technical-roadmap*")
Also check: docs/ai/*roadmap*.md, docs/ai/specs/*roadmap*.md
```

If no technical roadmap found, STOP: "No technical roadmap found. Create
one with `/speckit-pro:speckit-coach help me create a technical roadmap`."

### 2. Find the Spec in the Technical Roadmap

Read the technical roadmap and find the section for the requested
SPEC-ID (e.g., `### SPEC-009: Search & Database`).

Extract:

- **Spec name** (e.g., "Search & Database")
- **Short name** for the branch (e.g., "search-database")
- **Spec number** (e.g., 009)
- **Tool count** and tool names, only when the roadmap entry records them
- **Priority** (P1/P2/P3)
- **Dependencies** (what it depends on, what depends on it)
- **Scope description** (the full scope text from the
  technical roadmap — this drives the workflow prompts)
- **Status** (must be ⏳ Pending — if already In Progress
  or Complete, warn the user)

If the SPEC-ID is not found, STOP: "SPEC-ID not found in
technical roadmap. Available specs: <list pending specs>."
Offer to help the user add or correct the roadmap entry with
`/speckit-pro:speckit-coach`; do not invent the entry or continue scaffolding.

Run the reviewability setup gate before creating the worktree:

```text
Run runner helper reviewability-gate in setup mode for <technical-roadmap-path>
with spec_id <SPEC-ID>.
```

If it returns an unexcepted `block`, STOP and split the spec first. Warnings
may proceed only when the workflow records the scope budget and split decision.

### 3. Create Git Worktree

<hard_constraints>

**NEVER commit or push to main.** All work happens in the worktree. The
worktree branch is what gets pushed to remote. Re-read the active branch
immediately before every commit and push; if it is `main`, STOP before the
mutation.

</hard_constraints>

Before `git worktree add` or any artifact or roadmap write, invoke the
read-only runner helper `resolve-scaffold-worktree-placement` with the
deterministic single-segment `branch_name` and, only when the user supplied
one, `worktree_root_override`. Require `placement_status=resolved` and
`relation=same` or `relation=descendant`. On `conflict`, `invalid`, or
`relation=external`, report the returned `problems[]` and canonical path, then
STOP before mutation.

This ordering is invariant: the first resolver result comes before
`git worktree add`, artifact writes, or roadmap mutation. Only after that
result passes may scaffold create or reuse the worktree. A second resolver
check then runs after creation or reuse and immediately before bootstrap or
Grill Me. Neither bootstrap nor Grill Me may begin unless that second check
confirms the registered worktree described below.

Without an override, require the helper's exact
`TASK_ROOT/.worktrees/<branch-name>` result. Never derive placement from the
primary checkout, `git rev-parse --git-common-dir`, or the first
`git worktree list` record. Use the returned absolute `worktree_root`
unchanged.

Inspect `git remote -v` before git mutation and never assume `origin`. Honor
the helper's disposition:

1. On `disposition=reuse`, reuse the returned registered worktree without
   moving, recreating, duplicating, or pruning it. An existing local or remote
   branch never authorizes work in the primary checkout: all commits and pushes
   still originate from the resolved worktree branch, never `main`.
2. On `disposition=create`, inspect the intended branch locally and on every
   actual remote. STOP if more than one remote carries it. Add the returned
   worktree using the local branch, the single remote tracking branch, or a new
   branch as the observed state requires. Never commit or push `main` while
   recovering or reusing a remote branch.
3. Verify the active branch inside the returned worktree before any push. It
   must equal the helper's `branch_name` and must not be `main`.

Re-run `resolve-scaffold-worktree-placement` after worktree creation and again
immediately before bootstrap or Grill Me on both create and reuse paths.
Require `placement_status=resolved`, `disposition=reuse`, the identical
canonical `task_root`, `worktree_root`, and `branch_name`, plus
`relation=same` or `relation=descendant`. STOP before bootstrap or Grill Me if
any field drifts. Only then may the verified worktree branch be pushed to the
detected remote.

### 3.5. Bootstrap the Worktree (IN the Worktree)

A fresh worktree has only tracked files — no installed dependencies, no
build outputs, no code indexes. Checked-in agent config (for example a
project-scoped MCP server that runs a local build) can silently fail to
start until the worktree is bootstrapped, and the spec session then runs
without the project's code-intelligence tooling.

```text
1. Check the project's CLAUDE.md / AGENTS.md for a worktree preflight or
   bootstrap section (e.g. "Spec-worktree preflight"). If it documents
   commands, display the exact commands and wait for explicit operator
   approval before running them. Do not treat the presence of CLAUDE.md /
   AGENTS.md as approval. Run only the approved commands FROM the worktree,
   in order.

2. If no explicit bootstrap/preflight commands are documented, do not
   infer an install/build/index sequence. Report that no bootstrap is
   documented and ask the operator before running any package install,
   build, or index command.

3. If the project documents a code index or MCP prerequisite (for
   example: build, then the project's documented index-init command),
   run only the documented commands after explicit approval and verify
   the documented health check passes.

4. After any bootstrap command, run `git status --porcelain` in the
   worktree. If unexpected tracked changes appear, stop and report them
   before continuing.
```

Report what was bootstrapped — or that the project documents nothing —
in the scaffold summary. Never skip this silently: an unbootstrapped
worktree is how spec sessions end up running without the project's
tooling.

### 3.6 Blind-Spot Pass (IN the Worktree)

<hard_constraints>

**This step is mandatory.** Every `/scaffold-spec` invocation runs the
blind-spot pass FROM the worktree, immediately before the grill-me interview.
There is no skip flag, no skip argument, and no documented path that reaches
the interview without attempting the pass.

Mandatory to **attempt**, not to succeed: the pass fails open, as the end of
this step sets out.

</hard_constraints>

**Engine.** The pass runs on the already-shipped read-only `codebase-analyst`,
consumed unmodified. Do not add or edit an agent definition.

**Dispatch, then await.** Dispatch the analyst, then await its own final summary
BEFORE the interview begins:

```text
Agent(subagent_type: "speckit-pro:codebase-analyst", run_in_background: true, ...)
```

The await is not optional: the Claude agent definition carries
`background: true`, so an un-awaited dispatch hands back a task identifier
rather than findings.

**The bound. A single wait expiring is not the deadline.** Abandonment is
governed by one execution deadline for the whole pass:

| Bound | Value | On expiry |
| ----- | ----- | --------- |
| Per-wait timeout | whatever the surface provides | keep waiting; **not** a verdict |
| Pass execution deadline | **5 minutes from dispatch** | abandon the wait and record the `did not run` outcome with reason `wait deadline expired` |

"No reply at all" therefore has one observation point: the await returned
without a summary, or the deadline expired. Never infer it from a dispatch still
running. A summary arriving **after** the deadline does not retroactively change
the recorded outcome.

**Seed.** Read three things from the roadmap entry Step 2 already parsed:

| Seed element | Status | When absent |
| ------------ | ------ | ----------- |
| The entry's Scope text | **required** | The `**Scope:**` label is not universal, so read the scope text rather than matching a heading. Step 2 already extracts it |
| The entry's dependency chain | **required when the entry declares one, under any heading** | Read a renamed variant such as `**Deps:**` as the chain. Only when no declaration exists in any spelling, append the label with the literal `none` and continue on the Scope text alone. Never skip, never report a gap, never infer a chain |
| The `Key Files` section | **optional hint** | Omit the label entirely and continue. Never report a gap, never skip |

**Keep the two absent-field behaviours distinct.** A missing `Key Files` carries
no information, so its label is dropped. A missing `Depends On` **is**
information, so the literal `none` is written, and only when the entry declares
no dependency chain under any heading.

**Payload assembly.** The payload is two parts, in this order: the dispatch
block, then the appended seed material under these literal labels:

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
commentary, no prior findings, no spec text.

Each `Depends On` spec whose artifacts are not in the working tree is chased
into git history rather than reported absent — an archive sweep removes the
files, not the history.

**The dispatch block, carried verbatim.** It is byte-identical on both platform
variants, because the shipped `codebase-analyst` description frames the agent
for autopilot consensus resolution rather than for this technique, so this block
carries the whole framing. Send it first, then the appended material above it.
Do not paraphrase it, and do not normalise the one-word `blindspot pass` or the
phrase `unknown unknowns`. Never ask the operator about their familiarity: their
structural position is stated in the block as fact, not asked.

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

Return every finding worth raising, ranked by impact then surprise. Each finding:
N. **<Title>** - the finding, plus a repo-relative file or path pointer.
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
least one of the two rationale lines. A numbered title with neither fails the
test: the rationale is what makes a finding reviewable.

**A single expired wait is not the third outcome.** A wait expiring is a cue to
keep waiting; only the pass execution deadline expiring abandons the wait.

**Ranking and the set-aside count.** The findings have no count limit. Show
every finding **in the analyst's own order**. Never re-rank, merge, or rewrite
findings: the ranking is the analyst's, by impact with surprise as the tiebreak.
**No numeric score** is assigned.

**Always state the set-aside count the analyst names, including when it is
zero**, in one of these three shapes:

```text
Showing all N findings; none were set aside
Showing all N findings; M more were set aside
The blindspot pass raised no unknown unknowns.
```

The count in the printed line and the `M` in the design-concept record below
are the same number.

The third is the **sentinel echoed verbatim**: one string doing two jobs, the
analyst's signal to scaffold and scaffold's line to the operator, so no second
wording for "found nothing" can be invented.

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

**Do not normalise the one-word spelling inside the sentinel.** Where scaffold
speaks in its own voice (the two degraded lines above and the
`**Blind-spot pass:**` header key below), the term is hyphenated, so one run can
show both spellings. The sentinel is matched **literally**: normalising it to
`blind-spot` classifies the reply as **returned nothing usable** on exactly the
runs where the pass worked.

**Fail open.** Do **not** treat the dispatch outcome as a gate, and do **not**
retry-then-halt. If the dispatch fails or returns nothing usable, continue into
the interview with nothing seeded, and record the gap and its reason in **both**
sinks: the operator status line above, which scaffold prints, and the
design-concept header line below, which Step 4 verifies and repairs.

**"Nothing seeded" means no findings are seeded. It does not mean the labelled
block is omitted.** The block still travels in all three outcomes, carrying only
its status line in the degraded two. Omitting it there would leave the "did not
run" record with no mechanism to be written at all.

**The seeded block — one shape, two appearances.** Findings reach the interview
by being appended as a labelled block to the `scope` argument Step 4 **already**
passes. The block uses one shape in both places it appears — the operator output
and the seeded `scope` string — so the two records cannot drift:

```text
--- BLIND-SPOT PASS FINDINGS ---
<the numbered findings, or the status line for the outcome>
<the set-aside line, present only when findings are shown>
Record the Blind-spot pass line in the design concept's header blockquote.
Treat each finding as a candidate question; any finding not reached becomes an Open Question.
--- END BLIND-SPOT PASS FINDINGS ---
```

**The second line is the only conditional one.** It is present in the two shapes
that show findings. It is omitted when the sentinel came back, because the
sentinel is already the line above it, and in the two degraded outcomes, which
have no set-aside count to state. The delimiters and the two closing
instructions **never vary**, which is what lets the block keep one shape in all
three outcomes.

**Print the block's two closing instructions to the operator unchanged.** Do not
fork the two copies, soften the imperatives in one of them, or drop them from the
printed half.

The block's second closing instruction is how no finding is dropped silently: a
finding the interview resolves becomes an entry in the existing
question-and-answer record, and one it does not reach becomes an Open
Question.

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
clause** the status line above carried. A pass that ran and raised nothing is
the first shape with `N` and `M` both zero — which is what distinguishes it from
a pass that never ran.

The header line is the pass's only durable record: add no section to the design
concept, write no separate findings file, and leave what the interview produces
unchanged.

**Presentation is informational.** The run flows straight from the findings into
the first interview question. **No confirmation, no curation step, no
continue/abort prompt** between the two.

### 4. Run Grill Me Interview (IN the Worktree)

<hard_constraints>

**This step is mandatory.** Every `/scaffold-spec` invocation runs grill-me before
the workflow file is written. There is no `--no-grill` flag and no skip
path — the interview is what makes the workflow prompts good enough for
autonomous execution.

**Grill-me is human-in-the-loop only.** It uses `AskUserQuestion` to
interview the user. If you are running this command in a non-interactive
context (CI, background agent, automation), abort the entire `/scaffold-spec`
invocation — do not attempt to skip grilling.

</hard_constraints>

```text
1. Create the .process/ docs directory in the WORKTREE for the design concept
   (created when absent so the first exhaust artifact lands correctly):
   Create `<worktree_root>/docs/ai/specs/.process/` if absent.

2. Invoke the grill-me skill with the spec scope as input:
   Skill("grill-me", args: {
     mode: "setup",
     spec_id: "SPEC-<ID>",
     spec_name: "<spec name from roadmap>",
     scope: <full scope description from technical roadmap, with the Step 3.6
             BLIND-SPOT PASS FINDINGS block appended below it>,
     output_path: "<worktree_root>/docs/ai/specs/.process/SPEC-<ID>-design-concept.md"
   })

3. The skill walks the design tree using AskUserQuestion (one question
   at a time, with the AI's recommendation marked as the first option).
   It returns when the user reaches a natural stop, hits the soft cap
   at 30 questions and chooses to wrap up, or selects "End interview".

4. Verify the design concept doc exists:
   Read("<worktree_root>/docs/ai/specs/.process/SPEC-<ID>-design-concept.md")
   Must contain Goals, Non-goals, Module and Interface Deltas, Terms,
   Verification Gates, Design Tree (Q&A log), and Open Questions.
   Must also carry the `**Blind-spot pass:**` key in its header blockquote.

5. Repair that key when it is absent:
   The interview is the writer of first resort, but the request is one sentence
   inside a prose block handed to another skill, so verify rather than assume.
   If the key is missing, Edit the Step 3.6 header line into the existing header
   blockquote from the values already held at the moment the status line was
   rendered — the outcome, the `<reason>` clause, and N and M for the `ran`
   outcome. Nothing is derived a second time.
   Read to check and Edit to repair. No new section and no separate findings
   artifact.
```

When the interview does not return, nothing is owed. The run stops when no
interactive runtime is available, so no design concept exists to carry a record
and the Step 3.6 status line is the only one. That is correct rather than a gap:
the run does not continue, so there is no later reader to serve.

The labelled block is the **only** channel the pass uses into the interview, and
it travels in all three Step 3.6 outcomes — carrying only its status line in the
degraded two. Do not add a new interview argument and do not change what the
interview produces. The `scope` argument already exists; this appends to it.

The Q&A log and Goals/Non-goals from this doc drive the next step's
workflow prompts. Pass the doc path forward.

### 5. Copy Workflow Template (IN the Worktree)

All file operations happen in the worktree directory.

```text
0. Require the generic `speckit-pro-reviewability` preset to already exist in
   the worktree. If the preset is absent, STOP and report the missing
   prerequisite.

   Verify resolution from the worktree:
   From `<worktree_root>/`, run
   `specify preset resolve spec-template`,
   `specify preset resolve plan-template`, and
   `specify preset resolve tasks-template`.

1. Read the workflow template from the plugin:
   Read("${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/workflow-template.md")

2. Write the template to the WORKTREE:
   Write("<worktree_root>/docs/ai/specs/.process/SPEC-<ID>-workflow.md",
         content: <template content from step 1>)
```

### 5.5. Write the SPEC-MOC Marker (IN the Worktree)

Write a minimal `SPEC-MOC.md` navigation marker into the spec's CONTRACT
directory on EVERY new spec, regardless of how many slices it will ultimately
have (single-slice specs get the marker too — it is the version-gate carrier).

This marker is a CONTRACT artifact: it is written to `specs/<branch-name>/` —
NOT redirected to `.process/`, and NOT written to `docs/ai/specs/`. The
directory is named from the branch (NOT auto-numbered), so its `spec_id`
namespace-matches the directory.

```text
1. Create the spec's contract directory in the WORKTREE (scaffold owns this
   early creation; mkdir -p is a no-op if it already exists):
   Create `<worktree_root>/specs/<branch-name>/` if absent.

2. Read the spec-MOC template from the plugin:
   Read("${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/spec-moc-template.md")

3. Token-substitute the template (same {{TOKEN}} mechanism as the workflow
   template) and write it to the contract directory:
   Write("<worktree_root>/specs/<branch-name>/SPEC-MOC.md",
         content: <template with the tokens below substituted>)

   | Token | Replace With |
   | ----- | ------------ |
   | `{{ROADMAP_TITLE}}` | a short link text for the roadmap (e.g., the spec series name + " roadmap") |
   | `{{ROADMAP_FILENAME}}` | the existing `*-technical-roadmap.md` filename WITHOUT the `.md` extension (from Step 1) |
   | `{{SPEC_ID}}` | the roadmap identity, e.g., `SPEC-002` (must namespace-match `<branch-name>`) |
```

The written marker MUST carry:

- a non-empty, quoted relative `up:` markdown link pointing at the existing
  `*-technical-roadmap.md` — from `specs/<branch-name>/` this resolves as
  `../../docs/ai/specs/<roadmap-filename>.md` (the `../../docs/ai/specs/`
  prefix is hardcoded in the template; only the filename is tokenized), NEVER
  a `[[wikilink]]`;
- `structureVersion: 1` (carried verbatim from the template, with its "keep in
  sync with the lint scripts' hardcoded literal" comment); and
- a `spec_id` that namespace-matches the contract directory name.

### 6. Populate the Workflow File

Read the copied workflow file (in the worktree) and replace
ALL placeholders with spec-specific values from the technical
roadmap:

| Placeholder | Replace With |
| ----------- | ------------ |
| `SPEC_ID` | e.g., `SPEC-009` |
| `SPEC_NAME` | e.g., `Search & Database` |
| `BRANCH_NAME` | e.g., `009-search-database` |
| `DATE` | today's date, `YYYY-MM-DD` |
| `SPEC_DESCRIPTION` | the Specify prompt's feature description, built as described below |

**Populate the phase prompts** using BOTH the technical roadmap's scope
description AND the design concept doc from Step 4. The roadmap scope
is the seed; the design concept is the enrichment layer that fills in
the decisions the roadmap left ambiguous.

**Formal selection:** Populate `## Formal Methods` from the Design Concept's
approved decision, using the [shared formal contract](../speckit-autopilot/references/formal-methods.md).
When Quint is explicitly chosen, carry that model-language decision into Plan
and its catalog entry using the coach's `references/quint-guide.md`; available
Quint skills do not enroll additional behavior. Keep requested trace obligations
with the selected model through Tasks and final/Post verification.
Record none/deferred/enabled, a specific rationale, selected behavior/model IDs,
new/existing origin, and model/model_and_trace evidence. Carry this decision into
Plan, Tasks, Analyze, and Implement prompts. Tool availability or an existing
catalog is never consent. A deferred question stays in Clarify's existing flow.
New model files may remain pending until the explicit post-Plan author checkpoint;
missing selected existing models are setup gaps. Preserve the normal phase command
templates; the parent dispatches the separate author. Validate the copied workflow
with read-only formal-doctor against WORKFLOW_ROOT after population.

- **Specify Prompt:** Combine the roadmap scope description with the
  Goals, Non-goals, and major design decisions from
  `SPEC-<ID>-design-concept.md`. Quote specific Q&A entries when a
  prompt needs to capture *why* a particular decision was made.

- **Clarify Prompts:** Use the design concept's Open Questions section
  to seed the autopilot's clarify session focuses. Anything still open
  after the grill-me interview is exactly what `/speckit-clarify` should
  be told to dig into. Generate session focuses from the unresolved
  branches and the spec's main surfaces, one focus per open
  behavior area.

- **Plan Prompt:** Combine the tech stack from CLAUDE.md, the
  constitution, the roadmap scope description, AND the
  architecture / data-model / constraint decisions extracted from
  the design concept doc's Q&A log. Quote the user's chosen answer
  for any decision that drives a planning choice. Also reference
  the design concept doc path so the autopilot can re-read it
  during planning if it needs context the prompt didn't capture.
  Carry the design concept's Module and Interface Deltas section
  verbatim so plan.md names the same module and interface changes.

- **Checklist Prompts:** Recommend checklist domains based on the
  spec's scope and the design tree branches the grill-me session
  walked (use the signal extraction from `checklist-domains-guide.md`).

- **Tasks Prompt:** Reference the spec, plan, AND design concept
  doc. Use the design concept's Non-goals to bound task generation —
  flag any task that would cross those boundaries. Use the Q&A
  log's "why" context to inform task ordering and TDD test
  specifications.

- **Analyze Prompt:** Cross-artifact consistency check across
  spec.md, plan.md, tasks.md, AND the design concept doc. Flag any
  drift between the design concept's Goals / Non-goals / decisions,
  its Module and Interface Deltas, and its Verification Gates
  and what the downstream artifacts say. The design concept is the
  source of truth for scoping decisions captured during grill-me;
  if a downstream artifact contradicts it, the downstream artifact
  is wrong unless there is an explicit revision note.

- **Implement Prompt:** Reference tasks.md, plan.md, AND the
  design concept doc. When implementing, consult the Q&A log for
  the "why" behind decisions — this informs test specifications,
  edge-case handling, and refactor choices. Decisions captured in
  the design concept that aren't reflected in tasks.md should be
  surfaced as gaps before coding, not silently dropped. Carry the
  Verification Gates section verbatim so PROJECT_COMMANDS discovery
  and the TDD executors target the checks the interview agreed on.

### 7. Commit and Verify (IN the Worktree)

All commits happen on the worktree branch (see hard constraints).
Immediately before the commit and again immediately before the push, run
`git rev-parse --abbrev-ref HEAD` in the resolved worktree. The result must
equal the resolver's `branch_name` and must not be `main`; otherwise STOP.

```text
1. Stage and commit the design concept doc, the workflow file, AND the
   SPEC-MOC marker (the marker is a review-visible CONTRACT artifact — if it is
   written but left untracked it never reaches the PR). From the worktree, add
   `docs/ai/specs/.process/SPEC-<ID>-design-concept.md`,
   `docs/ai/specs/.process/SPEC-<ID>-workflow.md`, and
   `specs/<branch-name>/SPEC-MOC.md`, then commit with
   `chore(SPEC-XXX): add design concept and workflow for autopilot`.

2. Push the WORKTREE BRANCH:
   From `<worktree_root>/`, run `git push`.

   If the push fails or the remote rejects it, STOP and report the failure
   instead of continuing as though the scaffold succeeded. The failure report
   identifies the existing local branch, canonical worktree, workflow file,
   and local commit. Tell the operator to resolve the remote rejection and
   retry the push from that same existing worktree. Do not recreate the branch
   or worktree, regenerate the workflow, or replace the existing commit merely
   to retry the push.

3. Verify:
   - Read the design concept doc — must contain Goals, Non-goals,
     Q&A log, and Open Questions sections.
   - Read the workflow file back — no placeholders remain, and the
     Specify/Clarify Prompts contain content traceable to the
     design concept's Q&A log.
   - From the worktree, run `git rev-parse --abbrev-ref HEAD`
     → must show the spec branch, NOT main
   - From the worktree, run `git log --oneline -1`
     → must show the design-concept-and-workflow commit
```

Report:

```text
## Scaffold Complete

**Spec:** SPEC-009 Search & Database
**Branch:** 009-search-database
**Worktree:** .worktrees/009-search-database/
**Design Concept:** .worktrees/009-search-database/docs/ai/specs/.process/SPEC-009-design-concept.md
**Workflow:** .worktrees/009-search-database/docs/ai/specs/.process/SPEC-009-workflow.md
**Remote:** Pushed to <remote>/009-search-database
**Bootstrap:** <commands run, documented health check, or "no documented bootstrap">

**If you stop here, run:**
/cd <absolute-worktree-root>
/speckit-pro:speckit-autopilot <absolute-workflow-file> --stage plan

**Review both files** — the design concept doc captures the
decisions you made during grill-me; the workflow file is what the
autopilot will execute. Verify the phase prompts have enough context
for autonomous execution.
```

### 8. Update Technical Roadmap Status (IN the Worktree)

Update the technical roadmap's Progress Tracking table IN THE
WORKTREE (not on main) to mark the spec as `🔄 In Progress`:

```text
1. Edit the technical roadmap found in Step 1, using the WORKTREE path:
   Edit("<worktree_root>/<roadmap-path-from-step-1>")

2. Commit IN THE WORKTREE:
   Re-read the active branch first and STOP if it differs from the resolver's
   `branch_name` or equals `main`.
   From `<worktree_root>/`, stage `docs/ai/`, commit with
   `chore(SPEC-XXX): mark as In Progress`, and push the branch.
```

The technical roadmap update will reach main when the spec's PR is
merged (see hard constraints).

### 9. Hand Off to the Planning Stage

The hand-off sits here, after Step 8, once the design concept, the workflow file,
the SPEC-MOC marker, and the roadmap status flip are all committed and pushed.
Never hand off earlier: a planning stage that fails or is interrupted must never
leave the roadmap claiming the spec is still Ready.

**Scaffold never invokes the autopilot or `/cd`. It prints both commands; the
operator explicitly sends them in this same session.** On Claude Code the
autopilot skill carries `disable-model-invocation: true`, which the skills
documentation defines as "Only you can invoke the skill" — a deliberate setting,
because a seven-phase autonomous run that commits as it goes is exactly the kind
of side effect an operator must trigger themselves. **Never state that accepting
will run the planning phases or change directories automatically.**

**Run the hand-off check first. Two read-only tests.** They do not gate the
hand-off — one is always printed. They select its form and decide whether a
warning travels with it.

```text
1. Resolve the generated worktree with `git -C <absolute-worktree-root>
   rev-parse --show-toplevel`; require the canonical result to equal that root,
   and require the canonical absolute workflow file to be a readable regular
   file contained by it.
2. Confirm `git -C <absolute-worktree-root> status --porcelain` is clean.
```

The absolute root and canonical absolute workflow path are deliberately passed
separately. `/cd` changes Claude Code's live session directory and reloads
directory-scoped instructions; the absolute autopilot path then identifies
exactly the generated worktree even if another registered worktree contains a
stale same-named workflow. That duplicate therefore cannot make the retry
ambiguous or redirect planning commits to main.

**What the check must NOT test: the most recent commit.** After Step 8 the
newest commit is the roadmap status flip rather than the workflow-file commit,
so a last-commit test would fail on every correct run.

**What each result selects:**

| Check result | Effect on the hand-off |
| ------------ | ---------------------- |
| Step 1 passes | print the two-command same-session hand-off below |
| Step 1 fails | report the invalid generated worktree/path and retain the existing reopen/new-task recovery; never invite autopilot from the parent checkout |
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
nothing does. Use `AskUserQuestion`:

```text
Question: Scaffold is complete and pushed. Are you continuing into planning now?
Options, two, mutually exclusive, in this order:
  1. Continue now (Recommended)
  2. Stop here
```

The recommended answer comes first, per house convention. Both answers are fully
non-destructive, and both print the same command; the answer selects only how the
closing report frames it. Never fall back to parsing a free-text reply. When the
session exposes no structured confirmation mechanism, skip the question and
print the report — the hand-off does not depend on it.

**The budget counts what this step adds**: exactly one confirmation. Step 3's
reuse-or-recreate question and Step 3.5's bootstrap approval are pre-existing,
are not counted, and are not removed.

**The hand-off has exactly two commands, in this order:**

```text
/cd <absolute-worktree-root>
/speckit-pro:speckit-autopilot <absolute-workflow-file> --stage plan
```

Claude Code documents `/cd` as changing the current working directory for the
session and loading project instructions from that directory:
<https://code.claude.com/docs/en/commands>. The operator sends the autopilot
command only after `/cd` succeeds. If `/cd` fails, STOP the hand-off and use the
existing reopen/new-task fallback rooted at the generated worktree; never run
autopilot from the parent checkout.

The stage token is the literal lowercase `plan`, from the closed vocabulary
`plan`, `implement`, `full`. No aliases, no alternate casing, no long-form
spellings. The workflow file is the canonical absolute path in the generated
worktree, so a stale same-named copy in another registered worktree cannot make
the retry ambiguous. Never pass a state file, branch name, feature directory,
or environment variable to autopilot across the boundary.

**Nothing is rolled back on any path.** Everything scaffold owns is committed and
pushed before this step runs, so the operator who stops here defers the two
hand-off commands and loses no work.

### 10. Closing Report

**One report, rendered on every ending the run can reach:**

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
**Draft PR:** none (scaffold does not open one; autopilot does at PR time)

**Artifacts:**
- <repo-relative path>     (one line each; only paths that exist)

**Next step:**
<two-command hand-off block>
```

**The heading is one fixed string, `## Ready for Planning`**, on all three
endings.

**Fixed, conditional, and derived.** The heading and the draft-PR line are
fixed, except that the draft-PR line is conditional on a URL existing. The
outcome line, the artifact index, and the next step are **derived** — each has
its own rule below. `<two-command hand-off block>` is the Step 9 `/cd` command
followed by the absolute-workflow autopilot command. It remains one report element even
though it is rendered on two lines.

**The set-aside findings count MUST NOT appear here.** The list is closed at
four elements; that count lives in the design concept's header record and in the
seeded block, and the artifact index points at the file carrying it.

**The two reports must not restate the same fields**: no worktree path, no
remote line, and no bootstrap result here — the Scaffold Complete report already
gave all three, and the closed list admits none of them. The pushed branch
appears once, as an index entry, never as a repeated header field.

**The outcome line, one per ending.** One heading covers all three, so the
outcome line is where they are told apart. The index and the next step are the
same on all three, because no planning stage ran in any of them:

| Ending | Outcome line states |
| ------ | ------------------- |
| The operator is continuing now | everything scaffold owns is committed and pushed, and the planning hand-off is next |
| The operator stopped here | the run stopped at the operator's request, everything scaffold owns is committed and pushed, and nothing was rolled back |
| No structured confirmation mechanism was available | the question was not asked because the session exposes none, everything scaffold owns is committed and pushed, and nothing was rolled back |

Every line closes on **everything scaffold owns is committed and pushed**.

**When Step 9's cleanliness test failed, the outcome line carries one added
clause** naming the uncommitted changes as something to resolve before running
the hand-off. It is a clause on an existing element rather than a fifth element,
and it is the only check result that reaches this report as text — path
validation determines whether the normal hand-off or recovery is shown.

**The draft-PR line.** Show the URL when the run produced one. Otherwise state
plainly that there is none:

```text
**Draft PR:** none (scaffold does not open one; autopilot does at PR time)
```

Never omit the line silently, and never fabricate or guess a URL.

**The artifact index enumerates what the run actually produced.** It **must not
print a path that does not exist, and must not omit an artifact that does.**

**Derived from a closed candidate set:**

| Group | Candidates |
| ----- | ---------- |
| Scaffold-owned | `docs/ai/specs/.process/SPEC-<ID>-design-concept.md`, `docs/ai/specs/.process/SPEC-<ID>-workflow.md`, `specs/<feature>/SPEC-MOC.md`, the pushed branch name |

Nothing outside this set is listed. The planning-stage artifacts are **not**
candidates.

**The `SPEC-<ID>` token above is the roadmap identity in full, including whatever
namespace prefix it carries — it is not a literal `SPEC-` joined to an
identifier.** A `SPEC-011` run tests `SPEC-011-design-concept.md`. The candidates
above must be the filenames Steps 4 and 5 actually wrote. Never test a literally
`SPEC-`-prefixed name for a spec whose identity does not begin with `SPEC-`: that
path was never written, so the index would omit its primary artifact.

**The existence test is a read of the candidate path, and nothing more.** A path
that reads is listed; a path that does not read is omitted.
Never infer a path from convention, and never list a path that was not tested.
The pushed branch name is the one candidate that is not a path: it is listed
from the branch Step 7 pushed and needs no read, so the test above never
applies to it.

**The next step is the Step 9 two-command hand-off**, in the form that step's
check selected. Scaffold names
the planning hand-off as the operator's next action, never as its own action,
and never asks a second confirmation to offer it.
