# Changelog

## [0.5.0](https://github.com/racecraft-lab/typesafe-mcp/compare/v0.4.0...v0.5.0) (2026-09-18)

First release of Racecraft Lab's fork of [itsmostafa/typesafe-mcp](https://github.com/itsmostafa/typesafe-mcp). The fork's substance landed in [#1](https://github.com/racecraft-lab/typesafe-mcp/pull/1), [#2](https://github.com/racecraft-lab/typesafe-mcp/pull/2) and [#3](https://github.com/racecraft-lab/typesafe-mcp/pull/3), which squash-merged with non-conventional subjects, so this section is written by hand rather than generated from them.

### Features

* **Explicit backend selection.** `JEV_PROVIDER` chooses the backend: unset or `typesafe` for `https://api.typesafe.ai/v1/systemone`, `openrouter` for OpenRouter's Decisions endpoint at `https://openrouter.ai/api/alpha/decisions`. Upstream picked the backend from whichever API key happened to be set, so which account was billed and where state was sent depended on ambient environment ([#1](https://github.com/racecraft-lab/typesafe-mcp/pull/1))
* **Credentials from a private file.** `JEV_API_KEY_FILE` reads a key from a file that must be a regular file with no group or world permission bits, capped at 8 KiB, with one optional trailing newline. The provider's environment variable still works. Keys are redacted in every error path and never reach a prompt, a process argument, a log, or a generated client config ([#1](https://github.com/racecraft-lab/typesafe-mcp/pull/1))
* **Per-backend request and response validation.** TypeSafe accepts a string, object, array or null for instructions and criteria descriptions; OpenRouter's Decisions schema types all of those as strings. The stricter schema is applied to the OpenRouter backend only, rejected locally with the field path, rather than narrowing TypeSafe's contract globally. Responses are checked for a named model, reported usage, and scores inside the criteria range ([#1](https://github.com/racecraft-lab/typesafe-mcp/pull/1))
* **`evaluate setup mcp` generates configuration instead of applying it.** Upstream ran the client CLIs and rewrote Claude Desktop's config file, which also holds user preferences. The command now prints shell-quoted commands and a Codex TOML table and touches nothing on disk. `--dry-run=false` is refused rather than ignored ([#1](https://github.com/racecraft-lab/typesafe-mcp/pull/1))
* **Ships as a plugin for Claude Code and Codex.** One repository serves both: `.claude-plugin/` and `.agents/plugins/marketplace.json` for the two marketplaces, `mcp/claude.json` and `.mcp.json` for the two MCP surfaces, and `bin/evaluate-launch` to resolve the separately installed binary and apply plugin defaults ([#2](https://github.com/racecraft-lab/typesafe-mcp/pull/2))
* **Bundles TypeSafe's agent skill, adapted.** Vendored from `typesafe-ai/skills` 0.5.7 under MIT with its licence and provenance kept. Two sections are added: one routing in-session judgments to the `evaluate` tool rather than to a written integration, and one on the OpenRouter string constraint. Upstream's text is otherwise unchanged. Install this instead of the official `typesafe` plugin, not alongside it: both ship a skill named `typesafe-ai` ([#2](https://github.com/racecraft-lab/typesafe-mcp/pull/2))

### Bug Fixes

* **The updater no longer falls back to upstream.** `githubRepo` names this fork only. A release source that silently resolved to the original project would replace this binary with one that has none of these changes ([#1](https://github.com/racecraft-lab/typesafe-mcp/pull/1))
* **Versions are compared, not merely differenced.** Upstream treated any two unequal version strings as "update available", so an older release replaced a newer local build. Pre-release identifiers now follow SemVer precedence, so `rc.10` sorts after `rc.2`, and a build carrying metadata such as `v0.4.0+dirty` refuses to self-update at all ([#1](https://github.com/racecraft-lab/typesafe-mcp/pull/1))
* **The installer keeps the binary off `PATH`.** It installs to `~/.local/libexec/racecraft-jev/evaluate` so it cannot collide with an upstream `evaluate` ([#1](https://github.com/racecraft-lab/typesafe-mcp/pull/1))
* **The HTTP client refuses redirects** and carries a single deadline across all retries, so a redirected request cannot carry the Authorization header to another host and a retry budget cannot outlive its timeout ([#1](https://github.com/racecraft-lab/typesafe-mcp/pull/1))
* **plugin:** wire releases to the plugin manifests, add the Codex marketplace ([#5](https://github.com/racecraft-lab/typesafe-mcp/pull/5)) ([0cf4339](https://github.com/racecraft-lab/typesafe-mcp/commit/0cf4339577911899b292a60e70138f57dc38c07f))

### Continuous Integration

* Tests on Linux and macOS, with the race detector, plus a cross-compile of all four release targets ([#1](https://github.com/racecraft-lab/typesafe-mcp/pull/1))
* A fork-provenance job fails the build on an upstream reference in code or packaging, so a release can never point an operator at the original project's binary ([#1](https://github.com/racecraft-lab/typesafe-mcp/pull/1))
* CodeQL, Dependabot, dependency review, secret-scanning push protection, and the OSS project files ([#3](https://github.com/racecraft-lab/typesafe-mcp/pull/3))
* Release publication is gated: the tagged tree is tested, four targets are built, and the draft's own assets are downloaded, checksummed and executed before anything is published ([#1](https://github.com/racecraft-lab/typesafe-mcp/pull/1))
* A PR title check enforces Conventional Commits, so a squash subject can no longer land work that Release Please ignores ([#5](https://github.com/racecraft-lab/typesafe-mcp/pull/5))

## [0.4.0](https://github.com/itsmostafa/typesafe-mcp/compare/v0.3.0...v0.4.0) (2026-09-18)


### ⚠ BREAKING CHANGES

* `jev` is now `evaluate`. Installed 0.3.x binaries look for a `jev-<os>-<arch>.tar.gz` asset, so `jev update` fails against this release and cannot self-update across the rename; reinstall with install.sh, then re-run `evaluate setup mcp`. `JEV_INSTALL_DIR` is no longer read, and `go install .../cmd/jev@latest` no longer resolves.
* `jev mcp setup` is now `jev setup mcp`.

### Features

* move mcp setup under jev setup and add jev setup pi ([6a74477](https://github.com/itsmostafa/typesafe-mcp/commit/6a7447759fa2dea329064d544e3b12b1a0521fb9))
* move mcp setup under jev setup and add jev setup pi ([8d276bb](https://github.com/itsmostafa/typesafe-mcp/commit/8d276bba83af5bcc2f12539d91d26ba405325663))
* rename the cli from jev to evaluate ([7e96633](https://github.com/itsmostafa/typesafe-mcp/commit/7e9663347b824968480c6fd37a9c01591a8cb7f4))
* **setup:** drop pre-rename jev registrations on setup ([111cf15](https://github.com/itsmostafa/typesafe-mcp/commit/111cf15550f2a0bfd4209112a69bf78ed7a1fce5))
* **tools:** sharpen the evaluate tool description ([7433a7f](https://github.com/itsmostafa/typesafe-mcp/commit/7433a7f06ed43b576c850d86d1904ca6c460bde2))


### Bug Fixes

* **setup:** harden the pi extension and setup command tree ([d199f83](https://github.com/itsmostafa/typesafe-mcp/commit/d199f83e12ae8acc1346c96b19fbbd2aa76e9559))
* **setup:** honor an absolute PI_CODING_AGENT_DIR without HOME ([f29bb7a](https://github.com/itsmostafa/typesafe-mcp/commit/f29bb7acd5f323afd2a261c38a4b0d4482d54909))

## [0.3.0](https://github.com/itsmostafa/typesafe-mcp/compare/v0.2.0...v0.3.0) (2026-09-18)


### Features

* **client:** run Jev through OpenRouter as well as the TypeSafe API ([12c1aaa](https://github.com/itsmostafa/typesafe-mcp/commit/12c1aaabcd614b65477f0110375c3e80600238aa))
* **client:** run Jev through OpenRouter as well as the TypeSafe API ([1c79b89](https://github.com/itsmostafa/typesafe-mcp/commit/1c79b89a36bd78a060e246f0e51d5645a5cf0728))

## [0.2.0](https://github.com/itsmostafa/typesafe-mcp/compare/v0.1.0...v0.2.0) (2026-09-17)


### Features

* **cli:** add jev update self-update ([75ebc49](https://github.com/itsmostafa/typesafe-mcp/commit/75ebc499c6ded4e75d9e1fd2a42b3e68fc134190))
* **cli:** add jev update self-update ([6d3d519](https://github.com/itsmostafa/typesafe-mcp/commit/6d3d5190f800081da26299db18b6b51b69f514b4))

## 0.1.0 (2026-09-17)


### Continuous Integration

* **release:** publish GitHub releases with release-please ([304328f](https://github.com/itsmostafa/typesafe-mcp/commit/304328fe1401ba7d259eb5f52c0ad7da168757a3))

## Changelog
