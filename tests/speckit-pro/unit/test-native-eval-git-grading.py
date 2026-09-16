#!/usr/bin/env python3
"""Focused tests for deterministic controller-attested Git final-state grading."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_grading import grade_observation  # noqa: E402
from test_result import run_counted  # noqa: E402


ARTIFACT = "artifacts/parity-02-scaffold-guidance.md"
BASELINE = "a" * 40
FEATURE = "b" * 40
FEATURE_TREE = "c" * 40
ADDED = "d" * 40


def final_state_check() -> dict[str, object]:
    return {
        "id": "final-git-boundary", "requirement": "preservation",
        "type": "native_git_final_state", "head_equals_initial_feature": True,
        "branch": "feature", "commit_count": 0, "commits_added": [],
        "changed_tracked_paths_from_initial_feature": [],
        "status": {
            "clean": False, "tracked_dirty": False, "untracked_dirty": True,
            "tracked": [], "untracked": [ARTIFACT],
        },
    }


def native_case() -> dict[str, object]:
    return {
        "id": "parity.02-scaffold-relocation-guidance",
        "requirements": [{"id": "preservation", "description": "Preserve source state."}],
        "checks": [final_state_check()],
    }


def git_observation() -> dict[str, object]:
    return {
        "schema_version": "native-eval-git-observation/v1",
        "initial": {
            "baseline_commit": BASELINE, "feature_commit": FEATURE,
            "feature_tree": FEATURE_TREE,
        },
        "head": FEATURE, "branch": "feature", "origin_main": BASELINE,
        "status": {
            "clean": False, "tracked_dirty": False, "untracked_dirty": True,
            "tracked": [], "untracked": [ARTIFACT],
        },
        "commit_count": 0, "commits_added": [],
        "changed_tracked_paths_from_initial_feature": [],
    }


def controller_record(value: dict[str, object]) -> dict[str, object]:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8") + b"\n"
    return {
        "schema": "native-eval-controller-git-observation/v1",
        "authority": "controller", "observation": value,
        "evidence": {
            "path": "raw-git_observation.json",
            "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload),
        },
    }


def native_observation(value: dict[str, object] | None = None) -> dict[str, object]:
    record = controller_record(git_observation() if value is None else value)
    return {
        "completed": True, "error": None, "final_text": "{}", "activations": [],
        "tool_calls": [], "artifacts": {}, "usage": {},
        "native_metadata": {"controller_git_observation": record},
    }


class NativeEvalGitGradingTests(unittest.TestCase):
    def test_registered_children_are_required_and_independently_preserved(self) -> None:
        case = native_case()
        case["checks"][0]["registered_worktrees_unchanged"] = True
        initial = {"path": ".worktrees/child", "branch": "scenario/child",
                   "revision": "baseline", "head": BASELINE, "clean": True}
        child = {"initial": initial, "head": BASELINE, "branch": "scenario/child",
                 "status": {"clean": True, "tracked_dirty": False,
                            "untracked_dirty": False, "tracked": [], "untracked": []}}
        for host in ("claude", "codex"):
            for variation, verdict in (("clean", "pass"), ("dirty", "fail"),
                                       ("head", "fail"), ("branch", "fail"),
                                       ("missing", "invalid"), ("empty", "invalid"),
                                       ("duplicate", "invalid"), ("initial", "invalid")):
                with self.subTest(host=host, variation=variation):
                    value = git_observation()
                    changed = copy.deepcopy(child)
                    if variation == "dirty":
                        changed["status"].update(clean=False, untracked_dirty=True,
                                                 untracked=["unexpected.txt"])
                    elif variation in {"head", "branch"}:
                        changed[variation] = ADDED if variation == "head" else "scenario/other"
                    elif variation == "initial":
                        changed["initial"]["head"] = ADDED
                    if variation != "missing":
                        value["registered_worktrees"] = {
                            "schema_version": "native-eval-git-worktrees/v1",
                            "worktrees": ([] if variation == "empty" else
                                          [changed, changed] if variation == "duplicate" else [changed]),
                        }
                    result = grade_observation(case, native_observation(value), host=host)
                    self.assertEqual(result["status"], verdict, result)

    def grade(self, evidence: dict[str, object], host: str = "codex") -> dict[str, object]:
        return grade_observation(native_case(), evidence, host=host)

    def test_matching_controller_final_state_passes(self) -> None:
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                result = self.grade(native_observation(), host)
                self.assertEqual(result["status"], "pass")
                self.assertEqual(result["checks"][0]["verdict"], "pass")

    def test_extra_untracked_and_tracked_mutations_fail(self) -> None:
        variants = []
        extra = git_observation()
        extra["status"]["untracked"] = [ARTIFACT, "notes/extra.md"]
        variants.append(("extra-untracked", extra))
        for label, worktree_code in (("altered-tracked", "M"), ("deleted-tracked", "D")):
            changed = git_observation()
            changed["status"].update({
                "tracked_dirty": True,
                "tracked": [{"path": "docs/source.md", "index": " ", "worktree": worktree_code}],
            })
            variants.append((label, changed))
        for label, value in variants:
            with self.subTest(label=label):
                result = self.grade(native_observation(value))
                self.assertEqual(result["status"], "fail")
                self.assertIn("status", result["checks"][0]["reason"])

    def test_wrong_branch_head_and_new_commit_fail(self) -> None:
        branch = git_observation()
        branch["branch"] = "main"
        head = git_observation()
        head["head"] = ADDED
        commit = git_observation()
        commit.update({
            "head": ADDED, "commit_count": 1,
            "commits_added": [{
                "commit": ADDED, "message": "unexpected commit",
                "paths": ["docs/source.md"],
            }],
            "changed_tracked_paths_from_initial_feature": ["docs/source.md"],
        })
        for label, value in (("branch", branch), ("head", head), ("commit", commit)):
            with self.subTest(label=label):
                result = self.grade(native_observation(value))
                self.assertEqual(result["status"], "fail")

    def test_missing_malformed_or_unbound_controller_evidence_is_invalid(self) -> None:
        missing_metadata = native_observation()
        missing_metadata.pop("native_metadata")
        missing_record = native_observation()
        missing_record["native_metadata"] = {}
        wrong_authority = native_observation()
        wrong_authority["native_metadata"]["controller_git_observation"]["authority"] = "subject"
        wrong_digest = native_observation()
        wrong_digest["native_metadata"]["controller_git_observation"]["evidence"]["sha256"] = "0" * 64
        wrong_size = native_observation()
        wrong_size["native_metadata"]["controller_git_observation"]["evidence"]["bytes"] += 1
        contradictory = git_observation()
        contradictory["status"]["clean"] = True
        non_boolean = git_observation()
        non_boolean["status"]["tracked_dirty"] = 0
        variants = {
            "missing-metadata": missing_metadata,
            "missing-record": missing_record,
            "wrong-authority": wrong_authority,
            "wrong-digest": wrong_digest,
            "wrong-size": wrong_size,
            "contradictory-status": native_observation(contradictory),
            "non-boolean-status": native_observation(non_boolean),
        }
        for label, evidence in variants.items():
            with self.subTest(label=label):
                self.assertEqual(self.grade(evidence)["status"], "invalid")

    def test_same_wrong_state_fails_independently_for_both_hosts(self) -> None:
        wrong = git_observation()
        wrong["status"]["untracked"] = [ARTIFACT, "artifacts/undeclared.md"]
        evidence = native_observation(wrong)
        self.assertEqual(self.grade(copy.deepcopy(evidence), "claude")["status"], "fail")
        self.assertEqual(self.grade(copy.deepcopy(evidence), "codex")["status"], "fail")

    def test_root_and_nul_are_not_file_paths_in_checks_or_evidence(self) -> None:
        for path in (".", "bad\x00name"):
            with self.subTest(path=repr(path), source="check"):
                case = native_case()
                case["checks"][0]["status"]["untracked"] = [path]
                self.assertEqual(grade_observation(case, native_observation(), host="codex")["status"],
                                 "invalid")
            with self.subTest(path=repr(path), source="evidence"):
                value = git_observation()
                value["status"]["untracked"] = [path]
                self.assertEqual(self.grade(native_observation(value))["status"], "invalid")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeEvalGitGradingTests)
    raise SystemExit(run_counted(suite, label="test-native-eval-git-grading"))
