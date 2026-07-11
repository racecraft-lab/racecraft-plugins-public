#!/usr/bin/env python3
"""PRSG-009 post-implementation reference contract checks."""

from __future__ import annotations

import hashlib
import sys
import unittest
from collections.abc import Callable
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CLAUDE_REF = (
    REPO_ROOT
    / "speckit-pro"
    / "skills"
    / "speckit-autopilot"
    / "references"
    / "post-implementation.md"
)
CODEX_REF = (
    REPO_ROOT
    / "speckit-pro"
    / "codex-skills"
    / "speckit-autopilot"
    / "references"
    / "post-implementation-codex.md"
)
CLAUDE_DIST = (
    REPO_ROOT
    / "dist"
    / "claude"
    / "speckit-pro"
    / "skills"
    / "speckit-autopilot"
    / "references"
    / "post-implementation.md"
)
CODEX_DIST = (
    REPO_ROOT
    / "dist"
    / "codex"
    / "speckit-pro"
    / "skills"
    / "speckit-autopilot"
    / "references"
    / "post-implementation-codex.md"
)
BASELINE = (
    REPO_ROOT
    / "tests"
    / "speckit-pro"
    / "parity"
    / "bash-to-python"
    / "test-post-implementation-reference-baseline.txt"
)

LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def baseline_inventory(path: Path) -> list[str]:
    names: list[str] = []
    total: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("TOTAL: "):
            total = int(line.removeprefix("TOTAL: "))
        else:
            _ordinal, name = line.split(" ", 1)
            names.append(name)
    if total != len(names):
        raise AssertionError(f"baseline TOTAL {total} does not match {len(names)} names")
    return names


