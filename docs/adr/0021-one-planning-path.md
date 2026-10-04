# Every SPEC takes one planning path, with each phase trimmed

Status: accepted

Decision ticket: [Planning path: a shorter path for small SPECs, and what picks it](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1155), part of [Wayfinder: speckit-pro planning performance](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1144).

speckit-pro does not adopt upstream Spec Kit's shorter path. Every SPEC's plan stage runs all six planning phases (specify, clarify, plan, checklist, tasks, analyze). Each phase is trimmed instead: clarify runs one session of at most 5 questions (upstream's own cap), and the checklist and analyze shapes are set by [Checklist and analyze: auto-remediation or upstream ownership](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1157). There is no size class and no path switch.

Upstream treats clarify, checklist and analyze as optional and documents a shorter path for smaller features. But in the measured canary runs, each of them found at least one decision-changing item, even on a 120-line SPEC: clarify one per run, checklist three (including a test method that would have passed wrongly), and analyze one ([phase-value research](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1145)). A shorter path for small SPECs would have dropped four of those six catches. The waste was volume, not the phases: three clarify sessions and 14 questions where specify had left no markers, and consensus rounds that changed nothing.

## Considered Options

- **A size class picks the shorter path.** Rejected: it drops the phases that caught real problems on exactly the small SPECs where it would apply.
- **Clarify runs only when specify leaves markers.** Rejected: clarify would have been skipped in both runs, losing one decision-changing answer each time.
- **A decision model picks the path.** Rejected by ADR 0020; it also judged every test spec "full", including a docs-only one.

## Consequences

- The workflow template's three clarify sessions become one, and the stage table and the "only runs if markers" line in the phase reference must agree.
- The 30-minute target rests on trimming each phase and on the consensus, artifact, model and dispatch decisions, not on skipping phases.
