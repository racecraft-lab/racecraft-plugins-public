# Upstream baseline and justified deviations

This fork is `racecraft-lab/typesafe-mcp`, forked from
`itsmostafa/typesafe-mcp`. It exists to run Jev through OpenRouter's Decisions
API from a local stdio MCP server, with the TypeSafe-direct backend kept intact.

## Base commits

| | Commit | Release | Date |
|---|---|---|---|
| Inspected during handoff preparation | `a3fe1783e3fe6a35f9823fd5c0d68ecc3d8b180b` | 0.2.0 | 2026-09-17 |
| **Actual implementation base** | `2137d0268badd5622243424fa7993a12f3330691` | **0.4.0** | 2026-09-18 |

The implementation plan was written against 0.2.0. Upstream published 16
commits after the inspection and before this work began. The fork is based on
current upstream `main`, not rolled back to the inspected revision.

Verify the base:

```bash
git log --oneline -1 2137d0268badd5622243424fa7993a12f3330691
git diff --stat a3fe1783e3fe6a35f9823fd5c0d68ecc3d8b180b 2137d0268badd5622243424fa7993a12f3330691
```

## What changed upstream between 0.2.0 and 0.4.0

Four of these changes alter what the plan asked for. They are listed first.

### 1. Upstream added an OpenRouter Decisions backend

`cmd/evaluate/main.go` now has a `route()` function that returns either the
TypeSafe endpoint or `https://openrouter.ai/api/alpha/decisions` with the
`~typesafe/jev-latest` model. The endpoint and model the plan specified are
therefore already present upstream.

**What is still missing, and is what this fork implements:** `route()` picks the
backend by *which API key happens to be set in the environment*, TypeSafe
first. That is exactly the selection rule the plan forbids — "never infer the
backend from which keys happen to be set" — because an `OPENROUTER_API_KEY`
left in a shell by an unrelated tool silently decides where a request goes, and
a TypeSafe key present for another purpose silently wins. This fork replaces it
with explicit `JEV_PROVIDER` selection.

See "Behaviour changes visible to an operator" below: this is a breaking change
against upstream 0.4.0, not an addition.

### 2. The CLI was renamed `jev` to `evaluate`

The command, the package directory (`cmd/jev` to `cmd/evaluate`), the archive
member, and the release asset names all changed. Upstream also carries cleanup
that removes a stale `jev` client entry left by pre-rename installs.

This fork **follows the rename** rather than reverting it, to keep divergence
from upstream as small as possible: `cmd/evaluate`, binary `evaluate`, assets
`evaluate-<goos>-<goarch>.tar.gz`.

Consequences for the plan's text, which was written in `jev` terms:

| Plan said | This fork uses |
|---|---|
| `cmd/jev/*.go` | `cmd/evaluate/*.go` |
| install `~/.local/libexec/racecraft-jev/jev` | `~/.local/libexec/racecraft-jev/evaluate` |
| isolate from an existing `jev` | isolate from an existing `jev` **and** from upstream's `~/.local/bin/evaluate` |

The `JEV_*` environment variable names are unchanged. They name the model
family, not the executable, and renaming them would churn the operator-facing
contract for no gain.

### 3. Upstream added a `pi` integration

`setup pi` writes a TypeScript extension into pi's config directory, and
`cmd/evaluate/pi.ts` is embedded in the binary. The plan predates this and says
nothing about it.

This fork **leaves `setup pi` alone**. Only `setup mcp` becomes the non-mutating
generator described in the plan. Rewriting an integration the plan never scoped
would be a change that does not trace to the request.

`runPiSetup` called `route()` for an advisory hint; it now calls the explicit
resolver and reports the same kind of hint.

### 4. Upstream's setup mutates more client state than the inspected version

Beyond copying `TYPESAFE_*` variables, 0.4.0's `setup mcp` removes and re-adds
the Claude Code entry, rewrites Claude Desktop's config file (which also holds
the user's preferences), captures `OPENROUTER_API_KEY` from the environment,
and deletes any server named `jev` from all three clients.

