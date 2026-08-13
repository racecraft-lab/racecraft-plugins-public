---
name: speckit-scaffold-spec
description: "Use this skill when the user wants to set up, scaffold, bootstrap, prep, initialize, or prepare a SPEC-ID from the technical roadmap for autonomous execution. Triggers on: set up SPEC-XXX, scaffold SPEC-XXX, bootstrap SPEC-XXX for development, prep SPEC-XXX, initialize the workspace for SPEC-XXX, prepare SPEC-XXX for the autonomous run, create a spec branch and workflow for SPEC-XXX, generate the workflow file for SPEC-XXX, I need a workflow file generated for SPEC-XXX, fill the prompts from the roadmap, pre-fill the workflow template, start working on SPEC-XXX, populate the workflow file for SPEC-XXX. Opens with a blind-spot pass, creates the git worktree, spec branch, Design Concept doc, and populated workflow file, then can chain into planning. Strictly interactive — requires a human to answer the grill-me questions. Not for checking roadmap status (use /speckit-pro:speckit-status), running a populated workflow (use /speckit-pro:speckit-autopilot), or SDD coaching (use /speckit-pro:speckit-coach)."
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

Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `speckit-pro/skills/speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it.

## Codex Skill-Selection Guard

If this file is loaded in Codex, the runtime selected the Claude Code
variant from `skills/` instead of the Codex variant from `codex-skills/`.
Do not follow the Claude-oriented instructions below in Codex. Immediately
read and follow `../../codex-skills/speckit-scaffold-spec/SKILL.md` from this plugin
root, treat that document as the active skill, and report that the fallback
guard was triggered.

Prepare a spec from the technical roadmap for autonomous execution.
Creates the worktree, branch, and workflow file — ready for
`/speckit-pro:speckit-autopilot`.

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

## Invocation

```text
/speckit-pro:speckit-scaffold-spec SPEC-009
/speckit-pro:speckit-scaffold-spec SPEC-008
```

## What to Do

### -0.5 Verify Claude Agent Package Completeness

Before parsing or mutating the repository, resolve the plugin root from this
skill location and verify by filesystem reads that every bundled Claude Code
`agents/*.md` file is present, including `uat-runbook-author.md`.
`install-codex-agents` is deferred and unavailable; do not invoke it as a
validator or repair operation. If the file inventory is incomplete, STOP and
tell the user to update/reinstall `speckit-pro`, run `/reload-plugins`, and
retry. Claude Code
loads plugin agents directly from the plugin cache, so scaffold cannot safely
self-heal a missing Claude agent file.

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
- **Tool count** and tool names
- **Priority** (P1/P2/P3)
- **Dependencies** (what it depends on, what depends on it)
- **Scope description** (the full scope text from the
  technical roadmap — this drives the workflow prompts)
- **Status** (must be ⏳ Pending — if already In Progress
  or Complete, warn the user)

If the SPEC-ID is not found, STOP: "SPEC-ID not found in
technical roadmap. Available specs: <list pending specs>."

Run the reviewability setup gate before creating the worktree:

```text
Run runner helper reviewability-gate in setup mode for <technical-roadmap-path>.
```

If it returns an unexcepted `block`, STOP and split the spec first. Warnings
may proceed only when the workflow records the scope budget and split decision.

### 3. Create Git Worktree

<hard_constraints>

**NEVER commit or push to main.** All work happens in the
worktree. The worktree branch is what gets pushed to remote.

</hard_constraints>

```text
1. Detect remote name:
   Run `git remote -v`.

2. Create the branch and worktree:
   Run `git worktree add .worktrees/<number>-<short-name> -b <number>-<short-name>`.

3. Switch your working directory to the worktree:
   ALL subsequent commands run FROM the worktree path:
   .worktrees/<number>-<short-name>/

4. Push the WORKTREE BRANCH (not main) to remote:
   From `.worktrees/<number>-<short-name>/`, run
   `git push -u <remote> <number>-<short-name>`.

5. Verify you're on the correct branch:
   From `.worktrees/<number>-<short-name>/`, run
   `git rev-parse --abbrev-ref HEAD`.
   Must show: <number>-<short-name> (NOT main)
```

If the worktree already exists, ask the user whether to use
the existing one or recreate it.

If the branch already exists (locally or remotely), check it
out in the worktree instead of creating a new one.

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
consumed unmodified. Do not add or edit an agent definition on either platform,
and never add Grep, Glob, or Bash to this skill's `allowed-tools`, which stays
exactly `Read Edit Write Skill Agent ToolSearch`. The existing `Agent` grant
already makes the dispatch possible: this step needs **no new tool grant**.

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

**The two absent-field behaviours differ on purpose. Do not collapse them.**
`Key Files` is a hint whose absence carries no information, so its label is
dropped. A missing `Depends On` **is** information, so the literal `none` is
written instead: reading a renamed `**Deps:**` as an absent field would put
`none` in the payload for an entry that names several — a false statement rather
than a missing one.

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
least one of the two rationale lines. A numbered title with neither fails the
test: the rationale is what makes a finding reviewable.

**A single expired wait is not the third outcome.** A wait expiring is a cue to
keep waiting; only the pass execution deadline expiring abandons the wait.

**Cap, ranking, and the set-aside count.** At most five findings, and the cap is
**not operator-configurable**.

**Scaffold enforces the cap on what it renders.** The reply is model output and
cannot be relied on to obey. When more than five come back, show the first five
**in the analyst's own order**, count the remainder, and state that count
through the truncation string below. Never re-rank, merge, or rewrite findings
to fit: the ranking is the analyst's. **No numeric score** is assigned. Ranking
is reviewable rather than deterministic — ordered by impact with surprise as the
tiebreak, so a reader can check each rationale against the roadmap text.

**Always state the set-aside count, including when it is zero**, in one of these
three shapes:

```text
Showing the 5 highest-impact findings; N more were set aside
Showing all N findings; none were set aside
The blindspot pass raised no unknown unknowns.
```

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

**The one-word spelling inside the sentinel is deliberate. Do not normalise
it.** Everywhere scaffold speaks in its own voice — the two degraded lines
above, and the `**Blind-spot pass:**` header key below — the term is hyphenated,
so one run can show the operator both spellings. It reads as a typo and is not.
The sentinel is matched **literally**: normalising it to
`blind-spot` breaks the usable-reply test silently, classifying the reply as
**returned nothing usable** on exactly the runs where the pass worked.

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

**Two of the block's lines address the interview, and the operator sees them.**
That cost is accepted rather than overlooked. **Do not resolve it by forking the
two copies**, softening the imperatives in one of them, or dropping them from
the printed half. Any of those is the drift one shape exists to prevent.

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

Adding this key needs no schema change. Do **not** add a new section to the
design concept, do **not** write a separate findings artifact — specifically not
`.process/<SPEC-ID>-blind-spots.md` — and do **not** change what the interview
produces.

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
   Create `.worktrees/<number>-<short-name>/docs/ai/specs/.process/` if absent.

2. Invoke the grill-me skill with the spec scope as input:
   Skill("grill-me", args: {
     mode: "setup",
     spec_id: "SPEC-<ID>",
     spec_name: "<spec name from roadmap>",
     scope: <full scope description from technical roadmap, with the Step 3.6
             BLIND-SPOT PASS FINDINGS block appended below it>,
     output_path: ".worktrees/<number>-<short-name>/docs/ai/specs/.process/SPEC-<ID>-design-concept.md"
   })

3. The skill walks the design tree using AskUserQuestion (one question
   at a time, with the AI's recommendation marked as the first option).
   It returns when the user reaches a natural stop, hits the soft cap
   at 30 questions and chooses to wrap up, or selects "End interview".

4. Verify the design concept doc exists:
   Read(".worktrees/<number>-<short-name>/docs/ai/specs/.process/SPEC-<ID>-design-concept.md")
   Must contain Goals, Non-goals, Design Tree (Q&A log), and Open Questions.
   Must also carry the `**Blind-spot pass:**` key in its header blockquote.

5. Repair that key when it is absent:
   The interview is the writer of first resort, but the request is one sentence
   inside a prose block handed to another skill, so verify rather than assume.
   If the key is missing, Edit the Step 3.6 header line into the existing header
   blockquote from the values already held at the moment the status line was
   rendered — the outcome, the `<reason>` clause, and N and M for the `ran`
   outcome. Nothing is derived a second time.
   Read to check and Edit to repair. No new tool grant, no new machinery, no new
   section, no separate findings artifact, and no grill-me edit.
```

When the interview does not return, nothing is owed. The run stops when no
interactive runtime is available, so no design concept exists to carry a record
and the Step 3.6 status line is the only one. That is correct rather than a gap:
the run does not continue, so there is no later reader to serve.

The labelled block is the **only** channel the pass uses into the interview, and
it travels in all three Step 3.6 outcomes — carrying only its status line in the
degraded two. Do not add a new interview argument, do not change what the
interview produces, and never edit any file under the grill-me skill on either
platform. The `scope` argument already exists; this appends to it.

The Q&A log and Goals/Non-goals from this doc drive the next step's
workflow prompts. Pass the doc path forward.

### 5. Copy Workflow Template (IN the Worktree)

All file operations happen in the worktree directory.

```text
0. Require the generic `speckit-pro-reviewability` preset to already exist in
   the worktree. `ensure-reviewability-preset` is deferred and unavailable, so
   do not invoke it or claim setup generated preset files. If the preset is
   absent, STOP and report the deferred capability gap.

   Verify resolution from the worktree:
   From `.worktrees/<number>-<short-name>/`, run
   `specify preset resolve spec-template`,
   `specify preset resolve plan-template`, and
   `specify preset resolve tasks-template`.

1. Read the workflow template from the plugin:
   Read("${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/workflow-template.md")

2. Write the template to the WORKTREE:
   Write(".worktrees/<number>-<short-name>/docs/ai/specs/.process/SPEC-<ID>-workflow.md",
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
   Create `.worktrees/<number>-<short-name>/specs/<branch-name>/` if absent.

2. Read the spec-MOC template from the plugin:
   Read("${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/spec-moc-template.md")

3. Token-substitute the template (same {{TOKEN}} mechanism as the workflow
   template) and write it to the contract directory:
   Write(".worktrees/<number>-<short-name>/specs/<branch-name>/SPEC-MOC.md",
         content: <template with the tokens below substituted>)

   | Token | Replace With |
   | ----- | ------------ |
   | `{{ROADMAP_TITLE}}` | a short link text for the roadmap (e.g., the spec series name + " roadmap") |
   | `{{ROADMAP_FILENAME}}` | the existing `*-technical-roadmap.md` filename WITHOUT the `.md` extension (from Step 1) |
   | `{{SPEC_ID}}` | the roadmap identity, e.g., `PRSG-002` (must namespace-match `<branch-name>`) |
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
ALL placeholders with spec-specific values from the master
plan:

| Placeholder | Replace With |
| ----------- | ------------ |
| `SPEC_ID` | e.g., `SPEC-009` |
| `SPEC_NAME` | e.g., `Search & Database` |
| `BRANCH_NAME` | e.g., `009-search-database` |
| `TOOL_COUNT` | e.g., `10` |
| `TOOL_NAMES` | e.g., `search_tasks, search_projects, ...` |

**Populate the phase prompts** using BOTH the technical roadmap's scope
description AND the design concept doc from Step 4. The roadmap scope
is the seed; the design concept is the enrichment layer that fills in
the decisions the roadmap left ambiguous.

- **Specify Prompt:** Combine the roadmap scope description with the
  Goals, Non-goals, and major design decisions from
  `SPEC-<ID>-design-concept.md`. Quote specific Q&A entries when a
  prompt needs to capture *why* a particular decision was made.

- **Clarify Prompts:** Use the design concept's Open Questions section
  to seed the autopilot's clarify session focuses. Anything still open
  after the grill-me interview is exactly what `/speckit-clarify` should
  be told to dig into. Generate session focuses based on the tool types
  and any unresolved branches (e.g., "Session 1: Search API Behavior",
  "Session 2: Database Operations").

- **Plan Prompt:** Combine the tech stack from CLAUDE.md, the
  constitution, the roadmap scope description, AND the
  architecture / data-model / constraint decisions extracted from
  the design concept doc's Q&A log. Quote the user's chosen answer
  for any decision that drives a planning choice. Also reference
  the design concept doc path so the autopilot can re-read it
  during planning if it needs context the prompt didn't capture.

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
  drift between the design concept's Goals / Non-goals / decisions
  and what the downstream artifacts say. The design concept is the
  source of truth for scoping decisions captured during grill-me;
  if a downstream artifact contradicts it, the downstream artifact
  is wrong unless there is an explicit revision note.

- **Implement Prompt:** Reference tasks.md, plan.md, AND the
  design concept doc. When implementing, consult the Q&A log for
  the "why" behind decisions — this informs test specifications,
  edge-case handling, and refactor choices. Decisions captured in
  the design concept that aren't reflected in tasks.md should be
  surfaced as gaps before coding, not silently dropped.

### 7. Commit and Verify (IN the Worktree)

All commits happen on the worktree branch — NEVER on main.

```text
1. Stage and commit the design concept doc, the workflow file, AND the
   SPEC-MOC marker (the marker is a review-visible CONTRACT artifact — if it is
   written but left untracked it never reaches the PR). From the worktree, add
   `docs/ai/specs/.process/SPEC-<ID>-design-concept.md`,
   `docs/ai/specs/.process/SPEC-<ID>-workflow.md`, and
   `specs/<branch-name>/SPEC-MOC.md`, then commit with
   `chore(SPEC-XXX): add design concept and workflow for autopilot`.

2. Push the WORKTREE BRANCH:
   From `.worktrees/<number>-<short-name>/`, run `git push`.

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
/speckit-pro:speckit-autopilot docs/ai/specs/.process/SPEC-009-workflow.md --stage plan

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
   Edit(".worktrees/<number>-<short-name>/<roadmap-path-from-step-1>")

2. Commit IN THE WORKTREE:
   From `.worktrees/<number>-<short-name>/`, stage `docs/ai/`, commit with
   `chore(SPEC-XXX): mark as In Progress`, and push the branch.
```

**NEVER push to main.** The technical roadmap update will reach
main when the spec's PR is merged.

### 9. Chain into the Planning Stage

The chain sits here, after Step 8, once the design concept, the workflow file,
the SPEC-MOC marker, and the roadmap status flip are all committed and pushed.
Placing it earlier is rejected for a stated reason: a chained planning stage
that fails or is interrupted must never leave the roadmap claiming the spec is
still Ready. Steps 4 through 8 keep their numbers.

**Run the pre-chain check first. Two read-only tests, and both must pass.** If
any part fails, do NOT ask; print the hand-off command instead.

```text
1. Resolve the current checkout with `git rev-parse --show-toplevel`.
2. If the supplied workflow path exists inside that checkout, continue.
3. Confirm `git status --porcelain` is clean in the same checkout that
   step 1 resolved.
```

Step 2 is the Codex autopilot's Workflow Worktree Binding guard's own sentence,
reproduced word for word. Use those words. Do not paraphrase them as "resolves
inside", "is under", or "belongs to".

**This is an existence test on the supplied path. It is not a comparison of
directories.** Do not implement it by canonicalising the workflow path and
comparing its parent, its repository root, or its worktree root against the
current checkout root. A stale same-named workflow file in the parent checkout
passes every such comparison, so planning phases would run with their commits
landing there — usually main, which this skill may never commit to.

**What the check must NOT test: the most recent commit.** After Step 8 the
newest commit is the roadmap status flip rather than the workflow-file commit,
so a last-commit test would fail on every correct run.

Both commands are read-only, so this check adds no machinery.

**Print one line before asking.** State three facts and no more: accepting runs
the six planning phases in this same session without further prompts; those
phases commit as they go; declining leaves everything already pushed exactly as
it is. It is printed, not asked — no options — and does not count against the
budget below.

**Then ask exactly one confirmation, structured.** Use `AskUserQuestion`:

```text
Question: Scaffold is complete and pushed. Start the planning stage now?
Options, two, mutually exclusive, in this order:
  1. Start planning (Recommended)
  2. Stop here
```

The recommended answer comes first, per house convention. Declining is fully
non-destructive: everything scaffold owns is already committed and pushed.

Never fall back to parsing a free-text reply, and never chain by default when
the structured confirmation is unavailable.

**The budget counts what this step adds**: exactly one confirmation when the
chain is attempted, none when the pre-chain check fails. Step 3's
reuse-or-recreate question and Step 3.5's bootstrap approval are pre-existing,
are not counted, and are not removed.

**On acceptance, print the invocation verbatim, then run it:**

```text
/speckit-pro:speckit-autopilot <workflow-file> --stage plan
```

Without that line the accepted path is the only branch point where the operator
is told nothing, because the next output belongs to another skill. It also puts
the same string in front of them on both branches.

The stage token is the literal lowercase `plan`, from the closed vocabulary
`plan`, `implement`, `full`. No aliases, no alternate casing, no long-form
spellings. The workflow file path is the **sole** hand-off token: never pass a
state file, branch name, feature directory, or environment variable across the
boundary.

**The three no-chain paths.** Do not chain, and print the hand-off command
instead, in all three of these cases:

```text
1. The operator declines.
2. No structured confirmation mechanism is available in the session.
3. The pre-chain check above fails.
```

In every case **nothing is rolled back**: the operator loses one command and no
work.

**The hand-off command has one fixed form:**

| Platform | Hand-off command |
| -------- | ---------------- |
| Claude Code | `/speckit-pro:speckit-autopilot <workflow-file> --stage plan` |
| Codex CLI | start a new Codex task rooted at the spec worktree, then `$speckit-autopilot <workflow-file> --stage plan` |

The Codex rooting instruction is **part of the command, not commentary beside
it**: a Codex operator reaching this ending is by definition rooted outside the
worktree, so a bare invocation would hand them a command the Workflow Worktree
Binding guard stops.

Beyond the pre-chain check, the Claude chain is unconditional. Claude's
autopilot ships **no** worktree-binding guard, so a mis-rooted Claude chain
would resolve silently against the parent checkout rather than stopping — which
is why the check is required here too.

### 10. Closing Report

**One report, rendered on every terminal condition the run can reach.** Four
triggers, all four named because two of them are not choices:

```text
1. After the planning stage, on acceptance.
2. Immediately, when the operator declined.
3. Immediately, when no structured confirmation mechanism was available.
4. Immediately, when the pre-chain check failed.
```

Trigger 4 is the **ordinary** Codex run, not an edge case, which is why a
two-item accept-or-decline list is insufficient: it would leave the most common
Codex ending with no report owed.

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

**The heading is a closed three-value vocabulary, one per terminal condition.**
A two-value vocabulary would force one condition under a heading that is
false:

| Terminal condition | Heading |
| ------------------ | ------- |
| The operator declined, or the chain never fired | `## Stopped Before Planning` |
| The chain fired and the completion test passes | `## Planning Complete` |
| The chain fired and the completion test does not pass | `## Planning Incomplete` |

**Fixed, conditional, and derived.** The heading is selected from the closed set
above. The draft-PR line is conditional. The outcome line, the artifact index,
and the next step are **derived** — none is a fixed string, and each has its own
rule below. `<one command>` denotes one fixed string, not a bare invocation: on
the three no-chain paths it is the Step 9 hand-off command, whose Codex form
carries the rooting precondition. The slot stays one line per heading.

**The set-aside findings count MUST NOT appear here.** The list is closed at
four elements; that count lives in the design concept's header record and in the
seeded block, and the artifact index points at the file carrying it.

**The two reports must not restate the same fields**: no worktree path, no
remote line, and no bootstrap result here — the Scaffold Complete report already
gave all three and the closed list admits none of them. The pushed branch
appears once, as an index entry, never as a repeated header field.

**The outcome line, one per no-chain cause.** `## Stopped Before Planning`
covers a deliberate stop and two endings the operator did not choose, so the
outcome line is where they are told apart. The index and the next step are the
same on all three, since no planning stage ran:

| No-chain cause | Outcome line states |
| -------------- | ------------------- |
| The operator declined | the run stopped at the operator's request, and nothing was rolled back |
| No structured confirmation mechanism was available | the chain was not offered because the session exposes no structured confirmation mechanism, and nothing was rolled back |
| The rooting test failed | planning was not started in this session because the workflow file is outside the current checkout; everything scaffold owns is finished and pushed, and nothing was rolled back |
| The cleanliness test failed | the chain was not offered because the checkout has uncommitted changes, and nothing was rolled back |

This does not reopen the three no-chain paths: they still behave identically —
no chain, hand-off command printed, nothing rolled back. The two check failures
are told apart because their remedies differ: a dirty checkout is fixed in
place, while a mis-rooted session cannot be corrected from inside itself on
Codex, so its remedy is the new session the Codex hand-off command already
names.

Every line closes on **nothing was rolled back**, the fact the operator most
needs.

**The rooting row reads as an ending, not an apology.** On Codex it is the
ordinary outcome, reached by an operator who did nothing wrong and can do
nothing about it from inside that session, so the wording leads with what is
finished rather than with a negation. **The string is identical on both
platforms** — a platform-forked outcome line would be a divergence outside the
closed list of permitted differences — and it is true on both, because a Claude
session failing the same test is in the same position.

**The draft-PR line.** Show the URL when the run produced one. Otherwise state
plainly that there is none:

```text
**Draft PR:** none, because draft-PR creation is not part of this release
```

Never omit the line silently, and never fabricate or guess a URL. For every run
in this release "none" is the expected value, because draft-PR creation belongs
to a later spec.

**The artifact index enumerates what the run actually produced** — the
scaffold-owned artifacts plus whatever the planning stage wrote, including the
conditionally produced research artifact, the contract artifacts, and the
checklist domains this spec chose. It **must not print a path that does not
exist, and must not omit an artifact that does.** The set genuinely varies per
spec, so a derived index stays true where a fixed list would not.

**Derived from a closed candidate set.** Exactness in both directions is
unverifiable against an open set, so the candidates are fixed here:

| Group | Candidates |
| ----- | ---------- |
| Scaffold-owned | `docs/ai/specs/.process/SPEC-<ID>-design-concept.md`, `docs/ai/specs/.process/SPEC-<ID>-workflow.md`, `specs/<feature>/SPEC-MOC.md`, the pushed branch name |
| Planning-stage | `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `tasks.md`, each file under `contracts/`, each file under `checklists/` — all relative to `specs/<feature>/` |

Nothing outside this set is listed, so an unexpected file is a change to this
list rather than a silent omission.

**The existence test is a read of the candidate path, and nothing more.** A path
that reads is listed; a path that does not read is omitted. This is the only
existence test inside this skill's declared grant, and it adds no machinery.
Never add Grep, Glob, or Bash to widen that grant.

The two directory-valued members, `contracts/` and `checklists/`, are the one
place a plain read is insufficient. For those, the candidate paths are the
artifact names the run's own plan and checklist phases recorded, so the
enumeration still comes from a read rather than a directory listing. Never infer
a path from convention, and never list a path that was not tested.

**The next step, one rule per heading, so no heading ends on an undefined
line.** Under `## Stopped Before Planning` the value is the Step 9 hand-off
command.

Under `## Planning Complete` it is the Step 9 invocation with the stage token
advanced to the literal lowercase `implement`, the next member of the closed
vocabulary:

| Platform | Next step under `## Planning Complete` |
| -------- | -------------------------------------- |
| Claude Code | `/speckit-pro:speckit-autopilot <workflow-file> --stage implement` |
| Codex CLI | `$speckit-autopilot <workflow-file> --stage implement` |

The workflow file path is the same sole hand-off token, so nothing new crosses
the boundary. **Never chain into the implement stage, and never ask a second
confirmation to offer it.** The one confirmation Step 9 spends authorises the
plan stage only. The implement stage is named as the operator's next command,
never as scaffold's next action.

Under `## Planning Incomplete` it is the resume command, which **is** the next
step rather than a fifth element — the list is closed at four:

| Platform | Resume command |
| -------- | -------------- |
| Claude Code | `/speckit-pro:speckit-autopilot <workflow-file> --stage plan --from-phase <phase>` |
| Codex CLI | `$speckit-autopilot <workflow-file> --stage plan --from-phase <phase>` |

`<phase>` is **derived, not chosen**: the first planning-phase row in
`## Workflow Overview` without a terminal status, named in the autopilot's own
lowercase phase vocabulary — `specify`, `clarify`, `plan`, `checklist`, `tasks`,
`analyze`. It comes from the same single read the completion test below performs,
so naming the phases that finished and naming the phase to resume from are two
renderings of one result rather than two reads that could disagree. A phase that
**failed** rather than finished needs no special case: it is simply the first
non-terminal row.

**When every planning row is terminal, omit `--from-phase` entirely.**
`## Planning Incomplete` is reachable with all six rows terminal, because the
second completion condition is the other half of the test — that is the
strict-mode gate stop, where the row the operator must act on is
`Confidence Gate`. That row is **not** a planning-phase row and has **no token**
in the shipped `--from-phase` vocabulary, so it must never be named as
`<phase>`:

| State | Resume command |
| ----- | -------------- |
| A planning row is non-terminal | the invocation above, with `--from-phase <phase>` |
| All six planning rows terminal, second condition unmet | the invocation with `--stage plan` and **no** `--from-phase` |

The second row is shipped behaviour rather than a workaround: the autopilot
re-resolves the stage from this same status table, the `Confidence Gate` row
sits inside the plan stage's range, and a bare invocation therefore re-enters at
the gate. `<phase>` is one of the six tokens or absent, with no third
possibility — the autopilot range-checks `--from-phase` and stops on a value
outside that range, so an invented token yields a command that fails instead of
resuming.

**Completion is read from the workflow file.** When the chained planning stage
fails, stalls, or is interrupted, completion is determined **by reading the
workflow file** — no live session, and no state file. Two conditions, both in
that one artifact:

```text
1. Every planning-phase row in `## Workflow Overview` — Specify, Clarify,
   Plan, Checklist, Tasks, Analyze — carries a terminal status.
2. A `G6.5` confidence-gate verdict is recorded in the file, AND the
   `Confidence Gate` row does not carry a blocked status.
```

**Condition 2 needs its second clause, and must not instead demand a PASS.**
Presence alone would let a strict-mode gate stop — the very failure this report
exists to name — render under `## Planning Complete`. But a PASS-only test
breaks the **ordinary** case: G6.5 is advisory by default, and in advisory mode
`NO_DATA` soft-skips while `FAIL` logs its breakdown and proceeds to the next
phase. Planning really did complete on those runs, so requiring a PASS would
file the default-mode success as incomplete. The blocked-row clause tells the
two apart using only what the file already carries.

**The `Stage` row is corroborating, not the test.** It records what was
*resolved*, not what *completed*, so a file showing `Stage: plan` with Tasks
still pending is a run in flight rather than a finished one.

**Read the terminal-status vocabulary; never re-declare it.** It is owned by the
`WORKFLOW_TERMINAL_STATUSES` frozenset in
`speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`.
Read it there. **Do not write the status literals into this file**: two of them
differ only by a Unicode variation selector and render identically, so a hand
copy is both prohibited and easy to get wrong.

The reuse case is the same read: a worktree or branch reused from an earlier
scaffold run, carrying a partially complete workflow file, is evaluated by
terminal status on every planning row plus a recorded confidence-gate verdict,
from the file.

**The report names which planning phases reached a terminal status**, and gives
the resume command above.
