# Quickstart: TACD-002 Capability Discovery Directive and Agent Updates

## Prerequisites

- Work from the TACD-002 worktree root.
- Do not create or rename the branch during TACD-002 Plan or implementation.
- Keep TACD-003 prerequisite/user-facing messaging and TACD-004 enforcement/eval work out of scope.

## Validation Scenario 1: Source Guidance Uses The Shared Directive

1. Confirm the shared directive exists:

   ```bash
   test -f speckit-pro/skills/speckit-autopilot/references/capability-discovery.md
   ```

2. Review the scoped Claude and Codex source guidance surfaces.

Expected outcome:

- Claude agents and shared references point to `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`.
- Codex TOML agents point to the directive when stable or embed a compact equivalent with the source-note marker `Capability discovery equivalent: mirrors speckit-pro/skills/speckit-autopilot/references/capability-discovery.md for installed Codex TOML runtime.`
- Active behavior text chooses by capability category, not by default named optional MCP preference.
- Capability categories are not treated as a fixed fallback chain; guidance selects by task fit and evidence quality before fallback.

## Validation Scenario 2: Evidence And Fallback Wording Are Present

Review scoped runtime guidance for the required evidence formats:

```text
Capability path: <need> -> <selected capability/source>; Evidence: <citations or local file refs>; Confidence: <high|medium|low> (<brief reason>)
```

```text
No installed <capability> was available/usable; used <local/native/repo-local fallback>; confidence is <medium|low> because <reason>.
```

Expected outcome:

- Guidance tells agents to report capability path, evidence, and confidence.
- Guidance allows local, native platform, or repo-local fallback evidence when optional installed capabilities are missing, unavailable, or present but unusable.
- Fallback confidence is constrained to `medium` or `low` and does not overclaim high confidence.
- Guidance avoids full installed-tool inventories in normal answers.

## Validation Scenario 3: Metadata IDs Are Preserved And Classified

Review metadata fields that still contain concrete IDs:

- Codex dependency values in `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml`.
- Claude frontmatter `tools:` allowlist IDs in scoped agents.
- Generated manifest or path rewrite metadata, if present after payload refresh.

Expected outcome:

- The PR packet includes a preserved-ID table with file, field, classification, and behavior-scan result.
- Body prose and Codex TOML developer instructions no longer express named optional tools as preferred default behavior.

## Validation Scenario 4: Generated Payloads Are Refreshed From Source

Run:

```bash
bash scripts/build-plugin-payloads.sh
```

Then review source and generated diffs:

```bash
git diff -- speckit-pro dist/claude/speckit-pro dist/codex/speckit-pro
```

Run the builder a second time:

```bash
bash scripts/build-plugin-payloads.sh
```

Expected outcome:

- Generated payload changes trace back to source guidance changes.
- No hand-edited payload-only behavior changes remain.
- The second rebuild produces no unintended additional changes.

## Validation Scenario 5: Default Deterministic Suite Passes

Run:

```bash
bash tests/speckit-pro/run-all.sh
```

Expected outcome:

- Default deterministic layers pass.
- Any failure is investigated before PR handoff.

## Validation Scenario 6: Scope Guard

Review the final diff for TACD-003 and TACD-004 boundaries.

Expected outcome:

- No prerequisite check, public setup messaging, or broad plugin limitation documentation change is introduced except narrow active behavior pointers.
- No deterministic/eval enforcement is added.
- Deferred work names TACD-003 and TACD-004.
