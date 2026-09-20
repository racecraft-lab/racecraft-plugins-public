#!/usr/bin/env python3
"""Native evaluation execution preserves evidence and never inflates passes."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest import mock
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import native_eval_execution as execution
from native_eval_catalog import NATIVE_SYNTHESIS_MECHANISMS
from native_eval_capture import file_accesses
from native_eval_codex_rollouts import NativeRolloutInvalid
from native_eval_execution import run_evaluations
from test_result import run_counted


SKILL_CANARY = """---
name: native-eval-canary
description: Read the canary fixture and create its verification receipt when explicitly asked to exercise native-eval-canary.
---

Read fixture.txt in the working directory. Create receipt.txt with exactly the same content using a native file-editing tool. Reply CANARY_DONE after the write succeeds. Do not access unrelated files or use network tools.
"""
FIXTURE_READ_PATH = "fixture.txt"
FIXTURE_READ_BODY = "alpha\nbeta\n"
CLAUDE_SESSION = str(uuid.UUID(int=101))
CLAUDE_PROMPT_ID = str(uuid.UUID(int=102))
CLAUDE_COMMAND_ID = str(uuid.UUID(int=103))
CLAUDE_INJECTION_ID = str(uuid.UUID(int=104))
CLAUDE_MANUAL_SKILL = "fixture-plugin:static-skill"
CLAUDE_MANUAL_BODY = b"\n# Static skill\n\nAnswer the bounded request.\n"
CLAUDE_MANUAL_SOURCE = (
    b"---\nname: static-skill\ndescription: synthetic manual skill\n"
    b"user-invocable: true\ndisable-model-invocation: true\n---\n"
    + CLAUDE_MANUAL_BODY
)


def skill_witness(name, text):
    encoded = text.encode("utf-8")
    return {
        "path": f".agents/skills/{name}/SKILL.md", "text": text,
        "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def fixture_read_witness(body=FIXTURE_READ_BODY):
    encoded = body.encode("utf-8")
    return {FIXTURE_READ_PATH: {
        "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest(),
    }}


def case(*, semantic=False, resource_class="ordinary", pattern="done"):
    checks = [{"id": "text", "requirement": "r1", "type": "text", "source": "final_text", "pattern": pattern}]
    if semantic:
        checks.append({"id": "meaning", "requirement": "r1", "type": "semantic", "rubric": "The answer is useful."})
    return {
        "id": "case.one", "layer": "functional", "capability": "test", "prompt": "perform the test",
        "fixtures": [], "timeout_seconds": 30, "resource_class": resource_class,
        "requirements": [{"id": "r1", "description": "test"}], "checks": checks,
        "hosts": {
            "claude": {"skill": None, "allowed_tools": [], "modes": ["plugin"]},
            "codex": {"skill": None, "allowed_tools": [], "modes": ["project"]},
        },
    }


def fixture_read_case():
    value = case()
    value["checks"].append({
        "id": "fixture-read", "requirement": "r1", "type": "file_access",
        "operation": "read_file", "path": FIXTURE_READ_PATH,
    })
    return value


def claude_activation_case():
    value = case()
    value["prompt"] = "Use {{skill}} to perform the test"
    value["hosts"]["claude"]["skill"] = CLAUDE_MANUAL_SKILL
    value["checks"].append({
        "id": "selection", "requirement": "r1", "type": "selection",
        "expected": ["static-skill"], "allowed_extra": [],
    })
    return value


def causal_case(path="result.txt"):
    value = case(resource_class="nested")
    value["checks"].extend([
        {"id": "subagent", "requirement": "r1", "type": "tool_used",
         "name": "subagent", "min": 1, "max": 1},
        {"id": "causal", "requirement": "r1",
         "type": "subagent_returns_before_parent_file_change", "path": path},
    ])
    return value


def dispatch_case():
    value = case(resource_class="nested")
    value["checks"].append({
        "id": "dispatch", "requirement": "r1", "type": "native_subagent_dispatch",
        "expected": [{"item_id": "dispatch-i1", "role": "codebase-analyst"}],
        "forbidden_roles": ["domain-researcher", "spec-context-analyst"],
    })
    return value


def verification_case():
    value = case()
    value["checks"].append({
        "id": "verification", "requirement": "r1",
        "type": "native_verification_pointer", "workflow_file": "workflow.md",
        "command_id": "INTEGRATION_TEST",
        "pointer_path": "specs/parity-01/.process/emission/verification-pointer.json",
        "reusable": False,
    })
    return value


def claude_verification_case():
    value = verification_case()
    value["prompt"] = "Use {{skill}} to perform the test"
    value["hosts"]["claude"]["skill"] = CLAUDE_MANUAL_SKILL
    return value


RUNNER_REQUEST_PATH = "scenario-inputs/binding-request.json"


def runner_request():
    return {
        "schema_version": "1.0", "request_id": "workflow-binding-preflight",
        "helper_id": "resolve-workflow-binding",
        "operation": "resolve-workflow-binding", "mode": "read_only",
        "inputs": {"workflow_file": "docs/ai/specs/.process/SPEC-107-workflow.md"},
    }


def runner_result_case():
    value = case(pattern="binding.result")
    value["prompt"] = "Run the binding preflight and report the complete result."
    value["fixtures"] = [{"source": "request.json", "destination": RUNNER_REQUEST_PATH}]
    value["checks"].append({
        "id": "runner-result", "requirement": "r1", "type": "native_runner_result",
        "request_path": RUNNER_REQUEST_PATH,
        "helper_id": "resolve-workflow-binding",
        "operation": "resolve-workflow-binding", "mode": "read_only",
        "expected_status": "expected_failure", "expected_exit_code": 1,
        "stdout_field_path": ["binding_status"],
        "expected_stdout_value": "ambiguous",
        "response_field_path": ["binding_result"],
    })
    return value


def synthesis_return_case():
    value = case(resource_class="nested")
    value["checks"].extend([{
        "id": "mechanism", "requirement": "r1", "type": "native_synthesis_mechanism",
        "artifact_path": "result.txt",
        "per_host": copy.deepcopy(NATIVE_SYNTHESIS_MECHANISMS),
    },
        {"id": "source-a", "requirement": "r1", "type": "file_access",
         "operation": "read_file", "path": "scenario-inputs/analyst-a.md"},
        {"id": "source-b", "requirement": "r1", "type": "file_access",
         "operation": "read_file", "path": "scenario-inputs/analyst-b.md"},
    ])
    return value


def dedicated_synthesis_case():
    return synthesis_return_case()


def git_observation():
    baseline, feature, feature_tree = "a" * 40, "b" * 40, "c" * 40
    return {
        "schema_version": "native-eval-git-observation/v1",
        "initial": {
            "baseline_commit": baseline,
            "feature_commit": feature,
            "feature_tree": feature_tree,
        },
        "head": feature,
        "branch": "feature",
        "origin_main": baseline,
        "status": {
            "clean": True,
            "tracked_dirty": False,
            "untracked_dirty": False,
            "tracked": [],
            "untracked": [],
        },
        "commit_count": 0,
        "commits_added": [],
        "changed_tracked_paths_from_initial_feature": [],
    }


def row(host="claude", trial=1):
    return {"case_id": "case.one", "host": host, "mode": "plugin" if host == "claude" else "project", "trial": trial}


def pair_workflow(note):
    return (
        "## Results\n"
        "| Status | Notes | Findings |\n"
        "|---|---|---|\n"
        f"| PASS | {note} | finding-{note} |\n"
    )


def pair_case(repo, *, rubric="Treat equivalent meanings as a match.", independent_pattern=None):
    fixture = Path(repo) / "tests" / "speckit-pro" / "pair-fixture"
    fixture.mkdir(parents=True, exist_ok=True)
    compare = [{
        "field": field, "source": "workflow.md", "section_selector": "## Results",
        "extractor": f"table_column:{column}", "tolerance_key": field,
    } for field, column in (("results.notes", "Notes"), ("results.findings", "Findings"))]
    (fixture / "expected.json").write_text(json.dumps({
        "schema": "speckit.layer7.expected-equivalence.v1", "fixture_id": "pair-fixture",
        "description": "Expected paired workflow fields.", "compare": compare,
        "fail_fast": False, "report_format": "field-level-diff",
    }))
    (fixture / "tolerance.json").write_text(json.dumps({
        "schema": "speckit.layer7.tolerance.v1", "fixture_id": "pair-fixture",
        "description": "Paired workflow tolerances.",
        "fields": {field: {"tolerance": "semantic-equivalent", "rationale": rubric}
                   for field, _column in (("results.notes", "Notes"),
                                          ("results.findings", "Findings"))},
    }))
    checks = [{"id": "independent", "requirement": "r1", "type": "text",
               "source": "final_text", "pattern": independent_pattern or "done"}]
    return {
        "id": "case.one", "layer": "parity", "capability": "compare outputs",
        "prompt": "produce workflow.md", "fixtures": [], "timeout_seconds": 30,
        "resource_class": "ordinary", "requirements": [{"id": "r1", "description": "pair"}],
        "checks": checks,
        "hosts": {
            "claude": {"skill": None, "allowed_tools": [], "modes": ["plugin"]},
            "codex": {"skill": None, "allowed_tools": [], "modes": ["project"]},
        },
        "pairing": {
            "schema": "native-eval-pair/v1", "arms": {"claude": "plugin", "codex": "project"},
            "checks": [{"id": "outcome", "requirement": "r1", "type": "comparison_plan",
                        "expected_path": "tests/speckit-pro/pair-fixture/expected.json",
                        "tolerance_path": "tests/speckit-pro/pair-fixture/tolerance.json",
                        "invariant_keys": []}],
        },
    }


def config(output, *, retry_cases=(), retry_status=None, claude_concurrency=1,
           codex_concurrency=1, codex_model="codex-test"):
    return SimpleNamespace(
        output=Path(output), hosts=("claude", "codex"), runs=1, resume=True,
        retry_cases=tuple(retry_cases), retry_status=retry_status,
        claude_model="claude-test", codex_model=codex_model, judge_model="judge-test",
        claude_concurrency=claude_concurrency, codex_concurrency=codex_concurrency, nested_concurrency=1,
    )


def run_claude_activation_without_retained_refs(output, repo, value, callbacks):
    real_fresh = execution._fresh_claude_activation

    def omit_refs(*args, **kwargs):
        result = real_fresh(*args, **kwargs)
        evidence = args[5]
        evidence.pop("claude_activation_witness", None)
        evidence.pop("claude_activation_session", None)
        return result

    with mock.patch("native_eval_execution._fresh_claude_activation",
                    side_effect=omit_refs):
        return run_evaluations(
            config(output), {}, [value], [row()], repo_root=repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
        )


def run_report_with_capture(output, repo, value, host, callbacks):
    report = run_evaluations(
        config(output), {}, [value], [row(host)], repo_root=repo,
        prepare=callbacks.prepare, execute=callbacks.execute,
    )
    attempt = next((Path(output) / "attempts").iterdir())
    capture = json.loads((attempt / "capture.json").read_text())["payload"]
    return report, capture


def assert_verified_capture(test, report, capture):
    test.assertEqual(report["counts"]["passes"], 1, report)
    test.assertEqual(report["counts"]["infrastructure_invalid"], 0, report)
    test.assertIn("verification_record", capture["evidence"])


def assert_rejected_parent_synthesis(test, report, capture):
    test.assertEqual(report["counts"]["behavior_fails"], 0, report)
    test.assertEqual(report["counts"]["infrastructure_invalid"], 1, report)
    test.assertIsNone(capture["observation"])


def assert_claude_verification_capture(test, callbacks):
    report, capture = run_report_with_capture(
        test.output, test.repo, verification_case(), "claude", callbacks,
    )
    assert_verified_capture(test, report, capture)


def assert_codex_parent_synthesis_rejected(test, callbacks):
    report, capture = run_report_with_capture(
        test.output, test.repo, dedicated_synthesis_case(), "codex", callbacks,
    )
    assert_rejected_parent_synthesis(test, report, capture)


def retained_invalid_codex_capture(test):
    value = case(resource_class="nested")
    callbacks = NestedCallbacks(test.output)
    with mock.patch(
        "native_eval_execution._merge_codex_supplement",
        side_effect=ValueError("post-retention normalization failed"),
    ):
        initial = run_evaluations(
            config(test.output), {}, [value], [row("codex")],
            repo_root=test.repo, prepare=callbacks.prepare, execute=callbacks.execute,
        )
    test.assertEqual(initial["counts"]["infrastructure_invalid"], 1, initial)
    attempt = next((test.output / "attempts").iterdir())
    capture = json.loads((attempt / "capture.json").read_text())["payload"]
    labels = {
        execution._rollout_label(ROOT_THREAD),
        execution._rollout_label(CHILD_THREAD),
    }
    test.assertTrue(labels.issubset(capture["evidence"]))
    return value, callbacks, attempt, labels


def replay_retained_codex_capture(test, value, callbacks):
    for session in callbacks.codex_home.rglob("*.jsonl"):
        session.unlink()
    resumed = NestedCallbacks(test.output)
    with mock.patch(
        "native_eval_execution.collect_native_tree",
        side_effect=AssertionError("retained replay used live Codex sessions"),
    ):
        replay = run_evaluations(
            config(test.output), {}, [value], [row("codex")],
            repo_root=test.repo, prepare=resumed.prepare, execute=resumed.execute,
        )
    return replay, resumed


def claude_event_trace(events, *, text="done", tools=()):
    records = [
        {"type": "system", "subtype": "init", "model": "claude-test",
         "plugins": [], "tools": list(tools)},
        *events,
        {"type": "result", "subtype": "success", "is_error": False,
         "result": text, "usage": {"input_tokens": 2, "output_tokens": 1}},
    ]
    return "\n".join(json.dumps(record) for record in records)


def claude_trace(text="done", skill=None):
    events = []
    if skill is not None:
        events.extend([
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "skill-call",
              "name": "Skill", "input": {"skill": skill}}]}, "parent_tool_use_id": None},
            {"type": "user", "message": {"content": [{"type": "tool_result",
              "tool_use_id": "skill-call", "content": "Loaded skill", "is_error": False}]}},
        ])
    return claude_event_trace(events, text=text)


def claude_explicit_trace(cwd, *, session=CLAUDE_SESSION):
    return "\n".join(json.dumps(event) for event in [
        {"type": "system", "subtype": "init", "model": "claude-test",
         "cwd": cwd, "session_id": session, "claude_code_version": "2.1.273",
         "skills": [CLAUDE_MANUAL_SKILL], "plugins": [], "tools": []},
        {"type": "result", "subtype": "success", "is_error": False, "result": "done",
         "session_id": session, "terminal_reason": "completed", "stop_reason": "end_turn",
         "api_error_status": None, "usage": {"input_tokens": 2, "output_tokens": 1}},
    ])


def claude_explicit_session(prompt, directory, cwd, *, malformed=False):
    arguments = prompt[len(f"/{CLAUDE_MANUAL_SKILL} "):]
    command_content = (
        f"<command-message>{CLAUDE_MANUAL_SKILL}</command-message>\n"
        f"<command-name>/{CLAUDE_MANUAL_SKILL}</command-name>\n"
        f"<command-args>{arguments}</command-args>"
    )
    rendered = (
        f"Base directory for this skill: {directory}\n".encode()
        + CLAUDE_MANUAL_BODY + b"\n\nARGUMENTS: " + arguments.encode()
    ).decode()

    def identity(record_id, parent):
        return {
            "type": "user", "uuid": record_id, "parentUuid": parent,
            "sessionId": CLAUDE_SESSION, "promptId": CLAUDE_PROMPT_ID,
            "cwd": cwd, "version": "2.1.273", "entrypoint": "sdk-cli",
            "userType": "external", "isSidechain": False,
            "timestamp": "2026-09-15T23:33:01.647Z",
        }

    command = identity(CLAUDE_COMMAND_ID, None)
    command["message"] = {"role": "user", "content": command_content}
    injection = identity(CLAUDE_INJECTION_ID, "wrong-parent" if malformed else CLAUDE_COMMAND_ID)
    injection["isMeta"] = True
    injection["message"] = {"role": "user", "content": [{"type": "text", "text": rendered}]}
    return "".join(json.dumps(record, separators=(",", ":")) + "\n" for record in [
        command, injection,
        {"type": "assistant", "parentUuid": CLAUDE_INJECTION_ID,
         "message": {"role": "assistant", "content": [{"type": "text", "text": "done"}]}},
    ]).encode()


def claude_fixture_read_trace(body=FIXTURE_READ_BODY, *, failed=False):
    return "\n".join(json.dumps(event) for event in [
        {"type": "system", "subtype": "init", "model": "claude-test", "plugins": [],
         "tools": ["Bash"]},
        {"type": "assistant", "message": {"content": [{
            "type": "tool_use", "id": "bounded-read", "name": "Bash",
            "input": {"command": "sed -n '1,10p' fixture.txt"},
        }]}, "parent_tool_use_id": None},
        {"type": "user", "message": {"content": [{
            "type": "tool_result", "tool_use_id": "bounded-read", "content": body,
            "is_error": failed,
        }]}, "parent_tool_use_id": None},
        {"type": "result", "subtype": "success", "is_error": False, "result": "done",
         "usage": {"input_tokens": 2, "output_tokens": 1}},
    ])


def claude_agent_trace(text="done", *, prompt="Read fixture.txt", role="general-purpose"):
    return "\n".join(json.dumps(event) for event in [
        {"type": "system", "subtype": "init", "model": "claude-test", "plugins": [],
         "tools": ["Agent"]},
        {"type": "assistant", "message": {"content": [{
            "type": "tool_use", "id": "agent-call", "name": "Agent",
            "input": {"description": "Read fixture", "prompt": prompt,
                      "subagent_type": role},
        }]}, "parent_tool_use_id": None},
        {"type": "user", "message": {"content": [{
            "type": "tool_result", "tool_use_id": "agent-call",
            "content": "fixture read complete", "is_error": False,
        }]}, "parent_tool_use_id": None},
        {"type": "result", "subtype": "success", "is_error": False, "result": text,
         "usage": {"input_tokens": 2, "output_tokens": 1}},
    ])


def claude_causal_trace(cwd, variation="valid"):
    agent_input = {"description": "Read fixture", "prompt": "Read fixture.txt",
                   "subagent_type": "general-purpose"}
    if variation in {"resumed", "reused"}:
        agent_input["resume"] = "prior-agent"
    agent_use = {"type": "assistant", "message": {"content": [{
        "type": "tool_use", "id": "agent-call", "name": "Agent", "input": agent_input,
    }]}, "parent_tool_use_id": None}
    returned = ({"empty-return": " ", "empty-wrapper": [{"type": "text", "text": ""}],
                 "null-return": None}.get(variation, "fixture read complete"))
    agent_result = {"type": "user", "message": {"content": [{
        "type": "tool_result", "tool_use_id": "agent-call",
        "content": returned,
        "is_error": False,
    }]}, "parent_tool_use_id": None}
    target = "other.txt" if variation == "unrelated-write" else "result.txt"
    parent_id = "agent-call" if variation == "child-writer" else None
    tool_name = "Bash" if variation == "bash-write" else "Write"
    tool_input = ({"command": f"printf done > {target}"} if tool_name == "Bash" else
                  {"file_path": str(Path(cwd) / target), "content": "done"})
    write_use = {"type": "assistant", "message": {"content": [{
        "type": "tool_use", "id": "write-call", "name": tool_name, "input": tool_input,
    }]}, "parent_tool_use_id": parent_id}
    write_result = {"type": "user", "message": {"content": [{
        "type": "tool_result", "tool_use_id": "write-call", "content": "written",
        "is_error": False,
    }]}, "parent_tool_use_id": parent_id}
    work = [agent_use, agent_result, write_use, write_result]
    if variation == "early-write":
        work = [write_use, write_result, agent_use, agent_result, copy.deepcopy(write_use),
                copy.deepcopy(write_result)]
        work[4]["message"]["content"][0]["id"] = "later-write"
        work[5]["message"]["content"][0]["tool_use_id"] = "later-write"
    elif variation == "missing-return":
        work.remove(agent_result)
    events = [{"type": "system", "subtype": "init", "model": "claude-test", "cwd": str(cwd),
               "plugins": [], "tools": ["Agent", tool_name]}, *work,
              {"type": "result", "subtype": "success", "is_error": False, "result": "done",
               "usage": {"input_tokens": 2, "output_tokens": 1}}]
    return "\n".join(json.dumps(event) for event in events)


def claude_synthesis_trace(cwd):
    reads = []
    for index, path in enumerate(("scenario-inputs/analyst-a.md",
                                  "scenario-inputs/analyst-b.md")):
        call_id = f"read-{index}"
        reads.extend([
            {"type": "assistant", "message": {"content": [{
                "type": "tool_use", "id": call_id, "name": "Read",
                "input": {"file_path": path},
            }]}, "parent_tool_use_id": None},
            {"type": "user", "message": {"content": [{
                "type": "tool_result", "tool_use_id": call_id,
                "content": f"option {index}", "is_error": False,
            }]}, "parent_tool_use_id": None},
        ])
    agent_use = {"type": "assistant", "message": {"content": [{
        "type": "tool_use", "id": "agent-call", "name": "Agent",
        "input": {"description": "Synthesize retained analyst results",
                  "prompt": "Synthesize only the supplied analyst returns",
                  "subagent_type": "speckit-pro:consensus-synthesizer"},
    }]}, "parent_tool_use_id": None}
    agent_result = {"type": "user", "message": {"content": [{
        "type": "tool_result", "tool_use_id": "agent-call",
        "content": "consensus result", "is_error": False,
    }]}, "parent_tool_use_id": None}
    write_use = {"type": "assistant", "message": {"content": [{
        "type": "tool_use", "id": "write-call", "name": "Write",
        "input": {"file_path": str(Path(cwd) / "result.txt"), "content": "done"},
    }]}, "parent_tool_use_id": None}
    write_result = {"type": "user", "message": {"content": [{
        "type": "tool_result", "tool_use_id": "write-call",
        "content": "written", "is_error": False,
    }]}, "parent_tool_use_id": None}
    events = [
        {"type": "system", "subtype": "init", "model": "claude-test", "cwd": str(cwd),
         "plugins": [], "tools": ["Read", "Agent", "Write"]},
        *reads, agent_use, agent_result, write_use, write_result,
        {"type": "result", "subtype": "success", "is_error": False, "result": "done",
         "usage": {"input_tokens": 2, "output_tokens": 1}},
    ]
    return "\n".join(json.dumps(event) for event in events)


def codex_trace(text="done", thread_id="thread", items=()):
    return "\n".join(json.dumps(event) for event in [
        {"type": "thread.started", "thread_id": thread_id},
        {"type": "turn.started"},
        *({"type": "item.completed", "item": item} for item in items),
        {"type": "item.completed", "item": {"id": "answer", "type": "agent_message", "text": text}},
        {"type": "turn.completed", "usage": {"input_tokens": 2, "output_tokens": 1}},
    ])


def verification_record():
    return {
        "schema_version": "verification-record/v1", "execution_id": "a" * 32,
        "dispatch_id": "verify", "command_id": "INTEGRATION_TEST",
        "argv": ["python3", "specs/parity-01/verify.py"],
        "workflow_file": "workflow.md", "snapshot_sha256": "b" * 64,
        "environment_sha256": "c" * 64, "output_directory": "/private/tmp/outputs",
        "toolchain": {}, "exit_code": 0, "stdout_sha256": "d" * 64,
        "stderr_sha256": "e" * 64, "inputs_unchanged": True,
        "snapshot_unchanged": True, "producer": "runner-isolated-project-command/v1",
        "completed": True, "elapsed_seconds": 0.1, "isolation_mode": "copy_only",
    }


def verification_response(value):
    return {
        "schema_version": "1.0", "status": "ok", "exit_code": 0,
        "legacy_exit_code": None, "diagnostics": [], "request_id": "verify-request",
        "data": {
            "record_path": ".process/verification/" + "a" * 32 + ".json",
            "record": value, "observation_material": {}, "writes_state": True,
            "reusable": False, "requires_independent_native_event": True,
            "authorization_granted": False, "rerun_required": True,
            "limitations": ["copy_only_is_not_qualified_immutable_isolation"],
            "helper_id": "execute-verification", "operation": "execute-verification",
            "mode": "apply", "promotion_status": "supported",
        },
    }


def runner_result_response(*, binding_status="ambiguous"):
    stdout_json = {
        "binding_status": binding_status,
        "task_root": "/workspace", "workflow_root": None, "workflow_file": None,
        "relation": None,
        "candidates": ["/workspace", "/workspace/.worktrees/ambiguous"],
        "problems": ["workflow path exists in multiple registered worktrees"],
    }
    stdout_text = json.dumps(stdout_json, separators=(",", ":")) + "\n"

    def captured(text):
        return {
            "text": text, "byte_count": len(text.encode()),
            "limit_bytes": 16 * 1024, "truncated": False,
        }

    request = runner_request()
    return {
        "schema_version": "1.0", "status": "expected_failure", "exit_code": 1,
        "legacy_exit_code": None,
        "diagnostics": [{"source": "runner", "code": "validation_failure"}],
        "request_id": request["request_id"],
        "data": {
            "helper_id": request["helper_id"], "operation": request["operation"],
            "mode": "read_only", "executed_in_process": True,
            "stdin_mode": "single_json_request",
            "stdin_request": {key: value for key, value in request.items()
                              if key != "request_id"},
            "shell": False, "exit_code": 1,
            "stdout": captured(stdout_text), "stderr": captured(""),
            "timed_out": False, "writes_state": False,
            "stdout_json": stdout_json,
        },
    }


def runner_final_text(value):
    return json.dumps({
        "binding_result": value, "decision": "stop",
        "next_action": "provide_absolute_workflow_path",
    }, separators=(",", ":"))


def claude_verification_trace(output, *, command="python3 -m speckit_pro_runner < request.json"):
    return claude_event_trace([
        {"type": "assistant", "message": {"content": [{
            "type": "tool_use", "id": "verify-command", "name": "Bash",
            "input": {"command": command},
        }]}, "parent_tool_use_id": None},
        {"type": "user", "message": {"content": [{
            "type": "tool_result", "tool_use_id": "verify-command",
            "content": output, "is_error": False,
        }]}, "parent_tool_use_id": None},
    ], tools=("Bash",))


def claude_runner_result_trace(output, final_text, *, command=None, is_error=True):
    command = command or f"python3 -m speckit_pro_runner < {RUNNER_REQUEST_PATH}"
    return "\n".join(json.dumps(event) for event in [
        {"type": "system", "subtype": "init", "model": "claude-test",
         "plugins": [], "tools": ["Bash"]},
        {"type": "assistant", "message": {"content": [{
            "type": "tool_use", "id": "runner-command", "name": "Bash",
            "input": {"command": command},
        }]}, "parent_tool_use_id": None},
        {"type": "user", "message": {"content": [{
            "type": "tool_result", "tool_use_id": "runner-command",
            "content": output, "is_error": is_error,
        }]}, "parent_tool_use_id": None},
        {"type": "result", "subtype": "success", "is_error": False,
         "result": final_text, "usage": {"input_tokens": 2, "output_tokens": 1}},
    ])


def codex_verification_rollout(cwd, output, *, prompt="perform the test"):
    witness = skill_witness("native-eval-canary", SKILL_CANARY)
    return [
        rollout_meta(ROOT_THREAD, cwd),
        rollout_event({"type": "task_started", "turn_id": ROOT_TURN, "started_at": 1}),
        rollout_message(prompt, message_id="prompt-message"),
        rollout_message(
            selected_skill_text("native-eval-canary", witness, cwd, "speckit-pro"),
            kind="skills.selected_skill_instructions",
            message_id="selected-native-eval-canary",
        ),
        rollout_event({
            "type": "item_completed", "thread_id": ROOT_THREAD, "turn_id": ROOT_TURN,
            "started_at_ms": 2, "completed_at_ms": 3,
            "item": {
                "type": "CommandExecution", "id": "verify-command", "status": "completed",
                "command": "python3 -m speckit_pro_runner < request.json",
                "cwd": f"file://{cwd}",
                "stdout": output, "stderr": "", "aggregated_output": output,
                "formatted_output": output, "exit_code": 0, "duration": 0.1,
            },
        }),
        rollout_event({"type": "item_completed", "thread_id": ROOT_THREAD,
                       "turn_id": ROOT_TURN, "item": {"type": "AgentMessage",
                       "id": "final-message", "content": [{"type": "text", "text": "done"}]}}),
        rollout_event({"type": "task_complete", "turn_id": ROOT_TURN, "completed_at": 4}),
    ]


def codex_runner_result_rollout(
    cwd, output, prompt, *, command=None, command_cwd=None, exit_code=1,
):
    command = command or f"python3 -m speckit_pro_runner < {RUNNER_REQUEST_PATH}"
    witness = skill_witness("native-eval-canary", SKILL_CANARY)
    return [
        rollout_meta(ROOT_THREAD, cwd),
        rollout_event({"type": "task_started", "turn_id": ROOT_TURN, "started_at": 1}),
        rollout_message(prompt, message_id="prompt-message"),
        rollout_message(
            selected_skill_text("native-eval-canary", witness, cwd, "speckit-pro"),
            kind="skills.selected_skill_instructions",
            message_id="selected-native-eval-canary",
        ),
        rollout_event({
            "type": "item_completed", "thread_id": ROOT_THREAD, "turn_id": ROOT_TURN,
            "started_at_ms": 2, "completed_at_ms": 3,
            "item": {
                "type": "CommandExecution", "id": "runner-command", "status": "completed",
                "command": command, "cwd": command_cwd or cwd,
                "stdout": output, "stderr": "",
                "aggregated_output": output, "formatted_output": output,
                "exit_code": exit_code, "duration": 0.1,
            },
        }),
        rollout_event({"type": "item_completed", "thread_id": ROOT_THREAD,
                       "turn_id": ROOT_TURN, "item": {"type": "AgentMessage",
                       "id": "final-message", "content": [{"type": "text", "text": "done"}]}}),
        rollout_event({"type": "task_complete", "turn_id": ROOT_TURN, "completed_at": 4}),
    ]


ROOT_THREAD = str(uuid.UUID(int=1))
CHILD_THREAD = str(uuid.UUID(int=2))
ROOT_TURN = str(uuid.UUID(int=3))
CHILD_TURN = str(uuid.UUID(int=4))
SPAWN_CALL = "call_native_spawn"


def rollout_line(value):
    return json.dumps(value, separators=(",", ":"))


def rollout_meta(thread_id, cwd, *, parent=None, depth=0, path="/root/read_fixture",
                 role="native_canary_worker"):
    source = "exec" if parent is None else {"subagent": {"thread_spawn": {
        "parent_thread_id": parent, "depth": depth, "agent_path": path,
        "agent_nickname": "Ohm", "agent_role": role,
    }}}
    return {"timestamp": "2026-09-15T16:36:42Z", "type": "session_meta", "payload": {
        "id": thread_id, "session_id": parent or thread_id, "cwd": cwd,
        "cli_version": "0.154.0", "model_provider": "openai", "source": source,
        "thread_source": "user" if parent is None else "subagent",
    }}


def rollout_event(payload, timestamp="2026-09-15T16:36:42Z"):
    return {"timestamp": timestamp, "type": "event_msg", "payload": payload}


def rollout_message(text, *, kind="user.text", turn=ROOT_TURN, message_id=None):
    payload = {
        "type": "message", "role": "user",
        "content": [{"type": "input_text", "text": text}],
        "internal_chat_message_metadata_passthrough": {
            "content_item_kinds": [kind], "turn_id": turn, "create_time": 1_789_492_602,
        },
    }
    if message_id is not None:
        payload["id"] = message_id
    return {"timestamp": "2026-09-15T16:36:42Z", "type": "response_item", "payload": payload}


def selected_skill_text(name, witness, cwd, plugin_name=None):
    native_name = f"{plugin_name}:{name}" if plugin_name is not None else name
    return (f"<skill>\n<name>{native_name}</name>\n<path>{cwd}/{witness['path']}</path>\n"
            f"{witness['text']}\n</skill>")


def native_skill_records(cwd, prompt, witnesses, selected=("native-eval-canary",),
                         *, stale=False, malformed=False, plugin_name=None):
    records = [rollout_meta(ROOT_THREAD, cwd),
               rollout_event({"type": "task_started", "turn_id": ROOT_TURN, "started_at": 1}),
               rollout_message(prompt, message_id="prompt-message")]
    for index, name in enumerate(selected):
        text = selected_skill_text(name, witnesses[name], cwd, plugin_name)
        records.append(rollout_message(
            text, kind="skills.selected_skill_instructions",
            turn="malformed-turn" if malformed else CHILD_TURN if stale else ROOT_TURN,
            message_id=f"selected-{index}-{name}",
        ))
    records.extend([
        rollout_event({"type": "item_completed", "thread_id": ROOT_THREAD,
                       "turn_id": ROOT_TURN, "item": {"type": "AgentMessage",
                       "id": "final-message", "content": [{"type": "text", "text": "done"}]}}),
        rollout_event({"type": "task_complete", "turn_id": ROOT_TURN, "completed_at": 2}),
    ])
    return records


def root_rollout(cwd, *, prompt="perform the test", witnesses=None, include_child=True,
                 role="native_canary_worker", dispatch_message="Read only fixture.txt",
                 include_delivery=False, plugin_name=None):
    witnesses = witnesses or {
        "native-eval-canary": skill_witness("native-eval-canary", SKILL_CANARY),
    }
    records = [rollout_meta(ROOT_THREAD, cwd),
               rollout_event({"type": "task_started", "turn_id": ROOT_TURN, "started_at": 1}),
               rollout_message(prompt, message_id="prompt-message"),
               rollout_message(selected_skill_text("native-eval-canary",
                                                   witnesses["native-eval-canary"], cwd,
                                                   plugin_name),
                               kind="skills.selected_skill_instructions",
                               message_id="selected-native-eval-canary")]
    if include_child:
        records.extend([
            {"timestamp": "2026-09-15T16:36:43Z", "type": "response_item", "payload": {
                "type": "function_call", "namespace": "collaboration", "name": "spawn_agent",
                "call_id": SPAWN_CALL, "arguments": rollout_line({
                    "agent_type": role, "fork_turns": "all",
                    "message": dispatch_message, "task_name": "read_fixture",
                })}},
            rollout_event({"type": "item_completed", "thread_id": ROOT_THREAD,
                "turn_id": ROOT_TURN, "item": {"type": "SubAgentActivity", "id": SPAWN_CALL,
                "kind": "started", "agent_thread_id": CHILD_THREAD,
                "agent_path": "/root/read_fixture"}}, "2026-09-15T16:36:43Z"),
            rollout_event({"type": "item_completed", "thread_id": ROOT_THREAD,
                "turn_id": ROOT_TURN, "item": {"type": "CollabAgentToolCall", "id": "wait-call",
                "tool": "wait", "status": "completed", "sender_thread_id": ROOT_THREAD,
                "receiver_thread_ids": []}}, "2026-09-15T16:36:46Z"),
            rollout_event({"type": "item_completed", "thread_id": ROOT_THREAD,
                "turn_id": ROOT_TURN, "item": {"type": "FileChange", "id": "root-write",
                "status": "completed", "changes": [{"path": "result.txt", "kind": "add"}]}},
                "2026-09-15T16:36:47Z"),
            rollout_event({"type": "item_completed", "thread_id": ROOT_THREAD,
                "turn_id": ROOT_TURN, "item": {"type": "SubAgentActivity", "id": "finished",
                "kind": "completed", "agent_thread_id": CHILD_THREAD,
                "agent_path": "/root/read_fixture"}}, "2026-09-15T16:36:48Z"),
        ])
        if include_delivery:
            records.append({
                "timestamp": "2026-09-15T16:36:49Z", "type": "response_item", "payload": {
                    "type": "agent_message", "id": "delivery-one",
                    "author": "/root/read_fixture", "recipient": "/root",
                    "content": [{"type": "input_text", "text":
                                 "Message Type: FINAL_ANSWER\nPayload:\nfixture read complete"}],
                    "internal_chat_message_metadata_passthrough": {
                        "turn_id": ROOT_TURN, "create_time": 1_789_490_214,
                    },
                },
            })
    records.append(rollout_event({"type": "task_complete", "turn_id": ROOT_TURN, "completed_at": 2}))
    return records


def synthesis_rollout(cwd, *, prompt, witnesses, include_child=True,
                      include_delivery=True, role="consensus-synthesizer", malformed=False):
    records = root_rollout(
        cwd, prompt=prompt, witnesses=witnesses, include_child=include_child,
        role=role, include_delivery=include_delivery,
    )
    reads = [
        rollout_event({"type": "item_completed", "thread_id": ROOT_THREAD,
            "turn_id": ROOT_TURN, "item": {"type": "CommandExecution", "id": identity,
            "status": "completed", "command": ["cat", path], "cwd": cwd,
            "stdout": "retained analyst return\n", "stderr": "", "exit_code": 0}}, timestamp)
        for identity, path, timestamp in (
            ("read-a", "scenario-inputs/analyst-a.md", "2026-09-15T16:36:42.1Z"),
            ("read-b", "scenario-inputs/analyst-b.md", "2026-09-15T16:36:42.2Z"),
        )
    ]
    records[4:4] = reads
    if include_child and include_delivery:
        delivery_index = next(index for index, record in enumerate(records)
                              if record.get("type") == "response_item"
                              and record.get("payload", {}).get("id") == "delivery-one")
        delivery = records.pop(delivery_index)
        delivery["timestamp"] = "2026-09-15T16:36:46.5Z"
        finished_index = next(index for index, record in enumerate(records)
                              if record.get("payload", {}).get("item", {}).get("id")
                              == "finished")
        finished = records.pop(finished_index)
        finished["timestamp"] = "2026-09-15T16:36:46.2Z"
        write_index = next(index for index, record in enumerate(records)
                           if record.get("payload", {}).get("item", {}).get("id") == "root-write")
        records[write_index:write_index] = [finished, delivery]
    if not include_child:
        records.insert(-1, rollout_event({"type": "item_completed", "thread_id": ROOT_THREAD,
            "turn_id": ROOT_TURN, "item": {"type": "FileChange", "id": "root-write",
            "status": "completed", "changes": [{"path": "result.txt", "kind": "add"}]}},
            "2026-09-15T16:36:47Z"))
    if malformed:
        records.pop()
    return records


def causal_root_rollout(cwd, *, prompt="perform the test", witnesses=None, variation="valid"):
    witnesses = witnesses or {
        "native-eval-canary": skill_witness("native-eval-canary", SKILL_CANARY),
    }
    records = [rollout_meta(ROOT_THREAD, cwd),
               rollout_event({"type": "task_started", "turn_id": ROOT_TURN, "started_at": 1}),
               rollout_message(prompt, message_id="prompt-message"),
               rollout_message(selected_skill_text("native-eval-canary",
                                                   witnesses["native-eval-canary"], cwd),
                               kind="skills.selected_skill_instructions",
                               message_id="selected-native-eval-canary"),
               {"timestamp": "2026-09-15T16:36:43Z", "type": "response_item", "payload": {
                   "type": "function_call", "namespace": "collaboration", "name": "spawn_agent",
                   "call_id": SPAWN_CALL, "arguments": rollout_line({
                       "agent_type": "native_canary_worker", "fork_turns": "all",
                       "message": "Read only fixture.txt", "task_name": "read_fixture",
                   })}},
               rollout_event({"type": "item_completed", "thread_id": ROOT_THREAD,
                   "turn_id": ROOT_TURN, "item": {"type": "SubAgentActivity", "id": SPAWN_CALL,
                   "kind": "started", "agent_thread_id": CHILD_THREAD,
                   "agent_path": "/root/read_fixture"}}, "2026-09-15T16:36:43Z")]
    target = "other.txt" if variation == "unrelated-write" else "result.txt"
    action_type = "CommandExecution" if variation == "bash-write" else "FileChange"
    action = rollout_event({"type": "item_completed", "thread_id": ROOT_THREAD,
        "turn_id": CHILD_TURN if variation == "wrong-turn" else ROOT_TURN,
        "item": {"type": action_type, "id": "root-write", "status": "completed",
                 **({"command": ["sh", "-c", f"printf done > {target}"], "exit_code": 0,
                     "stdout": "", "stderr": ""} if action_type == "CommandExecution" else
                    {"changes": [{"path": target, "kind": "add"}]})}},
        "2026-09-15T16:36:49Z")
    if variation == "absent-turn":
        del action["payload"]["turn_id"]
    if variation == "early-write":
        early = copy.deepcopy(action)
        early["timestamp"] = "2026-09-15T16:36:44Z"
        early["payload"]["item"]["id"] = "early-write"
        records.append(early)
    records.append(rollout_event({"type": "item_completed", "thread_id": ROOT_THREAD,
        "turn_id": ROOT_TURN, "item": {"type": "SubAgentActivity", "id": "finished",
        "kind": "completed", "agent_thread_id": CHILD_THREAD,
        "agent_path": "/root/read_fixture"}}, "2026-09-15T16:36:48Z"))
    if variation != "missing-return":
        delivery = {"timestamp": "2026-09-15T16:36:48Z", "type": "response_item", "payload": {
            "type": "agent_message", "id": "delivery-one", "author": "/root/read_fixture",
            "recipient": "/root", "content": [{"type": "input_text",
                "text": " " if variation == "empty-return" else
                        "Message Type: FINAL_ANSWER\nPayload:\nfixture read complete"}],
            "internal_chat_message_metadata_passthrough": {"turn_id": ROOT_TURN,
                                                            "create_time": 1_789_490_214},
        }}
        records.append(delivery)
        if variation == "reused":
            duplicate = copy.deepcopy(delivery)
            duplicate["payload"]["id"] = "delivery-two"
            records.append(duplicate)
    if variation not in {"child-writer"}:
        records.append(action)
    records.append(rollout_event({"type": "task_complete", "turn_id": ROOT_TURN,
                                  "completed_at": 2}))
    return records


def child_rollout(cwd, *, child_cwd=None, cycle=False,
                  command_timestamp="2026-09-15T16:36:45Z",
                  role="native_canary_worker"):
    child_cwd = child_cwd or cwd
    records = [
        rollout_meta(CHILD_THREAD, child_cwd, parent=ROOT_THREAD, depth=1, role=role),
        rollout_meta(ROOT_THREAD, cwd),
        rollout_event({"type": "task_started", "turn_id": ROOT_TURN, "started_at": 1}),
        rollout_event({"type": "item_completed", "thread_id": ROOT_THREAD,
            "turn_id": ROOT_TURN, "item": {"type": "CollabAgentToolCall", "id": "wait-call",
            "tool": "wait", "status": "completed", "sender_thread_id": ROOT_THREAD,
            "receiver_thread_ids": []}}, "2026-09-15T16:36:46Z"),
        rollout_event({"type": "thread_settings_applied", "thread_id": CHILD_THREAD}),
        rollout_event({"type": "task_started", "turn_id": CHILD_TURN, "started_at": 3}),
        {"timestamp": "2026-09-15T16:36:47Z", "type": "turn_context", "payload": {
            "turn_id": CHILD_TURN, "root_turn_id": ROOT_TURN, "cwd": child_cwd,
            "model": "gpt-5.6-sol"}},
        rollout_event({"type": "item_completed", "thread_id": CHILD_THREAD,
            "turn_id": CHILD_TURN, "item": {"type": "CommandExecution", "id": "exec-child",
            "status": "completed", "command": ["cat", "fixture.txt"], "cwd": child_cwd,
            "stdout": "canary-input-v1\n", "stderr": "", "exit_code": 0}},
            command_timestamp),
        {"timestamp": "2026-09-15T16:36:48Z", "type": "token_usage_record", "payload": {
            "thread_id": CHILD_THREAD, "turn_id": CHILD_TURN, "root_turn_id": ROOT_TURN,
            "thread_token_usage": {"input_tokens": 20, "cached_input_tokens": 0,
                "cache_write_input_tokens": 0, "output_tokens": 4,
                "reasoning_output_tokens": 1, "total_tokens": 24}}},
    ]
    if cycle:
        records.extend([
            {"timestamp": "2026-09-15T16:36:47Z", "type": "response_item", "payload": {
                "type": "function_call", "namespace": "collaboration", "name": "spawn_agent",
                "call_id": "cycle-spawn", "arguments": rollout_line({"message": "cycle"})}},
            rollout_event({"type": "item_completed", "thread_id": CHILD_THREAD,
                "turn_id": CHILD_TURN, "item": {"type": "SubAgentActivity", "id": "cycle-spawn",
                "kind": "started", "agent_thread_id": ROOT_THREAD, "agent_path": "/root"}}),
            rollout_event({"type": "item_completed", "thread_id": CHILD_THREAD,
                "turn_id": CHILD_TURN, "item": {"type": "SubAgentActivity", "id": "cycle-finished",
                "kind": "completed", "agent_thread_id": ROOT_THREAD, "agent_path": "/root"}}),
        ])
    records.append(rollout_event({"type": "item_completed", "thread_id": CHILD_THREAD,
        "turn_id": CHILD_TURN, "item": {"type": "AgentMessage", "id": "child-return",
        "content": [{"type": "text", "text": "fixture read complete"}]}}))
    records.append(rollout_event({"type": "task_complete", "turn_id": CHILD_TURN, "completed_at": 4}))
    return records


def rollout_raw(records):
    return ("\n".join(rollout_line(record) for record in records) + "\n").encode()


class FakeTriggerStage:
    def __init__(self, root, host):
        self.stage_root = Path(root)
        self.host = host
        self.namespace = "speckit-pro-trigger" if host == "claude" else None
        self.skill_markers = ({"CODEX_SKILL_SELECTED:alpha-" + "a" * 32: "alpha"}
                              if host == "codex" else {})

    def as_dict(self):
        return {
            "schema_version": "native-trigger-stage/v1", "host": self.host,
            "target_skill": "alpha", "native_target": "speckit-pro-trigger:alpha",
            "namespace": self.namespace, "stage_root": str(self.stage_root),
            "sibling_skills": ["beta", "no-speckit-skill"],
            "skill_markers": dict(self.skill_markers),
            "witnesses": {}, "source_identities": {}, "staged_identities": {},
            "controlled_description_identity": {"source": "default"},
            "trial_id_sha256": "1" * 64, "catalog_sha256": "2" * 64,
            "attempt_sha256": "3" * 64,
        }


class FakeCallbacks:
    def __init__(self, output, *, texts=None, exit_codes=None, stderr=None, by_host=None):
        self.output = Path(output)
        self.had_output = self.output.exists()
        self.texts = list(texts or ["done"])
        self.exit_codes = list(exit_codes or [0])
        self.stderr = list(stderr or [""])
        self.by_host = dict(by_host or {})
        self.thread_id = None
        self.codex_items = ()
        self.trial_identities = []
        self.evidence_roots = []
        self.prepared = []
        self.executed = []
        self.codex_home = Path(output).parent / f"codex-home-{Path(output).name}-{id(self)}"

    def prepare(self, value, host, mode, repo_root, staging_dir, model, *, trial_identity=None,
                evidence_root=None):
        staging = Path(staging_dir)
        self.trial_identities.append(trial_identity)
        self.evidence_roots.append(evidence_root)
        self.prepared.append((host, staging))
        self.assert_staging_before_reservation(staging)
        workspace = staging / "workspace"
        workspace.mkdir()
        trigger_stage = None
        if value.get("layer") == "trigger":
            trigger_root = staging / "trigger-stage"
            trigger_root.mkdir()
            trigger_stage = FakeTriggerStage(trigger_root, host)
        runtime_identity = {"schema_version": "fake/v1", "host": host, "mode": mode,
                            "model": model, "stable": "same-input"}
        if host == "codex" and value.get("layer") != "trigger":
            runtime_identity["settings"] = {"skill_read_witnesses": {
                "native-eval-canary": skill_witness("native-eval-canary", SKILL_CANARY),
            }}
        return SimpleNamespace(
            command=[host, "run", value["prompt"]], cwd=workspace,
            environment={"PATH": "/safe/bin", "CODEX_HOME": str(self.codex_home)},
            host=host, mode=mode, attempt_dir=staging, trace_path=staging / "trace.jsonl",
            result_path=None, artifact_root=workspace,
            runtime_identity=runtime_identity,
            stdout_path=staging / "native-stdout.bin", stderr_path=staging / "native-stderr.bin",
            process_receipt_path=staging / "native-process.json",
            trigger_stage=trigger_stage, resource_class=value.get("resource_class", "ordinary"),
        )

    def assert_staging_before_reservation(self, staging):
        attempts = self.output / "attempts"
        if not self.had_output and attempts.exists():
            assert not any(attempts.iterdir())
        assert staging.parent == self.output.resolve() / "staging"

    def execute(self, prepared, timeout):
        self.executed.append(prepared.host)
        selected = self.by_host.get(prepared.host)
        if selected is None:
            text = self.texts.pop(0) if self.texts else "done"
            exit_code = self.exit_codes.pop(0) if self.exit_codes else 0
            stderr = self.stderr.pop(0) if self.stderr else ""
        else:
            text, exit_code, stderr = selected
        if prepared.trigger_stage is not None and prepared.host == "claude":
            raw_trace = claude_trace(text, "speckit-pro-trigger:alpha")
        elif prepared.trigger_stage is not None:
            marker = next(iter(prepared.trigger_stage.skill_markers))
            raw_trace = codex_trace(marker, self.thread_id or "thread", self.codex_items)
        elif prepared.host == "claude":
            raw_trace = claude_trace(text)
        else:
            raw_trace = codex_trace(text, self.thread_id or ROOT_THREAD, self.codex_items)
        if prepared.host == "codex" and prepared.trigger_stage is None \
                and prepared.resource_class != "nested":
            sessions = self.codex_home / "sessions" / "2026" / "09" / "15"
            sessions.mkdir(parents=True, exist_ok=True)
            thread_id = self.thread_id or ROOT_THREAD
            records = self.skill_rollout(prepared)
            (sessions / f"rollout-2026-09-15T16-36-42-{thread_id}.jsonl").write_bytes(
                rollout_raw(records)
            )
        prepared.stdout_path.write_bytes(raw_trace.encode())
        prepared.stderr_path.write_text(stderr)
        prepared.process_receipt_path.write_text(json.dumps({"exit_code": exit_code}) + "\n")
        prepared.trace_path.write_text(raw_trace)
        return SimpleNamespace(
            exit_code=exit_code, timed_out=False, process_evidence={"cleanup_verified": True},
            stdout=raw_trace, stderr=stderr, raw_trace=raw_trace, framework_result=None,
            artifact_root=prepared.artifact_root,
        )

    def skill_rollout(self, prepared):
        witnesses = prepared.runtime_identity["settings"]["skill_read_witnesses"]
        return native_skill_records(str(Path(prepared.cwd).resolve()), prepared.command[-1], witnesses)


class ClaudeActivationCallbacks(FakeCallbacks):
    def __init__(self, output, *, session="valid"):
        super().__init__(output)
        self.session = session

    def prepare(self, value, host, mode, repo_root, staging_dir, model, *, trial_identity=None,
                evidence_root=None):
        prepared = super().prepare(
            value, host, mode, repo_root, staging_dir, model,
            trial_identity=trial_identity, evidence_root=evidence_root,
        )
        skill = prepared.cwd / "skills" / "static-skill" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_bytes(CLAUDE_MANUAL_SOURCE)
        canonical = value["prompt"].replace("{{skill}}", CLAUDE_MANUAL_SKILL)
        prompt = f"/{CLAUDE_MANUAL_SKILL} {canonical}"
        prepared.command[-1] = prompt
        prepared.runtime_identity["settings"] = {
            "claude_explicit_activation": {
                "schema_version": "native-claude-explicit-activation-input/v1",
                "skill": CLAUDE_MANUAL_SKILL,
                "canonical_activation": "static-skill",
                "prompt": prompt,
                "skill_source": {
                    "path": "skills/static-skill/SKILL.md",
                    "bytes": len(CLAUDE_MANUAL_SOURCE),
                    "sha256": hashlib.sha256(CLAUDE_MANUAL_SOURCE).hexdigest(),
                },
            },
        }
        return prepared

    def execute(self, prepared, timeout):
        self.executed.append(prepared.host)
        subject_cwd = str(prepared.cwd / "subject-cwd")
        raw_trace = claude_explicit_trace(subject_cwd)
        prepared.stdout_path.write_bytes(raw_trace.encode())
        prepared.stderr_path.write_text("")
        prepared.process_receipt_path.write_text('{"exit_code":0}\n')
        prepared.trace_path.write_text(raw_trace)
        retained = prepared.attempt_dir / "retained"
        if self.session != "missing":
            project = retained / "config" / "projects" / "synthetic-project"
            project.mkdir(parents=True)
            session = claude_explicit_session(
                prepared.command[-1], prepared.cwd / "skills" / "static-skill",
                subject_cwd, malformed=self.session == "malformed",
            )
            (project / f"{CLAUDE_SESSION}.jsonl").write_bytes(session)
        return SimpleNamespace(
            exit_code=0, timed_out=False, process_evidence={"cleanup_verified": True},
            stdout=raw_trace, stderr="", raw_trace=raw_trace, framework_result=None,
            artifact_root=prepared.artifact_root, retained_root=retained,
        )


class ClaudeAbsentVerificationCallbacks(ClaudeActivationCallbacks):
    """A complete official Claude run whose subject never invokes the runner."""

    def __init__(self, output, *, variation="valid"):
        super().__init__(output)
        self.variation = variation

    def prepare(self, value, host, mode, repo_root, staging_dir, model, *, trial_identity=None,
                evidence_root=None):
        prepared = super().prepare(
            value, host, mode, repo_root, staging_dir, model,
            trial_identity=trial_identity, evidence_root=evidence_root,
        )
        prepared.runtime_identity["case_id"] = value["id"]
        prepared.runtime_identity["settings"]["native_toolchain"] = {
            "launchers": {"python3": {"path": "bin/python3"}},
        }
        prepared.result_path = prepared.attempt_dir / "framework-result.json"
        return prepared

    def execute(self, prepared, timeout):
        raw = super().execute(prepared, timeout)
        trace_path = str(prepared.trace_path.resolve())
        prompt = prepared.runtime_identity["settings"]["claude_explicit_activation"]["prompt"]
        framework = {
            "schemaVersion": 1, "claudeVersion": "2.1.273", "partial": False,
            "suite": {"caseFilter": prepared.runtime_identity["case_id"], "ablation": "none"},
            "cases": [{
                "name": prepared.runtime_identity["case_id"], "promptMarkdown": prompt,
                "arms": {"with": [{"error": None, "tracePath": trace_path}]},
            }],
        }
        if self.variation == "partial":
            framework["partial"] = True
        elif self.variation == "wrong-session":
            changed = claude_explicit_trace(str(prepared.cwd / "subject-cwd"), session="wrong-session")
            prepared.stdout_path.write_bytes(changed.encode())
            prepared.trace_path.write_text(changed)
            raw.stdout = raw.raw_trace = changed
        elif self.variation == "truncated-trace":
            changed = "\n".join(raw.raw_trace.splitlines()[:-1])
            prepared.stdout_path.write_bytes(changed.encode())
            prepared.trace_path.write_text(changed)
            raw.stdout = raw.raw_trace = changed
        elif self.variation == "malformed-runner":
            records = [json.loads(line) for line in raw.raw_trace.splitlines()]
            records[1:1] = [
                {"type": "assistant", "session_id": CLAUDE_SESSION,
                 "message": {"content": [{
                     "type": "tool_use", "id": "malformed-runner", "name": "Bash",
                     "input": {"command": "python3 -m speckit_pro_runner"},
                 }]}},
                {"type": "user", "session_id": CLAUDE_SESSION,
                 "message": {"content": [{
                     "type": "tool_result", "tool_use_id": "malformed-runner",
                     "content": "missing request", "is_error": True,
                 }]}},
            ]
            changed = "\n".join(json.dumps(record) for record in records)
            prepared.stdout_path.write_bytes(changed.encode())
            prepared.trace_path.write_text(changed)
            raw.stdout = raw.raw_trace = changed
        prepared.result_path.write_text(json.dumps(framework, sort_keys=True) + "\n")
        raw.framework_result = framework
        return raw


class RecoverableClaudeActivationCallbacks(ClaudeActivationCallbacks):
    """A Claude run whose official retained tree outlives capture normalization."""

    def __init__(self, output, retained_root):
        super().__init__(output)
        self.retained_root = retained_root

    def prepare(self, value, host, mode, repo_root, staging_dir, model, *, trial_identity=None,
                evidence_root=None):
        prepared = super().prepare(
            value, host, mode, repo_root, staging_dir, model,
            trial_identity=trial_identity, evidence_root=evidence_root,
        )
        prepared.runtime_identity["case_id"] = value["id"]
        prepared.result_path = prepared.attempt_dir / "framework-result.json"
        return prepared

    def execute(self, prepared, timeout):
        raw = super().execute(prepared, timeout)
        trace = self.retained_root / "out" / "trace.jsonl"
        trace.parent.mkdir(parents=True)
        trace.write_text(raw.raw_trace)
        project = self.retained_root / "config" / "projects" / "synthetic-project"
        project.mkdir(parents=True)
        source = next((raw.retained_root / "config" / "projects").glob("*/*.jsonl"))
        (project / source.name).write_bytes(source.read_bytes())
        framework = {
            "schemaVersion": 1,
            "cases": [{
                "name": prepared.runtime_identity["case_id"],
                "arms": {"with": [{"error": None, "tracePath": str(trace)}]},
            }],
        }
        prepared.result_path.write_text(json.dumps(framework, sort_keys=True) + "\n")
        raw.framework_result = framework
        return raw


class FixtureReadCallbacks(FakeCallbacks):
    def __init__(self, output, *, witness_body=FIXTURE_READ_BODY,
                 observed_body=None, status="completed", include_witness=True):
        super().__init__(output)
        self.witness_body = witness_body
        self.observed_body = witness_body if observed_body is None else observed_body
        self.status = status
        self.include_witness = include_witness

    def prepare(self, value, host, mode, repo_root, staging_dir, model, *, trial_identity=None,
                evidence_root=None):
        prepared = super().prepare(
            value, host, mode, repo_root, staging_dir, model,
            trial_identity=trial_identity, evidence_root=evidence_root,
        )
        if self.include_witness:
            prepared.runtime_identity.setdefault("settings", {})[
                "fixture_read_witnesses"
            ] = fixture_read_witness(self.witness_body)
        if host == "claude":
            prepared.runtime_identity["capture_options"] = {
                "tool_aliases": {"Bash": "command_execution"},
            }
        return prepared

    def execute(self, prepared, timeout):
        self.codex_items = ({
            "id": "bounded-read", "type": "command_execution", "status": self.status,
            "command": "sed -n '1,10p' fixture.txt",
            "aggregated_output": self.observed_body,
            "exit_code": 0 if self.status == "completed" else 1,
        },)
        result = super().execute(prepared, timeout)
        if prepared.host == "claude":
            raw_trace = claude_fixture_read_trace(
                self.observed_body, failed=self.status != "completed",
            )
            prepared.stdout_path.write_bytes(raw_trace.encode())
            prepared.trace_path.write_text(raw_trace)
            result.stdout = raw_trace
            result.raw_trace = raw_trace
        return result


class SkillInjectionCallbacks(FakeCallbacks):
    def __init__(self, output, *, target_text=SKILL_CANARY, sibling_injection=False,
                 no_injection=False, stale=False, malformed=False,
                 witness_contract="valid", cwd_name="workspace", exit_codes=None,
                 plugin_name=None, tamper_plugin_manifest=False):
        super().__init__(output, exit_codes=exit_codes)
        self.target_text = target_text
        self.sibling_injection = sibling_injection
        self.no_injection = no_injection
        self.stale = stale
        self.malformed = malformed
        self.witness_contract = witness_contract
        self.cwd_name = cwd_name
        self.plugin_name = plugin_name
        self.tamper_plugin_manifest = tamper_plugin_manifest
        self.prepared_objects = []

    def witnesses(self):
        values = {"native-eval-canary": skill_witness("native-eval-canary", self.target_text)}
        for index in range(1, 12):
            name = "sibling-skill" if index == 1 else f"catalog-skill-{index:02d}"
            values[name] = skill_witness(name, f"---\nname: {name}\ndescription: staged sibling\n---\n\n{name} body.\n")
        return values

    def prepare(self, value, host, mode, repo_root, staging_dir, model, *, trial_identity=None,
                evidence_root=None):
        prepared = super().prepare(value, host, mode, repo_root, staging_dir, model,
                                   trial_identity=trial_identity, evidence_root=evidence_root)
        if host == "codex" and value.get("layer") != "trigger":
            workspace = Path(staging_dir) / self.cwd_name
            workspace.mkdir(exist_ok=True)
            prepared.cwd = workspace
            settings = {"skill_read_witnesses": self.witnesses()}
            if self.witness_contract == "missing":
                settings = {}
            elif self.witness_contract == "malformed":
                settings["skill_read_witnesses"] = {"bad name": {}}
            if self.plugin_name is not None:
                agents = workspace / ".agents"
                manifest_dir = agents / ".codex-plugin"
                manifest_dir.mkdir(parents=True)
                (manifest_dir / "plugin.json").write_text(json.dumps({
                    "name": self.plugin_name,
                }))
                (workspace / ".codex").mkdir()
                settings.update({
                    "codex_runtime": {"schema_version": "fake-canonical/v1"},
                    "protected_control_trees": {
                        ".agents": execution._tree_digest(agents),
                        ".codex": execution._tree_digest(workspace / ".codex"),
                    },
                })
            prepared.runtime_identity = {
                "schema_version": "fake/v1", "host": host, "mode": mode,
                "model": model, "cwd_identity": self.cwd_name, "settings": settings,
            }
            if self.witness_contract == "bad-cwd":
                prepared.cwd = Path("relative-workspace")
        self.prepared_objects.append(prepared)
        return prepared

    def execute(self, prepared, timeout):
        result = super().execute(prepared, timeout)
        if self.tamper_plugin_manifest and prepared.host == "codex":
            (Path(prepared.cwd) / ".agents" / ".codex-plugin" / "plugin.json").write_text(
                json.dumps({"name": "tampered-plugin"})
            )
        return result

    def skill_rollout(self, prepared):
        witnesses = prepared.runtime_identity.get("settings", {}).get("skill_read_witnesses", {})
        selected = () if self.no_injection else ("native-eval-canary",)
        if self.sibling_injection:
            selected += ("sibling-skill",)
        return native_skill_records(
            str(Path(prepared.cwd).resolve()), prepared.command[-1], witnesses, selected,
            stale=self.stale, malformed=self.malformed, plugin_name=self.plugin_name,
        )


class GitObservationCallbacks(FakeCallbacks):
    def __init__(self, output, *, variation="valid"):
        super().__init__(output)
        self.variation = variation

    def prepare(self, value, host, mode, repo_root, staging_dir, model, *, trial_identity=None,
                evidence_root=None):
        prepared = super().prepare(
            value, host, mode, repo_root, staging_dir, model,
            trial_identity=trial_identity, evidence_root=evidence_root,
        )
        settings = prepared.runtime_identity.setdefault("settings", {})
        settings["git_fixture"] = {"fixture_schema_version": "native-eval-fixtures/v2"}
        if self.variation.startswith("child-"):
            settings["git_fixture"]["expected_result"] = {"worktrees": [{
                "path": ".worktrees/child", "branch": "scenario/child", "revision": "baseline",
                "head": git_observation()["initial"]["baseline_commit"], "clean": True,
            }]}
        prepared.git_observation_path = Path(staging_dir) / "native-git-observation.json"
        return prepared

    def execute(self, prepared, timeout):
        raw = super().execute(prepared, timeout)
        process = raw.process_evidence
        if self.variation == "error":
            process["git_observation_error"] = "synthetic controller observation failure"
            return raw
        if self.variation == "missing":
            return raw
        observed = git_observation()
        if self.variation.startswith("child-") and self.variation != "child-missing":
            initial = copy.deepcopy(prepared.runtime_identity["settings"]["git_fixture"]
                                    ["expected_result"]["worktrees"][0])
            child = {"initial": initial, "head": initial["head"], "branch": initial["branch"],
                     "status": copy.deepcopy(observed["status"])}
            if self.variation == "child-dirty":
                child["status"].update(clean=False, untracked_dirty=True, untracked=["unexpected.txt"])
            elif self.variation == "child-wrong-initial":
                child["initial"]["path"] = ".worktrees/other"
            observed["registered_worktrees"] = {
                "schema_version": "native-eval-git-worktrees/v1", "worktrees": [child],
            }
        if self.variation == "malformed":
            observed.pop("head")
        payload = json.dumps(
            observed, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8") + b"\n"
        prepared.git_observation_path.write_bytes(payload)
        process.update({
            "git_observation": observed,
            "git_observation_path": prepared.git_observation_path.name,
            "git_observation_sha256": hashlib.sha256(payload).hexdigest(),
            "git_observation_bytes": len(payload),
        })
        if self.variation == "tampered":
            prepared.git_observation_path.write_bytes(payload + b" ")
        return raw


class VerificationCallbacks(FakeCallbacks):
    def __init__(self, output, *, claude_capture_wrapper=False):
        super().__init__(output)
        self.claude_capture_wrapper = claude_capture_wrapper

    def prepare(self, value, host, mode, repo_root, staging_dir, model, *, trial_identity=None,
                evidence_root=None):
        prepared = super().prepare(
            value, host, mode, repo_root, staging_dir, model,
            trial_identity=trial_identity, evidence_root=evidence_root,
        )
        settings = prepared.runtime_identity.setdefault("settings", {})
        if host == "claude":
            settings["native_toolchain"] = {"launchers": {"python3": {"path": "bin/python3"}}}
        else:
            agents = Path(prepared.cwd) / ".agents"
            manifest = agents / ".codex-plugin" / "plugin.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"name":"speckit-pro"}\n')
            codex = Path(prepared.cwd) / ".codex"
            codex.mkdir()
            settings["codex_runtime"] = {"python": {
                "python3_command": "python3", "python3_path": "/protected/bin/python3",
                "executable": "/protected/bin/python3",
            }}
            settings["protected_control_trees"] = {
                ".agents": execution._tree_digest(agents),
                ".codex": execution._tree_digest(codex),
            }
        return prepared

    def execute(self, prepared, timeout):
        self.executed.append(prepared.host)
        value = verification_record()
        record_bytes = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
        record_path = prepared.artifact_root / ".process" / "verification" / f"{'a' * 32}.json"
        record_path.parent.mkdir(parents=True)
        record_path.write_bytes(record_bytes)
        pointer_path = (prepared.artifact_root
                        / "specs/parity-01/.process/emission/verification-pointer.json")
        pointer_path.parent.mkdir(parents=True)
        pointer_path.write_text(json.dumps({
            "schema_version": "native-eval-verification-pointer/v1",
            "record_path": ".process/verification/" + "a" * 32 + ".json",
            "record_sha256": hashlib.sha256(record_bytes).hexdigest(),
            "execution_id": "a" * 32, "command_id": "INTEGRATION_TEST",
            "snapshot_sha256": "b" * 64, "reusable": False,
            "isolation_mode": "copy_only",
        }))
        output = json.dumps(verification_response(value), separators=(",", ":"))
        if prepared.host == "claude":
            command = "python3 -m speckit_pro_runner < request.json"
            if self.claude_capture_wrapper:
                command = "\n".join([
                    'python3 -m speckit_pro_runner < request.json > '
                    + '"$TMPDIR/runner-output.json" 2>"$TMPDIR/runner-stderr.log"',
                    'echo "exit=$?"', 'echo "---stdout---"',
                    'cat "$TMPDIR/runner-output.json"', "echo",
                    'echo "---stderr---"', 'cat "$TMPDIR/runner-stderr.log"',
                ])
                output = f"exit=0\n---stdout---\n{output}\n\n---stderr---"
            raw_trace = claude_verification_trace(output, command=command)
        else:
            command = {
                "id": "verify-command", "type": "command_execution", "status": "completed",
                "command": "python3 -m speckit_pro_runner < request.json",
                "aggregated_output": output, "exit_code": 0,
            }
            raw_trace = codex_trace("done", ROOT_THREAD, (command,))
            sessions = self.codex_home / "sessions" / "2026" / "09" / "15"
            sessions.mkdir(parents=True, exist_ok=True)
            cwd = str(Path(prepared.cwd).resolve())
            (sessions / f"rollout-2026-09-15T16-36-42-{ROOT_THREAD}.jsonl").write_bytes(
                rollout_raw(codex_verification_rollout(cwd, output))
            )
        prepared.stdout_path.write_bytes(raw_trace.encode())
        prepared.stderr_path.write_text("")
        prepared.process_receipt_path.write_text('{"exit_code":0}\n')
        prepared.trace_path.write_text(raw_trace)
        return SimpleNamespace(
            exit_code=0, timed_out=False, process_evidence={"cleanup_verified": True},
            stdout=raw_trace, stderr="", raw_trace=raw_trace, framework_result=None,
            artifact_root=prepared.artifact_root,
        )


def runner_command_item(*, cwd, exit_code=0, output="", item_id="verify-command") -> dict:
    return {"type": "CommandExecution", "id": item_id, "status": "completed",
            "command": CODEX_RUNNER_COMMAND, "cwd": cwd,
            "stdout": output, "stderr": "", "aggregated_output": output,
            "formatted_output": output, "exit_code": exit_code, "duration": 0.1}


def runner_command_call(*, exit_code=0, item_id="verify-command") -> dict:
    return {"id": item_id, "type": "command_execution", "status": "completed",
            "command": CODEX_RUNNER_COMMAND, "aggregated_output": "", "exit_code": exit_code}


def codex_rollout_without_runner(cwd, *, items=(), complete=True) -> list:
    witness = skill_witness("native-eval-canary", SKILL_CANARY)
    records = [
        rollout_meta(ROOT_THREAD, cwd),
        rollout_event({"type": "task_started", "turn_id": ROOT_TURN, "started_at": 1}),
        rollout_message("perform the test", message_id="prompt-message"),
        rollout_message(selected_skill_text("native-eval-canary", witness, cwd, "speckit-pro"),
                        kind="skills.selected_skill_instructions",
                        message_id="selected-native-eval-canary"),
    ]
    for index, item in enumerate(items):
        records.append(rollout_event({
            "type": "item_completed", "thread_id": ROOT_THREAD, "turn_id": ROOT_TURN,
            "started_at_ms": 2 + index, "completed_at_ms": 3 + index, "item": item,
        }))
    records.append(rollout_event({
        "type": "item_completed", "thread_id": ROOT_THREAD, "turn_id": ROOT_TURN,
        "item": {"type": "AgentMessage", "id": "final-message",
                 "content": [{"type": "text", "text": "done"}]},
    }))
    if complete:
        records.append(rollout_event({"type": "task_complete", "turn_id": ROOT_TURN,
                                      "completed_at": 4}))
    return records


CODEX_RUNNER_COMMAND = "python3 -m speckit_pro_runner < request.json"
VERIFICATION_POINTER_PATH = "specs/parity-01/.process/emission/verification-pointer.json"


class AbsentVerificationCallbacks(VerificationCallbacks):
    """Subjects whose retained native rollout proves the runner never ran."""

    def __init__(self, output, *, variation="absent"):
        super().__init__(output)
        self.variation = variation

    def execute(self, prepared, timeout):
        self.executed.append(prepared.host)
        cwd = str(Path(prepared.cwd).resolve())
        if prepared.host == "claude":
            raw_trace = claude_trace("done")
            prepared.stdout_path.write_bytes(raw_trace.encode())
            prepared.stderr_path.write_text("")
            prepared.process_receipt_path.write_text('{"exit_code":0}\n')
            prepared.trace_path.write_text(raw_trace)
            return SimpleNamespace(
                exit_code=0, timed_out=False, process_evidence={"cleanup_verified": True},
                stdout=raw_trace, stderr="", raw_trace=raw_trace, framework_result=None,
                artifact_root=prepared.artifact_root,
            )
        if self.variation == "forged-absence":
            raw = super().execute(prepared, timeout)
            (prepared.artifact_root / VERIFICATION_POINTER_PATH).write_text(json.dumps({
                "schema": "native-eval-verification-absence/v1",
                "kind": "no-native-runner-invocation",
                "authority": "controller-bound-retained-native-evidence",
                "host": "codex",
                "root_trace": {"schema": "codex-native-plan-repair-trace/v1",
                               "thread_id": ROOT_THREAD, "raw_sha256": "f" * 64,
                               "runner_invocation_count": 0},
                "check": {"id": "verification", "workflow_file": "workflow.md",
                          "command_id": "INTEGRATION_TEST",
                          "pointer_path": VERIFICATION_POINTER_PATH, "reusable": False},
            }))
            return raw
        rollout_items: tuple = ()
        stdout_items: tuple = ()
        if self.variation == "wrong-cwd":
            rollout_items = (runner_command_item(cwd=cwd + "/elsewhere"),)
        elif self.variation == "failed":
            rollout_items = (runner_command_item(cwd=cwd, exit_code=1),)
        elif self.variation == "truncated-command":
            rollout_items = (runner_command_item(cwd=cwd, output='{"data":'),)
        elif self.variation == "duplicate":
            output = json.dumps(verification_response(verification_record()),
                                separators=(",", ":"))
            rollout_items = (
                runner_command_item(cwd=cwd, output=output),
                runner_command_item(cwd=cwd, output=output, item_id="verify-command-2"),
            )
            stdout_items = (
                runner_command_call(),
                runner_command_call(item_id="verify-command-2"),
            )
        if self.variation in {"unbound", "wrong-cwd", "failed", "truncated-command"}:
            stdout_items = (runner_command_call(
                exit_code=1 if self.variation == "failed" else 0),)
        raw_trace = codex_trace("done", ROOT_THREAD, stdout_items)
        sessions = self.codex_home / "sessions" / "2026" / "09" / "15"
        sessions.mkdir(parents=True, exist_ok=True)
        (sessions / f"rollout-2026-09-15T16-36-42-{ROOT_THREAD}.jsonl").write_bytes(
            rollout_raw(codex_rollout_without_runner(
                cwd, items=rollout_items, complete=self.variation != "truncated",
            ))
        )
        prepared.stdout_path.write_bytes(raw_trace.encode())
        prepared.stderr_path.write_text("")
        prepared.process_receipt_path.write_text('{"exit_code":0}\n')
        prepared.trace_path.write_text(raw_trace)
        return SimpleNamespace(
            exit_code=0, timed_out=False, process_evidence={"cleanup_verified": True},
            stdout=raw_trace, stderr="", raw_trace=raw_trace, framework_result=None,
            artifact_root=prepared.artifact_root,
        )


class RunnerResultCallbacks(VerificationCallbacks):
    def __init__(self, output, *, variation="valid"):
        super().__init__(output)
        self.variation = variation

    def prepare(self, value, host, mode, repo_root, staging_dir, model, *, trial_identity=None,
                evidence_root=None):
        prepared = super().prepare(
            value, host, mode, repo_root, staging_dir, model,
            trial_identity=trial_identity, evidence_root=evidence_root,
        )
        payload = (Path(repo_root) / "request.json").read_bytes()
        settings = prepared.runtime_identity.setdefault("settings", {})
        settings["fixture_read_witnesses"] = {
            RUNNER_REQUEST_PATH: {
                "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
            },
        }
        return prepared

    def execute(self, prepared, timeout):
        self.executed.append(prepared.host)
        value = runner_result_response(
            binding_status="resolved" if self.variation == "wrong-outcome" else "ambiguous"
        )
        output = json.dumps(value, separators=(",", ":"))
        if self.variation == "duplicate-output":
            output += output
        elif self.variation == "truncated-output":
            output = output[:-1]
        final_text = runner_final_text(value)
        command = f"python3 -m speckit_pro_runner < {RUNNER_REQUEST_PATH}"
        if self.variation == "wrong-path":
            command = "python3 -m speckit_pro_runner < scenario-inputs/other.json"
        elif self.variation == "wrong-runtime":
            command = f"/untrusted/python3 -m speckit_pro_runner < {RUNNER_REQUEST_PATH}"
        command_exit = 0 if self.variation == "wrong-exit" else 1
        if self.variation == "claim-only":
            raw_trace = (claude_trace(final_text) if prepared.host == "claude"
                         else codex_trace(final_text, ROOT_THREAD, ()))
        elif prepared.host == "claude":
            raw_trace = claude_runner_result_trace(
                output, final_text, command=command, is_error=command_exit != 0,
            )
        else:
            command = {
                "id": "runner-command", "type": "command_execution", "status": "completed",
                "command": command, "aggregated_output": output,
                "exit_code": command_exit,
            }
            raw_trace = codex_trace(final_text, ROOT_THREAD, (command,))
        if prepared.host == "codex":
            sessions = self.codex_home / "sessions" / "2026" / "09" / "15"
            sessions.mkdir(parents=True, exist_ok=True)
            if self.variation == "claim-only":
                records = [
                    record for record in codex_runner_result_rollout(
                        str(Path(prepared.cwd).resolve()), output, prepared.command[-1],
                    )
                    if not (record.get("type") == "event_msg"
                            and record.get("payload", {}).get("item", {}).get("type")
                            == "CommandExecution")
                ]
            else:
                command_text = command["command"] if isinstance(command, dict) else command
                records = codex_runner_result_rollout(
                    str(Path(prepared.cwd).resolve()), output, prepared.command[-1],
                    command=command_text,
                    command_cwd=(str(self.codex_home / "wrong-cwd")
                                 if self.variation == "wrong-cwd" else None),
                    exit_code=command_exit,
                )
            (sessions / f"rollout-2026-09-15T16-36-42-{ROOT_THREAD}.jsonl").write_bytes(
                rollout_raw(records)
            )
        prepared.stdout_path.write_bytes(raw_trace.encode())
        prepared.stderr_path.write_text("")
        prepared.process_receipt_path.write_text('{"exit_code":0}\n')
        prepared.trace_path.write_text(raw_trace)
        return SimpleNamespace(
            exit_code=0, timed_out=False, process_evidence={"cleanup_verified": True},
            stdout=raw_trace, stderr="", raw_trace=raw_trace, framework_result=None,
            artifact_root=prepared.artifact_root,
        )


class ChildVerifyRunnerResultCallbacks(RunnerResultCallbacks):
    """A Verify child, rather than the root, owns the native runner call."""

    def execute(self, prepared, timeout):
        self.executed.append(prepared.host)
        value = runner_result_response()
        output = json.dumps(value, separators=(",", ":"))
        cwd = str(Path(prepared.cwd).resolve())
        command = f"python3 -m speckit_pro_runner < {RUNNER_REQUEST_PATH}"
        root_items = (
            {"id": SPAWN_CALL, "type": "collab_tool_call", "tool": "spawn_agent",
             "status": "completed", "result": {"thread_id": CHILD_THREAD}},
            {"id": "wait-call", "type": "collab_tool_call", "tool": "wait",
             "status": "completed", "result": {"completed": [CHILD_THREAD]}},
            {"id": "root-write", "type": "file_change", "status": "completed",
             "changes": [{"path": "result.txt", "kind": "add"}]},
        )
        raw_trace = codex_trace(runner_final_text(value), ROOT_THREAD, root_items)

        witnesses = prepared.runtime_identity["settings"]["skill_read_witnesses"]
        root = root_rollout(
            cwd, prompt=prepared.command[-1], witnesses=witnesses, include_delivery=True,
            plugin_name="speckit-pro",
        )
        child = child_rollout(cwd)
        native_command = next(
            record["payload"]["item"] for record in child
            if record.get("payload", {}).get("item", {}).get("type") == "CommandExecution"
        )
        native_command.update({
            "id": "verify-runner-command", "command": command, "cwd": cwd,
            "stdout": output, "stderr": "", "aggregated_output": output,
            "formatted_output": output, "exit_code": 1, "duration": 0.1,
        })
        sessions = self.codex_home / "sessions" / "2026" / "09" / "15"
        sessions.mkdir(parents=True, exist_ok=True)
        (sessions / f"rollout-2026-09-15T16-36-42-{ROOT_THREAD}.jsonl").write_bytes(
            rollout_raw(root)
        )
        (sessions / f"rollout-2026-09-15T16-36-43-{CHILD_THREAD}.jsonl").write_bytes(
            rollout_raw(child)
        )
        prepared.stdout_path.write_bytes(raw_trace.encode())
        prepared.stderr_path.write_text("")
        prepared.process_receipt_path.write_text('{"exit_code":0}\n')
        prepared.trace_path.write_text(raw_trace)
        return SimpleNamespace(
            exit_code=0, timed_out=False, process_evidence={"cleanup_verified": True},
            stdout=raw_trace, stderr="", raw_trace=raw_trace, framework_result=None,
            artifact_root=prepared.artifact_root,
        )


class PairCallbacks(FakeCallbacks):
    def __init__(self, output, *, artifacts, texts=None):
        super().__init__(output, texts=texts)
        self.artifacts = dict(artifacts)

    def execute(self, prepared, timeout):
        (prepared.artifact_root / "workflow.md").write_text(self.artifacts[prepared.host])
        return super().execute(prepared, timeout)


class PairJudge:
    runtime_identity = {"schema": "fake-native-judge/v1", "runtime": "stable"}

    def __init__(self, verdicts):
        self.verdicts = list(verdicts)
        self.requests = []

    def __call__(self, request, grade_dir, model):
        self.requests.append(copy.deepcopy(request))
        passed = self.verdicts.pop(0)
        reference = request["evidence_references"][0]
        return {criterion["id"]: {"passed": passed, "evidence": [reference]}
                for criterion in request["semantic_criteria"]}


class NestedCallbacks(FakeCallbacks):
    def __init__(self, output, *, variation="valid"):
        super().__init__(output)
        self.variation = variation
        self.thread_id = ROOT_THREAD
        self.codex_home = Path(output).parent / f"codex-home-{variation}"
        self.dispatch_message = "Read only fixture.txt"
        self.dispatch_role = "native_canary_worker"
        self.codex_items = (
            {"id": SPAWN_CALL, "type": "collab_tool_call", "tool": "spawn_agent",
             "status": "completed", "result": {"thread_id": CHILD_THREAD}},
            {"id": "wait-call", "type": "collab_tool_call", "tool": "wait",
             "status": "completed", "result": {"completed": [CHILD_THREAD]}},
            {"id": "root-write", "type": "file_change", "status": "completed",
             "changes": [{"path": "result.txt", "kind": "add"}]},
        )

    def prepare(self, value, host, mode, repo_root, staging_dir, model, *, trial_identity=None,
                evidence_root=None):
        prepared = super().prepare(value, host, mode, repo_root, staging_dir, model,
                                   trial_identity=trial_identity, evidence_root=evidence_root)
        prepared.environment = {**prepared.environment, "CODEX_HOME": str(self.codex_home)}
        return prepared

    def execute(self, prepared, timeout):
        sessions = self.codex_home / "sessions" / "2026" / "09" / "15"
        sessions.mkdir(parents=True, exist_ok=True)
        cwd = str(Path(prepared.cwd).resolve())
        witnesses = prepared.runtime_identity["settings"]["skill_read_witnesses"]
        root = root_rollout(cwd, prompt=prepared.command[-1], witnesses=witnesses,
                            include_child=self.variation != "no-child",
                            role=self.dispatch_role, dispatch_message=self.dispatch_message,
                            include_delivery=getattr(self, "include_delivery", False))
        (sessions / f"rollout-2026-09-15T16-36-42-{ROOT_THREAD}.jsonl").write_bytes(rollout_raw(root))
        if self.variation != "no-child":
            child_cwd = str(self.codex_home / "wrong-workspace") if self.variation == "wrong-cwd" else cwd
            child_time = "2026-09-15T16:36:46Z" if self.variation == "ambiguous-order" \
                else "2026-09-15T16:36:45Z"
            child = child_rollout(cwd, child_cwd=child_cwd, cycle=self.variation == "cycle",
                                  command_timestamp=child_time, role=self.dispatch_role)
            (sessions / f"rollout-2026-09-15T16-36-43-{CHILD_THREAD}.jsonl").write_bytes(rollout_raw(child))
        return super().execute(prepared, timeout)


class SynthesisCallbacks(NestedCallbacks):
    def __init__(self, output, *, variation="valid"):
        super().__init__(output)
        self.variation = variation
        self.dispatch_role = "codebase-analyst" if variation == "wrong-role" \
            else "consensus-synthesizer"
        self.include_delivery = variation != "missing-delivery"
        reads = (
            {"id": "read-a", "type": "command_execution", "status": "completed",
             "command": "cat scenario-inputs/analyst-a.md", "aggregated_output": "option a",
             "exit_code": 0},
            {"id": "read-b", "type": "command_execution", "status": "completed",
             "command": "cat scenario-inputs/analyst-b.md", "aggregated_output": "option b",
             "exit_code": 0},
        )
        write = {"id": "root-write", "type": "file_change", "status": "completed",
                 "changes": [{"path": "result.txt", "kind": "add"}]}
        if variation != "no-child":
            spawn = {"id": SPAWN_CALL, "type": "collab_tool_call", "tool": "spawn_agent",
                     "status": "completed", "agent_type": self.dispatch_role,
                     "result": {"thread_id": CHILD_THREAD}}
            self.codex_items = (*reads, spawn, write)
        else:
            self.codex_items = (*reads, write)

    def execute(self, prepared, timeout):
        (prepared.artifact_root / "result.txt").write_text("done", encoding="utf-8")
        if prepared.host == "claude":
            self.executed.append(prepared.host)
            raw_trace = claude_synthesis_trace(prepared.cwd)
            prepared.stdout_path.write_bytes(raw_trace.encode())
            prepared.stderr_path.write_text("")
            prepared.process_receipt_path.write_text('{"exit_code":0}\n')
            prepared.trace_path.write_text(raw_trace)
            return SimpleNamespace(
                exit_code=0, timed_out=False, process_evidence={"cleanup_verified": True},
                stdout=raw_trace, stderr="", raw_trace=raw_trace, framework_result=None,
                artifact_root=prepared.artifact_root,
            )
        sessions = self.codex_home / "sessions" / "2026" / "09" / "15"
        sessions.mkdir(parents=True, exist_ok=True)
        cwd = str(Path(prepared.cwd).resolve())
        if self.variation == "absolute-write":
            self.codex_items[-1]["changes"][0]["path"] = str(Path(cwd) / "result.txt")
        witnesses = prepared.runtime_identity["settings"]["skill_read_witnesses"]
        if self.variation != "missing-root":
            root = synthesis_rollout(
                cwd, prompt=prepared.command[-1], witnesses=witnesses,
                include_child=self.variation != "no-child",
                include_delivery=self.include_delivery,
                role=self.dispatch_role,
                malformed=self.variation == "malformed-root",
            )
            if self.variation == "projected-write-id":
                native_write = next(
                    record["payload"]["item"] for record in root
                    if record.get("payload", {}).get("item", {}).get("id") == "root-write"
                )
                native_write["id"] = "native-root-write"
            (sessions / f"rollout-2026-09-15T16-36-42-{ROOT_THREAD}.jsonl").write_bytes(
                rollout_raw(root)
            )
        if self.variation != "no-child":
            child = child_rollout(cwd, role=self.dispatch_role)
            (sessions / f"rollout-2026-09-15T16-36-43-{CHILD_THREAD}.jsonl").write_bytes(
                rollout_raw(child)
            )
        return FakeCallbacks.execute(self, prepared, timeout)


class NativeSubagentCallbacks(NestedCallbacks):
    def execute(self, prepared, timeout):
        if prepared.host == "codex":
            return super().execute(prepared, timeout)
        self.executed.append(prepared.host)
        raw_trace = claude_agent_trace(
            prompt=getattr(self, "claude_dispatch_message", "Read fixture.txt"),
            role=getattr(self, "claude_dispatch_role", "general-purpose"),
        )
        prepared.stdout_path.write_bytes(raw_trace.encode())
        prepared.stderr_path.write_text("")
        prepared.process_receipt_path.write_text('{"exit_code":0}\n')
        prepared.trace_path.write_text(raw_trace)
        return SimpleNamespace(
            exit_code=0, timed_out=False, process_evidence={"cleanup_verified": True},
            stdout=raw_trace, stderr="", raw_trace=raw_trace, framework_result=None,
            artifact_root=prepared.artifact_root,
        )


class DispatchCallbacks(NativeSubagentCallbacks):
    def __init__(self, output):
        super().__init__(output)
        self.dispatch_message = "Inspect [[native-eval-item:dispatch-i1]]"
        self.dispatch_role = "codebase-analyst"
        self.claude_dispatch_message = self.dispatch_message
        self.claude_dispatch_role = self.dispatch_role
        self.include_delivery = True


class CausalCallbacks(NestedCallbacks):
    def __init__(self, output, *, variation="valid"):
        super().__init__(output, variation=variation)
        self.variation = variation

    def execute(self, prepared, timeout):
        if prepared.host == "claude":
            self.executed.append(prepared.host)
            raw_trace = claude_causal_trace(prepared.cwd, self.variation)
            prepared.stdout_path.write_bytes(raw_trace.encode())
            prepared.stderr_path.write_text("")
            prepared.process_receipt_path.write_text('{"exit_code":0}\n')
            prepared.trace_path.write_text(raw_trace)
            return SimpleNamespace(
                exit_code=0, timed_out=False, process_evidence={"cleanup_verified": True},
                stdout=raw_trace, stderr="", raw_trace=raw_trace, framework_result=None,
                artifact_root=prepared.artifact_root,
            )
        sessions = self.codex_home / "sessions" / "2026" / "09" / "15"
        sessions.mkdir(parents=True, exist_ok=True)
        cwd = str(Path(prepared.cwd).resolve())
        witnesses = prepared.runtime_identity["settings"]["skill_read_witnesses"]
        root = causal_root_rollout(cwd, prompt=prepared.command[-1], witnesses=witnesses,
                                   variation=self.variation)
        child = child_rollout(cwd)
        if self.variation == "child-writer":
            child.insert(-1, rollout_event({"type": "item_completed", "thread_id": CHILD_THREAD,
                "turn_id": CHILD_TURN, "item": {"type": "FileChange", "id": "child-write",
                "status": "completed", "changes": [{"path": "result.txt", "kind": "add"}]}},
                "2026-09-15T16:36:47Z"))
        (sessions / f"rollout-2026-09-15T16-36-42-{ROOT_THREAD}.jsonl").write_bytes(
            rollout_raw(root))
        (sessions / f"rollout-2026-09-15T16-36-43-{CHILD_THREAD}.jsonl").write_bytes(
            rollout_raw(child))
        if self.variation == "reused":
            self.codex_items = (*self.codex_items,
                {"id": "send-followup", "type": "collab_tool_call", "tool": "send_input",
                 "status": "completed", "result": {"delivered": True}})
        elif self.variation == "child-writer":
            self.codex_items = tuple(item for item in self.codex_items if item["id"] != "root-write")
        elif self.variation == "bash-write":
            self.codex_items = tuple(item for item in self.codex_items if item["id"] != "root-write") + (
                {"id": "root-write", "type": "command_execution", "status": "completed",
                 "command": ["sh", "-c", "printf done > result.txt"],
                 "aggregated_output": "", "exit_code": 0},)
        elif self.variation == "unrelated-write":
            self.codex_items = tuple(
                {**item, "changes": [{"path": "other.txt", "kind": "add"}]}
                if item["id"] == "root-write" else item for item in self.codex_items)
        elif self.variation == "early-write":
            early = {"id": "early-write", "type": "file_change", "status": "completed",
                     "changes": [{"path": "result.txt", "kind": "add"}]}
            self.codex_items = (self.codex_items[0], early, *self.codex_items[1:])
        return FakeCallbacks.execute(self, prepared, timeout)


class NativeExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / "run"
        self.repo = self.root / "repo"
        self.repo.mkdir()

    def test_stages_before_reservation_and_persists_raw_evidence(self):
        callbacks = FakeCallbacks(self.output)
        report = run_evaluations(
            config(self.output), {"schema_version": "native-eval-catalog/v1"}, [case()], [row()],
            repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(report["exit_status"], 0)
        self.assertEqual(report["counts"]["subject_launches"], 1)
        self.assertEqual(report["counts"]["passes"], 1, report)
        self.assertGreater(report["timings"]["wall_seconds"], 0)
        self.assertIn("native_execution_seconds", report["timings"])
        self.assertIn("aggregate_job_seconds", report["providers"]["claude"])
        self.assertNotIn("duration_seconds", report["providers"]["claude"])
        self.assertGreater(report["providers"]["claude"]["completed_subjects_per_wall_second"], 0)
        attempt = next((self.output / "attempts").iterdir())
        self.assertTrue((attempt / "launch-prepared.json").is_file())
        receipt = json.loads((attempt / "launch-prepared.json").read_text())
        self.assertEqual(receipt["command"], ["claude", "run", "perform the test"])
        self.assertNotIn("environment", receipt)
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        self.assertIn("process_receipt", capture["evidence"])
        self.assertIn("raw_trace", capture["evidence"])

    def test_resume_reuses_pass_and_grader_change_regrades_without_launch(self):
        first = FakeCallbacks(self.output)
        initial = run_evaluations(config(self.output), {}, [case()], [row()], repo_root=self.repo,
                                  prepare=first.prepare, execute=first.execute)
        self.assertEqual(initial["counts"]["passes"], 1)

        reused = FakeCallbacks(self.output)
        second = run_evaluations(config(self.output), {}, [case()], [row()], repo_root=self.repo,
                                 prepare=reused.prepare, execute=reused.execute)
        self.assertEqual(second["counts"]["reused"], 1)
        self.assertEqual(reused.executed, [])

        changed = copy.deepcopy(case())
        changed["checks"][0]["pattern"] = "never-matches"
        regraded = FakeCallbacks(self.output)
        third = run_evaluations(config(self.output), {}, [changed], [row()], repo_root=self.repo,
                                prepare=regraded.prepare, execute=regraded.execute)
        self.assertEqual(third["counts"]["regraded"], 1)
        self.assertEqual(third["counts"]["behavior_fails"], 1)
        self.assertEqual(regraded.executed, [])
        attempt = next((self.output / "attempts").iterdir())
        evidence = [json.loads(path.read_text())["payload"].get("evidence", {})
                    for path in attempt.glob("grade-*.json")]
        self.assertTrue(any("interpretation" in refs for refs in evidence))

    def test_fixture_read_proofs_bind_fresh_and_regrade_both_hosts_without_relaunch(self):
        rows = [row("claude"), row("codex")]
        callbacks = FixtureReadCallbacks(self.output)
        initial = run_evaluations(
            config(self.output), {}, [fixture_read_case()], rows, repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(initial["counts"]["passes"], 2, initial)
        attempts = list((self.output / "attempts").iterdir())
        expected = fixture_read_witness()
        for attempt in attempts:
            observation = json.loads((attempt / "capture.json").read_text())["payload"][
                "observation"
            ]
            self.assertEqual(
                observation["native_metadata"]["controller_fixture_read_witnesses"],
                {"authority": "controller-staged-fixtures", "witnesses": expected},
            )
            access = next(item for item in file_accesses(observation)
                          if item["path"] == FIXTURE_READ_PATH)
            self.assertEqual(access["provenance"]["sha256"],
                             expected[FIXTURE_READ_PATH]["sha256"])

        changed = fixture_read_case()
        changed["checks"][0]["pattern"] = "do.e"
        replay = FixtureReadCallbacks(self.output)
        regraded = run_evaluations(
            config(self.output), {}, [changed], rows, repo_root=self.repo,
            prepare=replay.prepare, execute=replay.execute,
        )
        self.assertEqual(regraded["counts"]["passes"], 2, regraded)
        self.assertEqual(regraded["counts"]["regraded"], 2)
        self.assertEqual(regraded["counts"]["subject_launches"], 0)
        self.assertEqual(replay.executed, [])
        for attempt in attempts:
            interpretation = next(
                path / "interpretation.json" for path in (attempt / "grades").iterdir()
                if (path / "interpretation.json").exists()
            )
            observation = json.loads(interpretation.read_text())["observation"]
            self.assertTrue(any(item["path"] == FIXTURE_READ_PATH
                                for item in file_accesses(observation)))

    def test_fixture_read_helper_source_change_regrades_without_changing_subject_input(self):
        value = fixture_read_case()
        original_source_sha = execution._source_sha

        def source_sha(helper_sha):
            def replaced(path):
                if Path(path).name == "native_eval_fixture_reads.py":
                    return helper_sha
                return original_source_sha(path)
            return replaced

        callbacks = FixtureReadCallbacks(self.output)
        with mock.patch.object(execution, "_source_sha", side_effect=source_sha("a" * 64)):
            initial = run_evaluations(
                config(self.output), {}, [value], [row("codex")], repo_root=self.repo,
                prepare=callbacks.prepare, execute=callbacks.execute,
            )
        self.assertEqual(initial["counts"]["passes"], 1, initial)

        replay = FixtureReadCallbacks(self.output)
        with mock.patch.object(execution, "_source_sha", side_effect=source_sha("b" * 64)):
            regraded = run_evaluations(
                config(self.output), {}, [value], [row("codex")], repo_root=self.repo,
                prepare=replay.prepare, execute=replay.execute,
            )
        self.assertEqual(regraded["counts"]["passes"], 1, regraded)
        self.assertEqual(regraded["counts"]["regraded"], 1)
        self.assertEqual(regraded["counts"]["subject_launches"], 0)
        self.assertEqual(replay.executed, [])

    def test_fixture_read_witness_change_is_a_new_subject_input(self):
        value = fixture_read_case()
        first = FixtureReadCallbacks(self.output)
        initial = run_evaluations(
            config(self.output), {}, [value], [row("codex")], repo_root=self.repo,
            prepare=first.prepare, execute=first.execute,
        )
        self.assertEqual(initial["counts"]["passes"], 1, initial)

        changed_body = "changed fixture\n"
        changed = FixtureReadCallbacks(
            self.output, witness_body=changed_body, observed_body=changed_body,
        )
        report = run_evaluations(
            config(self.output), {}, [value], [row("codex")], repo_root=self.repo,
            prepare=changed.prepare, execute=changed.execute,
        )
        self.assertEqual(report["counts"]["passes"], 1, report)
        self.assertEqual(report["counts"]["subject_launches"], 1)
        self.assertEqual(report["counts"]["regraded"], 0)
        self.assertEqual(changed.executed, ["codex"])
        self.assertEqual(len(list((self.output / "attempts").iterdir())), 2)

    def test_fixture_read_malformed_witness_and_forged_proof_are_invalid(self):
        class MalformedWitnessCallbacks(FixtureReadCallbacks):
            def prepare(self, *args, **kwargs):
                prepared = super().prepare(*args, **kwargs)
                prepared.runtime_identity["settings"]["fixture_read_witnesses"][
                    FIXTURE_READ_PATH
                ]["sha256"] = "not-a-sha"
                return prepared

        malformed_output = self.root / "malformed"
        malformed = MalformedWitnessCallbacks(malformed_output)
        report = run_evaluations(
            config(malformed_output), {}, [fixture_read_case()], [row("codex")],
            repo_root=self.repo, prepare=malformed.prepare, execute=malformed.execute,
        )
        self.assertEqual(report["counts"]["infrastructure_invalid"], 1, report)

        forged_output = self.root / "forged"
        forged = FixtureReadCallbacks(forged_output)
        original_normalize = execution.normalize_trace

        def forge_proof(*args, **kwargs):
            observation = original_normalize(*args, **kwargs)
            observation["native_metadata"]["fixture_read_proofs"] = []
            return observation

        with mock.patch.object(execution, "normalize_trace", side_effect=forge_proof):
            report = run_evaluations(
                config(forged_output), {}, [fixture_read_case()], [row("codex")],
                repo_root=self.repo, prepare=forged.prepare, execute=forged.execute,
            )
        self.assertEqual(report["counts"]["infrastructure_invalid"], 1, report)

    def test_fixture_read_missing_partial_failed_and_tampered_evidence_fail_closed(self):
        missing = FixtureReadCallbacks(self.output, include_witness=False)
        initial = run_evaluations(
            config(self.output), {}, [fixture_read_case()], [row("codex")],
            repo_root=self.repo, prepare=missing.prepare, execute=missing.execute,
        )
        self.assertEqual(initial["counts"]["behavior_fails"], 1, initial)
        attempt = next((self.output / "attempts").iterdir())
        captured = json.loads((attempt / "capture.json").read_text())["payload"]["observation"]
        self.assertNotIn("controller_fixture_read_witnesses", captured["native_metadata"])

        changed = fixture_read_case()
        changed["checks"][0]["pattern"] = "do.e"
        replay = FixtureReadCallbacks(self.output, include_witness=False)
        regraded = run_evaluations(
            config(self.output), {}, [changed], [row("codex")], repo_root=self.repo,
            prepare=replay.prepare, execute=replay.execute,
        )
        self.assertEqual(regraded["counts"]["behavior_fails"], 1, regraded)
        self.assertEqual(regraded["counts"]["regraded"], 1)
        self.assertEqual(regraded["counts"]["subject_launches"], 0)
        self.assertEqual(replay.executed, [])

        for label, options in (
            ("partial", {"observed_body": "alpha\n"}),
            ("failed", {"status": "failed"}),
        ):
            with self.subTest(label=label):
                output = self.root / label
                callbacks = FixtureReadCallbacks(output, **options)
                report = run_evaluations(
                    config(output), {}, [fixture_read_case()], [row("codex")],
                    repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
                )
                self.assertEqual(report["counts"]["behavior_fails"], 1, report)
                self.assertEqual(report["counts"]["infrastructure_invalid"], 0, report)
                observation = json.loads((next((output / "attempts").iterdir()) /
                                          "capture.json").read_text())["payload"]["observation"]
                self.assertFalse(any(item["path"] == FIXTURE_READ_PATH
                                     for item in file_accesses(observation)))

        launch = attempt / "launch-prepared.json"
        launch.write_text(launch.read_text() + " ")
        with self.assertRaisesRegex(ValueError, "raw evidence changed since capture"):
            run_evaluations(
                config(self.output), {}, [changed], [row("codex")], repo_root=self.repo,
                prepare=replay.prepare, execute=replay.execute,
            )

    def test_trigger_uses_stable_row_identity_and_stored_stage_for_regrade(self):
        value = case()
        value["layer"] = "trigger"
        value["hosts"]["claude"]["skill"] = "alpha"
        value["checks"].append({"id": "selected", "requirement": "r1", "type": "selection",
                                "expected": ["alpha"], "allowed_extra": []})
        stages = []
        captured_activations = []

        def qualify(stage, observation):
            stages.append(stage)
            captured_activations.append(observation["activations"])
            qualified = copy.deepcopy(observation)
            qualified["activations"] = ["alpha"]
            metadata = dict(qualified.get("native_metadata") or {})
            metadata["trigger_qualification"] = {"stage_root": str(stage.stage_root)}
            qualified["native_metadata"] = metadata
            return qualified

        first = FakeCallbacks(self.output)
        with mock.patch("native_eval_execution.qualify_trigger_observation", side_effect=qualify):
            initial = run_evaluations(config(self.output), {}, [value], [row()], repo_root=self.repo,
                                      prepare=first.prepare, execute=first.execute)
        self.assertEqual(initial["counts"]["passes"], 1)
        self.assertEqual(first.trial_identities, [
            'native-eval-row/v1:{"case_id":"case.one","host":"claude","mode":"plugin","trial":1}'
        ])
        original_stage_root = stages[0].stage_root
        rebound = []

        def rebind(runtime_identity, *, attempt_dir):
            rebound.append((runtime_identity, Path(attempt_dir)))
            return stages[0]

        changed = copy.deepcopy(value)
        changed["checks"][0]["pattern"] = "never-matches"
        resumed = FakeCallbacks(self.output)
        with mock.patch("native_eval_execution.qualify_trigger_observation", side_effect=qualify), \
                mock.patch("native_eval_execution.trigger_stage_from_runtime_identity",
                           side_effect=rebind):
            report = run_evaluations(config(self.output), {}, [changed], [row()], repo_root=self.repo,
                                     prepare=resumed.prepare, execute=resumed.execute)
        self.assertEqual(report["counts"]["behavior_fails"], 1)
        self.assertEqual(report["counts"]["regraded"], 1)
        self.assertEqual(resumed.executed, [])
        self.assertEqual(resumed.trial_identities, first.trial_identities)
        self.assertEqual(stages[1].stage_root, original_stage_root)
        self.assertEqual(rebound[0][1], original_stage_root.parent)
        self.assertEqual(captured_activations, [["alpha"], ["alpha"]])

    def test_claude_explicit_activation_is_bound_fresh_and_replayed_without_launch(self):
        value = claude_activation_case()
        callbacks = ClaudeActivationCallbacks(self.output)
        initial = run_evaluations(
            config(self.output), {}, [value], [row()], repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(initial["counts"]["passes"], 1, initial)
        attempt = next((self.output / "attempts").iterdir())
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        self.assertIn("claude_activation_session", capture["evidence"])
        self.assertIn("claude_activation_witness", capture["evidence"])
        observed = capture["observation"]
        self.assertEqual(observed["activations"], ["static-skill"])
        self.assertEqual(
            observed["native_metadata"]["claude_explicit_activation"]["authority"],
            "claude-session-loader",
        )

        resumed = ClaudeActivationCallbacks(self.output)
        source_sha = execution._source_sha

        def changed_activation_source(path):
            return "f" * 64 if Path(path).name == "native_eval_claude_activation.py" \
                else source_sha(path)

        with mock.patch("native_eval_execution._source_sha",
                        side_effect=changed_activation_source):
            replay = run_evaluations(
                config(self.output), {}, [value], [row()], repo_root=self.repo,
                prepare=resumed.prepare, execute=resumed.execute,
            )
        self.assertEqual(replay["counts"]["regraded"], 1, replay)
        self.assertEqual(replay["counts"]["passes"], 1, replay)
        self.assertEqual(replay["counts"]["subject_launches"], 0)
        self.assertEqual(resumed.executed, [])
        interpretation = next((attempt / "grades").glob("*/interpretation.json"))
        replayed = json.loads(interpretation.read_text())["observation"]
        self.assertEqual(replayed["activations"], ["static-skill"])

    def test_claude_activation_binding_rehydrates_only_bound_python_launcher(self):
        value = claude_activation_case()
        attempt = self.root / "activation-relocation"
        cwd = attempt / "plugin"
        prompt = (
            f"/{CLAUDE_MANUAL_SKILL} invoke "
            "<attempt_dir>/plugin/bin/python3 -m speckit_pro_runner < request.json"
        )
        source = {
            "path": "skills/static-skill/SKILL.md",
            "bytes": len(CLAUDE_MANUAL_SOURCE),
            "sha256": hashlib.sha256(CLAUDE_MANUAL_SOURCE).hexdigest(),
        }
        launch = {
            "host": "claude", "staging_dir": str(attempt), "cwd": str(cwd),
            "runtime_identity": {"settings": {"claude_explicit_activation": {
                "schema_version": "native-claude-explicit-activation-input/v1",
                "skill": CLAUDE_MANUAL_SKILL,
                "canonical_activation": "static-skill",
                "prompt": prompt,
                "skill_source": source,
            }}},
        }
        binding = execution._claude_activation_binding(value, "claude", launch)
        self.assertEqual(
            binding["prompt"],
            f"/{CLAUDE_MANUAL_SKILL} invoke {cwd / 'bin' / 'python3'} "
            "-m speckit_pro_runner < request.json",
        )

        malformed = copy.deepcopy(launch)
        malformed["runtime_identity"]["settings"]["claude_explicit_activation"][
            "prompt"
        ] = prompt.replace("plugin/bin/python3", "other/bin/python3")
        with self.assertRaisesRegex(ValueError, "relocation is malformed"):
            execution._claude_activation_binding(value, "claude", malformed)

    def test_claude_missing_session_is_incomplete_but_malformed_session_is_invalid(self):
        value = claude_activation_case()
        missing_output = self.root / "missing-claude-session"
        missing = ClaudeActivationCallbacks(missing_output, session="missing")
        report = run_evaluations(
            config(missing_output), {}, [value], [row()], repo_root=self.repo,
            prepare=missing.prepare, execute=missing.execute,
        )
        self.assertEqual(report["counts"]["incomplete"], 1, report)
        attempt = next((missing_output / "attempts").iterdir())
        self.assertFalse((attempt / "capture.json").exists())
        self.assertTrue((attempt / "raw-raw_trace.jsonl").is_file())
        self.assertTrue((attempt / "claude-activation-witness.json").is_file())

        malformed_output = self.root / "malformed-claude-session"
        malformed = ClaudeActivationCallbacks(malformed_output, session="malformed")
        report = run_evaluations(
            config(malformed_output), {}, [value], [row()], repo_root=self.repo,
            prepare=malformed.prepare, execute=malformed.execute,
        )
        self.assertEqual(report["counts"]["infrastructure_invalid"], 1, report)
        attempt = next((malformed_output / "attempts").iterdir())
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        self.assertIn("claude_activation_session", capture["evidence"])
        self.assertIn("direct loader injection", capture["error"])

    def test_claude_historical_capture_without_activation_raw_needs_renormalization(self):
        value = claude_activation_case()
        callbacks = ClaudeActivationCallbacks(self.output)
        initial = run_claude_activation_without_retained_refs(
            self.output, self.repo, value, callbacks,
        )
        self.assertEqual(initial["counts"]["passes"], 1, initial)

        changed = copy.deepcopy(value)
        changed["checks"][0]["pattern"] = "do.e"
        resumed = ClaudeActivationCallbacks(self.output)
        replay = run_evaluations(
            config(self.output), {}, [changed], [row()], repo_root=self.repo,
            prepare=resumed.prepare, execute=resumed.execute,
        )
        self.assertEqual(replay["counts"]["infrastructure_invalid"], 1, replay)
        self.assertEqual(replay["counts"]["subject_launches"], 0)
        self.assertIn("cannot recover Claude activation evidence", replay["results"][0]["reason"])
        self.assertEqual(resumed.executed, [])

    def test_claude_activation_is_recovered_from_bound_retained_framework_tree(self):
        value = claude_activation_case()
        retained_root = self.root / "e-recoverable"
        callbacks = RecoverableClaudeActivationCallbacks(self.output, retained_root)
        initial = run_claude_activation_without_retained_refs(
            self.output, self.repo, value, callbacks,
        )
        self.assertEqual(initial["counts"]["passes"], 1, initial)

        changed = copy.deepcopy(value)
        changed["checks"][0]["pattern"] = "do.e"
        resumed = RecoverableClaudeActivationCallbacks(self.output, retained_root)
        replay = run_evaluations(
            config(self.output), {}, [changed], [row()], repo_root=self.repo,
            prepare=resumed.prepare, execute=resumed.execute,
        )
        self.assertEqual(replay["counts"]["regraded"], 1, replay)
        self.assertEqual(replay["counts"]["passes"], 1, replay)
        self.assertEqual(replay["counts"]["subject_launches"], 0, replay)
        self.assertEqual(resumed.executed, [])
        captures = [
            json.loads(path.read_text())["payload"]
            for path in (self.output / "attempts").glob("*/capture.json")
        ]
        recovered = [capture for capture in captures
                     if "claude_activation_witness" in capture.get("evidence", {})]
        self.assertEqual(len(recovered), 1, captures)
        self.assertIn("claude_activation_session", recovered[0]["evidence"])

    def test_trigger_stage_drives_claude_namespace_and_codex_marker_capture(self):
        value = case()
        value["layer"] = "trigger"
        value["hosts"]["claude"]["skill"] = "alpha"
        value["hosts"]["codex"]["skill"] = "alpha"
        value["checks"] = [{"id": "selected", "requirement": "r1", "type": "selection",
                            "expected": ["alpha"], "allowed_extra": []}]
        observed = {}

        def retain_qualification(stage, observation):
            observed[stage.host] = copy.deepcopy(observation)
            return observation

        callbacks = FakeCallbacks(self.output)
        with mock.patch("native_eval_execution.qualify_trigger_observation",
                        side_effect=retain_qualification), \
                mock.patch("native_eval_execution.parse_native_skill_injections") as parse_skills, \
                mock.patch("native_eval_execution.collect_native_skill_injections") as collect_skills:
            report = run_evaluations(
                config(self.output), {}, [value], [row("claude"), row("codex")],
                repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
            )
        parse_skills.assert_not_called()
        collect_skills.assert_not_called()
        self.assertEqual(report["counts"]["passes"], 2)
        self.assertEqual(observed["claude"]["activations"], ["alpha"])
        self.assertEqual(observed["codex"]["activations"], ["alpha"])
        self.assertEqual(observed["claude"]["tool_calls"][0]["input"]["skill"],
                         "speckit-pro-trigger:alpha")

    def test_git_grader_source_changes_only_cases_using_final_state_checks(self):
        ordinary = case()
        git_case = copy.deepcopy(ordinary)
        git_case["checks"] = [{"type": "native_git_final_state"}]
        original = execution._source_sha
        for host in ("claude", "codex"):
            identities = []
            for revision in ("a" * 64, "b" * 64):
                def source_sha(path):
                    return revision if Path(path).name == "native_eval_git_grading.py" else original(path)
                with mock.patch.object(execution, "_source_sha", side_effect=source_sha):
                    identities.append(tuple(execution._grader_identity(value, host, "judge-test", None)
                                            for value in (ordinary, git_case)))
            with self.subTest(host=host):
                self.assertEqual(identities[0][0], identities[1][0])
                self.assertNotEqual(identities[0][1], identities[1][1])

    def test_catalog_validation_source_is_part_of_both_hosts_grading_identity(self):
        original = execution._source_sha
        for host in ("claude", "codex"):
            identities = []
            for revision in ("a" * 64, "b" * 64):
                def source_sha(path):
                    return revision if Path(path).name == "native_eval_catalog.py" else original(path)
                with mock.patch.object(execution, "_source_sha", side_effect=source_sha):
                    identities.append(execution._grader_identity(case(), host, "judge-test", None))
            with self.subTest(host=host):
                self.assertNotEqual(*identities)

    def test_codex_trigger_parser_source_changes_only_relevant_grader_and_regrades_capture(self):
        value = case()
        value["layer"] = "trigger"
        value["hosts"]["claude"]["skill"] = "alpha"
        value["hosts"]["codex"]["skill"] = "alpha"
        value["checks"] = [{"id": "selected", "requirement": "r1", "type": "selection",
                            "expected": ["alpha"], "allowed_extra": []}]
        ordinary = case()
        original_source_sha = execution._source_sha

        def identities(parser_sha):
            def source_sha(path):
                path = Path(path)
                if path.name == "run_codex_evals.py" and path.parent.name == "layer2-trigger":
                    return parser_sha
                return original_source_sha(path)

            with mock.patch.object(execution, "_source_sha", side_effect=source_sha):
                return {
                    "codex_trigger": execution._grader_identity(value, "codex", "judge-test", None),
                    "claude_trigger": execution._grader_identity(value, "claude", "judge-test", None),
                    "codex_ordinary": execution._grader_identity(ordinary, "codex", "judge-test", None),
                }, source_sha

        before, source_a = identities("a" * 64)
        after, source_b = identities("b" * 64)
        self.assertNotEqual(before["codex_trigger"], after["codex_trigger"])
        self.assertEqual(before["claude_trigger"], after["claude_trigger"])
        self.assertEqual(before["codex_ordinary"], after["codex_ordinary"])

        stages = []

        def qualify(stage, observation):
            stages.append(stage)
            qualified = copy.deepcopy(observation)
            qualified["activations"] = ["alpha"]
            return qualified

        first = FakeCallbacks(self.output)
        with mock.patch.object(execution, "_source_sha", side_effect=source_a), \
                mock.patch.object(execution, "qualify_trigger_observation", side_effect=qualify):
            initial = run_evaluations(config(self.output), {}, [value], [row("codex")],
                                      repo_root=self.repo, prepare=first.prepare, execute=first.execute)
        self.assertEqual(initial["counts"]["passes"], 1, initial)

        resumed = FakeCallbacks(self.output)
        with mock.patch.object(execution, "_source_sha", side_effect=source_b), \
                mock.patch.object(execution, "qualify_trigger_observation", side_effect=qualify), \
                mock.patch.object(execution, "trigger_stage_from_runtime_identity",
                                  return_value=stages[0]):
            replay = run_evaluations(config(self.output), {}, [value], [row("codex")],
                                     repo_root=self.repo, prepare=resumed.prepare,
                                     execute=resumed.execute)
        self.assertEqual(replay["counts"]["passes"], 1, replay)
        self.assertEqual(replay["counts"]["regraded"], 1)
        self.assertEqual(replay["counts"]["subject_launches"], 0)
        self.assertEqual(resumed.executed, [])

    def test_codex_exact_383_byte_native_injection_uses_adapter_witness_contract(self):
        self.assertEqual(len(SKILL_CANARY.encode("utf-8")), 383)
        value = case()
        value["hosts"]["codex"]["skill"] = "native-eval-canary"
        value["checks"].append({
            "id": "selected", "requirement": "r1", "type": "selection",
            "expected": ["native-eval-canary"], "allowed_extra": [],
        })
        callbacks = SkillInjectionCallbacks(self.output)

        with mock.patch("native_eval_execution.collect_native_skill_injections",
                        wraps=execution.collect_native_skill_injections) as collect:
            report = run_evaluations(
                config(self.output), {}, [value], [row("codex")], repo_root=self.repo,
                prepare=callbacks.prepare, execute=callbacks.execute,
            )
        collect.assert_called_once()
        self.assertIsNone(collect.call_args.kwargs["plugin_name"])

        self.assertEqual(report["counts"]["passes"], 1, report)
        self.assertEqual(len(callbacks.prepared_objects[0].runtime_identity["settings"]
                             ["skill_read_witnesses"]), 12)
        self.assertEqual(callbacks.evidence_roots, [self.output.resolve()])
        attempt = next((self.output / "attempts").iterdir())
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        observation = capture["observation"]
        self.assertEqual(observation["activations"], ["native-eval-canary"])
        proof = observation["native_metadata"]["codex_skill_injections"]
        self.assertEqual(proof["status"], "qualified")
        self.assertEqual(proof["injections"][0]["source_bytes"], 383)
        self.assertNotIn(SKILL_CANARY, json.dumps(proof))
        rollout_ref = capture["evidence"][f"codex_rollout_{ROOT_THREAD.replace('-', '_')}"]
        retained = attempt / rollout_ref["path"]
        source = next(callbacks.codex_home.glob(f"sessions/**/rollout-*-{ROOT_THREAD}.jsonl"))
        self.assertEqual(retained.read_bytes(), source.read_bytes())
        self.assertEqual(rollout_ref["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())

    def test_codex_controller_plugin_name_binds_fresh_and_retained_rollout_parsing(self):
        value = case()
        callbacks = SkillInjectionCallbacks(self.output, plugin_name="speckit-pro")
        with mock.patch("native_eval_execution.collect_native_skill_injections",
                        wraps=execution.collect_native_skill_injections) as collect:
            initial = run_evaluations(
                config(self.output), {}, [value], [row("codex")], repo_root=self.repo,
                prepare=callbacks.prepare, execute=callbacks.execute,
            )
        self.assertEqual(initial["counts"]["passes"], 1, initial)
        self.assertEqual(collect.call_args.kwargs["plugin_name"], "speckit-pro")

        changed = copy.deepcopy(value)
        changed["checks"][0]["pattern"] = "do.e"
        replay_callbacks = SkillInjectionCallbacks(self.output, plugin_name="speckit-pro")
        with mock.patch("native_eval_execution.parse_native_skill_injections",
                        wraps=execution.parse_native_skill_injections) as parse:
            replay = run_evaluations(
                config(self.output), {}, [changed], [row("codex")], repo_root=self.repo,
                prepare=replay_callbacks.prepare, execute=replay_callbacks.execute,
            )
        self.assertEqual(replay["counts"]["passes"], 1, replay)
        self.assertEqual(replay["counts"]["regraded"], 1)
        self.assertEqual(replay["counts"]["subject_launches"], 0)
        self.assertEqual(replay_callbacks.executed, [])
        self.assertEqual(parse.call_args.kwargs["plugin_name"], "speckit-pro")

    def test_codex_controller_plugin_name_rejects_changed_protected_tree(self):
        value = case()
        callbacks = SkillInjectionCallbacks(
            self.output, plugin_name="speckit-pro", tamper_plugin_manifest=True,
        )
        report = run_evaluations(
            config(self.output), {}, [value], [row("codex")], repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(report["counts"]["infrastructure_invalid"], 1, report)
        self.assertIn(".agents controls changed", report["results"][0]["reason"])

    def test_codex_controller_plugin_manifest_is_strict_and_canonical(self):
        for label, payload in (
            ("duplicate", '{"name":"speckit-pro","name":"other"}'),
            ("noncanonical", '{"name":"SpecKit-Pro"}'),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                workspace = Path(directory).resolve()
                manifest_dir = workspace / ".agents" / ".codex-plugin"
                manifest_dir.mkdir(parents=True)
                (workspace / ".codex").mkdir()
                (manifest_dir / "plugin.json").write_text(payload)
                settings = {
                    "codex_runtime": {"schema_version": "fake-canonical/v1"},
                    "protected_control_trees": {
                        ".agents": execution._tree_digest(workspace / ".agents"),
                        ".codex": execution._tree_digest(workspace / ".codex"),
                    },
                }
                prepared = SimpleNamespace(
                    cwd=workspace, runtime_identity={"settings": settings},
                )
                with self.assertRaisesRegex(ValueError, "manifest|plugin name"):
                    execution._codex_rollout_plugin_name(prepared)

    def test_codex_sibling_native_injection_is_counted_as_a_real_extra_activation(self):
        value = case()
        value["hosts"]["codex"]["skill"] = "native-eval-canary"
        value["checks"].append({
            "id": "selected", "requirement": "r1", "type": "selection",
            "expected": ["native-eval-canary"], "allowed_extra": [],
        })
        callbacks = SkillInjectionCallbacks(self.output, sibling_injection=True)

        report = run_evaluations(
            config(self.output), {}, [value], [row("codex")], repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
        )

        self.assertEqual(report["counts"]["behavior_fails"], 1, report)
        attempt = next((self.output / "attempts").iterdir())
        observation = json.loads((attempt / "capture.json").read_text())["payload"]["observation"]
        self.assertEqual(observation["activations"],
                         ["native-eval-canary", "sibling-skill"])

    def test_codex_native_injection_absence_stale_history_and_malformed_body_are_distinct(self):
        value = case()
        value["checks"].append({
            "id": "selected", "requirement": "r1", "type": "selection",
            "expected": [], "allowed_extra": [],
        })
        absent = SkillInjectionCallbacks(self.root / "absent", no_injection=True)
        absent_report = run_evaluations(
            config(self.root / "absent"), {}, [value], [row("codex")], repo_root=self.repo,
            prepare=absent.prepare, execute=absent.execute,
        )
        self.assertEqual(absent_report["counts"]["passes"], 1, absent_report)
        attempt = next((self.root / "absent" / "attempts").iterdir())
        proof = json.loads((attempt / "capture.json").read_text())["payload"]["observation"] \
            ["native_metadata"]["codex_skill_injections"]
        self.assertEqual((proof["status"], proof["activations"]), ("not_observed", []))

        expected = copy.deepcopy(value)
        expected["checks"][-1]["expected"] = ["native-eval-canary"]
        stale = SkillInjectionCallbacks(self.root / "stale", stale=True)
        stale_report = run_evaluations(
            config(self.root / "stale"), {}, [expected], [row("codex")], repo_root=self.repo,
            prepare=stale.prepare, execute=stale.execute,
        )
        self.assertEqual(stale_report["counts"]["behavior_fails"], 1, stale_report)

        malformed = SkillInjectionCallbacks(self.root / "malformed-turn", malformed=True)
        malformed_report = run_evaluations(
            config(self.root / "malformed-turn"), {}, [expected], [row("codex")],
            repo_root=self.repo, prepare=malformed.prepare, execute=malformed.execute,
        )
        self.assertEqual(malformed_report["counts"]["infrastructure_invalid"], 1,
                         malformed_report)

    def test_codex_native_skill_bodies_are_not_sent_to_semantic_judge(self):
        value = case(semantic=True)
        callbacks = SkillInjectionCallbacks(self.output)
        requests = []

        def judge(request, _grade_dir, _model):
            requests.append(copy.deepcopy(request))
            return {"meaning": {"passed": True, "evidence": ["final_text"]}}

        judge.runtime_identity = {"schema": "fake-native-judge/v1", "runtime": "stable"}
        report = run_evaluations(
            config(self.output), {}, [value], [row("codex")], repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute, judge_execute=judge,
        )
        self.assertEqual(report["counts"]["passes"], 1, report)
        self.assertEqual(len(requests), 1)
        self.assertNotIn(SKILL_CANARY, json.dumps(requests[0]))
        self.assertEqual(requests[0]["evidence"]["activations"], ["native-eval-canary"])

    def test_codex_regrade_uses_original_launch_cwd_and_witnesses_without_subject(self):
        value = case()
        value["hosts"]["codex"]["skill"] = "native-eval-canary"
        value["checks"].append({
            "id": "selected", "requirement": "r1", "type": "selection",
            "expected": ["native-eval-canary"], "allowed_extra": [],
        })
        first = SkillInjectionCallbacks(self.output)
        initial = run_evaluations(
            config(self.output), {}, [value], [row("codex")], repo_root=self.repo,
            prepare=first.prepare, execute=first.execute,
        )
        self.assertEqual(initial["counts"]["passes"], 1, initial)
        attempt = next((self.output / "attempts").iterdir())
        original_launch = json.loads((attempt / "launch-prepared.json").read_text())

        resumed = SkillInjectionCallbacks(self.output)
        source_sha = execution._source_sha

        def changed_qualifier_source(path):
            return "f" * 64 if Path(path).name == "native_eval_codex_rollouts.py" else source_sha(path)

        with mock.patch("native_eval_execution._source_sha",
                        side_effect=changed_qualifier_source):
            report = run_evaluations(
                config(self.output), {}, [value], [row("codex")], repo_root=self.repo,
                prepare=resumed.prepare, execute=resumed.execute,
            )

        self.assertEqual(resumed.executed, [])
        self.assertEqual(report["counts"]["subject_launches"], 0)
        self.assertEqual(report["counts"]["regraded"], 1)
        self.assertEqual(report["counts"]["passes"], 1, report)
        interpretations = list((attempt / "grades").glob("*/interpretation.json"))
        self.assertEqual(len(interpretations), 1)
        interpreted = json.loads(interpretations[0].read_text())["observation"]
        native_path = interpreted["native_metadata"]["codex_skill_injections"]["injections"][0]["native_path"]
        self.assertTrue(native_path.startswith(original_launch["cwd"] + "/"), native_path)
        self.assertNotEqual(original_launch["cwd"],
                            str(resumed.prepared_objects[0].cwd))

    def test_codex_changed_source_model_or_cwd_never_reuses_old_pass(self):
        value = case()
        scenarios = {
            "source": ({"target_text": SKILL_CANARY + "changed\n"}, {}),
            "model": ({}, {"codex_model": "codex-changed"}),
            "cwd": ({"cwd_name": "changed-workspace"}, {}),
        }
        for label, (callback_options, config_options) in scenarios.items():
            with self.subTest(label=label):
                output = self.root / label
                first = SkillInjectionCallbacks(output)
                initial = run_evaluations(
                    config(output), {}, [value], [row("codex")], repo_root=self.repo,
                    prepare=first.prepare, execute=first.execute,
                )
                self.assertEqual(initial["counts"]["passes"], 1, initial)
                changed = SkillInjectionCallbacks(output, exit_codes=[2], **callback_options)
                report = run_evaluations(
                    config(output, **config_options), {}, [value], [row("codex")],
                    repo_root=self.repo, prepare=changed.prepare, execute=changed.execute,
                )
                self.assertEqual(report["counts"]["reused"], 0)
                self.assertEqual(report["counts"]["subject_launches"], 1)
                self.assertEqual(report["counts"]["infrastructure_invalid"], 1)

    def test_codex_missing_or_malformed_witness_and_cwd_fail_closed(self):
        value = case()
        for contract in ("missing", "malformed", "bad-cwd"):
            with self.subTest(contract=contract):
                output = self.root / contract
                callbacks = SkillInjectionCallbacks(output, witness_contract=contract)
                report = run_evaluations(
                    config(output), {}, [value], [row("codex")], repo_root=self.repo,
                    prepare=callbacks.prepare, execute=callbacks.execute,
                )
                self.assertEqual(report["counts"]["passes"], 0)
                self.assertEqual(report["counts"]["infrastructure_invalid"], 1, report)

    def test_codex_historical_capture_without_native_rollout_needs_renormalization(self):
        value = case()
        first = SkillInjectionCallbacks(self.output)
        with mock.patch("native_eval_execution._rollout_evidence", return_value={}):
            initial = run_evaluations(
                config(self.output), {}, [value], [row("codex")], repo_root=self.repo,
                prepare=first.prepare, execute=first.execute,
            )
        self.assertEqual(initial["counts"]["passes"], 1, initial)

        changed = copy.deepcopy(value)
        changed["requirements"][0]["description"] = "requires current interpretation"
        resumed = SkillInjectionCallbacks(self.output)
        report = run_evaluations(
            config(self.output), {}, [changed], [row("codex")], repo_root=self.repo,
            prepare=resumed.prepare, execute=resumed.execute,
        )

        self.assertEqual(resumed.executed, [])
        self.assertEqual(report["counts"]["subject_launches"], 0)
        self.assertEqual(report["counts"]["infrastructure_invalid"], 1)
        self.assertTrue(report["results"][0]["reason"].startswith("needs_renormalization:"), report)

    def test_pair_semantic_criteria_share_one_codex_job_and_pair_only_regrade(self):
        value = pair_case(self.repo)
        artifacts = {"claude": pair_workflow("alpha"), "codex": pair_workflow("beta")}
        first_callbacks = PairCallbacks(self.output, artifacts=artifacts)
        first_judge = PairJudge([True])
        initial = run_evaluations(
            config(self.output), {}, [value], [row("claude"), row("codex")], repo_root=self.repo,
            prepare=first_callbacks.prepare, execute=first_callbacks.execute,
            judge_execute=first_judge,
        )
        self.assertEqual(initial["pair_counts"]["passes"], 1, initial)
        self.assertEqual(initial["pair_counts"]["judge_calls"], 1)
        self.assertEqual(len(first_judge.requests), 1)
        self.assertEqual(len(first_judge.requests[0]["semantic_criteria"]), 2)
        self.assertEqual(initial["providers"]["codex"]["pair_judge_calls"], 1)

        changed = pair_case(self.repo, rubric="Reject any materially different finding.")
        resumed_callbacks = PairCallbacks(self.output, artifacts=artifacts)
        changed_judge = PairJudge([False])
        changed_report = run_evaluations(
            config(self.output), {}, [changed], [row("claude"), row("codex")], repo_root=self.repo,
            prepare=resumed_callbacks.prepare, execute=resumed_callbacks.execute,
            judge_execute=changed_judge,
        )
        self.assertEqual(resumed_callbacks.executed, [])
        self.assertEqual(changed_report["counts"]["subject_launches"], 0)
        self.assertEqual(changed_report["pair_counts"]["regraded"], 1)
        self.assertEqual(changed_report["pair_counts"]["behavior_fails"], 1)
        self.assertEqual(changed_report["exit_status"], 1)

        cached_callbacks = PairCallbacks(self.output, artifacts=artifacts)
        cached_judge = PairJudge([])
        cached = run_evaluations(
            config(self.output), {}, [changed], [row("claude"), row("codex")], repo_root=self.repo,
            prepare=cached_callbacks.prepare, execute=cached_callbacks.execute,
            judge_execute=cached_judge,
        )
        self.assertEqual(cached_callbacks.executed, [])
        self.assertEqual(cached_judge.requests, [])
        self.assertEqual(cached["pair_counts"]["reused"], 1)
        self.assertEqual(cached["pair_counts"]["behavior_fails"], 1)

    def test_pair_preserves_both_wrong_failure_without_semantic_judge(self):
        value = pair_case(self.repo, independent_pattern="RIGHT")
        artifacts = {"claude": pair_workflow("same"), "codex": pair_workflow("same")}
        callbacks = PairCallbacks(self.output, artifacts=artifacts, texts=["WRONG", "WRONG"])
        judge = PairJudge([])
        report = run_evaluations(
            config(self.output), {}, [value], [row("claude"), row("codex")], repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute, judge_execute=judge,
        )
        self.assertEqual(report["counts"]["behavior_fails"], 2)
        self.assertEqual(report["pair_counts"]["behavior_fails"], 1)
        self.assertEqual(report["pair_counts"]["judge_calls"], 0)
        self.assertEqual(judge.requests, [])
        self.assertEqual(report["exit_status"], 1)

        reused = run_evaluations(
            config(self.output), {}, [value], [row("claude"), row("codex")], repo_root=self.repo,
            prepare=PairCallbacks(self.output, artifacts=artifacts).prepare,
            execute=lambda *_args: self.fail("cached failure relaunched a subject"),
            judge_execute=judge,
        )
        self.assertEqual(reused["pair_counts"]["reused"], 1)
        self.assertEqual(reused["pair_counts"]["behavior_fails"], 1)

    def test_pair_request_checkpoint_failure_is_terminal_without_judge_call(self):
        value = pair_case(self.repo)
        artifacts = {"claude": pair_workflow("alpha"), "codex": pair_workflow("beta")}
        callbacks = PairCallbacks(self.output, artifacts=artifacts)
        judge = PairJudge([True])
        original_write = execution._write_json_once

        def fail_pair_request(path, payload):
            if Path(path).name == "judge-request.json":
                raise OSError("synthetic pair request checkpoint failure")
            return original_write(path, payload)

        with mock.patch.object(execution, "_write_json_once", side_effect=fail_pair_request):
            report = run_evaluations(
                config(self.output), {}, [value], [row("claude"), row("codex")],
                repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
                judge_execute=judge,
            )

        self.assertEqual(report["pair_counts"]["infrastructure_invalid"], 1, report)
        self.assertEqual(report["pair_counts"]["incomplete"], 0, report)
        self.assertEqual(report["pair_counts"]["judge_calls"], 0)
        self.assertEqual(report["providers"]["codex"]["pair_judge_calls"], 0)
        self.assertEqual(judge.requests, [])
        self.assertFalse(report["pairs"][0]["judge_called"])
        self.assertIn("synthetic pair request checkpoint failure", report["pairs"][0]["reason"])
        grade = next((self.output / "pairs").glob("*/grade-*.json"))
        self.assertNotIn("evidence", json.loads(grade.read_text())["payload"])

    def test_pair_waits_for_both_independent_semantic_arm_grades(self):
        value = pair_case(self.repo)
        value["checks"].append({
            "id": "independent-semantic", "requirement": "r1", "type": "semantic",
            "rubric": "The artifact independently satisfies the requested workflow.",
        })
        artifacts = {"claude": pair_workflow("alpha"), "codex": pair_workflow("beta")}
        callbacks = PairCallbacks(self.output, artifacts=artifacts)
        judge = PairJudge([True, True, True])
        report = run_evaluations(
            config(self.output), {}, [value], [row("claude"), row("codex")], repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute, judge_execute=judge,
        )
        self.assertEqual(report["counts"]["passes"], 2)
        self.assertEqual(report["counts"]["judge_calls"], 2)
        self.assertEqual(report["pair_counts"]["passes"], 1)
        self.assertEqual(report["pair_counts"]["judge_calls"], 1)
        self.assertEqual(report["providers"]["codex"]["judge_calls"], 3)
        self.assertEqual(sorted(len(request["semantic_criteria"]) for request in judge.requests),
                         [1, 1, 2])

    def test_pair_uses_runtime_bound_subject_grader_identity_and_resumes(self):
        value = pair_case(self.repo)
        value["checks"].append({
            "id": "independent-semantic", "requirement": "r1", "type": "semantic",
            "rubric": "The artifact independently satisfies the requested workflow.",
        })
        artifacts = {"claude": pair_workflow("alpha"), "codex": pair_workflow("beta")}
        callbacks = PairCallbacks(self.output, artifacts=artifacts)
        judge = PairJudge([True, True, True])
        original_grader_identity = execution._grader_identity

        def runtime_bound_grader(*args):
            identity = original_grader_identity(*args)
            if len(args) == 5 and args[1] == "claude" and args[4] is not None:
                return hashlib.sha256(f"{identity}:runtime-bound".encode()).hexdigest()
            return identity

        with mock.patch.object(execution, "_grader_identity",
                               side_effect=runtime_bound_grader):
            report = run_evaluations(
                config(self.output), {}, [value], [row("claude"), row("codex")],
                repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
                judge_execute=judge,
            )
        self.assertEqual(report["counts"]["passes"], 2, report)
        self.assertEqual(report["pair_counts"]["passes"], 1, report)
        self.assertEqual(report["pair_counts"]["judge_calls"], 1, report)

        resumed_callbacks = PairCallbacks(self.output, artifacts=artifacts)
        resumed_judge = PairJudge([])
        with mock.patch.object(execution, "_grader_identity",
                               side_effect=runtime_bound_grader):
            resumed = run_evaluations(
                config(self.output), {}, [value], [row("claude"), row("codex")],
                repo_root=self.repo, prepare=resumed_callbacks.prepare,
                execute=lambda *_args: self.fail("cached subject relaunched"),
                judge_execute=resumed_judge,
            )
        self.assertEqual(resumed["counts"]["subject_launches"], 0, resumed)
        self.assertEqual(resumed["counts"]["reused"], 2, resumed)
        self.assertEqual(resumed["pair_counts"]["passes"], 1, resumed)
        self.assertEqual(resumed["pair_counts"]["reused"], 1, resumed)
        self.assertEqual(resumed_judge.requests, [])

    def test_pair_missing_or_reordered_arms_is_invalid_without_derived_work(self):
        value = pair_case(self.repo)
        artifacts = {"claude": pair_workflow("same"), "codex": pair_workflow("same")}
        for name, rows in (("missing", [row("claude")]),
                           ("reordered", [row("codex"), row("claude")])):
            with self.subTest(name=name):
                output = self.root / name
                callbacks = PairCallbacks(output, artifacts=artifacts)
                judge = PairJudge([])
                report = run_evaluations(
                    config(output), {}, [value], rows, repo_root=self.repo,
                    prepare=callbacks.prepare, execute=callbacks.execute, judge_execute=judge,
                )
                self.assertEqual(report["pair_counts"]["infrastructure_invalid"], 1)
                self.assertEqual(report["exit_status"], 3)
                self.assertEqual(judge.requests, [])
                self.assertFalse(any((output / "pairs").iterdir()))

    def test_invalid_retry_requires_matching_explicit_status(self):
        broken = FakeCallbacks(self.output, exit_codes=[2], stderr=["transport failed"])
        first = run_evaluations(config(self.output), {}, [case()], [row()], repo_root=self.repo,
                                prepare=broken.prepare, execute=broken.execute)
        self.assertEqual(first["counts"]["infrastructure_invalid"], 1)

        held = FakeCallbacks(self.output)
        second = run_evaluations(config(self.output), {}, [case()], [row()], repo_root=self.repo,
                                 prepare=held.prepare, execute=held.execute)
        self.assertEqual(second["counts"]["subject_launches"], 0)
        self.assertEqual(held.executed, [])

        retried = FakeCallbacks(self.output)
        third = run_evaluations(config(self.output, retry_cases=("case.one",), retry_status="invalid"), {},
                                [case()], [row()], repo_root=self.repo,
                                prepare=retried.prepare, execute=retried.execute)
        self.assertEqual(third["counts"]["retries"], 1)
        self.assertEqual(third["counts"]["passes"], 1)

    def test_semantic_case_is_held_without_judge_and_judged_after_deterministic_pass(self):
        value = case(semantic=True)
        held_callbacks = FakeCallbacks(self.output)
        held = run_evaluations(config(self.output), {}, [value], [row()], repo_root=self.repo,
                               prepare=held_callbacks.prepare, execute=held_callbacks.execute)
        self.assertEqual(held["counts"]["incomplete"], 1)
        self.assertEqual(held["counts"]["subject_launches"], 0)

        calls = []
        callbacks = FakeCallbacks(self.root / "judged")
        judged_config = config(self.root / "judged")

        def judge_execute(request, attempt_dir, model):
            calls.append((request, Path(attempt_dir), model))
            native = Path(attempt_dir) / "native"
            native.mkdir()
            for name, payload in {
                "native-stdout.bin": b"judge stdout", "native-stderr.bin": b"",
                "native-process.json": b'{"exit_code":0}\n',
                "trace.jsonl": b'{"type":"turn.completed"}\n',
                "judge-result.json": b'{"meaning":{"passed":true}}\n',
            }.items():
                (native / name).write_bytes(payload)
            return {"meaning": {"passed": True, "evidence": ["final_text"]}}

        judged = run_evaluations(judged_config, {}, [value], [row()], repo_root=self.repo,
                                 prepare=callbacks.prepare, execute=callbacks.execute, judge_execute=judge_execute)
        self.assertEqual(judged["counts"]["passes"], 1)
        self.assertEqual(judged["counts"]["judge_calls"], 1)
        self.assertEqual(len(calls), 1)
        grade_dir = calls[0][1]
        self.assertEqual(grade_dir.parent.name, "grades")
        attempt = grade_dir.parents[1]
        grade_receipt = next(attempt.glob("grade-*.json"))
        grade_payload = json.loads(grade_receipt.read_text())["payload"]
        self.assertIn("evidence", grade_payload)
        self.assertIn("judge_request", grade_payload["evidence"])
        self.assertIn("judge_response", grade_payload["evidence"])
        self.assertIn("judge_raw_trace", grade_payload["evidence"])
        self.assertIn("judge_process_receipt", grade_payload["evidence"])
        self.assertEqual(judged["limitations"], ["semantic_judge_runtime_identity_unverified"])

        changed = copy.deepcopy(value)
        changed["checks"][1]["rubric"] = "The answer is complete."
        regrade_callbacks = FakeCallbacks(self.root / "judged")
        regraded = run_evaluations(
            judged_config, {}, [changed], [row()], repo_root=self.repo,
            prepare=regrade_callbacks.prepare, execute=regrade_callbacks.execute,
            judge_execute=lambda request, attempt_dir, model: {
                "meaning": {"passed": False, "evidence": ["final_text"]}
            },
        )
        self.assertEqual(regraded["counts"]["regraded"], 1)
        self.assertEqual(regraded["counts"]["subject_launches"], 0)
        self.assertEqual(regraded["counts"]["behavior_fails"], 1)
        self.assertEqual(len(list((attempt / "grades").iterdir())), 2)

    def test_deterministic_failure_never_calls_judge(self):
        value = case(semantic=True, pattern="required")
        callbacks = FakeCallbacks(self.output)
        calls = []
        report = run_evaluations(
            config(self.output), {}, [value], [row()], repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
            judge_execute=lambda *args: calls.append(args),
        )
        self.assertEqual(report["counts"]["behavior_fails"], 1)
        self.assertEqual(calls, [])

    def test_judge_request_build_failure_is_terminal_without_judge_call(self):
        callbacks = FakeCallbacks(self.output)
        calls = []
        with mock.patch.object(
            execution, "build_judge_request",
            side_effect=ValueError("unsupported native tool for semantic judge projection: ToolSearch"),
        ):
            report = run_evaluations(
                config(self.output), {}, [case(semantic=True)], [row()], repo_root=self.repo,
                prepare=callbacks.prepare, execute=callbacks.execute,
                judge_execute=lambda *args: calls.append(args),
            )

        self.assertEqual(report["counts"]["infrastructure_invalid"], 1, report)
        self.assertEqual(report["counts"]["incomplete"], 0, report)
        self.assertEqual(report["counts"]["judge_calls"], 0)
        self.assertEqual(report["providers"]["codex"]["subject_judge_calls"], 0)
        self.assertEqual(calls, [])
        self.assertFalse(report["results"][0]["judge_called"])
        self.assertIn("unsupported native tool", report["results"][0]["reason"])
        attempt = next((self.output / "attempts").iterdir())
        grade = next(attempt.glob("grade-*.json"))
        self.assertNotIn("evidence", json.loads(grade.read_text())["payload"])

    def test_regrade_request_build_failure_is_terminal_without_subject_or_judge_call(self):
        value = case(semantic=True)
        initial_callbacks = FakeCallbacks(self.output)
        initial = run_evaluations(
            config(self.output), {}, [value], [row()], repo_root=self.repo,
            prepare=initial_callbacks.prepare, execute=initial_callbacks.execute,
            judge_execute=lambda *_args: {
                "meaning": {"passed": True, "evidence": ["final_text"]},
            },
        )
        self.assertEqual(initial["counts"]["passes"], 1, initial)
        changed = copy.deepcopy(value)
        changed["checks"][1]["rubric"] = "The answer remains complete."
        replay_callbacks = FakeCallbacks(self.output)
        calls = []
        with mock.patch.object(
            execution, "build_judge_request",
            side_effect=ValueError("synthetic regrade request failure"),
        ):
            replay = run_evaluations(
                config(self.output), {}, [changed], [row()], repo_root=self.repo,
                prepare=replay_callbacks.prepare, execute=replay_callbacks.execute,
                judge_execute=lambda *args: calls.append(args),
            )

        self.assertEqual(replay["counts"]["infrastructure_invalid"], 1, replay)
        self.assertEqual(replay["counts"]["incomplete"], 0, replay)
        self.assertEqual(replay["counts"]["subject_launches"], 0)
        self.assertEqual(replay["counts"]["regraded"], 1)
        self.assertEqual(replay["counts"]["judge_calls"], 0)
        self.assertEqual(replay_callbacks.executed, [])
        self.assertEqual(calls, [])
        self.assertFalse(replay["results"][0]["judge_called"])
        self.assertIn("synthetic regrade request failure", replay["results"][0]["reason"])

    def test_fresh_and_regraded_judges_use_trusted_subject_host_only_as_projection_policy(self):
        value = case(semantic=True)
        callbacks = FakeCallbacks(self.output)
        original_build = execution.build_judge_request
        projected_hosts = []
        requests = []

        def build_request(case_value, observation, approved_aliases=None, *, host=None):
            projected_hosts.append(host)
            return original_build(case_value, observation, approved_aliases, host=host)

        def judge(request, attempt_dir, model):
            requests.append(request)
            return {"meaning": {"passed": True, "evidence": ["final_text"]}}

        with mock.patch.object(execution, "build_judge_request", side_effect=build_request), \
                mock.patch.object(execution, "grade_observation",
                                  wraps=execution.grade_observation) as grade:
            fresh = run_evaluations(
                config(self.output), {}, [value], [row("claude")], repo_root=self.repo,
                prepare=callbacks.prepare, execute=callbacks.execute, judge_execute=judge,
            )
            changed = copy.deepcopy(value)
            changed["checks"][1]["rubric"] = "The answer remains complete."
            replay_callbacks = FakeCallbacks(self.output)
            replay = run_evaluations(
                config(self.output), {}, [changed], [row("claude")], repo_root=self.repo,
                prepare=replay_callbacks.prepare, execute=replay_callbacks.execute, judge_execute=judge,
            )

        self.assertEqual(projected_hosts, ["claude", "claude"], (fresh, replay))
        self.assertEqual([call.kwargs["host"] for call in grade.call_args_list],
                         ["claude", "claude", "claude", "claude"])
        self.assertEqual(len(requests), 2)
        self.assertTrue(all("host" not in request for request in requests))
        self.assertEqual(fresh["counts"]["subject_launches"], 1)
        self.assertEqual(fresh["providers"]["claude"]["judge_calls"], 0)
        self.assertEqual(fresh["providers"]["codex"]["judge_calls"], 1)
        self.assertEqual(replay["counts"]["subject_launches"], 0)
        self.assertEqual(replay["counts"]["regraded"], 1)

    def test_ambiguous_judge_native_receipts_are_explicitly_invalid(self):
        output = self.root / "ambiguous-judge"
        callbacks = FakeCallbacks(output)

        def ambiguous_judge(request, attempt_dir, model):
            grade_dir = Path(attempt_dir)
            (grade_dir / "native").mkdir()
            (grade_dir / "native-stdout.bin").write_bytes(b"root")
            (grade_dir / "native" / "native-stdout.bin").write_bytes(b"nested")
            return {"meaning": {"passed": True, "evidence": ["final_text"]}}

        report = run_evaluations(
            config(output), {}, [case(semantic=True)], [row()], repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute, judge_execute=ambiguous_judge,
        )
        self.assertEqual(report["counts"]["infrastructure_invalid"], 1)
        self.assertEqual(report["counts"]["judge_calls"], 1)
        self.assertTrue(report["results"][0]["judge_called"])
        self.assertIn("evidence is ambiguous", report["results"][0]["reason"])

    def test_auth_error_stops_only_that_provider_queue(self):
        rows = [row("claude", 1), row("claude", 2), row("codex", 1)]
        callbacks = FakeCallbacks(self.output, by_host={
            "claude": ("done", 2, "401 authentication required"),
            "codex": ("done", 0, ""),
        })
        report = run_evaluations(config(self.output), {}, [case()], rows, repo_root=self.repo,
                                 prepare=callbacks.prepare, execute=callbacks.execute)
        self.assertEqual(report["counts"]["subject_launches"], 2, report)
        self.assertEqual(report["counts"]["incomplete"], 1)
        self.assertIn("codex", callbacks.executed)
        self.assertEqual(report["providers"]["claude"]["held"], 1)

    def test_docker_credential_store_refusal_does_not_stop_provider_queue(self):
        message = "the Docker credential store holds a symbolic link inside it"
        self.assertIsNone(execution._classify_text(message, "stderr"))
        self.assertEqual(
            execution._classify_text(message + "; 401 authentication required", "stderr")["kind"],
            "auth",
        )
        rows = [row("claude", 1)]
        callbacks = FakeCallbacks(self.output, by_host={
            "claude": ("done", 1, message),
        })
        report = run_evaluations(
            config(self.output), {}, [case()], rows, repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(report["counts"]["subject_launches"], 1, report)
        self.assertEqual(report["counts"]["infrastructure_invalid"], 1)
        self.assertEqual(report["providers"]["claude"]["held"], 0)
        self.assertNotIn("provider_error", report["results"][0])

    def test_http_status_classifier_does_not_match_digits_inside_timestamp(self):
        for timestamp in ("2026-09-19T18:41:37.674015Z", "2026-09-19T18:42:37.429015Z"):
            with self.subTest(timestamp=timestamp):
                message = f"{timestamp} ERROR codex_core::tools::router: command rejected"
                self.assertIsNone(execution._classify_text(message, "stderr"))
        self.assertEqual(execution._classify_text("HTTP 401", "stderr")["kind"], "auth")
        self.assertEqual(execution._classify_text("HTTP 429", "stderr")["kind"], "quota")

    def test_codex_supplement_preserves_unobserved_completion_and_grading_rejects_it(self):
        observation = {
            "completed": True, "error": None, "final_text": "done", "activations": [],
            "tool_calls": [], "artifacts": {}, "usage": {},
            "native_metadata": {"thread_id": ROOT_THREAD},
        }
        supplement = {
            "root_thread_id": ROOT_THREAD,
            "dispatches": [{
                "id": SPAWN_CALL, "parent_thread_id": ROOT_THREAD,
                "child_thread_id": CHILD_THREAD, "order": 1, "status": "completed",
            }],
            "children": [{
                "thread_id": CHILD_THREAD,
                "native_metadata": {"cwd": str(self.repo.resolve())},
                "tool_calls": [{
                    "id": "post-terminal-command", "name": "command_execution",
                    "input": {"command": ["true"]}, "output": {"exit_code": 0},
                    "success": True, "namespace": None,
                    "native_type": "CommandExecution", "thread_id": CHILD_THREAD,
                    "status": "completed", "native_event_index": 9,
                    "post_terminal_completion": True, "model_observed": False,
                }],
            }],
        }

        execution._merge_codex_supplement(
            observation, supplement, self.repo,
            {ROOT_THREAD: b"", CHILD_THREAD: b""}, False,
        )

        tool = next(
            call for call in observation["tool_calls"]
            if call["id"] == "post-terminal-command"
        )
        self.assertIs(tool["input"]["_native"]["post_terminal_completion"], True)
        self.assertIs(tool["input"]["_native"]["model_observed"], False)
        grade = execution.grade_observation(case(semantic=True), observation)
        self.assertEqual(grade["status"], "invalid", grade)
        self.assertTrue(all(row["verdict"] == "invalid" for row in grade["checks"]))
        self.assertTrue(all("model did not observe" in row["reason"] for row in grade["checks"]))

    def test_codex_root_post_terminal_completion_is_unobserved_and_invalid(self):
        command_id = "exec-root-drained"
        command = ["/bin/zsh", "-c", "ripwire . --quality-delta"]
        raw_root = (json.dumps({
            "timestamp": "2026-09-19T16:36:42Z",
            "type": "event_msg",
            "payload": {
                "type": "item_completed", "thread_id": ROOT_THREAD,
                "turn_id": ROOT_TURN,
                "item": {"type": "CommandExecution", "id": command_id,
                         "command": command},
            },
        }, separators=(",", ":")) + "\n").encode()
        observation = {
            "completed": True, "error": None, "final_text": "done", "activations": [],
            "tool_calls": [{
                "id": "projected-root-command", "name": "command_execution",
                "input": {"command": command}, "output": {"exit_code": 0},
                "success": True, "parent_id": None,
            }],
            "artifacts": {}, "usage": {},
            "native_metadata": {"thread_id": ROOT_THREAD},
        }
        completion = {
            "schema": "codex-post-terminal-command-completion/v2",
            "model_observed": False, "thread_id": ROOT_THREAD,
            "item_id": command_id, "cwd": str(self.repo.resolve()),
            "source": "unified_exec_startup", "status": "completed", "exit_code": 0,
        }
        supplement = {
            "root_thread_id": ROOT_THREAD, "dispatches": [], "children": [],
            "native_metadata": {
                "post_terminal_completions": [completion],
                "rollout_raw_sha256": hashlib.sha256(raw_root).hexdigest(),
            },
        }

        execution._merge_codex_supplement(
            observation, supplement, self.repo, {ROOT_THREAD: raw_root}, False,
        )

        tool = observation["tool_calls"][0]
        self.assertEqual(tool["id"], command_id)
        self.assertFalse(tool["success"])
        self.assertIs(tool["input"]["_native"]["post_terminal_completion"], True)
        self.assertIs(tool["input"]["_native"]["model_observed"], False)
        grade = execution.grade_observation(case(semantic=True), observation)
        self.assertEqual(grade["status"], "invalid", grade)
        self.assertTrue(all(row["verdict"] == "invalid" for row in grade["checks"]))
        self.assertTrue(all("model did not observe" in row["reason"] for row in grade["checks"]))

    def test_codex_root_post_terminal_completion_rejects_bad_identity_sets(self):
        command_id = "exec-root-drained"
        command = ["/bin/zsh", "-c", "ripwire . --quality-delta"]
        raw_root = (json.dumps({
            "timestamp": "2026-09-19T16:36:42Z",
            "type": "event_msg",
            "payload": {
                "type": "item_completed", "thread_id": ROOT_THREAD,
                "turn_id": ROOT_TURN,
                "item": {"type": "CommandExecution", "id": command_id,
                         "command": command},
            },
        }, separators=(",", ":")) + "\n").encode()
        base_observation = {
            "completed": True, "error": None, "final_text": "done", "activations": [],
            "tool_calls": [{
                "id": "projected-root-command", "name": "command_execution",
                "input": {"command": command}, "output": {"exit_code": 0},
                "success": True, "parent_id": None,
            }],
            "artifacts": {}, "usage": {},
            "native_metadata": {"thread_id": ROOT_THREAD},
        }
        completion = {
            "schema": "codex-post-terminal-command-completion/v2",
            "model_observed": False, "thread_id": ROOT_THREAD,
            "item_id": command_id, "cwd": str(self.repo.resolve()),
            "source": "unified_exec_startup", "status": "completed", "exit_code": 0,
        }
        for name, completions in (
            ("duplicate", [completion, copy.deepcopy(completion)]),
            ("unmatched", [{**completion, "item_id": "exec-root-other"}]),
            ("malformed", [{**completion, "model_observed": True}]),
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                supplement = {
                    "root_thread_id": ROOT_THREAD, "dispatches": [], "children": [],
                    "native_metadata": {
                        "post_terminal_completions": completions,
                        "rollout_raw_sha256": hashlib.sha256(raw_root).hexdigest(),
                    },
                }
                execution._merge_codex_supplement(
                    copy.deepcopy(base_observation), supplement, self.repo,
                    {ROOT_THREAD: raw_root}, False,
                )

    def test_nested_codex_merges_exact_owned_rollouts_without_root_duplication(self):
        value = case(resource_class="nested")
        value["checks"].extend([
            {"id": "spawn", "requirement": "r1", "type": "tool_used",
             "name": "subagent", "min": 1, "max": 1},
            {"id": "child-read", "requirement": "r1", "type": "tool_used",
             "name": "command_execution", "min": 1, "max": 1},
            {"id": "child-before-root-write", "requirement": "r1", "type": "tool_order",
             "before": "command_execution", "after": "file_change"},
        ])
        callbacks = NestedCallbacks(self.output)
        with mock.patch("native_eval_execution.collect_native_skill_injections") as collect_skills:
            report = run_evaluations(config(self.output), {}, [value], [row("codex")],
                                     repo_root=self.repo, prepare=callbacks.prepare,
                                     execute=callbacks.execute)
        collect_skills.assert_not_called()
        self.assertEqual(report["counts"]["passes"], 1, report)
        attempt = next((self.output / "attempts").iterdir())
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        calls = capture["observation"]["tool_calls"]
        self.assertEqual([call["name"] for call in calls].count("subagent"), 1)
        self.assertNotIn("spawn_agent", [call["name"] for call in calls])
        self.assertEqual([call["id"] for call in calls].count("root-write"), 1)
        self.assertEqual(next(call for call in calls if call["id"] == "wait-call")["name"], "wait")
        spawn = next(call for call in calls if call["id"] == SPAWN_CALL)
        child = next(call for call in calls if call["id"] == "exec-child")
        self.assertEqual(child["parent_id"], spawn["id"])
        self.assertGreater(child["position"], spawn["position"])
        self.assertLess(child["position"], next(call for call in calls
                                                if call["id"] == "root-write")["position"])
        nested = capture["observation"]["native_metadata"]["nested_rollout"]
        self.assertEqual(nested["dispatches"][0]["role"], "native_canary_worker")
        self.assertEqual(nested["children"][0]["parent_thread_id"], ROOT_THREAD)
        self.assertEqual(capture["observation"]["native_metadata"]["nested_merge"]["ordering"], "exact")
        self.assertEqual(capture["observation"]["native_metadata"]["tool_name_aliases"], [{
            "tool_call_index": calls.index(spawn), "native_name": "spawn_agent",
            "canonical_name": "subagent", "id": SPAWN_CALL,
        }])
        self.assertIn("codex_rollout_supplement", capture["evidence"])
        for thread_id in (ROOT_THREAD, CHILD_THREAD):
            label = f"codex_rollout_{thread_id.replace('-', '_')}"
            retained = attempt / capture["evidence"][label]["path"]
            source = next(callbacks.codex_home.glob(f"sessions/**/rollout-*-{thread_id}.jsonl"))
            self.assertEqual(retained.read_bytes(), source.read_bytes())
        changed = copy.deepcopy(value)
        changed["checks"][0]["pattern"] = "never-matches"
        resumed = NestedCallbacks(self.output)
        regraded = run_evaluations(config(self.output), {}, [changed], [row("codex")],
                                   repo_root=self.repo, prepare=resumed.prepare,
                                   execute=resumed.execute)
        self.assertEqual(regraded["counts"]["behavior_fails"], 1)
        self.assertEqual(regraded["counts"]["regraded"], 1)
        self.assertEqual(regraded["results"][0]["reason"], "raw_capture_renormalized")
        self.assertEqual(resumed.executed, [])

    def test_codex_followup_is_projected_separately_from_initial_return(self):
        def delivered(text, index):
            encoded = text.encode("utf-8")
            return {
                "message_id": f"delivery-{index}", "text": text,
                "sha256": hashlib.sha256(encoded).hexdigest(), "bytes": len(encoded),
                "author": "/root/read_fixture", "recipient": "/root",
                "turn_id": ROOT_TURN, "native_event_index": index,
            }

        first = delivered("Message Type: FINAL_ANSWER\nPayload:\nFIRST", 11)
        second = delivered("Message Type: FINAL_ANSWER\nPayload:\nSECOND", 21)
        followup = {
            "call_id": "call-followup", "native_name": "followup_task",
            "target": "/root/read_fixture", "task_input": {"sha256": "a" * 64, "bytes": 11},
            "prior_completed_native_event_id": "completed-first",
            "prior_completed_native_event_index": 10,
            "call_record_index": 12, "interaction_record_index": 13,
            "result_record_index": 14,
            "completed_native_event_id": "completed-second",
            "completed_native_event_index": 20, "delivery": second,
        }
        dispatch = {
            "id": SPAWN_CALL, "name": "spawn_agent", "namespace": "collaboration",
            "parent_thread_id": ROOT_THREAD, "child_thread_id": CHILD_THREAD,
            "agent_path": "/root/read_fixture", "depth": 1,
            "role": "native_canary_worker", "role_source": "function_call",
            "task_name": "read_fixture", "fork_turns": "all",
            "task_input": {"sha256": "b" * 64, "bytes": 12},
            "followup_turns": [followup],
            "turn_completions": [
                {"kind": "completed", "id": "completed-first", "native_event_index": 10},
                {"kind": "completed", "id": "completed-second", "native_event_index": 20},
            ],
            "status": "completed", "parent_turn_id": ROOT_TURN,
            "native_event_index": 4,
            "completed_native_event_id": "completed-second",
            "completed_native_event_index": 20,
            "completion_source": "parent-subagent-activity",
            "terminal_failure": None, "delivery": first, "order": 1,
        }
        supplement = {
            "root_thread_id": ROOT_THREAD, "dispatches": [dispatch],
            "children": [{"thread_id": CHILD_THREAD, "tool_calls": []}],
        }
        calls = execution._nested_events(supplement)
        observation = {
            "tool_calls": calls,
            "native_metadata": {
                "nested_rollout": supplement,
                "nested_merge": {"events": [
                    {"id": SPAWN_CALL, "thread_id": ROOT_THREAD,
                     "turn_id": ROOT_TURN, "native_event_index": 4},
                    {"id": "call-followup", "thread_id": ROOT_THREAD,
                     "turn_id": ROOT_TURN, "native_event_index": 13},
                ]},
            },
        }
        for position, call in enumerate(calls):
            call["position"] = position
        execution._canonicalize_subagent_calls("codex", observation)
        execution._bind_subagent_return_order("codex", observation)

        spawn, projected_followup = observation["tool_calls"]
        self.assertEqual(spawn["output"]["result"], first["text"])
        self.assertEqual(projected_followup["name"], "send_input")
        self.assertEqual(projected_followup["output"]["result"], second["text"])
        self.assertEqual(
            observation["native_metadata"]["subagent_return_order"]["returns"][0]
            ["completion_index"],
            first["native_event_index"],
        )

        for variation in ("missing-call", "forged-result", "wrong-event"):
            with self.subTest(variation=variation), self.assertRaises(ValueError):
                changed = copy.deepcopy(observation)
                del changed["native_metadata"]["subagent_return_order"]
                if variation == "missing-call":
                    changed["tool_calls"].pop()
                elif variation == "forged-result":
                    changed["tool_calls"][-1]["output"]["result"] = "forged"
                else:
                    changed["native_metadata"]["nested_merge"]["events"][-1][
                        "native_event_index"
                    ] = 99
                execution._bind_subagent_return_order("codex", changed)

    def test_native_subagent_aliases_both_hosts_and_replays_without_subject_launches(self):
        value = case(resource_class="nested")
        value["checks"].append({"id": "subagent", "requirement": "r1", "type": "tool_used",
                                "name": "subagent", "min": 1, "max": 1})
        rows = [row("claude"), row("codex")]
        callbacks = NativeSubagentCallbacks(self.output)
        initial = run_evaluations(config(self.output), {}, [value], rows, repo_root=self.repo,
                                  prepare=callbacks.prepare, execute=callbacks.execute)
        self.assertEqual(initial["counts"]["passes"], 2, initial)
        self.assertCountEqual(callbacks.executed, ["claude", "codex"])

        attempts = list((self.output / "attempts").iterdir())
        captures = {}
        for attempt in attempts:
            launch = json.loads((attempt / "launch-prepared.json").read_text())
            payload = json.loads((attempt / "capture.json").read_text())["payload"]
            captures[launch["host"]] = payload["observation"]
        for host, native_name in (("claude", "Agent"), ("codex", "spawn_agent")):
            observation = captures[host]
            calls = observation["tool_calls"]
            self.assertEqual([call["name"] for call in calls].count("subagent"), 1)
            self.assertNotIn(native_name, [call["name"] for call in calls])
            self.assertFalse(any("native_name" in call for call in calls))
            alias = observation["native_metadata"]["tool_name_aliases"]
            self.assertEqual(len(alias), 1)
            self.assertEqual(alias[0]["native_name"], native_name)
            self.assertEqual(alias[0]["canonical_name"], "subagent")
            self.assertEqual(calls[alias[0]["tool_call_index"]]["id"], alias[0]["id"])
        claude_call = next(call for call in captures["claude"]["tool_calls"]
                           if call["name"] == "subagent")
        self.assertEqual(claude_call, {
            "id": "agent-call", "name": "subagent",
            "input": {"description": "Read fixture", "prompt": "Read fixture.txt",
                      "subagent_type": "general-purpose"},
            "position": 1, "parent_id": None, "success": True,
            "output": "fixture read complete",
        })

        changed = copy.deepcopy(value)
        changed["checks"][0]["pattern"] = "never-matches"
        replay = NativeSubagentCallbacks(self.output)
        regraded = run_evaluations(config(self.output), {}, [changed], rows, repo_root=self.repo,
                                   prepare=replay.prepare, execute=replay.execute)
        self.assertEqual(regraded["counts"]["behavior_fails"], 2, regraded)
        self.assertEqual(regraded["counts"]["regraded"], 2)
        self.assertEqual(regraded["counts"]["subject_launches"], 0)
        self.assertEqual(replay.executed, [])
        for result in regraded["results"]:
            attempt = Path(result["attempt"])
            grade = next(path for path in (attempt / "grades").iterdir()
                         if (path / "interpretation.json").exists())
            observation = json.loads((grade / "interpretation.json").read_text())["observation"]
            self.assertEqual([call["name"] for call in observation["tool_calls"]].count("subagent"), 1)

    def test_terminal_failed_codex_dispatch_is_preserved_and_never_counted_as_a_return(self):
        failure = {
            "schema": "codex-native-terminal-failure/v1",
            "turn_id": str(uuid.UUID(int=901)),
            "native_event_index": 84,
            "timestamp": "2026-09-19T20:20:00Z",
            "codex_error_info": "server_overloaded",
            "message_sha256": hashlib.sha256(
                b"Selected model is at capacity."
            ).hexdigest(),
            "message_bytes": len(b"Selected model is at capacity."),
        }
        call = execution._nested_dispatch({
            "id": "failed-spawn",
            "namespace": "collaboration",
            "parent_thread_id": str(uuid.UUID(int=900)),
            "child_thread_id": str(uuid.UUID(int=902)),
            "depth": 1,
            "agent_path": "/root/post_uat_author",
            "role": "uat-runbook-author",
            "role_source": "native",
            "task_name": "post_uat_author",
            "fork_turns": "all",
            "task_input": {"sha256": "a" * 64, "bytes": 20},
            "status": "failed",
            "order": 1,
            "completion_source": "child-task-complete-error",
            "terminal_failure": failure,
        }, None)
        self.assertFalse(call["success"])
        self.assertEqual(call["output"]["terminal_failure"], failure)

        observation = {"tool_calls": [call], "native_metadata": {}}
        execution._canonicalize_subagent_calls("codex", observation)
        with self.assertRaisesRegex(ValueError, "did not complete successfully"):
            execution._bind_subagent_return_order("codex", copy.deepcopy(observation))

        execution._bind_subagent_return_order(
            "codex", observation, allow_failed_dispatches=True,
        )
        self.assertEqual(observation["native_metadata"]["subagent_return_order"], {
            "schema": "native-subagent-return-order/v1",
            "scope": "direct-root-only",
            "returns": [],
            "parent_file_changes": [],
        })

    def test_native_dispatch_attribution_passes_both_hosts_and_replays_without_subjects(self):
        rows = [row("claude"), row("codex")]
        callbacks = DispatchCallbacks(self.output)
        initial = run_evaluations(
            config(self.output), {}, [dispatch_case()], rows, repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(initial["counts"]["passes"], 2, initial)
        self.assertEqual(initial["counts"]["infrastructure_invalid"], 0, initial)

        for attempt in (self.output / "attempts").iterdir():
            capture = json.loads((attempt / "capture.json").read_text())["payload"]
            metadata = capture["observation"]["native_metadata"]
            receipt = metadata["native_subagent_dispatch_attribution"]
            self.assertEqual(receipt["schema"], "native-subagent-dispatch-attribution/v1")
            self.assertEqual(receipt["authority"], "controller-bound-native-trace")
            self.assertEqual(receipt["calls"][0]["observed_item_ids"], ["dispatch-i1"])
            self.assertTrue(metadata["subagent_return_order"]["returns"])

        changed = copy.deepcopy(dispatch_case())
        changed["checks"][0]["pattern"] = "never-matches"
        replay_callbacks = DispatchCallbacks(self.output)
        replay = run_evaluations(
            config(self.output), {}, [changed], rows, repo_root=self.repo,
            prepare=replay_callbacks.prepare, execute=replay_callbacks.execute,
        )
        self.assertEqual(replay["counts"]["behavior_fails"], 2, replay)
        self.assertEqual(replay["counts"]["regraded"], 2, replay)
        self.assertEqual(replay["counts"]["subject_launches"], 0, replay)
        self.assertEqual(replay_callbacks.executed, [])

    def test_subagent_alias_is_exact_ordered_and_conflicts_fail_without_mutation(self):
        calls = [
            {"name": "Agent", "input": {"task": "no id"}, "parent_id": None,
             "position": 2, "output": "one", "success": True, "activation": "alpha"},
            {"id": "task", "name": "Task", "input": {}, "parent_id": None,
             "position": 3, "output": "advertised", "success": True},
            {"id": "wait", "name": "wait", "input": {}, "parent_id": None,
             "position": 4, "output": "waited", "success": True},
            {"id": "send", "name": "send_input", "input": {}, "parent_id": None,
             "position": 5, "output": "sent", "success": True},
            {"id": "canonical", "name": "subagent", "input": {}, "parent_id": None,
             "position": 6, "output": "already", "success": True},
            {"id": "wrong-host", "name": "spawn_agent", "input": {}, "parent_id": None,
             "position": 7, "output": "wrong", "success": True},
            {"id": "duplicate-a", "name": "Agent", "input": {"same": True},
             "parent_id": "owner", "position": 8, "output": "same", "success": True},
            {"id": "duplicate-b", "name": "Agent", "input": {"same": True},
             "parent_id": "owner", "position": 9, "output": "same", "success": True},
        ]
        before = copy.deepcopy(calls)
        observation = {"tool_calls": calls, "native_metadata": {"provider": "claude"}}
        execution._canonicalize_subagent_calls("claude", observation)
        self.assertEqual(len(calls), len(before))
        self.assertEqual([call["name"] for call in calls], [
            "subagent", "Task", "wait", "send_input", "subagent", "spawn_agent",
            "subagent", "subagent",
        ])
        for index, call in enumerate(calls):
            self.assertEqual({key: value for key, value in call.items() if key != "name"},
                             {key: value for key, value in before[index].items() if key != "name"})
        self.assertEqual(observation["native_metadata"]["tool_name_aliases"], [
            {"tool_call_index": 0, "native_name": "Agent", "canonical_name": "subagent"},
            {"tool_call_index": 6, "native_name": "Agent", "canonical_name": "subagent",
             "id": "duplicate-a"},
            {"tool_call_index": 7, "native_name": "Agent", "canonical_name": "subagent",
             "id": "duplicate-b"},
        ])

        conflict = {"tool_calls": [{"name": "Agent", "input": {}}],
                    "native_metadata": {"tool_name_aliases": []}}
        frozen = copy.deepcopy(conflict)
        with self.assertRaisesRegex(ValueError, "alias metadata conflicts"):
            execution._canonicalize_subagent_calls("claude", conflict)
        self.assertEqual(conflict, frozen)

    def test_causal_returns_pass_both_hosts_and_regrade_wrong_path_without_launches(self):
        rows = [row("claude"), row("codex")]
        callbacks = CausalCallbacks(self.output)
        initial = run_evaluations(config(self.output), {}, [causal_case()], rows,
                                  repo_root=self.repo, prepare=callbacks.prepare,
                                  execute=callbacks.execute)
        self.assertEqual(initial["counts"]["passes"], 2, initial)
        attempts = list((self.output / "attempts").iterdir())
        observations = [json.loads((attempt / "capture.json").read_text())["payload"]["observation"]
                        for attempt in attempts]
        self.assertTrue(all(observation["native_metadata"]["subagent_return_order"]["returns"]
                            for observation in observations))

        replay = CausalCallbacks(self.output)
        regraded = run_evaluations(config(self.output), {}, [causal_case("missing.txt")], rows,
                                   repo_root=self.repo, prepare=replay.prepare,
                                   execute=replay.execute)
        self.assertEqual(regraded["counts"]["behavior_fails"], 2, regraded)
        self.assertEqual(regraded["counts"]["regraded"], 2)
        self.assertEqual(regraded["counts"]["subject_launches"], 0)
        self.assertEqual(replay.executed, [])

    def test_native_synthesis_binds_real_return_metadata_fresh_and_regrade_both_hosts(self):
        value = synthesis_return_case()
        rows = [row("claude"), row("codex")]
        callbacks = SynthesisCallbacks(self.output)
        initial = run_evaluations(
            config(self.output), {}, [value], rows, repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(initial["counts"]["passes"], 2, initial)
        attempts = list((self.output / "attempts").iterdir())
        captured = {
            json.loads((attempt / "launch-prepared.json").read_text())["host"]:
            json.loads((attempt / "capture.json").read_text())["payload"]["observation"]
            for attempt in attempts
        }
        self.assertEqual(
            captured["claude"]["native_metadata"]["subagent_return_order"]["returns"][0]
            ["authority"],
            "claude-tool-result",
        )
        self.assertEqual(
            captured["codex"]["native_metadata"]["subagent_return_order"]["returns"][0]
            ["authority"],
            "codex-parent-delivery",
        )
        self.assertEqual(len(captured["codex"]["native_metadata"]["nested_rollout"]["children"]), 1)

        changed = copy.deepcopy(value)
        changed["checks"][1]["id"] = "source-a-regraded"
        replay_callbacks = SynthesisCallbacks(self.output)
        replay = run_evaluations(
            config(self.output), {}, [changed], rows, repo_root=self.repo,
            prepare=replay_callbacks.prepare, execute=replay_callbacks.execute,
        )
        self.assertEqual(replay["counts"]["regraded"], 2, replay)
        self.assertEqual(replay["counts"]["subject_launches"], 0)
        self.assertEqual(replay_callbacks.executed, [])
        interpreted = {
            json.loads((attempt / "launch-prepared.json").read_text())["host"]:
            json.loads((next(
                path for path in (attempt / "grades").iterdir()
                if (path / "interpretation.json").exists()
            ) / "interpretation.json").read_text())["observation"]
            for attempt in attempts
        }
        self.assertEqual(
            interpreted["claude"]["native_metadata"]["subagent_return_order"]["returns"][0]
            ["authority"],
            "claude-tool-result",
        )
        self.assertEqual(
            interpreted["codex"]["native_metadata"]["subagent_return_order"]["returns"][0]
            ["authority"],
            "codex-parent-delivery",
        )

    def test_codex_dedicated_synthesis_accepts_return_before_parent_write_and_regrade(self):
        value = dedicated_synthesis_case()
        callbacks = SynthesisCallbacks(self.output, variation="absolute-write")
        initial = run_evaluations(
            config(self.output), {}, [value], [row("codex")], repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(initial["counts"]["passes"], 1, initial)
        attempt = next((self.output / "attempts").iterdir())
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        observation = capture["observation"]
        self.assertEqual(observation["native_metadata"]["cwd"],
                         observation["native_metadata"]["codex_skill_injections"]["cwd"])
        conflicting = copy.deepcopy(observation)
        conflicting["native_metadata"]["cwd"] = "/unrelated-workspace"
        with self.assertRaisesRegex(ValueError, "cwd"):
            execution._merge_codex_skill_injections(
                conflicting, observation["native_metadata"]["codex_skill_injections"],
                ROOT_THREAD,
            )
        nested = observation["native_metadata"]["nested_rollout"]
        self.assertEqual([item["role"] for item in nested["dispatches"]],
                         ["consensus-synthesizer"])
        self.assertEqual([item["thread_id"] for item in nested["children"]], [CHILD_THREAD])
        self.assertEqual(set(nested["raw_sha256"]), {ROOT_THREAD, CHILD_THREAD})
        synthesis = next(call for call in observation["tool_calls"]
                         if call["name"] == "subagent")
        self.assertEqual(
            synthesis["output"]["result"],
            "Message Type: FINAL_ANSWER\nPayload:\nfixture read complete",
        )
        tampered = copy.deepcopy(nested)
        tampered["dispatches"][0]["delivery"]["text"] = "forged result"
        with self.assertRaisesRegex(ValueError, "conflicts with its delivery receipt"):
            execution._nested_events(tampered)
        self.assertEqual(
            observation["native_metadata"]["subagent_return_order"]["returns"][0]["authority"],
            "codex-parent-delivery",
        )
        names = [call["name"] for call in observation["tool_calls"]]
        self.assertEqual(names, ["command_execution", "command_execution", "subagent",
                                 "command_execution", "file_change"])
        self.assertEqual(
            [call["position"] for call in observation["tool_calls"]],
            sorted(call["position"] for call in observation["tool_calls"]),
        )

        changed = copy.deepcopy(value)
        changed["checks"][1]["id"] = "source-a-regraded"
        replay_callbacks = SynthesisCallbacks(self.output, variation="absolute-write")
        replay = run_evaluations(
            config(self.output), {}, [changed], [row("codex")], repo_root=self.repo,
            prepare=replay_callbacks.prepare, execute=replay_callbacks.execute,
        )
        self.assertEqual(replay["counts"]["passes"], 1, replay)
        self.assertEqual(replay["counts"]["regraded"], 1)
        self.assertEqual(replay["counts"]["subject_launches"], 0)
        self.assertEqual(replay_callbacks.executed, [])

        self._assert_projected_file_change_binding()

    def _assert_projected_file_change_binding(self):
        projected_output = self.root / "projected-write-id"
        projected_callbacks = SynthesisCallbacks(
            projected_output, variation="projected-write-id",
        )
        projected = run_evaluations(
            config(projected_output), {}, [dedicated_synthesis_case()], [row("codex")],
            repo_root=self.repo, prepare=projected_callbacks.prepare,
            execute=projected_callbacks.execute,
        )
        self.assertEqual(projected["counts"]["passes"], 1, projected)
        projected_attempt = next((projected_output / "attempts").iterdir())
        projected_observation = json.loads(
            (projected_attempt / "capture.json").read_text()
        )["payload"]["observation"]
        projected_writes = [
            call for call in projected_observation["tool_calls"]
            if call["name"] == "file_change"
        ]
        self.assertEqual([call["id"] for call in projected_writes], ["native-root-write"])

    def test_codex_root_file_change_binding_canonicalizes_only_entry_order(self):
        native_changes = {
            str(self.repo / "workflow.md"): {"type": "update"},
            str(self.repo / "obsolete.md"): {"type": "delete"},
            str(self.repo / "artifact.md"): {"type": "add"},
        }
        raw_root = rollout_raw([rollout_event({
            "type": "item_completed", "thread_id": ROOT_THREAD, "turn_id": ROOT_TURN,
            "item": {"type": "FileChange", "id": "native-root-write",
                     "status": "completed", "changes": native_changes},
        })])

        def projected(changes):
            return [{
                "id": "projected-write", "name": "file_change", "parent_id": None,
                "input": {"changes": changes},
            }]

        reordered = projected([
            {"path": "artifact.md", "kind": "add"},
            {"path": "obsolete.md", "kind": "delete"},
            {"path": "workflow.md", "kind": "update"},
        ])
        execution._rebind_codex_root_tool_ids(
            reordered, raw_root, ROOT_THREAD, str(self.repo),
        )
        self.assertEqual(reordered[0]["id"], "native-root-write")

        for label, changes, reason in (
            ("changed-kind", [
                {"path": "artifact.md", "kind": "update"},
                {"path": "obsolete.md", "kind": "delete"},
                {"path": "workflow.md", "kind": "update"},
            ], "disagrees with native event"),
            ("changed-path", [
                {"path": "other.md", "kind": "add"},
                {"path": "obsolete.md", "kind": "delete"},
                {"path": "workflow.md", "kind": "update"},
            ], "disagrees with native event"),
            ("duplicate-path", [
                {"path": "artifact.md", "kind": "add"},
                {"path": "artifact.md", "kind": "add"},
                {"path": "workflow.md", "kind": "update"},
            ], "duplicate paths"),
        ):
            with self.subTest(label=label), self.assertRaisesRegex(ValueError, reason):
                execution._rebind_codex_root_tool_ids(
                    projected(changes), raw_root, ROOT_THREAD, str(self.repo),
                )

    def test_codex_parent_only_synthesis_is_rejected_before_grading(self):
        callbacks = SynthesisCallbacks(self.output, variation="no-child")
        assert_codex_parent_synthesis_rejected(self, callbacks)

    def test_codex_dedicated_synthesis_requires_valid_root_return_and_exact_role(self):
        expected_by_variation = {
            "missing-root": (1, 0),
            "malformed-root": (1, 0),
            "missing-delivery": (1, 0),
            "wrong-role": (0, 1),
        }
        for variation, expected in expected_by_variation.items():
            with self.subTest(variation=variation):
                output = self.root / variation
                callbacks = SynthesisCallbacks(output, variation=variation)
                report = run_evaluations(
                    config(output), {}, [dedicated_synthesis_case()], [row("codex")],
                    repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
                )
                counts = report["counts"]
                self.assertEqual(
                    (counts["infrastructure_invalid"], counts["behavior_fails"]),
                    expected,
                    report,
                )
                self.assertEqual(counts["passes"], 0, report)

    def test_v2_git_observation_is_retained_and_replayed_for_both_hosts(self):
        rows = [row("claude"), row("codex")]
        callbacks = GitObservationCallbacks(self.output)
        value = case()
        value["checks"].append({
            "id": "final-state", "requirement": "r1", "type": "native_git_final_state",
            "head_equals_initial_feature": True, "branch": "feature",
            "commit_count": 0, "commits_added": [],
            "changed_tracked_paths_from_initial_feature": [],
            "status": git_observation()["status"],
        })
        initial = run_evaluations(
            config(self.output), {}, [value], rows, repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(initial["counts"]["passes"], 2, initial)
        attempts = list((self.output / "attempts").iterdir())
        for attempt in attempts:
            capture = json.loads((attempt / "capture.json").read_text())["payload"]
            ref = capture["evidence"]["git_observation"]
            retained = attempt / ref["path"]
            metadata = capture["observation"]["native_metadata"]["controller_git_observation"]
            self.assertEqual(metadata["observation"], git_observation())
            self.assertEqual(metadata["evidence"], ref)
            self.assertEqual(hashlib.sha256(retained.read_bytes()).hexdigest(), ref["sha256"])

        changed = copy.deepcopy(value)
        changed["checks"][0]["pattern"] = "do.e"
        replay_callbacks = GitObservationCallbacks(self.output)
        replay = run_evaluations(
            config(self.output), {}, [changed], rows, repo_root=self.repo,
            prepare=replay_callbacks.prepare, execute=replay_callbacks.execute,
        )
        self.assertEqual(replay["counts"]["passes"], 2, replay)
        self.assertEqual(replay["counts"]["regraded"], 2)
        self.assertEqual(replay["counts"]["subject_launches"], 0)
        self.assertEqual(replay_callbacks.executed, [])
        for attempt in attempts:
            grade_dir = next(path for path in (attempt / "grades").iterdir()
                             if (path / "interpretation.json").exists())
            interpreted = json.loads((grade_dir / "interpretation.json").read_text())["observation"]
            self.assertEqual(
                interpreted["native_metadata"]["controller_git_observation"]["observation"],
                git_observation(),
            )

    def test_v2_git_observation_missing_error_malformed_and_tampered_are_invalid(self):
        for variation in ("missing", "error", "malformed", "tampered"):
            with self.subTest(variation=variation):
                output = self.root / f"git-{variation}"
                callbacks = GitObservationCallbacks(output, variation=variation)
                report = run_evaluations(
                    config(output), {}, [case()], [row("claude"), row("codex")],
                    repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
                )
                self.assertEqual(report["counts"]["infrastructure_invalid"], 2, report)
                self.assertEqual(report["counts"]["passes"], 0, report)

    def test_registered_child_preservation_is_bound_on_capture_and_replay(self):
        for variation, count in (("child-clean", "passes"), ("child-dirty", "behavior_fails"),
                                 ("child-missing", "infrastructure_invalid"),
                                 ("child-wrong-initial", "infrastructure_invalid")):
            with self.subTest(variation=variation):
                output = self.root / variation
                callbacks = GitObservationCallbacks(output, variation=variation)
                value = case()
                value["checks"].append({
                    "id": "preservation", "requirement": "r1", "type": "native_git_final_state",
                    "head_equals_initial_feature": True, "branch": "feature",
                    "commit_count": 0, "commits_added": [],
                    "changed_tracked_paths_from_initial_feature": [],
                    "status": git_observation()["status"], "registered_worktrees_unchanged": True,
                })
                rows = [row("claude"), row("codex")]
                initial = run_evaluations(config(output), {}, [value], rows, repo_root=self.repo,
                                          prepare=callbacks.prepare, execute=callbacks.execute)
                self.assertEqual(initial["counts"][count], 2, initial)
                if count == "infrastructure_invalid":
                    continue
                changed = copy.deepcopy(value)
                changed["checks"][0]["pattern"] = "do.e"
                replay_callbacks = GitObservationCallbacks(output, variation=variation)
                replay = run_evaluations(config(output), {}, [changed], rows, repo_root=self.repo,
                                         prepare=replay_callbacks.prepare, execute=replay_callbacks.execute)
                self.assertEqual(replay["counts"][count], 2, replay)
                self.assertEqual(replay["counts"]["regraded"], 2, replay)
                self.assertEqual(replay["counts"]["subject_launches"], 0, replay)

    def test_native_verification_record_is_retained_and_replayed_for_both_hosts(self):
        rows = [row("claude"), row("codex")]
        value = verification_case()
        callbacks = VerificationCallbacks(self.output)
        initial = run_evaluations(
            config(self.output), {}, [value], rows, repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(initial["counts"]["passes"], 2, initial)
        attempts = list((self.output / "attempts").iterdir())
        self.assertEqual(len(attempts), 2)
        for attempt in attempts:
            capture = json.loads((attempt / "capture.json").read_text())["payload"]
            self.assertIn("verification_record", capture["evidence"])
            bound = capture["observation"]["native_metadata"]["controller_verification"]
            self.assertEqual(bound["checks"][0]["actual"]["record_sha256"],
                             capture["evidence"]["verification_record"]["sha256"])

        changed = copy.deepcopy(value)
        changed["checks"][0]["pattern"] = "do.e"
        replay_callbacks = VerificationCallbacks(self.output)
        replay = run_evaluations(
            config(self.output), {}, [changed], rows, repo_root=self.repo,
            prepare=replay_callbacks.prepare, execute=replay_callbacks.execute,
        )
        self.assertEqual(replay["counts"]["passes"], 2, replay)
        self.assertEqual(replay["counts"]["regraded"], 2)
        self.assertEqual(replay["counts"]["subject_launches"], 0)
        self.assertEqual(replay_callbacks.executed, [])

    def test_claude_verification_accepts_the_exact_bounded_capture_wrapper(self):
        assert_claude_verification_capture(
            self,
            VerificationCallbacks(self.output, claude_capture_wrapper=True),
        )

    def test_claude_runner_capture_wrapper_rejects_any_extra_shell_action(self):
        command = "\n".join([
            'python3 -m speckit_pro_runner < request.json > '
            + '"$TMPDIR/runner-output.json" 2>"$TMPDIR/runner-stderr.log"',
            'echo "exit=$?"', 'echo "---stdout---"',
            'cat "$TMPDIR/runner-output.json"', "echo",
            'echo "---stderr---"', 'cat "$TMPDIR/runner-stderr.log"',
        ])
        self.assertEqual(
            execution._claude_runner_capture_request_path(command, {"python3"}),
            "request.json",
        )
        for changed in (
            command + "\necho injected",
            command.replace("request.json", "../request.json"),
            command.replace("runner-output.json", "nested/runner-output.json"),
            command.replace("runner-stderr.log", "runner-output.json"),
            command.replace('"$TMPDIR/runner-output.json"',
                            "'$TMPDIR/runner-output.json'", 1),
            command.replace('echo "exit=$?"', 'echo "exit=0"'),
        ):
            with self.subTest(changed=changed):
                self.assertIsNone(
                    execution._claude_runner_capture_request_path(changed, {"python3"})
                )
        with self.assertRaisesRegex(ValueError, "wrapper output is malformed"):
            execution._claude_runner_capture_output(
                "exit=0\n---stdout---\n{}\n\n---stderr---\nuntrusted"
            )

    def test_claude_runner_accepts_only_the_exact_native_cwd_prelude(self):
        cwd = "/private/tmp/native fixture/cwd"
        command = (
            f"cd '{cwd}'\n"
            f"python3 -m speckit_pro_runner < {RUNNER_REQUEST_PATH}"
        )
        self.assertEqual(
            execution._claude_runner_request_path(command, {"python3"}, cwd),
            RUNNER_REQUEST_PATH,
        )
        for changed in (
            command.replace(cwd, "/private/tmp/other", 1),
            command + "\necho injected",
            command.replace("cd ", "cd -- ", 1),
            command.replace(RUNNER_REQUEST_PATH, "../request.json"),
        ):
            with self.subTest(changed=changed):
                self.assertIsNone(
                    execution._claude_runner_request_path(
                        changed, {"python3"}, cwd,
                    )
                )

    def test_claude_runner_accepts_only_the_bounded_tmp_capture_pipeline(self):
        cwd = "/private/tmp/native-fixture/cwd"
        command = (
            f"cd {cwd}\n"
            f"python3 -m speckit_pro_runner < {RUNNER_REQUEST_PATH} | "
            'tee "$TMPDIR/execute-verification-response.json" | '
            "python3 -m json.tool"
        )
        self.assertEqual(
            execution._claude_runner_request_path(command, {"python3"}, cwd),
            RUNNER_REQUEST_PATH,
        )
        for changed in (
            command.replace("$TMPDIR/", "/tmp/", 1),
            command.replace("json.tool", "other.tool", 1),
            command.replace(" | python3", " | cat | python3", 1),
            command + "\necho injected",
            command.replace("response.json", "nested/response.json", 1),
        ):
            with self.subTest(changed=changed):
                self.assertIsNone(
                    execution._claude_runner_request_path(
                        changed, {"python3"}, cwd,
                    )
                )

    def test_verification_persists_authenticated_bytes_if_source_changes_after_binding(self):
        real_bind = execution.bind_verification_result
        expected = (json.dumps(verification_record(), sort_keys=True, indent=2) + "\n").encode()
        for host in ("claude", "codex"):
            for variation in ("mutated", "removed"):
                with self.subTest(host=host, variation=variation):
                    output = self.root / f"verification-race-{host}-{variation}"
                    callbacks = VerificationCallbacks(output)

                    def racing_bind(check, invocation, read_record):
                        receipt = real_bind(check, invocation, read_record)
                        source = (callbacks.prepared[0][1] / "workspace"
                                  / receipt["actual"]["record_path"])
                        if variation == "mutated":
                            source.write_bytes(b'{"changed":true}\n')
                        else:
                            source.unlink()
                        return receipt

                    with mock.patch.object(
                        execution, "bind_verification_result", side_effect=racing_bind,
                    ):
                        initial = run_evaluations(
                            config(output), {}, [verification_case()], [row(host)],
                            repo_root=self.repo, prepare=callbacks.prepare,
                            execute=callbacks.execute,
                        )
                    self.assertEqual(initial["counts"]["passes"], 1, initial)
                    self.assertEqual(initial["counts"]["infrastructure_invalid"], 0, initial)
                    attempt = next((output / "attempts").iterdir())
                    capture = json.loads((attempt / "capture.json").read_text())["payload"]
                    receipt = capture["observation"]["native_metadata"]["controller_verification"]
                    retained_ref = capture["evidence"]["verification_record"]
                    retained = attempt / retained_ref["path"]
                    self.assertEqual(retained.read_bytes(), expected)
                    self.assertEqual(
                        hashlib.sha256(retained.read_bytes()).hexdigest(),
                        receipt["checks"][0]["actual"]["record_sha256"],
                    )

                    changed = verification_case()
                    changed["checks"][0]["pattern"] = "do.e"
                    replay_callbacks = VerificationCallbacks(output)
                    replay = run_evaluations(
                        config(output), {}, [changed], [row(host)], repo_root=self.repo,
                        prepare=replay_callbacks.prepare, execute=replay_callbacks.execute,
                    )
                    self.assertEqual(replay["counts"]["passes"], 1, replay)
                    self.assertEqual(replay["counts"]["infrastructure_invalid"], 0, replay)
                    self.assertEqual(replay["counts"]["regraded"], 1, replay)
                    self.assertEqual(replay["counts"]["subject_launches"], 0, replay)
                    self.assertEqual(replay_callbacks.executed, [])

    def test_codex_complete_trace_without_runner_invocation_retains_controller_absence(self):
        callbacks = AbsentVerificationCallbacks(self.output)
        report = run_evaluations(
            config(self.output), {}, [verification_case()], [row("codex")],
            repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(report["counts"]["behavior_fails"], 1, report)
        self.assertEqual(report["counts"]["infrastructure_invalid"], 0, report)
        self.assertEqual(report["counts"]["passes"], 0, report)
        self.assertEqual(report["counts"]["subject_launches"], 1, report)
        attempt = next((self.output / "attempts").iterdir())
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        self.assertNotIn("verification_record", capture["evidence"])
        reference = capture["evidence"]["verification_absence"]
        self.assertEqual(capture["observation"]["artifacts"], {})
        receipt = capture["observation"]["native_metadata"]["controller_verification"]
        self.assertEqual(receipt["checks"][0]["check_id"], "verification")
        absence = receipt["checks"][0]["absence"]
        self.assertEqual(absence["kind"], "no-native-runner-invocation")
        self.assertEqual(absence["authority"], "controller-bound-retained-native-evidence")
        self.assertEqual(absence["check"]["command_id"], "INTEGRATION_TEST")
        rollout = capture["evidence"][execution._rollout_label(ROOT_THREAD)]
        self.assertEqual(absence["root_trace"]["thread_id"], ROOT_THREAD)
        self.assertEqual(absence["root_trace"]["raw_sha256"], rollout["sha256"])
        self.assertEqual(absence["root_trace"]["runner_invocation_count"], 0)
        payload = (json.dumps(absence, sort_keys=True, separators=(",", ":")) + "\n").encode()
        retained = attempt / reference["path"]
        self.assertEqual(retained.read_bytes(), payload)
        self.assertEqual(reference["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(reference["bytes"], len(payload))
        verdicts = [json.loads(path.read_text())["payload"]["verdict"]
                    for path in attempt.glob("grade-*.json")]
        self.assertTrue(verdicts)
        self.assertTrue(all(verdict["status"] == "fail" for verdict in verdicts), verdicts)
        verification = [check for check in verdicts[0]["checks"]
                        if check["id"] == "verification"]
        self.assertEqual(verification[0]["verdict"], "fail")
        self.assertIn("absence", verification[0]["reason"])

    def test_claude_complete_bound_run_without_runner_is_behavior_fail_and_regrades(self):
        callbacks = ClaudeAbsentVerificationCallbacks(self.output)
        value = claude_verification_case()
        report = run_evaluations(
            config(self.output), {}, [value], [row("claude")], repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(report["counts"]["behavior_fails"], 1, report)
        self.assertEqual(report["counts"]["infrastructure_invalid"], 0, report)
        attempt = next((self.output / "attempts").iterdir())
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        reference = capture["evidence"]["verification_absence"]
        absence = capture["observation"]["native_metadata"][
            "controller_verification"]["checks"][0]["absence"]
        self.assertEqual(absence["host"], "claude")
        self.assertNotIn("root_trace", absence)
        self.assertEqual(absence["claude_trace"]["runner_invocation_count"], 0)
        retained = attempt / reference["path"]
        before = (retained.stat().st_ino, retained.stat().st_mtime_ns, retained.read_bytes())

        changed = claude_verification_case()
        changed["checks"][0]["pattern"] = "do.e"
        replay_callbacks = ClaudeAbsentVerificationCallbacks(self.output, variation="partial")
        replay = run_evaluations(
            config(self.output), {}, [changed], [row("claude")], repo_root=self.repo,
            prepare=replay_callbacks.prepare, execute=replay_callbacks.execute,
        )
        self.assertEqual(replay["counts"]["regraded"], 1, replay)
        self.assertEqual(replay["counts"]["behavior_fails"], 1, replay)
        self.assertEqual(replay["counts"]["infrastructure_invalid"], 0, replay)
        self.assertEqual(replay["counts"]["subject_launches"], 0, replay)
        self.assertEqual(replay_callbacks.executed, [])
        after = (retained.stat().st_ino, retained.stat().st_mtime_ns, retained.read_bytes())
        self.assertEqual(after, before)

    def test_claude_trace_identity_accepts_repeated_bound_init_and_rejects_mismatch(self):
        cwd = "/tmp/claude-subject"
        records = [json.loads(line) for line in claude_explicit_trace(cwd).splitlines()]
        records.insert(1, copy.deepcopy(records[0]))
        public_trace = "\n".join(json.dumps(record) for record in records).encode()
        session = b"retained-session\n"
        trace = {
            "session_id": CLAUDE_SESSION,
            "cwd": cwd,
            "cli_version": "2.1.273",
            "bytes": len(public_trace),
            "sha256": hashlib.sha256(public_trace).hexdigest(),
        }
        session_artifact = {
            "bytes": len(session),
            "sha256": hashlib.sha256(session).hexdigest(),
        }
        self.assertEqual(
            execution._claude_complete_trace_identity(
                records, trace, public_trace, session, session_artifact,
            ),
            (CLAUDE_SESSION, cwd, "2.1.273"),
        )

        records[1]["session_id"] = "wrong-session"
        with self.assertRaisesRegex(ValueError, "trace identity is inconsistent"):
            execution._claude_complete_trace_identity(
                records, trace, public_trace, session, session_artifact,
            )

    def test_stored_evidence_accepts_a_confined_relative_attempt_root(self):
        attempt = self.root / "relative-attempt"
        attempt.mkdir()
        retained = attempt / "raw-trace.jsonl"
        retained.write_text("{}\n")
        relative_attempt = Path(os.path.relpath(attempt.resolve(strict=True), Path.cwd()))
        resolved = execution._stored_evidence(
            relative_attempt, {"path": "raw-trace.jsonl"},
        )
        self.assertEqual(resolved.resolve(strict=True), retained.resolve(strict=True))

    def test_claude_absence_rejects_partial_truncated_wrong_session_and_malformed_runner(self):
        for variation in ("partial", "truncated-trace", "wrong-session", "malformed-runner"):
            with self.subTest(variation=variation):
                output = self.root / f"claude-{variation}"
                callbacks = ClaudeAbsentVerificationCallbacks(output, variation=variation)
                report = run_evaluations(
                    config(output), {}, [claude_verification_case()], [row("claude")],
                    repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
                )
                self.assertEqual(report["counts"]["infrastructure_invalid"], 1, report)
                self.assertEqual(report["counts"]["behavior_fails"], 0, report)

    def test_invalid_claude_absence_capture_is_renormalized_without_relaunch(self):
        value = claude_verification_case()
        callbacks = ClaudeAbsentVerificationCallbacks(self.output)
        with mock.patch(
            "native_eval_execution._claude_complete_trace_identity",
            side_effect=ValueError("legacy parser rejected continuation"),
        ):
            initial = run_evaluations(
                config(self.output), {}, [value], [row("claude")], repo_root=self.repo,
                prepare=callbacks.prepare, execute=callbacks.execute,
            )
        self.assertEqual(initial["counts"]["infrastructure_invalid"], 1, initial)
        self.assertEqual(initial["counts"]["subject_launches"], 1)
        original_attempt = next((self.output / "attempts").iterdir())

        resumed = ClaudeAbsentVerificationCallbacks(self.output)
        replay = run_evaluations(
            config(self.output), {}, [value], [row("claude")], repo_root=self.repo,
            prepare=resumed.prepare, execute=resumed.execute,
        )
        self.assertEqual(replay["counts"]["behavior_fails"], 1, replay)
        self.assertEqual(replay["counts"]["regraded"], 1, replay)
        self.assertEqual(replay["counts"]["subject_launches"], 0, replay)
        self.assertEqual(replay["results"][0]["reason"], "raw_capture_renormalized")
        self.assertEqual(resumed.executed, [])
        attempts = list((self.output / "attempts").iterdir())
        self.assertEqual(len(attempts), 2)
        recovered = next(path for path in attempts if path != original_attempt)
        capture = json.loads((recovered / "capture.json").read_text())["payload"]
        self.assertIsNone(capture["error"])
        self.assertIn("verification_absence", capture["evidence"])

    def test_invalid_claude_verification_recovers_deleted_record_from_bound_response(self):
        value = verification_case()
        callbacks = VerificationCallbacks(self.output, claude_capture_wrapper=True)
        with mock.patch(
            "native_eval_execution._fresh_verification",
            side_effect=ValueError("legacy parser rejected capture"),
        ):
            initial = run_evaluations(
                config(self.output), {}, [value], [row("claude")], repo_root=self.repo,
                prepare=callbacks.prepare, execute=callbacks.execute,
            )
        self.assertEqual(initial["counts"]["infrastructure_invalid"], 1, initial)
        original_attempt = next((self.output / "attempts").iterdir())
        original_capture = json.loads((original_attempt / "capture.json").read_text())["payload"]
        self.assertIn("artifact_manifest", original_capture["evidence"])
        record = callbacks.prepared[0][1] / "workspace/.process/verification" / f"{'a' * 32}.json"
        record.unlink()

        resumed = VerificationCallbacks(self.output, claude_capture_wrapper=True)
        replay = run_evaluations(
            config(self.output), {}, [value], [row("claude")], repo_root=self.repo,
            prepare=resumed.prepare, execute=resumed.execute,
        )
        self.assertEqual(replay["counts"]["passes"], 1, replay)
        self.assertEqual(replay["counts"]["regraded"], 1, replay)
        self.assertEqual(replay["counts"]["subject_launches"], 0, replay)
        self.assertEqual(replay["results"][0]["reason"], "raw_capture_renormalized")
        attempts = list((self.output / "attempts").iterdir())
        recovered = next(path for path in attempts if path != original_attempt)
        capture = json.loads((recovered / "capture.json").read_text())["payload"]
        retained = recovered / capture["evidence"]["verification_record"]["path"]
        expected = (json.dumps(
            verification_record(), sort_keys=True, indent=2, allow_nan=False,
        ) + "\n").encode()
        self.assertEqual(retained.read_bytes(), expected)

    def absent_verification_attempt(self, output=None):
        """Run one fresh zero-invocation attempt and return its stored capture."""

        output = self.output if output is None else output
        callbacks = AbsentVerificationCallbacks(output)
        report = run_evaluations(
            config(output), {}, [verification_case()], [row("codex")],
            repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(report["counts"]["behavior_fails"], 1, report)
        attempt = next((output / "attempts").iterdir())
        return attempt, json.loads((attempt / "capture.json").read_text())["payload"]

    def test_absent_verification_regrades_and_reconstructs_retained_absence(self):
        attempt, capture = self.absent_verification_attempt()
        retained = attempt / capture["evidence"]["verification_absence"]["path"]
        payload = retained.read_bytes()
        before = retained.stat()

        changed = verification_case()
        changed["checks"][0]["pattern"] = "do.e"
        replay_callbacks = AbsentVerificationCallbacks(self.output, variation="unbound")
        replay = run_evaluations(
            config(self.output), {}, [changed], [row("codex")], repo_root=self.repo,
            prepare=replay_callbacks.prepare, execute=replay_callbacks.execute,
        )
        self.assertEqual(replay["counts"]["regraded"], 1, replay)
        self.assertEqual(replay["counts"]["behavior_fails"], 1, replay)
        self.assertEqual(replay["counts"]["infrastructure_invalid"], 0, replay)
        self.assertEqual(replay["counts"]["subject_launches"], 0, replay)
        self.assertEqual(replay_callbacks.executed, [])
        after = retained.stat()
        self.assertEqual((after.st_ino, after.st_mtime_ns, retained.read_bytes()),
                         (before.st_ino, before.st_mtime_ns, payload))
        interpretations = list((attempt / "grades").glob("*/interpretation.json"))
        self.assertTrue(interpretations)
        for path in interpretations:
            marker = json.loads(path.read_text())["observation"]["native_metadata"][
                "controller_verification"]["checks"][0]["absence"]
            rebuilt = (json.dumps(marker, sort_keys=True, separators=(",", ":"))
                       + "\n").encode()
            self.assertEqual(rebuilt, payload)

    def test_absent_verification_regrade_with_changed_check_identity_is_invalid(self):
        self.absent_verification_attempt()
        changed = verification_case()
        changed["checks"][1]["command_id"] = "UNIT_TEST"
        replay_callbacks = AbsentVerificationCallbacks(self.output)
        replay = run_evaluations(
            config(self.output), {}, [changed], [row("codex")], repo_root=self.repo,
            prepare=replay_callbacks.prepare, execute=replay_callbacks.execute,
        )
        self.assertEqual(replay["counts"]["infrastructure_invalid"], 1, replay)
        self.assertEqual(replay["counts"]["behavior_fails"], 0, replay)
        self.assertEqual(replay["counts"]["subject_launches"], 0, replay)
        self.assertEqual(replay_callbacks.executed, [])
        self.assertIn("native verification absence evidence changed",
                      replay["results"][0]["reason"])

    def test_absent_verification_without_retained_evidence_is_invalid(self):
        real = execution._fresh_verification_absence

        def omit_evidence(*args, **kwargs):
            real(*args, **kwargs)
            return {}

        callbacks = AbsentVerificationCallbacks(self.output)
        with mock.patch.object(execution, "_fresh_verification_absence",
                               side_effect=omit_evidence):
            initial = run_evaluations(
                config(self.output), {}, [verification_case()], [row("codex")],
                repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
            )
        self.assertEqual(initial["counts"]["behavior_fails"], 1, initial)
        attempt = next((self.output / "attempts").iterdir())
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        self.assertNotIn("verification_absence", capture["evidence"])

        changed = verification_case()
        changed["checks"][0]["pattern"] = "do.e"
        replay = run_evaluations(
            config(self.output), {}, [changed], [row("codex")], repo_root=self.repo,
            prepare=AbsentVerificationCallbacks(self.output).prepare,
            execute=AbsentVerificationCallbacks(self.output).execute,
        )
        self.assertEqual(replay["counts"]["infrastructure_invalid"], 1, replay)
        self.assertEqual(replay["counts"]["behavior_fails"], 0, replay)
        self.assertIn("omitted native verification absence evidence",
                      replay["results"][0]["reason"])

    def test_subject_output_cannot_spoof_controller_absence(self):
        callbacks = AbsentVerificationCallbacks(self.output, variation="forged-absence")
        report = run_evaluations(
            config(self.output), {}, [verification_case()], [row("codex")],
            repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(report["counts"]["behavior_fails"], 1, report)
        self.assertEqual(report["counts"]["passes"], 0, report)
        self.assertEqual(report["counts"]["infrastructure_invalid"], 0, report)
        attempt = next((self.output / "attempts").iterdir())
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        self.assertNotIn("verification_absence", capture["evidence"])
        receipt_row = capture["observation"]["native_metadata"][
            "controller_verification"]["checks"][0]
        self.assertNotIn("absence", receipt_row)
        self.assertIn("call", receipt_row)
        verdicts = [json.loads(path.read_text())["payload"]["verdict"]
                    for path in attempt.glob("grade-*.json")]
        verification = [check for check in verdicts[0]["checks"] if check["id"] == "verification"]
        self.assertEqual(verification[0]["verdict"], "fail")

    def test_absent_verification_evidence_variants_stay_infrastructure_invalid(self):
        for variation, host in (("claude-absent", "claude"), ("unbound", "codex"),
                                ("wrong-cwd", "codex"), ("failed", "codex"),
                                ("truncated-command", "codex"), ("truncated", "codex"),
                                ("duplicate", "codex")):
            with self.subTest(variation=variation):
                output = self.root / variation
                callbacks = AbsentVerificationCallbacks(output, variation=variation)
                report = run_evaluations(
                    config(output), {}, [verification_case()], [row(host)],
                    repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
                )
                self.assertEqual(report["counts"]["infrastructure_invalid"], 1, report)
                self.assertEqual(report["counts"]["behavior_fails"], 0, report)
                self.assertEqual(report["counts"]["passes"], 0, report)

    def test_native_runner_expected_failure_is_bound_fresh_and_replayed_both_hosts(self):
        payload = (json.dumps(runner_request(), sort_keys=True, indent=2) + "\n").encode()
        (self.repo / "request.json").write_bytes(payload)
        rows = [row("claude"), row("codex")]
        callbacks = RunnerResultCallbacks(self.output)
        initial = run_evaluations(
            config(self.output), {}, [runner_result_case()], rows, repo_root=self.repo,
            prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(initial["counts"]["passes"], 2, initial)
        self.assertEqual(initial["counts"]["infrastructure_invalid"], 0, initial)
        attempts = list((self.output / "attempts").iterdir())
        self.assertEqual(len(attempts), 2)
        for attempt in attempts:
            launch = json.loads((attempt / "launch-prepared.json").read_text())
            sealed = launch["native_runner_result_inputs"]["requests"][RUNNER_REQUEST_PATH]
            self.assertEqual(sealed["sha256"], hashlib.sha256(payload).hexdigest())
            capture = json.loads((attempt / "capture.json").read_text())["payload"]
            receipt = capture["observation"]["native_metadata"]["controller_runner_results"]
            self.assertEqual(receipt["checks"][0]["actual"]["status"], "expected_failure")
            self.assertEqual(receipt["checks"][0]["actual"]["exit_code"], 1)

        changed = runner_result_case()
        changed["checks"][0]["pattern"] = "binding.resul."
        replay_callbacks = RunnerResultCallbacks(self.output)
        replay = run_evaluations(
            config(self.output), {}, [changed], rows, repo_root=self.repo,
            prepare=replay_callbacks.prepare, execute=replay_callbacks.execute,
        )
        self.assertEqual(replay["counts"]["passes"], 2, replay)
        self.assertEqual(replay["counts"]["regraded"], 2, replay)
        self.assertEqual(replay["counts"]["subject_launches"], 0, replay)
        self.assertEqual(replay_callbacks.executed, [])

    def test_codex_verify_child_runner_result_is_hash_bound_and_graded(self):
        payload = (json.dumps(runner_request(), sort_keys=True, indent=2) + "\n").encode()
        (self.repo / "request.json").write_bytes(payload)
        callbacks = ChildVerifyRunnerResultCallbacks(self.output)
        report = run_evaluations(
            config(self.output), {}, [runner_result_case()], [row("codex")],
            repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(report["counts"]["passes"], 1, report)
        self.assertEqual(report["counts"]["infrastructure_invalid"], 0, report)
        attempt = next((self.output / "attempts").iterdir())
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        receipt = capture["observation"]["native_metadata"]["controller_runner_results"]
        self.assertEqual(receipt["checks"][0]["actual"]["status"], "expected_failure")
        child_call = next(
            call for call in capture["observation"]["tool_calls"]
            if call.get("id") == "verify-runner-command"
        )
        self.assertIsNotNone(child_call["parent_id"])
        self.assertEqual(child_call["input"]["_native"]["thread_id"], CHILD_THREAD)

    def test_native_runner_claim_only_is_invalid_and_wrong_outcome_fails_both_hosts(self):
        payload = (json.dumps(runner_request(), sort_keys=True, indent=2) + "\n").encode()
        (self.repo / "request.json").write_bytes(payload)
        for variation, count_key in (
            ("claim-only", "infrastructure_invalid"),
            ("wrong-outcome", "behavior_fails"),
        ):
            with self.subTest(variation=variation):
                output = self.root / variation
                callbacks = RunnerResultCallbacks(output, variation=variation)
                report = run_evaluations(
                    config(output), {}, [runner_result_case()],
                    [row("claude"), row("codex")], repo_root=self.repo,
                    prepare=callbacks.prepare, execute=callbacks.execute,
                )
                self.assertEqual(report["counts"][count_key], 2, report)
                self.assertEqual(report["counts"]["passes"], 0, report)

    def test_native_runner_rejects_unauthenticated_or_incomplete_commands_both_hosts(self):
        payload = (json.dumps(runner_request(), sort_keys=True, indent=2) + "\n").encode()
        (self.repo / "request.json").write_bytes(payload)
        for variation in (
            "wrong-path", "wrong-runtime", "duplicate-output", "truncated-output",
            "wrong-exit",
        ):
            with self.subTest(variation=variation):
                output = self.root / variation
                callbacks = RunnerResultCallbacks(output, variation=variation)
                report = run_evaluations(
                    config(output), {}, [runner_result_case()],
                    [row("claude"), row("codex")], repo_root=self.repo,
                    prepare=callbacks.prepare, execute=callbacks.execute,
                )
                self.assertEqual(report["counts"]["infrastructure_invalid"], 2, report)
                self.assertEqual(report["counts"]["passes"], 0, report)

    def test_native_runner_rejects_codex_command_from_wrong_cwd(self):
        payload = (json.dumps(runner_request(), sort_keys=True, indent=2) + "\n").encode()
        (self.repo / "request.json").write_bytes(payload)
        callbacks = RunnerResultCallbacks(self.output, variation="wrong-cwd")
        report = run_evaluations(
            config(self.output), {}, [runner_result_case()], [row("codex")],
            repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
        )
        self.assertEqual(report["counts"]["infrastructure_invalid"], 1, report)
        self.assertEqual(report["counts"]["passes"], 0, report)

    def test_causal_wrong_order_early_later_and_wrong_writer_fail_both_hosts(self):
        for variation in ("early-write", "child-writer", "bash-write", "unrelated-write"):
            with self.subTest(variation=variation):
                output = self.root / variation
                callbacks = CausalCallbacks(output, variation=variation)
                report = run_evaluations(
                    config(output), {}, [causal_case()], [row("claude"), row("codex")],
                    repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
                )
                self.assertEqual(report["counts"]["passes"], 0, report)
                self.assertEqual(report["counts"]["behavior_fails"], 2, report)
                self.assertEqual(report["counts"]["infrastructure_invalid"], 0, report)

    def test_causal_missing_empty_and_reused_returns_are_invalid(self):
        for variation in ("missing-return", "empty-return", "reused"):
            with self.subTest(variation=variation):
                output = self.root / variation
                callbacks = CausalCallbacks(output, variation=variation)
                report = run_evaluations(
                    config(output), {}, [causal_case()], [row("claude"), row("codex")],
                    repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
                )
                self.assertEqual(report["counts"]["passes"], 0, report)
                self.assertEqual(report["counts"]["infrastructure_invalid"], 2, report)
                self.assertEqual(report["counts"]["behavior_fails"], 0, report)

        for variation in ("empty-wrapper", "null-return"):
            with self.subTest(variation=variation):
                output = self.root / variation
                callbacks = CausalCallbacks(output, variation=variation)
                report = run_evaluations(
                    config(output), {}, [causal_case()], [row("claude")], repo_root=self.repo,
                    prepare=callbacks.prepare, execute=callbacks.execute,
                )
                self.assertEqual(report["counts"]["infrastructure_invalid"], 1, report)

    def test_causal_codex_wrong_or_absent_action_turn_is_invalid(self):
        for variation in ("wrong-turn", "absent-turn"):
            with self.subTest(variation=variation):
                output = self.root / variation
                callbacks = CausalCallbacks(output, variation=variation)
                report = run_evaluations(
                    config(output), {}, [causal_case()], [row("codex")], repo_root=self.repo,
                    prepare=callbacks.prepare, execute=callbacks.execute,
                )
                self.assertEqual(report["counts"]["infrastructure_invalid"], 1, report)

    def test_causal_spoofed_indexes_streams_and_content_are_invalid(self):
        callbacks = CausalCallbacks(self.output)
        report = run_evaluations(config(self.output), {}, [causal_case()],
                                 [row("claude"), row("codex")],
                                 repo_root=self.repo, prepare=callbacks.prepare,
                                 execute=callbacks.execute)
        self.assertEqual(report["counts"]["passes"], 2, report)
        for attempt in (self.output / "attempts").iterdir():
            original = json.loads((attempt / "capture.json").read_text())["payload"]["observation"]
            host = json.loads((attempt / "launch-prepared.json").read_text())["host"]
            for field, value in (("completion_index", 999), ("native_stream", "other-stream"),
                                 ("content_sha256", "0" * 64), ("tool_call_index", 99)):
                with self.subTest(host=host, field=field):
                    changed = copy.deepcopy(original)
                    changed["native_metadata"]["subagent_return_order"]["returns"][0][field] = value
                    verdict = execution.grade_observation(causal_case(), changed)
                    self.assertEqual(verdict["status"], "invalid", verdict)
            changed = copy.deepcopy(original)
            changed["native_metadata"]["subagent_return_order"]["parent_file_changes"][0][
                "paths"] = ["forged-target.txt"]
            verdict = execution.grade_observation(causal_case("forged-target.txt"), changed)
            self.assertEqual(verdict["status"], "invalid", (host, verdict))

        self.assertEqual(execution._change_paths(
            "claude", {"name": "Read", "input": "valid JSON string"}, None,
        ), [])

    def test_nested_codex_no_child_cycle_and_wrong_cwd_fail_closed(self):
        for variation in ("no-child", "cycle", "wrong-cwd"):
            with self.subTest(variation=variation):
                output = self.root / variation
                callbacks = NestedCallbacks(output, variation=variation)
                report = run_evaluations(config(output), {}, [case(resource_class="nested")],
                                         [row("codex")], repo_root=self.repo,
                                         prepare=callbacks.prepare, execute=callbacks.execute)
                self.assertEqual(report["counts"]["passes"], 0)
                self.assertEqual(report["counts"]["infrastructure_invalid"], 1)
                attempt = next((output / "attempts").iterdir())
                capture = json.loads((attempt / "capture.json").read_text())["payload"]
                self.assertIsNone(capture["observation"])
                self.assertIsInstance(capture["error"], str)

    def test_invalid_codex_capture_is_renormalized_without_subject_relaunch(self):
        value = case(resource_class="nested")
        callbacks = NestedCallbacks(self.output)
        with mock.patch(
            "native_eval_execution.collect_native_tree",
            side_effect=NativeRolloutInvalid("legacy parser rejected capture"),
        ):
            initial = run_evaluations(
                config(self.output), {}, [value], [row("codex")],
                repo_root=self.repo, prepare=callbacks.prepare, execute=callbacks.execute,
            )
        self.assertEqual(initial["counts"]["infrastructure_invalid"], 1, initial)
        self.assertEqual(initial["counts"]["subject_launches"], 1)
        original_attempt = next((self.output / "attempts").iterdir())
        original_capture = json.loads(
            (original_attempt / "capture.json").read_text()
        )["payload"]
        self.assertIsNone(original_capture["observation"])
        self.assertIn("legacy parser rejected capture", original_capture["error"])
        self.assertTrue({"launch_prepared", "raw_trace", "process_receipt"}.issubset(
            original_capture["evidence"]
        ))

        resumed = NestedCallbacks(self.output)
        replay = run_evaluations(
            config(self.output), {}, [value], [row("codex")],
            repo_root=self.repo, prepare=resumed.prepare, execute=resumed.execute,
        )

        self.assertEqual(replay["counts"]["passes"], 1, replay)
        self.assertEqual(replay["counts"]["regraded"], 1)
        self.assertEqual(replay["counts"]["subject_launches"], 0)
        self.assertEqual(replay["results"][0]["reason"], "raw_capture_renormalized")
        self.assertEqual(resumed.executed, [])
        attempts = list((self.output / "attempts").iterdir())
        self.assertEqual(len(attempts), 2)
        recovered = next(path for path in attempts if path != original_attempt)
        recovered_capture = json.loads(
            (recovered / "capture.json").read_text()
        )["payload"]
        self.assertIsNone(recovered_capture["error"])
        self.assertIsNotNone(recovered_capture["observation"])
        self.assertTrue((recovered / "native-rollouts" / "supplement.json").is_file())

    def test_invalid_codex_capture_replays_retained_rollouts_after_session_cleanup(self):
        value, callbacks, original_attempt, rollout_labels = \
            retained_invalid_codex_capture(self)
        replay, resumed = replay_retained_codex_capture(self, value, callbacks)

        self.assertEqual(replay["counts"]["passes"], 1, replay)
        self.assertEqual(replay["counts"]["regraded"], 1)
        self.assertEqual(replay["counts"]["subject_launches"], 0)
        self.assertEqual(resumed.executed, [])
        recovered = next(
            path for path in (self.output / "attempts").iterdir()
            if path != original_attempt
        )
        recovered_capture = json.loads(
            (recovered / "capture.json").read_text()
        )["payload"]
        self.assertTrue(rollout_labels.issubset(recovered_capture["evidence"]))

    def test_retained_rollout_reference_index_fails_closed(self):
        label = execution._rollout_label(ROOT_THREAD)
        reference = {"path": "native-rollouts/root.jsonl", "sha256": "0" * 64}
        self.assertEqual(
            execution._retained_rollout_thread_ids({label: reference}),
            (ROOT_THREAD,),
        )
        for refs in (
            {"codex_rollout_not_a_uuid": reference},
            {"codex_rollout_AAAAAAAA_AAAA_AAAA_AAAA_AAAAAAAAAAAA": reference},
            {label: None},
        ):
            with self.subTest(refs=refs), self.assertRaises(ValueError):
                execution._retained_rollout_thread_ids(refs)

    def test_nested_order_check_is_invalid_when_cross_thread_timeline_is_ambiguous(self):
        value = case(resource_class="nested")
        value["checks"].append({"id": "ordered", "requirement": "r1", "type": "tool_order",
                                "before": "command_execution", "after": "file_change"})
        callbacks = NestedCallbacks(self.output, variation="ambiguous-order")
        report = run_evaluations(config(self.output), {}, [value], [row("codex")],
                                 repo_root=self.repo, prepare=callbacks.prepare,
                                 execute=callbacks.execute)
        self.assertEqual(report["counts"]["infrastructure_invalid"], 1)
        self.assertIn("cannot establish an exact cross-thread tool order",
                      report["results"][0]["reason"])

    def test_regrade_restores_hash_bound_artifact_absence_without_relaunch(self):
        value = case()
        value["checks"] = [{"id": "absent", "requirement": "r1", "type": "file_exists",
                            "path": "report.txt", "exists": False}]
        first = FakeCallbacks(self.output)
        initial = run_evaluations(config(self.output), {}, [value], [row()], repo_root=self.repo,
                                  prepare=first.prepare, execute=first.execute)
        self.assertEqual(initial["counts"]["passes"], 1)
        attempt = next((self.output / "attempts").iterdir())
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        self.assertIn("artifact_manifest", capture["evidence"])
        changed = copy.deepcopy(value)
        changed["checks"][0]["exists"] = True
        resumed = FakeCallbacks(self.output)
        report = run_evaluations(config(self.output), {}, [changed], [row()], repo_root=self.repo,
                                 prepare=resumed.prepare, execute=resumed.execute)
        self.assertEqual(report["counts"]["behavior_fails"], 1)
        self.assertEqual(report["counts"]["regraded"], 1)
        self.assertEqual(report["results"][0]["reason"], "raw_capture_renormalized")
        self.assertEqual(resumed.executed, [])

    def test_regrade_restores_exact_retained_artifact_bytes(self):
        value = case()
        value["checks"] = [{"id": "text", "requirement": "r1", "type": "text",
                            "source": "report.txt", "pattern": "artifact-v1"}]
        callbacks = FakeCallbacks(self.output)
        base_execute = callbacks.execute

        def execute_with_artifact(prepared, timeout):
            (prepared.artifact_root / "report.txt").write_text("artifact-v1")
            return base_execute(prepared, timeout)

        initial = run_evaluations(config(self.output), {}, [value], [row()], repo_root=self.repo,
                                  prepare=callbacks.prepare, execute=execute_with_artifact)
        self.assertEqual(initial["counts"]["passes"], 1)
        changed = copy.deepcopy(value)
        changed["checks"][0]["pattern"] = "artifact-v2"
        resumed = FakeCallbacks(self.output)
        report = run_evaluations(config(self.output), {}, [changed], [row()], repo_root=self.repo,
                                 prepare=resumed.prepare, execute=resumed.execute)
        self.assertEqual(report["counts"]["behavior_fails"], 1)
        self.assertEqual(report["counts"]["regraded"], 1)
        self.assertEqual(resumed.executed, [])
        attempt = next((self.output / "attempts").iterdir())
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        label = next(key for key in capture["evidence"]
                     if key.startswith("artifact_") and key != "artifact_manifest")
        retained = attempt / capture["evidence"][label]["path"]
        self.assertEqual(retained.read_bytes(), b"artifact-v1")

    def test_execute_exception_is_retained_as_invalid_capture(self):
        callbacks = FakeCallbacks(self.output)

        def explode(prepared, timeout):
            callbacks.executed.append(prepared.host)
            raise RuntimeError("native transport unavailable")

        report = run_evaluations(config(self.output), {}, [case()], [row()], repo_root=self.repo,
                                 prepare=callbacks.prepare, execute=explode)
        self.assertEqual(report["counts"]["infrastructure_invalid"], 1)
        attempt = next((self.output / "attempts").iterdir())
        capture = json.loads((attempt / "capture.json").read_text())["payload"]
        self.assertIn("native transport unavailable", capture["error"])
        self.assertIn("launch_prepared", capture["evidence"])

    def test_observed_missing_or_malformed_output_is_a_preserved_behavior_failure(self):
        for host in ("claude", "codex"):
            for kind in ("missing-text", "missing-json", "malformed-json"):
                with self.subTest(host=host, kind=kind):
                    output = self.root / f"{host}-{kind}"
                    callbacks = FakeCallbacks(output)
                    value = case()
                    check = {"id": "output", "requirement": "r1"}
                    if kind == "missing-text":
                        check.update(type="text", source="report.txt", pattern="ready")
                    else:
                        check.update(type="json_field", path="report.txt",
                                     field_path=["ready"], expected=True)
                    value["checks"] = [check]
                    base_execute = callbacks.execute

                    def execute_with_output(prepared, timeout):
                        if kind == "malformed-json":
                            (prepared.artifact_root / "report.txt").write_text("{broken")
                        return base_execute(prepared, timeout)

                    report = run_evaluations(
                        config(output), {}, [value], [row(host)], repo_root=self.repo,
                        prepare=callbacks.prepare, execute=execute_with_output,
                    )
                    self.assertEqual(report["counts"]["behavior_fails"], 1, report)
                    self.assertEqual(report["counts"]["infrastructure_invalid"], 0, report)
                    resumed = FakeCallbacks(output)
                    again = run_evaluations(
                        config(output), {}, [value], [row(host)], repo_root=self.repo,
                        prepare=resumed.prepare, execute=resumed.execute,
                    )
                    self.assertEqual(again["counts"]["behavior_fails"], 1)
                    self.assertEqual(again["counts"]["reused"], 1)
                    self.assertEqual(resumed.executed, [])

    def test_declared_binary_or_symlink_artifact_is_invalid_not_a_missing_pass(self):
        value = case()
        value["checks"] = [{"id": "exists", "requirement": "r1", "type": "file_exists",
                            "path": "report.txt", "exists": False}]
        for kind in ("binary", "symlink"):
            with self.subTest(kind=kind):
                output = self.root / kind
                callbacks = FakeCallbacks(output)
                base_execute = callbacks.execute

                def execute_with_artifact(prepared, timeout, selected=kind):
                    if selected == "binary":
                        (prepared.artifact_root / "report.txt").write_bytes(b"\xff")
                    else:
                        outside = self.root / "outside.txt"
                        outside.write_text("outside")
                        (prepared.artifact_root / "report.txt").symlink_to(outside)
                    return base_execute(prepared, timeout)

                report = run_evaluations(config(output), {}, [value], [row()], repo_root=self.repo,
                                         prepare=callbacks.prepare, execute=execute_with_artifact)
                self.assertEqual(report["counts"]["infrastructure_invalid"], 1)
                self.assertEqual(report["counts"]["passes"], 0)

    def test_plan_repair_context_binds_exact_dispatch_and_causal_rerun(self):
        request = {
            "schema_version": "1.0", "request_id": "plan-repair-g3",
            "helper_id": "validate-gate", "operation": "validate-gate",
            "mode": "read_only", "inputs": {"gate": "G3", "feature_dir": "feature"},
        }
        contexts = {
            "original-prompt": "Design the original human requirement.\n",
            "architecture": "No delivery callback is currently available.\n",
        }

        def response(passed):
            return {
                "schema_version": "1.0", "request_id": request["request_id"],
                "status": "success" if passed else "expected_failure", "exit_code": 0 if passed else 1,
                "data": {"stdin_request": {key: value for key, value in request.items()
                                             if key != "request_id"},
                         "stdout_json": {"gate": "G3", "pass": passed, "markers": 0 if passed else 1}},
            }

        initial, repaired = response(False), response(True)
        message = "\n".join([*contexts.values(), json.dumps(initial, indent=2)])
        command = "python3 -m speckit_pro_runner < scenario-inputs/g3-request.json"
        calls = [
            {"id": "g3-initial", "name": "Bash", "input": {"command": command},
             "output": json.dumps({"code": "validation_failure"}) + "\n" + json.dumps(initial),
             "success": False, "position": 1, "parent_id": None},
            {"id": "repair", "name": "subagent",
             "input": {"prompt": message, "subagent_type": "phase-executor"},
             "output": "repair complete", "success": True, "position": 3, "parent_id": None},
            {"id": "g3-rerun", "name": "Bash", "input": {"command": command},
             "output": json.dumps(repaired), "success": True, "position": 5, "parent_id": None},
        ]
        completions = []
        for index, call in enumerate(calls):
            encoded = json.dumps(call["output"], sort_keys=True, separators=(",", ":")).encode()
            completions.append({
                "tool_call_index": index, "id": call["id"],
                "native_name": "Agent" if index == 1 else "Bash",
                "tool_use_position": call["position"],
                "tool_result_position": call["position"] + 1,
                "output_sha256": hashlib.sha256(encoded).hexdigest(),
                "output_bytes": len(encoded),
            })
        observation = {
            "completed": True, "error": None, "final_text": "done", "activations": [],
            "tool_calls": calls, "artifacts": {}, "usage": {},
            "native_metadata": {"claude_tool_results": completions},
        }
        check = {
            "id": "repair-context", "requirement": "r1",
            "type": "native_plan_repair_context",
            "contexts": {"original-prompt": "scenario-inputs/original.md",
                         "architecture": "scenario-inputs/architecture.md"},
            "g3_request_path": "scenario-inputs/g3-request.json",
            "executor_role": "phase-executor", "max_repairs": 2,
            "terminal_outcome": "pass",
        }
        value = {"requirements": [{"id": "r1"}], "checks": [check]}
        fixture_values = {
            "scenario-inputs/original.md": contexts["original-prompt"],
            "scenario-inputs/architecture.md": contexts["architecture"],
            "scenario-inputs/g3-request.json": json.dumps(request),
        }
        sealed = {path: {"text": text, "bytes": len(text.encode()),
                         "sha256": hashlib.sha256(text.encode()).hexdigest()}
                  for path, text in fixture_values.items()}
        launch = {
            "cwd": "/private/tmp/plugin", "runtime_identity": {"settings": {
                "native_toolchain": {"launchers": {"python3": {"path": "bin/python3"}}},
            }},
            "native_plan_repair_inputs": {
                "schema": "native-plan-repair-sealed-inputs/v1",
                "authority": "controller-before-subject-launch", "fixtures": sealed,
            },
        }
        execution._bind_subagent_return_order("claude", observation)
        execution._bind_plan_repair_context(value, "claude", observation, launch)
        self.assertEqual(execution.grade_observation(value, observation, host="claude")["status"],
                         "pass")
        receipt = observation["native_metadata"]["native_plan_repair_context"]
        self.assertNotIn(message, json.dumps(receipt))

        for native_role, expected in (
            ("speckit-pro:phase-executor", "pass"),
            ("foreign:phase-executor", "fail"),
            ("speckit-pro:other-executor", "fail"),
        ):
            with self.subTest(native_role=native_role):
                variant = copy.deepcopy(observation)
                del variant["native_metadata"]["native_plan_repair_context"]
                variant["tool_calls"][1]["input"]["subagent_type"] = native_role
                execution._bind_plan_repair_context(value, "claude", variant, launch)
                self.assertEqual(
                    execution.grade_observation(value, variant, host="claude")["status"], expected,
                )

        float_limit = copy.deepcopy(value)
        float_limit["checks"][0]["max_repairs"] = 2.0
        self.assertEqual(
            execution.grade_observation(float_limit, observation, host="claude")["status"],
            "invalid",
        )

        missing = copy.deepcopy(observation)
        del missing["native_metadata"]["native_plan_repair_context"]
        missing["tool_calls"][1]["input"]["prompt"] = (
            contexts["original-prompt"] + json.dumps(initial)
        )
        execution._bind_plan_repair_context(value, "claude", missing, launch)
        self.assertEqual(execution.grade_observation(value, missing, host="claude")["status"],
                         "fail")

        late = copy.deepcopy(observation)
        late_receipt = late["native_metadata"]["native_plan_repair_context"]["checks"][0]
        late_receipt["dispatches"][0]["returned"] = 6
        self.assertEqual(execution.grade_observation(value, late, host="claude")["status"],
                         "fail")

    def test_codex_plan_repair_context_binds_raw_message_to_opaque_native_input(self):
        request = {"schema_version": "1.0", "request_id": "g3", "helper_id": "validate-gate",
                   "operation": "validate-gate", "mode": "read_only",
                   "inputs": {"gate": "G3", "feature_dir": "feature"}}

        def response(passed):
            return {"schema_version": "1.0", "request_id": "g3",
                    "data": {"stdin_request": {key: value for key, value in request.items()
                                                if key != "request_id"},
                             "stdout_json": {"pass": passed}}}

        context = "Original Plan prompt"
        initial, rerun = response(False), response(True)
        message = context + "\n" + json.dumps(initial)
        encoded_message = json.dumps(message, sort_keys=True, separators=(",", ":")).encode()
        opaque = {"kind": "opaque", "sha256": hashlib.sha256(encoded_message).hexdigest(),
                  "bytes": len(encoded_message)}
        delivery_text = b"repair complete"
        delivery = {"turn_id": ROOT_TURN, "author": "/root/repair", "recipient": "/root",
                    "native_event_index": 9, "bytes": len(delivery_text),
                    "sha256": hashlib.sha256(delivery_text).hexdigest()}
        command = ["/bin/zsh", "-c",
                   "python3 -m speckit_pro_runner < scenario-inputs/g3-request.json"]
        calls = [
            {"id": "g3-0", "name": "command_execution", "input": {"command": command},
             "output": json.dumps(initial), "success": False, "position": 0, "parent_id": None},
            {"id": "repair", "name": "subagent", "input": {"role": "phase-executor",
             "task_input": opaque}, "output": {"status": "completed"}, "success": True,
             "position": 1, "parent_id": None},
            {"id": "g3-1", "name": "command_execution", "input": {"command": command},
             "output": json.dumps(rerun), "success": True, "position": 2, "parent_id": None},
        ]
        observation = {
            "completed": True, "error": None, "final_text": "done", "activations": [],
            "tool_calls": calls, "artifacts": {}, "usage": {}, "native_metadata": {
                "nested_rollout": {"root_thread_id": ROOT_THREAD,
                    "raw_sha256": {ROOT_THREAD: "a" * 64},
                    "dispatches": [{"id": "repair", "parent_thread_id": ROOT_THREAD,
                                    "task_input": opaque, "delivery": delivery}]},
                "subagent_return_order": {"schema": "native-subagent-return-order/v1",
                    "scope": "direct-root-only", "parent_file_changes": [], "returns": [{
                        "tool_call_index": 1, "call_id": "repair",
                        "authority": "codex-parent-delivery", "native_stream": ROOT_THREAD,
                        "native_turn": ROOT_TURN, "completion_index": 9,
                        "content_sha256": delivery["sha256"], "content_bytes": delivery["bytes"],
                        "content_nonempty": True,
                    }]},
            },
        }
        check = {"id": "context", "requirement": "r1",
                 "type": "native_plan_repair_context",
                 "contexts": {"original": "scenario-inputs/original.md"},
                 "g3_request_path": "scenario-inputs/g3-request.json",
                 "executor_role": "phase-executor", "max_repairs": 2,
                 "terminal_outcome": "pass"}
        value = {"requirements": [{"id": "r1"}], "checks": [check]}
        fixtures = {"scenario-inputs/original.md": context,
                    "scenario-inputs/g3-request.json": json.dumps(request)}
        sealed = {path: {"text": text, "bytes": len(text.encode()),
                         "sha256": hashlib.sha256(text.encode()).hexdigest()}
                  for path, text in fixtures.items()}
        launch = {"runtime_identity": {"settings": {"codex_runtime": {"python": {
            "python3_command": "python3", "python3_path": "/protected/bin/python3",
            "executable": "/protected/bin/python3.11",
        }}}}, "native_plan_repair_inputs": {
            "schema": "native-plan-repair-sealed-inputs/v1",
            "authority": "controller-before-subject-launch", "fixtures": sealed,
        }}
        trace = {"schema": "codex-native-plan-repair-trace/v1",
                 "root_thread_id": ROOT_THREAD, "raw_sha256": "a" * 64,
                 "commands": [
                     {"id": "g3-0", "started_at_ns": 1, "completed_at_ns": 2,
                      "input": {"command": command}, "output": {"stdout": json.dumps(initial)}},
                     {"id": "g3-1", "started_at_ns": 7, "completed_at_ns": 8,
                      "input": {"command": command}, "output": {"stdout": json.dumps(rerun)}},
                 ],
                 "dispatches": [{"id": "repair", "role": "phase-executor",
                                  "message": message, "task_input": opaque,
                                  "invoked_at_ns": 3, "returned_at_ns": 6}]}
        execution._bind_plan_repair_context(value, "codex", observation, launch, trace)
        self.assertEqual(execution.grade_observation(value, observation, host="codex")["status"],
                         "pass")
        receipt = observation["native_metadata"]["native_plan_repair_context"]
        self.assertNotIn(message, json.dumps(receipt))
        self.assertEqual(receipt["checks"][0]["dispatches"][0]["opaque_task_input"], opaque)

    def test_plan_repair_sealing_rejects_unavailable_or_changed_trusted_fixture(self):
        fixture = self.repo / "plan-context.md"
        fixture.write_text("trusted context\n")
        body = fixture.read_bytes()
        value = {"fixtures": [{"source": "plan-context.md",
                                "destination": "scenario-inputs/context.md"}],
                 "checks": [{"id": "context", "type": "native_plan_repair_context",
                              "contexts": {"plan": "scenario-inputs/context.md"},
                              "g3_request_path": "scenario-inputs/context.md"}]}
        prepared = SimpleNamespace(runtime_identity={"settings": {"fixture_read_witnesses": {
            "scenario-inputs/context.md": {"bytes": len(body),
                                             "sha256": hashlib.sha256(body).hexdigest()},
        }}})
        sealed = execution._sealed_plan_repair_inputs(value, prepared, self.repo)
        self.assertEqual(sealed["authority"], "controller-before-subject-launch")

        fixture.write_text("changed\n")
        with self.assertRaisesRegex(ValueError, "witness changed"):
            execution._sealed_plan_repair_inputs(value, prepared, self.repo)
        fixture.unlink()
        with self.assertRaisesRegex(ValueError, "unavailable"):
            execution._sealed_plan_repair_inputs(value, prepared, self.repo)


if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(NativeExecutionTests),
                                 label="test-native-eval-execution"))
