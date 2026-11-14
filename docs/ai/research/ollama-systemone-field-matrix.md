# Ollama System One: field matrix for `/v1/systemone` and Clef

This is a hand-written field matrix, not a copy of any publisher's schema. It
records what was fetched and read on 2026-11-14, so a future Ollama backend in
`typesafe-jev/cmd/evaluate/` can be reviewed against sources and not against
memory. It follows the shape of `typesafe-jev/docs/provider-contracts.md`, and
its OpenRouter column is taken from that file.

Two routes get their own column in every table:

- **Cloud direct**: `https://ollama.com/v1/systemone`, API key, model `clef`.
- **Local daemon**: `http://localhost:11434/v1/systemone`, model `clef:cloud`,
  account from `ollama signin`. The daemon is a signing proxy to the same cloud
  service. It is not a second implementation.

A claim with no primary source is marked **Unconfirmed**, with the places that
were searched. Blog posts, community skills and search snippets are not
sources here. They were used only to find primary pages.

## Short answers

- **The daemon passes the cloud response through unchanged.** Status code, body
  and non-hop-by-hop headers (so `Retry-After`) are copied as received. It
  rewrites nothing on the way back. 402, 429 and 5xx from the cloud reach the
  client as the cloud sent them.
- **The daemon makes five statuses of its own**: 400, 401, 403, 500, 502. Only
  401 (no usable device key) and 502 (cannot reach ollama.com) matter in
  normal use. See "Daemon route".
- **Daemon down**: no HTTP status. The client sees a refused TCP connection.
- **Signed out**: 401 with a JSON `{"error": ...}` body. The exact body depends
  on where the failure happens. See "Daemon route".
- **`ollama pull clef:cloud` is not needed.** The daemon routes any `:cloud`
  name to ollama.com before it looks for a local model.
- **Minimum daemon**: 0.40.5 by the docs and the git history, 0.40.6 by the
  Clef library page. 0.40.16 (this Mac) meets both.
- **Score levels cap at 10** on every route. 26 is the local choice-option cap.
- **clef-flash is not offered on Ollama Cloud** on 2026-11-14, although the
  0.40.5 release notes say it is.

## Fetch provenance

The first column carries a short id. Source columns in the tables below cite
these ids. Raw copies are in `typesafe-jev/.artifacts/ollama-systemone/`
(ignored by `typesafe-jev/.gitignore`), under the file names shown.

