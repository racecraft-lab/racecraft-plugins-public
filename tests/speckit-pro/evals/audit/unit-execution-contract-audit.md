# Layer 4 unit execution-contract audit

## Verdict

This bounded deep review covers exactly seven registered Layer 4 unit executables and all 228 families loaded by their custom suites. All seven source hashes match the frozen deterministic inventory. The focused runs passed 443/443 house-counted units, including 266 generated subtests, with zero runtime skips on this host.

All 228 families are retained. No merge, replacement, or removal is supported by the reviewed bodies: each family has a distinct requirement or failure boundary and either direct assertions or a reviewed assertion-bearing helper path. This is not an audit of all Layer 4.

## Exact counts

| Executable | Loaded families | Static assertions | Static subtest sites | Runtime subtests | Counted units | Runtime skips |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| test-phase7-task-partition.py | 35 | 73 | 13 | 26 | 53 | 0 |
| test-task-execution.py | 39 | 63 | 6 | 23 | 56 | 0 |
| test-batched-task-results.py | 30 | 63 | 3 | 9 | 37 | 0 |
| test-execution-control.py | 45 | 123 | 10 | 43 | 78 | 0 |
| test-verification-docker.py | 45 | 168 | 20 | 103 | 133 | 0 |
| test-verification-git.py | 21 | 79 | 4 | 14 | 31 | 0 |
| test-autopilot-execution-contract.py | 13 | 42 | 8 | 48 | 55 | 0 |
| **Total** | **228** | **611** | **64** | **266** | **443** | **0** |

The house counter reports each generated subtest as one unit and each method without subtests as one unit. There are 51 methods with runtime subtests and 177 without them. Six families are skip-decorated, although none skipped on this host. Five family names explicitly cover preview or dry-run behavior.

## Findings

1. **Unit evidence is not live qualification.** The Docker suite uses synthetic archives, fixture executables, local Python subprocesses, and fake or patched clients (`tests/speckit-pro/unit/test-verification-docker.py:362`). The Git suite uses disposable local repositories and patches Docker boundaries (`tests/speckit-pro/unit/test-verification-git.py:27`). No Docker daemon, remote Git endpoint, native agent, or provider was contacted.
2. **Eleven autopilot families are structural drift guards.** The execution-policy classes inspect skill, template, agent, schema, and reference text (`tests/speckit-pro/unit/test-autopilot-execution-contract.py:25-81`, `:149-224`). They are useful, but they are not native execution proof.
3. **Custom loading matters.** The registered `test-execution-control.py` suite explicitly loads 45 families (`tests/speckit-pro/unit/test-execution-control.py:619-623`). Default module discovery would additionally inherit 20 verification methods into `DockerVerificationTests` and misleadingly report 65.
4. **Platform coverage remains conditional.** Five Docker families and one Git family have platform decorators. All ran here, but this does not establish other-host behavior.
5. **Clone similarity does not justify consolidation here.** Ripwire reports four Type-2 exact or renamed-body groups covering nine task-execution families and 35 Type-3 near-match rows touching the seven files. Manual review found distinct injected inputs and claims: new versus repeated phase boundaries, route versus repeated-heading TDD violations, dependency versus ownership aliases, and ordinary versus extensionless references. The near matches are shared fixture scaffolding, sibling cases, or comparisons to out-of-scope tests—not equivalent requirements. All remain `keep`. Every family has an assertion path, and seven representative failure controls passed 7/7.

## Evidence modes and limits

- `test-phase7-task-partition.py` and `test-task-execution.py` run helpers in process over temporary task and feature trees. They do not dispatch agents.
- `test-batched-task-results.py` uses temporary journals and two local CLI subprocess families. Native observations are synthetic records.
- `test-execution-control.py` uses temporary ledgers with patched process and Docker boundaries; its Docker families do not contact a daemon.
- `test-verification-docker.py` validates deterministic construction, policy, lifecycle, readback, and cleanup behavior with fakes, mocks, and local processes.
- `test-verification-git.py` exercises real local Git object and configuration behavior in disposable repositories, but not remotes or production repository diversity.
- `test-autopilot-execution-contract.py` combines authored-text and schema drift checks with two temporary-ledger mirror families.

The JSON ledger records the exact simulation mode, limitation, test doubles, source span, body hash, generated-subtest count, and disposition for every family.

## Dispositions

- Keep: 228
- Merge: 0
- Replace: 0
- Remove: 0

## Reproduction

- Frozen inventory: `tests/speckit-pro/evals/audit/deterministic-inventory.json`
- Frozen manifest SHA-256: `599aa951d91401951922214096fde4aac57389d1392694b5e25496bfc980dd4a`
- Audited source-set SHA-256: `d71235f61ceccf0a70e7cf2a7c4ccc945f3844ed5b5b65dd028d24e1c56f18a2`
- Source-set method: sorted newline-delimited `path<TAB>source_sha256` rows, including the final newline.
- Focused commands: each of the seven Python executables independently, followed by seven explicitly selected failure-path cases.
- Snapshot: `e1536a7a2f4b9b54fc88d357d01c4d8ea5fe46e6` at 2026-09-15T17:41:20Z.

No source, manifest, native-eval, generated artifact, Docker daemon, remote Git endpoint, provider, commit, or push mutation was performed.
