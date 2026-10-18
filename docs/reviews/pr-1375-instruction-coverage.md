# PR 1375: dispatch gate coverage

`tests/speckit-pro/unit/test-codex-spawn-fork-turns.py` derives both of its rules
from the files it scans. No reviewed-content fixture and no content pins remain,
so a wording edit to a Codex skill or agent needs no fixture change.

## Rules

- **Calls.** Every `spawn_agent(` call in a scanned file passes exactly one
  literal `fork_turns="none"`. The gate tokenizes each whole balanced call, so
  argument order and line wrapping do not matter. A `*` or `**` expansion, a second
  `fork_turns`, a dynamic value, or a marker inside another argument or a
  comment fails.
- **Files.** Every scanned skill file that names `spawn_agent` states the
  rule: `fork_turns` then `=` or `:` then `"none"` or `'none'`. Every agent
  TOML that names `spawn_agent` states it in `developer_instructions`. A new
  or renamed file that names `spawn_agent` without the rule fails.
- **Fail closed.** A file that is not strict UTF-8, an agent TOML that does
  not parse, an unterminated or untokenizable call, and a symlink in the skill
  tree each fail the gate. Both rules also run on the shipped `dist/codex`
  payload.

## Scope

The gate scans the rendered Codex skill tree and every generated Codex agent
TOML. It skips only the file kinds that cannot dispatch a Codex child agent:

- Python files under a `scripts/` directory;
- JSON schemas (`*.schema.json`);
- lockfiles (`*-lock.json`, `*-lock.yaml`, `*.lock`);
- the two verbatim upstream Quint trees, `speckit-coach/references/quint/quint-lang`
  and `quint-modeling`, pinned by path (`test-quint-reference-attribution.py`
  owns their provenance). An `UPSTREAM-NOTICE.md` elsewhere exempts nothing.

Every other file kind stays in scope, including unknown extensions, so a
renamed reference cannot leave the scan.

## Known limits

- **Natural-language intent is not checked.** A file that already states the
  rule can still carry contradictory prose, such as "for any child you launch,
  inherit the complete parent conversation", in a paragraph, a call's
  `message`, a comment, or agent metadata. Static checks cannot infer that
  intent. Whole-file content pins closed those keyword-free variants of
  security finding F1375-0784f4ad at `4429ffb6`. This fix round removed the
  pins, as review crc1375 asked, so the variants are accepted limits again.
  - **Why review still covers it:** the text reaches a shipped skill only
    through a pull request, and CODEOWNERS (`* @racecraft-lab/maintainers`)
    reviews that diff. A pin bump got exactly the same review, so the pins
    added friction but no independent check.
  - **What it needs:** a Daybreak re-check of the head that removes the pins.
- **Prose values other than "none" are not flagged.** Text such as
  ``use `fork_turns="all"` for the next child`` in a file that states the rule
  passes. One scanned skill rightly says "never use `fork_turns: "all"`", so a
  value scan would need a prose heuristic. The same review control applies.
- **Unsupported call fields.** The `prompt`, `context`, and `options` call
  examples cannot dispatch through the current hosted tool: its schema has no
  such fields. These are the Low and Info variants in the
  [source Daybreak review](https://github.com/racecraft-lab/racecraft-plugins-public/pull/1375#issuecomment-6244445195).
- **The file rule is per file, not per instruction.** A file that states the
  rule once can carry another dispatch sentence without it. Removing the
  argument from one of several statements in, say, `post-implementation.md`
  passes. A per-paragraph rule would need a prose heuristic; the autopilot
  `SKILL.md` states the rule for every call, and review covers the rest. A
  file with a single statement, such as `phase-driver.md`, is fully guarded.
- **Skipped kinds can still print text.** A Python script under `scripts/` or
  a schema `description` reaches an agent as text but is not scanned. Today
  none names `spawn_agent`; review covers a new one.
- **Prose that looks like a call fails closed.** Text such as
  `spawn_agent (the dispatcher)` is parsed as a call and fails. Write the name
  without a following parenthesis.
- **Outside the gate.** Hook-emitted context, plugin-manifest text, and later
  user prompts are not scanned. The gate does not measure the canary token
  target.
- **Linux validation.** It does not cover macOS plugin CI or the two
  real-sandbox `test_gate_hardening.py` cases. The orchestrator runs those
  before merging.
