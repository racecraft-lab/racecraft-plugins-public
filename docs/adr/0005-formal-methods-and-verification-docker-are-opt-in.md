# Formal methods and verification docker are opt-in and never stop a run

Status: accepted

Formal methods and verification docker stay off by default and are switched on per SPEC. Scaffold evaluates every SPEC for both: whether the design suits a formal model, and whether verification docker fits the host (it needs a Linux/arm64 Docker daemon). It offers both to the user every time, so users learn the capability exists even when they decline.

When a SPEC opts in, scaffold does the setup with the user present. It installs the tools, records them in the readiness record, and records a time and state bound for each selected model. Autopilot then treats both features as ordinary checks with no stops of their own. A missing tool, a failing check, or a check that overruns its bound climbs the retry ladder (ADR 0004). After the third attempt, the formal tasks are marked blocked-for-UAT and the run continues. The ladder may fix the model, its encoding or the code. It never lowers a recorded bound or drops a property to get a pass. A waiver happens only at UAT, where the human waives or rejects the blocked check; there is no mid-run waiver.

The canary asserts that scaffold evaluated and offered both features, then declines them. Opt-in runs get their own check, which does not gate a release.

## Considered Options

- **Keep their own stops (setup-gap halts, install approval during autopilot, a formal failure that blocks closeout).** Rejected: Apalache ran past 8M states, timed out and needed install approval, and the formal repair cap stopped the run after two attempts. Each broke the promise that planning and implement never stop.
- **Drop both.** Rejected: formal models catch design errors tests miss, and opt-in costs nothing in runs that decline.
- **Offer only when the SPEC looks like a fit.** Rejected: users who never see the offer never learn the feature exists.
- **Skip silently when a tool is missing.** Rejected: a selected check would vanish without evidence.
- **A plugin-wide time limit, or an overrun that passes with a note.** Rejected: models differ too much for one limit, and a bounded search that never finished proves nothing.
- **Let the ladder lower bounds.** Rejected: weakening a model to pass is a decision for the human at UAT.
- **Canary opts in.** Rejected: it would put Apalache installs and an arm64 Docker daemon on every release's critical path.

## Consequences

- Scaffold gains a feasibility pass and an install flow for formal tools and Docker.
- The formal repair cap, setup-gap halts and the mid-run operator waiver are deleted from autopilot.
- Where the per-model bound lives and how the separate opt-in check runs are open for the phase that builds them.
