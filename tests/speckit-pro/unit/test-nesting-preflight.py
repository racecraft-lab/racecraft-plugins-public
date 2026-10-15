#!/usr/bin/env python3
"""Nesting preflight: an observed nested spawn picks the plan-stage mode; depth settings never do (ADR 0026)."""

from __future__ import annotations

import itertools
import ast
import inspect
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
REPO_ROOT = TEST_DIR.parents[2]
sys.path.insert(0, str(TEST_DIR.parent / "lib"))
sys.path.insert(0, str(REPO_ROOT / "speckit-pro"))

from host_skill_views import host_skill_root  # noqa: E402
from runner_invocation import run_runner  # noqa: E402
from script_loader import load_script  # noqa: E402
from test_result import run_counted  # noqa: E402

from speckit_pro_runner.helpers import nesting_preflight  # noqa: E402
from speckit_pro_runner import autopilot_state  # noqa: E402
from speckit_pro_runner.formal import lifecycle  # noqa: E402
from speckit_pro_runner.helpers import plan_stage_terminal  # noqa: E402
from speckit_pro_runner.envelope import RunnerRequest  # noqa: E402
from speckit_pro_runner.atomic_write import AtomicWriteInterrupted, WritePreconditionChanged  # noqa: E402

VALIDATOR = REPO_ROOT / "tests/speckit-pro/layer6-integration/validate-canary-receipt.py"
SCHEMA = json.loads(VALIDATOR.with_name("canary-receipt.schema.json").read_text(encoding="utf-8"))


REQUEST_VARIABLE = "SPECKIT_PLAN_STAGE_MODE"


def setUpModule() -> None:
    # The runner inherits this environment; an operator's own setting must not leak into the cases.
    os.environ.pop(REQUEST_VARIABLE, None)


def resolve(environment: dict[str, str] | None = None, **inputs: object) -> dict:
    """Call the helper through the runner, as the autopilot does; every call must succeed."""
    request = {"schema_version": "1.0", "request_id": "nesting-test", "helper_id": "resolve-nesting-mode",
               "operation": "resolve-nesting-mode", "mode": "read_only", "inputs": inputs}
    completed, response, _ = run_runner(request, extra_env=environment)
    assert completed.returncode == 0, (completed.returncode, response)
    assert response["status"] == "ok", response
    return response["data"]


def apply_probe(root: Path, state_file: str = "autopilot-state.json", **probe: object) -> tuple:
    request = {
        "schema_version": "1.0", "request_id": "nesting-apply-test",
        "helper_id": "resolve-nesting-mode", "operation": "resolve-nesting-mode", "mode": "apply",
        "inputs": {"state_file": state_file, **probe},
    }
    return run_runner(request, cwd=root)


