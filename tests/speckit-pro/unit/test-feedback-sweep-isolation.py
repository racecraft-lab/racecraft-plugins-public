#!/usr/bin/env python3
"""Adversarial contracts for the feedback-sweep isolation boundary."""

from __future__ import annotations

import hashlib
import json
import importlib.util
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = Path(__file__).resolve().parent.parent / "lib"
for import_root in (PLUGIN_ROOT, LIB_DIR):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from test_result import run_counted  # noqa: E402
from speckit_pro_runner import sweep_isolation  # noqa: E402
from speckit_pro_runner import sweep_broker  # noqa: E402
from speckit_pro_runner import sweep_launcher  # noqa: E402
from speckit_pro_runner.helpers import read_only, registry  # noqa: E402


def git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        env={
            "PATH": os.environ.get("PATH", ""),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
        },
    )
    if completed.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {completed.stderr}")
    return completed.stdout.strip()


def issuer_secret_cases() -> tuple[str, ...]:
    return (
        "ghp" + "_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
        "github" + "_pat_" + "1A" * 41 + "bc",
        "xox" + "b-" + "1234567890123-1234567890123-AbCdEfGh1jKlMnOpQrStUvWx",
        "sk-" + "ant-" + "api03-" + "aB3" * 20 + "AA",
        "sk-" + "proj-" + "a1" * 12 + "T3Blbk" + "FJ" + "b2" * 12,
        "AIz" + "a" + "SyB1c2D3e4F5g6H7i8J9k0L1m2N3o4P5q6R",
        "AKI" + "A" + "IOSFODNN7EXAMPLE",
        "postgres://admin:" + "s3cret" + "password1@localhost:5432/app",
    )


class GitFixture:
    def __init__(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="sweep-isolation-")
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Sweep Test")
        git(self.root, "config", "user.email", "sweep.invalid")

    def close(self) -> None:
        self.temp.cleanup()

    def write(self, relative: str, content: str | bytes) -> Path:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
        return target

    def commit(self, message: str = "fixture") -> str:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", message)
        return git(self.root, "rev-parse", "HEAD")


class SnapshotIsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = GitFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_snapshot_uses_tracked_git_blobs_and_never_host_or_worktree_bytes(self) -> None:
        canary = f"CANARY-{secrets.token_hex(24)}"
        self.fixture.write("specs/001-safe/spec.md", "# Safe\ntracked text\n")
        self.fixture.commit()

        outside = Path(self.fixture.temp.name) / "home-secret.txt"
        outside.write_text(canary, encoding="utf-8")
        self.fixture.write(".env", canary)
        os.environ["SPECKIT_SWEEP_TEST_CANARY"] = canary
        (self.fixture.root / "host-link").symlink_to(outside)
        git(self.fixture.root, "add", "host-link")
        git(self.fixture.root, "commit", "-qm", "tracked symlink")
        sibling = Path(self.fixture.temp.name) / "sibling-worktree"
        git(self.fixture.root, "worktree", "add", "-q", "-b", "sibling-test", str(sibling), "HEAD")
        (sibling / "sibling-canary.txt").write_text(canary, encoding="utf-8")

        snapshot = sweep_isolation.GitSnapshot.capture(self.fixture.root)
        public = json.dumps(snapshot.list(), sort_keys=True)
        public += json.dumps(snapshot.search("CANARY-"), sort_keys=True)

        self.assertNotIn(canary, public)
        self.assertEqual(["specs/001-safe/spec.md"], [entry["path"] for entry in snapshot.list()])
        for refused in (".env", "host-link", ".git/config", "../home-secret.txt", str(outside)):
            with self.assertRaises(sweep_isolation.IsolationViolation):
                snapshot.read(refused)

    def test_snapshot_excludes_gitlinks_binary_oversize_sensitive_and_secret_blobs(self) -> None:
        canary = f"TOKEN-{secrets.token_hex(24)}"
        self.fixture.write("safe.txt", "ordinary text\n")
        self.fixture.write("binary.dat", b"prefix\x00suffix")
        self.fixture.write("large.txt", b"x" * (sweep_isolation.MAX_BLOB_BYTES + 1))
        self.fixture.write("config/credentials.json", "{}\n")
        self.fixture.write("leaky.txt", f"API_TOKEN={canary}\n")
        head = self.fixture.commit()
        git(self.fixture.root, "update-index", "--add", "--cacheinfo", f"160000,{head},vendor/module")
        git(self.fixture.root, "commit", "-qm", "gitlink")

        snapshot = sweep_isolation.GitSnapshot.capture(self.fixture.root)
        listed = {entry["path"] for entry in snapshot.list()}

        self.assertEqual({"safe.txt"}, listed)
        self.assertNotIn(canary, json.dumps(snapshot.list(), sort_keys=True))

    def test_credential_scanner_catches_bare_issuer_tokens_without_matching_prefix_prose(self) -> None:
        for index, secret in enumerate(issuer_secret_cases()):
            with self.subTest(case=index):
                self.assertTrue(sweep_isolation.secret_matches(secret))
        for prose in (
            "a ghp_ prefixed classic token",
            "sk-ant- keys are issued per workspace",
            "task-execution and sub-agent routing",
            "https://<user>:<password>@host/db",
        ):
            with self.subTest(prose=prose):
                self.assertFalse(sweep_isolation.secret_matches(prose))

    def test_outbound_redactor_removes_each_issuer_secret_and_preserves_url_context(self) -> None:
        for index, secret in enumerate(issuer_secret_cases()):
            with self.subTest(case=index):
                redacted, count = sweep_isolation.redact_model_text(secret)
                self.assertGreater(count, 0)
                self.assertNotIn(secret, redacted)
        url = issuer_secret_cases()[-1]
        redacted, _count = sweep_isolation.redact_model_text(url)
        self.assertIn("postgres://admin:", redacted)
        self.assertIn("@localhost:5432/app", redacted)

    def test_snapshot_is_exact_head_bound_and_literal_search_is_bounded(self) -> None:
        self.fixture.write("plan.md", "alpha.*literal\nalphaXliteral\n")
        first_head = self.fixture.commit("first")
        snapshot = sweep_isolation.GitSnapshot.capture(self.fixture.root)
        self.fixture.write("plan.md", "changed after capture\n")
        self.fixture.commit("second")

        self.assertEqual(first_head, snapshot.head)
        self.assertEqual("alpha.*literal\nalphaXliteral\n", snapshot.read("plan.md")["text"])
        hits = snapshot.search("alpha.*")
        self.assertEqual(1, len(hits))
        self.assertEqual(1, hits[0]["line"])
        with self.assertRaises(sweep_isolation.IsolationViolation):
            snapshot.search("")


class SessionAndReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = GitFixture()
        self.fixture.write("specs/001-safe/spec.md", "# Scope\nold text\n")
        self.fixture.write("specs/001-safe/plan.md", "# Plan\nold text\n")
        self.fixture.write("specs/001-safe/tasks.md", "# Tasks\nold text\n")
        self.head = self.fixture.commit()
        self.state_root = Path(self.fixture.temp.name) / "private-state"
        self.comment_canary = f"COMMENT-{secrets.token_hex(24)}"
        self.metadata = sweep_isolation.SweepSession.create(
            self.fixture.root,
            state_root=self.state_root,
            comments=[{
                "id": "RC_kwDO123",
                "surface": "review_thread",
                "author": "reviewer",
                "author_association": "MEMBER",
                "body": f"Please update the plan. {self.comment_canary}",
                "thread_resolved": False,
                "truncated": False,
            }],
            now=1_000,
            ttl_seconds=60,
        )
        self.session = sweep_isolation.SweepSession.open(
            self.metadata["session_id"], state_root=self.state_root, now=1_000
        )

    def tearDown(self) -> None:
        self.fixture.close()

    def classifier(self, **overrides: object) -> dict[str, object]:
        record: dict[str, object] = {
            "comment_id": "RC_kwDO123",
            "class": "amended",
            "target": "plan.md",
            "reason": "The plan needs the requested constraint.",
        }
        record.update(overrides)
        return record

    def synthesis(self, **overrides: object) -> dict[str, object]:
        record: dict[str, object] = {
            "comment_id": "RC_kwDO123",
            "outcome": "resolved",
            "agreement": "3/3",
            "basis": None,
            "edit": {"file": "plan.md", "anchor": "old text", "replacement": "new text"},
        }
        record.update(overrides)
        return record

    def test_public_session_metadata_never_contains_reviewer_text(self) -> None:
        encoded = json.dumps(self.metadata, sort_keys=True)
        self.assertNotIn(self.comment_canary, encoded)
        self.assertEqual(
            {"id", "surface", "body_sha256", "author_association"},
            set(self.metadata["comments"][0]),
        )

    def test_classifier_schema_is_exact_and_receipt_is_opaque(self) -> None:
        receipt = self.session.submit_result("classifier", self.classifier())
        self.assertRegex(receipt, r"^sweep-result:v1:[0-9a-f]{64}$")
        self.assertNotIn(self.comment_canary, receipt)
        projection = self.session.accept_receipt(receipt, expected_stage="classifier")
        self.assertEqual(
            {"comment_id": "RC_kwDO123", "class": "amended", "target": "plan.md"},
            projection,
        )
        with self.assertRaises(sweep_isolation.ReceiptViolation):
            self.session.accept_receipt(receipt, expected_stage="classifier")

    def test_malformed_and_extra_fields_are_rejected_without_receipt(self) -> None:
        invalid = (
            self.classifier(extra="smuggle"),
            self.classifier(**{"class": "maybe"}),
            self.classifier(target=None),
            self.classifier(reason="contains | pipe"),
            self.classifier(reason="x" * 513),
        )
        for record in invalid:
            with self.subTest(record=sorted(record)):
                with self.assertRaises(sweep_isolation.SchemaViolation):
                    self.session.submit_result("classifier", record)

    def test_private_capture_rejects_an_unbounded_comment_set(self) -> None:
        comments = [
            {
                "id": f"comment-{index}",
                "surface": "review_thread",
                "author": "reviewer",
                "author_association": "OWNER",
                "body": "bounded",
                "thread_resolved": False,
                "truncated": False,
            }
            for index in range(2)
        ]
        with patch.object(sweep_isolation, "MAX_SESSION_COMMENTS", 1):
            with self.assertRaises(sweep_isolation.SchemaViolation):
                sweep_isolation.SweepSession.create(
                    self.fixture.root,
                    comments=comments,
                    state_root=self.state_root,
                    now=1_000,
                )

    def test_receipts_are_session_bound_head_bound_expiring_and_cross_stage(self) -> None:
        receipt = self.session.submit_result("classifier", self.classifier())
        other = sweep_isolation.SweepSession.create(
            self.fixture.root,
            state_root=self.state_root,
            comments=[],
            now=1_000,
            ttl_seconds=60,
        )
        other_session = sweep_isolation.SweepSession.open(
            other["session_id"], state_root=self.state_root, now=1_000
        )
        with self.assertRaises(sweep_isolation.ReceiptViolation):
            other_session.accept_receipt(receipt, expected_stage="classifier")
        with self.assertRaises(sweep_isolation.ReceiptViolation):
            self.session.accept_receipt(receipt, expected_stage="perspective")

        self.fixture.write("post-capture.txt", "head drift\n")
        self.fixture.commit("head drift")
        with self.assertRaises(sweep_isolation.ReceiptViolation):
            self.session.accept_receipt(receipt, expected_stage="classifier")

        expired = sweep_isolation.SweepSession.open(
            self.metadata["session_id"], state_root=self.state_root, now=1_061
        )
        with self.assertRaises(sweep_isolation.ReceiptViolation):
            expired.accept_receipt(receipt, expected_stage="classifier")

    def test_session_invalidation_removes_private_state_and_blocks_reopen(self) -> None:
        session_path = self.session.session_path
        self.session.invalidate()
        self.assertFalse(session_path.exists())
        with self.assertRaises(sweep_isolation.ReceiptViolation):
            sweep_isolation.SweepSession.open(
                self.metadata["session_id"], state_root=self.state_root, now=1_000
            )

    def test_private_state_reader_rejects_a_symlinked_state_file(self) -> None:
        state_path = self.session.state_path
        target = state_path.with_name("state-copy.json")
        state_path.replace(target)
        state_path.symlink_to(target.name)
        with self.assertRaises(sweep_isolation.ReceiptViolation):
            self.session.head()

    def test_broker_capability_binds_one_comment_stage_and_rejects_raw_selectors(self) -> None:
        capability = self.session.issue_capability("RC_kwDO123", stage="classifier")
        self.assertRegex(capability, r"^sweep-cap:v1:[0-9a-f]{32}:[0-9a-f]{64}$")
        with patch.dict(
            os.environ,
            {
                "SPECKIT_SWEEP_STATE_ROOT": str(self.state_root),
                "SPECKIT_SWEEP_CAPABILITY": capability,
            },
            clear=False,
        ), patch.object(sweep_isolation.time, "time", return_value=1_000):
            comment = sweep_broker.call_tool("review_comment", {})
            self.assertEqual("RC_kwDO123", comment["comment_id"])
            with self.assertRaises(sweep_isolation.IsolationViolation):
                sweep_broker.call_tool(
                    "review_comment",
                    {"comment_id": "another-comment"},
                )
            with self.assertRaises(sweep_isolation.IsolationViolation):
                sweep_broker.call_tool(
                    "submit_result",
                    {
                        "result": self.classifier(comment_id="another-comment"),
                    },
                )

        for tool in sweep_broker.TOOLS:
            properties = set(tool["inputSchema"]["properties"])
            self.assertTrue(
                properties.isdisjoint(
                    {"capability", "session_id", "comment_id", "stage", "perspective"}
                )
            )

    def test_broker_records_and_returns_only_a_closed_error_code(self) -> None:
        capability = self.session.issue_capability("RC_kwDO123", stage="classifier")
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "submit_result",
                "arguments": {
                    "result": self.classifier(comment_id="WRONG_COMMENT")
                },
            },
        }
        with patch.dict(
            os.environ,
            {
                "SPECKIT_SWEEP_CAPABILITY": capability,
                "SPECKIT_SWEEP_STATE_ROOT": str(self.state_root),
            },
            clear=False,
        ), patch.object(sweep_isolation.time, "time", return_value=1_000):
            response = sweep_broker.handle_message(request)

        self.assertEqual(
            {
                "isError": True,
                "content": [{"type": "text", "text": "broker_error:comment_mismatch"}],
                "structuredContent": {"error_code": "comment_mismatch"},
            },
            response["result"],
        )
        self.assertEqual({"comment_mismatch": 1}, self.session.broker_error_counts())
        self.assertNotIn("WRONG_COMMENT", json.dumps(response, sort_keys=True))

        malformed_request = {
            **request,
            "id": 8,
            "params": {"name": "submit_result", "arguments": self.classifier()},
        }
        with patch.dict(
            os.environ,
            {
                "SPECKIT_SWEEP_CAPABILITY": capability,
                "SPECKIT_SWEEP_STATE_ROOT": str(self.state_root),
            },
            clear=False,
        ), patch.object(sweep_isolation.time, "time", return_value=1_000):
            malformed_response = sweep_broker.handle_message(malformed_request)
        self.assertEqual(
            "broker_error:submit_shape",
            malformed_response["result"]["content"][0]["text"],
        )
        self.assertEqual(
            {"comment_mismatch": 1, "submit_shape": 1},
            self.session.broker_error_counts(),
        )

    def test_consensus_capabilities_require_accepted_prior_stages_and_target(self) -> None:
        with self.assertRaises(sweep_isolation.ReceiptViolation):
            self.session.issue_capability(
                "RC_kwDO123", stage="perspective", perspective="codebase"
            )

        classifier_receipt = self.session.submit_result("classifier", self.classifier())
        self.session.accept_receipt(classifier_receipt, expected_stage="classifier")
        self.session.issue_capability(
            "RC_kwDO123", stage="perspective", perspective="codebase"
        )
        with self.assertRaises(sweep_isolation.ReceiptViolation):
            self.session.issue_capability("RC_kwDO123", stage="synthesis")

        for perspective in sweep_isolation.PERSPECTIVES:
            record = {
                "comment_id": "RC_kwDO123",
                "perspective": perspective,
                "finding": f"{perspective} supports the bounded change.",
                "evidence": ["specs/001-safe/plan.md:2"],
                "escape_hatch": False,
            }
            receipt = self.session.submit_result(
                "perspective", record, perspective=perspective
            )
            self.session.accept_receipt(receipt, expected_stage="perspective")

        capability = self.session.issue_capability("RC_kwDO123", stage="synthesis")
        with patch.dict(
            os.environ,
            {
                "SPECKIT_SWEEP_STATE_ROOT": str(self.state_root),
                "SPECKIT_SWEEP_CAPABILITY": capability,
            },
            clear=False,
        ), patch.object(sweep_isolation.time, "time", return_value=1_000):
            with self.assertRaises(sweep_isolation.SchemaViolation):
                sweep_broker.call_tool(
                    "submit_result",
                    {
                        "result": self.synthesis(
                            edit={
                                "file": "spec.md",
                                "anchor": "old text",
                                "replacement": "wrong target",
                            }
                        ),
                    },
                )

    def test_synthesis_cannot_override_an_accepted_escape_hatch(self) -> None:
        classifier_receipt = self.session.submit_result("classifier", self.classifier())
        self.session.accept_receipt(classifier_receipt, expected_stage="classifier")
        for perspective in sweep_isolation.PERSPECTIVES:
            record = {
                "comment_id": "RC_kwDO123",
                "perspective": perspective,
                "finding": f"{perspective} reached a bounded conclusion.",
                "evidence": ["specs/001-safe/plan.md:2"],
                "escape_hatch": perspective == "domain",
            }
            receipt = self.session.submit_result(
                "perspective", record, perspective=perspective
            )
            self.session.accept_receipt(receipt, expected_stage="perspective")

        capability = self.session.issue_capability("RC_kwDO123", stage="synthesis")
        with patch.dict(
            os.environ,
            {
                "SPECKIT_SWEEP_STATE_ROOT": str(self.state_root),
                "SPECKIT_SWEEP_CAPABILITY": capability,
            },
            clear=False,
        ), patch.object(sweep_isolation.time, "time", return_value=1_000):
            with self.assertRaises(sweep_isolation.SchemaViolation):
                sweep_broker.call_tool(
                    "submit_result",
                    {"result": self.synthesis()},
                )
            receipt = sweep_broker.call_tool(
                "submit_result",
                {
                    "result": {
                        "comment_id": "RC_kwDO123",
                        "outcome": "human_review",
                        "agreement": None,
                        "basis": "escape_unresolved",
                        "edit": None,
                    }
                },
            )
        self.assertRegex(receipt, r"^sweep-result:v1:[0-9a-f]{64}$")

    def test_perspective_and_synthesis_schemas_are_exact(self) -> None:
        perspective = {
            "comment_id": "RC_kwDO123",
            "perspective": "codebase",
            "finding": "The repository pattern supports this change.",
            "evidence": ["specs/001-safe/plan.md:2"],
            "escape_hatch": False,
        }
        receipt = self.session.submit_result("perspective", perspective, perspective="codebase")
        self.assertRegex(receipt, r"^sweep-result:v1:[0-9a-f]{64}$")
        with self.assertRaises(sweep_isolation.SchemaViolation):
            self.session.submit_result(
                "perspective", {**perspective, "evidence": ["/etc/passwd:1"]}, perspective="codebase"
            )
        with self.assertRaises(sweep_isolation.SchemaViolation):
            self.session.submit_result(
                "synthesis",
                self.synthesis(edit={"file": "README.md", "anchor": "old", "replacement": "new"}),
            )

    def test_receipt_gated_mutation_revalidates_every_precondition_before_write(self) -> None:
        receipt = self.session.submit_result("synthesis", self.synthesis())
        result = sweep_isolation.apply_synthesis_receipt(
            self.fixture.root,
            "specs/001-safe",
            self.session,
            receipt,
            mode="apply",
        )
        self.assertEqual("applied", result["status"])
        self.assertEqual("specs/001-safe/plan.md", result["path"])
        self.assertNotIn("new text", json.dumps(result, sort_keys=True))
        self.assertEqual("# Plan\nnew text\n", (self.fixture.root / "specs/001-safe/plan.md").read_text())

    def test_mutation_failure_produces_zero_write_for_duplicate_anchor_and_secret_replacement(self) -> None:
        target = self.fixture.root / "specs/001-safe/plan.md"
        target.write_text("old text\nold text\n", encoding="utf-8")
        before = target.read_bytes()
        duplicate = self.session.submit_result("synthesis", self.synthesis())
        with self.assertRaises(sweep_isolation.MutationViolation):
            sweep_isolation.apply_synthesis_receipt(
                self.fixture.root, "specs/001-safe", self.session, duplicate, mode="apply"
            )
        self.assertEqual(before, target.read_bytes())

        target.write_text("# Plan\nold text\n", encoding="utf-8")
        secret = f"API_TOKEN={secrets.token_hex(24)}"
        secret_receipt = self.session.submit_result(
            "synthesis", self.synthesis(edit={"file": "plan.md", "anchor": "old text", "replacement": secret})
        )
        result = sweep_isolation.apply_synthesis_receipt(
            self.fixture.root, "specs/001-safe", self.session, secret_receipt, mode="apply"
        )
        self.assertEqual("applied_redacted", result["status"])
        self.assertNotIn(secret, target.read_text(encoding="utf-8"))
        self.assertNotIn(secret, json.dumps(result, sort_keys=True))

    def test_mutation_rejects_stale_blob_wrong_path_and_oversized_replacement_without_write(self) -> None:
        target = self.fixture.root / "specs/001-safe/plan.md"
        cases = (
            self.synthesis(edit={"file": "README.md", "anchor": "old text", "replacement": "new"}),
            self.synthesis(
                edit={
                    "file": "plan.md",
                    "anchor": "old text",
                    "replacement": "x" * (sweep_isolation.MAX_REPLACEMENT_BYTES + 1),
                }
            ),
        )
        for record in cases:
            before = target.read_bytes()
            with self.subTest(edit=record["edit"]):
                with self.assertRaises((sweep_isolation.SchemaViolation, sweep_isolation.MutationViolation)):
                    receipt = self.session.submit_result("synthesis", record)
                    sweep_isolation.apply_synthesis_receipt(
                        self.fixture.root, "specs/001-safe", self.session, receipt, mode="apply"
                    )
                self.assertEqual(before, target.read_bytes())

    def test_mutation_preconditions_do_not_consume_a_valid_receipt(self) -> None:
        receipt = self.session.submit_result("synthesis", self.synthesis())
        other = GitFixture()
        try:
            other.write("specs/001-safe/plan.md", "# Plan\nold text\n")
            other.commit()
            with self.assertRaises(sweep_isolation.MutationViolation):
                sweep_isolation.apply_synthesis_receipt(
                    other.root, "specs/001-safe", self.session, receipt, mode="apply"
                )
            result = sweep_isolation.apply_synthesis_receipt(
                self.fixture.root, "specs/001-safe", self.session, receipt, mode="apply"
            )
            self.assertEqual("applied", result["status"])
        finally:
            other.close()

    def test_claude_launcher_accepts_only_a_broker_issued_receipt(self) -> None:
        receipt = self.session.submit_result("classifier", self.classifier())
        envelope = {
            "is_error": False,
            "result": f"wrapped prose {receipt}",
            "structured_output": {"receipt": receipt},
            "permission_denials": [],
            "subagent_stats": {"spawned": 1, "completed": 1, "failed": 0},
        }
        completed = SimpleNamespace(
            returncode=0,
            stdout=json.dumps(envelope),
            stderr="",
        )
        with patch.object(sweep_launcher, "verify_claude_boundary"), patch.object(
            sweep_launcher, "verify_claude_attestation"
        ), patch.object(sweep_launcher, "claude_command", return_value=["claude"]), patch.object(
            sweep_launcher.SweepSession, "open", return_value=self.session
        ), patch.object(
            sweep_launcher, "_run_claude_process", return_value=completed
        ) as claude_process:
            result = sweep_launcher.run_claude_sweep(
                plugin_root=PLUGIN_ROOT,
                repo_root=self.fixture.root,
                session_id=self.metadata["session_id"],
                comment_id="RC_kwDO123",
                stage="classifier",
                state_root=self.state_root,
            )
        self.assertEqual("amended", result["class"])
        self.assertEqual(receipt, result["receipt"])
        environment = claude_process.call_args.kwargs["environment"]
        self.assertRegex(
            environment["SPECKIT_SWEEP_CAPABILITY"],
            r"^sweep-cap:v1:[0-9a-f]{32}:[0-9a-f]{64}$",
        )

    def test_missing_feature_directory_is_a_closed_mutation_refusal(self) -> None:
        receipt = self.session.submit_result("synthesis", self.synthesis())
        with self.assertRaises(sweep_isolation.MutationViolation):
            sweep_isolation.apply_synthesis_receipt(
                self.fixture.root, "specs/missing", self.session, receipt, mode="apply"
            )


