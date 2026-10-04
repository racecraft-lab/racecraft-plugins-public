---
name: speckit-scaffold-spec
<!-- host:claude: Claude names skills as /speckit-pro:NAME and reads Claude-only frontmatter keys -->
description: "Use this skill when the user wants to set up, scaffold, bootstrap, prep, initialize, or prepare a SPEC-ID from the technical roadmap for autonomous execution. Triggers on: set up SPEC-XXX, scaffold SPEC-XXX, bootstrap SPEC-XXX for development, prep SPEC-XXX, initialize the workspace for SPEC-XXX, prepare SPEC-XXX for the autonomous run, create a spec branch and workflow for SPEC-XXX, generate the workflow file for SPEC-XXX, I need a workflow file generated for SPEC-XXX, fill the prompts from the roadmap, pre-fill the workflow template, start working on SPEC-XXX, populate the workflow file for SPEC-XXX. Opens with a blind-spot pass, creates the git worktree, spec branch, Design Concept doc, and populated workflow file, then hands off to planning. Accepts --answers-file for unattended setup; otherwise interviews the user. Not for checking roadmap status (use /speckit-pro:speckit-status), running a populated workflow (use /speckit-pro:speckit-autopilot), or SDD coaching (use /speckit-pro:speckit-coach)."
argument-hint: "SPEC-ID [--answers-file <repo-relative JSON path>]"
user-invocable: true
allowed-tools: Read Edit Write Skill Agent ToolSearch
license: MIT
<!-- /host -->
<!-- host:codex: Codex names skills as $NAME -->
description: "Use this skill when the user wants to set up, scaffold, bootstrap, prep, initialize, or prepare a SPEC-ID from the technical roadmap for autonomous execution. Triggers on: set up SPEC-XXX, scaffold SPEC-XXX, bootstrap SPEC-XXX for development, prep SPEC-XXX, initialize the workspace for SPEC-XXX, prepare SPEC-XXX for the autonomous run, create a spec branch and workflow for SPEC-XXX, generate the workflow file for SPEC-XXX, I need a workflow file generated for SPEC-XXX, fill the prompts from the roadmap, pre-fill the workflow template, start working on SPEC-XXX, populate the workflow file for SPEC-XXX. Opens with a blind-spot pass, creates the git worktree, spec branch, Design Concept doc, and populated workflow file, then hands off to planning. Accepts --answers-file for unattended setup; otherwise interviews the user. Not for checking roadmap status (use $speckit-pro:speckit-status), running a populated workflow (use $speckit-pro:speckit-autopilot), or SDD coaching (use $speckit-pro:speckit-coach)."
<!-- /host -->
---

# SpecKit Scaffold Spec

## Installed Runtime Contract

Installed Claude and Codex surfaces resolve Python 3.11 or newer, invoke
`[resolved_python, "-m", "speckit_pro_runner"]`, send one JSON request on
stdin, read one JSON response from stdout, and surface stderr diagnostics.
Do not add a shell fallback, `jq` parsing path, Git Bash, WSL, or
PowerShell-specific command-language requirement for installed workflows.

### Helper request fields

Use these exact runner request fields for the corresponding checks. `mode`
belongs to the request envelope; the last column is its `inputs` object.
Substitute repository-relative paths and the requested SPEC-ID for placeholders.
These examples name the runner's contract; the steps below determine when a check runs.

| Helper | `mode` | `inputs` |
| --- | --- | --- |
| `reviewability-gate` | `read_only` | `{"mode_name": "setup", "target": "<technical-roadmap-path>", "spec_id": "<SPEC-ID>"}` |
| `check-prerequisites` | `read_only` | `{"workflow_file": "<workflow-file>"}` |
| `check-roadmap-freshness` | `read_only` | `{"roadmap_path": "<technical-roadmap-path>"}` |
| `detect-commands` | `read_only` | `{}` |
| `research-broker-preflight` | `read_only` | `{}` |
| `o5-topology` | `read_only` | `{"target": "specs/<parent-branch>"}` |
| `resolve-workflow-binding` | `read_only` | `{"workflow_file": "<absolute-workflow-path>"}` |
| `resolve-scaffold-worktree-placement` | `read_only` | `{"branch_name": "<branch-name>"}` (add `worktree_root_override` only when the user supplied one) |
| `scaffold-answers` | `read_only` | `{"answers_file": "<answers-file>", "spec_id": "<SPEC-ID>"}` |
| `write-readiness-record` | `apply` | `{"host": "<host>", "execution_mode": "<mode>", "plugin_revision": "<version>", "observations": [{"item": "<item>", "status": "<status>", "evidence_source": "<one line>"}]}` (add `action`, `files`, `values` per observation; add `host_version` when reported) |