| Source | URL | Fetched | Evidence |
|---|---|---|---|
| `OA` Ollama System One page and OpenAPI | `https://docs.ollama.com/api/systemone.md` | 2026-11-14 | sha256 `a6c1b4701110553624ea2bfe045ac1663198240d185f8b93a4c1dde71294f381`, 14 569 bytes, `docs.ollama.com_api_systemone.md` |
| `OAY` Ollama OpenAPI document | `https://docs.ollama.com/openapi.yaml` | 2026-11-14 | sha256 `d8e08be41dd858c933c32bef5ee8d0c5faf7d7462069a49b368731cfbceaab03`, 87 400 bytes. Only used to look for `429`; no match in `/v1/systemone`. |
| `IDX` Ollama docs index | `https://docs.ollama.com/llms.txt` | 2026-11-14 | sha256 `b3d819a6579e34c72bf6fba1ab7074222bcf9653bfcbef84cc3732d934ded1b7`. System One entry says "v0.35.0 or later, or v0.40.5 or later for cloud models". |
| `DG` Decision guide | `https://docs.ollama.com/capabilities/decision.md` | 2026-11-14 | sha256 `a689c0f28e7eac0abfd9adb82fb556b90d02eea46e3c0d59c674551632a2647f` |
| `ERR` Errors | `https://docs.ollama.com/api/errors.md` | 2026-11-14 | sha256 `53592031243e6b0322d0826606e088ee6f24d2855c237a9768238d24f609ae24` |
| `AUTH` Authentication | `https://docs.ollama.com/api/authentication.md` | 2026-11-14 | sha256 `da3726163578cd296291bde5b1831c7274f63822f5e2690fbaedb52cfd1b463e` |
| `CM` Cloud models | `https://docs.ollama.com/cloud/models.md` | 2026-11-14 | sha256 `abe03e8e0e16f80ae773cd5c54fa17437a3e07b2e687ff7ea1136d8aecd739d4` |
| `CF` Cloud overview | `https://docs.ollama.com/cloud.md` | 2026-11-14 | sha256 `e7d2510ffc30dee1f6403333976ae6a7f7c95c7171df7b5dc4ef098f087a7f08` |
| `FAQ` Cloud FAQ | `https://docs.ollama.com/cloud/faq.md` | 2026-11-14 | sha256 `4906b757e4e9eeee2e2343ff0c6b6fe6d62febad781767b9a1f3ea42f54b3171` |
| `LOC` Local FAQ | `https://docs.ollama.com/faq.md` | 2026-11-14 | sha256 `124066996407a31069900aa6b80bb13d9d7f0ef8619d31b49c63f6fda181a4bb`. Used for the cloud-disable switches. |
| `LC` Library page, clef | `https://ollama.com/library/clef` | 2026-11-14 | sha256 `8200f7c56dc8df3c8982f1cc947967f386f3b900757ca13d209633fa7b853c17`. Tag table plus readme. |
| `LCT` Library tags, clef | `https://ollama.com/library/clef/tags` | 2026-11-14 | sha256 `0903fceb6735f9fb3b15308820ed98c786250288a61d2ed36356cfcf27e96665`. Nine tags, two with `cloud`. |
| `LF` Library page, clef-flash | `https://ollama.com/library/clef-flash` | 2026-11-14 | sha256 `6cd8599a02f1126d5eaa20ffe8ae2ed9dd7779f0d789470658a3b3a8889ff1c6` |
| `LFT` Library tags, clef-flash | `https://ollama.com/library/clef-flash/tags` | 2026-11-14 | sha256 `7214028ecb40ddfba0441feded05dd97e7e1e77a1290fd861d990573b1f01b18`. Five tags, none `cloud`. |
| `SD` Library search, decision models | `https://ollama.com/search?c=decision` | 2026-11-14 | sha256 `63492e6ba3d55505715d92056e49ec9a244d72315554a2a27d704d824d07f68b`. Lists `clef` and `clef-flash`. |
| `SC` Library search, cloud plus "clef" | `https://ollama.com/search?c=cloud&q=clef` | 2026-11-14 | sha256 `77ed559ecf3c1c081ff0df325757fb9f538ec06be2f529cbeb85ab8f335c827a`. Library links in the result: `clef` only. |
| `PR` Pricing | `https://ollama.com/pricing` | 2026-11-14 | sha256 `d2e97afd8e83aee28ed44092b0e1cf7df5584ec1cd6311269f058226a6719de2`. Price table has a `clef` row and no `clef-flash` row. |
| `TAGS` Direct cloud model list | `https://ollama.com/api/tags` | 2026-11-14 | sha256 `0cd50b9fbe7080261dc5ad161370a7e8458415e8b5dd702d872cc07c4b95f335`. 24 models; `clef:27b` (capabilities `decision`, `vision`) and no `clef-flash`. |
| `GH` ollama/ollama source | `https://github.com/ollama/ollama` | 2026-11-14 | `main` at `a5864fcb33969705de3c0ebfedf4b2a16c970bcc`. Blob ids: `server/cloud_proxy.go` `b57c509db242553fe3a9a15c621ebada5a4e8905`, `server/routes.go` `c331bafa8df56f8ca94da2f492d8f0c370296158`, `decision/systemone.go` `091c67a4c947d3cfa2389f68f3b37d2427adbe94`, `decision/clef.go` `f0dd24290fc9ac072aa4e649b5f571b4661bb8f5`, `server/systemone_test.go` `7f31c2f2953614be6adc62129f0f0cef0e675281`. Line numbers below refer to these blobs. |
| `RN` Release notes | `https://github.com/ollama/ollama/releases` | 2026-11-14 | v0.35.0 `4ebfe3294760551520e826bbc61be9973e523eabb778dcb9e0d03c691b867515`; v0.35.1 `d9642682be666bccffd085c22be19db6f6b60c89d3a381695910fc9a9b3f0850`; v0.40.5 `6e0fae23ed122308239d779cb89add523bd1b195e4e4013630ebf2b57c1ccc55`; v0.40.6 `f79702a54d1854e4815f5338da1a67f73d7a1b72b45d11665049a661e77f51c5`. Latest stable is v0.40.16 (2026-11-09); v0.40.17-rc0 is a pre-release. |
| `PRS` Pull requests | `https://github.com/ollama/ollama/pull/18969`, `.../pull/19036` | 2026-11-14 | #18969 "Introduce clef and clef flash on cloud", merged 2026-10-14, changed `server/routes.go` (+1 line) and `server/systemone_test.go`. #19036 "Launch clef in Ollama's cloud", merged 2026-10-15, changed only `docs/`. `compare` shows the #18969 merge commit is in v0.40.5 and not in v0.40.4. |
| `CFM` Cloudflare model pages | `https://developers.cloudflare.com/workers-ai/models/clef/index.md`, `.../clef-flash/index.md` | 2026-11-14 | sha256 `9512dfa3857d378d9d0d579e3b6c013daebb32d7d1d6df6b6354f6c0539df0c3` (clef), `6203f680e7ee670b2d2968e2af24789835863254a470504edea0e668bc114e03` (clef-flash) |
| `CFS` Cloudflare input schema | `https://developers.cloudflare.com/workers-ai/models/clef/schema-input.json` | 2026-11-14 | sha256 `9f6014fdb6f1d3cc32e1f8d01262b9f137743f0590402940c28f8a45114cb683`; byte-identical for `clef-flash` |
| `OR` OpenRouter Decisions reference | `https://openrouter.ai/docs/api-reference/decisions` | 2026-11-14 | sha256 `e8842e794b02b6eb982a3659aadc355fc7559bd083e31b289af2ce8928b85267`. Lists `cloudflare/clef-flash` among popular models. No Clef entry for the 27B model. |
| `PC` Existing contracts file | `typesafe-jev/docs/provider-contracts.md` | 2026-11-14 | Source of the OpenRouter column. |

