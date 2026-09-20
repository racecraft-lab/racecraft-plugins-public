---
name: typed-judgments
description: >
  Get a typed judgment with a probability from the `evaluate` MCP tool instead
  of deciding by intuition and asserting the result. Use when a step in the
  current task turns on a judgment call: whether a change is ready to merge,
  which of several options or owners fits, how severe or risky something is,
  whether a test failure is real or flaky, whether a result satisfies a
  constraint that was stated earlier, or classifying many items the same way.
  Covers the noul, choice and score primitives, how to batch questions, and how
  to read the numbers. Do NOT use for writing code or prose, for a lookup or
  search, or for any question whose possible answers cannot be listed up front.
license: MIT
metadata:
  author: Racecraft Lab
  version: 0.7.1 # x-release-please-version
  mcp-server: jev
---

# Typed judgments with Jev

The `evaluate` tool answers a question you define, from state you supply, with
a probability attached. Nothing to parse and no prompt to maintain.

## When to reach for it

The trigger is a judgment you are about to make by intuition and then state as
fact. In a working session that is usually one of:

| Moment | Question type |
|---|---|
| Is this change ready to merge? | `score` over readiness levels |
| Which of these options fits? Who owns this? | `choice` |
| How severe or risky is this? | `score` |
| Is this failure real or unrelated to the change? | `noul` |
| Does this satisfy the constraint stated earlier? | `noul` |
| Classify or rank many items the same way | one call per item |

Use it **before** asserting the judgment, not to confirm one already given.

## When not to

- Writing code, prose, commit messages, or anything generative.
- A search, a lookup, or reading a file: those are cheaper done directly.
- Any question whose answers cannot be listed up front. The answer space must
  be enumerable, at most 255 options.
- A judgment the user already made. Their decision stands.

## The three primitives

- **`noul`** — the probability a yes/no condition holds. Optional `criteria`
  is `{"true": "...", "false": "..."}`.
- **`choice`** — one option from a required `criteria` map of option to
  description.
- **`score`** — a position on an ordered array of at least two level
  descriptions. The answer is probability-weighted, so `2.13` means mostly
  level 2 with some weight on 3. That fraction is the signal; do not round it
  away.

## Learning to ask a better question

The rules below are the short version. TypeSafe publishes the long one, and it
is live rather than bundled here, so it stays current as the model does. Read a
page when the judgment in front of you is hard to frame, not routinely.

Mintlify serves Markdown by appending `.md` to a page path. Resolve relative
links against `https://docs.typesafe.ai`, and read targeted pages rather than
the whole site.

