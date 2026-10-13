# PR 1341 publication ownership repair

F1341-7616e256: **unowned artifact publication**. The plan terminal helper
previously removed only gallery-named pages and staged all of `specs/`.
Unknown entries could reach the public branch without a generated outcome.

The artifact publication owner now enumerates the confined directory and
requires its entries to be exactly the generated pages. Unexpected entries
remain available for recovery; publication stops with `integrity_failure`.
The terminal helper binds the validated handoff digests to Git blob identities,
checks every staging and commit boundary, and checks the committed tree before
each push. Staging covers the selected feature, workflow, and state. Changes to
artifacts from another feature cannot acquire this run's publication ownership.

The public seam is `finish-plan-stage`, exercised with real disposable Git
repositories and bare remotes. The shared policy ships in both host payloads.

## Variant coverage

All names below belong to `PublicationOwnershipTests` in
`tests/speckit-pro/unit/test-plan-stage-terminal.py`.

| Variant | Regression test |
| --- | --- |
| Interrupted author publication retains `.artifact-author-<page>.<token>.tmp` | `test_retained_author_temporary_blocks_publication` |
| Final HTML basename absent from the gallery | `test_unowned_final_html_blocks_publication` |
| Unowned hard link to outside readable bytes | `test_unowned_hardlink_blocks_publication_without_reading_target` |
| Unowned symlink would publish its target string | `test_unowned_symlink_blocks_publication_without_publishing_target_string` |
| Non-HTML file, nested directory, FIFO, broken link, spaces and newline in names | `test_every_unexpected_entry_type_blocks_publication` |
| Staged then removed unowned file at the boundary, packet or bookkeeping commit | `test_staged_then_removed_unowned_entries_block_every_commit_window` |
| Rename, hard-link or symlink substitution while staging a generated page | `test_staging_substitution_cannot_publish_unvalidated_page_bytes_or_links` |
| Unowned file already present in the committed tree | `test_committed_unowned_entry_blocks_push` |
| Unrelated feature's untracked artifacts | `test_unrelated_feature_artifacts_are_not_swept_into_the_commit` |
| Unrelated feature's staged artifacts | `test_unowned_staged_artifacts_from_another_feature_block_publication` |

The four reported variants and staging substitution/window cases exercise both
host inputs. `PayloadEvidenceTests` repeats this ownership suite against both
generated runners. Existing successful publication, gaps, escaped narrative
edits, interrupted authoring and confined cleanup tests remain mandatory.

## Adversarial review

The repair covers the directory scan, index entries at all three commits,
committed entries, both pushes, and the broad staging path. Files removed after
staging are checked through Git, rather than inferred from a later directory
scan. Owned filenames are insufficient: modes and exact blob identities must
also match, preventing substituted bytes or symbolic links from acquiring
ownership. No unexpected artifact is deleted as a recovery shortcut.

Git's [index output](https://git-scm.com/docs/git-ls-files),
[tree output](https://git-scm.com/docs/git-ls-tree), and
[object storage format](https://git-scm.com/docs/user-manual#_object_storage_format)
define the serialized evidence used by the checks. SHA-256 repositories use the
same blob content and header with the repository's selected hash function, as
described in the [hash transition](https://git-scm.com/docs/hash-function-transition).

## Known limits

- The prior accepted limits in [the terminal review follow-up](pr-1336-plan-terminal-review.md)
  remain unchanged. This delta does not reopen them.
- An actor who controls Git metadata or independently runs commits and pushes
  has authority outside the runner's publication boundary. These tests exercise
  filesystem entries and concurrent staging/commits observed by the helper;
  they do not claim to revoke independent Git authority.
- GitHub replies are scripted. No live preview or interactive question step is
  exercised; existing request-schema tests verify those contracts.
- Linux VM evidence does not establish macOS behavior. The orchestrator still
  owns native macOS plugin CI and
  `test_gate_hardening.py::test_pr_test_code_cannot_touch_the_host_under_the_real_sandbox`
  and
  `test_gate_hardening.py::test_pr_test_code_cannot_create_or_modify_any_file_in_the_clone`.
- Daybreak must re-check the pushed fix commits and account for every variant
  before resolving F1341-7616e256. This repair does not resolve that finding by
  itself or authorize a merge.
