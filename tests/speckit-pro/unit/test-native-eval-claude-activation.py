#!/usr/bin/env python3
"""Claude explicit skill evidence must come from its native loader records."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
import uuid
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted
import native_eval_claude_activation as activation
from native_eval_claude_activation import (
    AUTHORITY,
    ClaudeActivationInvalid,
    ClaudeActivationUnavailable,
    build_activation_witness,
    collect_retained_session,
    parse_explicit_activation,
)


SESSION = str(uuid.UUID(int=1))
PROMPT_ID = str(uuid.UUID(int=2))
COMMAND_ID = str(uuid.UUID(int=3))
INJECTION_ID = str(uuid.UUID(int=4))
SKILL = "fixture-plugin:static-skill"
DIRECTORY = "/private/tmp/native-activation/plugin/skills/static-skill"
CWD = "/private/tmp/native-activation/work/cwd"
VERSION = "2.1.273"
ARGUMENTS = "Read fixture.md and write only result.json."
PROMPT = f"/{SKILL} {ARGUMENTS}"
BODY = b"\n# Static skill\n\nRead the fixture and write the requested result.\n"
SKILL_BYTES = (
    b"---\n"
    b"name: static-skill\n"
    b"description: synthetic frozen native-shape fixture\n"
    b"user-invocable: true\n"
    b"disable-model-invocation: true\n"
    b"---\n" + BODY
)


def native_session_bytes(records):
    text = "".join(
        json.dumps(record, separators=(",", ":"), ensure_ascii=False) + "\n"
        for record in records
    )
    return text.encode("utf-8")


def trace(*, session=SESSION, cwd=CWD, version=VERSION, skills=None, duplicate_init=False):
    init = {
        "type": "system",
        "subtype": "init",
        "cwd": cwd,
        "session_id": session,
        "skills": [SKILL] if skills is None else skills,
        "claude_code_version": version,
        "uuid": str(uuid.UUID(int=5)),
    }
    records = [
        {"type": "system", "subtype": "hook_started", "session_id": session,
         "uuid": str(uuid.UUID(int=6))},
        init,
        {"type": "system", "subtype": "thinking_tokens", "session_id": session,
         "uuid": str(uuid.UUID(int=7)), "estimated_tokens": 50},
    ]
    if duplicate_init:
        records.append(copy.deepcopy(init))
    return native_session_bytes(records)


def continuation_trace():
    first = json.loads(trace().splitlines()[1])
    first.update(model="claude-test", plugins=[], tools=["Skill"])
    tool_use_id = "toolu_background"
    task_id = "task-background"
    second = copy.deepcopy(first)
    second["uuid"] = str(uuid.UUID(int=15))
    return native_session_bytes([
        first,
        {"type": "assistant", "message": {"content": [{
            "type": "tool_use", "id": tool_use_id, "name": "Agent",
            "input": {"description": "Finish UAT", "run_in_background": True},
        }]}, "parent_tool_use_id": None, "session_id": SESSION,
         "uuid": str(uuid.UUID(int=8))},
        {"type": "system", "subtype": "task_started", "task_id": task_id,
         "tool_use_id": tool_use_id, "description": "Finish UAT",
         "is_backgrounded": True, "session_id": SESSION,
         "uuid": str(uuid.UUID(int=9))},
        {"type": "user", "message": {"content": [{
            "type": "tool_result", "tool_use_id": tool_use_id,
            "content": "Agent launched", "is_error": False,
        }]}, "parent_tool_use_id": None, "session_id": SESSION,
         "uuid": str(uuid.UUID(int=10))},
        {"type": "system", "subtype": "background_tasks_changed", "tasks": [],
         "session_id": SESSION, "uuid": str(uuid.UUID(int=11))},
        {"type": "system", "subtype": "task_updated", "task_id": task_id,
         "patch": {"status": "completed", "end_time": 1234},
         "session_id": SESSION, "uuid": str(uuid.UUID(int=12))},
        {"type": "system", "subtype": "task_notification", "task_id": task_id,
         "tool_use_id": tool_use_id, "status": "completed",
         "output_file": "/tmp/task.out", "summary": "UAT complete",
         "session_id": SESSION, "uuid": str(uuid.UUID(int=13))},
        second,
        {"type": "result", "subtype": "success", "is_error": False,
         "result": "waiting", "usage": {"input_tokens": 1, "output_tokens": 1},
         "session_id": SESSION, "uuid": str(uuid.UUID(int=16)), "result_index": 0},
        {"type": "result", "subtype": "success", "is_error": False,
         "result": "finished", "usage": {"input_tokens": 1, "output_tokens": 1},
         "session_id": SESSION, "uuid": str(uuid.UUID(int=17)), "result_index": 1,
         "origin": {"kind": "task-notification"}},
    ])


def command_content(arguments=ARGUMENTS):
    return (
        f"<command-message>{SKILL}</command-message>\n"
        f"<command-name>/{SKILL}</command-name>\n"
        f"<command-args>{arguments}</command-args>"
    )


def rendered(body=BODY, directory=DIRECTORY, arguments=ARGUMENTS):
    return (
        f"Base directory for this skill: {directory}\n".encode()
        + body + b"\n\nARGUMENTS: " + arguments.encode()
    ).decode()


def identity(*, record_uuid, parent, prompt_id=PROMPT_ID, session=SESSION,
             cwd=CWD, version=VERSION):
    return {
        "type": "user",
        "uuid": record_uuid,
        "parentUuid": parent,
        "sessionId": session,
        "promptId": prompt_id,
        "cwd": cwd,
        "version": version,
        "entrypoint": "sdk-cli",
        "userType": "external",
        "isSidechain": False,
        "timestamp": "2026-09-15T23:33:01.647Z",
    }


def records(*, arguments=ARGUMENTS, body=BODY, command_parent=None,
            injection_parent=COMMAND_ID, command_session=SESSION,
            injection_session=SESSION, command_version=VERSION,
            injection_version=VERSION, command_cwd=CWD, injection_cwd=CWD):
    command = identity(
        record_uuid=COMMAND_ID, parent=command_parent, session=command_session,
        cwd=command_cwd, version=command_version,
    )
    command["message"] = {"role": "user", "content": command_content(arguments)}
    injection = identity(
        record_uuid=INJECTION_ID, parent=injection_parent, session=injection_session,
        cwd=injection_cwd, version=injection_version,
    )
    injection["isMeta"] = True
    injection["message"] = {
        "role": "user", "content": [{"type": "text", "text": rendered(body=body,
            arguments=arguments)}],
    }
    return [
        {"type": "queue-operation", "operation": "enqueue", "timestamp": "2026-09-15T23:33:01Z"},
        {"type": "queue-operation", "operation": "dequeue", "timestamp": "2026-09-15T23:33:01Z"},
        command,
        injection,
        {"type": "assistant", "parentUuid": INJECTION_ID,
         "message": {"role": "assistant", "content": [{"type": "text", "text": "done"}]}},
    ]


def witness(**overrides):
    values = {
        "skill_name": SKILL,
        "prompt": PROMPT,
        "staged_skill": SKILL_BYTES,
        "staged_skill_directory": DIRECTORY,
        "raw_trace": trace(),
    }
    values.update(overrides)
    return build_activation_witness(**values)


class NativeClaudeActivationTests(unittest.TestCase):
    def test_static_native_command_and_direct_injection_are_proven(self):
        expected = witness()
        raw = native_session_bytes(records())

        receipt = parse_explicit_activation(raw, expected)

        self.assertEqual(receipt["authority"], AUTHORITY)
        self.assertEqual(receipt["skill"], SKILL)
        self.assertEqual(receipt["session_id"], SESSION)
        self.assertEqual(receipt["command_record"]["index"], 2)
        self.assertEqual(receipt["injection_record"]["index"], 3)
        self.assertEqual(receipt["injection_record"]["parent_uuid"], COMMAND_ID)
        self.assertEqual(receipt["session_artifact"]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertNotIn(PROMPT, json.dumps(receipt))
        self.assertNotIn(BODY.decode().strip(), json.dumps(receipt))

    def test_witness_binds_static_source_prompt_rendering_and_public_init(self):
        result = witness()

        self.assertEqual(result["trace"]["session_id"], SESSION)
        self.assertEqual(result["trace"]["cwd"], CWD)
        self.assertEqual(result["trace"]["cli_version"], VERSION)
        self.assertEqual(result["skill_source"]["body_sha256"], hashlib.sha256(BODY).hexdigest())
        self.assertEqual(result["arguments"]["sha256"], hashlib.sha256(ARGUMENTS.encode()).hexdigest())
        self.assertNotIn(PROMPT, json.dumps(result))
        self.assertNotIn(DIRECTORY, json.dumps(result))

    def test_witness_accepts_one_evidence_bound_continuation(self):
        result = witness(raw_trace=continuation_trace())

        self.assertEqual(result["trace"]["session_id"], SESSION)
        self.assertEqual(result["trace"]["cli_version"], VERSION)

    def test_witness_rejects_unbound_or_changed_continuation(self):
        for variation in ("missing-bridge", "foreign-bridge", "changed-init", "bad-origin"):
            with self.subTest(variation=variation):
                values = [json.loads(line) for line in continuation_trace().splitlines()]
                second = next(index for index, record in enumerate(values)
                              if record.get("uuid") == str(uuid.UUID(int=15)))
                if variation == "missing-bridge":
                    values.pop(second - 3)
                elif variation == "foreign-bridge":
                    values[second - 1]["session_id"] = str(uuid.UUID(int=70))
                elif variation == "changed-init":
                    values[second]["cwd"] = "/private/tmp/elsewhere"
                else:
                    values[-1]["origin"] = {"kind": "user-prompt"}
                with self.assertRaises(ClaudeActivationInvalid):
                    witness(raw_trace=native_session_bytes(values))

    def test_correct_outcome_and_slash_text_without_loader_pair_do_not_activate(self):
        expected = witness()
        ordinary = identity(record_uuid=COMMAND_ID, parent=None)
        ordinary["message"] = {"role": "user", "content": PROMPT}
        outcome = {"type": "assistant", "parentUuid": COMMAND_ID,
                   "message": {"role": "assistant", "content": "result.json is correct"}}

        for candidate in (native_session_bytes([ordinary]), native_session_bytes([ordinary, outcome]),
                          native_session_bytes(records()[:3])):
            with self.subTest(records=candidate.count(b"\n")):
                with self.assertRaises(ClaudeActivationInvalid):
                    parse_explicit_activation(candidate, expected)

    def test_wrong_prompt_parent_body_session_version_and_cwd_are_rejected(self):
        variations = {
            "prompt": records(arguments="Do a different task."),
            "command-parent": records(command_parent=str(uuid.UUID(int=20))),
            "injection-parent": records(injection_parent=str(uuid.UUID(int=21))),
            "body": records(body=b"\n# Altered body\n"),
            "command-session": records(command_session=str(uuid.UUID(int=22))),
            "injection-session": records(injection_session=str(uuid.UUID(int=23))),
            "command-version": records(command_version="2.1.272"),
            "injection-version": records(injection_version="2.1.272"),
            "command-cwd": records(command_cwd="/private/tmp/elsewhere"),
            "injection-cwd": records(injection_cwd="/private/tmp/elsewhere"),
        }
        for label, value in variations.items():
            with self.subTest(label=label):
                with self.assertRaises(ClaudeActivationInvalid):
                    parse_explicit_activation(native_session_bytes(value), witness())

    def test_duplicate_commands_injections_and_nonadjacent_pair_are_rejected(self):
        base = records()
        second_command = copy.deepcopy(base[2])
        second_command["uuid"] = str(uuid.UUID(int=30))
        second_injection = copy.deepcopy(base[3])
        second_injection["uuid"] = str(uuid.UUID(int=31))
        second_injection["parentUuid"] = second_command["uuid"]
        variants = {
            "second-pair": base + [second_command, second_injection],
            "second-child": base + [copy.deepcopy(base[3])],
            "unrelated-duplicate-uuid": base + [{"type": "attachment", "uuid": COMMAND_ID}],
            "nonadjacent": base[:3] + [{"type": "attachment", "uuid": str(uuid.UUID(int=32))}]
                           + base[3:],
        }
        for label, value in variants.items():
            with self.subTest(label=label):
                with self.assertRaises(ClaudeActivationInvalid):
                    parse_explicit_activation(native_session_bytes(value), witness())

    def test_duplicate_keys_truncation_blank_records_and_non_json_are_rejected(self):
        valid = native_session_bytes(records())
        variants = {
            "duplicate-key": b'{"type":"queue-operation","type":"user"}\n' + valid,
            "truncated": valid.rstrip(b"\n"),
            "blank": b"\n" + valid,
            "non-json": b"not-json\n" + valid,
        }
        for label, value in variants.items():
            with self.subTest(label=label):
                with self.assertRaises(ClaudeActivationInvalid):
                    parse_explicit_activation(value, witness())

    def test_session_byte_and_record_bounds_are_enforced(self):
        raw = native_session_bytes(records())
        controls = {
            "bytes": mock.patch.object(activation, "MAX_SESSION_BYTES", len(raw) - 1),
            "records": mock.patch.object(activation, "MAX_SESSION_RECORDS", 2),
        }
        for label, control in controls.items():
            with self.subTest(label=label), control:
                with self.assertRaises(ClaudeActivationInvalid):
                    parse_explicit_activation(raw, witness())

    def test_arbitrary_later_user_spoof_is_not_the_root_loader_command(self):
        prior = identity(record_uuid=str(uuid.UUID(int=40)), parent=None)
        prior["message"] = {"role": "user", "content": "ordinary first prompt"}

        with self.assertRaises(ClaudeActivationInvalid):
            parse_explicit_activation(native_session_bytes([prior] + records()[2:]), witness())

    def test_wrong_or_ambiguous_public_init_is_rejected(self):
        variants = {
            "missing-skill": trace(skills=["fixture-plugin:other"]),
            "duplicate-skill": trace(skills=[SKILL, SKILL]),
            "duplicate-init": trace(duplicate_init=True),
            "bad-session": trace(session="not-a-session"),
            "relative-cwd": trace(cwd="relative/workspace"),
            "bad-version": trace(version="version with spaces"),
            "truncated": trace()[:-2],
            "duplicate-key": b'{"type":"system","subtype":"init","subtype":"init"}\n',
        }
        for label, value in variants.items():
            with self.subTest(label=label):
                with self.assertRaises(ClaudeActivationInvalid):
                    witness(raw_trace=value)

    def test_prompt_skill_frontmatter_and_dynamic_rendering_are_fail_closed(self):
        variations = {
            "not-explicit": {"prompt": "Please use static-skill"},
            "wrong-name": {"staged_skill": SKILL_BYTES.replace(
                b"name: static-skill", b"name: other")},
            "model-invocable": {"staged_skill": SKILL_BYTES.replace(
                b"disable-model-invocation: true", b"disable-model-invocation: false")},
            "not-user-invocable": {"staged_skill": SKILL_BYTES.replace(
                b"user-invocable: true", b"user-invocable: false")},
            "arguments-substitution": {"staged_skill": SKILL_BYTES + b"\n$ARGUMENTS\n"},
            "command-substitution": {"staged_skill": SKILL_BYTES + b"\n!`date`\n"},
            "wrong-directory": {"staged_skill_directory": "/private/tmp/native-activation/other"},
        }
        for label, values in variations.items():
            with self.subTest(label=label):
                with self.assertRaises(ClaudeActivationInvalid):
                    witness(**values)

    def test_regrade_uses_saved_raw_session_and_witness_only(self):
        expected = json.loads(json.dumps(witness()))
        retained_raw = bytes(native_session_bytes(records()))

        first = parse_explicit_activation(retained_raw, expected)
        second = parse_explicit_activation(retained_raw, expected)

        self.assertEqual(first, second)
        self.assertEqual(first["witness_sha256"], second["witness_sha256"])

    @unittest.skipUnless(
        os.name == "posix" and hasattr(os, "O_NOFOLLOW") and os.open in os.supports_dir_fd,
        "requires POSIX descriptor-relative collection",
    )
    def test_collector_returns_only_exact_owned_session_bytes(self):
        expected = witness()
        raw = native_session_bytes(records())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            projects = root / "config" / "projects"
            project = projects / "-private-tmp-native-activation-home-cwd"
            project.mkdir(parents=True)
            (project / f"{SESSION}.jsonl").write_bytes(raw)
            (project / SESSION).mkdir()
            other = projects / "-private-tmp-native-activation-home"
            (other / "memory").mkdir(parents=True)
            (project / f"{uuid.UUID(int=50)}.jsonl").write_text("unrelated\n")

            self.assertEqual(collect_retained_session(root, expected), raw)

    @unittest.skipUnless(
        os.name == "posix" and hasattr(os, "O_NOFOLLOW") and os.open in os.supports_dir_fd,
        "requires POSIX descriptor-relative collection",
    )
    def test_collector_missing_session_is_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config" / "projects" / "project").mkdir(parents=True)

            with self.assertRaises(ClaudeActivationUnavailable):
                collect_retained_session(root, witness())

    @unittest.skipUnless(
        os.name == "posix" and hasattr(os, "O_NOFOLLOW") and os.open in os.supports_dir_fd,
        "requires POSIX descriptor-relative collection",
    )
    def test_collector_project_and_entry_bounds_are_enforced(self):
        for label, limit_name in (("projects", "MAX_PROJECT_DIRECTORIES"),
                                  ("entries", "MAX_PROJECT_ENTRIES")):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                projects = root / "config" / "projects"
                project = projects / "project"
                project.mkdir(parents=True)
                (project / f"{SESSION}.jsonl").write_bytes(native_session_bytes(records()))
                if label == "projects":
                    (projects / "second-project").mkdir()
                    limit = 1
                else:
                    (project / "unrelated.jsonl").write_text("{}\n")
                    limit = 1
                with mock.patch.object(activation, limit_name, limit):
                    with self.assertRaises(ClaudeActivationInvalid):
                        collect_retained_session(root, witness())

    @unittest.skipUnless(
        os.name == "posix" and hasattr(os, "O_NOFOLLOW") and os.open in os.supports_dir_fd,
        "requires POSIX descriptor-relative collection",
    )
    def test_collector_rejects_symlinks_duplicates_and_special_entries(self):
        for variation in ("target-symlink", "project-symlink", "hardlink", "duplicate", "fifo"):
            with self.subTest(variation=variation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                projects = root / "config" / "projects"
                project = projects / "project"
                project.mkdir(parents=True)
                target = project / f"{SESSION}.jsonl"
                raw = native_session_bytes(records())
                if variation == "target-symlink":
                    backing = root / "backing.jsonl"
                    backing.write_bytes(raw)
                    target.symlink_to(backing)
                elif variation == "hardlink":
                    backing = root / "backing.jsonl"
                    backing.write_bytes(raw)
                    os.link(backing, target)
                else:
                    target.write_bytes(raw)
                if variation == "project-symlink":
                    (projects / "alias").symlink_to(project, target_is_directory=True)
                elif variation == "duplicate":
                    duplicate = projects / "duplicate"
                    duplicate.mkdir()
                    (duplicate / target.name).write_bytes(raw)
                elif variation == "fifo":
                    os.mkfifo(project / "unexpected")

                with self.assertRaises(ClaudeActivationInvalid):
                    collect_retained_session(root, witness())

    def test_witness_tampering_and_wrong_session_filename_content_are_rejected(self):
        expected = witness()
        for field in ("sha256", "bytes"):
            altered = copy.deepcopy(expected)
            altered["rendered_injection"][field] = (
                "0" * 64 if field == "sha256" else altered["rendered_injection"][field] + 1
            )
            with self.subTest(field=field):
                with self.assertRaises(ClaudeActivationInvalid):
                    parse_explicit_activation(native_session_bytes(records()), altered)
        with self.assertRaises(ClaudeActivationInvalid):
            parse_explicit_activation(
                native_session_bytes(records(command_session=str(uuid.UUID(int=60)),
                                             injection_session=str(uuid.UUID(int=60)))), expected,
            )


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeClaudeActivationTests),
        label="test-native-eval-claude-activation",
    ))
