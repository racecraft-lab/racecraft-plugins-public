#!/usr/bin/env python3
"""Validate repository agent-instruction file shape and drift guards."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

EXPECTED_AGENT_DIRS = (
    Path("."),
    Path("speckit-pro"),
    Path("tests/speckit-pro"),
    Path("docs-site"),
)
CLAUDE_WRAPPER = "@./AGENTS.md\n"
GEMINI_WRAPPER = "@./AGENTS.md\n"
COPILOT_POINTER = (
    "# Copilot Instructions\n"
    "\n"
    "Follow the repository agent contract in `AGENTS.md`. Do not maintain separate\n"
    "Copilot-specific project rules here.\n"
)
AGENT_CONTEXT_BUDGET_BYTES = 32_768
SKIP_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".specify",
    ".worktrees",
    "dist",
    "node_modules",
}
SKIP_PREFIXES = (
    Path("docs-site/src/content/docs/reference"),
    Path("tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache"),
)
INSTRUCTION_NAMES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}
FORBIDDEN_AGENT_PHRASES = (
    "<!-- SPECKIT START -->",
    "<!-- SPECKIT END -->",
    "Auto-generated from feature plans",
    "## Active Technologies",
    "## Recent Changes",
    "### Test Layers",
    "xplat-008",
    "xplat-009",
    "xplat-010",
)


def _display(path: Path) -> str:
    text = path.as_posix()
    return "." if text == "." else text


def _is_skipped(rel_dir: Path) -> bool:
    return any(rel_dir == prefix or prefix in rel_dir.parents for prefix in SKIP_PREFIXES)


def find_instruction_files(repo_root: Path) -> dict[str, list[Path]]:
    files = {name: [] for name in INSTRUCTION_NAMES}
    for dirpath, dirnames, filenames in os.walk(repo_root):
        current = Path(dirpath)
        rel_dir = current.relative_to(repo_root)
        if _is_skipped(rel_dir):
            dirnames[:] = []
            continue
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_NAMES]
        for filename in filenames:
            if filename in files:
                files[filename].append((current / filename).relative_to(repo_root))
    for matches in files.values():
        matches.sort()
    return files


def _read(repo_root: Path, rel_path: Path) -> str:
    return (repo_root / rel_path).read_text(encoding="utf-8")


def collect_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []
    expected_dirs = set(EXPECTED_AGENT_DIRS)
    files = find_instruction_files(repo_root)
    agent_dirs = {path.parent for path in files["AGENTS.md"]}

    if agent_dirs != expected_dirs:
        expected = ", ".join(_display(path / "AGENTS.md") for path in sorted(expected_dirs))
        actual = ", ".join(_display(path) for path in files["AGENTS.md"]) or "<none>"
        errors.append(f"AGENTS.md files must be exactly [{expected}], got [{actual}]")

    for directory in sorted(expected_dirs):
        agents = directory / "AGENTS.md"
        claude = directory / "CLAUDE.md"
        gemini = directory / "GEMINI.md"
        if not (repo_root / agents).is_file():
            continue
        if not (repo_root / claude).is_file():
            errors.append(f"missing Claude wrapper: {_display(claude)}")
        elif _read(repo_root, claude) != CLAUDE_WRAPPER:
            errors.append(f"{_display(claude)} must contain only {CLAUDE_WRAPPER.strip()!r}")
        if not (repo_root / gemini).is_file():
            errors.append(f"missing Gemini wrapper: {_display(gemini)}")
        elif _read(repo_root, gemini) != GEMINI_WRAPPER:
            errors.append(f"{_display(gemini)} must contain only {GEMINI_WRAPPER.strip()!r}")

    for filename in ("CLAUDE.md", "GEMINI.md"):
        expected_files = {directory / filename for directory in expected_dirs}
        actual_files = set(files[filename])
        extras = sorted(actual_files - expected_files)
        if extras:
            errors.append(
                f"unexpected {filename} files: {', '.join(_display(path) for path in extras)}"
            )

    total_bytes = 0
    for path in files["AGENTS.md"]:
        text = _read(repo_root, path)
        total_bytes += len(text.encode("utf-8"))
        for phrase in FORBIDDEN_AGENT_PHRASES:
            if phrase in text:
                errors.append(f"{_display(path)} contains stale agent-context exhaust: {phrase}")
    if total_bytes > AGENT_CONTEXT_BUDGET_BYTES:
        errors.append(
            f"AGENTS.md context is {total_bytes} bytes, above {AGENT_CONTEXT_BUDGET_BYTES}"
        )

    copilot = repo_root / ".github" / "copilot-instructions.md"
    if not copilot.is_file():
        errors.append("missing .github/copilot-instructions.md")
    elif copilot.read_text(encoding="utf-8") != COPILOT_POINTER:
        errors.append(".github/copilot-instructions.md must only point to AGENTS.md")

    return errors


class ValidateAgentInstructions(unittest.TestCase):
    def test_agent_instruction_files_do_not_drift(self) -> None:
        errors = collect_errors(REPO_ROOT)
        with self.subTest(msg="agent instruction files have canonical wrapper shape"):
            self.assertFalse(errors, "\n".join(errors))


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateAgentInstructions)


def main() -> int:
    # Sweeps whatever specs exist rather than depending on a named one, so
    # it is archive-safe by construction: an absent feature folder
    # contributes nothing. See install_specs_read_guard.
    return run_counted(
        build_suite(), label="validate-agent-instructions", allow_live_specs=True
    )


if __name__ == "__main__":
    raise SystemExit(main())
