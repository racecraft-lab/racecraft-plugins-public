Priority: minor

## Summary

The sweep receipt shape is stated four times with no comparison test, and the analyst prompts promise an anchor-uniqueness check that happens only after the receipt is accepted, so the analyst cannot retry. Codex stage instructions are written twice. The sweep, research and author brokers copy the same JSON-RPC loop, and the preview launcher and author broker duplicate sweep helpers.

## Evidence

- **brokers-and-verification-006** (minor): The receipt shape is stated four times: the shipped schema file (used by Codex), an inline CLAUDE_RECEIPT_OUTPUT_SCHEMA dict (used by Claude), RECEIPT_RE in sweep_isolation.py, and RECEIPT_RE/CAPABILITY_RE in the hook script. No test compares them, so a change to one silently desyncs the others.
  - `speckit-pro/speckit_pro_runner/sweep_launcher.py:86-96`, `speckit-pro/speckit_pro_runner/contracts/sweep-receipt-output.schema.json:1-11`, `speckit-pro/speckit_pro_runner/sweep_isolation.py:47-49`, `speckit-pro/scripts/sweep-isolation-hook.py:21-22`
- **brokers-and-verification-007** (minor): Both analyst prompts say the synthesis anchor 'matches the snapshot exactly once', but validate_result and submit_result never check that. The only uniqueness check is live_text.count(anchor) == 1 at apply time, after the receipt is accepted, so an ambiguous anchor is refused late and the analyst cannot retry.
  - `speckit-pro/agents/sweep-analyst.md:96`, `speckit-pro/codex-skills/speckit-autopilot/references/sweep-prompts/analyst.md:29`, `speckit-pro/speckit_pro_runner/sweep_isolation.py:1454`, `speckit-pro/speckit_pro_runner/sweep_isolation.py:1504`
- **brokers-and-verification-015** (minor): The Codex stage instructions ('first action must be review_comment', 'submit_result exactly once', the result field shape) are written both in CODEX_STAGE_PROMPTS and in the sweep-prompts markdown, then concatenated into one prompt. The Claude path also validates its stage against the Codex-named CODEX_STAGE_PROMPTS dict.
  - `speckit-pro/speckit_pro_runner/sweep_launcher.py:50-80`, `speckit-pro/speckit_pro_runner/sweep_launcher.py:189`, `speckit-pro/speckit_pro_runner/sweep_launcher.py:242`, `speckit-pro/codex-skills/speckit-autopilot/references/sweep-prompts/classifier.md:1-12`
- **brokers-and-verification-002** (minor): One 1583-line module holds five jobs: Git snapshot capture, GitHub comment capture through gh, the HMAC session and receipt store, result validation and redaction, and the artifact-mutating apply_synthesis_receipt. apply_synthesis_receipt also calls the private SweepSession._consume_result.
  - `speckit-pro/speckit_pro_runner/sweep_isolation.py:268`, `speckit-pro/speckit_pro_runner/sweep_isolation.py:556`, `speckit-pro/speckit_pro_runner/sweep_isolation.py:833`, `speckit-pro/speckit_pro_runner/sweep_isolation.py:1381`, `speckit-pro/speckit_pro_runner/sweep_isolation.py:1454`, `speckit-pro/speckit_pro_runner/sweep_isolation.py:1504`
- **brokers-and-verification-008** (minor): The stdio JSON-RPC loop (initialize, ping, tools/list, tools/call envelope, error framing, parse-error handling) is copied across the sweep, research and author brokers. mcp_protocol.py shares only version negotiation. Error handling already differs: the research broker maps any exception to internal_error, the sweep broker only its three violation classes.
  - `speckit-pro/speckit_pro_runner/sweep_broker.py:236-330`, `speckit-pro/speckit_pro_runner/research_broker.py:1042-1097`, `speckit-pro/speckit_pro_runner/mcp_protocol.py:1-20`
- **artifact-gallery-007** (minor): The preview launcher imports six underscore-private helpers from sweep_launcher and near-duplicates its prompt-resource resolver and Codex command builder (clone groups 83 and 84 in the evidence pack).
  - `speckit-pro/speckit_pro_runner/preview_launcher.py:21-30`, `speckit-pro/speckit_pro_runner/preview_launcher.py:57-79`, `speckit-pro/speckit_pro_runner/preview_launcher.py:95-165`
- **artifact-gallery-008** (minor): author_broker duplicates the private-root and atomic state-write logic in sweep_isolation (clone groups 22 and 32). It also joins two unrelated jobs, formal-file write sessions and preview verdict sessions, behind one capability store, and it imports two helpers modules, which forms a dependency cycle that read_only.py breaks only with a lazy import.
  - `speckit-pro/speckit_pro_runner/author_broker.py:66-100`, `speckit-pro/speckit_pro_runner/author_broker.py:14-22`, `speckit-pro/speckit_pro_runner/author_broker.py:194-259`

## Proposed fix

- brokers-and-verification-006: Load the Claude schema from the same JSON file and add a test that the hook script's patterns equal sweep_isolation's.
- brokers-and-verification-007: Check anchor uniqueness against the snapshot file for edit.file in validate_result, and return a broker error code so the analyst can retry.
- brokers-and-verification-015: Keep the instructions in the markdown only, and use a neutral STAGES tuple for stage validation in both commands.
- brokers-and-verification-002: Split into snapshot, github capture, session store and apply-mutation modules, and expose a public consume method instead of _consume_result.
- brokers-and-verification-008: Extend mcp_protocol.py with one serve(handle_call, server_info, tools) loop that each broker supplies a call handler and error mapper to.
- artifact-gallery-007: Extract the shared Codex isolation helpers into one module with public names and parameterize the resolver and command builder.
- artifact-gallery-008: Share the private-state helpers with sweep_isolation and consider splitting the formal and preview session kinds.

## Acceptance

- [ ] The Claude receipt schema loads from the shipped JSON file; a test compares the hook patterns with sweep_isolation.
- [ ] A regression test that fails before the fix: an ambiguous anchor is refused by validate_result with a retryable broker error.
- [ ] One MCP serve loop in mcp_protocol.py; shared isolation helpers have public names.
- [ ] Runner trust metadata and dist/ are regenerated; both suites pass.

## Related

- Overlaps files changed by the open stop-policy stack: #851. Land after that stack merges.
- Overlaps files changed by the in-progress fix for #832.
- Depends on #877
- Depends on #882

Found by the 2026-09 coherence audit.
