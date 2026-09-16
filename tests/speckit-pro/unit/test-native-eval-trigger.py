#!/usr/bin/env python3
"""Provider-free native trigger staging and evidence contracts."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TESTS / "lib"))

from native_eval_trigger import TriggerEvidenceError, qualify_trigger_observation, stage_trigger_catalog
from test_result import run_counted


def skill(name: str, description: str) -> bytes:
    return (
        f"---\nname: {name}\ndescription: {description}\n---\n\n"
        f"FULL PRODUCT WORKFLOW FOR {name}; MUST NOT BE STAGED.\n"
    ).encode("utf-8")


def observation(*, text: str = "done", activations=None, calls=None) -> dict[str, object]:
    return {
        "completed": True,
        "error": None,
        "final_text": text,
        "activations": list(activations or []),
        "tool_calls": list(calls or []),
        "artifacts": {},
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }


class NativeTriggerTests(unittest.TestCase):
    def make_sources(self, root: Path, host: str) -> tuple[Path, dict[str, bytes]]:
        source = root / ("skills" if host == "claude" else "codex-skills")
        originals = {}
        for name in ("alpha", "beta", "gamma"):
            payload = skill(name, f"Select {name} for its exact behavioral boundary.")
            path = source / name / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_bytes(payload)
            originals[name] = payload
        return source, originals

    def stage(self, root: Path, host: str, trial_id: str = "run/case/host/mode/1"):
        source, originals = self.make_sources(root, host)
        override = root / "controlled-description.txt"
        override.write_text("Use only when no staged capability applies.\n", encoding="utf-8")
        staged = stage_trigger_catalog(
            host, source, root / "stage", "alpha", trial_id,
            plugin_name="trigger-fixture", no_op_description_path=override,
        )
        return staged, originals

    def test_claude_stages_every_sibling_with_source_and_attempt_identities(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staged, originals = self.stage(root, "claude")
            self.assertEqual(staged.native_target, "trigger-fixture:alpha")
            self.assertEqual(staged.sibling_skills, ("beta", "gamma", "no-speckit-skill"))
            self.assertEqual(staged.skill_markers, {})
            self.assertEqual(set(staged.source_identities), {"alpha", "beta", "gamma"})
            self.assertEqual(set(staged.staged_identities), {"alpha", "beta", "gamma", "no-speckit-skill"})
            for name, payload in originals.items():
                self.assertEqual((root / "skills" / name / "SKILL.md").read_bytes(), payload)
                self.assertEqual(staged.source_identities[name]["sha256"], hashlib.sha256(payload).hexdigest())
                body = (staged.stage_root / "skills" / name / "SKILL.md").read_text()
                self.assertIn(f"description: Select {name} for its exact behavioral boundary.", body)
                self.assertNotIn("FULL PRODUCT WORKFLOW", body)
            no_op = (staged.stage_root / "skills/no-speckit-skill/SKILL.md").read_text()
            self.assertIn("description: Use only when no staged capability applies.", no_op)
            self.assertEqual(staged.controlled_description_identity["source"], "override")
            self.assertEqual(staged.as_dict()["attempt_sha256"], staged.attempt_sha256)

    def test_codex_stages_read_witnesses_and_stable_logical_trial_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, originals = self.make_sources(root, "codex")
            first = stage_trigger_catalog("codex", source, root / "first", "alpha", "logical-1")
            resumed = stage_trigger_catalog("codex", source, root / "resumed", "alpha", "logical-1")
            distinct = stage_trigger_catalog("codex", source, root / "distinct", "alpha", "logical-2")
            self.assertEqual(first.attempt_sha256, resumed.attempt_sha256)
            self.assertEqual(first.staged_identities, resumed.staged_identities)
            self.assertEqual(first.catalog_sha256, distinct.catalog_sha256)
            self.assertNotEqual(first.attempt_sha256, distinct.attempt_sha256)
            self.assertNotEqual(first.skill_markers, distinct.skill_markers)
            self.assertEqual(set(first.witnesses), {"alpha", "beta", "gamma", "no-speckit-skill"})
            self.assertEqual(set(first.skill_markers.values()), set(first.witnesses))
            for name, witness in first.witnesses.items():
                marker = next(marker for marker, selected in first.skill_markers.items() if selected == name)
                self.assertEqual(witness["body"].count(marker), 1)
            for name, payload in originals.items():
                self.assertEqual((source / name / "SKILL.md").read_bytes(), payload)

    def test_staging_rejects_missing_partial_symlinked_and_reused_catalogs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, _ = self.make_sources(root, "codex")
            with self.assertRaisesRegex(TriggerEvidenceError, "target skill is absent"):
                stage_trigger_catalog("codex", source, root / "missing", "absent", "trial")
            (source / "partial").mkdir()
            with self.assertRaisesRegex(TriggerEvidenceError, "skill source"):
                stage_trigger_catalog("codex", source, root / "partial-stage", "alpha", "trial")
            (source / "partial").rmdir()
            (source / "linked").symlink_to(source / "beta", target_is_directory=True)
            with self.assertRaisesRegex(TriggerEvidenceError, "symlink"):
                stage_trigger_catalog("codex", source, root / "linked-stage", "alpha", "trial")
            (source / "linked").unlink()
            first = stage_trigger_catalog("codex", source, root / "reused", "alpha", "trial")
            self.assertTrue(first.attempt_sha256)
            with self.assertRaisesRegex(TriggerEvidenceError, "already exists"):
                stage_trigger_catalog("codex", source, root / "reused", "alpha", "trial")

    def test_qualification_rejects_staged_bytes_changed_after_identity_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            staged, _ = self.stage(Path(directory), "codex")
            skill_file = staged.stage_root / ".agents/skills/alpha/SKILL.md"
            skill_file.write_text(skill_file.read_text() + "\nchanged\n", encoding="utf-8")
            with self.assertRaisesRegex(TriggerEvidenceError, "bytes changed"):
                qualify_trigger_observation(staged, observation())

    def test_current_repository_host_catalogs_stage_completely_without_product_bodies(self):
        plugin = TESTS.parents[1] / "speckit-pro"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for host, source_name in (("claude", "skills"), ("codex", "codex-skills")):
                source = plugin / source_name
                expected = {path.parent.name for path in source.glob("*/SKILL.md")}
                staged = stage_trigger_catalog(
                    host, source, root / host, "speckit-status", "repository-contract",
                )
                with self.subTest(host=host):
                    self.assertEqual(set(staged.source_identities), expected)
                    self.assertEqual(
                        set(staged.staged_identities), expected | {"no-speckit-skill"},
                    )
                    self.assertTrue(all(
                        "measurement stub used by the repository's skill-selection test suite"
                        in witness["body"] for witness in staged.witnesses.values()
                    ))

    def test_claude_qualification_returns_target_wrong_and_genuine_no_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            staged, _ = self.stage(Path(directory), "claude")
            target = {"name": "Skill", "input": {"skill": "trigger-fixture:alpha"},
                      "success": True, "output": "loaded"}
            result = qualify_trigger_observation(
                staged, observation(activations=["alpha"], calls=[target]),
            )
            self.assertEqual(result["activations"], ["alpha"])
            wrong = {**target, "input": {"skill": "trigger-fixture:beta"}}
            result = qualify_trigger_observation(
                staged, observation(activations=["beta"], calls=[wrong]),
            )
            self.assertEqual(result["activations"], ["beta"])
            no_selection = qualify_trigger_observation(
                staged, observation(text="I used alpha without invoking it."),
            )
            self.assertEqual(no_selection["activations"], [])

    def test_claude_no_skill_witness_is_preserved_but_not_a_product_activation(self):
        with tempfile.TemporaryDirectory() as directory:
            staged, _ = self.stage(Path(directory), "claude")
            fallback = {
                "name": "Skill",
                "input": {"skill": "trigger-fixture:no-speckit-skill"},
                "success": True,
                "output": "loaded",
            }
            result = qualify_trigger_observation(
                staged,
                observation(activations=["no-speckit-skill"], calls=[fallback]),
            )
            qualification = result["native_metadata"]["trigger_qualification"]
            self.assertEqual(result["activations"], [])
            self.assertEqual(qualification["actual_activations"], ["no-speckit-skill"])
            self.assertEqual(qualification["canonical_activations"], [])

    def test_claude_rejects_failed_unknown_multiple_mismatched_and_truncated_skill_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            staged, _ = self.stage(Path(directory), "claude")
            call = {"name": "Skill", "input": {"skill": "alpha"}, "success": True, "output": "ok"}
            cases = {
                "failed": [{**call, "success": False}],
                "unknown": [{**call, "input": {"skill": "other-plugin:alpha"}}],
                "multiple": [call, {**call, "input": {"skill": "beta"}}],
                "truncated": [{key: value for key, value in call.items() if key != "output"}],
            }
            for name, calls in cases.items():
                activations = ["alpha"] if name != "multiple" else ["alpha", "beta"]
                with self.subTest(name=name), self.assertRaises(TriggerEvidenceError):
                    qualify_trigger_observation(staged, observation(activations=activations, calls=calls))
            with self.assertRaisesRegex(TriggerEvidenceError, "disagree"):
                qualify_trigger_observation(staged, observation(activations=[], calls=[call]))

    def codex_read(self, staged, name: str, *, output=None, success=True):
        witness = staged.witnesses[name]
        return {
            "name": "command_execution",
            "input": {"command": f"cat {witness['path']}"},
            "success": success,
            "output": witness["body"] if output is None else output,
        }

    def marker(self, staged, name: str) -> str:
        return next(marker for marker, skill_name in staged.skill_markers.items() if skill_name == name)

    def test_codex_qualification_requires_matching_read_and_fresh_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            staged, _ = self.stage(Path(directory), "codex")
            marker = self.marker(staged, "alpha")
            result = qualify_trigger_observation(
                staged,
                observation(text=f"{marker}\nDone.", activations=["alpha"],
                            calls=[self.codex_read(staged, "alpha")]),
            )
            self.assertEqual(result["activations"], ["alpha"])
            self.assertEqual(
                result["native_metadata"]["trigger_qualification"]["consulted_skills"], ["alpha"],
            )
            wrong_marker = self.marker(staged, "beta")
            wrong = qualify_trigger_observation(
                staged,
                observation(text=wrong_marker, activations=["beta"],
                            calls=[self.codex_read(staged, "beta")]),
            )
            self.assertEqual(wrong["activations"], ["beta"])

    def test_codex_accepts_exact_command_cat_but_rejects_broader_shell_forms(self):
        with tempfile.TemporaryDirectory() as directory:
            staged, _ = self.stage(Path(directory), "codex")
            witness = staged.witnesses["alpha"]
            marker = self.marker(staged, "alpha")
            exact = self.codex_read(staged, "alpha")
            exact["input"]["command"] = (
                f"/bin/zsh -c 'command cat {witness['relative_path']}'"
            )
            result = qualify_trigger_observation(
                staged,
                observation(text=marker, activations=["alpha"], calls=[exact]),
            )
            self.assertEqual(result["activations"], ["alpha"])

            invalid_commands = {
                "nested login shell": (
                    f'/bin/zsh -c "zsh -lc \'command cat {witness["relative_path"]}\'"'
                ),
                "command option": (
                    f"/bin/zsh -c 'command -p cat {witness['relative_path']}'"
                ),
                "shell operator": (
                    f"/bin/zsh -c 'command cat {witness['relative_path']} && true'"
                ),
                "extra argument": (
                    f"/bin/zsh -c 'command cat {witness['relative_path']} extra'"
                ),
                "wrong path": "/bin/zsh -c 'command cat .agents/skills/beta/SKILL.md'",
            }
            for name, command in invalid_commands.items():
                call = self.codex_read(staged, "alpha")
                call["input"]["command"] = command
                with self.subTest(name=name), self.assertRaisesRegex(
                    TriggerEvidenceError, "exact staged skill-file read",
                ):
                    qualify_trigger_observation(
                        staged,
                        observation(text=marker, activations=["alpha"], calls=[call]),
                    )

    def test_codex_no_skill_witness_is_preserved_but_not_a_product_activation(self):
        with tempfile.TemporaryDirectory() as directory:
            staged, _ = self.stage(Path(directory), "codex")
            marker = self.marker(staged, "no-speckit-skill")
            result = qualify_trigger_observation(
                staged,
                observation(
                    text=f"{marker}\nNo staged skill applies.",
                    activations=["no-speckit-skill"],
                    calls=[self.codex_read(staged, "no-speckit-skill")],
                ),
            )
            qualification = result["native_metadata"]["trigger_qualification"]
            self.assertEqual(result["activations"], [])
            self.assertEqual(qualification["actual_activations"], ["no-speckit-skill"])
            self.assertEqual(qualification["canonical_activations"], [])
            self.assertEqual(qualification["consulted_skills"], ["no-speckit-skill"])

    def test_codex_unqualified_no_skill_marker_remains_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            staged, _ = self.stage(Path(directory), "codex")
            marker = self.marker(staged, "no-speckit-skill")
            with self.assertRaisesRegex(TriggerEvidenceError, "not corroborated"):
                qualify_trigger_observation(
                    staged,
                    observation(text=marker, activations=["no-speckit-skill"]),
                )

    def test_codex_read_without_marker_is_invalid_but_complete_no_read_is_no_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            staged, _ = self.stage(Path(directory), "codex")
            with self.assertRaisesRegex(TriggerEvidenceError, "not paired"):
                qualify_trigger_observation(
                    staged, observation(calls=[self.codex_read(staged, "alpha")]),
                )
            genuine_none = qualify_trigger_observation(
                staged, observation(text="No staged skill applies; alpha is only prose."),
            )
            self.assertEqual(genuine_none["activations"], [])

    def test_codex_rejects_marker_without_read_stale_marker_and_read_marker_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staged, _ = self.stage(root / "one", "codex", "logical-1")
            stale, _ = self.stage(root / "two", "codex", "logical-2")
            cases = {
                "marker without read": observation(
                    text=self.marker(staged, "alpha"), activations=["alpha"]),
                "stale marker": observation(text=self.marker(stale, "alpha")),
                "conflict": observation(
                    text=self.marker(staged, "beta"), activations=["beta"],
                    calls=[self.codex_read(staged, "alpha")]),
                "marker not first": observation(
                    text=f"Prose first.\n{self.marker(staged, 'alpha')}", activations=["alpha"],
                    calls=[self.codex_read(staged, "alpha")]),
            }
            for name, value in cases.items():
                with self.subTest(name=name), self.assertRaises(TriggerEvidenceError):
                    qualify_trigger_observation(staged, value)

    def test_codex_rejects_multiple_wrong_failed_and_truncated_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            staged, _ = self.stage(Path(directory), "codex")
            marker = self.marker(staged, "alpha")
            cases = {
                "multiple reads": observation(
                    text=marker, activations=["alpha"],
                    calls=[self.codex_read(staged, "alpha"), self.codex_read(staged, "beta")]),
                "wrong output": observation(
                    text=marker, activations=["alpha"],
                    calls=[self.codex_read(staged, "alpha", output="truncated")]),
                "failed read": observation(
                    text=marker, activations=["alpha"],
                    calls=[self.codex_read(staged, "alpha", success=False)]),
                "truncated read": observation(
                    text=marker, activations=["alpha"],
                    calls=[{key: value for key, value in self.codex_read(staged, "alpha").items()
                            if key != "output"}]),
                "repeated marker": observation(
                    text=f"{marker}\n{marker}", activations=["alpha", "alpha"],
                    calls=[self.codex_read(staged, "alpha")]),
            }
            for name, value in cases.items():
                with self.subTest(name=name), self.assertRaises(TriggerEvidenceError):
                    qualify_trigger_observation(staged, value)

    def test_malformed_or_incomplete_observations_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            staged, _ = self.stage(Path(directory), "claude")
            cases = [
                {**observation(), "completed": False},
                {**observation(), "error": "native failure"},
                {**observation(), "tool_calls": "not-a-list"},
                {**observation(), "activations": [True]},
                {**observation(), "usage": None},
            ]
            for value in cases:
                with self.assertRaises(TriggerEvidenceError):
                    qualify_trigger_observation(staged, value)


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeTriggerTests),
        label="test-native-eval-trigger",
    ))
