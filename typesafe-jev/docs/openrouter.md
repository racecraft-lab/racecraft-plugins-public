# Running Jev through OpenRouter

This server talks to one of two backends. Both take the same request shape:
`model`, `state`, and typed `questions`. Neither is a chat-completions
endpoint, and neither takes `messages`, `max_tokens`, or `stream`.

| `JEV_PROVIDER` | Endpoint | Credential | Default model | Billed by |
|---|---|---|---|---|
| unset or `typesafe` | `https://api.typesafe.ai/v1/systemone` | `TYPESAFE_API_KEY` | `jev-latest` | TypeSafe |
| `openrouter` | `https://openrouter.ai/api/alpha/decisions` | `OPENROUTER_API_KEY` | `~typesafe/jev-latest` | OpenRouter |

The default is TypeSafe. Selection is always explicit: which keys happen to be
present in the environment never decides where a request goes.

`~typesafe/jev-latest` is an alias. The leading tilde is part of the model id,
and an alias can resolve to a concrete model, so a successful response need not
repeat the alias you asked for. Check the `model` field in the response for what
actually ran.

`/api/alpha/` is an alpha path. It may move.

## What leaves your machine

Calling the `evaluate` tool sends the `state` and `questions` of that call to
the selected provider over HTTPS. Nothing else does: the server has no
background activity, no telemetry, and no logging of request contents.

The tool is annotated read-only, which means it changes nothing on your machine.
It does not mean the call is free or private. Each call is billed by the
selected provider, and a retry is billed again.

On the OpenRouter backend, two fixed attribution headers are sent:
`HTTP-Referer: https://github.com/racecraft-lab/racecraft-plugins-public` and
`X-OpenRouter-Title: Racecraft Jev MCP`. Neither is derived from your
filesystem paths or repository content.

Redirects are refused. An authenticated inference request is never forwarded to
a host that is not the configured endpoint.

## Credentials

The server reads exactly one credential, once, at startup. Rotating a key means
restarting the server, which for an MCP client means reconnecting it.

**With `JEV_API_KEY_FILE`**, the server reads that file and nothing else. An
unreadable or invalid file is fatal even when an environment key is present:
quietly using a different credential would bill an account you did not choose.

**Without it**, the server reads only the selected backend's own variable. An
OpenRouter process never falls back to `TYPESAFE_API_KEY`, or the reverse.

### Creating the key file

Use a dedicated inference key with a spending cap you have set, not a
management key.

```sh
mkdir -p -m 700 ~/.config/racecraft-jev
# Paste the key, then press ctrl-d. It stays out of your shell history,
# and out of the process arguments any other user can see.
cat > ~/.config/racecraft-jev/openrouter.key
chmod 600 ~/.config/racecraft-jev/openrouter.key
```

The file must be a regular file, at most 8 KiB, readable only by you. One
trailing newline is expected and ignored. Anything else, including surrounding
spaces or a second line, is rejected rather than silently trimmed into a
different credential.

This is a protected plaintext file, not an encrypted store. It is not committed,
and it should not be copied into a project folder.

### The environment-variable alternative

`OPENROUTER_API_KEY` in the client's environment works too. Prefer the key file:
a client launched from the desktop does not inherit your shell, so an exported
variable is often simply absent, and a key written into a client's JSON or TOML
config lands in a file with ordinary permissions and in every backup of it.

## Installing

Build or install the binary into its own directory, so it cannot collide with an
upstream `evaluate` on your `PATH`:

```sh
BIN="$HOME/.local/libexec/racecraft-jev/evaluate"
python3 plugin/scripts/install_evaluate.py    # the release that matches the plugin
"$BIN" version --verbose
```

`version --verbose` prints the version, the source repository, and the build
commit. It needs no network access and no credential, and it is how you confirm
you are looking at the Racecraft build rather than an upstream one.

Generate the client configuration. This command changes nothing:

```sh
JEV_PROVIDER=openrouter "$BIN" setup mcp \
  --client claude-code \
  --client codex \
  --key-file "$HOME/.config/racecraft-jev/openrouter.key"
```

Read the output, then run the commands yourself. They are reproduced below.

### Claude Code

Check the name is free first. If `jev-openrouter` already exists, inspect it and
stop rather than replacing something you did not put there.

