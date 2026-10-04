# Where the Artifact Author Spends Its Time

> Dated record. It describes `speckit-pro` at the 2.40.0 release commit (`f7c97c1af`).
> Line numbers cite that tree and may move. The two source runs are private canary
> runs, so this note gives aggregate numbers and no fixture content.

Research ticket: #1146. Parent map: #1144.

## Summary

The artifact author spends almost all of its time writing Python scripts that contain whole HTML pages. It never uses the `Write` or `Edit` tools and never calls the author broker. In the baseline run, 61% of its model time went to those page-writing scripts, 14% to validator scripts and renames (the validator was re-written for every page), and 25% to reads, searches and housekeeping.

Only 7 of the 25 marked regions across the four draft-stage templates need real narrative or a drawing. Eight are fully derivable from the planning record, and ten need a code skeleton plus short prose. Plan, tasks and spec files already carry stable headings, so a runner can fill the first group today.

The 2.40.0 smoke took 16 more minutes. Three things show in the transcripts. They overlap, so they do not sum to the gap:

- It selected a fourth page (6.1 minutes).
- It spent 15.2 minutes on checks it chose to run: fact-check scripts (10.3 minutes) and SVG-to-PNG render checks (4.9 minutes). The baseline ran none of the second kind.
- It wrote its page scripts 11 times for 4 pages, and 5 of those runs failed (the baseline wrote 3 scripts for 3 pages). Rework was 23% of its time.

The author agent file did not change between the two plugin commits (one word in a Codex-only block). The cause is run behavior and the page set, not new author instructions.

The four preview observers add no rendered evidence in headless runs. All four returned `unavailable`.

## Method and limits

- Source A: the baseline Claude Code plan-stage transcript (plugin commit before 2.40.0).
- Source B: the 2.40.0 smoke plan-stage transcript.
- I read every subagent message whose `parent_tool_use_id` is the author launch. That is 56 tool calls in the baseline and 88 in the smoke, matching the harness usage footer.
- **Time per call** is the interval between the previous message in the author's stream and the message that issued the call. Tool execution time is under 5 seconds in total in both runs, so this interval is almost entirely model time (reasoning plus output). The transcripts do not split reasoning from output.
- **Page boundaries** are set by the first read of each page's template. Setup calls before the first template read form a shared "setup" row. Time spent deciding on page N+1 while finishing page N lands on the page whose call comes next.
- **Kinds** were assigned by tool name and command content. A script that writes a page counts as `render/write`. A script that only reads the record or runs the host Python counts as `fact-check`.
- The earlier performance profile already reports the headline numbers (22.6 and 37.9 minutes, 56 and 88 tools). I do not repeat them beyond what the breakdown needs.

## 1. Author tool calls by page and kind

### Calls

Kinds: **read-input** (planning record, source files, project files), **read-ref** (manifest, gallery contract, grounding and discovery references), **read-tmpl** (shipped template), **render** (a script that builds and writes the page), **validate** (separate validator, atomic rename, or marker grep at the final path), **re-read** (Read of a finished page), **check** (searches and fact-check scripts), **visual** (SVG render to PNG and reading the PNG, plus probing for a renderer), **house** (`ls`, `mkdir`, `git status`, `rm`).

Baseline (56 calls, 25 turns):

| Page | read-input | read-ref | read-tmpl | render | validate | re-read | check | visual | house | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| setup | 16 | 5 | 0 | 0 | 0 | 0 | 2 | 0 | 3 | 26 |
| implementation-plan | 0 | 0 | 1 | 1 | 3 | 3 | 0 | 0 | 0 | 8 |
| spec-explainer | 0 | 0 | 3 | 1 | 3 | 2 | 1 | 0 | 1 | 11 |
| module-map | 0 | 0 | 3 | 1 | 3 | 2 | 1 | 0 | 0 | 10 |
| closing check | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| **All** | 16 | 5 | 7 | 3 | 9 | 7 | 4 | 0 | 5 | **56** |

Smoke (88 calls, 61 turns, stopped by `maxTurns: 60`):

