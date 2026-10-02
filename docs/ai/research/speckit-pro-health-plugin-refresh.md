# Research: plugin refresh fast path on both hosts

Ticket: #1020. Map: #1006. Date of research: 2026-10-01. Versions checked: Codex CLI 0.156.0, Claude Code 2.1.287.

## Answer

1. `codex plugin marketplace upgrade` times out because Codex runs every git step under a hard-coded 30 second limit with no setting to change it. A full (non-sparse) clone of this repo took 52 s here, so it cannot finish. A sparse, blob-less clone took 7 s, so a correctly registered sparse marketplace should fit. The upgrade only skips the clone when the stored revision equals the remote revision, which is why a hand-edited revision "works".
2. The supported Codex fast path is to register the repo checkout as a local marketplace root (`codex plugin marketplace add <path>`). Local roots are read in place: no clone, no timeout. Then `codex plugin remove` plus `codex plugin add` refreshes the installed copy. The TOML agents still need the bundled `install-codex-agents` helper and a Codex restart. That helper can run from a script.
3. Claude Code has no worktree-aware update. Each local-scope install is a separate record keyed by project path, and `claude plugin update` touches only the install for the current project. A script must run the update once per live worktree, with that worktree as the working directory.
4. The supported Claude refresh is `claude plugin marketplace update <name>` followed by `claude plugin update <plugin>@<name> --scope <scope>`. Then run `/reload-plugins` or start a new session.
5. The marketplace name registered locally in Claude Code (`racecraft-public-plugins`) differs from the name in this repo's marketplace file (`racecraft-plugins-public`). Any script must look the name up from the host's marketplace list by source, not hard-code it. The existing `scripts/refresh-local-plugin.py` hard-codes the repo name and also requires a Directory source, so it fails on a machine registered the way this one is (by reading the code; not run).

A single Python command can do all of it (see "Proposed one-command sequence"). Two steps cannot be automated away: Codex must be restarted, and a running Claude Code session needs `/reload-plugins` or a restart.

## Codex timeout cause

Confirmed from the openai/codex source (`codex-rs/core-plugins/src/marketplace_upgrade.rs` and `marketplace_upgrade/git.rs`, main branch):

- `MARKETPLACE_UPGRADE_GIT_TIMEOUT` is a constant `Duration::from_secs(30)`. It is passed to every git call in the upgrade. No config key or flag reads it.
- Each git call runs through `run_git_command_with_timeout`. On expiry it kills the child and returns `<context> timed out after 30s`. The staged directory is not cleaned up in that case.
- Upgrade flow per marketplace:
  1. `git ls-remote <source> <ref or HEAD>` to get the remote revision. If `ref` is a full SHA, no network call is made.
  2. If the installed snapshot's marketplace root validates and its stored metadata (source, ref, sparse paths, revision) equals the remote revision, return without cloning. Metadata lives in the snapshot's `.codex-marketplace-install.json`.
  3. Otherwise create a staging dir under `<codex home>/.tmp/marketplaces/.staging/marketplace-upgrade-*`, then clone into it.
  4. With no sparse paths: `git clone <source> <dest>` (full history, full tree), then `git checkout <ref>` if set. With sparse paths: `git clone --filter=blob:none --no-checkout`, `git sparse-checkout set <paths>`, `git checkout <ref or HEAD>`. None of the clones pass `--depth`.
  5. Validate the marketplace name in the staged root equals the configured name, write metadata, atomically activate.
- The same failure is reported upstream: openai/codex issue 24815 (open) shows `git clone marketplace source timed out after 30s` on a large repo, and issues 45943, 47735 and 38770 (open) report the leaked staging directories after a timeout.

Measured on this repo, read-only, scratch directories only (network speed varies by machine, so treat as one sample):

| Step | Result |
|---|---|
| Repo on GitHub (API `size`) | about 29 MB |
| Local object store | 40 MiB in 3 packs, 67,823 packed objects, 1,452 commits on the current branch, 2,291 across all refs |
| `git ls-remote ... HEAD` | 0.4 s |
| `git clone` (no filter, what Codex runs when no sparse paths are set) | 52.8 s wall, 33 MB `.git` |
| `git clone --filter=blob:none --no-checkout` (sparse mode, step 1) | 7.0 s wall, 4.8 MB `.git` |
| `git sparse-checkout set` plus `git checkout HEAD` for the three paths this machine configured | 1.0 s |

Local state on this machine:

- The configured Codex entry for this marketplace is a git source with `sparse_paths = [".agents/plugins", "dist/codex/speckit-pro", "typesafe-jev/plugin"]`. By the numbers above, a sparse upgrade fits inside 30 s here.
- The staging directory holds 63 orphaned `marketplace-upgrade-*` directories (2.8 GB total, dated Aug 21 to Sep 9, individual sizes up to 56 MB). Sizes of that order match full clones, which suggests earlier upgrades ran before sparse paths were set, or came from other configured marketplaces. Which marketplace produced them: not confirmed.
- The installed snapshot's recorded revision (`f9b7580`) is two commits behind the remote HEAD (`35f2d22`) at the time of the check. Both newer commits are docs-only, so no plugin payload difference was confirmed.

Not confirmed: which exact git step timed out in the original failure. The ticket does not include the error text. Candidates are the full clone (52 s measured) on an entry registered without `--sparse`, or a slow network on the sparse clone.

Root cause statement: the limit is fixed at 30 s, the registered marketplace must be sparse for the clone to fit, and any failure leaves a staging directory behind. The stale snapshot then forces a manual fast-forward, and the revision edit exists only to make step 2 above match so the upgrade skips the clone.

## Fast path per host

### Codex

Documented behavior (Codex CLI reference and plugin build guide on developers.openai.com):

