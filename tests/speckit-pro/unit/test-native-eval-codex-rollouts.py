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
INTERRUPT_CALL = "call_native_interrupt"
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
            "started_at_ms": 1000, "completed_at_ms": 1100,
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


def followup_root_records():
    records = root_records()
    followup_call = "call_followup_child"
    records[-1:-1] = [
        delivery_record(text="Message Type: FINAL_ANSWER\nPayload:\nFIRST",
                        message_id="delivery-first"),
        {"timestamp": "2026-09-15T16:36:50Z", "type": "response_item", "payload": {
            "type": "function_call", "namespace": "collaboration",
            "name": "followup_task", "call_id": followup_call,
            "arguments": line({"target": "/root/read_fixture", "message": "Check again"}),
            "internal_chat_message_metadata_passthrough": {"turn_id": ROOT_TURN},
        }},
        event({"type": "item_completed", "thread_id": ROOT, "turn_id": ROOT_TURN,
               "item": {"type": "SubAgentActivity", "id": followup_call,
                        "kind": "interacted", "agent_thread_id": CHILD,
                        "agent_path": "/root/read_fixture"}}),
        {"timestamp": "2026-09-15T16:36:51Z", "type": "response_item", "payload": {
            "type": "function_call_output", "call_id": followup_call, "output": "",
            "internal_chat_message_metadata_passthrough": {"turn_id": ROOT_TURN},
        }},
        event({"type": "item_completed", "thread_id": ROOT, "turn_id": ROOT_TURN,
               "item": {"type": "SubAgentActivity", "id": "subagent-completed-followup",
                        "kind": "completed", "agent_thread_id": CHILD,
                        "agent_path": "/root/read_fixture"}}),
        delivery_record(text="Message Type: FINAL_ANSWER\nPayload:\nSECOND",
                        message_id="delivery-second"),
    ]
    return records


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


def progress_delivery_record(*, author="/root/read_fixture", recipient="/root",
                             turn=ROOT_TURN, message_id="progress-1",
                             ciphertext="opaque-native-progress"):
    return {
        "timestamp": "2026-09-15T16:36:48Z",
        "type": "response_item",
        "payload": {
            "type": "agent_message",
            "author": author,
            "recipient": recipient,
            "id": message_id,
            "content": [
                {"type": "input_text", "text": (
                    f"Message Type: MESSAGE\nTask name: {recipient}\n"
                    f"Sender: {author}\nPayload:\n"
                )},
                {"type": "encrypted_content", "encrypted_content": ciphertext},
            ],
            "internal_chat_message_metadata_passthrough": {
                "turn_id": turn,
                "create_time": 1_789_490_213.196796,
            },
        },
    }


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


def followup_child_records():
    records = child_records()
    followup_turn = str(uuid.UUID(int=15))
    records.extend([
        event({"type": "task_started", "turn_id": followup_turn, "started_at": 5}),
        {"timestamp": "2026-09-15T16:36:50Z", "type": "turn_context", "payload": {
            "turn_id": followup_turn, "root_turn_id": ROOT_TURN,
            "cwd": CWD, "model": "gpt-5.6-sol",
        }},
        event({"type": "item_completed", "thread_id": CHILD, "turn_id": followup_turn,
               "item": {"type": "AgentMessage", "id": "followup-message",
                        "content": [{"type": "text", "text": "followup complete"}]}}),
        event({"type": "task_complete", "turn_id": followup_turn, "completed_at": 6}),
    ])
    return records


def collaboration_exchange(*, name, call_id, arguments, actor_thread, actor_turn,
                           counterpart_thread, target, activity_kind, output,
                           timestamps):
    return [
        {"timestamp": timestamps[0], "type": "response_item", "payload": {
            "type": "function_call", "namespace": "collaboration", "name": name,
            "call_id": call_id, "arguments": line(arguments),
            "internal_chat_message_metadata_passthrough": {"turn_id": actor_turn},
        }},
        event({"type": "item_completed", "thread_id": actor_thread,
               "turn_id": actor_turn,
               "item": {"type": "SubAgentActivity", "id": call_id,
                        "kind": activity_kind,
                        "agent_thread_id": counterpart_thread,
                        "agent_path": target}}),
        {"timestamp": timestamps[1], "type": "response_item", "payload": {
            "type": "function_call_output", "call_id": call_id,
            "output": output,
            "internal_chat_message_metadata_passthrough": {"turn_id": actor_turn},
        }},
    ]


def interrupted_root_records():
    records = root_records()
    records = [
        record for record in records
        if record.get("payload", {}).get("item", {}).get("kind") != "completed"
    ]
    records[-1:-1] = collaboration_exchange(
        name="interrupt_agent", call_id=INTERRUPT_CALL,
        arguments={"target": "read_fixture"}, actor_thread=ROOT,
        actor_turn=ROOT_TURN, counterpart_thread=CHILD,
        target="/root/read_fixture", activity_kind="interrupted",
        output=line({"previous_status": "running"}),
        timestamps=("2026-09-15T16:36:47Z", "2026-09-15T16:36:48Z"),
    )
    return records


def interrupted_child_records(*, post_terminal=False):
    records = [
        record for record in child_records()
        if record.get("payload", {}).get("item", {}).get("type") != "AgentMessage"
    ]
    records.insert(-1, event({
        "type": "item_completed", "thread_id": CHILD, "turn_id": CHILD_TURN,
        "item": {"type": "AgentMessage", "id": "commentary",
            "phase": "commentary", "content": [{"type": "Text", "text": "progress"}]},
    }))
    records[-1] = event({
        "type": "turn_aborted", "turn_id": CHILD_TURN, "reason": "interrupted",
        "started_at": 3, "completed_at": 4, "duration_ms": 1_000,
    })
    return with_post_terminal_command(records) if post_terminal else records


def with_interim_send(records, *, child=CHILD, parent=ROOT, turn=CHILD_TURN,
                      target="/root", ciphertext="opaque-native-progress",
                      call_id="call_interim_message"):
    records = copy.deepcopy(records)
    records[-2:-2] = collaboration_exchange(
        name="send_message", call_id=call_id,
        arguments={"target": target, "message": ciphertext}, actor_thread=child,
        actor_turn=turn, counterpart_thread=parent, target=target,
        activity_kind="interacted", output="",
        timestamps=("2026-09-15T16:36:48Z", "2026-09-15T16:36:49Z"),
    )
    return records


def with_post_terminal_command(records, *, thread=CHILD, turn=CHILD_TURN):
    return with_post_terminal_commands(
        records, thread=thread, turn=turn,
        commands=("ripwire . --quality-delta",),
    )


