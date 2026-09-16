# Layer 4 release/tooling unit audit

Status: **exact-scope audit, not qualification**

The companion `unit-release-tooling-audit.json` records every loaded family in
the twelve requested files. Each exact frozen-inventory ID has a disposition,
source line, evidence profile, assertion/subtest evidence, parameter source, and
skip count. The profiles state the requirement, failure mode, real execution
boundary, evidence, and any replacement.

## Scope result

- Reviewed: **194/194 loaded families** across **12/12 selected files**.
- Audit dispositions: **193 keep**, **1 replace**, **0 merge**, **0 remove**.
  The one replacement is now implemented and retains its audit lineage.
- All twelve sources matched their frozen SHA-256 when reviewed.
- This report covers only the named release/tooling chunk. It does **not** claim
  that all Layer 4 families have been audited.

| File | Families | Keep | Replace | Actual boundary |
|---|---:|---:|---:|---|
| `test-refresh-local-plugin.py` | 3 | 3 | 0 | Real CLI with tracked provider stubs and dry-run assertions |
| `test-release-pr-reconciliation.py` | 38 | 38 | 0 | Production logic with temporary Git/filesystems and injected GH/network/process I/O |
| `test-hosted-windows-preflight.py` | 34 | 34 | 0 | Emulated Windows facts and injected dispatch runners |
| `test-pr-checks-helpers.py` | 24 | 24 | 0 | Archive/filesystem integration and direct classification/result helpers |
| `test-docs-artifact.py` | 17 | 17 | 0 | Real temporary-filesystem confinement |
| `test-sync-marketplace-versions.py` | 1 | 1 | 0 | Real local CLI over temporary marketplace trees |
| `test-claude-hooks.py` | 1 | 1 | 0 | Real hook/local subprocess behavior, not a Claude session |
| `test-repo-bash-confinement.py` | 33 | 32 | 1 | Production parser over temporary Git trees plus one declaration family |
| `test-semantic-contract-identifiers.py` | 1 | 1 | 0 | Direct semantic registry dispatch |
| `test-privacy-scan.py` | 1 | 1 | 0 | Real tracked-tree privacy scan |
| `test-release-note-policy.py` | 15 | 15 | 0 | Direct parser/sanitizer behavior plus dependency declarations |
| `test-compose-release-notes.py` | 26 | 26 | 0 | Production composition with temporary snapshots and injected service I/O |

## Implemented replacement

`RepoBashConfinementTests.test_fixture_matrix_and_result_contract` did not
independently own the existence of its fixture cases. A bounded pre-repair
control patched its imported `CASES` list to empty for this unittest only. The
test ran and passed without entering the loop.

The replacement now asserts the exact ordered 36-case canonical roster before
iterating, while retaining every existing schema, status, blocking-count, and
finding-category assertion. The dedicated
`test_fixture_matrix_rejects_empty_roster` regression proves an empty roster is
rejected. No distinct Bash fixture case was removed.

- Frozen source SHA-256:
  `b5802e6fb623a2dfc7dba3f06070817f16e1b1030b0d20070b611f99931d3677`
- Implemented source SHA-256:
  `c9716c7278a238c01c6348abc50c67c510c521a30c46a2ba3898c8e38afdf6e9`
- Focused green evidence: empty-roster regression **1/1**; complete Bash
  confinement file **122/122**.

## Substantive keep boundaries

- Refresh-local-plugin tests execute the real helper, but provider interactions
  use tracked stubs. Dry-run output proves command construction, not installed
  client mutation.
- Release reconciliation/audit/lifecycle tests exercise production functions,
  byte-exact artifacts, temporary Git operations, and ordering. GH, HTTP, and
  selected subprocess edges are injected, so they do not qualify a remote
  release.
- Hosted Windows preflight tests thoroughly exercise architecture, platform,
  version, mutable-ref, timeout, JSON, envelope, metadata, change-selection,
  interpreter, and sentinel contracts. Windows facts are emulated on the
  current host; no hosted Windows runner was used.
- Three skip-decorated families are deliberate POSIX mode/symlink checks:
  tracked provider-stub execution, artifact executable-mode/symlink snapshots,
  and nonexecutable Actionlint rejection. Their absence on Windows is explicit.
- The two release-audit methods with zero direct assertion sites are not empty:
  both call `_assert_acquisition_failure`, whose body performs eight concrete
  return-code, call-count, byte, digest, summary, stdout, and stderr assertions.
- The `live_*` release-composition tests exercise live-path orchestration with
  injected service responses. They validate ordering, immutable snapshot reuse,
  and tamper rejection, not a live release mutation.
- Release-note policy cases use fixed nonempty adversarial inputs and direct
  production parsing/sanitization. Dependency/import families are retained as
  declaration checks and are not counted as sanitizer behavior.
- Claude hook tests run the real hook ports and inspect source restrictions, but
  do not execute an interactive Claude session.

## Focused execution

The twelve focused files produced **420/423 counted checks passing**:

- Eleven files passed completely.
- `test-privacy-scan.py` passed 7/10 and correctly rejected the concurrent tree
  in three privacy categories: local absolute paths, raw identifiers, and
  dynamic local identity/workspace terms. The findings originate outside the
  two files owned by this audit and were not edited here.

That failure is positive evidence that the privacy family scans real tracked
content rather than a mock or tautology. It also means the current shared tree
is not privacy-clean; this report does not reinterpret the failure as a pass.

Redacted exact findings:

- `absolute-local-home-path`:
  `integration-parity-inventory.json:131`, `:132`.
- `raw-uuid`: `test-native-eval-codex-rollouts.py:25-29`, `:299`, and
  `test-native-eval-execution.py:64-67`.
- `dynamic-local-identity-or-workspace-term`:
  `integration-parity-inventory.json:131`, `:132`.

Only file, line, and finding type are recorded; sensitive values are omitted.

## Post-audit privacy correction

The frozen `PrivacyScanTests.test_privacy_scan_contract` record remains
unchanged: frozen source SHA-256 `85380ce98accebe5e65fed59679f3a31c1d2dfe602a4abe4d78e2235d9a0883d`,
line 270, ten direct assertion sites, one subtest site, one fixed ten-check
roster, and no skip decorator. Its **keep** disposition also remains unchanged.

The current family is recorded separately at source SHA-256
`869d75db25dc13d229318a30c5543ba9f23c2f1c1ea565e8cfd8738d82a0c700`,
line 272, and body SHA-256
`faa65eb76e1eb6cb41e447746bc4d60821902400d031b76825d893c0a7e3925f`.
The correction permits exactly the controller-owned, no-network native-eval
Git fixture identity; it does not permit the `.invalid` domain or any address
pattern. A targeted control accepts that one identity and still reports a
different synthetic `.invalid` address. That negative address is assembled
from fixed source fragments only to exercise the scanner without making its
own fault input look like repository leakage; it is not derived from or hiding
an actual address.

RED evidence was two-stage: the current tree first failed **9/10** on the two
fixture identity lines, and the newly added exact-address control also failed
before the allowlist entry was added. GREEN evidence is privacy **10/10** plus
successful Python compilation and whitespace validation. Root independently
confirmed the privacy gate at **10/10**. No provider, network, generator, broad-suite, or host
configuration action was performed.

No provider, hosted runner, network service, release mutation, broad suite, or
generated artifact operation was run. If any of the twelve recorded source
hashes changes, the affected family bodies must be re-audited before applying
these dispositions.
