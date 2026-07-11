#!/usr/bin/env python3
"""Cross-platform Claude Code <-> Codex parity checks (port of validate-codex-parity.sh).

XPLAT-010 count-parity port (T024, US2). Python 3.11+ standard library only.
Asserts version/marketplace parity, agent parity in both directions (honouring
the CC-only and Codex-only exception lists), full CC<->Codex skill coverage,
Codex skill metadata sidecars, and that every ``../../skills/**.md`` reference in
a Codex ``SKILL.md`` resolves. Every former ``assert_*``/``_pass``/``_fail``
execution maps to one counted ``subTest`` unit; names reproduced verbatim via
``subTest(msg=...)`` for a 1:1 baseline match.

Two check names interpolate live data the script reads at runtime — the shared
plugin version and the marketplace name — so ``.claude-plugin/plugin.json`` and
the two ``marketplace.json`` files are baseline regeneration triggers alongside
the agent/skill directory inventories (count-parity contract §2, rule 4).

Directory globs and the reference-path ``sort -u`` are reproduced with sorted
inventories; the reference extraction mirrors the bash ``grep -oE`` per-line
match. Baseline:
``tests/speckit-pro/parity/xplat-010/validate-codex-parity-baseline.txt``
(TOTAL: 81).
"""

from __future__ import annotations

import json
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

CC_PLUGIN = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
CODEX_PLUGIN = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
CC_MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CODEX_MARKETPLACE = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
AGENTS_DIR = PLUGIN_ROOT / "agents"
CODEX_AGENTS_DIR = PLUGIN_ROOT / "codex-agents"
SKILLS_DIR = PLUGIN_ROOT / "skills"
CODEX_SKILLS_DIR = PLUGIN_ROOT / "codex-skills"

CC_ONLY_AGENTS = frozenset({"gate-validator", "consensus-synthesizer"})
CODEX_ONLY_AGENTS = frozenset({"autopilot-fast-helper"})

REF_RE = re.compile(r"\.\./\.\./skills/[^)]+\.md")


def _json_field(path: Path, key: str) -> str:
    """Mirror ``jq -r '.<key>'``: the value's string form, or ``null`` on
    missing key / unreadable / invalid JSON."""
    try:
        value = json.loads(path.read_text(encoding="utf-8")).get(key)
    except (json.JSONDecodeError, OSError, AttributeError):
        return "null"
    return "null" if value is None else str(value)


def _sorted_files(directory: Path, suffix: str) -> list[Path]:
    return sorted((p for p in directory.glob(f"*{suffix}") if p.is_file()), key=lambda p: p.name)


def _sorted_subdirs(directory: Path) -> list[Path]:
    return sorted((p for p in directory.iterdir() if p.is_dir()), key=lambda p: p.name)


