# Quickstart: Safe Capability Collection and Offline Replay

## Safety Boundary

Use this workflow only for a pinned local Codex build and candidates already
admitted by the current G56R-001 official-source ledger. Collection is
non-scored. It cannot establish platform support, effort support, eligibility,
quality, preference, ranking, or qualification.

Before collection:

1. Use a clean worktree at the intended repository revision.
2. Choose an absolute `raw_evidence_root` outside every Git worktree.
3. Restrict that root to the collecting operator (`0700` directories and
   `0600` files).
4. Confirm the resolved Codex executable/package and reported version belong to
   the same build used for app-server, CLI, and picker observations.
5. Do not paste raw responses, credentials, account identifiers, user prompts,
   paths, hostnames, or repository remotes into tracked files.

Create separate private input and raw-evidence directories before running the
commands below. Their immediate parent directories must be mode `0700`; every
existing private input file must be a regular non-symlink file with mode `0600`.

```sh
mkdir -p /absolute/path/outside/repository/g56r-002-private
mkdir -p /absolute/path/outside/repository/g56r-002-raw
chmod 0700 /absolute/path/outside/repository/g56r-002-private
chmod 0700 /absolute/path/outside/repository/g56r-002-raw
# After writing the captured refresh, name it by the SHA-256 of its exact bytes:
chmod 0600 /absolute/path/outside/repository/g56r-002-private/CAPTURE_SHA256.json
```

## 1. Run the Focused Offline Tests

```sh
python3 tests/speckit-pro/unit/test-g56r-002-capability-telemetry.py
```

This step requires no network, Codex client, or raw evidence store.

## 2. Revalidate the Current Ledger

Capture the 22 current official pages outside the repository first. The capture
JSON must contain the exact requested/canonical locator, RFC3339 UTC retrieval
time, status, invalidated claim IDs, base64-encoded retrieved UTF-8 body, and
content-addressed bounded extracts for every source. Then run the adapter's
offline normalization and authority check:

`CAPTURE_SHA256` is the lowercase SHA-256 of the complete capture file bytes.
The adapter rejects a filename that does not match those bytes.

```sh
python3 tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py refresh-sources \
  --manifest docs/ai/research/codex-agent-route-candidate-manifest.json \
  --captured-refresh /absolute/path/outside/repository/g56r-002-private/CAPTURE_SHA256.json \
  --raw-evidence-root /absolute/path/outside/repository/g56r-002-raw \
  --output /absolute/path/outside/repository/g56r-002-private/source-refresh.json
```

Review every outcome. A changed, inaccessible, withdrawn, redirected, or
conflicting source invalidates only its bound current claims/routes. Stop if the
output consumes historical `OSL-*` rows or cites a non-OpenAI canonical domain.
The command copies the exact aggregate capture into `raw_evidence_root`; the
normalized refresh remains private because it retains the base64-encoded
retrieved bodies needed to recheck every body and bounded-extract digest. Freeze
publication strips those body bytes, commits the capture digest in every
validated sanitized refresh row, and fails if the referenced raw object is
missing or disagrees with the normalized rows.

## 3. Pin the Client Identity

```sh
python3 tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py identify-client \
  --reported-version REPORTED_VERSION \
  --executable /absolute/path/to/codex \
  --distribution DISTRIBUTION_ID \
  --output /tmp/g56r-002-client-identity.json
```

The output must contain the reported version and either an immutable vendor
build ID or the SHA-256 of the resolved executable/package. Reuse the resulting
`client_identity_id` for all three surfaces; do not join mismatched builds.
Use `--build-id VENDOR_BUILD_ID` instead of `--executable` when the vendor
provides an immutable build ID.

## 4. Collect the Three Surfaces

App-server collection uses documented initialization, `model/list` with hidden
entries included, and documented provider-capability reads. CLI and picker use
complete non-mutating selector enumeration from a clean pinned-client session.

```sh
python3 tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py collect \
  --surface app_server \
  --client-identity /tmp/g56r-002-client-identity.json \
  --raw-evidence-root /absolute/path/outside/repository/g56r-002-raw \
  --work-item-kind task \
  --work-item-id G56R-002-T013 \
  --output /tmp/g56r-002-app-server-sanitized.json
```

