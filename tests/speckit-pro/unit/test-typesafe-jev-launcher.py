#!/usr/bin/env python3
"""Pin the missing-binary launcher's credential setup instructions."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "tests" / "speckit-pro" / "lib"))
from test_result import run_counted  # noqa: E402

LAUNCHER = REPO_ROOT / "typesafe-jev" / "plugin" / "scripts" / "evaluate_launch.py"


class TypesafeJevLauncherTests(unittest.TestCase):
    def test_missing_binary_explains_chain_keys_and_keyless_ollama_app(self) -> None:
        request = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(LAUNCHER)],
                input=json.dumps(request) + "\n",
                capture_output=True,
                text=True,
                env={**os.environ, "EVALUATE_BIN": str(Path(directory) / "missing-evaluate")},
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        instructions = json.loads(result.stdout)["result"]["instructions"]
        self.assertIn(
            "2. Put any keys your chain needs in ~/.config/racecraft-jev/ "
            "(typesafe.key, openrouter.key, or ollama.key; chmod 600). "
            "The signed-in Ollama app (ollama-local) needs no key file.\n",
            instructions,
        )
        self.assertNotIn("ollama-local.key", instructions)


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(TypesafeJevLauncherTests),
        label="test-typesafe-jev-launcher",
    ))
