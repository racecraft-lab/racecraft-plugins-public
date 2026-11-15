# Installing as a plugin

This directory is also a plugin for Claude Code and Codex, listed in the
Racecraft plugin marketplace. Installing it gives a client both halves at once:
the `evaluate` MCP tool, and TypeSafe's agent skill adapted to use it.

The alternative is [openrouter.md](openrouter.md), which registers the MCP
server by hand with no plugin involved. Both paths run the same binary. Use one.

## What is in the plugin

The payload lives in `plugin/`, and the two marketplace files at the repository
root point at it with the source `./typesafe-jev/plugin`. That separation is what
a client caches: everything outside `plugin/` (the Go source and the docs) stays
out of it. There is no generated payload: the directory is the whole plugin.

| Path | Purpose |
|---|---|
| `.claude-plugin/marketplace.json` (repository root) | Claude Code marketplace entry |
| `.agents/plugins/marketplace.json` (repository root) | Codex marketplace entry |
| `plugin/.claude-plugin/plugin.json` | Claude Code manifest |
| `plugin/.codex-plugin/plugin.json` | Codex manifest |
| `plugin/mcp/claude.json` | MCP entry for Claude Code |
| `plugin/.mcp.json` | MCP entry for Codex |
| `plugin/shared-skills/typesafe-ai/` | TypeSafe's skill, adapted, with its MIT licence |
| `plugin/shared-skills/typed-judgments/` | routes an in-session judgment to the tool |
| `plugin/scripts/evaluate_launch.py` | serves a no-tool stand-in when the binary is missing or on Windows; otherwise execs `evaluate mcp --plugin-defaults`, which handles a missing credential |
| `plugin/scripts/install_evaluate.py` | installs the release binary that matches the plugin |

Both manifests declare the same name and version, which a test enforces.

## One thing the plugin cannot carry

**The server binary is not in the plugin.** It is compiled Go, and committing
four platform builds to git would bloat every clone and still miss a fifth
platform. So the binary is installed once, separately, and `plugin/scripts/evaluate_launch.py`
finds it.

If the binary is missing, the launcher serves a stand-in MCP server with no
tools. Its instructions say how to install the binary and where the key file
goes. If the binary is there, the launcher replaces itself with
`evaluate mcp --plugin-defaults`, which does the same when no credential source
is configured at all. A user without a TypeSafe or OpenRouter key therefore sees
a connected server that explains itself rather than a failed one. Either way,
one line on stderr says so. Stdout carries only protocol frames, because a
human-readable line there is a frame the MCP client cannot parse.

The launcher never reads a key and starts no other process. A credential that
is configured but broken, such as a key file other users can read, is not
hidden behind the stand-in: the server refuses it and names the fix.
`evaluate call --check --plugin-defaults` gives the same verdict without
starting a server, as an exit code: 0 ready, 3 nothing configured, 4 broken.

Windows has no release build yet, so on Windows the launcher always serves the
stand-in.

## Install

**1. The binary**, once, from the plugin's own installer:

```sh
python3 plugin/scripts/install_evaluate.py
```

It installs the release that matches the plugin's version, tagged
`typesafe-jev-v<version>`, after checking it against the release's
`SHA256SUMS.txt`, and puts it at `~/.local/libexec/racecraft-jev/evaluate`.
Set `EVALUATE_BIN` if you keep it elsewhere. When the binary is missing, the
stand-in server's instructions give the installer's full path.

**2. The credential**, once. The plugin uses TypeSafe first and OpenRouter as
its fallback, each with its own key file. Either one is enough:

```sh
mkdir -p -m 700 ~/.config/racecraft-jev
cat > ~/.config/racecraft-jev/typesafe.key      # paste, then ctrl-d
chmod 600 ~/.config/racecraft-jev/typesafe.key
cat > ~/.config/racecraft-jev/openrouter.key    # the fallback
chmod 600 ~/.config/racecraft-jev/openrouter.key
```

The server runs with `--plugin-defaults`, which sets `JEV_API_KEY_FILE` to the
primary's file and `JEV_FALLBACK_API_KEY_FILE` to the fallback's, each only when
it is not already set **and the file exists**. An explicit value in the client's
environment still wins, and a key held only in `TYPESAFE_API_KEY` or
`OPENROUTER_API_KEY` is read when no key file is there. Through 0.8.0 the
launcher set both paths unconditionally, which stopped the server from reading
those variables at all. A missing TypeSafe key starts the server on OpenRouter;
a missing OpenRouter key leaves TypeSafe serving alone. No credential
is stored in any manifest, and a test checks for that.

**3. The plugin.** Each client reads its own marketplace file from the
racecraft-plugins-public repository, so the same source works for both.

Claude Code:

```sh
claude plugin marketplace add racecraft-lab/racecraft-plugins-public --scope user
claude plugin install typesafe-jev@racecraft-plugins-public --scope user
```

