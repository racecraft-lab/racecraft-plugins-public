#!/usr/bin/env python3
"""Focused CLI contracts for the Layer-7 transcript tools."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LAYER7 = TESTS_ROOT / "layer7-integration"
SCRUB = LAYER7 / "scrub-transcript.py"
REDUCE = LAYER7 / "reduce-transcript-fixture.py"
HELPERS = LAYER7 / "lib" / "transcript_helpers.py"
SHARED_LIB = TESTS_ROOT / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))
from test_result import run_counted  # noqa: E402


def run_script(script: Path, *args: str, input_text: str | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    child_env = os.environ.copy()
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        child_env.update(env)
    return subprocess.run(
        [sys.executable, str(script), *args],
        input=input_text,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=child_env,
        shell=False,
        check=False,
    )


class TranscriptToolTests(unittest.TestCase):
    def test_transcript_tool_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_events = [
                {
                    "type": "assistant",
                    "cwd": "/" + "Users/alice/Documents/work/racecraft-plugins-public",
                    "note": "Cache at C:\\" + "Users\\alice\\repo\\private.json",
                    "sessionId": "session-secret",
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": "original-agent-id",
                                "name": "Agent",
                                "input": {
                                    "subagent_type": "speckit-pro:codebase-analyst",
                                    "description": "Analyze Alice data",
                                    "prompt": "private prompt",
                                },
                            },
                            {
                                "type": "tool_use",
                                "id": "original-skill-id",
                                "name": "Skill",
                                "input": {"skill": None},
                            },
                            {
                                "type": "tool_use",
                                "id": "original-null-agent-id",
                                "name": "Agent",
                                "input": {"subagent_type": None, "description": None},
                            },
                            {
                                "type": "tool_use",
                                "id": "original-false-agent-id",
                                "name": "Agent",
                                "input": {"subagent_type": False, "description": False, "prompt": False},
                            },
                            {
                                "type": "tool_use",
                                "id": "original-false-skill-id",
                                "name": "Skill",
                                "input": {"skill": False, "args": False},
                            },
                        ],
                    },
                },
                {
                    "type": "user",
                    "message": {
                        "role": "user",
                        "content": [
                            {"type": "tool_result", "tool_use_id": "original-agent-id", "content": "private response"}
                        ],
                    },
                },
                {"type": "system", "subtype": "init", "tools": ["private-tool"]},
                {"type": "stream_event", "event": {"type": "content_block_delta", "private": "value"}},
            ]
            source_text = "".join(json.dumps(event, separators=(",", ":")) + "\n" for event in source_events)

            def scrubbed_events() -> list[dict[str, object]]:
                self.assertEqual(scrubbed.returncode, 0, scrubbed.stderr)
                return [json.loads(line) for line in scrubbed.stdout.splitlines()]

            def reduced_events() -> list[dict[str, object]]:
                self.assertEqual(reduced.returncode, 0, reduced.stderr)
                return [json.loads(line) for line in reduced.stdout.splitlines()]

            def helper_dispatches() -> list[dict[str, object]]:
                self.assertEqual(helper_extract.returncode, 0, helper_extract.stderr)
                return json.loads(helper_extract.stdout)

            checks: list[tuple[str, Callable[[], None]]] = []
            checks.append(("scrub helper exists", lambda: self.assertTrue(SCRUB.is_file())))
            checks.append(("reduce helper exists", lambda: self.assertTrue(REDUCE.is_file())))
            checks.append(("transcript library exists", lambda: self.assertTrue(HELPERS.is_file())))

            scrubbed = run_script(SCRUB, input_text=source_text, env={"TRANSCRIPT_SCRUB_EXTRA_REGEX": "Alice"})
            checks.append(("scrub stdin exits 0", lambda: self.assertEqual(scrubbed.returncode, 0, scrubbed.stderr)))
            checks.append(
                (
                    "scrub replaces machine paths",
                    lambda: self.assertEqual(
                        (scrubbed_events()[0]["cwd"], scrubbed_events()[0]["note"]),
                        ("<scrubbed>", "Cache at <HOME>"),
                    ),
                )
            )
            checks.append(("scrub replaces session metadata", lambda: self.assertEqual(scrubbed_events()[0]["sessionId"], "<scrubbed-session>")))
            checks.append(
                (
                    "scrub applies extra identity regex",
                    lambda: self.assertEqual(
                        scrubbed_events()[0]["message"]["content"][0]["input"]["description"], "Analyze <USER> data"
                    ),
                )
            )
            checks.append(("scrub reduces system inventory events", lambda: self.assertEqual(scrubbed_events()[2], {"type": "system", "subtype": "init"})))
            checks.append(
                (
                    "scrub reduces stream events",
                    lambda: self.assertEqual(scrubbed_events()[3], {"type": "stream_event", "subtype": "content_block_delta"}),
                )
            )

            malformed = run_script(SCRUB, input_text="{not-json}\n")
            checks.append(("scrub malformed JSON exits 1", lambda: self.assertEqual(malformed.returncode, 1)))

            in_place = root / "in-place.jsonl"
            in_place.write_text(source_text, encoding="utf-8")
            in_place_result = run_script(SCRUB, str(in_place))
            checks.append(("scrub in-place exits 0", lambda: self.assertEqual(in_place_result.returncode, 0, in_place_result.stderr)))
            checks.append(("scrub in-place reports path", lambda: self.assertIn(f"scrubbed: {in_place}", in_place_result.stdout)))
            checks.append(("scrub in-place writes valid JSONL", lambda: self.assertEqual(len(in_place.read_text(encoding="utf-8").splitlines()), 4)))

            missing_scrub = run_script(SCRUB, str(root / "missing.jsonl"))
            checks.append(("scrub missing file exits 1", lambda: self.assertEqual(missing_scrub.returncode, 1)))

            transcript = root / "transcript.jsonl"
            reduction_events = [json.loads(line) for line in source_text.splitlines()]
            reduction_events[0]["message"]["content"][0]["input"]["description"] = None
            transcript.write_text(
                "".join(json.dumps(event, separators=(",", ":")) + "\n" for event in reduction_events),
                encoding="utf-8",
            )
            expected = root / "expected.json"
            expected.write_text(
                json.dumps(
                    {
                        "response_assertions": [
                            {
                                "subagent_type": "speckit-pro:codebase-analyst",
                                "must_contain_any": ["Finding", "ignored-second"],
                                "must_contain_section_keywords": ["Evidence"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            reduced = run_script(REDUCE, str(transcript), str(expected))
            checks.append(("reduce transcript exits 0", lambda: self.assertEqual(reduced.returncode, 0, reduced.stderr)))
            checks.append(("reduce keeps only replay events", lambda: self.assertEqual(len(reduced_events()), 2)))
            checks.append(
                (
                    "reduce assigns deterministic tool ids",
                    lambda: self.assertEqual(reduced_events()[0]["message"]["content"][0]["id"], "tool-001"),
                )
            )
            checks.append(
                (
                    "reduce clears prompts",
                    lambda: self.assertEqual(
                        (
                            reduced_events()[0]["message"]["content"][0]["input"]["prompt"],
                            reduced_events()[0]["message"]["content"][1]["input"]["args"],
                            reduced_events()[0]["message"]["content"][4]["input"]["args"],
                        ),
                        ("", "", ""),
                    ),
                )
            )
            checks.append(
                (
                    "reduce jq-coalesces null and false Agent/Skill fields",
                    lambda: self.assertEqual(
                        (
                            reduced_events()[0]["message"]["content"][0]["input"]["description"],
                            reduced_events()[0]["message"]["content"][1]["input"]["skill"],
                            reduced_events()[0]["message"]["content"][2]["input"]["subagent_type"],
                            reduced_events()[0]["message"]["content"][2]["input"]["description"],
                            reduced_events()[0]["message"]["content"][3]["input"]["subagent_type"],
                            reduced_events()[0]["message"]["content"][3]["input"]["description"],
                            reduced_events()[0]["message"]["content"][4]["input"]["skill"],
                        ),
                        ("", "", "", "", "", "", ""),
                    ),
                )
            )
            checks.append(
                (
                    "reduce synthesizes expected response keywords",
                    lambda: self.assertEqual(
                        reduced_events()[1]["message"]["content"][0]["content"],
                        "Reduced parser fixture response for speckit-pro:codebase-analyst: Finding Evidence",
                    ),
                )
            )

            reduce_usage = run_script(REDUCE)
            checks.append(("reduce invalid usage exits 2", lambda: self.assertEqual(reduce_usage.returncode, 2)))
            reduce_missing = run_script(REDUCE, str(root / "missing.jsonl"), str(expected))
            checks.append(("reduce missing transcript exits 1", lambda: self.assertEqual(reduce_missing.returncode, 1)))

            fixture = LAYER7 / "test-fixtures" / "single-dispatch.jsonl"
            helper_extract = run_script(HELPERS, "extract-orchestrator-dispatches", str(fixture))
            checks.append(("transcript CLI extract exits 0", lambda: self.assertEqual(helper_extract.returncode, 0, helper_extract.stderr)))
            checks.append(("transcript CLI emits JSON dispatches", lambda: self.assertEqual(len(helper_dispatches()), 1)))
            helper_assert = run_script(HELPERS, "assert-dispatched-to", str(fixture), "speckit-pro:domain-researcher")
            checks.append(("transcript CLI assertions preserve exit signals", lambda: self.assertEqual(helper_assert.returncode, 1)))

            for name, check in checks:
                with self.subTest(msg=name):
                    check()


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TranscriptToolTests)
    raise SystemExit(run_counted(suite, label="test-transcript-tools"))
