#!/usr/bin/env python3
"""Checklist check-and-propose (ADR 0018): executors propose, the runner applies in domain order.

A domain executor returns its gaps and proposed edits and writes neither spec.md
nor plan.md. The `checklist-edits` helper snapshots both files before the executors
run, refuses to apply when either changed, and then applies one domain at a time in
workflow order under one lock, so no two writes touch the files at once.
"""

import hashlib
import json
import os
import subprocess
from pathlib import Path
import sys
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "speckit-pro"), str(REPO / "tests/speckit-pro/lib")]
from speckit_pro_runner.helpers import checklist_edits  # noqa: E402
from speckit_pro_runner.helpers.registry import MUTATION_HELPERS  # noqa: E402
from guide_text import PHASE_EXECUTION_GUIDES, guide_text, guide_view  # noqa: E402
from mutation_request_case import MutationRequestCase  # noqa: E402
from test_result import run_counted  # noqa: E402

HELPER_ID = "checklist-edits"
FEATURE = "specs/001-feature"
WORKFLOW = f"{FEATURE}/.process/workflow.md"
RECORD = f"{FEATURE}/.process/checklist-edits/applied.json"
FIXTURE = REPO / "tests/speckit-pro/unit/fixtures/mutation-helpers/requests" / f"{HELPER_ID}.json"
HOSTS = ("claude", "codex")
RETIRED = ("then applies them to spec.md or plan.md", "then edit the artifact")
SPEC = "# Spec\nLogin uses a password.\nExports are open.\n"
PLAN = "# Plan\nSessions never expire.\n"
DOMAINS = ["security", "ux", "api"]


def edit(gap: str, file: str, find: str, replace: str) -> dict[str, str]:
    return {"gap": gap, "file": file, "find": find, "replace": replace}


def proposal(domain: str, *edits: dict[str, str], gaps: list[str] | None = None) -> dict[str, Any]:
    ids = gaps if gaps is not None else sorted({item["gap"] for item in edits})
    return {"domain": domain, "gaps": [{"id": gap, "description": f"{domain} {gap}"} for gap in ids], "edits": list(edits)}


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ChecklistEditsCase(MutationRequestCase):
    """A checkout with a spec and a plan; the helpers send one batch of proposals."""

    helper_id = HELPER_ID
    files = {WORKFLOW: "# Workflow\n", f"{FEATURE}/spec.md": SPEC, f"{FEATURE}/plan.md": PLAN}
    fixed_inputs = {"workflow_file": WORKFLOW, "feature_dir": FEATURE}

    def baseline(self) -> dict[str, str]:
        return dict(self.read_only_data()["baseline"])

    def apply(self, *proposals: dict[str, Any], mode: str = "apply", **inputs: object) -> dict[str, Any]:
        fields: dict[str, Any] = {"domains": DOMAINS, "baseline": self.baseline(), "proposals": list(proposals)}
        return self.call(mode, **{**fields, **inputs})

    def text(self, name: str) -> str:
        return (self.root / FEATURE / name).read_text(encoding="utf-8")


