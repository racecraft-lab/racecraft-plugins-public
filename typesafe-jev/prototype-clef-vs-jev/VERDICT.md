# Verdict: Clef against Jev on 18 labelled cases (PROTOTYPE)

Question: on the owner's own judgments, do Clef and Jev agree, and which is faster?
Run: 2026-11-14, 90 requests (18 cases x 5 backends), sequential, no retries, no fallback, 0 errors.

**Verdict: Clef stays opt-in. It does not earn first place in the default chain.**
It ties TypeSafe Jev on accuracy (13/18 each), is about half as fast on the fair pair,
and costs about six times as much per token.

| backend | matches label | agrees with typesafe-jev | median ms | p90 ms | cost USD (18 calls) |
|---|---|---|---|---|---|
| typesafe-jev | 13/18 | 18/18 | 194 | 246 | 0.00025 |
| openrouter-jev | 12/18 | 17/18 | 263 | 368 | 0.00052 |
| openrouter-clef-flash | 12/18 | 15/18 | 373 | 535 | 0.00023 |
| ollama-clef (daemon) | 13/18 | 16/18 | 286 | 441 | 0.0015 (estimate) |
| ollama-clef-direct | 13/18 | 16/18 | 412 | 470 | 0.0015 (estimate) |

By question (matches label):

| question | typesafe-jev | ollama-clef | openrouter-clef-flash |
|---|---|---|---|
| pr_ready (7) | 7 | 7 | 6 (draft pr07 scored 0.88) |
| failure_real (5) | 1 | 2 | 1 |
| owner (6) | 5 | 4 | 5 |

Fair speed pairs:
- OpenRouter Jev 263 ms against OpenRouter clef-flash 373 ms: same route, Jev faster.
- TypeSafe Jev 194 ms against Clef direct 412 ms: both open a fresh connection per call.
  `evaluate call --check` start-up measured 6.3 ms median (20 runs, max 7.1 ms), so it
  does not change the result. This timing was taken after the run, by hand; `run.py`
  does not measure it.
- The daemon column (286 ms) is what the plugin would see on this Mac, not a fair pair.

Findings beyond the question:
- `failure_real` fails on every backend: real failures score below 0.5 almost everywhere.
  The question wording or its state is the problem, not the backend. Fix it before any
  backend comparison on that question.
- Clef via the daemon and Clef direct return identical answers; only latency differs.
- Clef cost is an input-token estimate at $0.24/M; the Jev columns report cost.

Limits: 18 cases, labels from repository history by fixed rules, failure set one-sided
(4 real, 1 flaky). Agreement on 18 items is not the ~50-item labelled set a gate needs.
