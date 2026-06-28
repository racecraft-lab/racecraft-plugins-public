# Platform User Journeys and Universal-Install Gaps

Status: XPLAT-003 research supplement
Date: 2026-06-28
Scope: Windows first, then macOS/Linux and managed/dual-install users

## Summary

SpecKit Pro is not universal just because Claude Code or Codex can install a
plugin. Universal means a user on the claimed platform can install the platform
product, install the official Spec Kit / `specify` prerequisites, add the
Racecraft marketplace, install SpecKit Pro, get every bundled
skill/agent/hook/runner source or launcher file, run first-use setup, run
scaffold and autopilot, receive a complete UAT runbook, update safely, and
repair stale or incomplete state without cloning source or installing any
plugin-only language toolchain.

The current repository does not yet meet that bar. The most important gaps are
native Windows execution, Codex custom-agent completeness, Bash/jq/rsync/perl
assumptions in installer and hook paths, missing Python runner/preflight files,
active Bash build/test/eval/release-readiness gates, and lack of a shared
autoheal/doctor path that scaffold and autopilot can invoke before producing
low-quality workflow output.

## Source Baseline

Official platform facts used here:

- Claude Code setup docs list native Windows, WSL, macOS, and Linux support.
  Native Windows can use PowerShell/CMD; Git for Windows is optional and only
  enables the Bash tool.
- Claude Code plugin docs define plugins as self-contained directories with
  skills, agents, hooks, MCP servers, LSP servers, monitors, scripts, and
  `bin/` executables. Plugin `bin/` executables are added to the Bash tool
  `PATH` while the plugin is enabled.
- Claude Code marketplace docs say users add marketplaces with
  `/plugin marketplace add`, install plugins with `/plugin install`, and that
  marketplace installs copy the plugin directory into a versioned local cache.
  Installed plugins cannot rely on files outside their own directory.
- Codex docs define plugins as installable bundles of skills, apps, MCP
  servers, hooks, and assets. Codex plugin marketplaces can be repo-scoped at
  `$REPO_ROOT/.agents/plugins/marketplace.json`, personal at
  `~/.agents/plugins/marketplace.json`, or added by
  `codex plugin marketplace add`.
- Codex skills can include optional scripts and references, but script support
  does not imply Bash, Node, jq, rsync, perl, Go, Rust, or Zig exists on every
  installed host. Python is allowed only through the documented SpecKit-Pro
  prerequisite boundary: official Spec Kit / `specify` and Python 3.11+.
- Codex custom agents are standalone TOML files under `~/.codex/agents/` or
  `.codex/agents/`; they are not automatically registered by a generic plugin
  skill install.
- Codex Windows docs say the Windows app supports plugins and skills, and that
  native Windows, unelevated/elevated sandbox modes, and WSL2 are separate
  operating modes.

Repository facts used here:

- `.claude-plugin/marketplace.json` points Claude Code to
  `./dist/claude/speckit-pro`.
- `.agents/plugins/marketplace.json` points Codex to
  `./dist/codex/speckit-pro`.
- Current generated Claude payload includes Claude skills, Claude agents,
  Claude hooks, `scripts/curated-set.json`, and `scripts/install-curated-set.sh`.
- Current generated Codex payload includes Codex skills, `codex-hooks.json`,
  `scripts/curated-set.json`, `scripts/install-curated-set.sh`, and ten
  `codex-agents/*.toml` files.
- Current Codex install skill and public install docs still list and copy nine
  TOML files, omitting `uat-runbook-author.toml`.
- Current Codex hook command uses POSIX shell constructs plus `jq` and `grep`.
- Current Codex custom-agent installer is a Bash script that can use `jq`,
  `sort -V`, `rsync`, `rm`, `cp`, and `perl`.
- Current generated payloads do not include `speckit-pro-runner` files,
  runner source, a runner manifest, or runner checksums.
- Current project validation and eval gates under `tests/speckit-pro/**` plus
  payload/release helper scripts are Bash-backed. They are not acceptable final
  release gates for a pure Python support claim.

## Universal Support Definition

XPLAT is only fully shipped when every claimed platform has current evidence for
all of these steps:

1. The user can install Claude Code or Codex on that platform using official
   product guidance.
2. The user can add or select the Racecraft marketplace without a source
   checkout when using a public marketplace path.
3. The installed plugin payload contains every required surface for that
   product: skills, agents, hooks, metadata, runner source or launcher files,
   manifests, and checksums.
4. The product loads the installed payload after its documented reload or
   restart step.
5. First-use setup detects missing SpecKit CLI/project integration
   prerequisites and either repairs them through an explicit user-approved path
   or fails closed with clear guidance.
