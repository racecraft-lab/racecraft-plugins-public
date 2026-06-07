#!/usr/bin/env bash
# ensure-reviewability-preset.sh — Install the generic speckit-pro reviewability preset.
#
# Usage:
#   ensure-reviewability-preset.sh [project-root] [plugin-root] [preset-id]
#
# The installed preset is generated from the host project's current core
# templates, then augmented with reviewability sections. This avoids replacing
# project-specific template policy with a static plugin copy.

set -euo pipefail

PROJECT_ROOT="${1:-$PWD}"
PLUGIN_ROOT="${2:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PRESET_ID="${3:-speckit-pro-reviewability}"

PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"
PLUGIN_ROOT="$(cd "$PLUGIN_ROOT" && pwd)"

# Ensure the consuming project's repo-root .gitattributes carries the .process/
# collapse rule (FR-009). Idempotent + corruption-safe: fixed-string whole-line
# presence guard, trailing-newline normalize before append, write to a
# same-directory temp then atomic rename.
ensure_collapse_rule() {
  local file="$PROJECT_ROOT/.gitattributes"
  local rule='**/.process/** linguist-generated=true'

  # Short-circuit if the rule is already present (whole-line, fixed-string match
  # because the rule contains '*' glob metacharacters).
  if [ -f "$file" ] && grep -qxF "$rule" "$file"; then
    return 0
  fi

  # Subshell scopes the cleanup trap locally. A bash RETURN trap is global — it
  # would leak and fire on every later function return; an EXIT trap inside a
  # subshell fires only when the subshell exits, so cleanup stays local.
  (
    tmp="$(mktemp "${file}.XXXXXX")"
    trap 'rm -f "$tmp"' EXIT

    if [ -f "$file" ]; then
      cat "$file" > "$tmp"
      # Normalize a missing trailing newline so the rule never concatenates onto
      # the last existing line (git-lfs#167).
      if [ -s "$tmp" ] && [ "$(tail -c1 "$tmp")" != "" ]; then
        printf '\n' >> "$tmp"
      fi
    fi
    printf '%s\n' "$rule" >> "$tmp"
    mv "$tmp" "$file"
  )
}

ensure_collapse_rule

if ! command -v python3 >/dev/null 2>&1; then
  printf '{"status":"block","error":"python3 is required to install the reviewability preset"}\n'
  exit 1
fi

PROJECT_ROOT="$PROJECT_ROOT" PLUGIN_ROOT="$PLUGIN_ROOT" PRESET_ID="$PRESET_ID" python3 - <<'PY'
import json
import os
from pathlib import Path

project_root = Path(os.environ["PROJECT_ROOT"])
plugin_root = Path(os.environ["PLUGIN_ROOT"])
preset_id = os.environ["PRESET_ID"]

specify_dir = project_root / ".specify"
templates_dir = specify_dir / "templates"
presets_dir = specify_dir / "presets"
preset_dir = presets_dir / preset_id
preset_templates_dir = preset_dir / "templates"
registry_path = presets_dir / ".registry"

required_templates = {
    "spec-template": templates_dir / "spec-template.md",
    "plan-template": templates_dir / "plan-template.md",
    "tasks-template": templates_dir / "tasks-template.md",
}

if not templates_dir.is_dir():
    print(json.dumps({
        "status": "block",
        "error": "SpecKit project templates were not found",
        "project_root": str(project_root),
        "expected": str(templates_dir),
    }))
    raise SystemExit(1)

missing = [name for name, path in required_templates.items() if not path.exists()]
if missing:
    print(json.dumps({
        "status": "block",
        "error": "Required core templates are missing",
        "missing": missing,
        "project_root": str(project_root),
    }))
    raise SystemExit(1)

SPEC_REVIEWABILITY_BLOCK = """### Reviewability Budget *(mandatory)*

<!--
  ACTION REQUIRED: Declare the expected review surface before planning.
  A spec that exceeds the block threshold must be split before implementation
  unless a ratified transition exception is recorded in the workflow and PR.
-->

- **Primary surface**: [schema/migration | API | UI | scheduler/runtime | harness/adapter | seed/config | docs/process]
- **Secondary surfaces, if any**: [List or N/A]
- **Projected reviewable LOC**: [Estimate excluding declared generated/lock/vendor artifacts]
- **Projected production files**: [Estimate]
- **Projected total files**: [Estimate]
- **Budget result**: [within budget | warning accepted | split required | transition exception]
- **Split decision**: [Why this remains one spec, or the exact follow-up specs]

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order,
  scope budget, traceability, verification evidence, known gaps, and rollback
  or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed
  files and verification evidence.
- Deferred work MUST name the follow-up spec or issue.
"""

