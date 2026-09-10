# FORMAL-001 acceptance record

Status: implementation, six draft PRs, stack linking, and local/hosted native
qualification complete. [Manual onboarding](onboarding-uat.md) is not performed.
Live coaching canaries require operator approval and have not run.

| Acceptance | Evidence required | Status |
|---|---|---|
| A1 / US1 | Beginner passing and intentional failing check; justified no-model case; expert shortcut | Automated example pass and intentional violation verified; manual UAT not performed |
| A2 / US2 | Real passing/failing, invalid/type error, unsupported, deadlock, temporal, incomplete induction, timeout, version/config mismatch | Native combined checkers/compiler 42/42 passed; detailed cases recorded below |
| A3 / US3 | New/reused models, missing config, parent root, clean checkout, interruptions, every resume form, waiver, planning/review invalidation | Deterministic lifecycle and installed-consumer checks passed; all existing resume/coverage/bookkeeping suites pass |
| A4 / US4 | Valid trace, real seeded defect, illegal transition with valid states, stale/missing/malformed/mismatched trace | Native Apalache/Quint 31/31 and TLC 27/27 trace checks passed in hosted macOS CI, including all three implementation languages |
| A5 / US5 | Manager capability matrix, fallback, partial mutation/recovery, preserved metadata and no duplicates | Nine deterministic cases passed; live CLI/skill/repository qualification, six existing-PR links, exact metadata preservation, and read-only resume boundary verified |
| A6 / all | Disabled compatibility, durable archival, every advertised install profile, targeted/full suites, artifact/ripwire gates, installed parity | 5,276/5,276 committed-checkout assertions; Ubuntu and macOS each passed native checkers 42/42 and setup/installed-consumer checks 13/13 |
| A7 / full harness | Complete suite-manifest review, test/eval coverage, full-plugin scaffold/autopilot and installed Claude/Codex integration, gap remediation and regression evidence | [Review and remediation complete](harness-review.md); full default suite, integration 4/4, parity contracts 12/12 and headless contracts 232/232 pass; live canaries pending approval |
| A8 / languages | Python, TypeScript, and Swift: real valid/defective implementations, ordered strict traces, numeric boundaries, source freshness, test/compile integration and documented runtime profiles | Executed all three producers, type/compile checks and seeded defects locally and on hosted macOS; qualification is limited to the recorded profiles |
| A9 / Quint | Pinned optional Quint/Apalache compatibility, ITF interoperability, useful model-based tests and separately checked observed implementation traces; no implicit downloads | Quint 0.32.0 / Apalache 0.62.2 native model and observed trace checks pass; no managed backend command is used |

## Delivery

