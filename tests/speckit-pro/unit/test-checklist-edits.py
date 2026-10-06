#!/usr/bin/env python3
"""Checklist check-and-propose (ADR 0018): executors propose, the runner applies in domain order.

A domain executor returns its gaps and proposed edits and writes neither spec.md
nor plan.md. The `checklist-edits` helper snapshots both files before the executors
run, refuses to apply when either changed, and then applies one domain at a time in
workflow order under one lock, so no two writes touch the files at once.
"""

from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
import fcntl
from functools import partial
import hashlib
import json
import os
import shutil
import stat
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
from speckit_pro_runner.helpers import checklist_edits, read_only  # noqa: E402
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


def raise_error(error: Exception) -> None:
    raise error


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


class InterruptionCase(ChecklistEditsCase):
    """Fault-injection helpers for applies that fail after they began writing."""

    def reset(self) -> None:
        for name, text in (("spec.md", SPEC), ("plan.md", PLAN)):
            (self.root / FEATURE / name).unlink(missing_ok=True)
            (self.root / FEATURE / name).write_text(text, encoding="utf-8")
        for extra in ("alias.md", "elsewhere.md"):
            (self.root / extra).unlink(missing_ok=True)

    def failing_write(self, failing_call: int) -> Any:
        def fail(number: int) -> None:
            if number == failing_call:
                raise OSError("disk full")

        return self.before_write(fail)

    def after_call(self, name: str, action: Callable[[], None]) -> Any:
        """Patch checklist_edits.`name` so `action` runs right after each real call returns."""
        real = getattr(checklist_edits, name)

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            returned = real(*args, **kwargs)
            action()
            return returned

        return patch.object(checklist_edits, name, wrapped)

    def assert_interrupted_after_writes(self, result: dict[str, Any], record_written: bool) -> None:
        """Every domain reached disk, nothing is half written, and the record is reported as it is on disk."""
        self.assertEqual(("expected_failure", "apply_interrupted", ["security", "ux", "api"], [], record_written),
                         (result["status"], result["diagnostics"][0]["code"], result["data"].get("applied"),
                          result["data"].get("partial"), result["data"].get("record_written")), result)
        self.assert_both_written()
        self.assertEqual(record_written, (self.root / RECORD).is_file())

    def around_lock(self, *, on_acquire: Callable[[], None] = lambda: None,
                    on_release: Callable[[], None] = lambda: None) -> Any:
        """Patch the apply lock so `on_acquire` runs before it is taken and `on_release` after it is released."""
        real = checklist_edits.held_feature

        @contextmanager
        def hooked(*args: Any, exclusive: bool) -> Iterator[Any]:
            if exclusive:
                on_acquire()
            with real(*args, exclusive=exclusive) as held:
                yield held
            if exclusive:
                on_release()

        return patch.object(checklist_edits, "held_feature", hooked)

    def apply_both(self) -> dict[str, Any]:
        return self.apply(proposal("security", edit("G1", "spec.md", "open", "private"),
                                   edit("G2", "plan.md", "never", "always")))

    def assert_both_written(self) -> None:
        self.assertEqual("# Spec\nLogin uses a password.\nExports are private.\n", self.text("spec.md"))
        self.assertEqual("# Plan\nSessions always expire.\n", self.text("plan.md"))


class CanonicalResultTests(InterruptionCase):
    """F1278-812f7be4 after the pre-checks: the result is checked against the canonical paths after acting."""

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
        with self.after_call("write_bytes_atomic", partial(swap_feature_directory, self.root)):
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

    def test_a_filesystem_without_atomic_swap_is_refused_as_such_not_blamed_on_a_writer(self) -> None:
        # Review 6016254217: no competing write, the platform just cannot swap.
        with patch.object(atomic_write, "swap_entries", return_value=False):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual(("expected_failure", "atomic_swap_unavailable"), (result["status"], result["diagnostics"][0]["code"]), result)
        self.assertNotIn("changed", result["data"], result)
        self.assertEqual(([], "spec.md"), (result["data"]["applied"], result["data"]["artifact"]), result)
        self.assertNotIn("redispatch", json.dumps(result["diagnostics"]).lower())
        self.assertEqual((SPEC, PLAN), (self.text("spec.md"), self.text("plan.md")))
        self.assertFalse((self.root / RECORD).exists())

    def test_no_op_domains_before_the_first_real_write_do_not_count_as_written(self) -> None:
        # Review 6017139882: an empty security proposal ran first, then the ux write found no atomic swap.
        before = {name: (self.root / FEATURE / name).read_bytes() for name in ("spec.md", "plan.md")}
        for fault, code in ((partial(patch.object, atomic_write, "swap_entries", return_value=False), "atomic_swap_unavailable"),
                            (partial(patch.object, atomic_write, "ensure_write_target_matches_snapshot_fd",
                                     side_effect=atomic_write.WritePreconditionChanged("changed")), "artifact_changed_during_check")):
            with self.subTest(code=code):
                with fault():
                    result = self.apply(proposal("security"), proposal("ux", edit("G1", "spec.md", "open", "private")))
                self.assertEqual(("expected_failure", code), (result["status"], result["diagnostics"][0]["code"]), result)
                self.assertEqual(before, {name: (self.root / FEATURE / name).read_bytes() for name in before})
                self.assertFalse((self.root / RECORD).exists())

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

    def test_a_competing_edit_displaced_by_the_swap_survives_a_rollback_that_cannot_swap_back(self) -> None:
        # Review 6017500362: the first swap displaced a competing edit, then the swap back returned False.
        real = atomic_write.swap_entries
        rollbacks: dict[str, Callable[[], bool]] = {"unavailable": lambda: False,
                                                    "error": partial(raise_error, OSError(5, "I/O error"))}
        for form, rollback in rollbacks.items():
            with self.subTest(rollback=form):
                self.reset()
                for leftover in (self.root / FEATURE).glob(".spec.md.*"):
                    leftover.unlink()
                calls = [0]

                def compete_then_fail_rollback(directory_fd: int, first: str, second: str) -> bool:
                    calls[0] += 1
                    if calls[0] == 1:
                        (self.root / FEATURE / "spec.md").write_text("# Competitor\n", encoding="utf-8")
                        return real(directory_fd, first, second)
                    return rollback()

                with patch.object(atomic_write, "swap_entries", compete_then_fail_rollback):
                    result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
                self.assertEqual(("expected_failure", "apply_interrupted", ["spec.md"], 2),
                                 (result["status"], result["diagnostics"][0]["code"], result["data"].get("partial"), calls[0]),
                                 result)
                self.assertIn("Exports are private.", self.text("spec.md"))
                kept = sorted((self.root / FEATURE).glob(".spec.md.kept-*"))
                self.assertEqual(["# Competitor\n"], [path.read_text(encoding="utf-8") for path in kept])
                self.assertEqual([], sorted((self.root / FEATURE).glob(".spec.md.tmp-*")))
                self.assertEqual(PLAN, self.text("plan.md"))
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

