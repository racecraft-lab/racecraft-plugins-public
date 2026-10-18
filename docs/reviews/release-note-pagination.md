# Release note pagination review

## Accepted limits

- Capture assembles all pages and stores empty Compare headers. The replay loader still rejects nonempty Link headers in old or manually supplied snapshots. That branch cannot be reached by newly captured snapshots; keeping it preserves fail-closed compatibility.
- Capture and replay each validate Compare totals at their own input seam. Repeated non-boolean integer checks enforce the same shape; they do not classify different outcomes.
- Capture rejects duplicate or missing commit SHAs; replay's shared `discover_commits` does not repeat that check. Replay reads only a snapshot whose SHA-256 matches the one recorded at capture, so a duplicate cannot reach it from a new run, and PR deduplication would hide a duplicate's effect anyway.
- `audit-release-notes.py` checks the published body with its own literal (`## Highlights` plus a blank line). It verifies composer output rather than detecting a composed input, and the release contract validator pins that literal. The composed-input check has one owner, `release_note_policy.is_composed_release_body`.
- Published-release recovery accepts only an original, uncomposed release body. After capture succeeds, rerun failed composition jobs against that immutable snapshot. A fresh recovery of an already composed body fails closed instead of treating Highlights as original release-please input.

## Verification scope

The 309-commit fixture covers capture, offline replay, and composition. The audit test accepts a 309-commit result. Recovery and workflow checks prove the published-release mode skips asset mutation. A live release recovery is intentionally left for a maintainer after merge.