class SurfaceConfinementTests(unittest.TestCase):
    def test_codex_version_executes_the_attested_binary_not_a_path_alias(self) -> None:
        alias = "/mutable-path/codex"
        resolved = Path("/trusted-runtime/codex")
        completed = SimpleNamespace(
            returncode=0,
            stdout="codex-cli 0.149.0\n",
            stderr="",
        )
        with (
            patch.object(
                sweep_launcher.shutil,
                "which",
                side_effect=(alias, str(resolved)),
            ) as which,
            patch.object(sweep_launcher, "_trusted_executable", return_value=resolved),
            patch.object(sweep_launcher.subprocess, "run", return_value=completed) as run,
        ):
            self.assertEqual((0, 149, 0), sweep_launcher._codex_version())

        arguments, = run.call_args.args
        self.assertEqual([str(resolved), "--version"], arguments)
        self.assertNotIn("executable", run.call_args.kwargs)
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertEqual(
            (("codex",), {"path": str(resolved.parent)}),
            (which.call_args_list[1].args, which.call_args_list[1].kwargs),
        )

    def test_runner_cannot_return_a_model_capability_to_the_parent(self) -> None:
        result = read_only.sweep_isolation_session(
            {
                "named_surface": "capability",
                "session_id": "a" * 32,
                "comment_id": "RC_kwDO123",
                "stage": "classifier",
            },
            REPO_ROOT,
        )
        self.assertEqual(2, result["exit_code"])
        self.assertNotIn("sweep-cap:v1:", result["stdout"])

    def test_broker_exposes_only_the_six_bounded_tools(self) -> None:
        self.assertEqual(
            {
                "snapshot_list",
                "snapshot_read",
                "snapshot_search",
                "review_comment",
                "consensus_inputs",
                "submit_result",
            },
            set(sweep_isolation.BROKER_TOOL_NAMES),
        )

    def test_submit_result_advertises_three_exact_stage_schemas(self) -> None:
        submit = next(tool for tool in sweep_broker.TOOLS if tool["name"] == "submit_result")
        result_schema = submit["inputSchema"]["properties"]["result"]
        variants = result_schema["oneOf"]
        self.assertEqual(3, len(variants))
        self.assertEqual(
            {
                frozenset({"comment_id", "class", "target", "reason"}),
                frozenset({"comment_id", "perspective", "finding", "evidence", "escape_hatch"}),
                frozenset({"comment_id", "outcome", "agreement", "basis", "edit"}),
            },
            {frozenset(variant["required"]) for variant in variants},
        )
        self.assertTrue(all(variant["additionalProperties"] is False for variant in variants))

    def test_broker_refuses_unsupported_python_before_reading_stdio(self) -> None:
        with patch.object(sweep_broker.sys, "version_info", (3, 10)):
            self.assertEqual(2, sweep_broker.main())

    def test_codex_launcher_is_ephemeral_user_config_free_and_disables_privileged_surfaces(self) -> None:
        runtime_root = REPO_ROOT.parent / "isolated-sweep-runtime"
        codex_runtime = REPO_ROOT.parent / "test-runtimes" / "codex"
        with patch.object(sweep_launcher, "codex_executable", return_value=codex_runtime):
            command = sweep_launcher.codex_command(
                plugin_root=PLUGIN_ROOT,
                repo_root=REPO_ROOT,
                runtime_root=runtime_root,
                capability=f"sweep-cap:v1:{'a' * 32}:{'b' * 64}",
                stage="classifier",
            )
        joined = " ".join(command)
        self.assertEqual(codex_runtime, Path(command[0]))
        filesystem = next(
            item
            for item in command
            if item.startswith("permissions.sweep-broker-only.filesystem=")
        )
        for runtime in (
            Path(command[0]).parent.parent,
            Path(sys.base_prefix).resolve(),
            runtime_root,
        ):
            self.assertIn(json.dumps(str(runtime)), filesystem)
        self.assertNotIn(json.dumps(str(REPO_ROOT)), filesystem)
        self.assertEqual(str(runtime_root), command[command.index("-C") + 1])
        for required in (
            "exec",
            "--ignore-user-config",
            "--ephemeral",
            "--strict-config",
            "--skip-git-repo-check",
            "--output-schema",
            "--json",
            "default_permissions",
            "shell_tool",
            "unified_exec",
            "multi_agent",
            "apps",
            "image_generation",
            "skill_search",
        ):
            self.assertIn(required, joined)
        self.assertNotIn("--sandbox", command)
        self.assertNotIn("code_mode_host", sweep_launcher.CODEX_DISABLED_FEATURES)
        self.assertIn(
            'mcp_servers.sweep-broker.default_tools_approval_mode="approve"',
            command,
        )
        enabled_tools = next(
            item
            for item in command
            if item.startswith("mcp_servers.sweep-broker.enabled_tools=")
        )
        for tool_name in sweep_isolation.BROKER_TOOL_NAMES:
            self.assertIn(json.dumps(tool_name), enabled_tools)
        self.assertIn(
            "cannot construct or guess the receipt",
            sweep_launcher.CODEX_STAGE_PROMPTS["classifier"],
        )
        self.assertIn(
            "must call the broker tools",
            sweep_launcher.CODEX_STAGE_PROMPTS["classifier"].casefold(),
        )
        for stage, required_tools in {
            "classifier": ("review_comment", "submit_result"),
            "perspective": ("review_comment", "consensus_inputs", "submit_result"),
            "synthesis": ("consensus_inputs", "submit_result"),
        }.items():
            for tool_name in required_tools:
                self.assertIn(
                    f"mcp__sweep-broker__{tool_name}",
                    sweep_launcher.CODEX_STAGE_PROMPTS[stage],
                )
            self.assertIn(
                "one top-level result field",
                sweep_launcher.CODEX_STAGE_PROMPTS[stage].casefold(),
            )

    def test_codex_event_projection_exposes_only_broker_tool_status(self) -> None:
        events = "\n".join(
            (
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "agent_message",
                            "text": "MODEL_PROSE_CANARY",
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "mcp_tool_call",
                            "server": "sweep-broker",
                            "tool": "review_comment",
                            "arguments": {"secret": "ARGUMENT_CANARY"},
                            "result": "RESULT_CANARY",
                            "error": None,
                        },
                    }
                ),
            )
        )

        projection = sweep_launcher.codex_event_projection(events)

        self.assertEqual(
            {
                "jsonl": True,
                "broker_calls": {"review_comment": {"completed": 1, "failed": 0}},
                "error_codes": {},
                "unexpected_tools": 0,
            },
            projection,
        )
        serialized = json.dumps(projection, sort_keys=True)
        for canary in ("MODEL_PROSE_CANARY", "ARGUMENT_CANARY", "RESULT_CANARY"):
            self.assertNotIn(canary, serialized)

    def test_codex_event_projection_maps_broker_errors_without_exposing_content(self) -> None:
        events = json.dumps(
            {
                "type": "item.completed",
                "item": {
                    "type": "mcp_tool_call",
                    "server": "sweep-broker",
                    "tool": "submit_result",
                    "arguments": {"result": {"reason": "ARGUMENT_CANARY"}},
                    "result": {
                        "isError": True,
                        "content": [],
                    },
                    "error": {
                        "kind": "MCP tool call failed",
                        "details": {
                            "message": "result comment does not match the model-call capability",
                            "private": "ERROR_CANARY",
                        },
                    },
                },
            }
        )

        projection = sweep_launcher.codex_event_projection(events)

        self.assertEqual({"comment_mismatch": 1}, projection["error_codes"])
        serialized = json.dumps(projection, sort_keys=True)
        self.assertNotIn("ARGUMENT_CANARY", serialized)
        self.assertNotIn("ERROR_CANARY", serialized)

    def test_codex_event_gate_requires_the_exact_stage_calls(self) -> None:
        def completed(tool: str, *, status: str = "completed") -> str:
            return json.dumps(
                {
                    "type": "item.completed",
                    "item": {
                        "type": "mcp_tool_call",
                        "server": "sweep-broker",
                        "tool": tool,
                        "arguments": {},
                        "result": {"content": []},
                        "error": None if status == "completed" else {"message": "failed"},
                        "status": status,
                    },
                }
            )

        output = "\n".join((completed("review_comment"), completed("submit_result")))
        projection = sweep_launcher.verify_codex_event_trace(output, stage="classifier")
        self.assertEqual(1, projection["broker_calls"]["submit_result"]["completed"])

        for invalid in (
            completed("submit_result"),
            output + "\n" + completed("submit_result"),
            completed("review_comment") + "\n" + completed("submit_result", status="failed"),
            "not-jsonl",
        ):
            with self.assertRaises(sweep_launcher.LauncherViolation):
                sweep_launcher.verify_codex_event_trace(invalid, stage="classifier")

    def test_codex_child_process_starts_only_from_the_empty_runtime(self) -> None:
        source = (PLUGIN_ROOT / "speckit_pro_runner/sweep_launcher.py").read_text(
            encoding="utf-8"
        )
        body = source.split("def run_codex_sweep(", 1)[1].split("def _claude_version(", 1)[0]
        self.assertIn("cwd=runtime_root", body)
        self.assertNotIn("cwd=repo_root", body)

    def test_codex_prompt_resolver_accepts_only_source_and_packaged_layouts(self) -> None:
        self.assertEqual(
            PLUGIN_ROOT
            / "codex-skills/speckit-autopilot/references/sweep-prompts/classifier.md",
            sweep_launcher.codex_prompt_resource(PLUGIN_ROOT, "classifier"),
        )
        packaged = REPO_ROOT / "dist/codex/speckit-pro"
        self.assertEqual(
            packaged / "skills/speckit-autopilot/references/sweep-prompts/analyst.md",
            sweep_launcher.codex_prompt_resource(packaged, "analyst"),
        )
        with self.assertRaises(sweep_launcher.LauncherViolation):
            sweep_launcher.codex_prompt_resource(REPO_ROOT, "classifier")

    def test_claude_launcher_is_a_separate_broker_only_process(self) -> None:
        claude_runtime = REPO_ROOT.parent / "test-runtimes" / "claude"
        with patch.object(sweep_launcher, "claude_executable", return_value=claude_runtime):
            command = sweep_launcher.claude_command(
                plugin_root=PLUGIN_ROOT,
                stage="classifier",
            )
        self.assertEqual(claude_runtime, Path(command[0]))
        for flag in (
            "--print",
            "--plugin-dir",
            "--setting-sources",
            "--no-session-persistence",
            "--disable-slash-commands",
            "--no-chrome",
            "--permission-mode",
            "--tools",
            "--allowedTools",
            "--output-format",
            "--json-schema",
        ):
            self.assertIn(flag, command)
        schema = json.loads(command[command.index("--json-schema") + 1])
        self.assertEqual({"receipt"}, set(schema["properties"]))
        self.assertEqual(["receipt"], schema["required"])
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual("", command[command.index("--setting-sources") + 1])
        exact_tools = {
            "Agent",
            *{
                f"mcp__plugin_speckit-pro_sweep-broker__{name}"
                for name in sweep_isolation.BROKER_TOOL_NAMES
            },
        }
        self.assertEqual(
            exact_tools,
            set(command[command.index("--tools") + 1].split(",")),
        )
        self.assertEqual(
            exact_tools,
            set(command[command.index("--allowedTools") + 1].split(",")),
        )
        self.assertNotIn("sweep-cap:v1:", "\0".join(command))
        for forbidden in ("Read", "Grep", "Glob", "Bash", "WebFetch", "WebSearch"):
            self.assertNotIn(forbidden, exact_tools)

    def test_claude_agents_and_hooks_are_receipt_only_and_broker_only(self) -> None:
        broker_prefix = "mcp__plugin_speckit-pro_sweep-broker__"
        for name in ("sweep-classifier.md", "sweep-analyst.md"):
            source = (PLUGIN_ROOT / "agents" / name).read_text(encoding="utf-8")
            frontmatter = source.split("---", 2)[1]
            self.assertIn(broker_prefix, frontmatter)
            for forbidden in ("Read", "Grep", "Glob", "Bash", "WebFetch", "WebSearch", "Agent"):
                self.assertNotRegex(frontmatter, rf"(?m)^tools:.*\b{forbidden}\b")
        hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        encoded = json.dumps(hooks, sort_keys=True)
        self.assertIn("SessionStart", encoded)
        self.assertIn("SubagentStop", encoded)
        self.assertIn("authorize-broker", encoded)
        self.assertIn("mcp__plugin_speckit-pro_sweep-broker__", encoded)
        self.assertIn(sweep_isolation.HOOK_VERSION, encoded)

    def test_codex_sweep_roles_are_not_callable_installed_agents(self) -> None:
        for name in ("sweep-classifier.toml", "sweep-analyst.toml"):
            self.assertFalse((PLUGIN_ROOT / "codex-agents" / name).exists())
        resources = PLUGIN_ROOT / "codex-skills" / "speckit-autopilot" / "references" / "sweep-prompts"
        self.assertTrue((resources / "classifier.md").is_file())
        self.assertTrue((resources / "analyst.md").is_file())

    def test_plugin_packages_the_local_broker_and_receipt_schema(self) -> None:
        manifest = json.loads((PLUGIN_ROOT / ".mcp.json").read_text(encoding="utf-8"))
        self.assertEqual({"sweep-broker"}, set(manifest["mcpServers"]))
        server = manifest["mcpServers"]["sweep-broker"]
        self.assertEqual(["-m", "speckit_pro_runner.sweep_broker"], server["args"])
        self.assertEqual("${CLAUDE_PLUGIN_ROOT}", server["env"]["PYTHONPATH"])
        self.assertEqual(
            manifest,
            json.loads(
                (REPO_ROOT / "dist/claude/speckit-pro/.mcp.json").read_text(encoding="utf-8")
            ),
        )

        codex_manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual("./.codex-plugin/sweep-mcp.json", codex_manifest["mcpServers"])
        codex_mcp = json.loads(
            (PLUGIN_ROOT / ".codex-plugin/sweep-mcp.json").read_text(encoding="utf-8")
        )
        codex_server = codex_mcp["mcpServers"]["sweep-broker"]
        self.assertEqual(["-m", "speckit_pro_runner.sweep_broker"], codex_server["args"])
        self.assertEqual(".", codex_server["cwd"])
        self.assertNotIn("env", codex_server)
        self.assertEqual(
            codex_mcp,
            json.loads(
                (
                    REPO_ROOT
                    / "dist/codex/speckit-pro/.codex-plugin/sweep-mcp.json"
                ).read_text(encoding="utf-8")
            ),
        )
        self.assertTrue(
            (PLUGIN_ROOT / "speckit_pro_runner/contracts/sweep-receipt-output.schema.json").is_file()
        )

    def test_codex_mcp_manifest_completes_a_stdio_handshake_without_pythonpath(self) -> None:
        manifest = json.loads(
            (PLUGIN_ROOT / ".codex-plugin/sweep-mcp.json").read_text(encoding="utf-8")
        )
        server = manifest["mcpServers"]["sweep-broker"]
        requests = (
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18", "capabilities": {}},
            },
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        self.assertEqual("python3", server["command"])
        completed = subprocess.run(
            [sys.executable, *server["args"]],
            cwd=PLUGIN_ROOT / server["cwd"],
            input="".join(json.dumps(request) + "\n" for request in requests),
            text=True,
            capture_output=True,
            check=False,
            env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"},
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("", completed.stderr)
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual("speckit-pro-sweep-broker", responses[0]["result"]["serverInfo"]["name"])
        self.assertEqual(
            set(sweep_broker.BROKER_TOOL_NAMES),
            {tool["name"] for tool in responses[1]["result"]["tools"]},
        )

    def test_runner_registers_private_capture_accept_launch_and_receipt_apply(self) -> None:
        self.assertIn("sweep-isolation-session", registry.HELPERS)
        self.assertIn("sweep-apply-result", registry.MUTATION_HELPERS)
        entry = registry.MUTATION_HELPERS["sweep-apply-result"]
        self.assertEqual(("dry_run", "apply"), entry.modes)
        implementation = (PLUGIN_ROOT / "speckit_pro_runner/helpers/read_only.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"launch_claude"', implementation)

    def test_runner_exposes_a_bounded_private_session_close_surface(self) -> None:
        source = read_only.sweep_isolation_session.__doc__ or ""
        self.assertIn("private", source)
        implementation = (PLUGIN_ROOT / "speckit_pro_runner/helpers/read_only.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"close"', implementation)


class CaptureAndHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = GitFixture()
        self.fixture.write("specs/001-safe/plan.md", "# Plan\nold text\n")
        self.fixture.write(
            "workflow.md",
            "# Workflow\n\n## Feedback Sweep Log\n\n"
            "| Comment ID | Class |\n| --- | --- |\n| logged-id | answered |\n",
        )
        self.fixture.commit()
        self.state_root = Path(self.fixture.temp.name) / "private-state"

    def tearDown(self) -> None:
        self.fixture.close()

    def test_private_capture_returns_only_metadata_and_filters_before_dispatch(self) -> None:
        canary = f"REVIEW-{secrets.token_hex(24)}"
        comments = [
            {
                "id": "candidate-id",
                "surface": "review_thread",
                "author": "reviewer",
                "author_association": "MEMBER",
                "body": f"Please amend plan.md. {canary}",
                "thread_resolved": False,
                "truncated": False,
            },
            {
                "id": "untrusted-id",
                "surface": "pr_conversation",
                "author": "outsider",
                "author_association": "NONE",
                "body": canary,
                "thread_resolved": False,
                "truncated": False,
            },
            {
                "id": "logged-id",
                "surface": "pr_conversation",
                "author": "reviewer",
                "author_association": "OWNER",
                "body": canary,
                "thread_resolved": False,
                "truncated": False,
            },
            {
                "id": "self-id",
                "surface": "pr_conversation",
                "author": "bot-login",
                "author_association": "OWNER",
                "body": "<!-- speckit-pro:feedback-sweep candidate-id -->\nRecorded.",
                "thread_resolved": False,
                "truncated": False,
            },
        ]
        metadata = sweep_isolation.capture_session_from_comments(
            self.fixture.root,
            workflow_file="workflow.md",
            self_login="bot-login",
            comments=comments,
            state_root=self.state_root,
            now=1_000,
        )
        public = json.dumps(metadata, sort_keys=True)
        self.assertNotIn(canary, public)
        self.assertEqual(["candidate-id"], [item["id"] for item in metadata["comments"]])
        self.assertEqual(
            {"untrusted_author", "already_logged", "self_reply"},
            {item["reason"] for item in metadata["excluded"]},
        )
        session = sweep_isolation.SweepSession.open(
            metadata["session_id"], state_root=self.state_root, now=1_000
        )
        self.assertIn(canary, session.review_comment("candidate-id")["block"])

    def test_github_capture_failure_creates_no_session(self) -> None:
        before = set(self.state_root.iterdir()) if self.state_root.exists() else set()
        with patch.object(
            sweep_isolation,
            "read_github_comments",
            side_effect=sweep_isolation.CaptureViolation("review_thread read failed"),
        ):
            with self.assertRaises(sweep_isolation.CaptureViolation):
                sweep_isolation.capture_github_session(
                    self.fixture.root,
                    repository="owner/repo",
                    pr_number=498,
                    workflow_file="workflow.md",
                    state_root=self.state_root,
                )
        after = set(self.state_root.iterdir()) if self.state_root.exists() else set()
        self.assertEqual(before, after)

    def test_codex_security_preflight_runs_before_github_capture(self) -> None:
        inputs = {
            "named_surface": "capture",
            "surface": "codex",
            "repository": "owner/repo",
            "pr_number": 498,
            "workflow_file": "workflow.md",
        }
        with patch.object(
            sweep_launcher,
            "verify_codex_boundary",
            side_effect=sweep_launcher.LauncherViolation("unsupported"),
        ), patch.object(sweep_isolation, "read_github_comments") as github_read:
            result = read_only.sweep_isolation_session(inputs, self.fixture.root)
        self.assertEqual(3, result["exit_code"])
        self.assertIn("isolation_boundary_unavailable", result["stdout"])
        github_read.assert_not_called()

    def test_capture_filters_from_committed_workflow_and_validation_failure_leaves_no_session(self) -> None:
        # The working copy tries to erase the durable skip key. Capture must use
        # the exact committed blob, not that mutable worktree content.
        (self.fixture.root / "workflow.md").write_text("# uncommitted replacement\n", encoding="utf-8")
        logged = {
            "id": "logged-id",
            "surface": "pr_conversation",
            "author": "reviewer",
            "author_association": "OWNER",
            "body": "Try to process me again.",
            "thread_resolved": False,
            "truncated": False,
        }
        metadata = sweep_isolation.capture_session_from_comments(
            self.fixture.root,
            workflow_file="workflow.md",
            self_login="bot-login",
            comments=[logged],
            state_root=self.state_root,
            now=1_000,
        )
        self.assertEqual([], metadata["comments"])
        self.assertEqual("already_logged", metadata["excluded"][0]["reason"])

        before = set(self.state_root.iterdir())
        with self.assertRaises(sweep_isolation.SchemaViolation):
            sweep_isolation.SweepSession.create(
                self.fixture.root,
                comments=[logged, logged],
                state_root=self.state_root,
                now=1_000,
            )
        self.assertEqual(before, set(self.state_root.iterdir()))

    def test_claude_hook_requires_exactly_a_mode_and_version(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "sweep-isolation-hook.py"
        payload = json.dumps({"cwd": str(REPO_ROOT)})
        with tempfile.TemporaryDirectory(prefix="sweep-hook-argv-") as temporary:
            env = {**os.environ, "TMPDIR": temporary}
            for arguments in (
                ["attest"],
                ["attest", sweep_isolation.HOOK_VERSION, "ignored"],
            ):
                with self.subTest(arguments=arguments):
                    refused = subprocess.run(
                        [sys.executable, str(script), *arguments],
                        input=payload,
                        text=True,
                        capture_output=True,
                        env=env,
                        check=False,
                    )
                    self.assertEqual(2, refused.returncode)
                    self.assertIn("version mismatch", refused.stderr)

    def test_claude_hook_attests_and_rejects_non_receipt_final_output(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "sweep-isolation-hook.py"
        with tempfile.TemporaryDirectory(prefix="sweep-hook-") as temporary:
            env = {**os.environ, "TMPDIR": temporary}
            base = {"cwd": str(REPO_ROOT), "agent_type": "sweep-classifier"}
            attest = subprocess.run(
                [sys.executable, str(script), "attest", sweep_isolation.HOOK_VERSION],
                input=json.dumps(base),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(0, attest.returncode, attest.stderr)
            attestation_root = Path(temporary) / f"speckit-pro-sweep-hooks-{os.getuid()}"
            attestation_record = json.loads(
                next(attestation_root.glob("*.json")).read_text(encoding="utf-8")
            )
            self.assertEqual(
                hashlib.sha256(script.read_bytes()).hexdigest(),
                attestation_record["hook_script_sha256"],
            )
            refused = subprocess.run(
                [sys.executable, str(script), "validate-stop", sweep_isolation.HOOK_VERSION],
                input=json.dumps({**base, "last_assistant_message": "review text"}),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(2, refused.returncode)
            accepted = subprocess.run(
                [sys.executable, str(script), "validate-stop", sweep_isolation.HOOK_VERSION],
                input=json.dumps(
                    {**base, "last_assistant_message": "sweep-result:v1:" + "a" * 64}
                ),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(0, accepted.returncode, accepted.stderr)

            broker_env = {
                **env,
                "SPECKIT_SWEEP_CAPABILITY": "sweep-cap:v1:" + "a" * 32 + ":" + "b" * 64,
            }
            direct_parent_dispatch = subprocess.run(
                [sys.executable, str(script), "pre-dispatch", sweep_isolation.HOOK_VERSION],
                input=json.dumps(base),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(2, direct_parent_dispatch.returncode)
            isolated_dispatch = subprocess.run(
                [sys.executable, str(script), "pre-dispatch", sweep_isolation.HOOK_VERSION],
                input=json.dumps(base),
                text=True,
                capture_output=True,
                env=broker_env,
                check=False,
            )
            self.assertEqual(0, isolated_dispatch.returncode, isolated_dispatch.stderr)
            parent_call = subprocess.run(
                [sys.executable, str(script), "authorize-broker", sweep_isolation.HOOK_VERSION],
                input=json.dumps({"cwd": str(REPO_ROOT)}),
                text=True,
                capture_output=True,
                env=broker_env,
                check=False,
            )
            self.assertEqual(2, parent_call.returncode)
            subagent_call = subprocess.run(
                [sys.executable, str(script), "authorize-broker", sweep_isolation.HOOK_VERSION],
                input=json.dumps({**base, "agent_id": "agent-isolated-sweep"}),
                text=True,
                capture_output=True,
                env=broker_env,
                check=False,
            )
            self.assertEqual(0, subagent_call.returncode, subagent_call.stderr)

    def test_claude_hook_rejects_a_symlinked_attestation_record(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "sweep-isolation-hook.py"
        with tempfile.TemporaryDirectory(prefix="sweep-hook-link-") as temporary:
            env = {**os.environ, "TMPDIR": temporary}
            base = {"cwd": str(REPO_ROOT), "agent_type": "sweep-classifier"}
            attest = subprocess.run(
                [sys.executable, str(script), "attest", sweep_isolation.HOOK_VERSION],
                input=json.dumps(base),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(0, attest.returncode, attest.stderr)
            root = Path(temporary) / f"speckit-pro-sweep-hooks-{os.getuid()}"
            record = next(root.glob("*.json"))
            target = root / "attestation-copy"
            record.replace(target)
            record.symlink_to(target.name)
            refused = subprocess.run(
                [sys.executable, str(script), "validate-stop", sweep_isolation.HOOK_VERSION],
                input=json.dumps(
                    {**base, "last_assistant_message": "sweep-result:v1:" + "a" * 64}
                ),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(2, refused.returncode)

    def test_parent_rejects_a_symlinked_claude_attestation_record(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "sweep-isolation-hook.py"
        with tempfile.TemporaryDirectory(prefix="sweep-parent-link-") as temporary:
            env = {**os.environ, "TMPDIR": temporary}
            base = {"cwd": str(REPO_ROOT), "agent_type": "sweep-classifier"}
            attest = subprocess.run(
                [sys.executable, str(script), "attest", sweep_isolation.HOOK_VERSION],
                input=json.dumps(base),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(0, attest.returncode, attest.stderr)
            root = Path(temporary) / f"speckit-pro-sweep-hooks-{os.getuid()}"
            record = next(root.glob("*.json"))
            target = root / "attestation-copy"
            record.replace(target)
            record.symlink_to(target.name)
            with patch.object(sweep_launcher.tempfile, "gettempdir", return_value=temporary):
                with self.assertRaises(sweep_launcher.LauncherViolation):
                    sweep_launcher.verify_claude_attestation(REPO_ROOT, PLUGIN_ROOT)


class WorkflowAndEvalContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.claude_reference = (
            PLUGIN_ROOT
            / "skills/speckit-autopilot/references/phase-execution.md"
        ).read_text(encoding="utf-8")
        self.codex_reference = (
            PLUGIN_ROOT
            / "codex-skills/speckit-autopilot/references/phase-execution-codex.md"
        ).read_text(encoding="utf-8")
        self.classifier_prompts = {
            "claude": (PLUGIN_ROOT / "agents/sweep-classifier.md").read_text(
                encoding="utf-8"
            ),
            "codex": (
                PLUGIN_ROOT
                / "codex-skills/speckit-autopilot/references/sweep-prompts/classifier.md"
            ).read_text(encoding="utf-8"),
        }
        self.analyst_prompts = {
            "claude": (PLUGIN_ROOT / "agents/sweep-analyst.md").read_text(
                encoding="utf-8"
            ),
            "codex": (
                PLUGIN_ROOT
                / "codex-skills/speckit-autopilot/references/sweep-prompts/analyst.md"
            ).read_text(encoding="utf-8"),
        }

    def test_active_sweep_references_use_private_receipts_and_fail_closed(self) -> None:
        for surface, source in (
            ("Claude", self.claude_reference),
            ("Codex", self.codex_reference),
        ):
            with self.subTest(surface=surface):
                for required in (
                    "sweep-isolation-session",
                    "sweep-apply-result",
                    "sweep-result:v1:<64-hex>",
                    "exact `HEAD`",
                    "zero model-derived writes, commits, pushes, replies, or downstream dispatches",
                    "later resumed run",
                ):
                    self.assertIn(required, source)
                self.assertNotIn("sweep-pr-feedback", source)
                self.assertNotIn(
                    "gh ... | resolved_python -m speckit_pro_runner", source
                )

    def test_claude_and_codex_use_their_surface_specific_isolation_boundaries(self) -> None:
        self.assertIn(
            "mcp__plugin_speckit-pro_sweep-broker__", self.claude_reference
        )
        self.assertIn("SubagentStop", self.claude_reference)
        self.assertIn("launch_claude", self.claude_reference)
        self.assertIn("separate `claude --print` process", self.claude_reference)
        self.assertIn(
            "codex exec --ignore-user-config --ignore-rules --ephemeral --strict-config",
            self.codex_reference,
        )
        self.assertIn("default_permissions", self.codex_reference)
        self.assertNotRegex(
            self.codex_reference,
            r"spawn_agent[^\n]{0,160}sweep-(?:classifier|analyst)",
        )

    def test_amendment_run_stops_before_broader_artifact_regeneration(self) -> None:
        for surface, source in (
            ("Claude", self.claude_reference),
            ("Codex", self.codex_reference),
        ):
            stop = source.index("Stop for human re-review before artifact regeneration")
            resume = source.index("On a later resumed run")
            with self.subTest(surface=surface):
                self.assertLess(stop, resume)

    def test_both_surfaces_ship_the_same_adversarial_isolation_eval(self) -> None:
        paths = {
            "claude": REPO_ROOT
            / "tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json",
            "codex": REPO_ROOT
            / "tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json",
        }
        evals: dict[str, dict[str, object]] = {}
        for surface, path in paths.items():
            records = json.loads(path.read_text(encoding="utf-8"))["evals"]
            matching = [record for record in records if record["id"] == 109]
            self.assertEqual(1, len(matching), surface)
            record = matching[0]
            joined = json.dumps(record, sort_keys=True)
            for required in (
                "home",
                "environment",
                "untracked .env",
                "sibling worktree",
                "symlink",
                "Git metadata",
                "canary",
                "zero",
            ):
                self.assertIn(required, joined, f"{surface}: {required}")
            evals[surface] = record

        self.assertIn("SubagentStop", json.dumps(evals["claude"], sort_keys=True))
        codex = json.dumps(evals["codex"], sort_keys=True)
        self.assertIn("codex exec", codex)
        self.assertIn("no spawn_agent", codex)

    def test_both_classifier_prompts_define_all_four_dispositions(self) -> None:
        required = (
            "asks for a change to `spec.md`, `plan.md`, or `tasks.md`",
            "already settle the objection",
            "recorded and not acted on",
            "asks for no action",
            "`amended` wins",
        )
        for surface, source in self.classifier_prompts.items():
            with self.subTest(surface=surface):
                normalized = " ".join(source.split())
                for phrase in required:
                    self.assertIn(phrase, normalized)

    def test_both_analyst_prompts_define_perspectives_and_synthesis_mapping(self) -> None:
        required = (
            "established repository patterns",
            "constitution, roadmap, and current planning artifacts",
            "documented guidance and industry practice",
            "Any unresolved `escape_hatch`",
            "`escape_unresolved`",
            "No two records materially agree",
            "`all_disagree`",
            "Exactly two materially agree",
            "`2/3`",
            "All three materially agree",
            "`3/3`",
        )
        for surface, source in self.analyst_prompts.items():
            with self.subTest(surface=surface):
                for phrase in required:
                    self.assertIn(phrase, source)

    def test_both_surfaces_ship_the_same_sweep_behavior_regression_eval(self) -> None:
        paths = {
            "claude": REPO_ROOT
            / "tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json",
            "codex": REPO_ROOT
            / "tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json",
        }
        records: dict[str, dict[str, object]] = {}
        for surface, path in paths.items():
            evals = json.loads(path.read_text(encoding="utf-8"))["evals"]
            matching = [record for record in evals if record["id"] == 110]
            self.assertEqual(1, len(matching), surface)
            record = matching[0]
            joined = json.dumps(record, sort_keys=True)
            for required in (
                "amended",
                "answered",
                "deferred",
                "no action",
                "three perspectives",
                "2/3",
                "3/3",
                "escape_unresolved",
                "all_disagree",
                "receipt",
            ):
                self.assertIn(required, joined, f"{surface}: {required}")
            records[surface] = record

        self.assertEqual(
            records["claude"]["expectations"], records["codex"]["expectations"]
        )

    def test_operator_live_smoke_covers_both_exact_clis_with_one_fixture(self) -> None:
        script = (
            REPO_ROOT
            / "tests/speckit-pro/layer7-integration/run-feedback-sweep-isolation-smoke.py"
        )
        self.assertTrue(script.is_file())
        spec = importlib.util.spec_from_file_location("feedback_sweep_live_smoke", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        self.assertEqual(
            {"claude": "2.1.245", "codex": "0.149.0"},
            module.REQUIRED_CLI_VERSIONS,
        )
        self.assertEqual(
            {
                "home",
                "environment",
                "untracked_env",
                "sibling_worktree",
                "symlink_target",
                "git_metadata",
            },
            set(module.CANARY_LOCATIONS),
        )
        self.assertEqual(("claude", "codex", "both"), module.SURFACE_CHOICES)
        self.assertEqual(
            {
                "claude": REPO_ROOT / "dist/claude/speckit-pro",
                "codex": REPO_ROOT / "dist/codex/speckit-pro",
            },
            module.PACKAGED_PLUGIN_ROOTS,
        )

        source = script.read_text(encoding="utf-8")
        self.assertIn("home_canary_path", source)
        self.assertNotIn('env["HOME"]', source)
        self.assertNotIn("plugin_root=PLUGIN_ROOT", source)

        manifest = json.loads(
            (REPO_ROOT / "tests/speckit-pro/suite-manifest.json").read_text(encoding="utf-8")
        )
        self.assertNotIn(script.name, json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    raise SystemExit(run_counted(suite, label="test-feedback-sweep-isolation"))
