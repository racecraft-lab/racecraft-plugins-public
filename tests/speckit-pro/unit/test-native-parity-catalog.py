#!/usr/bin/env python3
"""Owner tests for the faithful native parity candidate slice."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
CATALOG_PATH = TEST_ROOT / "evals" / "catalog.json"
FIXTURE_ROOT = TEST_ROOT / "evals" / "fixtures" / "parity"
AUDIT_PATH = TEST_ROOT / "evals" / "audit" / "integration-parity-audit.md"
sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_catalog import load_catalog  # noqa: E402
from native_eval_adapters import _git_controller_exclude, _write_git_controller_exclude  # noqa: E402
from native_eval_fixture_setup import (  # noqa: E402
    materialize_workspace,
    snapshot_git_repository_controls,
)
from native_eval_execution import _git_observation_record  # noqa: E402
from native_eval_git_observation import observe_git_state  # noqa: E402
from native_eval_grading import grade_observation  # noqa: E402
from native_eval_pairing import compile_pair_plan, grade_pair  # noqa: E402
from native_eval_runtime import stage_codex_runtime  # noqa: E402
from native_eval_toolchain import prepare_native_toolchain  # noqa: E402
from test_result import run_counted  # noqa: E402


REVIEW_CASE_ID = "parity.01-post-implementation-outcome"
FIXTURE_ID = "01-post-implementation-outcome"
REPORT_PATH = "artifacts/post-implementation-report.md"
SCAFFOLD_CASE_ID = "parity.02-scaffold-relocation-guidance"
SCAFFOLD_REPORT_PATH = "artifacts/parity-02-scaffold-guidance.md"
FUNCTIONAL_CATALOG_PATH = CATALOG_PATH
HELD_CASES = {
    "parity.03-reviewability-backstop": "parity-03-reviewability-backstop",
    "parity.04-stack-manager-guidance": "parity-04-stack-manager-guidance",
}
SPECIFY_INSTALLED = shutil.which("specify") is not None


def one_check_case(case: dict, check: dict) -> dict:
    requirement = next(row for row in case["requirements"] if row["id"] == check["requirement"])
    return {"requirements": [requirement], "checks": [check]}


def observation(
    *, activation: str = "speckit-autopilot", calls: list[dict] | None = None,
    artifacts: dict[str, str] | None = None,
    native_metadata: dict | None = None,
) -> dict:
    return {
        "completed": True,
        "error": None,
        "final_text": "",
        "activations": [activation],
        "tool_calls": calls or [],
        "artifacts": artifacts or {},
        "usage": {},
        "native_metadata": native_metadata or {},
    }


def controller_git_metadata(value: dict) -> dict:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8") + b"\n"
    reference = {
        "path": "raw-git-observation.json",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }
    return {"controller_git_observation": _git_observation_record(payload, reference)}


def fixture_record(row: dict[str, str]) -> dict[str, str]:
    payload = (REPO_ROOT / row["source"]).read_bytes()
    return {**row, "sha256": hashlib.sha256(payload).hexdigest()}


def materialization_plan(case: dict) -> dict:
    return {
        "schema_version": "native-eval-fixtures/v2",
        "source_root": str(REPO_ROOT),
        "fixtures": [fixture_record(row) for row in case["fixtures"]],
        "git_repository": {
            "recipe": case["git_fixture"]["recipe"],
            "baseline": [fixture_record(row) for row in case["git_fixture"]["baseline"]],
        },
    }


class NativeParityCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = load_catalog(CATALOG_PATH, REPO_ROOT)
        cls.cases = {
            case["id"]: case for case in cls.catalog["cases"] if case["layer"] == "parity"
        }
        cls.case = cls.cases[REVIEW_CASE_ID]
        functional = cls.catalog
        cls.active_catalog = functional
        cls.functional_cases = {case["id"]: case for case in functional["cases"]}
        cls.scaffold = cls.functional_cases[SCAFFOLD_CASE_ID]

    def test_nonvacuous_review_candidates_are_authored_and_pair_compile(self) -> None:
        self.assertEqual(set(self.cases), {REVIEW_CASE_ID, SCAFFOLD_CASE_ID})
        self.assertEqual(
            sum(
                case["id"] in {REVIEW_CASE_ID, SCAFFOLD_CASE_ID}
                for case in self.active_catalog["cases"]
            ),
            2,
        )
        self.assertEqual(self.case["layer"], "parity")
        self.assertEqual(self.case["resource_class"], "nested")
        self.assertEqual(self.case["required_tools"], ["specify"])
        self.assertEqual(self.case["git_metadata_access"], "write")
        self.assertEqual(self.case["hosts"]["claude"]["skill"], "speckit-pro:speckit-autopilot")
        self.assertEqual(self.case["hosts"]["codex"]["skill"], "speckit-autopilot")
        self.assertNotIn("speckit-pro:autopilot", json.dumps(self.case))
        prompt = self.case["prompt"]
        self.assertIn("dispatch exactly three host-native workers", prompt)
        self.assertIn("await and consume all three terminal reports", prompt)
        self.assertIn("must not execute any Task 10-14 track action itself", prompt)
        self.assertIn("required workflow.md and sibling autopilot-state.json control updates", prompt)
        self.assertIn("inputs.feature_dir=specs/parity-01", prompt)
        self.assertIn("inputs.workflow_file=workflow.md", prompt)
        self.assertIn("Run every final local gate and checkpoint step serially", prompt)
        self.assertIn("never emit final text while any tool item remains in progress", prompt)
        plan = compile_pair_plan(self.case, REPO_ROOT)
        self.assertEqual(plan["arms"], {"claude": "plugin", "codex": "project"})
        self.assertEqual(plan["declared_artifact_paths"], [REPORT_PATH])
        self.assertEqual(
            plan["checks"][0]["contracts"]["expected_path"],
            f"tests/speckit-pro/evals/fixtures/parity/{FIXTURE_ID}/expected-equivalence.json",
        )
        routing = next(
            check for check in self.case["checks"]
            if check["id"] == "authoritative-routing-evidence"
        )
        self.assertIn("workflow_file=workflow.md", routing["rubric"])
        self.assertIn("after the required workflow and sibling state updates", routing["rubric"])
        scaffold_plan = compile_pair_plan(self.scaffold, REPO_ROOT)
        self.assertEqual(scaffold_plan["arms"], {"claude": "plugin", "codex": "project"})
        self.assertEqual(scaffold_plan["declared_artifact_paths"], [SCAFFOLD_REPORT_PATH])
        self.assertEqual(
            scaffold_plan["checks"][0]["contracts"]["expected_path"],
            "tests/speckit-pro/evals/fixtures/parity/"
            "parity-02-scaffold-relocation-guidance/expected-equivalence.json",
        )

    def test_parity_02_reuses_upgrade_and_autopilot_functional_contracts(self) -> None:
        upgrade = self.functional_cases["functional.speckit-upgrade.case-5"]
        autopilot = self.functional_cases["functional.speckit-autopilot.case-29"]
        self.assertEqual(
            {row["id"] for row in upgrade["requirements"]},
            {"selection", "legacy-01", "legacy-02", "legacy-03", "legacy-04", "legacy-05"},
        )
        self.assertEqual(
            {row["id"] for row in autopilot["requirements"]},
            {"selection", *(f"legacy-{index:02d}" for index in range(1, 10))},
        )
        self.assertIn("migrate-structure", upgrade["capability"])
        self.assertIn("relocate-process-artifacts", upgrade["capability"])
        self.assertIn("only the eligible Tier-2 relocation candidate", autopilot["capability"])

        self.assertEqual(
            {(row["source"], row["destination"]) for row in self.scaffold["fixtures"]},
            {(row["source"], row["destination"]) for row in autopilot["fixtures"]},
        )
        fixture_destinations = {row["destination"] for row in self.scaffold["fixtures"]}
        preserved_sources = {
            check["source"]
            for check in self.scaffold["checks"]
            if check["type"] == "text" and check["source"] in fixture_destinations
        }
        self.assertEqual(preserved_sources, fixture_destinations)
        self.assertEqual(self.scaffold["git_fixture"], {
            "recipe": "baseline-feature-origin-main/v1",
            "baseline": [{
                "source": "tests/speckit-pro/evals/fixtures/parity/"
                "parity-02-scaffold-relocation-guidance/baseline.md",
                "destination": "README.md",
            }],
        })
        self.assertEqual(
            self.scaffold["hosts"]["claude"]["skill"],
            "speckit-pro:speckit-scaffold-spec",
        )
        self.assertEqual(self.scaffold["hosts"]["codex"]["skill"], "speckit-scaffold-spec")
        provenance = set(self.scaffold["provenance"])
        self.assertIn(
            "tests/speckit-pro/layer3-functional/evals/"
            "speckit-scaffold-spec-evals.json#eval-id=1",
            provenance,
        )
        self.assertIn(
            "tests/speckit-pro/layer3-functional/codex-evals/"
            "speckit-scaffold-spec-evals.json#eval-id=8",
            provenance,
        )

    def test_scaffold_prompt_and_inputs_do_not_supply_expected_outcomes(self) -> None:
        prompt = self.scaffold["prompt"]
        fixture_text = "\n".join(
            (REPO_ROOT / row["source"]).read_text(encoding="utf-8")
            for row in self.scaffold["fixtures"]
        )
        for answer in (
            "specs/spec-911-legacy",
            "promotion_status=deferred",
            "thawed_relocatable_process",
            "frozen/in-flight",
            "already-current/already-normalized",
            "non_speckit_namespace",
            "date_named_legacy_namespace",
        ):
            self.assertNotIn(answer, prompt)
            self.assertNotIn(answer, fixture_text)
        self.assertIn("the requested table shape is not an answer key", prompt)

    def test_scaffold_git_observation_distinguishes_exact_final_boundaries(self) -> None:
        def observed(mutate) -> dict:
            with tempfile.TemporaryDirectory(prefix="native-parity-scaffold-git-") as raw_tmp:
                workspace = Path(raw_tmp)
                result = materialize_workspace(materialization_plan(self.scaffold), workspace)
                receipt = result["git_repository"]
                exclude = workspace / ".git" / "info" / "exclude"
                exclude.parent.mkdir(exist_ok=True)
                exclude.write_text("# controller-owned exclusion\n", encoding="utf-8")
                controls = snapshot_git_repository_controls(workspace)
                report = workspace / SCAFFOLD_REPORT_PATH
                report.parent.mkdir(parents=True)
                report.write_text("# Scaffold Relocation Guidance\n", encoding="utf-8")
                mutate(workspace)
                return observe_git_state(workspace, controls, receipt)

        report_only = observed(lambda _workspace: None)
        self.assertEqual(report_only["head"], report_only["initial"]["feature_commit"])
        self.assertEqual(report_only["branch"], "feature")
        self.assertEqual(report_only["commit_count"], 0)
        self.assertEqual(report_only["commits_added"], [])
        self.assertEqual(report_only["changed_tracked_paths_from_initial_feature"], [])
        self.assertEqual(report_only["status"], {
            "clean": False,
            "tracked_dirty": False,
            "untracked_dirty": True,
            "tracked": [],
            "untracked": [SCAFFOLD_REPORT_PATH],
        })

        extra = observed(
            lambda workspace: (workspace / "unexpected.txt").write_text(
                "unexpected\n", encoding="utf-8",
            )
        )
        self.assertEqual(
            extra["status"]["untracked"],
            [SCAFFOLD_REPORT_PATH, "unexpected.txt"],
        )

        def change_inputs(workspace: Path) -> None:
            for relative in (
                ".specify/feature.json",
                "specs/spec-913-current/SPEC-MOC.md",
            ):
                path = workspace / relative
                path.write_text(path.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")

        changed = observed(change_inputs)
        self.assertEqual(changed["status"]["untracked"], [SCAFFOLD_REPORT_PATH])
        self.assertEqual(changed["status"]["tracked"], [
            {"path": ".specify/feature.json", "index": " ", "worktree": "M"},
            {"path": "specs/spec-913-current/SPEC-MOC.md", "index": " ", "worktree": "M"},
        ])

        def remove_original(workspace: Path) -> None:
            (workspace / "specs/spec-911-legacy/analysis.md").unlink()

        missing = observed(remove_original)
        self.assertEqual(missing["status"]["tracked"], [{
            "path": "specs/spec-911-legacy/analysis.md",
            "index": " ",
            "worktree": "D",
        }])

        boundary = next(
            check for check in self.scaffold["checks"] if check["id"] == "preservation-boundary"
        )
        for host in ("claude", "codex"):
            with self.subTest(host=host, state="report-only"):
                result = grade_observation(
                    one_check_case(self.scaffold, boundary),
                    observation(native_metadata=controller_git_metadata(report_only)),
                    host=host,
                )
                self.assertEqual(result["status"], "pass", result)
            for label, actual in (
                ("extra-untracked", extra),
                ("altered-tracked", changed),
                ("deleted-original", missing),
            ):
                with self.subTest(host=host, state=label):
                    result = grade_observation(
                        one_check_case(self.scaffold, boundary),
                        observation(native_metadata=controller_git_metadata(actual)),
                        host=host,
                    )
                    self.assertEqual(result["status"], "fail", result)
            with self.subTest(host=host, state="missing-controller-record"):
                result = grade_observation(
                    one_check_case(self.scaffold, boundary), observation(), host=host,
                )
                self.assertEqual(result["status"], "invalid", result)

    def test_forbidden_invocation_pattern_ignores_benign_searches(self) -> None:
        checks = {
            check["name"]: check
            for check in self.scaffold["checks"]
            if check["id"] in {"no-claude-relocation-command", "no-codex-relocation-command"}
        }
        for tool_name, check in checks.items():
            with self.subTest(tool=tool_name):
                benign = observation(
                    activation="speckit-scaffold-spec",
                    calls=[{
                        "name": tool_name,
                        "input": {
                            "command": "rg 'dry_run|apply|relocate-process-artifacts' speckit-pro",
                        },
                        "output": "source references",
                        "success": True,
                    }],
                )
                self.assertEqual(
                    grade_observation(one_check_case(self.scaffold, check), benign)["status"],
                    "pass",
                )
                attempted = observation(
                    activation="speckit-scaffold-spec",
                    calls=[{
                        "name": tool_name,
                        "input": {"command": "./relocate-process-artifacts.sh apply"},
                        "output": "not found",
                        "success": False,
                    }],
                )
                self.assertEqual(
                    grade_observation(one_check_case(self.scaffold, check), attempted)["status"],
                    "fail",
                )

    def test_scaffold_pair_requires_independent_correctness_before_comparison(self) -> None:
        report = """# Scaffold Relocation Guidance

