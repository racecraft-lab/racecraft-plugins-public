# Planning finding inventory concurrency

Finding: **F1397-a6199644**, planning finding lost update.

The `finish-plan-stage` apply path on Claude and Codex calls `add_findings`.
Previously it parsed inventory bytes and later replaced the inventory without
requiring those bytes to remain current. A reviewer could record a request or
finding in that interval and lose it. Atomic replacement alone did not preserve
the complete authoritative inventory required by ADR 0013.

The repair captures bytes, existence, file identity, link count, mode and parent
identity together through safe directory descriptors. `add_findings` parses that
snapshot and passes it unchanged to checked publication. A stale snapshot causes
refusal before page generation. Existing-file publication checks the displaced
entry and restores it on conflict; missing-file publication uses exclusive
creation. The default content-only snapshot contract for other callers remains
unchanged. Both generated host payloads carry the shared runner repair.

## Regression coverage

All tests below live in `tests/speckit-pro/unit/test-plan-stage-terminal.py`,
class `InventoryConcurrencyTests`. Each race runs through `finish-plan-stage`
for both Claude and Codex and checks preservation plus refusal before pages.

| Variant | Test |
| --- | --- |
| Existing request edit after capture | `test_inventory_edit_after_capture_preserves_reviewer_requests_on_both_hosts` |
| Missing inventory created after capture | `test_inventory_creation_after_missing_capture_preserves_new_findings_on_both_hosts` |
| Existing request edit during temporary-file flush | `test_inventory_edit_during_publication_preserves_reviewer_requests_on_both_hosts` |
| Missing inventory created during temporary-file flush | `test_inventory_creation_during_publication_preserves_new_findings_on_both_hosts` |
| Existing request edit at atomic install | `test_inventory_edit_at_atomic_install_preserves_reviewer_requests_on_both_hosts` |
| Missing inventory created at atomic install | `test_inventory_creation_at_atomic_install_preserves_new_findings_on_both_hosts` |
| Parent renamed and replaced, even with identical bytes | `test_inventory_parent_replacement_with_identical_bytes_is_refused_on_both_hosts` |
| File replaced with identical bytes in a different inode | `test_inventory_identical_inode_replacement_is_refused_on_both_hosts` |
| Hard-link alias added after capture | `test_inventory_new_hardlink_alias_is_refused_on_both_hosts` |
| Symlink substituted after capture or at atomic install | `test_inventory_symlink_substitution_is_refused_on_both_hosts` |
| Hard link substituted after capture or at atomic install | `test_inventory_hardlink_substitution_is_refused_on_both_hosts` |
| Pre-existing symlink and hard link remain refused | `test_existing_symlink_and_hardlink_inventories_remain_refused` |

The pre-existing-link checks preserve an already working refusal. Their late
substitution counterparts exercise the publication race. The race tests first
run against the unfixed implementation to demonstrate loss or a false success.

## Focused adversarial review

The inventory merges every existing key and request list from the same snapshot;
the defense applies to all finding IDs and request contents. Clean inventories
and strict shortfalls use the same publication path. No host-specific writer is
introduced. Adjacent approval and map writes already pass expected snapshots;
this repair preserves their default snapshot contract.

## Known limits

- The parent-replacement actor already controls the feature directory. The
  repair refuses a changed parent before opening the publication temporary file,
  and descriptor-relative publication cannot redirect a later write into a
  replacement directory. If the parent is renamed after the writer opens it,
  publication can land in that renamed-away directory through its held descriptor;
  the replacement directory's inventory is not overwritten. The regression test
  covers capture through reopening the parent. This does not revoke the actor's
  existing directory access.
- Info: an uncoordinated writer can retain a descriptor for the former inventory
  inode and write after the successful displaced-entry check but before cleanup
  removes that old inode. That write targets an already displaced inode rather
  than the canonical inventory pathname. Rename-based publication cannot make
  arbitrary external descriptor writers participate in the inventory protocol;
  this existing publication limitation is outside the pathname races repaired here.
- Missing or unsafe parent directories fail closed; the helper does not create
  a replacement feature directory.
- Daybreak must re-check a receipt containing the fix commits before resolving
  the finding. This repair does not authorize a merge.
- Linux tests do not provide native macOS or real macOS sandbox coverage. Those
  remain with the orchestrator before merging.
