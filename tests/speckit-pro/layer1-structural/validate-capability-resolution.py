#!/usr/bin/env python3
"""Layer-1 target-resolution check (port of validate-capability-resolution.sh, FR-004).

XPLAT-010 count-parity port (T020, US2). Python 3.11+ standard library only. For
each in-scope agent's directive/grounding reference, extract the repo-root-relative
path token verbatim and assert it re-roots under BOTH built trees
(``dist/claude/<token>`` and ``dist/codex/<token>``).

Every former ``_pass``/``_fail`` execution maps to one counted ``subTest`` unit;
names reproduced verbatim via ``subTest(msg=...)`` for a 1:1 baseline match.

Environment-path normalization (privacy hard constraint): the bash predecessor
interpolates the *absolute* agents-directory and ``dist/**`` tree paths into four
check names. That absolute repo-root prefix is environment noise (differs per
checkout), not check identity, and cannot be committed. The port emits — and the
committed baseline records — the repo-relative form (``speckit-pro/agents``,
``dist/claude`` …). Count and identity preserved; only the environment prefix is
normalized. The extracted path tokens themselves are already repo-relative
(``speckit-pro/...``), so ``resolves under ...`` names are verbatim.

Baseline: ``tests/speckit-pro/parity/bash-to-python/validate-capability-resolution-baseline.txt``
(TOTAL: 43).
"""

from __future__ import annotations

import re
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
DIST_CLAUDE = REPO_ROOT / "dist" / "claude"
DIST_CODEX = REPO_ROOT / "dist" / "codex"

DIRECTIVE_MARKER = "capability-discovery.md"
GROUNDING_MARKER = "grounding.md"
PATH_TOKEN_RE = re.compile(r"speckit-pro/[A-Za-z0-9._/-]*capability-discovery\.md")
GROUNDING_TOKEN_RE = re.compile(r"speckit-pro/[A-Za-z0-9._/-]*grounding\.md")

CC_EXCLUSIONS = frozenset({"consensus-synthesizer", "gate-validator", "phase-executor"})
CODEX_EXCLUSIONS = frozenset({"autopilot-fast-helper", "phase-executor"})


def _rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _excluded(runtime: str, name: str) -> bool:
    return name in (CC_EXCLUSIONS if runtime == "claude" else CODEX_EXCLUSIONS)


class ValidateCapabilityResolution(unittest.TestCase):
    def _collect_runtime(self, runtime: str, directory: Path, ext: str, found_tokens: list[str]) -> None:
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
            # Pointer coverage is the pointer check's job; here we only resolve
            # tokens that exist. A missing reference is skipped without a token.
            if DIRECTIVE_MARKER not in text:
                continue

            directive_tokens = sorted(set(PATH_TOKEN_RE.findall(text)))
            for token in directive_tokens:
                if token not in found_tokens:
                    found_tokens.append(token)
            with self.subTest(msg=f"{runtime}: extracted directive path token(s) from in-scope agent '{agent_name}'"):
                self.assertTrue(directive_tokens, f"agent references {DIRECTIVE_MARKER} but no path token matched in {_rel(agent_file)}")

            if GROUNDING_MARKER in text:
                grounding_tokens = sorted(set(GROUNDING_TOKEN_RE.findall(text)))
                for token in grounding_tokens:
                    if token not in found_tokens:
                        found_tokens.append(token)
                with self.subTest(msg=f"{runtime}: extracted grounding path token(s) from in-scope agent '{agent_name}'"):
                    self.assertTrue(grounding_tokens, f"agent references {GROUNDING_MARKER} but no path token matched in {_rel(agent_file)}")

    def test_target_resolution(self) -> None:
        found_tokens: list[str] = []
        self._collect_runtime("claude", AGENTS_DIR, "md", found_tokens)
        self._collect_runtime("codex", CODEX_AGENTS_DIR, "toml", found_tokens)

        with self.subTest(msg="at least one directive path token was collected from the inventory"):
            self.assertTrue(found_tokens, "no directive path tokens collected — refusing to report success on zero work")
        if not found_tokens:
            return

        with self.subTest(msg=f"built Claude payload tree exists ({_rel(DIST_CLAUDE)})"):
            self.assertTrue(DIST_CLAUDE.is_dir(), f"missing built tree: {_rel(DIST_CLAUDE)}")
        with self.subTest(msg=f"built Codex payload tree exists ({_rel(DIST_CODEX)})"):
            self.assertTrue(DIST_CODEX.is_dir(), f"missing built tree: {_rel(DIST_CODEX)}")

        for token in found_tokens:
            with self.subTest(msg=f"resolves under dist/claude: {token}"):
                self.assertTrue((DIST_CLAUDE / token).is_file(), f"absent in built Claude tree: dist/claude/{token}")
            with self.subTest(msg=f"resolves under dist/codex: {token}"):
                self.assertTrue((DIST_CODEX / token).is_file(), f"absent in built Codex tree: dist/codex/{token}")


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateCapabilityResolution)


def main() -> int:
    return run_counted(build_suite(), label="validate-capability-resolution")


if __name__ == "__main__":
    raise SystemExit(main())
