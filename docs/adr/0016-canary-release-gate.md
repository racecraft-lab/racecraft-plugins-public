# A private canary, weekly or on demand, gates every release

Status: accepted

Decision ticket: [Canary: fixture, variants, receipt, budget, release gate](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1028), part of [Wayfinder: speckit-pro health program](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1006). It settles how ADR 0003's gate is enforced and how often the canary reruns.

## Where it runs and how it gates

The canary lives in a private fixture repo and runs on the self-hosted Linux runners. Their runner group admits selected private repos only, so the canary cannot run from this public repo.

It runs once a week, Sunday 02:00 America/Chicago. It tests the open release PR's head commit, or main when no release PR is open. Each run is 5 variants on each host, 10 parallel jobs on fresh VMs. A GitHub App posts `canary / claude-code` and `canary / codex` commit statuses on the tested commit. Branch protection on the release PR requires both, so a release merges only after a green run on its exact head. A commit pushed after the run waits for the next one.

For a security fix or another urgent release, the owner can start an on-demand run instead of waiting for Sunday. It is a manual dispatch of the same workflow against the release PR's current head: the same 10 jobs, receipts, budgets and commit statuses, and the receipt records the trigger (`scheduled` or `on_demand`) and the stated reason. It is not a bypass; the release still merges only on a green run on its exact head (ADR 0003). Only one canary run may be active at a time, so the Codex auth-owner job never refreshes the same token chain twice; an on-demand run queues behind a run already in progress.

A red result on either host blocks releases and, per ADR 0002, brings back the fix-vehicle ban.

## What it runs

The fixture is a small Python CLI (standard library plus pytest) at a pinned tag. The base SPEC adds two stories, about 150 lines, each with a command a reviewer runs in UAT. Fixture changes are reviewed PRs to the fixture repo with a new tag, and they re-baseline the budget.

Each run takes the full user path: scaffold from an answers file, planning, plan review, and implement as a separate invocation.

- **Answers file.** Scaffold gains a public answers-file flag. Every interview question must be answered in the file. A missing or unknown answer fails scaffold; it never asks. The canary's file pre-answers the quality-gate confirmation (ADR 0007) and declines formal methods and verification Docker after the offer (ADR 0005).
- **Plan review.** A scripted reviewer drives `speckit-plan-review`, and the plan approval record is marked canary-issued by a canary-only test issuer (a recorded approval under ADR 0017; nothing is signed). That issuer is trusted only inside the canary's isolated host homes, and every production verifier rejects it. The canary proves the approval flow and record handling, never the real authority; [Plan approval authority: resolve protection and qualification under one macOS login](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1037) owns that proof (ADR 0015).

All five variants gate every release:

| Variant | Must hold |
|---|---|
| Base, with umask 077 and no task-list tools | The pass conditions below (ADR 0001) |
| Oversized plan | A split recommendation is recorded, the full plan is built, no stop (ADR 0009) |
| Security interrupt | A simulated responder answers under a runner permit; it reads as an authorized pause, not an unregistered stop (ADR 0011) |
| Missing question guard | The run may reach handoff, but the receipt is red (ADR 0011) |
| Security block in implement | Affected work is blocked-for-UAT and independent work finishes (ADR 0012, 0014) |

A run passes when there are zero questions after scaffold, planning ends at artifacts plus a draft PR, implement ends ready for UAT with a runbook, every stage is within budget, and there are zero unregistered stops (ADR 0010).

Draft PRs open in the fixture repo on a run-named branch. After the receipt is recorded, the harness closes the PR and deletes the branch.

## Budget

The budget file sets two limits for each host, variant and stage (scaffold, plan, implement): wall-clock time and total tokens. Each limit starts at the median of the first three green runs plus 50%. Limits change only through a reviewed PR, never by automatic ratchet. The budget is a pass condition only. It never stops a run, which keeps ADR 0004's rule that the retry ladder is the only failure path.

## Receipt