Repeat with `--surface cli` and `--surface interactive_picker`. The picker
method may consume an operator-recorded complete enumeration, but it must record
its visibility rules and evidence digest. If any collection is partial or
irreproducible, record `unknown`; never fill a missing value from another
surface.

This slice has no repository-approved live collector, so the command records a
content-addressed `unknown` observation after validating the external raw-store
boundary. It derives the active checkout's immutable revision/tree binding and
binds the typed work item into each observation. All three observations must
share those bindings. The `unknown-observation-v1` method is explicitly
non-authoritative and does not infer entries from another surface.
For each attempt, the collector writes one sanitized unknown-attempt record to
`raw_evidence_root/<sha256>.json`, verifies its exact bytes, and uses the same
digest in the observation's `raw://sha256:...` reference.

Raw captures remain outside Git. The adapter may emit only deny-by-default
sanitized, schema-allowlisted output for review.

## 5. Use the Canary Only When Discovery Is Unavailable

The canary command is permitted only for a source-admitted tuple whose
documented discovery is unavailable:

```sh
python3 tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py canary \
  --manifest docs/ai/research/codex-agent-route-candidate-manifest.json \
  --freeze /tmp/g56r-002-candidate-freeze.json \
  --model CANONICAL_MODEL_ID \
  --effort CANONICAL_EFFORT \
  --executor-result /absolute/path/outside/repository/g56r-002-private/canary-executor-result.json \
  --raw-evidence-root /absolute/path/outside/repository/g56r-002-raw \
  --output /tmp/g56r-002-canary-successor-freeze.json
```

The adapter accepts only a result from an approved injected executor contract
for a live launch. That executor must enforce the 30-second wall timeout, 64 KiB
combined output cap, process-tree termination, and zero retries; the result
uses the closed v1 envelope and records its contract/implementation/result
digests, approved platform, and enforcement acknowledgements. A successful
result is appended atomically to a content-addressed successor freeze; the
validated predecessor cannot be overwritten. Approval comes only from the
repository-owned executor-ID allowlist, which is intentionally empty in this
slice; an arbitrary result file cannot self-approve, so this command exits
nonzero before consuming an executor result. When `--freeze` is already
treatment-bound, also pass `--expected-telemetry-profile-id`,
`--expected-treatment-contract-digest`, and
`--expected-treatment-evidence-digest` from the separately validated treatment
bundle and retained evidence set; omitting any binding fails closed.
Default repository tests inject a deterministic
allowlist and fake result and launch no process. Only a future separately
reviewed admitted executor plus exit zero and the predeclared sentinel may
record pinned-environment availability. Every other terminal class is unknown
and excludes the tuple. To retry an independently proven transient condition,
create a successor snapshot first.

Before publication, the adapter resolves `evidence_digest` to
`RAW_EVIDENCE_ROOT/<sha256>.json`, verifies the private content-addressed file,
and requires its canonical closed redacted schema to match the result envelope.
An incomplete fixture observation alone does not authorize a canary: the
adapter derives documented-discovery unavailability only from an
`unknown-observation-v1` collection outcome in the validated matrix. Shared
candidate routes with the same model/effort use one canary key and retain their
independent source-admission decisions.
Private and content-addressed inputs are opened once without following a final
symlink, bounded from the opened descriptor, and checked for descriptor or
pathname replacement before their exact retained bytes are parsed or hashed.

## 6. Build and Review the Freeze

```sh
python3 tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py freeze \
  --manifest docs/ai/research/codex-agent-route-candidate-manifest.json \
  --source-refresh /absolute/path/outside/repository/g56r-002-private/source-refresh.json \
  --client-identity /tmp/g56r-002-client-identity.json \
  --app-server /tmp/g56r-002-app-server-sanitized.json \
  --cli /tmp/g56r-002-cli-sanitized.json \
  --interactive-picker /tmp/g56r-002-picker-sanitized.json \
  --raw-evidence-root /absolute/path/outside/repository/g56r-002-raw \
  --published-at RFC3339_UTC_PUBLICATION_TIME \
  --output docs/ai/research/codex-g56r-002-executable-candidate-freeze.json
```

When a pinned-build surface exposes both a raw label and the exact canonical
machine ID, pass an optional `--aliases /path/to/aliases.json`. Each map entry
must name the raw label and bind `canonical_model_id`,
`authority_kind: machine_readable_identifier`, and the observing
`authority_surface`. The adapter rejects aliases without one exact matching
entry on that same pinned surface.

