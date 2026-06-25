---
name: speckit-resolve-pr
description: "MANDATORY for resolving GitHub PR review comments by editing the source code those comments flagged. Use this skill — NOT a read-only PR review skill — whenever the user wants to ACT on PR review feedback by changing code, committing, and pushing. Triggers on these phrases: 'resolve PR review comments', 'address review feedback', 'fix the copilot comments', 'resolve the threads on PR #N', 'fix each review comment and resolve the threads', 'handle the Copilot review on this PR', 'work through the review comments on this PR', 'address them all', 'take care of the outstanding review feedback', or whenever a PR URL is pasted with unresolved comments. The skill edits files, runs project verification, commits the fixes, pushes, posts a reply per thread, and marks each thread resolved via gh API. NOT for read-only PR review, summarizing what a PR changes, or assessing PR merge risk — those are read-only review skills, this is a write skill that mutates the working tree."
argument-hint: "PR URL or number (e.g., https://github.com/owner/repo/pull/46 or 46)"
user-invocable: true
allowed-tools: Bash Read Edit Write Grep Agent ToolSearch
license: MIT
---

# Resolve PR Review Comments

## Capability discovery & grounding

Before researching or recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `speckit-pro/skills/speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it.

## Codex Skill-Selection Guard

If this file is loaded in Codex, the runtime selected the Claude Code
variant from `skills/` instead of the Codex variant from `codex-skills/`.
Do not follow the Claude-oriented instructions below in Codex. Immediately
read and follow `../../codex-skills/speckit-resolve-pr/SKILL.md` from this plugin
root, treat that document as the active skill, and report that the fallback
guard was triggered.

Address ALL unresolved review comments on a pull request,
fix the code, and mark each thread resolved.

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
  Bash("git remote -v") → extract OWNER/REPO from origin URL
  PR_NUMBER = the provided number
```

### 2. Discover Project Commands

Read CLAUDE.md and package.json (or equivalent) to find:
- BUILD command
- TYPECHECK command
- LINT command
- LINT_FIX command
- UNIT_TEST command
- INTEGRATION_TEST command

Detect package manager from lockfile if Node.js project.

### 3. Fetch All Unresolved Review Threads

Fetch review threads via GraphQL to get thread IDs (needed
for resolution) and comment details in one call:

```text
Bash("gh api graphql -f query='query {
  repository(owner: \"<OWNER>\", name: \"<REPO>\") {
    pullRequest(number: <PR_NUMBER>) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          path
          line
          comments(first: 10) {
            nodes {
              id
              databaseId
              body
              author { login }
              createdAt
            }
          }
        }
      }
    }
  }
}'")
```

Filter to unresolved threads only (`isResolved == false`).
Each thread's `id` is the threadId needed for resolution.
Each thread's `comments.nodes[0]` is the original review
comment with the reviewer's feedback.

If 0 unresolved threads, report "No unresolved comments
on PR #<PR_NUMBER>" and stop.

### 4. Process Comments — Partition by File, Parallel Across Files

**Partition the unresolved threads by file path.** Within a partition
(same file), process serially — concurrent edits to the same file race
on the `Edit` tool. Across partitions (different files), dispatch
parallel background subagents in ONE assistant message. This is
**Use site 6** of the [Agent Teams integration map](../skills/speckit-autopilot/references/agent-teams-integration.md)
— the WS-F1 pattern.

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

If `PARTITIONS` has ≥2 entries, dispatch ALL partitions in ONE
assistant message via background subagents:

```text
For each (file_path, threads) in PARTITIONS:
  Agent(
    subagent_type: "general-purpose",
    run_in_background: true,
    description: "Resolve PR #<N> comments on <file_path>",
    prompt: """
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
      (a) CODE FIX → Edit the file; run BUILD+TYPECHECK+UNIT_TEST; fix
          until clean.
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
    """
  )
```

If `PARTITIONS` has 1 entry (all threads on one file), do NOT spawn a
subagent — process directly in the orchestrator (no parallelism win,
extra tool-call latency).

#### 4d. Process cross-file comments serially

After all partition subagents return, process `CROSS_FILE` threads
one at a time in the orchestrator (each touches multiple files; serial
prevents inter-thread race).

### 5. Reply and Resolve Each Thread (orchestrator, serial)

The orchestrator collects partition-subagent results, then for each
thread (parallel partitions + serial cross-file) posts the reply and
resolves the thread via gh API. Writes to GitHub are cheap and ordered:

```text
Reply to the comment:
Bash("gh api repos/<OWNER>/<REPO>/pulls/<PR_NUMBER>/comments \
  -X POST \
  -f body='<explanation of what was fixed or why no change>' \
  -f in_reply_to=<comment_id>")

Resolve the review thread:
Bash("gh api graphql -f query='mutation {
  resolveReviewThread(input: {
    threadId: \"<thread_id>\"
  }) {
    thread { isResolved }
  }
}'")
```

The `<thread_id>` comes from the GraphQL query in Step 3
(each thread's `id` field). Do NOT use the comment's
node_id — thread resolution requires the thread ID.

### 6. Push All Changes

After all comments are addressed:

```text
Bash("git push")
```

### 7. Report Summary

```text
## PR Review Comments Resolved

**PR:** #<PR_NUMBER> (<OWNER>/<REPO>)

**Comments processed:** N total
- Code fixes: N (committed)
- Style fixes: N (committed)
- Replies only: N (questions/false positives)

**Commits pushed:** N
**Threads resolved:** N

**Remaining:** 0 unresolved
(or "N comments could not be resolved — manual review needed")
```
