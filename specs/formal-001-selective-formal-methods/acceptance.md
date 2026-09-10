# FORMAL-001 acceptance record

Status: incomplete. Automated results do not establish manual onboarding success.

| Acceptance | Evidence required | Status |
|---|---|---|
| A1 / US1 | Beginner passing and intentional failing check; justified no-model case; expert shortcut | Automated example pass and intentional violation verified; manual UAT not performed |
| A2 / US2 | Real passing/failing, invalid/type error, unsupported, deadlock, temporal, incomplete induction, timeout, version/config mismatch | Pending |
| A3 / US3 | New/reused models, missing config, parent root, clean checkout, interruptions, every resume form, waiver, planning/review invalidation | Pending |
| A4 / US4 | Valid trace, real seeded defect, illegal transition with valid states, stale/missing/malformed/mismatched trace | Pending |
| A5 / US5 | Manager capability matrix, fallback, partial mutation/recovery, preserved metadata and no duplicates | Pending |
| A6 / all | Disabled compatibility, durable archival, every advertised install profile, targeted/full suites, artifact/ripwire gates, installed parity | Pending |

## Delivery

| Order | Branch | PR | Verification |
|---|---|---|---|
| 1 | `codex/formal-methods/coaching` | Pending | 5,132/5,132 committed-checkout suite; docs validation including four browser checks |
| 2 | `codex/formal-methods/apalache` | Pending | Native Apalache 30/30; deterministic formal 18/18; installer 192/192; read-only helpers 107/107 |
| 3 | `codex/formal-methods/tlc` | Pending | Pending |
| 4 | `codex/formal-methods/lifecycle` | Pending | Pending |
| 5 | `codex/formal-methods/traces` | Pending | Pending |
| 6 | `codex/formal-methods/qualification` | Pending | Pending |

## Qualification boundaries

Apalache 0.62.2's official JAR profile has executed on macOS arm64 with Java
26.0.1. Other runtimes and containers remain unqualified. TLC 1.7.4 remains a target.
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