| When you are stuck on | Read |
| --- | --- |
| Which primitive fits, or asking several at once | [Primitives](https://docs.typesafe.ai/primitives.md) |
| Writing the options, levels or criteria | [Choice](https://docs.typesafe.ai/primitives/choice.md), [Score](https://docs.typesafe.ai/primitives/score.md), [Noul](https://docs.typesafe.ai/primitives/noul.md) |
| What to put in `state` and how to shape it | [State](https://docs.typesafe.ai/concepts/state.md) |
| An answer whose confidence is low, or what to do about it | [Confidence](https://docs.typesafe.ai/confidence.md), [Confidence-gated routing](https://docs.typesafe.ai/patterns/confidence-routing.md) |
| A judgment too big for one question | [Composite scoring](https://docs.typesafe.ai/patterns/composite-scoring.md), [Speculative fan-out](https://docs.typesafe.ai/patterns/fan-out.md) |
| A large state, and whether accuracy holds | [Models](https://docs.typesafe.ai/models.md), [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md) |
| Anything else | the [documentation index](https://docs.typesafe.ai/llms.txt) |

One caution specific to using the tool rather than writing code: the SDK pages
describe an integration you would write, which is a different job from the one
this skill is for. The
[advanced structure](https://docs.typesafe.ai/primitives/advanced.md) page
needs no such caution — the JSON structure it describes for instructions and
criteria works on both backends.

If the docs cannot be fetched, say so and work from what is here rather than
inventing a detail that depends on a version you cannot see.

## Rules that decide whether the answer is useful

**Batch.** Independent questions over the same state go in one call. They run
in parallel and cannot see each other's answers. Eight questions cost barely
more than one, so ask everything you want to know at once.

**Mind the context budget.** The model takes about 64,000 tokens per request in
total, and about 32,000 for the state plus the single longest question. The
tool estimates both before sending and refuses a request that cannot fit,
naming which budget was exceeded, so an oversized state costs nothing. Split
the state or judge it in parts rather than trimming a question down to nothing.
Accuracy also shifts as the state grows, which the jaggedness page above
covers.

**The id carries no meaning.** Question ids are never sent to the model.
`"is_regression"` tells it nothing; the full sentence in `instructions` does.

**Put the evidence in `state`.** Prefer a JSON object with named fields, and
point at them with backticked paths: ``judge only from `ticket.messages` ``.

**Give `choice` a no-match option.** Without one the model must pick from your
list even when nothing fits, and you will never know that happened.

**Score levels describe situations, not adjectives.** "Severe: a large account
is blocked from an imminent renewal" produces a usable answer. "High" does not.

**Read the numbers correctly.** A `noul` near 0.5 means *uncertain*, not
"medium intensity". `confidence` measures how concentrated the distribution is,
not whether the answer is right: a confidently wrong answer is what badly drawn
criteria produce.

**A missing number is not a zero.** On the `openrouter` backend, `confidence`
and `probabilities` are optional on a choice or score answer; the `typesafe`
backend always sends them. The tool reports an absent field as absent and never
substitutes a value, so check it is there before you branch on it. Structured
instructions and criteria, by contrast, work on both backends.

## Example

State, then several judgments about it in one call:

```json
{
  "state": {"pr": {"files_changed": 23, "tests_added": 9, "ci": {"tests": "pass"},
             "review_comments": [{"body": "the test does not clean up on failure"}]}},
  "questions": {
    "has_unresolved_feedback": {
      "type": "noul",
      "instructions": "At least one comment in `pr.review_comments` names a concrete problem that still needs a code change before merge.",
      "criteria": {"true": "A comment names a specific defect that is unresolved.",
                   "false": "All comments are questions, opinions, or resolved points."}},
    "merge_readiness": {
      "type": "score",
      "instructions": "Rate how ready this pull request is to merge as it stands.",
      "criteria": ["Not ready: checks failing or the change is wrong.",
                   "Needs work: checks pass but reviewers raised unaddressed problems.",
                   "Nearly ready: only minor points remain.",
                   "Ready: no open concerns and all checks pass."]}
  }
}
```

Report the number, not a paraphrase of it. "Merge readiness 1 of 3, and
`has_unresolved_feedback` 0.95" is the finding; "it looks about ready" throws
away what you paid for.

## Cost and privacy

Each call sends the state and questions to the configured provider and is
billed there. The read-only annotation means it changes nothing on this
machine, not that it is free or private. Do not put a secret in `state`.

Which backend is used is fixed by the operator's `JEV_PROVIDER` setting, not by
anything you pass.

## If the tool is not there

Check which of two situations you are in before doing anything else.

**No `evaluate` tool exists at all.** This skill was installed on its own, most
likely through `skills add`, which carries skill files and no MCP server. There
is nothing to route to. Say so once, make the judgment yourself in the ordinary
way, and do not offer to build an integration to stand in for it. If typed
judgments are wanted in a session, the plugin is what provides them:
`racecraft-lab/typesafe-mcp`.

**The tool exists but fails.** The plugin ships a launcher, not the binary, so
the usual cause is that the binary was never installed. The server reports the
path it looked at and the command that installs it; pass that on rather than
working around it.

In neither case is writing SDK or HTTP code a substitute for an in-session
judgment. That is what the `typesafe-ai` skill is for, and it is a different
job: building an integration into someone's software.
