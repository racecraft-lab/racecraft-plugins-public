#!/usr/bin/env python3
"""Checklist check-and-propose (ADR 0018): executors propose, the runner applies in domain order.

A domain executor returns its gaps and proposed edits and writes neither spec.md
nor plan.md. The `checklist-edits` helper snapshots both files before the executors
run, refuses to apply when either changed, and then applies one domain at a time in
workflow order under one lock, so no two writes touch the files at once.
"""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
import sys
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / "speckit-pro"), str(REPO / "tests/speckit-pro/lib")]
from speckit_pro_runner import atomic_write  # noqa: E402
from speckit_pro_runner.helpers import checklist_edits  # noqa: E402
from speckit_pro_runner.helpers.registry import MUTATION_HELPERS  # noqa: E402
from guide_text import PHASE_EXECUTION_GUIDES, guide_text, guide_view  # noqa: E402
from mutation_request_case import MutationRequestCase  # noqa: E402
from test_result import run_counted  # noqa: E402

HELPER_ID = "checklist-edits"
FEATURE = "specs/001-feature"
WORKFLOW = f"{FEATURE}/.process/workflow.md"
RECORD = f"{FEATURE}/.process/checklist-edits/applied.json"
OTHER_WORKFLOW = "docs/workflows/other.md"
FIXTURE = REPO / "tests/speckit-pro/unit/fixtures/mutation-helpers/requests" / f"{HELPER_ID}.json"
HOSTS = ("claude", "codex")
RETIRED = ("then applies them to spec.md or plan.md", "then edit the artifact")
SPEC = "# Spec\nLogin uses a password.\nExports are open.\n"
PLAN = "# Plan\nSessions never expire.\n"
DOMAINS = ["security", "ux", "api"]


def edit(*fields: str) -> dict[str, str]:
    """One proposed edit from (gap, file, find, replace)."""
    return dict(zip(("gap", "file", "find", "replace"), fields, strict=True))


