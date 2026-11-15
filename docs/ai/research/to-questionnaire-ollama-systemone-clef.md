# Ollama Cloud `/v1/systemone` and Clef: open questions

**Purpose:** we are adding Ollama Cloud as a backend for an open-source decision-model plugin. Its retry, fallback and billing logic depends on the answers below. The docs and our tests left them open.

**From:** the Racecraft maintainers of the `typesafe-jev` plugin, **To:** Ollama Cloud support, **How your answers will be used:** they set which statuses the plugin retries or moves to another backend on, and they are cited in our public field matrix. We will quote you as "Ollama support, <date>" unless you ask us not to.

## Context

The plugin sends typed judgment requests (noul, choice, score) to `/v1/systemone`, either through the local daemon (`localhost:11434`, model `clef:cloud`, signed in with `ollama signin`) or straight to `https://ollama.com/v1/systemone` with an API key. We read the System One docs, the OpenAPI, the pricing and privacy pages and the daemon source (v0.40.16). On 2026-11-14 we made 15 small billed calls. Our notes are public: https://github.com/racecraft-lab/racecraft-plugins-public/blob/research/ollama-clef/docs/ai/research/ollama-systemone-field-matrix.md (see "Live probes" and "Still Unconfirmed"). Each question below is something those sources did not settle.

## How to answer

Answer under each `>`. It should take about 20 minutes. Partial answers and "I don't know" are useful: mark anything you are unsure of rather than skipping it. A link to an internal or upcoming doc is a fine answer.

## Rate limits and 429

### Does `/v1/systemone` ever return 429?

_Why this matters: the endpoint's OpenAPI lists no 429, but the general errors page does. We need to know whether to handle it._

>

### Is there a request-rate or token-rate limit for `/v1/systemone`, apart from the concurrency limit?

_Why this matters: the pricing page gives 3 or 10 concurrent requests by plan, but no per-minute figure._

>

### What status and body does a client get when the concurrency queue is full?

_Why this matters: the pricing page says the request "will be rejected" but names no status._

>

### How long can a request wait in the queue before it is rejected?

>

### Does a 429 carry a `Retry-After` header?

>

## Billing and 402

### Does a pay-as-you-go account with no credits get a 402?

_Why this matters: the 402 text mentions a "Free plan" that the pricing page no longer lists._

>

### What is the 402 body, and does it say whether the cause is the plan or the credit balance?

>

### Is a request billed when it is rejected with a 400 (for example a context overflow or a bad score)?

_Why this matters: it decides whether a retry after a 400 can cost money._

>

### Is a request that ends in a 5xx billed, so that a retry could bill twice?

>

## clef-flash and model ids

### Is `clef-flash:cloud` a supported cloud model?

_Why this matters: it answered our calls on 2026-11-14 as its own model, but it has no `cloud` tag, no listing and no price. The v0.40.5 release notes say it is on cloud._

>

### What does `clef-flash` cost on Ollama Cloud?

>

### What is the context window for `clef-flash` on Ollama Cloud?

_Why this matters: the tags page says 256K, the clef-flash readme says 64K, and Cloudflare's hosting says 24,576._

>

### Is `clef:27b` a stable alias of `clef` on the cloud?

_Why this matters: both gave identical answers in our test, and `/api/tags` lists only `clef:27b`._

>

## Errors through the local daemon

### What does the cloud return when the daemon's device key is no longer linked to an account?

_Why this matters: the daemon passes this 401 through unchanged, and we only have test fixtures for its body._

>

### Which 5xx statuses can `/v1/systemone` return, and do they carry `Retry-After`?

>

### With a valid key, what status does a body over 13 MiB get: 413 or 400?

_Why this matters: the docs list both 400 and 413 for size and context errors. A context overflow returned 400 in our test._

>

### Is 400 the intended, stable status for a context overflow?

>

## Data retention for state and images

### Are images in a request handled under the same retention rules as the text `state`?

_Why this matters: the FAQ and privacy policy talk about prompts and responses, not images._

>

### Which is the binding statement: the FAQ's "does not store or log" or the privacy policy's "technical measures designed to minimize retention"?

>

### Do request logs or usage records keep question ids or criteria text?

_Why this matters: question ids are not sent to the model, but they do reach your servers._

>

## Request contract stability

### Is the score-level cap of 10 stable on the cloud?

_Why this matters: the clef-flash library page says "2 to 26 levels" for score, while the OpenAPI, the error message and the clef page say 10. We think the 26 is the choice-option cap and the page is a typo._

>

### Are object values for choice options and score levels supported, or only accepted today?

_Why this matters: the OpenAPI says string or null, but the cloud accepted objects in our test. We will only rely on them if they are supported._

>

### Is rounding probabilities to 4 decimal places a stable behaviour?

>

### Is `keep_alive` safe to send to the cloud, given that it is ignored there?

>

### Does `https://ollama.com/v1/systemone` accept a `Content-Encoding: zstd` body directly?

>

## Anything else?

Is there anything about `/v1/systemone` or Clef on Ollama Cloud that we did not ask, and should know before we ship a backend that retries and falls back on it?

>
