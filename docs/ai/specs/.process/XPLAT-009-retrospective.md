# XPLAT-009 Retrospective

## Outcome

XPLAT-009 removes plugin-owned Bash source from `speckit-pro/`, rebuilds Claude
and Codex payloads from the cleaned source tree, and records source-derived
zero-Bash and release-readiness proof.

PR: https://github.com/racecraft-lab/racecraft-plugins-public/pull/297

## What Worked

- The zero-Bash guard and payload completeness checks caught the right release
  boundary: active plugin source, generated payloads, and bounded installed-cache
  proof all report zero script files.
- The full deterministic suite provides the durable post gate: `2021/2021`
  passed after the XPLAT-009 runner guard update.

## What Needed Correction

- The autopilot run stopped after implementation verification instead of
  completing the post-implementation phases through PR creation. The resumed
  run fixed this by restoring every post item in both the visible plan and
  `autopilot-state.json`.
- The older XPLAT-004/XPLAT-008 runner guard treated generated payload and
  active skill changes as forbidden by default. XPLAT-009 intentionally owns
  those surfaces, so the test now allows declared XPLAT-009 paths while still
  requiring any changed `.sh` file in that boundary to be a deletion.
- RepoPrompt review-agent launch failed with `Transport closed`; parent-session
  review and deterministic gates completed instead.
- The first PR publication run exposed two post-creation issues: the live PR
  title needed the lowercase `xplat` conventional scope, and the docs reference
  generator still cited deleted Bash helper paths. Commit `d7346195` corrected
  both, and the PR checks passed after the rerun.
- Copilot returned a size-limit comment instead of code findings because the
  diff exceeds 20,000 lines. XPLAT-009 keeps the one-PR route because the final
  reviewability gate explicitly accepted the coupled source deletion, Python
  ownership, payload rebuild, and proof update.

## XPLAT-010 Handoff

- XPLAT-010 should own repository-wide Bash cleanup outside `speckit-pro/` and
  generated payload proof roots.
- XPLAT-010 should not reopen XPLAT-009's plugin-source deletion decision unless
  a specific active runtime regression is found.
- XPLAT-008 native operator UAT remains a separate release blocker and is not
  completed by XPLAT-009.