def proposal(domain: str, *edits: dict[str, str], gaps: list[str] | None = None) -> dict[str, Any]:
    ids = gaps if gaps is not None else sorted({item["gap"] for item in edits})
    return {"domain": domain, "gaps": [{"id": gap, "description": f"{domain} {gap}"} for gap in ids], "edits": list(edits)}


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def feature_locked(root: Path) -> bool:
    """Whether another descriptor holds the feature directory's lock right now."""
    directory = os.open(root / FEATURE, os.O_RDONLY)
    try:
        fcntl.flock(directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return True
    finally:
        os.close(directory)
    return False


class ChecklistEditsCase(MutationRequestCase):
    """A checkout with a spec and a plan; the helpers send one batch of proposals."""

    helper_id = HELPER_ID
    files = {WORKFLOW: "# Workflow\n", OTHER_WORKFLOW: "# Workflow\n", f"{FEATURE}/spec.md": SPEC, f"{FEATURE}/plan.md": PLAN}
    fixed_inputs = {"workflow_file": WORKFLOW, "feature_dir": FEATURE}

    def baseline(self) -> dict[str, str]:
        return dict(self.read_only_data()["baseline"])

    def apply(self, *proposals: Any, mode: str = "apply", **inputs: object) -> dict[str, Any]:
        """Send the proposals, with an empty one for each listed domain that sent none, as a clean domain would."""
        sent = {item["domain"] for item in proposals if isinstance(item, dict)}
        padded = [*proposals, *(proposal(name) for name in DOMAINS if name not in sent)]
        fields: dict[str, Any] = {"domains": DOMAINS, "baseline": self.baseline(), "proposals": padded}
        return self.call(mode, **{**fields, **inputs})

    def text(self, name: str) -> str:
        return (self.root / FEATURE / name).read_text(encoding="utf-8")

    @contextmanager
    def before_write(self, action: Callable[[int], None]) -> Iterator[None]:
        """Run `action(n)` just before the helper's n-th artifact write starts."""
        real = checklist_edits.write_bytes_atomic
        count = [0]

        def hooked(path: Path, content: bytes, **kwargs: Any) -> Any:
            count[0] += 1
            action(count[0])
            return real(path, content, **kwargs)

        with patch.object(checklist_edits, "write_bytes_atomic", hooked):
            yield


class ProposalTests(ChecklistEditsCase):
    """Proposals apply one domain at a time, in workflow order, under the lock."""

    def test_the_registry_serves_the_committed_request_fixture(self) -> None:
        self.assertEqual(HELPER_ID, json.loads(FIXTURE.read_text(encoding="utf-8"))["helper_id"])
        self.assertEqual(("read_only", "dry_run", "apply"), MUTATION_HELPERS[HELPER_ID].modes)
        self.assertEqual(["plan.md", "spec.md"], sorted(self.read_only_data()["baseline"]))

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
                self.assertEqual(["security", "ux", "api"], result["data"]["order"])
                self.assertEqual("# Spec\nLogin uses a password and a code sent by email.\nExports are open.\n", self.text("spec.md"))
                self.assertEqual("# Plan\nSessions expire.\n", self.text("plan.md"))

    def test_every_write_happens_under_the_lock_and_one_at_a_time(self) -> None:
        inside: list[bool] = []
        writes: list[str] = []
        real = checklist_edits.write_bytes_atomic

        def watched(path: Path, content: bytes, **kwargs: Any) -> Any:
            inside.append(feature_locked(self.root))
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
        self.assertFalse(feature_locked(self.root))

    def test_the_record_lists_each_domain_in_the_order_it_was_applied(self) -> None:
        self.apply(
            proposal("api", edit("G2", "spec.md", "open", "private")),
            proposal("security", edit("G1", "plan.md", "never", "always")),
        )
        record = json.loads((self.root / RECORD).read_text(encoding="utf-8"))
        self.assertEqual(["security", "ux", "api"], [row["domain"] for row in record["domains"]])
        self.assertEqual("checklist-edits/v1", record["schema_version"])


class ConflictTests(ChecklistEditsCase):
    """An edit that does not match exactly once discards its domain and spares the others."""

    def test_a_domain_whose_edit_does_not_match_applies_none_of_its_edits_and_later_domains_still_run(self) -> None:
        result = self.apply(
            proposal("security", edit("G1", "spec.md", "open", "private"), edit("G2", "plan.md", "missing text", "x")),
            proposal("ux", edit("G3", "spec.md", "a password", "a passkey")),
        )
        self.assertEqual("ok", result["status"], result)
        first, second, third = result["data"]["domains"]
        self.assertEqual(("conflict", 0), (first["status"], first["edits_applied"]))
        self.assertEqual([{"gap": "G2", "file": "plan.md", "reason": "find text not found"}], first["conflicts"])
        self.assertEqual("applied", second["status"])
        self.assertEqual(["ux", "api"], result["data"]["order"])
        self.assertEqual(("applied", 0), (third["status"], third["edits_applied"]))
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

    def test_a_held_lock_refuses_the_batch_without_stealing_it_or_writing(self) -> None:
        holder = os.open(self.root / FEATURE, os.O_RDONLY)
        self.addCleanup(os.close, holder)
        fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual("input_error", result["status"], result)
        self.assertIn("holds this feature", json.dumps(result))
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

    def test_a_listed_domain_with_no_proposal_is_refused_not_read_as_clean(self) -> None:
        result = self.call("apply", domains=DOMAINS, baseline=self.baseline(), proposals=[proposal("ux", edit("G1", "spec.md", "open", "private"))])
        self.assertEqual("input_error", result["status"], result)
        self.assertIn("missing ['security', 'api']", json.dumps(result))
        self.assertEqual(SPEC, self.text("spec.md"))

    def test_a_check_with_no_domains_compares_the_digests_only(self) -> None:
        before = self.baseline()
        check = {"domains": [], "baseline": before, "proposals": []}
        self.assertEqual("ok", self.call("dry_run", **check)["status"])
        (self.root / FEATURE / "spec.md").write_text(SPEC + "A verify run wrote this.\n", encoding="utf-8")
        result = self.call("dry_run", **check)
        self.assertEqual(("expected_failure", ["spec.md"]), (result["status"], result["data"]["changed"]))

    def test_a_write_failure_names_the_domains_already_applied(self) -> None:
        real = checklist_edits.write_bytes_atomic
        calls: list[str] = []

        def failing(path: Path, content: bytes, **kwargs: Any) -> Any:
            calls.append(path.name)
            if len(calls) == 2:
                raise OSError("disk full")
            return real(path, content, **kwargs)

        with patch.object(checklist_edits, "write_bytes_atomic", failing):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")),
                                proposal("ux", edit("G2", "plan.md", "never", "always")))
        self.assertEqual(("expected_failure", ["security"], "ux"), (result["status"], result["data"]["applied"], result["data"]["failed"]))
        self.assertEqual(("apply_interrupted", "# Spec\nLogin uses a password.\nExports are private.\n", PLAN),
                         (result["diagnostics"][0]["code"], self.text("spec.md"), self.text("plan.md")))
        self.assertFalse(feature_locked(self.root))

    def test_a_feature_directory_outside_the_repository_is_refused(self) -> None:
        for bad in ("../elsewhere", "/etc"):
            with self.subTest(bad):
                self.assertEqual("input_error", self.call("read_only", feature_dir=bad)["status"])

    def test_a_record_write_failure_reports_the_domains_already_applied(self) -> None:
        with patch.object(checklist_edits, "write_file_atomic", side_effect=OSError("disk full")):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual("expected_failure", result["status"], result)
        self.assertEqual(["security", "ux", "api"], result["data"]["applied"])
        self.assertEqual("apply_interrupted", result["diagnostics"][0]["code"])
        self.assertIn("Restore", result["diagnostics"][0]["remediation"]["summary"])
        self.assertIn("private", self.text("spec.md"))


