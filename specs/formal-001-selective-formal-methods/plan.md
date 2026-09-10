# FORMAL-001 implementation plan

Use Python 3.11+ standard library and the existing runner request/response and
helper registries. Keep selection, checker execution, freshness, and traces in
small modules under `speckit_pro_runner/formal/`. Reuse existing workflow binding,
stage resolution, PR packets, and agent distribution tooling.

The workflow's `## Formal Methods` JSON block is authoritative selection. The
catalog describes reusable models and does not enroll features. Compact run
records are distinct from authoring inputs. All paths resolve from the verified
workflow root, including parent-checkout invocation and resume.

Authoring is a conditional checkpoint after the normal Plan command, preserving
the seven phases and the phase executor's single-command contract. The parent
dispatches a bounded author agent with approved inputs and allowed output paths.
The formal checkpoint blocks stage entry independently of generic quality slots.

Checker adapters own exact supported command lines and conservative result
classification. External tools are optional. Local execution and pinned hosted
CI profiles require actual qualification; unsupported profiles remain unverified.

Trace validation binds producing tests, adapter and implementation inputs to the
current model. A valid state sequence also needs legal action transitions; replay
of a model counterexample alone does not establish implementation conformance.

## Implementation languages

Python, TypeScript, and Swift share a model-level action/state trace contract.
Their emitters observe real implementation transitions; the projection states
which implementation fields/actions correspond to the model. Keep compilation,
unit tests, model checking, and observed trace conformance as distinct evidence.

- Python: use standard-library JSON with `allow_nan=False`, ordered event arrays,
  and strict decoding; Python's default JSON behavior accepts nonfinite values,
  so defaults alone are insufficient. Preserve the existing project's unittest
  or pytest command and collect its trace after the producing tests.
- TypeScript: emit explicit JSON-compatible values and check safe integers at
  runtime. Keep the project's TypeScript compiler/typecheck and test commands.
  Node's built-in type stripping executes erasable syntax without type checking
  and ignores tsconfig; it is suitable for the standalone tutorial profile only.
- Swift: use Codable/Foundation JSONEncoder and preserve the test target's
  existing XCTest or Swift Testing integration. Capture state and event sequence
  together at the logical transition, without an intervening actor suspension;
  `await` permits reentrancy and cannot be treated as an atomic model step.

The interoperable model trace follows Apalache/Quint ITF: integers use decimal
strings in `#bigint` wrappers, preserving values across language runtimes.
Implementation projections use explicit booleans, strings, integers, and ordered
arrays/records. Floating-point domains,
optional/null values, sets, dates and identifiers need an explicit tested
projection; never silently round, coerce, reorder or drop them. Concurrent traces
need a justified action ordering and observation boundary, not wall-clock sorting.

- [ ] T5: ship and execute equivalent Python, TypeScript, and Swift examples,
  including a seeded illegal transition whose individual states remain valid.
- [ ] T6: verify test/compile hooks, source fingerprinting and hosted CI profiles
  across all three; do not advertise an unexecuted runtime or Apple platform.

Research uses current Context7 plus official documentation:
[Python JSON](https://docs.python.org/3.11/library/json.html),
[Node TypeScript](https://nodejs.org/docs/latest-v24.x/api/typescript.html),
[TypeScript erasable syntax](https://www.typescriptlang.org/tsconfig/erasableSyntaxOnly.html),
[ECMAScript safe integers](https://tc39.es/ecma262/multipage/numbers-and-dates.html#sec-number.issafeinteger),
[Swift concurrency](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/),
and [Foundation JSONEncoder](https://developer.apple.com/documentation/foundation/jsonencoder).
The cross-language trace format is our tested integration contract; those sources
do not themselves certify conformance to a TLA+ model.

## Quint modeling and trace integration

The operator added Quint to the research and qualification scope. Quint is an
optional modeling language/front end, with Apalache as a verification backend.
It does not remove the need to map Python, TypeScript, or Swift actions and state
to a model. Its model-based testing guidance supplies model traces to a test
driver; our conformance gate must also validate the implementation's observed
actions and states, including illegal transitions with individually valid states.

- [ ] T5: qualify a pinned Quint version against the selected Apalache version;
  inspect compilation/server behavior and prevent implicit backend downloads.
  Current research identifies Quint 0.32.0 as a candidate, not a compatibility
  claim. Prefer an explicit model-authoring path with reproducible artifacts.
- [ ] T5: use the official ITF value encoding and action metadata where applicable,
  documenting and testing the supported subset. Cover Python, TypeScript and
  Swift with explicit drivers/projections; do not infer a supported Swift library.
- [ ] T6: preserve disabled behavior, compiler/model/import fingerprints, failure
  classification, and profile-specific installation/upgrade recovery. Simulation
  and generated tests cannot be reported as exhaustive model-checking evidence.

Sources: [Quint overview](https://quint.sh/),
[model-based testing](https://github.com/quint-co/quint/blob/main/docs/content/docs/model-based-testing.mdx),
[CLI verification](https://github.com/quint-co/quint/blob/main/docs/content/docs/quint.md),
[Quint 0.32.0 release](https://github.com/quint-co/quint/releases/tag/v0.32.0),
and [ITF ADR-015](https://apalache-mc.org/docs/adr/015adr-trace.html).
The docs currently differ on TLC integration, so qualify the pinned release's
actual CLI behavior before offering that route. Both source and generated model
artifacts must participate in freshness checks if Quint compilation is selected.

PR management selects a manager before stack mutation. The packet path owns PR
titles and bodies. Optional gh-stack links verified existing PR URLs in declared
order and owns recovery once it has mutated the stack.

## Delivery ownership

See [tasks](tasks.md) for the six branch layers. Each layer includes its relevant
tests, documentation and regenerated payloads. Generated artifacts are rebuilt
from source. The final layer records full-suite, checker qualification, installed
parity and manual-UAT status against the exact pushed revision.

## Required full-harness review

- [ ] Review the official `quint-co/quint/skills` and `quint-co/quint-llm-kit`
  lightweight skills for pinned, attributed reuse inside the explicitly selected
  workflow. Preserve SpecKit's phase order, approved requirement authority,
  bounded agent permissions, and both Claude/Codex distributions. Audit upstream
  instructions before adoption; Docker/MCP setup must remain optional.

- [ ] Before final qualification and PR delivery, review the complete SpecKit Pro
  harness against `tests/speckit-pro/suite-manifest.json`: structural and unit
  tests, trigger and functional evals, integration runners, installed Claude and
  Codex payloads, scaffold/autopilot lifecycle, disabled-feature compatibility,
  and hosted/optional-runner CI contracts. Identify missing coverage, unreachable
  or misleading checks, and regressions across the full plugin. Remediate findings,
  run the relevant tests/evals plus the full required gates, and record actual
  evidence and any unavailable/manual checks separately in acceptance.md.
