# Codex parity is a release gate

Status: accepted

No speckit-pro release ships without a green canary receipt on both Claude Code and Codex for that exact commit. Codex is not best effort. Best effort is how Codex broke unseen: agents went stale after a release, and approval and consent waits cost over 24 hours of idle time, because nothing blocked a release on Codex.

Parity means the same outcomes and the same run experience on both hosts. From the first autopilot step on, the prompts, the progress block and the stop points must match. Only one-time host setup may differ (Codex hook trust and approval policy, Claude Code allow rules the plugin can only print). Scaffold runs that setup and records it in the readiness record.

The gate tests each host's latest stable release at release time. The canary receipt records both host versions, and the plugin docs state them as the tested floor. A later host release that breaks the plugin is caught by the next canary run.

The gate covers every speckit-pro release, with no hotfix bypass. It starts with the first release after the canary exists. Health-fix releases before that ship as today.

## Considered Options

- **Best effort for Codex.** Rejected: it contradicts the promise that everything holds on both hosts, and it is how Codex rotted.
- **Gate from phase 5 close.** Rejected: phases 1 to 4 could ship Codex regressions.
- **Freeze releases until both hosts are green.** Rejected: health fixes would pile up unreleased for the whole program.
- **Same outcomes only, UX free to differ.** Rejected in favor of matching the run experience too.
- **Documented per-host exceptions anywhere in the flow.** Rejected: the list can grow back into best effort. Only setup is exempt.
- **Pinned host versions, or latest plus previous.** Rejected: pinned versions drift from what users run; two versions per host doubles canary cost per release.
- **Hotfix bypass, or skip the gate for docs-only releases.** Rejected: a bypass is how a release breaks one host unseen, and skill prose is runtime behavior.

## Consequences

- Once the canary exists, Codex must be repaired before any further speckit-pro release ships.
- How the gate is enforced, and how often the canary reruns against new host releases, belong to the canary decision, not this ADR.
- A red canary on either host blocks releases and, per ADR 0002, brings back the fix-vehicle ban.