Cloudflare and OpenRouter pages are comparison sources. They describe other
hosts. They are never used for an Ollama fact unless the table row says so.

Local read-only checks on this Mac, 2026-11-14: `ollama --version` reports
0.40.16; `curl -s localhost:11434/api/version` returns `{"version":"0.40.16"}`;
`ollama list` shows four `:cloud` entries and no Clef entry. No sign-in state
was read. No cloud call was made. `ollama signin` and `ollama pull` were not
run.

To reproduce a hash, download the URL with `curl --fail --silent --show-error`
into the file name shown, then run `shasum -a 256` on it. A changed hash means
the publisher edited the page. Compare the tables below before changing code.

## Open points from 2026-11-14

| # | Question | Status | Evidence |
|---|---|---|---|
| 1 | Is clef-flash on Ollama Cloud? | **Contradicted**: not offered today, though announced | `RN` v0.40.5 says "use `clef:cloud` and `clef-flash:cloud`", and `PRS` #18969 is titled "clef and clef flash on cloud". Against that: `LFT` lists five tags and none is `cloud`; `LF` has no cloud badge; `SC` (cloud plus "clef") returns only `clef`; `TAGS` has `clef:27b` and no `clef-flash`; `PR` prices `clef` only; `DG`, `CM` and `OA` name only Clef for cloud. What `clef-flash:cloud` returns upstream is **Unconfirmed**: no billed call was made. The daemon would forward it (`GH` `server/systemone_test.go`, test `TestSystemOneHandlerCloudPassthrough`). |
| 2 | clef-flash context: 64K or 256K? | **Contradicted**: three sources, three numbers | `LFT` tag table: "256K context window" for every tag. `LF` readme: "64K context window". `CFM` (Cloudflare-hosted, not Ollama): 24,576 tokens. The 256K figure is tag metadata for the local weights. The 64K figure is the readme claim. Neither is tied to a loaded window. `OA` says only that "the complete input must fit the loaded context window" locally. For Ollama Cloud the question does not arise, because clef-flash is not offered. |
| 3 | Score levels cap: 10 or 26? | **Confirmed: 10**. The 26 is a different cap | 10: `OA` `maxItems: 10` and answer `maximum: 9`; `DG` "2–10 descriptions"; `LC` "2 to 10 level descriptions"; `GH` `decision/systemone.go` `ValidateLimits` (line 51, `len(levels) > 10`), which `Compile` calls for the `clef` encoding; `CFS` `maxItems: 10`. 26: `GH` `decision/clef.go` line 148 and `DG` "2–26 named options" cap **choice** options locally. `LF` says "2 to 26 levels" for score. That one page is the outlier, and the schema, the code and the sibling page all disagree with it. |
| 4 | Rate limits | **Confirmed** for concurrency, **Unconfirmed** for request rate | `PR`: Pay as you go and Pro 3 concurrent requests; Max and Team 10. Requests over the limit queue, and "if the queue is full, the request will be rejected" with no status or queue size stated. No requests-per-minute or tokens-per-minute figure for `/v1/systemone` appears in `OA`, `DG`, `CM`, `FAQ`, `PR` or `ERR`. Searched: all of those, plus `OAY` for `429` and `Retry-After`. The only documented per-minute limit (10 requests per minute) belongs to the separate usage endpoint, `docs.ollama.com/api/cloud-usage.md`. |
| 5 | Pricing | **Confirmed**: $0.24 per million input tokens | `PR` model table: `clef` input `$0.24`, cached input `-`, output `-`. `DG`: "billed per input token at the listed price". `CFM` lists the same $0.24 for Cloudflare's own hosting. No price exists for clef-flash on Ollama Cloud. Note: `OA` 402 text says "isn't included in the Free plan", and `PR` now shows "Pay as you go" at $0 with per-token billing, not a "Free plan". Whether 402 still fires for an account with no credits is **Unconfirmed**. |
| 6 | Data retention | **Confirmed**: zero data retention | `FAQ`: "Ollama operates with a zero data retention (ZDR) policy"; prompts and responses are processed "transiently", not stored or logged, and never used for training. `PR` privacy answers: "Prompt or response data is never logged or trained on", and hosting partners must have "no logging, no training, and zero data retention". Account and usage metadata are kept; the FAQ says it excludes prompt and response content. The legal text at `https://ollama.com/privacy` was not fetched. |
| 7 | Is 429 ever returned? | **Unconfirmed** for `/v1/systemone` | `OA` lists 400, 401, 402, 404, 413 and 500, and no 429. `ERR` lists 429 for the API in general ("e.g. when a rate limit is exceeded"). `PR` describes queueing and rejection. The daemon forwards any upstream status and `Retry-After` (see below), so a 429 would reach the client unchanged. No source says the System One cloud service sends one. |

