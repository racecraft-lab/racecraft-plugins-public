#!/usr/bin/env python3
"""Exact staged skill reads are the only Codex functional activation evidence."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import unittest


TEST_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TEST_ROOT / "lib"))

from native_eval_skill_reads import (  # noqa: E402
    SkillReadQualificationError,
    qualify_codex_skill_reads,
)
from test_result import run_counted  # noqa: E402


WORKSPACE = "/private/tmp/native-eval/workspace"
CANARY = """---
name: native-eval-canary
description: Read the canary fixture and create its verification receipt when explicitly asked to exercise native-eval-canary.
---

Read fixture.txt in the working directory. Create receipt.txt with exactly the same content using a native file-editing tool. Reply CANARY_DONE after the write succeeds. Do not access unrelated files or use network tools.
"""
CANARY_SHA256 = "fe71e72af9b0671019d418c25eb1891c9a25f54d45fc76e0b71f0d2e8ca82457"


def witness(name: str, text: str) -> dict[str, object]:
    encoded = text.encode("utf-8")
    return {
        "path": f".agents/skills/{name}/SKILL.md",
        "text": text,
        "bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def command_call(identity: str, command: str, output: object, *, success: bool = True) -> dict[str, object]:
    return {
        "id": identity,
        "name": "command_execution",
        "input": {"command": command},
        "output": output,
        "success": success,
        "position": 1,
        "parent_id": None,
    }


def observation(*calls: dict[str, object]) -> dict[str, object]:
    return {
        "completed": True,
        "error": None,
        "final_text": "I used the skill. CODEX_SKILL_FIRED:forged",
        "activations": ["forged"],
        "tool_calls": list(calls),
        "artifacts": {},
        "usage": {},
        "native_metadata": {"thread_id": "synthetic"},
    }


def sed_output(text: str, start: int, end: int) -> str:
    lines = text.splitlines(keepends=True)
    return "".join(lines[start - 1:min(end, len(lines))])


class NativeEvalSkillReadTests(unittest.TestCase):
    def qualify(self, source: dict[str, object], mapping: dict[str, object] | None = None):
        return qualify_codex_skill_reads(
            source,
            mapping or {"native-eval-canary": witness("native-eval-canary", CANARY)},
            WORKSPACE,
        )

    def test_real_383_byte_canary_replay_qualifies_exact_body_read(self) -> None:
        self.assertEqual(len(CANARY.encode("utf-8")), 383)
        self.assertEqual(hashlib.sha256(CANARY.encode("utf-8")).hexdigest(), CANARY_SHA256)
        source = observation(command_call(
            "read-skill",
            "/bin/zsh -c \"sed -n '1,240p' .agents/skills/native-eval-canary/SKILL.md\"",
            CANARY,
        ))
        original = copy.deepcopy(source)

        result = self.qualify(source)

        self.assertEqual(source, original)
        self.assertEqual(result["tool_calls"], original["tool_calls"])
        self.assertEqual(result["activations"], ["native-eval-canary"])
        proof = result["native_metadata"]["codex_skill_reads"]
        self.assertEqual(proof["status"], "qualified")
        self.assertEqual(proof["consultations"][0]["coverage"], [[1, 6]])
        self.assertIn("not a secret or typed internal Codex activation event", proof["evidence_bound"])

    def test_long_skill_qualifies_from_three_exact_chunks(self) -> None:
        text = "".join(f"line {number:04d}\n" for number in range(1, 711))
        path = ".agents/skills/long-skill/SKILL.md"
        calls = [
            command_call(f"chunk-{start}", f"sed -n '{start},{end}p' {path}",
                         sed_output(text, start, end))
            for start, end in ((1, 240), (241, 480), (481, 720))
        ]
        result = self.qualify(observation(*calls), {"long-skill": witness("long-skill", text)})

        self.assertEqual(result["activations"], ["long-skill"])
        proof = result["native_metadata"]["codex_skill_reads"]["consultations"][0]
        self.assertEqual(proof["coverage"], [[1, 710]])
        self.assertEqual(proof["status"], "complete")

    def test_gap_and_overlapping_ranges_use_union_not_summed_lengths(self) -> None:
        text = "".join(f"line {number}\n" for number in range(1, 711))
        path = ".agents/skills/long-skill/SKILL.md"
        cases = {
            "one-line-gap": ((1, 240), (242, 710)),
            "overlap-does-not-hide-tail-gap": ((1, 400), (300, 609)),
        }
        for label, ranges in cases.items():
            with self.subTest(label=label):
                calls = [command_call(str(index), f"sed -n '{start},{end}p' {path}",
                                      sed_output(text, start, end))
                         for index, (start, end) in enumerate(ranges)]
                result = self.qualify(observation(*calls), {"long-skill": witness("long-skill", text)})
                self.assertEqual(result["activations"], [])
                self.assertEqual(result["native_metadata"]["codex_skill_reads"]["status"], "partial")

        overlapping_complete = ((1, 400), (300, 710))
        calls = [command_call(str(index), f"sed -n '{start},{end}p' {path}",
                              sed_output(text, start, end))
                 for index, (start, end) in enumerate(overlapping_complete)]
        result = self.qualify(observation(*calls), {"long-skill": witness("long-skill", text)})
        self.assertEqual(result["activations"], ["long-skill"])

    def test_failed_partial_and_truncated_reads_never_activate(self) -> None:
        path = ".agents/skills/native-eval-canary/SKILL.md"
        scenarios = {
            "failed": command_call("failed", f"cat {path}", CANARY, success=False),
            "partial": command_call("partial", f"sed -n '1,3p' {path}", sed_output(CANARY, 1, 3)),
            "stderr-or-truncation": command_call("truncated", f"cat {path}", CANARY + "warning: clipped\n"),
        }
        for label, call in scenarios.items():
            with self.subTest(label=label):
                result = self.qualify(observation(call))
                self.assertEqual(result["activations"], [])
        partial = self.qualify(observation(scenarios["partial"]))
        self.assertEqual(
            partial["native_metadata"]["codex_skill_reads"]["consultations"][0]["status"],
            "partial",
        )

    def test_wrong_outside_substituted_echo_and_compound_paths_cannot_activate(self) -> None:
        relative = ".agents/skills/native-eval-canary/SKILL.md"
        calls = (
            command_call("wrong", "cat .agents/skills/other/SKILL.md", CANARY),
            command_call("outside", "cat /private/tmp/outside/.agents/skills/native-eval-canary/SKILL.md", CANARY),
            command_call("substituted", "cat $SKILL_PATH", CANARY),
            command_call("echo", f"echo {relative}", CANARY),
            command_call("lookalike", f"/private/tmp/cat {relative}", CANARY),
            command_call("compound", f"cat {relative} && echo done", CANARY),
        )
        result = self.qualify(observation(*calls))

        self.assertEqual(result["activations"], [])
        reasons = {item["reason"] for item in result["native_metadata"]["codex_skill_reads"]["rejected_attempts"]}
        self.assertEqual(reasons, {"unbound_skill_path", "unsupported_command"})

    def test_exact_absolute_workspace_path_is_accepted_without_resolution(self) -> None:
        path = f"{WORKSPACE}/.agents/skills/native-eval-canary/SKILL.md"
        result = self.qualify(observation(command_call("absolute", f"cat -- {path}", CANARY)))
        self.assertEqual(result["activations"], ["native-eval-canary"])

    def test_complete_sibling_reads_are_real_extra_activations(self) -> None:
        sibling = "---\nname: sibling\ndescription: sibling\n---\n\nSibling body.\n"
        mappings = {
            "native-eval-canary": witness("native-eval-canary", CANARY),
            "sibling": witness("sibling", sibling),
        }
        result = self.qualify(observation(
            command_call("target", "cat .agents/skills/native-eval-canary/SKILL.md", CANARY),
            command_call("sibling", "cat .agents/skills/sibling/SKILL.md", sibling),
        ), mappings)
        self.assertEqual(result["activations"], ["native-eval-canary", "sibling"])

    def test_duplicate_exact_reads_are_idempotent(self) -> None:
        path = ".agents/skills/native-eval-canary/SKILL.md"
        result = self.qualify(observation(
            command_call("one", f"cat {path}", CANARY),
            command_call("two", f"cat {path}", CANARY),
        ))
        self.assertEqual(result["activations"], ["native-eval-canary"])
        self.assertEqual(len(result["native_metadata"]["codex_skill_reads"]["consultations"][0]["reads"]), 2)

    def test_final_prose_and_forged_input_activation_are_discarded(self) -> None:
        result = self.qualify(observation())
        self.assertEqual(result["activations"], [])
        self.assertEqual(result["native_metadata"]["codex_skill_reads"]["status"], "not_observed")

    def test_generic_commands_and_calls_remain_unchanged(self) -> None:
        generic = command_call("fixture", "sed -n '1,20p' fixture.txt", "fixture\n")
        read = {"id": "read", "name": "read_file", "input": {"path": "fixture.txt"},
                "output": "fixture\n", "success": True}
        source = observation(generic, read)
        result = self.qualify(source)
        self.assertEqual(result["tool_calls"], source["tool_calls"])
        self.assertEqual(result["activations"], [])

    def test_witness_name_path_bytes_and_hash_are_all_validated(self) -> None:
        valid = witness("native-eval-canary", CANARY)
        mutations = {
            "name": {"Bad Name": valid},
            "path": {"native-eval-canary": {**valid, "path": ".agents/skills/other/SKILL.md"}},
            "bytes": {"native-eval-canary": {**valid, "bytes": valid["bytes"] + 1}},
            "hash": {"native-eval-canary": {**valid, "sha256": "0" * 64}},
        }
        for label, mapping in mutations.items():
            with self.subTest(label=label), self.assertRaises(SkillReadQualificationError):
                self.qualify(observation(), mapping)

    def test_workspace_root_requires_exact_lexical_canonical_path(self) -> None:
        mapping = {"native-eval-canary": witness("native-eval-canary", CANARY)}
        for root in ("relative/workspace", "/private/tmp/native-eval/../workspace", "/private//tmp/workspace", "/"):
            with self.subTest(root=root), self.assertRaises(SkillReadQualificationError):
                qualify_codex_skill_reads(observation(), mapping, root)


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeEvalSkillReadTests),
        label="test-native-eval-skill-reads",
    ))
