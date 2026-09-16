# Layer 4 quality and formal unit audit

Status: **audit complete; opt-in native execution not run in this audit**

The companion `unit-quality-formal-audit.json` records all **96/96** frozen,
loaded Layer 4 families from the eleven assigned files. Every member has a
substantive disposition, assertion/callee summary, evidence boundary, and
empty-vector or tautology review. It separately records all **19** inventory
support-only conditional methods with body-specific **keep** dispositions and
a distinct not-run execution fact. All current source hashes match the frozen
inventory.

## What passed

- The eleven focused scripts passed. Their reported counted units were 64, 33,
  50, 9, 20, 32, 41, 35, 13, 35, and 9 respectively.
- Two bounded negative controls also rejected: an empty eligible consensus
  fixture root, and an empty estimate-spec-size golden-fixture root.
- The consensus, estimator, table validator, CRAP join, scorer, quality gates,
  formal-selection parser, formal policy/trace code, and stack-manager planner
  therefore retain their local contracts.

## Evidence boundaries that matter

- CRAP and executor-mode tests execute their own local scripts against frozen
  tool-output/result documents. They do not run Radon, coverage.py, ESLint,
  Istanbul, or an executor benchmark.
- Formal-checker and formal-trace loaded families exercise lifecycle, schema,
  confinement, timeout, receipt, and checkpoint logic. Calls that would need a
  checker verdict are mocked. They are not Apalache, TLC, or Quint evidence.
- Formal setup tests keep cache/pin/confinement policy coverage, with download
  and external process boundaries mocked. They are not installation evidence.
- Stack-manager tests use controlled `git`/`gh` probe responses. They are not
  GitHub or gh-stack integration evidence.

## Conditional native methods

The frozen inventory intentionally excludes nineteen support-only methods from
the loaded family total. Their bodies and loaders were reviewed individually:

- Apalache/TLC/Quint methods have concrete pass, violation, malformed-model,
  timeout, fairness, and installation-drift assertions when explicit JAR/root
  prerequisites are supplied.
- The installed-consumer method is gated by `--native-setup`, whose help text
  explicitly authorizes isolated pinned installation and real checks.
- Native trace methods are labeled opt-in and require declared checker plus
  TypeScript/Swift prerequisites.

The default focused commands supplied no JAR/root/toolchain arguments, so the
conditional methods were not loaded. That is an execution-scope fact, not a
skip pass and not evidence that any method needs replacement.

## Scope boundary

The formal plan calls external tools optional and says actual qualification
belongs to the selected local or pinned hosted profile
(`specs/formal-001-selective-formal-methods/plan.md:18-20`). This audit did not
run such a profile. It therefore makes no new authorization claim and no
PR-level blocker finding. The CRAP, quality-tool, and stack-manager families
remain accurate only at their stated local fixture or mocked-boundary scope.
