# Formal methods: complete harness review

Reviewed 2026-09-10 against the suite manifest and the final feature's source,
generated Claude/Codex payloads, phase references, helper registry, and installed
execution contracts. This review covers the full plugin harness; it does not
equate deterministic assertions with live agent grades or manual onboarding UAT.

## Harness inventory and execution boundaries

| Surface | Registered coverage | Verification |
|---|---|---|
| Toolchain | Python/host preflight before the default suite | Included in committed-checkout runs |
| Layer 1 | Eight structural scripts: metadata, hooks, agents, skills, payloads, CI/release and spec lifecycle | Included in the full default suite |
| Layer 4 | 62 unit scripts, including runner gates, installation, phase coverage/bookkeeping, stage selection, emission/stack management, eval isolation, models, traces and setup | Included in the full default suite |
| Layer 5 | Agent tool and delegation boundaries | Included in the full default suite; formal author is a bounded leaf |
| Layer 7 | Four integration fixtures | Explicit integration run: 4/4 passed |
| Layer 8 | Four capability/parity fixtures | Direct dry run: 12/12 passed; live paired agent runs remain opt-in |
| Layer 2 | Claude/Codex trigger datasets and runners | Coverage/selection contracts pass; six new trigger cases cover formal coaching and execution routing |
| Layer 3 | Claude/Codex functional datasets and isolated headless runner | Eight new cases cover selectivity, beginner explanation, Quint/trace limits and stale-evidence resume; live evidence is recorded separately |

`run-all.py` intentionally prints commands for Layers 2/3, and Layer 8 has no
run-all execution block. Therefore `--all` is not evidence of live evaluation,
and `--layer 8` is not its supported invocation. Use the layer's direct runner.
The complete default suite and headless canaries run from committed clean
checkouts; final counts and live outcomes are recorded in `acceptance.md`.

## Integration coverage

| Contract | Tests and evidence |
|---|---|
| Ordinary workflows stay disabled | Selection tests, legacy runner fixtures, full default suite and actual source/installed CI-wrapper runs without a formal section |
| Scaffold to author to G3 | Both scaffold and autopilot references carry selection; bounded author exists in both payloads; agent contracts, installer materialization, pending/existing model and G3 tests |
| Reconciliation, resume and closeout | Current spec/plan/model/config/import/checker fingerprints, all resume forms, explicit waivers, state mirror and phase-coverage tests; native Plan/final/Post checks from installed payloads |
| Apalache/TLC interpretation | Actual positive/negative, syntax/type, unsupported, deadlock, timeout, temporal, finite-state and complete-induction cases; configuration override/dropped-property regressions |
| Quint | Pinned compiler plus full dependency identity; actual compile/check and observed-trace cases; syntax/version drift and unsupported profile rejection |
| Implementation traces | Real Python, TypeScript and Swift producers and seeded defects; full sequence/action reachability, hidden-state consistency, strict ITF values, numeric boundaries, malformed/missing/stale/mismatched evidence |
| Installation and upgrades | Preview has no writes, checksum rejection, bounded regular-member extraction, path confinement, unchanged existing releases, interrupted Quint receipts and actual repeat installation |
| PR management | Capability/topology/ownership matrix, explicit fallback and partial-mutation recovery; packet-owned metadata remains authoritative; live linking is qualified during delivery |
| Distribution | Generated-artifact contract, actual checkpoint execution from isolated source/Claude/Codex installations, and actual Codex formal-author materialization |
| CI and resource scope | Hosted path-scoped native job, pinned actions/tools, read-only repository token, application-test-before-trace ordering, ordinary CI and optional organization-runner admission unchanged |

## Findings and remediation

1. The existing eval datasets had no formal-specific coaching boundary cases.
   Added the four scenarios to both hosts, with separate rubrics and a bounded
   headless roster. Updated the roster's closed-set test without weakening its
   isolation or no-rubric-leakage assertions. Trigger datasets explicitly keep
   workflow execution out of the coach route.
2. Actual setup execution exposed npm's rejection of one config file serving as
   both global and user config. Setup now uses separate empty files inside its
   temporary staging directory. The native repeat-install and installed-consumer
   scenario passes after the fix; no user configuration is edited.
3. Tool setup needed explicit checks for escaped destination/receipt paths and
   interrupted installations. The implementation reuses path confinement, keeps
   mismatched existing bytes intact, and validates the pinned lockfile and receipt
   on reuse. Negative fixtures exercise those boundaries without network access.
   A relative-path regression also reproduced a false containment failure for
   npm's internal links. Normalizing the installation root before comparing
   resolved targets fixes it, following Python's documented `Path.resolve` and
   string-based `is_relative_to` semantics; the red/green regression is retained.
4. A passing model and isolated valid states are insufficient implementation
   evidence. Native qualification exercises an illegal `0 → 2` implementation
   transition whose states satisfy the bound, plus a hidden-state example that
   only a complete sequence check can reject. Both checker adapters reject these
   defects; weakening an invariant or replaying a counterexample is not accepted.
5. Static call maps do not resolve dynamically loaded test cases and checker
   adapters completely. Their actual dispatch is exercised by native tests and
   installed-runner checks. Ripwire's remaining metadata growth and dynamic-call
   findings are disclosed in acceptance evidence; no baseline/acknowledgment file
   was added to suppress them.

## Evidence limits

Manual beginner onboarding remains a human UAT task. A live explanatory canary
can show that an agent follows the coaching contract, but it cannot establish
that a beginner completed the workflow. Broad live parity of all existing
autopilot strategies is also separate from the installed Claude/Codex execution
checks. Unexecuted platforms and custom consumer container images are not
advertised as qualified. The acceptance record distinguishes each category.