def target_changes(root: Path, name: str) -> dict[str, Callable[[], None]]:
    """The receipt's changes to one artifact after the helper read it, keyed by form."""
    target = root / FEATURE / name
    other = root / "elsewhere.md"

    def mutate() -> None:
        target.write_text(target.read_text(encoding="utf-8") + "Concurrent.\n", encoding="utf-8")

    def replace() -> None:
        other.write_text("# Replaced\n", encoding="utf-8")
        os.replace(other, target)

    def delete() -> None:
        target.unlink()

    def link(text: str) -> Callable[[], None]:
        def substitute() -> None:
            other.unlink(missing_ok=True)
            other.write_text(text, encoding="utf-8")
            target.unlink()
            os.link(other, target)
        return substitute

    return {"content mutation": mutate, "regular-file replacement": replace, "deletion": delete,
            "hard-link substitution": link("# Linked\n"), "same-text hard-link substitution": link(target.read_text(encoding="utf-8"))}


class CompetingWriterTests(ChecklistEditsCase):
    """cr1278 High and F1278-812f7be4: no change made by anyone else is lost or overwritten with stale text."""

    def test_two_workflows_on_one_feature_never_lose_an_edit_reported_applied(self) -> None:
        # The Codex interleaving: both start from one baseline; the inner apply runs inside the outer one.
        baseline = self.baseline()
        inner: dict[str, Any] = {}

        def competitor(number: int) -> None:
            if number == 1:
                inner.update(self.apply(proposal("ux", edit("G2", "spec.md", "a password", "a passkey")),
                                        workflow_file=OTHER_WORKFLOW, baseline=baseline))

        with self.before_write(competitor):
            outer = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")), baseline=baseline)
        final = self.text("spec.md")
        lost = [word for word, result in (("passkey", inner), ("private", outer)) if result["status"] == "ok" and word not in final]
        self.assertEqual([], lost, (inner, outer, final))
        self.assertEqual("input_error", inner["status"], inner)
        self.assertEqual("ok", outer["status"], outer)

    def test_a_target_changed_after_the_read_refuses_the_batch_and_keeps_the_change(self) -> None:
        edits = {"spec.md": edit("G1", "spec.md", "open", "private"), "plan.md": edit("G1", "plan.md", "never", "always")}
        for name, change_edit in edits.items():
            for form in target_changes(self.root, name):
                with self.subTest(name=name, form=form):
                    for artifact, text in (("spec.md", SPEC), ("plan.md", PLAN)):
                        (self.root / FEATURE / artifact).unlink(missing_ok=True)
                        (self.root / FEATURE / artifact).write_text(text, encoding="utf-8")
                    change = target_changes(self.root, name)[form]
                    baseline = self.baseline()
                    target = self.root / FEATURE / name
                    seen: dict[str, Any] = {}

                    def act(number: int) -> None:
                        if number == 1:
                            change()
                            seen["text"] = target.read_text(encoding="utf-8") if target.exists() else None
                            seen["inode"] = target.stat().st_ino if target.exists() else None

                    with self.before_write(act):
                        result = self.apply(proposal("security", change_edit), baseline=baseline)
                    self.assertEqual(("expected_failure", [name]), (result["status"], result["data"].get("changed")), result)
                    self.assertEqual((seen["text"], seen["inode"]),
                                     (target.read_text(encoding="utf-8"), target.stat().st_ino) if target.exists() else (None, None))

    def test_a_replaced_feature_directory_is_not_written(self) -> None:
        moved = self.root / "specs/001-moved"

        def act(number: int) -> None:
            if number == 1:
                (self.root / FEATURE).rename(moved)
                (self.root / FEATURE).mkdir()
                (self.root / FEATURE / "spec.md").write_text(SPEC, encoding="utf-8")
                (self.root / FEATURE / "plan.md").write_text(PLAN, encoding="utf-8")

        with self.before_write(act):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual("expected_failure", result["status"], result)
        self.assertEqual((SPEC, SPEC), (self.text("spec.md"), (moved / "spec.md").read_text(encoding="utf-8")))

    def test_a_change_between_the_two_writes_of_a_domain_is_kept_and_reported(self) -> None:
        def act(number: int) -> None:
            if number == 2:
                (self.root / FEATURE / "plan.md").write_text(PLAN + "Concurrent.\n", encoding="utf-8")

        with self.before_write(act):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private"), edit("G2", "plan.md", "never", "always")))
        self.assertEqual(("expected_failure", "apply_interrupted"), (result["status"], result["diagnostics"][0]["code"]), result)
        self.assertEqual(([], "security", ["spec.md"]), (result["data"]["applied"], result["data"]["failed"], result["data"]["partial"]))
        self.assertEqual(PLAN + "Concurrent.\n", self.text("plan.md"))

    def test_a_change_between_domains_is_kept_and_reported(self) -> None:
        def act(number: int) -> None:
            if number == 2:
                (self.root / FEATURE / "spec.md").write_text("# Spec\nConcurrent.\nExports are private.\nLogin uses a password.\n", encoding="utf-8")

        with self.before_write(act):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")),
                                proposal("ux", edit("G2", "spec.md", "a password", "a passkey")))
        self.assertEqual(("expected_failure", ["security"], "ux", []),
                         (result["status"], result["data"].get("applied"), result["data"].get("failed"), result["data"].get("partial")), result)
        self.assertIn("Concurrent.", self.text("spec.md"))

    def test_a_check_with_no_domains_refuses_a_change_made_after_its_read(self) -> None:
        real = checklist_edits.read_artifacts
        calls = [0]

        def read_then_change(*args: Any) -> Any:
            contents = real(*args)
            calls[0] += 1
            if calls[0] == 1:
                (self.root / FEATURE / "spec.md").write_text(SPEC + "A late write.\n", encoding="utf-8")
            return contents

        before = self.baseline()
        with patch.object(checklist_edits, "read_artifacts", read_then_change):
            result = self.call("dry_run", domains=[], baseline=before, proposals=[])
        self.assertEqual(("expected_failure", ["spec.md"]), (result["status"], result["data"].get("changed")), result)