| Page | read-input | read-ref | read-tmpl | render | validate | re-read | check | visual | house | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| setup | 14 | 3 | 0 | 0 | 0 | 0 | 3 | 0 | 1 | 21 |
| implementation-plan | 0 | 0 | 1 | 3 | 1 | 1 | 2 | 5 | 3 | 16 |
| spec-explainer | 1 | 0 | 1 | 2 | 1 | 2 | 3 | 0 | 0 | 10 |
| code-approaches | 0 | 0 | 3 | 4 | 1 | 2 | 3 | 0 | 0 | 13 |
| module-map | 1 | 0 | 10 | 2 | 1 | 2 | 7 | 4 | 1 | 28 |
| **All** | 16 | 3 | 15 | 11 | 4 | 7 | 18 | 9 | 5 | **88** |

Counts that the tables do not show:

- `Write` calls: 0 in both runs. `Edit` calls: 0 in both runs. Author broker calls: 0 in both runs. Every page is written by a `python` heredoc through `Bash`.
- The agent's rule is to validate a sibling temporary file, rename it, then re-read and validate the final page (`speckit-pro/agents/artifact-author.md:130-175`). In the baseline that became six separate validator scripts (three on the temporary file, three on the final path), 7.8 to 9.7 thousand characters each, plus three small rename scripts. The model re-wrote the validator for every page.
- In the smoke, the validator moved inside the render script. The render script then ran, validated, and published in one call. That removed the separate validate calls but made every failed run re-emit the whole page.
- Page scripts are large. The baseline emitted about 124 thousand characters of tool input (110 thousand in calls over 5 thousand characters). The smoke emitted about 295 thousand (266 thousand in large calls). The visible text inside the filled regions is 25.5 thousand characters in the baseline and 31.1 thousand in the smoke, so the author writes roughly 5 to 9 times more code than prose.

### Time

Model time per page, in seconds (minutes in brackets):

| Page | Baseline | Smoke |
| --- | --- | --- |
| setup (reads, orient) | 218 (3.6) | 74 (1.2) |
| implementation-plan | 584 (9.7) | 952 (15.9) |
| spec-explainer | 185 (3.1) | 240 (4.0) |
| code-approaches | not selected | 367 (6.1) |
| module-map | 295 (4.9) | 635 (10.6) |
| closing check | 26 (0.4) | not present |
| **Total** | **1,308 (21.8)** | **2,268 (37.8)** |

The harness reports 22.5 and 37.9 minutes of wall clock. The difference is the first model turn and the final report.

Model time by kind, in seconds:

| Kind | Baseline | Smoke |
| --- | --- | --- |
| render (page-writing scripts) | 798 (61%) | 854 (38%) |
| validate (scripts, renames, marker greps) | 181 (14%) | 22 (1%) |
| check (searches, fact-check scripts, template region greps) | 120 (9%) | 682 (30%) |
| visual (render SVG to PNG, read it) | 0 | 293 (13%) |
| read-input | 83 (6%) | 165 (7%) |
| read-tmpl | 49 (4%) | 86 (4%) |
| house | 48 (4%) | 131 (6%) |
| re-read | 27 (2%) | 32 (1%) |
| read-ref and orient | 2 | 3 |

Where the time goes inside a page, baseline:

- implementation-plan: one render script cost 495 seconds (a 27 thousand character script). Two validators cost 64 seconds.
- spec-explainer: render 109 seconds, two validators 45 seconds.
- module-map: render 194 seconds, two validators 50 seconds, three template reads 38 seconds.

## 2. Pages the manifest selects at draft-PR time

`speckit-pro/artifact-gallery/manifest.json` has five entries with `"stage": "draft-pr"`. Four are `shipped`. One is `planned`.

| Entry | Trigger | Status | Selected when |
| --- | --- | --- | --- |
| `implementation-plan` (line 16) | `always` | shipped | every run |
| `spec-explainer` (line 27) | `always` | shipped | every run |
| `code-approaches` (line 38) | `any_of: competing_approaches` | shipped | planning weighed a real alternative |
| `module-map` (line 49) | `any_of: brownfield_change` | shipped | the change edits existing code |
| `architecture-viewer` (line 60) | `any_of: brownfield_change` | planned | never; a planned entry has no template and is not a gap |

Entries with stage `final-pr` or `ad-hoc` are not selected at this moment (`speckit-pro/agents/artifact-author.md:84-101`).

The two signals are defined in prose only (`speckit-pro/artifact-gallery/SPA-CONTRACT.md:73-74`, `speckit-pro/agents/artifact-author.md:96-101`). No runner code evaluates them. The runner checks only that every `always` page is present and that no non-draft page appears (`speckit-pro/speckit_pro_runner/artifact_review.py:250-261`). So the author model decides both signals on every run.

