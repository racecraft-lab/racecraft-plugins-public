---
description: Address all GitHub Copilot review comments on a PR, fix the code, and mark threads resolved using gh CLI.
allowed-tools: "*"
argument-hint: "PR URL or number (e.g., https://github.com/owner/repo/pull/46 or 46)"
---

# Resolve PR Review Comments

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

### 4. Process Each Comment

For EACH unresolved comment:

```text
1. Read the comment body and the file it references
2. Read the referenced file at the specified line
3. Understand what the reviewer is asking for
4. Determine the action:

   a. CODE FIX needed:
      - Edit the file to address the comment
      - Run verification: Bash("<BUILD> && <TYPECHECK> && <UNIT_TEST>")
      - If verification fails, fix until it passes
      - Stage and commit:
        Bash("git add <file> && git commit -m \
          'fix: address review - <brief summary>'")

   b. STYLE / FORMAT issue:
      - Run LINT_FIX command
      - Stage and commit

   c. QUESTION from reviewer:
      - Prepare a reply explaining the design rationale
      - Read relevant code context to ground the answer

   d. FALSE POSITIVE:
      - Prepare a reply explaining why no change is needed
```

### 5. Reply and Resolve Each Comment

After addressing each comment, reply AND resolve:

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
