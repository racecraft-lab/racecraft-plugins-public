# Decision-model skills landscape: Clef, Jev, OpenRouter Decisions, Ollama System One

Survey date: 2026-11-14. Scope: published plugins and agent skills for Clef or
for decision models in general. The aim is a list of ideas the
`typed-judgments` skill
(`typesafe-jev/plugin/shared-skills/typed-judgments/SKILL.md`) could borrow.

Rule used throughout: community skills are leads, never sources of API facts.
Where a skill states an API fact, it is listed under "Claims to verify" with
the file 1 verdict. File 1 is
`docs/ai/research/ollama-systemone-field-matrix.md`.

## Short answer

- **The universe is large and mostly Jev-only.** Search surfaced 1 182
  distinct repositories. Most of them only call Jev. Clef-specific skills and
  plugins number a few dozen, and nearly all are under six weeks old.
- **No vendor ships a Clef skill.** `cloudflare/skills` has none (re-checked
  2026-11-14). The vendor-published decision skills are TypeSafe's, OpenRouter's
  and Bespoke Labs' (Nimble).
- **44 entries are tabulated below.** Read depth is stated per entry, from a
  full `SKILL.md` down to a description only. Entries not read are not
  summarized beyond their own description.
- **Top three ideas to borrow**, detail in "Borrow list":
  1. Treat state as untrusted, run deterministic rules before the model, and
     fail closed on gates (never approve on an error).
  2. Write the decision as a truth table in code, with a named action for the
     between-threshold band.
  3. Tune thresholds on a labeled sample of about 50 items, pin the model id,
     and log the model id the response reports.

## Method and limits

This was a GitHub-only search. No web search index was queried, and no package
registry (npm, skills.sh) was searched. "Every skill" is not claimed.

| Query | Kind | GitHub total | Retrieved |
|---|---|---|---|
| `clef` in `SKILL.md` | code | 2 524 (mostly music "clef") | 100 |
| `systemone` in `SKILL.md` | code | 809 | 100 |
| `noul` in `SKILL.md` | code | 3 064 | 100 |
| `"decision model"` in `SKILL.md` | code | 2 276 | 100 |
| `"System One"` in `SKILL.md` | code | 2 196 | 100 |
| `typesafe jev` in `SKILL.md` | code | 3 120 | 100 |
| `clef-flash` in `SKILL.md` | code | 89 | 89 |
| `cloudflare clef decision` in `SKILL.md` | code | 103 | 100 |
| `ollama systemone` in `SKILL.md` | code | 66 | 66 |
| `openrouter decisions` in `SKILL.md` | code | 3 200 | 100 |
| `typesafe-sdk` in `SKILL.md` | code | 104 | 100 |
| `pplx-decider` in `SKILL.md` | code | 18 | 18 |
| `"/v1/systemone"` in `SKILL.md` | code | 539 | 100 |
| `jev` in `SKILL.md` | code | 9 088 | 100 |
| `typesafe` in `marketplace.json` | manifest | 223 | 100 |
| `clef` in `marketplace.json` | manifest | 87 | 87 |
| `systemone` in `plugin.json` | manifest | 46 | 46 |
| `"decision model"` in `plugin.json` | manifest | 170 | 100 |
| `clef decision model skill` | repository | 3 | 3 |
| `systemone skill` | repository | 6 | 6 |
| `typesafe jev plugin` | repository | 217 | 100 |
| `decision model agent skill` | repository | 128 | 100 |
| `noul choice score` | repository | 269 | 100 |
| `clef cloudflare agent` | repository | 18 | 18 |

GitHub's totals are approximate. One call returns at most 100 results, so any
query with a total over 100 was truncated, and the tail was not read.

- **Distinct repositories surfaced**: 1 182 (671 from the `SKILL.md` queries,
  563 from the manifest and repository queries, with overlap).
