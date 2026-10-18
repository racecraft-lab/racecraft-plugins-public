# Repair prompt security follow-up

## Scope and design

Finding `F1384-c5996f37` concerns repair prompt injection: supplied text could
become an active-looking remedy or change the prompt's display boundaries.
The public seam is the `plan-review-prompt` runner request. The policy layer
owns one display encoder, used by every finding, request and withdrawal field
rendered into the copyable prompt. Each value is a single-line ASCII JSON
string with punctuation escaped, preserving its exact decoded value while
preventing Markdown fences, links, mentions, control characters and bidi
characters from changing the display. Only validated request kinds and fixed
labels supply structure. Summaries are context; withdrawn text is history.
Structured response data retains the original values and selection decisions.

## Variant coverage

All tests below are in `tests/speckit-pro/unit/test-plan-review-prompt.py` and
run against source and both generated host payloads.

| Variant | Test |
| --- | --- |
| Summary newline forges a remedy | `test_summary_newlines_cannot_forge_active_remedies` |
| Summary backtick or tilde fence escapes display | `test_summary_fences_cannot_escape_the_display_context` |
| Withdrawn custom text forges a remedy, including newline, carriage return and fence forms | `test_withdrawn_text_cannot_forge_active_remedies` |
| Summary links, autolinks, mentions, POSIX/Windows paths, controls, Unicode separators and bidi | `test_summary_links_mentions_paths_controls_and_bidi_are_inert` |
| Operator-selected active instruction newline, fences, quotes and literal escapes | `test_active_instructions_are_quoted_without_changing_selection` |
| Finding and request identifiers with newlines, fences, quotes, literal escapes, mentions and bidi | `test_finding_and_request_identifiers_cannot_change_prompt_structure` |
| Closed kind enumeration and exact withdrawal finding/text after display encoding | `test_kind_and_exact_withdrawal_contract_survive_encoded_display` |
| Every displayed field with all ASCII characters and Unicode control/separator/bidi forms | `test_every_display_field_keeps_ascii_and_unicode_attacks_inside_one_value` |

The new variant tests failed against the original renderer before the fix.
The adversarial pass checks every interpolation in `_section`: finding ID,
summary, request ID, active text and withdrawn text. Request finding links
select the section by exact identity; withdrawal fields select an existing
custom request by exact identity and text. No path is opened from any of those
display values, so link, path and rename variants have no separate file-action
path here. The reviewed revision is a computed digest verified by equality,
not caller-supplied display text. Both hosts ship the same Python implementation.

## Known limits

- Encoding preserves a display boundary; it cannot guarantee an agent obeys
  the prompt. An active instruction remains an operator-selected instruction.
  No tool executes merely because a displayed value contains a link or path.
- `kind` is a closed enumeration and withdrawals require the stored finding
  and exact custom text. Arbitrary kinds or mismatched withdrawal text cannot
  reach the renderer as accepted requests; the rejection tests retain this
  invariant.
- The separate Low inventory finding `F1384-658c7e4d` remains open and outside
  this fix. Caller-supplied finding subsets and re-keyed IDs are still accepted;
  that path requires departure from the skill's full-inventory procedure.
- The skill's step 4 list of input fields is prose, and no check ties it to the
  helper's required field set. The gap predates this review delta and covers the
  older fields too. A renamed field still fails closed at the runner, which names it.
- Escaping all punctuation makes the copyable prompt harder for a person to read
  before copying it. This is the accepted cost of the display boundary; decoding
  each value restores its exact text.
- Linux verification cannot cover macOS plugin CI or
  `test_gate_hardening.py::test_pr_test_code_cannot_touch_the_host_under_the_real_sandbox`
  and `test_gate_hardening.py::test_pr_test_code_cannot_create_or_modify_any_file_in_the_clone`.
  Those remain orchestrator pre-merge checks. No live interview was exercised.
