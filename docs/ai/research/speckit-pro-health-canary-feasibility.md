# Research: can the canary run headless on both hosts

Ticket: #1019. Map: #1006. Probed with Claude Code 2.1.287 and codex-cli 0.156.0 (`--help` only, no billed runs).

## Answer

| Host | Feasible | Short reason |
| --- | --- | --- |
| Claude Code (`claude -p`) | With caveats | Plugins, skills, agents, resume and a machine-readable transcript all work headless. Scaffold cannot run as shipped: grill-me and scaffold abort in non-interactive runs by design, and `AskUserQuestion` is removed or denied in `-p`. |
| Codex (`codex exec`) | With caveats | `exec`, `--json`, `exec resume`, TOML agents and plugin skills work non-interactively. Same scaffold blocker (`request_user_input` has no answerer). Plugin install from a marketplace and from a fresh cache is the least documented part. |

Both hosts share one blocker, and it is in our skills, not in the hosts. Scaffold forbids a non-interactive run, with no skip path. The canary must therefore feed the interview through an explicit, tested "pre-answered interview" entry that is separate from the human path. That is a skill change that needs its own decision (it touches promise item 1, "scaffold is the only skill with heavy user interaction", and the guard text that exists to prevent autonomous interviews).

Recommended shape: a canary run does not run the interview. It starts the pipeline at "scaffold, with a committed answers file" (a fixture Design Concept plus roadmap entry), and a separate interactive-only check covers the interview itself. If the owner will not add a pre-answered entry, the fallback below applies.

## What the canary needs, per capability

Status key: C = confirmed in a primary source, P = confirmed by a local probe, R = confirmed in this repo, U = could not confirm.

### 1. Claude Code recipe

- Non-interactive run. `claude -p "<prompt>"`; exit code 0 on success, non-zero on failure; missing auth is printed as the result on stdout (C: headless docs).
- Plugin from a directory, no install. `--plugin-dir <path>` loads for the session only, id `<name>@inline` (C: plugin loading doc; P: help). This is what the repo's headless runner uses today (R).
- Plugin from a marketplace, from a fresh cache. Three documented routes (C):
  1. `claude plugin marketplace add <owner/repo or ./dir>` then `claude plugin install <name>@<marketplace>` in the shell before the run.
  2. `extraKnownMarketplaces` plus `enabledPlugins` in settings (managed settings apply in `-p`; repo `.claude/settings.json` marketplaces apply only in a trusted folder). Installs run in the background, so set `CLAUDE_CODE_SYNC_PLUGIN_INSTALL=1` to wait before the first turn.
  3. A seed directory: build with `CLAUDE_CODE_PLUGIN_CACHE_DIR=<dir>`, run with `CLAUDE_CODE_PLUGIN_SEED_DIR=<dir>`, and enable plugins through `enabledPlugins`.
  For a "fresh cache" test, point `CLAUDE_CODE_PLUGIN_CACHE_DIR` at an empty temp directory per run. Layout is `cache/<marketplace>/<plugin>/<version>/` (C).
- Prove the plugin loaded. In `stream-json` output the `system/init` event lists `plugins` and `plugin_errors`; a canary should fail when `plugin_errors` is non-empty or the plugin is absent (C).
- Invoke a plugin skill. "User-invoked skills and custom commands work. Include `/skill-name` in the prompt string and Claude Code expands it" (C). The repo already runs `/speckit-pro:speckit-autopilot workflow.md` this way (R).
- Custom agents. Plugin subagents are available; plugin agents ignore `hooks`, `mcpServers` and `permissionMode` frontmatter (C: subagents doc). `--agents <json-or-file>` also works in `-p`. `--bare` skips installed plugins, agents and hooks, so do not use `--bare` unless every piece is passed by flag (C). Subagents cannot use `AskUserQuestion` (C).
- Interview answers. With `--permission-prompts none`, "Claude Code removes the tools that need an answer from a person, such as `AskUserQuestion`"; with `--permission-mode dontAsk`, `AskUserQuestion` is denied even if allowed (C). So answers cannot arrive through the question tool. Options, best first:
  1. A committed answers file the skill reads (needs the skill change above). Deterministic, host-neutral, and the same file works on Codex.
  2. A prompt prefix carrying the answers. Works with no tooling change but the skill's guard text still tells the model to abort, so it needs the same skill change.
  3. Agent SDK with a `canUseTool` / user-input callback (C: headless doc points to the SDK user-input page; U: not read in full). It lets a script answer `AskUserQuestion` for real, which would test the unmodified interview. Claude only, so it breaks host parity.
  4. `--input-format stream-json` for streamed user turns (P: help; C: described as "realtime streaming input"). Usable to send follow-up user messages, but it does not answer a tool call. U: whether it can answer `AskUserQuestion`.
