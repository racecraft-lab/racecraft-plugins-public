"""Base case for mutation helpers that read a committed request fixture inside a throwaway checkout."""

import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from typing import Any
import unittest

REPO = Path(__file__).resolve().parents[3]
FIXTURES = REPO / "tests/speckit-pro/unit/fixtures/mutation-helpers/requests"


class MutationRequestCase(unittest.TestCase):
    """Subclasses name the helper, the files its checkout starts with and the inputs every call carries."""

    helper_id = ""
    files: dict[str, str] = {}
    fixed_inputs: dict[str, str] = {}

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / ".specify").mkdir()
        for name, text in self.files.items():
            (self.root / name).parent.mkdir(parents=True, exist_ok=True)
            (self.root / name).write_text(text, encoding="utf-8")
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)

    def call(self, mode: str, **inputs: object) -> dict[str, Any]:
        """Replay the committed request fixture with this test's mode and inputs."""
        from speckit_pro_runner.helpers.registry import dispatch_helper

        document = json.loads((FIXTURES / f"{self.helper_id}.json").read_text(encoding="utf-8"))
        document["inputs"] = {**document["inputs"], **self.fixed_inputs, **inputs}
        return dispatch_helper(SimpleNamespace(**{**document, "mode": mode}))

    def read_only_data(self) -> dict[str, Any]:
        result = self.call("read_only")
        self.assertEqual("ok", result["status"], result)
        return dict(result["data"])
