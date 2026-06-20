# UAT Runbook: tacd-004-verification-coverage

| Field | Value |
|-------|-------|
| Spec | tacd-004-verification-coverage |
| Branch | tacd-004-verification-coverage |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-19T23:27:28Z |



## Env Setup

There is no package manager, build toolchain, or app server for this repo. All
verification is done with shell commands that are already on any developer machine.
From the repository root (`.worktrees/tacd-004-verification-coverage`), the two
commands you need are:

- **Run the tests:** `bash tests/speckit-pro/run-all.sh`
- **Rebuild the plugin payloads:** `bash scripts/build-plugin-payloads.sh`

Confirm you are on the right branch before starting:
```
git rev-parse --abbrev-ref HEAD
```
Expected output: `tacd-004-verification-coverage`

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Named-tool regression cannot land unnoticed (Priority: P1) [US1]

This PR adds a guard that fails automatically if any active agent file is edited to
hardcode a specific optional vendor tool (like a named web-search or context tool) —
keeping the plugin vendor-neutral. Walk through the following steps to confirm the
guard works in both the passing and failing directions.

**Happy path — guard passes on clean state:**

1. From the repo root, run `bash tests/speckit-pro/run-all.sh --layer 5`
2. Confirm the output shows all checks passing and no named-vendor tool errors. The
   line near the end should read something like `Layer 5: all checks passed`.
3. Run `bash tests/speckit-pro/run-all.sh --layer 1` to run the structural checks.
4. Confirm all checks pass.

**Deliberate regression — guard catches the problem:**

5. Open any active agent file under `speckit-pro/agents/` (for example,
   `speckit-pro/agents/implement-executor.md`) in a text editor.
6. Add a line containing a named optional tool, such as:
   `preferred_tool: mcp__tavily-mcp__search`
7. Save the file. Run `bash tests/speckit-pro/run-all.sh --layer 5` again.
8. Confirm the test output FAILS and names the file you edited and the offending
   token. The suite should not silently pass.
9. Undo the edit (restore the file to its original state). Run the layer 5 check
   again and confirm it returns to passing.

**False-positive check — generic `mcp` vocabulary is allowed:**

10. Confirm that any existing use of the word `mcp` or `MCP` in agent files (without
    a named vendor suffix like `__tavily-mcp__`) does NOT cause the guard to fail.
    The layer 5 run from step 1 covers this implicitly.

- [ ] All steps above completed: guard passes on clean state, fails on deliberate
      regression (naming the offending file), and does not fire on generic `mcp`
      vocabulary.

---

<a id="us-2"></a>
### User Story 2 - Directive pointers are proven to exist and resolve (Priority: P1) [US2]

This PR adds checks that (a) every relevant agent file references the shared
capability-discovery guidance document, and (b) that document actually exists in the
built plugin payloads that consumers install. Walk through the steps below.

**Pointer-coverage check — all active agents reference the directive:**

1. Run `bash tests/speckit-pro/run-all.sh --layer 1`
2. Confirm the pointer-coverage validator passes. Look for a line referencing
   `validate-capability-pointer` with no failures.
3. Confirm the target-resolution validator passes. Look for a line referencing
   `validate-capability-resolution` with no failures. This means the directive file
   was found in both `dist/claude/` and `dist/codex/` (the built payloads consumers
   receive).

**Deliberate regression — missing pointer is caught:**

4. Open one of the active research or context-gathering agent files under
   `speckit-pro/agents/` (for example, `speckit-pro/agents/research-analyst.md`)
   and temporarily remove the line that references `capability-discovery.md`. Save
   the file.
5. Run `bash tests/speckit-pro/run-all.sh --layer 1`
6. Confirm the test FAILS and names the agent file you edited. The output should
   identify the uncovered agent, not silently pass.
7. Restore the file (undo the edit). Run the layer 1 check and confirm it returns
   to green.

**Deliberate regression — broken payload path is caught:**