class ValidateCodexParity(unittest.TestCase):
    def test_codex_parity(self) -> None:
        # --- Version Parity ---
        with self.subTest(msg="both plugin.json files exist"):
            self.assertTrue(
                CC_PLUGIN.is_file() and CODEX_PLUGIN.is_file(),
                f"missing one or both plugin.json files (CC: {CC_PLUGIN}, Codex: {CODEX_PLUGIN})",
            )
        if CC_PLUGIN.is_file() and CODEX_PLUGIN.is_file():
            cc_version = _json_field(CC_PLUGIN, "version")
            codex_version = _json_field(CODEX_PLUGIN, "version")
            with self.subTest(msg=f"CC and Codex plugin.json versions match ({cc_version})"):
                self.assertEqual(cc_version, codex_version, f"versions must match: CC={cc_version}, Codex={codex_version}")

        # --- Marketplace Parity ---
        with self.subTest(msg="both marketplace.json files exist"):
            self.assertTrue(
                CC_MARKETPLACE.is_file() and CODEX_MARKETPLACE.is_file(),
                f"missing one or both marketplace.json files (CC: {CC_MARKETPLACE}, Codex: {CODEX_MARKETPLACE})",
            )
        if CC_MARKETPLACE.is_file() and CODEX_MARKETPLACE.is_file():
            cc_marketplace_name = _json_field(CC_MARKETPLACE, "name")
            codex_marketplace_name = _json_field(CODEX_MARKETPLACE, "name")
            with self.subTest(msg=f"CC and Codex marketplace names match ({cc_marketplace_name})"):
                self.assertEqual(
                    cc_marketplace_name, codex_marketplace_name,
                    f"marketplace names must match: CC={cc_marketplace_name}, Codex={codex_marketplace_name}",
                )

        # --- Agent Parity (CC -> Codex) ---
        if AGENTS_DIR.is_dir() and CODEX_AGENTS_DIR.is_dir():
            for cc_agent_file in _sorted_files(AGENTS_DIR, ".md"):
                agent_name = cc_agent_file.name[: -len(".md")]
                if agent_name in CC_ONLY_AGENTS:
                    continue
                with self.subTest(msg=f"codex-agents/{agent_name}.toml exists for CC agent"):
                    self.assertTrue(
                        (CODEX_AGENTS_DIR / f"{agent_name}.toml").is_file(),
                        f"file not found: {CODEX_AGENTS_DIR / (agent_name + '.toml')}",
                    )
        else:
            with self.subTest(msg="agents/ and codex-agents/ directories exist"):
                self.fail(f"one or both agent directories missing (CC: {AGENTS_DIR}, Codex: {CODEX_AGENTS_DIR})")

        # --- Agent Parity (Codex -> CC) ---
        if AGENTS_DIR.is_dir() and CODEX_AGENTS_DIR.is_dir():
            for codex_agent_file in _sorted_files(CODEX_AGENTS_DIR, ".toml"):
                agent_name = codex_agent_file.name[: -len(".toml")]
                if agent_name in CODEX_ONLY_AGENTS:
                    continue
                with self.subTest(msg=f"agents/{agent_name}.md exists for Codex agent"):
                    self.assertTrue(
                        (AGENTS_DIR / f"{agent_name}.md").is_file(),
                        f"file not found: {AGENTS_DIR / (agent_name + '.md')}",
                    )

        # --- CC Skill Coverage (CC -> Codex) ---
        if SKILLS_DIR.is_dir() and CODEX_SKILLS_DIR.is_dir():
            for skill_dir in _sorted_subdirs(SKILLS_DIR):
                skill_name = skill_dir.name
                with self.subTest(msg=f"skills/{skill_name}/SKILL.md exists"):
                    self.assertTrue((SKILLS_DIR / skill_name / "SKILL.md").is_file(), f"file not found: {SKILLS_DIR / skill_name / 'SKILL.md'}")
                with self.subTest(msg=f"codex-skills/{skill_name}/SKILL.md exists for CC skill"):
                    self.assertTrue((CODEX_SKILLS_DIR / skill_name / "SKILL.md").is_file(), f"file not found: {CODEX_SKILLS_DIR / skill_name / 'SKILL.md'}")
        else:
            with self.subTest(msg="skills/ and codex-skills/ directories exist"):
                self.fail(f"one or both skills directories missing (CC: {SKILLS_DIR}, Codex: {CODEX_SKILLS_DIR})")

        # --- Codex Skill Metadata Sidecars ---
        if CODEX_SKILLS_DIR.is_dir():
            for skill_dir in _sorted_subdirs(CODEX_SKILLS_DIR):
                skill_name = skill_dir.name
                with self.subTest(msg=f"codex-skills/{skill_name}/agents/openai.yaml exists"):
                    self.assertTrue(
                        (CODEX_SKILLS_DIR / skill_name / "agents" / "openai.yaml").is_file(),
                        f"file not found: {CODEX_SKILLS_DIR / skill_name / 'agents' / 'openai.yaml'}",
                    )
        else:
            with self.subTest(msg="codex-skills/ directory exists for metadata sidecars"):
                self.fail(f"codex-skills directory missing: {CODEX_SKILLS_DIR}")

        # --- Shared Reference Integrity ---
        if SKILLS_DIR.is_dir() and CODEX_SKILLS_DIR.is_dir():
            for skill_dir in _sorted_subdirs(SKILLS_DIR):
                skill_name = skill_dir.name
                cc_refs = SKILLS_DIR / skill_name / "references"
                if not cc_refs.is_dir():
                    continue
                with self.subTest(msg=f"{skill_name}: CC skill references/ has at least one file"):
                    ref_count = sum(1 for p in cc_refs.iterdir() if p.is_file())
                    self.assertGreater(ref_count, 0, f"skills/{skill_name}/references/ exists but contains no files")

                codex_skill_file = CODEX_SKILLS_DIR / skill_name / "SKILL.md"
                if codex_skill_file.is_file():
                    text = codex_skill_file.read_text(encoding="utf-8", errors="replace")
                    matches: list[str] = []
                    for line in text.splitlines():
                        matches.extend(REF_RE.findall(line))
                    for rel_path in sorted(set(matches)):
                        stripped = rel_path.removeprefix("../../")
                        resolved = PLUGIN_ROOT / stripped
                        with self.subTest(msg=f"{skill_name}: referenced file exists ({stripped})"):
                            self.assertTrue(resolved.is_file(), f"file not found: {resolved}")


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateCodexParity)


def main() -> int:
    return run_counted(build_suite(), label="validate-codex-parity")


if __name__ == "__main__":
    raise SystemExit(main())
