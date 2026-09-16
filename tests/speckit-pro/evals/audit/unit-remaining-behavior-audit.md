# Layer 4 Remaining Behavior Audit — Mutation Helpers

## Verdict

This bounded slice deeply reviews all **192 frozen loaded families** in
`tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`. The audited
baseline matched the frozen inventory (`sha256:
896cc7f7484ae8018952bb6ff01d77ac25782d3ce1c170213dd74c65c743174f`).
The accepted nine-family remediation is now implemented and focused-verified at
source sha256 `632118246ca4eb27ec81004185508224c1fb03fcfbca89183d48a6ef8cb33192`.

The review found **183 keep**, **8 merge**, **1 replace**, and **0 remove**
dispositions. The eight merges and one replacement are resolved. It is not a
claim that Layer 4 is complete: after excluding the six earlier audit scopes,
**462 of the frozen Layer 4 families remain**.

## Exact accounting

| Measure | Count |
|---|---:|
| Frozen Layer 4 executables | 84 |
| Frozen Layer 4 loaded families | 1,615 |
| Earlier audit union | 55 files / 961 families |
| Remaining before this slice | 654 |
| Files selected here | 1 |
| Frozen families reviewed here | 192 |
| Overlap with earlier audit file lists | 0 |
| Remaining after this slice | 462 |

Frozen counts are deliberately separate: the file declared 192 executable methods,
contains 1,529 static assertion sites overall, has 1,252 assertion sites inside
the 192 loaded bodies, and has 15 static `subTest` call sites overall (9 inside
loaded bodies). It also has five preview/dry-run-named families and one
skip-decorated family. These measures are not interchangeable and do not turn
one method into multiple loaded families.

After remediation the file loads 186 methods, with 1,455 static assertion sites,
1,178 assertion sites inside loaded bodies, and 17 static `subTest` call sites.
The six-method decrease is exactly the eight-old-methods-to-two-matrices merge.
The two matrices generate eight case vectors, but those subtests are not counted
as eight loaded families. The nine original behavior vectors remain: eight
matrix cases plus the one secure-lock behavior.

The focused deterministic run passed **186/186**, with zero runtime skips:

`python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py`

## Implemented replacement

`MutationHelperTests.test_mutation_lock_directory_can_be_reused_on_python_311`
at frozen line 7771 was too weak. Its equality-only oracle passed when
`mutation_lock_dir` returned the same constant nonexistent path twice.

It is replaced by
`MutationHelperTests.test_mutation_lock_directory_is_created_secure_and_reused_on_python_311`.
The replacement patches the temporary root, calls twice, and asserts both
results equal the expected `speckit-pro-mutation-locks` directory; the path
exists; it is a real directory and not a symlink; its mode is `0700`; and its
owner matches `getuid()` where available. Its embedded negative control proves
that returning the same constant nonexistent path twice is rejected.

## Implemented evidence-grounded merges

Eight families repeated two behavior matrices and are merged without losing any
scenario or oracle:

1. Frozen lines 2433, 2471, 2505, and 2535 now map to
   `MutationHelperTests.test_install_codex_agents_failure_packaging_matrix`.
   It generates four subtests for operation `write`/`removal` crossed with secondary
   fault `backup_cleanup`/`target_read`. It retains the primary exception text,
   exactly-one-backup assertion, `preserved_paths`, and `cleanup_errors`.
2. Frozen lines 2572, 2627, 2687, and 2736 now map to
   `MutationHelperTests.test_install_codex_agents_restore_failure_packaging_matrix`.
   It generates four subtests for operation `write`/`removal` crossed with restore
   form `plain`/`recovery_copy`. It retains conflict text, backup and target
   `preserved_paths`, `secondary_restore_failure`, and
   `recovery_copy_incomplete` where injected.

Ripwire reported two exact-clone groups, but both are nested fault callbacks,
not loaded family bodies. Its type-3 output contained 198 family-to-family pair
rows spanning 112 unique families and 14 clusters. Body review showed that the
remaining near matches exercise different operations, race windows, injected
failures, platform backends, or final-state evidence, so they remain separate.

## Qualification limits

- Forty Windows-named families use `FakeWindowsKernel32`, patched `os.name`, and
  patched `ctypes` behavior. They are useful deterministic ABI and race-window
  simulations, but they are not live Windows-host qualification.
- PR-emission families capture a command plan and explicitly block deferred live
  mutation. They are not live GitHub or remote-Git proof.
- This slice launches no provider, Docker daemon, remote Git endpoint, or live
  GitHub mutation. Temporary local repositories and files are simulation only.
- Preview/dry-run and platform-conditional families remain loaded and reviewed;
  none is removed merely because it is optional, preview-oriented, or skipped
  on a different host.

## Negative-control sensitivity

Seven bounded controls were evaluated. Six were detected:

- two distinct mutation-lock paths;
- an empty route-policy mapping;
- corrupted Windows atomic-write state without target content;
- an unmatched PR route returning an empty response instead of `input_error`;
- forged UAT success before dirty-worktree refusal; and
- corruption of the request schema required fields and mode enum.

The previously surviving control—returning the same nonexistent mutation-lock
path twice—is now detected by the replacement. This added sensitivity proof is
not counted as another loaded family or original behavior vector. No vacuous
assertion family was found. Narrow one-assert families were body-reviewed; their
oracles observe ordering, handle identity, or exact fail-closed exceptions
rather than mere execution.

## Current-tree blocker preserved

The focused file is green, but generated runner trust metadata remains stale and
must continue to fail closed. At this snapshot:

- `speckit_pro_runner/gates/active_path_guard.py` actual sha256 is
  `34c525bfef929747539d191036e7ee18b9505410c64ca4971ac5ac29b940e06b`,
  while the recorded value is
  `1ce1992da223fce9764509ad65e29201f74e6fdd3bbb55ce23c3c0a817a15f24`.
- `speckit_pro_runner/gates/suite.py` actual sha256 is
  `9de2187107de87e3ba60dcb4ccf4efd4dd31e377c14814ec285d0d9354dc9cdd`,
  while the recorded value is
  `952ba73a708e849af054dcf324423f4c6cf89fd3edc76f6f02d2ca9c966bfa8f`.

This audit does not regenerate artifacts. Regeneration belongs after concurrent
runner-source changes settle. Because this report adds tracked Markdown under
`tests/speckit-pro/`, the repository's docs reference-generation follow-up also
remains an integration responsibility.

## Ripwire completion gates

`ripwire . --quality-delta` exited 2 against the Git HEAD fallback baseline:
606 regressions, 49 minor, 74 preexisting-worse, 532 new-symbol, and 25 gating
findings. This is a whole dirty-worktree result dominated by concurrent changes.
The first gate pairs a concurrently added parity fixture with the preexisting
`assert_response` helper in this test file; neither new matrix nor the secure-lock
replacement is a gating preexisting-worse symbol. Ripwire reports both matrices
as non-gating new-symbol complexity/verbosity findings, the visible cost of
retaining eight explicit fault vectors inside two table-driven methods.

`ripwire . --test-gate` exited 4 with 36 changed files, 1,967 impacted symbols,
144 test obligations, and 85 untested impacted symbols (25 shown). That is also
a whole dirty-worktree obligation. This audit ran only the authorized focused
mutation-helper executable and did not expand into native, provider, Docker,
remote, or full-suite execution.

The machine-readable companion records every family ID, source citation, body
hash, exact boundary evidence, assertion sensitivity, simulation limits,
disposition, and replacement contract.
