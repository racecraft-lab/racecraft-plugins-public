# Provider contracts: TypeSafe, OpenRouter and Ollama System One

This is a hand-written field matrix, not a byte-for-byte copy of either
publisher's schema. It records what was actually fetched and inspected, so the
per-backend limits and capabilities in the backend rows in
`cmd/evaluate/config.go`, and the universal request shape in
`cmd/evaluate/validation.go`, can be reviewed against a source rather than
against someone's memory.

Re-check this file whenever the integration changes. A drift check can run
without credentials; a change should trigger review rather than a silent
payload rewrite.

## Fetch provenance

| Source | URL | Fetched | Evidence |
|---|---|---|---|
| OpenRouter OpenAPI | `https://openrouter.ai/openapi.json` | 2026-11-14 | sha256 `553a2459a235c73dc4a040b81a2bf99aa47abe74551effd36a884b5c40e70f9e` |
| TypeSafe OpenAPI | `https://api.typesafe.ai/openapi.json` | 2026-11-14 | version 0.2.0, sha256 `3ca93b6e6b9aa8d7820531b78c66ed7a9798b11e6e163ad96b140fb3d75fbcf4` |
| TypeSafe models | `https://docs.typesafe.ai/models.md` | 2026-11-14 | `jev-latest` and `jev-preview` point at `jev-1.14.0` (released 2026-10-14); `jev-1.13.0` still accepted |
| TypeSafe changelog | `https://docs.typesafe.ai/changelog.md` | 2026-11-14 | Jev 1.14: box, better multilingual support; images and long context also on 1.13 |
| OpenRouter Decisions reference | `https://openrouter.ai/docs/api-reference/decisions` | 2026-11-14 | top-level `assets`; `refusal` answer |
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
| Ollama System One schema | `https://docs.ollama.com/api/systemone.md` | 2026-11-14 | sha256 `a6c1b4701110553624ea2bfe045ac1663198240d185f8b93a4c1dde71294f381` |
| Ollama decision guide | `https://docs.ollama.com/capabilities/decision.md` | 2026-11-14 | Cloud limits and confidence semantics; recorded in the research branch's `docs/ai/research/ollama-systemone-field-matrix.md` |

The Ollama columns follow that field matrix, including its distinction between
published contracts, observations and unconfirmed behavior. No live probes are
part of the backend's tests; they intercept the HTTP transport.

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

The 2026-11-14 fetch changes four things. `DecisionsRequest` gains a top-level
`assets` map of `DecisionsImageAsset` (`format`, `data_base64`, optional
`type`), in TypeSafe's shape; this server still sends `image_url` parts (see
Images). A new `DecisionsRefusalAnswer`, `{"type": "refusal"}`, answers a
question the provider declined. `DecisionsNoulAnswer` gains an optional
`confidence`. And `instructions` is no longer required on any question but
box, and now also allows `null`. Choice and score require only `type` and
`criteria`.

## Endpoints

| Backend | Endpoint | Auth | Default model |
|---|---|---|---|
| `typesafe` | `https://api.typesafe.ai/v1/systemone` | `Authorization: Bearer <TYPESAFE_API_KEY>` | `jev-latest` |
| `openrouter` | `https://openrouter.ai/api/alpha/decisions` | `Authorization: Bearer <OPENROUTER_API_KEY>` | `~typesafe/jev-latest` |
| `ollama` | `https://ollama.com/v1/systemone` | `Authorization: Bearer <OLLAMA_API_KEY>` | `clef` |
| `ollama-local` | `http://localhost:11434/v1/systemone` | none; no `Authorization` header | `clef:cloud` |

Ollama is opt-in through the chain. Under `--plugin-defaults`, it discovers
`~/.config/racecraft-jev/ollama.key`, with the same private-file checks and
positional key-file overrides as the other backends. `call --check` reports an
unusable key with exit 4 without HTTP. A server drops that hop at startup.

