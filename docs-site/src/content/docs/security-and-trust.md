---
title: "Security & Trust"
description: "Understand what SpecKit Pro can package or invoke on Claude Code and Codex, and which claims come from platform docs, repository files, or derived operating guidance."
---

Use this route when you need to understand what SpecKit Pro can package or
invoke on Claude Code and Codex, and which claims come from platform docs,
Racecraft repository files, or derived operating guidance.

DOC-008 is user documentation. It is not a security audit, certification,
formal threat model, control attestation, penetration test, or guarantee that a
given environment is safe. Platform permissions, sandboxing, managed policy,
network access, and connected-service authentication remain controlled by
Claude Code, Codex, your local settings, and your organization.

## Evidence Types

| Evidence Type | What It Means | What It Does Not Prove |
|---|---|---|
| Official vendor behavior | A current Claude Code or OpenAI Codex documentation page describes platform behavior, command syntax, settings, sandboxing, approvals, hooks, MCP/app behavior, plugins, skills, agents, or managed policy. | It does not describe Racecraft source files unless the vendor page explicitly documents that exact file or path. |
| Repository fact | A checked-in Racecraft file or generated DOC-007 reference page describes this repository's manifests, skills, agents, hooks, scripts, tests, generated payloads, or source-vs-dist layout. | It does not create a platform guarantee and does not override local or managed policy. |
| Recommended practice | Guidance derived from official vendor behavior plus Racecraft repository facts. | It is not a security certification, audit result, or vendor guarantee. |

## Official Vendor Behavior

