# Validation Guide: Attribution Foundation

Run from the EDA-001 worktree root on branch `eda-001-attribution-foundation`. This guide is for implementation validation; no listed implementation check has been run merely by writing Plan.

## Prerequisites

- Python 3.11+ for repository tests. No new test dependency or network access is required after fixtures are frozen.
- Existing repository tools for lint/type checking and the docs site's pinned toolchain. The scoped docs instructions require `pnpm --dir docs-site install --frozen-lockfile` before docs commands in a fresh worktree; this worktree's workflow already records bootstrap.
- Pinned source LICENSE/tree evidence harvested without modifying the fork. Fixtures must be local before the offline test runs.
- Complete the current slice's authored files before regeneration. The parent owns branches, commits, PRs, and gate recording.

## Focused red/green proof

1. Establish independent inventory, owner, license, valid zero-landed ledger, and synthetic credit fixtures under the durable test directory.
2. Before writing each notice/ledger capability, run `python3 tests/speckit-pro/unit/test-upstream-skill-attribution.py` with its tests present and demonstrate the expected missing-content or guarded-defect failure. Record the specific failing assertion; a missing test script is not red proof.
3. Add the minimal content/validator behavior for that unit and rerun the same command. Expected result: exit 0, with positive and targeted negative cases executed.
4. The real ledger has 38 rows and zero landed delivery rows. Its successful validation must not replace the synthetic landed-file cases, whose checked-file counts are nonzero.

See [ledger contract](contracts/ledger.md), [credit contract](contracts/credits.md), and [notice contract](contracts/notices.md) for exact failure conditions. Do not edit the real ledger to manufacture a landed-row demonstration.

## Slice 1 acceptance

- Inspect the Matt notice for both repository URLs, baseline tag and commit, modified-derivative explanation, ledger link, and one exact license block.
- Confirm the 38-row canonical ledger, bucket totals 18/7/4/9, exact owner/disposition map, 14 IGNORE reasons, and the three omission notes. All delivery rows are planned.
- Run the focused test; check that positive Markdown/TOML/Python cases select files, that missing/empty destinations fail, and that header/metadata and malformed zero-landed ledger mutations fail at the intended assertions.
- Confirm the README acknowledgment's link resolves to the authored Matt notice.

## Slice 2 acceptance

- Inspect the separate HumanLayer MIT notice and confirm exact commit `bba9d13ab34f0a87f1cc33df4dd196372393ddfc` and source path `plugins/show-me/skills/show-me/SKILL.md`.
- Follow the pr row's one transitive source to that notice. All other initial transitive arrays remain empty.
- Run the focused test. Missing/empty/duplicate pr source, altered pin/path/holder/license/notice, and missing/duplicate/changed HumanLayer license blocks must be rejected even though pr is still planned.

## Repository checks

Run the focused command and the normal quick suite:

```text
python3 tests/speckit-pro/unit/test-upstream-skill-attribution.py
python3 tests/speckit-pro/run-all.py
python3 scripts/run-python-lint.py run ruff
python3 scripts/run-python-lint.py run mypy
python3 tests/speckit-pro/unit/test-privacy-scan.py
```

Expected outcome: each exits 0. These checks verify the registered test, required standard-library/safety surfaces, privacy constraints, and configured lint/type gates. Use the prepared lint/type environment recorded by the parent; do not silently substitute an unpinned tool version. The CI suite command from AGENTS.md is:

```text
SPECKIT_SKIP_TOOLCHAIN_CHECK=1 GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_NOSYSTEM=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-default-suite.json
```

Expected outcome: exit 0 with no failed tests. A still-running native session is pending until its exact handle returns an integer exit code. Local success does not claim hosted container preflight success.

## Regenerate and inspect both payloads

```text
python3 scripts/refresh-release-artifacts.py
pnpm --dir docs-site reference:generate
pnpm --dir docs-site reference:check
pnpm --dir docs-site validate:quality
```

Expected outcome: exit 0; generated test and Plugin Authoring Source references reflect the test/README changes. A generated docs path/count comes from this actual run, not a hand-authored substitute.

In each of `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`, find `skills/speckit-coach/references/upstream/mattpocock-skills/UPSTREAM-NOTICE.md` and `ledger.json`. After slice 2, also find `skills/speckit-coach/references/upstream/humanlayer-show-me/UPSTREAM-NOTICE.md`. Compare each file's raw bytes to its authored source. Missing payload files or different bytes fail acceptance. Inspect generated diffs for unexpected behavior or manual version changes.

After the parent commits the source and generated outputs together, run:

```text
python3 scripts/refresh-release-artifacts.py --check
```

Expected outcome: exit 0. Before commit, this drift check is not a meaningful clean-tree success claim because uncommitted generated-input changes fail it.

## Review readiness

For each slice the parent records actual diff totals, red/green proofs, successful gates, any environment failures, generated-output receipts, and requirement traceability. Validate the exact final conventional PR title and release-note fence using the AGENTS.md commands before marking the PR ready. Required hosted checks, including container preflights, remain separate evidence.

No derivative content, fork edits, manual version changes, or runtime services are required. No formal model is required for static content and deterministic tests. Later delivery owners EDA-002–EDA-010 are responsible for their derivative files and row landing changes; EDA-011 closes out the inventory.
