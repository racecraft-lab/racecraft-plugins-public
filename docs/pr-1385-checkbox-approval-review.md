# Checkbox approval binding repair

Finding `F1385-400139c5` is an **approval-binding false pass**: a section-wide
checkbox exemption treats planning choices as completion evidence. A contributor
can uncheck an approved release requirement and verify the old approval.

The shared policy layer, `helpers/planning_approval.py`, owns the projection.
Implementation Progress uses typed table counters and summaries; arbitrary
checkboxes there remain planning inputs. Files Generated projects completion
state only for a bare backticked path with no prose or link wrapper. The path
itself stays bound. Success Criteria and Success Criteria Summary retain their
explicit completion-tick contract. Pre-Implementation Setup stays bound.

The public seam is manifest, record and verify, exercised on source and both
packaged hosts by `tests/speckit-pro/unit/test-planning-approval-checkboxes.py`.

| Variant | Test in `PlanningCheckboxTest` |
| --- | --- |
| Top-level / Phase 7 Implementation Progress, checked `x` / `X` to unchecked planning choice | `test_implementation_progress_choices_invalidate_record` |
| Top-level / Phase 7 Files Generated, checked `x` / `X` to unchecked planning choice | `test_files_generated_choices_invalidate_record` |
| Success Criteria / Success Criteria Summary completion ticks (Info control) | `test_success_criteria_ticks_preserve_record` |
| Pre-Implementation Setup planning choices (Info control) | `test_preimplementation_choices_invalidate_record` |
| Bare generated-path completion ticks | `test_files_generated_path_ticks_preserve_record` |
| Nested choices, backticked prose, path plus planning prose, Markdown links, fenced paths | `test_checkbox_lookalikes_keep_choices_bound` |
| Renamed generated path or replacement with a link | `test_generated_path_rename_and_link_edits_invalidate_record` |

Every checkbox-state case covers both `x` and `X`. Preserved-progress cases also
assert that a later planning-choice change still invalidates the record.
The Info controls intentionally passed before the repair; they define behavior
that must survive the security fix.

The unfixed VM run passed 48/120 cases and failed 72, including every reported
Medium heading/case combination on source, Claude and Codex. Failures showed an
unchanged manifest digest after unchecking the approved planning choice.

## Focused adversarial inventory

The changed module has three checkbox scopes: Implementation Progress, Files
Generated, and success criteria. The exemption is now a per-line payload
contract rather than a heading-wide boolean. Other progress fields are typed
table cells, typed summary values, or declared scaffolding. Fences stay literal.
The same policy is regenerated into both host payloads; no host-specific skill,
agent, or overlay rule is needed.

## Known limits

- A bare backticked path in Files Generated declares an output completion row;
  its tick does not express a planning choice. Paths with spaces or Markdown
  link wrappers fail closed as planning inputs. Renaming a path changes the
  manifest. The projection does not claim the file was generated or validated.
- Success Criteria ticks are completion by the existing contract; changing the
  criterion text still changes the manifest.
- Interactive confirmation is covered through its documented JSON contract,
  not exercised live in this unattended repair.
- Linux VM tests do not provide native macOS plugin CI coverage or execute
  `test_gate_hardening.py::test_pr_test_code_cannot_touch_the_host_under_the_real_sandbox`
  and
  `test_gate_hardening.py::test_pr_test_code_cannot_create_or_modify_any_file_in_the_clone`.
  The orchestrator must run those on macOS before merging.
- The finding remains open until a later Daybreak receipt includes the fix
  commits and accounts for every reported variant.
- Ripwire reports the new unittest methods as dead code, although the unittest
  loader executes them. Its duplication detector also groups the checkbox
  lookalike input tuple with the unrelated external-link rejection tuple in
  `test-checklist-edits.py`. Those tests exercise different public contracts;
  their shared normalized tuple/call syntax is not duplicate policy or logic.
  This advisory false positive is reported without changing the acknowledgement
  ledger or weakening either test.
