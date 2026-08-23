#!/usr/bin/env python3
"""Layer-4 contract tests for sync-marketplace-versions.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "scripts" / "sync-marketplace-versions.py"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


def run_sync(cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    child_env = os.environ.copy()
    if env:
        child_env.update(env)
    child_env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=cwd,
        text=True,
        capture_output=True,
        env=child_env,
        shell=False,
        check=False,
    )


def create_marketplace(root: Path, content: str) -> None:
    path = root / ".claude-plugin" / "marketplace.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def create_codex_marketplace(root: Path, content: str) -> None:
    path = root / ".agents" / "plugins" / "marketplace.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def create_plugin(root: Path, name: str, version: str | None) -> None:
    path = root / name / ".claude-plugin" / "plugin.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"name": name, "description": "Test plugin"}
    if version is not None:
        payload["version"] = version
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def create_codex_plugin(root: Path, plugin_path: str, name: str, version: str) -> None:
    path = root / plugin_path / ".codex-plugin" / "plugin.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"name": name, "description": "Test Codex plugin", "version": version, "skills": "./skills/"}) + "\n", encoding="utf-8")


def marketplace_version(root: Path, index: int = 0) -> str:
    return json.loads((root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))["plugins"][index].get("version", "")


def codex_marketplace_version(root: Path, index: int = 0) -> str:
    return json.loads((root / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))["plugins"][index].get("version", "")


class SyncMarketplaceVersionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.work = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _marketplace(self, name: str, content: str) -> Path:
        root = self.work / name
        create_marketplace(root, content)
        return root

    def test_sync_marketplace_versions_contract(self) -> None:
        self.assertTrue(SCRIPT.is_file(), f"file not found: {SCRIPT}")
        self.assertTrue(os.access(SCRIPT, os.X_OK), f"file not executable: {SCRIPT}")

        root = self._marketplace(
            "mismatch",
            """
            {
              "name": "test-marketplace",
              "plugins": [
                { "name": "my-plugin", "source": "./my-plugin", "description": "Test", "version": "0.5.0" }
              ]
            }
            """,
        )
        create_plugin(root, "my-plugin", "0.6.0")
        result = run_sync(root)
        with self.subTest(msg="Version mismatch — plugin.json=0.6.0, marketplace=0.5.0 -> updated to 0.6.0"):
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.subTest(msg="Version mismatch — marketplace.json updated to 0.6.0"):
            self.assertEqual(marketplace_version(root), "0.6.0")
        with self.subTest(msg="Version mismatch — stdout reports the change"):
            self.assertIn("0.6.0", result.stdout)

        root = self._marketplace("matching", '{"name":"test","plugins":[{"name":"my-plugin","source":"./my-plugin","description":"Test","version":"1.0.0"}]}')
        create_plugin(root, "my-plugin", "1.0.0")
        result = run_sync(root)
        with self.subTest(msg="Matching versions — both at 1.0.0, exit 0"):
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.subTest(msg="Matching versions — no stdout output"):
            self.assertEqual(result.stdout, "")
        with self.subTest(msg="Matching versions — marketplace.json unchanged"):
            self.assertEqual(marketplace_version(root), "1.0.0")

        root = self._marketplace("missing-plugin", '{"name":"test","plugins":[{"name":"ghost-plugin","source":"./ghost-plugin","description":"No plugin"}]}')
        result = run_sync(root)
        with self.subTest(msg="Missing plugin.json — exit 1"):
            self.assertEqual(result.returncode, 1)
        with self.subTest(msg="Missing plugin.json — stderr has error message"):
            self.assertIn("not found", result.stderr)

        root = self._marketplace(
            "multi",
            '{"name":"test","plugins":[{"name":"plugin-a","source":"./plugin-a","version":"1.0.0"},{"name":"plugin-b","source":"./plugin-b","version":"2.0.0"}]}',
        )
        create_plugin(root, "plugin-a", "1.1.0")
        create_plugin(root, "plugin-b", "2.1.0")
        result = run_sync(root)
        with self.subTest(msg="Multi-plugin — two plugins with different mismatches, exit 0"):
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.subTest(msg="Multi-plugin — plugin-a updated to 1.1.0"):
            self.assertEqual(marketplace_version(root, 0), "1.1.0")
        with self.subTest(msg="Multi-plugin — plugin-b updated to 2.1.0"):
            self.assertEqual(marketplace_version(root, 1), "2.1.0")
        with self.subTest(msg="Multi-plugin — stdout reports both changes"):
            self.assertIn("plugin-a", result.stdout)
        with self.subTest(msg="Multi-plugin — stdout reports plugin-b change"):
            self.assertIn("plugin-b", result.stdout)

        root = self.work / "bad-marketplace"
        (root / ".claude-plugin").mkdir(parents=True)
        (root / ".claude-plugin" / "marketplace.json").write_text("{ INVALID JSON !!!\n", encoding="utf-8")
        result = run_sync(root)
        with self.subTest(msg="Malformed marketplace.json — exit 1"):
            self.assertEqual(result.returncode, 1)

        root = self._marketplace("bad-plugin", '{"name":"test","plugins":[{"name":"bad-plugin","source":"./bad-plugin"}]}')
        bad_plugin = root / "bad-plugin" / ".claude-plugin" / "plugin.json"
        bad_plugin.parent.mkdir(parents=True)
        bad_plugin.write_text("{ NOT VALID JSON ]\n", encoding="utf-8")
        result = run_sync(root)
        with self.subTest(msg="Malformed plugin.json — exit 1"):
            self.assertEqual(result.returncode, 1)

        root = self._marketplace("no-jq", '{"name":"test","plugins":[{"name":"my-plugin","source":"./my-plugin","version":"0.1.0"}]}')
        create_plugin(root, "my-plugin", "0.2.0")
        result = run_sync(root, env={"PATH": "/usr/bin:/bin"})
        with self.subTest(msg="No jq dependency — exit 0"):
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.subTest(msg="No jq dependency — version still syncs"):
            self.assertEqual(marketplace_version(root), "0.2.0")

        root = self.work / "empty"
        root.mkdir()
        result = run_sync(root)
        with self.subTest(msg="No marketplace.json in cwd — exit 1"):
            self.assertEqual(result.returncode, 1)
        with self.subTest(msg="Wrong cwd — stderr mentions marketplace.json"):
            self.assertIn("marketplace.json", result.stderr)

        root = self._marketplace("external-source", '{"name":"test","plugins":[{"name":"ext","source":"https://github.com/example/plugin.git"}]}')
        result = run_sync(root)
        with self.subTest(msg="External git URL source — skipped without error, exit 0"):
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.subTest(msg="Non-relative source — stderr mentions skipping"):
            self.assertIn("Skipping", result.stderr)

        root = self._marketplace("missing-version", '{"name":"test","plugins":[{"name":"noversion","source":"./noversion"}]}')
        create_plugin(root, "noversion", None)
        result = run_sync(root)
        with self.subTest(msg="No version in plugin.json — exit 1"):
            self.assertEqual(result.returncode, 1)
        with self.subTest(msg="No version in plugin.json — stderr mentions version"):
            self.assertIn("version", result.stderr)

        root = self._marketplace("bad-semver", '{"name":"test","plugins":[{"name":"twopart","source":"./twopart"}]}')
        create_plugin(root, "twopart", "1.0")
        result = run_sync(root)
        with self.subTest(msg="Version '1.0' (two-part) — exit 1"):
            self.assertEqual(result.returncode, 1)
        with self.subTest(msg="Version '1.0' — stderr mentions semver"):
            self.assertIn("semver", result.stderr)

        root = self._marketplace("bad-semver-alpha", '{"name":"test","plugins":[{"name":"alpha","source":"./alpha"}]}')
        create_plugin(root, "alpha", "abc")
        result = run_sync(root)
        with self.subTest(msg="Version 'abc' — exit 1"):
            self.assertEqual(result.returncode, 1)
        with self.subTest(msg="Version 'abc' — stderr mentions semver"):
            self.assertIn("semver", result.stderr)

        root = self._marketplace("error-routing", '{"name":"test","plugins":[{"name":"missing","source":"./missing"}]}')
        result = run_sync(root)
        with self.subTest(msg="Error scenario (missing plugin.json) — stdout is empty"):
            self.assertEqual(result.stdout, "")
        with self.subTest(msg="Error scenario — stderr has error message"):
            self.assertIn("Error", result.stderr)

        root = self._marketplace("propagate-missing-plugin", '{"name":"test","plugins":[{"name":"missing","source":"./missing"}]}')
        result = run_sync(root)
        with self.subTest(msg="Missing plugin.json → exit 1"):
            self.assertEqual(result.returncode, 1)

        root = self._marketplace("propagate-malformed-marketplace", "{ NOT JSON")
        result = run_sync(root)
        with self.subTest(msg="Malformed marketplace → exit 1"):
            self.assertEqual(result.returncode, 1)

        root = self.work / "propagate-missing-marketplace"
        root.mkdir()
        result = run_sync(root)
        with self.subTest(msg="No marketplace.json → exit 1"):
            self.assertEqual(result.returncode, 1)

        root = self._marketplace("missing-source", '{"name":"test","plugins":[{"name":"no-source","description":"No source"}]}')
        result = run_sync(root)
        with self.subTest(msg="Entry without source field — exit 1"):
            self.assertEqual(result.returncode, 1)
        with self.subTest(msg="Missing source — stderr mentions source"):
            self.assertIn("source", result.stderr)

        root = self._marketplace("empty-plugins", '{"name":"test","plugins":[]}')
        result = run_sync(root)
        with self.subTest(msg="Empty plugins array — exit 0"):
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.subTest(msg="Empty plugins array — stderr has info message"):
            self.assertIn("No plugins", result.stderr)

        root = self._marketplace("add-version", '{"name":"test","plugins":[{"name":"new-plugin","source":"./new-plugin","description":"Brand new"}]}')
        create_plugin(root, "new-plugin", "1.0.0")
        result = run_sync(root)
        with self.subTest(msg="Marketplace entry without version — sync adds version field, exit 0"):
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.subTest(msg="Marketplace entry without version — version field added as 1.0.0"):
            self.assertEqual(marketplace_version(root), "1.0.0")
        with self.subTest(msg="Marketplace entry without version — stdout reports the addition"):
            self.assertIn("1.0.0", result.stdout)

        root = self._marketplace("traversal", '{"name":"test","plugins":[{"name":"evil","source":"./../etc/passwd"}]}')
        result = run_sync(root)
        with self.subTest(msg="Source with .. segment — exit 1"):
            self.assertEqual(result.returncode, 1)
        with self.subTest(msg="Path traversal source — stderr mentions illegal .. segments"):
            self.assertIn("..", result.stderr)

        root = self._marketplace("nested-traversal", '{"name":"test","plugins":[{"name":"sneaky","source":"./foo/../../../etc"}]}')
        result = run_sync(root)
        with self.subTest(msg="Source with nested .. segment — exit 1"):
            self.assertEqual(result.returncode, 1)

        root = self._marketplace("non-array", '{"name":"test","plugins":"not-an-array"}')
        result = run_sync(root)
        with self.subTest(msg="plugins field is a string (not array) — exit 1"):
            self.assertEqual(result.returncode, 1)
        with self.subTest(msg="plugins is string — stderr mentions not an array"):
            self.assertIn("not an array", result.stderr)

        root = self._marketplace("object-plugins", '{"name":"test","plugins":{"foo":"bar"}}')
        result = run_sync(root)
        with self.subTest(msg="plugins field is an object (not array) — exit 1"):
            self.assertEqual(result.returncode, 1)

        root = self._marketplace("codex", '{"name":"test","plugins":[]}')
        create_codex_marketplace(
            root,
            '{"name":"test-codex","plugins":[{"name":"codex-plugin","source":{"source":"local","path":"./dist/codex/codex-plugin"},"version":"0.1.0"}]}',
        )
        create_codex_plugin(root, "dist/codex/codex-plugin", "codex-plugin", "0.2.0")
        result = run_sync(root)
        with self.subTest(msg="Codex source.path schema — version mismatch updates from .codex-plugin/plugin.json"):
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.subTest(msg="Codex source.path schema — marketplace version updated"):
            self.assertEqual(codex_marketplace_version(root), "0.2.0")
        source = json.loads((root / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))["plugins"][0]["source"]
        with self.subTest(msg="Codex source.path schema — source object preserved"):
            self.assertEqual(source["path"], "./dist/codex/codex-plugin")
        with self.subTest(msg="Codex source.path schema — stdout reports the change"):
            self.assertIn("dist/codex/codex-plugin", result.stdout)

        # Count-neutral hardening checks supplement the 49-entry predecessor
        # inventory without changing its parity total.
        root = self._marketplace("nonfinite-json", '{"name":"test","plugins":[],"value":NaN}')
        result = run_sync(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid JSON", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

        root = self.work / "invalid-utf8"
        path = root / ".claude-plugin" / "marketplace.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"\xff\xfe")
        result = run_sync(root)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)

        root = self._marketplace("unicode", '{"name":"Café","plugins":[{"name":"unicode","source":"./unicode","version":"0.1.0"}]}')
        create_plugin(root, "unicode", "0.2.0")
        result = run_sync(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Café", (root / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))

        root = self._marketplace("empty-relative-source", '{"name":"test","plugins":[{"name":"root","source":"./"}]}')
        result = run_sync(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("must identify a plugin directory", result.stderr)

        root = self._marketplace("non-string-source-path", '{"name":"test","plugins":[{"name":"typed","source":{"path":7}}]}')
        result = run_sync(root)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(SyncMarketplaceVersionsTests)


def main() -> int:
    return run_counted(build_suite(), label="test-sync-marketplace-versions")


if __name__ == "__main__":
    raise SystemExit(main())
