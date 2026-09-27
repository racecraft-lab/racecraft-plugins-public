# Test Suite Instructions

This directory contains repository-only validation. Keep tests deterministic
unless a test file explicitly marks a live or operator-only path.

## Local Rules

- Use `suite-manifest.json` as the source of truth for layers, labels, dispatch,
  and default selection.
- Keep the default local suite (`run-all.py`) on Python 3.11+ standard library.
  A check that needs a third-party package follows constitution II: pinned in
  one repository-owned source, installed into an isolated virtual environment,
  run in its own layer or CI job, and failing, never skipping, when the package
  is missing.
- Do not add active shell or `jq` dependencies.
- If a `.md`, `.py`, or `.sh` file under this tree changes, regenerate or check
  the committed docs-site test reference page before finishing.
- Keep fixture changes narrow and explain why generated or proof data changed.
