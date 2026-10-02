# What pauses an unattended Codex run

Ticket: #1017 (map #1006). Researched against codex-cli 0.156.0 (local `--help`) and the openai/codex source at commit b707714 (shallow clone, `main` at research time).

## Answer

A Codex run waits on a human at exactly these places: command and file-change approvals, MCP tool approval and elicitation, `request_user_input`, `request_permissions`, execpolicy `prompt` rules, auto-review denials that tell the model to ask the user, untrusted hooks (silently skipped, not waited on), and sandbox network denials (which turn into approval requests). Every one is removable by configuration, but only some in `codex exec`.

Two findings change the design:

1. **`codex exec` does not wait.** It cancels MCP elicitations and rejects command approvals, file-change approvals, `request_user_input` and dynamic tool calls with a JSON-RPC error (-32000). A hang of about 21 hours therefore points to the interactive TUI or a goal run on the app-server path, not to `codex exec`. A `codex exec` run fails or degrades instead of waiting.
2. **`approval_policy = "never"` plus a sandbox is the only fully non-waiting combination.** `approvals_reviewer = "auto_review"` removes the human but adds a denial path: the reviewer can deny, and the model is then told to get explicit user approval.

Plugin rule of thumb: make the unattended path (`codex exec`) explicit about `approval_policy`, `sandbox_mode`, network, and per-MCP approval mode, and probe all of them before the run starts.

## Table

| Pause source | Trigger | Ahead-of-time detection | Config that removes the wait | Source |
|---|---|---|---|---|
| Command and file-change approval | `approval_policy = on-request` (default) or `untrusted`; model asks, or the sandbox blocks a command | Read effective `approval_policy` from config layers, or the `approval:` line `codex exec` prints at start. `codex exec -a` and `codex exec --help` list the values | `approval_policy = "never"` (`-a never`); failures return to the model. Or `granular` with `sandbox_approval=false`, `rules=false`, `skill_approval=false`, `request_permissions=false`, `mcp_elicitations=false` (each `false` auto-rejects instead of prompting) | S1, S2, S6 |
| Auto-review (guardian) | `approvals_reviewer = "auto_review"` (or `--approve-for-me`). Reviewer denies risky actions (sandbox escalation, blocked network, destructive calls). 90 s review timeout | Read `approvals_reviewer`; `codex features list` shows `guardian_approval` stable and on. No probe predicts a denial | Remove the reviewer (`approvals_reviewer = "user"` with `approval_policy = "never"`) so nothing is reviewed. Or keep auto-review and make requests unneeded: vendor or pin installs ahead of time, widen the sandbox allowlist, avoid external egress. A denied action cannot be force-approved by config | S1, S3, S6, S7 |
| MCP tool approval | Per-server `default_tools_approval_mode` or per-tool `approval_mode` is `auto`, `prompt` or `writes` and the tool needs approval | `codex mcp list --json`; read `mcp_servers.<id>.default_tools_approval_mode` | `mcp_servers.<id>.default_tools_approval_mode = "approve"` (speckit-pro already sets this for its brokers) | S1, S4, S8 |
| MCP elicitation | An MCP server sends `elicitation/create` (form or confirm). With `approval_policy = never`, or granular `mcp_elicitations=false`, it is declined by policy. A confirm elicitation with no schema is auto-accepted when the tool is auto-approved | Read `approval_policy`; list servers with `codex mcp list --json`. No static way to know which servers elicit (UNCONFIRMED: no server capability field in config) | `approval_policy = "never"`, or granular with `mcp_elicitations=false`; `default_tools_approval_mode = "approve"` for the confirm case. In `codex exec` elicitation is auto-cancelled regardless | S2, S5 |
| MCP -32001 timeout | A tool call or startup exceeds the timeout while a consent or elicitation waits. -32001 is not defined by Codex for this; Codex's own -32001 is the app-server "overloaded" code. See details | Read `tool_timeout_sec` and `startup_timeout_sec`; run `codex mcp list` and a one-tool probe | Raise `tool_timeout_sec` and `startup_timeout_sec` per server, and remove the consent wait (rows above) so the call never blocks on a human | S4, S5, S8 |
| Sandbox network limits | `sandbox_mode = workspace-write` with `sandbox_workspace_write.network_access = false` (default); permission profile proxy with `allow_local_binding = false` blocks loopback and private destinations | Read `sandbox_mode`, `sandbox_workspace_write.network_access`, `permissions.<name>.network`; probe with `codex sandbox <os> -- <cmd>` against the target port | `sandbox_workspace_write.network_access = true`; in a permission profile set `network.allow_local_binding = true` or add explicit `localhost` or IP allow rules under `network.domains`; or `sandbox_mode = "danger-full-access"` inside an externally sandboxed environment | S1, S6, S9 |
| Hook trust | Unreviewed or modified hook: status `Untrusted` or `Modified`. The hook is not run and nothing prompts in `codex exec` | Hash compare: `hooks.state.<key>.trusted_hash` versus the current hook hash; TUI hook review lists status. UNCONFIRMED: no non-interactive CLI listing found | `codex exec --dangerously-bypass-hook-trust` (automation that already vets sources), or persist `trusted_hash` after review. Managed (system or requirements) hooks are trusted | S10, S11 |
| `request_user_input` and dynamic tools | Model calls `request_user_input` or a dynamic tool | None needed in exec | In `codex exec` the call is rejected with -32000. In the TUI, the question panel is the wait. `features` flags for the tool were not located (UNCONFIRMED) | S2 |
| Execpolicy `prompt` rules | A `.rules` file marks a command `prompt` | List `.rules` files in user and project config | `--ignore-rules` for `codex exec`, or `granular.rules=false` | S1, S2, S6 |
| Goals marked `blocked` | `features.goals` (stable, default on). The agent sets `blocked` only after the same blocking condition recurs for 3 consecutive goal turns | Read `features.goals`; `codex features list` | Fix the root cause rows above. `blocked` is the symptom of an unremoved wait, not a pause source itself | S12 |

