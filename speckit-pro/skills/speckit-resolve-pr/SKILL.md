---
name: speckit-resolve-pr
<!-- host:claude: Claude reads a trigger-phrase description and Claude-only frontmatter keys -->
description: "MANDATORY for resolving GitHub PR review comments by editing the source code those comments flagged. Use this skill — NOT a read-only PR review skill — whenever the user wants to ACT on PR review feedback by changing code, committing, and pushing. Triggers on these phrases: 'resolve PR review comments', 'address review feedback', 'fix the copilot comments', 'resolve the threads on PR #N', 'fix each review comment and resolve the threads', 'handle the Copilot review on this PR', 'work through the review comments on this PR', 'address them all', 'take care of the outstanding review feedback', or whenever a PR URL is pasted with unresolved comments. The skill edits files, runs project verification, commits the fixes, pushes, posts a reply per thread, and marks each thread resolved via gh API. NOT for read-only PR review, summarizing what a PR changes, or assessing PR merge risk — those are read-only review skills, this is a write skill that mutates the working tree."
argument-hint: "PR URL or number (e.g., https://github.com/owner/repo/pull/46 or 46)"
user-invocable: true
allowed-tools: Read Edit Write Grep Agent ToolSearch
license: MIT
<!-- /host -->
<!-- host:codex: Codex keeps its own selection description -->
description: >
  Address actionable review feedback on a pull request, push the
  fixes, and resolve review threads. Reads the PR comments,
  updates the code, runs project verification, replies to review
  threads, and reports what changed.
<!-- /host -->
---

# Resolve PR Review Comments

## Capability discovery & grounding

<!-- host:claude: Claude resolves plugin files through CLAUDE_PLUGIN_ROOT -->
Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it.
<!-- /host -->
<!-- host:codex: Codex has no plugin-root variable, so it links relative to this skill -->
Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `../speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `../speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it.
<!-- /host -->

Address ALL unresolved review comments on a pull request,
fix the code, and mark each thread resolved.

## Scope

Use this skill when the user wants review feedback addressed on an existing
pull request. The goal is not a general code review. The goal is to read the
unresolved review feedback, make the necessary code changes, verify the branch,
reply to the review comments, and resolve the threads.

If the user wants a fresh review of a PR, use a review workflow instead. If
they want to learn how the post-PR loop works, redirect to
<!-- host:claude: Claude names skills with a slash -->
`/speckit-pro:speckit-coach`.
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
`$speckit-pro:speckit-coach`.
<!-- /host -->
This skill is for remediation and closure.

## Input

The user provides either:
- A full PR URL: `https://github.com/owner/repo/pull/46`
- A full PR review URL: `https://github.com/owner/repo/pull/46#pullrequestreview-123`
- Just a PR number: `46` (repo detected from `git remote -v`)

## What to Do

### 1. Parse Input and Detect Repo

```text
If full URL provided:
  Extract OWNER, REPO, PR_NUMBER from URL

If just a number:
  Run `git remote -v`, inspect the actual fetch/push remotes, and select the
  remote whose normalized GitHub URL identifies the current repository.
  Never assume that remote is named `origin`; stop on no match or ambiguity.
  PR_NUMBER = the provided number
```

Check out the PR branch and verify the actual code behavior in that
checkout. Never review or remediate from the diff alone.

Before editing anything, confirm `gh` is available and authenticated if thread
resolution is required, and inspect the repo state with `git status` so you
know whether unrelated user changes are already present. Do not overwrite
unrelated dirty worktree changes. If the current checkout cannot safely host
the remediation, create or switch to the correct branch without discarding
existing work.

### 2. Discover Project Commands

Read the project guidance files (CLAUDE.md, AGENTS.md) and package.json (or
equivalent) to find:
- BUILD command
- TYPECHECK command
- LINT command
- LINT_FIX command
- UNIT_TEST command
- INTEGRATION_TEST command

Detect package manager from lockfile if Node.js project; the
plugin's PreToolUse hook denies a shell command that uses a different
manager than the lockfile names.