## Capability

| Operation | Promotion Status | Authoritative Request | Runner Modes | Action |
|---|---|---|---|---|
| relocate-process-artifacts | deferred | none | unavailable | report capability gap; preserve artifacts; remaining scaffolding may continue under its normal prerequisites |

## Classification

| Spec | Decision | Reason |
|---|---|---|
| specs/spec-911-legacy | candidate | thawed_relocatable_process |
| specs/spec-912-active | suppress | frozen/in-flight |
| specs/spec-913-current | suppress | already-current/already-normalized |
| specs/spec-914-empty | suppress | no-candidate |
| specs/team-123-legacy | suppress | non_speckit_namespace |
| specs/2026-06-legacy | suppress | date_named_legacy_namespace |

## No Auto-Run

| Surface | Status |
|---|---|
| scaffold | no operation invoked |
"""
        with tempfile.TemporaryDirectory(prefix="native-parity-scaffold-grade-") as raw_tmp:
            workspace = Path(raw_tmp)
            result = materialize_workspace(materialization_plan(self.scaffold), workspace)
            receipt = result["git_repository"]
            exclude = workspace / ".git" / "info" / "exclude"
            exclude.parent.mkdir(exist_ok=True)
            exclude.write_text("# controller-owned exclusion\n", encoding="utf-8")
            controls = snapshot_git_repository_controls(workspace)
            report_path = workspace / SCAFFOLD_REPORT_PATH
            report_path.parent.mkdir(parents=True)
            report_path.write_text(report, encoding="utf-8")
            git_state = observe_git_state(workspace, controls, receipt)
            artifacts = {
                row["destination"]: (workspace / row["destination"]).read_text(encoding="utf-8")
                for row in self.scaffold["fixtures"]
            }
            artifacts[SCAFFOLD_REPORT_PATH] = report_path.read_text(encoding="utf-8")
        calls_by_host = {
            "claude": [{
                "name": "Read",
                "input": {"file_path": row["destination"]},
                "output": artifacts[row["destination"]],
                "success": True,
            } for row in self.scaffold["fixtures"]],
            "codex": [{
                "name": "command_execution",
                "input": {"command": f"cat -- {row['destination']}"},
                "output": artifacts[row["destination"]],
                "success": True,
            } for row in self.scaffold["fixtures"]],
        }
        git_metadata = controller_git_metadata(git_state)
        semantic_ids = {
            check["id"] for check in self.scaffold["checks"] if check["type"] == "semantic"
        }
        passing_verdicts = {
            check_id: {"passed": True, "evidence": [f"observation/{check_id}"]}
            for check_id in semantic_ids
        }
        grades = {}
        for host in ("claude", "codex"):
            grades[host] = grade_observation(
                self.scaffold,
                observation(
                    activation="speckit-scaffold-spec",
                    calls=calls_by_host[host],
                    artifacts=artifacts,
                    native_metadata=git_metadata,
                ),
                passing_verdicts,
                host=host,
            )
            self.assertEqual(grades[host]["status"], "pass", grades[host])

        plan = compile_pair_plan(self.scaffold, REPO_ROOT)

        def arm(host: str, grade: dict, arm_artifacts: dict[str, str]) -> dict:
            index = 1 if host == "claude" else 2
            return {
                "case_id": SCAFFOLD_CASE_ID,
                "host": host,
                "mode": "plugin" if host == "claude" else "project",
                "trial": 1,
                "input_fingerprint": str(index) * 64,
                "capture_sha256": chr(ord("a") + index) * 64,
                "grade_identity": chr(ord("c") + index) * 64,
                "grade_sha256": ("f" if host == "claude" else "0") * 64,
                "grade": grade,
                "observation": {"artifacts": arm_artifacts},
            }

        passing = grade_pair(
            self.scaffold,
            plan,
            [arm("claude", grades["claude"], artifacts), arm("codex", grades["codex"], artifacts)],
        )
        self.assertEqual(passing["status"], "pass", passing)

        wrong = report.replace("deferred", "available", 1)
        wrong_artifacts = {**artifacts, SCAFFOLD_REPORT_PATH: wrong}
        failing_verdicts = {
            check_id: {
                "passed": check_id != "capability-correctness",
                "evidence": [f"observation/{check_id}"],
            }
            for check_id in semantic_ids
        }
        failing_grades = {
            host: grade_observation(
                self.scaffold,
                observation(
                    activation="speckit-scaffold-spec",
                    calls=calls_by_host[host],
                    artifacts=wrong_artifacts,
                    native_metadata=git_metadata,
                ),
                failing_verdicts,
                host=host,
            )
            for host in ("claude", "codex")
        }
        self.assertTrue(all(grade["status"] == "fail" for grade in failing_grades.values()))
        same_wrong = grade_pair(
            self.scaffold,
            plan,
            [
                arm("claude", failing_grades["claude"], wrong_artifacts),
                arm("codex", failing_grades["codex"], wrong_artifacts),
            ],
        )
        self.assertEqual(same_wrong["status"], "fail")
        self.assertIn("independent grade failed", same_wrong["checks"][0]["reason"])

        forbidden_call = [{
            "name": "Bash",
            "input": {"command": "relocate-process-artifacts apply"},
            "output": "permission denied",
            "success": False,
        }]
        unsafe = grade_observation(
            self.scaffold,
            observation(
                activation="speckit-scaffold-spec",
                calls=[*calls_by_host["claude"], *forbidden_call],
                artifacts=artifacts,
                native_metadata=git_metadata,
            ),
            passing_verdicts,
            host="claude",
        )
        self.assertEqual(unsafe["status"], "fail")

    def test_post_case_materializes_a_clean_nonempty_git_diff_and_allows_local_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory(prefix="native-parity-post-") as raw_tmp:
            workspace = Path(raw_tmp)
            result = materialize_workspace(materialization_plan(self.case), workspace)
            receipt = result["git_repository"]
            self.assertTrue(receipt["clean"] and receipt["nonempty_diff"])
            self.assertEqual(receipt["branch"], "feature")
            self.assertNotEqual(receipt["head"], receipt["origin_main"])
            self.assertEqual(
                json.loads((workspace / ".specify" / "feature.json").read_text(encoding="utf-8")),
                {"feature_directory": "specs/parity-01"},
            )

            git = shutil.which("git")
            self.assertIsNotNone(git)
            diff = subprocess.run(
                [git, "diff", "--name-only", "origin/main...HEAD"], cwd=workspace,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
            ).stdout.splitlines()
            self.assertEqual(set(diff), {row["destination"] for row in self.case["fixtures"]})

            workflow = workspace / "workflow.md"
            workflow.write_text(workflow.read_text(encoding="utf-8") + "\nLocal checkpoint prepared.\n", encoding="utf-8")
            subprocess.run([git, "add", "workflow.md"], cwd=workspace, check=True)
            subprocess.run(
                [git, "-c", "user.name=Native Eval", "-c", "user.email=native-eval@example.invalid",
                 "-c", "commit.gpgsign=false",
                 "commit", "--quiet", "-m", "test local checkpoint"],
                cwd=workspace, check=True,
            )
            self.assertFalse(subprocess.run(
                [git, "status", "--porcelain=v1"], cwd=workspace,
                text=True, stdout=subprocess.PIPE, check=True,
            ).stdout)
            self.assertEqual(subprocess.run(
                [git, "rev-list", "--count", f"{receipt['feature_commit']}..HEAD"], cwd=workspace,
                text=True, stdout=subprocess.PIPE, check=True,
            ).stdout.strip(), "1")

    def test_initial_helpers_prove_real_additive_route_and_layer_fixture(self) -> None:
        with tempfile.TemporaryDirectory(prefix="native-parity-gates-") as raw_tmp:
            root = Path(raw_tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            fixture_result = materialize_workspace(materialization_plan(self.case), workspace)
            _write_git_controller_exclude(
                workspace,
                _git_controller_exclude(fixture_result, host="codex"),
            )
            runtime = stage_codex_runtime(REPO_ROOT, root / "build", workspace)
            toolchain = prepare_native_toolchain(workspace, required_tools=["specify"])
            environment = dict(os.environ)
            environment.update(toolchain.environment)
            environment["PYTHONPATH"] = runtime.pythonpath
            environment["PYTHONSAFEPATH"] = "1"
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            environment["PATH"] = os.pathsep.join(
                [*(str(path) for path in toolchain.path_entries), environment.get("PATH", "")]
            )

            specify = subprocess.run(
                [str(toolchain.launchers["specify"]), "--version"],
                cwd=workspace,
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(specify.returncode, 0, specify.stderr)
            self.assertEqual(
                specify.stdout.strip(),
                toolchain.runtime_identity["tools"]["specify"]["version"],
            )

            def run(
                helper_id: str,
                inputs: dict,
                *,
                expected_returncode: int = 0,
                expected_status: str = "ok",
            ) -> dict:
                request = {
                    "schema_version": "1.0",
                    "request_id": f"parity-01-{helper_id}",
                    "helper_id": helper_id,
                    "operation": helper_id,
                    "mode": "read_only",
                    "inputs": inputs,
                }
                completed = subprocess.run(
                    [sys.executable, "-B", "-m", "speckit_pro_runner"],
                    input=json.dumps(request),
                    cwd=workspace,
                    env=environment,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(
                    completed.returncode,
                    expected_returncode,
                    f"stderr={completed.stderr}\nstdout={completed.stdout}",
                )
                response = json.loads(completed.stdout)
                self.assertEqual(response["status"], expected_status, response)
                return response["data"]["stdout_json"]

            binding = run("resolve-workflow-binding", {"workflow_file": "workflow.md"})
            self.assertEqual(binding["binding_status"], "resolved")
            self.assertEqual(binding["relation"], "same")

            prerequisites = run(
                "check-prerequisites",
                {"workflow_file": "workflow.md"},
                expected_returncode=1,
                expected_status="expected_failure",
            )
            self.assertFalse(prerequisites["all_pass"], prerequisites)
            self.assertTrue(prerequisites["on_feature_branch"])
            self.assertFalse(prerequisites["is_worktree"])
            self.assertEqual(prerequisites["branch"], "feature")
            checks = {row["check"]: row for row in prerequisites["checks"]}
            self.assertTrue(checks["speckit_cli"]["pass"])
            self.assertFalse(checks["commands"]["pass"])
            self.assertIn(
                "Missing commands: speckit-specify speckit-plan speckit-tasks speckit-implement",
                checks["commands"]["message"],
            )

            stage = run(
                "resolve-autopilot-stage",
                {"workflow_file": "workflow.md", "autopilot_args": ["--stage", "implement"]},
            )
            self.assertEqual(stage["stage"], "implement")
            self.assertEqual(stage["source"], "argv")
            self.assertEqual(stage["basis"], "explicit --stage implement")

            workflow = workspace / "workflow.md"
            workflow.write_text(
                workflow.read_text(encoding="utf-8") + "\nRoute pending.\n",
                encoding="utf-8",
            )
            (workspace / "autopilot-state.json").write_text("{}\n", encoding="utf-8")
            route = run(
                "atomicity-route",
                {
                    "feature_dir": "specs/parity-01",
                    "workflow_file": "workflow.md",
                },
            )
            self.assertEqual(route["route"], "split-PR")
            self.assertTrue(route["releasable"])
            self.assertEqual(route["signals"], [
                "change-shape:additive-only",
                "topology:independent-multi-seam",
                "source-proof:direct-python-imports-only",
            ])

            planner = run("plan-layers-feature-dir", {"feature_dir": "specs/parity-01"})
            self.assertEqual(planner["status"], "ok", planner)
            self.assertEqual(planner["errors"], [])
            self.assertEqual(planner["warnings"], [])
            self.assertEqual(
                [(row["id"], row["depends_on"]) for row in planner["increments"]],
                [("us1", []), ("us2", [])],
            )
            self.assertEqual(
                [row["files"] for row in planner["increments"]],
                [["src/capability_alpha.py"], ["src/capability_beta.py"]],
            )
            self.assertEqual(
                [row["tests"] for row in planner["increments"]],
                [["tests/test_capability_alpha.py"], ["tests/test_capability_beta.py"]],
            )

    def test_checkpoint_contract_matches_shipped_post_contract(self) -> None:
        source = (
            REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot"
            / "references" / "post-implementation.md"
        ).read_text(encoding="utf-8")
        skill = (
            REPO_ROOT / "speckit-pro" / "skills" / "speckit-autopilot" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("current committed evidence", source)
        self.assertIn("Commit or otherwise checkpoint the packet/body", source)
        self.assertIn("mutation helper intentionally rejects a dirty worktree", source)
        self.assertIn('git commit -m "docs(SPEC-XXX): add UAT runbook"', source)
        self.assertIn("phase 7:    git add -A && git commit", skill)

        safety = next(check["rubric"] for check in self.case["checks"] if check["id"] == "mutation-boundary")
        self.assertIn("one or more local commits", safety)
        self.assertIn("controller Git observation", safety)
        self.assertIn("there is no push", safety)
        request_path = ".process/execution-control/native-eval-execute-verification-request.json"
        self.assertIn(request_path, self.case["prompt"])
        self.assertIn(request_path, safety)
        self.assertIn("Delete that transient request immediately", self.case["prompt"])
        self.assertIn("do not create or pass a changed-files evidence file", self.case["prompt"])
        self.assertIn("without a changed-files evidence file", safety)
        self.assertNotIn("no commit", safety)
        forbidden = [
            check for check in self.case["checks"]
            if check["id"].endswith("external-mutation-attempt")
        ]
        self.assertEqual({check["name"] for check in forbidden}, {"Bash", "command_execution"})
        self.assertTrue(all(check["min"] == check["max"] == 0 for check in forbidden))
        self.assertTrue(all(check["include_failed"] is True for check in forbidden))
        combined = "\n".join(
            (FIXTURE_ROOT / FIXTURE_ID / name).read_text(encoding="utf-8")
            for name in ("workflow.md", "spec.md", "plan.md", "tasks.md")
        )
        self.assertIn("Local commits are required checkpoints", combined)
        self.assertIn(request_path, combined)
        self.assertIn(
            "Do not create or pass a changed-files evidence file",
            " ".join(combined.split()),
        )
        self.assertIn("pushes and all PR mutations remain forbidden", " ".join(combined.split()))

    def test_route_and_verification_answers_are_not_staged_as_fixture_evidence(self) -> None:
        destinations = {row["destination"] for row in self.case["fixtures"]}
        self.assertNotIn(
            "specs/parity-01/.process/emission/verification-pointer.json",
            destinations,
        )
        staged_records = [*self.case["fixtures"], *self.case["git_fixture"]["baseline"]]
        staged_text = "\n".join(
            (REPO_ROOT / row["source"]).read_text(encoding="utf-8")
            for row in staged_records
            if (REPO_ROOT / row["source"]).suffix in {".md", ".json", ".py"}
        )
        self.assertNotIn("split-PR", staged_text)
        self.assertNotIn('"status":"ok"', staged_text)
        self.assertNotIn("native-eval-verification-pointer/v1", staged_text)

    def test_real_verification_result_can_bind_a_feature_emission_pointer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="native-parity-verification-") as raw_tmp:
            root = Path(raw_tmp)
            workspace = root / "workspace"
            workspace.mkdir()
            materialize_workspace(materialization_plan(self.case), workspace)
            runtime = stage_codex_runtime(REPO_ROOT, root / "build", workspace)
            environment = dict(os.environ)
            environment["PYTHONPATH"] = runtime.pythonpath
            environment["PYTHONSAFEPATH"] = "1"
            environment["PYTHONDONTWRITEBYTECODE"] = "1"

            def request(helper: str, mode: str, inputs: dict) -> dict:
                payload = {
                    "schema_version": "1.0",
                    "request_id": f"parity-01-{helper}",
                    "helper_id": helper,
                    "operation": helper,
                    "mode": mode,
                    "inputs": inputs,
                }
                completed = subprocess.run(
                    [sys.executable, "-B", "-m", "speckit_pro_runner"],
                    input=json.dumps(payload), cwd=workspace, env=environment,
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
                )
                self.assertEqual(
                    completed.returncode, 0,
                    f"stderr={completed.stderr}\nstdout={completed.stdout}",
                )
                response = json.loads(completed.stdout)
                self.assertEqual(response["status"], "ok", response)
                return response["data"]

            started = request(
                "execution-control", "apply",
                {"workflow_file": "workflow.md", "action": "start"},
            )
            run_id = started["ledger"]["run_id"]
            ledger_path = started["ledger_path"]
            request(
                "execution-control", "apply",
                {
                    "workflow_file": "workflow.md", "action": "reserve",
                    "dispatch_id": "parity-verify", "kind": "verification",
                    "expected_run_id": run_id, "ledger_path": ledger_path,
                },
            )
            executed = request(
                "execute-verification", "apply",
                {
                    "workflow_file": "workflow.md", "command_id": "INTEGRATION_TEST",
                    "dispatch_id": "parity-verify", "expected_run_id": run_id,
                    "ledger_path": ledger_path,
                },
            )

            record_path = executed["record_path"]
            self.assertRegex(record_path, r"^\.process/verification/[0-9a-f]{32}\.json$")
            record_bytes = (workspace / record_path).read_bytes()
            record = json.loads(record_bytes)
            self.assertEqual(record, executed["record"])
            self.assertEqual(record["command_id"], "INTEGRATION_TEST")
            self.assertEqual(record["argv"], ["python3", "specs/parity-01/verify.py"])
            self.assertEqual(record["exit_code"], 0)
            self.assertTrue(record["completed"])
            self.assertTrue(record["inputs_unchanged"])
            self.assertTrue(record["snapshot_unchanged"])
            self.assertEqual(record["isolation_mode"], "copy_only")
            self.assertFalse(executed["reusable"])
            self.assertTrue(executed["rerun_required"])

            pointer = {
                "schema_version": "native-eval-verification-pointer/v1",
                "record_path": record_path,
                "record_sha256": hashlib.sha256(record_bytes).hexdigest(),
                "execution_id": record["execution_id"],
                "command_id": record["command_id"],
                "snapshot_sha256": record["snapshot_sha256"],
                "reusable": executed["reusable"],
                "isolation_mode": record["isolation_mode"],
            }
            pointer_path = (
                workspace / "specs/parity-01/.process/emission/verification-pointer.json"
            )
            pointer_path.parent.mkdir(parents=True)
            pointer_path.write_text(
                json.dumps(pointer, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
            )
            captured = json.loads(pointer_path.read_text(encoding="utf-8"))

            def is_bound(value: dict) -> bool:
                return value == {
                    "schema_version": "native-eval-verification-pointer/v1",
                    "record_path": record_path,
                    "record_sha256": hashlib.sha256(record_bytes).hexdigest(),
                    "execution_id": executed["record"]["execution_id"],
                    "command_id": "INTEGRATION_TEST",
                    "snapshot_sha256": executed["record"]["snapshot_sha256"],
                    "reusable": False,
                    "isolation_mode": "copy_only",
                }

            self.assertTrue(is_bound(captured))

            for field, wrong in (
                ("record_path", ".process/verification/" + "0" * 32 + ".json"),
                ("record_sha256", "0" * 64),
                ("execution_id", "0" * 32),
                ("snapshot_sha256", "0" * 64),
                ("reusable", True),
            ):
                with self.subTest(field=field):
                    self.assertFalse(is_bound({**captured, field: wrong}))

    def test_report_is_declared_output_and_deterministic_checks_fail_without_evidence(self) -> None:
        destinations = {row["destination"] for row in self.case["fixtures"]}
        self.assertNotIn(REPORT_PATH, destinations)
        declared = {
            check.get("path") or check.get("source")
            for check in self.case["checks"]
            if check["type"] in {"file_exists", "text"}
        }
        self.assertIn(REPORT_PATH, declared)
        for check in self.case["checks"]:
            if check["type"] == "semantic":
                continue
            tested = observation()
            if check["type"] == "selection":
                tested = observation(activation="wrong-skill")
            elif check["type"] == "tool_used" and check["max"] == 0:
                tested = observation(calls=[{
                    "name": check["name"],
                    "input": {"cmd": "git push origin feature"},
                    "output": "blocked",
                    "success": False,
                }])
            result = grade_observation(one_check_case(self.case, check), tested)
            self.assertIn(result["status"], {"fail", "invalid"}, (check["id"], result))

    def test_independent_failure_blocks_pair_comparison(self) -> None:
        plan = compile_pair_plan(self.case, REPO_ROOT)
        report = (
            "## Outcome\n\n| Status | Decision | Evidence |\n|---|---|---|\n"
            "| CHECKPOINTED | stopped before PR creation | retained native evidence |\n"
        )
        arms = []
        for index, (host, mode) in enumerate((("claude", "plugin"), ("codex", "project"))):
            arms.append({
                "case_id": REVIEW_CASE_ID,
                "host": host,
                "mode": mode,
                "trial": 1,
                "input_fingerprint": str(index + 1) * 64,
                "capture_sha256": chr(ord("a") + index) * 64,
                "grade_identity": chr(ord("c") + index) * 64,
                "grade_sha256": chr(ord("e") + index) * 64,
                "grade": {"status": "fail"},
                "observation": {"artifacts": {REPORT_PATH: report}},
            })
        result = grade_pair(self.case, plan, arms)
        self.assertEqual(result["status"], "fail")
        self.assertNotIn("semantic_request", result)
        self.assertIn("independent grade failed", result["checks"][0]["reason"])

    def test_vacuous_policy_reimplementations_are_absent_and_uncovered_cases_remain_held(self) -> None:
        authored = json.dumps(self.catalog)
        audit = AUDIT_PATH.read_text(encoding="utf-8")
        audit = audit.split("## Four-case parity catalog slice", 1)[1].split("\n## ", 1)[0]
        for case_id, legacy_id in HELD_CASES.items():
            self.assertNotIn(case_id, self.cases)
            self.assertIn(legacy_id, audit)
        for directory in (
            "02-repository-migration-guidance",
            "03-reviewability-backstop",
            "04-stack-manager-guidance",
        ):
            held_fixture = FIXTURE_ROOT / directory
            self.assertFalse(held_fixture.exists() and any(held_fixture.iterdir()))
        for invented in ("parity_migration_policy.py", "parity_reviewability_policy.py", "parity_stack_policy.py"):
            self.assertNotIn(invented, authored)
        self.assertIn("vacuous reimplementation", audit)
        self.assertIn("functional.speckit-upgrade.case-5", audit)
        self.assertIn("functional.speckit-autopilot.case-29", audit)
        self.assertIn(SCAFFOLD_CASE_ID, audit)
        self.assertIn("check-prerequisites", audit)
        self.assertIn("specs/parity-01/.process/emission/", audit)
        self.assertIn("plan-layers", audit)

    def test_legacy_boundary_and_teams_amendment_remain_explicit(self) -> None:
        authored = json.dumps(self.catalog)
        self.assertTrue(any("parity-01-post-impl" in source for source in self.case["provenance"]))
        for obsolete in ("TeamCreate", "TeamDelete", "env-teams.json", '"teams"'):
            self.assertNotIn(obsolete, authored)
        self.assertIn("interactive claude teams are outside", authored.lower())


if not SPECIFY_INSTALLED:
    # The counted suite treats a skip as a failed unit, so remove this
    # installed-tool test on runners without Specify rather than reporting a
    # vacuous skip. It still runs wherever the real toolchain is installed.
    del NativeParityCatalogTests.test_initial_helpers_prove_real_additive_route_and_layer_fixture


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeParityCatalogTests)
    raise SystemExit(run_counted(suite, label="test-native-parity-catalog"))
