# Quickstart Validation Guide: HRNS-015

**Updated**: 2026-09-26. The eighteen-part delivery direction is owner-approved in the order recorded in plan.md, grouped under A → B → C1a → C1b → C2. Historical four/five-PR directions remain provenance. This guide defines validation after fixtures/repairs exist, not a report that this Plan pass ran implementation tests.

## Prerequisites and Setup

1. Use the explicitly bound feature worktree and its existing branch. Run commands from repository root; preserve other work and the private execution-control ledger/counters.
2. Use Python 3.11+ and the existing runner/test harness. No added Bash/jq/runtime dependency. Keep any historical or synthetic spec content under the test's own fixtures; tests must not open the active feature spec at runtime.
3. In a fresh worktree, prepare locked docs dependencies before docs commands: `pnpm --dir docs-site install --frozen-lockfile`.
4. For Python checks, use the repository's configured lint environment and `scripts/run-python-lint.py`; do not run detected raw `mypy .` across the tree or replace it with an invented gate.
5. Reconcile tasks/inventory to the approved eighteen-part direction and current marker contracts, then freeze each remaining acceptance case. Capture actual failing exit/result before its repair and passing exit/result after. Already-shipped #694/#698/#676 behaviors are baseline compatibility cases and should remain green.

## Existing Runnable Test Entry Points

These current entrypoints can run now; added acceptance cases may not exist yet. Passing an old entrypoint without the new case is not qualification of the new requirement. Commands run separately and their exact handles must reach terminal exits.

~~~text
python3 tests/speckit-pro/unit/test-speckit-pro-read-only-helpers.py
python3 tests/speckit-pro/unit/test-speckit-pro-mutation-helpers.py
python3 tests/speckit-pro/unit/test-autopilot-phase-coverage.py
python3 tests/speckit-pro/unit/test-generate-spec-index.py
python3 tests/speckit-pro/unit/test-reviewability-marker-guidance.py
python3 tests/speckit-pro/unit/test-native-scaffold-noninteractive.py
python3 tests/speckit-pro/layer1-structural/validate-skill-contracts.py
python3 tests/speckit-pro/layer1-structural/validate-spec-lifecycle-contracts.py
~~~

Tasks names new fixture/test files before implementation, registers them in suite-manifest, and supplies the exact per-case commands. The Plan candidate operations identify durable names for those additions; they are not scripts claimed to exist already.

## Slice A — Packet and Body

1. In an isolated test repository, prepare final-packet requests with absent/valid/blank/wrong-type/fence-breaking release_note; also prepare draft requests. Run the packet cases before repair and retain the specific failures.
2. After repair, repeat exactly those cases. A valid final note yields one Release note heading after the eight required headings, balanced fourth editable markers and one nonempty release-note fence. Omitted notes and drafts yield no note heading/fence/field; drafts keep zero editable fields. Malformed supplied notes reject.
3. Change only note body content and validate: protected fingerprint remains valid. Change protected heading/markers and validate: reject. Preserve one UAT Runbook heading between How To UAT and Verification.
4. Record a Phase 6.5 Verdict, render, change that Verdict and refresh with a supplied stale body. Expect the current protected Verification line. Missing/invalid Verdict blocks final emission; overview status is not substituted.
5. In a host fixture without packet ignore rules, validate/output with only the current canonical three untracked packet paths: succeed. Repeat with another packet, unrelated change, tracked packet modification or unreadable Git status: block. No ignore/force-add workaround.
6. Validate the emitted body against exact feat/fix title and host release-note policy using root AGENTS.md commands. Expect pass without manual body repair or skip label. Inspect both host instructions.

## Slice B — Gates, Index, Estimate and Commands

1. Keep named-entry, selected pragma and missing-budget #694 cases green. Add red-first complete/incomplete/duplicate/extra/placeholder/nonnumeric/at-block slice rows and ordered aggregate-result cases. Valid complete slices report their row sums and ordered slice_results; invalid rows block and name the field/slice.
2. Run ordinary and greenfield cases with identical file/surface counts. Only reviewable-LOC warn/block thresholds receive 1.5x; ordinary production/total/surface limits remain.
3. Add visible first/later Gap-token cases, two tags on one line, substring/mis-case/nested nonmatches and inline/fenced/indented code examples. G1–G4 and relevant count/details must agree with the stated visibility rule.
4. Use test-owned tracked stale index content and an untracked candidate inside a tracked directory. Before refresh, artifact check fails and names stale paths; after refresh it passes. Untracked candidates appear nowhere; staged additions remain eligible. Verify isolated check uses source-index membership.
5. Declare one quality slot, leave another undeclared, and test invalid object/key/blank/nonstring declarations. Valid overrides only its slot with declared provenance; absent slots preserve detection; invalid config fails G0 rather than falling back green. Preserve approved thresholds/basis.
6. Compare the same size input with/without additional distinct required_refactor_files. Expect the chosen 40 LOC weighting after modify discount and updated slice suggestion, ordinary baseline without signal and unchanged spike precedence. Do not count the same file twice.

