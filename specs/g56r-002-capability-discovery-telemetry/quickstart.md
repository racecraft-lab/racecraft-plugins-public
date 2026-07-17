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
  --output /absolute/path/outside/repository/g56r-002-private/source-refresh.json
```

Review every outcome. A changed, inaccessible, withdrawn, redirected, or
conflicting source invalidates only its bound current claims/routes. Stop if the
output consumes historical `OSL-*` rows or cites a non-OpenAI canonical domain.
The normalized refresh remains private because it retains the base64-encoded
retrieved bodies needed to recheck every body and bounded-extract digest. Freeze
publication strips those body bytes and commits only the validated sanitized
refresh rows.

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
nonzero before consuming an executor result. Default repository tests inject a deterministic
allowlist and fake result and launch no process. Only a future separately
reviewed admitted executor plus exit zero and the predeclared sentinel may
record pinned-environment availability. Every other terminal class is unknown
and excludes the tuple. To retry an independently proven transient condition,
create a successor snapshot first.

## 6. Build and Review the Freeze

```sh
python3 tests/speckit-pro/layer6-efficiency/lib/codex_capabilities.py freeze \
  --manifest docs/ai/research/codex-agent-route-candidate-manifest.json \
  --source-refresh /absolute/path/outside/repository/g56r-002-private/source-refresh.json \
  --client-identity /tmp/g56r-002-client-identity.json \
  --app-server /tmp/g56r-002-app-server-sanitized.json \
  --cli /tmp/g56r-002-cli-sanitized.json \
  --interactive-picker /tmp/g56r-002-picker-sanitized.json \
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
  --freeze docs/ai/research/codex-g56r-002-executable-candidate-freeze.json
```

This rebuilds the manifest binding, sanitized source refresh, surface matrix,
runtime snapshot, tuple decisions, derived candidate lists, canary records, and
the whole-freeze content identity.

Any later evidence change creates a successor freeze rather than editing the
published ID in place.

## 7. Validate Treatment and Replay Twice

```sh
python3 tests/speckit-pro/layer6-efficiency/lib/treatment_trace_schema.py replay \
  --fixture tests/speckit-pro/unit/fixtures/capability-treatment-replay/treatment-replay.json \
  --digest-manifest tests/speckit-pro/unit/fixtures/capability-treatment-replay/fixture-digests.json \
  --repeat 2
```

The validator checks hashes before parsing, the closed telemetry inventory,
six-ID joins, typed null states, configured-route proof, resource/lifecycle
fields, and separate resolver/service-reroute records. It must produce identical
normalized output, dispositions, and digests on both passes without network or
raw-store access.

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

Thirty days after freeze publication, delete the raw capture bytes from the
external store and retain only their content digest and deletion record. Do not
delete committed sanitized fixtures or published freeze records. Repository
tests must continue to pass after raw evidence is gone.
