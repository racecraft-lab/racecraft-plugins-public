#!/usr/bin/env python3
"""Layer-4 contracts for the Python Layer-6 efficiency runner.

Port target for ``test-l6-codex-runner.sh`` (XPLAT-010 PR9 T084 half).
The shell predecessor reported 23 assertions; this Python port preserves that
count with explicit, ordered subTest names pinned in the parity baseline.
"""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LAYER6 = TESTS_ROOT / "layer6-efficiency"
RUNNER = LAYER6 / "run-efficiency-benchmarks.py"
TOKEN_COUNTER = LAYER6 / "lib" / "token-counter.py"
QUALITY_SCORER = LAYER6 / "lib" / "quality-scorer.py"
BASELINE = TESTS_ROOT / "parity" / "xplat-010" / "test-l6-codex-runner-baseline.txt"
SHARED_LIB = TESTS_ROOT / "lib"
if str(SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(SHARED_LIB))

from test_result import run_counted  # noqa: E402


CURRENT_INVENTORY = [
    *["extracts the heredoc body, drops opening and closing markers"] * 4,
    *["leaves other TOML fields out of the body"] * 2,
    *["Runner --codex --agent stub-agent --sweep produces results JSON with 4 records"] * 6,
    "Results JSON contains 4 records (one per effort level)",
    *["Each record has the expected agent + non-zero token count"] * 2,
    *["Records carry the effort label in the model field"] * 4,
    *["Runner exits 1 with clear error when CODEX_BIN is missing"] * 2,
    *[
        "Runner with no --codex flag still uses claude "
        "(verified via fast-fail when claude is unavailable)"
    ]
    * 2,
]


def import_script(path: Path, name: str) -> ModuleType | None:
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def baseline_inventory(path: Path) -> list[str]:
    names: list[str] = []
    total: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("TOTAL: "):
            total = int(line.removeprefix("TOTAL: "))
            continue
        _ordinal, name = line.split(" ", 1)
        names.append(name)
    if total != len(names):
        raise AssertionError(f"baseline TOTAL {total} does not match {len(names)} names")
    return names


def run_runner(*args: str, env_overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
        shell=False,
        check=False,
    )


def run_script(path: Path, *args: str, input_text: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(path), *args],
        cwd=REPO_ROOT,
        text=True,
        input=input_text,
        capture_output=True,
        env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1"},
        shell=False,
        check=False,
    )


def write_python_executable(path: Path, source: str) -> None:
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    path.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)


def make_codex_stub(path: Path) -> Path:
    script_path = path if os.name != "nt" else path.with_name("codex-stub.py")
    write_python_executable(
        script_path,
        """\
        #!/usr/bin/env python3
        import json
        import os
        import sys
        from pathlib import Path

        argv = sys.argv[1:]
        out_file = ""
        effort = ""
        index = 0
        while index < len(argv):
            current = argv[index]
            if current == "-o" and index + 1 < len(argv):
                out_file = argv[index + 1]
                index += 2
                continue
            if current == "-c" and index + 1 < len(argv):
                value = argv[index + 1]
                if value.startswith("model_reasoning_effort="):
                    effort = value.split("=", 1)[1]
                index += 2
                continue
            index += 1

        prompt = sys.stdin.read()
        with Path(os.environ["CODEX_STUB_LOG"]).open("a", encoding="utf-8") as log:
            log.write(json.dumps({
                "argv": argv,
                "effort": effort,
                "has_output_file": bool(out_file),
                "prompt_contains_agent": "stub agent for testing" in prompt,
                "prompt_contains_input": "Return any answer." in prompt,
            }, sort_keys=True) + "\\n")

        if out_file:
            Path(out_file).write_text(f'''## Answer

        Mock answer at effort={effort}.

        ## Evidence

        - mock evidence from Python codex stub

        ## Confidence

        high
        ''', encoding="utf-8")

        print(json.dumps({
            "type": "turn.completed",
            "usage": {
                "input_tokens": 1000,
                "cached_input_tokens": 200,
                "output_tokens": 50,
                "reasoning_output_tokens": 30,
            },
        }))
        """,
    )
    if os.name != "nt":
        return script_path
    command_path = path.with_suffix(".cmd")
    command_path.write_text(
        "@echo off\r\n"
        + subprocess.list2cmdline([sys.executable, str(script_path)])
        + " %*\r\nexit /b %ERRORLEVEL%\r\n",
        encoding="utf-8",
    )
    return command_path


