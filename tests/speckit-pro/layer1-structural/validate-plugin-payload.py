#!/usr/bin/env python3
"""Guard: shipped platform payloads must be clean (port of validate-plugin-payload.sh).

XPLAT-010 count-parity port (T030, US2). Python 3.11+ standard library only.
``speckit-pro/`` is the rich authoring source tree (Claude + Codex variants side
by side); the marketplaces install generated ``dist/`` payloads so each platform
sees only its own manifest, skills, agents, hooks, and support files. This guard
rebuilds the payloads and asserts they are complete, exclusive, deterministic,
and installed from the ``dist/`` paths. Every former ``assert_*``/``_pass``/
``_fail`` execution maps to one counted ``subTest`` unit; names reproduced
verbatim via ``subTest(msg=...)`` for a 1:1 baseline match — including the two
``forbidden``-exclusion loops (4 Claude + 3 Codex units).

Behavior preserved from the bash predecessor: it invokes the real payload builder
(``python3 scripts/build-plugin-payloads.py``) at the "rebuilds from scratch" and
"deterministic" checks; the port does the same via ``subprocess`` (argv list,
``shell=False``). The builder is deterministic, so re-running it leaves ``dist/``
byte-identical.

Baseline: ``tests/speckit-pro/parity/bash-to-python/validate-plugin-payload-baseline.txt``
(TOTAL: 23).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

SOURCE_ROOT = REPO_ROOT / "speckit-pro"
BUILDER = REPO_ROOT / "scripts" / "build-plugin-payloads.py"
CLAUDE_PAYLOAD = REPO_ROOT / "dist" / "claude" / "speckit-pro"
CODEX_PAYLOAD = REPO_ROOT / "dist" / "codex" / "speckit-pro"

# rg pattern from the bash predecessor: source-tree skill path escapes.
PATH_ESCAPE_RE = re.compile(r"\.\./\.\./(?:skills|codex-skills)/|\.\./\.\./\.\./(?:skills|codex-skills)/")


def run_builder() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BUILDER)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        shell=False,
        check=False,
    )


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json_file(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise AssertionError(
            f"unable to read {_display_path(path)}: {exc.__class__.__name__}: {exc}"
        ) from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"malformed JSON in {_display_path(path)}: {exc.msg} "
            f"(line {exc.lineno}, column {exc.colno})"
        ) from exc


def count_skill_entrypoints(root: Path) -> int:
    """Mirror `find <root> -mindepth 2 -maxdepth 2 -type f -name SKILL.md | wc -l`."""
    if not root.is_dir():
        return 0
    return sum(1 for p in root.glob("*/SKILL.md") if p.is_file())


def skill_entrypoint_set(root: Path) -> str:
    """Mirror `(cd <root> && find . -mindepth 2 -maxdepth 2 -type f -name SKILL.md | LC_ALL=C sort)`."""
    if not root.is_dir():
        return ""
    entries = [f"./{p.relative_to(root).as_posix()}" for p in root.glob("*/SKILL.md") if p.is_file()]
    return "\n".join(sorted(entries))


def payload_fingerprint() -> str:
    """Mirror the sorted `shasum -a 256` fingerprint over both payload trees."""
    files: list[Path] = []
    for base in (CLAUDE_PAYLOAD, CODEX_PAYLOAD):
        if base.is_dir():
            files.extend(p for p in base.rglob("*") if p.is_file())
    lines = []
    for path in sorted(files, key=lambda p: p.as_posix()):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.as_posix()}")
    return "\n".join(lines)


class ValidatePluginPayload(unittest.TestCase):
    def test_payload(self) -> None:
        with self.subTest(msg="payload builder exists"):
            self.assertTrue(BUILDER.is_file(), f"file not found: {BUILDER}")

        with self.subTest(msg="payload builder rebuilds from scratch"):
            completed = run_builder()
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

        with self.subTest(msg="Claude payload directory exists"):
            self.assertTrue(CLAUDE_PAYLOAD.is_dir(), f"missing {CLAUDE_PAYLOAD}")

        with self.subTest(msg="Codex payload directory exists"):
            self.assertTrue(CODEX_PAYLOAD.is_dir(), f"missing {CODEX_PAYLOAD}")

        claude_source = ""
        with self.subTest(msg="Claude marketplace installs the Claude dist payload"):
            claude_market = load_json_file(REPO_ROOT / ".claude-plugin" / "marketplace.json")
            claude_source = claude_market["plugins"][0]["source"]
            self.assertEqual("./dist/claude/speckit-pro", claude_source, "Claude marketplace source")

        codex_source = ""
        with self.subTest(msg="Codex marketplace installs the Codex dist payload"):
            codex_market = load_json_file(REPO_ROOT / ".agents" / "plugins" / "marketplace.json")
            codex_source = codex_market["plugins"][0]["source"]["path"]
            self.assertEqual("./dist/codex/speckit-pro", codex_source, "Codex marketplace source.path")

        claude_rel = claude_source[2:] if claude_source.startswith("./") else claude_source
        with self.subTest(msg="Claude marketplace path resolves to a payload"):
            self.assertTrue(
                bool(claude_rel) and (REPO_ROOT / claude_rel).is_dir(),
                f"missing {_display_path(REPO_ROOT / claude_rel)}",
            )

        codex_rel = codex_source[2:] if codex_source.startswith("./") else codex_source
        with self.subTest(msg="Codex marketplace path resolves to a payload"):
            self.assertTrue(
                bool(codex_rel) and (REPO_ROOT / codex_rel).is_dir(),
                f"missing {_display_path(REPO_ROOT / codex_rel)}",
            )

        for forbidden in (".codex-plugin", "codex-skills", "codex-agents", "codex-hooks.json"):
            with self.subTest(msg=f"Claude payload excludes {forbidden}"):
                self.assertFalse((CLAUDE_PAYLOAD / forbidden).exists(), f"{forbidden} exists in the Claude payload")

        for forbidden in (".claude-plugin", "codex-skills", "agents"):
            with self.subTest(msg=f"Codex payload excludes {forbidden}"):
                self.assertFalse((CODEX_PAYLOAD / forbidden).exists(), f"{forbidden} exists in the Codex payload")

        with self.subTest(msg="Claude payload keeps the Claude skill set"):
            self.assertEqual(
                count_skill_entrypoints(SOURCE_ROOT / "skills"),
                count_skill_entrypoints(CLAUDE_PAYLOAD / "skills"),
                "Claude skill count",
            )

        with self.subTest(msg="Codex payload keeps exactly the Codex skill set"):
            self.assertEqual(
                skill_entrypoint_set(SOURCE_ROOT / "codex-skills"),
                skill_entrypoint_set(CODEX_PAYLOAD / "skills"),
                "Codex skill entrypoints",
            )

        with self.subTest(msg="Codex payload manifest exposes skills at ./skills/"):
            codex_manifest = load_json_file(CODEX_PAYLOAD / ".codex-plugin" / "plugin.json")
            self.assertEqual("./skills/", codex_manifest["skills"], "Codex manifest skills")

        with self.subTest(msg="Codex payload has no duplicate nested skill entrypoints"):
            skills_dir = CODEX_PAYLOAD / "skills"
            nested = 0
            if skills_dir.is_dir():
                nested = sum(
                    1
                    for p in skills_dir.rglob("SKILL.md")
                    if p.is_file() and len(p.relative_to(skills_dir).parts) >= 3
                )
            self.assertEqual(0, nested, "nested Codex SKILL.md count")

        with self.subTest(msg="Payload files do not reference source-tree skill paths"):
            matches: list[str] = []
            for base in (CLAUDE_PAYLOAD, CODEX_PAYLOAD):
                if not base.is_dir():
                    continue
                for path in base.rglob("*"):
                    if not path.is_file():
                        continue
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    if PATH_ESCAPE_RE.search(text):
                        matches.append(path.as_posix())
            self.assertEqual([], matches, "source-tree path references")

        with self.subTest(msg="Payload rebuild is deterministic"):
            first_fingerprint = payload_fingerprint()
            completed = run_builder()
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            second_fingerprint = payload_fingerprint()
            self.assertEqual(first_fingerprint, second_fingerprint, "payload fingerprint")

        with self.subTest(msg="release-please extra-files stay inside package paths"):
            config = load_json_file(REPO_ROOT / "release-please-config.json")
            bad: list[str] = []
            for package, cfg in config.get("packages", {}).items():
                for extra in cfg.get("extra-files", []):
                    path = extra.get("path", "") if isinstance(extra, dict) else ""
                    if path.startswith("../") or "/../" in path or path == "..":
                        bad.append(f"{package}: {path}")
            self.assertEqual([], bad, "release-please illegal pathing characters")

        with self.subTest(msg="CI committed payload files are current"):
            import os

            if os.environ.get("GITHUB_ACTIONS") == "true":
                diff = subprocess.run(
                    [
                        "git", "-C", str(REPO_ROOT), "diff", "--exit-code", "--",
                        "dist", ".claude-plugin/marketplace.json",
                        ".agents/plugins/marketplace.json", "release-please-config.json",
                    ],
                    text=True,
                    capture_output=True,
                    shell=False,
                    check=False,
                )
                self.assertEqual(0, diff.returncode, diff.stdout + diff.stderr)
            else:
                self.assertTrue(True)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidatePluginPayload)


def main() -> int:
    return run_counted(build_suite(), label="validate-plugin-payload")


if __name__ == "__main__":
    raise SystemExit(main())
