#!/usr/bin/env python3
"""Structural validation for .agents/plugins/marketplace.json (port of validate-codex-marketplace.sh).

XPLAT-010 count-parity port (T023, US2). Python 3.11+ standard library only.
Asserts the Codex marketplace descriptor exists, is valid JSON, carries the
required fields, and that its first plugin's ``source.path`` is a repo-relative
``./``-prefixed directory that resolves inside the repo root. Every former
``assert_*``/``_pass``/``_fail`` execution maps to one counted ``subTest`` unit;
names reproduced verbatim via ``subTest(msg=...)`` for a 1:1 baseline match.

Baseline: ``tests/speckit-pro/parity/bash-to-python/validate-codex-marketplace-baseline.txt``
(TOTAL: 13).
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

MARKETPLACE_JSON = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"


def _field_exists(data: object, dotted: str) -> bool:
    """Mirror assert_json_field_exists: walk ``a.b.c`` keys without raising."""
    current = data
    try:
        for key in dotted.split("."):
            current = current[key]
    except (KeyError, TypeError, IndexError):
        return False
    return True


def _nested(data: object, *keys: object) -> object:
    """Return ``data[k0][k1]...`` or ``None`` if any hop is missing (mirrors the
    bash inline ``python3 -c`` extractors, which print empty and fail on error)."""
    current = data
    try:
        for key in keys:
            current = current[key]  # type: ignore[index]
    except (KeyError, TypeError, IndexError):
        return None
    return current


class ValidateCodexMarketplace(unittest.TestCase):
    def test_codex_marketplace(self) -> None:
        with self.subTest(msg=".agents/plugins/marketplace.json exists"):
            self.assertTrue(MARKETPLACE_JSON.is_file(), f"file not found: {MARKETPLACE_JSON}")

        raw = MARKETPLACE_JSON.read_text(encoding="utf-8") if MARKETPLACE_JSON.is_file() else ""
        with self.subTest(msg=".agents/plugins/marketplace.json is valid JSON"):
            try:
                json.loads(raw)
            except json.JSONDecodeError:
                self.fail(".agents/plugins/marketplace.json is not valid JSON")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {}

        with self.subTest(msg="name field exists"):
            self.assertTrue(_field_exists(data, "name"), "JSON field 'name' does not exist")
        with self.subTest(msg="interface.displayName field exists"):
            self.assertTrue(_field_exists(data, "interface.displayName"), "JSON field 'interface.displayName' does not exist")

        with self.subTest(msg="plugins array exists"):
            plugins = data.get("plugins") if isinstance(data, dict) else None
            self.assertIsInstance(plugins, list, "plugins field is missing or not an array")

        with self.subTest(msg="first plugin name is speckit-pro"):
            first_name = _nested(data, "plugins", 0, "name")
            got = str(first_name) if first_name is not None else ""
            self.assertEqual("speckit-pro", got, f"expected first plugin name 'speckit-pro', got '{got}'")

        with self.subTest(msg="source.source is local"):
            source_kind = _nested(data, "plugins", 0, "source", "source")
            got = str(source_kind) if source_kind is not None else ""
            self.assertEqual("local", got, f"expected source.source 'local', got '{got}'")

        source_path_val = _nested(data, "plugins", 0, "source", "path")
        source_path = str(source_path_val) if source_path_val is not None else ""
        with self.subTest(msg="source.path is ./-prefixed and relative"):
            self.assertTrue(source_path.startswith("./"), f"source.path must start with ./, got '{source_path}'")

        # Bash concatenates "$REPO_ROOT/$source_path" then normalizes (string
        # concat, not os.path.join — an absolute source_path would not re-root).
        resolved_path = os.path.normpath(f"{REPO_ROOT}/{source_path}")
        with self.subTest(msg="source.path resolves to existing directory"):
            self.assertTrue(
                Path(resolved_path).is_dir(),
                f"source.path '{source_path}' does not resolve to an existing directory (checked: {resolved_path})",
            )

        with self.subTest(msg="source.path stays inside repo root"):
            repo_real = os.path.realpath(str(REPO_ROOT))
            target_real = os.path.realpath(resolved_path)
            self.assertEqual(
                repo_real, os.path.commonpath([repo_real, target_real]),
                f"source.path '{source_path}' resolves outside repo root",
            )

        with self.subTest(msg="policy.installation field exists"):
            val = _nested(data, "plugins", 0, "policy", "installation")
            self.assertTrue(val, "policy.installation field is missing or empty")
        with self.subTest(msg="policy.authentication field exists"):
            val = _nested(data, "plugins", 0, "policy", "authentication")
            self.assertTrue(val, "policy.authentication field is missing or empty")
        with self.subTest(msg="category field exists"):
            val = _nested(data, "plugins", 0, "category")
            self.assertTrue(val, "category field is missing or empty")


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateCodexMarketplace)


def main() -> int:
    return run_counted(build_suite(), label="validate-codex-marketplace")


if __name__ == "__main__":
    raise SystemExit(main())