class Layer6CodexRunnerTests(unittest.TestCase):
    def test_layer6_codex_runner_contract(self) -> None:
        runner = import_script(RUNNER, "l6_efficiency_runner")
        scorer = import_script(QUALITY_SCORER, "l6_quality_scorer")
        counter = import_script(TOKEN_COUNTER, "l6_token_counter")
        assigned_source = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (RUNNER, QUALITY_SCORER, TOKEN_COUNTER)
            if path.is_file()
        )

        direct_tokens = run_script(
            TOKEN_COUNTER,
            input_text=json.dumps(
                {
                    "usage": {
                        "input_tokens": 3,
                        "output_tokens": 4,
                        "cache_read_input_tokens": 5,
                        "cache_creation_input_tokens": 2,
                    }
                }
            ),
        )
        nested_tokens = run_script(
            TOKEN_COUNTER,
            input_text=json.dumps(
                {
                    "result": {
                        "usage": {
                            "input_tokens": 7,
                            "output_tokens": 11,
                            "cache_read_input_tokens": 13,
                            "cache_creation_input_tokens": 17,
                        }
                    }
                }
            ),
        )
        invalid_tokens = run_script(TOKEN_COUNTER, input_text="not-json")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actual = root / "actual.md"
            expected = root / "expected.md"
            actual.write_text(
                "## Answer\n\n- alpha beta gamma\n\n## Evidence\n\n- matching phrase here\n",
                encoding="utf-8",
            )
            expected.write_text(
                "## Answer\n\n- alpha beta gamma\n\n## Evidence\n\n- matching phrase here\n",
                encoding="utf-8",
            )
            missing_quality = run_script(QUALITY_SCORER, str(root / "missing.md"), str(expected))
            matching_quality = run_script(QUALITY_SCORER, str(actual), str(expected))

            toml_file = root / "syn-agent.toml"
            toml_file.write_text(
                textwrap.dedent(
                    '''\
                    name = "syn-agent"
                    model = "gpt-5.5"
                    developer_instructions = """
                    # Synthetic Agent

                    Body line A.
                    Body line B.
                    """
                    '''
                ),
                encoding="utf-8",
            )
            body = runner.extract_codex_agent_body(toml_file) if runner is not None else ""

            fake_plugin = root / "fake-plugin"
            fake_fixtures = root / "fixtures-codex"
            fake_results = root / "results-codex"
            (fake_plugin / "codex-agents").mkdir(parents=True)
            (fake_fixtures / "stub-agent").mkdir(parents=True)
            fake_results.mkdir()
            (fake_plugin / "codex-agents" / "stub-agent.toml").write_text(
                textwrap.dedent(
                    '''\
                    name = "stub-agent"
                    model = "gpt-5.5"
                    model_reasoning_effort = "xhigh"
                    developer_instructions = """
                    You are a stub agent for testing.
                    """
                    '''
                ),
                encoding="utf-8",
            )
            (fake_fixtures / "stub-agent" / "input-prompt.md").write_text(
                "## Stub Input\n\nReturn any answer.\n",
                encoding="utf-8",
            )
            (fake_fixtures / "stub-agent" / "expected-output.md").write_text(
                textwrap.dedent(
                    """\
                    ## Answer

                    Mock answer.

                    ## Evidence

                    - mock evidence from Python codex stub

                    ## Confidence

                    high
                    """
                ),
                encoding="utf-8",
            )
            codex_stub = root / "codex"
            codex_log = root / "codex-calls.jsonl"
            codex_stub = make_codex_stub(codex_stub)
            env = {
                "PLUGIN_ROOT": str(fake_plugin),
                "CODEX_BIN": str(codex_stub),
                "L6_FIXTURES_DIR": str(fake_fixtures),
                "L6_RESULTS_DIR": str(fake_results),
                "CODEX_STUB_LOG": str(codex_log),
            }
            sweep = run_runner("--codex", "--agent", "stub-agent", "--sweep", env_overrides=env)
            result_lines = [
                line.removeprefix("Results saved to: ").strip()
                for line in sweep.stdout.splitlines()
                if line.startswith("Results saved to: ")
            ]
            results_file = Path(result_lines[-1]) if result_lines else root / "missing-results.json"
            results = json.loads(results_file.read_text(encoding="utf-8")) if results_file.is_file() else []
            logs = [json.loads(line) for line in codex_log.read_text(encoding="utf-8").splitlines()] if codex_log.is_file() else []

            missing_codex = run_runner(
                "--codex",
                env_overrides=env | {"CODEX_BIN": f"/no/such/bin/{os.getpid()}"},
            )
            sweep_error_results = root / "sweep-error-results"
            sweep_error_results.mkdir()
            sweep_without_agent = run_runner(
                "--codex",
                "--sweep",
                env_overrides=env | {"L6_RESULTS_DIR": str(sweep_error_results)},
            )
            sweep_error_files = list(sweep_error_results.glob("*.json"))
            no_claude_path = root / "empty-path"
            no_claude_path.mkdir()
            claude_default = run_runner(env_overrides=env | {"PATH": str(no_claude_path)})

            self.assertEqual(baseline_inventory(BASELINE), CURRENT_INVENTORY)
            models = [record["model"] for record in results]
            checks = [
                (CURRENT_INVENTORY[0], lambda: self.assertIn("Body line A.", body)),
                (CURRENT_INVENTORY[1], lambda: self.assertIn("Body line B.", body)),
                (CURRENT_INVENTORY[2], lambda: self.assertNotIn("developer_instructions", body)),
                (CURRENT_INVENTORY[3], lambda: self.assertNotIn('"""', body)),
                (CURRENT_INVENTORY[4], lambda: self.assertNotIn("gpt-5.5", body)),
                (CURRENT_INVENTORY[5], lambda: self.assertNotIn("name =", body)),
                (
                    CURRENT_INVENTORY[6],
                    lambda: self.assertTrue(
                        runner is not None
                        and scorer is not None
                        and counter is not None
                        and "shell=True" not in assigned_source
                        and "os.system" not in assigned_source
                        and "jq" not in assigned_source
                        and sweep.returncode == 0,
                        sweep.stdout + sweep.stderr,
                    ),
                ),
                (
                    CURRENT_INVENTORY[7],
                    lambda: self.assertIn("Sweep mode: testing stub-agent across 4 effort levels", sweep.stdout),
                ),
                (CURRENT_INVENTORY[8], lambda: self.assertIn("effort=xhigh", sweep.stdout)),
                (CURRENT_INVENTORY[9], lambda: self.assertIn("effort=high", sweep.stdout)),
                (CURRENT_INVENTORY[10], lambda: self.assertIn("effort=medium", sweep.stdout)),
                (
                    CURRENT_INVENTORY[11],
                    lambda: self.assertTrue(
                        "effort=low" in sweep.stdout
                        and results_file.is_file()
                        and all(log["argv"][0] == "exec" for log in logs)
                        and all(log["has_output_file"] for log in logs)
                        and all(log["prompt_contains_agent"] and log["prompt_contains_input"] for log in logs)
                    ),
                ),
                (CURRENT_INVENTORY[12], lambda: self.assertEqual(len(results), 4)),
                (
                    CURRENT_INVENTORY[13],
                    lambda: self.assertTrue(
                        {record["agent"] for record in results} == {"stub-agent"}
                        and json.loads(direct_tokens.stdout)["total_tokens"] == 14
                        and json.loads(nested_tokens.stdout)["total_tokens"] == 48
                        and json.loads(invalid_tokens.stdout)["input_tokens"] == 0
                        and "WARNING" in invalid_tokens.stderr
                    ),
                ),
                (
                    CURRENT_INVENTORY[14],
                    lambda: self.assertTrue(
                        sum(record["tokens"] > 0 for record in results) == 4
                        and {record["tokens"] for record in results} == {1280}
                        and {record["quality"] for record in results} == {1.0}
                    ),
                ),
                (CURRENT_INVENTORY[15], lambda: self.assertEqual(models.count("effort=xhigh"), 1)),
                (CURRENT_INVENTORY[16], lambda: self.assertEqual(models.count("effort=high"), 1)),
                (CURRENT_INVENTORY[17], lambda: self.assertEqual(models.count("effort=medium"), 1)),
                (CURRENT_INVENTORY[18], lambda: self.assertEqual(models.count("effort=low"), 1)),
                (CURRENT_INVENTORY[19], lambda: self.assertEqual(missing_codex.returncode, 1)),
                (
                    CURRENT_INVENTORY[20],
                    lambda: self.assertTrue(
                        "CLI not found" in (missing_codex.stdout + missing_codex.stderr)
                        and sweep_without_agent.returncode == 2
                        and "requires --agent" in (sweep_without_agent.stdout + sweep_without_agent.stderr)
                        and len(sweep_error_files) == 1
                        and json.loads(sweep_error_files[0].read_text(encoding="utf-8")) == []
                    ),
                ),
                (
                    CURRENT_INVENTORY[21],
                    lambda: self.assertTrue(
                        "codex exec" not in (claude_default.stdout + claude_default.stderr)
                        and missing_quality.returncode == 1
                        and json.loads(missing_quality.stdout)["error"] == "missing files"
                    ),
                ),
                (
                    CURRENT_INVENTORY[22],
                    lambda: self.assertTrue(
                        "(runtime=codex)" not in (claude_default.stdout + claude_default.stderr)
                        and json.loads(matching_quality.stdout)["overall"] == 1.0
                    ),
                ),
            ]

            self.assertEqual([name for name, _check in checks], CURRENT_INVENTORY)
            for name, check in checks:
                with self.subTest(msg=name):
                    check()


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Layer6CodexRunnerTests)
    return run_counted(suite, label="test-l6-codex-runner")


if __name__ == "__main__":
    raise SystemExit(main())
