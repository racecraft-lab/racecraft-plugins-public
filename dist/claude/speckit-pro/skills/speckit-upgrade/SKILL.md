---
name: speckit-upgrade
description: "Upgrades an existing SpecKit installation safely with backup-and-restore for locally-modified files. Preserves the project constitution and template overrides. Handles the v0.8.13 slash-command to skills migration. Supports upgrading one or both integrations (Claude Code, Codex CLI) and refreshing the curated set of community extensions and presets. Use when the user says \"upgrade speckit\", \"update speckit\", \"refresh speckit\", \"new speckit version\", \"latest speckit\", \"upgrade specify cli\", \"safe speckit upgrade\", \"speckit migration to skills\", \"preserve my constitution during upgrade\", or asks how to upgrade without losing template edits. Hands off to /speckit-pro:speckit-install if .specify/ is missing."
argument-hint: "(optional) integration keys to upgrade, e.g. 'claude', 'codex', or omit for all"
user-invocable: true
allowed-tools: Bash Read Edit Write
license: MIT
---

# SpecKit Upgrade

