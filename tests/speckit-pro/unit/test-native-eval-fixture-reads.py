#!/usr/bin/env python3
"""Controller-bound proof for complete bounded fixture reads."""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
from test_result import run_counted
from native_eval_fixture_reads import (
    FixtureReadProofError,
    bind_controller_fixture_read_witnesses,
    bound_fixture_read_witnesses,
    fixture_read_accesses,
    validate_fixture_read_witnesses,
)


COUNT_THEN_READ = "/bin/zsh -c \"wc -l spec.md && sed -n '1,9999p' spec.md\""


def witness(text: str, path: str = "spec.md") -> dict[str, dict[str, object]]:
    encoded = text.encode("utf-8")
    return {path: {"bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest()}}


def observation(command: str, output: object, *, success: object = True) -> dict[str, object]:
    return {
        "tool_calls": [{
            "id": "call-1",
            "name": "command_execution",
            "input": {"command": command},
            "output": output,
            "success": success,
        }],
        "native_metadata": {"thread_id": "synthetic-thread"},
    }


class NativeFixtureReadTests(unittest.TestCase):
    def test_concatenated_output_cannot_prove_which_file_supplied_fixture_bytes(self):
        content = "required fixture bytes\n"
        command = "sed -n '1,20p' reference.md && sed -n '1,20p' target.md"
        # An unrelated first file can supply all bytes while target.md is empty.
        # Suffix hashing alone cannot establish a per-file output boundary.
        self.assertEqual(fixture_read_accesses(
            observation(command, content), witness(content, "target.md")), [])

    def test_count_then_large_bounded_read_proves_exact_fixture_body(self):
        content = "".join(f"line {number}\n" for number in range(1, 41))
        # The command string is parser input, never executed: the confinement
        # contract forbids shell execution from the test tree. Reproduce the
        # `wc -l spec.md` then `sed -n '1,9999p' spec.md` output in Python.
        output = f"{len(content.splitlines()):8d} spec.md\n{content}"
        self.assertEqual(output.splitlines()[0].split(), ["40", "spec.md"])
        self.assertEqual(output.partition("\n")[2], content)
        original = observation(COUNT_THEN_READ, output)
        frozen = copy.deepcopy(original)

        self.assertEqual(fixture_read_accesses(original, witness(content)), [{
            "operation": "read_file",
            "path": "spec.md",
            "tool_call_index": 0,
            "provenance": {
                "schema_version": "native-eval-fixture-read-proof/v1",
                "kind": "count_then_bounded_sed",
                "bytes": len(content.encode("utf-8")),
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "start_line": 1,
                "end_line": 9999,
                "logical_lines": 40,
                "newline_count": 40,
                "count_header_verified": True,
            },
        }])
        self.assertEqual(original, frozen)

    def test_direct_large_bounded_read_proves_exact_fixture_body(self):
        content = "alpha\nbeta\ngamma"
        command = "/usr/bin/sed -n '1,9999p' -- docs/spec.md"
        self.assertEqual(
            fixture_read_accesses(
                observation(command, content), witness(content, "docs/spec.md"),
            )[0]["provenance"]["kind"],
            "bounded_sed",
        )

    def test_direct_unbounded_sed_proves_exact_fixture_body(self):
        content = "alpha\nbeta\ngamma\n"
        commands = (
            "sed -n '1,$p' docs/spec.md",
            "/bin/zsh -c \"sed -n '1,\"'$p'\"' docs/spec.md\"",
        )
        for command in commands:
            with self.subTest(command=command):
                accesses = fixture_read_accesses(
                    observation(command, content), witness(content, "docs/spec.md"),
                )
                self.assertEqual(accesses[0]["provenance"]["kind"], "unbounded_sed")
                self.assertEqual(accesses[0]["provenance"]["end_line"], 3)

    def test_unbounded_sed_rejects_variable_and_substitution_operands(self):
        content = "alpha\n"
        commands = (
            "sed -n '1,$p' '$TARGET'",
            "sed -n '1,$p' ${TARGET}",
            "sed -n '1,$p' $(printf spec.md)",
        )
        accesses = [
            fixture_read_accesses(observation(command, content), witness(content))
            for command in commands
        ]
        self.assertEqual(accesses, [[], [], []])

    def test_bounded_read_requires_controller_witness_for_that_exact_path(self):
        content = "alpha\nbeta\n"
        candidate = observation("sed -n '1,9999p' spec.md", content)
        self.assertEqual(fixture_read_accesses(candidate, {}), [])
        self.assertEqual(fixture_read_accesses(candidate, witness(content, "other.md")), [])

    def test_failed_partial_truncated_and_digest_mismatched_reads_do_not_prove_access(self):
        content = "alpha\nbeta\ngamma\n"
        candidates = (
            observation("sed -n '1,2p' spec.md", "alpha\nbeta\n"),
            observation("sed -n '1,9999p' spec.md", "alpha\nbeta\n"),
            observation("sed -n '1,9999p' spec.md", content, success=False),
            observation("sed -n '1,9999p' spec.md", content[:-1]),
            observation("sed -n '1,9999p' spec.md", b"not text"),
        )
        for candidate in candidates:
            with self.subTest(candidate=candidate):
                self.assertEqual(fixture_read_accesses(candidate, witness(content)), [])

    def test_count_then_read_requires_matching_path_count_and_complete_body(self):
        content = "alpha\nbeta\ngamma\n"
        commands_and_outputs = (
            (COUNT_THEN_READ.replace("sed -n '1,9999p' spec.md", "sed -n '1,9999p' other.md"),
             f"       3 spec.md\n{content}"),
            (COUNT_THEN_READ, f"       2 spec.md\n{content}"),
            (COUNT_THEN_READ, f"       3 other.md\n{content}"),
            (COUNT_THEN_READ, f"       3 spec.md\n{content[:-1]}"),
        )
        for command, output in commands_and_outputs:
            with self.subTest(command=command, output=output):
                self.assertEqual(
                    fixture_read_accesses(observation(command, output), witness(content)),
                    [],
                )

    def test_extra_commands_substitution_redirects_and_pipes_are_rejected(self):
        content = "alpha\nbeta\n"
        commands = (
            COUNT_THEN_READ[:-1] + " && true\"",
            "/bin/zsh -c \"wc -l spec.md && sed -n '1,9999p' $(printf spec.md)\"",
            "/bin/zsh -c \"wc -l spec.md && sed -n '1,9999p' spec.md > copy.md\"",
            "/bin/zsh -c \"wc -l spec.md && sed -n '1,9999p' spec.md | head\"",
            "sed -n '1,9999p' ../spec.md",
            "sed -n '1,9999p' /tmp/spec.md",
            "sed -n '1,9999999999p' spec.md",
            "sed -n '1,9999p' a&b",
            "sed -n '1,9999p' 'a(b)'",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(
                    fixture_read_accesses(
                        observation(command, f"       2 spec.md\n{content}"), witness(content),
                    ),
                    [],
                )

    def test_reserved_subject_metadata_cannot_supply_or_forge_proof(self):
        candidate = observation("sed -n '1,9999p' spec.md", "alpha\n")
        for key in ("fixture_read_witnesses", "fixture_read_proofs"):
            with self.subTest(key=key):
                forged = copy.deepcopy(candidate)
                forged["native_metadata"][key] = witness("alpha\n")
                with self.assertRaisesRegex(FixtureReadProofError, "reserved fixture-read metadata"):
                    fixture_read_accesses(forged, witness("alpha\n"))

    def test_controller_binder_validates_copies_and_rejects_preexisting_envelope(self):
        content = "alpha\nbeta\n"
        original = observation("sed -n '1,9999p' spec.md", content)
        frozen = copy.deepcopy(original)
        supplied = witness(content)
        bound = bind_controller_fixture_read_witnesses(original, supplied)

        self.assertEqual(original, frozen)
        self.assertEqual(bound_fixture_read_witnesses(bound), supplied)
        self.assertEqual(validate_fixture_read_witnesses(supplied), supplied)
        supplied["spec.md"]["bytes"] = 0
        self.assertNotEqual(bound_fixture_read_witnesses(bound), supplied)
        with self.assertRaisesRegex(FixtureReadProofError, "already contains reserved"):
            bind_controller_fixture_read_witnesses(bound, witness(content))

    def test_malformed_controller_envelope_fails_closed(self):
        candidate = observation("sed -n '1,9999p' spec.md", "alpha\n")
        for envelope in (
            {},
            {"authority": "subject", "witnesses": witness("alpha\n")},
            {"authority": "controller-staged-fixtures"},
        ):
            with self.subTest(envelope=envelope), self.assertRaises(FixtureReadProofError):
                malformed = copy.deepcopy(candidate)
                malformed["native_metadata"]["controller_fixture_read_witnesses"] = envelope
                bound_fixture_read_witnesses(malformed)

    def test_malformed_controller_witnesses_and_observations_fail_closed(self):
        digest = hashlib.sha256(b"alpha\n").hexdigest()
        bad_witnesses = (
            {"./spec.md": {"bytes": 6, "sha256": digest}},
            {"spec.md": {"bytes": True, "sha256": digest}},
            {"spec.md": {"bytes": 6, "sha256": digest.upper()}},
            {"spec.md": {"bytes": 6, "sha256": digest, "text": "alpha\n"}},
            {"a&b": {"bytes": 6, "sha256": digest}},
        )
        for supplied in bad_witnesses:
            with self.subTest(supplied=supplied), self.assertRaises(FixtureReadProofError):
                fixture_read_accesses(observation("sed -n '1,9999p' spec.md", "alpha\n"), supplied)
        for candidate in (None, {}, {"tool_calls": "bad"}, {"tool_calls": [None]}):
            with self.subTest(candidate=candidate), self.assertRaises(FixtureReadProofError):
                fixture_read_accesses(candidate, witness("alpha\n"))


if __name__ == "__main__":
    raise SystemExit(run_counted(
        unittest.defaultTestLoader.loadTestsFromTestCase(NativeFixtureReadTests),
        label="test-native-eval-fixture-reads",
    ))