Each run leaves one JSON canary receipt per host. It records the commit, host and plugin versions, fixture tag, and each variant's verdict with its failed assertions. It also records per-stage time and tokens against budget, questions after scaffold, unregistered stops, decisions-list counts by kind, retry-ladder attempts and the blocked-for-UAT count. Receipts plus redacted transcripts and run state are stored as private-repo artifacts for 90 days. The receipt schema and its validator live in `tests/speckit-pro/layer7-integration/`.

## Authentication

Both hosts run on the owner's subscriptions, never API keys, per [Research: subscription auth for the canary on self-hosted runners](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1035).

- **Claude Code** uses a `claude setup-token` token as `CLAUDE_CODE_OAUTH_TOKEN`. It does not refresh, so all jobs share it.
- **Codex** on a personal plan uses an `auth.json` round trip from a login dedicated to the canary, never the owner's own login. A serial auth-owner job restores the file, refreshes it, checks that it outlives the run, and writes it back as a secret. The variant jobs then use it read-only. This must hold over one stale-token week with two parallel runs before the canary gates. If it proves fragile, Codex alone moves to a Platform API key.
- **Credential handling.** Credentials are GitHub environment secrets on the fixture repo, passed per step. They are never baked into the runner image or microVM metadata, never passed as command-line arguments, and never logged or uploaded. A job fails if `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` or `CODEX_API_KEY` is set. A usage-limit hit fails the run. Claude usage credits stay off or capped.

If the Codex probe shows headless plugin install or `$skill` expansion does not work, the plugin is fixed before the canary is declared ready, with no named exception. If the gap is in Codex itself, plugin install is one-time host setup, which ADR 0003 exempts, so the harness may run the documented install step.

## Local dogfooding

The same harness runs on a developer's Mac against a local build, deployed to both hosts through the plugin refresh fast path, in a scratch clone marked per ADR 0002. Its receipt is marked `local` with a dirty-tree flag. It is feedback only and can never post a release status.

## Failures become checks

A red receipt opens an issue that links the failed assertion. The PR that closes the issue must add a deterministic test, in the layer suites or unit tests, that fails before the fix. A PR check enforces that a test was added. The issue closes only after the next green run, weekly or on demand.

## Considered Options

- **Local run on an enrolled Mac, release CI checks committed receipts.** Rejected: the owner chose the HAL runners, and a gate should not depend on one person's machine.
- **GitHub-hosted runners with secrets.** Rejected: model cost in public CI, and no private runner pool.
- **Run per release PR, or a daily host-version check.** Rejected for a weekly off-peak run plus on-demand runs for urgent releases.
- **Loosen the exact-commit binding for faster releases.** Rejected: it amends ADR 0003.
- **Maintainer approves the plan live, or implement from a fixture plan.** Rejected: a live approval makes the canary attended and waits on real-authority qualification; a fixture plan never proves that the plan just produced can be approved and built.
- **Canary-only scaffold switch, or skip scaffold.** Rejected: the canary would test a path users never take, or not test scaffold at all.
- **Some variants on a slower schedule.** Rejected: all five gate.
- **Wall clock only, or auto-ratcheting limits.** Rejected: token burn goes unseen, or one lucky run turns normal runs red.
- **Receipt only, or unscrubbed transcripts kept forever.** Rejected: a red run would need a week's rerun to diagnose, or leaked content would be kept indefinitely.
- **Reviewer checklist or canary-only assertion for failures.** Rejected: the first is a prose rule; the second keeps feedback weekly.
- **API keys for Codex now.** Rejected for subscription auth with a proven-first gate; the API key stays the fallback.

## Consequences

- Routine releases ship at most once a week, after Sunday's run. Security fixes and other urgent releases ship after an on-demand green run.
- A private fixture repo, a GitHub App with commit-status permission on this repo, release-PR branch protection, and fixture-repo secrets must exist before the gate starts.
- Scaffold gains a public answers-file flag.
- A Codex auth prototype must pass before the canary gates releases.
- A stale or broken Codex token chain makes the Codex half red until someone logs in again or the API-key fallback is adopted.