- Session resume across stages. `--resume <session-id>`, `--continue`, `--resume <path to .jsonl>`; capture the id from `--output-format json` or the stream `result` event (C). Do not pass `--no-session-persistence` for staged runs: the repo's headless runner does pass it, so a staged canary needs a different invocation (R, P).
- Transcript and counting question-tool calls. `--output-format stream-json --verbose`. Subagent messages carry `parent_tool_use_id`; add `--forward-subagent-text` for subagent text (C). Denied calls appear as `permission_denied` system messages and in `permission_denials` on the final `result` (C). Counting `tool_use` blocks with `name == "AskUserQuestion"` gives the question count; it should be 0 in the pre-answered path.
- Timeouts and spend. `--max-budget-usd` (P, C). No wall-clock flag for the whole run: wrap with an external timeout. SIGTERM exits 143 and records no result for the turn in progress; SIGINT ends the turn cleanly (C). Background subagents keep `-p` open until done, with a 10 minute idle ceiling (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`) (C).
- Auth. Local: subscription login. CI: one of `ANTHROPIC_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_AUTH_TOKEN` (R: the repo adapter requires exactly one of these; C: bare mode reads `ANTHROPIC_API_KEY` only). Plugins synced from claude.ai do not load under token-based auth (C), which is fine because the canary should use marketplace or `--plugin-dir` plugins.
- No task-list tools variant. Restrict with `--tools` / `--disallowedTools` (P: help lists both) to remove `TaskCreate`, `TaskUpdate`, `TaskList`. The autopilot skill already names these tools as required in places (R: skill text), so this variant is expected to fail today and is the point of the variant.
- umask 077 variant. Run the launcher as `umask 077; claude -p ...`. Nothing host-specific; the repo already has 0o077 permission checks in runner code (R). U: whether the Claude plugin cache install itself tolerates a restrictive umask (not probed).

### 2. Codex recipe

- Non-interactive run. `codex exec [PROMPT]`, `-` reads the prompt from stdin; piped stdin plus a prompt arg is appended as a `<stdin>` block (C: docs; P: help).
- Auth. CI: `CODEX_API_KEY=<key> codex exec ...`; or seed `~/.codex/auth.json` on a trusted runner; `codex login --with-api-key` reads a key on stdin (C: docs; P: help). `--ignore-user-config` still uses `CODEX_HOME` for auth (P). Local: ChatGPT login.
- Sandbox and approvals. Default is read-only; use `--sandbox workspace-write` for scaffold and implement. `--dangerously-bypass-approvals-and-sandbox` exists for externally sandboxed runners (C, P). `--approve-for-me` routes approvals to automatic review (P).
- Plugins from a marketplace. `codex plugin marketplace add|list|upgrade|remove`, `codex plugin add|list|remove` exist (P: help). This repo ships a local marketplace file whose entry points at a built Codex plugin directory (R). U: exact non-interactive install flags, whether `exec` loads an installed plugin's skills without a trust prompt, and where the cache lives. A fresh-cache test should set `CODEX_HOME` to an empty temp directory (the repo's adapter already isolates `CODEX_HOME`, R), then `codex plugin marketplace add` and `codex plugin add` before `codex exec`. This sequence is unverified end to end.
- Invoke a plugin skill. Codex names skills with a dollar sign (`$speckit-autopilot`) (R: skill text). U: that `codex exec` expands `$skill` mentions from an installed plugin; the repo's Codex adapter stages skills itself rather than relying on installed-plugin discovery (R).
- Custom agents. TOML files in `.codex/agents/` or `~/.codex/agents/` with `name`, `description`, `developer_instructions`. In `exec`, "subagents can run when applicable project or skill instructions request delegation"; they inherit the parent sandbox and approval mode; an action needing fresh approval fails and the error returns to the parent (C: subagents doc). The repo registers agents per run with `--config agents.<name>.config_file=<path>` and enables `--enable multi_agent` for nested cases (R). Concurrency: `agents.max_concurrent_threads_per_session` (C).
- Interview answers. Same blocker. `request_user_input` has no answerer under `exec`; the Codex guard text says to stop in `codex exec` (R). Answers file or prompt prefix are the only host-neutral routes. U: whether any `exec` flag can answer `request_user_input`.
- Resume across stages. `codex exec resume <SESSION_ID|thread name>` or `--last`, with a new prompt (or `-` for stdin) (C, P). The session must be recorded: do not pass `--ephemeral` (the repo's trigger runs do; its functional runs record sessions, R). Take the session id from the `thread.started` event (C: event name; U: field name `thread_id` not verified in this session).
- Transcript. `codex exec --json` emits JSONL: `thread.started`, `turn.started`, `turn.completed`, `turn.failed`, and items `agent_message`, `command_execution`, `reasoning`, `file_changes`, `mcp_tool_calls`, `web_search`, `plan_updates` (C: docs). U: how a `request_user_input` call or a subagent spawn appears in `--json`; the repo reads native rollout files as a supplement for this reason (R: `native_eval_codex_rollouts.py`, "native_rollout_supplement_required"). Count question calls from rollouts, not from `--json` alone, until probed.
- Final output. `-o <file>` writes the last message; `--output-schema <file>` forces a JSON final answer (C, P). Useful for the receipt.
- Timeouts. No per-run flag found in `exec --help` (P). Use an external timeout and per-case `timeout_seconds` as the repo does (R).
- No task-list tools variant. Codex's progress tool is `update_plan`; the repo enables it with `--config tools.update_plan.enabled=true` (R). Disable it by omitting that config (U: whether the default is on in 0.156.0).
- umask 077 variant. Same shell wrapper. U: untested on Codex.

### 3. Variants

| Variant | Claude | Codex | Note |
| --- | --- | --- | --- |
| umask 077 | shell `umask 077` before launch | same | Mostly tests our runner file modes and plugin install. |
| No task-list tools | `--tools` / `--disallowedTools` | omit `update_plan` | Expected to fail today, which is the finding the variant exists to produce. |
| Split recommendation | fixture plan over the PR budget | same | Host-neutral, driven by the fixture. Autopilot already has a ratified-split path (R). |

## Fallback if a host cannot run the full canary

1. Split the canary into a deterministic layer and a live layer. The deterministic layer replays committed transcripts through the existing scrub and reduce tools and asserts the receipt schema, question-call count 0, and stage order. It runs on both hosts with no billing.
2. Run the live layer per stage rather than end to end: scaffold-with-answers, then plan, then implement, each a separate `exec`/`-p` call chained by resume. If resume fails on a host, restart each stage from the committed artifacts of the previous one (the stage runner already accepts `--stage plan|implement|full` and `--from-phase`, R).
3. If one host cannot take pre-answered input at all, keep the live canary on the other host, run the deterministic layer on both, and record the gap as a named release exception in the receipt. This conflicts with promise item 5, so it needs an explicit owner decision, not a silent downgrade.
4. If the owner rejects any pre-answered scaffold entry, the interview stays interactive-only and the canary starts at the plan stage from a committed scaffold output. The scaffold step is then covered by the interactive verification already described for layer 7 (R).

## Existing repo seams to reuse

All paths are under `tests/speckit-pro/` unless noted. There is no `layer7-integration/` directory yet; the layer 7 directory is `layer7-parity/`. The receipt directory named in the ticket is new.

- `layer3-functional/run-headless-evals.py`: builds the exact `claude -p --output-format stream-json --verbose --no-session-persistence --restricted --permission-mode dontAsk --permission-prompts none --plugin-dir ...` and `codex exec --json --ephemeral --strict-config --ignore-user-config ...` commands. Closest thing to the canary launcher. It disables session persistence, so staged resume needs a variant.
- `lib/native_eval_claude_adapter.py`: runs Claude cases through `claude plugin eval <plugin> --case <id> --runs 1 --no-publish --trust-plugin --scaffold --keep-temp --json <file>`; `--scaffold` runs the case's fixture setup script. `--trust-plugin` is the documented CI answer for the trust prompt. Auth comes from exactly one automation credential variable.
- `lib/native_eval_codex_adapter.py`, `lib/codex_isolation.py`, `lib/native_eval_codex_rollouts.py`: Codex run assembly, per-agent `agents.<name>.config_file` registration, `CODEX_HOME` isolation, rollout capture.
- `evals/` (`catalog.json`, `README.md`, `audit/`): the canonical case catalog (`native-eval-catalog/v1`), per-case `timeout_seconds`, `resource_class`, `response_json_field` grading with per-host expectations, and the executor `run-native-evals.py`. A canary case can be a catalog case.
- `layer7-parity/`: legacy parity fixtures. The parity README says headless `claude -p` always uses ordinary subagents and cannot prove genuine agent teams, and it names layer 7 as the home of host-parity gates. `run-parity-fixtures.py` shows a minimal `claude -p --max-budget-usd` autopilot launch.
- `layer6-integration/scrub-transcript.py`, `reduce-transcript-fixture.py`, `run-e2e-fixtures.py`: transcript scrub and reduce for the deterministic replay layer.
- `lib/native_eval_fixture_setup.py`, `lib/native_eval_git_scaffold.py`, `lib/native_eval_upstream_scaffold.py`: fixture-repo staging for the fixture SPEC repo.
- `lib/native_eval_pool.py`, `lib/native_eval_store.py`: concurrency limits and result store; receipts can reuse the store's strict JSON helpers (`lib/native_eval_strict_json.py`).
- `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and `speckit-pro/skills/grill-me/SKILL.md`: the two files that must change for a pre-answered entry. Both carry host-conditional blocks (`host:claude`, `host:codex`) and rendered mirrors under `speckit-pro/codex-skills/`; a change needs the existing parity tests (`unit/test-host-parity-generator.py` and the layer 1 run).
- `claude plugin eval`: exists in 2.1.287 (P: `claude plugin --help` lists it; its own `--help` was not read in this session, so flag semantics beyond those the repo adapter uses are U).

## Open items for the canary ticket

1. Decide the pre-answered scaffold entry (answers file vs prompt prefix vs SDK harness), as an ADR.
2. Probe Codex `exec` end to end once: install from the local marketplace into an empty `CODEX_HOME`, invoke a `$skill`, spawn a TOML agent, resume, and record how `request_user_input` and subagent spawns appear in `--json`.
3. Probe Claude once: empty `CLAUDE_CODE_PLUGIN_CACHE_DIR`, `claude plugin marketplace add` plus `install`, `-p` with `--output-format stream-json --verbose` and persistence on, then `--resume`.
4. Confirm how plan approval is requested today. Autopilot text names no question tool for plan approval (R: grep of the skill), and the approval record is a later ticket; the canary needs an approval input that is not a question tool.

## Sources

Primary, read this session:
- Claude Code headless / Agent SDK CLI: code.claude.com/docs/en/headless
- Claude Code plugin loading, cache layout, `--plugin-dir`: code.claude.com/docs/en/plugins/loading
- Claude Code plugin marketplace CLI: code.claude.com/docs/en/plugin-marketplaces
- Claude Code org plugin management, seed containers and CI, `CLAUDE_CODE_SYNC_PLUGIN_INSTALL`, `CLAUDE_CODE_PLUGIN_SEED_DIR`: code.claude.com/docs/en/plugins/org
- Claude Code subagents (plugin agent limits, `--agents` in `-p`, `AskUserQuestion` removal): code.claude.com/docs/en/sub-agents
- Codex non-interactive mode: learn.chatgpt.com/docs/non-interactive-mode (redirect from developers.openai.com/codex/noninteractive)
- Codex subagents and custom agents: learn.chatgpt.com/docs/agent-configuration/subagents (redirect from developers.openai.com/codex/agent-configuration/subagents)
- Local probes: `claude --help`, `claude plugin --help`, `codex exec --help`, `codex exec resume --help`, `codex plugin --help`, `codex plugin marketplace --help`, `codex login --help`
- This repo: files listed under "Existing repo seams to reuse", plus the autopilot, scaffold and grill-me skill texts.

Not read: the openai/codex source tree and the Agent SDK user-input page. Claims about Codex `--json` shapes for question calls, `$skill` expansion in `exec`, and non-interactive plugin install are therefore marked U.
