---
description: Execute the installed archive sweep contract.
---

# Archive sweep command contract

Run the project-local executable below from the already-bound worktree root.
Do not execute integration-specific prerequisite metadata from `extension.yml`.

```text
python3 .specify/extensions/archive/bin/archive_sweep.py --repo-root . --current-target specs/spec-920-current --prerequisite-mode <native-worktree-binding> --output .specify/archive-sweep-result.json
```

`<native-worktree-binding>` is `claude_native_worktree_binding` for Claude and
`codex_native_worktree_binding` for Codex. Treat exit 0 plus
`status=no_candidates` as an executed no-op. Persist the returned object under
`archive_sweep` in `autopilot-state.json` before completing Archive Sweep.
