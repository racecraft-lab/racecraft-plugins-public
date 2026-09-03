#!/usr/bin/env python3
"""Contracts for Layer-2 trigger-eval coverage of every described skill.

A skill's frontmatter ``description`` is the only text the runtime reads when
it decides whether to load that skill. A described skill with no trigger eval
set therefore ships an unmeasured routing surface: nothing proves the
description fires on the phrasings it claims, and nothing proves it stays quiet
on a neighbouring skill's phrasings. These contracts hold the eval directories
level with the skill directories on both platforms, and hold every eval set to
the shared two-key query shape the runners parse.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LAYER2 = TESTS_ROOT / "layer2-trigger"
PLATFORMS = (
    ("claude", PLUGIN_ROOT / "skills", LAYER2 / "evals"),
    ("codex", PLUGIN_ROOT / "codex-skills", LAYER2 / "codex-evals"),
)
MINIMUM_QUERIES_PER_LABEL = 3

SHARED_LIB = TESTS_ROOT / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from test_result import run_counted  # noqa: E402


def frontmatter_description(skill_file: Path) -> str:
    """Return the frontmatter ``description`` value, folded blocks included."""

    lines = skill_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    body: list[str] = []
    collecting = False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if collecting:
            if line.startswith((" ", "\t")):
                body.append(line.strip())
                continue
            collecting = False
        if line.startswith("description:"):
            first = line[len("description:") :].strip()
            if first in {">", "|", ">-", "|-", ""}:
                collecting = True
                continue
            body.append(first)
    return " ".join(part for part in body if part).strip().strip("\"'")


def described_skills(skills_root: Path) -> list[str]:
    return sorted(
        path.parent.name
        for path in skills_root.glob("*/SKILL.md")
        if frontmatter_description(path)
    )


def eval_path(eval_root: Path, skill: str) -> Path:
    return eval_root / f"{skill}-trigger.json"


class TriggerEvalCoverageTests(unittest.TestCase):
    def test_every_described_skill_has_a_trigger_eval_set(self) -> None:
        missing: list[str] = []
        for platform, skills_root, eval_root in PLATFORMS:
            for skill in described_skills(skills_root):
                path = eval_path(eval_root, skill)
                if not path.is_file():
                    missing.append(f"{platform}: {path.relative_to(TESTS_ROOT)}")
        self.assertEqual(missing, [])

    def test_trigger_eval_sets_use_the_shared_query_shape(self) -> None:
        violations: list[str] = []
        for _platform, _skills_root, eval_root in PLATFORMS:
            for path in sorted(eval_root.glob("*-trigger.json")):
                relative = path.relative_to(TESTS_ROOT)
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as error:
                    violations.append(f"{relative}: invalid JSON ({error})")
                    continue
                if not isinstance(data, list) or not data:
                    violations.append(f"{relative}: expected a non-empty list")
                    continue
                for index, item in enumerate(data):
                    if not isinstance(item, dict) or set(item) != {"query", "should_trigger"}:
                        violations.append(f"{relative}[{index}]: expected query and should_trigger keys")
                        continue
                    if not isinstance(item["query"], str) or not item["query"].strip():
                        violations.append(f"{relative}[{index}]: query must be a non-empty string")
                    if not isinstance(item["should_trigger"], bool):
                        violations.append(f"{relative}[{index}]: should_trigger must be a boolean")
        self.assertEqual(violations, [])

    def test_trigger_eval_sets_balance_positive_and_negative_queries(self) -> None:
        violations: list[str] = []
        for _platform, _skills_root, eval_root in PLATFORMS:
            for path in sorted(eval_root.glob("*-trigger.json")):
                data = json.loads(path.read_text(encoding="utf-8"))
                positives = sum(1 for item in data if item.get("should_trigger") is True)
                negatives = sum(1 for item in data if item.get("should_trigger") is False)
                if min(positives, negatives) < MINIMUM_QUERIES_PER_LABEL:
                    violations.append(
                        f"{path.relative_to(TESTS_ROOT)}: {positives} positive, {negatives} negative"
                    )
        self.assertEqual(violations, [])


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TriggerEvalCoverageTests)
    return run_counted(suite, label="test-trigger-eval-coverage")


if __name__ == "__main__":
    raise SystemExit(main())