## Details

### What speckit-pro does today

Found with ripwire on the speckit-pro package (files named by role, not path).

- The Codex launcher for brokers runs `codex exec` with `--ignore-user-config`, `--ignore-rules`, `--ephemeral`, `--strict-config`, a custom permission profile (network off, filesystem read-only), `web_search="disabled"`, and per-broker `required=true`, `enabled_tools`, `default_tools_approval_mode="approve"`. It sets no `approval_policy` and no `approvals_reviewer` on that command line. That is safe only because `--ignore-user-config` drops a user's `on-request` and `codex exec` rejects approvals rather than waiting. It would stop being safe if the launcher were pointed at the TUI.
- Per-agent `sandbox_mode` in generated Codex agent files is advisory; the parent's sandbox wins (code comment in the host-parity module).
- Codex hooks are shipped in a hooks file (`PreToolUse` guards, a `Stop` guard). The README says Codex skips them until you review and trust them. The default autopilot path therefore runs unguarded on Codex until trust is persisted. UNCONFIRMED: whether the runner tries `--dangerously-bypass-hook-trust` or writes `trusted_hash`; no hit found.
- The autopilot validator carries `execution_environment`, `sandbox_mode`, `approval_reviewer`, `writable_roots` as autonomy fields, so a record of these exists in the plugin. A readiness record can read them.

### Approval policy

Source enum `AskForApproval`: `untrusted`, `on-request` (default), `granular{...}`, `never`. `never`: "Failures are immediately returned to the model, and never escalated to the user for approval." Granular fields: `sandbox_approval`, `rules`, `skill_approval`, `request_permissions`, `mcp_elicitations`; a `false` field auto-rejects. `codex exec --help` on 0.156.0 documents only `on-request` and `never` for `-a`; `granular` is config-only.

### Exec behavior

`codex exec` handles app-server requests itself: MCP elicitation gets a `Cancel` response; command approval, file-change approval, `request_user_input`, dynamic tool calls, token refresh, attestation and external time each get an error response "not supported in exec mode". Nothing blocks. The cost: the model sees failures and may stall, retry, or report blocked. A run that fails 3 goal turns in a row on the same cause becomes `blocked`.

### Auto-review

Source: `ApprovalsReviewer` is `user` (default) or `auto_review` (alias `guardian_subagent`). The reviewer is pinned to a read-only sandbox and `approval_policy = never`. Review timeout is 90 s. A denial prepends a developer message (`MANUAL_APPROVAL_DEVELOPER_PREFIX`) so the model knows a later explicit user approval counts. Strict auto-review for MCP can decline an elicitation with the message "Do not proceed without asking the user for explicit approval." Docs: the default policy denies critical-risk actions; high-risk actions need user authorization and no deny rule. This matches the observed denials (pinned install, `npm audit`, external worker, preview observer): each is an egress or escalation request. The review prompt text and the exact deny rules were not read (UNCONFIRMED); no config key removes a specific denial.

### MCP consent and the -32001 timeout

Approval modes (`AppToolApproval`): `auto` (default), `prompt`, `writes`, `approve`. Mixed modes intersect to the stricter one. Timeouts: the docs say 10 s startup and 60 s per tool. The source at the researched commit has 30 s startup and 300 s per tool as constants. The docs and source disagree (UNCONFIRMED which applies to 0.156.0); set both explicitly.

About -32001: in the Codex source the only -32001 is the app-server overload code. MCP's own client SDKs also use -32001 for "request timed out". I found no place where Codex emits -32001 for a consent wait. So the observed error most likely came from the MCP server or its SDK timing out while Codex held the call open behind a consent prompt (UNCONFIRMED inference). The fix is the same either way: remove the consent wait (`approve`, or `approval_policy = never`) and raise `tool_timeout_sec`.

### Sandbox and loopback

Docs: `allow_local_binding = false` (default) blocks loopback and private destinations; add explicit `localhost` or IP allow rules, or set `allow_local_binding = true`. Source comment: it "permits local servers and direct host-loopback connections and skips the proxy's additional private-network destination checks. Proxy domain rules still apply." In the plain `workspace-write` mode, outbound network is off unless `sandbox_workspace_write.network_access = true`. A blocked network request becomes an approval request (docs list "blocked network requests" among what auto-review evaluates), so under `on-request` it waits and under `never` it fails.