## Endpoints and routes

| | Cloud direct | Local daemon | OpenRouter | Source |
|---|---|---|---|---|
| URL | `https://ollama.com/v1/systemone` | `http://localhost:11434/v1/systemone` | `https://openrouter.ai/api/alpha/decisions` | `OA`, `DG`, `PC` |
| Method | `POST`, JSON | `POST`, JSON | `POST`, JSON | `OA` |
| Daemon behavior | n/a | Registered at `GH` `server/routes.go` line 2434 behind `cloudPassthroughMiddleware`. A body whose `model` ends in `:cloud` (or `-cloud` after a tag) is proxied to `https://ollama.com:443/v1/systemone`. Any other model runs locally. | n/a | `GH` |
| Streaming | Not supported: "Returns one JSON response" | same | not applicable | `OA` |
| Base URL override | n/a | `OLLAMA_CLOUD_BASE_URL`; non-loopback hosts are refused in release mode | n/a | `GH` `server/cloud_proxy.go` `resolveCloudProxyBaseURL`, lines 438 to 483 |

The request body for the daemon route must be JSON with a string `model`. If
it is not, the middleware calls the local handler, which answers with a local
400 or 404.

## Authentication

| | Cloud direct | Local daemon | OpenRouter | Source |
|---|---|---|---|---|
| Credential | API key from `https://ollama.com/settings/keys` | None from the client for the local call. The daemon signs the outbound call with its own device key. | `Authorization: Bearer <OPENROUTER_API_KEY>` | `AUTH`, `OA`, `PC` |
| Header | `Authorization: Bearer $OLLAMA_API_KEY` | A client `Authorization` header is overwritten. `signCloudProxyRequest` sets `Authorization` to a signature of `METHOD,URI` plus a `ts` query value, but only when the target host is `ollama.com`. | Bearer | `AUTH`, `GH` `server/cloud_proxy.go` lines 408 to 436 |
| Account link | Key belongs to an account | `ollama signin` links the device public key (`~/.ollama/id_ed25519.pub` on macOS) to the account | n/a | `AUTH`, `FAQ` |
| Key lifetime | "API keys do not expire"; revoke in settings | Device key stays until removed | n/a | `AUTH` |
| Extra headers sent upstream | n/a | `X-Ollama-Client-Version: <daemon version>`; all other client headers except hop-by-hop ones | n/a | `GH` `server/cloud_proxy.go` lines 28 to 57 and 203 to 212 |
| Plan gate | "Cloud models need a paid plan or purchased usage credits" | same | n/a | `OA` |
| Kill switch | n/a | `OLLAMA_NO_CLOUD=1` or `disable_ollama_cloud` in `~/.ollama/server.json` makes the daemon refuse with 403 | n/a | `LOC`, `GH` `internal/cloud/policy.go` |

## Model ids

| Id | Where it is valid | Source |
|---|---|---|
| `clef` | Cloud direct ("Direct API requests use `clef`"). Also the local model name after `ollama pull clef`. | `CM`, `LC` |
| `clef:27b` | Listed by `TAGS` for direct cloud. Whether `/v1/systemone` accepts it directly is **Unconfirmed**; it is the model name the daemon sends for `clef:27b-cloud`. | `TAGS`, `GH` `internal/modelref/modelref.go` `parseSourceSuffix` |
| `clef:cloud` | Local daemon. The daemon strips `:cloud` and sends `clef` upstream. | `DG`, `LC`, `GH` |
| `clef:27b-cloud` | Local daemon, legacy suffix. Sent upstream as `clef:27b`. Listed in `LCT`. | `LCT`, `GH` |
| `clef`, `clef:27b`, `clef:27b-q4_K_M`, and other local tags | Local daemon, local inference, needs `ollama pull`. | `LCT` |
| `clef-flash` | Local only. No cloud tag. | `LFT` |
| `cloudflare/clef-flash` | OpenRouter Decisions. | `OR` |
| `@cf/cloudflare/clef`, `@cf/cloudflare/clef-flash` | Cloudflare Workers AI. Body `model` must be `clef` or `clef-flash`. | `CFM`, `CFS` |

