# FORMAL-001 task ownership

Established before implementation. Each branch is based on the preceding layer;
the first is based on verified main. PR URLs and validation live in acceptance.md.

| Task | PR order / branch suffix | Scope | Requirements |
|---|---|---|---|
| T1 | 1 / `coaching` | Selection contract, selective coaching, guided first checks | FR1, FR2 |
| T2 | 2 / `apalache` | Catalog, doctor/check, Apalache, scaffold-author-check-commit-resume, both author agents | FR3–FR6, FR8, FR9 |
| T3 | 3 / `tlc` | TLC execution, checker selection, real result qualification | FR5 |
| T4 | 4 / `lifecycle` | Complete freshness/reconciliation/closeout, waiver semantics, optional PR manager | FR7–FR9, FR11 |
| T5 | 5 / `traces` | Implementation traces, tested projection and seeded defect | FR10 |
| T6 | 6 / `qualification` | Consumer CI, installation/upgrade recovery, onboarding, release verification | FR12 |

All branch names begin `codex/formal-methods/`. No layer may claim evidence owned
by a later layer. No manager is selected solely from the existence of its schema.

- [ ] T1 implemented and verified
- [ ] T2 implemented and verified
- [ ] T3 implemented and verified
- [ ] T4 implemented and verified
- [ ] T5 implemented and verified
- [ ] T6 implemented and verified