class RollbackFailureTests(InterruptionCase):
    """F1278-8834bd5e: failed recovery cannot turn a committed exchange into a refusal."""

    def failed_rollback(self, target: Path, change: Callable[[], None], *, raises: bool,
                        rename_fails: bool = False) -> Any:
        real = atomic_write.swap_entries
        calls = [0]

        def exchange_target_then_fail_rollback(directory: int, first: str, second: str) -> bool:
            if second != target.name:
                return real(directory, first, second)
            calls[0] += 1
            if calls[0] == 1:
                change()
                return real(directory, first, second)
            if raises:
                raise OSError("rollback I/O failure")
            return False

        injected = ExitStack()
        injected.enter_context(patch.object(atomic_write, "swap_entries", exchange_target_then_fail_rollback))
        if rename_fails:
            injected.enter_context(patch.object(atomic_write.os, "rename", side_effect=OSError("recovery rename failed")))
        return injected

    def test_failed_rollbacks_report_every_committed_target_and_keep_every_displaced_form(self) -> None:
        for name in ("spec.md", "plan.md", "applied.json"):
            for form in ("content", "replacement", "recreation", "hard-link", "alias", "symlink"):
                for raises in (False, True):
                    with self.subTest(target=name, form=form, raises=raises):
                        self.reset()
                        target = self.root / (RECORD if name == "applied.json" else f"{FEATURE}/{name}")
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.unlink(missing_ok=True)
                        target.write_text("{}" if name == "applied.json" else SPEC if name == "spec.md" else PLAN)
                        for kept in target.parent.glob(f".{name}.*"):
                            kept.unlink()
                        other = self.root / "elsewhere.md"
                        other.write_text("# Competitor\n")

                        def change() -> None:
                            if form == "content":
                                target.write_text("# Competitor\n")
                            elif form == "replacement":
                                os.replace(other, target)
                            elif form == "alias":
                                os.link(target, self.root / "alias.md")
                            else:
                                target.unlink()
                                if form == "recreation":
                                    target.write_text("# Competitor\n")
                                elif form == "hard-link":
                                    os.link(other, target)
                                else:
                                    target.symlink_to(other)

                        with self.failed_rollback(target, change, raises=raises):
                            result = self.apply_both() if name != "applied.json" else self.apply()
                        self.assertEqual(("expected_failure", "apply_interrupted"),
                                         (result["status"], result["diagnostics"][0]["code"]), result)
                        self.assertNotIn("nothing was applied", result["diagnostics"][0]["message"])
                        if name == "applied.json":
                            self.assertTrue(result["data"]["record_written"], result)
                            self.assertEqual(DOMAINS, result["data"]["applied"])
                            self.assertEqual((SPEC, PLAN), (self.text("spec.md"), self.text("plan.md")))
                        else:
                            self.assertEqual(["spec.md"] if name == "spec.md" else ["spec.md", "plan.md"],
                                             result["data"]["partial"], result)
                            self.assertIn("private" if name == "spec.md" else "always", self.text(name))
                        kept = list(target.parent.glob(f".{name}.kept-*"))
                        self.assertEqual(1, len(kept))
                        self.assertEqual(form == "symlink", kept[0].is_symlink())
                        expected = ("{}" if name == "applied.json" else SPEC if name == "spec.md" else PLAN) if form == "alias" else "# Competitor\n"
                        self.assertEqual(expected, kept[0].read_text())
                        if form == "alias":
                            self.assertTrue(kept[0].samefile(self.root / "alias.md"))
                        if form in ("hard-link", "symlink"):
                            self.assertEqual("# Competitor\n", other.read_text())

    def test_failed_recovery_rename_keeps_the_displaced_temporary_entry(self) -> None:
        for name in ("spec.md", "plan.md", "applied.json"):
            for raises in (False, True):
                with self.subTest(target=name, raises=raises):
                    self.reset()
                    target = self.root / (RECORD if name == "applied.json" else f"{FEATURE}/{name}")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if name == "applied.json":
                        target.write_text("{}")
                    for temporary in target.parent.glob(f".{name}.*"):
                        temporary.unlink()
                    with self.failed_rollback(target, partial(target.write_text, "# Competitor\n"),
                                              raises=raises, rename_fails=True):
                        result = self.apply_both() if name != "applied.json" else self.apply()
                    self.assertEqual("apply_interrupted", result["diagnostics"][0]["code"], result)
                    temporary = list(target.parent.glob(f".{name}.tmp-*"))
                    self.assertEqual(["# Competitor\n"], [path.read_text() for path in temporary])
                    self.assertIn(temporary[0].name, result["diagnostics"][0]["message"])
                    if name == "applied.json":
                        self.assertTrue(result["data"]["record_written"], result)
                    else:
                        self.assertIn(name, result["data"]["partial"], result)
                        self.assertIn("private" if name == "spec.md" else "always", self.text(name))

    def test_failed_rollbacks_in_later_domains_report_the_current_write(self) -> None:
        for raises in (False, True):
            with self.subTest(raises=raises):
                self.reset()
                target = self.root / FEATURE / "plan.md"
                with self.failed_rollback(target, partial(target.write_text, "# Competitor\n"), raises=raises):
                    result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")),
                                        proposal("ux", edit("G2", "plan.md", "never", "always")))
                self.assertEqual((["security"], "ux", ["plan.md"]),
                                 (result["data"]["applied"], result["data"]["failed"], result["data"]["partial"]), result)
                self.assert_both_written()

    def test_recovery_name_allocation_cannot_delete_the_displaced_entry(self) -> None:
        for name in ("spec.md", "plan.md", "applied.json"):
            with self.subTest(target=name):
                self.reset()
                target = self.root / (RECORD if name == "applied.json" else f"{FEATURE}/{name}")
                target.parent.mkdir(parents=True, exist_ok=True)
                if name == "applied.json":
                    target.write_text("{}")
                for kept in target.parent.glob(f".{name}.*"):
                    kept.unlink()
                with ExitStack() as injected:
                    def compete() -> None:
                        target.write_text("# Competitor\n")
                        injected.enter_context(patch.object(atomic_write.uuid, "uuid4", side_effect=OSError("allocation failed")))

                    injected.enter_context(self.failed_rollback(target, compete, raises=False))
                    result = self.apply_both() if name != "applied.json" else self.apply()
                kept = list(target.parent.glob(f".{name}.kept-*"))
                self.assertEqual(["# Competitor\n"], [path.read_text() for path in kept])
                self.assertEqual("apply_interrupted", result["diagnostics"][0]["code"], result)
                if name == "applied.json":
                    self.assertTrue(result["data"]["record_written"], result)
                else:
                    self.assertIn(name, result["data"]["partial"], result)


class CommittedStateTests(InterruptionCase):
    """F1278-d7ff996f and F1278-afb94c5e: a failure after the first write reports what is on disk."""

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
        self.assertIn("a passkey", self.text("spec.md"))
        self.assertEqual(PLAN, self.text("plan.md"))

    def test_a_first_artifact_failure_reports_no_current_domain_mutation(self) -> None:
        with self.failing_write(1):
            result = self.apply_both()
        self.assertEqual(("expected_failure", [], "security", [], False),
                         (result["status"], result["data"].get("applied"), result["data"].get("failed"),
                          result["data"].get("partial"), result["data"].get("record_written")), result)
        self.assertEqual((SPEC, PLAN), (self.text("spec.md"), self.text("plan.md")))
        self.assertFalse((self.root / RECORD).exists())

    def test_a_one_artifact_domain_cannot_split_its_edits(self) -> None:
        for name, find, replacement in (("spec.md", "open", "private"), ("plan.md", "never", "always")):
            with self.subTest(artifact=name):
                with self.failing_write(1):
                    result = self.apply(proposal("security", edit("G1", name, find, replacement)))
                self.assertEqual(([], []), (result["data"].get("applied"), result["data"].get("partial")), result)
                self.assertEqual((SPEC, PLAN), (self.text("spec.md"), self.text("plan.md")))
                with self.failing_write(2):  # There is no second artifact write in this domain.
                    result = self.apply(proposal("security", edit("G1", name, find, replacement)))
                self.assertEqual("ok", result["status"], result)
                self.assertIn(replacement, self.text(name))
                (self.root / FEATURE / name).write_text(SPEC if name == "spec.md" else PLAN, encoding="utf-8")

    def test_a_lock_failure_before_any_artifact_write_is_a_true_refusal(self) -> None:
        with self.around_lock(on_acquire=partial(raise_error, OSError("lock acquisition failed"))):
            result = self.apply_both()
        self.assertEqual("input_error", result["status"], result)
        self.assertEqual((SPEC, PLAN), (self.text("spec.md"), self.text("plan.md")))
        self.assertFalse((self.root / RECORD).exists())

    def test_a_refusal_raised_after_the_writes_reports_them(self) -> None:
        # A ValueError, not an OSError, after the artifacts reached disk.
        with patch.object(checklist_edits, "write_file_atomic", side_effect=ValueError("record directory is not usable")):
            result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private")))
        self.assertEqual(("expected_failure", ["security", "ux", "api"]), (result["status"], result["data"].get("applied")), result)
        self.assertIn("private", self.text("spec.md"))

