# CC ↔ Codex Skill Parity — Intentional Divergence Notes

This document explains why the Claude Code and Codex variants of
speckit-pro's skills are **not** byte-for-byte mirrors, and lists the
exact strings and structures that `validate-codex-skills.sh` pins to
the Codex variant. Anyone modifying either variant should read this
before assuming a divergence is a bug.

## Why CC and Codex variants diverge

Claude Code and Codex CLI expose different runtime primitives. A
faithful "Codex skill" cannot just be a sed-rewrite of the CC skill
because the underlying tool surfaces differ:

| Concept | Claude Code | Codex CLI |
|---------|-------------|-----------|
| Subagent dispatch | `Agent(...)` tool with `run_in_background: true` for parallel batches | `spawn_agent` + `wait_agent` separate calls |
| Slash-command invocation | `Skill("speckit-specify", args: "...")` | `$speckit-specify ...` (skill prefix syntax) |
| Plan tracking | `TaskCreate` / `TaskUpdate` (this conversation's task panel) | `update_plan` (Codex-native plan tool) + `autopilot-state.json` persistence |
| Persistent state | In-context conversation + workflow file | Workflow file + `autopilot-state.json` (Codex compacts more aggressively) |
| Agent Teams | Available (experimental, env-var-gated) | **Not available** |
| Background execution | Per-call `run_in_background: true` flag | `spawn_agent` is async by default; `wait_agent` synchronizes |
| Fast helper | N/A (Claude's main thread is fast enough) | `autopilot-fast-helper` for sub-second compression/triage work |
| Subagent installation | Plugin auto-installs into `~/.claude/plugins/cache/...` | Custom agents live in `.codex/agents/` (project) or `~/.codex/agents/` (user); require explicit `$install` step |
| Sandbox/permission model | `permissionMode` frontmatter (acceptEdits, plan, …) | `sandbox_mode` frontmatter (read-only, workspace-write) |
| Model selection | `model: opus` etc. + `/model` slash command | `model: gpt-5.5` etc. + `model_reasoning_effort` |

Trying to force byte-for-byte mirrors would either lie about the
runtime contract or break one of the two integrations.

## Body-pinned strings in `validate-codex-skills.sh`

The validator enforces that the Codex `speckit-autopilot/SKILL.md`
**body** contains these exact tokens (any change must preserve them):

1. `update_plan` — the progress contract; required for plan tracking
2. `autopilot-state.json` — durable persistence in the workflow dir
3. `spawn_agent` + `wait_agent` (both must appear) — phase dispatch primitives
4. `followup_task` + `send_message` (both must appear); `send_input` must NOT appear (obsolete)
5. `Exactly one plan item is `in_progress`` — Codex plan invariant
6. `phase family coverage is mandatory` + `Phase 7: Implement - Pending task decomposition` + `Post: Doctor Extension Check` + `Post: Retrospective` — all-phase coverage
7. `PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]` — canonical PHASES order
8. `` `--from-phase` changes only the starting index `` — `--from-phase` semantics
9. `After the Tasks phase and G5 pass` + `the placeholder no longer exists` + `each concrete Phase 7 item names task IDs` — G5 placeholder replacement
10. `all seven SDD phases are complete` + `items are missing, pending, or in progress` + `execute Step 3` — resume-into-Post guardrail
11. `agents/openai.yaml` — skill metadata sidecar path
12. `.codex/agents/` + `~/.codex/agents/` (both must appear) — installed-agent search paths
13. `$install` — escape hatch when subagents missing
14. `autopilot-fast-helper` — optional fast helper name
15. `Only the parent orchestrator may call this helper` + `latency optimization, not a dependency` — fast-helper guardrails

The validator also enforces **negative** assertions on the Codex body:
no Claude-only runtime primitives (`TaskCreate`, `TaskUpdate`, `Agent(`,
`Bash(`, `Opus-class`, `Opus 4.6`, `/model opus`, `/effort max`,
`/speckit[.:]`, `run /<command>`, `general-purpose agent`).

## Implication: cannot trim Codex SKILL.md the same way

The CC variant of `speckit-autopilot/SKILL.md` was aggressively trimmed
in WS-A (1,070 → ~500 lines) by moving most content into
`references/*.md`. WS-G subsequently applied a similar progressive-disclosure
pass to the Codex variant (1,230 → 751 lines). The Codex variant cannot be
trimmed AS aggressively as the CC variant because:

1. The 15 body-pinned strings above must remain in the **body** (the
   validator checks `$body`, not `$runtime_doc`, for 8 of them).
2. The Codex Runtime Contract section names the entire
   `spawn_agent`/`wait_agent`/`update_plan`/`autopilot-state.json`
   surface — none has a CC equivalent and the validator pins it.
3. Codex's `references/phase-execution-codex.md` and
   `post-implementation-codex.md` are pulled into `runtime_doc` by the
   validator (lines 105-112), but most pinned strings still target the
   body specifically.

**A modest Codex trim that IS in scope:** the per-item post-impl details
duplicated between the SKILL.md and `post-implementation-codex.md`
could be consolidated into the reference. Estimated cut: ~50 lines on
a 1,200-line file. Low priority.

## When adding a new Codex feature

If you need to add a string the CC validator does NOT check but Codex
DOES check, modify both:

1. `codex-skills/speckit-autopilot/SKILL.md` — add the content
2. `tests/layer1-structural/validate-codex-skills.sh` — add the
   `assert_contains "$body" "<new string>"` test
3. Update this doc to list the new pinned string

This keeps the asymmetry **intentional and visible** rather than
silent.

## When the divergence becomes obsolete

If Anthropic and Codex converge on a common runtime contract (unlikely
soon), this doc + the divergent `validate-codex-skills.sh` assertions
should be removed and the variants merged. Until then, the divergence
is the cheapest way to support both integrations honestly.

## Related references

- `tests/layer1-structural/validate-codex-skills.sh` — the validator
  that enforces these pins
- `tests/layer1-structural/validate-codex-parity.sh` — separate
  validator for shared-reference link integrity (CC ↔ Codex)
- `codex-skills/speckit-autopilot/SKILL.md` — the Codex skill body
  these pins apply to
- `codex-skills/speckit-autopilot/references/phase-execution-codex.md`
- `codex-skills/speckit-autopilot/references/post-implementation-codex.md`
