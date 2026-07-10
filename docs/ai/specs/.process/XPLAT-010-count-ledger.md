# XPLAT-010 Count-Parity Ledger

Running record of the `.sh` → `.py` count-parity ports in the XPLAT-010 stack
(FR-013). Each port PR appends **one delta line** proving 1:1 name-and-count
parity against its committed baseline under
`tests/speckit-pro/parity/xplat-010/`. The cumulative roll-up lands in
`docs/ai/specs/.process/XPLAT-010-suite-parity-result.json` (Polish phase).

Columns:

- **PR** — the stack slice (e.g. `PR 3a`).
- **Script** — the ported test module (`.py`), or the swap performed.
- **Mode** — the invocation mode when a script has more than one baseline pair.
- **bash → python** — assertion counts on each side (must be equal).
- **names_equal** — `yes` when the ordered canonical check-name inventory is
  identical (a rename/drop makes this `no` and flags a regression).
- **baseline** — the committed baseline pointer, or `n/a` for a count-neutral swap.

| PR | Script | Mode | bash → python | names_equal | baseline |
|----|--------|------|---------------|-------------|----------|
| PR 13 | port: `test-estimate-spec-size.sh` → `test-estimate-spec-size.py` | default | 33 → 33 | yes | `tests/speckit-pro/parity/xplat-010/test-estimate-spec-size-baseline.txt` |
| PR 2 | wrapper swap: `test-speckit-pro-runner.sh` → `test-speckit-pro-runner.py` | default | 0 → 0 (pure `python3 …` shim; no own assertions) | n/a | n/a |
| PR 2 | wrapper swap: `test-speckit-pro-read-only-helpers.sh` → `test-speckit-pro-read-only-helpers.py` | default | 0 → 0 (pure `python3 …` shim; no own assertions) | n/a | n/a |
| PR 3a | port: `validate-agents.sh` → `validate-agents.py` | default | 104 → 104 | yes | `tests/speckit-pro/parity/xplat-010/validate-agents-baseline.txt` |
| PR 3a | port: `validate-capability-pointer.sh` → `validate-capability-pointer.py` | default | 52 → 52 | yes | `tests/speckit-pro/parity/xplat-010/validate-capability-pointer-baseline.txt` |
| PR 3a | port: `validate-capability-resolution.sh` → `validate-capability-resolution.py` | default | 43 → 43 | yes | `tests/speckit-pro/parity/xplat-010/validate-capability-resolution-baseline.txt` |
| PR 3a | port: `validate-codex-agents.sh` → `validate-codex-agents.py` | default | 148 → 148 | yes | `tests/speckit-pro/parity/xplat-010/validate-codex-agents-baseline.txt` |
| PR 3a | port: `validate-codex-hooks.sh` → `validate-codex-hooks.py` | default | 9 → 9 | yes | `tests/speckit-pro/parity/xplat-010/validate-codex-hooks-baseline.txt` |
| PR 3a | port: `validate-codex-marketplace.sh` → `validate-codex-marketplace.py` | default | 13 → 13 | yes | `tests/speckit-pro/parity/xplat-010/validate-codex-marketplace-baseline.txt` |
| PR 3a | port: `validate-codex-parity.sh` → `validate-codex-parity.py` | default | 81 → 81 | yes | `tests/speckit-pro/parity/xplat-010/validate-codex-parity-baseline.txt` |
| PR 3a | port: `validate-codex-plugin.sh` → `validate-codex-plugin.py` | default | 33 → 33 | yes | `tests/speckit-pro/parity/xplat-010/validate-codex-plugin-baseline.txt` |
| PR 3a | port: `validate-curated-set.sh` → `validate-curated-set.py` | default | 58 → 58 | yes | `tests/speckit-pro/parity/xplat-010/validate-curated-set-baseline.txt` |
| PR 3a | port: `validate-hooks.sh` → `validate-hooks.py` | default | 11 → 11 | yes | `tests/speckit-pro/parity/xplat-010/validate-hooks-baseline.txt` |
| PR 3b | port: `validate-payload-completeness.sh` → `validate-payload-completeness.py` | default | 52 → 52 | yes | `tests/speckit-pro/parity/xplat-010/validate-payload-completeness-baseline.txt` |
| PR 3b | port: `validate-plugin-payload.sh` → `validate-plugin-payload.py` | default | 23 → 23 | yes | `tests/speckit-pro/parity/xplat-010/validate-plugin-payload-baseline.txt` |
| PR 3b | port: `validate-plugin.sh` → `validate-plugin.py` | default | 8 → 8 | yes | `tests/speckit-pro/parity/xplat-010/validate-plugin-baseline.txt` |
| PR 3b | port: `validate-pr-checks-sentinel.sh` → `validate-pr-checks-sentinel.py` | default | 28 → 28 | yes | `tests/speckit-pro/parity/xplat-010/validate-pr-checks-sentinel-baseline.txt` |
| PR 3b | port: `validate-process-gitattributes.sh` → `validate-process-gitattributes.py` | default | 6 → 6 | yes | `tests/speckit-pro/parity/xplat-010/validate-process-gitattributes-baseline.txt` |
| PR 3b | port: `validate-release-workflow.sh` → `validate-release-workflow.py` | default | 24 → 24 | yes | `tests/speckit-pro/parity/xplat-010/validate-release-workflow-baseline.txt` |
| PR 3b | port: `validate-scripts.sh` → `validate-scripts.py` | default | 37 → 37 | yes | `tests/speckit-pro/parity/xplat-010/validate-scripts-baseline.txt` |
| PR 3b | port: `validate-skill-capability-pointers.sh` → `validate-skill-capability-pointers.py` | default | 55 → 55 | yes | `tests/speckit-pro/parity/xplat-010/validate-skill-capability-pointers-baseline.txt` |
| PR 3b | port: `validate-skills.sh` → `validate-skills.py` | default | 124 → 124 | yes | `tests/speckit-pro/parity/xplat-010/validate-skills-baseline.txt` |
| PR 3b | port: `validate-spec-index-determinism.sh` → `validate-spec-index-determinism.py` | default | 16 → 16 | yes | `tests/speckit-pro/parity/xplat-010/validate-spec-index-determinism-baseline.txt` |
| PR 3b | new validator failure-path regression module | default | 0 → 5 | n/a (new regression coverage) | `tests/speckit-pro/layer4-scripts/test-layer1-validator-regressions.py` |
| PR 4 | port: `validate-moc-orphan.sh` → `validate-moc-orphan.py` | default | 29 → 29 | yes | `tests/speckit-pro/parity/xplat-010/validate-moc-orphan-baseline.txt` |
| PR 4 | port: `validate-moc-orphan.sh` → `validate-moc-orphan.py` | explicit scan-root | 0 → 0 | yes | `tests/speckit-pro/parity/xplat-010/validate-moc-orphan-scan-root-baseline.txt` |
| PR 4 | port: `validate-moc-stale-index.sh` → `validate-moc-stale-index.py` | default | 11 → 11 | yes | `tests/speckit-pro/parity/xplat-010/validate-moc-stale-index-baseline.txt` |
| PR 4 | port: `validate-codex-skills.sh` → `validate-codex-skills.py` | default | 161 → 161 | yes | `tests/speckit-pro/parity/xplat-010/validate-codex-skills-baseline.txt` |
| PR 4 | port: `validate-payload-conformance.sh` → `validate-payload-conformance.py` | default | 209 → 209 | yes | `tests/speckit-pro/parity/xplat-010/validate-payload-conformance-baseline.txt` |
| PR 4 | port: `test-moc-lint-exit-codes.sh` → `test-moc-lint-exit-codes.py` | default, non-root | 36 → 36 | yes | `tests/speckit-pro/parity/xplat-010/test-moc-lint-exit-codes-baseline.txt` |
| PR 5 | port: `validate-tool-scoping.sh` → `validate-tool-scoping.py` | default | 186 → 186 | yes | `tests/speckit-pro/parity/xplat-010/validate-tool-scoping-baseline.txt` |
| PR 5 | port: `test-check-toolchain.sh` → `test-check-toolchain.py` | default | 26 → 26 | yes | `tests/speckit-pro/parity/xplat-010/test-check-toolchain-baseline.txt` |
| PR 5 | workflow self-validator update: `validate-pr-checks-sentinel.py` | default | 28 → 30 (intentional PR5 workflow-contract expansion) | n/a | `tests/speckit-pro/parity/xplat-010/validate-pr-checks-sentinel-baseline.txt` |
| PR 6 | port: `test-refresh-local-plugin.sh` → `test-refresh-local-plugin.py` | default | 58 → 58 | yes | `tests/speckit-pro/parity/xplat-010/test-refresh-local-plugin-baseline.txt` |
| PR 6 | port: `test-sync-marketplace-versions.sh` → `test-sync-marketplace-versions.py` | default | 49 → 49 | no (intentional `jq`-dependency replacement under T055) | retired Bash: `tests/speckit-pro/parity/xplat-010/test-sync-marketplace-versions-bash-baseline.txt`; current Python: `tests/speckit-pro/parity/xplat-010/test-sync-marketplace-versions-baseline.txt` |
| PR 6 | new contract coverage: `.claude/hooks/*.py` | default | 0 → 22 | n/a | `tests/speckit-pro/parity/xplat-010/test-claude-hooks-baseline.txt` |
| PR 7a | port: `test-transcript-helpers.sh` → `test-transcript-helpers.py` | default | 42 → 42 | yes | `tests/speckit-pro/parity/xplat-010/test-transcript-helpers-baseline.txt` |
| PR 7a | new CLI contracts: `scrub-transcript.py` + `reduce-transcript-fixture.py` | default | 0 → 25 | n/a | `tests/speckit-pro/parity/xplat-010/test-transcript-tools-baseline.txt` |
| PR 7b | port: `run-dispatch-fixtures.sh` → `run-dispatch-fixtures.py` | replay | 184 → 184 | yes | `tests/speckit-pro/parity/xplat-010/run-dispatch-fixtures-baseline.txt` |
| PR 7b | port: `run-return-format-fixtures.sh` → `run-return-format-fixtures.py` | replay | 17 → 17 | yes | `tests/speckit-pro/parity/xplat-010/run-return-format-fixtures-baseline.txt` |
| PR 7b | port: `run-e2e-fixtures.sh` → `run-e2e-fixtures.py` | replay | 23 → 23 | yes | `tests/speckit-pro/parity/xplat-010/run-e2e-fixtures-baseline.txt` |
| PR 7b | port: `run-grounding-fixtures.sh` → `run-grounding-fixtures.py` | replay | 33 → 33 | yes | `tests/speckit-pro/parity/xplat-010/run-grounding-fixtures-baseline.txt` |
| PR 7b | port: `run-all-fixtures.sh` → `run-all-fixtures.py` | replay | 257 → 257 | yes | `tests/speckit-pro/parity/xplat-010/run-all-fixtures-baseline.txt` |
| PR 7b | new replay/live runner contract | default | 0 → 31 | n/a | `tests/speckit-pro/parity/xplat-010/test-layer7-runners-baseline.txt` |
| PR 7b | shipped gate regression expansion | default | 57 → 58 | n/a | n/a |
| PR 8 | port: `run-parity-fixtures.sh` → `run-parity-fixtures.py` | dry-run | 12 → 12 | yes | `tests/speckit-pro/parity/xplat-010/run-parity-fixtures-baseline.txt` |
| PR 8 | port: `test-l8-extractors.sh` → `test-l8-extractors.py` | default | 19 → 19 | yes | `tests/speckit-pro/parity/xplat-010/test-l8-extractors-baseline.txt` |
| PR 8 | replacement: `test-l8-judge.sh` → deterministic local judge contract | default | 16 → 16 | no (intentional removal of live-LLM judgment) | retired Bash: `tests/speckit-pro/parity/xplat-010/test-l8-judge-bash-baseline.txt`; current Python: `tests/speckit-pro/parity/xplat-010/test-l8-judge-baseline.txt` |
| PR 8 | fixture environment inputs: 8 `env-*.sh` → 8 `env-*.json` | default | 0 → 0 (data-only inputs) | n/a | n/a |
| PR 8 | new Layer-8 runner/portability contract | default | 0 → 33 | n/a | `tests/speckit-pro/parity/xplat-010/test-layer8-runner-baseline.txt` |
| PR 8 | shipped gate regression expansion | default | 58 → 59 | n/a | n/a |
| PR 9 | port: `test-eval-runner-skill-selection.sh` → `.py` | default | 13 → 13 | yes | `tests/speckit-pro/parity/xplat-010/test-eval-runner-skill-selection-baseline.txt` |
| PR 9 | port: `test-l6-codex-runner.sh` → `.py` | default | 23 → 23 | yes | `tests/speckit-pro/parity/xplat-010/test-l6-codex-runner-baseline.txt` |
| PR 9 | live runner/library swaps for Layers 2/3/6 | command-plan / live-only | 0 → 0 (predecessors emit no counted assertions) | n/a | eleven per-entrypoint baselines under `tests/speckit-pro/parity/xplat-010/` |
| PR 9 | `run-all.py` scope/command-plan contract expansion | default | 20 → 24 | n/a | n/a |
| PR 9 | new Layer-2 runner/staging contract | default | 0 → 24 | n/a | `tests/speckit-pro/parity/xplat-010/test-layer2-trigger-runners-baseline.txt` |
| PR 9 | new Layer-2 signal-restoration contract | default | 0 → 7 | n/a | `tests/speckit-pro/parity/xplat-010/test-layer2-signal-restoration-baseline.txt` |
| PR 9 | new Layer-6 portability contract | default | 0 → 18 | n/a | `tests/speckit-pro/parity/xplat-010/test-layer6-portability-baseline.txt` |
| PR 9 | shipped gate manifest-reference strengthening | default | 59 → 59 (existing method strengthened) | n/a | n/a |