- `codex plugin marketplace add` accepts a Git source (with `--ref`, repeatable `--sparse PATH`) or a local marketplace root directory.
- `codex plugin marketplace upgrade [NAME]` refreshes only Git marketplace snapshots. It has `--json` (`selectedMarketplaces`, `upgradedRoots`, `errors`).
- `codex plugin add`, `list` and `remove` have `--json`. `add --json` prints `pluginId`, `name`, `marketplaceName`, `version`, `installedPath`, `authPolicy`.
- For a local plugin the docs say to update the directory the marketplace entry points at and restart so the install picks up the new files. Installing a plugin needs a new session before skills and tools appear.
- Custom agents are standalone TOML files under `~/.codex/agents/` or a project `.codex/agents/`. Plugin installation does not copy them there (Codex subagents docs; this repo's `install` skill says the same and names `$install` as the way to copy them).

Source facts (marketplace_add.rs): adding a local root records the entry without staging a clone. Adding a name that already exists from a different source fails with "already added from a different source; remove it before adding this source". So switching this machine's `racecraft-plugins-public` entry from the Git snapshot to the checkout needs `codex plugin marketplace remove racecraft-plugins-public` first.

Fast path, in order of preference:

1. Maintainer or dogfood machine: point the marketplace at the checkout (local root). Refresh is then `codex plugin remove speckit-pro@racecraft-plugins-public`, `codex plugin add speckit-pro@racecraft-plugins-public --json`, run the agent install helper, restart. No network, no 30 s limit. The repo marketplace file (`.agents/plugins/marketplace.json`, name `racecraft-plugins-public`) already points at `./dist/codex/speckit-pro` and the committed `dist/` is current after `scripts/refresh-release-artifacts.py`.
2. Machine that must track GitHub: keep the sparse Git entry, run `codex plugin marketplace upgrade racecraft-plugins-public --json`, and check `errors`. If it reports a timeout, fall back to option 1 or retry; the limit cannot be raised. Do not edit the revision or fast-forward the snapshot by hand: it is Codex-owned state and the manual route is what this ticket replaces.
3. Agents: run the bundled `install-codex-agents` runner helper in `apply` mode (the repo's `install` skill documents the helper, its `dry_run` then `apply` order, the `destination` default `~/.codex/agents/`, and a `restart_required` result). The helper resolves the plugin's `codex-agents/` from the installed plugin and does not mutate plugin caches. The runner is invoked as `python -m speckit_pro_runner` with one JSON request on stdin (`--help` in `__main__.py`). The exact request envelope fields were not confirmed in this pass (only the `schema_version` check and required-field check were seen); read `envelope.py` and the `install` skill before wiring it.
4. Restart Codex. Not scriptable from outside a running TUI. Not confirmed whether Codex can hot-reload agent TOML; the repo's skill says restart.

Not confirmed: whether `codex plugin add` on an already-installed plugin refreshes the cache without a prior `remove`. The existing repo script uses remove then add, and so does this plan. A `remove` deletes the plugin's local cache per its help text.

### Claude Code

Documented behavior (code.claude.com plugin docs: discover-plugins, plugins/loading, plugins/cli-reference):

- Install scopes: user (`~/.claude/settings.json`), project (`.claude/settings.json`), local (`.claude/settings.local.json`, this repository only). Local overrides project overrides user.
- `claude plugin install` and `uninstall` default to user scope. `claude plugin update <plugin>` with no `--scope` updates "the most specific scope it's installed at for your current project, checking local, project, user, then managed" (v2.1.281 and later). It takes `--json`, `-y`, `-s`.
- Install records are in `installed_plugins.json` under the plugins root, one record per install with `scope`, `projectPath` (project and local only), `installPath`, `version`. `claude plugin list --json` exposes the same fields. The records are separate per project path, so a worktree is a separate project.
- Cache layout: `cache/<marketplace>/<plugin>/<version>/`. For a relative-path plugin inside a Git-hosted marketplace and no `version` in manifest or entry, the version is the commit SHA of the installed directory (12 characters). Docs state: a manifest that pins `version` keeps users on the cached copy until the string changes.
- `claude plugin marketplace update [name]` refreshes the marketplace catalog from its source. It takes no flags except `--json` (with a name).
- Auto-update: off by default for third-party marketplaces, on by default for official ones. It runs once per interactive session after a random delay of up to ten minutes. The running session keeps loaded versions; run `/reload-plugins` or restart.
- `claude plugin install name@marketplace` refreshes that marketplace first unless it is a local directory source or was refreshed in the last 30 seconds.
- Changelog: v2.1.281 made `plugin update` resolve the scope instead of assuming user. An earlier fix addressed project-scoped plugins not loading from worktrees of the same repository.

Observed on this machine (read-only, from the records):

- The Claude marketplace for this repo is registered as `racecraft-public-plugins` from the GitHub repo, auto-update on. The repo's own marketplace file is named `racecraft-plugins-public`. The two names differ by word order. Why the registered name differs: not confirmed (a rename, or a hand-chosen name at `marketplace add`).
- `speckit-pro` has 22 install records: 1 user and 21 local, spread across 9 distinct version SHAs. 17 of the 21 local records point to project paths that no longer exist on disk (deleted worktrees). Some of the 21 belong to worktrees of a different repository.
- The cache for this plugin holds 54 version directories (300 MB).
- The user record and the current checkout's local record were refreshed at the same time. Other worktrees' local records kept the SHA they had at creation. This matches the docs: update acts on the current project only. Whether auto-update skips records of other project paths: not confirmed.
- The user-scope SHA equals the last release commit rather than the newest commit. Because the version is the SHA of the installed directory, docs-only commits would not move it. Not confirmed; check by comparing `git log -1 -- dist/claude/speckit-pro` with the cache folder name.

Fast path:

1. `claude plugin marketplace update <registered name>`.
2. `claude plugin update speckit-pro@<registered name> --scope user --json -y`.
3. For each live worktree of this repo (`git worktree list --porcelain`, skip paths that do not exist): run `claude plugin update speckit-pro@<registered name> --scope local --json -y` with that worktree as the working directory. Use `claude plugin list --json` in the same directory to confirm `version` and `projectPath`.
4. Report, but do not touch, local records whose `projectPath` is gone. Removing them needs `claude plugin uninstall ... --scope local`, which the docs describe as acting on the current project; whether it can target a deleted path was not confirmed. Do not edit `installed_plugins.json` or the cache by hand (this repo's own `update-and-rollback` page says the same).
5. Reload: `/reload-plugins` in running sessions, or a new session.

For worktrees created later, a cheaper fix is to not install per worktree: user scope already applies in every project on the machine (docs), so a worktree needs no local record when the user-scope install is current. Whether this plugin can rely on that: not confirmed, since the local installs may exist for a reason outside this ticket.

## Proposed one-command sequence

Extend `scripts/refresh-local-plugin.py` (it already builds artifacts, validates the Claude payload, and does Claude and Codex refresh). It is one Python command: `python3 scripts/refresh-local-plugin.py`. Needed changes:

1. Resolve names, do not hard-code them:
   - Claude: parse `claude plugin marketplace list --json`, choose the entry whose `source.repo` is this repo's `owner/name` (fall back to the name in `.claude-plugin/marketplace.json`). Do not require a Directory source.
   - Codex: parse `codex plugin marketplace list --json`, choose the entry by `marketplaceSource`, fall back to the name in `.agents/plugins/marketplace.json`.
2. Build: `python3 scripts/refresh-release-artifacts.py` (already step one today), so committed `dist/` matches source.
3. Codex marketplace: if the entry is a local root equal to this checkout, nothing to do. If it is a Git entry, run `codex plugin marketplace upgrade <name> --json` and read `errors`. On a timeout error, print the supported switch (`marketplace remove`, then `marketplace add <checkout>`) and stop, or perform it behind an explicit `--local-marketplace` flag because it changes the user's Codex config.
4. Codex plugin: `codex plugin remove <id>` (tolerate "not installed"), then `codex plugin add <id> --json`; keep `installedPath` and `version`.
5. Codex agents: run the `install-codex-agents` helper with `dry_run`, compare the plan, then `apply`, reading `restart_required` from the response.
6. Claude marketplace: `claude plugin marketplace update <name>`.
7. Claude installs: update user scope, then for each existing worktree of this repo update local scope with `cwd=<worktree>`, all with `--json -y`. Collect `outcome`, `message`, new `version`.
8. Verify: `codex plugin list --json` shows the installed `version` equal to the checkout's Codex plugin manifest version; `claude plugin list --json` per worktree shows the same SHA as the user record.
9. Print one summary table, the stale local records (missing project path), and the two manual steps: restart Codex, and `/reload-plugins` or a new Claude Code session. Exit non-zero if any step reported `outcome: failed`.

Replaces today's manual steps: snapshot fast-forward (gone with a local root), revision edit (gone), `codex plugin add` (steps 3 and 4), `$install` (step 5), Claude plugin update (steps 6 and 7), local-scope re-pins (step 7). Remaining by hand: the Codex restart and the Claude reload.

Risks to check when implementing:

- Step 7 was designed from the docs and the install records, not run (no state-changing command was run in this research).
- Run Claude updates sequentially. Whether concurrent `plugin update` calls are safe against `installed_plugins.json` was not confirmed.
- `-y` is documented for accepting a marketplace-declared command and is required when stdin or stdout is not a TTY; this plugin's source is a plain relative path, so no command should be shown. Confirm on first run.

## Sources

Local, read-only (commands listed, nothing mutating run):

- `codex plugin --help`, `codex plugin marketplace --help`, `codex plugin marketplace upgrade --help`, `codex plugin marketplace list`, `codex --version` (0.156.0).
- `claude plugin --help`, `claude plugin update --help`, `claude plugin marketplace --help`, `claude plugin marketplace update --help`, `claude plugin marketplace list --json`, `claude plugin list --json`, `claude --version` (2.1.287).
- Claude plugin state: `known_marketplaces.json`, `installed_plugins.json`, and the `cache/` folder listing under the plugins root (read only).
- Codex state: the marketplace entry in `config.toml`, the snapshot's `.codex-marketplace-install.json`, the `.staging` directory listing and sizes.
- Network probes, scratch directory only: `git ls-remote`, a full clone, a blob-less clone plus sparse checkout of this repo.
- Repo files: `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `scripts/refresh-local-plugin.py`, `scripts/refresh-release-artifacts.py`, `docs-site/src/content/docs/update-and-rollback.md`, `dist/codex/speckit-pro/skills/install/SKILL.md`, `speckit-pro/speckit_pro_runner/__main__.py`, `speckit-pro/speckit_pro_runner/envelope.py`.
- `ripwire . --for="plugin marketplace install refresh"` to locate the refresh script and marketplace files.

Primary, upstream:

- openai/codex, `codex-rs/core-plugins/src/marketplace_upgrade.rs`, `marketplace_upgrade/git.rs`, `marketplace_upgrade/activation.rs`, `marketplace_add.rs` (main branch, fetched 2026-10-01).
- openai/codex issues 24815, 45943, 47735, 38770 (all open at check time).
- Codex CLI reference: https://developers.openai.com/codex/cli/reference
- Codex plugins: https://developers.openai.com/codex/plugins
- Codex plugin build guide: https://developers.openai.com/codex/plugins/build
- Codex subagents (custom agent files): https://developers.openai.com/codex/subagents
- Claude Code: https://code.claude.com/docs/en/discover-plugins, https://code.claude.com/docs/en/plugins/loading, https://code.claude.com/docs/en/plugins/cli-reference, https://code.claude.com/docs/en/plugin-marketplaces, https://code.claude.com/docs/en/changelog

Not looked at or not confirmed:

- The original timeout error text and which git step failed.
- Whether `codex plugin add` refreshes an installed plugin without `remove`.
- Codex hot reload of agent TOML.
- The runner request envelope for `install-codex-agents`.
- Whether `claude plugin uninstall --scope local` can target a deleted project path.
- Claude auto-update behavior across other projects' local records.
- Why the Claude marketplace name differs from the marketplace file name.
- Concurrency safety of parallel `claude plugin update` calls.
