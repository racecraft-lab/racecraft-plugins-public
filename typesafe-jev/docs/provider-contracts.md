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
| OpenRouter OpenAPI | `https://openrouter.ai/openapi.json` | 2026-10-17 | sha256 `e55c500ad16a9a68d2de7c251f5871fa65e3697cf4fe9363820eca4b3fffd484`, 2 694 235 bytes |
| TypeSafe docs index | `https://docs.typesafe.ai/llms.txt` | 2026-09-20 | index of the pages below |
| TypeSafe structure rules | `https://docs.typesafe.ai/primitives/advanced.md` | 2026-09-20 | "Where structure is allowed" table |
| TypeSafe images | `https://docs.typesafe.ai/images.md` | 2026-10-17 | `assets`, the images header, pixel and byte limits |
| TypeSafe box | `https://docs.typesafe.ai/primitives/box.md` | 2026-10-17 | instructions-only question; edges in 0..1 |
| TypeSafe models and long context | `https://docs.typesafe.ai/models.md` | 2026-10-17 | 64k/32k defaults; 262,144 with the long-context header |
| TypeSafe request rules | `https://docs.typesafe.ai/api.md` | 2026-10-17 | score cap of 10; 32 MiB body |
| OpenRouter Jev | `https://openrouter.ai/docs/guides/community/jev` | 2026-10-17 | 262,144-token window; `box` on Jev 1.14 |
| OpenRouter multimodal decisions | `https://openrouter.ai/docs/guides/community/multimodal-decisions` | 2026-10-17 | `image_url` data URLs; pixel and byte limits |
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
2026-09-20 fetch (sha256 `a913f294a303280cb37b3114640d94d4c0197919d88d68a0849e782fda32f3f2`,
2 153 530 bytes) has them as `anyOf` string, object, or array, which is what
TypeSafe has always documented. The request matrix below and the per-backend
validation were both updated to match; see the note under it for what the
change was.

The 2026-10-17 fetch adds `DecisionsBoxQuestion` and `DecisionsBoxAnswer` to
the Decisions discriminator. `DecisionsRequest` still has no top-level `images`
or `assets` field. `DecisionsScoreQuestion.criteria` still sets `minItems: 1`
and no `maxItems`. `DecisionsBoxAnswer` requires `type` and `box`
(`top`, `bottom`, `left`, `right`); `confidence` is optional.

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
| `instructions` (noul, choice, score, box) | string, object, array, null | string, object, array (required; no null) |
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
| `box` | `type`, `instructions` | not accepted; the question locates one target in an image |

`questions` is a map; the `type` property is the discriminator. Question ids are
map keys and are not sent to the model.

### Local policy, not publisher-enforced

These constraints are this fork's, applied so a malformed call fails locally
instead of spending a request. Do not cite them as provider requirements.

- `questions` must be non-empty.
- Instruction strings and criteria description strings must be non-blank.
- A score question needs at least two levels. OpenRouter's schema sets
  `minItems: 1`; a one-level scale is a degenerate question, not a schema error.
- A score question takes at most ten levels. TypeSafe's API page says the API
  accepts up to 10 (fetched 2026-10-17). OpenRouter's schema sets no
  `maxItems`. The cap is applied on both backends so a request cannot pass one
  and fail the fallback.
- A serialized request is capped at 32 MiB, the body limit both publishers
  document. The response is still capped at 16 MiB. One decoded image file is
  capped at 16 MiB, which base64 expands to about 22 MiB of JSON, so the old
  16 MiB request cap rejected an image the backends accept.

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
| `box` | **`box`** (`top`, `bottom`, `left`, `right`), `confidence` when sent | **`type`**, **`box`**; `confidence` optional |

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
- A `box` edge is a fraction of the image, from 0 to 1, measured from the
  top-left. TypeSafe documents `left < right` and `top < bottom`. This server
  requires all four edges and that order. OpenRouter's schema requires the
  four edges and does not require `confidence`.
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

## Images

The tool takes one backend-neutral `images` map. Each entry is a caller-chosen
name with exactly one of an absolute `path` or standard `data_base64` (no
`data:` prefix, no whitespace), and an optional `format` of `png`, `jpg`, or
`jpeg`. A reference is a whole string equal to that name, or an object whose
only field is `{"image": "name"}`, inside `state`, `instructions`, or
`criteria`. A name that merely occurs inside a longer string is not a
reference. Every image must be referenced, and a `box` question must have one.
Raw `image_url` parts and a top-level `assets` map are rejected on input, so
an unvalidated picture cannot skip the local checks.

`JEV_IMAGES` gates images and `box`. Unset or `false` leaves both off; `true`
turns both on; any other value is a startup error. The operator sets it,
because the bytes leave the machine and are billed. While it is off, the
server opens no image file and makes no request.