**PR 13 note (T121–T130):** The estimator Layer-4 test follows the
Per-Port Protocol against historical predecessor commit
`c9176902d98082415aac88954b2f66fa6c499506`. Six-item dual-run proof:
(1) `VERBOSE=true bash tests/speckit-pro/layer4-scripts/test-estimate-spec-size.sh`
in that historical checkout, parsed by `tests/speckit-pro/lib/capture_baseline.py`;
(2) `python3 tests/speckit-pro/layer4-scripts/test-estimate-spec-size.py`;
(3) committed baseline `tests/speckit-pro/parity/xplat-010/test-estimate-spec-size-baseline.txt`;
(4) ordered-name inventory diff: no differences, 1:1 preserved;
(5) Bash `33` == Python `33`; (6) intentional change: none.

**PR 2 note:** No test-logic ports land in PR 2. The two rows above record the
count-neutral removal of the redundant Bash wrappers — the suite manifest now
lists the `.py` modules they shimmed directly, so the same assertions run with no
count change. The parity tooling (`lib/capture_baseline.py`, `lib/test_result.py`)
and this ledger are established here for the ports in PRs 3a–9.

**PR 3a note (batch 1 of 2, T018–T022):** The first five mechanical Layer-1
validators port with exact 1:1 name-and-count parity against their committed
baselines. Two of them — `validate-capability-pointer` and
`validate-capability-resolution` — had their bash predecessors interpolate the
*absolute* agents-directory / `dist/**` tree paths into a handful of check names
(2 and 4 names respectively). That absolute repo-root prefix is environment noise
(it differs per checkout — CI checks out under a different absolute root), never part of the
check identity, and would violate the repo's privacy hard constraint if committed.
Both the committed baseline and the Python port record the **repo-relative** form
(`speckit-pro/agents`, `dist/claude`, …); the assertion count and the check
identity are preserved, and only the environment-specific prefix is normalized —
so `names_equal` remains `yes` against the committed baseline. The extracted path
tokens (`speckit-pro/skills/...`) are already repo-relative and are recorded
verbatim.

