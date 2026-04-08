# /resolve-pr

Address all unresolved review comments on a pull request, fix the code,
and mark each thread resolved.

## Arguments

- `pr` (required): PR URL or number
  Examples: `https://github.com/owner/repo/pull/46`, `46`

## Workflow

1. **Parse Input** — extract OWNER, REPO, PR_NUMBER from the URL. If just a number,
   detect repo from `git remote -v`.

2. **Discover Project Commands** — read CLAUDE.md / AGENTS.md and package.json to find
   build, typecheck, lint, test commands.

3. **Fetch Unresolved Review Threads** — use `gh api graphql` to get all unresolved
   threads with thread IDs, file paths, line numbers, and comment bodies.

4. **Process Each Comment**:
   - Read the referenced file at the specified line
   - Determine action: code fix, style fix, question reply, or false positive
   - For code fixes: edit file, run verification (`build && typecheck && test`),
     commit with `git commit -m "fix: address review - <summary>"`
   - For style fixes: run lint fix, commit
   - For questions/false positives: prepare a reply

5. **Reply and Resolve** — for each comment, reply via `gh api` and resolve the
   thread via GraphQL `resolveReviewThread` mutation.

6. **Push** — `git push` all commits.

7. **Report Summary** — comments processed (code fixes, style fixes, replies),
   commits pushed, threads resolved, any remaining unresolved.
