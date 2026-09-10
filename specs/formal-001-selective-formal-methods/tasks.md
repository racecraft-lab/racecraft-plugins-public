# FORMAL-001 task ownership

Established before implementation. Each branch is based on the preceding layer;
the first is based on verified main. PR URLs and validation live in acceptance.md.

| Task | PR order / branch suffix | Scope | Requirements |
|---|---|---|---|
| T1 | 1 / `coaching` | Selection contract, selective coaching, guided first checks | FR1, FR2 |
| T2 | 2 / `apalache` | Catalog, doctor/check, Apalache, scaffold-author-check-commit-resume, both author agents | FR3–FR6, FR8, FR9 |
| T3 | 3 / `tlc` | TLC execution, checker selection, real result qualification | FR5 |
| T4 | 4 / `lifecycle` | Complete freshness/reconciliation/closeout, waiver semantics, optional PR manager | FR7–FR9, FR11 |
| T5 | 5 / `traces` | Implementation traces, tested projection and seeded defects in Python, TypeScript, and Swift | FR10, FR13 |
| T5b | 5 / `traces` | Optional Quint compilation/Apalache checking, upstream guidance reuse, full selected workflow and ITF conformance | FR14 |
| T6 | 6 / `qualification` | Consumer CI, installation/upgrade recovery, onboarding, release verification | FR12 |
| T6a | 6 / `qualification` | Review the complete SpecKit Pro harness: suite manifest, tests, evals, full-plugin integration, missing coverage and regressions; remediate and retest findings before delivery | FR12; operator follow-up |

All branch names begin `codex/formal-methods/`. No layer may claim evidence owned
by a later layer. No manager is selected solely from the existence of its schema.

- [x] T1 implemented and verified
- [x] T2 implemented and verified
- [x] T3 implemented and verified
- [x] T4 implemented and verified
- [x] T5 implemented and verified
- [ ] T6 implemented and verified
- [x] T6a complete harness review finished; gaps remediated and regression evidence recorded
- [x] T5a qualify Python, TypeScript, and Swift trace emitters against the same model, including legal-state/illegal-transition defects
- [ ] T6b qualify language tooling and CI profiles; record unexecuted profiles explicitly
- [x] T5b research and qualify Quint's optional Apalache modeling path and ITF trace integration; preserve explicit installation and selection
