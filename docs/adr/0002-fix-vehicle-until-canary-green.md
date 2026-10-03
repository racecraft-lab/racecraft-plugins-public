# speckit-pro does not drive its own repair until the canary is green

Status: accepted

The health program is built with the Matt Pocock flow (wayfinder, to-spec, to-tickets, implement), one PR per ticket through `gh stack`. No speckit-pro skill (scaffold, autopilot, resolve-pr, grill-me, prd) plans or builds health work. Running speckit-pro as the thing under test stays allowed: canary runs, fixture runs and evidence runs on scratch SPECs. A broken autopilot that repairs itself turns each regression into a stalled run, so the plugin under repair cannot be the tool doing the repair.

The ban lifts in two stages. A green canary receipt on both hosts for the release that closes phase 5 opens Part D acceptance runs only. General use waits for the full Definition of done. A red canary on either host brings the ban back until both hosts are green again. Fixes made in the meantime go through the Matt Pocock flow.

A repo hook enforces the ban on both hosts. It blocks speckit-pro skills invoked by a typed command or by the model, unless the session's clone is marked as scratch. The mark is an untracked, clone-local git config key (`speckit-health.scratch`) that is set when the scratch clone is made. The owner's checkout and its worktrees never carry it. Canary and evidence runs, and the Part D acceptance run in this repo, each happen in a marked scratch clone. Fixture repos that are not clones of this repo do not carry the hook at all. The hook stays in place until the Definition of done is met. A PR then deletes it, and from that point this ADR is the only rule for a red canary.

## Considered Options

- **speckit-pro on itself.** Dogfoods early. Rejected: every regression can stall the fix for that regression.
- **Hybrid by phase** (switch to speckit-pro at an interim gate). Rejected: no gate short of the canary proves the plugin can carry real work.
- **Written rule only** (ADR plus an AGENTS.md line). Rejected in favor of a hook: an agent can miss a rule, but it cannot get past a hook.
- **Env flag as the test escape.** Rejected: it leaks into any session that inherits the environment, a driving run included. The clone-local mark stays with the scratch clone.
- **Path check against the owner's checkout.** Rejected: it needs that path stored outside the repo, and it breaks when the checkout moves.
- **Hook reads canary receipts** and blocks only while a host is red. Rejected: it couples a repo hook to the receipt format for a ban that ends once.

## Consequences

- Building the hook is an execution item in the program spec, not a map decision. On Claude Code it is a tracked project settings hook (`UserPromptSubmit` for typed commands, `PreToolUse` on `Skill` for model calls). On Codex it is a project `UserPromptSubmit` hook for typed `$skill` mentions, plus `PreToolUse` on `Bash` for model calls: Codex has no skill tool, so the hook blocks the model reading an installed speckit-pro `SKILL.md`. Both need one-time trust.
- A Part D acceptance SPEC in this repo (HRNS-015) starts from scratch in a marked scratch clone, not in a worktree of the owner's checkout.
- Every speckit-pro change during the program, a user-reported bug included, goes through the same flow.