## Slice C1a — Post Names and Completion

1. Compare both host lists, workflow template and formal lifecycle subset with the requested 13-name POST_STEPS authority. Final Reviewability Backstop and PR Packet/Body Generation remain separate. Any newly necessary source edit must be counted before delivery.
2. Run full-boundary cases with each missing/duplicate/pending/in-progress/mismatched/unjustifiably skipped row in either persisted record. Expect nonzero exit and every affected canonical name, even when no rows are recognized.
3. Complete every row in both representations: workflow Complete maps to state completed. Only an identical reason-coded absent-extension skip for a canonical optional extension row can substitute after both registry and directory absence evidence.
4. Resume a legacy 11-row record: preserve unique exact-name progress; initialize new/renamed rows pending and refuse full completion. Stage-only returns keep out-of-stage rows visible and make no full-completion claim. Ordinary status-evidence checks alone do not prove this boundary.

## Slice C1b — Executor Return and Teardown

1. Freeze structural cases for all four executor kinds on both hosts. Their required return contract includes each child result or supported stop, graceful shutdown request, no-active-child and cleanup confirmation.
2. Run host acceptance observations only in the authorized execution boundary. Clean return requires actual confirmations; a missing result/capability/evidence is named unresolved and cannot be called clean.
3. Keep separate the host's retention of completed inspectable threads and actual active-child state. Do not assert Codex post-parent child lifetime from these fixtures; HRNS-017 owns that observation.

## Slice C2 — Feedback, Scaffold, Envelopes and Legacy Links

1. Use offline mocked review connections with multiple thread pages and multiple comment pages inside a thread. Exhaust each independent cursor. A failed page/missing cursor/inconsistent connection blocks all replies and resolutions.
2. Record verify, commit, push, fresh matching headRefOid, reply, resolution and readback events. Failed verification yields no push/reply/resolve; failed push/query/mismatch yields no reply/resolve and retains the local commit. A success allows only serial reply/resolve after the fresh head match, with confirmed state.
3. Deliver a late nonempty analyst result: consume it and record ran regardless of duration. Separately exercise dispatch error, empty return and explicit operator abandonment: same specific reason in Design Concept/operator status. Silence/time/whole-workflow stop never invent abandonment.
4. Apply the approved FR-024 contract: Each documented inline request envelope must match a passing fixture byte for byte. Execute the five registered request envelopes on both hosts in fixture-safe modes: status index-check/topology, scaffold reviewability/worktree-placement and phase index-writing. Expect accepted exact envelopes and no malformed-request error. The broader sweep remains HRNS-019.
5. Keep new-template #698 links green. Update an existing roadmap with a real verified legacy target: preserve it. Update a broken legacy link: repair to actual .process output. Resolve targets relative to the containing roadmap.

## Repository Verification and Each PR Boundary

After targeted red/green, use the smallest relevant layer and then required suites. These commands come from the current repository contract; none was run as implementation verification in this Plan pass.

~~~text
python3 tests/speckit-pro/run-all.py --layer 1
python3 tests/speckit-pro/run-all.py --layer 4
python3 tests/speckit-pro/run-all.py
SPECKIT_SKIP_TOOLCHAIN_CHECK=1 GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_SYSTEM=/dev/null GIT_CONFIG_NOSYSTEM=1 PYTHONPATH=speckit-pro python3 -m speckit_pro_runner < tests/speckit-pro/unit/fixtures/runner-gates/requests/run-default-suite.json
python3 scripts/run-python-lint.py run ruff
python3 scripts/run-python-lint.py run mypy
python3 scripts/refresh-release-artifacts.py
pnpm --dir docs-site reference:generate
~~~

Use the repository's configured lint executable/environment; setup is owned by the toolchain, not an implicit install in this guide. Regenerate after source changes; commit generated outputs with their source before artifact-checking, since dirty tracked inputs fail the check. Then run separately:

~~~text
python3 scripts/refresh-release-artifacts.py --check
pnpm --dir docs-site reference:check
pnpm --dir docs-site validate:quality
~~~

Docs full validation and workflow lint apply when their actual inputs change, using root AGENTS.md. Before PR creation, run the exact final title and release-note policy gates from that contract; use the official gh-stack skill and packet-owned body. Record actual base/head changed paths, reviewable LOC, production paths, every generated/trust/reference/process path and current marker proof. Exceeding4 production or reaching25 total paths blocks; so do stale/malformed/unusable evidence and non-size safety failures. Candidate tables and draft-skipped CI are not substitutes. Preserve private ledger identity and consumed budgets through any permitted recovery.