- **Keyword screen on the 922 `SKILL.md` hits**: each file's opening text was
  matched against System One terms. About 500 repositories match on Jev,
  TypeSafe, System One, noul, Kev, Nimble, Laya, or Clef. The screen has false
  positives (music "clef", the CLEF evaluation conference, "decision model" in
  the product-management sense), so the count is a ceiling, not a census.
- **Marketplaces**: only GitHub-hosted manifests were searched. Catalog
  repositories that appeared in results, such as `aiskillstore/marketplace`,
  `hashgraph-online/awesome-codex-plugins`, `davepoon/buildwithclaude`,
  `majiayu000/claude-skill-registry` and `anthropics/claude-plugins-official`,
  were not inspected one by one. The Clef hits in `aiskillstore/marketplace`
  were a music skill.
- **Excluded**: `nathanweir/clef` (a Common Lisp editor).
- **Inclusion rule for the tables**: the repository holds a skill, plugin or
  mod aimed at Clef, or at decision models in general, and it was read to the
  depth stated. Repositories that only call Jev, or that matched on keywords
  and were not read, are counted above but not listed.
- **Licences** come from the GitHub API. `none` means the API reports no
  licence and the repository root has no licence file (checked by listing the
  root). `NOASSERTION` means a licence file exists that GitHub did not
  recognize. Dates are UTC commit dates on the default branch. The SHA is the
  first 12 characters of the head commit.

## Seed repositories

