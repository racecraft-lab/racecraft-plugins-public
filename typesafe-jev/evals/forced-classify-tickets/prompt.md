---
tags: [forced]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

Use the `evaluate` MCP tool to decide, for each ticket in `tickets.json`, which team should own it. Report one owner per ticket id.