class PostImplementationReferenceTests(unittest.TestCase):
    def test_reference_contract(self) -> None:
        claude_body = CLAUDE_REF.read_text(encoding="utf-8")
        codex_body = CODEX_REF.read_text(encoding="utf-8")
        codex_dist_body = CODEX_DIST.read_text(encoding="utf-8")

        checks: list[tuple[str, Callable[[], None]]] = [
            (
                "Claude reference routes split-PR post-impl through multi-pr-emission",
                lambda: self.assertIn("multi-pr-emission", claude_body),
            ),
            (
                "Claude reference consumes the PRSG-008 layer plan without new slicing heuristics",
                lambda: self.assertIn("plan-layers", claude_body),
            ),
            (
                "Claude reference consumes the PRSG-008 layer plan without new slicing heuristics",
                lambda: self.assertIn("MUST NOT infer, reroute, or re-slice", claude_body),
            ),
            (
                "Claude reference records durable PRS rows and resume state",
                lambda: self.assertIn("schemaVersion: 2", claude_body),
            ),
            (
                "Claude reference records durable PRS rows and resume state",
                lambda: self.assertIn("multi_pr_emission", claude_body),
            ),
            (
                "Claude reference blocks failed slices before PR creation",
                lambda: self.assertIn("stop before `gh pr create`", claude_body),
            ),
            (
                "Claude reference blocks failed slices before PR creation",
                lambda: self.assertIn("next_slice_id", claude_body),
            ),
            (
                "Claude reference requires reslicing continuation before final response",
                lambda: self.assertIn("autopilot_continuation", claude_body),
            ),
            (
                "Claude reference requires reslicing continuation before final response",
                lambda: self.assertIn("Never end the run or report completion while", claude_body),
            ),
            (
                "Claude reference documents explicit stack PR creation and restack",
                lambda: self.assertIn(
                    "gh pr create --base <base> --head <head> --body-file <body-file>",
                    claude_body,
                ),
            ),
            (
                "Claude reference documents explicit stack PR creation and restack",
                lambda: self.assertIn("restack", claude_body),
            ),
            (
                "Claude reference keeps scoped CI as evidence, not workflow YAML changes",
                lambda: self.assertIn("MUST NOT modify `.github/workflows/pr-checks.yml`", claude_body),
            ),
            (
                "Codex mirror carries equivalent multi-PR emission behavior",
                lambda: self.assertIn("multi-pr-emission", codex_body),
            ),
            (
                "Codex mirror carries equivalent multi-PR emission behavior",
                lambda: self.assertIn("plan-layers", codex_body),
            ),
            (
                "Codex mirror carries equivalent multi-PR emission behavior",
                lambda: self.assertIn("MUST NOT infer, reroute, or re-slice", codex_body),
            ),
            (
                "Codex mirror carries equivalent multi-PR emission behavior",
                lambda: self.assertIn("schemaVersion: 2", codex_body),
            ),
            (
                "Codex mirror carries equivalent multi-PR emission behavior",
                lambda: self.assertIn("multi_pr_emission", codex_body),
            ),
            (
                "Codex mirror carries equivalent multi-PR emission behavior",
                lambda: self.assertIn("stop before `gh pr create`", codex_body),
            ),
            (
                "Codex mirror carries equivalent multi-PR emission behavior",
                lambda: self.assertIn("autopilot_continuation", codex_body),
            ),
            (
                "Codex mirror carries equivalent multi-PR emission behavior",
                lambda: self.assertIn("Never report completion while", codex_body),
            ),
            (
                "Codex mirror carries equivalent multi-PR emission behavior",
                lambda: self.assertIn(
                    "gh pr create --base <base> --head <head> --body-file <body-file>",
                    codex_body,
                ),
            ),
            (
                "Codex mirror carries equivalent multi-PR emission behavior",
                lambda: self.assertIn("restack", codex_body),
            ),
            (
                "Codex mirror carries equivalent multi-PR emission behavior",
                lambda: self.assertIn("MUST NOT modify `.github/workflows/pr-checks.yml`", codex_body),
            ),
            (
                "Claude reference blocks skeleton-quality UAT before PR creation",
                lambda: self.assertIn("validate-uat-runbook", claude_body),
            ),
            (
                "Claude reference blocks skeleton-quality UAT before PR creation",
                lambda: self.assertIn("STOP before PR-body generation or PR creation", claude_body),
            ),
            (
                "Claude reference blocks skeleton-quality UAT before PR creation",
                lambda: self.assertNotIn("A plain skeleton is an acceptable fallback", claude_body),
            ),
            (
                "Codex reference blocks skeleton-quality UAT before PR creation",
                lambda: self.assertIn("validate-uat-runbook", codex_body),
            ),
            (
                "Codex reference blocks skeleton-quality UAT before PR creation",
                lambda: self.assertIn("STOP before PR-body generation or PR creation", codex_body),
            ),
            (
                "Codex reference blocks skeleton-quality UAT before PR creation",
                lambda: self.assertNotIn("A plain skeleton is an acceptable fallback", codex_body),
            ),
            (
                "Claude dist reference mirrors source",
                lambda: self.assertEqual(
                    sha256(CLAUDE_REF),
                    sha256(CLAUDE_DIST),
                    "dist/claude post-implementation reference",
                ),
            ),
            (
                "Codex dist reference carries multi-PR contract",
                lambda: self.assertIn("multi-pr-emission", codex_dist_body),
            ),
            (
                "Codex dist reference carries multi-PR contract",
                lambda: self.assertIn("MUST NOT infer, reroute, or re-slice", codex_dist_body),
            ),
            (
                "Codex dist reference carries multi-PR contract",
                lambda: self.assertIn("schemaVersion: 2", codex_dist_body),
            ),
            (
                "Codex dist reference carries multi-PR contract",
                lambda: self.assertIn("autopilot_continuation", codex_dist_body),
            ),
            (
                "Codex dist reference carries multi-PR contract",
                lambda: self.assertIn(
                    "MUST NOT modify `.github/workflows/pr-checks.yml`",
                    codex_dist_body,
                ),
            ),
        ]

        self.assertEqual(baseline_inventory(BASELINE), [name for name, _check in checks])
        for name, check in checks:
            with self.subTest(msg=name):
                check()


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(PostImplementationReferenceTests)


def main() -> int:
    return run_counted(build_suite(), label="test-post-implementation-reference")


if __name__ == "__main__":
    raise SystemExit(main())
