# Canary subscription auth on self-hosted runners: research findings

> Status: research complete. Resolves
> [#1035](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1035)
> for the canary design in
> [#1028](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1028)
> (map [#1006](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1006)).
> Sources read on 2026-10-02. Doc pages are unversioned, so each doc citation
> describes the page on that date. Source code is pinned to a commit.
> No live login was run, no real credential file was read, and the runner host
> was not touched.

## Answer

Both hosts can run on the owner's subscription, but not the same way.

- **Claude Code: feasible and simple.** `claude setup-token` mints a one-year,
  inference-only OAuth token. Each VM gets it as `CLAUDE_CODE_OAUTH_TOKEN`. The
  client never refreshes or rewrites it, so five parallel jobs can share one
  token with no rotation race. Anthropic documents this exact use in GitHub
  Actions.
- **Codex: feasible, with a stateful round trip.** No static subscription token
  exists for personal ChatGPT plans. The only path is to seed `auth.json` from a
  trusted `codex login` and restore it on each VM. Codex refresh tokens are
  single-use, so concurrent refreshes from five copies can break the login. The
  run needs one job that owns refresh and writes the rotated file back, and the
  five variants must start with an access token that will not expire mid-run.
- **Fallback:** if the Codex round trip proves fragile, run the Codex half on a
  Platform API key (OpenAI's recommended path for CI) and keep Claude on the
  subscription.

## 1. Claude Code headless credential

**Mechanism.** `claude setup-token` runs the same browser flow as `/login`,
prints "a one-year OAuth token", and "does not save the token anywhere"; you
set it as `CLAUDE_CODE_OAUTH_TOKEN`. It "authenticates with your Claude
subscription and requires a Pro, Max, Team, or Enterprise plan" and "can only
make model requests" (no Remote Control, no claude.ai connectors; local MCP
servers still work).
[Authentication: Generate a long-lived token](https://code.claude.com/docs/en/authentication#generate-a-long-lived-token)

**Precedence traps.** The token ranks fifth. `ANTHROPIC_AUTH_TOKEN`,
`ANTHROPIC_API_KEY`, and `apiKeyHelper` all beat it, and "in non-interactive
mode (`-p`), the key is always used when present." A stray API key on the VM
would silently bill the API.
[Authentication precedence](https://code.claude.com/docs/en/authentication#authentication-precedence)

**`--bare` breaks it.** "Bare mode does not read `CLAUDE_CODE_OAUTH_TOKEN`."
The headless page recommends `--bare` for CI and says it "will become the
default for `-p` in a future release." The canary must not pass `--bare`, and
must watch for that default change.
[Authentication](https://code.claude.com/docs/en/authentication#generate-a-long-lived-token),
[Headless: bare mode](https://code.claude.com/docs/en/headless#start-faster-with-bare-mode)

**Lifetime and refresh.** One year. The docs describe no client-side refresh for
this token; the refresh and expiry-warning text applies to `/login` sessions
("The warning appears only when a claude.ai login is the active credential").
On expiry or revocation the run fails with `OAuth token has expired` or
`OAuth token revoked`.
[Renew an expiring login](https://code.claude.com/docs/en/authentication#renew-an-expiring-login),
[Errors: OAuth token revoked or expired](https://code.claude.com/docs/en/errors)

**Revocation.** Not documented on the official pages read. Open issues in the
first-party repo report revoking from claude.ai Settings > Claude Code, and one
reports the revoke button not working:
[anthropics/claude-code#57400](https://github.com/anthropics/claude-code/issues/57400),
[#98582](https://github.com/anthropics/claude-code/issues/98582),
[#48373](https://github.com/anthropics/claude-code/issues/48373).
Deleting the GitHub secret does not revoke it: "If you delete a secret, the
credential it held stays valid" (said of the API key there; nothing suggests the
OAuth token differs).
[GitHub Actions: Uninstall](https://code.claude.com/docs/en/github-actions#uninstall)

**Five concurrent runs.** Because the token is a static bearer credential with no
refresh step, five VMs can present it at once with no write-back and no race.
No page states a per-token concurrency cap. Usage across all five draws on the
one subscription's shared limits (section 4).

## 2. Codex headless credential

**What exists.**

| Option | Personal ChatGPT plan? | Fit for a 02:00 fresh VM |
| - | - | - |
| `codex login --device-auth` | Yes (enable device-code login in ChatGPT security settings) | No. Needs a human per login. [Auth: headless](https://learn.chatgpt.com/docs/auth) |
| Copy `auth.json` into `CODEX_HOME` | Yes. Documented fallback for headless machines | Yes, with write-back. [Auth: copy your auth cache](https://learn.chatgpt.com/docs/auth) |
| `CODEX_ACCESS_TOKEN` | No. "Currently supported for ChatGPT Business and Enterprise workspaces." 1 to 90 day validity | Only on a Business or Enterprise workspace. [Access tokens](https://learn.chatgpt.com/docs/enterprise/access-tokens) |
| `CODEX_API_KEY` / API key login | Not a subscription | The fallback. Billed "at standard API rates." [Auth](https://learn.chatgpt.com/docs/auth) |

The client reads `CODEX_ACCESS_TOKEN` from the environment directly
([manager.rs L1535-1557](https://github.com/openai/codex/blob/a956835d020762cb2b570053af06f643a11c0ecc/codex-rs/login/src/auth/manager.rs#L1535-L1557)),
and `CODEX_API_KEY` "takes precedence over any other auth method"
([L1499-1505](https://github.com/openai/codex/blob/a956835d020762cb2b570053af06f643a11c0ecc/codex-rs/login/src/auth/manager.rs#L1499-L1505)).
So `CODEX_API_KEY` must be absent on subscription runs.

**OpenAI's own CI guide.** "Maintain Codex account auth in CI/CD (advanced)"
covers exactly this case. Key lines:

- "The right way to authenticate automation is with an API key. Use this guide
  only if you specifically need to run the workflow as your Codex account."
- Use it only when "the runner is trusted private infrastructure", "you can
  preserve the refreshed `auth.json` between runs", and "only one machine or
  serialized job stream will use a given `auth.json` copy."
- "Do not use this workflow for public or open-source repositories."
- For ephemeral runners: restore, run, then "write the updated `auth.json` back
  to secure storage". "The key requirement is that the write-back step stores
  the refreshed file that Codex produced during the run, not the original seed."
- Rules: "Do not share the same file across concurrent jobs or multiple
  machines." Reseed if "another machine or concurrent job rotated the token
  first."
- Seed with `cli_auth_credentials_store = "file"`, then check `auth_mode` is
  `"chatgpt"` and a refresh token is present.

[CI/CD auth guide](https://learn.chatgpt.com/docs/auth/ci-cd-auth)

**How refresh works in the client** (codex `rust-v0.160.0`, commit
`a956835d`):

- Proactive refresh fires when the access token JWT expires within 5 minutes,
  or, if no expiry is readable, when `last_refresh` is older than 8 days
  ([manager.rs L203-204](https://github.com/openai/codex/blob/a956835d020762cb2b570053af06f643a11c0ecc/codex-rs/login/src/auth/manager.rs#L203-L204),
  [L3004-3026](https://github.com/openai/codex/blob/a956835d020762cb2b570053af06f643a11c0ecc/codex-rs/login/src/auth/manager.rs#L3004-L3026)).
  A failed proactive refresh is logged and the old token is used
  ([L2393-2407](https://github.com/openai/codex/blob/a956835d020762cb2b570053af06f643a11c0ecc/codex-rs/login/src/auth/manager.rs#L2393-L2407)).
- On a 401 the client reloads `auth.json` from disk, then refreshes
  ([L1850-1858](https://github.com/openai/codex/blob/a956835d020762cb2b570053af06f643a11c0ecc/codex-rs/login/src/auth/manager.rs#L1850-L1858)).
  Refresh does a guarded reload and skips the network call if the file already
  changed
  ([L2844-2880](https://github.com/openai/codex/blob/a956835d020762cb2b570053af06f643a11c0ecc/codex-rs/login/src/auth/manager.rs#L2844-L2880)).
  The lock is in-process only; separate VMs never see each other's file.
- Refresh tokens are single-use. The server returns `refresh_token_reused`
  ("Your refresh token has already been used to generate a new access token"),
  which the client maps to a permanent failure: "Please log out and sign in
  again"
  ([manager.rs L207, L1680-1688](https://github.com/openai/codex/blob/a956835d020762cb2b570053af06f643a11c0ecc/codex-rs/login/src/auth/manager.rs#L1680-L1688),
  [util.rs L23-30](https://github.com/openai/codex/blob/a956835d020762cb2b570053af06f643a11c0ecc/codex-rs/login/src/auth/util.rs#L23-L30)).

**What this means for 5 parallel VMs.**

1. Each VM gets an identical copy. If the access token is still valid for the
   whole run, no VM refreshes and nothing rotates. This is the safe case.
2. If the access token is stale, all five refresh with the same refresh token.
   One wins; four get `refresh_token_reused` and fail. A field report in an
   OpenAI repo says reuse then revoked the grant "for every client of that
   `~/.codex`" until a manual re-login
   ([openai/codex-plugin-cc#789](https://github.com/openai/codex-plugin-cc/issues/789),
   user report, not confirmed by OpenAI).
3. Ephemeral VMs discard the winner's rotated file. Without write-back, the
   stored seed holds a used refresh token, and the next stale week fails.
4. A seed copied from the owner's laptop shares a token chain with the laptop.
   Whichever side refreshes first breaks the other. Seed from a separate
   `codex login` in a dedicated `CODEX_HOME`. (That a second login yields an
   independent chain is inferred, not confirmed.)

**A design that respects these rules.** One Codex "auth owner" job runs first,
alone (a GitHub `concurrency` group):

1. Restore `auth.json` from the secret.
2. Run one trivial `codex exec`. The client refreshes only if stale.
3. Decode the access token's `exp` claim locally (never print it). Fail closed
   if it expires before the run's wall-clock budget ends.
4. Write the file back to the secret (see section 5).
5. Pass the result to the five variant jobs, which use it read-only and never
   write back.

At a weekly cadence, `last_refresh` alternates between about 7 days (no
refresh) and about 14 days (refresh in the owner job). That is safe only if the
access token lives longer than about 8 days plus the run. A field report puts
its lifetime at about 10 days after login
([codex-plugin-cc#789](https://github.com/openai/codex-plugin-cc/issues/789)
shows a 10-day-old file whose token "had expired the day before"). The fail-closed
check in step 3 covers the case where that is wrong. Passing the file from the
owner job to the variant jobs needs care: job outputs and artifacts are logged
or stored, so prefer a short-lived encrypted hand-off or have each variant job
restore the just-written secret.

The simpler alternative is OpenAI's own "serialized job stream": run the five
Codex variants on one VM with one `auth.json`, then write back once. That keeps
the supported rules but drops "each variant on a fresh VM".

## 3. Terms and policy

**Anthropic: permitted for the owner's own use, via the documented token.**

- The Consumer Terms (Pro and Max; effective 2025-10-08) forbid access "through
  automated or non-human means, whether through a bot, script, or otherwise",
  "except when you are accessing our Services via an Anthropic API Key or where
  we otherwise explicitly permit it." They also forbid sharing "Account
  credentials with anyone else."
  [Consumer Terms](https://www.anthropic.com/legal/consumer-terms)
- Anthropic explicitly permits the CI case: `setup-token` is "for CI pipelines,
  scripts, or other environments where interactive browser login isn't
  available"
  ([Authentication](https://code.claude.com/docs/en/authentication#generate-a-long-lived-token)),
  and the GitHub Actions page documents `CLAUDE_CODE_OAUTH_TOKEN` as a repository
  secret, including scheduled runs: "If you authenticate with an OAuth token,
  runs use your Claude subscription instead of API billing."
  ([GitHub Actions](https://code.claude.com/docs/en/github-actions))
- Limits on that permission: OAuth "is designed to support ordinary use of
  Claude Code", and "Advertised usage limits for Pro and Max plans assume
  ordinary, individual usage of Claude Code and the Agent SDK." Developers may
  not "route requests through Free, Pro, or Max plan credentials on behalf of
  their users." "Anthropic reserves the right to take measures to enforce these
  restrictions and may do so without prior notice."
  [Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance)
- Verdict: a weekly canary for the owner's own plugin, on the owner's own
  subscription, with the unmodified binary, fits the documented path. Keep the
  token in this one private repo; do not share it across an org (the docs
  steer org-wide secrets to API keys because "an OAuth token is tied to the
  subscription of the person who ran `claude setup-token`").

**OpenAI: tolerated, not recommended.**

- The Terms of Use forbid you to "automatically or programmatically extract
  data or Output", to "circumvent any rate limits or restrictions", and to
  "share your account credentials or make your account available to anyone
  else."
  [Terms of Use](https://openai.com/policies/terms-of-use/) (effective date not
  captured; the page blocked direct fetch and the extract omitted it).
- OpenAI's own docs publish the CI pattern above for "enterprise and other
  trusted private automation", while saying "API keys are still the recommended
  option for most CI/CD jobs" and "Use API key authentication for programmatic
  Codex CLI workflows, such as CI/CD jobs."
  [CI/CD auth guide](https://learn.chatgpt.com/docs/auth/ci-cd-auth),
  [Auth](https://learn.chatgpt.com/docs/auth)
- Verdict: a first-party guide covers this exact use on private runners, so it
  is defensible. It is not the endorsed default, and the Terms text on automated
  Output extraction leaves residual ambiguity that only OpenAI can settle.

## 4. Usage limits and what happens at the limit

**Claude.**

- Pro and Max limits "are shared across Claude and Claude Code"
  ([support article](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan),
  updated 2026-08-19). It gives no numbers.
- Limit kinds: session, weekly, and per-family Opus and Sonnet limits. "Claude
  Code blocks further requests until the reset time." "A single burst of heavy
  activity, such as a large workflow fanout, can exhaust the weekly allowance
  before the session window resets."
  [Errors: session limit](https://code.claude.com/docs/en/errors)
- In `-p`, there is no wait: "Background sessions and `-p` runs: the menu row
  isn't available," and automatic continue is described for "interactive
  sessions." Treat a limit hit as a failed run.
  [Interactive mode: wait for a usage limit](https://code.claude.com/docs/en/interactive-mode#wait-for-a-usage-limit-to-reset)
- Spill-over: when usage credits are on, they pay once a window runs out, up to
  a monthly spend limit.
  [Errors: monthly spend limit](https://code.claude.com/docs/en/errors).
  The support article says Claude Code "requires explicit consent before
  transitioning to paid API usage." Keep usage credits off, or capped, for the
  canary account.
- Transient throttles ("Server is temporarily limiting requests") are retried
  with backoff since v2.1.199.
  [Errors](https://code.claude.com/docs/en/errors)

**Codex.**

- Plus: 5-hour estimates per model (for example GPT-6.1 Sol 15-160 local
  messages). "Pro plans currently have no five-hour limit." "Weekly limits may
  also apply."
  [Pricing](https://learn.chatgpt.com/docs/pricing?codex-pricing-plans=individual&codex-usage-limits=plus)
- At the limit: "the agent will be able to continue working on that turn,
  subject to fair use limits." Plus and Pro can buy credits. "All users may also
  run extra local chats using an API key." No automatic fall back to API billing
  is described.
  [Pricing](https://learn.chatgpt.com/docs/pricing)
- In the client, a `UsageLimitReached` error is not retried; the turn returns
  the error
  ([turn.rs L1699-1705](https://github.com/openai/codex/blob/a956835d020762cb2b570053af06f643a11c0ecc/codex-rs/core/src/session/turn.rs#L1699-L1705)).

**Do five parallel runs fit?** Unknown without a measured run. The canary SPEC is
small (about 150 LOC, two stories), but each run spans scaffold, plan, and
implement. On Claude Pro, or on ChatGPT Plus with a large model, five at once
could exhaust a 5-hour window. Measure one variant's usage first and size from
that.

## 5. Getting a secret onto a runner microVM

**What the runner platform offers** (v2.0.8, commit `6ae624e1`):

- Each VM boots from a rootfs built from an OCI image and is "destroyed after
  the job is finished, no state is preserved between jobs"
  (docs/index.md, upstream runner source at `6ae624e1`,
  server/pool.go L473-478, upstream runner source at `6ae624e1`).
  There is no volume or secret-mount feature.
- Per-pool `metadata` from the host's YAML config goes to every VM in the pool
  through Firecracker MMDS at `169.254.169.254`, next to the runner's JIT config
  (configuration.md L150-156, upstream runner source at `6ae624e1`,
  pool.go L480-520, upstream runner source at `6ae624e1`,
  agent/mmds/client.go L73-112, upstream runner source at `6ae624e1`).
- Runners register as single-job JIT runners
  (pool.go L506-510, upstream runner source at `6ae624e1`).

**Do not use the image or MMDS for credentials.** A secret baked into the image
sits in the registry and in every VM. A secret in pool metadata sits in
plaintext in the host config, and any step of any job in the org runner group
can read it from the metadata endpoint. Neither supports Codex write-back.

**Use GitHub Actions secrets.** Put both credentials in an environment secret on
the private fixture repo (for example an environment limited to the default
branch), and expose each only to the step that needs it.

Rules the run must follow:

- Pass credentials by environment variable or a `0600` file under a `0700`
  directory. Never as a command-line argument: "secrets as command-line
  arguments ... can be seen by another job running on the same runner, such as
  `ps x -w`."
  [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use)
- `auth.json` is JSON, and GitHub warns: "do not use a blob of JSON ... to
  encapsulate a secret value, as this significantly reduces the probability the
  secrets will be properly redacted." Never print it. Extract the token fields
  and `::add-mask::` each before any step that might echo them.
  [GitHub secure use](https://docs.github.com/en/actions/reference/security/secure-use)
- No `set -x` in credential steps. No env dumps in receipts.
- Never upload `CODEX_HOME`, `~/.claude`, session transcripts, or `codex-login.log`
  as artifacts or caches.
- Unset `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, and `CODEX_API_KEY` on
  subscription runs, and fail the step if any is set. For Codex, also check
  `codex login status` before the run.
- Codex write-back uses `PUT /repos/{owner}/{repo}/actions/secrets/{name}`,
  which needs a token with the "Secrets" repository permission (write) and a
  LibSodium-encrypted value; `gh secret set` does the encryption.
  [REST: repository secrets](https://docs.github.com/en/rest/actions/secrets#create-or-update-a-repository-secret).
  That write token is itself a secret; scope it to the fixture repo only.

## 6. Recommendation

1. **Claude: use `claude setup-token`.** Store the token as
   `CLAUDE_CODE_OAUTH_TOKEN` in a fixture-repo environment secret. Run
   `claude -p` without `--bare`. Assert no API key variables are set. Calendar
   a renewal before the one-year expiry. Keep usage credits off or capped.
2. **Codex: use the seeded `auth.json` round trip, guarded.** Seed from a
   dedicated `codex login` (file store, own `CODEX_HOME`), not the owner's daily
   login. Add the single auth-owner job with a fail-closed expiry check and
   write-back. Variants use the file read-only. Treat any `refresh_token_reused`
   as a reseed signal and an infrastructure failure, not a canary failure.
3. **Prototype first.** Before the weekly schedule, run the auth-owner job plus
   two Codex variants in parallel across one forced-stale week to confirm no
   variant refreshes.
4. **Fallback if Codex subscription auth proves fragile:** run the Codex half
   with a Platform API key (`CODEX_API_KEY`), OpenAI's recommended CI path,
   billed at API rates. If the owner moves to a ChatGPT Business or Enterprise
   workspace, `CODEX_ACCESS_TOKEN` (up to 90 days, revocable, no rotation) would
   replace the round trip. If Claude subscription auth were ever refused,
   `ANTHROPIC_API_KEY` is the same-shape swap.

## Not confirmed

- **Claude token revocation path.** Only GitHub issues describe it (claude.ai
  Settings > Claude Code). Looked in the authentication, errors, GitHub Actions,
  and legal pages.
- **Concurrency cap for one Claude OAuth token.** No page states one. Looked in
  the same pages plus the support article.
- **Whether `claude -p` draws usage credits without a prompt** when they are
  enabled. The errors page implies credits pay automatically; the support
  article says Claude Code asks for consent.
- **Whether automatic continue ever applies to `-p`.** The docs scope it to
  interactive sessions and exclude the manual wait for `-p`.
- **Codex access token lifetime.** About 10 days per one field report; OpenAI
  does not document it. The 8-day `last_refresh` interval is only a fallback in
  code.
- **Whether refresh-token reuse revokes the whole chain.** One field report says
  yes; OpenAI docs say only to reseed.
- **Whether a second `codex login` yields an independent token chain** from the
  owner's existing login.
- **OpenAI Terms of Use effective date,** and whether the "programmatically
  extract ... Output" clause reaches a first-party-documented CI use.
- **Plan tiers.** Which Claude plan (Pro or Max) and ChatGPT plan (Plus or Pro)
  the owner holds, and no numeric Claude limits are published. Fit of five
  parallel runs needs a measured run.
- **Runner platform logging of MMDS metadata.** Firecracker runs at `Debug` log
  level (pool.go L488, upstream runner source at `6ae624e1`);
  not checked whether metadata reaches that log. Moot if credentials stay out of
  metadata.