class ProposalTests(ChecklistEditsCase):
    """Proposals apply one domain at a time, in workflow order, under the lock."""

    def test_the_committed_request_fixture_is_served_by_the_registry(self) -> None:
        self.assertEqual(("read_only", "dry_run", "apply"), MUTATION_HELPERS[HELPER_ID].modes)

    def test_read_only_returns_the_digests_of_both_artifacts_and_writes_nothing(self) -> None:
        result = self.call("read_only")
        self.assertEqual({"spec.md": digest(SPEC), "plan.md": digest(PLAN)}, result["data"]["baseline"])
        self.assertFalse(result["data"]["writes_state"])
        self.assertFalse((self.root / RECORD).exists())

    def test_a_proposal_returns_gaps_and_edits_and_no_artifact_is_written(self) -> None:
        result = self.apply(
            proposal("security", edit("G1", "spec.md", "a password", "a password and a second factor")), mode="dry_run"
        )
        self.assertEqual("ok", result["status"], result)
        row = result["data"]["domains"][0]
        self.assertEqual(("security", 1, "applied", 1), (row["domain"], row["gaps"], row["status"], row["edits_applied"]))
        self.assertEqual((SPEC, PLAN), (self.text("spec.md"), self.text("plan.md")))
        self.assertFalse((self.root / RECORD).exists())

    def test_domains_apply_in_workflow_order_whatever_order_their_proposals_arrive_in(self) -> None:
        # The ux edit only matches once the security edit has run, so arrival order would show.
        security = proposal("security", edit("G1", "spec.md", "a password", "a password and a code"))
        ux = proposal("ux", edit("G2", "spec.md", "a code", "a code sent by email"), edit("G3", "plan.md", "never expire", "expire"))
        for arrival in ((security, ux), (ux, security)):
            with self.subTest(first=arrival[0]["domain"]):
                (self.root / FEATURE / "spec.md").write_text(SPEC, encoding="utf-8")
                (self.root / FEATURE / "plan.md").write_text(PLAN, encoding="utf-8")
                result = self.apply(*arrival)
                self.assertEqual("ok", result["status"], result)
                self.assertEqual(["security", "ux"], result["data"]["order"])
                self.assertEqual("# Spec\nLogin uses a password and a code sent by email.\nExports are open.\n", self.text("spec.md"))
                self.assertEqual("# Plan\nSessions expire.\n", self.text("plan.md"))

    def test_every_write_happens_under_the_lock_and_one_at_a_time(self) -> None:
        inside: list[bool] = []
        writes: list[str] = []
        real = checklist_edits.write_bytes_atomic

        def watched(path: Path, content: bytes, **kwargs: Any) -> Any:
            lock = self.root / RECORD
            inside.append(lock.with_suffix(".lock").is_dir())
            writes.append(path.name)
            return real(path, content, **kwargs)

        with patch.object(checklist_edits, "write_bytes_atomic", watched):
            result = self.apply(
                proposal("security", edit("G1", "spec.md", "open", "private"), edit("G2", "plan.md", "never", "always")),
                proposal("api", edit("G3", "spec.md", "private", "private to owners")),
            )
        self.assertEqual("ok", result["status"], result)
        self.assertTrue(inside and all(inside), inside)
        self.assertEqual(["spec.md", "plan.md", "spec.md"], writes)
        self.assertFalse((self.root / RECORD).with_suffix(".lock").exists())

    def test_the_record_lists_each_domain_in_the_order_it_was_applied(self) -> None:
        self.apply(
            proposal("api", edit("G2", "spec.md", "open", "private")),
            proposal("security", edit("G1", "plan.md", "never", "always")),
        )
        record = json.loads((self.root / RECORD).read_text(encoding="utf-8"))
        self.assertEqual(["security", "api"], [row["domain"] for row in record["domains"]])
        self.assertEqual("checklist-edits/v1", record["schema_version"])


class ConflictTests(ChecklistEditsCase):
    """An edit that does not match exactly once discards its domain and spares the others."""

    def test_a_domain_whose_edit_does_not_match_applies_none_of_its_edits_and_later_domains_still_run(self) -> None:
        result = self.apply(
            proposal("security", edit("G1", "spec.md", "open", "private"), edit("G2", "plan.md", "missing text", "x")),
            proposal("ux", edit("G3", "spec.md", "a password", "a passkey")),
        )
        self.assertEqual("ok", result["status"], result)
        first, second = result["data"]["domains"]
        self.assertEqual(("conflict", 0), (first["status"], first["edits_applied"]))
        self.assertEqual([{"gap": "G2", "file": "plan.md", "reason": "find text not found"}], first["conflicts"])
        self.assertEqual("applied", second["status"])
        self.assertEqual(["ux"], result["data"]["order"])
        self.assertEqual("# Spec\nLogin uses a passkey.\nExports are open.\n", self.text("spec.md"))
        self.assertEqual(PLAN, self.text("plan.md"))

    def test_an_edit_whose_find_text_matches_twice_is_a_conflict_not_a_guess(self) -> None:
        result = self.apply(proposal("security", edit("G1", "spec.md", "s", "S")))
        self.assertEqual(f"find text matches {SPEC.count('s')} times", result["data"]["domains"][0]["conflicts"][0]["reason"])
        self.assertEqual(SPEC, self.text("spec.md"))

    def test_gaps_with_no_edit_are_listed_for_the_orchestrator(self) -> None:
        result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private"), gaps=["G1", "G2"]))
        self.assertEqual(["G2"], result["data"]["domains"][0]["unproposed_gaps"])