class StateEvidenceTests(unittest.TestCase):
    def test_apply_persists_operator_mode_and_validates_its_complete_evidence(self) -> None:
        validator = load_script("phase_coverage_operator_mode", REPO_ROOT / "speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py")
        cases = (("flat", "allowed", "operator_requested_flat"),
                 ("nested", "allowed", "nested_spawn_allowed"),
                 ("nested", "refused", "nested_spawn_refused"), ("", "allowed", "probe_invalid"))
        for host, (requested, spawn, reason) in itertools.product(("claude-code", "codex"), cases):
            with self.subTest(host=host, requested=requested, spawn=spawn), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / ".specify").mkdir()
                target = root / "autopilot-state.json"
                target.write_text("{}\n", encoding="utf-8")
                with patch.dict(os.environ, {REQUEST_VARIABLE: requested}):
                    completed, result, _ = apply_probe(root, host=host, nested_spawn=spawn)
                self.assertEqual(0, completed.returncode, result)
                state = json.loads(target.read_text(encoding="utf-8"))
                self.assertEqual(reason, state["nesting_mode"]["data"]["reason"])
                self.assertEqual(result, state["nesting_mode"])
                self.assertEqual({"state_status_errors": []}, validator.validate_state_status(state))
                if requested == "flat":
                    state["nesting_mode"]["data"]["requested_mode"] = "nested"
                    self.assertTrue(validator.validate_state_status(state)["state_status_errors"])

    def test_apply_refuses_uuid_request_ids_before_writing(self) -> None:
        private_id = "abcdefab-" + "1234-5678-abcd-" + "0123456789ab"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".specify").mkdir()
            target = root / "autopilot-state.json"
            target.write_text("{}\n", encoding="utf-8")
            request = RunnerRequest("probe-" + private_id, "resolve-nesting-mode", "resolve-nesting-mode", "apply",
                                    {"repo_root": str(root), "state_file": target.name, "host": "codex"})
            with patch.object(nesting_preflight, "resolve_repo_root", return_value=root):
                result = nesting_preflight.apply_nesting_preflight_helper(None, request)
            self.assertEqual("input_error", result["status"])
            self.assertEqual(False, result["data"]["writes_state"])
            self.assertEqual("{}\n", target.read_text(encoding="utf-8"))

    def test_persisted_runner_outcomes_pass_state_validation(self) -> None:
        validator = load_script("nesting_state_validator", REPO_ROOT / "speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py")
        probes = [
            {"nested_spawn": outcome, "configured_depth": depth}
            for outcome in ("allowed", "refused", "not_run") for depth in (0, 3)
        ] + [{}, {"nested_spawn": "unknown"}, {"configured_depth": -1}, {"unexpected": True},
             {"host": "unknown"}, {"host": None}]
        for host in ("claude-code", "codex"):
            for probe in probes:
                with self.subTest(host=host, probe=probe), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    (root / ".git").mkdir()
                    (root / ".specify").mkdir()
                    state_file = root / "autopilot-state.json"
                    state_file.write_text("{}\n", encoding="utf-8")
                    completed, envelope, _ = apply_probe(root, **{"host": host, **probe})
                    self.assertEqual(0, completed.returncode, envelope)
                    state = json.loads(state_file.read_text(encoding="utf-8"))
                    self.assertEqual({"state_status_errors": []}, validator.validate_state_status(state))
                    if probe.get("nested_spawn") == "refused":
                        other_host = "codex" if host == "claude-code" else "claude-code"
                        for prerequisite in (None, "", "wrong host prerequisite", nesting_preflight.PREREQUISITES[other_host]):
                            with self.subTest(prerequisite=prerequisite):
                                state["nesting_mode"]["data"]["prerequisite"] = prerequisite
                                self.assertTrue(validator.validate_state_status(state)["state_status_errors"])

    def test_apply_requires_a_nonempty_request_id_before_writing(self) -> None:
        for host, request_id in itertools.product(("claude-code", "codex"), (None, "", "   ")):
            with self.subTest(host=host, request_id=request_id), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / ".git").mkdir()
                (root / ".specify").mkdir()
                state_file = root / "autopilot-state.json"
                state_file.write_text("{}\n", encoding="utf-8")
                request = {
                    "schema_version": "1.0", "helper_id": "resolve-nesting-mode",
                    "operation": "resolve-nesting-mode", "mode": "apply",
                    "inputs": {"state_file": "autopilot-state.json", "host": host, "nested_spawn": "allowed"},
                }
                if request_id is not None:
                    request["request_id"] = request_id
                completed, envelope, _ = run_runner(request, cwd=root)
                self.assertNotEqual(0, completed.returncode, envelope)
                self.assertEqual("input_error", envelope["status"])
                self.assertEqual("{}\n", state_file.read_text(encoding="utf-8"))