def with_session_backed_post_terminal_command(records, *, thread=CHILD,
                                              turn=CHILD_TURN):
    records = with_post_terminal_command(records, thread=thread, turn=turn)
    terminal_index = next(
        index for index, record in enumerate(records)
        if record.get("payload", {}).get("type") in {"task_complete", "turn_aborted"}
    )
    invocation = records[terminal_index - 2]["payload"]
    response = records[terminal_index - 1]["payload"]
    completion = records[terminal_index + 1]["payload"]["item"]
    session_id = int(completion["process_id"])
    invocation["input"] = invocation["input"].replace(
        "text(r.output);", "text(JSON.stringify(r));",
    )
    response["output"] = [
        {"type": "input_text", "text": "Script completed\nWall time 30.0 seconds\nOutput:\n"},
        {"type": "input_text", "text": line({
            "chunk_id": "bound-session", "wall_time_seconds": 30.0,
            "session_id": session_id, "original_token_count": 1,
            "output": "still running\n",
        })},
    ]
    poll_call = "call_post_terminal_poll"
    records[terminal_index:terminal_index] = [
        {
            "timestamp": "2026-09-15T16:36:47Z",
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call", "id": "ctc_post_terminal_poll",
                "status": "completed", "call_id": poll_call, "name": "exec",
                "input": (
                    "const r = await tools.write_stdin("
                    f"{{session_id:{session_id},chars:\"\",yield_time_ms:30000,"
                    "max_output_tokens:6000}); text(JSON.stringify(r));\n"
                ),
                "internal_chat_message_metadata_passthrough": {"turn_id": turn},
            },
        },
        {
            "timestamp": "2026-09-15T16:36:48Z",
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call_output", "id": "ctco_post_terminal_poll",
                "call_id": poll_call, "output": "aborted by user after 27.2s",
                "internal_chat_message_metadata_passthrough": {"turn_id": turn},
            },
        },
    ]
    return records