def same_text_swaps(root: Path, name: str) -> dict[str, Callable[[], None]]:
    """Swaps that keep the bytes but change which file the canonical name holds, or add an alias to it."""
    target = root / FEATURE / name
    other = root / "elsewhere.md"

    def replace() -> None:
        other.write_bytes(target.read_bytes())
        os.replace(other, target)

    def link() -> None:
        other.unlink(missing_ok=True)
        other.write_bytes(target.read_bytes())
        target.unlink()
        os.link(other, target)

    def alias() -> None:
        os.link(target, root / "alias.md")

    return {"same-text replacement": replace, "same-text hard-link substitution": link, "added hard-link alias": alias}


def swap_feature_directory(root: Path) -> None:
    """Rename the feature away and put a competitor's copy of the original artifacts under its name."""
    feature = root / FEATURE
    feature.rename(root / "specs/001-detached")
    feature.mkdir()
    (feature / "spec.md").write_text(SPEC, encoding="utf-8")
    (feature / "plan.md").write_text(PLAN, encoding="utf-8")


class CanonicalResultTests(ChecklistEditsCase):
    """F1278-812f7be4 after the pre-checks: the result is checked against the canonical paths after acting."""

    def reset(self) -> None:
        for name, text in (("spec.md", SPEC), ("plan.md", PLAN)):
            (self.root / FEATURE / name).unlink(missing_ok=True)
            (self.root / FEATURE / name).write_text(text, encoding="utf-8")
        for extra in ("alias.md", "elsewhere.md"):
            (self.root / extra).unlink(missing_ok=True)

    def test_a_check_with_no_domains_refuses_a_same_text_swap_made_after_its_read(self) -> None:
        for name in ("spec.md", "plan.md"):
            for form in same_text_swaps(self.root, name):
                with self.subTest(name=name, form=form):
                    self.reset()
                    swap = same_text_swaps(self.root, name)[form]
                    real = checklist_edits.read_artifacts
                    calls = [0]

                    def read_then_swap(*args: Any) -> Any:
                        contents = real(*args)
                        calls[0] += 1
                        if calls[0] == 1:
                            swap()
                        return contents

                    before = self.baseline()
                    with patch.object(checklist_edits, "read_artifacts", read_then_swap):
                        result = self.call("dry_run", domains=[], baseline=before, proposals=[])
                    self.assertEqual("expected_failure", result["status"], result)
                    self.assertIn(name, result["data"].get("changed", []), result)

    def test_a_feature_directory_swapped_after_the_parent_check_is_never_reported_applied(self) -> None:
        real = atomic_write.ensure_safe_write_target_fd
        done = [False]

        def check_then_swap(parent_fd: int, name: str) -> None:
            real(parent_fd, name)
            if name == "spec.md" and not done[0]:
                done[0] = True
                swap_feature_directory(self.root)

        with patch.object(atomic_write, "ensure_safe_write_target_fd", check_then_swap):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual(("expected_failure", "apply_interrupted"), (result["status"], result["diagnostics"][0]["code"]), result)
        self.assertIn("spec.md", result["data"].get("moved", []), result)
        self.assertFalse(result["data"]["record_written"], result)
        self.assertEqual(SPEC, self.text("spec.md"))

    def test_a_feature_directory_swapped_after_the_last_write_is_never_reported_applied(self) -> None:
        real = checklist_edits.write_bytes_atomic

        def write_then_swap(path: Path, content: bytes, **kwargs: Any) -> Any:
            written = real(path, content, **kwargs)
            swap_feature_directory(self.root)
            return written

        with patch.object(checklist_edits, "write_bytes_atomic", write_then_swap):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual(("expected_failure", "apply_interrupted"), (result["status"], result["diagnostics"][0]["code"]), result)
        self.assertIn("spec.md", result["data"].get("moved", []), result)
        self.assertFalse(result["data"]["record_written"], result)
        self.assertFalse((self.root / RECORD).exists())
        self.assertEqual(SPEC, self.text("spec.md"))

    def test_a_record_directory_swapped_after_it_opens_is_never_reported_written(self) -> None:
        real = atomic_write.ensure_safe_write_target_fd
        done = [False]

        def check_then_swap(parent_fd: int, name: str) -> None:
            real(parent_fd, name)
            if name == "applied.json" and not done[0]:
                done[0] = True
                directory = (self.root / RECORD).parent
                directory.rename(self.root / "detached-record")
                directory.mkdir()

        with patch.object(atomic_write, "ensure_safe_write_target_fd", check_then_swap):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual(("expected_failure", False), (result["status"], result["data"].get("record_written")), result)
        self.assertIn("applied.json", result["data"].get("moved", []), result)
        self.assertFalse((self.root / RECORD).exists())

    def test_an_artifact_substituted_after_the_final_check_is_kept_and_reported(self) -> None:
        edits = {"spec.md": edit("G1", "spec.md", "open", "private"), "plan.md": edit("G1", "plan.md", "never", "always")}
        for name, change_edit in edits.items():
            with self.subTest(name=name):
                self.reset()
                real = atomic_write.ensure_write_target_matches_snapshot_fd
                done = [False]

                def check_then_substitute(parent_fd: int, target_name: str, expected: dict[str, Any]) -> None:
                    real(parent_fd, target_name, expected)
                    if target_name == name and not done[0]:
                        done[0] = True
                        other = self.root / "elsewhere.md"
                        other.write_text("# Competitor\n", encoding="utf-8")
                        os.replace(other, self.root / FEATURE / name)

                with patch.object(atomic_write, "ensure_write_target_matches_snapshot_fd", check_then_substitute):
                    result = self.apply(proposal("security", change_edit))
                self.assertEqual(("expected_failure", [name]), (result["status"], result["data"].get("changed")), result)
                self.assertEqual("# Competitor\n", self.text(name))

    def test_an_unavailable_swap_refuses_the_write_and_keeps_a_competing_edit(self) -> None:
        target = self.root / FEATURE / "spec.md"

        def unavailable(*args: Any) -> bool:
            target.write_text("# Competitor\n", encoding="utf-8")
            return False

        with patch.object(atomic_write, "swap_entries", unavailable):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual("expected_failure", result["status"], result)
        self.assertEqual("# Competitor\n", self.text("spec.md"))
        self.assertFalse((self.root / RECORD).exists())
        self.assertFalse(feature_locked(self.root))

    def test_a_concurrent_record_is_kept_and_reported(self) -> None:
        for prior in (False, True):
            with self.subTest(prior_record=prior):
                self.reset()
                record = self.root / RECORD
                record.unlink(missing_ok=True)
                if prior:
                    record.parent.mkdir(parents=True, exist_ok=True)
                    record.write_text('{"earlier": true}\n', encoding="utf-8")
                real = checklist_edits.write_file_atomic

                def compete_then_write(path: Path, content: str, **kwargs: Any) -> Any:
                    path.write_text('{"competitor": true}\n', encoding="utf-8")
                    return real(path, content, **kwargs)

                with patch.object(checklist_edits, "write_file_atomic", compete_then_write):
                    result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
                self.assertEqual(("expected_failure", False), (result["status"], result["data"].get("record_written")), result)
                self.assertEqual('{"competitor": true}\n', record.read_text(encoding="utf-8"))

    def test_a_record_substituted_after_the_final_check_is_kept_and_reported(self) -> None:
        for prior in (False, True):
            with self.subTest(prior_record=prior):
                self.reset()
                record = self.root / RECORD
                record.unlink(missing_ok=True)
                if prior:
                    record.parent.mkdir(parents=True, exist_ok=True)
                    record.write_text('{"earlier": true}\n', encoding="utf-8")
                real = atomic_write.ensure_write_target_matches_snapshot_fd

                def check_then_compete(parent_fd: int, target_name: str, expected: dict[str, Any]) -> None:
                    real(parent_fd, target_name, expected)
                    if target_name == "applied.json":
                        record.write_text('{"competitor": true}\n', encoding="utf-8")

                with patch.object(atomic_write, "ensure_write_target_matches_snapshot_fd", check_then_compete):
                    result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
                self.assertEqual(("expected_failure", False), (result["status"], result["data"].get("record_written")), result)
                self.assertEqual('{"competitor": true}\n', record.read_text(encoding="utf-8"))