class RecordStateTests(InterruptionCase):
    """F1278-afb94c5e: the application record's state is reported as observed on disk, never assumed."""

    def test_a_failure_before_record_publication_reports_both_artifacts_and_no_record(self) -> None:
        with patch.object(checklist_edits, "write_file_atomic", side_effect=OSError("record publication failed")):
            result = self.apply_both()
        self.assert_interrupted_after_writes(result, record_written=False)

    def test_a_record_parent_open_failure_reports_both_artifacts_and_no_record(self) -> None:
        real = checklist_edits.write_file_atomic

        def fail_parent_open(path: Path, content: str, **kwargs: Any) -> Any:
            with patch.object(atomic_write, "open_safe_parent_fd", side_effect=OSError("record parent open failed")):
                return real(path, content, **kwargs)

        with patch.object(checklist_edits, "write_file_atomic", fail_parent_open):
            result = self.apply_both()
        self.assertEqual(("expected_failure", "apply_interrupted", ["security", "ux", "api"], False),
                         (result["status"], result["diagnostics"][0]["code"], result["data"].get("applied"),
                          result["data"].get("record_written")), result)
        self.assert_both_written()
        self.assertFalse((self.root / RECORD).exists())

    def test_a_record_parent_sync_failure_keeps_both_artifacts_and_the_record(self) -> None:
        real = os.fsync
        faults: list[int] = []

        def fail_record_parent_sync(fd: int) -> None:
            record = self.root / RECORD
            info = os.fstat(fd)
            if stat.S_ISDIR(info.st_mode) and record.is_file() and info.st_ino == record.parent.stat().st_ino:
                faults.append(fd)
                raise OSError("record parent sync failed")
            real(fd)

        with patch.object(os, "fsync", fail_record_parent_sync):
            result = self.apply_both()
        self.assertEqual(1, len(faults))
        # The shared writer treats a directory sync failure after installation as best-effort.
        self.assertEqual("ok", result["status"], result)
        self.assert_both_written()
        record = json.loads((self.root / RECORD).read_text(encoding="utf-8"))
        self.assertEqual(["security", "ux", "api"], [row["domain"] for row in record["domains"]])

    def test_an_unreadable_published_record_is_unknown_never_not_written(self) -> None:
        for fault in ("parent_open", "record_open", "record_read", "parent_close"):
            with self.subTest(fault=fault):
                record = self.root / RECORD
                record.unlink(missing_ok=True)
                (self.root / FEATURE / "spec.md").write_text(SPEC, encoding="utf-8")
                (self.root / FEATURE / "plan.md").write_text(PLAN, encoding="utf-8")
                real = os.open
                faults: list[str] = []
                snapshot = checklist_edits.snapshot_write_target_fd
                close = os.close

                def fail_after_publication(path: Any, *args: Any, **kwargs: Any) -> int:
                    name = "checklist-edits" if fault == "parent_open" else "applied.json"
                    if fault in ("parent_open", "record_open") and os.fspath(path) == name and record.is_file():
                        faults.append(fault)
                        raise OSError("published record is unreadable")
                    return real(path, *args, **kwargs)

                def fail_record_read(fd: int, name: str) -> dict[str, Any]:
                    if fault == "record_read" and name == "applied.json" and record.is_file():
                        faults.append(fault)
                        raise OSError("published record read failed")
                    return snapshot(fd, name)

                def fail_parent_close(fd: int) -> None:
                    info = os.fstat(fd)
                    should_fail = fault == "parent_close" and record.is_file() and info.st_ino == record.parent.stat().st_ino
                    close(fd)
                    if should_fail:
                        faults.append(fault)
                        raise OSError("record parent close failed")

                with ExitStack() as injected:
                    injected.enter_context(patch.object(os, "open", fail_after_publication))
                    injected.enter_context(patch.object(checklist_edits, "snapshot_write_target_fd", fail_record_read))
                    injected.enter_context(patch.object(os, "close", fail_parent_close))
                    result = self.apply_both()
                self.assertGreater(len(faults), 0)
                self.assert_both_written()
                self.assertTrue(record.is_file())
                self.assertEqual(("expected_failure", "apply_interrupted", ["security", "ux", "api"]),
                                 (result["status"], result["diagnostics"][0]["code"], result["data"].get("applied")), result)
                self.assertIsNone(result["data"]["record_written"], result)
                self.assertIn("state unknown", result["diagnostics"][0]["message"])
                self.assertIn("publication completed", result["diagnostics"][0]["message"])
                self.assertNotIn("not written", result["diagnostics"][0]["message"])

    def test_both_payloads_report_unknown_for_an_unreadable_published_record(self) -> None:
        for host in HOSTS:
            with self.subTest(host=host):
                (self.root / RECORD).unlink(missing_ok=True)
                (self.root / FEATURE / "spec.md").write_text(SPEC, encoding="utf-8")
                (self.root / FEATURE / "plan.md").write_text(PLAN, encoding="utf-8")
                inputs = {"domains": DOMAINS, "baseline": self.baseline(), "proposals": [
                    proposal("security", edit("G1", "spec.md", "open", "private"), edit("G2", "plan.md", "never", "always")),
                    proposal("ux"), proposal("api"),
                ]}
                result = run_dist_command(host, self.root, dist_request("apply", inputs), unreadable_record=True)
                self.assertEqual(("expected_failure", ["security", "ux", "api"]),
                                 (result["status"], result["data"].get("applied")), result)
                self.assertIsNone(result["data"]["record_written"], result)
                self.assertIn("publication completed", result["diagnostics"][0]["message"])
                self.assert_both_written()
                self.assertTrue((self.root / RECORD).is_file())

    def test_a_missing_or_different_published_record_is_reported_as_observed(self) -> None:
        for content in (None, b"not JSON", b"\xff", b'{"other": true}'):
            with self.subTest(content=content):
                (self.root / FEATURE / "spec.md").write_text(SPEC, encoding="utf-8")
                (self.root / FEATURE / "plan.md").write_text(PLAN, encoding="utf-8")
                def change_record(observed: bytes | None = content) -> None:
                    record = self.root / RECORD
                    if observed is None:
                        record.unlink()
                    else:
                        record.write_bytes(observed)
                    raise OSError("record changed at lock release")

                with self.around_lock(on_release=change_record):
                    result = self.apply_both()
                self.assertEqual(("expected_failure", ["security", "ux", "api"], False),
                                 (result["status"], result["data"].get("applied"), result["data"].get("record_written")), result)
                self.assert_both_written()
                self.assertIn("absent or different (publication completed)", result["diagnostics"][0]["message"])

    def test_a_failure_after_the_record_is_published_reports_it_written(self) -> None:
        # Same contract, two faults: the record's own publication step, then the lock release after it.
        faults = {
            "record publication": lambda: self.after_call("write_file_atomic", partial(raise_error, OSError("directory sync failed"))),
            "lock release": lambda: self.around_lock(on_release=partial(raise_error, OSError("lock cleanup failed"))),
        }
        for label, fault in faults.items():
            with self.subTest(fault=label):
                self.reset()
                (self.root / RECORD).unlink(missing_ok=True)
                with fault():
                    result = self.apply_both()
                self.assert_interrupted_after_writes(result, record_written=True)

    def test_a_record_path_held_by_a_directory_is_refused_before_any_write(self) -> None:
        (self.root / RECORD).mkdir(parents=True)
        result = self.apply_both()
        self.assertEqual("input_error", result["status"], result)
        self.assertEqual(SPEC, self.text("spec.md"))
        self.assertEqual(PLAN, self.text("plan.md"))

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
        self.assertEqual(("expected_failure", "application record", None),
                         (result["status"], result["data"].get("failed"), result["data"].get("record_written")), result)