Run TYPECHECK and UNIT_TEST locally before posting any review comment
or reply. Scope every finding to files the PR changed unless the user
explicitly asks for a broader review.

### 3. Fetch All Unresolved Review Threads

Fetch review threads via GraphQL with `gh api graphql` to get thread IDs
(needed for resolution) and comment details in one call. Query
`repository.pullRequest.reviewThreads(first: 100)` and include each thread's
`id`, `isResolved`, `path`, `line`, and the first 10 comments with `id`,
`databaseId`, `body`, `author.login`, and `createdAt`.

Filter to unresolved threads only (`isResolved == false`).
Each thread's `id` is the threadId needed for resolution.
Each thread's `comments.nodes[0]` is the original review
comment with the reviewer's feedback.

If 0 unresolved threads, report "No unresolved comments
on PR #<PR_NUMBER>" and stop.

### 4. Process Comments — Partition by File, Parallel Across Files

<!-- host:claude: Claude edits with the Edit tool and maps this use site to Agent Teams -->
**Partition the unresolved threads by file path.** Within a partition
(same file), process serially — concurrent edits to the same file race
on the `Edit` tool. Across partitions (different files), dispatch
parallel background subagents in ONE assistant message. This is
**Use site 6** of the [Agent Teams integration map](../speckit-autopilot/references/agent-teams-integration.md).
<!-- /host -->
<!-- host:codex: Codex edits with apply_patch and dispatches with spawn_agent -->
**Partition the unresolved threads by file path.** Within a partition
(same file), process serially — concurrent `apply_patch` calls to the same
file race. Across partitions (different files), dispatch parallel background
subagents in ONE tool turn.
<!-- /host -->

#### 4a. Detect cross-file comments

Before partitioning, scan each thread's comment body for cross-file
hints (e.g., "rename `foo` and update all callers", "this affects
`bar.ts` too", references to other paths). Cross-file comments are
**serialized** — they touch multiple files and cannot run in parallel
with siblings without race risk.

```text
For each thread:
  cross_file = false
  if comment body mentions other paths/files/symbols that imply
     edits beyond thread.path:
    cross_file = true
  thread.cross_file = cross_file
```

#### 4b. Build partitions

```text
PARTITIONS = {}            # file_path -> [threads]
CROSS_FILE = []            # serialized, processed last

For each thread:
  if thread.cross_file:
    CROSS_FILE.append(thread)
  else:
    PARTITIONS[thread.path].append(thread)
```

#### 4c. Dispatch parallel subagents per partition

Dispatch subagents only when `PARTITIONS` has 2 or more entries and the
fixes are large enough to repay each worker's setup cost (it re-reads the
file, rebuilds context, and re-runs the checks). A few small fixes are
faster to make directly, one partition at a time. When you dispatch, send
ALL partitions at once:

<!-- host:claude: Claude dispatches background subagents with the Agent tool -->
```text
For each (file_path, threads) in PARTITIONS:
  Agent(
    subagent_type: "general-purpose",
    run_in_background: true,
    description: "Resolve PR #<N> comments on <file_path>",
    prompt: <the worker prompt below>
  )
```
<!-- /host -->
<!-- host:codex: Codex has no general-purpose role; it spawns the built-in default role and waits on each handle -->
For each partition, call `spawn_agent` to start one built-in `default` subagent
without a model or reasoning-effort override, all in ONE tool turn, with the
worker prompt below as its task. Then `wait_agent` on every handle until each
delivers its result; a status update or a timed-out wait is not the result.
<!-- /host -->

The worker prompt:

```text
Fix the following review threads on `<file_path>`. Threads are
ordered by line number; address them in order.

## Project commands (from Step 2)
BUILD: <BUILD>
TYPECHECK: <TYPECHECK>
UNIT_TEST: <UNIT_TEST>
LINT_FIX: <LINT_FIX>

## Threads
<list of {thread_id, line, comment_body, comment_id}>

## What to do for each thread
Read the referenced code and its surroundings first.
(a) CODE FIX → make the smallest correct fix; run
    BUILD+TYPECHECK+UNIT_TEST; fix until clean.
(b) STYLE → run LINT_FIX.
(c) QUESTION → prepare a reply (no code change).
(d) FALSE POSITIVE → prepare a reply explaining why no change.

## When done
Commit ALL fixes for this file in one commit:
  git add <file_path>
  git commit -m "fix: address review - <brief summary>"
Return a structured summary:
  - Threads handled (count, IDs, action taken per ID)
  - Commit SHA (if any fix committed; null otherwise)
  - Verification result (pass/fail; if fail, surface error)
  - Per-thread reply text (for the orchestrator to post)
Do NOT push. Do NOT post replies. Do NOT resolve threads.
The orchestrator handles git push and gh API calls serially.
```

If `PARTITIONS` has 1 entry (all threads on one file), do NOT spawn a
subagent — process directly in the orchestrator (no parallelism win,
extra tool-call latency).

When a reviewer is simply asking a question and the existing code is
correct, do not churn the code just to make the thread go away. Reply
with a grounded explanation instead.

#### 4d. Process cross-file comments serially

After all partition subagents return, process `CROSS_FILE` threads
one at a time in the orchestrator (each touches multiple files; serial
prevents inter-thread race).

### 5. Verify, Push, Confirm

Do not resolve a thread until the relevant code path has been verified. After
all comments are addressed, finish in one pass:

1. Run the full suite: FULL_VERIFY, or BUILD && TYPECHECK && LINT &&
   UNIT_TEST && INTEGRATION_TEST. A failure here reopens Step 4; do
   not push a red branch. If verification fails, keep working until you
   either fix it or can clearly explain why the repo was already failing
   independently. Never reply “fixed” on a thread while the branch is still
   broken.
2. Run `git push`.
3. Confirm with `git status -sb`: the branch line must not read
   `ahead`. Do not report completion until that confirmation is in
   hand. While an autopilot workflow is active, the plugin's Stop hook
   blocks ending the turn with unpushed commits.

Group related review fixes into intentional commits rather than one commit
per comment. Do not amend or rewrite history unless the user explicitly asks
for it. If the repo already has unrelated local changes, work around them
rather than reverting them.

### 6. Reply and Resolve Each Thread (orchestrator, serial)

The orchestrator collects partition-subagent results, then for each
thread (parallel partitions + serial cross-file) posts the reply and
resolves the thread via gh API. Writes to GitHub are cheap and ordered:

```text
Reply to the comment:
Use `gh api repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>/comments` with `POST`,
`body='<explanation of what was fixed or why no change>'`, and
`in_reply_to=<comment_id>`.

Resolve the review thread:
Use `gh api graphql` with the `resolveReviewThread` mutation and
`threadId: "<thread_id>"`.
```

The `<thread_id>` comes from the GraphQL query in Step 3
(each thread's `id` field). Do NOT use the comment's
node_id — thread resolution requires the thread ID.

A new finding of your own (not a reply) goes inline: `POST
repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>/comments` with `path`, `line`,
`side`, and `commit_id` targeting the exact diff line. A summary
comment is not a substitute for an inline one.

If GitHub tooling is unavailable, stop after making, verifying, and pushing
the fix, and tell the user that thread resolution could not be completed from
the current environment.

### 7. Report Summary

```text
## PR Review Comments Resolved

**PR:** #<PR_NUMBER> (<OWNER>/<REPO>)

**Comments processed:** N total
- Code fixes: N (committed)
- Style fixes: N (committed)
- Replies only: N (questions/false positives)

**Verification:** <commands run and result>
**Commits pushed:** N (confirmed: `git status -sb` shows no `ahead`)
**Threads resolved:** N

**Remaining:** 0 unresolved
(or "N comments could not be resolved — manual review needed")
```

If anything remains open, name the blocker explicitly: missing auth, failing
verification, ambiguous feedback, or a thread that needs a human decision.

## Boundaries

Stay within files touched by the PR unless a review comment forces a broader
change. Do not turn a review-remediation task into a drive-by refactor. The
goal is to satisfy the actionable review feedback and leave the branch in a
mergeable state.
