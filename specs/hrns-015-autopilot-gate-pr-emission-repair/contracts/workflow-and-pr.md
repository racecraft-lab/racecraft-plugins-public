# Workflow, Packet, and Review Contract Deltas

## Final PR packet

The final packet input accepts one optional `release_note` property. Its JSON schema remains closed to unknown properties. When supplied, the renderer appends one `## Release note` after the eight required headings. The section has its own balanced editable markers; only the enclosed note body is editable. Structure validation requires exactly one nonempty `release-note` fence inside it. The heading and markers remain in the protected fingerprint, and a note body change may vary without changing protected content. Final editable-field count becomes four when the note is supplied; without it, the existing field set remains. Drafts retain zero fields and no release-note section.

The existing single `## UAT Runbook` heading stays between `## How To UAT` and `## Verification`. Under Verification, a protected generated line renders the **current** Phase 6.5 table `Verdict` (`proceed`, `remediate`, or `stop`). Final creation and refresh read that value even if an input body would otherwise bypass rendering. Missing/invalid verdict blocks final emission; Workflow Overview status and score are not fallback sources. The validated packet body is the PR body source, and a feature PR's release-note policy must pass without manual repair.

The packet dirty guard derives canonical paths from the validated feature directory and packet ID: `<id>.json`, `<id>/body.md`, and `<id>/validation.json` under the current packet directory. It ignores only those paths when untracked. A second packet, unrelated path, tracked modification, or unreadable Git status blocks both validation-write and output mutations.

## Post completion

`POST_STEPS` is the sole ordered 13-name source, with Final Reviewability Backstop and PR Packet/Body Generation separate. A new completion-boundary rule reads the persisted workflow and `autopilot-state.json`. Each canonical Post name must occur exactly once and be `completed` in both records. It reports every missing, duplicate, pending, or in-progress row and returns nonzero. Claude and Codex invoke it immediately before announcing successful completion; the existing `status-evidence` audit is not the completion contract.

Every team-capable phase, analyze, checklist, and implement executor on both hosts either obtains each child's final result or uses a supported stop operation, then requests graceful team shutdown and confirms no active child plus cleanup completion. A clean result is forbidden while any of these confirmations is missing; the structured executor result lists unresolved IDs/evidence. No assumption about Codex child lifetime after parent return satisfies this rule.

## Resolve-pr feedback protocol

Use `gh api graphql` for all unresolved review threads and their comments. Request bounded connection pages and continue each connection while `pageInfo.hasNextPage` is true, using its nonempty `endCursor`. Each thread's comments have an independent cursor; a failed page, inconsistent pageInfo, or absent continuation cursor makes feedback incomplete and stops before replies/resolution.

After complete collection: apply fixes, run required verification, commit, push, then query the PR's `headRefOid` freshly via GraphQL and compare with the intended local commit SHA. A failed gate, push, query, or mismatch stops before review replies. With a match, reply and resolve serially, read each thread back, and report confirmed resolved status. Existing file partitioning may still parallelize independent *fixes*; publication and review mutation follow the serial ordering.

## Scaffold blind-spot result

A dispatched analyst is awaited without a fixed five-minute timeout. A nonempty result is `ran` regardless of elapsed time. Only a dispatch error, empty return, or explicit operator instruction to continue without findings permits no-findings continuation. Record the outcome and specific reason in the existing Design Concept header `**Blind-spot pass:**` line and mirror it in the operator status. A whole-workflow stop request stops work, rather than being reinterpreted as abandonment. Elapsed time and silence never imply operator intent.