That decision differed between the two runs:

- Baseline: the author searched `spec.md`, `plan.md`, `tasks.md` and the design concept for weighed alternatives and found none. It had read `research.md` but treated its rejected options as "decided detail", and reported `code-approaches` as not selected.
- Smoke: the author found `Alternatives considered` blocks in `research.md` and selected the page.

Both records carry that kind of block, so the same input led to different selections. This is a judgment call that a rule in code would remove. See section 6.

## 3. Marked regions and their classification

Each template carries paired `<!-- FILL:name:START -->` and `<!-- FILL:name:END -->` markers, and a header comment lists each slot with its source document. The author fills 25 regions across the four selected templates.

Class key:

- **S (structured):** every value is a field, count, ID, path, list item or verbatim block in the record. A runner can fill it.
- **M (mixed):** the skeleton is deterministic (headings, IDs, paths, order, counts, source listings), but at least one value is a prose rewrite or condensation. A runner can emit the skeleton and a lifted-text fallback. A model would polish the prose.
- **N (narrative):** the content is synthesis, a rating, or a drawing. The record does not contain it.

I classified from the template slot inventory (`Slot:` header comments) and from what the author actually wrote in both runs.

### implementation-plan (8 regions: S 1, M 5, N 2)

| Region | Slot source | Class | Why |
| --- | --- | --- | --- |
| document-title | spec.md | S | Fixed pattern: artifact kind, feature ID, feature name. |
| feature-header | spec.md | M | ID and name are fields. The one-line intent is a condensed rewrite of the plan summary. |
| plan-stats | plan.md | M | Phase count (task phase headings), file count (Declared File Operations) and projected size (reviewability budget) are fields. The "flag the work sits behind" has no field in the record. |
| phases | plan.md | M | Phase headings, `Purpose` lines, task ID ranges and file paths exist in tasks.md. The plan defines no phases, so the author took them from tasks.md. Blurbs are condensed. |
| data-flow | plan.md | N | An SVG drawing, a caption and a text equivalent. The record has no graph. |
| mockups | design-concept.md | M | For a command-line feature these are terminal transcripts lifted from acceptance scenarios and the contract. For a UI feature they would be N. |
| risk-register | plan.md, research.md | N | The record names risks but does not rate them. The author wrote High, Medium and Low labels and marked them `[inference]`. |
| task-inventory | tasks.md | M | Groups, counts and task IDs are fields. The one-line summaries condense long task text. |

### spec-explainer (7 regions: S 4, M 2, N 1)

| Region | Slot source | Class | Why |
| --- | --- | --- | --- |
| document-title | spec.md | S | Fixed pattern. |
| feature-header | spec.md | M | ID and name are fields. The lede is a condensed rewrite. |
| tldr | spec.md | N | A plain-English summary of the whole feature. |
| goals | spec.md | S | The design concept has a `Goals` list. Lifting it is verbatim. |
| non-goals | design-concept.md, spec.md | S | The design concept has a `Non-goals` list, and the tasks file repeats it. |
| acceptance-criteria | spec.md | S | The spec lists `Given / When / Then` scenarios per story. One foldable entry per scenario. A label such as "Story 1, scenario 3" is deterministic. |
| clarification-faq | spec.md, design-concept.md | M | The design concept has a Q&A log with the question, recommended answer and decision. The author rewrote questions and added cross-references. |

### code-approaches (4 regions: S 1, M 1, N 2)

| Region | Slot source | Class | Why |
| --- | --- | --- | --- |
| document-title | spec.md | S | Fixed pattern. |
| feature-header | spec.md | N | The "one-line question these approaches answer" requires choosing which decision to show. |
| approaches | research.md, plan.md | N | `Alternatives considered` bullets and rejection reasons exist in research.md. The code snippet per approach, the pro and con grid and the "meets requirement" flags do not. The author marked several pros `[inference]` and ran a small experiment to check one claim. |
| recommendation | research.md | M | The chosen option and its rationale are recorded. The "what would reopen the question" text is the author's reading. |

### module-map (6 regions: S 2, M 2, N 2)