**PR 3a note (batch 2 of 2, T023–T027):** The remaining five mechanical Layer-1
validators port with exact 1:1 name-and-count parity against their committed
baselines (13, 81, 33, 58, 11 → same). Intentional change: `none` for every row.
Unlike batch 1, none of these five interpolate an absolute repo-root prefix into
any check name, so no environment-path normalization was needed — the ports read
live data and reproduce the bash logic directly, and all names are recorded
verbatim. Two data-driven name sources are recorded as baseline regeneration
triggers (count-parity contract §2, rule 4): `validate-codex-parity` interpolates
the shared plugin version (`.claude-plugin`/`.codex-plugin` `plugin.json`) and the
marketplace name (both `marketplace.json` files) into two check names and
enumerates each Codex `SKILL.md`'s `../../skills/**.md` reference links; and
`validate-curated-set` derives its per-entry check names from live
`speckit-pro/scripts/curated-set.json` content. Adding, removing, or reordering
any of those inputs changes the inventory and requires recapturing the affected
baseline. This completes PR 3a — all ten batch-1+batch-2 Layer-1 validators are
ported; ten `.sh` deleted.

**PR 3b note (part 1 of 2, T029–T033):** The first five PR-3b mechanical Layer-1
validators port with exact 1:1 name-and-count parity against their committed
baselines (52, 23, 8, 28, 6 → same). Intentional change: `none` for every row.