## Capability discovery & grounding

<!-- host:claude: Claude resolves plugin files through CLAUDE_PLUGIN_ROOT -->
Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it.
<!-- /host -->
<!-- host:codex: Codex has no plugin-root variable, so it links relative to this skill -->
Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `../speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `../speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it.
<!-- /host -->

Prepare a spec from the technical roadmap for autonomous execution.
Creates the worktree, branch, and workflow file — ready for
<!-- host:claude: Claude names skills with a slash -->
`/speckit-pro:speckit-autopilot`.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
`$speckit-pro:speckit-autopilot`.
<!-- /host -->

## Scope

This skill owns the mutation-heavy bootstrap step: identify the roadmap entry,
create or reuse the correct worktree branch, generate the workflow file, and
leave the repository in a state where the autopilot can start immediately.

If the user is still figuring out how to decompose a feature, write a
technical roadmap, or understand the SDD process, redirect them to
<!-- host:claude: Claude names skills with a slash -->
`/speckit-pro:speckit-coach`.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
`$speckit-pro:speckit-coach`.
<!-- /host -->
Do not invent roadmap data or phase prompts from vague requirements when the
roadmap entry does not exist.

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
Run runner helper o5-topology with the request fields above.
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
<!-- host:claude: Claude names skills with a slash -->
/speckit-pro:speckit-scaffold-spec SPEC-009
/speckit-pro:speckit-scaffold-spec SPEC-008 --answers-file answers.json
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
$speckit-pro:speckit-scaffold-spec SPEC-009
$speckit-pro:speckit-scaffold-spec SPEC-008 --answers-file answers.json
<!-- /host -->
```

## Input

Accept:

- a required `SPEC-ID` such as `SPEC-009`
- an optional `--answers-file <repo-relative JSON path>` for unattended setup
- an optional technical roadmap path if the user already knows it
- an optional worktree root override if the repository uses a nonstandard
  location

If the request does not include a SPEC-ID, stop; ask for it only in interactive mode. Everything
else should be derived from the repository.

## Hard Constraints

- Never commit or push `main`.
- Re-read the active branch immediately before every commit and push; if it is
  `main`, stop before the mutation.
- Detect the actual git remote name before pushing.
- Create or reuse a dedicated worktree branch for the spec.
- After the worktree exists, perform all file edits inside the worktree, not in
  the main checkout.
- Use the shared workflow template shipped with this plugin at
  `skills/speckit-coach/templates/workflow-template.md` relative to the
  speckit-pro plugin root directory.
- Do not leave placeholder tokens such as `SPEC_ID`, `SPEC_NAME`, or empty
  phase prompts in the generated workflow.
- Never run the autopilot at the end. Setup stops once the workflow is ready,
  committed, and pushed, and prints the hand-off Step 9 defines. The operator
  runs it.
- In interactive mode, always run the Grill Me interview before writing the workflow file. The
  Design Concept doc is a required setup output, not optional. Setup must not
  attempt to fabricate design-concept content if grill-me aborts.

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

## Answers-file mode

With `--answers-file`, first call runner helper `scaffold-answers` in
`read_only` mode with `inputs.answers_file` and `inputs.spec_id`. Run it from
the task checkout before any mutation, retain its returned answers across the
worktree change, and proceed only on `status=ok`. On failure, print
`data.problems[]` and end scaffold. `data.questions_allowed=false` applies to
all later steps, including bootstrap, offers, artifact replacement and handoff.
Report any additional required answer by its key and end rather than asking.

The JSON contract is `schema_version: "scaffold-answers/v1"`, the invocation's
`spec_id`, and an `answers` object. Its interview keys are `goals`, `non_goals`,
`module_interface_deltas`, `terms`, `verification_gates`, `design_tree`, and
`open_questions`, each holding the user's text for the corresponding Design
Concept section. Supply explicit booleans for `quality_gate_confirmation`,
`formal_methods`, `verification_docker`, and `continue_to_planning`.
`bootstrap_commands` must be `[]`; the helper rejects supplied commands.
Prepare dependencies through interactive approval before unattended scaffold.
The helper owns validation of these keys and values.

Continue the blind-spot pass. At Step 4, instead of invoking interactive
Grill Me, write the Design Concept using the validated interview answers and
the shared `grill-me/references/output-formats.md` layout. Preserve the supplied
Q&A log, mark the source as the answers file, record zero questions asked, and
carry the blind-spot header. Leave an existing Design Concept unchanged and
report the replacement answer needed. Unanswered findings remain Open Questions.

Use the prepared environment and skip Step 3.5 bootstrap. Present the quality-gate
confirmation, formal-methods offer and verification-Docker offer, and record
their file answers. Carry accepted selections from `verification_gates` into
the workflow; a selection needing more details ends with the missing key.
At Step 9, use `continue_to_planning` for the closing report and print the
planning command. The operator still starts planning as a separate invocation.
The interactive instructions below apply when `--answers-file` is absent.

## What to Do

<!-- host:claude: Claude loads plugin agents from the plugin cache and cannot repair them from inside a skill -->
### -0.5 Verify Claude Agent Package Completeness

Before parsing or mutating the repository, resolve the plugin root from this
skill location and verify by filesystem reads that every bundled Claude Code
`agents/*.md` file is present, including `uat-runbook-author.md`.
Do not use `install-codex-agents` as a Claude-side repair: Claude Code loads
plugin agents from the plugin cache, so scaffold cannot safely self-heal a
missing Claude agent file. If the file inventory is incomplete, STOP and
tell the user to update/reinstall `speckit-pro`, run `/reload-plugins`, and
retry.
<!-- /host -->
<!-- host:codex: Codex installs custom agents with the install-codex-agents helper -->
### -0.5 Verify Codex Agent Install

Before parsing or mutating the repository, resolve the plugin root and verify
with the promoted `install-codex-agents` helper. Replay the selected installation inputs
with request-envelope `mode="dry_run"`. For a static installation, use these request fields:

```json
{"mode": "dry_run", "inputs": {"destination": "<selected-destination>", "model": "<selected-model>", "luna_fallback": false}}
```

For a route-aware installation, use these request fields instead:

```json
{"mode": "dry_run", "inputs": {"destination": "<selected-destination>", "route_policy_manifest": "<selected-route-manifest>", "strict_model_override": "<selected-override>"}}
```

Substitute the actual selected values, including the selected `luna_fallback` boolean.
Omit optional fields that were absent from the selected installation, preserving
its user-scope destination when `destination` was omitted. Route-aware verification
reuses the selected manifest and optional override instead of static model defaults.
The plan must show every bundled TOML, including
`uat-runbook-author.toml`, as current. If any required file is missing or stale,
STOP, instruct the user to run `$speckit-pro:install`, restart Codex, and then retry
scaffold. Do not apply the repair inside scaffold because this process cannot
reload changed custom agents safely.
<!-- /host -->

### 0. Ensure SpecKit CLI

Check for the official SpecKit CLI before parsing or mutating the repository:

Use command execution to confirm `command -v specify` finds the official
`specify` CLI after including common user-local binary directories
(`$HOME/.local/bin`, `/opt/homebrew/bin`, `/usr/local/bin`) on PATH.

If missing and `uv` exists, install it:

Run `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`.

If `uv` is unavailable or install fails, STOP and tell the operator to install
SpecKit with that command. Do not continue with setup without the `specify`
command. Do not run `specify init --here --force` automatically: project
initialization and forced refreshes can overwrite managed files. Recommend it
only when `.specify/` is absent and the operator explicitly approves project
initialization.

### 1. Find the Technical Roadmap

Use the roadmap path the user supplied. Otherwise search before asking where
it lives: files matching `**/*technical*roadmap*` or `**/*technical-roadmap*`,
plus `docs/ai/*roadmap*.md` and `docs/ai/specs/*roadmap*.md`.

If no technical roadmap found, STOP: "No technical roadmap found. Create
one with
<!-- host:claude: Claude names skills with a slash -->
`/speckit-pro:speckit-coach help me create a technical roadmap`."
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
`$speckit-pro:speckit-coach help me create a technical roadmap`."
<!-- /host -->

Before parsing the roadmap, run runner helper `check-roadmap-freshness` with
`roadmap_path` set to the roadmap path relative to the repository root. It
fetches the remote and compares the roadmap in this checkout with the one on
the remote default branch. Require `verdict=proceed`. On `verdict=stop`, print
the returned `stop_message` unchanged and STOP: parse no roadmap entry, run no
gate, and write nothing. Keep the returned `base_revision`: step 3 bases a new
spec worktree branch on it, so the roadmap you parse and the worktree come from
the same revision.

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
- **Status** (⏳ Pending proceeds. If the roadmap marks the spec
  complete, warn the user and STOP. If it marks the spec in progress,
  reuse its existing worktree branch rather than creating a second setup;
  the placement helper in step 3 returns `disposition=reuse` for it)

If the SPEC-ID is not found, STOP: "SPEC-ID not found in
technical roadmap. Available specs: <list pending specs>."
Offer to help the user add or correct the roadmap entry with
<!-- host:claude: Claude names skills with a slash -->
`/speckit-pro:speckit-coach`; do not invent the entry or continue scaffolding.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
`$speckit-pro:speckit-coach`; do not invent the entry or continue scaffolding.
<!-- /host -->

Run the reviewability setup gate before creating the worktree:

```text
Run runner helper reviewability-gate with the request fields above.
Set `target` to the repository-relative technical roadmap path and `spec_id`
to the requested SPEC-ID.
```

If it returns an unexcepted `block`, STOP and split the spec first. Tell the
user which threshold requires decomposition. Warnings may proceed only when the
workflow records the scope budget and split decision.

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
STOP before mutation. An explicit override is not permission to escape the
current task workspace.

This ordering is invariant: the first resolver result comes before
`git worktree add`, artifact writes, or roadmap mutation. Only after that
result passes may scaffold create or reuse the worktree. A second resolver
check then runs after creation or reuse and immediately before bootstrap or
Grill Me. Neither bootstrap nor Grill Me may begin unless that second check
confirms the registered worktree described below.

Without an override, require the helper's exact
`TASK_ROOT/.worktrees/<branch-name>` result, where `TASK_ROOT` is the canonical
current task checkout. Never derive worktree placement from
`git rev-parse --git-common-dir`, the primary checkout, or the first
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
   branch as the observed state requires. Base a new branch on the
   `base_revision` from step 1, never on the checkout's current commit. Never commit or push `main` while
   recovering or reusing a remote branch.
3. Never substitute a different path because branch creation or remote lookup
   is inconvenient; rerun the resolver if live state changes.
4. Verify the active branch inside the returned worktree before any push. It
   must equal the helper's `branch_name` and must not be `main`.

Re-run `resolve-scaffold-worktree-placement` after
worktree creation and again before bootstrap or Grill Me on both create and
reuse paths.
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

**This step is mandatory.** Every scaffold invocation runs the
blind-spot pass FROM the worktree, immediately before the grill-me interview.
There is no skip flag, no skip argument, and no documented path that reaches
the interview without attempting the pass.

Mandatory to **attempt**, not to succeed: the pass fails open, as the end of
this step sets out.

</hard_constraints>

**Engine.** The pass runs on the already-shipped read-only `codebase-analyst`,
consumed unmodified. Do not add or edit an agent definition.

<!-- host:claude: Claude dispatches the plugin agent with the Agent tool -->
**Dispatch, then await.** Dispatch the analyst, then await its own final summary
BEFORE the interview begins:

```text
Agent(subagent_type: "speckit-pro:codebase-analyst", run_in_background: true,
      prompt: "...\nReference dir: ${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/")
```

The await is not optional: the Claude agent definition carries
`background: true`, so an un-awaited dispatch hands back a task identifier
rather than findings.

**Arm the deadline in the same turn as the dispatch.** Start the deadline timer
as a background command (`run_in_background: true`) that runs
`[resolved_python, "-c", "import time; time.sleep(300)"]`, the same resolved
interpreter the runner uses. It exits 300 seconds (the pass execution deadline
below) after dispatch, and its completion notice wakes the session while the
analyst is still running; nothing else would. Keep both task ids, then act on
whichever completion notice arrives first:

- **The analyst replies first:** stop the timer with `TaskStop` on its task id,
  so a stale wake cannot land mid-interview, then classify the reply below.
- **The timer completes first:** the deadline has passed. Stop the analyst with
  `TaskStop` on its task id, record `did not run` with reason
  `wait deadline expired`, and continue into the interview.

If the timer call is denied or fails, nothing can enforce the deadline: stop
the analyst with `TaskStop` and record `did not run` with reason
`dispatch error: <the timer's error>`.
<!-- /host -->
<!-- host:codex: Codex spawns the custom agent with spawn_agent and polls wait_agent -->
**Dispatch, then await.** Dispatch with `spawn_agent`, using
`agent_type: "codebase-analyst"` and `fork_turns: "none"`, then poll
`wait_agent` in a bounded loop until the actual summary is delivered. The Seed
below is a self-contained task package, so the analyst does not need inherited
turns. Never omit `fork_turns` and never use `fork_turns: "all"` while selecting
this custom agent: a full-history fork inherits the parent agent type and Codex
rejects the incompatible override. A status update, an unrelated mailbox wake,
or a terminal status without a delivered result is **not** the result. Call
`close_agent` only when that action is exposed. The await completes BEFORE the
interview starts. Each `wait_agent` call is one wait; consecutive expired waits
are the loop's cue to check the execution deadline below, not a second
independently-triggering bound.

**The loop is the deadline timer.** Note the dispatch time. On every
`wait_agent` call, pass `timeout_ms` set to the time left until the pass
execution deadline, never more, so the loop wakes no later than the deadline.
When the deadline passes with no summary, call `close_agent` on the analyst
when that action is exposed, otherwise `interrupt_agent` when exposed, then
record `did not run` with reason `wait deadline expired` and continue into the
interview. When neither action is exposed, abandon the wait and leave the
thread to the host; the recorded outcome is the same.
<!-- /host -->

**The bound. A single wait expiring is not the deadline.** Abandonment is
governed by one execution deadline for the whole pass:

| Bound | Value | On expiry |
| ----- | ----- | --------- |
| Per-wait timeout | whatever the surface provides | keep waiting; **not** a verdict |
| Pass execution deadline | **5 minutes from dispatch** | stop the analyst as the dispatch step above says, and record the `did not run` outcome with reason `wait deadline expired` |

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

**The dispatch block, carried verbatim.** It is one text for both hosts,
because the shipped `codebase-analyst` description frames the agent
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

Budget: at most 40 tool calls. When you reach it, stop exploring and return the
findings you have, ranked as below; a partial list beats no report.

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

**This step is mandatory in interactive mode.** Every interactive scaffold invocation runs grill-me before
the workflow file is written. There is no `--no-grill` flag and no skip
path — the interview is what makes the workflow prompts good enough for
autonomous execution.

<!-- host:claude: Claude asks through AskUserQuestion -->
**Grill-me is human-in-the-loop only.** It uses `AskUserQuestion` to
interview the user. If you are running this command in a non-interactive
context (CI, background agent, automation), abort the entire scaffold
invocation — do not attempt to skip grilling.
<!-- /host -->
<!-- host:codex: Codex asks through request_user_input, with a foreground chat fallback -->
**Grill-me is human-in-the-loop only.** Codex grill-me uses a
picker-first HITL guard: call `request_user_input` for each Grill Me question
when it is available. If it is unavailable in an active foreground user chat, ask the same
single Grill Me question in free text and wait for the direct reply. In an
autonomous, background, CI, or subagent run, stop before writing and require
direct user interaction; never start a free-text interview there.
<!-- /host -->

</hard_constraints>

1. Create the `.process/` docs directory in the WORKTREE for the design
   concept (created when absent so the first exhaust artifact lands
   correctly): `<worktree_root>/docs/ai/specs/.process/`.

2. Invoke the grill-me skill from inside the worktree in setup mode, with the
   spec scope as input:

<!-- host:claude: Claude invokes a sibling skill with the Skill tool -->
   ```text
   Skill("grill-me", args: {
     mode: "setup",
     spec_id: "SPEC-<ID>",
     spec_name: "<spec name from roadmap>",
     scope: <full scope description from technical roadmap, with the Step 3.6
             BLIND-SPOT PASS FINDINGS block appended below it>,
     output_path: "<worktree_root>/docs/ai/specs/.process/SPEC-<ID>-design-concept.md"
   })
   ```
<!-- /host -->
<!-- host:codex: Codex invokes a sibling skill by its dollar-sign name -->
   Invoke `$speckit-pro:grill-me` with a setup-mode marker, the spec ID and name, the full
   scope description from the technical roadmap (and any constraints,
   dependencies, or stated tools) with the step 3.6 BLIND-SPOT PASS FINDINGS
   block appended below it, and the output path
   `<worktree_root>/docs/ai/specs/.process/SPEC-<ID>-design-concept.md`.
<!-- /host -->

3. The skill walks the design tree one question at a time, with the AI's
   recommendation marked as the first option, and surfaces the key answers
   (Goals, Non-goals, major design decisions) back to this skill. It returns
   when the user reaches a natural stop, hits the soft cap at 30 questions and
   chooses to wrap up, or selects "End interview". If grill-me aborts (no
   interactive runtime), stop setup and report the condition.
   Do not synthesize design-concept content yourself.

4. Read `<worktree_root>/docs/ai/specs/.process/SPEC-<ID>-design-concept.md`
   — `<ID>` being the roadmap identity in full, including whatever namespace
   prefix it carries. Reading a path the run never wrote would report the key
   absent and repair a file that does not exist. The doc must contain Goals,
   Non-goals, Module and Interface Deltas, Terms, Verification Gates, Design
   Tree (Q&A log), and Open Questions. It must also carry the
   `**Blind-spot pass:**` key in its header blockquote.

5. Repair that key when it is absent. The interview is the writer of first
   resort, but the request is one sentence inside a prose block handed to
   another skill, so verify rather than assume. If the key is missing, edit
   the Step 3.6 header line into the existing header blockquote from the values
   already held at the moment the status line was rendered — the outcome, the
   `<reason>` clause, and N and M for the `ran` outcome. Nothing is derived a
   second time. Read to check and edit to repair. No new section and no
   separate findings artifact.

When the interview does not return, nothing is owed. The run stops when no
interactive runtime is available, so no design concept exists to carry a record
and the Step 3.6 status line is the only one. That is correct rather than a gap:
the run does not continue, so there is no later reader to serve.

The labelled block is the **only** channel the pass uses into the interview, and
it travels in all three Step 3.6 outcomes — carrying only its status line in the
degraded two. Do not add a new interview argument, do not change what the
interview produces, and never edit any file under the grill-me skill. The
`scope` input already exists; this appends to it.

The Q&A log and Goals/Non-goals from this doc drive the next step's
workflow prompts. Pass the doc path forward.

### 5. Copy Workflow Template (IN the Worktree)

All file operations happen in the worktree directory.

0. Require the generic `speckit-pro-reviewability` preset to already exist in
   the worktree. If the preset is absent, STOP and report the missing
   prerequisite.

   Verify resolution from `<worktree_root>/` with
   `specify preset resolve spec-template`,
   `specify preset resolve plan-template`, and
   `specify preset resolve tasks-template`. Each command should resolve to
   `.specify/presets/speckit-pro-reviewability/` or to a project-specific
   higher-priority override that intentionally includes the reviewability
   sections.

1. Read the shared workflow template from the plugin. Do not author a new
   template from scratch.
<!-- host:claude: Claude resolves plugin files through CLAUDE_PLUGIN_ROOT -->
   Read `${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/workflow-template.md`.
<!-- /host -->
<!-- host:codex: Codex has no plugin-root variable, so it links relative to this skill -->
   Read `../speckit-coach/templates/workflow-template.md` relative to this skill.
<!-- /host -->

2. Write the template content to the WORKTREE at
   `<worktree_root>/docs/ai/specs/.process/SPEC-<ID>-workflow.md`.

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
<!-- host:claude: Claude resolves plugin files through CLAUDE_PLUGIN_ROOT -->
   ${CLAUDE_PLUGIN_ROOT}/skills/speckit-coach/templates/spec-moc-template.md
<!-- /host -->
<!-- host:codex: Codex has no plugin-root variable, so it links relative to this skill -->
   ../speckit-coach/templates/spec-moc-template.md (relative to this skill)
<!-- /host -->

3. Token-substitute the template (same {{TOKEN}} mechanism as the workflow
   template) and write it to the contract directory at
   <worktree_root>/specs/<branch-name>/SPEC-MOC.md, with the tokens below
   substituted:

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
  after the grill-me interview is exactly what the Clarify phase should
  be told to dig into. Generate session focuses from the unresolved
  branches and the spec's main surfaces, one focus per open
  behavior area.

- **Plan Prompt:** Combine the tech stack from CLAUDE.md / AGENTS.md, the
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

The prompts should be strong enough that the autopilot can execute without the
user hand-editing obvious missing context. If a critical detail cannot be
derived from the roadmap or the design concept, stop and report the gap rather
than filling it with fiction.

### 6.5 Write the Readiness Record (IN the Worktree)

Record what this run observed, so autopilot reads evidence instead of
stopping to ask (ADR 0008). From the worktree root, run helper
`write-readiness-record` with the request fields above. The step is done when
the response is `ok` with a `record_path`, or a failed write is reported.

<!-- host:claude: Claude names its own host and reads the plugin manifest through the plugin root -->
Set `host` to `claude`. Set `plugin_revision` to the `version` in
`${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json`.
<!-- /host -->
<!-- host:codex: Codex names its own host and reads the plugin manifest relative to this skill -->
Set `host` to `codex`. Set `plugin_revision` to the `version` in
`../../.codex-plugin/plugin.json`.
<!-- /host -->
Set `execution_mode` to `answers-file` or `interactive`. Send one observation
per item:

| `item` | Observed from |
| --- | --- |
| `plugin_payload` | the agent check at the start of this run and the revision above |
| `project_integration` | the Specify, bootstrap and detect-commands results |
| `github_auth` | one bounded GitHub authentication check |
| `mcp_servers` | the `research-broker-preflight` result |
| `typesafe_jev` | whether this session exposes the Jev `evaluate` tool |
| `reviewability_report` | the setup gate result, cited by roadmap path and SPEC-ID |

- Record `verified` for a check that passed in this run. Record `unavailable`
  for a failed check or a declined fix, `unknown` for what this session cannot
  observe, and `not_applicable` for a capability this workflow does not need.
- Give every `unavailable` or `unknown` item an `action`: what the user does
  next.
- Send `files` as repository-relative paths and `values` as named text; the
  helper stores digests only. Send `evidence_source` as one plain line.
- The helper observes `local_capability` and `quality_gates` itself. Omit
  `host_version` when the host does not report it.
- Print one line per `unavailable` or `unknown` item with its action, then
  continue. A declined fix, a failed fix, or a failed write leaves scaffold
  finishing normally.

The record is git-ignored; leave it unstaged.

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

2. Push the WORKTREE BRANCH to the detected remote:
   From `<worktree_root>/`, run `git push -u <remote> <branch-name>`.

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
**Worktree root:** <absolute path from `git rev-parse --show-toplevel` run inside the worktree>
**Remote:** Pushed to <remote>/009-search-database
**Bootstrap:** <commands run, documented health check, or "no documented bootstrap">

<!-- host:claude: Claude changes the session directory with /cd before invoking the autopilot -->
**If you stop here, run:**
/cd <absolute-worktree-root>
/speckit-pro:speckit-autopilot <absolute-workflow-file> --stage plan
<!-- /host -->
<!-- host:codex: Codex runs the autopilot by its dollar-sign name in the same task -->
**Next step:** continue in this same Codex task by running:
$speckit-pro:speckit-autopilot <absolute-workflow-file> --stage plan
<!-- /host -->

**Review both files** — the design concept doc captures the
decisions you made during grill-me; the workflow file is what the
autopilot will execute. Verify the phase prompts have enough context
for autonomous execution.
```

Never hand off only the inner workflow path from the parent checkout. The
absolute workflow path identifies the generated spec worktree; autopilot binds
all execution there and never treats main, a detached checkout, or the parent
checkout as its mutation root.

### 8. Update Technical Roadmap Status (IN the Worktree)

Update the technical roadmap's Progress Tracking table IN THE
WORKTREE (not on main) to mark the spec as `🔄 In Progress`:

```text
1. Edit the technical roadmap found in Step 1 at its WORKTREE path,
   `<worktree_root>/<roadmap-path-from-step-1>`.

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

<!-- host:claude: Claude hands off with /cd and a slash command in the same session -->
**Scaffold never invokes the autopilot or `/cd`. It prints both commands; the
operator explicitly sends them in this same session.** On Claude Code the
autopilot skill carries `disable-model-invocation: true`, which the skills
documentation defines as "Only you can invoke the skill" — a deliberate setting,
because a seven-phase autonomous run that commits as it goes is exactly the kind
of side effect an operator must trigger themselves. **Never state that accepting
will run the planning phases or change directories automatically.**
<!-- /host -->
<!-- host:codex: Codex hands off with one dollar-sign command in the same task -->
**Scaffold never invokes the autopilot. It prints the command; the operator runs
it as the next message in the same task.** A skill body invoking a sibling skill
mid-session is unverified on Codex, and a seven-phase autonomous run that
commits as it goes is exactly the kind of side effect an operator must trigger
themselves. Printing a command that always works beats shipping an invocation
that may not. **Never state that accepting silently runs the planning phases;
the operator explicitly starts them with the printed command.**
<!-- /host -->

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

<!-- host:claude: only Claude changes the session directory before the autopilot runs -->
The absolute root and canonical absolute workflow path are deliberately passed
separately. `/cd` changes Claude Code's live session directory and reloads
directory-scoped instructions; the absolute autopilot path then identifies
exactly the generated worktree even if another registered worktree contains a
stale same-named workflow. That duplicate therefore cannot make the retry
ambiguous or redirect planning commits to main.
<!-- /host -->

**What the check must NOT test: the most recent commit.** After Step 8 the
newest commit is the roadmap status flip rather than the workflow-file commit,
so a last-commit test would fail on every correct run.

**What each result selects:**

| Check result | Effect on the hand-off |
| ------------ | ---------------------- |
| Step 1 passes | print the same-session hand-off below |
| Step 1 fails | report the helper's `binding_status` and `problems[]`, and print the recovery: reopen in a new session or task rooted at the generated worktree; never invite autopilot from the parent checkout |
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
nothing does.
<!-- host:claude: Claude asks through AskUserQuestion -->
Use `AskUserQuestion`:
<!-- /host -->
<!-- host:codex: Codex asks through request_user_input -->
Use `request_user_input` when it is present:
<!-- /host -->

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

**The budget counts what this step adds**: exactly one confirmation. Step 3.5's
bootstrap approval and the grill-me questions are pre-existing, are not counted,
and are not removed.

<!-- host:claude: Claude changes the session directory with /cd, then runs the slash command -->
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
<!-- /host -->
<!-- host:codex: Codex has no directory-change command; autopilot binds to the absolute workflow path -->
**The hand-off has one command:**

```text
$speckit-pro:speckit-autopilot <absolute-workflow-file> --stage plan
```

This is the ordinary same-task outcome. OpenAI documents worktrees as
separate checkouts and Handoff as movement between Local and a task's associated
worktree, including returning that task to the same associated worktree; it is
not an arbitrary filesystem-path selector:
<https://learn.chatgpt.com/docs/environments/git-worktrees>. This hand-off does
not pretend to move the task or change its checkout. Autopilot instead binds
every operation and agent explicitly to the registered nested `WORKFLOW_ROOT`.
If Step 1 cannot prove a registered, canonical binding, report its concrete
`binding_status` and `problems[]` and stop before mutation; the fail-closed
fallback is a new Codex task rooted at the canonical worktree. A later user may
explicitly select the absolute workflow path from the same Codex task; the
autopilot checks that selection and permissions at invocation time.

The leading `$speckit-pro:speckit-autopilot` token is the invocation form this skill set
uses: Codex plugin skills are invoked via `$speckit-pro:<skill-name>`, never via a
`/<plugin>:<skill>` slash command.
<!-- /host -->

The stage token is the literal lowercase `plan`, from the closed vocabulary
`plan`, `implement`, `full`. No aliases, no alternate casing, no long-form
spellings. The workflow file is the canonical absolute path in the generated
worktree, so a stale same-named copy in another registered worktree cannot make
the retry ambiguous. Never pass a state file, branch name, feature directory,
or environment variable to autopilot across the boundary.

**Nothing is rolled back on any path.** Everything scaffold owns is committed and
pushed before this step runs, so the operator who stops here defers the
hand-off and loses no work.

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
<hand-off block>
```

**The heading is one fixed string, `## Ready for Planning`**, on all three
endings.

**Fixed, conditional, and derived.** The heading and the draft-PR line are
fixed, except that the draft-PR line is conditional on a URL existing. The
outcome line, the artifact index, and the next step are **derived** — each has
its own rule below. `<hand-off block>` is the Step 9 hand-off in the form its
check selected.
<!-- host:claude: Claude's hand-off is two commands -->
On Claude Code it is the `/cd` command followed by the absolute-workflow
autopilot command. It remains one report element even though it is rendered on
two lines.
<!-- /host -->
<!-- host:codex: Codex's hand-off is one command -->
On Codex it is the one absolute-workflow autopilot command.
<!-- /host -->

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

**The next step is the Step 9 hand-off**, in the form that step's
check selected. Scaffold names
the planning hand-off as the operator's next action, never as its own action,
and never asks a second confirmation to offer it.

## Failure Handling

Stop instead of improvising when any of the following are true:

- no technical roadmap exists
- the SPEC-ID is not in the roadmap
- the branch or worktree state is ambiguous and cannot be safely reused
- git push fails
- the workflow still contains unresolved placeholders after population; name
  each placeholder that remains
- grill-me aborts because no interactive runtime is available. Scaffolding is
  HITL-gated by design.
<!-- host:codex: codex exec is Codex's non-interactive mode -->
  On Codex this happens under `codex exec` or a CI runner; re-run scaffold in
  an interactive Codex session.
<!-- /host -->

If scaffolding partially succeeds before a failure, report exactly what was created
and what remains unfinished so the user can resume without duplicating work.
For a push failure, preserve and report the existing absolute worktree root,
spec branch, workflow path, local commit SHA, detected remote, and failed push
diagnostic. Do not recreate the branch or worktree, repeat completed scaffold
mutations, or claim the remote branch exists. After the remote problem is
fixed, retry the same failed push from that same worktree with
`git -C <absolute-worktree-root> push -u <remote> <spec-branch>`, then resume at
the first unfinished scaffold step. The hand-off remains blocked until the
same-worktree retry succeeds and the branch is verified on the detected remote.
