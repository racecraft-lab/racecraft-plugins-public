#!/usr/bin/env python3
"""Codex native rollout supplements must prove, not infer, nested behavior."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted
import native_eval_codex_rollouts as rollouts
from native_eval_codex_rollouts import (
    NativeRolloutIncomplete,
    NativeRolloutInvalid,
    NativeRolloutPending,
    collect_native_skill_injections,
    collect_native_tree,
    extract_native_plan_repair_trace,
    parse_native_skill_injections,
    parse_native_tree,
)


# Synthetic identities keep real native session identifiers out of public fixtures.
ROOT = str(uuid.UUID(int=1))
CHILD = str(uuid.UUID(int=2))
GRANDCHILD = str(uuid.UUID(int=3))
ROOT_TURN = str(uuid.UUID(int=4))
CHILD_TURN = str(uuid.UUID(int=5))
SECOND_CHILD = str(uuid.UUID(int=7))
CWD = "/private/tmp/native-case/workspace"
CALL = "call_native_spawn"
PROMPT = "Use $alpha to inspect the declared fixture."
ALPHA_BODY = "---\nname: alpha\ndescription: synthetic project skill\n---\n\n" + "A" * 8_500 + "\n"
BETA_BODY = "---\nname: beta\ndescription: synthetic sibling skill\n---\n\nBeta body.\n"
GAMMA_BODY = "---\nname: gamma\ndescription: second synthetic sibling\n---\n\nGamma body.\n"
_MISSING = object()


def line(value):
    return json.dumps(value, separators=(",", ":"))


def meta(thread_id, *, parent=None, depth=0, path="/root/read_fixture", cwd=CWD):
    source = "exec" if parent is None else {"subagent": {"thread_spawn": {
        "parent_thread_id": parent,
        "depth": depth,
        "agent_path": path,
        "agent_nickname": "Ohm",
        "agent_role": "native_canary_worker",
    }}}
    return {"timestamp": "2026-09-15T16:36:42Z", "type": "session_meta", "payload": {
        "id": thread_id,
        "session_id": parent or thread_id,
        "cwd": cwd,
        "cli_version": "0.154.0",
        "model_provider": "openai",
        "source": source,
        "thread_source": "user" if parent is None else "subagent",
    }}


def event(payload):
    return {"timestamp": "2026-09-15T16:36:42Z", "type": "event_msg", "payload": payload}


def root_records(*, child=CHILD, call_id=CALL, message="Read only fixture.txt"):
    return [
        meta(ROOT),
        event({"type": "task_started", "turn_id": ROOT_TURN, "started_at": 1}),
        {"timestamp": "2026-09-15T16:36:43Z", "type": "response_item", "payload": {
            "type": "function_call", "namespace": "collaboration", "name": "spawn_agent",
            "call_id": call_id, "arguments": line({"agent_type": "native_canary_worker",
                "fork_turns": "all", "message": message, "task_name": "read_fixture"}),
        }},
        event({"type": "item_completed", "thread_id": ROOT, "turn_id": ROOT_TURN,
            "item": {"type": "SubAgentActivity", "id": call_id, "kind": "started",
                "agent_thread_id": child, "agent_path": "/root/read_fixture"}}),
        event({"type": "item_completed", "thread_id": ROOT, "turn_id": ROOT_TURN,
            "item": {"type": "CommandExecution", "id": "root-command", "status": "completed",
                "command": ["echo", "must-not-be-supplemented"], "stdout": "root\n", "exit_code": 0}}),
        event({"type": "item_completed", "thread_id": ROOT, "turn_id": ROOT_TURN,
            "item": {"type": "CollabAgentToolCall", "id": "wait-call", "tool": "wait",
                "status": "completed", "sender_thread_id": ROOT, "receiver_thread_ids": []}}),
        event({"type": "item_completed", "thread_id": ROOT, "turn_id": ROOT_TURN,
            "item": {"type": "SubAgentActivity", "id": "subagent-completed-turn", "kind": "completed",
                "agent_thread_id": child, "agent_path": "/root/read_fixture"}}),
        event({"type": "task_complete", "turn_id": ROOT_TURN, "completed_at": 2}),
    ]


def delivery_record(*, author="/root/read_fixture", recipient="/root", turn=ROOT_TURN,
                    text="Message Type: FINAL_ANSWER\nPayload:\nCANARY_OK", message_id="delivery-1"):
    payload = {
        "type": "agent_message",
        "author": author,
        "recipient": recipient,
        "content": [{"type": "input_text", "text": text}],
        "internal_chat_message_metadata_passthrough": {
            "turn_id": turn,
            "create_time": 1_789_490_214.196796,
        },
    }
    if message_id is not _MISSING:
        payload["id"] = message_id
    return {"timestamp": "2026-09-15T16:36:49Z", "type": "response_item",
            "payload": payload}


def child_records(*, thread=CHILD, parent=ROOT, depth=1, path="/root/read_fixture",
                  cwd=CWD, turn=CHILD_TURN, status="completed", exit_code=0):
    return [
        meta(thread, parent=parent, depth=depth, path=path, cwd=cwd),
        meta(ROOT),  # Native child rollouts include inherited parent history.
        event({"type": "task_started", "turn_id": ROOT_TURN, "started_at": 1}),
        event({"type": "thread_settings_applied", "thread_id": thread}),
        event({"type": "task_started", "turn_id": turn, "started_at": 3}),
        {"timestamp": "2026-09-15T16:36:47Z", "type": "turn_context", "payload": {
            "turn_id": turn, "root_turn_id": ROOT_TURN, "cwd": cwd, "model": "gpt-5.6-sol"}},
        event({"type": "item_completed", "thread_id": thread, "turn_id": turn, "item": {
            "type": "CommandExecution", "id": "exec-child", "status": status,
            "command": ["/bin/zsh", "-c", "cat fixture.txt"], "cwd": cwd,
            "stdout": "canary-input-v1\n", "stderr": "", "aggregated_output": "canary-input-v1\n",
            "formatted_output": "canary-input-v1\n", "exit_code": exit_code,
        }}),
        {"timestamp": "2026-09-15T16:36:48Z", "type": "token_usage_record", "payload": {
            "thread_id": thread, "turn_id": turn, "root_turn_id": ROOT_TURN,
            "thread_token_usage": {"input_tokens": 24586, "cached_input_tokens": 9600,
                "cache_write_input_tokens": 0, "output_tokens": 92,
                "reasoning_output_tokens": 14, "total_tokens": 24678},
        }},
        event({"type": "item_completed", "thread_id": thread, "turn_id": turn,
            "item": {"type": "AgentMessage", "id": "message", "content": [{"type": "text",
                "text": "final prose is not tool evidence"}]}}),
        event({"type": "task_complete", "turn_id": turn, "completed_at": 4}),
    ]


def raw(records):
    return ("\n".join(line(record) for record in records) + "\n").encode()


def fixture_tree():
    return {ROOT: raw(root_records()), CHILD: raw(child_records())}


def root_only_tree():
    records = [
        record for record in root_records()
        if record.get("payload", {}).get("type") != "function_call"
        and record.get("payload", {}).get("item", {}).get("type") != "SubAgentActivity"
    ]
    return {ROOT: raw(records)}


def skill_witness(name, text):
    encoded = text.encode("utf-8")
    return {
        "path": f".agents/skills/{name}/SKILL.md",
        "text": text,
        "bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def skill_witnesses():
    return {"alpha": skill_witness("alpha", ALPHA_BODY),
            "beta": skill_witness("beta", BETA_BODY),
            "gamma": skill_witness("gamma", GAMMA_BODY)}


def selected_skill_text(name, witnesses=None, *, cwd=CWD, plugin_name=None):
    witness = (witnesses or skill_witnesses())[name]
    native_name = f"{plugin_name}:{name}" if plugin_name is not None else name
    return (f"<skill>\n<name>{native_name}</name>\n<path>{cwd}/{witness['path']}</path>\n"
            f"{witness['text']}\n</skill>")


def user_message(text, *, turn=ROOT_TURN, kind="user.text", message_id=_MISSING,
                 role="user"):
    payload = {
        "type": "message",
        "role": role,
        "content": [{"type": "input_text", "text": text}],
        "internal_chat_message_metadata_passthrough": {
            "content_item_kinds": [kind],
            "turn_id": turn,
            "create_time": 1_789_492_602,
        },
    }
    if message_id is not _MISSING:
        payload["id"] = message_id
    return {"timestamp": "2026-09-15T16:36:43Z", "type": "response_item",
            "payload": payload}


def skill_records(*, selected="alpha", include_injection=True, message_id=_MISSING,
                  plugin_name=None):
    records = [
        meta(ROOT),
        event({"type": "task_started", "turn_id": ROOT_TURN, "started_at": 1}),
        user_message(PROMPT, message_id="prompt-message"),
    ]
    if include_injection:
        records.append(user_message(
            selected_skill_text(selected, plugin_name=plugin_name),
            kind="skills.selected_skill_instructions",
            message_id=message_id,
        ))
    records.extend([
        event({"type": "item_completed", "thread_id": ROOT, "turn_id": ROOT_TURN,
               "item": {"type": "AgentMessage", "id": "final-message",
                        "content": [{"type": "text", "text": "done"}]}}),
        event({"type": "task_complete", "turn_id": ROOT_TURN, "completed_at": 2}),
    ])
    return records


class NativeCodexRolloutTests(unittest.TestCase):
    def test_plan_repair_trace_exposes_ephemeral_command_and_dispatch_lifecycle(self):
        message = 'Prompt body\n{"status":"expected_failure","data":{"stdout_json":{"pass":false}}}'
        records = [
            meta(ROOT),
            event({"type": "task_started", "turn_id": ROOT_TURN, "started_at": 1}),
            event({"type": "item_completed", "thread_id": ROOT, "turn_id": ROOT_TURN,
                   "started_at_ms": 1000, "completed_at_ms": 1100, "item": {
                       "type": "CommandExecution", "id": "g3-initial", "status": "failed",
                       "command": ["/bin/zsh", "-c", "python3 -m speckit_pro_runner < request.json"],
                       "stdout": "{}\n", "stderr": "diagnostic\n", "exit_code": 1,
                   }}),
            {"timestamp": "2026-09-15T16:36:43Z", "type": "response_item", "payload": {
                "type": "function_call", "namespace": "collaboration", "name": "spawn_agent",
                "call_id": CALL, "arguments": line({"agent_type": "phase-executor",
                    "message": message, "task_name": "plan_repair"}),
            }},
            event({"type": "item_completed", "thread_id": ROOT, "turn_id": ROOT_TURN,
                   "item": {"type": "SubAgentActivity", "id": CALL, "kind": "started",
                            "agent_thread_id": CHILD, "agent_path": "/root/plan_repair"}}),
            event({"type": "item_completed", "thread_id": ROOT, "turn_id": ROOT_TURN,
                   "item": {"type": "SubAgentActivity", "id": "repair-finished", "kind": "completed",
                            "agent_thread_id": CHILD, "agent_path": "/root/plan_repair"}}),
            delivery_record(author="/root/plan_repair", text="repair complete"),
            event({"type": "item_completed", "thread_id": ROOT, "turn_id": ROOT_TURN,
                   "started_at_ms": 5000, "completed_at_ms": 5100, "item": {
                       "type": "CommandExecution", "id": "g3-rerun", "status": "completed",
                       "command": ["/bin/zsh", "-c", "python3 -m speckit_pro_runner < request.json"],
                       "stdout": "{}\n", "stderr": "", "exit_code": 0,
                   }}),
            event({"type": "task_complete", "turn_id": ROOT_TURN, "completed_at": 6}),
        ]
        result = extract_native_plan_repair_trace(ROOT, raw(records))
        self.assertEqual([item["id"] for item in result["commands"]],
                         ["g3-initial", "g3-rerun"])
        self.assertEqual(result["dispatches"][0]["message"], message)
        self.assertEqual(result["dispatches"][0]["role"], "phase-executor")
        self.assertEqual(result["dispatches"][0]["task_input"]["kind"], "opaque")

        broken = copy.deepcopy(records)
        del broken[2]["payload"]["started_at_ms"]
        with self.assertRaisesRegex(NativeRolloutInvalid, "lifecycle timing"):
            extract_native_plan_repair_trace(ROOT, raw(broken))

    def test_root_only_tree_requires_explicit_opt_in_and_still_captures_actual_children(self):
        with self.assertRaisesRegex(NativeRolloutInvalid, "no trusted nested dispatch"):
            parse_native_tree(ROOT, root_only_tree())

        root_only = parse_native_tree(ROOT, root_only_tree(), allow_root_only=True)
        self.assertEqual(root_only["dispatches"], [])
        self.assertEqual(root_only["children"], [])
        self.assertEqual(set(root_only["raw_sha256"]), {ROOT})

        nested = parse_native_tree(ROOT, fixture_tree(), allow_root_only=True)
        self.assertEqual([item["child_thread_id"] for item in nested["dispatches"]], [CHILD])
        self.assertEqual([item["thread_id"] for item in nested["children"]], [CHILD])

    def test_realistic_nested_rollout_proves_dispatch_ownership_behavior_and_usage(self):
        result = parse_native_tree(ROOT, fixture_tree())
        self.assertEqual(result["schema"], "codex-native-rollout-supplement/v1")
        self.assertEqual(result["scope"], "nested-rollouts-only")
        self.assertFalse(result["root_tool_calls_included"])
        self.assertEqual([call["name"] for call in result["dispatches"]], ["spawn_agent"])
        dispatch = result["dispatches"][0]
        self.assertEqual((dispatch["parent_thread_id"], dispatch["child_thread_id"]), (ROOT, CHILD))
        self.assertEqual(dispatch["role"], "native_canary_worker")
        self.assertEqual(dispatch["role_source"], "function_call")
        self.assertEqual(dispatch["task_input"]["kind"], "opaque")
        self.assertNotIn("Read only fixture", json.dumps(result))
        child = result["children"][0]
        self.assertEqual(child["parent_thread_id"], ROOT)
        self.assertEqual(child["native_metadata"]["model"], "gpt-5.6-sol")
        self.assertEqual(child["usage"]["total_tokens"], 24678)
        self.assertEqual(child["tool_calls"][0]["name"], "command_execution")
        self.assertEqual(child["tool_calls"][0]["output"]["stdout"], "canary-input-v1\n")
        self.assertNotIn("root-command", json.dumps(result))
        self.assertNotIn("wait-call", json.dumps(result))

    def test_dispatch_item_markers_are_opt_in_bounded_opaque_evidence(self):
        messages = (
            "no marker",
            "[[native-eval-item:dispatch-i1]]",
            "[[native-eval-item:dispatch-i1]] then [[native-eval-item:other-item]]",
        )
        for message, expected in zip(messages, ([], ["dispatch-i1"], ["dispatch-i1", "other-item"])):
            with self.subTest(message=message):
                tree = fixture_tree()
                tree[ROOT] = raw(root_records(message=message))
                default = parse_native_tree(ROOT, tree)["dispatches"][0]
                self.assertNotIn("item_attribution", default)
                dispatch = parse_native_tree(
                    ROOT, tree, capture_dispatch_item_markers=True,
                )["dispatches"][0]
                proof = dispatch["item_attribution"]
                self.assertEqual(proof["observed_item_ids"], expected)
                self.assertEqual(proof["observed_marker_count"], len(expected))
                self.assertFalse(proof["markers_truncated"])
                self.assertEqual(proof["task_input"], dispatch["task_input"])
                self.assertNotIn(message, json.dumps(dispatch))

        repeated = " ".join("[[native-eval-item:dispatch-i1]]" for _ in range(65))
        tree = fixture_tree()
        tree[ROOT] = raw(root_records(message=repeated))
        proof = parse_native_tree(
            ROOT, tree, capture_dispatch_item_markers=True,
        )["dispatches"][0]["item_attribution"]
        self.assertEqual(len(proof["observed_item_ids"]), 64)
        self.assertEqual(proof["observed_marker_count"], 65)
        self.assertTrue(proof["markers_truncated"])

    def test_parent_delivery_is_native_bound_opaque_evidence(self):
        records = root_records()
        records.insert(-1, delivery_record(message_id=_MISSING))
        tree = {ROOT: raw(records), CHILD: raw(child_records())}
        dispatch = parse_native_tree(ROOT, tree, require_delivery=True)["dispatches"][0]
        delivery = dispatch["delivery"]
        rendered = "Message Type: FINAL_ANSWER\nPayload:\nCANARY_OK".encode()
        self.assertEqual(dispatch["parent_turn_id"], ROOT_TURN)
        self.assertLess(dispatch["native_event_index"],
                        dispatch["completed_native_event_index"])
        self.assertEqual(dispatch["completed_native_event_id"], "subagent-completed-turn")
        self.assertLess(dispatch["completed_native_event_index"],
                        delivery["native_event_index"])
        self.assertEqual(delivery, {
            "message_id": None,
            "sha256": hashlib.sha256(rendered).hexdigest(),
            "bytes": len(rendered),
            "author": "/root/read_fixture",
            "recipient": "/root",
            "turn_id": ROOT_TURN,
            "native_event_index": len(records) - 2,
        })
        self.assertNotIn("CANARY_OK", json.dumps(dispatch))

    def test_required_parent_delivery_missing_is_incomplete(self):
        with self.assertRaises(NativeRolloutPending):
            parse_native_tree(
                ROOT, {ROOT: raw(root_records())}, require_delivery=True
            )
        with self.assertRaises(NativeRolloutIncomplete):
            parse_native_tree(ROOT, fixture_tree(), require_delivery=True)
        self.assertIsNone(parse_native_tree(ROOT, fixture_tree())["dispatches"][0]["delivery"])

    def test_parent_delivery_ownership_turn_and_content_fail_closed(self):
        for variation in ("author", "recipient", "turn", "missing-metadata", "duplicate",
                          "empty", "ambiguous", "encrypted", "bad-id", "bad-required-flag"):
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                records = root_records()
                delivery = delivery_record()
                if variation == "author":
                    delivery["payload"]["author"] = "/root/wrong"
                elif variation == "recipient":
                    delivery["payload"]["recipient"] = "/root/other"
                elif variation == "turn":
                    delivery["payload"]["internal_chat_message_metadata_passthrough"][
                        "turn_id"] = CHILD_TURN
                elif variation == "missing-metadata":
                    del delivery["payload"]["internal_chat_message_metadata_passthrough"]
                elif variation == "empty":
                    delivery["payload"]["content"][0]["text"] = " "
                elif variation == "ambiguous":
                    delivery["payload"]["content"].append(
                        {"type": "input_text", "text": "second"})
                elif variation == "encrypted":
                    delivery["payload"]["content"] = [
                        {"type": "encrypted_content", "encrypted_content": "opaque"}]
                elif variation == "bad-id":
                    delivery["payload"]["id"] = 7
                elif variation == "bad-required-flag":
                    records.insert(-1, delivery)
                    parse_native_tree(
                        ROOT, {ROOT: raw(records), CHILD: raw(child_records())},
                        require_delivery="yes",
                    )
                    continue
                records.insert(-1, delivery)
                if variation == "duplicate":
                    records.insert(-1, copy.deepcopy(delivery))
                parse_native_tree(
                    ROOT, {ROOT: raw(records), CHILD: raw(child_records())},
                    require_delivery=True,
                )

    def test_distinct_sibling_deliveries_bind_by_native_agent_path(self):
        records = root_records()
        records[-1:-1] = [
            {"timestamp": "2026-09-15T16:36:46Z", "type": "response_item", "payload": {
                "type": "function_call", "namespace": "collaboration", "name": "spawn_agent",
                "call_id": "call_second", "arguments": line({
                    "agent_type": "native_canary_worker", "message": "opaque",
                    "task_name": "second",
                })}},
            event({"type": "item_completed", "thread_id": ROOT, "turn_id": ROOT_TURN,
                "item": {"type": "SubAgentActivity", "id": "call_second", "kind": "started",
                    "agent_thread_id": SECOND_CHILD, "agent_path": "/root/second"}}),
            event({"type": "item_completed", "thread_id": ROOT, "turn_id": ROOT_TURN,
                "item": {"type": "SubAgentActivity", "id": "second-completed",
                    "kind": "completed", "agent_thread_id": SECOND_CHILD,
                    "agent_path": "/root/second"}}),
            delivery_record(message_id="delivery-first"),
            delivery_record(author="/root/second", message_id="delivery-second"),
        ]
        tree = {
            ROOT: raw(records),
            CHILD: raw(child_records()),
            SECOND_CHILD: raw(child_records(
                thread=SECOND_CHILD, path="/root/second", turn=str(uuid.UUID(int=8)))),
        }
        result = parse_native_tree(ROOT, tree, require_delivery=True)
        self.assertEqual(
            [item["delivery"]["author"] for item in result["dispatches"]],
            ["/root/read_fixture", "/root/second"],
        )
        self.assertEqual(
            [item["delivery"]["message_id"] for item in result["dispatches"]],
            ["delivery-first", "delivery-second"],
        )
        duplicate_id = copy.deepcopy(records)
        duplicate_id[-2]["payload"]["id"] = "delivery-first"
        with self.assertRaises(NativeRolloutInvalid):
            parse_native_tree(
                ROOT,
                {ROOT: raw(duplicate_id), CHILD: tree[CHILD], SECOND_CHILD: tree[SECOND_CHILD]},
                require_delivery=True,
            )

    def test_parent_action_before_delivery_is_preserved_as_before_not_consumption(self):
        records = root_records()
        action_index = next(index for index, record in enumerate(records)
                            if record["payload"].get("item", {}).get("id") == "root-command")
        records.insert(-1, delivery_record())
        dispatch = parse_native_tree(
            ROOT, {ROOT: raw(records), CHILD: raw(child_records())}, require_delivery=True,
        )["dispatches"][0]
        self.assertLess(action_index, dispatch["delivery"]["native_event_index"])

    def test_failed_child_tool_is_observed_but_is_not_a_success(self):
        tree = fixture_tree()
        tree[CHILD] = raw(child_records(status="failed", exit_code=7))
        call = parse_native_tree(ROOT, tree)["children"][0]["tool_calls"][0]
        self.assertFalse(call["success"])
        self.assertEqual(call["output"]["exit_code"], 7)

    def test_wait_and_prose_without_native_activity_are_not_dispatch_evidence(self):
        records = root_records()
        records = [record for record in records
                   if not (record["type"] == "response_item")
                   and not (record["type"] == "event_msg"
                            and record["payload"].get("item", {}).get("type") == "SubAgentActivity")]
        with self.assertRaises(NativeRolloutInvalid):
            parse_native_tree(ROOT, {ROOT: raw(records)})

    def test_message_is_always_opaque_including_ciphertext_shaped_input(self):
        for message in ("plaintext fixture request", {"ciphertext": "sealed-value", "version": 1}):
            with self.subTest(kind=type(message).__name__):
                tree = fixture_tree()
                tree[ROOT] = raw(root_records(message=message))
                task = parse_native_tree(ROOT, tree)["dispatches"][0]["task_input"]
                self.assertEqual(set(task), {"kind", "sha256", "bytes"})
                self.assertNotIn("fixture request", json.dumps(task))
                self.assertNotIn("sealed-value", json.dumps(task))

    def test_role_falls_back_only_to_bound_native_session_metadata(self):
        tree = fixture_tree()
        records = root_records()
        arguments = json.loads(records[2]["payload"]["arguments"])
        del arguments["agent_type"]
        records[2]["payload"]["arguments"] = line(arguments)
        tree[ROOT] = raw(records)
        dispatch = parse_native_tree(ROOT, tree)["dispatches"][0]
        self.assertEqual((dispatch["role"], dispatch["role_source"]),
                         ("native_canary_worker", "session_meta"))

    def test_missing_rollout_is_pending_but_unreferenced_raw_is_invalid(self):
        with self.assertRaises(NativeRolloutPending):
            parse_native_tree(ROOT, {ROOT: raw(root_records())})
        tree = fixture_tree()
        tree[GRANDCHILD] = raw(child_records(thread=GRANDCHILD))
        with self.assertRaises(NativeRolloutInvalid):
            parse_native_tree(ROOT, tree)

    def test_parent_cwd_depth_and_path_binding_are_exact(self):
        changes = {
            "parent": {"parent": GRANDCHILD},
            "cwd": {"cwd": "/private/tmp/other-case/workspace"},
            "depth": {"depth": 2},
            "path": {"path": "/root/other"},
        }
        for label, kwargs in changes.items():
            with self.subTest(label=label), self.assertRaises(NativeRolloutInvalid):
                tree = fixture_tree()
                tree[CHILD] = raw(child_records(**kwargs))
                parse_native_tree(ROOT, tree)

    def test_activity_and_spawn_call_must_join_without_duplicates(self):
        for variation in ("wrong-call", "not-spawn", "duplicate-call", "duplicate-start", "missing-complete"):
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                records = root_records()
                if variation == "wrong-call":
                    records[2]["payload"]["call_id"] = "other-call"
                elif variation == "not-spawn":
                    records[2]["payload"]["name"] = "wait_agent"
                elif variation == "duplicate-call":
                    records.insert(3, copy.deepcopy(records[2]))
                elif variation == "duplicate-start":
                    records.insert(4, copy.deepcopy(records[3]))
                else:
                    del records[-2]
                parse_native_tree(ROOT, {ROOT: raw(records), CHILD: raw(child_records())})

    def test_malformed_truncated_failed_or_unterminated_child_fails_closed(self):
        for variation in ("duplicate-key", "truncated", "no-final-newline", "error",
                          "missing-terminal", "duplicate-terminal"):
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                tree = fixture_tree()
                records = child_records()
                if variation == "duplicate-key":
                    tree[CHILD] = tree[CHILD].replace(b'"type":"session_meta"',
                        b'"type":"session_meta","type":"session_meta"', 1)
                elif variation == "truncated":
                    tree[CHILD] = tree[CHILD][:-5]
                elif variation == "no-final-newline":
                    tree[CHILD] = tree[CHILD][:-1]
                elif variation == "error":
                    records.insert(-1, event({"type": "error", "thread_id": CHILD,
                        "turn_id": CHILD_TURN, "message": "child failed"}))
                    tree[CHILD] = raw(records)
                elif variation == "missing-terminal":
                    tree[CHILD] = raw(records[:-1])
                else:
                    tree[CHILD] = raw(records + [copy.deepcopy(records[-1])])
                parse_native_tree(ROOT, tree)

    def test_session_parent_fields_are_independent_ownership_checks(self):
        for field, value in (("session_id", GRANDCHILD), ("thread_source", "user")):
            with self.subTest(field=field), self.assertRaises(NativeRolloutInvalid):
                tree = fixture_tree()
                records = child_records()
                records[0]["payload"][field] = value
                tree[CHILD] = raw(records)
                parse_native_tree(ROOT, tree)

    def test_rollout_event_byte_and_child_bounds_fail_closed(self):
        cases = (
            ("events", "MAX_EVENTS_PER_ROLLOUT", 1),
            ("bytes", "MAX_ROLLOUT_BYTES", 8),
            ("children", "MAX_CHILDREN", 0),
        )
        for label, field, limit in cases:
            with self.subTest(label=label), mock.patch.object(rollouts, field, limit), \
                    self.assertRaises(NativeRolloutInvalid):
                parse_native_tree(ROOT, fixture_tree())

    def test_duplicate_item_identity_and_invalid_usage_fail_closed(self):
        for variation in ("duplicate-item", "boolean-usage", "negative-usage"):
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                tree = fixture_tree()
                records = child_records()
                if variation == "duplicate-item":
                    records.insert(7, copy.deepcopy(records[6]))
                else:
                    records[7]["payload"]["thread_token_usage"]["input_tokens"] = (
                        True if variation == "boolean-usage" else -1)
                tree[CHILD] = raw(records)
                parse_native_tree(ROOT, tree)

    def test_spawn_argument_duplicate_keys_fail_closed(self):
        records = root_records()
        records[2]["payload"]["arguments"] = (
            '{"agent_type":"first","agent_type":"native_canary_worker",'
            '"message":"opaque","task_name":"read_fixture"}'
        )
        with self.assertRaises(NativeRolloutInvalid):
            parse_native_tree(ROOT, {ROOT: raw(records), CHILD: raw(child_records())})

    def test_recursive_native_child_is_owned_by_its_actual_parent(self):
        child = child_records()
        child.insert(-1, {"timestamp": "2026-09-15T16:36:49Z", "type": "response_item", "payload": {
            "type": "function_call", "namespace": "collaboration", "name": "spawn_agent",
            "call_id": "call_grandchild", "arguments": line({"agent_type": "native_canary_worker",
                "message": "opaque", "task_name": "grandchild"})}})
        child.insert(-1, event({"type": "item_completed", "thread_id": CHILD,
            "turn_id": CHILD_TURN, "item": {"type": "SubAgentActivity", "id": "call_grandchild",
                "kind": "started", "agent_thread_id": GRANDCHILD,
                "agent_path": "/root/read_fixture/grandchild"}}))
        child.insert(-1, event({"type": "item_completed", "thread_id": CHILD,
            "turn_id": CHILD_TURN, "item": {"type": "SubAgentActivity", "id": "done-grandchild",
                "kind": "completed", "agent_thread_id": GRANDCHILD,
                "agent_path": "/root/read_fixture/grandchild"}}))
        grandchild = child_records(thread=GRANDCHILD, parent=CHILD, depth=2,
            path="/root/read_fixture/grandchild", turn=str(uuid.UUID(int=6)))
        tree = {ROOT: raw(root_records()), CHILD: raw(child), GRANDCHILD: raw(grandchild)}
        result = parse_native_tree(ROOT, tree)
        self.assertEqual([item["parent_thread_id"] for item in result["dispatches"]], [ROOT, CHILD])
        self.assertEqual([item["depth"] for item in result["children"]], [1, 2])

    def test_cycle_and_child_limit_fail_closed(self):
        child = child_records()
        child.insert(-1, {"timestamp": "2026-09-15T16:36:49Z", "type": "response_item", "payload": {
            "type": "function_call", "namespace": "collaboration", "name": "spawn_agent",
            "call_id": "cycle", "arguments": line({"message": "opaque"})}})
        child.insert(-1, event({"type": "item_completed", "thread_id": CHILD,
            "turn_id": CHILD_TURN, "item": {"type": "SubAgentActivity", "id": "cycle",
                "kind": "started", "agent_thread_id": ROOT, "agent_path": "/root"}}))
        child.insert(-1, event({"type": "item_completed", "thread_id": CHILD,
            "turn_id": CHILD_TURN, "item": {"type": "SubAgentActivity", "id": "cycle-done",
                "kind": "completed", "agent_thread_id": ROOT, "agent_path": "/root"}}))
        with self.assertRaises(NativeRolloutInvalid):
            parse_native_tree(ROOT, {ROOT: raw(root_records()), CHILD: raw(child)})

    def test_exact_native_skill_injection_accepts_missing_message_id_and_large_project_body(self):
        result = parse_native_skill_injections(
            ROOT, raw(skill_records()), expected_cwd=CWD, expected_prompt=PROMPT,
            skill_witnesses=skill_witnesses(),
        )
        self.assertEqual(result["schema"], "codex-native-skill-injection/v1")
        self.assertEqual(result["status"], "qualified")
        self.assertEqual(result["activations"], ["alpha"])
        self.assertEqual(result["turn_id"], ROOT_TURN)
        self.assertEqual(result["scope"], "root-selected-skill-instructions")
        self.assertEqual(result["cwd"], CWD)
        self.assertEqual(result["injections"][0]["source_bytes"], len(ALPHA_BODY.encode()))
        self.assertGreater(result["injections"][0]["source_bytes"], 8_000)
        self.assertNotIn("message_id", result["injections"][0])
        self.assertNotIn(ALPHA_BODY, json.dumps(result))

    def test_plugin_qualified_native_skill_injection_keeps_canonical_activation_key(self):
        result = parse_native_skill_injections(
            ROOT, raw(skill_records(plugin_name="mini-plugin")),
            expected_cwd=CWD, expected_prompt=PROMPT,
            skill_witnesses=skill_witnesses(), plugin_name="mini-plugin",
        )
        self.assertEqual(result["activations"], ["alpha"])
        self.assertEqual(result["injections"][0]["skill"], "alpha")

    def test_plugin_name_is_exact_and_canonical_without_namespace_fallback(self):
        cases = {
            "qualified-without-controller-name": (
                skill_records(plugin_name="mini-plugin"), None),
            "unqualified-with-controller-name": (skill_records(), "mini-plugin"),
            "wrong-qualified-name": (
                skill_records(plugin_name="other-plugin"), "mini-plugin"),
        }
        for label, (records, plugin_name) in cases.items():
            with self.subTest(label=label), self.assertRaises(NativeRolloutInvalid):
                parse_native_skill_injections(
                    ROOT, raw(records), expected_cwd=CWD, expected_prompt=PROMPT,
                    skill_witnesses=skill_witnesses(), plugin_name=plugin_name,
                )
        for plugin_name in ("", "Mini-Plugin", "mini_plugin", "mini:plugin", 7):
            with self.subTest(plugin_name=plugin_name), self.assertRaises(NativeRolloutInvalid):
                parse_native_skill_injections(
                    ROOT, raw(skill_records()), expected_cwd=CWD,
                    expected_prompt=PROMPT, skill_witnesses=skill_witnesses(),
                    plugin_name=plugin_name,
                )

    def test_no_injection_and_one_wrong_sibling_are_valid_behavioral_observations(self):
        none = parse_native_skill_injections(
            ROOT, raw(skill_records(include_injection=False)), expected_cwd=CWD,
            expected_prompt=PROMPT, skill_witnesses=skill_witnesses(),
        )
        wrong = parse_native_skill_injections(
            ROOT, raw(skill_records(selected="beta", message_id="selected-beta")),
            expected_cwd=CWD, expected_prompt=PROMPT, skill_witnesses=skill_witnesses(),
        )
        self.assertEqual((none["status"], none["activations"]), ("not_observed", []))
        self.assertEqual((wrong["status"], wrong["activations"]), ("qualified", ["beta"]))
        self.assertEqual(wrong["injections"][0]["message_id"], "selected-beta")

    def test_multiple_known_siblings_are_preserved_in_rollout_order(self):
        records = skill_records(selected="beta", message_id="selected-beta")
        records.insert(4, user_message(
            selected_skill_text("gamma"), kind="skills.selected_skill_instructions",
            message_id="selected-gamma",
        ))
        result = parse_native_skill_injections(
            ROOT, raw(records), expected_cwd=CWD, expected_prompt=PROMPT,
            skill_witnesses=skill_witnesses(),
        )
        self.assertEqual(result["activations"], ["beta", "gamma"])
        self.assertEqual([item["record_index"] for item in result["injections"]], [3, 4])

    def test_expected_and_extra_activation_are_both_preserved_for_shared_grading(self):
        records = skill_records(selected="alpha", message_id="selected-alpha")
        records.insert(4, user_message(
            selected_skill_text("beta"), kind="skills.selected_skill_instructions",
            message_id="selected-beta",
        ))
        result = parse_native_skill_injections(
            ROOT, raw(records), expected_cwd=CWD, expected_prompt=PROMPT,
            skill_witnesses=skill_witnesses(),
        )
        self.assertEqual(result["activations"], ["alpha", "beta"])

    def test_duplicate_activation_or_present_message_identity_is_invalid(self):
        cases = {}
        repeated_skill = skill_records(selected="alpha", message_id="selected-alpha-one")
        repeated_skill.insert(4, user_message(
            selected_skill_text("alpha"), kind="skills.selected_skill_instructions",
            message_id="selected-alpha-two",
        ))
        cases["activation"] = repeated_skill
        repeated_identity = skill_records(selected="alpha", message_id="same-message")
        repeated_identity.insert(4, user_message(
            selected_skill_text("beta"), kind="skills.selected_skill_instructions",
            message_id="same-message",
        ))
        cases["message-identity"] = repeated_identity
        for label, records in cases.items():
            with self.subTest(label=label), self.assertRaises(NativeRolloutInvalid):
                parse_native_skill_injections(
                    ROOT, raw(records), expected_cwd=CWD, expected_prompt=PROMPT,
                    skill_witnesses=skill_witnesses(),
                )

    def test_stale_or_inherited_skill_injection_cannot_satisfy_current_turn(self):
        records = skill_records(include_injection=False)
        records.insert(1, user_message(
            selected_skill_text("alpha"), turn=CHILD_TURN,
            kind="skills.selected_skill_instructions", message_id="inherited-selection",
        ))
        result = parse_native_skill_injections(
            ROOT, raw(records), expected_cwd=CWD, expected_prompt=PROMPT,
            skill_witnesses=skill_witnesses(),
        )
        self.assertEqual(result["activations"], [])
        self.assertEqual(result["status"], "not_observed")

    def test_skill_injection_classification_and_content_fail_closed(self):
        for variation in ("extra-kind", "missing-metadata", "wrong-role", "extra-content",
                          "bad-message-id", "truncated-body", "wrong-path", "unknown-skill",
                          "duplicate"):
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                records = skill_records()
                injection = records[3]
                payload = injection["payload"]
                metadata = payload["internal_chat_message_metadata_passthrough"]
                if variation == "extra-kind":
                    metadata["content_item_kinds"].append("user.text")
                elif variation == "missing-metadata":
                    del payload["internal_chat_message_metadata_passthrough"]
                elif variation == "wrong-role":
                    payload["role"] = "assistant"
                elif variation == "extra-content":
                    payload["content"].append({"type": "input_text", "text": "duplicate"})
                elif variation == "bad-message-id":
                    payload["id"] = 7
                elif variation == "truncated-body":
                    payload["content"][0]["text"] = payload["content"][0]["text"][:-9]
                elif variation == "wrong-path":
                    payload["content"][0]["text"] = payload["content"][0]["text"].replace(
                        "/.agents/skills/alpha/SKILL.md", "/.agents/skills/beta/SKILL.md", 1)
                elif variation == "unknown-skill":
                    payload["content"][0]["text"] = payload["content"][0]["text"].replace(
                        "<name>alpha</name>", "<name>gamma</name>", 1)
                else:
                    records.insert(4, copy.deepcopy(injection))
                parse_native_skill_injections(
                    ROOT, raw(records), expected_cwd=CWD, expected_prompt=PROMPT,
                    skill_witnesses=skill_witnesses(),
                )

    def test_root_source_cwd_prompt_turn_and_terminal_bindings_fail_closed(self):
        for variation in ("source", "session-id", "thread-source", "session-cwd",
                          "requested-cwd", "prompt",
                          "prompt-class", "prompt-turn", "duplicate-prompt",
                          "injection-after-terminal", "native-error", "missing-terminal"):
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                records = skill_records()
                expected_cwd = CWD
                expected_prompt = PROMPT
                if variation == "source":
                    records[0]["payload"]["source"] = "api"
                elif variation == "session-id":
                    records[0]["payload"]["session_id"] = CHILD
                elif variation == "thread-source":
                    records[0]["payload"]["thread_source"] = "subagent"
                elif variation == "session-cwd":
                    records[0]["payload"]["cwd"] = "/private/tmp/other/workspace"
                elif variation == "requested-cwd":
                    expected_cwd = "/private/tmp/other/workspace"
                elif variation == "prompt":
                    expected_prompt = "Use $alpha for a different task."
                elif variation == "prompt-class":
                    records[2]["payload"]["internal_chat_message_metadata_passthrough"][
                        "content_item_kinds"] = ["skills.selected_skill_instructions"]
                elif variation == "prompt-turn":
                    records[2]["payload"]["internal_chat_message_metadata_passthrough"][
                        "turn_id"] = CHILD_TURN
                elif variation == "duplicate-prompt":
                    records.insert(3, copy.deepcopy(records[2]))
                elif variation == "injection-after-terminal":
                    injection = records.pop(3)
                    records.append(injection)
                elif variation == "native-error":
                    records.insert(-1, event({"type": "turn_failed", "thread_id": ROOT,
                        "turn_id": ROOT_TURN, "message": "synthetic failure"}))
                else:
                    records.pop()
                parse_native_skill_injections(
                    ROOT, raw(records), expected_cwd=expected_cwd,
                    expected_prompt=expected_prompt, skill_witnesses=skill_witnesses(),
                )

    def test_skill_witness_schema_and_complete_bytes_are_strict(self):
        for variation in ("empty", "bad-path", "bad-bytes", "bad-hash", "extra-field"):
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                witnesses = skill_witnesses()
                if variation == "empty":
                    witnesses = {}
                elif variation == "bad-path":
                    witnesses["alpha"]["path"] = ".agents/skills/beta/SKILL.md"
                elif variation == "bad-bytes":
                    witnesses["alpha"]["bytes"] += 1
                elif variation == "bad-hash":
                    witnesses["alpha"]["sha256"] = "0" * 64
                else:
                    witnesses["alpha"]["source"] = "synthetic"
                parse_native_skill_injections(
                    ROOT, raw(skill_records()), expected_cwd=CWD, expected_prompt=PROMPT,
                    skill_witnesses=witnesses,
                )

    def test_collect_skill_injection_copies_exact_root_bytes_and_hash_refs(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            sessions = base / "sessions" / "2026" / "09" / "15"
            sessions.mkdir(parents=True)
            content = raw(skill_records())
            source = sessions / f"rollout-2026-09-15T11-36-42-{ROOT}.jsonl"
            source.write_bytes(content)
            destination = base / "attempt" / "native-skill"
            result = collect_native_skill_injections(
                ROOT, base / "sessions", destination, expected_cwd=CWD,
                expected_prompt=PROMPT, skill_witnesses=skill_witnesses(),
            )
            self.assertEqual(result["schema"], "codex-native-skill-injection-collection/v1")
            self.assertEqual(set(result["evidence"]), {ROOT})
            ref = result["evidence"][ROOT]
            self.assertEqual((destination / ref["path"]).read_bytes(), content)
            self.assertEqual(ref["sha256"], hashlib.sha256(content).hexdigest())
            self.assertEqual(result["supplement"]["activations"], ["alpha"])
            self.assertEqual(json.loads((destination / "supplement.json").read_text()),
                             result["supplement"])

    def test_collect_skill_injection_passes_exact_controller_plugin_name(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            sessions = base / "sessions"
            sessions.mkdir()
            content = raw(skill_records(plugin_name="mini-plugin"))
            source = sessions / f"rollout-2026-09-15T11-36-42-{ROOT}.jsonl"
            source.write_bytes(content)
            result = collect_native_skill_injections(
                ROOT, sessions, base / "attempt" / "native-skill",
                expected_cwd=CWD, expected_prompt=PROMPT,
                skill_witnesses=skill_witnesses(), plugin_name="mini-plugin",
            )
            self.assertEqual(result["supplement"]["activations"], ["alpha"])

    def test_collect_skill_injection_rejects_ambiguous_sources_and_destinations(self):
        for variation in ("duplicate-root", "symlink-root", "existing-destination",
                          "symlink-destination"):
            with self.subTest(variation=variation), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                sessions = base / "sessions"
                sessions.mkdir()
                filename = f"rollout-2026-09-15T11-36-42-{ROOT}.jsonl"
                source = sessions / filename
                source.write_bytes(raw(skill_records()))
                destination = base / "attempt" / "native-skill"
                if variation == "duplicate-root":
                    duplicate_dir = sessions / "2026"
                    duplicate_dir.mkdir()
                    (duplicate_dir / filename).write_bytes(raw(skill_records()))
                elif variation == "symlink-root":
                    target = sessions / "rollout-source.jsonl"
                    source.replace(target)
                    source.symlink_to(target)
                elif variation == "existing-destination":
                    destination.mkdir(parents=True)
                else:
                    target = base / "existing-native-skill"
                    target.mkdir()
                    destination.parent.mkdir()
                    destination.symlink_to(target)
                with self.assertRaises(NativeRolloutInvalid):
                    collect_native_skill_injections(
                        ROOT, sessions, destination, expected_cwd=CWD,
                        expected_prompt=PROMPT, skill_witnesses=skill_witnesses(),
                    )

    def test_collect_copies_exact_bytes_and_returns_hash_refs(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            sessions = base / "sessions" / "2026" / "09" / "15"
            sessions.mkdir(parents=True)
            tree = fixture_tree()
            for index, (thread_id, content) in enumerate(tree.items()):
                (sessions / f"rollout-2026-09-15T11-36-4{index}-{thread_id}.jsonl").write_bytes(content)
            (sessions / "rollout-2026-09-15T11-00-00-unrelated.jsonl").write_text("not json")
            result = collect_native_tree(ROOT, base / "sessions", base / "attempt" / "native")
            self.assertEqual(set(result["evidence"]), {ROOT, CHILD})
            for thread_id, content in tree.items():
                ref = result["evidence"][thread_id]
                copied = base / "attempt" / "native" / ref["path"]
                self.assertEqual(copied.read_bytes(), content)
                self.assertEqual(ref["sha256"], hashlib.sha256(content).hexdigest())
                self.assertEqual(ref["bytes"], len(content))
            self.assertTrue((base / "attempt" / "native" / "supplement.json").is_file())

    def test_collect_can_require_and_publish_bound_parent_delivery(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            sessions = base / "sessions"
            sessions.mkdir()
            records = root_records()
            records.insert(-1, delivery_record())
            tree = {ROOT: raw(records), CHILD: raw(child_records())}
            for thread_id, content in tree.items():
                (sessions / f"rollout-2026-09-15T11-36-42-{thread_id}.jsonl").write_bytes(content)
            result = collect_native_tree(
                ROOT, sessions, base / "attempt", require_delivery=True
            )
            delivery = result["supplement"]["dispatches"][0]["delivery"]
            self.assertEqual((delivery["author"], delivery["recipient"]),
                             ("/root/read_fixture", "/root"))

    def test_collect_required_delivery_fails_before_publishing_incomplete_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            sessions = base / "sessions"
            sessions.mkdir()
            for thread_id, content in fixture_tree().items():
                (sessions / f"rollout-2026-09-15T11-36-42-{thread_id}.jsonl").write_bytes(content)
            destination = base / "attempt"
            with self.assertRaises(NativeRolloutIncomplete):
                collect_native_tree(ROOT, sessions, destination, require_delivery=True)
            self.assertFalse(destination.exists())

    def test_collect_missing_duplicate_symlink_and_existing_destination_fail_closed(self):
        for variation in ("missing", "duplicate", "symlink", "destination"):
            with self.subTest(variation=variation), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                sessions = base / "sessions"
                sessions.mkdir()
                root_path = sessions / f"rollout-2026-09-15T11-36-42-{ROOT}.jsonl"
                root_path.write_bytes(raw(root_records()))
                child_path = sessions / f"rollout-2026-09-15T11-36-47-{CHILD}.jsonl"
                if variation != "missing":
                    child_path.write_bytes(raw(child_records()))
                if variation == "duplicate":
                    duplicate_dir = sessions / "2026"
                    duplicate_dir.mkdir()
                    (duplicate_dir / child_path.name).write_bytes(raw(child_records()))
                elif variation == "symlink":
                    child_path.unlink()
                    child_path.symlink_to(root_path)
                destination = base / "native"
                if variation == "destination":
                    destination.mkdir()
                error = NativeRolloutPending if variation == "missing" else NativeRolloutInvalid
                with self.assertRaises(error):
                    collect_native_tree(ROOT, sessions, destination)


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeCodexRolloutTests),
        label="test-native-eval-codex-rollouts",
    ))