PLAN_REVIEWABILITY_LINE = "**Reviewability Budget**: [Primary surface; projected reviewable LOC; production files; total files; budget result]"

PLAN_REVIEWABILITY_BLOCK = """For all specs, the generated plan MUST also define:

- The primary review surface and any secondary surfaces.
- Whether the spec stays within the reviewability budget from the project
  constitution: warn above 400 reviewable LOC, 6 production files, 15 total
  files, or more than one primary surface; block above 800 reviewable LOC,
  8 production files, 25 total files, or more than one primary surface unless a
  ratified split exception exists.
- The exact split decision when the budget is exceeded, including follow-up
  spec IDs or issue IDs for deferred work.
- The PR review packet source: what changed, why, non-goals, review order,
  scope budget, traceability, verification, known gaps, and rollback/flags.
"""

TASKS_REVIEWABILITY_BLOCK = """**Reviewability**: Generated tasks MUST preserve the spec's reviewability
budget. If task generation expands beyond 400 reviewable LOC, 6 production
files, 15 total files, or more than one primary surface, add an explicit
reviewability checkpoint task before implementation. If it expands beyond
800 reviewable LOC, 8 production files, 25 total files, or more than one
primary surface without a ratified exception, stop and split the spec instead
of adding more implementation tasks.
"""

TASKS_CHECKPOINT_TASK = "- [ ] T009A Verify reviewability budget against planned task/file scope and record split decision or exception before implementation"
TASKS_PR_PACKET_TASK = "- [ ] TXXX Generate or update the PR review packet with review order, scope budget, traceability, verification evidence, known gaps, and rollback/flag notes"
TASKS_AVOID_LINE = "- Avoid: expanding a task list past the reviewability budget instead of splitting the spec"


def insert_before(text: str, block: str, markers: list[str]) -> tuple[str, bool]:
    for marker in markers:
        index = text.find(marker)
        if index != -1:
            prefix = text[:index].rstrip()
            suffix = text[index:].lstrip("\n")
            return f"{prefix}\n\n{block.rstrip()}\n\n{suffix}", True
    return f"{text.rstrip()}\n\n{block.rstrip()}\n", True


def augment_spec(text: str) -> tuple[str, bool]:
    if "### Reviewability Budget" in text:
        return text, False
    return insert_before(text, SPEC_REVIEWABILITY_BLOCK, ["### Key Entities", "## Success Criteria"])


def augment_plan(text: str) -> tuple[str, bool]:
    changed = False
    if "Reviewability Budget" not in text:
        lines = text.splitlines()
        output = []
        inserted = False
        for line in lines:
            output.append(line)
            if not inserted and line.startswith("**Scale/Scope**:"):
                output.append(PLAN_REVIEWABILITY_LINE)
                inserted = True
                changed = True
        if not inserted:
            output.append(PLAN_REVIEWABILITY_LINE)
            changed = True
        text = "\n".join(output) + ("\n" if text.endswith("\n") else "")

    if "The primary review surface and any secondary surfaces" not in text:
        text, block_changed = insert_before(text, PLAN_REVIEWABILITY_BLOCK, ["## Project Structure"])
        changed = changed or block_changed
    return text, changed


def augment_tasks(text: str) -> tuple[str, bool]:
    changed = False
    if "**Reviewability**:" not in text:
        text, block_changed = insert_before(text, TASKS_REVIEWABILITY_BLOCK, ["**Organization**:"])
        changed = changed or block_changed

    if "T009A Verify reviewability budget" not in text:
        marker = "- [ ] T009 Setup environment configuration management"
        if marker in text:
            text = text.replace(marker, f"{marker}\n{TASKS_CHECKPOINT_TASK}", 1)
        else:
            text = f"{text.rstrip()}\n{TASKS_CHECKPOINT_TASK}\n"
        changed = True

    if "Generate or update the PR review packet" not in text:
        marker = "- [ ] TXXX Run quickstart.md validation"
        if marker in text:
            text = text.replace(marker, f"{TASKS_PR_PACKET_TASK}\n{marker}", 1)
        else:
            text = f"{text.rstrip()}\n{TASKS_PR_PACKET_TASK}\n"
        changed = True

    if TASKS_AVOID_LINE not in text:
        marker = "- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence"
        if marker in text:
            text = text.replace(marker, f"{marker}\n{TASKS_AVOID_LINE}", 1)
        else:
            text = f"{text.rstrip()}\n{TASKS_AVOID_LINE}\n"
        changed = True

    return text, changed


