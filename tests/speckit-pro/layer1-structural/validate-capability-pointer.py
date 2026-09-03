#!/usr/bin/env python3
"""Layer-1 pointer-coverage check (port of validate-capability-pointer.sh, FR-003).

XPLAT-010 count-parity port (T019, US2). Python 3.11+ standard library only.
Every former ``_pass``/``_fail`` execution maps to one counted ``subTest`` unit;
bash check names are reproduced verbatim via ``subTest(msg=...)`` for a 1:1
inventory match against the committed baseline.

Environment-path normalization: the bash predecessor interpolates the *absolute*
agents-directory path into the ``agents directory exists (...)`` check name. That
absolute repo-root prefix is environment noise (it differs per checkout — CI
checks out under a different absolute root), never part of the check identity, and
would violate the privacy hard constraint if committed. The port emits — and the committed
baseline records — the repo-relative directory (``speckit-pro/agents``). Count and
check identity are preserved; only the environment-specific prefix is normalized.

Baseline: ``tests/speckit-pro/parity/bash-to-python/validate-capability-pointer-baseline.txt``
(TOTAL: 52).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

AGENTS_DIR = PLUGIN_ROOT / "agents"
CODEX_AGENTS_DIR = PLUGIN_ROOT / "codex-agents"

DIRECTIVE_MARKER = "capability-discovery.md"
GROUNDING_MARKER = "grounding.md"
CAPABILITY_NOTE = "Capability path:"

# Out-of-scope exclusion sets — the ONLY agents allowed to omit the pointer.
CC_EXCLUSIONS = frozenset(
    {
        "consensus-synthesizer",
        "phase-executor",
        # These two roles are deliberately confined to the snapshot broker and
        # must return only a receipt. Capability discovery, grounding files,
        # and evidence-note prose are outside that closed surface.
        "sweep-analyst",
        "sweep-classifier",
    }
)
CODEX_EXCLUSIONS = frozenset({"autopilot-fast-helper", "phase-executor"})
# Approved-equivalent allowlist — currently empty (every in-scope agent references
# the directive directly). Format when non-empty: "<runtime>:<agent-name>".
APPROVED_EQUIVALENTS: frozenset[str] = frozenset()


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _excluded(runtime: str, name: str) -> bool:
    return name in (CC_EXCLUSIONS if runtime == "claude" else CODEX_EXCLUSIONS)


def _approved_equivalent(runtime: str, name: str) -> bool:
    return f"{runtime}:{name}" in APPROVED_EQUIVALENTS


class ValidateCapabilityPointer(unittest.TestCase):
    def _check_runtime(self, runtime: str, directory: Path, ext: str) -> None:
        rel_dir = _rel(directory)
        with self.subTest(msg=f"{runtime}: agents directory exists ({rel_dir})"):
            self.assertTrue(directory.is_dir(), f"agents directory missing: {rel_dir}")
        if not directory.is_dir():
            return

        files = sorted(f for f in directory.glob(f"*.{ext}") if f.is_file())
        with self.subTest(msg=f"{runtime}: active-agent glob matched at least one agent"):
            self.assertTrue(files, f"no active agents found under {rel_dir}/*.{ext}")
        if not files:
            return

        for agent_file in files:
            agent_name = agent_file.name[: -(len(ext) + 1)]
            if _excluded(runtime, agent_name):
                continue
            text = agent_file.read_text(encoding="utf-8", errors="replace")

            with self.subTest(
                msg=f"{runtime}: in-scope agent '{agent_name}' references {DIRECTIVE_MARKER} (or approved equivalent)"
            ):
                self.assertTrue(
                    DIRECTIVE_MARKER in text or _approved_equivalent(runtime, agent_name),
                    f"uncovered in-scope agent: {runtime} '{agent_name}' references neither "
                    f"{DIRECTIVE_MARKER} nor an approved equivalent",
                )

            with self.subTest(msg=f"{runtime}: in-scope agent '{agent_name}' references {GROUNDING_MARKER}"):
                self.assertIn(GROUNDING_MARKER, text, f"{runtime} '{agent_name}' does not reference {GROUNDING_MARKER}")

            with self.subTest(
                msg=f"{runtime}: in-scope agent '{agent_name}' output requires the grounding evidence note"
            ):
                self.assertIn(
                    CAPABILITY_NOTE, text,
                    f"in-scope agent '{agent_name}' ({runtime}) output format does not require the grounding evidence note",
                )

    def test_pointer_coverage(self) -> None:
        self._check_runtime("claude", AGENTS_DIR, "md")
        self._check_runtime("codex", CODEX_AGENTS_DIR, "toml")


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateCapabilityPointer)


def main() -> int:
    return run_counted(build_suite(), label="validate-capability-pointer")


if __name__ == "__main__":
    raise SystemExit(main())
