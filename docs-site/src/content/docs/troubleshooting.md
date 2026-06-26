---
title: "Troubleshooting"
description: "Diagnose SpecKit Pro when it is missing, stale, blocked by policy, or behaving differently from the checked-in source — match the symptom, then take a read-only inspection step first."
---

Use this route when SpecKit Pro is missing, stale, blocked by policy, or
behaving differently from the checked-in source. The page is browser
documentation only: it does not run local diagnostics, grant permissions, invoke
plugin workflows, inspect your filesystem, or repair configuration.

Start by matching the symptom, then use the read-only inspection item before
taking any manual recovery action. Commands and paths are examples for you to
run or inspect in your own agent environment.

## Symptom Matrix

| Case | Platform | Symptom | Likely Cause | Read-only Inspect Command/File | Recommended Fix | Follow-up Link | Source Citation |
|---|---|---|---|---|---|---|---|
| Install failure | Both | SpecKit Pro is not visible after following an install guide. | The marketplace source, generated payload, or platform reload/restart step is incomplete. | Review the platform plugin manager view, the marketplace entry, and the generated payload path named by the install guide. | Side effect: platform plugin state may change. Use the platform install guide to refresh the marketplace source, repeat the platform install flow, then reload Claude Code or restart Codex as directed. | [Review update and rollback](/racecraft-plugins-public/update-and-rollback/) | [Claude install guide](/racecraft-plugins-public/install/claude-code/), [Codex install guide](/racecraft-plugins-public/install/codex/) |
| Marketplace source | Both | The marketplace does not show the expected `speckit-pro` entry or shows old metadata. | The marketplace source is stale, points at the wrong repository, or is restricted by managed policy. | Claude Code: open `/plugin` and inspect marketplace details. Codex: `codex plugin marketplace list --json`. | Side effect: marketplace source metadata may change. Refresh the approved marketplace source through the platform flow; do not bypass organization-managed sources. | [Check trust boundaries](/racecraft-plugins-public/security-and-trust/) | [Claude plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [Codex CLI reference](https://developers.openai.com/codex/cli/reference) |
| Generated payload | Both | Source changes are present in `speckit-pro/`, but installed behavior still reflects older files. | The generated Claude or Codex payload has not been refreshed or the marketplace points at an old payload. | Compare `speckit-pro/`, `dist/claude/speckit-pro/`, `dist/codex/speckit-pro/`, and the generated payload references. | Side effect: generated payload or platform plugin state may change. Use the project-owned payload refresh or marketplace flow; do not hand-edit generated payloads for recovery. | [Review source vs dist](/racecraft-plugins-public/reference/source-vs-dist/) | [Source vs dist reference](/racecraft-plugins-public/reference/source-vs-dist/) |
| Installed runtime state | Both | The platform still loads old skills, agents, hooks, or metadata after a source or payload update. | Installed plugin runtime state is stale relative to the marketplace source or generated payload. | Claude Code: inspect `/plugin` details. Codex: `codex plugin list --json` and review documented fields such as version, enabled state, source, marketplace source, and installed path when present. | Side effect: installed plugin state may change. Prefer platform refresh, reinstall, remove, reload, or restart flows before any cache-specific action. Cache mutation is last resort only. | [Recover stale installs](/racecraft-plugins-public/update-and-rollback/#stale-cache) | [Claude plugins reference](https://code.claude.com/docs/en/plugins-reference), [Codex CLI reference](https://developers.openai.com/codex/cli/reference) |
| Permissions or approvals | Both | A workflow stalls on network, filesystem, hook, MCP, or outside-workspace access. | Platform sandbox, approval policy, or managed configuration blocks the action. | Review the visible approval prompt, platform settings, and managed policy docs relevant to the blocked action. | Side effect: approving or changing policy can grant broader access. Follow your local or organization policy; do not bypass managed controls from docs guidance. | [Review security and trust](/racecraft-plugins-public/security-and-trust/) | [Claude permissions](https://code.claude.com/docs/en/permissions), [Codex permissions](https://developers.openai.com/codex/permissions) |
| Spec Kit CLI prerequisite | Both | SpecKit commands fail before creating or validating spec artifacts. | The Spec Kit CLI is absent, unavailable on `PATH`, or not the expected version for this repository. | `specify --version` | Side effect: toolchain state may change. Install or select the expected Spec Kit CLI before rerunning the workflow. | [Review first run](/racecraft-plugins-public/first-run/) | [Scripts reference](/racecraft-plugins-public/reference/scripts/), [check-prerequisites source](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh), [specify CLI helper source](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/speckit-pro/skills/speckit-autopilot/scripts/lib/specify-cli.sh) |
| GitHub CLI prerequisite | Both | PR, review, or GitHub-backed verification steps cannot run. | `gh` is missing, unauthenticated, or not configured for the target repository. | `gh --version` and `gh auth status` | Side effect: authentication state may change. Configure `gh` only for the account and repository you intend to use. | [Review contributor shell](/racecraft-plugins-public/contribute-and-release/) | [Scripts reference](/racecraft-plugins-public/reference/scripts/) |
| jq prerequisite | Both | JSON-based helper scripts or validation steps fail with command-not-found or parse errors. | `jq` is missing or unavailable to shell helpers. | `jq --version` | Side effect: local toolchain state may change. Add `jq` through your normal package manager before rerunning script-driven checks. | [Review scripts reference](/racecraft-plugins-public/reference/scripts/) | [Scripts reference](/racecraft-plugins-public/reference/scripts/) |
| Codex custom agents | Codex | `$speckit-autopilot` can load the plugin skill, but required executor or consensus agents are unavailable. | Plugin installation loaded bundled skills, but Codex custom-agent TOML registration was not refreshed. | Review the install skill report and the selected Codex agent destination for the expected TOML filenames listed in the Codex install guide. | Side effect: custom-agent files may be copied to the selected Codex agent directory. Run `@SpecKit Pro -> install` or `$install` only as a manual recovery action, then restart Codex. | [Review Codex install](/racecraft-plugins-public/install/codex/#register-custom-agents) | [Agents reference](/racecraft-plugins-public/reference/agents/) |
| Path confusion | Both | A local marketplace points at `speckit-pro/`, or a personal Codex install points at source instead of generated payload. | Authoring source and generated platform payloads were mixed up. | Review `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, and the path listed in the relevant install guide. | Side effect: marketplace or copied payload state may change. Point marketplaces at generated payloads or approved sources, then refresh through platform flows. | [Review source vs dist](/racecraft-plugins-public/reference/source-vs-dist/) | [Manifests reference](/racecraft-plugins-public/reference/manifests/) |
| Version drift | Both | Manifest version, marketplace listing, generated payload, and installed behavior do not agree. | Source manifests, generated manifests, marketplace catalog, or installed runtime state are out of sync. | Compare generated manifest pages, platform plugin detail views, and CLI JSON version fields where documented. | Side effect: platform plugin state or copied payload state may change. Sync to a known marketplace source, generated payload, Git ref, or manifest version; avoid direct installed-cache edits. | [Use version sync guidance](/racecraft-plugins-public/update-and-rollback/#version-sync) | [Manifests reference](/racecraft-plugins-public/reference/manifests/) |
| Source vs generated mismatch | Both | Generated reference pages or install behavior disagree with checked-in source files. | Generated reference pages or platform payloads are stale relative to source. | `pnpm --dir docs-site reference:check` | Side effect: validation only reports state. Refresh generated references or payloads through their owning project flow before publishing, not by editing generated subpages by hand. | [Review reference boundary](/racecraft-plugins-public/reference/) | [Reference source vs dist](/racecraft-plugins-public/reference/source-vs-dist/) |

## Read-Only Inspection Boundary

Inspection cells are intentionally limited to state-reporting commands, platform
detail views, manual file paths, or source/reference links. They do not contain
install, remove, reload, restart, approval, edit, delete, rebuild, config-write,
cache-edit, or secret-printing commands.

When a fix mutates state, the side effect is named first. Recovery actions live
in the recommended fix column or on [Update & Rollback](/racecraft-plugins-public/update-and-rollback/),
not in the inspection column.

## When To Switch Pages

- Use [Security & Trust](/racecraft-plugins-public/security-and-trust/) when the
  question is about platform permissions, sandboxing, hooks, MCP/app
  integrations, managed policy, or what the plugin can package.
- Use [Update & Rollback](/racecraft-plugins-public/update-and-rollback/) when
  you need refresh, reinstall, remove, rollback, stale-payload, stale-cache, or
  version-sync procedures.
- Use [Reference](/racecraft-plugins-public/reference/) when you need source
  evidence for manifests, skills, agents, hooks, scripts, tests, or source vs
  generated payload ownership.