```sh
claude mcp list
claude mcp get jev-openrouter    # expect "not found" on a first install
```

```sh
BIN="$HOME/.local/libexec/racecraft-jev/evaluate"
KEY_FILE="$HOME/.config/racecraft-jev/openrouter.key"

claude mcp add jev-openrouter \
  --scope user \
  --transport stdio \
  -e 'JEV_PROVIDER=openrouter' \
  -e 'JEV_MODEL=~typesafe/jev-latest' \
  -e 'JEV_REQUEST_TIMEOUT=45s' \
  -e "JEV_API_KEY_FILE=$KEY_FILE" \
  -- "$BIN" mcp

claude mcp get jev-openrouter
```

The quoting matters. `JEV_MODEL` begins with a tilde, which an unquoted shell
word expands to a home directory. `-e` is variadic, so each pair gets its own
flag and `--` closes the option list before the command.

Start a new Claude Code session and run `/mcp` to confirm the server and its
`evaluate` tool. A registered entry proves the client can launch the process. It
does not prove a provider call succeeds.

### Codex

```sh
codex mcp list
```

`codex mcp add` overwrites an existing entry of the same name without asking, so
check the list before reusing a name.

```sh
BIN="$HOME/.local/libexec/racecraft-jev/evaluate"
KEY_FILE="$HOME/.config/racecraft-jev/openrouter.key"

codex mcp add jev-openrouter \
  --env 'JEV_PROVIDER=openrouter' \
  --env 'JEV_MODEL=~typesafe/jev-latest' \
  --env 'JEV_REQUEST_TIMEOUT=45s' \
  --env "JEV_API_KEY_FILE=$KEY_FILE" \
  -- "$BIN" mcp

codex mcp list
```

The equivalent `~/.codex/config.toml` entry, with your own absolute paths. Add
only the keys you need to the existing table; do not append a duplicate one.

```toml
[mcp_servers.jev-openrouter]
command = "/path/to/your-home-directory/.local/libexec/racecraft-jev/evaluate"
args = ["mcp"]
startup_timeout_sec = 10
tool_timeout_sec = 75

[mcp_servers.jev-openrouter.env]
JEV_PROVIDER = "openrouter"
JEV_MODEL = "~typesafe/jev-latest"
JEV_API_KEY_FILE = "/path/to/your-home-directory/.config/racecraft-jev/openrouter.key"
JEV_REQUEST_TIMEOUT = "45s"
```

`tool_timeout_sec` should exceed `JEV_REQUEST_TIMEOUT`, or the client gives up
while the server is still within the budget it was given.

### Take the tool out of Codex's code mode

Codex routes MCP tools through code mode by default, and this one does not work
well there: the turn can end before the result comes back, and the tool may be
called several times when once was asked for. Add its namespace to
`~/.codex/config.toml`:

```toml
[features.code_mode]
direct_only_tool_namespaces = ["mcp__jev_openrouter"]
```

Note the underscore. Codex maps the hyphen in the server name `jev-openrouter`
to `_` in the tool namespace, so a name with a hyphen does not appear here
verbatim. If the file already has a `[features.code_mode]` table, add only the
one line to it rather than repeating the header, and keep any namespaces
already listed.

A plugin cannot set this. It is the operator's configuration.

Start a new Codex session and run `/mcp`.

### Neither client's own model changes

Attaching this server adds a tool. It does not touch `ANTHROPIC_BASE_URL`,
`ANTHROPIC_AUTH_TOKEN`, Codex's `model_provider`, or either client's login
state, and no new Anthropic or OpenAI credential is needed to use it. Claude
Code keeps talking to Anthropic and Codex keeps talking to OpenAI; only the
`evaluate` tool reaches OpenRouter.

## Verifying it works

Ask each client, in a new session:

> Call the `evaluate` tool from the `jev-openrouter` MCP server exactly once. Do
> not make the judgment yourself or substitute another model. Use this state: "A
> production checkout service is unavailable and customers cannot complete
> purchases." Ask three independent questions in one request: a `noul` for
> whether this describes a customer-impacting incident; a `choice` of billing,
> engineering, or sales for the responsible team; and a `score` over the ordered
> levels minor disruption, major disruption, service unavailable. Use string
> instructions and string criteria descriptions. Report the actual tool result,
> the resolved model, and any usage or cost fields. Say so if confidence or
> probabilities are absent; do not invent them.