Four of the five (`validate-plugin`, `validate-plugin-payload`,
`validate-pr-checks-sentinel`, `validate-process-gitattributes`) interpolate no
absolute repo-root prefix into any check name, so their names are recorded
verbatim. Two per-occurrence normalizations apply only to
`validate-payload-completeness`, whose bash predecessor built data-driven check
names from live paths and line counts (count-parity contract §2):
  1. *Absolute-path → repo-relative* (privacy hard constraint, PR 3a precedent):
     21 of its 52 names embedded the absolute dist/source path — the built-skills
     directory-exists name (1), each per-skill `source SKILL.md … readable` name
     (10), and each per-skill `built SKILL.md is readable` name (10). The absolute
     repo-root prefix is environment noise (differs per checkout); both the
     committed baseline and the port emit the repo-relative form
     (`dist/claude/speckit-pro/skills`, `speckit-pro/skills/<name>/SKILL.md`,
     `dist/claude/speckit-pro/skills/<name>/SKILL.md`).
  2. *BSD `wc -l` padding → clean integer* (macOS-vs-CI formatting noise): the 10
     per-skill length-tolerance names rendered `dist=     363` under macOS BSD
     `wc -l` (right-justified); GNU/Linux `wc` (CI) and the Python port emit
     `dist=363`. The leading whitespace is normalized to the CI integer in both
     baseline and port.
