# PR 1375: complete instruction review coverage

The dispatch gate binds each rendered Codex skill file and each agent's
`developer_instructions` to its complete reviewed text before examining calls
or excerpts. The inventory includes surfaces with no dispatch keywords.
Adding, renaming, editing, emptying, reordering, or changing whitespace in an
instruction surface requires explicit review of its content pin. Existing
readable excerpts remain available alongside the complete-surface SHA-256 pins.

The pins freeze the instruction content at the previously reviewed head
`826dcf3f2421e63800555cd608229d771c246295`. They are not automatically refreshed
by artifact generation. Review source changes before changing a pin; inspect
the complete source file when adding a new inventory entry.

## Known limits

- The `prompt`, `context`, and `options` call examples cannot dispatch through
  the current hosted tool: its schema has no such fields. These are the Low
  and Info variants in the [source Daybreak review](https://github.com/racecraft-lab/racecraft-plugins-public/pull/1375#issuecomment-6244445195),
  rather than reachable tool invocations. Regression subtests still require
  review of their text, so example syntax cannot hide instructions.
- Content pins prove that text matches reviewed evidence; they do not infer
  natural-language intent or approve an inventory edit. Inventory edits require
  review just as the existing literal excerpt inventory did.
- This is static repository coverage of shipped instructions. It does not
  measure the canary token target or inspect prompts supplied later by users.
  Those remain outside this PR's acceptance claim.
- Linux validation does not cover macOS plugin CI or the two real-sandbox
  `test_gate_hardening.py` cases. The orchestrator runs those before merging.