| Owner | Repo | Licence | Last commit (date, SHA) | What it teaches about Clef and decision models | What `typed-judgments` could borrow |
|---|---|---|---|---|---|
| `cloudflare` | `skills` | Apache-2.0 | 2026-11-10, `cbf893b95422` | The re-check found no Clef skill. A text search of the whole tree for `clef`, `systemone`, `noul`, `decision model` and `typesafe` has no match, and GitHub code search for `clef` in this repo returns 0. The repo has Workers AI reference notes (`skills/cloudflare/references/workers-ai/`) and nothing on decision models. The Workers AI docs sidebar lists a "Cloudflare Skills" entry; its target was not checked. Read: repo tree read for the keywords above; no SKILL.md on the topic exists. | Nothing for typed-judgments. Worth a re-check when Cloudflare ships a skill: it would be the first vendor source for the Workers AI route. |
| `typesafe-ai` | `skills` | MIT | 2026-10-23, `302eea662c54` | One skill, `typesafe-ai` (v0.6.2, "Release v0.6.2"). Jev only, no Clef. Teaches: Jev judges and code decides (write the decision as a truth table); design the state with the "human test"; one atomic judgment per question, avoid "or"; ask the null case as a separate noul; confidence is rarely the gate; 0.7 and 0.3 as starting noul thresholds; probe the live API with a budget and with permission; "yellow flags" for prompt gymnastics; cookbooks. The live docs are the source of truth for limits. Read: SKILL.md in full. | `typed-judgments` already carries the 0.7/0.3 cut-offs, the companion noul and the id-carries-no-meaning rule. Still to borrow: the truth-table framing with a row for the between-threshold band; the human test; "name the confusing case in the criteria"; option names are sent to the model but ids are not; look at score `probabilities` before trusting the position; one noul per statement when several can be true; the yellow-flag list. |
| `lyhu` | `skills-cloudflare-clef` | Apache-2.0 | 2026-10-04, `51a6fe14c3f1` | Two skills. `cloudflare-clef`: a Python standard-library client (`evaluate.py`) for a self-hosted Clef endpoint (default `127.0.0.1:8000/v1/systemone`), with exit codes 0, 1 and 2 and an error JSON that carries `fallback_used`. Fail-closed rule: on an unreachable service or high uncertainty, a high-risk action never auto-approves. Keeps untrusted data in `state` and the question in `instructions`. Local call log with p50 and p95 statistics. `ego-clef`: browser-step decisions that hand back to the main agent below confidence 0.6, after no progress, over a step budget (6, max 20), or in login, payment, delete and download contexts. Benchmarks in `benchmarks/` are author-run. Read: SKILL.md of both skills and README read; benchmark reports skimmed. | The fail-closed contract for gates (an error is never an approval). An explicit hand-back list for risky contexts. Separating untrusted text from the question. A local log of every call and its latency. See "Claims to verify" for the API facts it states, which conflict with file 1 in four places. |
| `aaddrick` | `building-with-decision-models` | MIT | 2026-10-10, `aa9e881ae8fd` | One skill with a large tree: `providers/` (11 files, including `clef.md` and `ollama.md`), `models/` (11 files), `prior-art/` (shape files for gates, control loops, stream filters, rerank, images and more) and `patterns.md`. Packaged for many agents (Claude, Codex, Cursor and others). Teaches: code owns the workflow; 11 rules; act / confirm / escalate bands scaled to the cost of a wrong action; min to combine parts and max to combine "something is wrong" flags; calibration belongs to one model version on one serving stack, so tune every threshold on labeled data; pin a versioned model id and log the id the response reports; a four-step protocol for switching models with a shadow period; known bad fits. Provider files give limits per host, snapshot 2026-10-06. Read: SKILL.md, `providers/clef.md`, `providers/ollama.md`, `models/clef.md` read in full; other files listed only. | Ranked in the borrow list: deterministic check before the model ("the model may make that decision stricter, never looser"); hostile text in state; calibration per model version with a labeled set; the switch-models protocol; the rule that a confidence threshold does not carry over between providers or between a noul and a choice. |
| `sakamoto-sann` | `clef-screen-triage` | MIT | 2026-10-07, `1c75c9bfee6e` | A Codex skill (Japanese README and evaluation record) that classifies a public screenshot as loading, error, content or unclear with Clef-flash on Workers AI, then routes to `continue_visual_check`, `bounded_wait` or `codex`. Prefers a DOM check when one answers the question. Thresholds (probability 0.8, confidence 0.5, top-two margin 0.3) were fixed before a second evaluation set. Caches successes for 24 hours, caps uncached calls at 20 per day, and does not retry. A `--public-image` flag records that the caller approved sending that image out. The evaluation record is honest about limits: 13 of 13 class matches, but only 8 of 13 usable to skip a check, and the author graded it. Read: SKILL.md, README and `references/evaluation.md` read. | Pre-fix thresholds, then test on a separate set. A cumulative wait budget. A per-day call cap and a cache so a loop cannot run up cost. A named route for each outcome, with errors and low confidence routed to the stronger path. An evaluation note that states what was not measured. |

Full SHAs of the five seed heads: `cloudflare/skills`
`cbf893b954222276bf1af57e5f23379231e0efb9`; `typesafe-ai/skills`
`302eea662c54bca6730873fe245bec1d69ebc23d`; `lyhu/skills-cloudflare-clef`
`51a6fe14c3f1a07bf0a65d22e885f9323ad675fe`;
`aaddrick/building-with-decision-models`
`aa9e881ae8fd30fc50cc2387df97c23df2c23176`; `sakamoto-sann/clef-screen-triage`
`1c75c9bfee6ec7c4980a549a509b38f0942a0fce`.

## Clef-specific skills, plugins and mods found by search

