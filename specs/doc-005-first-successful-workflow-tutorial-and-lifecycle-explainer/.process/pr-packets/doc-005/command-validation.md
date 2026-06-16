# DOC-005 Command Validation

Validated from the DOC-005 worktree on 2026-06-16.

## Commands Checked

| Evidence | Result |
| --- | --- |
| `specify version` | Reported Specify CLI `0.10.3.dev0` on Darwin arm64. |
| `specify init --help` | Includes `specify init --here --integration codex --integration-options="--skills" --script sh`. |
| `specify integration list` | Lists `codex` as the Codex CLI integration key and marks it multi-install safe. |
| `find speckit-pro/codex-skills -maxdepth 2 -name SKILL.md -print` | Found `grill-me`, `speckit-prd`, `speckit-status`, `speckit-scaffold-spec`, and `speckit-autopilot` skill entrypoints. |

## Published Snippet

```bash
specify init --here --integration codex --integration-options="--skills" --script sh
```

This snippet is used only for Codex Spec Kit initialization guidance. Claude
Code setup remains linked to the Claude Code install route.
