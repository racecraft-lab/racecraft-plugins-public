# Phase Driver Reference

The phase-executor agent reads this file in full at dispatch, so it holds only the driver rules and
the flat summary format. Keep it small: `test-phase-driver.py` caps its size. The rest of the phase
contract stays in [phase-execution.md](./phase-execution.md).

## Nested-mode phase driver

7. **Drive a phase in nested mode.** When the parent's prompt carries `Mode: nested`, a
   `Phase:` line and the phase brief, you are the Phase driver. The phase runs in your fresh
   context and the parent keeps only your envelope. This overrides the opening paragraph's
   limits on delegation, for the executors named below only; never dispatch `phase-executor`.
   - **Specify, Plan, Tasks** (`inner_agent` null): run the skill under rules 1 and 2 yourself.
     Plan then runs the formal-model-author and formal-check sequence of `formal-methods.md`
     before G3. Tasks then calls `publish-tasks-output` with `brief.inputs.tasks_output`, runs
     mandatory after_tasks hooks and every `brief.after_tasks_hooks.run` hook through
     `read-tasks-output` with the unchanged publisher `tasks_binding`, as the
     bound-consumer handoff in §Phase 5 of `phase-execution.md` specifies. A pathname
     consumer also requires `live_path`.
     Run each selected optional hook once; skip every `brief.after_tasks_hooks.skip`
     entry. Record each run as `optional_hook_run` and each unconfirmed skip as
     `authority_action_skipped` through `decisions-list`, with the exact extension,
     command, event and confirmation or its absence. No workflow-level approval
     replaces a runner-selected run entry. Stop on a hook or binding failure and
     return a failed or blocked envelope. Then run G5 with that same `tasks_binding`.
     Report successful optional runs and skips in envelope `counts.optional_hooks_run`
     and `counts.optional_hooks_skipped`. Leave other phases' optional hooks to the parent.
   - **Clarify, Checklist, Analyze**: request `phase-brief` again with `mode=flat` and the
     wave inputs your phase needs. Dispatch `inner_agent` (`clarify-executor`, `checklist-executor`
     or `analyze-executor`), then the consensus agents, as its
     `agent`, `slices` and `waves` say, and follow `skills/speckit-autopilot/references/phase-execution.md` and
     `skills/speckit-autopilot/references/consensus-protocol.md` for answers, edits and repair.
   Dispatch with `spawn_agent`, and wait with `wait_agent` using `brief.wait.codex.timeout_ms`.
   Run the phase's gate with `validate-gate`, repair within the shared reservation, and record
   the phase results in the workflow file.
   Finish with one `phase-envelope/v1` JSON object and nothing else, under 2,048 bytes:
   `schema_version`, `phase` (the parent's `Phase:`), `status` (`pass` only when every gate you ran passed; else `fail`
   or `blocked`), `next_action`, repo-relative `artifacts`, `gates` (the phase gate and any
   other you ran, each `pass` or `fail`), `counts` (`markers` and `task_count` as the gate
   reports them), a `blocker` of at most 240 characters, and your `usage` counters. The runner
   re-verifies the envelope from disk and a claim never passes a gate. If your turn budget is
   nearly spent, return `status` `blocked` and name what remains in `blocker`.

## Phase executor summary

```text
## Phase Result

**Files created/modified:**
- path/to/file.md (created/modified)

**Metrics:**
- Relevant phase metrics and counts

**Markers found:**
- [NEEDS CLARIFICATION]: N; [Gap]: N; [CRITICAL]: N (or "None" if clean)

**Errors:** None (or describe any errors)
```
