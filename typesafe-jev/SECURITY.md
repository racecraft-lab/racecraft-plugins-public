# Security policy

## Reporting a vulnerability

Report privately through GitHub's [private vulnerability
reporting](https://github.com/racecraft-lab/racecraft-plugins-public/security/advisories/new)
on this repository. Please do not open a public issue for a vulnerability.

Include what you did, what happened, and what you expected. A minimal
reproduction is worth more than a long description. **Never include a real API
key in a report**, even a revoked one; describe where it came from instead.

We acknowledge a report within 3 business days and aim to ship a fix within 90
days, sooner for severe issues. Timelines, updates, and credit follow the
repository's [disclosure process](../SECURITY.md#disclosure-process).

## Scope

This is a local stdio MCP server. It runs as a subprocess of your agent, with
your permissions, and talks only to the provider endpoints in its configured
backend chain.

In scope:

- A credential leaking anywhere it should not be: stdout, stderr, an error
  message, a tool result, generated configuration, or a crash dump.
- Request state reaching a host other than the configured endpoint.
- A response being presented as a valid judgment when it is not.
- The updater or installer fetching or executing something other than a
  verified release artifact of this repository.
- Key-file handling: permissions, symlinks, races between check and read.

Out of scope:

- The provider's own answers. A wrong or biased judgment is a model question,
  not a vulnerability.
- Anything requiring an attacker who can already write to your key file, your
  client configuration, or the installed binary. At that point they have your
  account.
- Cost. A large bill from calling the tool many times is a budgeting matter;
  set a spending cap on the key.
- Upstream `itsmostafa/typesafe-mcp`. Report that to its own maintainers, and
  if it also affects this fork, say so here too.

## What this tool does with your data

Calling `evaluate` sends the `state` and `questions` of that call to a
provider in the configured backend chain. Remote providers are reached over
HTTPS. The one exception is `ollama-local`, which sends them over plain HTTP to
`localhost:11434`, the signed-in Ollama daemon on your own machine, with no
credential. Any local process listening on that port receives them, so add
`ollama-local` to the chain only on a machine where you run that daemon.
Nothing else sends request contents. There is no telemetry, no
background activity, and no logging of request contents.

The tool is annotated read-only, meaning it changes nothing on your machine.
That is not a statement about privacy or cost.

Do not put a secret in `state` to have a judgment made about it.

## Credential handling

- Read once at startup, from `JEV_API_KEY_FILE` or the selected backend's own
  environment variable. There is no fallback between the two. A bare binary
  defaults to TypeSafe alone: a second backend is used only when the operator
  names a chain through `JEV_CHAIN`, the legacy provider pair, or the per-user
  chain file. The plugin's launcher opts into TypeSafe then OpenRouter with
  `--plugin-defaults`. `JEV_CHAIN` or the chain file overrides the built-in
  chain in both modes, with the same precedence. Each backend reads its own
  credential; hop 2 uses `JEV_FALLBACK_API_KEY_FILE` or its own environment
  variable, with key-file discovery also available under `--plugin-defaults`.
- The chain file is read only from an absolute home directory. If the home
  is empty or relative, no chain file is read and the mode's built-in chain
  applies unless environment configuration overrides it.
- A key file must be a regular file, at most 8 KiB, not readable by group or
  others. Empty values, control characters, surrounding whitespace, and
  unexpanded `${...}` placeholders are rejected rather than repaired.
- Credentials redact themselves when printed, so a stray `%v` cannot leak one.
- Protecting a plaintext file is not encryption. It keeps other local accounts
  out; it does not protect against someone who can read your home directory.

Use a dedicated inference key with a spending cap, not a management key.

## Supported versions

The default branch is supported. This project has no long-term support
branches, and a fix ships in the next release rather than being backported.
