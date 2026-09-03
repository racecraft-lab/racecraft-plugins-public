# Fixture 04 — Clarify, domain-only category

Verifies `[domain]` tag routes only to `domain-researcher`. Mirrors
fixture 01 but for the domain category. Together with fixture 01 they
establish the single-category baseline for two of the three named
categories.

## Keeping the item text keyword-free

The item above must stay clear of the security keywords listed in
`references/consensus-protocol.md`, in the singular and the plural. A
keyword anywhere in the item text widens dispatch to all three analysts,
which would contradict this fixture's `must_not_dispatch_to`. Replay mode
never reads `prompt.txt`, so only a `--live` run would notice; the unit
test `test-consensus-routing-helpers.py` routes this item text against the
`parse-consensus-categories` helper to catch the drift without a live run.
