"""Shared fixture for the readiness record tests: a scratch SpecKit project and the runner request."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from host_skill_views import host_skill_root
from runner_invocation import PLUGIN_ROOT, assert_runner_response, run_runner


def current_plugin_revision() -> str:
    """The executing runner manifest owns the revision for valid readiness fixtures."""
    manifest = PLUGIN_ROOT / "speckit_pro_runner/speckit-pro-runner.manifest.json"
    return json.loads(manifest.read_text(encoding="utf-8"))["plugin_version"]


def readiness_request(observations: list[dict[str, object]], host: str = "claude", request_id: str = "test-readiness",
                      mode: str = "apply", **inputs: object) -> dict[str, object]:
    body = {"host": host, "execution_mode": "interactive", "plugin_revision": current_plugin_revision(),
            "observations": observations, **inputs}
    return {"schema_version": "1.0", "request_id": request_id, "helper_id": "write-readiness-record",
            "operation": "write-readiness-record", "mode": mode, "inputs": body}


def scaffold_step(host: str) -> str:
    path = host_skill_root(host) / "speckit-scaffold-spec" / "SKILL.md"
    return path.read_text(encoding="utf-8").split("### 6.5 Write the Readiness Record", 1)[1].split("\n### ", 1)[0]


class ReadinessCase(unittest.TestCase):
    default_host = "claude"
    request_id = "test-readiness"

    def setUp(self) -> None:
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.root.joinpath(".specify").mkdir()

    def run_helper(self, observations: list[dict[str, object]], host: str | None = None) -> dict:
        request = readiness_request(observations, host or self.default_host, self.request_id)
        return run_runner(request, cwd=self.root)[1]

    def items(self, response: dict) -> dict:
        assert_runner_response(self, response, "ok", 0)
        return response["data"]["record"]["items"]

    def documented_rows(self, names: tuple[str, ...]) -> dict[str, dict[str, bool]]:
        """For each host, whether scaffold step 6.5 has a table row for each item."""
        return {host: {name: f"| `{name}` |" in scaffold_step(host) for name in names}
                for host in ("claude", "codex")}

    def item(self, observation: dict[str, object], host: str | None = None) -> dict:
        """The record item one observation produces."""
        return self.items(self.run_helper([observation], host))[str(observation["item"])]

    def refuse_each(self, observations: list[dict[str, object]], host: str | None = None) -> None:
        for observation in observations:
            with self.subTest(observation=observation):
                assert_runner_response(self, self.run_helper([observation], host), "input_error", 2)

    def assert_item(self, item: dict, status: str, evidence: tuple[str, ...] = (), action: tuple[str, ...] = ()) -> None:
        self.assertEqual(status, item["status"])
        for text in evidence:
            self.assertIn(text, item["evidence_source"])
        for text in action:
            self.assertIn(text, item["action"])

    def check_codex_only(self, names: tuple[str, ...], observations: list[dict[str, object]]) -> None:
        """Claude records `names` not_applicable and refuses their observations; Codex without any records unknown."""
        recorded = self.items(self.run_helper([], "claude"))
        self.assertEqual(dict.fromkeys(names, ("not_applicable", False)),
                         {name: (recorded[name]["status"], "action" in recorded[name]) for name in names})
        self.refuse_each(observations, "claude")
        recorded = self.items(self.run_helper([], "codex"))
        for name in names:
            self.assertEqual("unknown", recorded[name]["status"], name)
            self.assertTrue(recorded[name]["action"])

    def check_documented(self, names: tuple[str, ...]) -> None:
        """Only the Codex scaffold step documents `names`; the Claude step says they are `not_applicable`."""
        self.assertEqual({"claude": dict.fromkeys(names, False), "codex": dict.fromkeys(names, True)},
                         self.documented_rows(names))
        self.assertIn("`not_applicable`", scaffold_step("claude"))
