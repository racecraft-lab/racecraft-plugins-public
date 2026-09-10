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
| 1 | `codex/formal-methods/coaching` | Pending | Pending |
| 2 | `codex/formal-methods/apalache` | Pending | Pending |
| 3 | `codex/formal-methods/tlc` | Pending | Pending |
| 4 | `codex/formal-methods/lifecycle` | Pending | Pending |
| 5 | `codex/formal-methods/traces` | Pending | Pending |
| 6 | `codex/formal-methods/qualification` | Pending | Pending |

## Qualification boundaries

Apalache 0.62.2 and TLC 1.7.4 are targets, not yet advertised compatibility.
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
