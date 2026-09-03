#!/usr/bin/env python3
"""Unit tests for the two consensus runner helpers.

`parse-consensus-categories` turns one executor "Unresolved for consensus" line
into the analyst set the orchestrator must dispatch. `aggregate-crl` turns a
workflow file's Consensus Resolution Log into the Round-2 escape-rate metric
behind the documented 10% re-evaluation trigger.

Both rule sets used to live only in `references/consensus-protocol.md` prose,
which named two Bash scripts that no longer existed, so a routing mistake was
invisible to every test. Each row of that reference's category table is pinned
here, and the aggregation cases use the reference's own five-row worked example
as an inline fixture rather than reading a workflow file off disk.

The helpers run in process against a temporary root so each case states exactly
one behavior; the request-envelope path is covered by
test-speckit-pro-read-only-helpers.py.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
SHARED_LIB = REPO_ROOT / "tests" / "speckit-pro" / "lib"

if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from test_result import run_counted  # noqa: E402

from speckit_pro_runner.helpers.read_only import (  # noqa: E402
    aggregate_crl,
    parse_consensus_categories,
)

CODEBASE = "speckit-pro:codebase-analyst"
SPEC = "speckit-pro:spec-context-analyst"
DOMAIN = "speckit-pro:domain-researcher"
ALL_THREE = [CODEBASE, SPEC, DOMAIN]
KNOWN_ANALYSTS = frozenset(ALL_THREE)

REFERENCE_DOC = PLUGIN_ROOT / "skills" / "speckit-autopilot" / "references" / "consensus-protocol.md"
DISPATCH_FIXTURES = REPO_ROOT / "tests" / "speckit-pro" / "layer7-integration" / "dispatch-fixtures"

# The five worked-example rows from consensus-protocol.md §Logging, trimmed in
# the free-text cells only. Rounds are 1, 1, 2, 1→2, 1 and one outcome is
# `escape-hatch`, so the documented aggregate is 5 items, 3 Round 1, 2 Round 2,
# 1 escape and a 20.00% rate.
REFERENCE_LOG = """# Workflow

### Consensus Resolution Log