class RefusalTests(ChecklistEditsCase):
    """A request that breaks the contract writes nothing."""

    def test_an_existing_lock_refuses_the_batch_without_stealing_it_or_writing(self) -> None:
        lock = (self.root / RECORD).with_suffix(".lock")
        lock.parent.mkdir(parents=True)
        lock.mkdir()
        result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual("input_error", result["status"], result)
        self.assertTrue(lock.is_dir())
        self.assertEqual((SPEC, PLAN), (self.text("spec.md"), self.text("plan.md")))

    def test_an_artifact_written_while_the_executors_ran_refuses_the_batch(self) -> None:
        before = self.baseline()
        (self.root / FEATURE / "plan.md").write_text(PLAN + "An executor wrote this.\n", encoding="utf-8")
        result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")), baseline=before)
        self.assertEqual("expected_failure", result["status"], result)
        self.assertEqual(["plan.md"], result["data"]["changed"])
        self.assertEqual(SPEC, self.text("spec.md"))
        self.assertFalse((self.root / RECORD).exists())

    def test_malformed_requests_are_refused_and_nothing_is_written(self) -> None:
        good = edit("G1", "spec.md", "open", "private")
        cases = {
            "unknown domain": proposal("billing", good),
            "edit names an unknown gap": proposal("security", edit("G9", "spec.md", "open", "private"), gaps=["G1"]),
            "file outside spec and plan": proposal("security", edit("G1", "tasks.md", "open", "private")),
            "path traversal": proposal("security", edit("G1", "../spec.md", "open", "private")),
            "empty find text": proposal("security", edit("G1", "spec.md", "", "private")),
            "unknown edit field": proposal("security", {**good, "mood": "calm"}),
            "duplicate gap id": {**proposal("security", good), "gaps": [{"id": "G1", "description": "a"}, {"id": "G1", "description": "b"}]},
            "oversized replace": proposal("security", edit("G1", "spec.md", "open", "x" * 20001)),
            "not an object": "security",
        }
        for label, bad in cases.items():
            with self.subTest(label):
                result = self.apply(bad)
                self.assertEqual("input_error", result["status"], result)
                self.assertEqual((SPEC, PLAN), (self.text("spec.md"), self.text("plan.md")))
        duplicate = self.apply(proposal("security", good), proposal("security", good))
        self.assertEqual("input_error", duplicate["status"], duplicate)
        self.assertEqual("input_error", self.apply(domains=["security", "security"])["status"])
        self.assertEqual("input_error", self.apply(baseline={"spec.md": "x"})["status"])
        self.assertFalse((self.root / RECORD).exists())

    def test_a_feature_directory_outside_the_repository_is_refused(self) -> None:
        for bad in ("../elsewhere", "/etc"):
            with self.subTest(bad):
                self.assertEqual("input_error", self.call("read_only", feature_dir=bad)["status"])


def run_dist_helper(host: str, root: Path, mode: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Send one request to the runner a host's payload ships, from inside a throwaway checkout."""
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    request = {**document, "mode": mode, "inputs": {**document["inputs"], "workflow_file": WORKFLOW, "feature_dir": FEATURE, **inputs}}
    environment = {**os.environ, "PYTHONPATH": str(REPO / "dist" / host / "speckit-pro")}
    done = subprocess.run([sys.executable, "-m", "speckit_pro_runner"], input=json.dumps(request), capture_output=True,
                          text=True, env=environment, cwd=root, check=True)
    return json.loads(done.stdout)


class HostParityTests(unittest.TestCase):
    def test_both_payloads_plan_and_apply_the_same_proposals_in_the_same_order(self) -> None:
        proposals = [
            proposal("ux", edit("G2", "spec.md", "a code", "a code by email")),
            proposal("security", edit("G1", "spec.md", "a password", "a password and a code")),
        ]
        outcomes = []
        for host in HOSTS:
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                (root / ".specify").mkdir()
                (root / WORKFLOW).parent.mkdir(parents=True)
                (root / WORKFLOW).write_text("# Workflow\n", encoding="utf-8")
                (root / FEATURE / "spec.md").write_text(SPEC, encoding="utf-8")
                (root / FEATURE / "plan.md").write_text(PLAN, encoding="utf-8")
                baseline = run_dist_helper(host, root, "read_only", {})["data"]["baseline"]
                applied = run_dist_helper(host, root, "apply", {"domains": DOMAINS, "baseline": baseline, "proposals": proposals})
                outcomes.append((applied["status"], applied["data"]["order"], applied["data"]["domains"],
                                 (root / FEATURE / "spec.md").read_text(encoding="utf-8")))
        self.assertEqual("ok", outcomes[0][0])
        self.assertEqual(["security", "ux"], outcomes[0][1])
        self.assertEqual(outcomes[0], outcomes[1])


EXECUTOR_GUIDES = ("agents/checklist-executor.md", "codex-agents/checklist-executor.toml")


class GuidanceTests(unittest.TestCase):
    """The prose points at the helper and never tells an executor to write the artifacts."""

    def test_the_checklist_executor_proposes_edits_and_never_writes_spec_or_plan_on_either_host(self) -> None:
        for relative in EXECUTOR_GUIDES:
            text = guide_text(relative)
            self.assertEqual([], [(relative, phrase) for phrase in ("Proposed Edits", "Do not edit spec.md or plan.md") if phrase not in text])
            self.assertEqual([], [(relative, phrase) for phrase in RETIRED if phrase in text])

    def test_the_phase_four_flow_applies_proposals_through_the_helper_on_both_hosts(self) -> None:
        for guide in PHASE_EXECUTION_GUIDES:
            text = guide_view(guide)
            self.assertEqual((True, True, False), ("runner helper `checklist-edits`" in text, "in domain order" in text,
                                                   "Domain 2 may depend on Domain 1's gap fixes" in text), guide)


if __name__ == "__main__":
    sys.exit(
        run_counted(
            unittest.TestSuite(
                unittest.defaultTestLoader.loadTestsFromTestCase(case)
                for case in (ProposalTests, ConflictTests, RefusalTests, HostParityTests, GuidanceTests)
            ),
            label="test-checklist-edits",
        )
    )
