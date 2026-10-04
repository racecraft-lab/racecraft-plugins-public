# Native Spec Kit v1.1.0 coverage: what speckit-pro adopts, rejects or defers

Status: accepted

Decision ticket: [Native-capability coverage ledger](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1176), part of [Wayfinder: speckit-pro planning performance](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1144).

speckit-pro builds on upstream Spec Kit (github/spec-kit, tag v1.1.0, commit f1d3a4f). This ledger records the status of each upstream capability, so nobody re-proposes a rejected one without new evidence. Revisit it whenever the CLI pin moves.

| Capability | Status | Why |
|---|---|---|
| CLI version | Adopt: pinned to v1.1.0 | One owner holds the pin; scaffold offers it, autopilot notes a mismatch ([#1174](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1174)) |
| specify, plan, tasks | Adopt as-is | The phase-executor runs the upstream commands |
| clarify | Adopt the cap | One session, at most 5 questions, with a recommended answer each; the run answers, since planning never waits for a user (ADR 0021) |
| checklist | Adopt, with agent remediation | Upstream leaves checklists to the reviewer; speckit-pro remediates gaps, because ADR 0013 requires every finding fixed before approval ([#1157](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1157)) |
| analyze | Adopt, with agent remediation | Upstream is read-only; speckit-pro fixes findings for the same reason |
| Shorter path | Reject | Each optional phase caught real problems on a small SPEC (ADR 0021) |
| `lean` preset | Reject | It drops `research.md`, which G3 needs, and the hooks; its specify asks the user a question ([#1147](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1147)) |
| Workflow engine (`specify workflow run`) | Reject | Fan-out trips the ledger lock and the engine would be a second ledger; it adds no speed (ADR 0018) |
| Extension hooks | Adopt upstream ownership | Upstream commands run mandatory hooks; the runner brief lists optional ones (ADR 0018) |
| Preset `replace` strategy | Adopt (today) | The reviewability preset ships as three replace forks, now installed by the plugin with `specify preset add` |
| Preset `prepend`, `append`, `wrap` | Defer | `append` reproduces the reviewability preset within 1%, but moves its sections to the end of each template. Adopt after a canary run shows plan quality and G3 hold ([#1173](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1173)) |
| `specify artifact` | Reject | It inventories commands and templates, not feature files, so it cannot back the planning manifest or the phase brief |
| Bundles | Defer | Hooks are not bundle components, non-catalog presets fail to install, and the saving is operator confirmations only |
| Implement with `[P]` delegation | Defer | Implement stage; a follow-on map |
| converge | Defer | Runs after implement; a follow-on map |
