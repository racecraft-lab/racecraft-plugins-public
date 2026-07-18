# G56R-002 Capability Evidence

## Freeze Result

The current append-only treatment successor preserves a valid capability freeze
with zero eligible tuples:

- Candidate freeze: `sha256:4563bb9c21f9c2378b70d67c5bfe6f82e2febda01b8506bf2e274081bba7b149`
- Runtime snapshot: `sha256:450a655fabafb765b19bfc9ff3cbefe4b075d6c40fdbc5fd9dbc8ce8c4cfc3fe`
- Surface matrix: `sha256:99739c0895250de0eb0cf1a0215fd2e5168213081d41f6b2f828c274528c32b2`
- Pinned client identity: `sha256:5a4532ddce5b4806ee681c6becac4541be13a2f9eb5af2ee2e618e4094dee285`
- Current source-refresh set: `sha256:6f382a11b06df40e03719d713fae09c8d88a9ddb9586b735a48f039ac8505ea9`
- Complete tuple decisions: `sha256:b53455921d0b4fc9734c582490f5ea8071f972161ad06984f4d80ba7f36ee981`

Zero eligibility is intentional. The app-server, CLI, and interactive-picker
collections are each recorded as `unknown` under the same pinned client
identity. No surface value was inferred, no runtime observation created source
authority, and no runtime model, effort, or capability entry was materialized.
All 23 provisional routes remain present as explicit exclusions. Every route
records `canonical_effort_unknown`, `effort_not_source_admitted`, and
`collection_evidence_non_authoritative`: its model sources remain current, but
the inherited route has no authoritative canonical effort token and the
unknown collection method cannot authorize inclusion.

## Authority and Collection Method

The adapter validated exactly 22 unique current `OPENAI-DOC-*` source records
from the G56R-001 v3 manifest and rejected historical `OSL-*` rows as active
authority. It also quarantined the inherited punctuation-only effort values in
`G56R-001-ESR-003`; none became an effort token.

Execution-time revalidation found 20 sources whose raw HTML digest changed,
one stable redirect, and one byte-stable current source. Nineteen changed
sources retained their exact prior bounded extracts. `OPENAI-DOC-011` changed
its bounded pricing wording from “Work” to “Work mode”, so the refresh fails
closed by invalidating only `G56R-V2-MODEL_PRICING`. All canonical URLs matched
the exact requested or canonical locator in the current manifest. Only body and
extract digests, bounded extracts, locators, and claim bindings enter the
committed freeze; raw source bodies do not.

The operator-local capture supplied measured URLs, strict RFC3339 UTC
timestamps, outcomes, claim-scoped invalidations, bounded extracts, and the
actual retrieved UTF-8 bodies. The adapter computed every body and extract
digest itself, reduced HTML to visible text, required each extract to occur in
that body, and reconstructed facts, bindings, and prior-record identity from
the current manifest. The raw-body capture and normalized refresh remain
outside Git in an operator-only directory with mode `0700` and files with mode
`0600`. The normalized refresh keeps the retrieved body bytes long enough for
freeze-time revalidation; the published freeze strips them.
The aggregate capture is stored as the exact-byte content-addressed object
`sha256:26b4bc034cac55e149b1b0b5c7648531be2f84d46385160f3c6c30ac582df70a`;
the refresh command rejects a filename that does not match those bytes, copies
that exact object into `raw_evidence_root`, and binds its digest into every
sanitized source-refresh row in the freeze.

The pinned identity records `codex-cli 0.144.4` and an executable SHA-256 rather
than an absolute executable path. The three surface collections emitted
explicit `unknown` observations with no entries through the closed
`unknown-observation-v1` method. That method is non-authoritative;
`fixture-enumeration-v1` is synthetic, and the live collection-method allowlist
is empty. An arbitrary collection-method ID is rejected rather than becoming
authority. The matrix remains aggregate-valid because its canonical surface
order, shared client, repository and typed work-item bindings, normalization
map, and integrity digest are provable; missing surface evidence is tuple-local.