`ollama-local` always loads without a key and ignores key-file settings. Its
`call --check` verdict is usable (`none` / `ok`), without contacting the daemon.
The operator signs the daemon in; the plugin never signs in or pulls models.
The 2026-11-14 research field matrix records that cloud models need no pull.
It identifies 0.40.5 as the code-supported minimum daemon version and 0.40.6
as the safe floor matching both documentation pages. A daemon 401 means sign
in again; a `signin_url` may be present, while the real upstream body for an
unlinked device remains unconfirmed.

The OpenAPI document lists a `servers` base of `https://openrouter.ai/api/v1`,
but the Decisions path key is `/api/alpha/decisions`, absolute from the host
root. The full URL is therefore `https://openrouter.ai/api/alpha/decisions`, not
`.../api/v1/api/alpha/decisions`. This is an alpha path and may move.

None of these endpoints is a chat-completions endpoint. Requests carry `model`,
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

| Field | TypeSafe accepts | OpenRouter accepts | Ollama accepts | `ollama-local` |
|---|---|---|---|---|
| `instructions` (noul, choice, score, box) | string, object, array, null | string, object, array, null (required on box only) | required for noul, choice and score; string, object or array; no box | same as `ollama` |
| choice `criteria` values | string, object, array, null | string, object, array, **null** | documented string or null; object values accepted in research probes | same as `ollama` |
| score `criteria` entries | string, object, array, null | string, object, array (`minItems: 1`; no null) | documented strings; object levels accepted in research probes | same as `ollama` |
| noul `criteria.true` / `.false` | string, object, array, null | string, object, array; when `criteria` is present both keys are required (no null) | optional criteria; when given, true and false string descriptions | same as `ollama` |

Ollama's structured criteria capability follows the 2026-11-14 observations
for choice and score, beyond the published string schema. The local validator
continues to require non-blank instructions and complete noul criteria.

| Per-hop limit | TypeSafe | OpenRouter | Ollama | `ollama-local` |
|---|---|---|---|---|
| Question types | noul, choice, score, box | noul, choice, score, box | noul, choice, score | same as `ollama` |
| Questions | no local count cap | no local count cap | 64 | same as `ollama` |
| Choice options | 1–255 | 1–255 | 2–255 | same as `ollama` |
| Score levels | 2–10 | 2–10 | 2–10 | same as `ollama` |
| Serialized body | 32 MiB | 32 MiB | 13 MiB | same as `ollama` |
| Images in this implementation | operator opt-in | operator opt-in | operator opt-in | same as `ollama` |

Every Ollama per-hop refusal takes a capability route to a later able hop;
with none available it is exit 2 and sends no HTTP request. Ollama has the same
operator image trust as OpenRouter: `JEV_IMAGES=true` is required before any
image is read or sent. Its top-level base64 array accepts at most 4 images,
4 MiB each and 8 MiB total, within the 13 MiB serialized body cap.

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
| `noul` | `type` | optional; if present, `true` and `false` both required |
| `choice` | `type`, `criteria` | required |
| `score` | `type`, `criteria` | required |
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

| Field | TypeSafe | OpenRouter | Ollama | `ollama-local` |
|---|---|---|---|---|
| top-level required | `model`, `answers`, `usage` | `model`, `answers`, `usage` | `model`, `answers`, `usage` | same as `ollama` |
| `usage` | `input_tokens`, `output_tokens` | `input_tokens`, `output_tokens` required; `cost`, `input_tokens_details.cached_tokens` optional | `input_tokens`, `output_tokens` (often zero) | same as `ollama` |
| `id`, `provider`, `annotations` | not present | optional | not present | same as `ollama` |

Answer shapes, with **required** properties in bold:

| Answer | TypeSafe | OpenRouter | Ollama | `ollama-local` |
|---|---|---|---|---|
| `noul` | **`noul`** | **`type`**, **`noul`**; `confidence` optional | **`type`**, **`noul`**; no confidence or probabilities | same as `ollama` |
| `choice` | **`choice`**, **`confidence`**, **`probabilities`** | **`type`**, **`choice`**; `confidence`, `probabilities` optional | **`type`**, **`choice`**, **`confidence`**, **`probabilities`** | same as `ollama` |
| `score` | **`score`**, **`confidence`**, **`legend`**, **`probabilities`** | **`type`**, **`score`**; `confidence`, `legend`, `probabilities` optional | **`type`**, **`score`**, **`confidence`**, **`legend`**, **`probabilities`** | same as `ollama` |
| `box` | **`box`** (`top`, `bottom`, `left`, `right`), **`confidence`** (number or `null`) | **`type`**, **`box`**; `confidence` optional | not supported | same as `ollama` |
| `refusal` | not sent | **`type`** only: the provider declined this question | not documented | same as `ollama` |

Ollama's choice and score confidence is `1 - H(p) / ln(N)`, an entropy
measure, not calibrated correctness. Thresholds tuned for Jev do not transfer.
The existing decoder accepts missing ids and noul confidence without filling
them in, and preserves the original response bytes.

This asymmetry is the single most important response fact for this server:
**OpenRouter may omit `confidence` and `probabilities` where TypeSafe always
sends them.** An absent field is absent. It is never filled in with a default,
an estimate, or a value carried over from another question.

A `noul` answer has no `confidence` field on TypeSafe. OpenRouter's schema
allows an optional one. This server checks it is in 0 to 1 when present and
never asks for one.

A `refusal` answer is passed through as that question's whole answer: the
other questions in the call still answer, and the call does not fail. It
carries no value, and none is filled in. A refusal that also carries a value
(`noul`, `choice`, `score`, `box`, `confidence`, or `probabilities`) is
malformed and fails the call. TypeSafe does not document a refusal; one from
it would be accepted the same way.

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
| `ollama` | none; automatic replay is not documented as safe and may bill again |
| `ollama-local` | none; the same replay policy as cloud direct |

Ollama's endpoint documents 400, 401, 402, 404, 413 and 500, with
`{"error":"<string>"}` bodies. Context overflow was observed as 400.
Endpoint 429 behavior and `Retry-After` on 402, 429 or 5xx remain unconfirmed.
The chain still applies its account-status policy to a received 401, 402,
403, 429 or 5xx; a 404 is a path failure. These are client policy, not claims
that Ollama promises those statuses. Image retention differences remain
unconfirmed as well.

Both Ollama routes bill the same account. Under ADR 0028, an account failure
(401, 402, 403, 429 or other 5xx) skips every later hop on that account, even
across intervening hops on another account. Only failures on the session's own
hop persist those skips; a capability-routed failure skips for that call only.
A refused connection, a 404, or a daemon 502/503 moves on without the account
skip, so cloud direct can still answer. The daemon's 502 is documented in the
research matrix as a failure to reach the cloud; treating daemon 503 the same
way is client policy, not a documented Ollama status guarantee.

Authentication, credit, validation, payload, and not-found failures are never
retried: a replay would fail the same way and bill again. `500` and `502` are
not retried either: neither is documented as transient, and a replayed
inference call bills again.

The OpenAPI document declares no `Retry-After` response header for these
statuses. This server still honours one when a response carries it, in both the
delay-seconds and HTTP-date forms, because doing so is correct HTTP behaviour
regardless of whether the publisher documents it. A valid `Retry-After` is
treated as a minimum wait, never as a cap to negotiate down.

## Request and hop deadlines

`JEV_REQUEST_TIMEOUT` bounds the whole call, including retries (45 s by
default, at most 5 m). `JEV_HOP_TIMEOUT` bounds each hop's attempts and retry
waits (10 s by default, capped at a shorter request budget). An explicit hop
timeout must be a positive duration no greater than the request timeout; an
invalid value fails at start-up.

The last hop that can take this request gets all the time remaining, including
in a one-hop chain. A hop deadline routes only this call onward and leaves the
session where it was. A failure on that later route does not move the original
session. Exhausting the whole request deadline ends the call as a timeout
(provider error, exit 5) without a session-move log. Dial deadlines on a live
call remain unreachable failures.