| Repo | Licence | Last commit (date, SHA) | Scope | Read | What to borrow |
|---|---|---|---|---|---|
| `peterfriese/system-one-foundation-models` | Apache-2.0 | 2026-11-12, `815b37ec1bd8` | Three skills for Apple Foundation Models in Swift: `clef-foundation-models`, `jev-foundation-models`, `system-one-foundation-models` (confidence routing, retry policy, proxy credentials). | descriptions only | Confidence routing as a typed policy object (idea only, Swift specific). |
| `timmo001/skills` | Apache-2.0 | 2026-11-14, `5e8cde5d362d` | `decision-models`: local decisions through Ollaya or Ollama, or hosted Clef on Workers AI; triage, routing, moderation and prompt-injection screening. | description only | Injection screening as a named use of a noul. |
| `kolbasik/coding-agent-guard` | MIT | 2026-11-12, `9cc4a5d5871f` | Hook-based guard for coding agents. Optionally runs a decision model, including `clef:cloud` through a local Ollama, as one of several injection screens, with a judge beside it. | excerpt of SKILL.md | Shows the daemon route used as a screen. Its pattern: a model score is a signal, and a second judge decides. |
| `luandro/clef` | none | 2026-10-05, `6af3cd4ba536` | A skill for a third-party proxy on a workers.dev host that maps `jev-latest`, `jev-preview` and `jev-1.x.y` to Clef. It states the proxy rejects more than 10 score levels (live check 2026-10-04) and wraps errors in its own envelope. | SKILL.md (first 5 200 of 7 681 characters) | Do not borrow. It routes Jev model names to Clef without telling the caller, and sends state to an unvetted host. The licence is declared in the skill file only. |
| `fitchmultz/pi-agent-skills` | MIT | 2026-11-13, `9e6bdc6a09e0` | `clef` skill for the Pi agent: native tool, three Workers AI ids (`clef`, `clef-flash`, `clef-omni`) with context and price per model. | SKILL.md in full | Check each model's context window and input kinds before sending; treat supplied data as data. |
| `lv-kit/dbml-editor` | none | 2026-11-11, `39e2bd7f02cb` | `cloudflare-clef` skill (in `.agents/` and `.claude/`): bounded decision workflows on Workers AI Clef. "A model probability is evidence for a decision, not authorization." The skill file says MIT; the repo has no licence file. | SKILL.md in full | Short, vendor-neutral wording for "probability is evidence, not authorization". |
| `zhinea/clef-browser` | none | 2026-10-04, `63509589c13e` | Browser agent skill whose judgments run on Workers AI Clef instead of default Jev providers. | description only | none |
| `dwain-barnes/clef-model-router` | Apache-2.0 | 2026-10-04, `04a262b3361b` | Claude Code mod that picks the model and effort per turn with Clef-flash, with a deterministic fallback when Clef is slow, down or out of quota. Reports "not measured yet" on routing quality. | README head | Fail open to a deterministic default for routing, fail closed for gates. Say what is unmeasured. |
| `nicolasmertens/judge-clef` | MIT | 2026-10-07, `8c11a6cfa890` | Claude Code mod: size is measured, and Clef judges only the timing of `/compact`. | README head | Measure what code can measure; ask the model only the judgment part. |
| `chrisns/claude-clef-chrome-ultrafast` | MIT | 2026-10-23, `4b8277f2edb9` | Mod that lets a local Ollama `clef-flash` pick page elements, with hand-back to Claude when unsure. Reports 60 passing runs, 5 jobs, 3 runs each. | README head | Hand-back route when the model is unsure; report cost and turns, not only accuracy. |
| `HighlyLoadedEgo/ClefMCP` | Apache-2.0 | 2026-11-02, `b14e31c10346` | MCP server and dataset classifier for local Clef-flash through llama.cpp, with YAML profiles and explicit review results. | README head | Explicit "review" result as a third outcome. |
| `zachsents/agent-quick-browse` | MIT | 2026-10-10, `f700139a31a5` | CLI, MCP server and Chrome bridge that drive a logged-in Chrome with Clef. | description only | none |
| `GShadow-Dev/clef-safari-browser` | MIT | 2026-10-08, `e1efbf835ddd` | Native Safari agent on Clef with free-tier budget controls. | description only | Budget controls as a first-class setting. |
| `atostivint/hermes-adaptive-effort` | MIT | 2026-11-14, `048d1f11ea7a` | Hermes plugin: a separate scorer (Jev, OpenAI Decisions, OpenRouter, Clef, local Ollama, custom) sets the effort of each request. Off by default; fails open; retries transient statuses (408, 429, 500, 502, 503, 504, 529). Marked pre-release. | README head | Off by default and fails open for a non-critical tuning use. Its retry list is a policy, not an Ollama fact. |
| `Iamsdt/context-triage` | none | 2026-11-01, `0b7fe1fd34bf` | Per old turn, Clef chooses keep, compress or drop. One live smoke test; no benchmarks, and it says so. | README head | State the verification level in the README. |
| `kfatyuip/hermes-clef-compaction` | none | 2026-11-14, `dd31cc638ddb` | Hermes session compaction with Clef, with caching and reuse. | description only | none |
| `dbirks/home-k8s` | none | 2026-11-14, `9ac81aeb51f2` | `clef-omni-nvfp4` skill: quantize, serve, grade and benchmark Clef-Omni on one GPU. Cluster-operations notes, not a decision-API skill. | description only | none |
| `homie-rocks/homie` | Apache-2.0 | 2026-10-31, `ee1bf2a5dc69` | Game-studio skills whose AI guides use Clef on Workers AI by default, or Clef on the player's own machine in development. | descriptions only | none |
| `exoticknight/dsh-system1` | Apache-2.0 | 2026-11-06, `d681f8568b9f` | Provider-neutral plugin unifying Jev, Clef, Drex, Decider, Laya and custom providers. | description only | One adapter interface over many providers. |
| `bladerik/decision-benchmark` | MIT | 2026-11-11, `cedf99f6b0bd` | Agent skill (Slovak README) that checks whether a decision model fits a task and benchmarks every OpenRouter decision model on your own 50 to 100 labeled items: accuracy, accuracy when confident, speed, cost per 1 000 items. | README head | A labeled-sample benchmark as a step before wiring a model in. It matches the repo rule "earn a gate" in `subagents.md` (about 50 items). |
| `Haple/system-one` | NOASSERTION | 2026-10-15, `58301cf26121` | Free course on decision models with 22 lessons and a claim of 14 318 API calls measured by the authors. Also installable as a skill. | README head | Treat its measurements as leads. Its licence file is unrecognized by GitHub. |

