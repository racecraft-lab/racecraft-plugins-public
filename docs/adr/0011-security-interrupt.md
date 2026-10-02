# Security interrupts require runner receipts and consent to one bounded action

Status: accepted

Implementation status: planning decision; this ticket changes no plugin runtime behavior. Question-tool enforcement and live host parity are not yet implemented or verified.

Planning may pause only to obtain missing consent for one necessary, otherwise permitted security action when no safe authorized alternative satisfies the SPEC. The runner classifies eligibility and issues a question permit; a human response supplies separate action consent. Neither record overrides a forbidden action, host permission boundary, managed denial, harm halt, or plan-approval requirement.

Decision: [Security interrupt: definition, runner receipt, question-tool hook per host](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1022), part of [Wayfinder: speckit-pro health program](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1006).

## Eligibility

All of these conditions must hold before the runner issues a question permit:

- The run is planning, the proposed action is necessary for a declared requirement/work item, and there is no safe authorized alternative that satisfies it.
- The action falls in the closed set below and lacks valid consent for its exact scope.
- Existing policy otherwise permits the action. ADR 0010's authority skips and harm halts remain authoritative; this mechanism cannot authorize an exception to them.
- Current identity, evidence integrity, required guard execution, and a supported interactive question path are verified. A saved readiness status or an agent's assertion supplies no authority.

| Category | Missing consent that can qualify |
| --- | --- |
| Repository-data egress | Sending repository content to a recipient not authorized for that operation and data scope. An allowed endpoint alone does not authorize every payload or effect. |
| Credential or permission change | An otherwise permitted change to credentials or permissions whose exact effect lacks consent. No credential value enters a question, public receipt, or review artifact. |
| Security-control change | An otherwise permitted change to a security control whose exact effect lacks consent. A forbidden disablement or veto bypass remains skipped. |

Ordinary setup, scope, quality, model-choice, and planning questions do not qualify. If a safe authorized alternative exists, choose it, record the choice in the decisions list, and continue. Unknown or incomplete classification evidence produces no permit: never infer authorization or relabel a general question as security. Invalid evidence uses the retry ladder for its failing check; affected work is deferred when it cannot proceed safely. The endpoint entries themselves remain with the map's egress-allowlist work.

## Classification and records

The agent submits a structured proposed action and the exact proposed question input. The runner owns the closed category checks and authorization decision; an agent or model classification is advisory input only. The action record identifies its category, command/tool, recipient/target, intended effect, repository-data selectors and fingerprints where applicable, execution boundary, affected work item, necessity/alternative evidence, and applicable policy/authorization digests. Missing or mismatched required fields cannot pass. Policy does not learn its rules by parsing guidance prose.

Extend the existing scoped autonomy-boundary and authorization contracts rather than creating another authorization owner. The existing egress helper renders text and hashes; it does not capture consent or persist an authorization. Classification, receipt validation, consent capture, and action consumption need executable runner contracts when implemented.

| Record | Binding and meaning |
| --- | --- |
| Question permit | Runner-issued authority to present exactly one security question about the proposed action. Bind the record to the run, host/session, repository/worktree/branch boundary, action-scope digest, policy digest, guard manifest/script hashes, and canonical question-tool name/input digest. It is not action consent. |
| Action consent | Explicit affirmative human evidence authorizing exactly one bounded action in that run. Bind it to the question permit and the same action/policy/boundary scope. It cannot persist into future runs or authorize another action. |
| Guard invocation evidence | Current-run evidence from the host-delivered hook event, bound to the host/session, current guard hashes, event/tool identity, actual event/input digest, and decision. It proves that invocation, not every possible tool path. |

The question hook atomically consumes the matching permit and records the actual tool-use identity available at invocation. Missing, malformed, consumed, cross-run, cross-session, or mismatched permits deny the entire question call. A call containing unrelated or multiple questions cannot borrow the permit. Do not add unsupported receipt fields to a host's question-tool schema; the hook looks up the runner-owned pending permit and compares the actual input.

