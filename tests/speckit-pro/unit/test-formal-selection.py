#!/usr/bin/env python3
"""Selection is explicit; malformed records cannot silently disable gates."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO_ROOT / "speckit-pro"), str(REPO_ROOT / "tests/speckit-pro/lib")]

from speckit_pro_runner.formal.selection import SelectionError, selection_from_workflow, validate_selection
from test_result import run_counted


def selected() -> dict:
    return {"schema_version": "1.0", "status": "enabled", "rationale": "Retries can race with cancellation.", "models": [
        {"id": "lease-owner", "behavior": "At most one owner", "origin": "new", "evidence": "model"}
    ]}


def workflow(record: dict) -> str:
    return "# Workflow\n\n## Formal Methods\n\n```json\n" + json.dumps(record) + "\n```\n\n## Phase 1\n"


class FormalSelectionTests(unittest.TestCase):
    def test_explicit_selection_and_legacy_absence(self) -> None:
        self.assertEqual(selected(), selection_from_workflow(workflow(selected())))
        self.assertEqual("none", selection_from_workflow("# Retry concurrency .tla apalache") ["status"])
        for status in ("none", "deferred"):
            with self.subTest(status=status):
                record = {**selected(), "status": status, "models": []}
                self.assertEqual(record, validate_selection(record))
        reused = selected()
        reused["models"][0].update(origin="existing", evidence="model_and_trace")
        self.assertEqual(reused, validate_selection(reused))

    def test_invalid_selection_fails_closed(self) -> None:
        for change in ({"status": "auto"}, {"schema_version": "2.0"}, {"rationale": " "},
                       {"models": []}, {"models": {}}, {"skip": True},
                       {"status": "none"}, {"models": selected()["models"] * 2}):
            with self.subTest(change=change), self.assertRaises(SelectionError):
                selection_from_workflow(workflow({**selected(), **change}))
        for field, value in (("id", "../escape"), ("id", "Upper"), ("origin", "auto"),
                             ("behavior", ""), ("evidence", "typecheck"), ("evidence", True)):
            record = selected()
            record["models"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(SelectionError):
                validate_selection(record)

    def test_fenced_prompts_are_not_authoritative_sections(self) -> None:
        # Real phase prompts use a longer outer fence so inner JSON stays literal.
        prompt = "````markdown\n" + workflow(selected()) + "\n````\n"
        self.assertEqual("none", selection_from_workflow(prompt)["status"])
        self.assertEqual(selected(), selection_from_workflow(prompt + workflow(selected())))

    def test_duplicate_or_unfinished_records_are_errors(self) -> None:
        for text in ("## Formal Methods\n", workflow(selected()) * 2,
                     '## Formal Methods\n```json\n{"status":"none", "status":"enabled"}\n```',
                     '## Formal Methods\n```json\n{{FORMAL_SELECTION}}\n```',
                     '## Formal Methods\n```json\n{}\n```\n```json\n{}\n```'):
            with self.subTest(text=text), self.assertRaises(SelectionError):
                selection_from_workflow(text)

    def test_contract_schema_matches_supported_values(self) -> None:
        from speckit_pro_runner.formal import selection
        schema = json.loads((REPO_ROOT / "speckit-pro/speckit_pro_runner/contracts/formal-selection.schema.json").read_text())
        properties = schema["properties"]
        self.assertEqual(selection.SCHEMA_VERSION, properties["schema_version"]["const"])
        self.assertEqual(list(selection.STATUSES), properties["status"]["enum"])
        model = properties["models"]["items"]["properties"]
        self.assertEqual(list(selection.ORIGINS), model["origin"]["enum"])
        self.assertEqual(list(selection.EVIDENCE_LEVELS), model["evidence"]["enum"])


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(FormalSelectionTests), label="test-formal-selection"))
