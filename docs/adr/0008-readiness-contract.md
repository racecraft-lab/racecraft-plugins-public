# Scaffold owns readiness preparation; autopilot reads evidence without a setup stop

Status: accepted

Implementation status: planning decision; this ticket changes no plugin runtime behavior.

Scaffold writes a local, ignored `.specify/readiness/<host>.json` for each project/worktree and host (`claude` or `codex`). Autopilot reads it and records current observations only in run state and the decisions list. A missing, malformed or stale record never prompts the user or stops G0. This replaces repeated setup interruptions with explicit evidence and visible gaps, while preserving live authorization and integrity checks.

Decision: [Readiness record: fields, moved stop sites, scaffold per host](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1021), part of [Wayfinder: speckit-pro health program](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1006).

## Record contract

The record names its schema version, project/worktree binding, host and host version, execution mode, loaded plugin revision and observation time. Each item records its status, evidence source, observation time and fingerprints of the inputs on which the observation depends. The supported statuses are `verified`, `unavailable`, `unknown` and `not_applicable`. Missing or unobservable evidence is `unknown`; `not_applicable` is only for a capability the selected workflow does not require. There is no blanket "ready" verdict that can authorize a run.

| Item | Evidence to retain |
| --- | --- |
| Plugin and agents | Effective installation scope and loaded payload revision; required agent inventory and shipped/installed hashes; the selected installation/routing inputs and whether the repaired payload is loaded in the session. |
| Project integration | Specify availability/version; project initialization, constitution and host integration assets; setup-contract/template checks; detected and confirmed project commands; required extension versions and supported helper input contracts. |
| Services | GitHub authentication result; required MCP servers/tools, startup/auth observations and bounded timeouts; required broker availability. Configuration alone does not prove a live connection or callable tool. |
| Permission preparation | Observed approval/sandbox/auto-review posture, managed constraints, required hook definitions/hashes and enabled/trusted observations; a reference and digest for the applicable egress policy. These are facts, never consent. |
| Local capability health | Bounded checks for required temporary storage, required loopback use and file modes on the record and sensitive temporary files the workflow creates. No recursive cleanup, repository-wide mode changes or security-control changes. |
| Selected verification | Formal tools and verification Docker only when selected, including versions, setup results and the selected per-model bounds. Current model inputs and verification receipts remain live checks. |
| Quality gates | The current confirmed file and its digest, or unratified shipped defaults with the reason: missing file or the first validation problem. No saved proposal, decline flag or credentials. |
| Reviewability | Advisory setup report with its roadmap/SPEC/slice evidence references and relevant fingerprints. Size never becomes a readiness stop; unresolved evidence remains visibly unknown. |

Host task-list tools are excluded (ADR 0001). The record stores no credentials or raw permission tokens; public decision evidence uses repository-relative placeholders and omits local identities. Changes to the exact schema and helper request examples must be covered by executable contract checks when this decision is implemented.

## What scaffold does

Scaffold owns the preparation checks, including those it already performs. It observes the effective host scope, offers safe setup fixes within the user's authorization, performs approved preparation, checks the result and writes the snapshot. It may finish after a declined or unsuccessful fix, recording each remaining item as unavailable or unknown with the evidence and required action. An installation success is not proof that the current session loaded the new payload.

| Shared preparation | Claude Code | Codex |
| --- | --- | --- |
| Check Specify/project assets, templates and helper contracts; detect project commands and extensions; check GitHub/required services; measure/propose quality gates; report reviewability; set up selected formal/Docker tools; inspect required local capability health. | Check the effective project/worktree plugin scope and bundled agent package; run the bounded permission probe during scaffold; observe required MCP authentication/approval, hook configuration and effective permission setup. A plugin cannot supply user permission rules. | Compare installed agents with the shipped templates using the selected installation/routing inputs; observe effective approval/sandbox constraints, auto-review, required MCP consent/startup and exact-hash hook trust. Disk configuration does not prove launch overrides or loaded-thread permissions. |

Refresh/reload or restart belongs to preparation. Use the host's supported mechanism and verify the loaded revision, rather than hard-coding one reload behavior for every version. Missing observability stays unknown. Scaffold does not silently broaden permissions, grant egress consent or disable a control to make a check pass.

The exact current helper inputs must be preserved: `reviewability-gate` uses `mode_name="setup"`, `target` and `spec_id`; `check-prerequisites` uses `workflow_file`; `check-roadmap-freshness` uses `roadmap_path`; `detect-commands` and `research-broker-preflight` use empty inputs. Codex agent verification uses `mode="dry_run"` and replays the selected installation inputs: static installation uses `destination`, `model` and `luna_fallback`; route-aware installation uses `destination`, `route_policy_manifest` and the optional `strict_model_override`. Do not infer a new `routing_mode` key or verify a routed installation using unrelated static defaults.

## Freshness and G0

Freshness is per item. A relevant changed payload, agent, hook, host version, project/worktree binding, managed policy, selected tool, routing manifest, project command source or configuration fingerprint invalidates the observation that depends on it. An unrelated commit or elapsed time alone does not invalidate every item. The observation timestamp is context, not a fixed expiry rule.