Only environment-specific formatting is normalized; the count and the check
identity are preserved, so `names_equal` stays `yes`.

Data / live-file-driven baseline regeneration triggers recorded for this batch
(count-parity contract §2, rule 4): `validate-payload-completeness` derives its
per-skill names and length numbers from the live Claude skill set, each source
`SKILL.md`'s last non-guard `## ` heading, and the source/built line counts +
per-skill guard-section size (it and `validate-plugin-payload` invoke the payload
builder / read `dist/**` live); `validate-pr-checks-sentinel` folds the live
`.github/workflows/*.yml` glob into its single 28th YAML-validity outcome and
reads `pr-checks.yml` content live. Adding/removing a skill, editing a source
heading or length, changing the built payload, or adding a workflow file changes
the affected inventory and requires recapturing that baseline. This is part 1 of
PR 3b (T029–T033); part 2 (T034–T038) ports the remaining five and lands the
batched manifest-registration + green-suite confirmation (T039).

**PR 3b note (part 2 of 2, T034–T039):** The remaining five PR-3b mechanical
Layer-1 validators port with exact 1:1 name-and-count parity against their
committed baselines (24, 37, 55, 124, 16 → same). Intentional change: the
`validate-release-workflow` YAML syntax check is now stdlib-only and no longer
depends on optional PyYAML/Ruby parser availability, satisfying the XPLAT-010
runtime contract while preserving the single counted YAML-validity assertion.

