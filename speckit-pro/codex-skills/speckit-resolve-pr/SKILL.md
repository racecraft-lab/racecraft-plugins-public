---
name: speckit-resolve-pr
description: >
  Address actionable review feedback on a pull request, push the
  fixes, and resolve review threads. Reads the PR comments,
  updates the code, runs project verification, replies to review
  threads, and reports what changed.
---

# SpecKit Resolve PR

## Scope

Use this skill when the user wants review feedback addressed on an existing
pull request. The goal is not a general code review. The goal is to read the
unresolved review feedback, make the necessary code changes, verify the branch,
reply to the review comments, and resolve the threads.

If the user wants a fresh review of a PR, use a review workflow instead. If
they want to learn how the post-PR loop works, redirect to `$speckit-coach`.
This skill is for remediation and closure.

## Input

Accept either:

- a pull request number
- a pull request URL
- a review-comment URL anchored to a specific PR review

If only a PR number is supplied, derive the repository from `git remote -v`.
Never assume the remote is named `origin`; inspect the actual remotes first.

## Preconditions

Before editing anything:

- ensure the current checkout is on the PR branch or switch to it safely
- confirm `gh` is available and authenticated if thread resolution is required
- inspect the repo state with `git status` so you know whether unrelated user
  changes are already present

Do not overwrite unrelated dirty worktree changes. If the current checkout
cannot safely host the remediation, create or switch to the correct branch
without discarding existing work.

## Discover Project Verification Commands

Read the project guidance files and package manifests to determine the real
verification commands. For JavaScript or TypeScript projects, detect the
package manager from the lockfile before running anything. Capture, when
available:

- build
- typecheck
- lint
- lint-fix
- unit tests
- integration tests

Run the narrowest relevant checks while fixing each comment, then run the full
required verification before finishing.

## Gather Review Feedback

Use the best available source for unresolved review feedback:

- prefer GitHub connector tooling for PR metadata and flat comment reads when
  available
- use `gh api` GraphQL when you need thread IDs, resolution status, or reply
  context

The important data for each unresolved thread is:

- thread ID
- file path
- line number or diff context
- comment body
- original reviewer

If there are no unresolved threads, report that clearly and stop.

## Process Threads One by One

For each unresolved thread:

1. Read the referenced file and surrounding code.
2. Understand whether the reviewer is asking for a real code change, a naming
   cleanup, a test addition, or only an explanation.
3. Make the smallest correct fix that addresses the actual concern.
4. Re-run the relevant verification for that change.
5. If the comment points to a broader correctness problem, expand the fix far
   enough to make the branch safe, but stay scoped to the review request.

When a reviewer is simply asking a question and the existing code is correct,
do not churn the code just to make the thread go away. Reply with a grounded
explanation instead.

## Verification Standard

Do not resolve a thread until the relevant code path has been verified. At
minimum:

- run the targeted tests or checks needed for the fix
- ensure the broader project verification required by the repo still passes

If verification fails, keep working until you either fix it or can clearly
explain why the repo was already failing independently. Never reply “fixed” on
a thread while the branch is still broken.

## Commit Strategy

Group related review fixes into intentional commits. Avoid one commit per
comment if several comments are part of the same issue. Use clear commit
messages and push the branch after the fixes are verified.

Do not amend or rewrite history unless the user explicitly asks for it. If the
repo already has unrelated local changes, work around them rather than
reverting them.

## Reply and Resolve

After a thread is addressed:

- reply with what changed, or with the rationale for no code change
- resolve the review thread using the real thread ID, not just the comment ID

If GitHub tooling is unavailable, stop after making and verifying the fix and
tell the user that thread resolution could not be completed from the current
environment.

## Reporting

Finish with a concise summary that includes:

- PR identifier
- number of threads processed
- whether fixes were code changes, replies only, or both
- verification commands run
- whether the branch was pushed
- whether all unresolved threads were resolved

If anything remains open, list the blocker explicitly: missing auth, failing
verification, ambiguous feedback, or a thread that needs a human decision.

## Boundaries

Stay within files touched by the PR unless a review comment forces a broader
change. Do not turn a review-remediation task into a drive-by refactor. The
goal is to satisfy the actionable review feedback and leave the branch in a
mergeable state.
