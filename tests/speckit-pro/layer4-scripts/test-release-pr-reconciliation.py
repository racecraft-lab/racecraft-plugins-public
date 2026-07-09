#!/usr/bin/env python3
"""Regression coverage for unchanged release PR reconciliation."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


resolver = load_module("resolve_release_prs", REPO_ROOT / "scripts" / "resolve_release_prs.py")
refresh = load_module("refresh_release_artifacts", REPO_ROOT / "scripts" / "refresh-release-artifacts.py")
sync = load_module("sync_release_pr", REPO_ROOT / "scripts" / "sync_release_pr.py")


class FakeGuard:
    HASHES = {
        "dist/claude/speckit-pro": "c" * 64,
        "dist/codex/speckit-pro": "d" * 64,
    }

    @classmethod
    def payload_tree_inventory(cls, _repo_root: Path, source_root: str, _row: dict):
        return {"tree_hash": cls.HASHES[source_root], "files": ["manifest.json"]}


def proof(rows: list[dict]) -> str:
    return json.dumps({"schema_version": "1.0", "proofs": rows}, indent=2) + "\n"


def row(product: str, tree_hash: str) -> dict:
    return {
        "product": product,
        "source_payload_root": f"dist/{product}/speckit-pro",
        "source_payload_tree_hash": tree_hash,
    }


class ReleasePrReconciliationTests(unittest.TestCase):
    def test_action_output_takes_precedence(self) -> None:
        created = [{"number": 302, "title": "release", "headBranchName": "release-please--branches--main--components--speckit-pro"}]
        unrelated = [{"number": 99, "title": "other", "headRefName": "feature/not-release", "baseRefName": "main"}]
        self.assertEqual(resolver.resolve_release_prs(created, unrelated, "main")[0]["number"], 302)

    def test_unchanged_open_release_pr_is_discovered(self) -> None:
        open_prs = [
            {"number": 9, "title": "other", "headRefName": "feature/other", "baseRefName": "main"},
            {"number": 302, "title": "release", "headRefName": "release-please--branches--main--components--speckit-pro", "baseRefName": "main"},
            {"number": 303, "title": "fork", "headRefName": "release-please--branches--main--components--fork", "baseRefName": "main", "isCrossRepository": True},
            {"number": 7, "title": "wrong base", "headRefName": "release-please--branches--dev--components--speckit-pro", "baseRefName": "dev"},
        ]
        self.assertEqual(
            resolver.resolve_release_prs([], open_prs, "main"),
            [{"number": 302, "title": "release", "headBranchName": "release-please--branches--main--components--speckit-pro"}],
        )

    def test_no_open_release_pr_is_a_clean_noop(self) -> None:
        self.assertEqual(resolver.resolve_release_prs([], [], "main"), [])

    def test_unsafe_action_branch_is_rejected(self) -> None:
        with self.assertRaises(resolver.ResolutionError):
            resolver.resolve_release_prs(
                [{"number": 302, "title": "release", "headBranchName": "feature/not-release"}],
                [],
                "main",
            )

    def test_sync_merges_base_before_refresh_and_pushes(self) -> None:
        class FakeRunner:
            def __init__(self) -> None:
                self.commands: list[list[str]] = []
                self.fetch_heads = iter(["release-head", "main-head"])

            def run(self, argv, _cwd) -> None:
                self.commands.append(list(argv))

            def output(self, argv, _cwd) -> str:
                command = list(argv)
                self.commands.append(command)
                if command == ["git", "rev-parse", "FETCH_HEAD"]:
                    return next(self.fetch_heads)
                if command == ["git", "status", "--porcelain"]:
                    return " M generated-file"
                if command == ["git", "rev-parse", "HEAD"]:
                    return "reconciled-head"
                raise AssertionError(command)

        runner = FakeRunner()
        sync.sync_release_branch(
            REPO_ROOT,
            {"number": 302, "title": "release", "headBranchName": "release-please--branches--main--components--speckit-pro"},
            "main",
            runner,
        )
        merge_index = runner.commands.index(["git", "merge", "--no-edit", "main-head"])
        refresh_index = runner.commands.index([sync.sys.executable, "scripts/refresh-release-artifacts.py"])
        docs_index = runner.commands.index(["pnpm", "--dir", "docs-site", "reference:generate"])
        push_index = runner.commands.index(["git", "push", "origin", "HEAD:release-please--branches--main--components--speckit-pro"])
        self.assertLess(merge_index, refresh_index)
        self.assertLess(refresh_index, docs_index)
        self.assertLess(docs_index, push_index)

    def test_canonical_mapping_recovers_legacy_partial_bump(self) -> None:
        old_claude = "a" * 64
        old_codex = "b" * 64
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            evidence = repo_root / refresh.EVIDENCE_PROOF
            evidence.parent.mkdir(parents=True)
            evidence.write_text(proof([row("claude", old_claude), row("codex", old_codex)]), encoding="utf-8")
            self.assertEqual(
                refresh.canonical_proof_hash_replacements(repo_root, FakeGuard),
                {old_claude: "c" * 64, old_codex: "d" * 64},
            )

    def test_missing_canonical_proof_fails_with_targeted_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stderr = io.StringIO()
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                refresh.canonical_proof_hash_replacements(Path(tmp), FakeGuard)

            self.assertEqual(raised.exception.code, 1)
            self.assertIn("unable to read canonical installed-cache proof", stderr.getvalue())
            self.assertIn(refresh.EVIDENCE_PROOF, stderr.getvalue())

    def test_malformed_canonical_proof_fails_with_targeted_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proof_path = Path(tmp) / refresh.EVIDENCE_PROOF
            proof_path.parent.mkdir(parents=True)
            proof_path.write_text("{not-json\n", encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
                refresh.canonical_proof_hash_replacements(Path(tmp), FakeGuard)

            self.assertEqual(raised.exception.code, 1)
            self.assertIn("is malformed JSON", stderr.getvalue())
            self.assertIn(refresh.EVIDENCE_PROOF, stderr.getvalue())

    def test_legacy_repair_preserves_deliberate_hash_sentinels(self) -> None:
        old_claude = "a" * 64
        old_codex = "b" * 64
        zero_hash = "0" * 64
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            canonical = repo_root / "canonical.json"
            stale = repo_root / "stale.json"
            mismatch = repo_root / "mismatch.json"
            canonical.write_text(proof([row("claude", old_claude), row("codex", old_codex)]), encoding="utf-8")
            stale.write_text(proof([row("claude", zero_hash), row("codex", old_codex)]), encoding="utf-8")
            mismatch.write_text(proof([row("claude", old_claude), row("codex", old_claude)]), encoding="utf-8")
            proof_files = [canonical, stale, mismatch]
            pre_bumped = {path: ["e" * 64, "f" * 64] for path in proof_files}

            refresh.refresh_proof_tree_hashes(
                repo_root,
                proof_files,
                pre_bumped,
                FakeGuard,
                canonical_replacements={old_claude: "c" * 64, old_codex: "d" * 64},
            )

            self.assertIn(zero_hash, stale.read_text(encoding="utf-8"))
            mismatch_rows = json.loads(mismatch.read_text(encoding="utf-8"))["proofs"]
            self.assertEqual(mismatch_rows[1]["source_payload_tree_hash"], "c" * 64)
            self.assertNotEqual(mismatch_rows[1]["source_payload_tree_hash"], "d" * 64)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReleasePrReconciliationTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    print(f"test-release-pr-reconciliation: {total - failed}/{total} passed")
    raise SystemExit(0 if result.wasSuccessful() else 1)
