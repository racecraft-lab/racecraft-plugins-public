# The canary drives the real scaffold grill through an operator agent

Status: accepted

Scaffold exists to grill the operator before it writes the workflow file. The
Grill Me answers become the Design Concept, and planning works from it. Until
now the canary ran scaffold with `--answers-file`, which skips the grill and
writes the Design Concept from a JSON file. So the canary never tested the step
that decides what planning works from, and its phase 1 check, "0 questions
after scaffold", passed only because no questions were asked at all.

We decided four things (owner, 2026-10-18).

1. **The canary runs the real interactive scaffold.** An operator agent answers
   each grill question. It gets the roadmap entry and the fixture answers, and
   nothing about the planted catches, so a catch counts only when the grill or a
   later phase finds it. When the fixture answers do not cover a question, it
   answers "no preference" and the receipt records the question.
2. **One pinned operator for both hosts:** Claude Sonnet at medium effort,
   pinned in the fixture, so receipts from the two hosts stay comparable. On
   Claude Code a PreToolUse hook on `AskUserQuestion` returns the operator's
   answers. On Codex an app-server client answers `item/tool/requestUserInput`
   and every approval request, because `codex exec` rejects the question tool.
   The question guard ([ADR 0011](0011-security-interrupt.md)) allows questions
   during scaffold.
3. **The receipt judges the grill.** Gates: the grill asked at least one
   question through the real question tool, the Design Concept has every
   required section, and no question follows scaffold. Measurements, which never
   fail a run: the count of "no preference" answers, and whether the grill asked
   about each planted catch.
4. **Answers-file mode is removed as a feature**, but only after the canary
   runs the real grill on both hosts. The removal takes the flag, the
   `scaffold-answers` helper and its contract, its tests and the skill text in
   one PR with a release note.

## Considered Options

- **Fixture answers matched to questions by topic.** Repeatable, but grill
  questions change from run to run, and a new kind of question gets no answer.
- **The host's own model as the operator.** Matches each host, but the two hosts
  would get different operators.
- **Keeping answers-file mode as a feature or a second canary variant.** Rejected
  by the owner: one scaffold path, and the canary tests the path users run.

## Consequences

Phase 1 closes only when the canary runs the real grill on both hosts with no
question after scaffold. Canary round 5 (2026-10-18) does not prove phase 1,
because it skipped the grill. Each phase closes on its own checks; later-phase
failures are listed as expected and are not filed.