class UntrustedTextTests(ChecklistEditsCase):
    """Existing hidden-character and composed-credential guards."""

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
        (self.root / FEATURE / "spec.md").write_text(f"Token ghp_{first}.\n", encoding="utf-8")
        result = self.apply(proposal("ux", edit("G2", "spec.md", first, first + second)))
        self.assertEqual("ok", result["status"], result)
        self.assertEqual(["security", "api"], result["data"]["order"])
        self.assertEqual("edits would write credential-shaped text", result["data"]["domains"][1]["conflicts"][0]["reason"])
        self.assertNotIn(first + second, self.text("spec.md"))



class PlanningContextTests(ChecklistEditsCase):
    """Composed text and persisted proposal metadata."""

    def test_ordinary_edits_apply_in_the_shipped_spec_template(self) -> None:
        template = (REPO / "dist/codex/speckit-pro/presets/speckit-pro-reviewability/templates/spec-template.md").read_text(encoding="utf-8")
        original = template.replace("[Describe this user journey in plain language]", "Login uses a password.", 1)
        for name in ("spec.md", "plan.md"):
            with self.subTest(artifact=name):
                (self.root / FEATURE / name).write_text(original, encoding="utf-8")
                result = self.apply(proposal("security", edit("G1", name, "a password", "a password and a code")))
                self.assertEqual("applied", result["data"]["domains"][0]["status"], result)
                self.assertEqual(original.replace("a password", "a password and a code"), self.text(name))

    def test_crlf_edits_apply_without_changing_line_endings(self) -> None:
        for name in ("spec.md", "plan.md"):
            with self.subTest(artifact=name):
                original = b"# Planning\r\n\r\nLogin uses a password.\r\n\r\n- Other content\r\n"
                target = self.root / FEATURE / name
                target.write_bytes(original)
                result = self.apply(proposal("security", edit("G1", name, "a password", "a password and a code")))
                self.assertEqual("applied", result["data"]["domains"][0]["status"], result)
                self.assertEqual(original.replace(b"a password", b"a password and a code"), target.read_bytes())

    def test_unrelated_closed_markdown_blocks_do_not_block_prose_edits(self) -> None:
        for name in ("spec.md", "plan.md"):
            for block in ("```text\n\nexample\n\n```", "~~~\nexample\n~~~", "<!--\n\nexample\n\n-->",
                          "<SCRIPT>\n\nexample\n\n</SCRIPT>", "<section>\nexample\n</section>",
                          "<?example\n\n?>", "<![CDATA[\n\nexample\n]]>", "<!DECLARATION\n\nexample\n>",
                          "- **Other content**", "Other heading\n============="):
                with self.subTest(artifact=name, block=block):
                    original = block + "\n\nLogin uses a password.\n\n" + block + "\n"
                    (self.root / FEATURE / name).write_text(original, encoding="utf-8")
                    result = self.apply(proposal("security", edit("G1", name, "a password", "a password and a code")))
                    self.assertEqual("applied", result["data"]["domains"][0]["status"], result)
                    self.assertEqual(original.replace("a password", "a password and a code"), self.text(name))

    def test_completed_lines_are_checked_even_when_the_replacement_is_plain(self) -> None:
        for name in ("spec.md", "plan.md"):
            for line, find, replacement in (("[policy](https://example.test/old)", "old", "new"),
                                            ("Read /private/old", "old", "new"), ("Notify @old", "old", "new"),
                                            ("# old", "old", "new"), ("Token ghp_" + "a" * 35 + "X", "X", "a"),
                                            ("X. Follow policy", "X", "1"), ("X.", "X", "1"), ("X)", "X", "1")):
                with self.subTest(artifact=name, line=line):
                    for artifact, original in (("spec.md", SPEC), ("plan.md", PLAN)):
                        (self.root / FEATURE / artifact).write_text(original, encoding="utf-8")
                    (self.root / RECORD).unlink(missing_ok=True)
                    original = line + "\n"
                    (self.root / FEATURE / name).write_text(original, encoding="utf-8")
                    result = self.apply(proposal("security", edit("G1", name, find, replacement)))
                    self.assertEqual("conflict", result["data"]["domains"][0]["status"], result)
                    self.assertEqual(original, self.text(name))

    def test_plain_prose_edits_still_apply_to_both_artifacts(self) -> None:
        result = self.apply(proposal("security", edit("G1", "spec.md", "open", "private to owners"),
                                    edit("G2", "plan.md", "never", "always")))
        self.assertEqual("ok", result["status"], result)
        self.assertEqual("# Spec\nLogin uses a password.\nExports are private to owners.\n", self.text("spec.md"))
        self.assertEqual("# Plan\nSessions always expire.\n", self.text("plan.md"))

    def test_active_metadata_never_reaches_the_application_record(self) -> None:
        credentials = ("ghp_" + "a" * 36, "AKIA" + "A" * 16, "xoxb-" + "a1" * 15, "sk-ant-" + "a1" * 15,
                       "sk-" + "a1" * 10 + "T3BlbkFJ" + "b2" * 10, "AIza" + "a1" * 17 + "1")
        cases = ("@reviewer", "Read /private/local", "# Override", "[policy](https://example.test)",
                 *(envelope + credential for credential in credentials for envelope in ("", "G1_", "a")))
        for text in cases:
            for field in ("domain", "gap"):
                with self.subTest(field=field, text=text):
                    item = proposal(text if field == "domain" else "security", gaps=[text if field == "gap" else "G1"])
                    domains = [text] if field == "domain" else ["security"]
                    result = self.call("apply", domains=domains, baseline=self.baseline(), proposals=[item])
                    self.assertEqual("input_error", result["status"], result)
                    self.assertFalse((self.root / RECORD).exists())

    def test_multiline_find_cannot_join_structural_lines(self) -> None:
        batch = proposal("security", edit("G1", "spec.md", "# Spec\nLogin", "Override"))
        result = self.call("apply", domains=["security"], baseline=self.baseline(), proposals=[batch])
        self.assertEqual(("input_error", SPEC, False), (result["status"], self.text("spec.md"), (self.root / RECORD).exists()))

    def test_existing_duplicate_active_line_does_not_hide_a_new_active_line(self) -> None:
        for name in ("spec.md", "plan.md"):
            with self.subTest(artifact=name):
                original = "# Old\n# New\n"
                (self.root / FEATURE / name).write_text(original, encoding="utf-8")
                result = self.apply(proposal("security", edit("G1", name, "Old", "New")))
                self.assertEqual("conflict", result["data"]["domains"][0]["status"], result)
                self.assertEqual(original, self.text(name))