## Decision-model skills with a wider scope

| Repo | Licence | Last commit (date, SHA) | Scope | Read | What to borrow |
|---|---|---|---|---|---|
| `OpenRouterTeam/skills` | none | 2026-11-11, `a110aad60723` | OpenRouter Decisions skill (`openrouter-decisions`), vendor-published. Steps: split judgment from computation; pick the primitive; minimal state; questions with inclusion and exclusion rules; pin a model from the live catalog; gate in code with named constants; probe before trusting (clear, ambiguous, no-match, empty, negated and adversarial inputs). Ships `decide.ts --compare` to run one request across models. | SKILL.md in full | Probe-set recipe; code-side facts settle the action before the model runs; every threshold is a named constant with the cost of each mistake written beside it. |
| `bespokelabsai/nimble` | none | 2026-11-09, `b30ec429fcd7` | Vendor plugin for Nimble, a hosted noul/choice/score API (up to 64 questions per request). Not Clef. | description only | Packaging of a vendor plugin with its own skill. |
| `jaredpalmer/kev` | Apache-2.0 | 2026-10-22, `2074cc442562` | Kev open decision models. Skills `kev-deploy` (host a TypeSafe-compatible endpoint on Modal) and `kev-finetune` (fine-tune on your workload, calibrate, deploy). Repo skills also cover its own PR and review rules. | descriptions only | Fine-tune-and-calibrate workflow as a future "when the base model misses" pointer. |
| `aaddrick/building-with-typesafe-jev` | MIT | 2026-10-01, `a46856c9fbc8` | Earlier Jev-only sibling of the decision-models skill. | not read | none |
| `ollaya-dev/ollaya` | Apache-2.0 | 2026-11-06, `d3cf29fa9f68` | `ollaya-decisions` skill for local decision models served by Ollaya, with an MCP `decide` tool. | description only | none beyond the use list |
| `nathanfaucett/agents` | MIT | 2026-11-08, `0525c9530f5f` | `ollama-decision`: quick local decisions through Ollama System One; triggers on "ollama decision", "systemone", "laya". | SKILL.md head | Trigger phrases for a local backend. |
| `alingavriliuc/ollama-decision-skills` | MIT | 2026-10-05, `01ba372de782` | Skills for projects that call Ollama decision models (nimble, tev1) through `/v1/systemone`. | description only | none |
| `digitaldreams/tuhin` | MIT | 2026-10-31, `94477c5beca3` | `system-one` skill with a dated hands-on log of a local Ollama run (nimble, CPU only): per-question state re-scoring, error text for a long state, weak spots (date math, double negatives, quantifiers). | excerpt of SKILL.md | The weak-spot list backs the "keep math, dates and negation in code" rule. Its Ollama facts are claims to verify. |
| `bojansandhaus/jev-decisions-hermes` | MIT | 2026-10-09, `e1a3bf57220c` | Plugin for tool-risk reviews, human-approval recommendations, a local decision journal and learned corrections. | description only | A local decision journal. |
| `svilupp/systemoneprompts` | MIT | 2026-10-18, `8d1410245dc7` | TypeScript package skill for authoring System One decision definitions as TOML, with validation and evaluation. | description only | Keep question text in one file under version control (the TypeSafe skill says the same). |
| `tumf/jev-cli` | MIT | 2026-10-06, `dab9a649cc0b` | `jev` CLI and `jev-mcp` stdio server skill. | description only | none |
| `paulrobello/systemone-mcp-server` | MIT | 2026-10-29, `66b8c02629b2` | MCP server and `ask-systemone` skill: judge files without reading them into context. | description only | Judge a file by path, not by pasting it. |
| `ckorhonen/jev-lint` | MIT | 2026-11-09, `d2eaa7b524aa` | Fuzzy-linter hook for coding agents with two skills: set-up, and an evaluation workflow with labeled dev and holdout payloads. | descriptions only | Labeled dev and holdout split for a judge. |
| `kelasdev/jev-skill-router` | MIT | 2026-10-15, `609e6842c1cc` | OpenCode plugin: Jev picks at most one SKILL.md to inject, with two gated calls. | description only | none |
| `mhiqrambg/systemone-decision-mcp` | MIT | 2026-11-03, `bf7c7eb36502` | MCP server that decides which MCP tools and skills a task needs, with rule-based fallback. | description only | Rule fallback beside the model. |
| `wuyoscar/jev-skill` | MIT | 2026-11-12, `7ca55e1bb7aa` | Multi-skill Jev pack (`jev-act`, `jev-triage`, `jev-eval`, `jev-documents`). Most-starred of the Jev-only skill packs reached. | file names only | none |
| `cobusgreyling/Jev` | MIT | 2026-10-10, `77b65c6b6ded` | Jev skills for routing, fan-out and guardrails. | file names only | none |
| `OpenAF/openaf` | Apache-2.0 | 2026-11-13, `dbe05634afe2` | Scripting tool with an LLM skill that lists Ollama native decisions (local or `:cloud`) among its adapters and does not retry on a failed request. | excerpt | none |