The response `model` is the name the cloud used, so `clef` for a `clef:cloud`
request. The OpenAPI text says "Model name from the request", which is not what
the daemon test shows: it sends `clef-flash:cloud` and expects `clef-flash`
back (`GH` `server/systemone_test.go`).

## Request fields

| Field | Cloud direct | Local daemon (`clef:cloud`) | OpenRouter | Source |
|---|---|---|---|---|
| `model` | Required string, non-blank | Required string. A `:cloud` suffix selects the cloud route. | Required | `OA`, `GH` |
| `state` | Required. String, object or array. Objects and arrays are serialized as JSON text. "Not interpreted as chat messages or multimodal input". Must be non-blank. | same, passed through untouched | Required string, object or array | `OA`, `PC` |
| `images` | Optional array of base64 strings. See "Images". | same | Not a request field; media goes in `state` parts, and top-level `assets` since 2026-11-14 | `OA`, `PC` |
| `questions` | Required map, 1 to 64 entries. Names up to 100 characters of ASCII letters, digits, `_`, `.`, `-`. | same limits, enforced by the cloud, not the daemon | Required map. Ids not sent to the model. | `OA`, `DG`, `PC` |
| `keep_alive` | Accepted by the schema (string or number). The Clef page says "Optional, local only". Effect on cloud is **Unconfirmed**. | Forwarded untouched | Not applicable | `OA`, `LC` |
| `stream`, `messages`, `max_tokens`, tools | Not supported ("streaming, video, tools, and generation controls are not supported") | same | not applicable | `OA` |
| Unknown top-level fields | Accepted or rejected: **Unconfirmed**. The OpenAPI sets no `additionalProperties` on the request. | Forwarded untouched | n/a | `OA` |
| `Content-Encoding: zstd` body | **Unconfirmed** | Decompressed by the daemon, capped at 20 MiB, then forwarded as plain JSON. A bad stream gives a local 400. | n/a | `GH` `server/cloud_proxy.go` lines 81 to 92 |

### Question objects

| Field | Cloud direct | Local daemon | OpenRouter | Source |
|---|---|---|---|---|
| `type` | `choice`, `noul` or `score`. No `box`. | same | `noul`, `choice`, `score`, `box` | `OA`, `PC` |
| `instructions` | Required on all three types. String, or an object or array serialized as JSON text. | Same as cloud direct. A local (non-cloud) Clef run accepts a missing `instructions` and uses the question name instead; that is not a cloud rule. | Optional (and nullable) except on `box` | `OA`, `GH` `decision/clef.go` `clefField`, `PC` |
| `choice.criteria` | Object, 2 to 255 keys, keys non-blank. Values `string` or `null`. | Same as cloud direct | Map with string, object, array or `null` values | `OA`, `LC`, `PC` |
| `noul.criteria` | Optional. Keys `true` and `false` only, string values, no other keys. | Same as cloud direct | Optional; if present both keys required | `OA`, `PC` |
| `score.criteria` | Array of strings, 2 to 10 items, lowest first | Same as cloud direct | Array, `minItems: 1`, no `maxItems` | `OA`, `PC` |
| Structured (object or array) criteria values | Documented as `string` or `null` only. **Unconfirmed** whether the cloud accepts objects. Cloudflare's own Clef schema allows string, object or array (`CFS`). | The daemon does not check; the cloud decides | Allowed | `OA`, `CFS`, `PC` |

The local Clef encoder (`GH` `decision/clef.go`, `clefValue`) accepts any JSON
value as a criteria description. The local generic encoder rejects objects with
"choice criteria must map option keys to descriptions or null"
(`decision/systemone.go` line 261). So local Clef and the OpenAPI text disagree
about object criteria. This is the row that decides whether a future
`StructuredEntries`-style flag for Ollama would be true or false. It stays
**Unconfirmed** for cloud until a billed probe settles it.

## Response: what comes back

| Field | Cloud direct | Local daemon | OpenRouter | Source |
|---|---|---|---|---|
| Top level, required | `model`, `answers`, `usage` | Same body as cloud direct, byte for byte | `model`, `answers`, `usage` | `OA`, `GH` `server/cloud_proxy.go` lines 246 to 256 |
| `id`, `provider`, `annotations` | Not present | Not present | Optional | `OA`, `PC` |
| Local-only top level `prompt_eval_cached_count` | Not in the cloud schema. **Unconfirmed** for cloud. | The local handler's response type has an optional `prompt_eval_cached_count` (`GH` `decision/types.go`). A proxied cloud call carries whatever the cloud sends. | n/a | `GH` |
| Content type | JSON | JSON, header copied from upstream | JSON | `OA`, `GH` |