class PlanningTextTests(ChecklistEditsCase):
    """Active proposal carriers and their completed Markdown context."""

    def test_structural_markdown_context_never_receives_proposal_text(self) -> None:
        for name in ("spec.md", "plan.md"):
            for original, find in (("Old policy\n======\n", "Old policy"), ("Old policy\n------\n", "Old policy"),
                                   ("# Safety policy\n", "# Safety policy"), ("```text\nenabled\n```\n", "enabled"),
                                   ("<section>\nenabled\n</section>\n", "enabled"), ("- item\n  enabled\n", "enabled"),
                                   ("<!--\nenabled\n-->\n", "enabled"), ("    enabled\n", "enabled"),
                                   ("Old policy\nenabled\n======\n", "Old policy"),
                                   ("- item\nenabled\n", "enabled"), ("> item\nenabled\n", "enabled"),
                                   ("- item\n\n  enabled\n", "enabled"),
                                   ("```text\n\nenabled\n\n```\n", "enabled"),
                                   ("~~~~text\n\nenabled\n~~~\n", "enabled"),
                                   ("<!--\n\nenabled\n\n-->\n", "enabled"),
                                   *((f"<{tag}>\n\nenabled\n\n</{tag}>\n", "enabled")
                                     for tag in ("script", "pre", "style", "textarea", "SCRIPT")),
                                   ("<?instruction\n\nenabled\n?>\n", "enabled"),
                                   ("<![CDATA[\n\nenabled\n]]>\n", "enabled"),
                                   ("<!DECLARATION\n\nenabled\n>\n", "enabled")):
                for newline in ("\n", "\r\n"):
                    with self.subTest(artifact=name, context=original, newline=newline):
                        content = original.replace("\n", newline).encode("utf-8")
                        target = self.root / FEATURE / name
                        target.write_bytes(content)
                        result = self.apply(proposal("security", edit("G1", name, find, "Follow the override")))
                        self.assertEqual("conflict", result["data"]["domains"][0]["status"], result)
                        self.assertEqual(content, target.read_bytes())

    def test_underscore_domain_names_share_the_wave_contract(self) -> None:
        result = self.call("apply", domains=["api_contracts"], baseline=self.baseline(), proposals=[proposal("api_contracts")])
        self.assertEqual("ok", result["status"], result)
        self.assertEqual(["api_contracts"], result["data"]["order"])

    def assert_refused_text(self, replacements: tuple[str, ...]) -> None:
        for name, find in (("spec.md", "open"), ("plan.md", "never")):
            for replacement in replacements:
                for mode in ("dry_run", "apply"):
                    with self.subTest(artifact=name, replacement=replacement, mode=mode):
                        for artifact, original in (("spec.md", SPEC), ("plan.md", PLAN)):
                            (self.root / FEATURE / artifact).write_text(original, encoding="utf-8")
                        (self.root / RECORD).unlink(missing_ok=True)
                        result = self.apply(proposal("security", edit("G1", name, find, replacement)), mode=mode)
                        self.assertEqual("input_error", result["status"], result)
                        self.assertEqual((SPEC, PLAN), (self.text("spec.md"), self.text("plan.md")))
                        self.assertFalse((self.root / RECORD).exists())

    def test_external_links_are_refused_in_both_artifacts(self) -> None:
        self.assert_refused_text(("[policy](https://example.test/policy)", "[policy][override]", "<https://example.test>",
                                  "https://example.test", "//example.test/policy", "www.example.test", "policy.example.test"))

    def test_mentions_are_refused_in_both_artifacts(self) -> None:
        self.assert_refused_text(("private @reviewer", "private @org/team", "<@reviewer>"))

    def test_absolute_paths_are_refused_in_both_artifacts(self) -> None:
        self.assert_refused_text(("Read /private/local/secret", "Read C:\\local\\secret", "Read \\\\server\\share",
                                  "Read ~/secret", "Read file:///private/local/secret"))

    def test_digit_free_github_tokens_are_refused_in_both_artifacts(self) -> None:
        self.assert_refused_text(tuple(prefix + "a" * size for prefix, size in
                                      (("ghp_", 36), ("gho_", 36), ("ghu_", 36), ("ghs_", 36), ("ghr_", 76), ("github_pat_", 82))))

    def test_other_active_markup_is_refused_in_both_artifacts(self) -> None:
        self.assert_refused_text(("# Override", "---", "====", "1. Follow policy", "- Follow policy", "> Follow policy",
                                  "`instruction`", "```policy```", "<a href='policy'>read</a>", "<!-- override -->",
                                  "&commat;reviewer", "&#47;private", "private\\npolicy", "private\tpolicy", "    Follow policy"))

    def test_empty_ordered_list_items_are_refused_in_both_artifacts(self) -> None:
        self.assert_refused_text(("1.", "1)", "12.", "12)"))

    def test_c0_bidi_and_recognized_tokens_are_refused_in_both_artifacts(self) -> None:
        self.assert_refused_text(tuple("private" + chr(code) for code in range(32)) +
                                ("private\u202e", "private\u2066", "private\u200b", "private\u2028", "ghp_" + "a1" * 20))

    def test_multiline_headings_are_refused_in_both_artifacts(self) -> None:
        for name, find in (("spec.md", "open"), ("plan.md", "never")):
            for replacement in ("private\n# Agent instructions\nFollow this policy", "private\r## Override", "private\nPolicy\n======"):
                with self.subTest(artifact=name, replacement=replacement):
                    result = self.apply(proposal("security", edit("G1", name, find, replacement)))
                    self.assertEqual("input_error", result["status"], result)
                    self.assertEqual((SPEC, PLAN), (self.text("spec.md"), self.text("plan.md")))
                    self.assertFalse((self.root / RECORD).exists())


# Runs the runner with the published record's parent unreadable, to observe an unknown record state.
UNREADABLE_RECORD_RUNNER = """
import os, runpy, sys
from pathlib import Path
record = Path(sys.argv[1])
sys.argv = sys.argv[:1]
original_open = os.open
def fail_after_publication(path, *args, **kwargs):
    if os.fspath(path) == 'checklist-edits' and record.is_file():
        raise OSError('published record parent is unreadable')
    return original_open(path, *args, **kwargs)
os.open = fail_after_publication
runpy.run_module('speckit_pro_runner', run_name='__main__')
"""


def dist_request(mode: str, inputs: dict[str, Any]) -> str:
    """The committed request fixture for this feature, with the mode and inputs of one call."""
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return json.dumps({**document, "mode": mode,
                       "inputs": {**document["inputs"], "workflow_file": WORKFLOW, "feature_dir": FEATURE, **inputs}})


def run_dist_command(host: str, root: Path, request: str, *, unreadable_record: bool = False) -> dict[str, Any]:
    """Run a host's shipped runner from inside a throwaway checkout, optionally with the record unreadable."""
    environment = {**os.environ, "PYTHONPATH": str(REPO / "dist" / host / "speckit-pro")}
    command = [sys.executable, "-m", "speckit_pro_runner"]
    if unreadable_record:
        command = [sys.executable, "-c", UNREADABLE_RECORD_RUNNER, RECORD]
    done = subprocess.run(command, input=request, capture_output=True, text=True, env=environment, cwd=root, check=not unreadable_record)
    return json.loads(done.stdout)