6. Scaffold and autopilot run without depending on Bash, jq, rsync, perl, Git
   Bash, WSL, or a language toolchain beyond the official Spec Kit / `specify`
   Python prerequisite.
7. UAT output is complete enough to use: no empty PR placeholders, no raw HTML
   anchors in reader-facing runbooks, concrete test steps, clear expected
   results, and source-backed gaps.
8. Update and autoheal flows can detect stale caches, missing agents, missing
   runner source or launcher files, version drift, and incomplete payloads.
9. Build/test/eval/payload/release-readiness gates that validate or publish
   shipped plugin behavior run through Python standard-library commands.

## Journey 1: Windows Native User + Claude Code

Current user path:

1. Install Claude Code on Windows with the official PowerShell, CMD, or WinGet
   path.
2. Start `claude` in the project directory.
3. Add and install SpecKit Pro:

   ```text
   /plugin marketplace add racecraft-lab/racecraft-plugins-public
   /plugin install speckit-pro@racecraft-plugins-public
   /reload-plugins
   ```

4. Open `/plugin` and confirm `speckit-pro` is installed from
   `racecraft-plugins-public`.
5. Verify the namespaced skill surface:

   ```text
   /speckit-pro:speckit-status
   /speckit-pro:speckit-coach walk me through SDD
   ```

6. For full use in a consumer repo, run `/speckit-pro:speckit-install` if the
   repo does not have SpecKit CLI and project integrations.
7. Run `/speckit-pro:speckit-scaffold-spec <SPEC-ID>`.
8. Run `/speckit-pro:speckit-autopilot <workflow.md>`.
9. Review generated PR packet and UAT runbook before opening or updating the PR.

Current gaps:

- Claude Code can run natively on Windows without Git Bash, but our current
  Claude plugin hook and setup guidance still assume Bash-style commands in
  several places.
- Claude plugin `bin/` is documented as available to the Bash tool. That does
  not prove a native Windows user without Git Bash can execute a plugin `bin/`
  runner through the same path.
- `/speckit-pro:speckit-install` currently wraps `specify`, `uv`, and
  `install-curated-set.sh`; this is not a proven Windows-native path.
- Current generated payloads do not contain Python runner source, launcher
  metadata, or Windows interpreter-discovery evidence.
- Native Windows UAT has not proven scaffold, autopilot, hooks, UAT runbook
  generation, and PR packet closeout end-to-end.

Target XPLAT behavior:

- The Claude payload includes `scripts/speckit_pro_runner.py`, any required
  thin launcher metadata, and manifest/SHA-256 metadata.
- Claude skill and hook paths invoke Python through a documented
  platform-compatible command form and do not rely on Bash or PowerShell helper
  logic.
- `/speckit-pro:speckit-status`, scaffold, and autopilot preflight missing
  prerequisites before doing meaningful work.
- If the user lacks SpecKit CLI, the plugin reports the exact setup gap without
  emitting broken Bash instructions.
- UAT verifies Windows native with and without Git for Windows if public claims
  cover both paths.

## Journey 2: Windows Native User + Codex

Current user path:

1. Install Codex on Windows using the official app or CLI path.
2. Add/select the Racecraft marketplace. Public CLI form should be:

   ```text
   codex plugin marketplace add racecraft-lab/racecraft-plugins-public
   ```

   Repo-local testing can instead open this repository in Codex and use the
   checked-in `.agents/plugins/marketplace.json`.
3. Open the Codex plugin directory:

   ```text
   codex
   /plugins
   ```

4. Install `SpecKit Pro` from the Racecraft marketplace.
5. Start a new Codex thread or restart Codex when plugin enablement changes.
6. Run the Codex-only install skill so custom-agent TOML files are copied:

   ```text
   @SpecKit Pro -> install
   ```

   or:

   ```text
   $install
   ```

7. Restart Codex so custom agents load.
8. Verify plugin skills:

   ```text
   $speckit-status
   $speckit-coach walk me through SDD
   ```

9. For full use in a consumer repo, run `$speckit-install` if SpecKit CLI and
   project integrations are missing.
10. Run `$speckit-scaffold-spec <SPEC-ID>`.
11. Run `$speckit-autopilot <workflow.md>`.
12. Review generated PR packet and UAT runbook before opening or updating the
   PR.

Current gaps:

- Codex custom agents are not complete by current installer contract: the
  payload contains `uat-runbook-author.toml`, but the installer and docs expect
  only nine TOML files.
- The Codex installer is a Bash script and uses Unix tooling that is not
  guaranteed on native Windows.
