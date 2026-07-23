# Research: G56R-002 Capability and Telemetry Evidence

## Decision Summary

| Topic | Decision | Reason |
|---|---|---|
| Platform authority | Current canonical OpenAI documentation only | Runtime, repository, CLI, and picker evidence cannot create a platform fact |
| Primary discovery | Pinned app-server initialization, `model/list(includeHidden: true)`, then documented provider-capability discovery | The official app-server contract exposes the narrowest field-level discovery surface |
| Secondary surfaces | Complete non-mutating CLI and picker enumeration for the same `client_identity_id` | Cross-checks the pinned experience without overriding documentation |
| Normalization | `(official-ledger canonical model ID, canonical effort token)` | Prevents display labels or aliases from silently broadening eligibility |
| Hidden models | Record visibility; require independent source admission | Preserves evidence without turning discovery into candidate authority |
| Effective treatment | Profile-supported observed value, or approved consumed-configuration proof plus complete reroute monitoring | Requested configuration alone cannot prove an undocumented effective value |
| Service reroute | Separate post-assignment event joined by surface, `threadId`, and `turnId` | It must never overwrite resolver-selected fallback evidence |
| Probe fallback | One 30-second, 64 KiB, zero-retry canary per snapshot/model/effort | Establishes only pinned-environment availability while avoiding an undocumented campaign |
| Repository evidence | Deny-by-default sanitized, canonical JSON and SHA-256 | Supports deterministic replay without committing raw live responses |
| Module boundary | Codex adapter plus neutral schema/replay validator | Smallest design that preserves vendor provenance without a cross-vendor framework |

## Current Official Evidence Bindings

The source refresh performed for Specify used the official OpenAI documentation
MCP after Context7 transport closed. These bindings are the only platform-fact
inputs to the plan; implementation must revalidate the 22 current
`OPENAI-DOC-*` records before publishing the freeze.

