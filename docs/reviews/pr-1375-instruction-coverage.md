# PR 1375: complete instruction review coverage

The dispatch gate binds each rendered Codex skill file and each complete agent TOML
file (including descriptions and other metadata) to its reviewed bytes before examining calls
or excerpts. The inventory includes surfaces with no dispatch keywords.
Adding, renaming, editing, emptying, reordering, or changing whitespace in an
instruction surface requires explicit review of its content pin. Existing
readable excerpts remain available alongside the complete-surface SHA-256 pins. Files are decoded strictly without newline
normalization before pin comparison.

The pins freeze the skill and agent file content at the previously reviewed head
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
- Coverage is the rendered Codex skill tree and generated Codex agent TOML
  files. Hook-emitted context, plugin-manifest text, and later user prompts
  are outside this gate. None of those surfaces changes in this follow-up.
  The gate also does not measure the canary token target.
- Linux validation does not cover macOS plugin CI or the two real-sandbox
  `test_gate_hardening.py` cases. The orchestrator runs those before merging.