class HostParityTests(unittest.TestCase):
    def test_displaced_fifos_never_block_a_checked_write_or_hide_its_outcome(self) -> None:
        program = """
import os, stat, sys
from pathlib import Path
from speckit_pro_runner import atomic_write
root, name, outcome = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
target = root / name
target.write_bytes(b'original')
parent = os.open(root, os.O_RDONLY)
expected = atomic_write.snapshot_write_target_fd(parent, name)
os.close(parent)
real, calls = atomic_write.swap_entries, 0
def exchange_with_fifo(directory, first, second):
    global calls
    calls += 1
    if calls == 1:
        target.unlink()
        os.mkfifo(target)
        return real(directory, first, second)
    if outcome == 'success':
        return real(directory, first, second)
    if outcome == 'error':
        raise OSError('rollback failed')
    return False
atomic_write.swap_entries = exchange_with_fifo
try:
    atomic_write.write_bytes_atomic(target, b'proposal', trust_root=root, expected_snapshot=expected)
except OSError as error:
    assert calls == 2, 'fault must reach the displaced-entry read and rollback'
    if outcome == 'success':
        assert isinstance(error, atomic_write.WritePreconditionChanged)
        assert stat.S_ISFIFO(target.stat().st_mode)
    else:
        assert isinstance(error, atomic_write.AtomicWriteInterrupted)
        assert target.read_bytes() == b'proposal'
        kept = list(root.glob('.' + name + '.kept-*'))
        assert len(kept) == 1 and stat.S_ISFIFO(kept[0].stat().st_mode)
else:
    raise AssertionError('FIFO substitution was accepted')
"""
        for host in ("source", *HOSTS):
            payload = REPO / "speckit-pro" if host == "source" else REPO / "dist" / host / "speckit-pro"
            for name in ("spec.md", "plan.md", "applied.json"):
                for outcome in ("success", "unavailable", "error"):
                    with self.subTest(host=host, target=name, rollback=outcome), tempfile.TemporaryDirectory() as temporary:
                        try:
                            done = subprocess.run([sys.executable, "-c", program, temporary, name, outcome],
                                                  env={**os.environ, "PYTHONPATH": str(payload)},
                                                  capture_output=True, text=True, timeout=3, check=False)
                        except subprocess.TimeoutExpired:
                            self.fail("checked writer blocked on the displaced FIFO")
                        self.assertEqual(0, done.returncode, done.stdout + done.stderr)

    def assert_payload_cases(self, cases: tuple[str, ...], expected: int | None = None) -> None:
        program = """
import runpy, sys, unittest
from pathlib import Path
from speckit_pro_runner.helpers import checklist_edits, read_only
assert Path(checklist_edits.__file__).is_relative_to(Path(sys.argv[1]))
scope = runpy.run_path(sys.argv[2])
suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(scope[name]) for name in sys.argv[3:])
sys.exit(scope['run_counted'](suite, label='shipped-matrix'))
"""
        for host in HOSTS:
            with self.subTest(host=host, cases=cases):
                payload = REPO / "dist" / host / "speckit-pro"
                done = subprocess.run([sys.executable, "-c", program, str(payload), __file__, *cases],
                                      env={**os.environ, "PYTHONPATH": str(payload)},
                                      capture_output=True, text=True, check=False)
                self.assertEqual(0, done.returncode, done.stdout + done.stderr)
                if expected is not None:
                    self.assertIn(f"{expected}/{expected} passed", done.stdout)

    def test_both_payloads_fail_g4_closed_on_unstable_or_missing_evidence(self) -> None:
        self.assert_payload_cases(("GateFourTests",))

    def test_both_payloads_cover_the_failed_rollback_matrix(self) -> None:
        self.assert_payload_cases(("RollbackFailureTests",), 47)

    def test_both_payloads_reject_the_untrusted_text_matrix(self) -> None:
        self.assert_payload_cases(("UntrustedTextTests", "PlanningTextTests", "PlanningContextTests"))

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
                baseline = run_dist_command(host, root, dist_request("read_only", {}))["data"]["baseline"]
                applied = run_dist_command(host, root, dist_request("apply", {"domains": DOMAINS, "baseline": baseline, "proposals": proposals}))
                outcomes.append((applied["status"], applied["data"]["order"], applied["data"]["domains"],
                                 (root / FEATURE / "spec.md").read_text(encoding="utf-8")))
        self.assertEqual("ok", outcomes[0][0])
        self.assertEqual(["security", "ux", "api"], outcomes[0][1])
        self.assertEqual(outcomes[0], outcomes[1])


EXECUTOR_GUIDES = ("agents/checklist-executor.md", "codex-agents/checklist-executor.toml")


G4_INPUTS = {"gate": "G4", "feature_dir": FEATURE}
RECEIPT = f"{FEATURE}/.process/checklist-edits/coverage.json"
CLEAN_REPORT = "- [x] CHK001 Is token expiry defined?\n"
GAP_LINE = "- [ ] CHK009 Is account lockout defined? [Gap]\n"


