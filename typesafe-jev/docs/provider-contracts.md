# Provider contracts: OpenRouter Decisions and TypeSafe System One

This is a hand-written field matrix, not a byte-for-byte copy of either
publisher's schema. It records what was actually fetched and inspected, so the
per-backend validation in `cmd/evaluate/validation.go` can be reviewed against a
source rather than against someone's memory.

Re-check this file whenever the integration changes. A drift check can run
without credentials; a change should trigger review rather than a silent
payload rewrite.

## Fetch provenance

| Source | URL | Fetched | Evidence |
|---|---|---|---|
| OpenRouter OpenAPI | `https://openrouter.ai/openapi.json` | 2026-09-20 | sha256 `a913f294a303280cb37b3114640d94d4c0197919d88d68a0849e782fda32f3f2`, 2 153 530 bytes |
| TypeSafe docs index | `https://docs.typesafe.ai/llms.txt` | 2026-09-20 | index of the pages below |
| TypeSafe structure rules | `https://docs.typesafe.ai/primitives/advanced.md` | 2026-09-20 | "Where structure is allowed" table |
| TypeSafe score semantics | `https://docs.typesafe.ai/primitives/score.md` | 2026-09-18 | level numbering and score range |
| TypeSafe response envelope | `https://docs.typesafe.ai/sdk/python/api/types/responses.md` | 2026-09-18 | `SystemOneResponse` JSON schema |

The raw documents are kept in the ignored `.artifacts/` directory. Reproduce the
hash with:

```bash
curl --fail --silent --show-error https://openrouter.ai/openapi.json \
  -o .artifacts/openrouter.openapi.json
shasum -a 256 .artifacts/openrouter.openapi.json
```

A hash that no longer matches means OpenRouter republished the document. That is
expected over time; compare the Decisions schemas below before changing code.

**This has already happened once.** The 2026-09-18 fetch recorded Decisions
schemas that typed every instruction and description as a plain string. The
2026-09-20 fetch has them as `anyOf` string, object, or array, which is what
TypeSafe has always documented. The request matrix below and the per-backend
validation were both updated to match; see the note under it for what the
change was.

## Endpoints

| Backend | Endpoint | Auth | Default model |
|---|---|---|---|
| `typesafe` | `https://api.typesafe.ai/v1/systemone` | `Authorization: Bearer <TYPESAFE_API_KEY>` | `jev-latest` |
| `openrouter` | `https://openrouter.ai/api/alpha/decisions` | `Authorization: Bearer <OPENROUTER_API_KEY>` | `~typesafe/jev-latest` |

The OpenAPI document lists a `servers` base of `https://openrouter.ai/api/v1`,
but the Decisions path key is `/api/alpha/decisions`, absolute from the host
root. The full URL is therefore `https://openrouter.ai/api/alpha/decisions`, not
`.../api/v1/api/alpha/decisions`. This is an alpha path and may move.

Neither endpoint is a chat-completions endpoint. Requests carry `model`,
`state`, and `questions`; they never carry `messages`, `max_tokens`, or
`stream`.

## Request: what each backend accepts

`DecisionsRequest` requires `model`, `state`, and `questions`. `state` is a
string, a JSON object, or a JSON array. Optional OpenRouter fields not used by
this server: `provider`, `session_id`, `trace`, `user`.

The backends used to diverge on how much JSON structure a question may carry.
They no longer meaningfully do. TypeSafe's "Where structure is allowed" table
says every field below accepts `string`, `object`, `array`, or `null`.
OpenRouter's Decisions schemas now type the same fields as `anyOf` string,
object, or array, and additionally allow `null` for choice option descriptions.

| Field | TypeSafe accepts | OpenRouter accepts |
|---|---|---|
| `instructions` (all three types) | string, object, array, null | string, object, array (required; no null) |
| choice `criteria` values | string, object, array, null | string, object, array, **null** |
| score `criteria` entries | string, object, array, null | string, object, array (`minItems: 1`; no null) |
| noul `criteria.true` / `.false` | string, object, array, null | string, object, array; when `criteria` is present both keys are required (no null) |

All that survives of the divergence is `null` in the three positions this server
requires a value anyway, so no per-backend rule is left in the validator. The
capability is still carried on `ProviderSpec.StructuredEntries` rather than
assumed, so a backend that re-narrows is one field to flip.

**What changed on 2026-09-20.** `validateEntry` no longer rejects objects and
arrays on OpenRouter, and the separate narrow tool schema that typed
`instructions` as a plain string for that backend was removed: exporting it now
would hide a capability the backend has. Structured instructions and criteria —
the form TypeSafe's own docs and agent skill teach — work on both backends.

Required-ness per OpenRouter's schemas:

| Question type | Required properties | `criteria` |
|---|---|---|
| `noul` | `type`, `instructions` | optional; if present, `true` and `false` both required |
| `choice` | `type`, `instructions`, `criteria` | required |
| `score` | `type`, `instructions`, `criteria` | required |