- `codex-hooks.json` uses POSIX shell, `jq`, and `grep`; it has no Windows
  command override.
- Codex docs support Windows plugins and skills, but they do not guarantee a
  plugin-root `bin/` discovery model equivalent to Claude's Bash `PATH`
  behavior.
- The marketplace-update auto-sync behavior in the install skill depends on
  `jq`, `sort -V`, `rsync`, or destructive wipe-and-copy fallback logic, none of
  which is acceptable as a universal native Windows repair path.
- There is no Windows-native doctor that proves the installed Codex plugin
  cache, copied custom-agent destination, hooks, and runner source or launcher
  files match the release.

Target XPLAT behavior:

- The Codex payload includes all required custom-agent TOML templates, including
  `uat-runbook-author.toml`.
- `$install` uses the bundled cross-platform runner or a documented Codex-native
  platform path to copy and verify agents.
- The expected agent list is derived from the payload or a checked manifest, not
  duplicated manually in README text and installer arrays.
- Codex hooks use `commandWindows` or route through the runner so native Windows
  does not require Bash, jq, grep, rsync, or perl.
- Scaffold and autopilot call the same install-completeness doctor before
  generating workflow artifacts.

## Journey 3: Windows User Running WSL

Current user path:

1. Install WSL2 and keep the project inside the Linux filesystem.
2. Install Claude Code or Codex inside WSL using the Linux instructions.
3. Install SpecKit Pro from the relevant marketplace inside that WSL runtime.
4. Use the Linux journey for plugin skills, agents, hooks, scaffold, and
   autopilot.

Current gaps:

- This is a Linux journey on a Windows machine, not native Windows support.
- It can hide native Windows defects because Bash, Unix paths, and Linux
  package behavior are available in WSL.
- Public support claims must say whether "Windows" means native Windows, WSL,
  or both.

Target XPLAT behavior:

- Native Windows and WSL are tested and reported separately.
- If WSL is supported as a fallback, the docs state that the plugin runs inside
  WSL and uses Linux runner files.
- WSL success never substitutes for native Windows UAT evidence.

## Journey 4: macOS or Linux User + Claude Code

Current user path:

1. Install Claude Code using the official native installer or package manager.
2. Start `claude` in the project.
3. Add and install SpecKit Pro:

   ```text
   /plugin marketplace add racecraft-lab/racecraft-plugins-public
   /plugin install speckit-pro@racecraft-plugins-public
   /reload-plugins
   ```

4. Verify `/plugin`, `/speckit-pro:speckit-status`, and
   `/speckit-pro:speckit-coach`.
5. Run `/speckit-pro:speckit-install` if project integration is missing.
6. Run scaffold, autopilot, UAT review, and PR packet generation.

Current gaps:

- macOS/Linux are closer to the current Bash-heavy implementation, but still
  not fully universal. `jq`, `rsync`, `perl`, `uv`, `gh`, and `specify` are not
  guaranteed for every user.
- No macOS/Linux runner source, launcher, or installed-cache invocation evidence
  exists in the generated Claude payload.
- Existing UAT quality issues mean a successful run can still produce a weak or
  incomplete runbook.

Target XPLAT behavior:

- macOS/Linux payloads include matching Python runner source, any required thin
  launcher, and installed-cache launch evidence.
- The plugin reports missing optional tools as prerequisites, not as cryptic
  shell failures.
- UAT output quality gates block empty placeholders and reader-facing raw HTML.

## Journey 5: macOS or Linux User + Codex

Current user path:

1. Install Codex using the official app or CLI path.
2. Add/select the marketplace with the Codex app or:

   ```text
   codex plugin marketplace add racecraft-lab/racecraft-plugins-public
   ```

3. Open `/plugins`, install SpecKit Pro, and restart/start a new thread as
   needed.
4. Run `@SpecKit Pro -> install` or `$install` to copy custom agents.
5. Restart Codex.
6. Verify `$speckit-status` and `$speckit-coach`.
7. Run `$speckit-install`, `$speckit-scaffold-spec`, and `$speckit-autopilot`
   as needed.

Current gaps:

- Current Codex custom-agent install is incomplete for
  `uat-runbook-author.toml`.
- Even on Unix-like systems, jq/rsync/perl may be absent.
- No Codex runner source, launcher metadata, manifest, checksum, or
  installed-cache invocation evidence exists yet.
- There is no shared doctor that proves plugin cache freshness plus copied
  agent freshness before autopilot uses subagents.

Target XPLAT behavior:

- Codex installer copies every bundled agent listed by the payload manifest.
- Codex status/scaffold/autopilot repair or fail closed when copied agents are
  absent or stale.
- Codex uses documented plugin skill, hook, or MCP command surfaces for runner
  invocation rather than assuming Claude's `bin/` behavior applies.

## Journey 6: Dual Claude Code + Codex User

Current user path:

1. Install both products.
2. Install SpecKit Pro separately in Claude Code and Codex; these are separate
   plugin ecosystems.
3. In Claude Code, verify `/speckit-pro:<skill>`.
4. In Codex, run `$install`, restart, and verify `$speckit-*`.
5. For a shared project, run SpecKit project integration once per desired
   integration, for example Claude and Codex skills mode.
6. Use either platform to scaffold or autopilot, but review generated files and
   PR packet before switching platforms.

Current gaps:

- Claude plugin agents and Codex custom-agent TOML registrations are different
  surfaces. One product being healthy does not prove the other is healthy.
- Current docs and installer logic can drift because the expected agent list is
  duplicated.
- Stale installed cache behavior differs between products.
- The project can appear installed in one product while the other lacks agents,
  hooks, or fresh payload metadata.

Target XPLAT behavior:

- A single install-completeness contract declares the required Claude payload
  files and required Codex copied-agent files.
- Product-specific doctor output says which side is healthy and which repair was
  attempted.
- Scaffold/autopilot output records the platform used and the plugin/runtime
  readiness evidence available at execution time.

## Journey 7: Managed or Enterprise User

Current user path:

1. Install the platform product under organization policy.
2. Confirm the Racecraft marketplace source is allowed.
3. Install the plugin only from approved marketplace sources.
4. Confirm hooks, MCP servers, network access, local writes, and custom-agent
   destinations are permitted by policy.
5. Run normal status, install, scaffold, and autopilot flows.

Current gaps:

- Current autoheal ideas may require writes to `~/.codex/agents/`,
  `.codex/agents/`, or plugin caches. Managed environments may block those
  writes.
- Current installer fallback logic can remove and recreate active plugin
  directories. That is not an acceptable default repair behavior in restricted
  environments.
- Hook trust and command execution policies can disable automation even when the
  plugin appears installed.

Target XPLAT behavior:

- Doctor distinguishes "missing" from "blocked by policy".
- Autoheal never mutates plugin caches or global agent registries without a
  clear, minimal, user-approved action.
- Managed install docs include the exact policy surfaces that must allow the
  plugin.

## Autoheal Requirements for Scaffold and Autopilot

The scaffold and autopilot skills need a shared preflight/doctor path before
they do meaningful work. It should be callable from both products and should be
implemented through the selected cross-platform runner once XPLAT ships.

Required checks:

1. Identify platform product: Claude Code or Codex.
2. Identify OS mode: Windows native, Windows WSL, macOS, or Linux.
3. Identify installed plugin version, marketplace name, and payload root.
4. Verify the installed payload contains required skills, agents, hooks, and
   scripts for that product.
5. Verify the runner source and any thin launcher for the current platform exist
   and match the manifest/checksum.
6. For Claude Code, verify plugin agents are present in the installed payload.
7. For Codex, verify every required `codex-agents/*.toml` template is copied to
   the selected custom-agent destination, including `uat-runbook-author.toml`.
8. Verify hooks are platform-compatible, including Windows command overrides
   where required.
9. Verify SpecKit CLI availability separately from plugin availability.
10. Verify project integration state separately from plugin availability.
11. Verify UAT runbook quality gates: no raw HTML anchors in reader-facing
    sections, no empty `PRPR: <set on PR open>` style placeholders, concrete
    scenario steps, expected results, evidence fields, and gap entries.

Required repair behavior:

- If repair is safe and product-local, perform it with explicit approval and
  report exactly what changed.
- If repair would cross a policy boundary or require network/package install,
  stop and report the exact prerequisite.
- If a stale marketplace or cache is detected, prefer documented platform
  update/reinstall/reload flows before cache mutation.
- Never silently continue into scaffold or autopilot when required agents,
  runner source or launcher files, or project integration state are missing.

## Gap Register

