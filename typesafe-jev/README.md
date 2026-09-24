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

This repository is both an MCP server and a plugin for Claude Code and Codex.
The plugin bundles the `evaluate` tool together with TypeSafe's agent skill,
adapted to use it: see [docs/plugin.md](docs/plugin.md). Install it **instead
of** the official `typesafe` plugin, not alongside it.

```sh
# Claude Code
claude plugin marketplace add racecraft-lab/typesafe-mcp --scope user
claude plugin install typesafe-jev@racecraft-typesafe --scope user

# Codex
codex plugin marketplace add racecraft-lab/typesafe-mcp
codex plugin add typesafe-jev@racecraft-typesafe
```

The binary is installed separately either way, by step 1 of the quickstart
below. The plugin carries a launcher, not four platform builds.

In Claude Code you can also invoke either skill by name:
`/typesafe-jev:typed-judgments` and `/typesafe-jev:typesafe-ai`.

### Other agents, via skills.sh

Both skills install into twenty-odd other agents with no plugin involved, the
same way upstream distributes its own:

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

**1. Install** (macOS and Linux, amd64 and arm64).

Fetch the installer, read it, then run it:

```sh
curl -fsSL -o install.sh \
  https://raw.githubusercontent.com/racecraft-lab/typesafe-mcp/main/install.sh
sh install.sh
```

It installs to `~/.local/libexec/racecraft-jev/evaluate`, deliberately **not** on your `PATH`, so it cannot collide with an upstream `evaluate` you may already have. Point clients at that absolute path. Building from source works too, into the same directory:

```sh
task install
```

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

Issues and pull requests are welcome. The repo uses [Task](https://taskfile.dev):

```sh
task check     # gofmt, go vet, and tests with -race
task inspect   # open the MCP Inspector against a local build
```

Upstream fixes are welcome too. Provider support is kept separate from this fork's branding and release changes so it can be offered upstream.