Confirm the tool was actually invoked, rather than the assistant answering in
prose. All three answer ids should come back with matching types. Do not expect
particular probability values from a stochastic service, and do not expect the
returned model to equal the alias you asked for.

A `noul` answer carries no confidence field on either backend, by design. On
OpenRouter, `confidence` and `probabilities` are optional on choice and score
answers too, and may be absent where TypeSafe always sends them.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `no credential; set OPENROUTER_API_KEY` | No key file and no environment key, or an empty one | Create the key file and set `JEV_API_KEY_FILE` |
| `JEV_API_KEY_FILE ... is readable by group or others` | Permissions too open | `chmod 600` the file |
| `JEV_API_KEY_FILE ... does not exist` (ENOENT) | Relative path, or a path the client cannot see | Use an absolute path; a client launched from the desktop has a different working directory |
| `is an unexpanded ${...} placeholder` | A config template was copied without substitution | Put the real key in the file |
| `has leading or trailing whitespace` | A stray space or second line from a copy-paste | Rewrite the file with `cat >` and one trailing newline |
| `JEV_PROVIDER=... is not a known backend` | Misspelling | Use `typesafe` or `openrouter`; there is no fuzzy matching on purpose |
| Requests go to TypeSafe when you wanted OpenRouter | `JEV_PROVIDER` is unset, so the default applies | Set `JEV_PROVIDER=openrouter`; an `OPENROUTER_API_KEY` alone does not select it |
| `HTTP 401` | Wrong or revoked key for the selected backend | Check which backend you selected, then the key for it |
| `HTTP 402` | Out of credits, or the key's spending limit is reached | Add credits or raise the cap |
| `HTTP 403` | The key is valid but not permitted for this call; a management key cannot run inference | Use an inference key |
| `HTTP 404` | Could be the model id, could be the alpha endpoint moving | Check the model first; do not switch to chat completions |
| `HTTP 429`, `503`, `524`, or `529` | Rate limited, unavailable, upstream timeout, or overloaded | Retried automatically within the budget; retry later if it persists |
| A choice or score answer has no `confidence` or `probabilities` | Optional on OpenRouter; always sent by TypeSafe | Check the field is present before branching on it; do not substitute a default |
| `the next retry would not fit in the ... budget` | Retry-After exceeds the remaining timeout | Raise `JEV_REQUEST_TIMEOUT`, or retry later |
| The tool times out in Codex but the server looks fine | `tool_timeout_sec` is below `JEV_REQUEST_TIMEOUT` | Raise `tool_timeout_sec` |
| Two `evaluate` tools appear | An upstream install is also registered | They are separate servers; remove the one you do not want, or rename this one with `--name` |
| `evaluate update` refuses | This is a source build, or the latest release is not newer | Rebuild from the fork; an older release never replaces a newer build |

Do not work around any of these by disabling TLS verification, loosening file
permissions beyond `600`, or bypassing an organization policy.

## Rollback

Removing the server removes a tool. It does not affect either client's own
model or authentication, or any other MCP entry.

```sh
claude mcp remove jev-openrouter --scope user
codex mcp remove jev-openrouter
```

Confirm those against your installed clients' `--help` before running them, then
restart the affected sessions.

To remove the binary, delete `~/.local/libexec/racecraft-jev/evaluate`. When
upgrading instead, keep a copy of the working binary first: the installer
refuses to replace an existing file unless `EVALUATE_FORCE=1`.

Delete or revoke the API key only when you mean to. Other tools may use it.

## Maintenance

Re-check this integration when the provider contract changes. Fetch the
OpenRouter schema, compare it against [provider-contracts.md](provider-contracts.md),
and review any difference rather than rewriting payloads to match:

```sh
curl --fail --silent --show-error https://openrouter.ai/openapi.json \
  -o .artifacts/openrouter.openapi.json
shasum -a 256 .artifacts/openrouter.openapi.json
```

That check needs no credential. A changed hash is expected over time and means
"read the Decisions schemas again", not "something is broken".

When a provider call fails, the tool returns an error to the agent. It never
falls back to the other backend: sending the same state somewhere else, and
billing a second account, is a decision for the operator to make deliberately by
changing `JEV_PROVIDER`.
