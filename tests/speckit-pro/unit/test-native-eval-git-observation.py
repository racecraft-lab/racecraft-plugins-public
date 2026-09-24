#!/usr/bin/env python3
"""Focused tests for controller-side native-evaluation Git observations."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import stat
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
sys.path.insert(0, str(TEST_ROOT / "lib"))

import native_eval_fixture_setup as fixture_setup  # noqa: E402
import native_eval_git_observation as observation  # noqa: E402
from native_eval_git_observation import (  # noqa: E402
    GitObservationError,
    observe_git_state,
    observe_git_topology,
    snapshot_git_topology,
)
from test_result import run_counted  # noqa: E402


def git_tree_snapshot(root: Path) -> dict[str, tuple[object, ...]]:
    records: dict[str, tuple[object, ...]] = {}
    for path in (root, *sorted(root.rglob("*"))):
        metadata = path.lstat()
        mode = metadata.st_mode
        relative = "." if path == root else path.relative_to(root).as_posix()
        if stat.S_ISREG(mode):
            detail: object = hashlib.sha256(path.read_bytes()).hexdigest()
            kind = "file"
        elif stat.S_ISLNK(mode):
            detail = os.readlink(path)
            kind = "symlink"
        elif stat.S_ISDIR(mode):
            detail = None
            kind = "directory"
        else:
            detail = None
            kind = "other"
        records[relative] = (
            kind,
            stat.S_IMODE(mode),
            metadata.st_size,
            metadata.st_mtime_ns,
            detail,
        )
    return records


class NativeEvalGitObservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def plan(self, fixture_root: Path) -> dict[str, object]:
        source = fixture_root / "source"
        source.mkdir(parents=True)
        (source / "baseline.txt").write_text("baseline\n", encoding="utf-8")
        (source / "feature.txt").write_text("feature\n", encoding="utf-8")
        return {
            "schema_version": "native-eval-fixtures/v2",
            "source_root": str(source),
            "fixtures": [{
                "source": "feature.txt",
                "destination": "README.md",
                "sha256": hashlib.sha256((source / "feature.txt").read_bytes()).hexdigest(),
            }],
            "git_repository": {
                "recipe": "baseline-feature-origin-main/v1",
                "baseline": [{
                    "source": "baseline.txt",
                    "destination": "README.md",
                    "sha256": hashlib.sha256((source / "baseline.txt").read_bytes()).hexdigest(),
                }],
            },
        }

    def fixture(self, name: str) -> tuple[Path, dict[str, object], dict[str, object]]:
        fixture_root = self.root / name
        workspace = fixture_root / "workspace"
        workspace.mkdir(parents=True)
        receipt = fixture_setup.materialize_workspace(self.plan(fixture_root), workspace)["git_repository"]
        exclude = workspace / ".git" / "info" / "exclude"
        exclude.parent.mkdir(exist_ok=True)
        exclude.write_text("# controller-owned exclusion\n", encoding="utf-8")
        controls = fixture_setup.snapshot_git_repository_controls(workspace)
        return workspace, receipt, controls

    def git_write(self, workspace: Path, *arguments: str) -> None:
        config = self.root / "writer-config"
        config.touch(exist_ok=True)
        hooks = self.root / "writer-hooks"
        hooks.mkdir(exist_ok=True)
        environment = fixture_setup._git_environment(config)
        git = shutil.which("git")
        self.assertIsInstance(git, str)
        self.assertEqual(str(Path(git).resolve()), fixture_setup._git_executable())
        completed = subprocess.run(
            [
                git,
                "-c",
                f"core.hooksPath={hooks}",
                "-c",
                "maintenance.auto=false",
                *arguments,
            ],
            cwd=workspace,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))

    def marker_program(self, path: Path, marker: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"#!{sys.executable}\nfrom pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n",
            encoding="utf-8",
        )
        path.chmod(0o700)

    def external_repository(self, name: str) -> tuple[Path, str]:
        repository = self.root / name
        config = self.root / "external-writer-config"
        config.touch(exist_ok=True)
        environment = fixture_setup._git_environment(config)
        git = shutil.which("git")
        self.assertIsInstance(git, str)
        self.assertEqual(str(Path(git).resolve()), fixture_setup._git_executable())
        common = dict(cwd=self.root, env=environment, stdin=subprocess.DEVNULL,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=30)
        completed = subprocess.run([git, "init", "--quiet", str(repository)], **common)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        completed = subprocess.run(
            [git, "-C", str(repository), "config", "user.name", "Controller"], **common)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        completed = subprocess.run(
            [git, "-C", str(repository), "config", "user.email", "native-eval@example.invalid"], **common)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        (repository / "external.txt").write_text("external\n", encoding="utf-8")
        completed = subprocess.run([git, "-C", str(repository), "add", "external.txt"], **common)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        completed = subprocess.run(
            [git, "-C", str(repository), "commit", "--quiet", "--no-gpg-sign", "-m", "external"], **common)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        completed = subprocess.run([git, "-C", str(repository), "rev-parse", "HEAD"], **common)
        self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
        return repository, completed.stdout.decode("ascii").strip()

    def test_unchanged_feature_is_clean_with_zero_relative_commits(self) -> None:
        workspace, receipt, controls = self.fixture("unchanged")
        git_before = git_tree_snapshot(workspace / ".git")
        result = observe_git_state(workspace, controls, receipt)

        self.assertEqual(result["schema_version"], "native-eval-git-observation/v1")
        self.assertEqual(result["head"], receipt["feature_commit"])
        self.assertEqual(result["branch"], "feature")
        self.assertEqual(result["origin_main"], receipt["baseline_commit"])
        self.assertEqual(result["commit_count"], 0)
        self.assertEqual(result["commits_added"], [])
        self.assertEqual(result["changed_tracked_paths_from_initial_feature"], [])
        self.assertEqual(result["status"], {
            "clean": True,
            "tracked_dirty": False,
            "untracked_dirty": False,
            "tracked": [],
            "untracked": [],
        })
        json.dumps(result, sort_keys=True, allow_nan=False)
        self.assertEqual(git_tree_snapshot(workspace / ".git"), git_before)

    def test_uncommitted_paths_are_dirty_but_never_new_commits(self) -> None:
        workspace, receipt, controls = self.fixture("uncommitted")
        (workspace / "README.md").write_text("dirty tracked\n", encoding="utf-8")
        (workspace / "artifact.md").write_text("untracked\n", encoding="utf-8")

        result = observe_git_state(workspace, controls, receipt)
        self.assertEqual(result["commit_count"], 0)
        self.assertEqual(result["commits_added"], [])
        self.assertEqual(result["changed_tracked_paths_from_initial_feature"], [])
        self.assertEqual(result["status"]["tracked"], [{
            "path": "README.md",
            "index": " ",
            "worktree": "M",
        }])
        self.assertEqual(result["status"]["untracked"], ["artifact.md"])
        self.assertFalse(result["status"]["clean"])
        with mock.patch.object(observation, "MAX_PATHS", 0):
            with self.assertRaisesRegex(GitObservationError, "path count exceeds limit"):
                observe_git_state(workspace, controls, receipt)

    def test_fixture_commits_never_start_detached_auto_maintenance(self) -> None:
        # A detached `git maintenance run --auto` holds objects/maintenance.lock
        # while the control-path walk runs, so a vanished lock fails it at random.
        trace = self.root / "git-trace"
        real_environment = fixture_setup._git_environment

        def traced_environment(config: Path) -> dict[str, str]:
            return {**real_environment(config), "GIT_TRACE": str(trace)}

        with mock.patch.object(fixture_setup, "_git_environment", traced_environment):
            workspace, _receipt, _controls = self.fixture("traced")
            (workspace / "artifact.md").write_text("traced artifact\n", encoding="utf-8")
            self.git_write(workspace, "add", "--", "artifact.md")
            self.git_write(workspace, "commit", "--quiet", "--no-gpg-sign", "-m", "traced")
        log = trace.read_text(encoding="utf-8")
        self.assertIn("built-in: git commit", log)
        self.assertNotIn("maintenance run", log)

    def test_commit_records_message_paths_and_feature_relative_count(self) -> None:
        workspace, receipt, controls = self.fixture("committed")
        (workspace / "artifact.md").write_text("committed artifact\n", encoding="utf-8")
        self.git_write(workspace, "add", "--", "artifact.md")
        self.git_write(workspace, "commit", "--quiet", "--no-gpg-sign", "-m", "add required artifact")

        result = observe_git_state(workspace, controls, receipt)
        self.assertEqual(result["commit_count"], 1)
        self.assertNotEqual(result["head"], receipt["feature_commit"])
        self.assertEqual(result["changed_tracked_paths_from_initial_feature"], ["artifact.md"])
        self.assertEqual(result["commits_added"][0]["commit"], result["head"])
        self.assertEqual(result["commits_added"][0]["message"], "add required artifact\n")
        self.assertEqual(result["commits_added"][0]["paths"], ["artifact.md"])
        self.assertTrue(result["status"]["clean"])

        with mock.patch.object(observation, "MAX_COMMITS", 0):
            with self.assertRaisesRegex(GitObservationError, "new commit count exceeds limit"):
                observe_git_state(workspace, controls, receipt)
        with mock.patch.object(observation, "MAX_MESSAGE_BYTES", 1):
            with self.assertRaisesRegex(GitObservationError, "commit message exceeds limit"):
                observe_git_state(workspace, controls, receipt)
        with mock.patch.object(observation, "MAX_TOTAL_COMMIT_PATHS", 0):
            with self.assertRaisesRegex(GitObservationError, "commit path count exceeds limit"):
                observe_git_state(workspace, controls, receipt)

    def test_amended_and_rewritten_feature_history_is_rejected(self) -> None:
        for kind in ("amend", "reset"):
            with self.subTest(rewrite=kind):
                workspace, receipt, controls = self.fixture(f"rewrite-{kind}")
                if kind == "amend":
                    self.git_write(
                        workspace,
                        "commit",
                        "--amend",
                        "--quiet",
                        "--no-gpg-sign",
                        "-m",
                        "rewritten feature",
                    )
                else:
                    self.git_write(workspace, "reset", "--hard", "origin/main")
                with self.assertRaisesRegex(GitObservationError, "not an ancestor"):
                    observe_git_state(workspace, controls, receipt)

    def test_wrong_receipt_objects_and_changed_origin_ref_fail_closed(self) -> None:
        workspace, receipt, controls = self.fixture("wrong-receipt")
        cases = []
        wrong_baseline = copy.deepcopy(receipt)
        wrong_baseline["baseline_commit"] = wrong_baseline["origin_main"] = "0" * 40
        cases.append(("baseline", wrong_baseline, "verify baseline failed"))
        wrong_feature = copy.deepcopy(receipt)
        wrong_feature["feature_commit"] = wrong_feature["head"] = "1" * 40
        wrong_feature["feature_tree"] = "2" * 40
        cases.append(("feature", wrong_feature, "verify feature failed"))
        wrong_branch = copy.deepcopy(receipt)
        wrong_branch["branch"] = "main"
        cases.append(("branch", wrong_branch, "branch is malformed"))
        for label, candidate, message in cases:
            with self.subTest(receipt=label):
                with self.assertRaisesRegex(GitObservationError, message):
                    observe_git_state(workspace, controls, candidate)

        self.git_write(
            workspace,
            "update-ref",
            "refs/remotes/origin/main",
            receipt["feature_commit"],
        )
        with self.assertRaisesRegex(GitObservationError, "baseline or origin/main"):
            observe_git_state(workspace, controls, receipt)

    def test_malformed_receipt_rejects_before_any_git_process(self) -> None:
        workspace, receipt, controls = self.fixture("malformed-receipt")
        malformed = {**receipt, "agent_claim": "trusted"}
        with mock.patch.object(subprocess, "run", side_effect=AssertionError("Git executed")):
            with self.assertRaisesRegex(GitObservationError, "receipt is malformed"):
                observe_git_state(workspace, controls, malformed)

    def test_changed_or_redirected_controls_reject_before_any_git_process(self) -> None:
        scenarios = ("config", "missing-config", "commondir", "head-symlink")
        for scenario in scenarios:
            with self.subTest(control=scenario):
                workspace, receipt, controls = self.fixture(f"unsafe-{scenario}")
                if scenario == "config":
                    (workspace / ".git/config").write_text("[core]\n\thooksPath = /unsafe\n", encoding="utf-8")
                    message = "controls do not match"
                elif scenario == "missing-config":
                    (workspace / ".git/config").unlink()
                    message = "config is unavailable"
                elif scenario == "commondir":
                    (workspace / ".git/commondir").write_text("../outside\n", encoding="utf-8")
                    message = "control paths contain a redirect"
                else:
                    head = workspace / ".git/HEAD"
                    saved = head.with_name("HEAD.saved")
                    head.rename(saved)
                    try:
                        os.symlink(saved, head)
                    except OSError as exc:
                        self.skipTest(f"symlinks unavailable: {exc}")
                    message = "control paths contain a symlink"
                with mock.patch.object(subprocess, "run", side_effect=AssertionError("Git executed")):
                    with self.assertRaisesRegex(GitObservationError, message):
                        observe_git_state(workspace, controls, receipt)

    def test_ambient_config_diff_pager_and_local_hooks_never_execute(self) -> None:
        workspace, receipt, controls = self.fixture("ambient")
        marker = self.root / "external-executed"
        program = self.root / "external.py"
        self.marker_program(program, marker)
        global_config = self.root / "hostile-global-config"
        global_config.write_text(
            f"[core]\n\thooksPath = {self.root}\n\tpager = {program}\n"
            f"[diff]\n\texternal = {program}\n"
            f"[diff \"evil\"]\n\ttextconv = {program}\n",
            encoding="utf-8",
        )
        (workspace / ".git/info/attributes").write_text("README.md diff=evil\n", encoding="utf-8")
        local_hook = workspace / ".git/hooks/post-index-change"
        self.marker_program(local_hook, marker)
        hostile = {
            "GIT_CONFIG_GLOBAL": str(global_config),
            "GIT_EXTERNAL_DIFF": str(program),
            "GIT_PAGER": str(program),
            "PAGER": str(program),
        }
        with mock.patch.dict(os.environ, hostile, clear=False):
            result = observe_git_state(workspace, controls, receipt)
        self.assertTrue(result["status"]["clean"])
        self.assertFalse(marker.exists())

    def test_git_failures_timeouts_output_overflow_and_truncation_fail_closed(self) -> None:
        workspace = self.root
        environment = {"PATH": os.environ["PATH"]}
        failure = subprocess.CompletedProcess(["git"], 2)
        with mock.patch.object(observation.subprocess, "run", return_value=failure):
            with self.assertRaisesRegex(GitObservationError, "Git forced failure failed"):
                observation._git_result("git", workspace, environment, ["status"], "forced failure")
        with mock.patch.object(
            observation.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired("git", 30),
        ):
            with self.assertRaisesRegex(GitObservationError, "Git forced timeout timed out"):
                observation._git_result("git", workspace, environment, ["status"], "forced timeout")

        def overflow(*_args: object, **kwargs: object):
            kwargs["stdout"].write(b"x" * (observation.MAX_OUTPUT_BYTES + 1))
            return subprocess.CompletedProcess(["git"], 0)

        with mock.patch.object(observation.subprocess, "run", side_effect=overflow):
            with self.assertRaisesRegex(GitObservationError, "output exceeds limit"):
                observation._git_result("git", workspace, environment, ["status"], "overflow")
        with self.assertRaisesRegex(GitObservationError, "truncated or malformed"):
            observation._path_list(b"unterminated", "forced path list")

    def test_existing_recipe_inspector_still_rejects_modified_postrun(self) -> None:
        workspace, receipt, controls = self.fixture("existing-inspector")
        (workspace / "README.md").write_text("modified after fixture creation\n", encoding="utf-8")
        result = observe_git_state(workspace, controls, receipt)
        self.assertTrue(result["status"]["tracked_dirty"])
        with self.assertRaisesRegex(ValueError, "receipt invariants"):
            fixture_setup.inspect_git_repository(workspace, controls)

    def test_topology_observation_distinguishes_existing_created_and_reused_worktrees(self) -> None:
        workspace, receipt, controls = self.fixture("dynamic-topology")
        existing = workspace / ".worktrees/existing"
        existing.parent.mkdir()
        self.git_write(workspace, "worktree", "add", "--quiet", "-b", "scenario/existing", str(existing))

        baseline = snapshot_git_topology(workspace, controls, receipt)
        self.assertEqual([row["path"] for row in baseline["worktrees"]], [".", ".worktrees/existing"])
        self.assertEqual([row["name"] for row in baseline["branches"]], ["feature", "main", "scenario/existing"])
        reused = observe_git_topology(workspace, controls, receipt, baseline)
        self.assertEqual(reused["initial"], reused["current"])

        created = workspace / ".worktrees/created"
        self.git_write(workspace, "worktree", "add", "--quiet", "-b", "scenario/created", str(created))
        observed = observe_git_topology(workspace, controls, receipt, baseline)
        self.assertEqual([row["path"] for row in observed["initial"]["worktrees"]], [".", ".worktrees/existing"])
        self.assertEqual([row["path"] for row in observed["current"]["worktrees"]], [".", ".worktrees/created", ".worktrees/existing"])
        self.assertEqual([row["name"] for row in observed["current"]["branches"]], ["feature", "main", "scenario/created", "scenario/existing"])

    def test_topology_records_dirty_child_and_branch_change_against_actual_baseline(self) -> None:
        workspace, receipt, controls = self.fixture("topology-dirty")
        child = workspace / ".worktrees/work"
        child.parent.mkdir()
        self.git_write(workspace, "worktree", "add", "--quiet", "-b", "scenario/work", str(child))
        baseline = snapshot_git_topology(workspace, controls, receipt)

        (child / "actor.txt").write_text("dirty\n", encoding="utf-8")
        self.git_write(child, "checkout", "--quiet", "--detach")
        observed = observe_git_topology(workspace, controls, receipt, baseline)
        before = next(row for row in observed["initial"]["worktrees"] if row["path"] == ".worktrees/work")
        after = next(row for row in observed["current"]["worktrees"] if row["path"] == ".worktrees/work")
        self.assertEqual(before["branch"], "scenario/work")
        self.assertIsNone(after["branch"])
        self.assertEqual(after["status"]["untracked"], ["actor.txt"])

    def test_topology_records_worktree_omission_against_the_caller_baseline(self) -> None:
        workspace, receipt, controls = self.fixture("topology-omission")
        child = workspace / ".worktrees/work"
        child.parent.mkdir()
        self.git_write(workspace, "worktree", "add", "--quiet", "-b", "scenario/work", str(child))
        baseline = snapshot_git_topology(workspace, controls, receipt)
        self.git_write(workspace, "worktree", "remove", "--force", str(child))
        observed = observe_git_topology(workspace, controls, receipt, baseline)
        self.assertEqual([row["path"] for row in observed["initial"]["worktrees"]], [".", ".worktrees/work"])
        self.assertEqual([row["path"] for row in observed["current"]["worktrees"]], ["."])

    def test_topology_tolerates_absent_optional_admin_entries_and_rejects_foreign_ones(self) -> None:
        workspace, receipt, controls = self.fixture("topology-admin-entries")
        child = workspace / ".worktrees/work"
        child.parent.mkdir()
        self.git_write(workspace, "worktree", "add", "--quiet", "-b", "scenario/work", str(child))
        admin = workspace / ".git" / "worktrees" / "work"

        # Git materializes only some optional entries here; which ones depends on
        # its version and on the operations that have run, so their absence is a
        # valid layout rather than tampering.
        for name in ("ORIG_HEAD", "logs", "refs"):
            target = admin / name
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
        snapshot_git_topology(workspace, controls, receipt)

        # Anything outside the declared set still fails closed, and the failure
        # names the offending entry instead of only reporting unequal sets.
        (admin / "foreign").write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(GitObservationError, r"undeclared entries: \['foreign'\]"):
            snapshot_git_topology(workspace, controls, receipt)

    def test_topology_rejects_contradictory_baselines_but_allows_current_root_change(self) -> None:
        workspace, receipt, controls = self.fixture("topology-invariants")
        baseline = snapshot_git_topology(workspace, controls, receipt)
        wrong_root = copy.deepcopy(baseline)
        wrong_root["worktrees"][0]["head"] = receipt["baseline_commit"]
        next(row for row in wrong_root["branches"] if row["name"] == "feature")["head"] = receipt["baseline_commit"]
        with self.assertRaisesRegex(GitObservationError, "baseline root"):
            observe_git_topology(workspace, controls, receipt, wrong_root)
        wrong_branch = copy.deepcopy(baseline)
        wrong_branch["branches"][0]["head"] = receipt["baseline_commit"]
        with self.assertRaisesRegex(GitObservationError, "branch table"):
            observe_git_topology(workspace, controls, receipt, wrong_branch)

        (workspace / "README.md").write_text("current root change\n", encoding="utf-8")
        self.git_write(workspace, "add", "README.md")
        self.git_write(workspace, "commit", "--quiet", "--no-gpg-sign", "-m", "current root change")
        observed = observe_git_topology(workspace, controls, receipt, baseline)
        self.assertNotEqual(observed["current"]["worktrees"][0]["head"], receipt["feature_commit"])
        self.assertEqual(observed["current"]["worktrees"][0]["branch"], "feature")
        self.assertEqual(observed["current"]["branches"][0], {
            "name": "feature", "head": observed["current"]["worktrees"][0]["head"],
        })

    def test_gitlink_is_rejected_before_status_can_run_external_fsmonitor(self) -> None:
        workspace, receipt, controls = self.fixture("gitlink-external-marker")
        external, external_head = self.external_repository("external-gitlink")
        marker = self.root / "external-fsmonitor-ran"
        program = self.root / "external-fsmonitor.py"
        self.marker_program(program, marker)
        self.git_write(external, "config", "core.fsmonitor", str(program))
        nested = workspace / "external"
        nested.mkdir()
        (nested / ".git").write_text(f"gitdir: {external / '.git'}\n", encoding="utf-8")
        self.git_write(workspace, "update-index", "--add", "--cacheinfo",
                       f"160000,{external_head},external")

        for operation in (
            lambda: observe_git_state(workspace, controls, receipt),
            lambda: snapshot_git_topology(workspace, controls, receipt),
        ):
            with self.subTest(operation=operation):
                marker.unlink(missing_ok=True)
                with self.assertRaisesRegex(GitObservationError, "gitlink"):
                    operation()
                self.assertFalse(marker.exists(), "external fsmonitor must not execute")

    def test_topology_rejects_external_or_unsafe_dynamic_worktrees_before_git_reads(self) -> None:
        for label in ("external", "symlink-marker", "unsafe-controls"):
            with self.subTest(label=label):
                workspace, receipt, controls = self.fixture("topology-" + label)
                child = workspace / ".worktrees/work"
                child.parent.mkdir()
                self.git_write(workspace, "worktree", "add", "--quiet", "-b", "scenario/work", str(child))
                if label == "external":
                    outside = self.root / "external-worktree"
                    self.git_write(workspace, "worktree", "add", "--quiet", "-b", "scenario/external", str(outside))
                elif label == "symlink-marker":
                    marker = child / ".git"
                    saved = child / ".git.saved"
                    marker.rename(saved)
                    try:
                        marker.symlink_to(saved)
                    except OSError as exc:
                        self.skipTest(f"symlinks unavailable: {exc}")
                else:
                    (workspace / ".git/config").write_text("[core]\n\thooksPath = /unsafe\n", encoding="utf-8")
                with mock.patch.object(observation, "_git") as git, \
                        self.assertRaises(GitObservationError):
                    snapshot_git_topology(workspace, controls, receipt)
                git.assert_not_called()

    def test_topology_rejects_malformed_listing_and_preserves_explicit_empty_current_topology(self) -> None:
        workspace, receipt, controls = self.fixture("topology-malformed")
        baseline = snapshot_git_topology(workspace, controls, receipt)
        self.assertEqual(baseline["worktrees"], [{
            "path": ".", "head": receipt["feature_commit"], "branch": "feature",
            "status": {"clean": True, "tracked_dirty": False, "untracked_dirty": False,
                       "tracked": [], "untracked": []},
        }])
        with mock.patch.object(
            observation, "_worktree_listing",
            return_value={workspace: {"head": receipt["feature_commit"], "branch": "feature"},
                          workspace / ".worktrees/unknown": {"head": receipt["feature_commit"], "branch": "scenario/unknown"}},
        ):
            with self.assertRaisesRegex(GitObservationError, "topology"):
                snapshot_git_topology(workspace, controls, receipt)

    def test_registered_worktrees_are_real_confined_and_relocatable(self) -> None:
        receipts = []
        for name in ("first-topology", "second-topology"):
            root = self.root / name
            plan = self.plan(root)
            plan["git_repository"]["worktrees"] = [
                {"path": ".worktrees/base", "branch": "scenario/base", "revision": "baseline"},
                {"path": ".worktrees/work", "branch": "scenario/work", "revision": "feature"},
            ]
            workspace = root / "workspace"
            workspace.mkdir()
            result = fixture_setup.materialize_workspace(plan, workspace)
            receipts.append(result)
            controls = fixture_setup.snapshot_git_repository_controls(workspace)
            self.assertEqual(fixture_setup.inspect_git_repository(workspace, controls), result["git_repository"])
            listing = subprocess.check_output(["git", "worktree", "list", "--porcelain"], cwd=workspace, text=True)
            for row in result["worktrees"]:
                child = workspace / row["path"]
                self.assertIn("worktree " + str(child.resolve()), listing)
                self.assertIn("branch refs/heads/" + row["branch"], listing)
                self.assertTrue((child / ".git").is_file())
                self.assertEqual(row["head"], result["git_repository"][row["revision"] + "_commit"])
        self.assertEqual(receipts[0], receipts[1])

    def test_registered_worktree_observation_accepts_official_runner_relocation(self) -> None:
        runner = self.root / "runner"
        fixture_root = runner / "fixture"
        plan = self.plan(fixture_root)
        plan["git_repository"]["worktrees"] = [
            {"path": ".worktrees/work", "branch": "scenario/work", "revision": "feature"},
        ]
        workspace = runner / "home/cwd"
        workspace.mkdir(parents=True)
        result = fixture_setup.materialize_workspace(plan, workspace)
        controls = fixture_setup.snapshot_git_repository_controls(workspace)

        sealed = runner / "sealed"
        sealed.mkdir()
        (runner / "home").rename(sealed / "home")
        relocated = sealed / "home/cwd"

        observed = observation.observe_registered_worktrees(
            relocated, controls, result["git_repository"], result["worktrees"],
        )
        self.assertEqual(observed["schema_version"], "native-eval-git-worktrees/v1")
        self.assertEqual(observed["worktrees"][0]["initial"], result["worktrees"][0])
        self.assertEqual(observed["worktrees"][0]["head"], result["worktrees"][0]["head"])
        self.assertTrue(observed["worktrees"][0]["status"]["clean"])

    def test_registered_worktree_observation_rejects_lookalike_relocated_marker(self) -> None:
        runner = self.root / "runner-lookalike"
        fixture_root = runner / "fixture"
        plan = self.plan(fixture_root)
        plan["git_repository"]["worktrees"] = [
            {"path": ".worktrees/work", "branch": "scenario/work", "revision": "feature"},
        ]
        workspace = runner / "home/cwd"
        workspace.mkdir(parents=True)
        result = fixture_setup.materialize_workspace(plan, workspace)
        controls = fixture_setup.snapshot_git_repository_controls(workspace)

        sealed = runner / "sealed"
        sealed.mkdir()
        (runner / "home").rename(sealed / "home")
        relocated = sealed / "home/cwd"
        marker = relocated / ".worktrees/work/.git"
        marker.write_text(
            f"gitdir: {self.root / 'outside/.git/worktrees/work'}\n", encoding="utf-8",
        )

        with self.assertRaisesRegex(GitObservationError, "marker escaped"):
            observation.observe_registered_worktrees(
                relocated, controls, result["git_repository"], result["worktrees"],
            )

    def test_registered_worktree_observation_binds_initial_and_current_state(self) -> None:
        root = self.root / "observed-topology"
        plan = self.plan(root)
        plan["git_repository"]["worktrees"] = [
            {"path": ".worktrees/base", "branch": "scenario/base", "revision": "baseline"},
            {"path": ".worktrees/work", "branch": "scenario/work", "revision": "feature"},
        ]
        workspace = root / "workspace"
        workspace.mkdir()
        result = fixture_setup.materialize_workspace(plan, workspace)
        controls = fixture_setup.snapshot_git_repository_controls(workspace)
        observed = observation.observe_registered_worktrees(
            workspace, controls, result["git_repository"], result["worktrees"],
        )
        self.assertEqual(observed["schema_version"], "native-eval-git-worktrees/v1")
        self.assertEqual(
            [row["initial"] for row in observed["worktrees"]], result["worktrees"],
        )
        self.assertTrue(all(row["status"]["clean"] for row in observed["worktrees"]))
        self.assertEqual(
            [row["head"] for row in observed["worktrees"]],
            [row["head"] for row in result["worktrees"]],
        )

        child = workspace / ".worktrees/work"
        (child / "actor.txt").write_text("changed\n", encoding="utf-8")
        changed = observation.observe_registered_worktrees(
            workspace, controls, result["git_repository"], result["worktrees"],
        )
        self.assertFalse(changed["worktrees"][1]["status"]["clean"])
        self.assertEqual(changed["worktrees"][1]["status"]["untracked"], ["actor.txt"])

    def test_registered_worktree_observation_rejects_escaped_git_marker(self) -> None:
        root = self.root / "escaped-topology"
        plan = self.plan(root)
        plan["git_repository"]["worktrees"] = [
            {"path": ".worktrees/work", "branch": "scenario/work", "revision": "feature"},
        ]
        workspace = root / "workspace"
        workspace.mkdir()
        result = fixture_setup.materialize_workspace(plan, workspace)
        controls = fixture_setup.snapshot_git_repository_controls(workspace)
        outside = self.root / "outside"
        outside.mkdir()
        marker = workspace / ".worktrees/work/.git"
        original_marker = marker.read_text(encoding="utf-8")
        marker.write_text(
            f"gitdir: {outside}\n", encoding="utf-8",
        )
        with self.assertRaisesRegex(GitObservationError, "marker escaped"):
            observation.observe_registered_worktrees(
                workspace, controls, result["git_repository"], result["worktrees"],
            )
        marker.write_text(original_marker, encoding="utf-8")
        admin = Path(original_marker.removeprefix("gitdir: ").strip())
        (admin / "commondir").write_text(str(outside) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(GitObservationError, "common directory is malformed"):
            observation.observe_registered_worktrees(
                workspace, controls, result["git_repository"], result["worktrees"],
            )

    def test_registered_worktree_preflight_rejects_redirects_before_any_git_call(self) -> None:
        def poison(label: str, workspace: Path, outside: Path) -> None:
            marker = workspace / ".worktrees/work/.git"
            admin = Path(marker.read_text(encoding="utf-8").removeprefix("gitdir: ").strip())
            if label == "admin-root":
                root = workspace / ".git/worktrees"
                root.rename(workspace / ".git/worktrees-original")
                root.symlink_to(outside, target_is_directory=True)
            elif label == "admin-entry":
                (workspace / ".git/worktrees/undeclared").mkdir()
            elif label == "child-marker":
                marker.unlink()
                marker.symlink_to(outside / "metadata")
            elif label == "common-HEAD":
                target = workspace / ".git/HEAD"
                target.unlink()
                target.symlink_to(outside / "metadata")
            elif label == "common-refs":
                target = workspace / ".git/refs"
                target.rename(workspace / ".git/refs-original")
                target.symlink_to(outside, target_is_directory=True)
            elif label == "common-commondir":
                (workspace / ".git/commondir").symlink_to(outside / "metadata")
            else:
                target = admin / label
                target.unlink()
                target.symlink_to(outside / "metadata")

        for label in (
            "admin-root", "admin-entry", "child-marker", "commondir", "HEAD", "index",
            "common-HEAD", "common-refs", "common-commondir",
        ):
            with self.subTest(label=label):
                root = self.root / f"preflight-{label}"
                plan = self.plan(root)
                plan["git_repository"]["worktrees"] = [{
                    "path": ".worktrees/work", "branch": "scenario/work", "revision": "feature",
                }]
                workspace = root / "workspace"
                workspace.mkdir()
                result = fixture_setup.materialize_workspace(plan, workspace)
                controls = fixture_setup.snapshot_git_repository_controls(workspace)
                outside = root / "outside"
                outside.mkdir()
                (outside / "metadata").write_text("outside\n", encoding="utf-8")
                poison(label, workspace, outside)
                with mock.patch.object(observation, "_git") as git, \
                        self.assertRaises(GitObservationError):
                    observation.observe_registered_worktrees(
                        workspace, controls, result["git_repository"], result["worktrees"],
                    )
                git.assert_not_called()

    def test_worktree_topology_rejects_unsafe_or_ambiguous_input_before_writes(self) -> None:
        valid = {"path": ".worktrees/task", "branch": "scenario/task", "revision": "feature"}
        invalid = [[], [valid] * 2, [valid] * 5, [{**valid, "extra": True}]]
        invalid.extend([{**valid, "path": path}] for path in ("../escape", "/tmp/escape", ".worktrees/../escape", ".worktrees/a/b", ".git/task"))
        invalid.extend([{**valid, "branch": branch}] for branch in ("main", "feature", "--orphan", "scenario/a..b"))
        invalid.append([{**valid, "revision": "HEAD~1"}])
        for index, rows in enumerate(invalid):
            with self.subTest(rows=rows):
                root = self.root / f"invalid-topology-{index}"
                plan = self.plan(root)
                plan["git_repository"]["worktrees"] = rows
                workspace = root / "workspace"
                workspace.mkdir()
                with self.assertRaises(ValueError):
                    fixture_setup.materialize_workspace(plan, workspace)
                self.assertEqual(list(workspace.iterdir()), [])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeEvalGitObservationTests)
    raise SystemExit(run_counted(suite, label="test-native-eval-git-observation"))