| Platform | Claim | Citation | Boundary Note |
|---|---|---|---|
| Claude Code | Plugins are discovered, installed, inspected, updated, and removed through Claude Code plugin and marketplace flows. | [Discover plugins](https://code.claude.com/docs/en/discover-plugins), [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [Plugins reference](https://code.claude.com/docs/en/plugins-reference) | These docs describe Claude Code behavior, not Racecraft release quality. |
| Claude Code | Plugin authors can package plugin components such as slash commands, agents, hooks, MCP servers, and settings-related assets according to Claude Code plugin docs. | [Create plugins](https://code.claude.com/docs/en/plugins), [Plugins reference](https://code.claude.com/docs/en/plugins-reference) | A packaged component is still subject to platform policy and user approval. |
| Claude Code | Settings, environment variables, permissions, sandboxing/security, hooks, subagents, and managed MCP affect what plugin-provided workflows can do. | [Settings](https://code.claude.com/docs/en/settings), [Environment variables](https://code.claude.com/docs/en/env-vars), [Permissions](https://code.claude.com/docs/en/permissions), [Sandbox environments](https://code.claude.com/docs/en/sandbox-environments), [Security](https://code.claude.com/docs/en/security), [Hooks](https://code.claude.com/docs/en/hooks), [Subagents](https://code.claude.com/docs/en/sub-agents), [Managed MCP](https://code.claude.com/docs/en/managed-mcp) | DOC-008 does not tell users to bypass local or organization-managed controls. |
| Codex | Plugins, plugin manifests, skills, subagents/custom agents, hooks, MCP/app integrations, config, CLI commands, sandboxing, approvals, and managed configuration are Codex platform surfaces. | [Plugins](https://developers.openai.com/codex/plugins), [Build plugins](https://developers.openai.com/codex/plugins/build), [Agent Skills](https://developers.openai.com/codex/skills), [Subagents](https://developers.openai.com/codex/subagents), [Hooks](https://developers.openai.com/codex/hooks), [MCP](https://developers.openai.com/codex/mcp) | These docs do not make Racecraft local paths vendor-stable unless the exact path is documented. |
| Codex | Codex configuration, environment variables, permissions, sandboxing, approval policy, managed configuration, and AGENTS.md instructions govern local behavior. | [Config basics](https://developers.openai.com/codex/config-basic), [Config reference](https://developers.openai.com/codex/config-reference), [Environment variables](https://developers.openai.com/codex/environment-variables), [Permissions](https://developers.openai.com/codex/permissions), [Sandboxing](https://developers.openai.com/codex/concepts/sandboxing), [Agent approvals & security](https://developers.openai.com/codex/agent-approvals-security), [Managed configuration](https://developers.openai.com/codex/enterprise/managed-configuration), [AGENTS.md](https://developers.openai.com/codex/guides/agents-md) | Browser docs cannot grant permissions, run plugin workflows, or change config. |
| Codex | Codex CLI JSON output is the preferred documented way to inspect plugin state when available. | [CLI reference](https://developers.openai.com/codex/cli/reference) | Hardcoded cache paths from local docs or installer output are local runtime evidence unless OpenAI documents the exact path. |

## Racecraft Repository Facts

| Surface | Repository Fact | Citation | Boundary Note |
|---|---|---|---|
| Source tree | `speckit-pro/` is the mixed authoring source tree; generated payloads under `dist/claude/` and `dist/codex/` are platform-specific output. | [Source vs dist](/racecraft-plugins-public/reference/source-vs-dist/) | Do not patch a stale install by editing generated payloads or installed caches directly. |
| Manifests | Marketplace and plugin manifests exist as checked-in source and generated payload manifests. | [Manifests](/racecraft-plugins-public/reference/manifests/) | Manifest evidence identifies file layout and metadata, not install success. |
| Skills | SpecKit Pro exposes Claude Code and Codex skill surfaces with platform-specific invocation forms. | [Skills](/racecraft-plugins-public/reference/skills/) | Skill availability still depends on platform installation and refresh state. |
| Agents | Claude Code plugin agents and Codex TOML custom-agent templates are separate surfaces. | [Agents](/racecraft-plugins-public/reference/agents/) | Codex custom-agent TOML registration is not automatic just because plugin skills are installed. |
| Hooks | Hook configuration is present in Racecraft source or generated payload files where documented by DOC-007. | [Hooks](/racecraft-plugins-public/reference/hooks/) | Hook files are configuration evidence; hook execution remains governed by platform policy. |
| Scripts and tests | Repository scripts and validation layers document how the project builds, validates, and checks generated references. | [Scripts](/racecraft-plugins-public/reference/scripts/), [Tests](/racecraft-plugins-public/reference/tests/) | DOC-008 does not add new scripts, live diagnostics, or CI enforcement. |
| Install docs | Claude Code and Codex install pages record first-install boundaries and platform-specific registration details. | [Install: Claude Code](/racecraft-plugins-public/install/claude-code/), [Install: Codex](/racecraft-plugins-public/install/codex/) | Install docs are not a formal control review. |

## Recommended Practice

| Practice | Reason | Follow-up |
|---|---|---|
| Treat source, generated payload, marketplace source, installed runtime state, and copied custom-agent files as separate surfaces. | This reduces stale-state confusion and keeps editable source separate from runtime state. | [Source vs dist](/racecraft-plugins-public/reference/source-vs-dist/) |
| Use read-only inspection before recovery. | It helps identify whether the issue is marketplace source, generated payload, installed state, policy, or custom-agent registration. | [Troubleshooting](/racecraft-plugins-public/troubleshooting/) |
| Prefer platform-managed refresh, reinstall, remove, reload, or restart flows before cache-specific actions. | Direct cache edits or deletion can hide the real source/payload mismatch and should not be the default fix. | [Update & Rollback](/racecraft-plugins-public/update-and-rollback/) |
| Re-run Codex custom-agent registration only when bundled TOML agent files or installer output indicate it is needed. | Codex plugin installation, bundled skill loading, TOML custom-agent registration, and restart are separate steps. | [Codex custom agents](/racecraft-plugins-public/install/codex/#register-custom-agents) |
| Follow managed policy rather than bypassing it. | Organization policy may intentionally restrict marketplaces, network, hooks, MCP/app integrations, config, or approvals. | [Troubleshooting permissions](/racecraft-plugins-public/troubleshooting/#symptom-matrix) |

## Evaluator Checklist

Use this checklist for a quick trust review:

1. Confirm the platform claim is cited to the narrowest official Claude Code or
   OpenAI Codex doc.
2. Confirm the Racecraft claim is cited to a generated DOC-007 reference page or
   checked-in source file.
3. Confirm recommended practice is phrased as derived guidance, not a guarantee.
4. Confirm browser-rendered docs do not claim to run workflows, grant
   permissions, inspect local filesystems, or repair local state.
5. Confirm recovery guidance routes users through platform flows and does not
   make direct cache edits the default fix.

For symptom-level diagnosis, use
[Troubleshooting](/racecraft-plugins-public/troubleshooting/). For procedural
recovery, use [Update & Rollback](/racecraft-plugins-public/update-and-rollback/).
