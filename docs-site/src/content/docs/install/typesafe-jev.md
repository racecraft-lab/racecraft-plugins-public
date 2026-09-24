---
title: "Install: TypeSafe Jev"
description: "Install the typesafe-jev plugin in Claude Code or Codex, install its evaluate binary, add an optional TypeSafe or OpenRouter key, and roll back."
---

Use this route to install the `typesafe-jev` plugin, which adds one MCP tool,
`evaluate`, and two skills. The tool asks TypeSafe's Jev model for typed
judgments with probabilities: `noul`, `choice`, and `score` answers instead of
prose.

## What You Need

- The plugin, from this marketplace.
- The `evaluate` binary, installed once, separately. The plugin carries a
  launcher, not platform builds. Release builds exist for macOS and Linux on
  amd64 and arm64. Windows has none yet.
- Python 3.11 or newer on `PATH` as `python3`, which runs the launcher and the
  installer.
- Optionally, a TypeSafe or OpenRouter API key. Without one, the plugin still
  connects: its server offers no tools and its instructions say how to add a
  key. Each call with a key sends the state and questions you pass to that
  provider, which bills for the call.

## Install The Plugin

Claude Code:

```text
/plugin marketplace add racecraft-lab/racecraft-plugins-public
/plugin install typesafe-jev@racecraft-plugins-public
/reload-plugins
```

Codex reads `.agents/plugins/marketplace.json` from this repository. Open the
repository in Codex, open `/plugins`, and add `typesafe-jev`.

The marketplace installs the plugin from `typesafe-jev/plugin/`. There is no
generated payload for it: that directory is the whole plugin.

## Install The Binary

Run the plugin's installer once. From a checkout of this repository:

```text
python3 typesafe-jev/plugin/scripts/install_evaluate.py
```

The installer downloads the release tagged `typesafe-jev-v<version>` that
matches the plugin's version, checks it against the release's
`SHA256SUMS.txt`, and installs it to `~/.local/libexec/racecraft-jev/evaluate`.
That path is deliberately not on `PATH`. Pass `--force` to replace an existing
binary, and `--version` to pick another release. When the binary is missing,
the plugin's MCP server says so in its instructions and names the installer's
full path.

## Add A Key (Optional)

The plugin uses TypeSafe first and OpenRouter as its fallback, each with its
own key file. Either one is enough. Put the key in a file only you can read:

```text
mkdir -p ~/.config/racecraft-jev
chmod 700 ~/.config/racecraft-jev
touch ~/.config/racecraft-jev/typesafe.key
chmod 600 ~/.config/racecraft-jev/typesafe.key
```

Paste the key into `typesafe.key` with an editor. Use `openrouter.key` the same
way for an OpenRouter key. A key file that other users can read is refused, and
the server names the fix. Reconnect the `jev` MCP server afterwards.

A key held only in `TYPESAFE_API_KEY` or `OPENROUTER_API_KEY` also works, but
only when the agent's MCP process inherits that variable. A desktop-launched
client usually does not, so prefer the key file.

To check the setup without a network call:

```text
~/.local/libexec/racecraft-jev/evaluate call --check --plugin-defaults
```

It exits 0 when a key is ready, 3 when none is configured, and 4 when a
configured key cannot be used.

## Moving From The Old Marketplace

Earlier releases came from the `racecraft-typesafe` marketplace. Uninstall that
copy first, or you get two `jev` servers and two sets of skills:

```text
/plugin uninstall typesafe-jev@racecraft-typesafe
/plugin marketplace remove racecraft-typesafe
```

The binary path and the key files do not change. A 0.8.0 binary is too old for
this plugin's launcher, so run the installer with `--force` once.

## Roll Back

Uninstall the plugin from the client's plugin UI or CLI. The binary and the key
files live outside the plugin and survive it. Delete
`~/.local/libexec/racecraft-jev/evaluate` and the key files separately if you no
longer want them.

For the tool's reference, the backends, and the settings, see the
[typesafe-jev README](https://github.com/racecraft-lab/racecraft-plugins-public/blob/main/typesafe-jev/README.md).