The action guard requires verified human consent and current matching scope before dispatch. Record dispatch and consumption atomically so concurrent dispatches or retries cannot reuse the grant. Changed recipient, data, command/effect, boundary, or policy invalidates the match. An interrupted or unknown action outcome never releases the grant for automatic redispatch; reconcile its outcome without replaying the action. A question permit, readiness record, plan approval, or elapsed time alone authorizes nothing.

Private run state retains the needed human evidence and scope under existing integrity/provenance checks. Public receipts and decisions use redacted descriptions, repository-relative references, and digests. Proven forgery or tampering follows ADR 0010's harm halt; an ordinary missing or stale record is not automatically evidence of tampering.

## Question-tool guards on both hosts

Use synchronous local command hooks that call the same runner policy. Claude Code's `PreToolUse` guards `AskUserQuestion`; Codex's `PreToolUse` guards `request_user_input` on supported local tool paths. Inventory and cover every exposed equivalent question/wait tool, including alternate question tools and `ExitPlanMode` where applicable, so an agent cannot substitute a different interactive path. Apply the policy to the parent and dispatched agents. Outside an active autopilot run, this guard must not prevent scaffold or ordinary interactive work.

For a disallowed question, return the host's supported explicit `PreToolUse` denial (`permissionDecision: "deny"`, or exit 2 with a redacted reason). Record the rejected question and conservative treatment in the decisions list without asking for a reply. A valid question permit lets the normal question-tool flow proceed; it neither auto-answers the question nor overrides the host's own restrictions. All hook-input parsing and runner failures that the command can catch must return a supported denial rather than a generic error or empty success.

Host hook execution is not a complete security boundary. Codex documents specialized paths that can bypass tool hooks, changed/untrusted hooks that are skipped, and hook responses/errors that can fail without blocking the tool. The runner therefore also refuses guarded dispatch and receipt issuance without the required evidence. A timeout, killed hook, unsupported tool path, or missing hook is not converted into an enforcement success. If the host cannot prevent questions through a required path, that capability is unavailable; the run cannot claim the no-question contract is enforced on it.

## Trust, liveness, and missing guards

Scaffold's per-host readiness record already includes required hook definitions/hashes and enabled/trusted observations (ADR 0008). Explicitly retain observed trust for each required guard: trusted, untrusted/disabled, or unknown, with its exact observed definition hash and evidence source. Human hook review/trust and reload belong to scaffold preparation; never bypass trust or broaden permissions automatically during autopilot. Configuration or an old trust observation does not prove current execution.

At run start and before the first phase transition, the runner checks current-run activation evidence for the required guards, current fingerprints, and supported tool coverage. A startup/session token alone cannot certify question denial or Stop enforcement. Each relevant invocation must produce its own evidence; a question-guard event does not prove a Stop-guard event occurred. Invalidate affected observations after a changed hook, loaded payload, host/session, or relevant configuration. Recheck before protected dispatch and phase transitions, with actual event evidence retained when those events occur.

Missing or failed evidence is a failing check on ADR 0004's retry ladder. Keep actions requiring that guard blocked throughout repair attempts; after the ladder is spent, affected work becomes blocked-for-UAT. Independent safe work whose safety is still enforceable continues. This adds no new harm-halt reason and never returns the run to scaffold for a setup question. A red or incomplete guard check cannot be reported as a passed check, completed protected work, or a fully produced artifact. The canary remains red.

## Human response and unavailable interaction