Answer shapes. **Required** properties in bold.

| Answer | Cloud direct and daemon | OpenRouter | Source |
|---|---|---|---|
| `noul` | **`type`**, **`noul`** (number 0 to 1). No `confidence`, no `probabilities`. | **`type`**, **`noul`**; `confidence` optional | `OA`, `PC` |
| `choice` | **`type`**, **`choice`**, **`probabilities`**, **`confidence`** | **`type`**, **`choice`**; `confidence`, `probabilities` optional | `OA`, `PC` |
| `score` | **`type`**, **`score`**, **`legend`**, **`probabilities`**, **`confidence`** | **`type`**, **`score`**; the rest optional | `OA`, `PC` |
| `box`, `refusal` | Not sent | Both exist | `OA`, `PC` |

Value ranges and rules:

| Item | Ollama (both routes) | Source |
|---|---|---|
| `probabilities` | Values 0 to 1, "normalized over the supplied candidates, summing to 1 subject to floating-point precision". Choice keys are the option keys. Score keys are zero-based indices as strings. | `OA` |
| `confidence` | 0 to 1. `1 - H(p) / ln(N)`, entropy over the candidates. "Not calibrated correctness". Zero means uniform. | `OA`, `DG` |
| `score` | Probability-weighted zero-based index, "not rounded to a level or normalized to 0–1". Schema maximum 9. | `OA` |
| `legend` | Index strings mapped to the criterion text | `OA` |
| Ties | Choice follows the model's option order | `OA`, `LC` |
| Rounding | The docs say only that the **examples** are rounded to four decimals. Server rounding is **Unconfirmed**. | `OA` |
| Unrecognized fields | None documented | `OA` |

OpenRouter's Jev and Jev-style answers use a different `confidence` formula,
so a threshold tuned on one does not carry over. See `PC`.

## Usage

| Field | Cloud direct and daemon | OpenRouter | Source |
|---|---|---|---|
| `usage.input_tokens` | Required integer. "Total evaluated input tokens, including image positions. Shared context is counted again when the model scores questions separately." | Required | `OA`, `PC` |
| `usage.output_tokens` | Required integer. "Tokens generated internally for scoring ... May exceed the question count". Clef examples show `0`. | Required | `OA`, `LC` |
| `cost`, cached-token detail | Not in the schema | Optional | `OA`, `PC` |
| Billing basis | Input tokens at $0.24 per million; no output or cached price listed | Per model; `cost` is reported | `PR`, `OR` |

## Images

| | Cloud direct | Local daemon | OpenRouter | Source |
|---|---|---|---|---|
| Where | Top-level `images` array | same | `image_url` parts in `state`, or top-level `assets` | `OA`, `PC` |
| Encoding | Base64 string per image. "URLs and data URLs are not supported". | same | Data URL in a part | `OA`, `DG` |
| Formats | PNG, JPEG, WebP | same | PNG, JPEG for Jev | `DG`, `LC`, `PC` |
| Count and size | Up to 4 images; each at most 4 MiB and 16 megapixels; 8 MiB in total | same, enforced by the cloud | 16 MiB file, 256 or 280 to 1568 px sides (Jev) | `OA`, `DG`, `PC` |
| Reference from `state` | None. Images are shared by all questions, in request order. | same | Part position | `OA` |
| Audio, video | Models with audio input also accept WAV clips in `images`. Clef is documented for text, JSON and images only. The Ollama server rejects video. | same | Model dependent | `OA`, `LC`, `GH` `decision/systemone.go` line 41 |
| Needs vision model | Yes. Clef is vision-capable. | same | n/a | `OA`, `TAGS` |

## Limits and context budgets

| Limit | Cloud direct | Local daemon (`clef:cloud`) | Source |
|---|---|---|---|
| Request body | 13 MiB | Cloud's 13 MiB. The daemon's local caps of 32 MiB and 64 KiB text do **not** apply on the cloud route: the middleware proxies and stops before the local handler runs. | `OA`, `DG`, `GH` `server/cloud_proxy.go` lines 74 to 137 |
| Local text and schema cap | not applicable | 64 KiB for local models (1 MiB for some renderers); local only | `OA`, `GH` `server/routes.go` |
| Questions per request | 1 to 64 | same | `OA` |
| Choice options | 2 to 255 | same | `OA`, `LC` ("up to 255 in the cloud") |
| Score levels | 2 to 10 | same | `OA`, `DG` |
| Context window | 65,536 tokens, input never truncated | same | `DG`, `LC`, `OA` |
| Over-window behavior | Rejected, not truncated. Status is **Unconfirmed**: `OA` assigns the case to both 400 ("exceeds ... a cloud model's token limit") and 413 ("exceeds ... the model's context window"). | same | `OA` |
| Local model context | Loaded window (tag metadata says 256K) | same, but not used on the cloud route | `LCT`, `OA` |
| Concurrency | 3 (Pay as you go, Pro) or 10 (Max, Team); queued, then rejected | same account limits | `PR` |
| Daemon request timeout | not applicable | None. The daemon calls ollama.com with `http.DefaultClient` and has an open TODO for timeouts. A client must set its own. | `GH` `server/cloud_proxy.go` lines 223 to 226 |

