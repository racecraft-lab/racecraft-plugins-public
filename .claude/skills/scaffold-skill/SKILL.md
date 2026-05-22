---
name: scaffold-skill
description: Scaffold a new skill inside speckit-pro (or another plugin in this marketplace). Creates skills/<name>/SKILL.md with valid YAML frontmatter, optionally mirrors under codex-skills/, then runs bash tests/run-all.sh --layer 1 to verify. Triggers on "scaffold skill", "add a skill", "new speckit skill", "create skill in plugin".
license: MIT
---

# scaffold-skill

Scaffolds a new skill in a marketplace plugin. Both user-invocable and Claude-invocable.

## Inputs to ask for

1. **Plugin** — which plugin (default: `speckit-pro`)
2. **Skill name** — kebab-case, e.g. `my-skill`
3. **Description** — one sentence with concrete trigger phrases (the description is what Claude matches on; vague descriptions = skill never fires)
4. **Codex mirror** — yes/no. If yes, also create under `codex-skills/<name>/SKILL.md`
5. **References / scripts** — does the skill need supporting files? Default: no (start minimal per CLAUDE.md "Simplest change" rule)

## What this creates

```
<plugin>/skills/<name>/
└── SKILL.md
```

With frontmatter:
```yaml
---
name: <name>
description: <description>
license: MIT
---
```

Optional Codex mirror:
```
<plugin>/codex-skills/<name>/
└── SKILL.md
```

Optional `references/` and `scripts/` subdirs (only if user said yes).

## Post-create

Always run:
```bash
cd <plugin> && bash tests/run-all.sh --layer 1
```

If Codex mirror created, also run:
```bash
cd <plugin> && bash tests/layer1-structural/validate-codex-skills.sh
```

If either fails, fix the SKILL.md before reporting success.

## What this does NOT do

- Does not touch `marketplace.json` or `release-please-config.json` (skills don't have their own version; they live inside a plugin)
- Does not commit (use `plugin-publish` skill for that, or commit manually)
- Does not write skill body content — only the frontmatter scaffold. User fills in the body.

## Hard rules

- Frontmatter must have at minimum `name` and `description`
- `name` in frontmatter must match the directory name
- Description must include concrete trigger phrases — not just "Helps with X"
- Codex mirror must have identical `name` to the Claude Code skill
