---
name: speckit-install
description: "Installs the official SpecKit CLI and initializes one or both coding-agent integrations (Claude Code, Codex CLI). Detects existing installs and hands off to /speckit-pro:speckit-upgrade rather than overwriting. Optionally installs the curated set of community extensions and presets. Use when the user says \"install speckit\", \"set up speckit\", \"initialize speckit\", \"add speckit to this repo\", \"install spec-kit\", \"bootstrap speckit\", \"first-time speckit setup\", \"install the specify cli\", \"set up specify\", or wants to install for claude only, codex only, or both side-by-side. Not for upgrading an existing install (use /speckit-pro:speckit-upgrade) or running workflows (use /speckit-pro:speckit-autopilot)."
argument-hint: "(optional) integration keys, e.g. 'claude', 'codex', or 'claude codex'"
user-invocable: true
allowed-tools: Bash Read Edit Write
license: MIT
---

# SpecKit Install

