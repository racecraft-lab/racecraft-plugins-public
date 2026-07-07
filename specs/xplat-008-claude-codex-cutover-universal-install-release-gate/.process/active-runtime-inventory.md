# XPLAT-008 Active Runtime Inventory

This inventory defines which paths are active installed-runtime surfaces for
the XPLAT-008 no-shell/no-jq guard.

## Blocking Active Installed-Runtime Scope

| Category | Paths | Guard behavior |
|---|---|---|
| Claude skills | `speckit-pro/skills/**/*.md` except source-only references and scripts | Blocks required Bash, `.sh`, `jq`, Git Bash, WSL, PowerShell-specific command language, shell parsing, shell interpolation, and command-string subprocess guidance when presented as installed workflow execution. |
| Codex skills | `speckit-pro/codex-skills/**/*.md` except source-only references and scripts | Same as Claude skills. |
| Claude agents | `speckit-pro/agents/**/*.md` | Blocks shell-only installed workflow execution guidance. Tool permission names such as `Bash` are not a runtime prerequisite by themselves. |
| Codex agents | `speckit-pro/codex-agents/**/*.toml` | Blocks shell-only installed workflow execution guidance. |
| Hooks | `speckit-pro/hooks/hooks.json`, `speckit-pro/codex-hooks.json` | Blocks shell parsing, `jq`, and shell command strings for installed hook behavior. |
| Generated payload runtime files | `dist/claude/speckit-pro/**`, `dist/codex/speckit-pro/**` | Blocks prohibited shell-only active behavior after generated payload rebuild. |
| Install guidance | `README.md`, `speckit-pro/README.md`, `docs-site/src/content/docs/install/**`, `docs-site/src/content/docs/first-run.md`, `docs-site/src/content/docs/troubleshooting.md`, `docs-site/src/content/docs/security-and-trust.md`, `docs-site/src/content/docs/update-and-rollback.md` | Blocks statements that make Bash, Git Bash, WSL, PowerShell-specific command language, or `jq` required for installed plugin workflows. |
| Release gates | `.github/workflows/pr-checks.yml`, `.github/workflows/release.yml` | Allows only minimal CI dispatch glue that directly invokes `python -m speckit_pro_runner`; blocks plugin validation logic implemented through shell pipelines. |

## Explicit Exceptions

| Category | Paths | Guard behavior |
|---|---|---|
| Archive/provenance | `.specify/memory/**` | Allowed. Historical command text is not active installed runtime behavior. |
| Upstream Spec Kit generated helpers | `.specify/scripts/bash/**` | Allowed. These belong to consumer Spec Kit projects, not SpecKit Pro installed runtime. |
| Tests and fixtures | `tests/**`, `speckit-pro/**/scripts/**`, `speckit-pro/**/templates/**`, `speckit-pro/**/references/**` | Allowed as source-checkout validation or parity evidence unless explicitly named by a release gate. |
| Docs prose outside install/runtime claims | `docs/**`, `docs-site/**` outside the install/trust/update/first-run surfaces | Allowed unless included by a public-claim release check. |
| CI docs validation | `.github/workflows/deploy-docs.yml`, docs-only jobs in `pr-checks.yml` | Allowed as docs tooling, not installed runtime behavior. |

## Runner Invocation Contract

Active installed surfaces use a resolved Python `>=3.11` interpreter and invoke
the runner as:

```text
[resolved_python, "-m", "speckit_pro_runner"]
```

The surface sends one JSON request on stdin, reads one JSON response from
stdout, treats stderr as diagnostics only, and never uses a shell fallback.

