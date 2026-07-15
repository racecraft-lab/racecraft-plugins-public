# Test Suite Instructions

This directory contains repository-only validation. Keep tests deterministic
unless a test file explicitly marks a live or operator-only path.

## Local Rules

- Use `suite-manifest.json` as the source of truth for layers, labels, dispatch,
  and default selection.
- Keep repo-owned test tooling on Python 3.11+ standard library.
- Do not add active shell or `jq` dependencies.
- If a `.md`, `.py`, or `.sh` file under this tree changes, regenerate or check
  the committed docs-site test reference page before finishing.
- Keep fixture changes narrow and explain why generated or proof data changed.
