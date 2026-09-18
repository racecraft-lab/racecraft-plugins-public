# Verification report

What was actually run, on what, with what result. A check that did not run is
marked `NOT RUN`, never inferred from a related one that passed.

```text
Implementation commit:  4f156b454c41af059aa61eafaac8dc842e778b7a  (PR #1 head)
Upstream base commit:   2137d0268badd5622243424fa7993a12f3330691  (0.4.0)
Upstream commit the plan inspected:
                        a3fe1783e3fe6a35f9823fd5c0d68ecc3d8b180b  (0.2.0)
Branch:                 feat/openrouter-decisions
Repository:             racecraft-lab/typesafe-mcp
Date:                   2026-09-18
```

## Environment

| | |
|---|---|
| OS | macOS 27.0 (build 26A428), Darwin 27.0.0 |
| Architecture | arm64 |
| Go on the host | go1.26.5 darwin/arm64 |
| Go actually used | go1.27.1 darwin/arm64 |
| Claude Code | 2.1.276 |
| Codex CLI | codex-cli 0.154.0 |

The host toolchain is older than the `go 1.27.1` directive in `go.mod`.
`GOTOOLCHAIN=auto` downloaded and used 1.27.1, so the declared toolchain was
not lowered to suit the machine. CI pins the same way, with
`go-version-file: go.mod`.

## Baseline, before any change

Run against the unmodified fork at `2137d026`, with no provider credential:

| Command | Result |
|---|---|
| `go mod download` | PASS |
| `go mod verify` | PASS (all modules verified) |
| `go vet ./...` | PASS |
| `go test -count=1 ./...` | PASS |
| `go test -race -count=1 ./...` | PASS |
| `gofmt -l .` | PASS (no output) |
| `go build -o bin/evaluate-baseline ./cmd/evaluate` | PASS |
| `./bin/evaluate-baseline version` | `v0.4.0+dirty` |

The upstream suite was green before this work started, so a later failure is
attributable to this branch.

## Offline checks, at the implementation commit

| Command | Result |
|---|---|
| `go mod verify` | PASS |
| `gofmt -l .` | PASS (no output) |
| `go vet ./...` | PASS |
| `go test -count=1 ./...` | PASS |
| `go test -race -count=1 ./...` | PASS |
| `git diff --check` | PASS |
| `sh -n install.sh` | PASS |

57 top-level tests, 44 named subtests, all passing. Every one runs offline
against `httptest` servers, temporary directories, and fake keys. None reads a
real configuration directory, a real credential, or a provider endpoint.

| File | Tests | Covers |
|---|---|---|
| `config_test.go` | 11 | CFG-01 to CFG-07, KEY-01 to KEY-05 |
| `validation_test.go` | 13 | REQ-01 to REQ-08, RES-01 to RES-05 |
| `client_test.go` | 12 | HTTP-01 to HTTP-10, SEC-01 |
| `mcp_test.go` | 6 | MCP-01 to MCP-04, backend-aware instructions |
| `setup_test.go` | 7 | SET-01 to SET-04 |
| `update_test.go` | 3 | REL-01, REL-02 |
| `evaluate_test.go` | 5 | retained upstream regressions |

### Build targets

Cross-compiled with `CGO_ENABLED=0 go build -trimpath`:

| Target | Built | Runtime-tested |
|---|---|---|
| `darwin/arm64` | PASS | **yes**, locally and on CI `macos-latest` |
| `darwin/amd64` | PASS | NOT RUN (no amd64 macOS host available) |
| `linux/amd64` | PASS | **yes**, CI `ubuntu-latest` |
| `linux/arm64` | PASS | NOT RUN |

A successful cross-compile is not a runtime test. `linux/arm64` and
`darwin/amd64` are built but never executed.

## Manual smoke checks

Run against a local build, no credential and no network:

```text
$ ./bin/evaluate version
v0.4.1-0.20260918134145-0b9372ce3245+dirty

$ ./bin/evaluate version --verbose
version:    v0.4.1-0.20260918134145-0b9372ce3245+dirty
repository: racecraft-lab/typesafe-mcp
commit:     0b9372ce32459571f272ee99c1d0f7a4d222688b
```

