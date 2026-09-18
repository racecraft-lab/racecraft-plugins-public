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

| Check | Status |
|---|---|
| LIVE-01: one authorized raw Decisions call | **NOT RUN** |
| LIVE-02: one authorized Claude Code batch | **NOT RUN** |
| LIVE-03: one authorized Codex batch | **NOT RUN** |
| Native Claude/Codex auth and model preserved | **NOT VERIFIED** by execution |

Blocker for all four: no OpenRouter credential was supplied, and none was
requested. The owner enters a key locally using the key-file workflow in
[openrouter.md](openrouter.md), and separately authorizes installation and any
billed call. No key was asked for in conversation and no policy was bypassed to
obtain one.

The native-authentication claim is a design property, not an executed check.
Nothing in this server reads or writes `ANTHROPIC_BASE_URL`,
`ANTHROPIC_AUTH_TOKEN`, Codex's `model_provider`, or either client's login
state; `setup mcp` writes no file at all. That is verifiable by reading the
diff, and `TestSetupMutatesNothing` proves the no-write part against a temporary
home. It has not been confirmed by running both clients.

**This integration is not production-verified.** It is review-ready with the
live checks explicitly outstanding.

## Client installation

| Check | Status |
|---|---|
| `claude mcp add --help` inspected (2.1.276) | done |
| `codex mcp add --help` inspected (0.154.0) | done |
| Server registered in the owner's Claude Code | **NOT RUN** |
| Server registered in the owner's Codex | **NOT RUN** |

Both clients' help output was read to confirm the generated commands match the
installed versions: Claude Code's `-e/--env` is variadic and its `--scope` and
`--transport` options exist as used; Codex takes `--env KEY=VALUE` before `--`
and the server name as a positional argument.

No real client configuration was changed. The owner runs the generated commands
when they choose to.

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

1. LIVE-01, LIVE-02, and LIVE-03 have not run.
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