Three baseline hygiene notes apply:
  1. `validate-skill-capability-pointers` normalized four absolute checkout-path
     names to repo-relative names (`speckit-pro/skills`,
     `speckit-pro/codex-skills`, `dist/claude`, `dist/codex`), matching the PR
     3a privacy/CI portability precedent.
  2. `validate-spec-index-determinism` preserves the true `16/16` shell summary.
     Its bash predecessor executed two assertions under the same
     `generate-spec-index-write is registered as deferred` current-test name;
     verbose capture printed the second as a bare `PASS`, so the committed
     baseline records that duplicate name explicitly instead of losing a count.
  3. Data-driven regeneration triggers for this batch are the Claude skill list
     and frontmatter/body content (`validate-skills`), Claude/Codex skill
     inventories and dist payload pointer files (`validate-skill-capability-pointers`),
     release workflow content (`validate-release-workflow`), contract/template
     files (`validate-scripts`), and runner registry/template sentinel output
     (`validate-spec-index-determinism`).

**PR 4 note (T040–T045):** The four heavier Layer-1 validators port with exact
1:1 count parity against their committed baselines, including the
`validate-moc-orphan` explicit scan-root invocation mode (`0 → 0`) recorded as a
separate baseline per the count-parity contract. The active co-located Layer-4
MOC subprocess test `test-moc-lint-exit-codes` is also ported in this slice with
the pinned non-root count (`36 → 36`); the root-only `31` divergence remains
documented as an environment caveat, not the count of record. Intentional
change: `validate-moc-stale-index.py` now maps an unexpected no-arg harness
exception to exit `2` and still removes the transient broken-symlink fixture,
preserving the old three-way exit-class contract without shell utility stubs.
Baseline hygiene: `validate-payload-conformance` normalizes four checkout-path
check names to repo-relative payload paths (`dist/claude/...`, `dist/codex/...`),
matching the PR-3a/3b privacy and CI-portability precedent while preserving
the check identities and count.
`test-moc-id-normalize.sh` and `test-generate-spec-index.sh` were already
classified as deleted orphan-target tests in the PR-1 disposition ledger, so
`test-moc-lint-exit-codes` is the only active Layer-4 MOC test ported here.

**PR 5 note (T046–T053):** `validate-tool-scoping` is now Python-authoritative
through the suite manifest (`dispatch=python-module`) and the shipped runner
uses the manifest-backed `run-layer-scripts.py --layer 5` path instead of the
retired native `check_layer5` shim. `test-check-toolchain` ports the active
Layer-4 contract for the top-level `check-toolchain.py` port with exact
`26 → 26` parity; the top-level checker preserves the predecessor modes
(`tests`, `shell`, `docs`, `all`) but is covered through the Layer-4 contract
rather than listed as a counted suite script. The `pr-checks.yml` docs-toolchain
step now dispatches `speckit_pro_runner` directly with a docs-mode request
fixture and no repo-local Bash script. `validate-pr-checks-sentinel` intentionally
expands from `28` to `30` checks to lock that workflow swap: one positive
docs-mode runner dispatch assertion and one negative Bash-dispatch assertion.
PR-body branch-protection callout to carry forward: **PR 5 is
required-check-neutral**; it changes a `run:` step inside the existing
`validate-plugins` surface, renames no job/status check, and requires no manual
branch-protection update (contrast PR 11 and PR 12).