## Claims to verify

These statements come from community skills and are not accepted as facts. The
last column says what file 1 found. File 1 rests on Ollama's docs and source,
and on Cloudflare's published schema for comparison.

| Source skill | Claim | File 1 verdict |
|---|---|---|
| `lyhu/skills-cloudflare-clef` | Choice takes 1 to 64 labels | **Conflicts.** Ollama cloud: 2 to 255. Ollama local: 2 to 26. Cloudflare schema: 2 to 255. |
| `lyhu/skills-cloudflare-clef` | Score takes 1 to 16 levels | **Conflicts.** 2 to 10 on every route (Ollama OpenAPI, Ollama source, Cloudflare schema). |
| `lyhu/skills-cloudflare-clef` | Choice `confidence` is the winner's probability | **Conflicts** for Ollama: `1 - H(p) / ln(N)`, entropy based. Other hosts were not checked. |
| `lyhu/skills-cloudflare-clef` | Score `legend` is an array | **Conflicts.** Ollama documents an object keyed by zero-based index strings. |
| `lyhu/skills-cloudflare-clef` | Noul has no `confidence` | **Agrees** for Ollama. |
| `aaddrick/building-with-decision-models` | Ollama score levels are 2 to 26 ("depends on the model"), snapshot 2026-10-06 | **Conflicts.** The Ollama OpenAPI says 2 to 10 today, and `ValidateLimits` rejects more than 10. The 26 cap is the local choice cap. |
| `aaddrick/building-with-decision-models` | Clef choice limit is 255 and "26 is wrong" | **Partly agrees.** 255 holds for Ollama cloud. Ollama's own pages and code say 2 to 26 for local Clef. |
| `aaddrick/building-with-decision-models` | Ollama text and schema limit is 64 KiB, 32 MiB with images | **Agrees for local models.** It does not apply to the `clef:cloud` daemon route: the daemon proxies before its local checks. |
| `aaddrick/building-with-decision-models` | Ollama returns 400 for `:cloud` tags | **Stale.** That branch exists in the local handler, but the middleware proxies `:cloud` requests first, so a client does not reach it. |
| `aaddrick/building-with-decision-models` | Ollama `confidence` is `1 - H/ln N` | **Agrees.** |
| `aaddrick/building-with-decision-models` | Ollama rounds to four decimals | **Agrees** with the billed probes in the field matrix (`PBB`, observed once on 2026-11-14): every value had at most 4 decimal places. The docs say only that the examples are rounded. |
| `aaddrick/building-with-decision-models` | Clef-flash on Cloudflare has a 65,536-token context and costs $0.09 per million input tokens (2026-10-06) | **Conflicts** with the Cloudflare model page fetched 2026-11-14: 24,576 tokens and $0.038. |
| `fitchmultz/pi-agent-skills` | Clef-flash 24,576 tokens and $0.038; Clef 65,536 and $0.24 | **Agrees** with Cloudflare's page. Clef's $0.24 also matches the Ollama pricing page. |
| `digitaldreams/tuhin` | Ollama rejects object criteria for choice with a 400 | **Conflicts** for Ollama Cloud Clef: a billed probe got 200 with object option values (field matrix `PBB` `b08`, observed once). The OpenAPI says string or null, and the generic local encoder rejects objects, so the claim may hold for other local models. |
| `digitaldreams/tuhin` | `usage.input_tokens` counts the state again for each question | **Agrees.** The OpenAPI says shared context is counted again when questions are scored separately. |
| `digitaldreams/tuhin` | A long local prompt returns 400 with the text `prompt 0 has N tokens; expected 1-M` | **Unconfirmed.** Not in the docs; local models only. |
| `luandro/clef` | Score limit is 2 to 10; choice up to 255 | **Agrees** with the cloud rows. The proxy is a third-party host and is not a source for Ollama. |
| `atostivint/hermes-adaptive-effort` | Transient statuses 408, 429, 500, 502, 503, 504 and 529 are worth retrying | **Not covered.** Ollama documents none of them as retryable for System One. A retry policy is a local choice. |
| `kolbasik/coding-agent-guard` | `clef:cloud` can run through a local Ollama as a screen | **Agrees.** It is the documented daemon route. |
| `Haple/system-one` | 14 318 measured API calls | **Not covered.** A lead for calibration only. |

