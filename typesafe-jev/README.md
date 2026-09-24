# Typesafe MCP (Racecraft Lab fork)

**Give your AI agent typed evaluations instead of free text.** `evaluate` is an MCP server that lets Claude Code, Codex, and [pi](https://pi.dev) call [TypeSafe](https://typesafe.ai)'s Jev model and get back probabilities they can branch on.

This is Racecraft Lab's fork of [itsmostafa/typesafe-mcp](https://github.com/itsmostafa/typesafe-mcp). It adds explicit backend selection, a private key-file workflow, per-backend request validation, and a setup command that generates configuration instead of applying it. [docs/upstream-baseline.md](docs/upstream-baseline.md) records every difference and why.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

```
┌──────────────┐  evaluate   ┌──────────┐  POST /v1/systemone  ┌──────────────┐
│ Claude Code  │ ──────────▶ │ evaluate │ ───────────────────▶ │ TypeSafe API │
│ Codex        │   (stdio)   │  (MCP)   │                      │  ── or ──    │
│ pi           │ ◀────────── │          │ ◀─────────────────── │  OpenRouter  │
└──────────────┘ typed JSON  └──────────┘   POST /decisions    └──────────────┘
                                  ▲
                            JEV_PROVIDER picks one
```

## Why this exists

**Problem:** When an agent needs a yes/no call, a routing decision, or a severity rating, it usually asks an LLM, then parses prose and hopes the format holds. The answer has no probability attached, so the agent cannot tell a confident "yes" from a coin flip.

**Solution:** `evaluate` exposes one tool, `evaluate`, that sends state plus typed questions to Jev and returns structured answers with probabilities. Nothing to parse and no prompt formatting to maintain.

## Install as a plugin, or by hand

This directory is both an MCP server and a plugin for Claude Code and Codex,
listed in the [Racecraft plugin marketplace](../README.md). The plugin bundles
the `evaluate` tool together with TypeSafe's agent skill, adapted to use it: see
[docs/plugin.md](docs/plugin.md). Install it **instead of** the official
`typesafe` plugin, not alongside it.

```sh
# Claude Code
claude plugin marketplace add racecraft-lab/racecraft-plugins-public --scope user
claude plugin install typesafe-jev@racecraft-plugins-public --scope user

# Codex
codex plugin marketplace add racecraft-lab/racecraft-plugins-public
codex plugin add typesafe-jev@racecraft-plugins-public
```

Installed it from the old `racecraft-typesafe` marketplace? Uninstall that copy
and remove that marketplace first, or the client runs two `jev` servers. The
binary path and the key files do not change.

The binary is installed separately either way, by step 1 of the quickstart
below. The plugin carries a launcher, not four platform builds. Until the binary
and a key are in place, the plugin's server connects with no tools and says
what is missing.

In Claude Code you can also invoke either skill by name:
`/typesafe-jev:typed-judgments` and `/typesafe-jev:typesafe-ai`.

### Other agents, via skills.sh

Both skills install into twenty-odd other agents with no plugin involved, the
same way upstream distributes its own. This path reads the archived standalone
repository, so its skills stay at the version it last released:

```sh
skills add racecraft-lab/typesafe-mcp          # run through npx
skills add racecraft-lab/typesafe-mcp --skill typed-judgments
```

**That path carries the skills only.** There is no MCP server and so no
`evaluate` tool. Both skills mention that tool, so both say to check it exists
before relying on it and to make the judgment normally when it does not. What
they are still worth installing for is the part that needs no tool: designing
the questions, and building a TypeSafe integration in your own code. For
judgments inside a session, install the plugin instead.

The by-hand path below registers the same server with no plugin involved. Use
one or the other.

## Quickstart

**1. Install** (macOS and Linux, amd64 and arm64; Windows has no release build yet).

The installer is a Python script in the plugin, at `plugin/scripts/install_evaluate.py`. Read it, then run it from a checkout of this repository, or from the installed plugin's directory:

```sh
python3 plugin/scripts/install_evaluate.py
```

It downloads the release tagged `typesafe-jev-v<version>` for this machine, checks it against that release's `SHA256SUMS.txt`, and installs it to `~/.local/libexec/racecraft-jev/evaluate`. By default it installs the plugin's own version, so the binary matches the launcher; `--version 0.9.0` picks another, and `--force` replaces an existing binary. It never asks GitHub for the "latest" release, because this repository releases more than one component. The path is deliberately **not** on your `PATH`, so it cannot collide with an upstream `evaluate` you may already have. Point clients at that absolute path. Building from source works too, into the same directory:

```sh
go build -trimpath -o ~/.local/libexec/racecraft-jev/evaluate ./cmd/evaluate
```

`evaluate update` later moves an installed release to the newest `typesafe-jev-v*` release, and ignores every other component's releases.

**2. Choose a backend.** Selection is explicit. Which API keys happen to be set never decides where your state is sent or which account is billed.

| `JEV_PROVIDER` | Endpoint | Key variable | Default model |
|---|---|---|---|
| unset or `typesafe` | `https://api.typesafe.ai/v1/systemone` | `TYPESAFE_API_KEY` | `jev-latest` |
| `openrouter` | `https://openrouter.ai/api/alpha/decisions` | `OPENROUTER_API_KEY` | `~typesafe/jev-latest` |

Get a TypeSafe key at <https://console.typesafe.ai/>, or an OpenRouter key at <https://openrouter.ai/keys>. OpenRouter's Decisions endpoint is on its `/api/alpha/` path and may move.

**3. Put the key in a private file.** This is preferred over an environment variable, which a client launched from the desktop does not inherit from your shell:

```sh
mkdir -p -m 700 ~/.config/racecraft-jev
# Paste the key, then press ctrl-d. It stays out of your shell history.
cat > ~/.config/racecraft-jev/openrouter.key
chmod 600 ~/.config/racecraft-jev/openrouter.key
```

The server rejects a key file that is readable by group or others, larger than 8 KiB, empty, or still holding a `${...}` placeholder.

**4. Generate the client configuration.** This prints commands and changes nothing:

```sh
JEV_PROVIDER=openrouter ~/.local/libexec/racecraft-jev/evaluate setup mcp \
  --client claude-code \
  --client codex \
  --key-file "$HOME/.config/racecraft-jev/openrouter.key"
```

Review the output, then run the commands yourself. Full instructions, including rollback, are in [docs/openrouter.md](docs/openrouter.md).

Using [pi](https://pi.dev)? It has no MCP client, so `evaluate` ships a pi extension instead. Unlike `setup mcp`, this one does write a file:

```sh
evaluate setup pi
```

That writes `~/.pi/agent/extensions/evaluate.ts`, which registers `evaluate` as a native pi tool and talks to `evaluate mcp` for you. Run `/reload` in pi to pick it up. Nothing is baked into the file: the extension reads your key from the shell pi runs in.

**5. Ask your agent a judgment question**

> "Use evaluate to decide whether this ticket is urgent and which team should own it: *Help! My payouts have been failing for 3 days.*"

The agent calls `evaluate` with:

```json
{
  "state": "Help! My payouts have been failing for 3 days.",
  "questions": {
    "is_urgent": {"type": "noul", "instructions": "Does this convey urgency?"},
    "department": {"type": "choice", "instructions": "Which team should handle this?",
      "criteria": {"billing": "Payments, refunds", "technical": "Bugs, outages", "sales": "Pricing"}}
  }
}
```

It gets back the raw response JSON, with each answer under the same id you gave it.

## What you get

- **Setup that changes nothing.** `evaluate setup mcp` prints the commands and config for the clients you name. It never runs a client CLI, edits a config file, or reads your key: only the key-file *path* appears in its output, never a value.
- **Explicit backends.** `JEV_PROVIDER` selects TypeSafe or OpenRouter, and each backend reads only its own credential. An `OPENROUTER_API_KEY` left in a shell by another tool cannot silently reroute and re-bill your setup.
- **Answers your code can branch on.** Three question types: `noul` (probability a condition holds), `choice` (one option from a map), `score` (position on ordered levels).
- **Both backends at full capability.** Structured instructions and criteria, and null option descriptions, work on TypeSafe and OpenRouter alike. Validation is per backend rather than a shared lowest common denominator, so neither is narrowed to suit the other, and a request a backend would reject fails locally before it costs anything.
- **Rate limits handled honestly.** Each backend retries only the statuses it documents as transient, `Retry-After` is honoured as a minimum wait, and retry waits come out of the same timeout as the attempts. Authentication, credit, and validation failures are never replayed.
- **Several questions, one call.** Batch independent questions over the same state; they run in parallel.
- **Agents that use it well out of the box.** The server ships usage guidance (narrow questions, JSON state, no-match options) to the client, so the agent writes better questions without extra prompting.
- **A single static binary.** No runtime, no Node, no Python. Redirects are refused, the request timeout defaults to 45s across all attempts, and request and response bodies are capped at 16 MiB.

## About TypeSafe

[TypeSafe](https://typesafe.ai) builds System One models: small units of AI intelligence you use like programming primitives. Instead of generating text, they turn natural language and application state into typed judgments and probabilities that code can combine. Jev is one of them.

[Website](https://typesafe.ai) · [Docs](https://docs.typesafe.ai) · [API reference](https://docs.typesafe.ai/api) · [Console](https://console.typesafe.ai/)

## Reference

### `evaluate`

| Field | Required | Description |
|---|---|---|
| `state` | yes | Content to judge: plain text, or a JSON object/array with named fields |
| `questions` | yes | Map of question id to `{type, instructions, criteria?}` |
| `model` | no | The call's model, then `JEV_MODEL`, then the backend default. Passed through exactly as given |

Criteria by type: `noul` takes optional `{"true": ..., "false": ...}` descriptions; `choice` requires a map of option to description; `score` requires an ordered array of at least 2 levels.

**Both backends accept the same values.** TypeSafe accepts a string, object, array, or null for instructions and for every criteria description. OpenRouter's Decisions schema accepts a string, object, or array for all of them, and null for choice option descriptions — the one shape it does not take is a null where this server requires a value anyway. OpenRouter typed these fields as plain strings until it republished the schema; nothing here narrows them any more. [docs/provider-contracts.md](docs/provider-contracts.md) has the field-by-field comparison with a source for each row.

### `evaluate call`

A one-shot form of the same tool, for a program rather than an agent. It reads
one request, `{"state": ..., "questions": {...}, "model": "..."}`, from stdin
(at most 16 MiB), runs it through the same path as the MCP tool, fallback and
both validations included, and writes the provider's JSON to stdout. Stderr
carries a diagnostic that never includes a key or the request.

`evaluate call --check` loads the configuration and credentials, makes no
network call, and prints the value-free state of each credential source as
JSON: where it comes from (`explicit-file`, `default-file`, `environment`, or
`none`) and whether it is `ok`, `absent`, or `unusable`.

`--plugin-defaults` (on `call` and `mcp`) points each unset key-file variable at
`~/.config/racecraft-jev/<provider>.key`, only when that file exists.

| Exit | Meaning |
|---|---|
| 0 | Answered, and the response passed validation |
| 2 | Request rejected locally: its shape, the 255-option cap, or the context budget |
| 3 | No credential source configured for the primary or the fallback |
| 4 | A credential source is configured but unusable, including an explicit key-file path whose file is absent, or the configuration itself is invalid |
| 5 | Provider or transport error, or timeout, after the client's own retries |
| 6 | The response failed validation |

A broken source is exit 4 even when the other backend's key works: a key file
you set up is never passed over silently. The MCP server is more forgiving in
that one case. It drops the broken fallback with a line on stderr and serves
the primary.

### Settings

| Variable | Default | Meaning |
|---|---|---|
| `JEV_PROVIDER` | `typesafe` | Which backend to use |
| `JEV_MODEL` | backend default | Model id, passed through unchanged |
| `JEV_API_KEY_FILE` | unset | Absolute path to a private key file; wins over the environment key |
| `JEV_REQUEST_TIMEOUT` | `45s` | Bounds the whole evaluation, retry waits included |
| `JEV_MAX_RETRIES` | `3` | Additional attempts, 0 to 5 |
| `JEV_FALLBACK_PROVIDER` | unset | Opt-in second backend, used when the primary refuses its credential (401, 402, 403), is not found (404), throttles (429), fails (5xx) or cannot be reached. The session then stays on it. Never used for a request the primary rejected by shape |
| `JEV_FALLBACK_API_KEY_FILE` | unset | The fallback's key file, by the same rules as `JEV_API_KEY_FILE` |

An invalid value for any of these is a startup error, not a silent fallback.

### Using the official TypeSafe skill alongside this server

TypeSafe publishes an agent skill (`typesafe-ai`) that teaches an agent the System One programming model: how to pick a primitive, structure state, and compose judgments. It is documentation, not a server, and it bundles no MCP configuration, so the two work together with nothing to reconcile.

They divide cleanly. The skill is for **designing** judgments, and for writing an application that calls TypeSafe from your own code. This server is for **making** a judgment during a session, without the agent writing an integration first.

The structured instructions and criteria the skill teaches now work on **both** backends. OpenRouter's Decisions schema typed those fields as plain strings until it republished them as string, object, or array, so nothing needs reconciling and no backend has to be selected to use the form the skill describes.

One asymmetry is still worth knowing, and it is in the reply rather than the request: OpenRouter marks `confidence` and `probabilities` optional on choice and score answers, where TypeSafe always sends them. The server says so in its instructions at connect time. An absent field is reported absent and never filled in with a plausible number, so branch on it only after checking it is there.

### Manual client config

Skip `evaluate setup mcp` and point your client at the absolute path of `evaluate mcp`, with `JEV_PROVIDER` and either `JEV_API_KEY_FILE` or the backend's key variable in its environment. [docs/openrouter.md](docs/openrouter.md) has worked examples for both clients, and rollback for each.

For pi, `evaluate setup pi` writes into `~/.pi/agent/extensions/` (or `$PI_CODING_AGENT_DIR/extensions/`), which pi discovers with no settings change. To install by hand, copy `cmd/evaluate/pi.ts` there as `evaluate.ts` and replace `__EVALUATE_BINARY__` with the quoted absolute path to your `evaluate` binary and `__EVALUATE_INSTRUCTIONS__` with a quoted guidance string.

## Contributing

Issues and pull requests are welcome, in the
[racecraft-plugins-public](https://github.com/racecraft-lab/racecraft-plugins-public)
repository. From its root, the same checks CI runs:

```sh
python3 scripts/check-go-module.py check   # module checksums, gofmt, vet, tests with -race, cross-compile
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the rules a change follows.

Upstream fixes are welcome too. Provider support is kept separate from this fork's branding and release changes so it can be offered upstream.