This fork replaces all of that with configuration generation. See
"Behaviour changes" below.

### Remaining upstream changes, with no effect on the plan

- `install.sh` and `Taskfile.yml` updated for the rename.
- `.github/workflows/release-please.yml` and the release manifest advanced to
  0.4.0; `release-please-config.json` gained `draft: true` and
  `force-tag-creation: true`.
- `README.md` documents both backends and the key-presence routing rule.
- `.gitignore` tracks the renamed binary.

## Behaviour changes visible to an operator

Each of these is a deliberate deviation from upstream 0.4.0. They belong in the
changelog and in the PR description.

### Backend selection is explicit

**Before:** the backend was whichever key was set, TypeSafe winning ties.

**After:** `JEV_PROVIDER` selects it. Unset means `typesafe`, preserving the
default for every existing TypeSafe user. An unknown or blank-after-trimming
value is a configuration error, not a silent fallback.

**Who this breaks:** an operator running upstream 0.4.0 with only
`OPENROUTER_API_KEY` set and no `JEV_PROVIDER`. They previously reached
OpenRouter; they now get a startup error naming the missing TypeSafe
credential. The error text tells them to set `JEV_PROVIDER=openrouter`.

This is the intended trade. Implicit routing means the destination of a request
— and the account billed for it — depends on unrelated environment state.

### A backend never falls back to the other backend's credential

An OpenRouter process reads only the OpenRouter credential, and a TypeSafe
process only the TypeSafe one. There is no implicit cross-provider fallback in
either direction. An operator can name one with `JEV_FALLBACK_PROVIDER`, and the
fallback then reads its own credential, never the primary's.

### `setup mcp` no longer edits client configuration

**Before:** it invoked `claude` and `codex`, rewrote Claude Desktop's config
file, baked every `TYPESAFE_*` variable plus `OPENROUTER_API_KEY` into the
generated entries, and deleted servers named `jev`.

**After:** it prints the commands and config snippets for the clients named with
`--client`, and changes nothing. It never runs a client CLI or a shell, never
touches a config file, and never puts a key value in its output — only the
key-file path.

**Why:** baking a secret into `~/.claude.json` or `~/.codex/config.toml` copies
it into a file with ordinary permissions, a backup, and possibly a dotfiles
repository. The remove-before-add path could also leave a client with no server
at all if the add failed. Generating commands keeps the operator in control of
their own configuration, which is the plan's requirement.

Automated merging with rollback can return in a later change. It is not needed
for the OpenRouter integration to work.

### Other changed defaults

| Setting | Upstream 0.4.0 | This fork |
|---|---|---|
| HTTP timeout | 60s per attempt, no overall bound | `JEV_REQUEST_TIMEOUT`, default 45s, covering all attempts and retry waits |
| Retries | fixed 3, on 429/529 for both backends | `JEV_MAX_RETRIES`, default 3, per-backend statuses |
| Redirects | followed | refused for authenticated requests |
| Model override | tool argument only | tool argument, then `JEV_MODEL`, then backend default |
| Credential source | environment only | `JEV_API_KEY_FILE` if set, else the selected backend's environment key |
| Updater version check | string equality | semantic version, upgrade only |
| Update/install source | `itsmostafa/typesafe-mcp` | `racecraft-lab/typesafe-mcp`, with no upstream fallback |

## What was deliberately not changed

- The single tool named `evaluate`, its argument names, and its annotations.
- Go, Cobra, the MCP Go SDK v1.7.0, and stdio transport.
- TypeSafe's accepted input shapes. Structured instructions and null criteria
  descriptions still work, and now work on the OpenRouter backend too, which
  republished its Decisions schemas to accept them.
- Upstream's tool guidance about question ids, batching, and what confidence
  means.
- `setup pi` and `cmd/evaluate/pi.ts`.
- The `go.mod` toolchain directive and pinned dependency versions.
- Upstream attribution, the LICENSE, and the historical changelog.