class StatePersistenceTests(unittest.TestCase):
    def test_shared_state_update_preserves_a_competing_writer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            target = root / "autopilot-state.json"
            target.write_text('{"plan": []}', encoding="utf-8")
            newer = '{"plan": ["concurrent progress"]}'
            original = autopilot_state.write_bytes_atomic

            def compete(*args, **kwargs):
                target.write_text(newer, encoding="utf-8")
                return original(*args, **kwargs)

            with patch.object(autopilot_state, "write_bytes_atomic", side_effect=compete):
                with self.assertRaises(WritePreconditionChanged):
                    autopilot_state.update(root, target.name, lambda state: state.update(status="completed"))
            self.assertEqual(newer, target.read_text(encoding="utf-8"))

    def test_write_failures_report_whether_state_may_have_changed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".specify").mkdir()
            request = RunnerRequest("probe", "resolve-nesting-mode", "resolve-nesting-mode", "apply",
                                    {"repo_root": str(root), "state_file": "autopilot-state.json", "host": "codex"})
            for error, changed in ((WritePreconditionChanged("stale"), False), (OSError("write refused"), False),
                                   (AtomicWriteInterrupted("publication uncertain"), True)):
                with self.subTest(error=type(error).__name__), patch.object(nesting_preflight, "resolve_repo_root", return_value=root), patch.object(nesting_preflight, "persist_nesting_mode", side_effect=error):
                    result = nesting_preflight.apply_nesting_preflight_helper(None, request)
                    self.assertEqual("internal_failure", result["status"])
                    self.assertEqual(changed, result["data"]["writes_state"])
                    self.assertEqual("nesting_state_write_failed", result["diagnostics"][0]["code"])

    def test_apply_refuses_an_oversized_state_without_replacing_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".specify").mkdir()
            target = root / "autopilot-state.json"
            content = json.dumps({"notes": "x" * 1_048_576})
            target.write_text(content, encoding="utf-8")
            completed, result, _ = apply_probe(root, host="codex")
            self.assertEqual(2, completed.returncode, result)
            self.assertEqual(content, target.read_text(encoding="utf-8"))

    def test_state_mutations_have_one_owner(self) -> None:
        # A structural contract: none of the three callers may grow another
        # state read/modify/write implementation (AGENTS.md invariant 2).
        for caller in (nesting_preflight.persist_nesting_mode, lifecycle.mirror_checkpoint,
                       plan_stage_terminal.record_pull_request):
            with self.subTest(caller=caller.__name__):
                tree = ast.parse(inspect.getsource(caller))
                calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call)]
                self.assertTrue(any(isinstance(call, ast.Attribute) and isinstance(call.value, ast.Name)
                                    and call.value.id == "autopilot_state" and call.attr == "update"
                                    for call in calls), "state mutations must use the shared owner")

    def test_apply_persists_the_complete_envelope_on_each_host(self) -> None:
        for host in ("claude-code", "codex"):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / ".git").mkdir()
                (root / ".specify").mkdir()
                state_file = root / "autopilot-state.json"
                state_file.write_text(json.dumps({"plan": [], "active_step": "Phase 0"}), encoding="utf-8")
                completed, envelope, _ = apply_probe(root, host=host, nested_spawn="allowed", configured_depth=3)
                self.assertEqual(0, completed.returncode, envelope)
                state = json.loads(state_file.read_text(encoding="utf-8"))
                self.assertEqual("nested", state["nesting_mode"]["data"]["mode"])
                self.assertEqual("nesting-mode/v1", state["nesting_mode"]["data"]["schema_version"])
                self.assertEqual(envelope, state["nesting_mode"])
                self.assertEqual([], state["plan"])
                self.assertEqual("Phase 0", state["active_step"])

    def test_invalid_state_is_refused_without_overwriting_it(self) -> None:
        for content in (None, "{", "[]", '{"plan": [], "plan": [1]}', '{"elapsed": NaN}'):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / ".specify").mkdir()
                target = root / "autopilot-state.json"
                if content is not None:
                    target.write_text(content, encoding="utf-8")
                completed, envelope, _ = apply_probe(root, host="codex", nested_spawn="allowed")
                self.assertEqual(2, completed.returncode, envelope)
                self.assertEqual("nesting_state_invalid", envelope["diagnostics"][0]["code"])
                self.assertEqual(content, target.read_text(encoding="utf-8") if target.exists() else None)

    def test_apply_writes_only_an_autopilot_state_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".specify").mkdir()
            other = root / "package.json"
            other.write_text('{"name": "x"}', encoding="utf-8")
            completed, envelope, _ = apply_probe(root, "package.json", host="codex", nested_spawn="allowed")
            self.assertEqual(2, completed.returncode, envelope)
            self.assertEqual("nesting_state_invalid", envelope["diagnostics"][0]["code"])
            self.assertEqual('{"name": "x"}', other.read_text(encoding="utf-8"))

    def test_apply_refuses_symlinks_and_paths_outside_the_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            (root / ".specify").mkdir(parents=True)
            outside = Path(tmp) / "outside.json"
            outside.write_text('{"keep": true}', encoding="utf-8")
            # Positive control: unsupported apply mode must not look like a
            # working symlink guard merely because every request is refused.
            target = root / "autopilot-state.json"
            target.write_text("{}", encoding="utf-8")
            completed, result, _ = apply_probe(root, host="claude-code", nested_spawn="allowed")
            self.assertEqual(0, completed.returncode, result)
            self.assertEqual("nested", json.loads(target.read_text(encoding="utf-8"))["nesting_mode"]["data"]["mode"])
            target.unlink()
            (root / "autopilot-state.json").symlink_to(outside)
            for path in ("autopilot-state.json", "../outside.json", str(outside)):
                with self.subTest(path=path):
                    completed, envelope, _ = apply_probe(root, path, host="claude-code", nested_spawn="allowed")
                    self.assertEqual(2, completed.returncode, envelope)
                    self.assertEqual('{"keep": true}', outside.read_text(encoding="utf-8"))