def with_post_terminal_commands(
    records, *, thread=CHILD, turn=CHILD_TURN,
    commands=("ripwire . --quality-delta", "ripwire . --test-gate"),
    native_syntax=False,
):
    records = copy.deepcopy(records)
    terminal_ms = records[-1]["payload"]["completed_at"] * 1000
    invocations = []
    completions = []
    for index, command in enumerate(commands):
        suffix = f"{index + 8:012x}"
        item_id = "exec-" + "-".join(("0" * 8, "0" * 4, "0" * 4, "0" * 4, suffix))
        request = {
            "cmd": command,
            "workdir": CWD,
            "yield_time_ms": 10_000,
            "max_output_tokens": 12_000,
        }
        call_id = f"call_post_terminal_command_{index}"
        encoded_request = (
            "{\n"
            f"  cmd: {line(command)},\n"
            f"  workdir: {line(CWD)},\n"
            "  yield_time_ms: 10000,\n"
            "  max_output_tokens: 12000\n"
            "}"
            if native_syntax else line(request)
        )
        invocation = {
            "timestamp": "2026-09-15T16:36:43Z",
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call",
                "id": f"ctc_post_terminal_command_{index}",
                "status": "completed",
                "call_id": call_id,
                "name": "exec",
                "input": (f"const r = await tools.exec_command({encoded_request});\n"
                          "text(r.output);"),
                "internal_chat_message_metadata_passthrough": {
                    "turn_id": turn,
                    "create_time": 1_789_850_290.426259 + index,
                },
            },
        }
        response = {
            "timestamp": "2026-09-15T16:36:44Z",
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call_output",
                "id": f"ctco_post_terminal_command_{index}",
                "call_id": call_id,
                "output": [{"type": "input_text", "text": ""}],
                "internal_chat_message_metadata_passthrough": {
                    "turn_id": turn,
                    "create_time": 1_789_850_307.142412 + index,
                },
            },
        }
        invocations.extend((invocation, response))
        completions.append({
            "timestamp": "2026-09-15T16:36:49Z",
            "ordinal": 98 + index,
            "type": "event_msg",
            "payload": {
                "type": "item_completed",
                "thread_id": thread,
                "turn_id": turn,
                "item": {
                    "type": "CommandExecution",
                    "id": item_id,
                    "process_id": str(93_111 + index),
                    "command": ["/bin/zsh", "-c", command],
                    "cwd": f"file://{CWD}",
                    "parsed_cmd": [{"type": "unknown", "cmd": command}],
                    "source": "unified_exec_startup",
                    "status": "completed",
                    "stdout": "quality clean\n",
                    "stderr": "",
                    "aggregated_output": "quality clean\n",
                    "formatted_output": "quality clean\n",
                    "exit_code": 0,
                },
                "started_at_ms": terminal_ms - 500 - index,
                "completed_at_ms": terminal_ms + 1_000 + index,
            },
        })
    records[-1:-1] = invocations
    records[-1]["ordinal"] = 97
    records.extend(completions)
    return records


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
    def test_completed_child_can_run_one_bound_native_followup_turn(self):
        result = parse_native_tree(
            ROOT,
            {ROOT: raw(followup_root_records()), CHILD: raw(followup_child_records())},
            require_delivery=True,
        )
        dispatch = result["dispatches"][0]

        self.assertEqual(dispatch["status"], "completed")
        self.assertEqual(dispatch["completed_native_event_id"],
                         "subagent-completed-followup")
        self.assertEqual(len(dispatch["followup_turns"]), 1)
        self.assertEqual(dispatch["followup_turns"][0]["call_id"],
                         "call_followup_child")
        self.assertEqual(dispatch["delivery"]["text"],
                         "Message Type: FINAL_ANSWER\nPayload:\nFIRST")
        self.assertEqual(dispatch["followup_turns"][0]["delivery"]["text"],
                         "Message Type: FINAL_ANSWER\nPayload:\nSECOND")
        self.assertEqual(result["children"][0]["terminal"], "completed")

    def test_repeated_child_completion_requires_exact_followup_lifecycle(self):
        variations = (
            "missing-call", "wrong-target", "wrong-interaction-child",
            "wrong-interaction-path", "wrong-output", "extra-completion",
            "duplicate-completion-id", "interrupted-first-turn",
        )
        for variation in variations:
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                records = followup_root_records()
                call = next(
                    record for record in records
                    if record.get("payload", {}).get("name") == "followup_task"
                )
                interaction = next(
                    record for record in records
                    if record.get("payload", {}).get("item", {}).get("kind") == "interacted"
                )
                output = next(
                    record for record in records
                    if record.get("payload", {}).get("type") == "function_call_output"
                    and record["payload"].get("call_id") == "call_followup_child"
                )
                completions = [
                    record for record in records
                    if record.get("payload", {}).get("item", {}).get("kind") == "completed"
                    and record["payload"]["item"].get("agent_thread_id") == CHILD
                ]
                if variation == "missing-call":
                    call["payload"]["name"] = "send_message"
                elif variation == "wrong-target":
                    call["payload"]["arguments"] = line({
                        "target": "/root/other", "message": "Check again",
                    })
                elif variation == "wrong-interaction-child":
                    interaction["payload"]["item"]["agent_thread_id"] = GRANDCHILD
                elif variation == "wrong-interaction-path":
                    interaction["payload"]["item"]["agent_path"] = "/root/other"
                elif variation == "wrong-output":
                    output["payload"]["output"] = "unexpected"
                elif variation == "extra-completion":
                    extra = copy.deepcopy(completions[-1])
                    extra["payload"]["item"]["id"] = "unbound-extra-completion"
                    records.insert(-1, extra)
                elif variation == "duplicate-completion-id":
                    completions[-1]["payload"]["item"]["id"] = completions[0][
                        "payload"
                    ]["item"]["id"]
                else:
                    completions[0]["payload"]["item"]["kind"] = "interrupted"
                parse_native_tree(
                    ROOT,
                    {ROOT: raw(records), CHILD: raw(followup_child_records())},
                    require_delivery=True,
                )

    def test_file_change_mapping_is_normalized_to_exec_json_shape(self):
        records = child_records()
        tool = next(
            record["payload"]["item"] for record in records
            if record.get("payload", {}).get("item", {}).get("type") == "CommandExecution"
        )
        tool.clear()
        tool.update({
            "type": "FileChange", "id": "file-change", "status": "completed",
            "changes": {
                f"{CWD}/added.py": {"type": "add", "content": "new\n"},
                f"{CWD}/updated.py": {
                    "type": "update", "unified_diff": "@@ -1 +1 @@\n-old\n+new\n",
                    "move_path": None,
                },
                f"{CWD}/deleted.py": {"type": "delete", "content": "old\n"},
            },
        })

        call = parse_native_tree(
            ROOT, {ROOT: raw(root_records()), CHILD: raw(records)},
        )["children"][0]["tool_calls"][0]

        self.assertEqual(call["input"]["changes"], [
            {"path": f"{CWD}/added.py", "kind": "add"},
            {"path": f"{CWD}/updated.py", "kind": "update"},
            {"path": f"{CWD}/deleted.py", "kind": "delete"},
        ])

    def test_file_change_exec_json_list_remains_supported_and_validated(self):
        records = child_records()
        tool = next(
            record["payload"]["item"] for record in records
            if record.get("payload", {}).get("item", {}).get("type") == "CommandExecution"
        )
        tool.clear()
        changes = [{"path": f"{CWD}/added.py", "kind": "add"}]
        tool.update({
            "type": "FileChange", "id": "file-change", "status": "completed",
            "changes": changes,
        })

        call = parse_native_tree(
            ROOT, {ROOT: raw(root_records()), CHILD: raw(records)},
        )["children"][0]["tool_calls"][0]

        self.assertEqual(call["input"]["changes"], changes)

    def test_file_change_mapping_metadata_fails_closed(self):
        invalid_changes = {
            "empty": {},
            "empty-path": {"": {"type": "add", "content": "new"}},
            "non-mapping-metadata": {f"{CWD}/file.py": "add"},
            "unknown-type": {f"{CWD}/file.py": {"type": "copy", "content": "new"}},
            "non-string-type": {f"{CWD}/file.py": {"type": ["add"], "content": "new"}},
            "missing-add-content": {f"{CWD}/file.py": {"type": "add"}},
            "unexpected-add-field": {
                f"{CWD}/file.py": {"type": "add", "content": "new", "kind": "add"},
            },
            "missing-update-move-path": {
                f"{CWD}/file.py": {"type": "update", "unified_diff": "@@"},
            },
            "invalid-update-move-path": {
                f"{CWD}/file.py": {
                    "type": "update", "unified_diff": "@@", "move_path": 7,
                },
            },
            "missing-delete-content": {f"{CWD}/file.py": {"type": "delete"}},
        }
        for label, changes in invalid_changes.items():
            with self.subTest(label=label), self.assertRaisesRegex(
                NativeRolloutInvalid, "native file change",
            ):
                records = child_records()
                tool = next(
                    record["payload"]["item"] for record in records
                    if record.get("payload", {}).get("item", {}).get("type")
                    == "CommandExecution"
                )
                tool.clear()
                tool.update({
                    "type": "FileChange", "id": "file-change", "status": "completed",
                    "changes": changes,
                })
                parse_native_tree(ROOT, {ROOT: raw(root_records()), CHILD: raw(records)})

        with self.assertRaisesRegex(NativeRolloutInvalid, "native file change path"):
            rollouts._tool_call({
                "type": "FileChange", "id": "file-change", "status": "completed",
                "changes": {7: {"type": "add", "content": "new"}},
            }, CHILD, 0)

    def test_file_change_list_rejects_empty_duplicate_or_ambiguous_entries(self):
        invalid_changes = {
            "empty": [],
            "duplicate-path": [
                {"path": f"{CWD}/file.py", "kind": "add"},
                {"path": f"{CWD}/file.py", "kind": "update"},
            ],
            "empty-path": [{"path": "", "kind": "add"}],
            "non-string-path": [{"path": 7, "kind": "add"}],
            "non-mapping-entry": [f"{CWD}/file.py"],
            "unknown-kind": [{"path": f"{CWD}/file.py", "kind": "copy"}],
            "non-string-kind": [{"path": f"{CWD}/file.py", "kind": ["add"]}],
            "ambiguous-kind": [{
                "path": f"{CWD}/file.py", "kind": "add", "type": "update",
            }],
        }
        for label, changes in invalid_changes.items():
            with self.subTest(label=label), self.assertRaisesRegex(
                NativeRolloutInvalid, "native file change",
            ):
                records = child_records()
                tool = next(
                    record["payload"]["item"] for record in records
                    if record.get("payload", {}).get("item", {}).get("type")
                    == "CommandExecution"
                )
                tool.clear()
                tool.update({
                    "type": "FileChange", "id": "file-change", "status": "completed",
                    "changes": changes,
                })
                parse_native_tree(ROOT, {ROOT: raw(root_records()), CHILD: raw(records)})

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

        delayed = extract_native_plan_repair_trace(
            ROOT, raw(with_post_terminal_commands(
                records, thread=ROOT, turn=ROOT_TURN, native_syntax=True,
            )),
        )
        completions = delayed["post_terminal_completions"]
        drained = [item for item in delayed["commands"]
                   if item.get("post_terminal_completion")]
        self.assertEqual(len(completions), 2)
        self.assertEqual({item["id"] for item in drained},
                         {item["item_id"] for item in completions})
        self.assertTrue(all(item["model_observed"] is False for item in drained))
        self.assertTrue(all(item["success"] is False for item in drained))

        broken = copy.deepcopy(records)
        del broken[2]["payload"]["started_at_ms"]
        with self.assertRaisesRegex(NativeRolloutInvalid, "lifecycle timing"):
            extract_native_plan_repair_trace(ROOT, raw(broken))

    def test_authenticated_command_trace_includes_hash_bound_child_but_g3_stays_root_only(self):
        returned_root = root_records()
        returned_root.insert(-1, delivery_record())
        raw_by_thread = {ROOT: raw(returned_root), CHILD: raw(child_records())}
        tree = parse_native_tree(ROOT, raw_by_thread)
        trace = extract_native_plan_repair_trace(
            ROOT, raw_by_thread[ROOT], validated_dispatches={
                "dispatches": tree["dispatches"],
                "authenticated_tree": (raw_by_thread, tree),
            },
        )

        self.assertEqual([item["id"] for item in trace["commands"]], ["root-command"])
        self.assertEqual(
            [(item["thread_id"], item["id"]) for item in trace["authenticated_commands"]],
            [(ROOT, "root-command"), (CHILD, "exec-child")],
        )
        child = trace["authenticated_commands"][1]
        self.assertEqual(child["cwd"], CWD)
        self.assertEqual(child["raw_sha256"], tree["raw_sha256"][CHILD])
        self.assertEqual(child["output"]["stdout"], "canary-input-v1\n")

    def test_authenticated_command_trace_rejects_omission_and_forged_bindings(self):
        returned_root = root_records()
        returned_root.insert(-1, delivery_record())
        raw_by_thread = {ROOT: raw(returned_root), CHILD: raw(child_records())}
        tree = parse_native_tree(ROOT, raw_by_thread)
        variants = {}

        omitted = dict(raw_by_thread)
        del omitted[CHILD]
        variants["omitted"] = (omitted, tree, "rollout set")

        forged_sha = copy.deepcopy(tree)
        forged_sha["raw_sha256"][CHILD] = "f" * 64
        variants["sha"] = (raw_by_thread, forged_sha, "not hash-bound")

        forged_thread = copy.deepcopy(tree)
        forged_thread["children"][0]["thread_id"] = GRANDCHILD
        variants["thread"] = (raw_by_thread, forged_thread, "rollout set")

        forged_cwd = copy.deepcopy(tree)
        forged_cwd["children"][0]["tool_calls"][0]["input"]["cwd"] = CWD + "/other"
        variants["cwd"] = (raw_by_thread, forged_cwd, "validated tools")

        forged_output = copy.deepcopy(tree)
        forged_output["children"][0]["tool_calls"][0]["output"]["stdout"] = "forged\n"
        variants["output"] = (raw_by_thread, forged_output, "validated tools")

        for label, (raws, validated, error) in variants.items():
            with self.subTest(label=label), self.assertRaisesRegex(
                NativeRolloutInvalid, error,
            ):
                extract_native_plan_repair_trace(
                    ROOT, raw_by_thread[ROOT], validated_dispatches={
                        "dispatches": tree["dispatches"],
                        "authenticated_tree": (raws, validated),
                    },
                )

        duplicate = list(child_records())
        duplicate.insert(-2, copy.deepcopy(duplicate[6]))
        with self.assertRaisesRegex(NativeRolloutInvalid, "repeats native item"):
            parse_native_tree(ROOT, {ROOT: raw(root_records()), CHILD: raw(duplicate)})