| Region | Slot source | Class | Why |
| --- | --- | --- | --- |
| document-title | spec.md | S | Fixed pattern. |
| feature-header | spec.md | S | A sentence naming where the change lands. It follows from the NEW and MODIFIED entries in Declared File Operations. |
| module-summary | plan.md | N | A paragraph on how the modules fit and which run the change turns on. |
| module-graph | plan.md | N | An SVG, a caption and a text equivalent. Call edges for existing code can come from the source, but the new edges come from plan prose. |
| modules | plan.md | M | Path, line range, "before the change" source listing and Unchanged or Changed flag are mechanical. About 40% of the region's bytes are source listings. The role and change descriptions are prose. |
| key-files | plan.md | M | Path and New or Existing come from Declared File Operations. "What it holds" lifts from the plan's interface deltas and the task text. |

### Counts

| Page | Regions | S | M | N |
| --- | --- | --- | --- | --- |
| implementation-plan | 8 | 1 | 5 | 2 |
| spec-explainer | 7 | 4 | 2 | 1 |
| code-approaches | 4 | 1 | 1 | 2 |
| module-map | 6 | 2 | 2 | 2 |
| **All** | **25** | **8** | **10** | **7** |

Share of filled content, by class (HTML bytes inside the markers; visible text in brackets):

| Run | Pages | S | M | N |
| --- | --- | --- | --- | --- |
| Baseline | 3 (21 regions) | 17% (20%) | 50% (54%) | 33% (26%) |
| Smoke | 4 (25 regions) | 15% (19%) | 40% (45%) | 45% (36%) |

The smoke has a larger N share because `code-approaches` is mostly N.

Two cautions on the classification:

- It rests on two runs of one private fixture. A feature with a UI would push `mockups` to N. A feature with an interview-built design concept would carry richer Q&A and `Alternatives offered` fields and push `clarification-faq` and `approaches` toward S and M.
- S and M rely on the stable headings that the plan, tasks and spec templates emit (`Declared File Operations`, `Phase N`, `Purpose`, `Acceptance Scenarios`, `Alternatives considered`). Those templates come from the upstream Spec Kit commands and project overrides, so a parser must tolerate drift.

## 4. What the preview observers add

The observer is a Haiku agent with only the `Artifact` tool and the broker's `submit_preview_verdict` tool (`speckit-pro/agents/artifact-preview-observer.md:1-31`). It is meant to publish one finished page, check the rendered title and body, and submit one closed verdict. The broker rehashes the page and returns only the verdict and a SHA-256.

What it added in these runs:

| Run | Observers | Tokens each | Duration each | Verdict |
| --- | --- | --- | --- | --- |
| Baseline | 1 (implementation-plan only) | 8.5 thousand | 14 s | `unavailable` |
| Smoke | 4 (one per page) | 8.0 to 10.5 thousand | 12 to 36 s | `unavailable` x4 |

Each observer made one call, to `submit_preview_verdict`. None had a usable `Artifact` preview surface in a headless run, so none saw a rendered page. The observers add a brokered `unavailable` record bound to the page hash. They add no rendered evidence here.

### Why the smoke spawned four