class ModeDecisionTests(unittest.TestCase):
    def test_operator_can_hold_a_nest_capable_host_to_flat(self) -> None:
        for host in ("claude-code", "codex"):
            with self.subTest(host=host):
                data = resolve(host=host, nested_spawn="allowed", requested_mode="flat")
                self.assertEqual(("flat", "operator_requested_flat"), (data["mode"], data["reason"]))
                self.assertEqual("flat", data["requested_mode"])
                self.assertIsNone(data["prerequisite"])

    def test_the_runner_reads_the_operator_setting_from_its_environment(self) -> None:
        for host in ("claude-code", "codex"):
            with self.subTest(host=host):
                data = resolve({REQUEST_VARIABLE: "flat"}, host=host, nested_spawn="allowed")
                self.assertEqual(("flat", "operator_requested_flat", "flat"),
                                 (data["mode"], data["reason"], data["requested_mode"]))
        refused = resolve({REQUEST_VARIABLE: "nested"}, host="codex", nested_spawn="refused")
        self.assertEqual(("flat", "nested_spawn_refused"), (refused["mode"], refused["reason"]))
        invalid = resolve({REQUEST_VARIABLE: ""}, host="codex", nested_spawn="allowed")
        self.assertEqual(("flat", "probe_invalid"), (invalid["mode"], invalid["reason"]))

    def test_an_explicit_request_wins_over_the_environment(self) -> None:
        flat = resolve({REQUEST_VARIABLE: "nested"}, host="codex", nested_spawn="allowed", requested_mode="flat")
        self.assertEqual(("flat", "operator_requested_flat", "flat"),
                         (flat["mode"], flat["reason"], flat["requested_mode"]))
        nested = resolve({REQUEST_VARIABLE: "flat"}, host="codex", nested_spawn="allowed", requested_mode="nested")
        self.assertEqual(("nested", "nested"), (nested["mode"], nested["requested_mode"]))

    def test_the_observed_spawn_picks_the_mode_on_each_host(self) -> None:
        expected = {"allowed": ("nested", "nested_spawn_allowed", False), "refused": ("flat", "nested_spawn_refused", True)}
        for host, (outcome, (mode, reason, has_prerequisite)) in itertools.product(("claude-code", "codex"), expected.items()):
            with self.subTest(host=host, outcome=outcome):
                data = resolve(host=host, nested_spawn=outcome)
                self.assertEqual((mode, reason, has_prerequisite), (data["mode"], data["reason"], bool(data["prerequisite"])))

    def test_requesting_nested_still_requires_an_observed_spawn(self) -> None:
        for host in ("claude-code", "codex"):
            answers = [resolve(host=host, nested_spawn=spawn, requested_mode="nested")
                       for spawn in ("allowed", "refused", "not_run")]
            self.assertEqual([
                ("nested", "nested_spawn_allowed", "nested"),
                ("flat", "nested_spawn_refused", "nested"),
                ("flat", "probe_not_run", "nested"),
            ], [(answer["mode"], answer["reason"], answer["requested_mode"]) for answer in answers], host)

    def test_no_override_preserves_the_default_and_records_no_request(self) -> None:
        data = resolve(host="codex", nested_spawn="allowed")
        self.assertEqual(("nested", "nested_spawn_allowed"), (data["mode"], data["reason"]))
        self.assertIsNone(data["requested_mode"])

    def test_a_configured_depth_alone_decides_neither_mode(self) -> None:
        for host, depth in (("claude-code", 3), ("claude-code", 1), ("codex", 2), ("codex", 0)):
            with self.subTest(host=host, depth=depth):
                self.assertEqual("flat", resolve(host=host, nested_spawn="refused", configured_depth=depth)["mode"])
                self.assertEqual("nested", resolve(host=host, nested_spawn="allowed", configured_depth=depth)["mode"])
                self.assertEqual("flat", resolve(host=host, configured_depth=depth)["mode"])

    def test_the_configured_depth_is_recorded_not_decided_on(self) -> None:
        self.assertEqual(3, resolve(host="codex", nested_spawn="refused", configured_depth=3)["configured_depth"])
        self.assertIsNone(resolve(host="codex", nested_spawn="refused")["configured_depth"])

    def test_prerequisites_name_the_setting_each_host_honors(self) -> None:
        claude = resolve(host="claude-code", nested_spawn="refused")["prerequisite"]
        self.assertIn("CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH", claude)
        codex = resolve(host="codex", nested_spawn="refused")["prerequisite"]
        self.assertIn("agents.max_depth", codex)
        self.assertIn("ignored", codex)


