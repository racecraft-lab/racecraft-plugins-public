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

## Cross-host review notes

These notes are accepted limits from the cross-host review at head
`97d551cb618278532f48f92701138503cea4eec0`. They are not reachable defects.

- **Bare backticked token under Files Generated (Low).** The completion-tick
  match is shape-based. A planning choice written as a bare backticked token,
  such as ``- [x] `require-signed-release` ``, under a heading named Files
  Generated would count as a completion tick. No template or guidance writes a
  planning choice in that form there, and adding such a line changes the
  manifest, so a contributor can only toggle a line that was approved in that
  shape.
- **Function-level import in `read_only.py` (Low).** The stage resolver imports
  `admit_implement` from `planning_approval` at call time because that module
  imports the resolver's map functions. The import runs after both modules are
  initialized, so no runtime failure is reachable. It stays a structural note
  for a later ownership refactor.
- **Malformed `findings` in a stored record.** A record whose `findings` is not
  an object now refuses with the `record` field instead of an internal failure.
- **Non-text `reviewed_evidence` entries in a stored record.** A record whose
  `reviewed_evidence` holds a list or object now refuses with the `record` field
  instead of an internal failure (cross-host review at head
  `08c5592008fe76b39a94c1dc0c2ab25b586727bc`).

### Repository identity notes (cross-host review at head `c27e3838fc9ad9cc5a9788c4b416312816aa986a`)

- **Exact origin spelling (Low).** Admission compares the record's
  `repository` to the `origin` URL as an exact string. A record in a different
  letter case, or an origin with a trailing slash, an SSH host alias or a user
  or token in the URL, refuses with `repository` although it names the same
  repository. Every case fails closed: no foreign repository is admitted. The
  contract now tells the recorder to copy `owner/name` exactly as `origin`
  spells it, which covers the ordinary clone forms.
- **`verify` does not check the origin (Info).** Only `admit` binds the
  checkout's origin, as ADR 0013 requires for implement entry; `verify` can
  pass for a record that `admit` refuses. Record now runs the same origin
  check, so this needs the origin or the stored record to change after
  recording.

### Repository identity fixes and notes (fix round after head `cb78f81335eea1c207b58da6ab91449cb3428699`)

- **Record agrees with admission (R1385-a6c81a9c, fixed).** `action=record`
  runs the admission origin check before it writes, in `dry_run` and `apply`.
  A `repository` that admission would refuse now refuses at record time with
  `planning approval field repository`, so no record is keyed to a manifest
  digest that can never be admitted.
- **One home for GitHub remote spellings (R1385-269bf837, fixed).**
  `speckit_pro_runner/github_remote.py` now holds the spellings. Admission,
  gh-stack qualification and the egress policy prose take them from it, and a
  test fails when a second runner module spells a GitHub remote. The move kept
  each caller's exact results, so two differences remain on purpose. gh-stack
  qualification still accepts only its three-spelling profile (no bare scp
  spelling, no `ssh://` URL), now named `GH_STACK_FORMS` in the owner; a test
  pins it. The egress prose still names the push URL, while admission reads
  the fetch URL. Each difference fails closed, and changing either is its own
  behavior change.
- **Probe timeout literal (R1385-08cf55b3, Low).** Admission probes `origin`
  with a 10 second timeout; gh-stack qualification uses its own 20 second
  constant. Each caller keeps its own probe, so the owner holds no timeout. A
  `git remote get-url` call reads local config and returns at once; a hang
  only makes admission refuse with `repository`, so no wrong admission is
  reachable.
- **Non-string `repository` interpolated (R1385-cb03af6c, Info).** A stored
  `null` or number is formatted into the spellings (for example
  `https://github.com/None`) before any type check. Git never prints such an
  origin for a real GitHub remote, so the match fails and the record refuses
  with `repository`, as the tests show.
- **Arch edge `gates/payloads.py` to `runtime.py` (R1385-ab772b91, Info).**
  `ripwire --arch` reports this edge as new against the baseline. An earlier
  pull request added it, outside this diff, and this round adds no new edge.
