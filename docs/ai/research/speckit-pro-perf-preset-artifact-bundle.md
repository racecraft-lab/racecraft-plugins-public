# Preset strategies, `specify artifact` and bundles against speckit-pro

> Status: research complete for ticket #1173 (map #1144). Research only. No plugin behavior changes.
> Snapshot: 2026-10-04. speckit-pro 2.40.0 (main at f7c97c1af). Upstream github/spec-kit tag v1.1.0, commit f1d3a4f8337ebbd3ae22760a9c12e3352b93a175.
> Upstream citations are `path:line` in that tag. speckit-pro citations are `path:line` on main at the snapshot. ADRs 0013, 0017 and 0018 are cited from branch `docs/speckit-pro-planning-performance` (they are not on main yet).
> Builds on `docs/ai/research/speckit-pro-perf-native-spec-kit.md` (branch `research/perf-native-spec-kit`, ticket #1147).

## Short answer

None of the three speeds up the plan stage. The plan stage is dominated by consensus waits, serial executors and artifact authoring (prior measurement), and these three features touch install, template layout and inventory only.

| Capability | Could speckit-pro use it | Plan-stage time or tokens | Recommendation |
| --- | --- | --- | --- |
| Preset composition (`append`, `prepend`, `wrap`) | Yes, for the reviewability preset. About 85 inserted lines replace a 580-line fork. All reviewability sections move to the end of each template. | None measured. Composed output is within 1% of the fork's size. | Adopt as a maintenance change, together with a real installer. Not a speed change. |
| `specify artifact` | Not for the planning manifest or phase brief. It inventories commands, templates, scripts and hooks, not feature files. | None. | Reject for ADR 0013, 0017 and 0018. Defer a narrow diagnostic use. |
| Bundles | Not today. Hooks are not a bundle component, speckit-pro ships no extension, and its presets and curated extensions cannot be resolved from default catalogs. | None. | Defer. Revisit only if speckit-pro hosts its own install-allowed catalog. |

Two findings matter more than the three verdicts:

1. **A fresh project has no way to get the reviewability preset from the plugin.** The generator was deleted on 2026-07-08 and nothing replaced it. The scaffold skill stops when the preset is absent.
2. **The curated extension and preset install flow fails on default catalogs at v1.1.0.** `specify extension add verify`, `extension add review` and `preset add claude-ask-questions` all refuse with "discovery-only" (measured). The install and upgrade skills tell the operator to run exactly those commands.

## What was run

Everything below marked "measured" ran against the CLI built from the v1.1.0 tag, in throwaway projects outside this repository. No model calls.

- `specify init` of two scratch projects (Claude integration), then `preset add --dev`, `preset resolve`, `preset list --json`, `artifact list --json`, `artifact info`, `bundle validate`, `bundle install`, `bundle search`, `extension add`, `preset add`.
- Template composition through `.specify/scripts/bash/resolve-template.sh`, the same function (`resolve_template_content`) that `setup-plan.sh`, `setup-tasks.sh` and `create-new-feature.sh` call.
- Template drift: raw templates at v0.5.1, v0.8.0 and v1.0.1 diffed against v1.1.0.

Nothing here ran a plan end to end on a model. Estimates are labeled.

## 1. Preset composition strategies

### What it is

- Default is **replace**: the first match in the priority stack wins entirely. Templates and commands can also use **prepend** (preset text before lower-priority text), **append** (after it) and **wrap** (replaces the `{CORE_TEMPLATE}` placeholder with lower-priority text). Scripts support replace and wrap (`docs/reference/presets.md:202`).
- The stack, highest first: project-local overrides, installed presets by priority (lower number wins), extensions, core (`docs/reference/presets.md:204-209`).
- The composition code joins layers with a blank line: prepend is `layer + "\n\n" + content`, append is `content + "\n\n" + layer`, wrap is `layer.replace("{CORE_TEMPLATE}", content)` (`src/specify_cli/presets/_resolver.py:886-905`). The shell and Python script resolvers implement the same three (`scripts/python/common.py:612-670`, `scripts/bash/common.sh:626`).
- Templates reach the agent through scripts that call the composing resolver: `scripts/bash/setup-plan.sh:46` writes the composed plan template to `plan.md`, `scripts/bash/setup-tasks.sh:54` and `scripts/bash/create-new-feature.sh:441` do the same for tasks and spec.
- A manifest entry sets `strategy:` per file (`src/specify_cli/presets/_manifest.py:245-260`). Composition is whole-file only. There is no insert-at-heading, no section merge and no more than one `{CORE_TEMPLATE}` insertion point per wrapper.
- Composition strategies exist since v0.8.0 (`CHANGELOG.md:1735`). A wrap loop bug was fixed in v1.0.4 (`CHANGELOG.md:259`).

### The reviewability preset today

- `.specify/presets/speckit-pro-reviewability/preset.yml:15-31` declares three templates, each `type: "template"` with `replaces:` and no `strategy`, so each is a full replace.
- Sizes: 155 (plan), 162 (spec), 263 (tasks) lines, 580 total, 21,785 bytes. The preset requires `speckit_version >=0.5.1` (`preset.yml:12-13`).
- Diffed against the v1.1.0 core templates, the fork adds about 85 lines and changes a few cosmetic ones:
  - Spec: 31 inserted lines, one block after line 100 (Reviewability Notes, Reviewability Budget, PR Review Packet Requirements).
  - Plan: 42 inserted lines in three hunks (a Reviewability Budget line in Technical Context; `## Module and Interface Deltas` with `## Declared File Operations`; a "generated plan MUST also define" list), plus 7 rendered command-name lines.
  - Tasks: 11 inserted lines in four hunks (a Reviewability paragraph, task `T009A`, a PR-packet task, and an Avoid line), plus 1 rendered command-name line.
- The runner reads one heading from these sections: `## Declared File Operations` (`speckit-pro/speckit_pro_runner/helpers/read_only.py:6319`, a line-by-line match, so it does not depend on position).

### How a fresh project gets the preset today

It does not, except by manual copy. Where I looked, and what I found:

- **Plugin payload.** `find` for `preset.yml` and `bundle.yml` under the repository returns one file: the dogfood copy at `.specify/presets/speckit-pro-reviewability/preset.yml`. `speckit-pro/` and the built `dist/` payloads contain no preset directory.
- **Install skill.** Step 5 compares the project to `speckit-pro/scripts/curated-set.json` and offers those entries (`speckit-pro/skills/speckit-install/SKILL.md:206-238`). The roster has five third-party extensions and one third-party preset, `claude-ask-questions` (`curated-set.json:1-30`). The reviewability preset is not in it.
- **Upgrade skill.** Step 8 does the same (`speckit-pro/skills/speckit-upgrade/SKILL.md:355-380`). It never touches `.specify/presets/`, so a forked preset also goes stale silently on a Spec Kit upgrade.
- **Scaffold skill.** Step 5.0 reads "Require the generic `speckit-pro-reviewability` preset to already exist in the worktree. If the preset is absent, STOP and report the missing prerequisite" (`speckit-pro/skills/speckit-scaffold-spec/SKILL.md:810-812`). It names no way to create it.
- **Runner.** `detect_presets` only reads existing presets (`read_only.py:1884-1925`) and special-cases this one by name (`read_only.py:1901-1902`). No runner code writes a preset.
- **History.** A generator did exist: `speckit-pro/skills/speckit-coach/scripts/ensure-reviewability-preset.sh` (353 lines), added in f85c2368a (2026-05-07, #46) and deleted in 7bc6be1a9 (2026-07-08, #297, the Bash eradication). It copied the host project's core templates, inserted the reviewability blocks at string markers, wrote `preset.yml` and a README, and wrote `.specify/presets/.registry` itself (priority capped at 5). It also appended `**/.process/** linguist-generated=true` to `.gitattributes`. By 2026-07-12 (fb9a773b9) the scaffold skill said the helper "is deferred and unavailable"; that sentence was removed on 2026-09-09 (95ff29475). Nothing replaced either job. The only `.gitattributes` rule I found is the repository's own.
- **The dogfood copy is hand-maintained.** Its registry entry reads `source: "project-local-generated"`, `manifest_hash: "project-local-generated"`, `installed_at: "generated-by-speckit-pro-setup"` (`.specify/presets/.registry:3-10`). The CLI never wrote it. Its README still says setup generates the preset and still names the deleted helper (`.specify/presets/speckit-pro-reviewability/README.md:3-4,16-17`).

Measured: in a fresh v1.1.0 project, `specify preset add --dev <path-to-the-dogfood-preset> --priority 5` installs it, writes a normal registry entry (sha256 `manifest_hash`, `source: local`), and `specify preset resolve plan-template` reports it as the top layer. So the native command works. Only the delivery of the files is missing.

### Trial: the same sections as `append`

I built a throwaway preset with the 85 inserted lines as three `strategy: "append"` files and installed it with `preset add --dev`.

- `preset resolve plan-template` printed the chain `[base] core`, then `[append] <preset>`.
- Composed sizes against the fork: plan 5,695 vs 5,714 bytes, spec 6,036 vs 6,034, tasks 10,115 vs 10,037 (the trial's tasks body carried one extra changed line). Lines: 157, 164, 266 vs 155, 162, 263.
- Every reviewability section is present. All of them sit after the core content. In the plan, that means after `## Complexity Tracking`: the Budget line, `## Module and Interface Deltas` and `## Declared File Operations` run together at the end, and the loose Budget line has lost its place inside Technical Context.
- A `wrap` template cannot fix that. It can put text before and after the core, not between two core headings.

### Could speckit-pro use it, and for what

Yes, for one job: stop forking the core templates. The fork's only upstream-tracking mechanism was the deleted generator. Composition gives the same property with no code. The resolver re-reads the core on every use, so a Spec Kit upgrade flows through, and only the 85 reviewability lines stay speckit-pro's to maintain.

How much that is worth is modest. Template drift in the core is small:

| Window | spec | plan | tasks |
| --- | --- | --- | --- |
| v0.5.1 to v1.1.0 (the preset's floor) | 13 changed lines | 37 | 11 |
| v1.0.1 to v1.1.0 | 0 | 0 | 0 |

The v0.5.1 changes are trailing-whitespace edits and the move from `/speckit.plan` literals to `__SPECKIT_COMMAND_PLAN__` placeholders. That second change is the kind a fork misses. Core templates in an initialized project are rendered for the active integration at init (the scratch project's composed plan template shows `/speckit-plan`), so composition inherits the host's own invocation style.

### What blocks it on Claude Code and Codex

- **No host-specific blocker for templates.** Both hosts read templates through the same `.specify/scripts/` resolvers. A templates-only preset registers no commands (`registered_commands: {}` in the scratch registry), so the rule that preset commands reach only the active integration (`docs/reference/presets.md:200`) does not apply.
- **PyYAML on the first `python3`.** The bash resolver parses the preset manifest with Python and returns an error if none is found (`scripts/bash/common.sh:626-700`). The upgrade skill already checks this (`speckit-pro/skills/speckit-upgrade/SKILL.md:186-196`). Composition adds no new requirement.
- **Placement.** The Budget line and Module Deltas lose their mid-document position (see the trial). Whether that changes plan quality or gate G3 results needs a model run. Not tested.
- **Tests read the fork.** `tests/speckit-pro/layer1-structural/validate-spec-templates-and-extensions.py:23-24,68-74` and `validate-skill-contracts.py:277-278` read the preset template files directly. They would need to assert on composed output (via `resolve-template.sh`) instead.
- **Delivery.** The preset directory has to ship in both plugin payloads (Claude and Codex), and the skills need a plugin-relative path on each host (`${CLAUDE_PLUGIN_ROOT}` on Claude, a skill-relative path on Codex, the pattern the install skill already uses at `SKILL.md:221-226`). Payload inventory checks (`speckit-pro/speckit_pro_runner/install_inventory.py`) will need to know the new files. I did not trace those checks.
- **Updates are destructive.** `specify preset update` removes, then adds, with no rollback; a failed add leaves no preset (`docs/reference/presets.md:34-70`). The upgrade skill would need to snapshot the preset directory first, or the scaffold skill's STOP fires after a bad upgrade.
- **Version floor.** Composing templates through the shell scripts has a known fix at v1.0.4 (`CHANGELOG.md:259`). Set `requires.speckit_version` to at least `>=1.0.4`; the current `>=0.5.1` is too low.

### Effect on plan-stage time or tokens

None, measured on size and estimated for the rest. The agent receives the same sections either way. The plan template is about 5.7 KB in both forms, roughly 1.5K tokens at 4 bytes per token (estimate), read once per plan run. Against the baseline of 93.8 min and 38.9M tokens (prior digest, private notes), that is noise. The gain is maintenance: a smaller surface to review, and upstream template changes arrive without a rebuild.

### Recommendation: adopt, as a maintenance change

Adopt `append` for the three reviewability templates, and in the same change give the preset a real installer: ship the directory in the plugin and have install, upgrade and scaffold run `specify preset add --dev <plugin path> --priority 5`. The installer gap is the bigger problem, and composition makes it cheap to close, because the plugin no longer has to generate anything from the host's core. Do not sell it as a speed-up.

Acceptance checks for the follow-up: composed output contains every section the gate and runner read; `preset resolve` shows `[append]` over `[base] core` on both hosts; a plan run on a model passes G3 with the end-of-file placement; the upgrade path survives a failed `preset update`.

## 2. `specify artifact`

### What it is

- A read-only inventory of **commands, templates, scripts and hooks**, "regardless of which layer contributes it" (`docs/reference/artifacts.md:3`). It answers "what exists and what is the composition stack behind it" (`artifacts.md:5`).
- Subcommands: `list`, `info <name>`, `lookup <lookupId>`. All require `--json`; omitting it exits 2 with a usage message (`artifacts.md:7`, measured: exit 2, "text output is not yet implemented").
- Row shape: `id`, `name`, `kind`, `description`, `stack` (`artifacts.md:68-74`). The kind is one of `command`, `template`, `script`, `hook` (`artifacts.md:72`; `src/specify_cli/artifacts/models.py:11`). Stack rows carry layer, preset or extension id, strategy, `active`, `hidden`, `manifestPath`, `lookupId`, `sourcePath` (`artifacts.md:134-146`).
- Hook rows report registration from `.specify/extensions.yml`, not condition results (`artifacts.md:220`). Skills are excluded (`artifacts.md:76`).
- Added in v1.0.7 (`CHANGELOG.md:189,192`).

Measured on a fresh project: `artifact list --json` returned 19 rows (10 commands, 5 templates, 4 scripts), 11.6 KB, in about 0.45 s. `artifact info template:plan-template --json` showed the `append` layer over the core layer, with `lookupId` and `sourcePath`.

### Could the planning manifest or phase brief use it

No. The planning manifest in ADR 0013 and 0017 is a deterministic list of repository-relative **feature files** with content digests: `spec.md`, `plan.md`, normalized task definitions, contracts, research, checklists, formal models and verification settings. ADR 0013 says the runner must "inventory every authoritative input consumed by the planner or executor and derive the manifest from that inventory". The phase brief in ADR 0018 lists the agent to dispatch, its inputs, the files it may read and the gate to check. All of that is about the files of one feature. `specify artifact` has no row for any of them. It knows what Spec Kit defines, not what a feature produced.

The runner already has the right primitives for its own inventory: `PLANNING_DOCUMENTS` (`speckit-pro/speckit_pro_runner/execution_control.py:63-64`) and `fingerprints` (`speckit-pro/speckit_pro_runner/task_execution.py:30`), which hashes spec, plan and checkbox-normalized tasks. Reading files and hashing them needs no external CLI.

One narrow overlap exists. The templates and commands that shape a plan are arguably planning inputs: a preset change alters what `plan.md` contains. `artifact info` returns the stack with `sourcePath` for each layer. The runner can get the same by hashing those template files directly, so this does not justify a CLI dependency.

A second overlap is diagnostic. `detect_presets` hand-parses `preset.yml` with a regex, counts hook lines in `extensions.yml`, and hardcodes this preset's template string (`read_only.py:1884-1925`). `preset list --json` (`docs/reference/presets.md:89-100`) and `artifact list --json` hook rows would replace that parsing. The gain is code deleted from a read-only helper, not time.

### What blocks it on Claude Code and Codex

- Nothing host-specific. It is a host-neutral CLI. The runner already locates it with `shutil.which("specify")` (`speckit-pro/speckit_pro_runner/runtime.py:144`).
- It needs `specify >= 1.0.7` on PATH and a project with `.specify/`. Outside one it exits 1 with a JSON error on stderr (`artifacts.md:226-239`).
- The runner contract is "zero Bash" and structured helpers. A new subprocess dependency in a read-only helper would need a fail-open path for a missing or older CLI.

### Effect on plan-stage time or tokens

None. One call costs about 0.45 s (measured) and the output would not replace any read the plan stage does today.

### Recommendation: reject for the manifest and brief, defer the diagnostic use

Reject it for ADR 0013, 0017 and 0018: the data model does not cover feature files. Defer the `detect_presets` cleanup; it is cosmetic and needs a version floor.

## 3. Bundles

### What it is

- A versioned, installable unit that composes **extensions, presets, workflows and steps** through each primitive's own installer (`docs/reference/bundles.md:3`; `src/specify_cli/bundles/manifest.py:21`). It adds no runtime behavior (`bundles.md:3`).
- The manifest is `bundle.yml`. Every extension, preset and workflow entry must pin a `version`; every preset entry must also declare `priority` and `strategy` (`manifest.py:195-216`).
- `bundle install` initializes a project if needed, skips components already present, and aborts with no changes if the bundle pins a different integration than the project's (`bundles.md:72`). Version pins apply only on first install or refresh (`bundles.md:100`). A failed refresh does not roll back (`bundles.md:80`).
- First-party bundles are `bugfix` and `assess` (`bundles.md:14-21`). Community bundles are discovery-only by default (`bundles.md:171-172`).

### Could speckit-pro ship its presets, extensions and hooks as one bundle

Not as the question assumes, for four reasons.

1. **Hooks are not a component.** The component kinds are extensions, presets, steps, workflows (`manifest.py:21`). Hooks arrive only inside an extension (`.specify/extensions.yml`). The plugin's own Claude and Codex hooks (`speckit-pro/hooks/`, `speckit-pro/codex-hooks.json`) are outside Spec Kit and no bundle can install them.
2. **speckit-pro ships no extension.** `find speckit-pro -name extension.yml` returns nothing. The curated set is five community extensions and one community preset (`curated-set.json`). A bundle can only reference them.
3. **References resolve only from the wheel or an install-allowed catalog.** A preset ref is installed from assets bundled in the Spec Kit wheel, else from a preset catalog (`src/specify_cli/bundles/primitives.py:181-237`). Extensions work the same way (`primitives.py:271-331`). The ref's `source:` field is parsed and never used by the installers. The default community catalogs are `install_allowed=False` (`src/specify_cli/presets/_catalog.py:335-336`). Measured:
   - `specify bundle validate` on a one-preset bundle: "preset 'x' is not bundled, installed, or present in any active catalog."
   - `specify bundle install` on it: "Preset 'x' not found in any catalog."
   - `specify extension add verify` and `extension add review`: refused as discovery-only, with advice to use `--from <archive-url>` or a catalog "you curate and control".
   - `specify preset add claude-ask-questions`: refused as discovery-only.
4. **A preset `strategy` in a bundle is recorded, not applied.** It is required by validation (`manifest.py:210-214`) but only stored and printed (`bundles/records.py:202`, `bundles/command_info.py:142-154`). The installer passes `priority` and nothing else (`primitives.py:186,230-231`). Composition is set by the preset's own manifest.

### Would it simplify install and upgrade

Only if speckit-pro hosts its own **install-allowed** catalog (preset, extension and bundle catalog JSON plus download archives) and each project adds it with `specify ... catalog add`. That moves work into the plugin: a catalog to publish and version, archives to host, and an operator step to trust it. Upstream warns that a project supplying its own catalogs "is not evidence anything in it was reviewed" (`bundles.md:179`). The bundle would also pin every component version, so each curated extension bump becomes a bundle release, and `bundle update` has no rollback.

What it would save: the install skill today asks the operator to confirm up to seven separate commands (five extensions, one preset, plus the reviewability preset once it exists). A bundle makes that one command. That is operator seconds, in an interactive step that is not on the plan stage's path. The bundle also does not replace the plugin install, the CLI install or the per-integration init that the install skill drives.

### What blocks it on Claude Code and Codex

- A bundle is integration-agnostic unless it pins one `integration.id`. A bundle for both hosts must stay agnostic and inherit the active integration (`bundles.md:72`). A project with both Claude and Codex installed has one active integration at a time, so one bundle install reaches one host's command registration until the other is switched (the same limit as `docs/reference/presets.md:200` for commands).
- No host difference beyond that. Both hosts shell out to the same CLI.

### Effect on plan-stage time or tokens

None. Bundles act at install time.

### Recommendation: defer

Do not build a bundle now. First fix the install flow that exists (next section). Revisit bundles if speckit-pro decides to host a curated catalog; at that point a bundle is a thin manifest on top of it.

## Side findings (outside the three questions)

- **Curated install commands fail at v1.1.0 defaults.** The install and upgrade skills hand the operator `specify extension add <id>` or `specify preset add <id>` (`speckit-install/SKILL.md:230-238`, `speckit-upgrade/SKILL.md:373-377`). `curated-set.json` has no source URLs, and the default community catalogs refuse installs. Measured on a fresh project. Not checked: whether the author's user-level catalog config differs. Needs its own ticket.
- **Stale references in the preset.** The plan template points at `estimate-reviewable-loc.sh` (retired in #297), and the preset README names the deleted helper. An append rewrite is the natural moment to fix both.
- **The `.gitattributes` collapse rule** the old generator added for `.process/` files has no replacement in the plugin.

## Not confirmed

- Whether end-of-file placement of the reviewability sections changes plan quality, gate G3 results or consensus behavior. Needs a model run on both hosts.
- Whether any gate, validator or skill depends on section order in the three templates. I found the one heading the runner reads and the three test files that read the fork, not a full dependency list.
- Whether `specify preset add --dev` from a plugin cache path is stable across plugin updates, and how the Codex payload should carry the directory.
- Which release first made `resolve_template_content` available to all three setup scripts. The v1.0.4 floor comes from a changelog fix, not from a bisect.
- Whether a user-level or project-level catalog config on any real project changes the discovery-only results.
- Bundle behavior beyond the paths I ran: refresh, update, remove and the on-demand project init were read in source and docs, not exercised.
- Plan-stage savings above are estimates or zero by construction. Nothing here measured a plan run.

## Follow-ups this suggests

1. Ship the reviewability preset as an `append` preset and install it with `specify preset add --dev` from install, upgrade and scaffold. Restore the `.gitattributes` rule in the same change or drop it deliberately.
2. Fix the curated-set install commands (per-entry `--from` URLs, or a documented catalog step).
3. Leave ADR 0013, 0017 and 0018 manifest and brief design as they are. Do not add a `specify artifact` dependency.