The freeze command accepts no free-form repository or work-item value. It
rebuilds those values from the three observations and rejects a mismatch.
When the matrix contains an `unknown-observation-v1` result, initial publication
also resolves every content-addressed attempt record under `raw_evidence_root`
and verifies its exact deterministic bytes before creating the tracked freeze.

Review that:

- joins use canonical model ID and effort token;
- raw labels and disagreements are preserved;
- runtime evidence never admits a model or effort;
- hidden entries require independent current-ledger admission;
- ordinary gaps exclude only the affected tuple;
- fixture and unknown collection methods remain non-authoritative;
- the freeze ID covers the complete published payload except the ID itself;
  and
- no raw or machine-sensitive value entered the tracked artifact.

Revalidate the complete published artifact after generation:

```sh
python3 tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py validate-freeze \
  --manifest docs/ai/research/codex-agent-route-candidate-manifest.json \
  --freeze docs/ai/research/codex-g56r-002-executable-candidate-freeze.json \
  --predecessor-freeze /tmp/g56r-002-capability-predecessor-freeze.json \
  --expected-telemetry-profile-id sha256:9be2156764d858a2358a778414e4f978325e69686f11359ad1a7b168463a8979 \
  --expected-treatment-contract-digest sha256:8c2f9e182d4a97f0934f7f79ab260a09777cfde362f7e8d3bf9a7884101a5199 \
  --expected-treatment-evidence-digest sha256:e9c1b23f4b09b594f17d23f7632cab25eb1f73f8b63c1e91da0544507c73ce1f
```

The predecessor path must be the trusted, canonical US1 artifact retained by
the operator. The three expected treatment IDs come from the separately validated
treatment bundle, never from the successor artifact itself. This rebuilds the
manifest binding, sanitized source refresh, surface matrix, runtime snapshot,
tuple decisions, derived candidate lists, canary records, lineage, treatment
contract and exact evidence-set bindings, and the whole-freeze content identity.

Any later evidence change creates a successor freeze rather than editing the
published ID in place.

## 7. Validate the Treatment Bundle

```sh
python3 tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py validate \
  --fixture tests/speckit-pro/unit/fixtures/capability-treatment-replay/treatment-replay.json
```

The US2 validator checks the closed telemetry inventory, six-ID joins, typed
null states, configured-route proof, resource/lifecycle fields, and separate
resolver/service-reroute records. Its positive fixtures prove both authorized
success paths: configured proof with complete observed reroute capture, and an
observed supported route bound to a canonical non-null model/effort tuple. This
does not authorize publication for an excluded capability tuple: a successor
can publish `proven` only for a prior-freeze tuple that is included,
source-admitted, availability-supported, and surface-agreed. Its `published_at`
must be no earlier than every bound route-resolution and non-null observation
timestamp. The offline repository command is supported
on macOS, Linux, and Windows: it uses descriptor-relative traversal where
available and verifies the final Windows file handle against the approved
repository path. Operator-only raw-evidence commands remain POSIX-only. The
digest-manifest replay command and its
two-pass normalized-output comparison are T026-T030 work and remain unavailable
until the US3 replay increment is implemented.

## 8. Repository Verification

```sh
python3 tests/speckit-pro/unit/test-g56r-002-capability-telemetry.py
python3 -u tests/speckit-pro/run-all.py --layer 1
pnpm --dir docs-site reference:generate
pnpm --dir docs-site reference:check
python3 -u tests/speckit-pro/run-all.py
git diff --check
```

The generated reference page must be regenerated, not hand-edited. Live
collection is never part of the default deterministic suite.

## Retention Cleanup

Freeze and canary publication automatically add immutable content-addressed
records under `raw_evidence_root/retention-records/`. Those records become
governing only after the exact freeze bytes exist and an immutable receipt is
directory-fsynced under `publication-receipts/`. Re-running the same publication
recovers a crash between those steps; a different artifact at the output path
fails before registration. Records left by failed publication remain reported
as non-governing pending claims. Each protects its evidence only until the
earlier of its declared deadline or 30 days after registration; cleanup uses
the latest governing or individually capped pending deadline. Before registration, publication
semantically revalidates the source capture, every non-fixture observation, and
every canary result against the retained private bytes. It publishes and
re-reads the exact canonical output as a single-link target through one
identity-bound parent descriptor before issuing a receipt. Recovery rejects an
existing matching output if any alternate hard link remains. Private record directories are likewise
enumerated and opened through one identity-bound descriptor; directory
replacement, entry substitution, or a changed before/after entry set fails
closed. Before the deadline, verify that every
governing retained digest still has its exact bytes:

Every capability JSON input is strict UTF-8 JSON with unique object keys and
finite numbers. Inputs deeper than 64 levels or larger than 100,000 total nodes
fail closed, including parser recursion failures.
Source-capture materialization accepts only bytes-like input no larger than
32 MiB and enforces that bound before parsing or hashing.

```sh
python3 tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py retention \
  --raw-evidence-root /absolute/path/outside/repository/g56r-002-raw \
  --as-of 2026-08-16T04:44:32.543010Z \
  --mode verify \
  --output /absolute/path/outside/repository/g56r-002-raw/retention-report.json
```

At or after the latest 30-day deadline, apply cleanup using the adapter's
current UTC clock and then verify that state. The example deadline below is
derived from the committed freeze's `2026-07-17T04:44:32.543011Z`
`published_at`; a successor freeze can extend it.

```sh
python3 tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py retention \
  --raw-evidence-root /absolute/path/outside/repository/g56r-002-raw \
  --mode cleanup \
  --output /absolute/path/outside/repository/g56r-002-raw/cleanup-report.json
python3 tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py retention \
  --raw-evidence-root /absolute/path/outside/repository/g56r-002-raw \
  --as-of 2026-08-16T04:44:32.543011Z \
  --mode verify \
  --output /absolute/path/outside/repository/g56r-002-raw/retention-report.json
```

Cleanup first appends and directory-fsyncs an immutable v2 intent under
`deletion-intents/`, binding the original private file identity. It then
renames that exact inode to a deterministic quarantine name and
directory-fsyncs the raw store. An immutable v3 successor binds the initial
intent, quarantine name, and quarantine identity before unlink. Cleanup then
unlinks the quarantined bytes, proves through the still-open descriptor that
the link count is zero and the content digest is unchanged, directory-fsyncs
the raw store, and appends the immutable v2 completion proof under
`deletion-records/`. The proof retains the raw digest, complete retention record
history, governing deadline, actual successful cleanup time, proof method, and
v3 authority. If v3 persistence fails, a retry resumes the exact quarantined
inode from v2. A retry from v3 proceeds only while the exact bound quarantine
still exists; if unlink occurs without a durable completion record, the state
is indeterminate and remains fail-closed. Reappeared targets, identity-changed
quarantine entries, and missing, forked, or disconnected intent chains remain
fail-closed. Repeated cleanup after durable completion is idempotent. Every raw
file must have exactly one hard link. Append-only writes
directory-fsync after both final-name publication and temporary-name removal.
A shared parent-directory advisory lock is acquired before a reserved temporary
pathname appears and held through writer commit or recovery; every temporary
also holds its own advisory lock until commit. After a crash, the next operation
holds both locks and re-proves the temporary's directory-relative
pathname and inode before discarding a single-link pre-publication file. If both
names survive, recovery additionally proves the temporary is the sole alternate
link to the exact target and re-syncs the directory. Public append-only outputs
use the same protocol, and identical source-capture writers accept only a
verified content-addressed, single-link winner;
cleanup fails closed if a power-loss artifact or any alternate hard link still
reaches governed bytes. Before quarantine, a retry requires the exact canonical
v2 identity; afterward it requires the exact v2- or v3-bound quarantine identity
until verified unlink. Registration and
cleanup serialize through the persistent
mode-`0600` `.retention-lock` advisory-lock file. A process crash releases the
kernel lock automatically, while another live operation fails closed. Do not
remove the lock file: unlinking it during an active operation can defeat
serialization by allowing a second lock inode. `--as-of` is accepted only for
read-only verification;
cleanup always uses current UTC. Do not delete committed sanitized fixtures or
published freeze records; repository tests continue to pass without the raw
store. Live private-store commands fail closed on Windows until the adapter can
verify an owner-only DACL equivalent to POSIX `0700`/`0600`.
