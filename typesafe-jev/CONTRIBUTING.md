# Contributing

Thanks for looking. This is Racecraft Lab's fork of
[itsmostafa/typesafe-mcp](https://github.com/itsmostafa/typesafe-mcp), adding
explicit backend selection and an OpenRouter Decisions path.

**If your change is not specific to this fork, consider sending it upstream
first.** Provider support here is kept in commits separate from branding and
release changes precisely so it can be offered upstream. A fix that helps
everyone is better placed there.

## Getting set up

You need Go. The version is pinned in `go.mod`, and `GOTOOLCHAIN=auto` (the
default) will fetch it, so an older local Go is fine. Do not lower the
directive to match your machine.

```sh
git clone https://github.com/racecraft-lab/typesafe-mcp.git
cd typesafe-mcp
task check          # gofmt, go vet, and tests with -race
```

Without [Task](https://taskfile.dev):

```sh
go mod verify
test -z "$(gofmt -l .)"
go vet ./...
go test -count=1 ./...
go test -race -count=1 ./...
```

Everything runs offline. No test needs a credential, a network, or your real
configuration directory, and none should ever gain one.

## What a change should look like

**Tests inspect behaviour, not text.** A test that greps a README for a
promise proves nothing. Assert on the HTTP request that was made, the schema
the client receives, or the file that was written.

**Say why in the commit message, not what.** The diff shows what changed. The
message should explain the reasoning someone will need in a year: what went
wrong before, what you decided, and what you rejected.

**Be surgical.** Match the surrounding style. Don't reformat adjacent code or
fix unrelated things in the same change; mention them instead.

**Cite a source for provider behaviour.** Claims about what TypeSafe or
OpenRouter accept belong in `docs/provider-contracts.md` with a link and a
fetch date. Do not infer a contract from one observed response, and do not
guess at a versioned API.

**Keep the two backends honest.** Both accept structured instructions, and both
accept a null choice option description; OpenRouter reached that point later,
when it republished its Decisions schemas. Never narrow both to satisfy one,
and never leave a narrowing in place once the reason for it is gone — a rule
that outlives its source hides a capability the backend has. If you add a rule,
say whether it is the provider's requirement or this fork's policy.

## Things this project deliberately will not do

Proposals along these lines will be declined, so please ask before building
one:

- Infer the backend from which API keys happen to be set. That is what this
  fork exists to remove.
- Fall back to the other backend on its own. A fallback exists only when the
  operator names one with `JEV_FALLBACK_PROVIDER`; without it the error goes to
  the agent and the operator decides.
- Add an environment variable that points the server at an arbitrary URL.
  Tests inject endpoints through constructors instead.
- Make `setup mcp` edit client configuration again.
- Echo provider error bodies into tool errors. They can quote the submitted
  state back.
- Invent a confidence or probability that a provider did not return.

## Live tests

Tests that call a real provider are skipped unless `EVALUATE_LIVE=1`. They cost
real money. CI never sets it and has no credential.

```sh
EVALUATE_LIVE=1 JEV_PROVIDER=openrouter \
  JEV_API_KEY_FILE="$HOME/.config/racecraft-jev/openrouter.key" \
  go test -count=1 -run TestLive -v ./cmd/evaluate
```

Never commit a key, a real response containing one, or a `.artifacts/` file.
Secret scanning with push protection is enabled on this repository, but do not
rely on it to catch your mistake.

## Pull requests

Open it as a draft until CI is green. In the description, cover what changed
and why, anything that behaves differently than before, and what you actually
ran. If you could not run something, say so and mark it `NOT RUN` rather than
implying it passed.

CI runs on Linux and macOS. macOS is not redundant: the key-file permission
checks are filesystem behaviour.

## Reporting a vulnerability

Privately, please: see [SECURITY.md](SECURITY.md). Not in an issue.

## Licence

MIT, matching upstream. By contributing you agree your work ships under it.
Keep the existing copyright notices and upstream attribution intact.