## Borrow list

Ranked by value to `typed-judgments`. None of these is applied. This file
changes no skill.

1. **Untrusted state, code-first rules, fail closed.** Say that text in
   `state` may argue for its own answer (keep it in its own named field, point
   at it by path, and add an injection noul), that no model answer alone
   authorizes a side effect, and that a rule code can state exactly (a
   denylist, a cap, a protected branch) runs before the model, so the model may
   only make the outcome stricter. Add that a failed call is never an approval.
   Sources: `aaddrick/building-with-decision-models` (rule 10 and "Common
   mistakes"), `lyhu/skills-cloudflare-clef` (fail-closed contract),
   `typesafe-ai/skills` ("surface a failed call as an error"),
   `OpenRouterTeam/skills` (adversarial probes). Today the skill covers secrets
   in state and passes a tool failure up, and says nothing on injection.
2. **Truth table with a named action for every band.** Map each answer to
   act, review or escalate, and give the between-0.3-and-0.7 band its own row
   with a named fallback. Say which uses fail open to a default (routing, tuning)
   and which fail closed (gates). Sources: `typesafe-ai/skills`, `OpenRouterTeam/skills`
   (step 6), `aaddrick/building-with-decision-models` ("Using the numbers"),
   `dwain-barnes/clef-model-router` and `lyhu/skills-cloudflare-clef` (the two
   directions).
3. **Calibration belongs to one model version.** Tune cut-offs on about 50
   labeled items, pin a versioned model id, log the `model` the response
   reports, and re-tune when the model or the backend changes. A noul
   threshold does not carry to a choice, and a Jev `confidence` threshold does
   not carry to Ollama's entropy-based `confidence`. This matches the "earn a
   gate" rule in `subagents.md` (about 50 items, precision 0.8). Sources:
   `aaddrick/building-with-decision-models` ("Changing models"),
   `bladerik/decision-benchmark`, `OpenRouterTeam/skills`, and
   `sakamoto-sann/clef-screen-triage` (fix thresholds before the second test
   set).
4. **Decompose the decision.** The TypeSafe skill calls "should this be
   escalated?" a question at the wrong layer and asks for the component
   judgments, with code combining them. The `typed-judgments` table row "Is
   this change ready to merge? Use a `score` over readiness levels" and its
   `merge_readiness` example are of that form. Treat this as a question for the
   skill's owner, not a finding: a readiness score can still be a deliberate
   summary question.
5. **A probe set recipe.** Clear, ambiguous, no-match, empty, negated and
   adversarial inputs before trusting a threshold (`OpenRouterTeam/skills`,
   step 7).
6. **Look at `probabilities`, not only `score`.** A fractional score can hide
   a two-peaked answer, and it should drive thresholds and sorting, not a
   magnitude read-off (`typesafe-ai/skills`, `aaddrick/building-with-decision-models`).
   The skill now tells the reader not to round the fraction away. Both points
   can stand.
7. **Question craft.** The "human test" for state, no "or" inside a question,
   name the confusing case in the criteria, option names reach the model but
   ids do not, one noul per statement when several can hold
   (`typesafe-ai/skills`).
8. **Deterministic check first.** Use a DOM check, a regex fact or a count in
   code before asking the model (`sakamoto-sann/clef-screen-triage`,
   `OpenRouterTeam/skills`).
9. **Budgets for hot loops.** Cache, a per-day call cap, no automatic retries
   and a cumulative wait budget (`sakamoto-sann/clef-screen-triage`,
   `lyhu/skills-cloudflare-clef` `ego-clef`).
10. **Per-provider differences once an Ollama backend exists.** The
    `confidence` formula, the option and level caps, and the absence of `box`
    and `refusal` differ by host. See file 1.

## Not reached

- Query results past the first 100 hits per query.
- Package registries and any web index.
- Most of the roughly 500 keyword-matched Jev repositories: counted, not read.
- The contents of the aggregator catalogs named above.
- Whether any of the listed skills work against the live Ollama cloud route.
  No skill was run.