The encoder in `images.go` is the only place that chooses a wire format.
Multipart is TypeSafe's preferred upload and OpenRouter rejects it, so both
backends get base64 JSON.

| | TypeSafe | OpenRouter |
| --- | --- | --- |
| Where the bytes go | top-level `assets` map, `{type: "image", format, data_base64}`, keyed by a minted `jevimg-` token substituted for the caller's name | an `image_url` part, `data:image/png;base64,...` or `data:image/jpeg;base64,...`, in place of the reference |
| Header | `TypeSafe-Danger-Zone-Images: true` on any request with an image or a `box` question | none |
| What must not be sent | the neutral `images` map | `assets`, `images`, and any TypeSafe danger-zone header. A TypeSafe `assets` map posted here is ignored, the call still returns HTTP 200, and it is still billed |

Asset keys are minted from the caller's name. TypeSafe treats a reference as
plain text and will match a short name inside an ordinary word (`cat` inside
`category`). The minted key is long enough that this does not happen, and it
is re-hashed once if that token already occurs in the text.

Local checks, before any request is billed. Errors name `images.<name>` only
when the name is at most 128 characters, trimmed, and free of newlines. They
never quote a path, base64, or file bytes.

| Limit | TypeSafe | OpenRouter |
| --- | --- | --- |
| Formats | PNG, JPEG. Animated PNG (an `acTL` chunk before `IDAT`) rejected | PNG, JPEG. Same animated-PNG rejection. WebP is a general Decisions type, not a Jev one |
| Decoded file | 16 MiB | 16 MiB |
| Side length, inclusive | 280–1568 px | 256–1568 px |
| Total pixels, inclusive | 78,400–2,458,624 | 78,400–2,458,624 |
| Remote URLs | not accepted by this server | rejected by the provider; this server never sends one |

EXIF orientation is not applied. TypeSafe documents that it does not apply it
either, and rewriting pixels here would make the two backends disagree about
which way is up.

`box` needs Jev 1.14. A model this server knows is 1.13 is rejected locally:
on TypeSafe, `jev-latest`, `jev-1.13.0`, and `jev-1.13` (as of 2026-10-17
`jev-latest` still points at 1.13, while `jev-preview` and `jev-1.14.0` are
1.14); on OpenRouter, `typesafe/jev-1.13`, `~typesafe/jev-1.13`,
`typesafe/jev-1.13.0`, and `~typesafe/jev-1.13.0`. `typesafe/jev-1.14` and
`~typesafe/jev-latest` are allowed. An id this list does not name is sent
through, so an operator's own model string is not rewritten into a 404 they
did not ask to see. `runOn` fills the backend default before the check, so an
omitted model on TypeSafe fails as `jev-latest` rather than being billed.

## Jev context budgets

Sources: <https://docs.typesafe.ai/models.md> and
<https://openrouter.ai/docs/guides/community/jev>, both read 2026-10-17.
TypeSafe's long-context header raises both of its budgets. OpenRouter's window
is already the long one, and image requests there already run in that mode on
the far side. No header is sent to OpenRouter.

| Budget | TypeSafe, default | TypeSafe, `JEV_LONG_CONTEXT=true` | OpenRouter |
| --- | --- | --- | --- |
| Whole request: state plus every question | 64,000 tokens | 262,144 tokens | 262,144 tokens |
| State plus the single longest question | 32,000 tokens | 262,144 tokens | 262,144 tokens |
| Header | none | `TypeSafe-Danger-Zone-Long-Context: true` on every TypeSafe request while the flag is set, including ones that fit the default window | none |

The flag is process-wide, parsed like `JEV_IMAGES`. Leaving it unset is the
right default: TypeSafe documents the long window as slower and less accurate.

Both budgets are enforced locally by `validateBudget`, from an estimate of
four bytes per token of the text. Image bytes live in the `images` map and
are not part of the estimate. No tokenizer ships here, and adding one for a
guardrail would be a poor trade. The ratio under-counts dense input such as
CJK or code, so the estimate errs toward letting a borderline request through
and leaving the provider to judge it. A text-small request can still be
rejected by the provider once image tokens are counted; TypeSafe's image-token
guidance was not published on the 2026-10-17 fetch.

That direction is deliberate. The check exists to turn an opaque response into
a useful message, not to second-guess the backend. Probed on 2026-09-18: a
45,000-token state returned `HTTP 400; the provider rejected the request shape;
check question types and criteria`, which is both billed and misleading, since
the questions were fine and the state was the problem.

Jev also ingests the state once and evaluates every question against it in
parallel, which is why batching costs so little and why the second budget
exists: many small questions can pass the total and still blow the state-plus-
longest one.