class DepthNeverStopsTheRunTests(unittest.TestCase):
    """Every input, however wrong, returns status ok with flat mode; an error would route into recovery."""

    def test_missing_garbled_and_unknown_evidence_degrades_to_flat(self) -> None:
        cases = [
            {}, {"host": "claude-code"}, {"host": "codex", "nested_spawn": "not_run"},
            {"host": "codex", "nested_spawn": "maybe"}, {"host": "codex", "nested_spawn": True},
            {"host": "codex", "nested_spawn": ["allowed"]}, {"host": "gemini", "nested_spawn": "allowed"},
            {"host": "codex", "nested_spawn": "allowed", "configured_depth": "deep"},
            {"host": "codex", "nested_spawn": "allowed", "configured_depth": -4},
            {"host": "codex", "nested_spawn": "allowed", "configured_depth": True},
            {"host": "codex", "nested_spawn": "allowed", "unexpected": 1},
        ]
        for inputs in cases:
            with self.subTest(inputs=inputs):
                data = resolve(**inputs)
                self.assertEqual("flat", data["mode"])
                self.assertIn(data["reason"], {"probe_not_run", "probe_invalid"})
                self.assertIsNone(data["prerequisite"])

    def test_insufficient_depth_is_never_a_stop(self) -> None:
        data = resolve(host="claude-code", nested_spawn="refused", configured_depth=1)
        self.assertEqual("flat", data["mode"])

    def test_malformed_requested_modes_degrade_to_flat(self) -> None:
        for requested in (None, "", "auto", "FLAT", True, 1, ["flat"], {"mode": "flat"}):
            with self.subTest(requested=requested):
                data = resolve(host="codex", nested_spawn="allowed", requested_mode=requested)
                self.assertEqual(("flat", "probe_invalid"), (data["mode"], data["reason"]))
                self.assertIsNone(data["requested_mode"])

    def test_no_stop_policy_label_keys_on_depth(self) -> None:
        for path in (REPO_ROOT / "speckit-pro/speckit_pro_runner/stop_policy.py",
                     REPO_ROOT / "speckit-pro/skills/speckit-autopilot/references/stop-policy.md"):
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("nesting", text, path.name)
            self.assertNotIn("spawn_depth", text, path.name)