- The broker binds one session to one artifact path and one expected SHA-256 (`speckit-pro/speckit_pro_runner/author_broker.py:210-250`). One observer serves one session, so each generated page needs its own observer (`speckit-pro/skills/speckit-autopilot/references/artifact-review.md:80-98`).
- The smoke generated four pages, so it needed four observers. The orchestrator said so directly: each page needs its own brokered observation.
- The baseline observed only the first page. Its stop report says the other two were "pending" and "not attempted". The pre-2.40.0 text said an inconclusive observation "ends this attempt as pending", and the baseline orchestrator appears to have read the first `unavailable` that way. It gave no reason, so this is my reading.
- Release 2.40.0 changed the text (`f8f7371f5`, #1139). The runner now reports a terminal `unavailable` with `resume_action: none` only when every generated page has a matching closed brokered `unavailable` observation (`speckit-pro/skills/speckit-autopilot/references/artifact-review.md`, "Delivery after publication"; `speckit-pro/speckit_pro_runner/artifact_review.py`). Pages that lack one stay pending and cause a retry on resume.
- The first observer ran alone and the other three ran in parallel, about 1.1 minutes in all. The orchestrator also made four `create_preview_session` and four `close_session` calls around them.

So the count is not a model choice. It is page count times the one-observer-per-page binding, plus the new terminal rule.

## 5. Why the smoke took longer (88 tools, 38 minutes, versus 56 tools, 22 minutes)

The transcripts show the following.

**The planning record was only slightly larger.** The files the author reads (spec, plan, tasks, research, data model, quickstart, contract) total about 75 thousand bytes in the baseline and 85 thousand in the smoke (+14%). The three pages both runs produced have 49 thousand bytes of filled content in the baseline and 53 thousand in the smoke (+9%). Input and output volume do not explain a 72% rise in time on those three pages (17.7 to 30.5 minutes).

**The author file did not change.** The only difference in `speckit-pro/agents/artifact-author.md` between the baseline plugin commit (`7de31e787893`) and 2.40.0 is one word in a Codex-only block. The frontmatter is `model: sonnet`, `effort: max`, `maxTurns: 60` (lines 12-16). The gallery manifest and templates are also unchanged between the two commits.

**Where the 16 extra minutes went (960 seconds):**

| Driver | Evidence | Seconds |
| --- | --- | --- |
| Fact-check scripts and searches | 18 calls against 4 in the baseline. Scripts that re-read spec, plan, tasks and research and asserted numbers, IDs and quotes before writing. One ran a small Python experiment to ground a claim. | +562 |
| SVG render checks | 9 calls. The author probed for a renderer, converted the page's SVG to PNG, read the PNG, fixed it, and repeated. The baseline did none. The agent file does not ask for this. | +293 |
| Housekeeping, input reads, template reads | More `ls` and `git status` calls, repeated section reads of the module-map template (10 reads of one template), one slow re-read of a source file. | +202 |
| Page-writing scripts | 11 render runs against 3, but total render time was close (854 against 798 seconds), because the baseline wrote each page once in one very long script. | +56 |
| Validation | The smoke folded validation into the render script, so separate validate calls fell. | -159 |
| Re-read and other | | +6 |

**Rework in the smoke.** Of 11 render runs, 5 failed and 2 re-published a page after a content fix. The 5 failures cost about 7 minutes of model time, and the 2 re-publishes about 1.7 minutes. Together that is 23% of the smoke's author time. The causes were one bug in the author's own script, one failed grounding assertion, and three trips of its own leftover-sample-text check on labels that the template owns. Each failure re-emitted a script of 18 to 32 thousand characters. The baseline had no failures and no re-publishes.

**The fourth page.** `code-approaches` took 367 seconds (6.1 minutes), 38% of the gap. Part of that overlaps with the rework above, since it had 2 of the 5 failures and 1 re-publish.

**The turn limit.** The baseline used 25 turns. The smoke used 61 against `maxTurns: 60`, returned a fragment, and the orchestrator resumed the same agent with a message to get the outcome list (about 28 seconds). `phase-execution.md` treats a truncated report as a whole-set gap, so the resume goes beyond that text. See "Not confirmed".

**What the transcripts do not show:** why this run chose to fact-check and to render diagrams. The agent file asks to ground every claim and to leave no placeholder text (`speckit-pro/agents/artifact-author.md:28-35, 123-124, 210`), which could explain both, but the baseline had the same instructions and did neither. I read this as run-to-run variance at `effort: max`, not a change in the plugin. One sample per run cannot size that variance.

## 6. Conclusion: what share of authoring a runner could do in code

**Mechanical machinery, no model needed: about 30% of the baseline's author time, and most of the smoke's overhead.**

In the baseline, the steps that are pure plumbing took 399 of 1,308 seconds (30%): reading inputs and templates, writing and re-writing validators, rename, re-read, and housekeeping. In the smoke, adding the retries (23% of author time), fact-check scripts (27%) and SVG checks (13%) shows how much of the author's time can go to hand-built verification that a shared validator would make unnecessary.

The runner already has the pieces:

- Marker parsing and template-skeleton comparison: `_fill_skeleton` in `speckit-pro/speckit_pro_runner/artifact_review.py:97-112`. It is used today only as a post-hoc trust check.
- Atomic file writes: `speckit-pro/speckit_pro_runner/atomic_write.py`, used by the author broker.
- A parser for `Declared File Operations`: `declared_file_entries` in `speckit-pro/speckit_pro_runner/helpers/read_only.py:6315`. Its pattern is strict, so an entry such as "MODIFIED README.md (usage ...)" with trailing text is skipped. The smoke plan has such a line.
- A precedent for skeleton-then-polish: `generate-uat-skeleton` writes a deterministic runbook skeleton and the `uat-runbook-author` agent rewrites it in place (`speckit-pro/agents/uat-runbook-author.md`).

**Selection, signals and the page set: deterministic in code.** `brownfield_change` is true when Declared File Operations has any `MODIFIED` entry. `competing_approaches` is true when `research.md` has a non-empty `Alternatives considered` block (or the design concept has non-empty `Alternatives offered`). Writing these rules down removes the 3-page versus 4-page variance seen here.

**Region content:**

| Share | Regions | Fill bytes (smoke) |
| --- | --- | --- |
| Runner can fill fully (S) | 8 of 25 | 15% |
| Runner fills the skeleton and a lifted-text fallback; a model polishes prose (M) | 10 of 25 | 40% |
| Needs a model: narrative or drawing (N) | 7 of 25 | 45% |

The seven N regions are `data-flow` and `risk-register` (implementation-plan), `tldr` (spec-explainer), `feature-header` and `approaches` (code-approaches), and `module-summary` and `module-graph` (module-map).

**Estimate, not a measurement.** If the runner owns selection, validation, atomic publish and the S regions, and the model is asked only for the prose of the M and N regions as short text slots that the runner wraps in template markup, then:

- The model would emit roughly the visible prose (about 14 thousand characters in the smoke for M and N regions, including the text inside SVGs) rather than 295 thousand characters of scripts.
- The retry loop, the per-page validator and the leftover-sample-text check move out of the model.
- The narrative work that remains is seven regions, with M regions as optional polish.

Time scales with output volume in these transcripts (about 95 characters per second in the baseline), so the model's share would fall from 100% of the stage to something like one fifth to one third. That is my extrapolation from character counts. I did not build or time a runner filler.

Two risks to weigh against that:

- A lifted-text fallback reads worse than the author's condensed prose. The M classification exists for that reason.
- Drawings (`data-flow`, `module-graph`) stay model work, and the smoke's visual checks suggest they are where authors spend verification effort. A runner-owned geometry check (the smoke's authors wrote one) would be reusable.