`questions` is a map; the `type` property is the discriminator. Question ids are
map keys and are not sent to the model.

### Local policy, not publisher-enforced

These constraints are this fork's, applied so a malformed call fails locally
instead of spending a request. Do not cite them as provider requirements.

- `questions` must be non-empty.
- Instruction strings and criteria description strings must be non-blank.
- A score question needs at least two levels. OpenRouter's schema sets
  `minItems: 1`; a one-level scale is a degenerate question, not a schema error.
- A serialized request is capped at 16 MiB.

## Response: what comes back

Both backends return a `model`, a `usage` block, and an `answers` map keyed by
the request's question ids.

| Field | TypeSafe | OpenRouter |
|---|---|---|
| top-level required | `model`, `usage` | `model`, `answers`, `usage` |
| `usage` | `input_tokens`, `output_tokens` | `input_tokens`, `output_tokens` required; `cost` optional |
| `id`, `provider` | not present | optional |

Answer shapes, with **required** properties in bold:

| Answer | TypeSafe | OpenRouter |
|---|---|---|
| `noul` | **`noul`** | **`type`**, **`noul`** |
| `choice` | **`choice`**, **`confidence`**, **`probabilities`** | **`type`**, **`choice`**; `confidence`, `probabilities` optional |
| `score` | **`score`**, **`confidence`**, **`legend`**, **`probabilities`** | **`type`**, **`score`**; `confidence`, `legend`, `probabilities` optional |

This asymmetry is the single most important response fact for this server:
**OpenRouter may omit `confidence` and `probabilities` where TypeSafe always
sends them.** An absent field is absent. It is never filled in with a default,
an estimate, or a value carried over from another question.

A `noul` answer has no `confidence` field on either backend. Asking for one is a
bug, not a provider omission.

### Value ranges

- `noul` is a probability of yes, from 0 to 1.
- `confidence` is from 0 to 1. It measures how concentrated the probability
  distribution is, not whether the answer is correct.
- `probabilities` values are from 0 to 1 and sum to approximately 1.
- `score` is **not** a probability. It is a position on the level number line:
  levels are numbered from 0 by their position in the `criteria` array, so a
  three-level scale returns 0 to 2. The valid range is `0` to
  `len(criteria) - 1`, and the value may fall between levels. Constraining a
  score to 0–1 would reject almost every valid answer.

Unrecognized response fields are preserved and returned to the caller. The
server validates the envelope; it does not rebuild a narrower one.

## Documented error statuses

OpenRouter's Decisions path documents `400`, `401`, `402`, `403`, `404`, `413`,
`429`, `500`, `502`, `503`, `524`, and `529`, each with an
`{"error": {"code", "message"}}` body. `524` (upstream timeout) and `529`
(overloaded) were not in the documented list at the 2026-09-18 fetch and are at
the 2026-09-20 one.

The retry policy in `client.go` is this fork's, not a provider guarantee:

| Backend | Retried |
|---|---|
| `typesafe` | 429, 529 |
| `openrouter` | 429, 503, 524, 529 |

Authentication, credit, validation, payload, and not-found failures are never
retried: a replay would fail the same way and bill again. `500` and `502` are
not retried either: neither is documented as transient, and a replayed
inference call bills again.

The OpenAPI document declares no `Retry-After` response header for these
statuses. This server still honours one when a response carries it, in both the
delay-seconds and HTTP-date forms, because doing so is correct HTTP behaviour
regardless of whether the publisher documents it. A valid `Retry-After` is
treated as a minimum wait, never as a cap to negotiate down.

## Attribution headers

`HTTP-Referer` and `X-OpenRouter-Title` both appear in the fetched OpenAPI
document. This server sends fixed values for the OpenRouter backend only:
the public fork URL and `Racecraft Jev MCP`. Neither is derived from a local
filesystem path or from repository content.

## Jev context budgets

Source: <https://docs.typesafe.ai/models.md>, read 2026-09-20.

| Budget | Limit |
| --- | --- |
| Whole request: state plus every question | 64,000 tokens |
| State plus the single longest question | 32,000 tokens |

Both are enforced locally by `validateBudget`, from an estimate of four bytes
per token. No tokenizer ships here, and adding one for a guardrail would be a
poor trade. The ratio under-counts dense input such as CJK or code, so the
estimate errs toward letting a borderline request through and leaving the
provider to judge it.

That direction is deliberate. The check exists to turn an opaque response into
a useful message, not to second-guess the backend. Probed on 2026-09-18: a
45,000-token state returned `HTTP 400; the provider rejected the request shape;
check question types and criteria`, which is both billed and misleading, since
the questions were fine and the state was the problem.

Jev also ingests the state once and evaluates every question against it in
parallel, which is why batching costs so little and why the second budget
exists: many small questions can pass the total and still blow the state-plus-
longest one.