If a retry cannot finish within the hop deadline, its HTTP status keeps its
meaning for session moves. This rule is provisional pending owner review.

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

An `{"image": "..."}` object whose value names no provided image is ordinary
data, such as `{"image": "hero.jpg"}` in a product record, and is sent as
written. The trade-off: a mistyped marker is not refused on its own. It fails
because its image is then unreferenced, and that error names the object's path
(never its value) so the typo can be found. If the same image is also
referenced correctly somewhere else, a mistyped marker goes through as data.
A top-level `assets` map is rejected on input. So is any hand-written media
part in `state`, `instructions`, or `criteria`, on every request, whether or
not `JEV_IMAGES` is set. Keys and the `type` value are compared trimmed and
case-folded. An object is a media part when any of these holds:

- its `type` is `image_url`, `input_audio`, `video_url`, `input_image`,
  `file`, or `input_file`, whatever its other fields are;
- a payload field (`image_url`, `input_audio`, `video_url`, `file`,
  `file_data`, `file_url`, `file_id`, `image`, or `audio`) holds a `data:`
  URL, or an object with a `data:` URL in one of its fields, whatever the
  `type` says;
- it has no `type` (no non-empty string under a type key) and a payload field
  holds an object.

OpenRouter's multimodal guide documents `image_url` for image models and
`input_audio` and `video_url` for `cloudflare/clef-omni`, and the caller's
`model` passes through, so each is reachable. A plain string such as an image
link, or a typed object that names no part and carries no `data:` URL, is
ordinary state. The rule costs one false positive: an ordinary object whose
`type` is `file` is refused. An unvalidated picture or clip therefore cannot
skip `JEV_IMAGES` or the local checks.

`JEV_IMAGES` gates images and `box`. Unset or `false` leaves both off; `true`
turns both on; any other value is a startup error. The operator sets it,
because the bytes leave the machine and are billed. While it is off, the
server opens no image file and makes no request.

The encoder in `images.go` is the only place that chooses a wire format.
Multipart is TypeSafe's preferred upload and OpenRouter rejects it, so both
backends get base64 JSON.

| | TypeSafe | OpenRouter | Ollama | `ollama-local` |
| --- | --- | --- | --- | --- |
| Where the bytes go | top-level `assets` map, `{type: "image", format, data_base64}`, keyed by a minted `jevimg-` token substituted for the caller's name | an `image_url` part, `data:image/png;base64,...` or `data:image/jpeg;base64,...`, in place of the reference | top-level `images` array of base64 strings, each file once, in sorted image-name order | same as `ollama` |
| Header | `TypeSafe-Danger-Zone-Images: true` on any request with an image or a `box` question | none | none | same as `ollama` |
| What must not be sent | the neutral `images` map | `assets`, `images`, and any TypeSafe danger-zone header. OpenRouter has accepted `assets` since the 2026-11-14 fetch; this server keeps `image_url`, which every Decisions model reads, rather than send two wire formats to one backend | neutral image map, `assets`, data URLs, inline image parts or TypeSafe headers | same as `ollama` |

For Ollama, whole-name string references and `{"image":"name"}` markers in
state, instructions and criteria become `"image 1"`, `"image 2"`, and so on,
matching the sorted array order. Repeated references reuse that position and
never duplicate bytes. Longer strings and object keys remain unchanged, as
with the other encoders. Ollama accepts no `box` questions; those route on.
The existing PNG/JPEG input contract remains; WebP is not enabled by this client.

Ollama allows at most 4 images, 4 MiB per decoded file, 8 MiB of decoded files
in total and 16,000,000 pixels per image, with no separate side-length cap.
Every image refusal routes to a later able hop without moving the session.
The final serialized body, including text and base64, must fit 13 MiB.
Rate-limit behavior and image retention remain unconfirmed.

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
| Images in the request body | each file once, in `assets`, within the 32 MiB body once base64-encoded | every reference carries the whole data URL, so each use counts toward the 32 MiB body |
| Expanded request | 32 MiB, adding the image again for each use | the same 32 MiB, for Jev behind OpenRouter |
| Remote URLs | not accepted by this server | rejected by the provider; this server never sends one |