augmenters = {
    "spec-template": augment_spec,
    "plan-template": augment_plan,
    "tasks-template": augment_tasks,
}

preset_templates_dir.mkdir(parents=True, exist_ok=True)
changed_templates = []
for name, source in required_templates.items():
    original = source.read_text()
    augmented, changed = augmenters[name](original)
    target = preset_templates_dir / f"{name}.md"
    if not target.exists() or target.read_text() != augmented:
        target.write_text(augmented)
        changed_templates.append(name)

preset_manifest = f'''schema_version: "1.0"

preset:
  id: "{preset_id}"
  name: "SpecKit Pro Reviewability"
  version: "1.0.0"
  description: "Adds reviewability budgets and PR review packet requirements while preserving host project template policy."
  author: "speckit-pro"
  repository: "https://github.com/racecraft-lab/racecraft-plugins-public"
  license: "MIT"

requires:
  speckit_version: ">=0.5.1"

provides:
  templates:
    - type: "template"
      name: "spec-template"
      file: "templates/spec-template.md"
      description: "Feature specification template with reviewability budget and PR packet requirements."
      replaces: "spec-template"
    - type: "template"
      name: "plan-template"
      file: "templates/plan-template.md"
      description: "Implementation plan template with reviewability gate checks."
      replaces: "plan-template"
    - type: "template"
      name: "tasks-template"
      file: "templates/tasks-template.md"
      description: "Task template with reviewability checkpoint and PR packet task."
      replaces: "tasks-template"

tags:
  - "reviewability"
  - "verification-debt"
  - "speckit-pro"
'''

manifest_path = preset_dir / "preset.yml"
manifest_changed = not manifest_path.exists() or manifest_path.read_text() != preset_manifest
if manifest_changed:
    manifest_path.write_text(preset_manifest)

readme = f"""# SpecKit Pro Reviewability Preset

This preset is generated by `speckit-pro` setup from the host project's current
core templates. It adds reviewability budgets and PR review packet requirements
without editing `.specify/templates/*.md` directly.

After Spec Kit upgrades, verify resolution:

```bash
specify preset resolve spec-template
specify preset resolve plan-template
specify preset resolve tasks-template
```

Those commands should resolve to `.specify/presets/{preset_id}/templates/...`.
If they do not, rerun `$speckit-scaffold-spec` or the `ensure-reviewability-preset.sh`
helper instead of patching core templates.
"""
readme_path = preset_dir / "README.md"
readme_changed = not readme_path.exists() or readme_path.read_text() != readme
if readme_changed:
    readme_path.write_text(readme)

presets_dir.mkdir(parents=True, exist_ok=True)
if registry_path.exists():
    try:
        registry = json.loads(registry_path.read_text())
    except json.JSONDecodeError:
        registry = {}
else:
    registry = {}

registry.setdefault("schema_version", "1.0")
presets = registry.setdefault("presets", {})
entry = presets.setdefault(preset_id, {})
previous_entry = dict(entry)
entry.update({
    "version": "1.0.0",
    "source": "project-local-generated",
    "manifest_hash": "project-local-generated",
    "enabled": True,
    "priority": min(int(entry.get("priority", 5)), 5),
    "installed_at": "generated-by-speckit-pro-setup",
})
registry_changed = previous_entry != entry or registry_path.read_text() if registry_path.exists() else True
serialized_registry = json.dumps(registry, indent=2, sort_keys=True) + "\n"
if not registry_path.exists() or registry_path.read_text() != serialized_registry:
    registry_path.write_text(serialized_registry)
    registry_changed = True
else:
    registry_changed = False

changed = bool(changed_templates or manifest_changed or readme_changed or registry_changed)
print(json.dumps({
    "status": "installed" if changed else "present",
    "project_root": str(project_root),
    "plugin_root": str(plugin_root),
    "preset_id": preset_id,
    "preset_dir": str(preset_dir),
    "changed_templates": changed_templates,
    "manifest_changed": manifest_changed,
    "readme_changed": readme_changed,
    "registry_changed": registry_changed,
}))
PY
