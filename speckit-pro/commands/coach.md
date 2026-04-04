---
description: Get SDD coaching and SpecKit guidance. Ask about methodology, commands, troubleshooting, technical roadmaps, workflow tracking, or the speckit-pro plugin itself.
allowed-tools:
  - Read
  - Glob
  - Grep
argument-hint: "e.g. 'walk me through SDD', 'help with clarify', 'which checklists', 'how does autopilot work', 'consensus protocol'"
---

# SpecKit Coach

Provide SDD methodology coaching and SpecKit guidance.

## Invocation

The user asks a question about SDD, SpecKit commands, or the speckit-pro plugin:

```
/speckit-pro:coach walk me through SDD
/speckit-pro:coach help with clarify
/speckit-pro:coach how does the autopilot work
/speckit-pro:coach which checklist domains for my spec
```

## What to Do

1. **Load the speckit-coach skill** using the Skill tool: `Skill("speckit-coach")`
2. **Pass the user's question** to the skill
3. The skill contains routing tables and reference material — follow it exactly

## No Prerequisites

The coach skill works without SpecKit installed — it provides guidance on setup too.