G0 reads and validates the record without repairing or rewriting it. A missing, unreadable or incompatible record supplies no verified evidence. It compares relevant fingerprints and reruns cheap, bounded, read-only checks; authentication, connectivity and current session boundaries require fresh observations because they can change without a file change. A saved status cannot substitute for those observations. An unavailable comparison or probe produces unknown, never an inferred pass.

G0 appends `readiness stale: <item>` with the reason, current observation and available evidence to the decisions list and run state, then continues on the applicable safe defaults. It neither asks a setup question nor returns the user to scaffold during the run. A current valid quality-gates file remains authoritative even when its cached readiness item is stale; a missing or invalid file uses the shipped in-memory defaults from ADR 0007, never a cached measured proposal. The whole-file threshold cost after a decline remains explicit in the PR body and UAT runbook.

If a required capability is unavailable, the affected check/work uses the existing retry ladder and blocked-for-UAT handling; independent work continues. The run cannot mark a check passed or an artifact produced when the required evidence or capability is absent. Failed preparation and unresolved readiness observations remain visible in the review artifacts and UAT handoff.

## Stop sites and boundaries

The following current setup interruptions move into scaffold preparation and readiness reporting. Their ordinary failures no longer cause an autopilot setup question or standalone G0 stop:

| Current source site | Target treatment |
| --- | --- |
| Autopilot `references/prerequisites.md:398-414`, missing plugin scripts | Verify loaded payload during scaffold; record a gap if repair cannot complete. An unusable payload does not fabricate phase completion. |
| `references/prerequisites.md:435-486`, Claude package / Codex Jev presence | Scaffold verifies the effective package and required services; run-start observations remain bounded and noninteractive. |
| `references/prerequisites.md:521-530`, project prerequisites | Move setup detection/repair to scaffold; retain fresh workflow/identity checks. |
| `references/prerequisites.md:46-77,176-229`, permission preparation | Move setup probes and configuration questions to scaffold. Action-specific authorization and security interrupts remain live. |
| `references/prerequisites.md:723-757` and `SKILL.md:243-247,717-725`, Codex agent refresh | Scaffold compares/repairs selected installed agents and verifies the loaded revision; stale run evidence is logged. |
| `references/prerequisites.md:807-812`, selected formal setup | Scaffold prepares selected tools/bounds; later missing tools and failed verification use ADR 0005 and the retry ladder. |
| `references/prerequisites.md:849-870`, quality-gates G0 block | Delete the missing/invalid-file stop and use ADR 0007's defaults and disclosure. |
| Autopilot `SKILL.md:969-975`, host task-list/progress materialization | Delete the host task-list requirement under ADR 0001; the runner's progress block remains. |

These references describe the audited source, not a completed migration. Scaffold already checks agent completeness, Specify, roadmap freshness/reviewability, worktree placement, bootstrap and preset resolution (`speckit-pro/skills/speckit-scaffold-spec/SKILL.md:199-238,255-303,316-394,774-784`). The assertion that scaffold checks none of readiness is incorrect; implementation extends the existing checks rather than duplicating them.

Readiness evidence never replaces current workflow/worktree/branch binding, invocation validity, ledger integrity, formal input/evidence binding, action-specific security consent or user approval of the plan. Decisions about their failure handling remain with [Stop-policy enforcement: harm halts, fail-closed deferral, and the decisions list](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1015), [Security interrupt: definition, runner receipt, question-tool hook per host](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1022) and [Plan approval record](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1014). This decision grants no release, installation or implementation approval.

## Evidence and consequences

- Current helper contracts: `speckit-pro/speckit_pro_runner/helpers/read_only.py:1437-1587,2212-2225`; Codex install inputs: `speckit-pro/codex-skills/install/SKILL.md:80-87,147-165` and `speckit-pro/speckit_pro_runner/helpers/install.py:1887-1942,1998-2020`. Existing checks do not establish this durable cache; host integration/version gaps must not be called verified.
- Host limitations and preparation flow: [Research: what pauses an unattended Codex run](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1017#issuecomment-5943092264), [Research: what pauses an unattended Claude Code run, and can a hook deny the question tools](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1018#issuecomment-5943147158), and [Research: plugin refresh fast path on both hosts](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1020#issuecomment-5943147761).
- Current official [Codex hook documentation](https://learn.chatgpt.com/docs/hooks#review-and-trust-hooks) says changed/untrusted hooks are skipped pending exact-hash trust and startup warns about review. Hook discovery alone does not establish execution. The older research gist's "silent" wording is version-specific, not a readiness guarantee.
- Current [Claude MCP documentation](https://code.claude.com/docs/en/mcp) exposes connection/authentication and project approval states; [plugin CLI documentation](https://code.claude.com/docs/en/plugins/cli-reference) exposes effective scope/version observations. Neither is a substitute for action-specific authorization.

The rejected alternative was a version-controlled per-SPEC certificate invalidated by every tree change: it conflates shared planning inputs with host-local state and goes stale on unrelated edits. Refusing to finish scaffold until every setup check passes was also rejected; explicit gaps let planning reach its review handoff while retaining honest failed-check evidence. This planning session did not probe live readiness, install anything or test question-tool hooks. Implementation must prove these outcomes on both hosts with missing/stale/unknown cases and the canary.