Codex, which has no scope flag because marketplaces are global under `~/.codex`:

```sh
codex plugin marketplace add racecraft-lab/racecraft-plugins-public
codex plugin add typesafe-jev@racecraft-plugins-public
```

Restart the client afterwards. Both commands track `main`. Releases are tagged
`typesafe-jev-vX.Y.Z`. The same marketplace also lists `speckit-pro`, which
releases on its own tags.

If you installed this plugin from the old `racecraft-typesafe` marketplace,
uninstall that copy and remove that marketplace first. Otherwise the client
runs two `jev` servers and loads two copies of each skill.

Claude Code and Codex both change these commands from time to time. Check
`claude plugin --help` and `codex plugin --help` if either is rejected.

## Replaces the official TypeSafe plugin

Install this **instead of** TypeSafe's `typesafe` plugin, not alongside it.

Both ship a skill named `typesafe-ai`, so installing both is a collision. More
importantly, upstream's skill teaches an agent to write SDK or HTTP code against
the TypeSafe API. That is right when building an application and wrong when a
judgment is needed in the current session and the tool is already connected. The
vendored copy adds a section that makes the distinction, and leaves the rest of
upstream's text alone.

Provenance is recorded in the file's own header: `typesafe-ai/skills`, plugin
version 0.6.2, MIT, with the licence kept beside it. A test asserts the licence,
the provenance, and that upstream's guidance survived the edit.

When TypeSafe publishes a new skill version, re-vendor it and re-apply the two
additions rather than editing around the old copy.

## Defaults the plugin sets

```json
"env": {
  "JEV_REQUEST_TIMEOUT": "45s"
}
```

The manifests leave backend and model selection to the binary, so they do not
mask the operator's chain file. Resolution order is:

1. `JEV_CHAIN`, a comma-separated list such as `openrouter,typesafe`.
2. The legacy `JEV_PROVIDER` / `JEV_FALLBACK_PROVIDER` pair. A provider alone
   selects one hop. An empty `JEV_FALLBACK_PROVIDER` is unset. Combining a
   configured legacy provider with `JEV_CHAIN` fails.
3. The comma-separated file `~/.config/racecraft-jev/chain`.
4. The built-in `typesafe,openrouter` under `--plugin-defaults`, which the
   plugin's launcher always passes. Without that flag, the built-in is
   `typesafe` alone. Both modes use `jev-latest` on TypeSafe.

A chain accepts at most four distinct registered providers, with no empty
entries. This layer registers `typesafe` and `openrouter`; Ollama remains for
later layers. A missing chain file uses the built-in order; an unreadable or
invalid file fails startup. Environment configuration wins without reading the
file. `evaluate call --plugin-defaults` and the MCP server resolve identically.
The chain file and `JEV_CHAIN` override the built-in chain in both modes, with
the same precedence. A bare binary uses a second backend only when the
operator names a chain; the plugin's launcher opts into TypeSafe then OpenRouter.
`evaluate setup mcp` prints client configuration using `JEV_CHAIN`.

Hop 1 keeps `JEV_API_KEY_FILE`; hop 2 keeps `JEV_FALLBACK_API_KEY_FILE`. With
`--plugin-defaults`, every hop also discovers
`~/.config/racecraft-jev/<provider>.key`, before its provider's environment key.
`--check` reports exit 4 on any unusable credential. The server instead drops
that hop with one log line and starts if any hop has a usable credential.
Setting `JEV_FALLBACK_API_KEY_FILE` without a configured second hop fails startup.
`JEV_MODEL` and the tool's `model` argument apply only to configured hop 1,
even if that hop is dropped. Every later hop uses its provider's default.

A failure with 401, 402, 403, 404, 429, 5xx or an unreachable destination moves
the session down one hop after that hop's retries. It never moves back until a
restart. Local refusal by the next hop still prevents a move (FB-08); capability
routing, account skipping and per-hop deadlines belong to later layers. The
backend note lists the loaded order and updates the tool description with the
serving hop after a move. Clients receive a tool-list change notification.
All hops share the one 45s budget, so the client's 75s abort still fits.

The Codex entry also sets `tool_timeout_sec: 75`, above the 45s request budget,
so the client does not give up while the server is still inside the time it was
given.

## Codex: take the tool out of code mode

Codex routes MCP tools through code mode by default, and this one does not work
well there. Add to `~/.codex/config.toml`, adding only the line if the table
already exists:

```toml
[features.code_mode]
direct_only_tool_namespaces = ["mcp__jev"]
```

The namespace follows the server name in `.mcp.json`, which is `jev` here. A
plugin cannot set this setting; it is the operator's own configuration.

## Rollback

Remove the plugin with your client's plugin command. That removes the tool and
the skill together, and touches neither client's own model nor its
authentication.

The binary and the key file are outside the plugin and survive it. Delete
`~/.local/libexec/racecraft-jev/evaluate` and the key file separately if you
want them gone, and revoke the key only when you mean to.
