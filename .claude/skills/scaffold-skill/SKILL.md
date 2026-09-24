---
name: scaffold-skill
description: Scaffold a new skill inside speckit-pro (or another plugin in this marketplace). Creates skills/<name>/SKILL.md with valid YAML frontmatter, optionally mirrors under codex-skills/, then runs python3 tests/speckit-pro/run-all.py --layer 1 to verify. Triggers on "scaffold skill", "add a skill", "new speckit skill", "create skill in plugin".
license: MIT
---

# scaffold-skill

Scaffolds a new skill in a marketplace plugin. Both user-invocable and Claude-invocable.

## Inputs to ask for

1. **Plugin** — which plugin (default: `speckit-pro`)
2. **Skill name** — kebab-case, e.g. `my-skill`
3. **Description** — one sentence with concrete trigger phrases (the description is what Claude matches on; vague descriptions = skill never fires)
4. **Codex mirror** — required for a `speckit-pro` skill: Layer 1 fails when `skills/<name>/` has no `codex-skills/<name>/SKILL.md`. Create it with the Codex frontmatter and sidecar described below.
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

Codex mirror (required for `speckit-pro`):
```
<plugin>/codex-skills/<name>/
├── SKILL.md
└── agents/openai.yaml
```

The Codex `SKILL.md` frontmatter carries `name` and `description` only: Layer 1 rejects the Claude Code-only keys `license`, `user-invocable`, `disable-model-invocation`, and `argument-hint` there. Copy the `agents/openai.yaml` shape from a sibling Codex skill.

Optional `references/` and `scripts/` subdirs (only if user said yes).

## Post-create

Always run from the repository root:
```console
python3 tests/speckit-pro/run-all.py --layer 1
```

Add the new Codex skill's name to `validate_codex_skills_SKILLS` in `tests/speckit-pro/layer1-structural/validate-skill-contracts.py`. Layer 1 runs the Codex frontmatter checks only for skills listed there.

If Layer 1 fails, fix the SKILL.md before reporting success. A new skill under `speckit-pro/` changes shipped source, so also run `python3 scripts/refresh-release-artifacts.py`; the `artifact-consistency` CI job fails without it.

## What this does NOT do

- Does not touch `marketplace.json` or `release-please-config.json` (skills don't have their own version; they live inside a plugin)
- Does not commit (use `plugin-publish` skill for that, or commit manually)
- Does not write skill body content — only the frontmatter scaffold. User fills in the body.

## Hard rules

- Frontmatter must have at minimum `name` and `description`
- `name` in frontmatter must match the directory name
- Description must include concrete trigger phrases — not just "Helps with X"
- Codex mirror must have identical `name` to the Claude Code skill
