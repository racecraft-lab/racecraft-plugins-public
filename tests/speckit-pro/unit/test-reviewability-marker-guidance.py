#!/usr/bin/env python3
"""PRSG-013 reviewability marker guidance parity checks."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
LIB_DIR = TEST_DIR.parent / "lib"
sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


SOURCE_PATHS = {
    "claude_skill": REPO_ROOT / "speckit-pro/skills/speckit-autopilot/SKILL.md",
    "claude_gate": REPO_ROOT / "speckit-pro/skills/speckit-autopilot/references/gate-validation.md",
    "claude_phase": REPO_ROOT / "speckit-pro/skills/speckit-autopilot/references/phase-execution.md",
    "claude_post": REPO_ROOT / "speckit-pro/skills/speckit-autopilot/references/post-implementation.md",
    "claude_workflow": REPO_ROOT
    / "speckit-pro/skills/speckit-autopilot/references/workflow-file-protocol.md",
    "codex_skill": REPO_ROOT / "speckit-pro/codex-skills/speckit-autopilot/SKILL.md",
    "codex_phase": REPO_ROOT
    / "speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md",
    "codex_post": REPO_ROOT
    / "speckit-pro/codex-skills/speckit-autopilot/references/post-implementation-codex.md",
    "claude_evals": REPO_ROOT
    / "tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json",
    "codex_evals": REPO_ROOT
    / "tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json",
}
BASELINE = REPO_ROOT / "tests/speckit-pro/parity/bash-to-python/test-reviewability-marker-guidance-baseline.txt"
MARKER_PLAN_SCHEMA_PATHS = (
    REPO_ROOT / "speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json",
    REPO_ROOT / "dist/claude/speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json",
    REPO_ROOT / "dist/codex/speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json",
    REPO_ROOT
    / "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json",
    REPO_ROOT
    / "tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/codex/speckit-pro/skills/speckit-autopilot/contracts/pr-marker-plan.schema.json",
)
MARKER_CHECKPOINT_SCHEMA_PATH = (
    REPO_ROOT
    / "specs/g56r-002-capability-discovery-telemetry/contracts/marker-checkpoint.schema.json"
)
MARKER_CHECKPOINT_PATHS = tuple(
    REPO_ROOT
    / f"specs/g56r-002-capability-discovery-telemetry/.process/checkpoints/us{index}.json"
    for index in range(1, 4)
)


CHECKS = (
    (
        "Claude guidance says valid current size-only block continues to marker planning",
        "claude_combined",
        "valid current size-only",
    ),
    (
        "Claude guidance says size-only block is not a manual re-slicing stop",
        "claude_combined",
        "not a manual re-slicing stop",
    ),
    ("Claude guidance sends size-only block into marker planning", "claude_combined", "marker planning"),
    ("Claude guidance sends size-only block into marker emission", "claude_combined", "marker emission"),
    ("Codex guidance mirrors valid size-only continuation", "codex_combined", "valid current size-only"),
    ("Codex guidance mirrors no manual re-slicing stop", "codex_combined", "not a manual re-slicing stop"),
    ("Codex guidance mirrors marker planning", "codex_combined", "marker planning"),
    ("Codex guidance mirrors marker emission", "codex_combined", "marker emission"),
    (
        "Guidance preserves malformed/stale marker correctness stops",
        "claude_combined",
        "malformed/stale marker state",
    ),
    ("Guidance preserves failed verification stop", "claude_combined", "failed verification"),
    ("Guidance preserves invalid packet stop", "claude_combined", "invalid packet"),
    ("Guidance preserves unsafe output stop", "claude_combined", "unsafe output"),
    ("Guidance preserves unusable gate evidence stop", "claude_combined", "unusable gate evidence"),
    (
        "Codex guidance preserves malformed/stale marker correctness stops",
        "codex_combined",
        "malformed/stale marker state",
    ),
    ("Codex guidance preserves failed verification stop", "codex_combined", "failed verification"),
    ("Codex guidance preserves invalid packet stop", "codex_combined", "invalid packet"),
    ("Codex guidance preserves unsafe output stop", "codex_combined", "unsafe output"),
    ("Codex guidance preserves unusable gate evidence stop", "codex_combined", "unusable gate evidence"),
    (
        "Claude evidence prompts include gate status/mode/exit/evidence path",
        "claude_combined",
        "gate status/mode/exit/evidence path",
    ),
    ("Claude evidence prompts include fingerprint status", "claude_combined", "fingerprint status"),
    ("Claude evidence prompts include ordered marker IDs", "claude_combined", "ordered marker IDs"),
    ("Claude evidence prompts include checkpoints", "claude_combined", "checkpoints"),
    ("Claude evidence prompts include warnings", "claude_combined", "warnings"),
    ("Claude evidence prompts include final marker_split", "claude_combined", "final marker_split"),
    ("Claude evidence prompts include packet validation", "claude_combined", "packet validation"),
    ("Claude evidence prompts include PR mappings", "claude_combined", "PR mappings"),
    (
        "Claude marker emission guidance separates source feature dir from branch prefix",
        "claude_combined",
        "--source-feature-dir specs/<feature>",
    ),
    (
        "Claude marker emission guidance preserves source evidence paths",
        "claude_combined",
        "Full verification evidence, scoped evidence, PRS, and MOC files stay under",
    ),
    (
        "Codex evidence prompts include gate status/mode/exit/evidence path",
        "codex_combined",
        "gate status/mode/exit/evidence path",
    ),
    ("Codex evidence prompts include fingerprint status", "codex_combined", "fingerprint status"),
    ("Codex evidence prompts include ordered marker IDs", "codex_combined", "ordered marker IDs"),
    ("Codex evidence prompts include checkpoints", "codex_combined", "checkpoints"),
    ("Codex evidence prompts include warnings", "codex_combined", "warnings"),
    ("Codex evidence prompts include final marker_split", "codex_combined", "final marker_split"),
    ("Codex evidence prompts include packet validation", "codex_combined", "packet validation"),
    ("Codex evidence prompts include PR mappings", "codex_combined", "PR mappings"),
    (
        "Codex marker emission guidance separates source feature dir from branch prefix",
        "codex_combined",
        "--source-feature-dir specs/<feature>",
    ),
    (
        "Codex marker emission guidance preserves source evidence paths",
        "codex_combined",
        "Full verification evidence, scoped evidence, PRS, and MOC files stay under",
    ),
    (
        "Workflow guidance persists pr_marker_plan outside tasks.md",
        "claude_workflow",
        "top-level `pr_marker_plan`",
    ),
    (
        "Workflow guidance forbids authoritative marker state in tasks.md",
        "claude_workflow",
        "not authoritative marker state in `tasks.md`",
    ),
    ("Workflow guidance requires repo-relative evidence paths", "claude_workflow", "repo-relative"),
    (
        "Layer 3 Claude eval covers size-only marker continuation",
        "claude_evals",
        "valid current size-only block",
    ),
    ("Layer 3 Claude eval rejects manual re-slicing stop", "claude_evals", "no manual re-slicing stop"),
    ("Layer 3 Claude eval requires marker evidence", "claude_evals", "marker evidence"),
    (
        "Layer 3 Claude eval requires source-dir branch-prefix separation",
        "claude_evals",
        "--source-feature-dir specs/<feature>",
    ),
    (
        "Layer 3 Codex eval covers size-only marker continuation",
        "codex_evals",
        "valid current size-only block",
    ),
    ("Layer 3 Codex eval rejects manual re-slicing stop", "codex_evals", "no manual re-slicing stop"),
    ("Layer 3 Codex eval requires marker evidence", "codex_evals", "marker evidence"),
    (
        "Layer 3 Codex eval requires source-dir branch-prefix separation",
        "codex_evals",
        "--source-feature-dir specs/<feature>",
    ),
    ("Paired evals require final marker_split", "evals_combined", "final marker_split"),
    ("Paired evals require PR mappings", "evals_combined", "PR mappings"),
    (
        "Paired evals require branch namespace conflict handling",
        "evals_combined",
        "Git ref namespace conflicts",
    ),
)


def baseline_inventory(path: Path) -> list[str]:
    names: list[str] = []
    total: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("TOTAL: "):
            total = int(line.removeprefix("TOTAL: "))
        else:
            _ordinal, name = line.split(" ", 1)
            names.append(name)
    if total != len(names):
        raise AssertionError(f"baseline TOTAL {total} does not match {len(names)} names")
    return names


class ReviewabilityMarkerGuidanceTests(unittest.TestCase):
    """Keep Claude, Codex, workflow, and eval marker guidance aligned."""

    @classmethod
    def setUpClass(cls) -> None:
        bodies = {name: path.read_text(encoding="utf-8") for name, path in SOURCE_PATHS.items()}
        bodies["claude_combined"] = "\n".join(
            bodies[name] for name in ("claude_skill", "claude_gate", "claude_phase", "claude_post", "claude_workflow")
        )
        bodies["codex_combined"] = "\n".join(
            bodies[name] for name in ("codex_skill", "codex_phase", "codex_post")
        )
        bodies["evals_combined"] = "\n".join(bodies[name] for name in ("claude_evals", "codex_evals"))
        cls.bodies = bodies

    def test_reviewability_marker_guidance_contract(self) -> None:
        self.assertEqual(baseline_inventory(BASELINE), [name for name, _body_key, _expected in CHECKS])
        for name, body_key, expected in CHECKS:
            with self.subTest(msg=name):
                self.assertIn(expected, self.bodies[body_key])

    def test_pr_marker_plan_schema_accepts_polish_without_weakening_existing_markers(self) -> None:
        schema_bodies = [path.read_bytes() for path in MARKER_PLAN_SCHEMA_PATHS]
        self.assertTrue(all(body == schema_bodies[0] for body in schema_bodies[1:]))

        schema = json.loads(schema_bodies[0])
        marker_properties = schema["$defs"]["marker"]["properties"]
        marker_id_pattern = re.compile(marker_properties["id"]["pattern"])
        marker_kinds = marker_properties["kind"]["enum"]

        for marker_id in ("foundation", "us1", "us12-part3", "full-spec", "polish"):
            with self.subTest(marker_id=marker_id):
                self.assertIsNotNone(marker_id_pattern.fullmatch(marker_id))
        for marker_id in ("setup", "us", "us1-part", "full_spec", "polish-part1"):
            with self.subTest(invalid_marker_id=marker_id):
                self.assertIsNone(marker_id_pattern.fullmatch(marker_id))
        for marker_kind in ("foundation", "user_story", "user_story_part", "full_spec", "polish"):
            with self.subTest(marker_kind=marker_kind):
                self.assertIn(marker_kind, marker_kinds)
        with self.subTest(invalid_marker_kind="maintenance"):
            self.assertNotIn("maintenance", marker_kinds)

    def test_pr_marker_plan_schema_binds_completion_and_emission_evidence(self) -> None:
        schema = json.loads(MARKER_PLAN_SCHEMA_PATHS[0].read_text(encoding="utf-8"))
        checkpoint = schema["$defs"]["checkpoint"]
        emission = schema["$defs"]["emission_mapping"]
        strict = schema["allOf"][0]["then"]["properties"]
        strict_source = strict["source_fingerprint"]
        strict_marker = strict["markers"]["items"]
        strict_checkpoint = strict_marker["properties"]["implementation_checkpoint"]
        strict_emission = strict_marker["properties"]["emission_mapping"]

        self.assertEqual(
            schema["properties"]["schema_version"]["enum"],
            ["pr-marker-plan.v1", "pr-marker-plan.v2"],
        )
        self.assertNotIn("changed_file_manifest_sha", schema["$defs"]["source_fingerprint"]["required"])
        self.assertIn("changed_file_manifest_sha", strict_source["required"])
        self.assertEqual(schema["properties"]["created_at"], {"type": "string"})
        self.assertEqual(schema["properties"]["updated_at"], {"type": "string"})
        self.assertEqual(strict["created_at"], {"$ref": "#/$defs/utc_timestamp"})
        self.assertEqual(strict["updated_at"], {"$ref": "#/$defs/utc_timestamp"})
        self.assertTrue(checkpoint["additionalProperties"])
        self.assertTrue(emission["additionalProperties"])
        self.assertEqual(
            strict_checkpoint["allOf"][0]["then"]["required"],
            [
                "evidence_path",
                "checkpoint_evidence_sha",
                "checkpoint_evidence_commit_sha",
                "verification_evidence_path",
                "commit_sha",
                "head_sha",
                "completed_at",
                "completed_task_ids",
                "summary",
                "validation",
                "freshness",
            ],
        )
        self.assertEqual(
            strict_marker["allOf"][0]["then"]["properties"]["implementation_checkpoint"]["properties"]["status"],
            {"const": "complete"},
        )
        self.assertEqual(
            strict_marker["allOf"][1]["then"]["properties"]["reviewability"]["required"],
            ["head_sha"],
        )
        status_rules = {
            branch["if"]["properties"]["status"]["const"]: branch["then"]["properties"]["markers"]["items"]
            ["properties"]
            for branch in schema["allOf"]
            if "status" in branch["if"]["properties"]
        }
        self.assertEqual(
            set(status_rules),
            {"planned", "checkpointing", "emission_ready", "emitting", "emitted", "collapsed", "stale", "invalid"},
        )
        self.assertEqual(status_rules["planned"]["implementation_checkpoint"]["properties"]["status"], {"const": "pending"})
        self.assertEqual(status_rules["planned"]["emission_mapping"]["properties"]["status"], {"const": "pending"})
        self.assertEqual(status_rules["checkpointing"]["emission_mapping"]["properties"]["status"], {"const": "pending"})
        self.assertEqual(status_rules["emission_ready"]["implementation_checkpoint"]["properties"]["status"], {"const": "complete"})
        self.assertEqual(
            status_rules["emission_ready"]["emission_mapping"]["properties"]["status"],
            {"enum": ["pending", "marker_split"]},
        )
        self.assertEqual(
            status_rules["emitting"]["emission_mapping"]["properties"]["status"],
            {"enum": ["pending", "marker_split", "emitted"]},
        )
        self.assertEqual(status_rules["emitted"]["emission_mapping"]["properties"]["status"], {"const": "emitted"})
        self.assertEqual(
            status_rules["collapsed"]["emission_mapping"]["properties"]["status"],
            {"const": "hazard_collapsed"},
        )
        terminal_preserving_statuses = {"enum": ["pending", "marker_split", "emitted", "hazard_collapsed"]}
        self.assertEqual(status_rules["stale"]["emission_mapping"]["properties"]["status"], terminal_preserving_statuses)
        self.assertEqual(status_rules["invalid"]["emission_mapping"]["properties"]["status"], terminal_preserving_statuses)
        lifecycle_branches = {
            branch["if"]["properties"]["status"]["const"]: branch["then"]
            for branch in schema["allOf"]
            if "status" in branch["if"]["properties"]
        }
        self.assertEqual(
            lifecycle_branches["stale"]["properties"]["warnings"]["contains"]["properties"]["code"],
            {"const": "MARKER_PLAN_STALE"},
        )
        self.assertEqual(
            lifecycle_branches["invalid"]["properties"]["warnings"]["contains"]["properties"]["code"],
            {"const": "MARKER_PLAN_INVALID"},
        )
        self.assertEqual(
            strict_checkpoint["properties"]["checkpoint_evidence_sha"]["pattern"],
            r"^sha256:[0-9a-f]{64}$",
        )
        for field_schema in strict_source["properties"].values():
            self.assertEqual(field_schema["pattern"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(
            strict_marker["properties"]["reviewability"]["properties"]["head_sha"]["pattern"],
            r"^[0-9a-f]{40}$",
        )
        self.assertIn("without traversal", schema["$defs"]["repo_path"]["description"])
        self.assertEqual(schema["$defs"]["utc_timestamp"]["pattern"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertEqual(
            strict_emission["allOf"][0]["then"]["required"],
            ["packet_path"],
        )
        self.assertEqual(
            strict_emission["allOf"][1]["then"]["required"],
            ["packet_path", "pr_number", "pr_url"],
        )

    def test_completed_marker_evidence_is_immutable_and_freshness_is_separate(self) -> None:
        schema = json.loads(MARKER_CHECKPOINT_SCHEMA_PATH.read_text(encoding="utf-8"))
        required = set(schema["required"])
        self.assertTrue(
            {
                "implementation_checkpoint_sha",
                "tasks_sha",
            }.issubset(required)
        )
        self.assertNotIn("current_tasks_sha", required)
        self.assertIn("immutable", schema["description"].lower())
        mutable_fields = {
            "source_fingerprint_contract",
            "tasks_sha_scope",
            "current_tasks_sha",
            "checkpoint_marker_tasks_sha",
            "current_marker_tasks_sha",
            "updated_at",
        }
        for path in MARKER_CHECKPOINT_PATHS[:2]:
            checkpoint = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(required.issubset(checkpoint))
            self.assertEqual(checkpoint["status"], "complete")
            self.assertEqual(checkpoint["source_fingerprint_status"], "current")
            self.assertFalse(mutable_fields & set(checkpoint))

        state = json.loads(
            (REPO_ROOT / "docs/ai/specs/.process/autopilot-state.json").read_text(encoding="utf-8")
        )
        for marker in state["pr_marker_plan"]["markers"][:2]:
            implementation_checkpoint = marker["implementation_checkpoint"]
            self.assertRegex(implementation_checkpoint["checkpoint_evidence_commit_sha"], r"^[0-9a-f]{40}$")
            freshness = implementation_checkpoint["freshness"]
            self.assertEqual(freshness["source_fingerprint_contract"], "marker-task-lines.v2")
            self.assertEqual(
                freshness["checkpoint_marker_tasks_sha"],
                freshness["current_marker_tasks_sha"],
            )


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ReviewabilityMarkerGuidanceTests)


def main() -> int:
    return run_counted(build_suite(), label="test-reviewability-marker-guidance")


if __name__ == "__main__":
    raise SystemExit(main())