All three observations bind repository revision
`ab272f05937bd08a50e40710b3f1ad3b0dc8452b`, tree object
`f51c4d7253598ef466ac402922afa869512b1bde`, repository binding
`sha256:b8db97fb46090729074fca06a15041aee74232b3642ef3780ebf8365c6d965cf`,
and typed task `G56R-002-T013`. The collector derived the immutable Git values
from a clean committed checkout containing the adapter and contracts; staged,
unstaged, or untracked state makes collection fail. The freeze accepts no
caller-supplied substitute.
The runtime snapshot derives the same repository and work-item values from the
matrix, and both participate in its content identity.
Every tuple additionally binds the G56R-001 manifest snapshot, complete route
and agent-contract digests, instruction/source hashes, official-source and
effort-record refresh digests, all three surface observations, hidden state,
normalization, and the same runtime snapshot ID.

## Probe, Telemetry, and Successors

The repository-owned canary-executor allowlist is empty. No canary ran and an
external result or freeze-carried approval cannot self-approve. The CLI exits
before consuming a result while that allowlist is empty. A separately reviewed executor would still
be limited to one 30-second, 64 KiB, zero-retry attempt per snapshot/model/effort
and could prove only pinned-environment availability.

The telemetry-profile ID currently binds an explicit pending-treatment
placeholder. Increment 2 must publish a successor freeze when the closed
telemetry and exact-treatment contract is available; it must not edit this
content identity. Any later source, client, surface, normalization, or tuple
decision change likewise creates a successor ID.

The published-freeze validator rechecks the pinned manifest digest, all 22
sanitized source-refresh rows, matrix integrity and canonical observation
order, repository/work-item equality, runtime snapshot, complete tuple
decisions, derived included/excluded lists, canary approvals/results, and every
redundant top-level ID. The candidate-freeze ID hashes the complete published
payload except the ID itself, so a replay or mutation cannot preserve the same
identity.

This is the first committed G56R-002 freeze. Earlier identities produced during
the rejected, uncommitted implementation review were drafts rather than
published predecessors. The CLI nevertheless accepts explicit predecessor IDs
for every later freeze and runtime-snapshot successor.

Raw captures, if any, remain in an operator-only content-addressed store outside
the repository with directory mode `0700` and file mode `0600`; symlinks,
special files, permissive descendants, and Git worktree locations are rejected.
The source-refresh digest resolves to the aggregate capture containing all 22
retrieved bodies. Each surface's `raw://sha256:...` reference is backed by a mode-`0600`
sanitized attempt record named by that exact digest, and collection re-reads
the stored bytes before publishing the observation.
Freeze and canary publication stage one content-addressed retention record per
non-fixture digest. Each record binds the freeze ID, publication time, and exact
30-day deletion deadline, but becomes governing only after the exact artifact
bytes exist and a content-addressed publication receipt is directory-fsynced.
An interrupted publication can be recovered idempotently; unreceipted records
remain pending and cannot extend deletion. The deterministic
`retention` command verifies pre-deadline presence, fails closed on missing or
overdue bytes, and in `cleanup` mode appends and directory-fsyncs the complete
deletion record before removing the expired bytes, then directory-fsyncs the
raw store. Replaying cleanup is idempotent; the digest,
retention history, and deletion record remain auditable after the bytes are
gone. Registration and cleanup share an atomic private-root lock, so a newer
publication cannot extend a digest while cleanup is deleting it. Destructive
cleanup derives its deletion time from current UTC and rejects `--as-of`;
arbitrary logical timestamps are read-only verification inputs. The committed
JSON is deny-by-default sanitized and contains no
retrieved source bodies, credentials, headers, cookies, prompt content, account
identifiers, hostnames, absolute paths, or repository remotes.
Private-store operations fail closed on Windows until owner-only DACL validation
can enforce the same access boundary as POSIX `0700` directories and `0600`
files; offline committed-artifact validation remains platform-neutral.
Append-only private writes directory-fsync after both final-name publication
and temporary-name removal. Every governed raw file must have one hard link;
cleanup fails closed if a crash artifact or alternate name still reaches the
same inode.