| Field or behavior | Official source | Classification ceiling | Permitted claim |
|---|---|---|---|
| App-server model catalog | [`model/list`](https://learn.chatgpt.com/docs/app-server#list-models-modellist) | `stable_native` only for fields explicitly documented on the pinned surface | Observed model entries and documented selector metadata within the collection completeness rule |
| Hidden catalog entries | Same `model/list` section; `includeHidden: true` | `stable_native` for the documented hidden flag and request option | Observed visibility state; never independent candidate admission |
| Supported/default reasoning efforts | Same `model/list` section | `stable_native` when the exact field remains documented | Observed effort options/default for the pinned app-server build; not universal support beyond the source claim |
| Input modalities and other model metadata | Same `model/list` section | Per-field native classification only | Observed documented values; absent values remain typed missing/null |
| Provider capability bounds | [`modelProvider/capabilities/read`](https://learn.chatgpt.com/docs/app-server) | `experimental_native` or `undocumented` until each returned field has field-level authority | Pinned-build observation only for documented fields; no inference from an incomplete published response shape |
| Service reroute event | [`model/rerouted`](https://learn.chatgpt.com/docs/app-server#turn-events) | `conditional` | An observed event proves its `threadId`, `turnId`, `fromModel`, `toModel`, and `reason` only |
| Reroute absence | Same turn-event contract plus pinned telemetry completeness rule | `conditional` | No-reroute claim only when the surface guarantees full capture through terminal state |
| API prompt treatment | [GPT-5.6 prompting guide](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6.md) | API-surface only | Prompt construction facts for API treatment; never Codex agent fields, availability, defaults, telemetry, or exact treatment |
| CLI selector values | No field-level official binding established | `undocumented` unless a current canonical source is added | Retained cross-surface evidence only; can narrow a tuple but cannot create a platform claim |
| Interactive picker values | No field-level official binding established | `undocumented` unless a current canonical source is added | Retained visibility evidence only; can narrow a tuple but cannot create a platform claim |

## Source-Ledger Refresh Rules

1. Read the G56R-001 v3 machine manifest and select exactly the 22 current
   `OPENAI-DOC-*` records. Historical `OSL-*` rows remain historical.
2. Resolve only canonical allowlisted OpenAI domains and record retrieval time,
   canonical locator, body digest, bounded field-level extract, and status.
3. Compare each record with its prior digest and claim bindings. A redirect,
   access failure, withdrawal, conflict, or material field change invalidates
   only the dependent current claims and routes.
4. Do not rewrite a source record merely because an old historical marker is
   absent. Publish a new refresh outcome and successor freeze.
5. Runtime evidence cannot repair an invalidated official claim. The tuple
   remains excluded until current official authority exists.

## Surface Collection Decisions

### Client identity

`client_identity_id` is the digest of canonical JSON containing the reported
client version and an immutable vendor build ID. If the client exposes no build
ID, use the SHA-256 of the resolved executable or application package. Every
surface observation must reference the same digest. A mismatch invalidates the
aggregate rather than an individual tuple because attribution is impossible.

### App-server method

Initialize the pinned server, capture the documented client/server identity,
call `model/list` with hidden entries included, and issue documented provider
capability reads only for discovered provider/model inputs. Record method ID,
fixed inputs, ordered raw response digest, timestamps, and any pagination or
completeness signal. Do not guess a field absent from the published contract.

### CLI and picker methods

Use a clean session with fixed configuration and no mutation. Enumerate the
complete selector view available to the pinned client and record the method,
visibility rules, ordered labels, and evidence digest. A partial, ambiguous, or
irreproducible enumeration is `unknown`. Picker omission of a hidden entry is
consistent only when the picker method proves complete enumeration under its
recorded visibility policy.

### Normalization and disagreements

Join only canonical model IDs and effort tokens admitted by the current ledger.
Retain raw labels. Aliases require a versioned one-to-one mapping backed by
field-level official documentation or a machine-readable identifier from the
same pinned build. Preserve all conflicting values in a disagreement record;
no surface wins. Missing, hidden, or contradictory evidence excludes only its
tuple unless client identity, matrix version, aggregate hash, or key uniqueness
is invalid.

## Telemetry Classification Semantics

| Class | Source requirement | Completeness and claims |
|---|---|---|
| `stable_native` | Field-level current official contract | Claim only an observed value within the declared complete capture |
| `experimental_native` | Officially documented but unstable field | Claim only the observed pinned-build value |
| `derived_from_controlled_configuration` | Hash-bound configuration and launch consumption proof | Claim requested/assigned intent only |
| `conditional` | Documented predicate and capture boundary | Claim presence under the predicate; absence is unknown without completeness |
| `unavailable` | Profile proves no collectable value on the pinned surface | Typed value remains null |
| `not_applicable` | Explicit applicability predicate is false | Typed value remains null |
| `undocumented` | No field-level official authority | Evidence may be retained but supports no platform or treatment claim |

Entries are keyed by `(client_identity_id, surface, field_path)`. Omission means
`undocumented`; classifications never inherit across surfaces.

## Configured-Route and Effective-Treatment Decisions

Approved configured-route proof binds the exact consumed materialization to the
named agent, explicit model/effort, candidate and agent-contract IDs,
instruction/configuration hashes, client identity, controlled overrides, and
launch. It proves requested assignment only and is acceptable only when the
profile permits the path and reroute monitoring is complete.

Effective model or effort requires an observed profile field with official
support and a satisfied completeness rule. `model/rerouted` proves only its
documented event fields. It does not prove effort, named-agent identity, or the
absence of another event. Ambiguous event joins or incomplete capture produce
unknown treatment and tuple-local exclusion.

## Canary and Raw-Evidence Decisions

- One launch per `(snapshot ID, canonical model ID, canonical effort)`.
- 30-second wall timeout and 64 KiB combined stdout/stderr cap; terminate the
  process tree on either bound.
- No retry in a snapshot. An independently proven transient condition requires
  a successor snapshot.
- Only exit zero plus the predeclared sentinel records pinned-environment
  availability. Every closed-taxonomy error records unknown and exclusion.
- `raw_evidence_root` is required, content-addressed, outside the repository,
  and operator-only (`0700` directories, `0600` files). Delete captures 30 days
  after freeze publication while preserving the digest and deletion record.
- Sanitize before commit with a deny-by-default allowlist and deterministic
  fixture-local pseudonyms. Serialize sorted-key compact UTF-8 JSON and hash the
  exact bytes with SHA-256.

## Alternatives Rejected

- **App-server wins disagreements**: rejects the user-selected surface-matrix
  policy and hides pinned-client contradictions.
- **Configured intent equals effective treatment**: would fabricate an
  undocumented effective model or effort.
- **Repeated availability probes**: becomes a live campaign and leaks into
  qualification.
- **Raw responses in Git**: violates the accepted evidence and privacy boundary.
- **Shared cross-vendor prober**: adds abstraction before a second compatible
  implementation exists and risks importing Claude-specific mechanics.
- **Modify the benchmark runner now**: couples capability contracts to G56R-003
  scoring and exceeds the present slice.

## Implementation-Time Evidence Gap

CLI and picker values for the pinned client are intentionally unknown until the
operator collection step runs. That is not a specification gap: the contract
has a deterministic unknown/exclusion outcome and can publish a freeze with no
fabricated eligibility. Any successor observation creates a successor freeze.