| Gap | User impact | Required owner |
|---|---|---|
| Missing runner source or launcher metadata in both generated payloads | No cross-platform runner claim can be made | XPLAT-004/XPLAT-007 |
| No Windows Python interpreter-discovery command path | Native Windows users may fail before useful work starts | XPLAT-004/XPLAT-007 |
| Claude `bin/` is Bash-tool-specific | Native Windows without Git Bash may not execute plugin `bin/` artifacts | XPLAT-004/XPLAT-007 |
| Codex has no Claude-style `bin/` guarantee | Codex runner invocation must use documented skill/hook/MCP paths | XPLAT-004/XPLAT-007 |
| Codex installer omits `uat-runbook-author.toml` | UAT author agent may be missing even when plugin seems installed | Install skill / XPLAT-007 |
| Codex installer depends on Bash/jq/rsync/perl | Native Windows repair path is not universal | Install skill / XPLAT-007 |
| Codex hook depends on POSIX shell/jq/grep | Native Windows hook path is not universal | Hook owner / XPLAT-007 |
| SpecKit CLI setup depends on uv/specify/network | Plugin install and project bootstrap are separate prerequisites | Install/upgrade skills |
| Curated-set installer depends on Bash/gh | Optional extension setup may fail without clear platform repair | Install/upgrade skills |
| UAT runbook can contain raw HTML anchors and empty PR placeholders | UAT evidence is hard to review and not reader-ready | Autopilot / UAT author |
| No shared doctor/preflight used by scaffold and autopilot | Broken installs can produce broken workflow artifacts | Scaffold/autopilot owners |
| Active tests/evals/payload builders are Bash-backed | Pure Python support claims would still depend on Unix tooling to prove or publish shipped behavior | XPLAT-007 |
| No per-platform UAT matrix for install, full use, update, and repair | Universal support claim lacks evidence | XPLAT-007 |
| No current tag/version freshness gate across Claude and Codex payloads | Users can install stale or mismatched plugin versions | Release/process owners |

## Public Claim Boundary

Do not claim any of the following until XPLAT evidence exists:

- "Works on Windows, macOS, and Linux" without saying exactly which product and
  OS mode were tested.
- "No prerequisites" for full SpecKit use. The plugin can be self-contained
  while SpecKit CLI/project setup still has prerequisites.
- "Codex agents are installed" based only on plugin skill presence.
- "Marketplace verifies runner files" or "trusted runner" before manifest,
  checksum, local verification, and release evidence exist.
- "Windows supported" when only WSL passed.

Allowed wording before full XPLAT cutover:

- "Marketplace install payload exists for Claude Code and Codex."
- "Python-runner support is planned and blocked on prerequisite preflight,
  runner source integrity, install-completeness evidence, and platform UAT."
- "Codex custom-agent registration requires a separate install/repair step
  until autoheal is implemented and verified."

## XPLAT Fully Shipped Acceptance

XPLAT is universal only when this matrix passes for each claimed platform:

| Platform mode | Claude Code install | Codex install | Full use | Update | Autoheal |
|---|---|---|---|---|---|
| Windows native without Git Bash | Pass required if claimed | Pass required if claimed | Scaffold/autopilot/UAT pass | Version/cache pass | Doctor repair/fail-closed pass |
| Windows native with Git for Windows | Pass required if claimed | Pass required if claimed | Scaffold/autopilot/UAT pass | Version/cache pass | Doctor repair/fail-closed pass |
| Windows WSL2 | Pass if claimed separately | Pass if claimed separately | Linux runner path pass | Version/cache pass | Doctor repair/fail-closed pass |
| macOS arm64/x64 | Pass required if claimed | Pass required if claimed | Scaffold/autopilot/UAT pass | Version/cache pass | Doctor repair/fail-closed pass |
| Linux x64/arm64 | Pass required if claimed | Pass required if claimed | Scaffold/autopilot/UAT pass | Version/cache pass | Doctor repair/fail-closed pass |

Each pass must record product version, plugin version, marketplace source,
installed payload path, runner file ID, checksum result, custom-agent state,
SpecKit CLI state, scaffold command, autopilot command, UAT runbook quality
result, and any repair action taken.

## Recommended Next Spec Work

1. Patch the Codex install skill and docs to include `uat-runbook-author.toml`
   or derive the expected list from the packaged payload.
2. Add an XPLAT doctor contract that both scaffold and autopilot must call.
3. Move Codex install/repair behavior off Bash/jq/rsync/perl and onto the
   selected runner or another documented cross-platform path.
4. Add Windows command overrides or runner-backed hooks for Codex and Claude
   where needed.
5. Add generated-payload gates that prove Claude and Codex dist payloads contain
   the same released version, every expected bundled agent, and every claimed
   runner source and any thin launcher.
6. Replace active Bash tests, eval runners, payload builders, and
   release-readiness checks with Python standard-library gates before XPLAT-007
   cutover.
7. Add platform UAT scenarios for native Windows, WSL, macOS, Linux, Claude
   Code, Codex, update, stale cache, missing agents, and missing SpecKit CLI.