The expanded-request row follows TypeSafe's limits table (fetched
2026-10-17): every use of a reference adds the image again. TypeSafe counts
each image after it processes it, which can make it larger than the file, and
does not publish that size. The local check counts the file size, so a request
it passes can still be refused by TypeSafe for size.

EXIF orientation is not applied. TypeSafe documents that it does not apply it
either, and rewriting pixels here would make the two backends disagree about
which way is up.

`box` needs Jev 1.14. A model this server knows is 1.13 is rejected locally:
on TypeSafe, `jev-1.13.0` and `jev-1.13`; on OpenRouter, `typesafe/jev-1.13`,
`~typesafe/jev-1.13`, `typesafe/jev-1.13.0`, and `~typesafe/jev-1.13.0`.
`jev-latest`, `jev-preview`, and `jev-1.14.0` on TypeSafe, and
`typesafe/jev-1.14` and `~typesafe/jev-latest` on OpenRouter, are allowed. As
of the 2026-11-14 fetch, TypeSafe's `jev-latest` and `jev-preview` both point
at `jev-1.14.0` (until then `jev-latest` was 1.13 and was rejected here). An id
this list does not name is sent through, so an operator's own model string is
not rewritten into a 404 they did not ask to see. `prepare` fills the backend
default before the check.

### Capability routes and the per-backend gates

The two backends' local gates differ: the side minimum
(280 on TypeSafe, 256 on OpenRouter), and the context budget (64,000 and
32,000 on TypeSafe without `JEV_LONG_CONTEXT`, 262,144 on OpenRouter). The
later hops never run the caller's model, so:

- A box question on the fallback runs on that backend's default, which is
  Jev 1.14 on both: `jev-latest` on TypeSafe, `~typesafe/jev-latest` on
  OpenRouter.
- Universal shape errors are rejected before per-hop limits and capabilities,
  except image-file errors. Image files are read lazily, so a file that cannot
  be read or is not PNG or JPEG is reported only after a hop's earlier checks
  pass; a hop refusal can therefore be reported first. Either way the request
  is a local rejection (exit 2) and nothing is sent. Each hop checks its own limits and image opt-in before any request is sent
  to it. A refusal takes a capability route to the next able hop and leaves
  the session where it is. Images are read at most once across those checks.
- Only a failure on the session's own hop moves the session. A routed call
  that fails on a later hop continues down without moving the session.
- A failure moves the session before the next hop checks the request. If that
  hop cannot take it, this call routes on while the session stays on that hop.
  If no able hop remains, the caller gets the network failure (exit 5), with
  the route reason added. With no network call, no able hop means exit 2.
- Once a session is on the fallback, a local refusal there is still exit 2,
  since no call was made, and its message says the session is on the fallback.

## Jev context budgets

Sources: <https://docs.typesafe.ai/models.md> and
<https://openrouter.ai/docs/guides/community/jev>, both read 2026-10-17.
TypeSafe's long-context header raises both of its budgets. OpenRouter's window
is already the long one, and image requests there already run in that mode on
the far side. No header is sent to OpenRouter.

| Budget | TypeSafe, default | TypeSafe, `JEV_LONG_CONTEXT=true` | OpenRouter | Ollama | `ollama-local` |
| --- | --- | --- | --- | --- | --- |
| Whole request: state plus every question | 64,000 tokens | 262,144 tokens | 262,144 tokens | 65,536 tokens | same as `ollama` |
| State plus the single longest question | 32,000 tokens | 262,144 tokens | 262,144 tokens | 65,536 tokens (whole-input window; no separate larger mode) | same as `ollama` |
| Header | none | `TypeSafe-Danger-Zone-Long-Context: true` on every TypeSafe request while the flag is set, including ones that fit the default window | none | none; `JEV_LONG_CONTEXT` never raises this budget | same as `ollama` |

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