## Not confirmed, and where I looked

- **Why the smoke chose to fact-check and render diagrams.** Looked in: the author agent file, the dispatch text in `phase-execution.md`, the author's visible text and tool inputs in both transcripts. The agent file is the same. Run variance is my inference.
- **Reasoning versus output time.** Message timestamps cover both. Thinking-token events exist in the stream but are not tied to individual author calls, so I did not split them.
- **Token totals.** The harness footers report 347 thousand tokens (baseline) and 124 thousand (smoke). The smoke figure is not comparable (it is smaller despite more calls), so I did not use tokens.
- **Gallery build identity.** The scratch builds used by the two runs have different directory names. The template read sizes and the manifest read size match across runs, and the smoke's template size matches the committed template, but I did not hash the baseline build.
- **Whether resuming a truncated author is allowed.** `phase-execution.md` calls a truncated report a whole-set gap. The orchestrator resumed the agent instead and obtained a complete list. I did not check whether another section allows this.
- **Classification of M regions as lift-able.** I read the final pages and the record. I did not build a prototype to confirm the lifted text passes the template checks.
- **Observer behavior on a host with a preview surface.** Both runs were headless. I have no transcript of an observer that could render.
- **Sample size.** Two runs, one fixture, one feature each. Nothing here sizes variance.

## Sources

- `speckit-pro/agents/artifact-author.md` (selection, fill, publish sequence, frontmatter)
- `speckit-pro/agents/artifact-preview-observer.md`
- `speckit-pro/artifact-gallery/manifest.json`, `SPA-CONTRACT.md`, and the four shipped templates under `speckit-pro/artifact-gallery/templates/`
- `speckit-pro/speckit_pro_runner/author_broker.py` (session binding and verdicts), `artifact_review.py` (`_fill_skeleton`, `_selection`), `preview_launcher.py` (the Codex launcher, not exercised in these Claude runs)
- `speckit-pro/skills/speckit-autopilot/references/phase-execution.md` ("Artifact generation: the `artifact-author` dispatch") and `artifact-review.md` ("Delivery after publication")
- `speckit-pro/speckit_pro_runner/helpers/read_only.py` (`declared_file_entries`)
- Commit `f8f7371f5` (#1139), which changed the observer rule between the two runs
- The baseline and 2.40.0 smoke plan-stage transcripts (private)
