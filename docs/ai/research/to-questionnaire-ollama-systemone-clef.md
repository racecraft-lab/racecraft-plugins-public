# Ollama Cloud `/v1/systemone` and Clef: open questions

**Purpose:** we are adding Ollama Cloud as a backend for an open-source decision-model plugin. Its retry, fallback and billing logic depends on the answers below. The docs and our tests left them open.

**From:** the Racecraft maintainers of the `typesafe-jev` plugin, **To:** Ollama Cloud support, **How your answers will be used:** they set which statuses the plugin retries or moves to another backend on, and they are cited in our public field matrix. We will quote you as "Ollama support, <date>" unless you ask us not to.

## Context

The plugin sends typed judgment requests (noul, choice, score) to `/v1/systemone`, either through the local daemon (`localhost:11434`, model `clef:cloud`, signed in with `ollama signin`) or straight to `https://ollama.com/v1/systemone` with an API key. We read the System One docs, the OpenAPI, the pricing and privacy pages and the daemon source (v0.40.16). On 2026-11-14 we made 15 small billed calls. Our notes are public: https://github.com/racecraft-lab/racecraft-plugins-public/blob/research/ollama-clef/docs/ai/research/ollama-systemone-field-matrix.md (see "Live probes" and "Still Unconfirmed"). Each question below is something those sources did not settle.

## Answers found without Ollama (2026-11-14)

We had no time to wait for Ollama, so each question below carries the best public answer: Ollama's docs, pages, source and issues, an official client, Cloudflare's docs, and our own probes (field matrix "Live probes"). Each answer says whether it is documented, observed or unknown. An observation is behaviour on one day, not a contract. The questions marked **Unknown** are the ones still worth sending.

## How to answer

Answer under each `>`. It should take about 20 minutes. Partial answers and "I don't know" are useful: mark anything you are unsure of rather than skipping it. A link to an internal or upcoming doc is a fine answer.

## Rate limits and 429

### Does `/v1/systemone` ever return 429?

_Why this matters: the endpoint's OpenAPI lists no 429, but the general errors page does. We need to know whether to handle it._