For comparison, Cloudflare Workers AI truncates a long text `state` to fit,
where Ollama rejects (`CFM`). Cloudflare's context window is 65,536 for Clef
and 24,576 for clef-flash.

## Documented error statuses

Body shape for Ollama errors is `{"error": "<string>"}` (`ErrorResponse` in
`OA`), not OpenRouter's `{"error": {"code", "message"}}`.

| Status | Cloud direct, per `OA` | Local daemon | Source |
|---|---|---|---|
| 400 | Invalid request, unsupported model or runner, or a prompt over the context or token limit | Cloud's 400 passes through. The daemon adds its own 400 for an unreadable body, a bad zstd stream, or invalid JSON in the model rewrite. | `OA`, `GH` |
| 401 | "A cloud model was requested without signing in, or with an invalid API key." | Cloud's 401 passes through. The daemon adds its own 401 when it cannot sign (below). | `OA`, `GH` |
| 402 | "The cloud model isn't included in the Free plan. Add usage credits or upgrade. Also returned when a payment fails." | Passes through | `OA`, `GH` |
| 403 | Not listed | Daemon only: cloud disabled, body `{"error":"ollama cloud is disabled: remote model is unavailable"}` | `GH` `internal/cloud/policy.go`, `server/routes.go` line 60 |
| 404 | Model not found | Passes through. A bare `clef` (no `:cloud`) is a local model, so a daemon 404 means "not pulled". | `OA` |
| 413 | Request over 13 MiB or the context window | Passes through | `OA` |
| 429 | Not listed for this endpoint. Listed generally in `ERR`. | Passes through, with `Retry-After`, if the cloud sends one | `ERR`, `GH` test `TestCloudResponsesPreservesUpstreamResponses` |
| 500 | Model loading, rendering or scoring failed | Passes through. The daemon adds its own 500 only when it cannot build the request. | `OA`, `GH` |
| 502 | Not listed for this endpoint. `ERR`: "e.g. when a cloud model cannot be reached". | Daemon only: it could not reach ollama.com; body is the Go transport error text | `ERR`, `GH` lines 226 to 230 |
| 503, 504, 524, 529 | Not documented | Pass through if the cloud sends them | `OA`, `GH` |

Whether a cloud error carries `Retry-After` is **Unconfirmed**. `OAY` declares
the header on two other endpoints and not on `/v1/systemone`.

## Daemon route: what the proxy does

Source: `GH` `server/cloud_proxy.go` at the pinned blob, unless noted.

**Pass-through.** After the upstream call, `proxyCloudRequestWithPath` copies
the response headers (minus hop-by-hop ones), sets `c.Status(resp.StatusCode)`,
and streams the body with `copyProxyResponseBody` (lines 238 to 256). It reads
no body and rewrites nothing. A 402, 429 or 5xx therefore reaches the client
with the cloud's status and text. The preservation tests in
`server/routes_cloud_test.go` (`TestCloudResponsesPreservesUpstreamResponses`:
401, 403, 429 with `Retry-After`, and a 200 body) run on `/v1/responses`, not
on `/v1/systemone`. They exercise the same function. The System One test
covers only the 200 path.

**What the daemon rewrites on the way out:**

- the body `model`: `clef:cloud` becomes `clef`, `clef:27b-cloud` becomes
  `clef:27b` (`replaceJSONModelField`, `parseSourceSuffix`);
- `Authorization`: replaced by a device signature, with a `ts` query value;
- `X-Ollama-Client-Version`: added;
- the JSON is re-encoded without HTML escaping (`marshalNoHTMLEscape`), so a
  body can differ in whitespace and key order from the client's.

**Statuses the daemon creates itself:**

