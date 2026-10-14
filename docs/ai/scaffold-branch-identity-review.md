# Scaffold branch identity: review limits

The runner derives one scaffold branch from the exact roadmap ID and title.
Both rendered hosts call that same read-only seam before worktree placement.
Naming policy lives in
[`scaffold_identity.py`](../../speckit-pro/speckit_pro_runner/helpers/scaffold_identity.py);
the existing placement helper still validates the branch and task-local path.

## Known limits

- **Other namespaces and number forms fail closed.** Numeric spec directories
  belong to the SPEC namespace under the existing MOC contract. This helper
  accepts `SPEC-NNN` only, including lowercase spelling. Other inputs, such as
  `PRSG-001` or `SPEC-006a`, stop before placement or writes. Supporting them
  would require a separate directory-identity change; this PR does not make it.
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

## Host coverage

The provider-free tests execute each rendered host's documented helper request
and check the identical numeric branch. They also verify the registered
completion marker on both hosts, generated payload parity and the shared
zero-bash guard. Interactive question steps were checked from their documented
shape, not exercised in a live Claude Code or Codex interview. Native macOS CI
and real sandbox hardening remain orchestrator checks.