class GateFourTests(ChecklistEditsCase):
    """G4 judges one stable read of spec.md, plan.md and the checklist reports; no caller claim can pass it."""

    def setUp(self) -> None:
        super().setUp()
        self.feature = self.root / FEATURE
        self.outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.outside)
        (self.outside / "security.md").write_text(GAP_LINE, encoding="utf-8")
        self.reset_tree()

    def reset_tree(self) -> None:
        """A marker-free feature with one checklist report, rebuilt from scratch for each variant."""
        for path in (self.feature, self.root / "previous", self.root / "alias.md"):
            if path.is_symlink() or path.is_file():
                path.unlink()
            elif path.exists():
                shutil.rmtree(path)
        (self.feature / "checklists").mkdir(parents=True)
        (self.root / WORKFLOW).parent.mkdir(parents=True)
        (self.root / WORKFLOW).write_text("# Workflow\n", encoding="utf-8")
        (self.feature / "spec.md").write_text(SPEC, encoding="utf-8")
        (self.feature / "plan.md").write_text(PLAN, encoding="utf-8")
        (self.feature / "checklists/security.md").write_text(CLEAN_REPORT, encoding="utf-8")

    def gate(self) -> dict[str, Any]:
        return dict(json.loads(read_only.validate_gate(G4_INPUTS, self.root)["stdout"]))

    def test_g4_requires_a_markdown_report_not_a_placeholder(self) -> None:
        checklists = self.feature / "checklists"
        for name in (".gitkeep", "notes.txt", "security.MD"):
            with self.subTest(entry=name):
                self.reset_tree()
                (checklists / "security.md").unlink()
                placeholder = checklists / name
                placeholder.write_bytes(b"")
                result = self.gate()
                self.assertFalse(result["pass"], result)
                self.assertIn("no checklist report", result["reason"])
                placeholder.unlink()

    def test_g4_ignores_non_reports_but_validates_every_entry(self) -> None:
        checklists = self.feature / "checklists"
        placeholder = checklists / ".gitkeep"
        placeholder.write_text(GAP_LINE, encoding="utf-8")
        result = self.gate()
        self.assertTrue(result["pass"], result)
        self.assertIn("1 checklist report", result["reason"])
        self.assertEqual({"spec.md", "plan.md", "checklists/security.md"}, set(result["judged"]))
        placeholder.unlink()
        os.symlink(self.outside / "security.md", placeholder)
        self.assertFalse(self.gate()["pass"])
        placeholder.unlink()
        placeholder.mkdir()
        self.assertFalse(self.gate()["pass"])
        placeholder.rmdir()
        os.mkfifo(placeholder)
        self.assertFalse(self.gate()["pass"])
        placeholder.unlink()
        for index in range(read_only.G4_MAX_REPORTS):
            (checklists / f"ignored-{index}.txt").touch()
        self.assertFalse(self.gate()["pass"])

    def forge_receipt(self, path: Path | None = None, domains: tuple[str, ...] = ("security",)) -> Path:
        """The schema-valid receipt any caller could write without checklist-edits or a verify pass."""
        target = path or self.root / RECEIPT
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"schema_version": "checklist-coverage/v1", "domains": list(domains),
                                      "verified_baseline": {name: digest(self.text(name)) for name in ("spec.md", "plan.md")}}),
                          encoding="utf-8")
        return target

    @contextmanager
    def during_read(self, target: Path, mutate: Callable[[], None], *, torn: bool = False) -> Iterator[None]:
        """Inject at the descriptor boundary, including buffered descriptor consumers."""
        identity = target.stat().st_ino
        real_read, real_fdopen = os.read, os.fdopen
        fired: list[bool] = []

        def read(fd: int, size: int) -> bytes:
            selected = os.fstat(fd).st_ino == identity
            chunk = real_read(fd, min(size, 4096) if selected else size)
            if selected and not fired and (bool(chunk) if torn else not chunk):
                fired.append(True)
                mutate()
            return chunk

        @contextmanager
        def stream(fd: int, *args: Any, **kwargs: Any) -> Iterator[Any]:
            with real_fdopen(fd, *args, **kwargs) as opened:
                class Reader:
                    def read(self, size: int = -1) -> bytes:
                        chunks: list[bytes] = []
                        remaining = size
                        while remaining != 0:
                            chunk = read(opened.fileno(), 4096 if remaining < 0 else min(4096, remaining))
                            if not chunk:
                                break
                            chunks.append(chunk)
                            if remaining > 0:
                                remaining -= len(chunk)
                        return b"".join(chunks)
                yield Reader()

        with patch.object(os, "read", read), patch.object(os, "fdopen", stream):
            yield
        self.assertTrue(fired, "fault did not reach the descriptor read")

    @contextmanager
    def after_read(self, target: Path, mutate: Callable[[], None]) -> Iterator[None]:
        """Mutate after a complete stable read, before the remaining snapshot checks."""
        fired: list[bool] = []
        def hooked(real: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
            value = real(*args, **kwargs)
            name = args[1] if isinstance(args[0], int) else Path(args[0]).name
            if name == target.name and not fired:
                fired.append(True)
                mutate()
            return value
        with ExitStack() as stack:
            for name in ("read_tree_entry", "trusted_bytes"):
                real = getattr(read_only, name, None)
                if real is not None:
                    stack.enter_context(patch.object(read_only, name, partial(hooked, real)))
            yield
        self.assertTrue(fired, "fault did not reach a complete file read")

    # F1281-fa5e5023: a verification claim is not evidence that any verify pass ran, and no domain list is stored.
    def test_checklist_edits_records_no_domain_list_and_refuses_every_verification_claim(self) -> None:
        statuses = [self.call("apply", domains=["security"], baseline=self.baseline(), proposals=[proposal("security")])["status"]]
        statuses += [self.call("apply", domains=[], proposals=[], baseline=self.baseline(), verified_domains=claimed)["status"]
                     for claimed in (DOMAINS, ["security"], ["security", "ux", "foreign"])]
        self.assertEqual(["ok", "input_error", "input_error", "input_error"], statuses)
        self.assertEqual([], sorted(path.name for path in (self.root / RECEIPT).parent.glob("coverage*")))
        verdict = self.gate()
        self.assertEqual((True, "0 [Gap] markers in spec.md, plan.md and 1 checklist report"), (verdict["pass"], verdict["reason"]))

    # F1281-d099791e and F1281-510e5f28: caller-written evidence never changes the verdict.
    def test_g4_verdict_ignores_caller_written_coverage_receipts(self) -> None:
        receipt = self.root / RECEIPT
        nested = "[" * 1100 + "]" * 1100
        many = tuple(f"d{index}" for index in range(5000))

        def hard_link() -> None:
            self.forge_receipt(self.root / "alias.md")
            os.link(self.root / "alias.md", receipt)

        variants: dict[str, Callable[[], object]] = {
            "regular": self.forge_receipt, "hard link": hard_link,
            "deep nesting": lambda: receipt.write_text(nested, encoding="utf-8"),
            "5000 domains": lambda: self.forge_receipt(domains=many)}
        for tree in ("reports", "no reports"):
            for name, forge in variants.items():
                with self.subTest(tree=tree, receipt=name):
                    self.reset_tree()
                    if tree == "no reports":
                        shutil.rmtree(self.feature / "checklists")
                    expected = self.gate()
                    receipt.parent.mkdir(parents=True, exist_ok=True)
                    forge()
                    self.assertEqual(expected, self.gate())

    def link_checklists_out_of_root(self) -> None:
        """Move the real checklists/ aside and put a link to a directory of [Gap] reports in its place."""
        os.rename(self.feature / "checklists", self.feature / "checklists-old")
        os.symlink(self.outside, self.feature / "checklists", target_is_directory=True)

    def test_g4_fails_closed_without_contained_checklist_reports(self) -> None:
        checklists = self.feature / "checklists"
        variants: dict[str, Callable[[], object]] = {
            "deleted": lambda: shutil.rmtree(checklists),
            "emptied": lambda: (checklists / "security.md").unlink(),
            "renamed": lambda: checklists.rename(self.feature / "checklists-old"),
            "linked out of root": self.link_checklists_out_of_root,
            "linked report": lambda: os.symlink(self.outside / "security.md", checklists / "linked.md")}
        for name, mutate in variants.items():
            with self.subTest(variant=name):
                self.reset_tree()
                mutate()
                self.forge_receipt()
                self.assertFalse(self.gate()["pass"], name)

    def test_g4_fails_closed_on_any_checklist_entry_it_cannot_read_or_classify(self) -> None:
        # checklists/ is flat: a nested directory, readable or not, fails G4 instead of hiding a [Gap] report.
        checklists = self.feature / "checklists"
        locked: list[Path] = []
        real_open = os.open
        denied: list[str] = []

        def open_readable(path: Any, *args: Any, **kwargs: Any) -> int:
            # Containers may run as root, which bypasses chmod(0). Inject the
            # actual failed-open condition at the OS boundary on every platform.
            if Path(path).name in {item.name for item in locked}:
                denied.append(Path(path).name)
                raise PermissionError("G4 fixture denies read access")
            return real_open(path, *args, **kwargs)

        def nested(mode: int) -> None:
            (checklists / "hidden").mkdir()
            (checklists / "hidden/gap.md").write_text(GAP_LINE, encoding="utf-8")
            os.chmod(checklists / "hidden", mode)
            locked.append(checklists / "hidden")

        def lock(path: Path) -> None:
            os.chmod(path, 0)
            locked.append(path)

        variants: dict[str, Callable[[], None]] = {
            "readable nested directory": lambda: nested(0o755),
            "unreadable nested directory": lambda: nested(0),
            "unreadable report": lambda: lock(checklists / "security.md"),
            "unreadable checklists directory": lambda: lock(checklists),
            "fifo": lambda: os.mkfifo(checklists / "pipe.md")}
        for name, mutate in variants.items():
            with self.subTest(variant=name):
                self.reset_tree()
                mutate()
                try:
                    denied.clear()
                    with patch.object(os, "open", open_readable):
                        verdict = self.gate()
                    if name in ("unreadable report", "unreadable checklists directory"):
                        self.assertEqual([locked[-1].name], denied, "must reach the failed-open boundary")
                finally:
                    while locked:
                        os.chmod(locked.pop(), 0o755)
                self.assertFalse(verdict["pass"], (name, verdict))

    def test_g4_fails_closed_on_missing_or_linked_shared_artifacts(self) -> None:
        for name in ("spec.md", "plan.md"):
            for linked in (False, True):
                with self.subTest(artifact=name, linked=linked):
                    self.reset_tree()
                    self.forge_receipt()
                    (self.feature / name).unlink()
                    if linked:
                        (self.feature / name).symlink_to(self.outside / "security.md")
                    self.assertFalse(self.gate()["pass"])

    def swap_entry(self, target: Path, variant: str) -> None:
        """Every recorded replacement shape, with an explicit gap in replacement content."""
        if variant == "hard link":
            os.link(target, self.root / "alias.md")
            (self.root / "alias.md").write_text(GAP_LINE, encoding="utf-8")
            return
        saved = self.root / "previous"
        target.rename(saved)
        if variant == "regular":
            if saved.is_dir():
                shutil.copytree(saved, target)
                (target / "gap.md").write_text(GAP_LINE, encoding="utf-8")
            else:
                target.write_text(GAP_LINE, encoding="utf-8")
        elif variant == "file":
            target.write_text(GAP_LINE, encoding="utf-8")
        elif variant == "in-root link":
            target.symlink_to(saved, target_is_directory=saved.is_dir())
        elif variant == "out-of-root link":
            target.symlink_to(self.outside if saved.is_dir() else self.outside / "security.md")
        elif variant == "fifo":
            os.mkfifo(target)

    def test_g4_refuses_every_post_read_namespace_mutation(self) -> None:
        for inject in (self.during_read, self.after_read):
            for relative in ("spec.md", "plan.md", "checklists/security.md", "checklists", "."):
                variants = ("deleted", "regular", "in-root link", "out-of-root link")
                variants += ("file",) if relative == "checklists" else ()
                variants += ("fifo", "hard link") if relative.endswith(".md") else ()
                for variant in variants:
                    with self.subTest(target=relative, variant=variant):
                        self.reset_tree()
                        target = self.feature / relative
                        trigger = target if relative.endswith(".md") else self.feature / "checklists/security.md"
                        with inject(trigger, partial(self.swap_entry, target, variant)):
                            verdict = self.gate()
                        self.assertFalse(verdict["pass"], verdict)
            for nested in (False, True):
                with self.subTest(added_report_nested=nested):
                    self.reset_tree()
                    report = self.feature / "checklists/security.md"
                    def add_report() -> None:
                        parent = report.parent / "nested" if nested else report.parent
                        parent.mkdir(exist_ok=True)
                        (parent / "added.md").write_text(GAP_LINE, encoding="utf-8")
                    with inject(report, add_report):
                        self.assertFalse(self.gate()["pass"])

    def test_g4_refuses_torn_reads_and_transient_hard_links(self) -> None:
        before = b"a" * 4096 + b"[Gap]" + b"b" * 4091
        after = b"[Gap]" + b"a" * 4091 + b"b" * 4096
        for relative in ("spec.md", "plan.md", "checklists/security.md"):
            for alias in (False, True):
                with self.subTest(target=relative, hard_link=alias):
                    self.reset_tree()
                    target = self.feature / relative
                    target.write_bytes(before)
                    def rewrite() -> None:
                        writer = self.root / "alias.md" if alias else target
                        if alias:
                            os.link(target, writer)
                        writer.write_bytes(after)
                        if alias:
                            writer.unlink()
                    with self.during_read(target, rewrite, torn=True):
                        verdict = self.gate()
                    self.assertFalse(verdict["pass"], verdict)
                    self.assertNotIn("judged", verdict, "a torn buffer must not be judged")

    def test_g4_rejects_preexisting_hard_links_and_reports_exact_clean_digests(self) -> None:
        expected = {"spec.md": digest(SPEC), "plan.md": digest(PLAN), "checklists/security.md": digest(CLEAN_REPORT)}
        self.assertEqual(expected, self.gate()["judged"])
        for relative in expected:
            with self.subTest(target=relative):
                self.reset_tree()
                os.link(self.feature / relative, self.root / "alias.md")
                self.assertFalse(self.gate()["pass"])

    def test_g4_rejects_unsafe_report_names_without_echoing_them(self) -> None:
        for name in ("[click](evil).md", "@everyone.md", "bidi\u202e.md", "line\nfeed.md", "control\x7f.md", "<tag>.md"):
            with self.subTest(name=ascii(name)):
                self.reset_tree()
                (self.feature / "checklists" / name).write_text(CLEAN_REPORT, encoding="utf-8")
                verdict = self.gate()
                self.assertFalse(verdict["pass"], verdict)
                self.assertNotIn(name, json.dumps(verdict, ensure_ascii=False))

    # F1281-2350a979: fixed bounds on report count and total bytes fail closed; the flat layout bounds depth.
    def test_g4_fails_closed_beyond_its_report_count_or_byte_limits(self) -> None:
        checklists = self.feature / "checklists"

        def reports(count: int, content: bytes) -> None:
            for index in range(count):
                (checklists / f"extra-{index}.md").write_bytes(content)

        variants: dict[str, tuple[Callable[[], None], bool]] = {
            "64 reports": (lambda: reports(63, CLEAN_REPORT.encode()), True),
            "65 reports": (lambda: reports(64, CLEAN_REPORT.encode()), False),
            "one report over the byte limit": (lambda: reports(1, b"x" * 8 * 1024 * 1024), False),
            "reports over the byte limit together": (lambda: reports(3, b"x" * 3 * 1024 * 1024), False)}
        for name, (mutate, passes) in variants.items():
            with self.subTest(variant=name):
                self.reset_tree()
                mutate()
                self.assertEqual(passes, self.gate()["pass"], name)


def checklist_passages() -> list[str]:
    """Each host's checklist flow rendered from the shared source."""
    return [" ".join(guide_view(guide).split(anchor, 1)[1][:8000].split())
            for guide, anchor in zip(PHASE_EXECUTION_GUIDES,
                                     ("### Phase 4: Checklist", "Checklist only:"), strict=True)]


class GuidanceTests(unittest.TestCase):
    """The prose points at the helper and never tells an executor to write the artifacts."""

    def test_the_checklist_executor_proposes_edits_and_never_writes_spec_or_plan_on_either_host(self) -> None:
        for relative in EXECUTOR_GUIDES:
            text = guide_text(relative)
            self.assertEqual([], [(relative, phrase) for phrase in ("Proposed Edits", "Do not edit spec.md or plan.md") if phrase not in text])
            self.assertEqual([], [(relative, phrase) for phrase in RETIRED if phrase in text])

    def test_every_verify_gap_reaches_consensus_and_the_final_checkpoint_always_runs_on_both_hosts(self) -> None:
        for passage in checklist_passages():
            queue_at = passage.index("initial run items plus every verify-pass 'Unresolved for consensus' item")
            self.assertLess(queue_at, passage.index("phase brief", queue_at))
            for phrase in ("verify_items", "Always request the final phase brief", "verify_baseline",
                           "before marking any domain completed", "final verify-pass unresolved items return to consensus"):
                self.assertIn(phrase, passage)
            self.assertEqual([], [phrase for phrase in ("send no third request", "verified_domains") if phrase in passage])

    def test_the_phase_four_flow_applies_proposals_through_the_helper_on_both_hosts(self) -> None:
        # Each host's own checklist passage: Claude's Phase 4 section, Codex's checklist-only loop step.
        for guide, anchor in zip(PHASE_EXECUTION_GUIDES, ("### Phase 4: Checklist", "Checklist only:"), strict=True):
            passage = guide_view(guide).split(anchor, 1)[1][:5000]
            claude = "Phase" in anchor
            apply_at, verify_at, consensus_at, rerun_at = (
                passage.find(text) for text in ("mode apply" if claude else "in apply mode", "Mode: verify",
                                                "Request the phase brief again with `items`" if claude else "Request the phase brief with items",
                                                "verify_baseline"))
            self.assertTrue(0 <= apply_at < verify_at < consensus_at < rerun_at, (guide, apply_at, verify_at, consensus_at, rerun_at))
            self.assertIn("every original domain", passage)
            for phrase in ("runner helper `checklist-edits`", "in domain order", "dry_run"):
                self.assertIn(phrase, passage, guide)
            self.assertNotIn("Domain 2 may depend on Domain 1's gap fixes", passage)
            self.assertIn("restore both files before any retry", passage)
            self.assertIn("its state is unknown", passage)
            if "Phase" in anchor:
                verify_prompt = passage.split('prompt: "Mode: verify', 1)[1].split('")', 1)[0]
                self.assertIn("Reference slices: <brief.slices, verbatim>", verify_prompt)


if __name__ == "__main__":
    sys.exit(
        run_counted(
            unittest.TestSuite(
                unittest.defaultTestLoader.loadTestsFromTestCase(case)
                for case in (ProposalTests, ConflictTests, RefusalTests, CompetingWriterTests, CanonicalResultTests, RollbackFailureTests, CommittedStateTests,
                             RecordStateTests,
                             UntrustedTextTests, PlanningTextTests, PlanningContextTests, HostParityTests, GateFourTests, GuidanceTests)
            ),
            label="test-checklist-edits",
        )
    )