| Order | Branch | PR | Verification |
|---|---|---|---|
| 1 | `codex/formal-methods/coaching` | [#558](https://github.com/racecraft-lab/racecraft-plugins-public/pull/558) | 5,132/5,132 committed-checkout suite; docs validation including four browser checks |
| 2 | `codex/formal-methods/apalache` | [#559](https://github.com/racecraft-lab/racecraft-plugins-public/pull/559) | 5,214/5,214 committed-checkout suite; native Apalache 30/30; installer 192/192; read-only helpers 107/107 |
| 3 | `codex/formal-methods/tlc` | [#560](https://github.com/racecraft-lab/racecraft-plugins-public/pull/560) | 34/34 deterministic and native Apalache/TLC checks; final combined qualification in layer 6 |
| 4 | `codex/formal-methods/lifecycle` | [#561](https://github.com/racecraft-lab/racecraft-plugins-public/pull/561) | 5,240/5,240 committed-checkout suite; 39/39 combined native/formal checks; manager 9/9; phase coverage 39/39; bookkeeping 289/289; stage resolution 257/257; mutation helpers 192/192; routing eval contracts 21/21 |
| 5 | `codex/formal-methods/traces` | [#562](https://github.com/racecraft-lab/racecraft-plugins-public/pull/562) | 5,262/5,262 committed-checkout suite; native model, trace and language checks recorded below |
| 6 | `codex/formal-methods/qualification` | [#563](https://github.com/racecraft-lab/racecraft-plugins-public/pull/563) | 5,276/5,276 committed-checkout suite; hosted native checkers 42/42 and installed setup 13/13 on both platforms; hosted trace checks 31/31 and 27/27; docs/browser validation passed |

All six PRs remain drafts and are linked in this order in GitHub stack 564.
Each exact title, body, release note, base branch and head identity was validated
through the existing PR packet path before creation and verified after linking.
Packets record explicit size exceptions for the approved six functional
boundaries; their numerical review budgets are not claimed as passing.

Hosted native evidence is [run 34441556263](https://github.com/racecraft-lab/racecraft-plugins-public/actions/runs/34441556263),
for PR head `c8c05d73a85dcd15ee83f8b02052c66d84ee4c28` (checkout merge
`cdb68c0e00ddf364e6d3120574837e2831e48df6`). The separate default PR Checks
workflow skips substantive jobs on drafts; its successful wrapper is not a
hosted full-suite result. The full-suite count above is from the committed local
checkout at `621dddbdd`; subsequent changes record delivery evidence.

## Qualification boundaries

Apalache 0.62.2's official JAR profile has executed on macOS arm64 with Java
26.0.1. TLC 1.7.4's official JAR has also executed on that runtime. The pinned
official Apalache Linux amd64 image passed both positive and negative checks
under Docker emulation on macOS arm64, using Temurin 25.0.4+7. Hosted Ubuntu x64
passed with Temurin 25.0.4+1 and Python 3.11.16; hosted macOS arm64 passed with
Temurin 25.0.4+101.0.LTS and Python 3.11.9. Both used Node.js 24.11.1. The macOS
trace jobs also used the locked TypeScript 6.0.3/Node types 24.13.2 toolchain and
that runner image's Swift compiler. Its precise Swift version is not separately
logged, so only the linked runner profile is qualified. Other runtimes and
custom containers are unqualified.
Installation requires operator authorization. Hosted CI remains the default.
Organization runner admission and VM sizing are not inferred from this repository.

## Coaching-layer evidence

- Baseline deterministic suite: 5,108/5,108 passed on main before changes.
- Selection validator: 23/23 assertions passed, including legacy absence,
  malformed/duplicate records, explicit origin and evidence levels, and fenced
  phase prompts that must not become authoritative selection.
- Counter example: Apalache 0.62.2 build `f0dec98`, Java 26.0.1 on macOS arm64;
  `check --config=Counter.cfg --length=5 Counter.tla` completed with `NoError`,
  exit 0. In a separate copy, changing `count <= Limit` to `count < Limit`
  produced a state-2 invariant violation and exit 12. This checks the tutorial
  on this runtime only; it does not qualify other installation profiles.
- Download `apalache-0.62.2.tgz` SHA256 verified against the official release:
  `765f610537281a0f25b8c30f2554f19523e2859c824e80e62276653ee23c10e2`.

## Apalache-layer evidence

- Native qualification: `python3 tests/speckit-pro/unit/test-formal-checkers.py
  --apalache-jar /path/to/apalache-0.62.2/lib/apalache.jar`: 30/30 assertions.
  Includes passing/violating invariants, syntax/type errors, unsupported ENABLED
  and fairness, deadlock, temporal checks, complete induction and a failing
  consequence after passing base/step, actual checker timeout, and checksum drift.
- The qualified JAR SHA256 is
  `079b6c2320252469dcf79afec6886b8255d3dd1b34a9484433c88986752efaa8`.
- Native testing found that SPECIFICATION could defeat an induction initializer.
  The integration requires matching explicit INIT/NEXT, rejects unsupported
  configuration, and verifies the checker's reported predicates. See the pinned
  [Apalache configuration implementation](https://github.com/apalache-mc/apalache/blob/v0.62.2/passes/src/main/scala/at/forsyte/apalache/tla/passes/pp/ConfigurationPassImpl.scala).
- Deterministic lifecycle cases cover pending new versus missing existing models,
  content-bound evidence, G3, every resume entry, and preserving earlier Specify
  and Clarify phases. Waivers, final trace validation, and full coverage/state
  integration belong to later layers and are not claimed here.
- Ripwire found no remaining preexisting function complexity regression after
  isolating formal resume policy. Registry/fixture growth and agent-roster churn
  are expected metadata changes; dynamically invoked checker capture/tests are
  covered by executable tests. These findings were reviewed, not suppressed.

## TLC-layer evidence

- Native qualification ran both pinned checkers with the deterministic contract
  cases: 34/34 assertions passed. TLC cases include complete finite exploration,
  an invariant violation, deadlock, syntax error, an unsupported infinite domain,
  temporal progress with weak fairness, and a liveness counterexample without it.
- The official TLC 1.7.4 JAR SHA256 is
  `936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88`;
  its SHA1 matches the release asset and its manifest identifies `v1.7.4`.
- The adapter requires the native property's full catalog mapping, preserves
  SPECIFICATION/fairness, and rejects temporal symmetry in this profile. Each run
  gets its own metadata and Java temporary directories. Native TLC qualification
  required the sandbox to permit its local runtime socket.
- A 34/34 combined run is automated evidence, not manual onboarding acceptance
  or qualification of other Java, OS, or container profiles.

## Lifecycle-layer evidence

- Current planning evidence, separate operator waivers, superseded/interrupted
  records, all resume forms, final/Post implementation scope, and durable-state
  coverage passed deterministic tests. Native checkers also passed the combined
  39/39 run; execution remained on the previously qualified macOS Java profile.
- Manager selection passed nine deterministic cases covering both capabilities,
  missing CLI/skill, unsupported version/repository, incompatible topology,
  explicit fallback, existing PR identity/metadata boundaries, and partial
  mutation recovery. The live delivery qualified gh-stack 0.1.1, the available
  skill, repository access and ordered branch/PR topology before mutation.
  Linking existing URLs created stack 564; the Stacks API confirmed exactly
  PRs 558–563 in order, and all packet-owned bodies, titles, bases, heads and
  draft states were unchanged. The read-only resume helper refused a manager
  switch after the recorded attempted boundary; the actual remote state was
  reconciled and persisted without creating duplicate PRs or a second stack.
- The shared phase, gate and Post references now enforce the selected checks.
  The complete existing mutation helper, stage resolution, coverage, bookkeeping
  and eval-routing contract tests passed. Full committed-checkout and installed
  integration qualification are still required for delivery.
- Ripwire's quality review identified layering churn and input-validation
  complexity. PR identity validation was separated from local ancestry checks,
  and checkpoint writing retains its original four-argument interface. Test-gate
  references are covered by the manifest suites/native checks; dynamic dispatch
  and preexisting unrelated scripts remain limitations of its static reach map.

## Trace and Quint layer evidence

- Native trace qualification passed 31/31 Apalache/Quint and 26/26 TLC checks.
  All three real implementations passed; changing their increments from one to
  two failed conformance despite every observed count remaining within bounds.
  The full-sequence query also rejected a sequence whose hidden states could
  only appear consistent if adjacent transitions were checked independently.
- Python 3.11.0, Node.js 24.11.1 with TypeScript 6.0.3 and Node types 24.13.2,
  and Swift 6.3.3 executed on macOS arm64. Swift compiles with strict concurrency
  and warnings as errors; the trace producer executes through the Swift source
  runtime. These results do not qualify every application, library, or platform.
- All three preserved `9007199254740993` exactly through decimal ITF integers;
  Apalache checked those large-integer traces. Both native engines exercised ITF
  scalar, tuple/list, set, map, and record values. Floating point, malformed or
  mismatched shapes, duplicate JSON keys, stale bindings and partial receipts
  are rejected. Unsupported ITF values never become a pass.
- Native testing identified duplicate assignment hints when combining Next and
  the observed action, including UNCHANGED. The trace query uses Apalache's typed
  JSON IR and documented equivalent equalities while preserving every constraint.
  Typed intermediate output is essential: an untyped parse loses type annotations.
  Actual model checking follows the conversion; typechecking alone is not evidence.
- Quint 0.32.0 compiles JSON using its pinned installed tree and Node permission
  mode; Apalache 0.62.2 owns execution. Model pass/violation, syntax failure,
  temporal checking, installation drift and observed implementation defects were
  exercised. Ordinary checks cannot invoke Quint's managed backend download path.
- Upstream Quint skills at `6fb2924e00707cef6dbc5e30db606d555c447123` and LLM Kit
  skills at `cc75369f741af7d490936f82002c2d28e3b3d78d` were audited without
  installation. Both skill scans reported zero findings. Pinned language/modeling
  guidance is reused on demand; SpecKit retains selection, requirement authority,
  bounded authoring, phase order and closeout decisions.
- Agent contracts passed 345/345, mutation helpers 192/192, and the repository
  Bash-confinement gate passed. Ripwire review separated receipt checking,
  language validation and checker execution by responsibility. Its remaining
  churn/parameter findings and dynamic test reach limitations are recorded;
  no baseline or acknowledgement files suppress them.