class ReceiptModeTests(unittest.TestCase):
    """One source: the runner's mode values are exactly the canary receipt schema's `mode` enum."""

    def test_runner_modes_equal_the_receipt_schema_enum(self) -> None:
        self.assertEqual(set(SCHEMA["properties"]["mode"]["enum"]), set(nesting_preflight.MODES))

    def test_state_evidence_schema_uses_the_runner_version_and_receipt_modes(self) -> None:
        schema_path = REPO_ROOT / "speckit-pro/skills/speckit-autopilot/contracts/autopilot-state-status.schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))["$defs"]["nesting_mode"]["properties"]["data"]
        self.assertEqual(nesting_preflight.SCHEMA_VERSION, data["properties"]["schema_version"]["const"])
        self.assertEqual(set(nesting_preflight.MODES), set(data["properties"]["mode"]["enum"]))

    def test_a_flat_result_records_mode_flat_in_a_receipt(self) -> None:
        validator = load_script("canary_receipt", VALIDATOR)
        for nested_spawn, expected in (("refused", "flat"), ("allowed", "nested"), ("not_run", "flat")):
            with self.subTest(nested_spawn=nested_spawn):
                data = resolve(host="codex", nested_spawn=nested_spawn)
                self.assertEqual(expected, data["mode"])
                failures = validator.json_schema_failures(
                    data["mode"], SCHEMA["properties"]["mode"], SCHEMA, "receipt.mode")
                self.assertEqual([], failures)

    def test_an_operator_flat_answer_is_a_valid_codex_receipt_mode(self) -> None:
        validator = load_script("canary_receipt", VALIDATOR)
        fixtures = load_script("read_only_helper_fixtures", TEST_DIR / "test-speckit-pro-read-only-helpers.py")
        data = resolve(host="codex", nested_spawn="allowed", requested_mode="flat")
        receipt = fixtures.receipt()
        receipt["mode"] = data["mode"]
        self.assertEqual("flat", receipt["mode"])
        self.assertEqual([], validator.validate_receipt(receipt))


class SkillContractTests(unittest.TestCase):
    def test_both_hosts_delegate_nesting_state_persistence_to_the_runner(self) -> None:
        sections = [
            (host_skill_root(host) / "speckit-autopilot" / "SKILL.md").read_text(encoding="utf-8")
            .partition("## Step 1.5: Nesting Preflight")[2].partition("## Step 2:")[0]
            for host in ("claude", "codex")
        ]
        for instruction in ("operation=resolve-nesting-mode mode=apply", "`request_id`", "`state_file`", "The runner writes the complete response"):
            self.assertTrue(all(instruction in section for section in sections), instruction)
        self.assertTrue(all("Persist the complete response" not in section for section in sections))

    def test_both_hosts_leave_the_operator_setting_to_the_runner(self) -> None:
        required = {
            "SKILL.md": ("Do not read `SPECKIT_PLAN_STAGE_MODE`", "runs\nno extra command"),
            "references/prerequisites.md": ("SPECKIT_PLAN_STAGE_MODE=flat", "operator_requested_flat"),
        }
        for host, (relative, phrases) in itertools.product(("claude", "codex"), required.items()):
            document = host_skill_root(host) / "speckit-autopilot" / relative
            for phrase in phrases:
                self.assertIn(phrase, document.read_text(encoding="utf-8"), f"{host}: {relative}")

    def test_both_hosts_run_the_preflight_before_the_main_loop_and_dispatch_flat_otherwise(self) -> None:
        for host in ("claude", "codex"):
            text = (host_skill_root(host) / "speckit-autopilot" / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(host=host):
                self.assertIn("helper_id=resolve-nesting-mode", text)
                prerequisites = (host_skill_root(host) / "speckit-autopilot" / "references" / "prerequisites.md").read_text(encoding="utf-8")
                self.assertIn("resolve-nesting-mode", prerequisites)
                self.assertLess(text.index("## Step 1.5: Nesting Preflight"), text.index("## Step 2: Main Execution Loop"))
                self.assertIn("`data.prerequisite` once", text)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-nesting-preflight"))
