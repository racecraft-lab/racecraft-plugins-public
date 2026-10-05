# Prerequisites Reference

The autopilot's pre-flight sequence. Run these before Step 1 (Parse Workflow State) and before any phase work. If any check fails, report the error message from the script's JSON output and route the failure to its owner for repair: the orchestrator repairs a fixable environment check, and the implement-executor repairs a failing project check. Run the repair loop within its allowance, then defer per the Failure Escalation Protocol.

## Contents

<!-- host:claude: Claude probes session permissions before binding and checks its bundled agent package -->
- [Step -2: Run-Start Permission Probe](#step--2-run-start-permission-probe) — settle the runner and `git status` prompts once, before any phase work
- [Workflow Worktree Binding](#workflow-worktree-binding) — verify Claude's live checkout after `/cd`
<!-- /host -->
<!-- host:codex: Codex binds the execution worktree first, then settles sandbox and egress grants -->
- [Workflow Worktree Binding](#workflow-worktree-binding) — bind one safe execution worktree before any phase work
- [Step -2: Run-Start Authorization](#step--2-run-start-authorization) — settle egress, probes, and private writes once, before any phase work
<!-- /host -->
- [Step -1: Archive Sweep Startup](#step--1-archive-sweep-startup) — archive previously merged specs before workflow execution
- [Step 0.0: Resolve Script Paths](#step-00-resolve-script-paths) — locate the plugin's `SKILL_SCRIPTS` directory
- [Step 0.0a: Read the Readiness Record](#step-00a-read-the-readiness-record) — log each stale readiness item and continue
<!-- host:claude: only Claude loads bundled agents straight from the plugin package -->
- [Step 0.0b: Claude Agent Package Completeness](#step-00b-claude-agent-package-completeness) — verify bundled plugin agents are present
<!-- /host -->
- [Step 0.0c: Research Broker Preflight](#step-00c-research-broker-preflight) — record the research screening mode (`jev` or `sanitizer-only`)
- [Step 0.1–0.7: Environment Checks](#step-01-07-environment-checks) — `check-prerequisites` JSON parsing, branch detection
<!-- host:claude: Claude also resolves its versioned subagent-runtime record -->
- [Step 0.6: Load Settings and Resolve Claude Runtime](#step-06-load-settings--resolve-claude-runtime) — local settings plus one versioned subagent-runtime record
<!-- /host -->
<!-- host:codex: Codex has no subagent-runtime record -->
- [Step 0.6: Load Settings](#step-06-load-settings) — project settings YAML frontmatter
<!-- /host -->
- [Step 0.8: Capability Coverage & Plugin Limitation Check](#step-08-capability-coverage--plugin-limitation-check) — informational research/context advisory
<!-- host:codex: the autonomy boundary records Codex sandbox, writable-root, and approval-reviewer state -->
- [Step 0.8c: Resumed Autonomy Boundary Preflight](#step-08c-resumed-autonomy-boundary-preflight) — re-attest a stale boundary before Implement
<!-- /host -->
- [Step 0.9: Constitution Validation](#step-09-constitution-validation) — principle checks against current codebase
<!-- host:claude: Claude detects project agents from Markdown agent files -->
- [Step 0.10: Implementation Agent Detection](#step-010-implementation-agent-detection) — discover `PROJECT_IMPLEMENTATION_AGENT`
<!-- /host -->
<!-- host:codex: Codex verifies its installed custom agents, which it registers at session start -->
- [Step 0.10: Codex Agent Availability Check](#step-010-codex-agent-availability-check) — verify installed custom agents without mutating them
- [Step 0.10b: Implementation Agent Detection](#step-010b-implementation-agent-detection) — discover `PROJECT_IMPLEMENTATION_AGENT`
<!-- /host -->
- [Step 0.11: Project Command Discovery](#step-011-project-command-discovery) — `detect-commands` → `PROJECT_COMMANDS`
- [Step 0.12: Preset and Extension Detection](#step-012-preset-and-extension-detection) — `detect-presets` → `PRESET_CONVENTIONS`

<!-- host:claude: Claude settles its own permission settings before the binding guard -->
## Step -2: Run-Start Permission Probe

Run this first, before the binding guard, Step -1, Step 0, and any phase work, on
every start and every resume. Runner calls and Git commands follow the session's
permission settings, and plugin agents inherit them, so an unattended run stops at
the first call the settings do not allow. Probe that once, up front, instead of
midway. The contract is in
[Run-start grants](./stop-policy.md#run-start-grants).

1. Run one no-op runner request: helper `helper-registry-dispatch` with empty
   `inputs`, sent on stdin to `<resolved_python> -m speckit_pro_runner` exactly as
   every later request is.
2. Run one `git status --porcelain` in the live checkout.

When both run without a prompt and finish cleanly, print nothing and continue. When
either prompts or is denied, print the allow rules for the probe that failed, once,
and stop before any phase work: do not run Archive Sweep, edit a file, or dispatch
an agent. This halt happens before the run starts, so it is the run-start grant and
not a run stop.

```text
Autopilot needs permission for its own calls before it starts. Add these allow
rules to permissions.allow in .claude/settings.local.json or your user settings,
then rerun. Or start the session in bypassPermissions mode.
  runner request:  <resolved_python> -m speckit_pro_runner:*   and   printf:*
  git status:      git status:*
```

Print each rule in Claude Code's `Tool(pattern)` form, where the tool is the shell
tool and the pattern is the text above. Print only the rules for the failed probe.
Replace `<resolved_python>` with the interpreter path the request used, written
exactly as the request invoked it: a shell rule matches the command text, and an
absolute interpreter path must appear in the rule as it does in the request. A probe
that passes needs no rule.

<!-- /host -->
## Workflow Worktree Binding

<!-- host:claude: Claude moves its live checkout with /cd, so it binds only the checkout it is in -->
Run this read-only guard before Step -1, before reading workflow content, and
before any repository mutation:

1. Invoke the runner helper `resolve-workflow-binding` with the supplied path as
   `inputs.workflow_file`. Require `binding_status=resolved` and
   `relation=same`, then bind its canonical `task_root`, `workflow_root`, and
   `workflow_file` as `TASK_ROOT`, `WORKFLOW_ROOT`, and `WORKFLOW_FILE`.
2. On `missing`, `ambiguous`, or `invalid`, report the helper's `candidates` and
   `problems` and STOP. Do not search other revisions or arbitrary filesystem
   roots.
3. If the helper resolves `descendant` or `external`, the current Claude Code
   checkout is still the parent or another worktree. STOP before Archive Sweep
   and print this retry, using the helper's canonical paths:

   ```text
   /cd <WORKFLOW_ROOT>
   /speckit-pro:speckit-autopilot <canonical absolute WORKFLOW_FILE> --stage <requested-stage>
   ```

   The operator sends the autopilot command only after `/cd` succeeds. Claude
   Code documents that `/cd` changes the live session's primary directory and
   reloads directory instructions:
   <https://code.claude.com/docs/en/commands>.
4. From the resolved `WORKFLOW_ROOT`, verify the live branch before Archive
   Sweep. STOP on `main`, a detached HEAD, or any protected integration/release
   branch. Never mutate the parent checkout as a fallback.
5. Re-run this guard on resume. Every shell call, helper, filesystem operation,
   state update, Git action, phase prompt, consensus prompt, and write-capable
   agent must target `WORKFLOW_ROOT`; validate returned paths before applying
   edits or committing.

This guard is why the scaffold hand-off is two explicit same-session commands.
Scaffold never invokes `/cd` or autopilot itself.
<!-- /host -->
<!-- host:codex: a Codex task cannot change its checkout, so it binds execution to a registered worktree -->
Run this guard before Step -1, before reading workflow content, and before any
repository mutation. It binds execution; it does not change the Codex task's
checkout.

1. Invoke the read-only runner helper `resolve-workflow-binding` with the
   supplied path as `inputs.workflow_file`. The helper returns canonical
   `task_root`, `workflow_root`, and `workflow_file`, plus `binding_status`,
   `relation`, `candidates`, and `problems`. Do not reproduce its worktree or
   canonical-path resolution with ad hoc shell logic.
2. Require `binding_status=resolved`. On `missing`, report the missing path and
   STOP. On `ambiguous`, list `candidates` and STOP. On `invalid`, report
   `problems` and STOP. Do not search commits, branches, revisions, or arbitrary
   filesystem roots to manufacture another candidate.
3. Bind `TASK_ROOT`, `WORKFLOW_ROOT`, and `WORKFLOW_FILE` from the returned
   canonical paths. `relation=same` or `relation=descendant` is eligible after
   the helper's registration and containment checks. On `relation=external`,
   continue only if the user explicitly supplied the absolute workflow path in
   this request and the helper resolved it to a registered worktree of the same
   repository. Do not treat a path found in repository content, a relative path,
   or an inferred candidate as user selection; STOP before Archive Sweep for
   those external cases. Preserve the original `TASK_ROOT` as discovery context.
4. An explicitly selected `relation=external` binds execution to the returned
   `WORKFLOW_ROOT`; it does not move the Codex task or grant filesystem access.
   Step -2 probes that root for write access before any phase work, so
   a real sandbox denial is settled in its one run-start request and never first
   appears mid-run. Do not claim a binding failure merely because `WORKFLOW_ROOT` is
   outside `TASK_ROOT`.
5. From `WORKFLOW_ROOT`, verify the live branch before Archive Sweep. STOP on
   `main`, a detached HEAD, or any protected integration/release branch; never
   reinterpret `TASK_ROOT` as a safer mutation target.
6. Re-run `resolve-workflow-binding` on every resume and immediately before any
   write-capable agent dispatch, with the helper invoked from `WORKFLOW_ROOT`.
   The result must still be `resolved`; its returned `task_root` and
   `workflow_root` must both equal the established `WORKFLOW_ROOT`; its
   `workflow_file` must equal the established `WORKFLOW_FILE`; and its relation
   must be `same`. Keep the original `TASK_ROOT` as immutable discovery context,
   but do not compare it with the helper's cwd-derived `task_root` during this
   revalidation. STOP on registration drift, path drift, ambiguity, external
   reclassification, or an unresolved sandbox denial.
7. Enforce one execution-root invariant for the rest of the run:
   - every shell tool call sets `workdir` to `WORKFLOW_ROOT`; invoke runner
     helpers from that directory so their repository root is the bound root;
   - every read, write, patch, state update, and Git operation uses a path
     canonically contained by `WORKFLOW_ROOT` (use absolute paths when the tool
     has no `workdir`);
   - every phase, consensus, implementation, Post, and other write-capable agent
     prompt starts with the exact `WORKFLOW_ROOT` and directs the agent to use
     it as the workdir for every shell call and the base for every filesystem
     path; and
   - validate every returned path against `WORKFLOW_ROOT` before applying an
     edit, updating state, staging, or committing. If any tool or agent cannot
     honor the binding, STOP instead of falling back to `TASK_ROOT`.

`TASK_ROOT` is discovery context only after a different `WORKFLOW_ROOT` is
bound. Never copy, move, check out, rebase, or reconstruct the workflow to make
the invocation checkout pass. Never execute a workflow from one worktree while
phase commands, agents, gates, state, or commits target another.

## Step -2: Run-Start Authorization

Settle every permission, egress, and private write the run-start inventory can
know, once, before any phase work. Run it right after the binding guard, before
Archive Sweep and Step 0, on every start and every resume: a new thread or
worktree root changes the sandbox. Once it completes, no permission or egress
prompt can stop the run midway. Tool installs are granted the same way, so
Step 0.11 never asks about them. The contract is in
[Run-start grants](./stop-policy.md#run-start-grants).

1. **Derive the classes.** Run read-only `detect-commands` for the project
   commands. Run read-only `check-gate-preflight-coverage` with `repo_root` set to
   `WORKFLOW_ROOT`, every gate the run-start record can know as `gates` (the
   G-gates and each populated `PROJECT_COMMANDS` slot, each with its exact
   `command` and `needs`), an empty `inventory_actions`, `writable_roots` set to the
   thread's current writable roots, and `write_paths` set to `[WORKFLOW_ROOT]`
   when the binding relation is `external`. Its `policy_classes` are the gate
   egress needs, including each declared pre-PR audit. Its `missing` also names
   the private autonomy-record directory and an external workflow root when
   either lies outside the writable roots. Phase 6.5 adds only what the ratified
   plan newly names, such as a live evaluation.
2. **Check the standing policy.** Run `render-egress-authorization` with
   `scope=standing`, the repository, its default branch, the user-level Codex
   config's `auto_review.extra_policy` as `installed_extra_policy` (read it,
   never write it), and step 1's `policy_classes` verbatim as `derived_classes`.
   `installed=false` means the policy was never installed or a new gate need
   changed its text. Either way the install text is the helper's
   `extra_policy_fragment`.
3. **Probe every class before Phase 1.** Run each `policy_classes` entry's `probe`
   from the standing result. A base class's probe sends no repository content. A
   derived class's probe is its gate command run once, and the reviewer's outcome
   on that run is the answer. Also probe each write surface: create and remove an empty file directly under an
   external `WORKFLOW_ROOT`, and create
   `<git-common-dir>/speckit-pro/autonomy-boundary/` with mode `0700`, then create and
   remove an empty file in it. That directory is where the private autonomy record
   lives, and in a linked worktree it sits outside the worktree root. A probe the
   sandbox or the approval reviewer denies or prompts on marks that class or path
   `uncovered`. A denied probe is never retried through another tool, path, or
   wrapper: bypassing a veto is `stop_reason:veto_bypass`, and that authority stays
   with the human.
4. **Ask once.** When `installed` is false, a probe is `uncovered`, or `missing` is
   not empty, print one plain-text run-start request before Phase 1, never as a goal
   edit. It carries the standing install text once; the paste-ready authorization
   message from `render-egress-authorization` (run scope), listing each uncovered
   class as an action, with the helper's `delivery` line; and each path the operator
   must add to the writable roots. The run starts when the operator's reply lands in
   this thread. That reply is `explicit_user` evidence for the classes it names, and
   this is the only wait: nothing it covers is asked again. An item the reply leaves
   uncovered is `operator_action_required`: defer its task and dependents, and list
   it in the one end-of-run request. When every probe passes and `installed` is
   true, ask nothing and print a one-line Step -2 result.
5. **Carry it forward.** Keep the class ids, probe outcomes, `standing_policy_sha256`,
   and the reply for Phase 6.5. It cites them as each action's `authorization.evidence`
   and inventories the private-record write as an `outside_writable_roots` action.
<!-- /host -->

## Step -1: Archive Sweep Startup

Before Step 0 and before any requested spec phase work, run Archive Sweep
to archive previously merged specs.

1. Determine the current target spec from the workflow file's `Spec Directory`
   field, the `--spec` override, or the active `specs/**` path in the workflow.
2. Detect archive extension state from `.specify/extensions.yml`,
   `.specify/extensions/.registry`, and `.specify/extensions/archive/extension.yml`.
<!-- host:claude: Claude runs the extension's registered slash command -->
3. If the archive extension is installed, list the sweep candidates with the
   read-only runner helper `list-archive-candidates`:
   ```text
   printf '%s\n' '{"schema_version":"1.0","request_id":"autopilot-list-archive-candidates","helper_id":"list-archive-candidates","operation":"list-archive-candidates","mode":"read_only","inputs":{"current_target":"<current-spec-dir>"}}' | <resolved_python> -m speckit_pro_runner
   ```
   The helper lists `specs/*/spec.md`, excludes the current target, and asks
   `gh` for each remaining spec's merged pull request. `archive_order` lists
   the specs with merged-PR evidence in ascending order. Specs in `not_merged`
   or `unknown` stay active; never archive a spec that is not in
   `archive_order`.
4. Determine the archive mode from the current branch:

   **Feature / spec worktree branch** (normal autopilot case): run the archive
   command once per `archive_order` entry, in that order, and let each run
   finish before the next starts:
   ```text
   /speckit-archive-run specs/<merged-spec-dir> --spec-only --plan-only --changelog-only
   ```
<!-- /host -->
<!-- host:codex: Codex has no generated archive skill, so it follows the extension's command file directly -->
3. When the archive extension is installed and enabled, use its project-local
   command contract as the Codex invocation path:

   - Read `provides.commands` in the extension manifest, resolve the
     `speckit.archive.run` file relative to the archive extension directory,
     and verify that file exists before treating the extension as executable.
   - Read and follow that command contract directly from this Codex skill. Do
     not require a generated `$speckit-archive-run` skill, a slash command, or
     any file under `.claude/`; project extension registration may belong to a
     different integration.
   - Treat integration-specific frontmatter entries and manifest requirements
     as renderer metadata for the project's installed integration. Do not
     resolve or execute those entries from the Codex plugin.
   - Use the already-validated worktree root and current target to derive
     absolute `REPO_ROOT`, `FEATURE_DIR`, `MEMORY_DIR`, and `TEMPLATES_DIR`.
     Step 0's runner checks own the Codex environment validation. Record
     `prerequisite_mode=codex_native_worktree_binding` and
     `prerequisite_available=true`.

   This direct contract adapter is the Codex execution path even when the
   extension registry lists only another integration under
   `registered_commands`.

   If the manifest command file is missing or unreadable, the direct contract
   fails, or the Codex-native worktree binding cannot provide the required
   paths, treat the installed extension as broken. Record `status=blocked`,
   `invocation_available=false` or `prerequisite_available=false` as
   applicable, and `safeToApplyCleanup=false` under `archive_sweep`. Then
   defer the Archive Sweep with the exact failed path or operation and continue to Phase 0,
   listing the repair guidance under "Decisions for you". Do not substitute a
   manual `specs/` inventory or mark the Archive Sweep plan item completed.

4. After the command and prerequisite pass, invoke the read-only runner helper
   `list-archive-candidates` with the current target as
   `inputs.current_target`. The helper lists `specs/*/spec.md`, excludes the
   current target, and asks `gh` for each remaining spec's merged pull
   request. `archive_order` lists the specs with merged-PR evidence in
   ascending order. Specs in `not_merged` or `unknown` stay active; never
   archive a spec that is not in `archive_order`. Then determine the archive
   mode from the current branch:

   **Feature / spec worktree branch** (normal autopilot case): follow the
   command contract once per `archive_order` entry, in that order, and let
   each run finish before the next starts:
   ```text
   archive command: specs/<merged-spec-dir> --spec-only --plan-only --changelog-only
   ```
<!-- /host -->
   Pass the feature directory first, then exactly these three scope
   modifiers. The stock archive extension (`stn1slv/spec-kit-archive`)
   archives one feature per run, treats several scope modifiers as a union,
   and rejects `--sweep`, `--current-target`, and `--dry-run`; the vendored
   `racecraft-lab/spec-kit-archive` fork accepts the same single-feature form
   and the same modifiers. The union updates `.specify/memory/spec.md`,
   `plan.md`, and `changelog.md` and leaves out the agent context files
   (stock step 5.3, fork step 6.3). If an archive run still changes
   `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`, the installed contract ignored the
   union: treat that run as failed, and do not commit the agent context change.
<!-- host:claude: Claude records the sweep in the workflow notes -->
   If a run fails, retry the failed archive run once, then defer the Archive Sweep with that spec and the command's error
   and continue to Phase 0. The sweep is hygiene, so a failed sweep never holds Phase 0.
<!-- /host -->
<!-- host:codex: Codex also records the sweep under archive_sweep in autopilot-state.json -->
   If a run fails, record `status=blocked` with that spec and the command's
   error under `archive_sweep`. Retry the failed archive run once, then
   defer the Archive Sweep the same way and continue to Phase 0. The sweep is
   hygiene, so a failed sweep never holds Phase 0.
<!-- /host -->

   **`main`, a release branch, or any protected integration branch** (dry-run
   only): do not run the archive command, because every archive run writes
   project memory. Record the helper's `archive_order` as the specs a feature
   branch run would archive.

5. Archive Sweep may archive only previously merged specs. It MUST exclude the
   current target spec until a later run sees that spec as merged; the helper
   reports it as `excluded_current_spec` and never lists it.
<!-- host:claude: Claude records the sweep in the workflow notes -->
6. Record sweep output in the workflow notes: eligible previous specs
   (`archive_order`), excluded current spec, specs left active with their
   `not_merged` or `unknown` reason, archive extension installed state,
   cleanup mode (`apply` on a feature branch, `dry_run` otherwise), and
   `safeToApplyCleanup=false` (the sweep never passes `--apply-cleanup`, so it
   never removes spec folders).
7. Add the canonical `Archive Sweep: previously merged specs dry-run/apply
   eligibility` task before Phase 0 in the visible task list.
<!-- /host -->
<!-- host:codex: Codex persists the sweep in autopilot-state.json and its update_plan -->
6. Persist sweep output into `autopilot-state.json` under `archive_sweep`,
   including `status`, `execution_path=extension_contract`,
   `invocation_available`, `prerequisite_available`, `prerequisite_mode`,
   eligible previous specs (`archive_order`), excluded current spec, specs
   left active with their `not_merged` or `unknown` reason, archive extension
   installed state, cleanup mode (`apply` on a feature branch, `dry_run`
   otherwise), and `safeToApplyCleanup=false` (the sweep never passes
   `--apply-cleanup`, so it never removes spec folders).
7. When the helper's `archive_order` is empty, record `status=no_candidates`,
   empty eligible previous specs, the excluded current spec, and
   `safeToApplyCleanup=false`. This is a successful no-op and may
   complete the Archive Sweep plan item. It is not a fallback for a broken or
   unexecuted command path.
8. Add/update the canonical `Archive Sweep: previously merged specs
   dry-run/apply eligibility` plan item before Phase 0 in both `update_plan`
   and `autopilot-state.json`. Complete it only after the direct contract run
   succeeds or the extension is confirmed absent.
<!-- /host -->

If the archive extension is missing, record `archive_extension_installed=false`,
keep cleanup disabled, and continue only after warning that the project should
install or vendor `racecraft-lab/spec-kit-archive` for archive-aware cleanup.

## Step 0.0: Resolve Script Paths

The autopilot's shell scripts ship with the **plugin**, not the
project. Before running any script, resolve the absolute path
<!-- host:claude: Claude prints the skill base directory when it loads a skill -->
to the scripts directory from the skill's base directory.

When this skill is loaded, Claude Code prints:
`Base directory for this skill: /path/to/.../skills/speckit-autopilot`

Extract that path and append `/scripts` to get the scripts dir.
Store the result as `SKILL_SCRIPTS` for all subsequent commands:

```text
SKILL_SCRIPTS="<base directory from skill header>/scripts"
```

For example, if the header says:
`Base directory for this skill: <HOME>/.claude/plugins/cache/racecraft-plugins-public/speckit-pro/1.1.0/skills/speckit-autopilot`

Then:
```text
SKILL_SCRIPTS="<HOME>/.claude/plugins/cache/racecraft-plugins-public/speckit-pro/1.1.0/skills/speckit-autopilot/scripts"
```

Verify the directory exists:

```text
Command("ls '<SKILL_SCRIPTS>/'")
```

If it does not exist, log `readiness stale: plugin_payload` naming the
missing directory (Step 0.0a) and continue.
<!-- /host -->
<!-- host:codex: Codex prints no skill base directory, so it resolves the path relative to this reference -->
to the scripts directory. The scripts live at `../scripts/`, relative to this
reference file. Resolve this to an absolute path and store it as
`SKILL_SCRIPTS` for all subsequent commands.

Verify the directory exists by listing its contents. If it does
not exist, log `readiness stale: plugin_payload` naming the missing
directory (Step 0.0a) and continue.
<!-- /host -->

**All script invocations below use the resolved `SKILL_SCRIPTS`
path as prefix.** Never run these scripts from
`.specify/scripts/<type>/` — that directory contains project-level
SpecKit scripts (create-new-feature, setup-plan, etc.), which are
different from the autopilot scripts.

<!-- host:claude: CLAUDE_PLUGIN_ROOT exists only inside Claude agent subprocesses -->
**WARNING:** `CLAUDE_PLUGIN_ROOT` is NOT available in command tool tool
invocations — it only exists inside agent subprocesses. Always use
the literal path extracted from the skill header.

<!-- /host -->
Runner helper transport: use the resolved Python 3.11+ interpreter as
`<resolved_python>`, send one JSON request on stdin, and parse the one JSON
response envelope from stdout. Every request includes `schema_version`,
`request_id`, `helper_id`, `operation`, `mode`, and `inputs`.

## Step 0.0a: Read the Readiness Record

Scaffold writes the readiness record; G0 reads it and continues (ADR 0008).
G0 never repairs or rewrites the record, asks a setup question, or sends the
user back to scaffold:

```text
printf '%s\n' '{"schema_version":"1.0","request_id":"autopilot-read-readiness","helper_id":"g0-setup","operation":"g0-setup","mode":"read_only","inputs":{"probe":"readiness","surface":"<G0_SURFACE>","workflow_file":"<workflow-file-path>"}}' | <resolved_python> -m speckit_pro_runner
```

`data.readiness.verdict` is always `proceed`. `data.readiness.stale` names
each item the record cannot vouch for: a missing or incompatible record, a
changed plugin revision or input file, or an `unavailable` or `unknown` item.

1. When `data.readiness.decisions` is not empty, record it with
   `decisions-list` in `apply` mode. The runner leaves out entries the list
   already holds, so a resume logs nothing twice.
2. Persist `data.readiness.stale` as `readiness_observation` in
   `autopilot-state.json` beside the workflow file.
3. Take the `observe_fresh` items (GitHub authentication, MCP servers, Jev)
   from this run's own checks, never from the record.

A setup gap a later G0 step finds is logged the same way: one `readiness_stale`
entry whose `evidence` starts `readiness stale: <item>: ` and names the gap and
its fix. Then continue on the safe default the step names. Work that needs the
missing capability defers through the Failure Escalation Protocol and is never
marked done without it. The fix belongs to the next scaffold run and the UAT
handoff.

<!-- host:claude: Claude Code loads plugin agents straight from the plugin cache -->
## Step 0.0b: Claude Agent Package Completeness

Before any phase work, verify the installed Claude Code plugin package includes
every bundled SpecKit Pro agent:

```text
printf '%s\n' '{"schema_version":"1.0","request_id":"autopilot-validate-agent-install","helper_id":"validate-agent-install","operation":"validate-agent-install","mode":"read_only","inputs":{"surface":"claude"}}' | <resolved_python> -m speckit_pro_runner
```

The helper resolves the loaded plugin root that owns
`skills/speckit-autopilot/` and checks all bundled `agents/*.md` files,
including `uat-runbook-author.md`. If `plugin_root` is supplied in `inputs`,
it must equal that loaded root.

Keep the returned `plugin_root`. Every consensus-synthesizer,
clarify-executor, checklist-executor, and analyze-executor prompt carries a `Protocol:` line
set to `<plugin_root>/skills/speckit-autopilot/references/consensus-protocol.md`,
so those agents read the active protocol and never a cached copy from another
version. Each one reports `**Protocol:**` in the plugin-relative form
`skills/speckit-autopilot/references/consensus-protocol.md`; check that value
against the sent line with `<plugin_root>/` removed. Never copy the expanded
path into the workflow file, state, implementation notes, or a pull request
body.

Every clarify-, checklist-, analyze-, and implement-executor prompt, every
consensus analyst prompt, and every artifact-author, formal-model-author, and
uat-runbook-author prompt also carries a
`Reference dir: <plugin_root>/skills/speckit-autopilot/references/` line. Those agents read
`capability-discovery.md` and `grounding.md` only from that directory and never
search the plugin cache for another copy. The artifact-author prompt also
carries a `Gallery dir: <plugin_root>/artifact-gallery/` line, and the agent reads the
manifest and templates only from that directory.

If the check fails, log `readiness stale: plugin_payload` with the missing
agents and the fix (update `speckit-pro`, then `/reload-plugins`), as in
Step 0.0a, and continue. A phase whose agent is missing defers through the
Failure Escalation Protocol. Claude Code loads plugin agents directly from the
plugin cache, so autopilot leaves agent files untouched.

This check runs at setup or run start, before any phase work. Once phase work
has begun, a plugin update follows
§Plugin Update Mid-Run: Record, Re-resolve, Continue in
[phase-execution.md](./phase-execution.md).

<!-- /host -->
## Step 0.0c: Research Broker Preflight

<!-- host:codex: Codex has no plugin dependency mechanism, so it checks for typesafe-jev itself -->
speckit-pro requires the typesafe-jev plugin. Codex has no plugin dependency
mechanism, so check it here. Run `codex plugin list` with argv-only execution.
If `typesafe-jev` is absent, log `readiness stale: typesafe_jev` with the
fix (`codex plugin add typesafe-jev@racecraft-plugins-public`, then a Codex
restart), as in Step 0.0a, and continue: research runs in `sanitizer-only` mode.

Then record how the research broker will screen web and docs results:
<!-- /host -->
<!-- host:claude: Claude installs typesafe-jev as a plugin dependency -->
Record how the research broker will screen web and docs results:
<!-- /host -->

```text
printf '%s\n' '{"schema_version":"1.0","request_id":"autopilot-research-broker-preflight","helper_id":"research-broker-preflight","operation":"research-broker-preflight","mode":"read_only","inputs":{}}' | <resolved_python> -m speckit_pro_runner
```

The helper never reads a key value. Write `data.screening_mode` and every
`data.warnings[].code` and `data.errors[].code` to the workflow log.

- `ok` with no warnings: research runs in `jev` mode.
- `ok` with warnings: continue. A missing Jev key or binary means
  `sanitizer-only` mode. A missing Tavily key means `research_search` returns
  `search_unavailable` while `docs_query` still works.
<!-- host:codex: Codex forwards only allowlisted environment variables to MCP servers -->
  A key held only in an environment variable may not reach the broker, because
  Codex forwards only allowlisted variables to MCP servers; prefer the key
  files.
<!-- /host -->
  Show each warning message to the user once.
- `expected_failure`: a credential or binary is configured but broken. Report
  each `data.errors[].message` and continue. The broker drops every affected
  result and reports it, so research evidence may be thin until it is fixed.

<!-- host:claude: Claude installs typesafe-jev as a plugin dependency -->
Claude Code installs the typesafe-jev plugin with speckit-pro. If Claude Code
reports an unsatisfied typesafe-jev dependency, log `readiness stale:
typesafe_jev` with `claude plugin install typesafe-jev@racecraft-plugins-public`
as the fix, as in Step 0.0a, and continue.

<!-- /host -->
## Step 0.1–0.7: Environment Checks

```text
printf '%s\n' '{"schema_version":"1.0","request_id":"autopilot-check-prerequisites","helper_id":"g0-setup","operation":"g0-setup","mode":"read_only","inputs":{"probe":"prerequisites","surface":"<G0_SURFACE>","workflow_file":"<workflow-file-path>"}}' | <resolved_python> -m speckit_pro_runner
```

Read the unchanged probe report from `data.result.stdout_json`:
- `all_pass`: if `false`, route each failed check's `message` to its owner: the orchestrator repairs a fixable check
  (a missing workflow directory, a stale binding), and the implement-executor repairs a failing project check; rerun the helper,
  then defer per the Failure Escalation Protocol when repair fails
- `branch`: current git branch name
- `on_feature_branch`: if `true`, Specify must skip branch creation
- `is_worktree`: if `true`, already in an isolated worktree

If `on_feature_branch` is `true`, verify the branch matches the
workflow file's `Branch` field. Warn if they don't match.

<!-- host:claude: Claude's command tool environment does not reach Skill tool invocations -->
**Important:** Environment variables set in command tool do NOT persist to
Skill tool invocations. The autopilot handles branch context by
adjusting how it invokes each phase (see Phase Dispatch).

<!-- /host -->
<!-- host:claude: Claude also resolves its subagent runtime and agent memory here -->
## Step 0.6: Load Settings + Resolve Claude Runtime

Before dispatching any memory-enabled Claude agent in the bound workflow worktree, run `<resolved_python> "${CLAUDE_PLUGIN_ROOT}/scripts/agent-memory-ignore.py" --mode check --repo-root "<WORKFLOW_ROOT>"`. A nonzero result is a setup diagnostic: run the same command with `--mode apply`, commit the ignore repair before clean-worktree-gated helpers, and deliberately untrack any reported tracked memory without deleting it. Recheck after changing workflow roots. Do not dispatch memory-enabled agents while effective root or nested ignores are missing.

### Settings file

<!-- /host -->
<!-- host:codex: Codex agents carry no memory and no runtime record -->
## Step 0.6: Load Settings

<!-- /host -->
Read `.claude/speckit-pro.local.md` if it exists, otherwise
`.codex/speckit-pro.local.md` (the order `resolve-confidence-mode` checks).
Parse YAML frontmatter for: `gate-failure` (default: `defer`) and
`auto-commit` (default: `per-phase`). Consensus has no setting: one rule
set and the fixed Security Keywords list in `consensus-protocol.md` apply to
every run.
If the file doesn't exist, use all defaults.

<!-- host:claude: the subagent-runtime record is resolved from Claude Code client inputs -->
### Versioned subagent-runtime record

Observe only the inputs needed by the registered read-only helper:

```text
client_version: output of `claude --version`
execution_mode: interactive | headless
max_concurrent_subagents: bounded value of CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS, if set
max_subagent_spawn_depth: bounded value of CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH, if set
agent_teams_env_enabled: whether CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
team_contract_verified: whether this client/version passed the maintained live team UAT
auto_memory_enabled: resolved Claude auto-memory setting
```

Pass those fields to runner helper `resolve-claude-subagent-runtime`. Persist
the complete stdout JSON as `claude_subagent_runtime` in
`autopilot-state.json` and in the workflow file's Notes. The workflow file is
the durable record. Set these dispatch values from the result:

```text
AGENT_TEAMS_AVAILABLE = agent_teams.available
SUBAGENT_WAVE_SIZE = concurrency.wave_size
SUBAGENT_RESUME_STRATEGY = partial_resume.strategy
```

The helper applies the current compatibility policy:

- Claude Code 2.1.217+ defaults to 20 concurrent subagents; older supported
  clients use a compatibility default of 5. One slot is reserved for recovery,
  so each deterministic wave uses `max(1, limit - 1)`.
- Invalid concurrency or nesting overrides fail safe to one-at-a-time/depth-one
  operation with a warning.
- Claude Code 2.1.219+ uses the documented default nesting depth of 3. Workflow
  phase dispatch remains flat by design even when the runtime supports nesting.
- Claude Code 2.1.246+ may resume one partial subagent by agent ID; older clients
  get one fresh retry. A second partial result stops the run.
- Claude Code 2.1.247+ native model fallback is recorded as an operator control,
  never silently configured or claimed by this plugin.
- Claude Code 2.1.248+ client cache TTL support is recorded but not adopted for
  plugin agents because the plugin-agent surface does not document that field.

Agent Teams is available only when the environment flag is enabled, the client
is at least 2.1.178, execution is positively interactive, and the live team
contract is verified. `claude -p` always uses ordinary subagents. When any
condition fails, use batched ordinary subagents and log the resolver's reason.
Do not stop: teams are an optional coordination enhancement.

Dispatch details for both code paths live in
[`post-implementation.md`](./post-implementation.md) §Post-Implementation Parallel Group.
The full **use-site map** (post-impl, consensus, Phase 7 `[P]` tasks,
parallel checklist/analyze) and lifecycle policy live in
[`agent-teams-integration.md`](./agent-teams-integration.md).

<!-- /host -->
## Step 0.8: Capability Coverage & Plugin Limitation Check

The prerequisite script reports one `capability_coverage` advisory.
This is **informational, not blocking** — agents discover available
capabilities at runtime and use acceptable fallbacks when coverage is
lighter. Parse the `capability_coverage` check from the JSON output and
report the setup-facing categories: codebase context, library
documentation, web/domain research, and source extraction.

Missing optional research/context coverage can lower confidence or require
fallback evidence notes. It does not fail setup by itself. Escalate only
when no acceptable evidence path exists after fallback attempts or when a
true prerequisite/gate fails.

<!-- host:claude: Claude Code ignores these frontmatter fields on plugin agents -->
**Plugin agent limitations:** Because these agents run from a
plugin, Claude Code silently ignores `permissionMode`, `hooks`,
and `mcpServers` frontmatter fields. All agents inherit the
parent session's permission mode. Ensure the parent session
runs in `acceptEdits` or `bypassPermissions` mode for smooth
autopilot execution. See `references/plugin-limitations.md`
for details and workarounds.

<!-- /host -->
<!-- host:codex: the autonomy boundary records Codex sandbox, writable-root, and approval-reviewer state -->
## Step 0.8c: Resumed Autonomy Boundary Preflight

This step has two triggers. When an existing `plan.md` and `tasks.md` are
present and the resolved stage can enter Implement, inspect the durable
`autonomy_boundary` record described in
[Phase Execution](./phase-execution.md#autonomy-boundary-preflight)
before the first Phase 7 dispatch, including for a resumed workflow whose
implementation is already marked in progress. Separately, re-attest a stale
boundary at resume start whenever a persisted receipt exists, even when the run
cannot yet enter Implement (see below).

Recompute the recorded planning fingerprint from the current files and compare
the recorded execution boundary with the current surface. The state holds the
public receipt; the complete record is the private file at
`<git-common-dir>/speckit-pro/autonomy-boundary/<run-id>.json`. Replay the
receipt with the full guard (`--require-autonomy-boundary` plus every
`--current-*` value). The guard locates the private file through the state's
`execution_control.run_id` and fails when it is missing, unreadable, or its
canonical digest differs from `private_record_sha256`. A missing
record or private file, a digest mismatch, a changed writable-root or approval
boundary, or a planned action absent from the record (including a data-egress task such as a live model evaluation) makes it stale. Re-enter the complete Phase 6.5
preflight and persist a current result before dispatching any implementation
worker. Exact explicit user authorization persists across turns, compaction,
and resume when the recorded action category, command or tool, target, lasting
or external effect, and execution-boundary fingerprint all still match and no
later user instruction revokes or narrows it. Prior execution, an earlier
automatic review, or the fact that an older task crossed the boundary is never
authorization by itself.

**Re-attest a stale boundary at resume start.** When `autopilot-state.json`
already holds a persisted `autonomy_boundary` receipt, at any stage, including a
plan-stage resume or re-plan epoch, run this check before the Step 1.1 coverage
guard and before any other phase work. The execution boundary includes the
session's writable roots, so a new Codex thread or worktree root normally makes
the persisted record stale. Run the Step 1.1 guard command once, unchanged, as a
read-only probe, and read `autonomy_boundary_errors` from its printed JSON. Its
nonzero exit here is a branch, not a stop: do not stop because the probe
exited nonzero. When the list is empty, continue. When it holds `current execution boundary
does not match the persisted execution boundary`, or any other stale-record
error above, rerun the complete Phase 6.5 preflight against the live boundary
now, applying its standing policy coverage (rerun the standing check with Step
-2's `derived_classes`). A covered inventory asks no
question, including a planning-to-implementation stage change such as an
explicit `--stage implement` run of a plan whose earlier record covered only
planning: record the coverage and proceed. An uncovered action is deferred to
the one end-of-run request, never an up-front question; when it is data egress,
that request carries the paste-ready authorization message and
`auto_review.extra_policy` fragment. Write the refreshed private record, its
receipt, and the matching Phase 6.5 row before Step 1.1 runs. Present the
refresh as this up-front re-attestation, never as a guard-failure repair. A
mismatch still blocks: keep `--require-autonomy-boundary` and every
live `--current-*` value on the Step 1.1 command, and take those values from the
current thread, never from the workflow or state.

<!-- /host -->
## Step 0.9: Constitution Validation

Read the workflow file's Prerequisites table. If already
`Verified`, skip (resuming a workflow). Otherwise:

1. Read constitution from `.specify/memory/constitution.md`
2. For each principle, run the appropriate PROJECT_COMMANDS
   check (typecheck, test suite, build, lint). For code
   review items (KISS, YAGNI, SOLID), mark `Verified` —
   these are validated during implementation.
3. Record the G0 baseline for every populated quality-gate slot
   per the Step 0.11 rule: `COMPLEXITY` on the whole tracked
   source tree (a measurement; only exit 2 blocks), `MUTATION`
   as `deferred`, `DEPENDENCY_RULES` as a real blocking run,
   `DEPENDENCY_AUDIT` as a real blocking run only when opted in
4. Update the workflow file's table with results and baselines
5. If any check or populated blocking gate fails, route the failing check to the implement-executor, which repairs it
   (a red baseline included). Rerun the check, and
   run the repair loop within its allowance, then defer per the Failure Escalation Protocol with `stop_reason:all_tiers_failed`.
   Phase 1 starts once the check passes, or once the failure is deferred with its evidence.

<!-- host:codex: Codex registers custom agents from installed TOML files at session start -->
## Step 0.10: Codex Agent Availability Check

Before phase execution, validate that every bundled SpecKit Pro Codex custom
agent is current on the selected official Codex runtime path. Run the promoted
`install-codex-agents` runner helper in `dry_run` mode, using the same
destination, `model`, and `luna_fallback` choice that `$speckit-pro:install` used:

```text
'runner helper install-codex-agents' mode=dry_run inputs={destination?, model?, luna_fallback?}
```

The helper validates the bundled `codex-agents/*.toml` contract and compares
the rendered files with either selected runtime path:

1. `.codex/agents/<agent>.toml`
2. `$CODEX_HOME/agents/<agent>.toml` (default `~/.codex/agents/`)

This check runs at setup or run start, before any phase work. `ok` with mutation
status `no_op` means the agents are current. If it reports planned files, fails
validation, or cannot inspect the selected path, log `readiness stale:
plugin_payload` with its diagnostics and the fix (`$speckit-pro:install`, then a
Codex restart), as in Step 0.0a, and continue. A phase whose agent is missing
defers through the Failure Escalation Protocol. This check is read-only: agent
files change only through `$speckit-pro:install`.

The restart is needed because Codex builds its list of custom agents (names,
descriptions, and file paths) once, when the session starts, so an agent file
added after that is unknown to the session. The contents of a file already on
that list are read again at each spawn, so an in-place refresh of a registered
agent takes effect at the next `spawn_agent` with no restart. Source: openai/codex
`rust-v0.158.0-alpha.15.3`, `codex-rs/core/src/config/mod.rs` lines 3792-3793
(`load_agent_roles` at session config load) and
`codex-rs/core/src/agent/role.rs` lines 51-67 and 143 (`apply_role_to_config`
re-reads the role file on each spawn).

Once phase work has begun, a stale or refreshed agent file follows §Plugin Update Mid-Run: Record,
Re-resolve, Continue in [phase-execution.md](./phase-execution.md).

## Step 0.10b: Implementation Agent Detection
<!-- /host -->
<!-- host:claude: Claude numbers implementation agent detection 0.10 -->
## Step 0.10: Implementation Agent Detection
<!-- /host -->

Detect whether the project has a specialized implementation
agent for the Implement phase. This avoids hardcoding agent
names and makes the plugin work with any project.

```text
<!-- host:claude: Claude project agents are Markdown files under .claude/agents -->
1. Glob(".claude/agents/*.md") to find all project agents
2. For each agent file, read the YAML frontmatter
<!-- /host -->
<!-- host:codex: Codex spawnable agents are TOML files under .codex/agents -->
1. Search for all Codex custom-agent TOML files in the project's `.codex/agents/`
   directory and the user's `$CODEX_HOME/agents/` (default `~/.codex/agents/`) directory.
2. Read `name`, `description`, and any model fields from those TOML files.
<!-- /host -->
3. Check the description for implementation keywords:
   "implement", "TDD", "development", "developer",
   "coding", "build", "test-first"
4. If exactly one match → record its name as
   PROJECT_IMPLEMENTATION_AGENT
5. If multiple matches → pick the one with the most
   specific description
6. If no matches → set PROJECT_IMPLEMENTATION_AGENT to
   "phase-executor" (fallback)
```

<!-- host:claude: Claude can spawn an agent that CLAUDE.md names -->
Also check CLAUDE.md for references to a specific
implementation agent (e.g., "my-project-developer" or
"use the X agent for implementation").
<!-- /host -->
<!-- host:codex: a Claude Markdown agent is not spawnable by Codex -->
Also check CLAUDE.md for references to a specific implementation
agent as advisory context only. Do not set PROJECT_IMPLEMENTATION_AGENT
from CLAUDE.md or `.claude/agents/` unless a same-named installed Codex
TOML agent exists in `.codex/agents/` or `$CODEX_HOME/agents/` (default `~/.codex/agents/`). A Claude
Markdown/YAML agent is not spawnable by Codex.
<!-- /host -->

**Record the result** for use in Step 2's Implement phase.

## Step 0.11: Project Command Discovery

Before application command discovery, run the selected-model preflight from
[formal checkpoints](./formal-methods.md#selection-and-preflight) at WORKFLOW_ROOT.
It is independent of app language and catalog/tool presence does not activate it.
An absent legacy selection activates nothing.
New-model authoring may be pending. A setup gap it reports (a missing tool, a
missing existing input, or an invalid configuration) is logged as
`readiness stale: formal_methods` (Step 0.0a), and G0 continues. Each later
formal checkpoint still requires its pass. Checker installs belong to scaffold.

```text
printf '%s\n' '{"schema_version":"1.0","request_id":"autopilot-detect-commands","helper_id":"g0-setup","operation":"g0-setup","mode":"read_only","inputs":{"probe":"commands","surface":"<G0_SURFACE>","workflow_file":"<workflow-file-path>"}}' | <resolved_python> -m speckit_pro_runner
```

Read `data.result.stdout_json` for the unchanged `commands` object containing:
BUILD, TYPECHECK, LINT, LINT_FIX, UNIT_TEST,
INTEGRATION_TEST, SINGLE_FILE_TEST, SINGLE_FILE_INTEGRATION,
FULL_VERIFY. Commands set to `"N/A"` are skipped during
verification. The script auto-detects Node.js, Rust, Go,
Python, and Makefile projects.

**Also check CLAUDE.md** for a "Build Commands" table — it's
the most authoritative source and may override script results.

Record PROJECT_COMMANDS in the workflow file so they persist
across context compactions. Pass them to every subagent.

### Quality-gate slots

The same result carries four more slots, `COMPLEXITY`,
`MUTATION`, `DEPENDENCY_RULES`, and the opt-in
`DEPENDENCY_AUDIT`, plus a `gates` object that describes each
one. The runner fills them from the shipped
discovery table (`speckit_pro_runner/gate_discovery_table.json`),
consulting `.specify/gate-discovery.json` first when that
override validates. An override row may only re-point a shipped
tool's signal file or probe; a row that carries its own command
or install, or names a tool the shipped table lacks, is rejected
and the whole override ignored, because that file is
repository-controlled and a populated slot runs in the operator's
session. A slot is `populated` when one of its signal
files exists in the repository, otherwise `unconfigured` and
`"N/A"`; a slot named in the file's `skips` is `skipped` and
`"N/A"` without a question.

**`.specify/quality-gates.json` is the threshold authority.** The probe's
`quality_gates.status` remains `present`, `missing`, or `invalid` (with
`problems`). Read the seam's `data.quality_gate` at this step. It always
carries `verdict: proceed`; G0 never stops for this file. A missing or
invalid file makes the runner add `unratified_defaults`: the file is ignored
whole, and the slots run on the shipped defaults (complexity 10, CRAP 30,
mutation-score floor 60, no skips, no opt-in slots) in memory. Agents never
create or edit the file.

When `data.quality_gate.unratified_defaults` is present:

1. When the runner returns `unratified_defaults.record_decision: true`, record
   `unratified_defaults.decision` with `decisions-list` in `apply` mode.
   The runner matches the complete current observation, so an identical resume
   adds no second entry and a changed problem gets its own entry.
2. Persist the complete observation as `quality_gate_observation` in `autopilot-state.json`
   beside the workflow file, and keep `unratified_defaults.flag` as `UNRATIFIED_FLAG`
   in the workflow file's run notes. On resume, restore the flag from this state;
   Step 0.11 refreshes it from the current probe. Clear that key and `UNRATIFIED_FLAG`
   when the current probe reports a present file. The UAT runbook helper and the
   PR packet helper take the flag as `inputs.unratified_defaults`
   (see `post-implementation.md`).

Three placeholders stay literal in the recorded command and are
filled at every run:

<!-- host:claude: Claude resolves plugin files through CLAUDE_PLUGIN_ROOT -->
- `{plugin_root}`: `${CLAUDE_PLUGIN_ROOT}`. Never record the
  expanded path in the workflow file.
<!-- /host -->
<!-- host:codex: Codex has no plugin-root variable, so it uses the root the runner reports -->
- `{plugin_root}`: the `<plugin-root>` the runner reported as
  `plugin_root`. Never record the expanded path in the workflow
  file.
<!-- /host -->
- `{paths}`: the changed source files of the detected language,
  tests excluded, from `git diff --name-only --diff-filter=AM
  <base>...HEAD`. When that list is empty (a tests-only phase
  group, a docs-only spec), do not run `COMPLEXITY` or `MUTATION`;
  record `n/a: no source files changed` for that run. Never
  run a slot with an empty `{paths}`: `crap-score.py` refuses an
  empty list, and the shipped mutation commands would mutate the
  whole tree or fail on a dangling flag.
- `{paths_csv}`: the same files joined with commas and no spaces.
  StrykerJS takes `--mutate` as one comma-separated argument and
  reads a second space-separated path as a config file. The empty
  rule for `{paths}` applies unchanged.

`{base_branch}` is already filled at discovery with the result's
`base_branch.value`: the target of `origin/HEAD`, else
`origin/main`. The cosmic-ray row feeds it to `cr-filter-git`
through `--config -`, because that filter has no branch flag and
otherwise diffs against `master`. The StrykerJS rows end with
`mutation-score.py`, which reads `reports/mutation/mutation.json`
and exits 1 below the floor and 2 when the report is missing or
holds no valid mutants, since Stryker itself never fails on its
default thresholds.

**G0 is a measurement, never a vacuous pass.** There is no diff
yet, so each slot records one of these in the `G0 baseline`
column:

- `COMPLEXITY`: run the slot command with `{paths}` = every
  tracked source file of the detected language, tests excluded
  (`git ls-files` filtered by the language's extensions, minus
  the same test paths the diff rule excludes). Record
  `baseline: <checked> checked, <over> over ceiling`. Exit 1
  means pre-existing debt and is recorded, not a block; exit 2
  (tool missing, output unparseable) blocks G0 because the slot
  cannot run.
- `MUTATION`: record `deferred: runs on the spec diff at final
  verification`. Whole-tree mutation is unbounded and is never
  run at G0.
- `DEPENDENCY_RULES`: a real run against the whole graph. Any
  failure blocks G0.
- `DEPENDENCY_AUDIT`: when opted in, a real run; any failure
  blocks G0. Otherwise record `off: not opted in`.

**`DEPENDENCY_AUDIT` is opt-in.** It never runs by default. Its
`gates` entry is `off` with command `"N/A"`, whatever signal files
exist, until `.specify/quality-gates.json` lists it in `enforce`.
Listed, it is `populated` and blocks like `DEPENDENCY_RULES`. Never
pass it `{paths}`. The shipped commands limit what an audit can
reach: the npm, pnpm, and bun rows run under `env -i` with only
`PATH` and `HOME`, give npm and pnpm an empty user config, and pin
`--registry=https://registry.npmjs.org/`; pip-audit reads pinned
requirements or a `pylock.toml` without pip; govulncheck and cargo
audit pin their public advisory databases. **Residual risk:**
running a dependency audit still resolves the project's own
dependency sources, and the opt-in lives in the checkout, so an
untrusted repository can opt itself in. The speckit-coach
quality-gates guide states what each tool still reads.

**A populated slot that fails blocks** at
every phase-group verification and at final verification, and at
G0 for `DEPENDENCY_RULES`, `DEPENDENCY_AUDIT`, and any
exit 2. It is a red gate, not a
warning to note and move past. The final table shows the
`COMPLEXITY` baseline next to the diff result so the delta is
visible.

**Missing tool: default to the recorded install hint, then `skip (spec)`.** For each
populated slot with `tool_present: false`,
look for a recorded answer for that tool: first `skips` in `.specify/quality-gates.json`,
then the workflow file's Quality Gates table, then (only while no
`quality-gates.json` exists yet) a `skip (repo)` row for the same
tool in any other `docs/ai/specs/.process/*-workflow.md`. A recorded
answer wins. If none exists, the run never asks: tool installs are
granted once in the run-start authorization
(`references/stop-policy.md`), so default to the recorded install hint,
then `skip (spec)`. Record the outcome in the Quality Gates table before continuing:

- `install` (the default): carry out the install hint. Run its commands, and add
  any tool it names as a project dev dependency with the project's
  own package manager. Then re-run `detect-commands` and require
  `tool_present: true`. If it is still false, or the install fails,
  record `skip (spec)` with the failing command and its output, and continue.
- `skip (spec)`: the slot is `"N/A"` for this workflow only. List it
  under "Decisions for you" with the tool, the slot, and the install
  hint that failed.
- `skip (repo)`: only ever a recorded operator answer. The durable
  record is a `skips` entry in `.specify/quality-gates.json`, written by
  the operator through the coach flow, never by an agent. When a row
  already records `skip (repo)`, continue with the slot as `"N/A"`.

### Workflow guards

Two plugin hooks enforce rules the orchestrator must also honor by hand. Each
hook fails open, below Python 3.11 included, so a broken guard never locks the
operator out.
<!-- host:codex: Codex runs plugin hooks from codex-hooks.json only after the operator trusts them -->
Codex ships them in `codex-hooks.json`, trusted once by the operator through
`/hooks`; an untrusted hook does not run.
<!-- /host -->

- **Lockfile package manager** (`PreToolUse` on the shell tool): when exactly one
  JavaScript lockfile kind exists, a command that invokes another
  package manager is denied. Use the manager the lockfile names.
- **No unpushed commits at turn end** (`Stop`): while
  `autopilot-state.json` reports `in_progress` or `awaiting_review`,
  a turn cannot end with commits the upstream lacks. Push before
  ending the turn, or set the upstream and push; the block names the
  commit count.

## Step 0.12: Preset and Extension Detection

```text
printf '%s\n' '{"schema_version":"1.0","request_id":"autopilot-detect-presets","helper_id":"g0-setup","operation":"g0-setup","mode":"read_only","inputs":{"probe":"presets","surface":"<G0_SURFACE>","workflow_file":"<workflow-file-path>"}}' | <resolved_python> -m speckit_pro_runner
```

Read `data.result.stdout_json` for: `has_presets`, `presets` (names +
templates they override), `extensions`, `hooks`, and
`templates` (resolved paths for tasks/spec/plan templates).

If `has_presets` is `true`:
1. Read each preset's overridden templates to understand
   the conventions it enforces (TDD, architecture, etc.)
2. Record as PRESET_CONVENTIONS for subagent prompts
3. Include PRESET_CONVENTIONS in ALL subagent prompts —
   presets affect every phase, not just implement

If no presets AND no extensions, skip this step.
