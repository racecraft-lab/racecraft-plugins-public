# Scaffold branch identity: review limits

The runner derives one scaffold branch from the exact roadmap ID and title.
Both rendered hosts call that same read-only seam before worktree placement.
Naming policy lives in
[`scaffold_identity.py`](../../speckit-pro/speckit_pro_runner/helpers/scaffold_identity.py);
identity normalization lives in the public
[`spec_identity.py`](../../speckit-pro/speckit_pro_runner/spec_identity.py) owner
shared with the spec index. That existing contract already recognizes namespaced
directories and letter-suffixed numbers. Scaffold derives `<number>-<slug>` for
SPEC and `<lowercase-namespace>-<number>-<slug>` otherwise, including `006a`.
The existing placement helper still validates the branch and task-local path.

## Known limits

- **ASCII normalization can lose non-ASCII words.** NFKD normalization followed
  by ASCII conversion gives `cafe` for `Café`, but drops characters that do not
  decompose to ASCII. Mixed-language titles can therefore lose text; wholly
  non-ASCII titles may produce no slug and are rejected. These are reachable
  input limits, although the reported defect uses an ASCII title. Both hosts
  still return the same result for identical inputs.
- **Very long titles have no naming-helper length cap.** A title exceeding a
  worktree filesystem's segment limit can be refused during placement or Git
  creation. No such title appears in the reported example; this PR does not
  add a platform-specific truncation rule or claim coverage of that case.
- **Legacy branches are preserved.** An in-progress entry whose existing
  branch differs from the canonical result requires operator reconciliation.
  Scaffold reports both identities and stops rather than creating a second
  setup. This PR does not rename or migrate existing branches.
- **Completion is a scaffold hand-off.** `scaffold_complete` is registered as
  an authority reason, printed after successful scaffold completion. Scaffold
  does not call `finalize-run`; this change does not add a new finalization
  disposition. The operator starts planning in a separate invocation.
- **Static graph evidence has limits.** Ripwire does not model these runner
  subprocess calls or unittest discovery as direct call edges. Its new-test
  dead-code rows are not evidence that the tests are unrun; counted VM test
  results provide execution evidence. Small additive registry, fixture and
  manifest table-size rows are non-gating. No quality acknowledgments were added.

## Retained cross-host review notes

- **R1342-e849f2b3 (Low): interrupted legacy setup.** A half-scaffolded Pending
  entry under an old model-chosen branch can bypass the In Progress check and
  create a second worktree under the canonical name. The roadmap switches to
  In Progress only at Step 8. This transition case requires operator
  reconciliation; this fix does not migrate legacy setups.
- **R1342-3c272119 (Info): operator boundaries.** The exception that an
  operator-chosen boundary ends the run instead of deferring is stated only in
  stop-policy guidance. This pre-existing pattern remains a note.
- **R1342-a4332e5e (Info): finalization vocabulary.** `finalize-run` accepts
  `scaffold_complete` inside autopilot, although no real autopilot path names
  it. This remains a note; scaffold does not call `finalize-run`.
- **R1342-73a18938 (Info): review size.** The reviewed head contained about
  275 reviewable LOC, six production files and 16 handwritten files, one over
  the 15-file warning tier. These are the original review's counts; the shared
  owner and regression coverage add to that diff.

## Host coverage

The provider-free tests execute each rendered host's documented helper request
against each packaged runner and check identical SPEC, namespaced and
letter-suffixed branches. They also verify the registered
completion marker on both hosts, generated payload parity and the shared
zero-bash guard. Interactive question steps were checked from their documented
shape, not exercised in a live Claude Code or Codex interview. Native macOS CI
and real sandbox hardening remain orchestrator checks.