class CommittedStateTests(ChecklistEditsCase):
    """F1278-d7ff996f and F1278-afb94c5e: a failure after the first write reports what is on disk."""

    def failing_write(self, failing_call: int) -> Any:
        def fail(number: int) -> None:
            if number == failing_call:
                raise OSError("disk full")

        return self.before_write(fail)

    def test_a_half_written_first_domain_is_reported_as_partial(self) -> None:
        with self.failing_write(2):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private"), edit("G2", "plan.md", "never", "always")))
        self.assertEqual(("expected_failure", [], "security", ["spec.md"]),
                         (result["status"], result["data"]["applied"], result["data"]["failed"], result["data"].get("partial")), result)
        self.assertEqual(("# Spec\nLogin uses a password.\nExports are private.\n", PLAN), (self.text("spec.md"), self.text("plan.md")))

    def test_a_half_written_later_domain_is_reported_as_partial(self) -> None:
        with self.failing_write(3):
            result = self.apply(proposal("security", edit("G1", "spec.md", "a password", "a passkey")),
                                proposal("ux", edit("G2", "spec.md", "open", "private"), edit("G3", "plan.md", "never", "always")))
        self.assertEqual((["security"], "ux", ["spec.md"]),
                         (result["data"]["applied"], result["data"]["failed"], result["data"].get("partial")), result)
        self.assertIn("private", self.text("spec.md"))

    def test_a_record_published_before_its_failure_is_reported_written(self) -> None:
        real = checklist_edits.write_file_atomic

        def publish_then_fail(path: Path, content: str, **kwargs: Any) -> None:
            real(path, content, **kwargs)
            raise OSError("directory sync failed")

        with patch.object(checklist_edits, "write_file_atomic", publish_then_fail):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual(("expected_failure", "apply_interrupted"), (result["status"], result["diagnostics"][0]["code"]), result)
        self.assertEqual((["security", "ux", "api"], True), (result["data"]["applied"], result["data"].get("record_written")), result)
        self.assertTrue((self.root / RECORD).is_file())

    def test_a_record_path_held_by_a_directory_is_refused_before_any_write(self) -> None:
        (self.root / RECORD).mkdir(parents=True)
        result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual("input_error", result["status"], result)
        self.assertEqual(SPEC, self.text("spec.md"))

    def test_a_refusal_raised_after_the_writes_reports_them(self) -> None:
        # A ValueError, not an OSError, after the artifacts reached disk.
        with patch.object(checklist_edits, "write_file_atomic", side_effect=ValueError("record directory is not usable")):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual(("expected_failure", ["security", "ux", "api"]), (result["status"], result["data"].get("applied")), result)
        self.assertIn("private", self.text("spec.md"))

    def test_a_lock_release_failure_after_the_writes_reports_them(self) -> None:
        real = checklist_edits.held_feature

        @contextmanager
        def failing_release(*args: Any, exclusive: bool) -> Iterator[Any]:
            with real(*args, exclusive=exclusive) as held:
                yield held
            if exclusive:
                raise OSError("lock cleanup failed")

        with patch.object(checklist_edits, "held_feature", failing_release):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual(("expected_failure", ["security", "ux", "api"], True),
                         (result["status"], result["data"].get("applied"), result["data"].get("record_written")), result)
        self.assertIn("private", self.text("spec.md"))


    def test_a_record_directory_swapped_for_a_link_is_not_followed(self) -> None:
        # Validator differential: the record path is checked link-free, then must be written the same way.
        outside = self.root / "outside"
        outside.mkdir()

        def act(number: int) -> None:
            if number == 1:
                directory = (self.root / RECORD).parent
                shutil.rmtree(directory)
                directory.symlink_to(outside, target_is_directory=True)

        with self.before_write(act):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual([], sorted(path.name for path in outside.iterdir()))
        self.assertEqual(("expected_failure", "application record", False),
                         (result["status"], result["data"].get("failed"), result["data"].get("record_written")), result)