class NativeCodexDeliveryTests(unittest.TestCase):
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

    def test_parent_delivery_retains_native_bound_result_evidence(self):
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
            "text": rendered.decode(),
            "sha256": hashlib.sha256(rendered).hexdigest(),
            "bytes": len(rendered),
            "author": "/root/read_fixture",
            "recipient": "/root",
            "turn_id": ROOT_TURN,
            "native_event_index": len(records) - 2,
        })
        self.assertEqual(delivery["text"], "Message Type: FINAL_ANSWER\nPayload:\nCANARY_OK")

    def test_terminal_failed_child_supplies_missing_parent_completion_activity(self):
        records = [record for record in root_records()
                   if record.get("payload", {}).get("item", {}).get("kind") != "completed"]
        command = next(
            record["payload"] for record in records
            if record.get("payload", {}).get("item", {}).get("type")
            == "CommandExecution"
        )
        command.update({"started_at_ms": 1000, "completed_at_ms": 1100})
        records.insert(-1, delivery_record(
            text=("Message Type: FINAL_ANSWER\nPayload:\nAgent errored: "
                  "Selected model is at capacity."),
        ))
        failed = child_records()
        failed[-1]["payload"].update({
            "last_agent_message": None,
            "error": {
                "message": "Selected model is at capacity.",
                "codex_error_info": "server_overloaded",
            },
        })
        tree = {ROOT: raw(records), CHILD: raw(failed)}

        result = parse_native_tree(ROOT, tree, require_delivery=True)
        dispatch = result["dispatches"][0]
        child = result["children"][0]
        self.assertEqual(dispatch["status"], "failed")
        self.assertEqual(dispatch["completion_source"], "child-task-complete-error")
        self.assertIsNone(dispatch["completed_native_event_index"])
        self.assertEqual(dispatch["terminal_failure"]["codex_error_info"],
                         "server_overloaded")
        self.assertEqual(child["terminal"], "failed")
        self.assertEqual(child["native_metadata"]["terminal_failure"],
                         dispatch["terminal_failure"])
        self.assertEqual(dispatch["delivery"]["author"], "/root/read_fixture")
        trace = extract_native_plan_repair_trace(
            ROOT, raw(records), validated_dispatches=result["dispatches"],
        )
        self.assertEqual(trace["dispatches"][0]["id"], CALL)
        with self.assertRaisesRegex(NativeRolloutInvalid, "completion index"):
            extract_native_plan_repair_trace(ROOT, raw(records))

        forged = copy.deepcopy(result["dispatches"])
        forged[0]["status"] = "completed"
        with self.assertRaisesRegex(NativeRolloutInvalid, "failed dispatch proof"):
            extract_native_plan_repair_trace(
                ROOT, raw(records), validated_dispatches=forged,
            )

        successful = copy.deepcopy(failed)
        del successful[-1]["payload"]["error"]
        with self.assertRaisesRegex(NativeRolloutInvalid, "unmatched subagent activity"):
            parse_native_tree(ROOT, {ROOT: raw(records), CHILD: raw(successful)})

        malformed = copy.deepcopy(failed)
        malformed[-1]["payload"]["error"]["message"] = ""
        with self.assertRaisesRegex(NativeRolloutInvalid, "terminal error message"):
            parse_native_tree(ROOT, {ROOT: raw(records), CHILD: raw(malformed)})

        for label, mutate, pattern in (
            ("missing-code",
             lambda payload: payload["error"].pop("codex_error_info"),
             "terminal error code"),
            ("blank-code",
             lambda payload: payload["error"].update({"codex_error_info": " "}),
             "terminal error code"),
            ("non-string-code",
             lambda payload: payload["error"].update({"codex_error_info": 503}),
             "terminal error code"),
            ("conflicting-message",
             lambda payload: payload.update({"last_agent_message": "partial result"}),
             "conflicts with a final message"),
        ):
            with self.subTest(label=label):
                variant = copy.deepcopy(failed)
                mutate(variant[-1]["payload"])
                with self.assertRaisesRegex(NativeRolloutInvalid, pattern):
                    parse_native_tree(ROOT, {ROOT: raw(records), CHILD: raw(variant)})

        matched = root_records()
        matched.insert(-1, delivery_record(
            text=("Message Type: FINAL_ANSWER\nPayload:\nAgent errored: "
                  "Selected model is at capacity."),
        ))
        matched_result = parse_native_tree(
            ROOT, {ROOT: raw(matched), CHILD: raw(failed)}, require_delivery=True,
        )
        self.assertEqual(matched_result["dispatches"][0]["status"], "failed")
        self.assertEqual(matched_result["dispatches"][0]["completion_source"],
                         "parent-subagent-activity")

        without_delivery = [record for record in records
                            if record.get("type") != "response_item"
                            or record.get("payload", {}).get("type") != "agent_message"]
        with self.assertRaises(NativeRolloutIncomplete):
            parse_native_tree(
                ROOT, {ROOT: raw(without_delivery), CHILD: raw(failed)},
                require_delivery=True,
            )

        failed_root = root_records()
        failed_root[-1]["payload"].update({
            "last_agent_message": None,
            "error": {"message": "root failed", "codex_error_info": "server_overloaded"},
        })
        with self.assertRaisesRegex(NativeRolloutInvalid, "root rollout ended"):
            parse_native_tree(ROOT, {ROOT: raw(failed_root), CHILD: raw(child_records())})

    def test_interrupted_child_is_bound_failed_without_a_parent_delivery(self):
        result = parse_native_tree(
            ROOT,
            {ROOT: raw(interrupted_root_records()),
             CHILD: raw(interrupted_child_records(post_terminal=True))},
            require_delivery=True,
        )
        dispatch = result["dispatches"][0]
        child = result["children"][0]
        self.assertEqual(dispatch["status"], "failed")
        self.assertEqual(dispatch["completion_source"], "parent-subagent-interrupted")
        self.assertEqual(dispatch["completed_native_event_id"], INTERRUPT_CALL)
        self.assertIsNone(dispatch["delivery"])
        self.assertEqual(dispatch["terminal_failure"]["codex_error_info"], "interrupted")
        self.assertEqual(child["terminal"], "failed")
        self.assertEqual(child["native_metadata"]["terminal_failure"],
                         dispatch["terminal_failure"])
        drained = child["native_metadata"]["post_terminal_completions"]
        self.assertEqual(len(drained), 1)
        self.assertFalse(drained[0]["model_observed"])
        self.assertEqual(drained[0]["command"], "ripwire . --quality-delta")
        trace_records = interrupted_root_records()
        command = next(
            record["payload"] for record in trace_records
            if record.get("payload", {}).get("item", {}).get("type")
            == "CommandExecution"
        )
        command.update({"started_at_ms": 1000, "completed_at_ms": 1100})
        trace = extract_native_plan_repair_trace(
            ROOT, raw(trace_records),
            validated_dispatches=result["dispatches"],
        )
        self.assertEqual(trace["dispatches"], [])

    def test_interrupted_parent_lifecycle_binding_fails_closed(self):
        for variation in (
            "missing-call", "wrong-call", "duplicate-call", "wrong-target",
            "wrong-path", "wrong-turn", "wrong-child", "missing-output",
            "bad-output", "output-before-activity", "duplicate-interruption",
            "completed-conflict", "forged-delivery",
        ):
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                records = interrupted_root_records()
                call_index = next(index for index, record in enumerate(records)
                                  if record.get("payload", {}).get("name") == "interrupt_agent")
                activity_index = next(index for index, record in enumerate(records)
                                      if record.get("payload", {}).get("item", {}).get("kind")
                                      == "interrupted")
                output_index = next(index for index, record in enumerate(records)
                                    if record.get("payload", {}).get("type")
                                    == "function_call_output")
                if variation == "missing-call":
                    del records[call_index]
                elif variation == "wrong-call":
                    records[call_index]["payload"]["name"] = "wait_agent"
                elif variation == "duplicate-call":
                    records.insert(call_index + 1, copy.deepcopy(records[call_index]))
                elif variation == "wrong-target":
                    records[call_index]["payload"]["arguments"] = line({"target": "other"})
                elif variation == "wrong-path":
                    records[activity_index]["payload"]["item"]["agent_path"] = "/root/other"
                elif variation == "wrong-turn":
                    records[activity_index]["payload"]["turn_id"] = CHILD_TURN
                elif variation == "wrong-child":
                    records[activity_index]["payload"]["item"]["agent_thread_id"] = GRANDCHILD
                elif variation == "missing-output":
                    del records[output_index]
                elif variation == "bad-output":
                    records[output_index]["payload"]["output"] = line({
                        "previous_status": "completed",
                    })
                elif variation == "output-before-activity":
                    output = records.pop(output_index)
                    records.insert(call_index, output)
                elif variation == "duplicate-interruption":
                    records.insert(activity_index + 1, copy.deepcopy(records[activity_index]))
                elif variation == "completed-conflict":
                    records.insert(-1, event({
                        "type": "item_completed", "thread_id": ROOT,
                        "turn_id": ROOT_TURN, "item": {
                            "type": "SubAgentActivity", "id": "completed-too",
                            "kind": "completed", "agent_thread_id": CHILD,
                            "agent_path": "/root/read_fixture",
                        },
                    }))
                else:
                    records.insert(-1, delivery_record())
                parse_native_tree(
                    ROOT,
                    {ROOT: raw(records), CHILD: raw(interrupted_child_records())},
                    require_delivery=True,
                )

    def test_interrupted_child_terminal_fails_closed_on_conflicting_evidence(self):
        for variation in (
            "wrong-reason", "bad-timing", "missing-abort", "duplicate-abort",
            "completed-too", "final-message", "wrong-turn", "successful-child",
        ):
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                root = interrupted_root_records()
                child = interrupted_child_records()
                if variation == "wrong-reason":
                    child[-1]["payload"]["reason"] = "cancelled"
                elif variation == "bad-timing":
                    child[-1]["payload"]["duration_ms"] = -1
                elif variation == "missing-abort":
                    child.pop()
                elif variation == "duplicate-abort":
                    child.append(copy.deepcopy(child[-1]))
                elif variation == "completed-too":
                    child.append(event({
                        "type": "task_complete", "turn_id": CHILD_TURN,
                        "completed_at": 4,
                    }))
                elif variation == "final-message":
                    child.insert(-1, event({
                        "type": "item_completed", "thread_id": CHILD,
                        "turn_id": CHILD_TURN, "item": {
                            "type": "AgentMessage", "id": "message",
                            "content": [{"type": "text", "text": "conflict"}],
                        },
                    }))
                elif variation == "wrong-turn":
                    child[-1]["payload"]["turn_id"] = str(uuid.UUID(int=6))
                else:
                    child = child_records()
                parse_native_tree(ROOT, {ROOT: raw(root), CHILD: raw(child)})

        with self.assertRaises(NativeRolloutInvalid):
            parse_native_tree(
                ROOT,
                {ROOT: raw(root_records()), CHILD: raw(interrupted_child_records())},
            )

    def test_native_progress_delivery_does_not_duplicate_final_answer(self):
        records = root_records()
        records[-1:-1] = [progress_delivery_record(), delivery_record()]
        tree = {ROOT: raw(records), CHILD: raw(with_interim_send(child_records()))}

        parsed = parse_native_tree(ROOT, tree, require_delivery=True)
        dispatch = parsed["dispatches"][0]

        self.assertEqual(dispatch["delivery"]["message_id"], "delivery-1")
        self.assertEqual(dispatch["delivery"]["text"],
                         "Message Type: FINAL_ANSWER\nPayload:\nCANARY_OK")
        interim = dispatch["interim_deliveries"]
        self.assertEqual(len(interim), 1)
        self.assertEqual(interim[0]["call_id"], "call_interim_message")
        self.assertEqual(interim[0]["message_id"], "progress-1")
        self.assertEqual(len(interim[0]["sha256"]), 64)
        self.assertNotIn("opaque-native-progress", json.dumps(interim))
        command = next(
            record["payload"] for record in records
            if record.get("payload", {}).get("item", {}).get("type")
            == "CommandExecution"
        )
        command.update({"started_at_ms": 1000, "completed_at_ms": 1100})
        trace = extract_native_plan_repair_trace(
            ROOT, raw(records), validated_dispatches=parsed["dispatches"],
        )
        self.assertEqual(trace["dispatches"][0]["delivery_record_index"],
                         dispatch["delivery"]["native_event_index"])
        forged = copy.deepcopy(parsed["dispatches"])
        forged[0]["delivery"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(
            NativeRolloutInvalid, "validated delivery binding disagrees",
        ):
            extract_native_plan_repair_trace(
                ROOT, raw(records), validated_dispatches=forged,
            )

        progress_only = root_records()
        progress_only.insert(-1, progress_delivery_record())
        with self.assertRaises(NativeRolloutIncomplete):
            parse_native_tree(
                ROOT, {ROOT: raw(progress_only),
                       CHILD: raw(with_interim_send(child_records()))},
                require_delivery=True,
            )

    def test_malformed_progress_delivery_is_not_silently_ignored(self):
        variations = (
            "message-type", "task-name", "sender", "payload", "recipient", "turn",
            "message-id", "missing-encrypted", "extra-content", "empty-encrypted",
        )
        for variation in variations:
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                progress = progress_delivery_record()
                payload = progress["payload"]
                if variation == "message-type":
                    payload["content"][0]["text"] = payload["content"][0]["text"].replace(
                        "Message Type: MESSAGE", "Message Type: FINAL_ANSWER")
                elif variation == "task-name":
                    payload["content"][0]["text"] = payload["content"][0]["text"].replace(
                        "Task name: /root", "Task name: /root/other")
                elif variation == "sender":
                    payload["content"][0]["text"] = payload["content"][0]["text"].replace(
                        "Sender: /root/read_fixture", "Sender: /root/other")
                elif variation == "payload":
                    payload["content"][0]["text"] += "unexpected"
                elif variation == "recipient":
                    payload["recipient"] = "/root/other"
                elif variation == "turn":
                    payload["internal_chat_message_metadata_passthrough"]["turn_id"] = CHILD_TURN
                elif variation == "message-id":
                    payload["id"] = ""
                elif variation == "missing-encrypted":
                    payload["content"].pop()
                elif variation == "extra-content":
                    payload["content"].append({"type": "input_text", "text": "extra"})
                else:
                    payload["content"][1]["encrypted_content"] = ""
                records = root_records()
                records[-1:-1] = [progress, delivery_record()]
                parse_native_tree(
                    ROOT, {ROOT: raw(records),
                           CHILD: raw(with_interim_send(child_records()))},
                    require_delivery=True,
                )

    def test_interim_delivery_requires_one_to_one_causal_child_send(self):
        variations = (
            "unbound", "ciphertext-mismatch", "duplicate-delivery", "replayed-send",
            "wrong-target", "wrong-interaction-call", "wrong-interaction-parent",
            "wrong-interaction-path", "wrong-interaction-turn", "after-final",
        )
        for variation in variations:
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                child = with_interim_send(child_records())
                parent = root_records()
                deliveries = [progress_delivery_record(), delivery_record()]
                if variation == "unbound":
                    child = child_records()
                elif variation == "ciphertext-mismatch":
                    deliveries[0] = progress_delivery_record(ciphertext="different")
                elif variation == "duplicate-delivery":
                    deliveries.insert(1, progress_delivery_record(message_id="progress-2"))
                elif variation == "replayed-send":
                    child = with_interim_send(
                        child, call_id="call_interim_message_2",
                    )
                elif variation == "wrong-target":
                    call = next(record for record in child
                                if record.get("payload", {}).get("name") == "send_message")
                    call["payload"]["arguments"] = line({
                        "target": "/root/other", "message": "opaque-native-progress",
                    })
                else:
                    interaction = next(
                        record for record in child
                        if record.get("payload", {}).get("item", {}).get("kind") == "interacted"
                    )
                    if variation == "wrong-interaction-call":
                        interaction["payload"]["item"]["id"] = "different-call"
                    elif variation == "wrong-interaction-parent":
                        interaction["payload"]["item"]["agent_thread_id"] = SECOND_CHILD
                    elif variation == "wrong-interaction-path":
                        interaction["payload"]["item"]["agent_path"] = "/root/other"
                    elif variation == "wrong-interaction-turn":
                        interaction["payload"]["turn_id"] = ROOT_TURN
                    elif variation == "after-final":
                        deliveries.reverse()
                parent[-1:-1] = deliveries
                parse_native_tree(
                    ROOT, {ROOT: raw(parent), CHILD: raw(child)}, require_delivery=True,
                )

    def test_multiple_interim_deliveries_preserve_causal_order(self):
        child = with_interim_send(child_records(), ciphertext="ciphertext-1",
                                  call_id="call_interim_1")
        child = with_interim_send(child, ciphertext="ciphertext-2",
                                  call_id="call_interim_2")
        parent = root_records()
        parent[-1:-1] = [
            progress_delivery_record(message_id="progress-1", ciphertext="ciphertext-1"),
            progress_delivery_record(message_id="progress-2", ciphertext="ciphertext-2"),
            delivery_record(),
        ]

        dispatch = parse_native_tree(
            ROOT, {ROOT: raw(parent), CHILD: raw(child)}, require_delivery=True,
        )["dispatches"][0]

        self.assertEqual(
            [value["call_id"] for value in dispatch["interim_deliveries"]],
            ["call_interim_1", "call_interim_2"],
        )
        self.assertEqual(
            [value["message_id"] for value in dispatch["interim_deliveries"]],
            ["progress-1", "progress-2"],
        )

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

    def test_child_interaction_with_parent_is_not_a_nested_dispatch(self):
        records = child_records()
        interaction = event({
            "type": "item_completed", "thread_id": CHILD, "turn_id": CHILD_TURN,
            "item": {"type": "SubAgentActivity", "id": "message-parent",
                     "kind": "interacted", "agent_thread_id": ROOT,
                     "agent_path": "/root"},
        })
        records.insert(-1, interaction)
        tree = fixture_tree()
        tree[CHILD] = raw(records)
        result = parse_native_tree(ROOT, tree)
        self.assertEqual([item["thread_id"] for item in result["children"]], [CHILD])

        interaction["payload"]["item"]["kind"] = "unknown"
        tree[CHILD] = raw(records)
        with self.assertRaisesRegex(NativeRolloutInvalid, "unknown subagent activity kind"):
            parse_native_tree(ROOT, tree)

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

class NativeCodexValidationTests(unittest.TestCase):
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

class NativeCodexSkillInjectionTests(unittest.TestCase):
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

class NativeCodexCollectionTests(unittest.TestCase):
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


class PostTerminalCommandTests(unittest.TestCase):
    def test_exec_wrapper_allows_only_trailing_whitespace(self):
        for suffix, accepted in (("\n", True), ("\n\t", True), ("\ntext('extra');", False)):
            with self.subTest(suffix=suffix):
                records = with_post_terminal_command(child_records())
                invocation = next(
                    record for record in records
                    if record.get("payload", {}).get("type") == "custom_tool_call"
                    and record["payload"].get("name") == "exec"
                )
                invocation["payload"]["input"] += suffix
                tree = fixture_tree()
                tree[CHILD] = raw(records)
                if accepted:
                    self.assertEqual(
                        len(parse_native_tree(ROOT, tree)["children"][0][
                            "native_metadata"
                        ]["post_terminal_completions"]),
                        1,
                    )
                else:
                    with self.assertRaisesRegex(
                        NativeRolloutInvalid, "no unique native exec invocation",
                    ):
                        parse_native_tree(ROOT, tree)

    def test_correlated_completion_is_visible_but_not_model_observed(self):
        tree = fixture_tree()
        tree[CHILD] = raw(with_post_terminal_command(child_records()))

        child = parse_native_tree(ROOT, tree)["children"][0]
        completions = child["native_metadata"]["post_terminal_completions"]
        self.assertEqual(len(completions), 1)
        completion = completions[0]
        command = child["tool_calls"][-1]

        self.assertEqual(completion["schema"],
                         "codex-post-terminal-command-completion/v2")
        self.assertFalse(completion["model_observed"])
        self.assertEqual((completion["terminal_ordinal"], completion["completion_ordinal"]),
                         (97, 98))
        self.assertEqual(completion["item_id"], command["id"])
        self.assertEqual(completion["command"], "ripwire . --quality-delta")
        self.assertEqual(completion["cwd"], CWD)
        self.assertEqual(len(child["native_metadata"]["rollout_raw_sha256"]), 64)
        self.assertFalse(command["model_observed"])
        self.assertTrue(command["post_terminal_completion"])
        self.assertFalse(command["success"])
        self.assertEqual(command["status"], "completed")
        self.assertEqual(command["output"]["exit_code"], 0)

        root_tree = fixture_tree()
        root_tree[ROOT] = raw(with_post_terminal_command(
            root_records(), thread=ROOT, turn=ROOT_TURN,
        ))
        root_completions = parse_native_tree(ROOT, root_tree)["native_metadata"][
            "post_terminal_completions"
        ]
        self.assertEqual(len(root_completions), 1)
        root_completion = root_completions[0]
        self.assertFalse(root_completion["model_observed"])
        self.assertEqual(root_completion["thread_id"], ROOT)

class SessionBackedPostTerminalCommandTests(unittest.TestCase):
    def test_session_backed_completion_binds_exec_poll_and_native_process(self):
        records = with_session_backed_post_terminal_command(
            interrupted_child_records(),
        )
        result = parse_native_tree(
            ROOT,
            {ROOT: raw(interrupted_root_records()), CHILD: raw(records)},
            require_delivery=True,
        )
        completion = result["children"][0]["native_metadata"][
            "post_terminal_completions"
        ][0]

        self.assertEqual(completion["process_id"], "93111")
        self.assertEqual(completion["native_session_id"], 93111)
        self.assertEqual(len(completion["native_session_polls"]), 1)
        self.assertEqual(completion["native_session_polls"][0]["call_id"],
                         "call_post_terminal_poll")
        self.assertFalse(completion["model_observed"])

    def test_session_backed_completion_identity_adversaries_fail_closed(self):
        for variation in (
            "process-mismatch", "poll-session-mismatch", "duplicate-session",
            "poll-not-interrupted", "poll-crossed-turn", "malformed-poll",
        ):
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                records = with_session_backed_post_terminal_command(
                    interrupted_child_records(),
                )
                terminal_index = next(
                    index for index, record in enumerate(records)
                    if record.get("payload", {}).get("type") == "turn_aborted"
                )
                invocation_response = records[terminal_index - 3]["payload"]
                poll = records[terminal_index - 2]["payload"]
                poll_response = records[terminal_index - 1]["payload"]
                completion = records[terminal_index + 1]["payload"]["item"]
                if variation == "process-mismatch":
                    completion["process_id"] = "93112"
                elif variation == "poll-session-mismatch":
                    poll["input"] = poll["input"].replace("session_id:93111",
                                                          "session_id:93112")
                elif variation == "duplicate-session":
                    invocation_response["output"].append(copy.deepcopy(
                        invocation_response["output"][-1]
                    ))
                elif variation == "poll-not-interrupted":
                    poll_response["output"] = [{
                        "type": "input_text", "text": line({
                            "chunk_id": "still-running", "wall_time_seconds": 30.0,
                            "session_id": 93111, "original_token_count": 2,
                            "output": "still running\n",
                        }),
                    }]
                elif variation == "poll-crossed-turn":
                    poll_response["internal_chat_message_metadata_passthrough"][
                        "turn_id"
                    ] = ROOT_TURN
                else:
                    poll["input"] += "text('extra');"
                parse_native_tree(
                    ROOT,
                    {ROOT: raw(interrupted_root_records()), CHILD: raw(records)},
                    require_delivery=True,
                )


class PostTerminalDrainTests(unittest.TestCase):
    def test_started_only_overlapping_final_gate_fails_closed(self):
        for owner in ("child", "root"):
            with self.subTest(owner=owner):
                thread = CHILD if owner == "child" else ROOT
                turn = CHILD_TURN if owner == "child" else ROOT_TURN
                initial = child_records() if owner == "child" else root_records()
                records = with_post_terminal_commands(
                    initial, thread=thread, turn=turn,
                    commands=(
                        "ripwire . --quality-delta && ripwire . --test-gate",
                        "ripwire . --test-gate",
                    ),
                )
                invocations = [
                    record for record in records
                    if record.get("payload", {}).get("type") == "custom_tool_call"
                    and record["payload"].get("name") == "exec"
                ]
                duplicate = copy.deepcopy(invocations[-1])
                duplicate["payload"].update({
                    "id": "ctc_started_only_duplicate",
                    "call_id": "call_started_only_duplicate",
                    "status": "in_progress",
                })
                duplicate["payload"]["input"] = duplicate["payload"]["input"].replace(
                    "ripwire . --test-gate", "ripwire . --quality-delta",
                )
                terminal_index = next(
                    index for index, record in enumerate(records)
                    if record.get("payload", {}).get("type") == "task_complete"
                )
                records.insert(terminal_index, duplicate)
                tree = fixture_tree()
                tree[thread] = raw(records)
                with self.assertRaisesRegex(NativeRolloutInvalid, "unfinished exec invocation"):
                    parse_native_tree(ROOT, tree)

    def test_two_correlated_completions_are_bounded_and_fail_closed(self):
        for owner in ("child", "root"):
            with self.subTest(owner=owner):
                tree = fixture_tree()
                thread = CHILD if owner == "child" else ROOT
                turn = CHILD_TURN if owner == "child" else ROOT_TURN
                records = child_records() if owner == "child" else root_records()
                tree[thread] = raw(with_post_terminal_commands(
                    records, thread=thread, turn=turn, native_syntax=(owner == "child"),
                ))
                parsed = parse_native_tree(ROOT, tree)
                if owner == "child":
                    subject = parsed["children"][0]
                    calls = subject["tool_calls"][-2:]
                    self.assertEqual({call["id"] for call in calls}, {
                        value["item_id"]
                        for value in subject["native_metadata"]["post_terminal_completions"]
                    })
                    for call in calls:
                        self.assertFalse(call["model_observed"])
                        self.assertTrue(call["post_terminal_completion"])
                        self.assertFalse(call["success"])
                else:
                    subject = parsed
                completions = subject["native_metadata"]["post_terminal_completions"]
                self.assertEqual(len(completions), 2)
                self.assertEqual(
                    [value["completion_ordinal"] for value in completions],
                    [98, 99],
                )
                self.assertEqual(len({value["item_id"] for value in completions}), 2)
                self.assertEqual(len({value["call_id"] for value in completions}), 2)
                self.assertEqual(len({value["invocation_id"] for value in completions}), 2)
                self.assertEqual(len({value["response_id"] for value in completions}), 2)

    def test_multiple_completion_adversaries_fail_closed(self):
        variations = (
            "over-bound", "ordinal-gap", "reordered", "duplicate-item",
            "duplicate-call", "duplicate-invocation", "duplicate-response",
            "wrong-thread", "wrong-turn", "wrong-status", "wrong-source",
            "bad-start", "bad-complete", "interleaved-work", "unmatched-command",
        )
        for variation in variations:
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                count = 9 if variation == "over-bound" else 2
                commands = tuple(f"ripwire . --gate-{index}" for index in range(count))
                records = with_post_terminal_commands(child_records(), commands=commands)
                terminal_index = next(
                    index for index, record in enumerate(records)
                    if record.get("payload", {}).get("type") == "task_complete"
                )
                suffix = records[terminal_index + 1:]
                if variation == "ordinal-gap":
                    suffix[1]["ordinal"] += 1
                elif variation == "reordered":
                    records[terminal_index + 1:] = reversed(suffix)
                elif variation == "duplicate-item":
                    suffix[1]["payload"]["item"]["id"] = suffix[0]["payload"]["item"]["id"]
                elif variation == "wrong-thread":
                    suffix[1]["payload"]["thread_id"] = GRANDCHILD
                elif variation == "wrong-turn":
                    suffix[1]["payload"]["turn_id"] = ROOT_TURN
                elif variation == "wrong-status":
                    suffix[1]["payload"]["item"]["status"] = "failed"
                elif variation == "wrong-source":
                    suffix[1]["payload"]["item"]["source"] = "unified_exec_poll"
                elif variation == "bad-start":
                    suffix[1]["payload"]["started_at_ms"] = 4_000
                elif variation == "bad-complete":
                    suffix[1]["payload"]["completed_at_ms"] = 3_999
                elif variation == "interleaved-work":
                    suffix[1]["payload"]["item"]["type"] = "AgentMessage"
                elif variation == "unmatched-command":
                    suffix[1]["payload"]["item"]["command"][-1] = "not invoked"
                else:
                    invocations = [
                        record for record in records[:terminal_index]
                        if record.get("payload", {}).get("type") == "custom_tool_call"
                        and record["payload"].get("name") == "exec"
                    ]
                    responses = [
                        record for record in records[:terminal_index]
                        if record.get("payload", {}).get("type") == "custom_tool_call_output"
                    ]
                    if variation == "duplicate-call":
                        invocations[1]["payload"]["call_id"] = invocations[0]["payload"]["call_id"]
                        responses[1]["payload"]["call_id"] = responses[0]["payload"]["call_id"]
                    elif variation == "duplicate-invocation":
                        invocations[1]["payload"]["id"] = invocations[0]["payload"]["id"]
                    elif variation == "duplicate-response":
                        responses[1]["payload"]["id"] = responses[0]["payload"]["id"]
                tree = fixture_tree()
                tree[CHILD] = raw(records)
                parse_native_tree(ROOT, tree)

    def test_other_post_terminal_work_fails_closed(self):
        variations = (
            "message", "reasoning", "file-change", "collaboration", "native-error",
            "failed-status", "nonzero", "missing-start", "missing-complete",
            "boolean-timing", "start-after-terminal", "complete-before-terminal",
            "wrong-source", "wrong-thread", "wrong-turn", "duplicate-id", "invalid-id",
            "changed-command", "changed-cwd", "missing-invocation", "missing-response",
            "duplicate-invocation", "wrong-response-turn", "malformed-response",
            "extra-later-record", "ordinal-gap",
        )
        for variation in variations:
            with self.subTest(variation=variation), self.assertRaises(NativeRolloutInvalid):
                tree = fixture_tree()
                records = with_post_terminal_command(child_records())
                completion = records[-1]
                payload = completion["payload"]
                item = payload["item"]
                if variation == "message":
                    item["type"] = "AgentMessage"
                elif variation == "reasoning":
                    item["type"] = "Reasoning"
                elif variation == "file-change":
                    item["type"] = "FileChange"
                elif variation == "collaboration":
                    item["type"] = "CollabAgentToolCall"
                elif variation == "native-error":
                    payload["type"] = "error"
                elif variation == "failed-status":
                    item["status"] = "failed"
                elif variation == "nonzero":
                    item["exit_code"] = 7
                elif variation == "missing-start":
                    del payload["started_at_ms"]
                elif variation == "missing-complete":
                    del payload["completed_at_ms"]
                elif variation == "boolean-timing":
                    payload["completed_at_ms"] = True
                elif variation == "start-after-terminal":
                    payload["started_at_ms"] = 4_001
                elif variation == "complete-before-terminal":
                    payload["completed_at_ms"] = 3_999
                elif variation == "wrong-source":
                    item["source"] = "unified_exec_poll"
                elif variation == "wrong-thread":
                    payload["thread_id"] = GRANDCHILD
                elif variation == "wrong-turn":
                    payload["turn_id"] = ROOT_TURN
                elif variation == "duplicate-id":
                    duplicate = event({
                        "type": "item_completed", "thread_id": CHILD,
                        "turn_id": CHILD_TURN,
                        "item": {"type": "AgentMessage", "id": item["id"],
                                 "content": [{"type": "Text", "text": "duplicate"}]},
                    })
                    records.insert(-4, duplicate)
                elif variation == "invalid-id":
                    item["id"] = "exec-not-a-uuid"
                elif variation == "changed-command":
                    item["command"][-1] = "ripwire . --test-gate"
                elif variation == "changed-cwd":
                    item["cwd"] = "file:///private/tmp/other"
                elif variation == "missing-invocation":
                    del records[-4]
                elif variation == "missing-response":
                    del records[-3]
                elif variation == "duplicate-invocation":
                    records.insert(-3, copy.deepcopy(records[-4]))
                elif variation == "wrong-response-turn":
                    records[-3]["payload"][
                        "internal_chat_message_metadata_passthrough"
                    ]["turn_id"] = ROOT_TURN
                elif variation == "malformed-response":
                    records[-3]["payload"]["output"] = [{"type": "output_text", "text": ""}]
                elif variation == "extra-later-record":
                    records.append(event({"type": "token_count"}))
                else:
                    completion["ordinal"] = 100
                tree[CHILD] = raw(records)
                parse_native_tree(ROOT, tree)


if __name__ == "__main__":
    suite = unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeCodexRolloutTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeCodexDeliveryTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeCodexValidationTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(
            NativeCodexSkillInjectionTests,
        ),
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeCodexCollectionTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(PostTerminalCommandTests),
        unittest.defaultTestLoader.loadTestsFromTestCase(
            SessionBackedPostTerminalCommandTests,
        ),
        unittest.defaultTestLoader.loadTestsFromTestCase(PostTerminalDrainTests),
    ))
    raise SystemExit(run_counted(
        suite,
        label="test-native-eval-codex-rollouts",
    ))
