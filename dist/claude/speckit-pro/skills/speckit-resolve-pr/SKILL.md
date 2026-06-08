---
name: speckit-resolve-pr
description: "MANDATORY for resolving GitHub PR review comments by editing the source code those comments flagged. Use this skill — NOT a read-only PR review skill — whenever the user wants to ACT on PR review feedback by changing code, committing, and pushing. Triggers on these phrases: 'resolve PR review comments', 'address review feedback', 'fix the copilot comments', 'resolve the threads on PR #N', 'fix each review comment and resolve the threads', 'handle the Copilot review on this PR', 'work through the review comments on this PR', 'address them all', 'take care of the outstanding review feedback', or whenever a PR URL is pasted with unresolved comments. The skill edits files, runs project verification, commits the fixes, pushes, posts a reply per thread, and marks each thread resolved via gh API. NOT for read-only PR review, summarizing what a PR changes, or assessing PR merge risk — those are read-only review skills, this is a write skill that mutates the working tree."
argument-hint: "PR URL or number (e.g., https://github.com/owner/repo/pull/46 or 46)"
user-invocable: true
allowed-tools: Bash Read Edit Write Grep Agent
license: MIT
---

# Resolve PR Review Comments