Probe: `codex sandbox` runs a command under the Codex sandbox; running a connect test to the needed port tells you ahead of time. I did not run it (UNCONFIRMED output shape).

### Hook trust

Source (`hook_trust_status`): built-in is trusted; managed is `Managed`; others compare `trusted_hash` in `hooks.state.<key>` with the current hash: match is `Trusted`, mismatch is `Modified`, absent is `Untrusted`. Only enabled and (`Managed` or `Trusted` or bypass) handlers are registered. An untrusted hook is dropped, with no wait and no failure. That is worse than a pause: a guard hook silently does not guard. `--dangerously-bypass-hook-trust` ("Intended only for automation that already vets hook sources") appears in `codex exec --help`.

### Other waits

- TUI-only: question panel for `request_user_input`, approval dialogs, goal menu, hook review. `codex exec` replaces all with auto-reject.
- Goals: statuses `active`, `paused`, `blocked`, `usage_limited`, `budget_limited`, `complete`. `usage_limited` and `budget_limited` are set by the system and wait on the user; they are not approval waits.
- MCP OAuth login waits on a browser callback (`timed out waiting for OAuth callback` in source). Detect with `codex mcp list` auth status (UNCONFIRMED field). Remove by logging in before the run.
- Startup handshake: a required server that fails to start (`required=true`) fails the run rather than waiting.
- ChatGPT auth token refresh is unsupported in exec; a stale login ends the run (UNCONFIRMED how it surfaces). `codex doctor --json` is the ahead-of-time check for auth and config health.

### Recommended unattended profile (for the readiness record)

Primary: `codex exec --sandbox workspace-write -a never` plus `-c sandbox_workspace_write.network_access=true` when the plan needs the network, `default_tools_approval_mode="approve"` for each needed MCP server, raised tool timeouts, and hook trust persisted before the run (or the bypass flag where the sources are vetted). Docs' own CI recommendation: `--sandbox read-only --ask-for-approval never`; for write access with review, `--sandbox workspace-write --ask-for-approval on-request -c approvals_reviewer=auto_review`. The second form can still deny, so a planning run that must never stop should avoid it, or treat a denial as a security interrupt candidate.

Preflight checks a plugin can run without a model call: `codex --version`, `codex doctor --json`, `codex features list`, `codex mcp list --json`, effective config for the keys above, hook hashes, and `codex sandbox` connect tests.

## Not confirmed

- Which Codex version the 21-hour goal run used and whether it was TUI or app-server.
- The origin of the observed -32001 (see above).
- Auto-review's exact deny rules and whether any config marks a command pre-authorized.
- Docs versus source timeout defaults.
- Whether an effective-config dump command exists in 0.156.0 (none found in `codex --help`; `codex doctor` may cover it).

## Sources

- S1: `codex exec --help` and `codex --help`, codex-cli 0.156.0 (local).
- S2: openai/codex `codex-rs/protocol/src/protocol.rs` (`AskForApproval`, `GranularApprovalConfig`); `codex-rs/exec/src/lib.rs` (`handle_server_request`, `canceled_mcp_server_elicitation_response`).
- S3: openai/codex `codex-rs/protocol/src/config_types.rs` (`ApprovalsReviewer`); `codex-rs/core/src/guardian/` and `codex-rs/ext/guardian-reviewer/src/lib.rs` (`REVIEW_TIMEOUT` 90 s).
- S4: openai/codex `codex-rs/config/src/mcp_types.rs` (`AppToolApproval`); `codex-rs/codex-mcp/src/rmcp_client.rs` (timeout constants), `connection_manager/startup.rs`.
- S5: openai/codex `codex-rs/codex-mcp/src/elicitation.rs` (`elicitation_is_rejected_by_policy`, `can_auto_accept_elicitation`); `codex-rs/app-server/src/error_code.rs` (-32001 overload).
- S6: Codex configuration reference, https://learn.chatgpt.com/docs/config-file/config-reference (redirected from developers.openai.com/codex/config-reference).
- S7: Codex agent approvals and security docs, https://learn.chatgpt.com/docs/agent-approvals-security.
- S8: `codex mcp list --help`, `codex features list` (local).
- S9: openai/codex `codex-rs/config/src/permissions_toml.rs` (`allow_local_binding`, `domains`).
- S10: openai/codex `codex-rs/hooks/src/engine/discovery.rs` (`hook_trust_status`), `codex-rs/config/src/hook_config.rs` (`trusted_hash`).
- S11: `codex exec --help` (`--dangerously-bypass-hook-trust`).
- S12: openai/codex `codex-rs/ext/goal/src/spec.rs` (blocked rule), `codex-rs/protocol/src/protocol.rs` (`ThreadGoalStatus`).
- speckit-pro side: ripwire task map of the package (Codex launcher, host-parity module, Codex hooks file, README install-safety section).