| # | Type    | Question/Gap/Finding        | Categories         | Round | Outcome         | Resolution           | Analysts Used |
|---|---------|-----------------------------|--------------------|-------|-----------------|----------------------|---------------|
| 1 | Clarify | Session token format?       | [domain]           | 1     | high-confidence | JWT with 24h expiry  | domain-researcher |
| 2 | Gap     | Rate limit thresholds       | [codebase, domain] | 1     | both-agree      | Added to spec 4.2    | codebase-analyst, domain-researcher |
| 3 | Finding | Missing integration tests   | [ambiguous]        | 2     | 3/3             | Added task T050      | codebase-analyst, spec-context-analyst, domain-researcher |
| 4 | Clarify | Bcrypt vs argon2?           | [codebase]         | 1→2   | escape-hatch    | Argon2               | codebase-analyst then the other two |
| 5 | Finding | OAuth callback URL handling | [security]         | 1     | [HUMAN REVIEW]  | Surfaced to user     | All |
"""


def fenced_item_line(prompt: str) -> str | None:
    """The tagged unresolved item out of a dispatch-fixture prompt, or None.

    A routing fixture states its item inside the first fenced block and wraps it
    across lines for width. The helper reads one line, so the block is rejoined
    the way the executor would have written it. A first block that does not open
    with a category bracket belongs to some other kind of fixture, which this
    cross-check has nothing to say about.
    """
    block: list[str] | None = None
    for line in prompt.splitlines():
        if line.startswith("```"):
            if block is None:
                block = []
                continue
            break
        if block is not None:
            block.append(line.strip())
    if not block:
        return None
    item = " ".join(part for part in block if part)
    return item if item.startswith("[") else None


def section_between(text: str, start: str, end: str) -> str:
    """The slice of ``text`` from the ``start`` marker up to the ``end`` marker."""
    head = text.index(start)
    return text[head : text.index(end, head)]


def route(line: str) -> tuple[dict[str, object], int]:
    """Run parse-consensus-categories over one unresolved-item line."""
    with tempfile.TemporaryDirectory() as raw_root:
        result = parse_consensus_categories({"line": line}, Path(raw_root).resolve())
    return json.loads(result["stdout"]), int(result["exit_code"])


def analysts_for(line: str) -> list[str]:
    payload, exit_code = route(line)
    assert exit_code == 0, exit_code
    return list(payload["analysts"])


def aggregate(body: str | None, **inputs: object) -> tuple[dict[str, object], int, str]:
    """Run aggregate-crl over ``body`` written into a temporary repository root.

    ``body`` of None writes no file at all, which is the missing-input case.
    """
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        if body is not None:
            (root / "workflow.md").write_text(body, encoding="utf-8")
        request: dict[str, object] = {"workflow_file": "workflow.md"}
        request.update(inputs)
        result = aggregate_crl(request, root)
    stdout = result["stdout"].strip()
    payload = json.loads(stdout) if stdout else {}
    return payload, int(result["exit_code"]), result["stderr"]


class RoutingTests(unittest.TestCase):
    def test_each_single_category_tag_routes_to_its_own_analyst(self) -> None:
        for tag, analyst in (("codebase", CODEBASE), ("spec", SPEC), ("domain", DOMAIN)):
            with self.subTest(tag=tag):
                self.assertEqual(analysts_for(f"[{tag}] Q1: which pattern applies?"), [analyst])

    def test_security_tag_routes_to_all_three(self) -> None:
        payload, exit_code = route("[security] Q2: how is the session token stored?")
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["analysts"], ALL_THREE)
        self.assertIn("security", payload["reason"])

    def test_security_tag_overrides_a_narrower_tag_beside_it(self) -> None:
        self.assertEqual(analysts_for("[codebase, security] Q3: token storage?"), ALL_THREE)

    def test_security_keyword_in_the_item_text_widens_a_narrow_tag(self) -> None:
        # The reference defines the `[security]` tag by the keywords in the item
        # text, so an executor that tags narrowly must still get all three.
        payload, exit_code = route("[codebase] Q: where is the session token stored?")
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["tags"], ["codebase"])
        self.assertEqual(payload["analysts"], ALL_THREE)
        self.assertIn("security keyword", payload["reason"])

    def test_hyphenated_and_shouted_keywords_still_widen(self) -> None:
        for line in (
            "[spec] Q: how often do we rotate the API-Key?",
            "[domain] Q: what is the PII retention window?",
            "[codebase] Q: which module owns access-control?",
        ):
            with self.subTest(line=line):
                self.assertEqual(analysts_for(line), ALL_THREE)

    def test_plural_security_keywords_widen_a_narrow_tag(self) -> None:
        # The reference lists the keywords in the singular, but the questions
        # executors actually write are plural, so the plural must widen too.
        # Each line below carries exactly one keyword, in the plural.
        for line in (
            "[codebase] Q: how are API tokens rotated?",
            "[spec] Q: where do user credentials live?",
            "[domain] Q: which cookies does the browser keep?",
            "[codebase] Q: which module grants permissions?",
            "[spec] Q: how are passwords hashed?",
            "[domain] Q: are secrets kept in env vars?",
            "[codebase] Q: what makes sessions time out?",
        ):
            with self.subTest(line=line):
                self.assertEqual(analysts_for(line), ALL_THREE)

    def test_a_keyword_inside_a_longer_word_does_not_widen(self) -> None:
        # Boundaries are non-alphanumeric, so `token` in `tokenizer` and `auth`
        # in `authored` are not security keywords and must not widen dispatch.
        # The trailing-plural allowance must not loosen that: a keyword followed
        # by more letters is still a different word.
        self.assertEqual(analysts_for("[codebase] Q: which tokenizer does the parser use?"), [CODEBASE])
        self.assertEqual(analysts_for("[spec] Q: who authored the roadmap?"), [SPEC])
        self.assertEqual(analysts_for("[codebase] Q: is the payload tokenised on write?"), [CODEBASE])
        self.assertEqual(analysts_for("[spec] Q: what does permissioning mean here?"), [SPEC])
        self.assertEqual(analysts_for("[domain] Q: is the design sessionless by default?"), [DOMAIN])

    def test_ambiguous_tag_routes_to_all_three(self) -> None:
        payload, _ = route("[ambiguous] Q4: unclear which perspective applies")
        self.assertEqual(payload["analysts"], ALL_THREE)
        self.assertIn("ambiguous", payload["reason"])

    def test_missing_prefix_routes_to_all_three(self) -> None:
        payload, exit_code = route("Q5: no category prefix was written at all")
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["tags"], [])
        self.assertEqual(payload["analysts"], ALL_THREE)

    def test_unknown_tag_routes_to_all_three(self) -> None:
        payload, _ = route("[frobnicate] Q6: a tag nobody defined")
        self.assertEqual(payload["tags"], ["frobnicate"])
        self.assertEqual(payload["analysts"], ALL_THREE)
        self.assertIn("unknown", payload["reason"])

    def test_known_tag_beside_an_unknown_tag_still_routes_to_all_three(self) -> None:
        self.assertEqual(analysts_for("[codebase, frobnicate] Q7: half-known"), ALL_THREE)

    def test_marker_from_another_phase_is_an_unknown_tag_not_a_route(self) -> None:
        self.assertEqual(analysts_for("[NEEDS CLARIFICATION] Q8: leaked marker"), ALL_THREE)

    def test_empty_bracket_routes_to_all_three(self) -> None:
        payload, _ = route("[] Q9: an empty prefix")
        self.assertEqual(payload["tags"], [])
        self.assertEqual(payload["analysts"], ALL_THREE)

    def test_multi_tag_dispatches_the_union(self) -> None:
        self.assertEqual(analysts_for("[codebase, domain] Q10: bcrypt or argon2?"), [CODEBASE, DOMAIN])

    def test_union_order_follows_the_table_not_the_line(self) -> None:
        self.assertEqual(
            analysts_for("[domain, codebase] Q11: same union, reversed"),
            analysts_for("[codebase, domain] Q11: same union"),
        )

    def test_repeated_tag_dispatches_one_analyst(self) -> None:
        self.assertEqual(analysts_for("[spec, spec] Q12: repeated tag"), [SPEC])

    def test_list_marker_and_letter_case_do_not_change_routing(self) -> None:
        for line in (
            "- [codebase] Q13: bulleted item",
            "* [CODEBASE] Q13: starred and shouted",
            "1. [ Codebase ] Q13: numbered and padded",
        ):
            with self.subTest(line=line):
                self.assertEqual(analysts_for(line), [CODEBASE])

    def test_tags_are_reported_normalized(self) -> None:
        payload, _ = route("- [Domain, CODEBASE] Q14: mixed case")
        self.assertEqual(payload["tags"], ["domain", "codebase"])

    def test_output_never_names_a_shell_script(self) -> None:
        result_text = json.dumps(route("[spec] Q15: any item")[0])
        self.assertNotIn(".sh", result_text)


class AggregationTests(unittest.TestCase):
    def test_reference_example_yields_the_documented_escape_rate(self) -> None:
        payload, exit_code, _ = aggregate(REFERENCE_LOG)
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["total_items"], 5)
        self.assertEqual(payload["round1"], 3)
        self.assertEqual(payload["round2"], 2)
        self.assertEqual(payload["escape_hatch"], 1)
        self.assertEqual(payload["escape_rate_percent"], 20.0)
        self.assertEqual(payload["threshold_percent"], 10.0)
        self.assertIs(payload["exceeds_threshold"], True)

    def test_rounds_partition_the_items(self) -> None:
        payload, _, _ = aggregate(REFERENCE_LOG)
        self.assertEqual(payload["round1"] + payload["round2"], payload["total_items"])

    def test_ascii_arrow_counts_as_an_escalation(self) -> None:
        payload, _, _ = aggregate(REFERENCE_LOG.replace("1→2", "1->2"))
        self.assertEqual(payload["round2"], 2)
        self.assertEqual(payload["escape_hatch"], 1)

    def test_arrow_alone_counts_as_an_escape_without_an_outcome_column(self) -> None:
        body = (
            "## Consensus Resolution Log\n\n"
            "| Item | Categories | Round |\n"
            "|---|---|---|\n"
            "| I1 | `[codebase]` | 1 |\n"
            "| I2 | `[spec]` | 1→2 |\n"
        )
        payload, exit_code, _ = aggregate(body)
        self.assertEqual(exit_code, 0)
        self.assertEqual((payload["total_items"], payload["round1"], payload["round2"]), (2, 1, 1))
        self.assertEqual(payload["escape_hatch"], 1)

    def test_spaced_and_emphasized_arrow_counts_as_an_escalation(self) -> None:
        # The shape real workflow logs use: `1 → **2**`, and a deferred Round 1
        # that carries a parenthetical and must not read as an escalation.
        body = (
            "### Consensus Resolution Log\n\n"
            "| Item | Round |\n"
            "|---|---|\n"
            "| S1/Q1 | 1 |\n"
            "| S2/R1 | 1 → **2** |\n"
            "| S3/Q4 | 1 (deferred) |\n"
        )
        payload, _, _ = aggregate(body)
        self.assertEqual((payload["total_items"], payload["round1"], payload["round2"]), (3, 2, 1))
        self.assertEqual(payload["escape_hatch"], 1)

    def test_heading_matches_at_any_level(self) -> None:
        deep = REFERENCE_LOG.replace("### Consensus Resolution Log", "##### Consensus Resolution Log")
        self.assertEqual(aggregate(deep)[0]["total_items"], 5)

    def test_rows_stop_at_the_next_heading(self) -> None:
        body = REFERENCE_LOG + (
            "\n### Feedback Sweep Log\n\n"
            "| # | Comment ID | CRL # |\n"
            "|---|---|---|\n"
            "| 1 | IC_1 | 4 |\n"
        )
        self.assertEqual(aggregate(body)[0]["total_items"], 5)

    def test_unreadable_round_cell_counts_as_round_one(self) -> None:
        body = (
            "### Consensus Resolution Log\n\n"
            "| Item | Round |\n"
            "|---|---|\n"
            "| I1 | not routed |\n"
        )
        payload, _, _ = aggregate(body)
        self.assertEqual((payload["total_items"], payload["round1"], payload["round2"]), (1, 1, 0))
        self.assertEqual(payload["escape_hatch"], 0)

    def test_absent_log_aggregates_to_zero_without_failing(self) -> None:
        payload, exit_code, stderr = aggregate("# Workflow\n\nNo consensus was needed.\n")
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["total_items"], 0)
        self.assertEqual(payload["escape_rate_percent"], 0.0)
        self.assertIs(payload["exceeds_threshold"], False)
        self.assertIn("Consensus Resolution Log", stderr)

    def test_table_without_a_round_column_aggregates_to_zero(self) -> None:
        body = (
            "### Consensus Resolution Log\n\n"
            "| Item | Outcome |\n"
            "|---|---|\n"
            "| I1 | both-agree |\n"
        )
        self.assertEqual(aggregate(body)[0]["total_items"], 0)

    def test_rate_equal_to_the_threshold_does_not_exceed_it(self) -> None:
        rows = "".join(
            f"| {number} | 1 | {'escape-hatch' if number == 1 else 'both-agree'} |\n"
            for number in range(1, 11)
        )
        body = "### Consensus Resolution Log\n\n| # | Round | Outcome |\n|---|---|---|\n" + rows
        payload, _, _ = aggregate(body)
        self.assertEqual(payload["total_items"], 10)
        self.assertEqual(payload["escape_rate_percent"], 10.0)
        self.assertIs(payload["exceeds_threshold"], False)

    def test_threshold_percent_is_an_input(self) -> None:
        payload, exit_code, _ = aggregate(REFERENCE_LOG, threshold_percent=25)
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["threshold_percent"], 25.0)
        self.assertIs(payload["exceeds_threshold"], False)

    def test_numeric_string_threshold_is_accepted(self) -> None:
        payload, exit_code, _ = aggregate(REFERENCE_LOG, threshold_percent="25")
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["threshold_percent"], 25.0)

    def test_non_numeric_threshold_is_rejected(self) -> None:
        payload, exit_code, _ = aggregate(REFERENCE_LOG, threshold_percent="soon")
        self.assertEqual(exit_code, 2)
        self.assertIn("threshold_percent", payload["error"])

    def test_missing_workflow_file_is_reported(self) -> None:
        payload, exit_code, stderr = aggregate(None)
        self.assertEqual(exit_code, 1)
        self.assertEqual(payload, {})
        self.assertIn("workflow.md", stderr)

    def test_empty_workflow_file_input_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            result = aggregate_crl({"workflow_file": ""}, Path(raw_root).resolve())
        self.assertEqual(int(result["exit_code"]), 2)
        self.assertIn("workflow_file", json.loads(result["stdout"])["error"])


class DispatchFixtureAgreementTests(unittest.TestCase):
    """The Layer 7 dispatch fixtures and the helper must want the same thing.

    A live Layer 7 run follows the reference, which mandates dispatching exactly
    what `parse-consensus-categories` returns. Replay mode reads the recorded
    transcripts and never opens `prompt.txt`, so a fixture whose item text routes
    somewhere its `expected.json` forbids stays green until the first `--live`
    run. Routing each fixture's own item here closes that gap without a live run.
    """

    def test_every_tagged_dispatch_fixture_agrees_with_the_helper(self) -> None:
        checked = 0
        for fixture in sorted(path for path in DISPATCH_FIXTURES.iterdir() if path.is_dir()):
            prompt_file = fixture / "prompt.txt"
            expected_file = fixture / "expected.json"
            if not prompt_file.is_file() or not expected_file.is_file():
                continue
            item = fenced_item_line(prompt_file.read_text(encoding="utf-8"))
            if item is None:
                continue
            checked += 1
            expected = json.loads(expected_file.read_text(encoding="utf-8"))
            analysts = set(analysts_for(item))
            with self.subTest(fixture=fixture.name):
                required = KNOWN_ANALYSTS.intersection(expected.get("must_dispatch_to", []))
                self.assertEqual(
                    required - analysts,
                    set(),
                    f"{fixture.name}: expected.json requires analysts the helper does not return for {item!r}",
                )
                self.assertEqual(
                    analysts.intersection(expected.get("must_not_dispatch_to", [])),
                    set(),
                    f"{fixture.name}: the helper returns an analyst expected.json forbids for {item!r}",
                )
                cap = expected.get("max_dispatch_count")
                if isinstance(cap, int) and not isinstance(cap, bool):
                    self.assertLessEqual(
                        len(analysts),
                        cap,
                        f"{fixture.name}: the helper returns more analysts than max_dispatch_count for {item!r}",
                    )
        self.assertGreaterEqual(checked, 8, "expected the tagged routing fixtures to be found and checked")


class ReferenceProseTests(unittest.TestCase):
    """The shipped reference must send the orchestrator to the helper, once.

    The reference is the Claude orchestrator's routing instruction. While any
    passage still describes hand-parsing the prefix, an orchestrator that obeys
    that passage never reaches the widening rules the helper owns, and the Codex
    surface (whose Layer 1 check already bans the hand-routing wording) and the
    Claude surface disagree about how the same protocol runs.
    """

    def setUp(self) -> None:
        self.text = REFERENCE_DOC.read_text(encoding="utf-8")

    def test_no_passage_tells_the_orchestrator_to_route_by_hand(self) -> None:
        for phrase in (
            "per the routing table",
            "The orchestrator parses the prefix",
            "parses comma-separated category lists",
            "the analyst(s) named by the category prefix",
            "routing per the",
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, self.text)

    def test_the_tier_a_opening_names_the_helper(self) -> None:
        opening = section_between(self.text, "## Category-Routed Dispatch (Tier A)", "### Category tags")
        self.assertIn("parse-consensus-categories", opening)

    def test_the_multi_category_paragraph_names_the_helper(self) -> None:
        paragraph = section_between(self.text, "**Multi-category tags**", "### Two-round protocol")
        self.assertIn("parse-consensus-categories", paragraph)

    def test_the_round_one_pseudocode_names_the_helper(self) -> None:
        round_one = section_between(self.text, "ROUND 1 — category-routed", "ROUND 2 — full fan-out")
        self.assertIn("parse-consensus-categories", round_one)


def build_suite() -> unittest.TestSuite:
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite()
    for case in (RoutingTests, AggregationTests, DispatchFixtureAgreementTests, ReferenceProseTests):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-consensus-routing-helpers")


if __name__ == "__main__":
    raise SystemExit(main())