The `+dirty` suffix is Go's VCS stamp for a build from a modified tree. The
updater refuses to replace such a build, which `TestDevelopmentBuildsHaveNoVersion`
also asserts.

`setup mcp --client claude-code --client codex --key-file ...` printed the
Claude Code commands, the Codex commands, and the equivalent TOML table, with
the key-file path present and no key value anywhere. Nothing was written.

`go run ./cmd/evaluate setup mcp ...` correctly refused, because a `go run`
binary is deleted on exit and would leave a client pointing at a path that no
longer exists.

## Provider contract

| | |
|---|---|
| Source | `https://openrouter.ai/openapi.json` |
| Fetched | 2026-09-18 |
| sha256 | `bea6d54d1204f94f33dd464a5541046b17744e118c2eff27e3268865fe65f201` |
| Size | 2 165 871 bytes |

Confirmed present: the `/api/alpha/decisions` path, and the `DecisionsRequest`,
`DecisionsResponse`, `DecisionsNoulQuestion`, `DecisionsChoiceQuestion`,
`DecisionsScoreQuestion`, `DecisionsNoulAnswer`, `DecisionsChoiceAnswer`, and
`DecisionsScoreAnswer` schemas.

TypeSafe's side was read from `docs.typesafe.ai`: the structure rules, the score
semantics, and the `SystemOneResponse` schema. Both are summarized field by
field, with sources, in [provider-contracts.md](provider-contracts.md).

This is documentation-level evidence of a contract. It is **not** proof that any
particular key can call the endpoint.

### Two corrections to the implementation plan, from the fetched schema

The plan said the OpenAPI document's declared `Retry-After` headers backed the
retry policy. The fetched document declares **no** `Retry-After` header on these
statuses. The header is still honoured when a response carries one, as correct
HTTP behaviour, but it is documented as this fork's policy rather than the
provider's contract.

The plan called for score criteria of "at least two levels" as though it were a
schema rule. `DecisionsScoreQuestion` sets no `minItems`. The two-level minimum
is this fork's local policy and is labelled as such.

## Live tests

Run 2026-09-18 against OpenRouter, with a key the owner placed in
`~/.config/racecraft-jev/openrouter.key` themselves. The key was never typed
into a conversation, passed as an argument, or printed.

| Check | Status |
|---|---|
| LIVE-01: one authorized raw Decisions call | **PASS** |
| LIVE-01b: the same batch through this server | **PASS** |
| LIVE-01c: the same batch through the launcher over real stdio | **PASS** |
| LIVE-02: one authorized Claude Code batch | **PASS** |
| LIVE-03: one authorized Codex batch | **PASS** |
| Native Claude/Codex auth and model preserved | **PASS** |

### LIVE-01: raw HTTPS call

`POST https://openrouter.ai/api/alpha/decisions` with the three-primitive
fixture, using `curl` and no project code, to establish that the contract and
the credential work independently of this implementation.

```text
HTTP 200
model:       typesafe/jev-1.13-20260917
usage:       input_tokens=512 output_tokens=79 cost=2.1504e-05
id:          gen-dec-1789741031-rPefX4WoAe6xW2Dv53wY
provider:    TypeSafe
answers:     customer_impact noul=0.99
             owner choice=engineering confidence=1
             disruption score=2 confidence=1 (+legend, +probabilities)
```

### LIVE-01b: through this server

`runEvaluate` with the real resolved config, so the credential, request
validation, transport, and response validation all took part.

```text
backend=openrouter endpoint=https://openrouter.ai/api/alpha/decisions
model=~typesafe/jev-latest credential=file ~/.config/racecraft-jev/openrouter.key
latency: 831ms   resolved model: typesafe/jev-1.13-20260917   cost: 2.1252e-05
```

A companion check confirmed the OpenRouter backend rejects structured
instructions locally, naming `questions.impact.instructions`, with no request
sent and nothing billed.

### LIVE-01c: through the launcher, over real stdio

The installed binary at `~/.local/libexec/racecraft-jev/evaluate`, launched by
`bin/evaluate-launch` exactly as a plugin-installed client would, driven by a
real MCP `CommandTransport`. `initialize`, `tools/list`, and `tools/call` all
succeeded over the protocol.

