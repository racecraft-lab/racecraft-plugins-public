#!/usr/bin/env python3
"""Post-implementation reference contract checks."""

from __future__ import annotations

import sys
import unittest
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
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


CONTRACT_CHECKS = (
    ("Claude reference routes split-PR post-impl through multi-pr-emission", "claude", ("multi-pr-emission",), ()),
    ("Claude reference consumes the layer plan without new slicing heuristics", "claude", ("plan-layers",), ()),
    ("Claude reference consumes the layer plan without new slicing heuristics", "claude", ("MUST NOT infer, reroute, or re-slice",), ()),
    ("Claude reference records durable PRS rows and resume state", "claude", ("schemaVersion: 2",), ()),
    ("Claude reference records durable PRS rows and resume state", "claude", ("multi_pr_emission",), ()),
    ("Claude reference blocks failed slices before PR creation", "claude", ("stop before `gh pr create`",), ()),
    ("Claude reference blocks failed slices before PR creation", "claude", ("next_slice_id",), ()),
    ("Claude reference requires reslicing continuation before final response", "claude", ("autopilot_continuation",), ()),
    ("Claude reference requires reslicing continuation before final response", "claude", ("Never end the run or report completion while",), ()),
    ("Claude reference documents explicit stack PR creation and restack", "claude", ("gh pr create --base <base> --head <head> --body-file <body-file>",), ()),
    ("Claude reference documents explicit stack PR creation and restack", "claude", ("restack",), ()),
    ("Claude reference keeps scoped CI as evidence, not workflow YAML changes", "claude", ("MUST NOT modify `.github/workflows/pr-checks.yml`",), ()),
    ("Codex mirror carries equivalent multi-PR emission behavior", "codex", ("multi-pr-emission",), ()),
    ("Codex mirror carries equivalent multi-PR emission behavior", "codex", ("plan-layers",), ()),
    ("Codex mirror carries equivalent multi-PR emission behavior", "codex", ("MUST NOT infer, reroute, or re-slice",), ()),
    ("Codex mirror carries equivalent multi-PR emission behavior", "codex", ("schemaVersion: 2",), ()),
    ("Codex mirror carries equivalent multi-PR emission behavior", "codex", ("multi_pr_emission",), ()),
    ("Codex mirror carries equivalent multi-PR emission behavior", "codex", ("stop before `gh pr create`",), ()),
    ("Codex mirror carries equivalent multi-PR emission behavior", "codex", ("autopilot_continuation",), ()),
    ("Codex mirror carries equivalent multi-PR emission behavior", "codex", ("Never report completion while",), ()),
    ("Codex mirror carries equivalent multi-PR emission behavior", "codex", ("gh pr create --base <base> --head <head> --body-file <body-file>",), ()),
    ("Codex mirror carries equivalent multi-PR emission behavior", "codex", ("restack",), ()),
    ("Codex mirror carries equivalent multi-PR emission behavior", "codex", ("MUST NOT modify `.github/workflows/pr-checks.yml`",), ()),
    ("Claude reference blocks skeleton-quality UAT before PR creation", "claude", ("validate-uat-runbook",), ()),
    ("Claude reference blocks skeleton-quality UAT before PR creation", "claude", ("STOP before PR-body generation or PR creation",), ()),
    ("Claude reference blocks skeleton-quality UAT before PR creation", "claude", (), ("A plain skeleton is an acceptable fallback",)),
    ("Codex reference blocks skeleton-quality UAT before PR creation", "codex", ("validate-uat-runbook",), ()),
    ("Codex reference blocks skeleton-quality UAT before PR creation", "codex", ("STOP before PR-body generation or PR creation",), ()),
    ("Codex reference blocks skeleton-quality UAT before PR creation", "codex", (), ("A plain skeleton is an acceptable fallback",)),
    ("Claude reference requires current feature-local packet", "claude", ("specs/<feature>/.process/pr-packets/<packet-id>.json",), ()),
    ("Codex reference requires current feature-local packet", "codex", ("specs/<feature>/.process/pr-packets/<packet-id>.json",), ()),
    ("Claude reference consumes read-only packet validation in memory", "claude", ("data.stdout_json", "writes_state=false"), ()),
    ("Codex reference consumes read-only packet validation in memory", "codex", ("data.stdout_json", "writes_state=false"), ()),
    ("Claude reference keeps restack deferred with explicit fallback", "claude", ("runner `restack` operation is\ndeferred, has no authoritative request", "gh pr edit <number> --base <branch>"), ()),
    ("Codex reference keeps restack deferred with explicit fallback", "codex", ("runner `restack` operation is\ndeferred, has no authoritative request", "gh pr edit <number> --base <branch>"), ()),
)


class PostImplementationReferenceTests(unittest.TestCase):
    def test_reference_contract(self) -> None:
        bodies = {
            "claude": CLAUDE_REF.read_text(encoding="utf-8"),
            "codex": CODEX_REF.read_text(encoding="utf-8"),
        }
        for name, host, required, forbidden in CONTRACT_CHECKS:
            with self.subTest(msg=name):
                for phrase in required:
                    self.assertIn(phrase, bodies[host])
                for phrase in forbidden:
                    self.assertNotIn(phrase, bodies[host])


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(PostImplementationReferenceTests)


def main() -> int:
    return run_counted(build_suite(), label="test-post-implementation-reference")


if __name__ == "__main__":
    raise SystemExit(main())
