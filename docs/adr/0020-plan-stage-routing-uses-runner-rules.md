# Plan-stage routing uses runner rules; the decision model waits for HRNS-024 and HRNS-027

Status: accepted

Decision ticket: [Decision model: may typesafe-jev choose which Spec Kit commands run](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1154), part of [Wayfinder: speckit-pro planning performance](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1144).

During the health program, the plan stage routes with runner rules and the executors' recommended answers. Every SPEC runs all six planning phases (ADR 0021). It doesn't ask a decision model. The typesafe-jev evaluation goes to the harness-uplift work as input: the shared typed-decision contract (HRNS-024) and the dual-host Jev adapter (HRNS-027), which are off by default, need per-project consent, and run in shadow mode first.

[The evaluation](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1148) found the decision model cheap (about 1/150 of an orchestrator turn per 20-question batch), fast (0.2 s) and stable. It fit the per-item consensus tier well, checklist domains partly, run-or-skip clarify weakly, and the planning path not at all. But useful judgments need the spec text sent to an external provider. ADR 0011 treats repository-data egress as a security action that needs consent, and a default-off, consented adapter is already planned. The performance target doesn't depend on it: the per-item consensus tier, the best fit, can key on the runner's own security classifier and constitution flags.

## Considered Options

- **Shadow mode inside the health program.** Rejected: it pulls part of HRNS-027 into the freeze, for accuracy data that HRNS-027 already plans to gather.
- **Opt-in and acting, with consent from scaffold.** Rejected: it builds an egress path during the freeze for a saving the runner rules already deliver.
- **On by default.** Rejected: it conflicts with ADR 0011's egress consent and with HRNS-027's default-off rule.

## Consequences

- The routing rules (consensus tier, planning path, checklist domains) are runner code with fixture tests, identical on both hosts.
- HRNS-024 and HRNS-027 inherit the evaluation's question wording, state shapes, audit fields (question-set hash, state digest, model, backend, probabilities, thresholds) and the finding that derived features alone fail.
- The research broker's existing Jev screening is unaffected.
