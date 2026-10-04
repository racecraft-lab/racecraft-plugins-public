# Plan-stage consensus runs only for security and low-confidence items

Status: accepted

Decision ticket: [Consensus tier: when consensus runs instead of the recommended answer](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1156), part of [Wayfinder: speckit-pro planning performance](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1144).

On the plan stage, the run applies the executor's recommended answer for every item except two kinds:
- **Security items** (an explicit security tag or a security keyword) still get all-three consensus, with its later rounds.
- **Low-confidence items** get one analyst, routed by the executor's category tag, with no synthesizer round. A high-confidence analyst answer replaces the recommendation, with the recommendation recorded as the rejected alternative. Otherwise the recommendation stands.

Every low-confidence item is listed first among the decisions-list entries for plan review. The "sources disagreed" and "unresolved after the fix pass" triggers are removed.

In the measured canary runs, 7 items reached consensus. All 7 ended with the executor's own recommendation, none were security items, and the rounds took 31% of each plan stage. Plan review (ADR 0013) now walks a human through every decisions-list entry before anything is built, which consensus was partly standing in for. Keeping one analyst for low-confidence items keeps a second opinion exactly where the executor doubted itself.

## Considered Options

- **Security only.** Rejected by the owner: low-confidence items would reach plan review with no second opinion.
- **Keep today's triggers.** Rejected: consensus stays the largest wait, and the 30-minute target fails.
- **A decision model picks the tier.** Rejected by ADR 0020.

## Consequences

- The retry ladder's second rung keeps its consensus diagnosis (ADR 0004). This ADR covers plan-stage items only.
- Security handling is unchanged: all-three consensus, and the security interrupt rules of ADR 0011.
- Analyst effort drops from max to high (per [Model and effort per plan-stage agent](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1150)), and the synthesizer runs only on security rounds.