> **Observed by users, not documented for this endpoint.** `docs.ollama.com/api/errors.md` lists 429 "e.g. when a rate limit is exceeded"; `api/systemone.md` lists no 429. One open issue ([ollama/ollama#19111](https://github.com/ollama/ollama/issues/19111), Pro plan, no Ollama reply) shows `429 Too Many Requests: timed out waiting for a concurrent request slot` after 5m0s on the daemon's `/api/chat`, during a suspected incident. No 429 in our 15 sequential `/v1/systemone` probes. Plan for 429 as "queue timeout".

### Is there a request-rate or token-rate limit for `/v1/systemone`, apart from the concurrency limit?

_Why this matters: the pricing page gives 3 or 10 concurrent requests by plan, but no per-minute figure._

> **Partly answered.** `ollama.com/pricing` lists no per-minute request or token limit and says the session and weekly limits of the old plans no longer apply; usage is monthly credits, with an email at 90% of included usage on paid plans. A page not listing a limit does not prove none exists.

### What status and body does a client get when the concurrency queue is full?

_Why this matters: the pricing page says the request "will be rejected" but names no status._

> **Unknown for `/v1/systemone`.** Pricing says a request that finds the queue full "will be rejected" with no status. The only observed rejection is the 429 "timed out waiting for a concurrent request slot" in #19111, which is a queue timeout, not a full queue.

### How long can a request wait in the queue before it is rejected?

> **Observed by users: about 5 minutes** (#19111, one report). Pricing gives no figure. The designed timeout may differ.

### Does a 429 carry a `Retry-After` header?

> **Unknown.** Neither errors page mentions it, and #19111 captured no headers. The daemon would pass the header through (`server/cloud_proxy.go`). The official `ollama-python` client (0.6.0 to 0.6.3) drops all headers, never reads `Retry-After` and never retries, so callers back off themselves.

## Billing and 402

### Does a pay-as-you-go account with no credits get a 402?

_Why this matters: the 402 text mentions a "Free plan" that the pricing page no longer lists._

> **Unknown.** `api/systemone.md` says 402 means the model "isn't included in the Free plan"; the pricing page no longer lists a Free plan and does not say what happens when credits run out. Only a call from an empty account would settle it.

### What is the 402 body, and does it say whether the cause is the plan or the credit balance?

> **Unknown.** The docs give only an `error` string. Treat any 402 as "this account cannot pay for this backend" and move on.

### Is a request billed when it is rejected with a 400 (for example a context overflow or a bad score)?

_Why this matters: it decides whether a retry after a 400 can cost money._

> **Unknown.** No public source says. Cost is per input token at $0.24 per million, so a rejected tiny request costs at most a fraction of a cent either way, but do not retry a 400 unchanged.

### Is a request that ends in a 5xx billed, so that a retry could bill twice?

> **Unknown.** No public source says. Assume a retry may bill again and cap retries.

## clef-flash and model ids

### Is `clef-flash:cloud` a supported cloud model?

_Why this matters: it answered our calls on 2026-11-14 as its own model, but it has no `cloud` tag, no listing and no price. The v0.40.5 release notes say it is on cloud._

> **Not officially.** It answered our probe on 2026-11-14 as its own model (`"model":"clef-flash"`), but its tags page has five local tags and no cloud tag, while clef's page does. No docs page names it for cloud. Treat it as unsupported and liable to disappear.

### What does `clef-flash` cost on Ollama Cloud?

> **No price published.** Cloudflare Workers AI charges $0.038 per million input tokens for its own hosting; that is not an Ollama price.

### What is the context window for `clef-flash` on Ollama Cloud?

_Why this matters: the tags page says 256K, the clef-flash readme says 64K, and Cloudflare's hosting says 24,576._

> **Unknown.** The local tags say 256K, the readme 64K, Cloudflare 24,576. For `clef`, the cloud tags list 64K and match the observed 65,536 cap, so 256K is the local-weights figure. Which cap applies to `clef-flash:cloud` was not probed.

### Is `clef:27b` a stable alias of `clef` on the cloud?

_Why this matters: both gave identical answers in our test, and `/api/tags` lists only `clef:27b`._

> **An alias today, with no stability promise.** `clef:cloud` and `clef:27b-cloud` share digest `5896d5380b6c` on the tags page and gave identical answers in our probes. Bare `clef:27b` is a local tag (digest `fdd5939e1bd9`, same as `clef:latest`), and through the daemon it gets a local 404. Use `clef:cloud` or `clef`.

## Errors through the local daemon

### What does the cloud return when the daemon's device key is no longer linked to an account?

_Why this matters: the daemon passes this 401 through unchanged, and we only have test fixtures for its body._

> **Unknown.** The direct route with no or a fake key returns `{"error":"Unauthorized"}` (observed). The daemon's own signing failure returns `{"error":"unauthorized","signin_url":...}` (source). The upstream body for an unlinked key was not found in any public source. Handle any 401 as "backend unavailable".

### Which 5xx statuses can `/v1/systemone` return, and do they carry `Retry-After`?

> **Partly answered.** `api/systemone.md` lists 500; `api/errors.md` adds 502 "when a cloud model cannot be reached" (the daemon also makes its own 502). No 503 is documented. `Retry-After` on 5xx is unknown.

### With a valid key, what status does a body over 13 MiB get: 413 or 400?

_Why this matters: the docs list both 400 and 413 for size and context errors. A context overflow returned 400 in our test._

> **Unknown.** The docs list both; without a key the cloud returns 401 before checking size. Treat 400 and 413 alike: a request this backend cannot take.

### Is 400 the intended, stable status for a context overflow?

> **Observed, not promised.** Our probe got 400 `Request requires 80146 tokens; the maximum is 65536`. `api/systemone.md` assigns the case to both 400 and 413, so accept either.

## Data retention for state and images

### Are images in a request handled under the same retention rules as the text `state`?

_Why this matters: the FAQ and privacy policy talk about prompts and responses, not images._

> **Unknown.** No document treats images separately. The FAQ, pricing page and privacy policy speak of prompts and responses.

### Which is the binding statement: the FAQ's "does not store or log" or the privacy policy's "technical measures designed to minimize retention"?

> **The privacy policy.** The Terms (August 2026) incorporate only the Privacy Policy. It says content is processed transiently and "not stored beyond the time required to fulfill the request", and not used for training. The FAQ's zero-retention wording is Ollama's statement but is not incorporated into the Terms.

### Do request logs or usage records keep question ids or criteria text?

_Why this matters: question ids are not sent to the model, but they do reach your servers._

> **Partly answered.** The privacy policy collects account data, usage metadata (app version, request counts), diagnostics, IP address and general location, kept "as needed". It publishes no field list, so whether question ids or criteria reach any log is unknown. Keep secrets and personal data out of ids and criteria.

## Request contract stability

### Is the score-level cap of 10 stable on the cloud?

_Why this matters: the clef-flash library page says "2 to 26 levels" for score, while the OpenAPI, the error message and the clef page say 10. We think the 26 is the choice-option cap and the page is a typo._

> **10 for `clef`, unknown for `clef-flash`.** The OpenAPI, the clef page and the cloud's own 400 (`score criteria must contain 2–10 levels`) say 10. The clef-flash page says 2 to 26 for score and was not probed. Cap score at 10 on every Ollama model.

### Are object values for choice options and score levels supported, or only accepted today?

_Why this matters: the OpenAPI says string or null, but the cloud accepted objects in our test. We will only rely on them if they are supported._

> **Accepted today, not documented.** Our probes got 200 for object option values and object score levels, and the `legend` echoed the object. The OpenAPI says string or null. Do not rely on objects.

### Is rounding probabilities to 4 decimal places a stable behaviour?

> **Observed, not documented.** Every value in our probes had at most 4 decimals; the docs say only that the examples are rounded. Do not compare probabilities for exact equality.

### Is `keep_alive` safe to send to the cloud, given that it is ignored there?

> **Safe today, by observation.** The clef page calls it "Optional, local only"; our probes with `5m`, `0` and an invalid string all got identical 200 answers. Omit it on cloud anyway.

### Does `https://ollama.com/v1/systemone` accept a `Content-Encoding: zstd` body directly?

> **Unknown for direct calls.** The daemon decompresses zstd before forwarding, and that worked in our probe. Send plain JSON to ollama.com.

## Anything else?

Is there anything about `/v1/systemone` or Clef on Ollama Cloud that we did not ask, and should know before we ship a backend that retries and falls back on it?

>
