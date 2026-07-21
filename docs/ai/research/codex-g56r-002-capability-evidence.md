# G56R-002 Capability Evidence

## Freeze Result

The current append-only treatment successor preserves a valid capability freeze
with zero eligible tuples:

- Candidate freeze: `sha256:087cd717bd4daf9e41f064b86e70335e011c2ba33c5a7b4d3d95a2962f22629c`
- Telemetry profile: `sha256:9be2156764d858a2358a778414e4f978325e69686f11359ad1a7b168463a8979`
- Treatment contract: `sha256:8c2f9e182d4a97f0934f7f79ab260a09777cfde362f7e8d3bf9a7884101a5199`
- Treatment evidence set: `sha256:e9c1b23f4b09b594f17d23f7632cab25eb1f73f8b63c1e91da0544507c73ce1f`
- Published at: `2026-07-18T19:40:00Z`
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

The current successor binds telemetry profile
`sha256:9be2156764d858a2358a778414e4f978325e69686f11359ad1a7b168463a8979`,
exact-treatment contract
`sha256:8c2f9e182d4a97f0934f7f79ab260a09777cfde362f7e8d3bf9a7884101a5199`,
and treatment evidence set
`sha256:e9c1b23f4b09b594f17d23f7632cab25eb1f73f8b63c1e91da0544507c73ce1f`.
Any later source, client, surface, normalization, telemetry, treatment-evidence,
or tuple-decision change creates another successor ID.

Success-path fixtures exercise the standalone treatment contract, but successor
publication cannot turn that evidence into capability authority. A `proven`
trace must map to an included, source-admitted, availability-supported,
surface-agreed prior tuple; excluded tuples may retain only non-authoritative
dispositions. The successor timestamp is also ordered after every bound route
resolution and non-null observation capture.

Raw-evidence cleanup begins with an identity-bound v2 deletion intent. It
renames that inode to a deterministic quarantine name, synchronizes the raw
root, and journals a v3 successor binding the quarantine name and identity
before unlink. A failure before v3 can resume from the v2-bound quarantine; a
failure after v3 can resume only while the exact v3-bound quarantine still
exists. If unlink occurs without a durable completion record, absence alone
cannot prove deletion and cleanup remains fail-closed. Reappeared targets,
identity-changed quarantines, forked intent chains, and hard-link races also
remain fail-closed.

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
Before registration, publication semantically revalidates the source capture,
every non-fixture observation, and every canary result against the retained
private bytes. The public append-only target is created, inode-checked, and
re-read through one identity-bound parent descriptor as a single-link file; the
exact canonical bytes are checked again before the receipt is written. An
existing matching output is recoverable only when it satisfies the same
single-link invariant.
An interrupted publication can be recovered idempotently; unreceipted records
remain non-governing pending claims, but each protects evidence until the
earlier of its declared deadline or 30 days after registration. The effective
deadline is the latest governing or individually capped pending deadline. The deterministic
`retention` command verifies pre-deadline presence, fails closed on missing or
overdue bytes, and in `cleanup` mode first appends and directory-fsyncs a
deletion-intent record. It then unlinks the expired bytes descriptor-relative,
proves the open descriptor has zero links with unchanged content identity,
directory-fsyncs the raw store, and only then appends and directory-fsyncs the
terminal deletion record with the actual successful cleanup time. Replaying
cleanup after durable completion is idempotent; a v3 intent whose quarantine
and completion record are both absent is indeterminate and fails closed. The
digest, retention history, and deletion record remain auditable after the bytes
are gone. Registration and cleanup share an atomic private-root lock, so a newer
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
same inode. Retention, receipt, intent, and deletion-record directories are
loaded through one identity-bound directory descriptor, with descriptor-relative
entry opens and an unchanged before/after entry set; directory replacement or
a mixed snapshot fails closed.
Capability JSON parsing also fails closed on duplicate keys, non-finite values,
invalid UTF-8, parser recursion, nesting beyond 64 levels, or more than 100,000
total nodes.
Source-capture materialization rejects non-bytes-like or greater-than-32-MiB
input before parsing or hashing. A shared parent-directory advisory lock is
acquired before any reserved temporary pathname appears and is held through
writer commit or recovery. Every temporary also holds an advisory lock until
commit. Recovery obtains both locks and re-proves the
directory-relative pathname and inode before removing an abandoned single-link
pre-publication file. A linked temporary additionally must be the sole alternate
name for the exact target and bytes; recovery syncs before and after unlink and
re-proves the target is single-link. Public append-only directories use the same
protocol, and a concurrent identical source capture accepts only the verified
content-addressed winner.