```text
latency over stdio: 611ms
resolved model:     typesafe/jev-1.13-20260917
usage:              input_tokens=480 output_tokens=78 cost=2.016e-05
```

The server's instructions arrived carrying the backend note, confirming an
agent sees which backend is configured and that only strings are accepted.

### Three design decisions the live runs confirmed

1. **The alias does not come back.** `~typesafe/jev-latest` resolved to
   `typesafe/jev-1.13-20260917` every time. Code that compared the returned
   model to the requested one would have failed.
2. **A score is not a probability.** Every run returned `score: 2` on a
   three-level scale. Clamping a score to 0-1, which the plan's response rules
   warned against, would have rejected a valid answer on the first live call.
3. **Zero is a real value.** `probabilities` came back with genuine zeros for
   the ruled-out options. Treating them as absent would have discarded them.

A `noul` answer carried no `confidence` field, as both schemas say it should
not. No value was invented to fill it.

### LIVE-02: Claude Code

Registered at user scope as `jev-openrouter` (the name was free; `claude mcp
list` was checked first), then driven with `claude -p` and the tool allowed.
`claude mcp get` reported **Connected**.

The client invoked the tool and returned the provider's JSON verbatim:

```text
resolved model: typesafe/jev-1.13-20260917
usage:          input_tokens=681 output_tokens=77 cost=2.8602e-05
answers:        customer_impact noul=0.98
                responsible_team choice=engineering confidence=1
                severity_level score=2 confidence=1
```

It reported unprompted that the `noul` answer carried no `confidence` and no
`probabilities`, rather than inventing either. That is the behaviour the tool
guidance is there to produce.

### LIVE-03: Codex

Registered as `jev-openrouter` and driven with `codex exec`.

```text
resolved model: typesafe/jev-1.13-20260917
usage:          input_tokens=404 output_tokens=71 cost=1.6968e-05
answers:        customer_impact noul=0.98
                owner choice=engineering confidence=1
                disruption score=2 confidence=1 (+legend)
```

Two client-side findings, neither a server defect:

**Codex needs the tool taken out of code mode.** On the first attempt Codex
emitted a well-formed call and the turn ended before the result came back, and
it called the tool three times rather than once. Adding this server's namespace
to `direct_only_tool_namespaces` fixed it:

```toml
[features.code_mode]
direct_only_tool_namespaces = ["mcp__jev_openrouter"]
```

Note the underscore: Codex maps the hyphen in `jev-openrouter` to `_` in the
tool namespace. A plugin cannot set this; it is the operator's config.

**Validation was confirmed through a real client.** Before that fix, Codex sent
a `noul` question whose criteria used `yes`/`no` keys. The server rejected it
with `questions.customer_impacting_incident.criteria.true is required when
criteria is given` and sent nothing to the provider. The field path was enough
for the client to diagnose it without help.

### Native authentication and model preserved

Both client configurations were backed up first and compared afterwards.

**Claude Code** (`~/.claude.json`): the only change under my control is one
added key, `mcpServers["jev-openrouter"]`. No existing server was modified or
removed. `oauthAccount`, `userID`, `primaryApiKey`, and
`customApiKeyResponses` are byte-identical. Claude Code continued answering
from its own Anthropic session throughout, with no new credential.

**Codex** (`~/.codex/config.toml`): a semantic comparison of all keys shows
279 after versus 272 before, with the seven additions all under
`mcp_servers.jev-openrouter`, and **no changed values** anywhere else. Codex
kept using its own OpenAI authentication.

One incidental change to report: `codex mcp add` rewrites the whole file
through its own TOML serializer. That reordered keys, rendered
`startup_timeout_sec = 120` as `120.0`, and dropped one empty array,
`mcp_servers.node_repl.args = []`. The values are equivalent and nothing else
was lost, but it is a side effect of the client's own command, not of this
server, and it is a reason to keep a backup before running it.

### Rollback, verified available

```sh
claude mcp remove jev-openrouter --scope user
codex mcp remove jev-openrouter
```

Total spend across all five live runs: roughly **$0.00011**.

