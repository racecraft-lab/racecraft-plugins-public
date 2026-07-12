#!/usr/bin/env python3
"""Validate repository-local Spec Kit extension and generated-command integrity."""

from __future__ import annotations

import json
import re
import stat
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

EXTENSIONS_ROOT = REPO_ROOT / ".specify" / "extensions"
REGISTRY_PATH = EXTENSIONS_ROOT / ".registry"
HOOKS_PATH = REPO_ROOT / ".specify" / "extensions.yml"
FILE_ENTRY = re.compile(r'^\s+file:\s+["\']?([^"\']+)["\']?\s*$')
HOOK_COMMAND = re.compile(r"^\s+command:\s+([A-Za-z0-9_.-]+)\s*$")


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def declared_files(extension_dir: Path) -> list[Path]:
    manifest = extension_dir / "extension.yml"
    paths: list[Path] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = FILE_ENTRY.match(line)
        if match is not None:
            paths.append(extension_dir / match.group(1))
    return paths


def claude_skill_path(command: str) -> Path:
    return REPO_ROOT / ".claude" / "skills" / command.replace(".", "-") / "SKILL.md"


class ValidateSpecifyExtensions(unittest.TestCase):
    def test_extension_integrity(self) -> None:
        with self.subTest(msg="Spec Kit extension registry exists"):
            self.assertTrue(REGISTRY_PATH.is_file(), f"file not found: {REGISTRY_PATH}")
        with self.subTest(msg="Spec Kit extension hook configuration exists"):
            self.assertTrue(HOOKS_PATH.is_file(), f"file not found: {HOOKS_PATH}")
        if not REGISTRY_PATH.is_file() or not HOOKS_PATH.is_file():
            return

        registry = load_registry()
        extensions = registry.get("extensions") if isinstance(registry, dict) else None
        with self.subTest(msg="Spec Kit extension registry has schema 1.0 and extension records"):
            self.assertEqual(registry.get("schema_version"), "1.0")
            self.assertIsInstance(extensions, dict)
        if not isinstance(extensions, dict):
            return

        registered_commands: set[str] = set()
        for extension_id, record in sorted(extensions.items()):
            if not isinstance(record, dict) or record.get("enabled") is not True:
                continue
            extension_dir = EXTENSIONS_ROOT / extension_id
            with self.subTest(msg=f"enabled extension payload exists: {extension_id}"):
                self.assertTrue((extension_dir / "extension.yml").is_file())
            if not (extension_dir / "extension.yml").is_file():
                continue
            for path in declared_files(extension_dir):
                with self.subTest(msg=f"declared extension file exists: {path.relative_to(REPO_ROOT)}"):
                    self.assertTrue(path.is_file(), f"declared extension file not found: {path}")

            commands = record.get("registered_commands")
            if not isinstance(commands, dict):
                continue
            claude_commands = commands.get("claude", [])
            if not isinstance(claude_commands, list):
                continue
            for command in claude_commands:
                if not isinstance(command, str):
                    continue
                registered_commands.add(command)
                with self.subTest(msg=f"registered Claude extension command resolves: {command}"):
                    self.assertTrue(
                        claude_skill_path(command).is_file(),
                        f"generated Claude skill not found for {command}: {claude_skill_path(command)}",
                    )

        hook_commands = {
            match.group(1)
            for line in HOOKS_PATH.read_text(encoding="utf-8").splitlines()
            if (match := HOOK_COMMAND.match(line)) is not None
        }
        for command in sorted(hook_commands):
            with self.subTest(msg=f"configured extension hook resolves: {command}"):
                self.assertIn(command, registered_commands)

        verify = extensions.get("verify")
        with self.subTest(msg="Verify extension is pinned to repaired v1.0.3 payload"):
            self.assertIsInstance(verify, dict)
            self.assertEqual(verify.get("version") if isinstance(verify, dict) else None, "1.0.3")

        verify_loader = EXTENSIONS_ROOT / "verify" / "scripts" / "bash" / "load-config.sh"
        with self.subTest(msg="Verify Bash loader retains its declared executable mode"):
            self.assertTrue(
                verify_loader.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH),
                f"declared executable is not executable: {verify_loader}",
            )


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateSpecifyExtensions)


def main() -> int:
    return run_counted(build_suite(), label="validate-specify-extensions")


if __name__ == "__main__":
    raise SystemExit(main())
