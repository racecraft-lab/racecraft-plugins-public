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