- An explicit affirmative response supplies consent only after the runner verifies its provenance and matching scope. Execution still needs all normal policy and host checks.
- A refusal defers the affected work, records the refusal, and continues independent safe work. Do not retry the same consent request automatically.
- An unanswered interactive request remains paused. There is no implicit-consent timeout; elapsed time is neither approval nor refusal.
- If the host cannot collect a reply, including headless modes that reject question tools, planning defers the affected work and continues safely. It never fabricates a reply or claims an interrupt was presented.
- Implement never issues a question permit or pauses for this consent. Missing consent makes affected work blocked-for-UAT; independent work continues. Dependency and handoff mechanics remain with [Security item during implement: skip-and-list mechanics](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1024) and [Blocked-for-UAT in the ledger, PR body and UAT runbook](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1023).

## Required parity evidence

Implementation must add deterministic runner contract tests and real host-path integration tests on both hosts. A mock invocation of a hook script does not prove that a host actually calls it. Record the host version, loaded payload and hook hashes, run/boundary bindings, actual tool/event identities, decisions, action dispatch counts, and redacted receipt references.

The shared acceptance matrix covers:

1. A necessary permitted planning action without consent produces exactly one matching security question; an affirmative response permits exactly one matching action.
2. Already authorized actions proceed without a question. Safe alternatives, forbidden actions, ordinary questions, and unknown classification evidence receive no question permit.
3. Missing, malformed, replayed, cross-boundary, changed-scope, and mixed/batched question receipts deny the question or action as appropriate, with no unauthorized dispatch.
4. Refusal continues independent safe work; no reply stays pending; unavailable/headless interaction defers; implement never asks.
5. Parent, agent, equivalent question-tool, and code-mode paths enforce the same contract where supported. Unsupported paths remain visibly unavailable.
6. Missing, disabled, changed/untrusted hooks, stale startup tokens, wrong-event tokens, hook exceptions, malformed outputs, and timeouts cannot produce an enforcement pass. Guard-dependent work follows the ladder while independent safe work continues.
7. Actual nonterminal and terminal Stop events exercise ADR 0010 independently of the question guard. The terminal record cannot claim missing guard evidence was produced.

The normal canary remains question-free after scaffold. Dedicated security variants provide an explicit simulated human responder for eligible interactive cases and distinguish an authorized security pause from an unregistered stop. Missing/untrusted-guard variants must be red even when safe continuation reaches a review handoff. These requirements feed [Canary: fixture, variants, receipt, budget, release gate](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1028); they do not resolve its fixture, harness, budget, or release-gate design.

## Evidence and trade-offs

- Current source has no question-tool matcher in `speckit-pro/hooks/hooks.json:15` or `speckit-pro/codex-hooks.json:8`. The egress helper reports `writes_state=False` (`speckit-pro/speckit_pro_runner/helpers/egress_authorization.py:350`). Existing scoped authorization bindings are in `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py:3975,4199,4230`.
- Current role enforcement has parent/unknown-role pass-through and catches failures with empty success (`speckit-pro/speckit_pro_runner/host_parity.py:233`; `speckit-pro/scripts/codex-agent-policy-hook.py:34,63`). Existing sweep attestation binds hook hashes and age, not the run or individual invocation (`speckit-pro/scripts/sweep-isolation-hook.py:105,138`). None proves this future security contract.
- Official [Codex hook trust](https://learn.chatgpt.com/docs/hooks#review-and-trust-hooks), [tool coverage](https://learn.chatgpt.com/docs/hooks#tool-coverage), and [PreToolUse](https://learn.chatgpt.com/docs/hooks#pretooluse) documentation establish the limitations and supported denial shapes. Official [Claude Code hooks](https://code.claude.com/docs/en/hooks#pretooluse-decision-control) documents explicit denial and host permission precedence. Context7 and current official OpenAI documentation were consulted; no live question or Stop guard was tested in this planning session.

Rejected alternatives were agent-only classification, broad security categories, exceptions to forbidden actions, reusable/cross-run consent, startup-only execution proof, stopping all independent work for a missing guard, rejecting all headless planning, and waiting after a refusal. Narrow receipts cost more explicit evidence but prevent a question permit or setup snapshot from silently becoming execution authority.
