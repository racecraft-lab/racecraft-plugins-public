# Layer 4 unit/workflow evaluation audit

Status: **proposal, not qualification**

This audit reviews every loaded family from the nine selected Layer 4 files in
the frozen `deterministic-inventory.json`. The machine-readable companion
`unit-workflow-eval-audit.json` is the complete family-by-family record: exact
inventory ID, source line, disposition, requirement, failure mode, coverage
boundary, evidence, and replacement mapping.

## Snapshot and boundary

- Reviewed: **84/84 loaded families** across **9/9 selected files**.
- Dispositions: **74 keep**, **10 replace**, **0 merge**, **0 remove**.
- Every reviewed file matched its frozen SHA-256 when inspected. The exact nine
  hashes are recorded in the JSON. A later hash change invalidates the affected
  source review until its family bodies are re-audited.
- The review used Ripwire bodies/callees plus the frozen inventory enumeration.
- No live provider or native model behavior was exercised by this audit.
  Passing mocks, parsers, replay fixtures, previews, preflights, and authored
  contract scans are credited only at those boundaries.
- A `replace` disposition is not permission to delete unique coverage. The
  stated replacement must exist, be executable, and retain the mapped
  requirement before the old family can be removed.

| Selected file | Families | Keep | Replace | Primary boundary |
|---|---:|---:|---:|---|
| `test-functional-headless-runner.py` | 58 | 58 | 0 | Runner implementation, local process integration, parsers, and declarations |
| `test-eval-runner-skill-selection.py` | 9 | 8 | 1 | Authored contracts, previews, fixtures, and mock-fed selection plumbing |
| `test-integration-runners.py` | 1 | 1 | 0 | Replay runner and aggregation implementation |
| `test-parity-runner.py` | 2 | 1 | 1 | Negative canaries and fake-client runner wiring |
| `test-parity-extractors.py` | 1 | 1 | 0 | Markdown parser/CLI behavior |
| `test-parity-judge.py` | 1 | 0 | 1 | Deterministic comparison/judge contract |
| `test-transcript-helpers.py` | 1 | 1 | 0 | Replay transcript parser behavior |
| `test-transcript-tools.py` | 1 | 1 | 0 | Local transcript-tool CLI behavior |
| `test-performance-fixtures.py` | 10 | 3 | 7 | Historical declarations and frozen fixture provenance |

## Replacement findings

### Skill-selection family does not execute native selection

`EvalRunnerSkillSelectionTests.test_eval_runner_skill_selection_contract`
runs structural scanners, preview/preflight paths, and an immutable fake Claude.
It does not observe a native Claude or Codex selecting the target skill, and its
Codex skill roster is a second ordinal list rather than native result evidence.

Replacement boundary: split out and retain the useful structural and preview
checks. Satisfy the behavioral claim with canonical semantic-keyed paired cases
that record one executable Claude selection and one executable Codex selection
for every required skill.

### Layer 7 mock runner encodes the retired comparison model

`Layer7RunnerTests.test_layer7_runner_contract` compares two fake Claude modes
(`teams` and `fallback`) and never runs Codex. It also asserts that a missing
executable or semantic-equivalent comparison can finish with zero failures and
one skip. That is runner-wiring evidence, not automated cross-client parity.

Replacement boundary: retain the distinct runner failure cases, but map the
gate to independently graded Claude correctness, independently graded Codex
correctness, and a typed comparison of those two results. Missing clients and
unexecuted semantic judgments are non-pass states. Genuine interactive-team
verification remains a separate manual, non-PR-blocking activity; it is not a
substitute pass for automated Claude/Codex parity.

### Semantic-equivalent judge skip exits successfully

`Layer7JudgeTests.test_judge_contract` explicitly expects `status="skip"`,
`skipped=true`, and CLI exit code zero when differing values are described as
semantically equivalent. This permits an unevaluated semantic claim to be
pass-compatible.

Replacement boundary: retain byte, exact-value, and numeric-tolerance checks.
Require semantic comparison to return a typed executed result; unavailable or
unexecuted semantic judgment must not pass.

### Performance loops do not own roster non-emptiness

Bounded controls modified temporary copies only:

- With `manifest["scenarios"] = []`, five families still passed: source-byte
  provenance, reference-task reset/completeness, pending workflow phases,
  common Tasks input propagation, and dependency-inventory workload binding.
- With `manifest["authored_files"] = []`, the protocol/timing family still
  passed, including its authored-file hash subclaim.

These are not false assertions over the current nonempty fixture. They are
ownership gaps: each named family can go green without exercising the parameter
set named in its requirement. Each replacement therefore adds an exact nonempty
roster assertion before preserving the existing per-item checks.

`test_native_qualification_fails_closed` also mixes durable historical facts
(pending status, zero completed runs, baseline pin, twelve planned native
workflows) with historical authorization/budget fields. The replacement must
preserve the former as snapshot provenance without using the latter as current
authority. The original twelve-workflow performance acceptance and manual UAT
remain separate pending work; this Layer 4 migration does not complete or waive
them.

## Coverage retained deliberately

- All 58 functional-headless families are retained. Their mocks inject process,
  event, environment, or OS boundary conditions into real runner logic; they do
  not by themselves claim provider correctness. The POSIX-only real process and
  signal families remain platform-gated implementation integration tests.
- Layer 6 runner coverage is retained for real replay-script execution,
  nonzero discovery, nested summary validation, aggregate behavior, argv safety,
  scrubbing, and malformed response assertions. Its Claude capture is mocked,
  so native behavior belongs elsewhere.
- Transcript helper/tool and parity extractor families are legitimate parser or
  local CLI coverage with nonempty positive and negative fixtures. They remain
  separate from native evaluation cases.
- The Layer 7 invariant mutation family is retained as deterministic negative
  coverage even while the main mock parity contract is replaced.

## Executability and remaining work

This is a requirements inventory and replacement proposal. It does not claim
that the ten replacements are implemented or qualified. The parent integration
must map each replacement record in the JSON to an executable retained check or
canonical native case before removing or relaxing an existing family. Generated
reference artifacts, manifests, runners, fixtures, and provider corpora were not
changed here.