The native-authentication claim now rests on a design property *and* an
executed check. Nothing in this server reads or writes `ANTHROPIC_BASE_URL`,
`ANTHROPIC_AUTH_TOKEN`, Codex's `model_provider`, or either client's login
state, and `setup mcp` writes no file at all; that is visible in the diff, and
`TestSetupMutatesNothing` proves the no-write part against a temporary home.
The configuration comparisons above confirm it in practice: after registering
and using the server in both clients, Claude Code's auth fields were
byte-identical and Codex's configuration had no changed values outside the new
entry.

What that still does not establish is durability. Each client made one
successful call. That is evidence the path works, not that it keeps working
across upgrades of either client.

**The integration is verified end to end on this machine**, from the resolved
configuration through the credential, transport, and both validation passes, to
a real answer returned inside both native clients, with their own
authentication and models untouched.

What that does **not** cover: Linux and `darwin/amd64` at runtime, the release
pipeline, and sustained use. One successful call in each client is evidence the
path works, not evidence it is reliable.

## Client installation

| Check | Status |
|---|---|
| `claude mcp add --help` inspected (2.1.276) | done |
| `codex mcp add --help` inspected (0.154.0) | done |
| Server registered in the owner's Claude Code | done, with the owner's approval |
| Server registered in the owner's Codex | done, with the owner's approval |

Both clients' help output was read to confirm the generated commands match the
installed versions: Claude Code's `-e/--env` is variadic and its `--scope` and
`--transport` options exist as used; Codex takes `--env KEY=VALUE` before `--`
and the server name as a positional argument.

The generated commands were run with the owner's explicit approval after the
exact commands and their rollback were shown. Both configurations were backed
up first.

## Continuous integration

| | |
|---|---|
| Run | `35353510787` |
| Result | **success** |
| Jobs | `test (ubuntu-latest)`, `test (macos-latest)`, `cross-compile`, `fork provenance` |

The first run on this PR (`35353280213`) failed one job. Both test jobs and the
cross-compile passed; the `fork provenance` job failed on itself, because it
greps for the upstream path and therefore contains it. Fixed in `4f156b4` by
moving the pattern to an environment variable and excluding the workflow file,
and the rerun is green.

Worth recording as evidence that the check works: it caught a real match on its
first execution, even though the match was its own text.

## Release readiness

| Control | Status |
|---|---|
| Fork created, ancestry verified | done (`racecraft-lab/typesafe-mcp`, parent `itsmostafa/typesafe-mcp`) |
| `gh workflow disable release-please.yml` | **could not run**: the workflow is not registered on the fork's default branch yet, so GitHub returned 404 |
| `RELEASE_ENABLED` repository variable | **not set**, which is what keeps the pipeline off |
| `release` environment with required reviewers | **not configured**; the owner must add it |
| Publication ordering fixed | done: test the tag, build, verify the draft's own assets, then publish |
| Tag or release created | **no**, and none should be until the checks below pass |

Actions are enabled on the fork, but the release workflow only triggers on a
push to `main`, and this work is a branch and a draft PR. The code-level gate is
what actually holds: with `RELEASE_ENABLED` unset, every job in the release
workflow is skipped.

### Outstanding release blockers

1. ~~LIVE-01, LIVE-02, and LIVE-03 have not run.~~ All pass; see above.
2. `RELEASE_ENABLED` and the protected `release` environment are not configured.
3. The new pre-publication asset gate has never executed, because no release has
   been attempted. It is code that has not run.
4. The fork inherits a release-please manifest at `0.4.0`. The first Racecraft
   version is the maintainer's choice and has not been made.
5. ~~Linux and macOS CI have not run yet.~~ Done: run `35353510787` is green on both.

## How to reproduce

```sh
git clone https://github.com/racecraft-lab/typesafe-mcp.git
cd typesafe-mcp
git switch feat/openrouter-decisions

go mod verify
test -z "$(gofmt -l .)"
go vet ./...
go test -count=1 ./...
go test -race -count=1 ./...
sh -n install.sh

go build -trimpath -o bin/evaluate ./cmd/evaluate
./bin/evaluate version --verbose
JEV_PROVIDER=openrouter ./bin/evaluate setup mcp --client claude-code
```

None of it needs a credential or a provider endpoint.