8. Rename or temporarily delete
   `dist/claude/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
9. Run `bash tests/speckit-pro/run-all.sh --layer 1`
10. Confirm the target-resolution check FAILS for the Claude payload tree (and
    similarly fails if you break the Codex tree under `dist/codex/`).
11. Restore the file by running `bash scripts/build-plugin-payloads.sh`, then confirm
    the layer 1 check returns to green.

- [ ] All steps above completed: pointer-coverage and resolution checks pass on clean
      state and fail (naming the specific agent or path) on deliberate regressions.

---

<a id="us-3"></a>
### User Story 3 - Eval expectations enforce vendor-neutral, capability-first answers (Priority: P2) [US3]

This PR rewrites the test "expected output" files for the autopilot and coach skills
(both Claude and Codex versions) so they no longer accept answers that name a specific
vendor tool. The checks below confirm the eval files are valid and no longer contain a
hardcoded vendor preference.

**Confirm the eval files are valid JSON:**

1. From the repo root, run the following four commands one at a time and confirm each
   prints `valid:` followed by the filename (no errors):
   ```
   jq -e . tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json >/dev/null && echo "valid"
   jq -e . tests/speckit-pro/layer3-functional/evals/speckit-coach-evals.json >/dev/null && echo "valid"
   jq -e . tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json >/dev/null && echo "valid"
   jq -e . tests/speckit-pro/layer3-functional/codex-evals/speckit-coach-evals.json >/dev/null && echo "valid"
   ```

**Confirm no named-vendor preference survives in the eval expected outputs:**

2. Run:
   ```
   grep -l "Tavily\|tavily\|context7\|Context7\|RepoPrompt" \
     tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json \
     tests/speckit-pro/layer3-functional/evals/speckit-coach-evals.json \
     tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json \
     tests/speckit-pro/layer3-functional/codex-evals/speckit-coach-evals.json \
     || echo "no named-vendor preference remains"
   ```
3. Confirm the output is `no named-vendor preference remains` (or that the `grep`
   returns no matching filenames). If any filename is listed, open it and confirm
   the match is an absence-arm assertion (stating the tool should NOT be present),
   not a preference for that tool.

**Confirm the five behavior scenarios are present:**

4. Open `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json` in
   a text editor or viewer.
5. Confirm it contains scenarios covering: installed-capability discovery, fallback
   when named tools are unavailable, evidence path, citations or local-file
   references, and lowered confidence when fallback quality is lower. Each should be
   a separate fixture entry. Repeat for the Codex version at
   `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json`.
6. Confirm Claude and Codex eval files cover the same scenarios (parity — the same
   behaviors are tested for both runtimes).

- [ ] All steps above completed: four eval files are valid JSON, no named-vendor
      preference survives in expected outputs, and the five behavior scenarios are
      present in both Claude and Codex eval files.

---

<a id="us-4"></a>
### User Story 4 - Installed skills ship complete bodies (Priority: P1) [US4]

Before this PR, running the payload build script would silently produce nearly-empty
skill files (about 10 lines instead of 300+) for 8 of 10 Claude skills — meaning
anyone who installed the plugin received skills with empty guidance. This PR fixes the
builder and adds a check that catches any recurrence. Walk through the steps below.

**Confirm the payload rebuild restores full skill bodies:**

1. From the repo root, run `bash scripts/build-plugin-payloads.sh`
   Wait for it to complete. You should see no errors.
2. Check the line count of a rebuilt skill body:
   ```
   wc -l dist/claude/speckit-pro/skills/speckit-coach/SKILL.md
   ```
   Confirm the output shows roughly 370 lines or more — not 10. Before the fix this
   file would show about 10 lines.
3. Optionally check a few more skills to confirm all are restored:
   ```
   for s in dist/claude/speckit-pro/skills/*/SKILL.md; do
     printf "%-50s %s lines\n" "$s" "$(wc -l < "$s")"
   done
   ```
   Every skill listed should show a line count well above 10.
4. Confirm the rebuilt payloads match what is committed (no uncommitted drift):
   ```
   git diff --exit-code -- dist
   ```
   Expect no output and an exit code of 0 (clean). If there is output, the committed
   payloads were not yet updated to match the fixed builder.

**Confirm the body-completeness check now passes:**

5. Run `bash tests/speckit-pro/run-all.sh --layer 1`
6. Confirm the body-completeness validator passes. Look for a line referencing
   `validate-payload-completeness` with no failures.

**Deliberate regression — truncated payload is caught:**

7. Open `dist/claude/speckit-pro/skills/speckit-coach/SKILL.md` in a text editor.
   Delete everything after the first heading in the body (leave only the first 10
   lines or so). Save the file.
8. Run `bash tests/speckit-pro/run-all.sh --layer 1`
9. Confirm the test FAILS and names `speckit-coach` (or the specific file) as the
   truncated skill.
10. Restore the file by running `bash scripts/build-plugin-payloads.sh` again.
    Confirm the layer 1 check returns to green.

**Full suite must pass end-to-end:**

11. Run `bash tests/speckit-pro/run-all.sh`
12. Confirm the final line of output reports all checks passed (something like
    `3269/3269 passed` — the exact count may differ slightly but there should be
    zero failures and the suite completes without a live AI run).

- [ ] All steps above completed: skill bodies are full-length after rebuild, the
      body-completeness check passes on clean state and fails (naming the skill) on a
      truncated payload, and the full suite is green.

---

## FR Coverage Matrix

| What the spec requires | Step(s) that prove it |
|------------------------|----------------------|
| Named-tool guard fails when an agent reintroduces a hardcoded vendor tool | US1, steps 5–9 |
| Named-tool guard does not fire on generic `mcp` vocabulary or schema metadata identifiers | US1, steps 1–4 and step 10 |
| Named-MCP tool assertions removed from the tool-scoping contract | US1, step 1 (layer 5 passes without any named-vendor requirement) |
| Every relevant active agent references the capability-discovery directive | US2, steps 1–3 |
| Missing pointer in an active agent makes the check fail | US2, steps 4–7 |
| Directive exists at the path consumers receive in both Claude and Codex payloads | US2, steps 1–3 (target-resolution check) |
| Broken payload path makes the target-resolution check fail | US2, steps 8–11 |
| Eval expected outputs assert absence of named-vendor set and affirmative capability-first answer | US3, steps 1–3 |
| Five behavior scenarios present as committed fixtures (no live AI run needed) | US3, steps 4–6 |
| Claude and Codex eval files are in parity | US3, step 6 |
| Payload builder strips only the Codex guard block; full skill bodies are restored | US4, steps 1–4 |
| Body-completeness check fails when a built skill is truncated | US4, steps 7–10 |
| Full default deterministic suite passes without live AI eval execution | US4, steps 11–12 |


## Negative-Path Tests

Run each scenario below and confirm the stated safe behavior. You do not need to commit any of these changes — undo them immediately after observing the expected result.

- **Guard terminator wraps across two lines**: Edit a source `SKILL.md` so its
  Codex guard-block closing phrase is split across two lines. Rebuild with
  `bash scripts/build-plugin-payloads.sh`. Open the resulting built
  `dist/claude/...` file and confirm the body is not empty — the builder stopped at
  the next section heading (or the end of file), not at the line-split terminator.
  Undo: revert the source file and rebuild.

- **Generic `mcp` word is not flagged**: Confirm an agent file that contains only
  the word `mcp` or `MCP` (without a vendor suffix like `__tavily-mcp__`) does not
  cause the layer 5 named-tool check to fail. The baseline run in US1 step 1 covers
  this implicitly.

- **Exact schema or dependency identifier is not flagged**: If an agent file contains
  a tool identifier required by a platform schema or dependency manifest (e.g., a
  config key that must match a vendor ID exactly), confirm the layer 5 guard does not
  flag it. The baseline run in US1 step 1 covers this for the current agent inventory.

- **Approved equivalent pointer is accepted**: Some Codex agent files carry a line
  like `Capability discovery equivalent: mirrors …/capability-discovery.md` instead
  of a literal path reference. Confirm the pointer-coverage check (US2, step 1)
  accepts these agents without requiring a literal path.

- **Source-tree presence is not enough**: Remove the directive file from only the
  built payload (`dist/claude/.../capability-discovery.md`) while leaving the source
  file untouched. Run `bash tests/speckit-pro/run-all.sh --layer 1`. Confirm the
  target-resolution check FAILS (US2, step 10). The check verifies the built payload,
  not just the source tree. Undo: run `bash scripts/build-plugin-payloads.sh`.

- **Skill with no guard block is unaffected**: If a source `SKILL.md` has no Codex
  guard block at all, the builder must leave its body unchanged. Confirm that such a
  skill's built file matches its source and the body-completeness check still passes
  after a rebuild.

- **No live AI run required**: Confirm that `bash tests/speckit-pro/run-all.sh`
  completes fully without invoking `claude -p` or any network call. The default suite
  (Layers 1, 4, 5) is entirely deterministic.

## Self-Review Findings

**Self-Review:** <not available — workflow file not provided>

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

Revert the PR commit (`git revert <SHA>`). No data migration is needed. The payload
fix is forward-only: re-running `bash scripts/build-plugin-payloads.sh` from any
commit always rebuilds payloads from source, so no hand-edited files need to be
undone. The deterministic guards are stateless and add no persistent state to roll
back.