class UntrustedTextTests(ChecklistEditsCase):
    """F1278-5ad50d38: hidden characters and credential-shaped text never reach spec.md or plan.md."""

    def test_hidden_characters_and_credentials_are_refused_and_nothing_is_written(self) -> None:
        cases = {
            "bidi override": edit("G1", "spec.md", "open", "open \u202eetavirp"),
            "isolate": edit("G1", "spec.md", "open", "\u2066private\u2069"),
            "terminal escape": edit("G1", "spec.md", "open", "\x1b[2Jprivate"),
            "line separator": edit("G1", "spec.md", "open", "private\u2028"),
            "hidden find": edit("G1", "spec.md", "open\u200b", "private"),
            "credential": edit("G1", "spec.md", "open", "private; token: ghp_" + "a1" * 20),
        }
        for label, bad in cases.items():
            with self.subTest(label):
                result = self.apply(proposal("security", bad))
                self.assertEqual("input_error", result["status"], result)
                self.assertEqual((SPEC, PLAN), (self.text("spec.md"), self.text("plan.md")))

    def test_edits_that_only_together_form_a_credential_are_a_conflict(self) -> None:
        # Validator differential: each replace passes the credential check alone; the written line does not.
        first, second = "a1" * 10, "b2" * 10
        result = self.apply(proposal("security", edit("G1", "spec.md", "open", f"open ghp_{first}")),
                            proposal("ux", edit("G2", "spec.md", f"{first}.", f"{first}{second}.")))
        self.assertEqual("ok", result["status"], result)
        self.assertEqual(["security", "api"], result["data"]["order"])
        self.assertEqual("edits would write credential-shaped text", result["data"]["domains"][1]["conflicts"][0]["reason"])
        self.assertNotIn(first + second, self.text("spec.md"))

    def test_markdown_tabs_and_line_breaks_still_apply(self) -> None:
        result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private:\n\t- see [ADR](docs/adr.md)")))
        self.assertEqual("ok", result["status"], result)
        self.assertIn("private:\n\t- see [ADR](docs/adr.md)", self.text("spec.md"))


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
            proposal("api"),
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
        self.assertEqual(["security", "ux", "api"], outcomes[0][1])
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
        # Each host's own checklist passage: Claude's Phase 4 section, Codex's checklist-only loop step.
        for guide, anchor in zip(PHASE_EXECUTION_GUIDES, ("### Phase 4: Checklist", "Checklist only:"), strict=True):
            passage = guide_view(guide).split(anchor, 1)[1][:3500]
            apply_at, consensus_at, verify_at = (passage.find(text) for text in ("mode apply" if "Phase" in anchor else "in apply mode",
                                                                               "consensus", "Mode: verify"))
            self.assertTrue(0 <= apply_at < consensus_at < verify_at, (guide, apply_at, consensus_at, verify_at))
            for phrase in ("runner helper `checklist-edits`", "in domain order", "dry_run"):
                self.assertIn(phrase, passage, guide)
            self.assertNotIn("Domain 2 may depend on Domain 1's gap fixes", passage)
            self.assertIn("restore both files before any retry", passage)


if __name__ == "__main__":
    sys.exit(
        run_counted(
            unittest.TestSuite(
                unittest.defaultTestLoader.loadTestsFromTestCase(case)
                for case in (ProposalTests, ConflictTests, RefusalTests, CompetingWriterTests, CanonicalResultTests, CommittedStateTests,
                             UntrustedTextTests, HostParityTests, GuidanceTests)
            ),
            label="test-checklist-edits",
        )
    )