**PR 6 note (T054–T061):** The refresh helper preserves the predecessor's true
`58 → 58` ordered check-name inventory. The marketplace-sync helper preserves
all 49 predecessor assertion positions, with 47 behavior-preserving names and
two explicit replacements for the retired `jq` prerequisite; separate retired
Bash and current Python baselines make that intentional T055 change reviewable
instead of claiming false name equality. The new 22-check hook contract locks
stdin-JSON handling, exit `0`/`2`, Python Layer-1 dispatch, and the absence of
`os.system`, `shell=True`, and `jq` execution.

**PR 7a note (T062–T066):** The Python transcript library preserves all 42
predecessor check names and assertion positions. The 24-check CLI contract adds
direct coverage for scrub/reduce behavior, including Windows user-path
redaction and Bash-compatible null coalescing. The three Bash helper/tool
predecessors remain temporarily as explicit dependencies of the four unported
replay runners; PR 7b deletes them atomically with those consumers. Deleting
them in PR 7a would make this stack increment non-runnable.

**PR 7b note (T067–T072):** All four replay classes and the aggregate runner
preserve the Bash predecessor's ordered `257`-assertion inventory. The new
26-check runner contract covers replay summaries, live capture through a
discovered executable, scrub/reduce integration, argv-list subprocesses, and
shell-free execution. Layer 7 now dispatches through the manifest-backed Python
module path; the shipped native `check_layer7` is retired, which expands its
gate regression suite from 57 to 58 methods. The three PR-7a transitional Bash
dependencies are deleted with their last Bash consumers in this slice.

**PR 8 note (T073–T080):** The dry-run Layer-8 fixture inventory and extractor
test preserve exact ordered parity (`12 → 12` and `19 → 19`). The judge's
`16 → 16` count is an intentional contract replacement: the retired Bash test
proved a live Claude shim, while the Python test proves only deterministic
`byte-identical`, `exact`, and `tolerance-1` arms and a skip-with-warning for
`semantic-equivalent`; separate baselines prevent a false name-equality claim.
The 29-check runner contract adds OS-neutral subprocess doubles, exact resolved
`CLAUDE_BIN` invocation, platform temp-directory selection, raw-byte precedence
over extractor configuration, and a live tracked-tree `.sh` absence check.
Layer 8 now dispatches through the manifest-backed Python module path; retiring
native `check_layer8` expands the shipped gate regression suite from 58 to 59.

**PR 9 note (T081–T087):** The two active predecessor tests retain exact
`13 → 13` and `23 → 23` ordered inventories. The live entrypoints themselves
had no counted assertion protocol, so their `0 → 0` baselines are inventory
markers only; behavior is instead locked by 25 supplemental Layer-2 signal and
Layer-6 portability checks plus the existing 24-check staging contract. Bare
`--live` preserves the predecessor's default Layers 1/4/5 scope, while `--all`
continues to select Layers 2/3/6 and enable live mode; command plans now name
Python entrypoints. Layer 6 invokes exact resolved executable paths, uses
Windows-safe timestamps and explicit UTF-8 decoding, strips trailing prompt
newlines like shell command substitution, atomically persists partial JSON,
and cleans temporary files after spawn errors. Layer 2 converts `SIGHUP` and
`SIGTERM` into controlled unwinding so moved skills restore before exit. One
intentional safety change is explicit: a restore collision returns exit `2`
and preserves the backup instead of silently ignoring the failed restoration.
The shipped suite gate now derives AI runner references from manifest
`scripts[]`; its 59-method count is unchanged because the existing dispatch
test was strengthened rather than duplicated.