| Status | Cause | Body |
|---|---|---|
| 400 | Body unreadable, zstd stream bad, or model rewrite failed | `{"error": "<text>"}` |
| 401 | Local signing failed (`auth.Sign` returned an error, for example no device key) | `{"error":"unauthorized","signin_url":"https://ollama.com/connect?name=<host>&key=<public key>"}`; `signin_url` is left out when the public key cannot be read |
| 403 | Cloud disabled by env or config | `{"error":"ollama cloud is disabled: remote model is unavailable"}` |
| 500 | Request or URL could not be built | `{"error": "<text>"}` |
| 502 | `http.DefaultClient.Do` failed: DNS, TLS, connection reset, or no network | `{"error": "<Go error text>"}` |

**Daemon down.** The client gets no HTTP response. A TCP connect to a closed
local port ends in "connection refused": `curl` exits 7. This was observed on
an unused port (127.0.0.1, 11999), not on a stopped daemon. A stopped daemon
on 11434 behaves the same at the TCP layer, but that was not tested. Do not
confuse it with a 502, which means the daemon is up and ollama.com is not
reachable.

**Signed out.** Two cases give two bodies, both 401:

1. The daemon cannot sign: the local 401 above, with `signin_url`.
2. The daemon signs, but the device key is not linked to an account. The
   request is forwarded and ollama.com answers. The daemon copies that 401
   and its body unchanged. `OA` says "Through a local server, the response
   includes a `signin_url`". The daemon's own tests use
   `{"error":"unauthorized","signin_url":"https://ollama.com/connect?key=..."}`
   as an example upstream body, but that is a test fixture. The real upstream
   body is **Unconfirmed**: no unsigned or unlinked call was made. Searched:
   `OA`, `AUTH`, `ERR`, `GH` tests.

A client should treat any 401 from this route as "sign in again", and read
`signin_url` only when present.

**Does `clef:cloud` need `ollama pull`?** No. The middleware runs before any
local model lookup, and `parseAndValidateModelRef` only parses the name. The
System One test sends `clef-flash:cloud` to a daemon whose model directory is
empty and gets 200. `CM` agrees: "Cloud models do not need to be downloaded."
`ollama list` here shows other `:cloud` entries. Those are listing stubs and
the route does not consult them.

**Minimum daemon version.**

| Source | Says |
|---|---|
| `OA`, `IDX`, `DG` | v0.35.0 for System One, v0.40.5 for cloud models |
| `LC` readme | "To use Clef in Ollama's cloud, use Ollama 0.40.6 or later"; Clef itself needs 0.35.1 |
| `RN` v0.35.1 | First release with Clef and image input |
| `RN` v0.40.5 | "Decision models are now available on cloud" |
| `PRS` | The routing change (#18969) is in v0.40.5. #19036 landed in the 0.40.6 cycle and changed only docs. |

The code supports 0.40.5. The 0.40.6 on the library page is the docs-only
change. Use 0.40.6 as a safe floor if you want to match both pages. This Mac
runs 0.40.16, which is the latest stable release and above both numbers.

## Notes for a validator

These follow from the rows above. They are not decisions.

- Do not reuse the OpenRouter or TypeSafe answer parser for `noul`: Ollama
  sends no `confidence` and no `probabilities` on it.
- Ollama has no `box` and no `refusal`.
- `confidence` is an entropy measure, so it is on a different scale from Jev's.
- The daemon route needs a client-side timeout and a client-side check that
  the body is within the cloud's limits, because the daemon enforces none.
- Treat 401, 402 and 403 as non-retryable. A daemon 502 means ollama.com was
  unreachable.
- Retrying 429, 502 or other 5xx is a policy choice. Ollama documents none of
  them as safe to retry, and a replayed call may bill again.

## Still Unconfirmed

| Item | Where it was searched |
|---|---|
| Upstream response to `clef-flash:cloud` | Not called. `DG`, `CM`, `OA`, `LFT`, `TAGS`, `PR`, `SC`. |
| Real body of an upstream 401 for an unlinked device key | `OA`, `AUTH`, `ERR`; daemon tests give fixtures only. |
| Status for context overflow (400 or 413) | `OA` states both. |
| Cloud acceptance of object or array criteria | `OA` says string or null. `CFS` allows more. Local Clef code accepts any JSON. |
| Server-side rounding of `probabilities` and `confidence` | `OA` rounds examples only. |
| `Retry-After` on System One errors | `OAY`, `OA`. |
| Request-rate limit for `/v1/systemone` | `PR`, `FAQ`, `CM`, `OA`, `ERR`. |
| Whether 402 still applies to a pay-as-you-go account with no credits | `OA` text names a "Free plan" that `PR` no longer lists. |
| Direct acceptance of `clef:27b` | `TAGS` lists it; `CM` and `DG` say `clef`. |
| `keep_alive` effect on cloud | `LC` says "local only"; `OA` accepts the field. |
| Whether the cloud accepts `Content-Encoding: zstd` | Not documented. |
| Privacy policy text | `https://ollama.com/privacy` was not fetched. |
