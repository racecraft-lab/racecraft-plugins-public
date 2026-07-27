#!/usr/bin/env python3
"""Layer 6: Agent Efficiency Benchmarks.

Usage:
  python3 run-efficiency-benchmarks.py
  python3 run-efficiency-benchmarks.py --agent <name>
  python3 run-efficiency-benchmarks.py --agent <name> --sweep
  python3 run-efficiency-benchmarks.py --codex
  python3 run-efficiency-benchmarks.py --codex --agent <name> --sweep
"""

from __future__ import annotations

import datetime as _datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from types import ModuleType
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / "lib"
PLUGIN_ROOT = Path(os.environ.get("PLUGIN_ROOT", SCRIPT_DIR.parents[2] / "speckit-pro")).resolve()
RUNTIME_CLAUDE = "claude"
RUNTIME_CODEX = "codex"
SWEEP_CONFIGS = ("opus", "sonnet", "haiku")
CODEX_SWEEP_CONFIGS = ("xhigh", "high", "medium", "low")
CLAUDE_EXECUTABLE_NAMES = frozenset({"claude", "claude.exe", "claude.cmd", "claude.bat"})
CODEX_EXECUTABLE_NAMES = frozenset({"codex", "codex.exe", "codex.cmd", "codex.bat"})


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    spec.loader.exec_module(module)
    return module


TOKEN_COUNTER = load_module(LIB_DIR / "token-counter.py", "l6_token_counter")
QUALITY_SCORER = load_module(LIB_DIR / "quality-scorer.py", "l6_quality_scorer")


class Palette:
    def __init__(self) -> None:
        if sys.stdout.isatty():
            self.bold = "\033[1m"
            self.green = "\033[0;32m"
            self.red = "\033[0;31m"
            self.yellow = "\033[0;33m"
            self.cyan = "\033[0;36m"
            self.reset = "\033[0m"
        else:
            self.bold = ""
            self.green = ""
            self.red = ""
            self.yellow = ""
            self.cyan = ""
            self.reset = ""


COLORS = Palette()


class MissingValueError(ValueError):
    """Raised when a predecessor-required positional flag value is absent."""


class Config:
    def __init__(
        self,
        *,
        runtime: str = RUNTIME_CLAUDE,
        target_agent: str = "",
        sweep_mode: bool = False,
        claude_bin: str | None = None,
        codex_bin: str | None = None,
    ) -> None:
        self.runtime = runtime
        self.target_agent = target_agent
        self.sweep_mode = sweep_mode
        self.claude_bin = claude_bin or os.environ.get("CLAUDE_BIN", "claude")
        self.codex_bin = codex_bin or os.environ.get("CODEX_BIN", "codex")


class ResultWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.records: list[dict[str, Any]] = []

    def append(self, agent: str, model: str, tokens: int, wall_time: int, quality: float | int, exit_code: int) -> None:
        self.records.append(
            {
                "agent": agent,
                "model": model,
                "tokens": tokens,
                "wall_time": wall_time,
                "quality": quality,
                "exit_code": exit_code,
                "non_release_evidence": True,
            }
        )
        self.write()

    def write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent)
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(self.records, separators=(",", ":")) + "\n")
            os.replace(temporary_path, self.path)
        except Exception:
            try:
                os.close(fd)
            except OSError:
                pass
            temporary_path.unlink(missing_ok=True)
            raise


def usage_error(message: str) -> int:
    print(message, file=sys.stderr)
    return 2


def parse_args(argv: list[str]) -> Config:
    runtime = RUNTIME_CLAUDE
    target_agent = ""
    sweep_mode = False
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--agent":
            if index + 1 >= len(argv):
                raise MissingValueError("Missing value for --agent")
            target_agent = argv[index + 1]
            index += 2
        elif arg == "--sweep":
            sweep_mode = True
            index += 1
        elif arg == "--codex":
            runtime = RUNTIME_CODEX
            index += 1
        else:
            raise ValueError(f"Unknown flag: {arg}")
    return Config(runtime=runtime, target_agent=target_agent, sweep_mode=sweep_mode)


def resolve_dirs(runtime: str) -> tuple[Path, Path]:
    if runtime == RUNTIME_CODEX:
        fixtures = Path(os.environ.get("L6_FIXTURES_DIR", SCRIPT_DIR / "fixtures-codex"))
        results = Path(os.environ.get("L6_RESULTS_DIR", SCRIPT_DIR / "results-codex"))
    else:
        fixtures = Path(os.environ.get("L6_FIXTURES_DIR", SCRIPT_DIR / "fixtures"))
        results = Path(os.environ.get("L6_RESULTS_DIR", SCRIPT_DIR / "results"))
    return fixtures, results


def resolve_executable(command: str, allowed_names: frozenset[str] | None = None) -> Path | None:
    has_separator = os.sep in command or (os.altsep is not None and os.altsep in command)
    if has_separator:
        candidate = Path(command).expanduser()
        if not candidate.is_file() or (os.name != "nt" and not os.access(candidate, os.X_OK)):
            return None
        executable = Path(os.path.abspath(candidate))
        return executable if allowed_names is None or executable.name.casefold() in allowed_names else None
    executable = shutil.which(command)
    resolved = Path(os.path.abspath(executable)) if executable else None
    return resolved if resolved is not None and (allowed_names is None or resolved.name.casefold() in allowed_names) else None


def resolve_runtime_executable(config: Config) -> Path | None:
    command = config.claude_bin if config.runtime == RUNTIME_CLAUDE else config.codex_bin
    allowed_names = CLAUDE_EXECUTABLE_NAMES if config.runtime == RUNTIME_CLAUDE else CODEX_EXECUTABLE_NAMES
    executable = resolve_executable(command, allowed_names)
    if executable is not None:
        return executable
    if config.runtime == RUNTIME_CLAUDE:
        print(f"ERROR: {command} CLI not found. Layer 6 (Claude) requires 'claude -p'.")
    else:
        print(f"ERROR: {command} CLI not found. Layer 6 (Codex) requires 'codex exec'.")
    return None


def selected_executable_env(executable: Path) -> dict[str, str]:
    env = os.environ.copy()
    selected_dir = str(executable.parent)
    current_path = env.get("PATH", "")
    env["PATH"] = selected_dir if not current_path else f"{selected_dir}{os.pathsep}{current_path}"
    return env


def timestamp() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def collect_agents(fixtures_dir: Path, target_agent: str) -> list[str]:
    if target_agent:
        return [target_agent]
    if not fixtures_dir.is_dir():
        return []
    return sorted(path.name for path in fixtures_dir.iterdir() if path.is_dir())


def extract_claude_agent_body(agent_file: Path) -> str:
    lines = agent_file.read_text(encoding="utf-8").splitlines()
    marker_count = 0
    body: list[str] = []
    for line in lines:
        if line == "---":
            marker_count += 1
            continue
        if marker_count >= 2:
            body.append(line)
    return "\n".join(body)


def extract_codex_agent_body(toml_file: Path) -> str:
    data = tomllib.loads(toml_file.read_text(encoding="utf-8"))
    value = data.get("developer_instructions", "")
    return value.rstrip("\n") if isinstance(value, str) else ""


def compose_prompt(agent_body: str, input_text: str) -> str:
    body = agent_body.rstrip("\n")
    prompt = input_text.rstrip("\n")
    return f"{body}\n\n---\n\n{prompt}" if body else prompt


def claude_prompt(agent: str, input_text: str) -> str:
    agent_file = PLUGIN_ROOT / "agents" / f"{agent}.md"
    if agent_file.is_file():
        return compose_prompt(extract_claude_agent_body(agent_file), input_text)
    return input_text.rstrip("\n")


def codex_prompt(agent: str, input_text: str) -> str:
    agent_file = PLUGIN_ROOT / "codex-agents" / f"{agent}.toml"
    if agent_file.is_file():
        return compose_prompt(extract_codex_agent_body(agent_file), input_text)
    return input_text.rstrip("\n")


def quality_overall(actual_file: Path, expected_file: Path) -> float | int:
    payload, _exit_code = QUALITY_SCORER.score_files(actual_file, expected_file)
    return payload.get("overall", 0)


def print_outcome(overall: float | int, wall_time: int, tokens: int) -> None:
    if overall == -1:
        print(f"{COLORS.yellow}OK{COLORS.reset} (no baseline) | {wall_time}s | {tokens} tokens")
    elif float(overall) >= 0.7:
        print(f"{COLORS.green}PASS{COLORS.reset} ({float(overall) * 100:.0f}%) | {wall_time}s | {tokens} tokens")
    else:
        print(f"{COLORS.red}FAIL{COLORS.reset} ({float(overall) * 100:.0f}%) | {wall_time}s | {tokens} tokens")


def run_benchmark(agent: str, model: str, fixtures_dir: Path, writer: ResultWriter, claude_executable: Path) -> None:
    fixture_dir = fixtures_dir / agent
    input_file = fixture_dir / "input-prompt.md"
    expected_file = fixture_dir / "expected-output.md"

    if not input_file.is_file():
        print(f"  {COLORS.yellow}SKIP{COLORS.reset} {agent} (no input-prompt.md)")
        return

    prompt = claude_prompt(agent, input_file.read_text(encoding="utf-8"))
    argv = ["claude", "-p", "--output-format", "json"]
    if model:
        argv.extend(["--model", model])

    label = f"{agent} ({model})" if model else agent
    print(f"  Running {COLORS.bold}{label}{COLORS.reset} ... ", end="", flush=True)

    start = _datetime.datetime.now()
    try:
        completed = subprocess.run(
            argv,
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            env=selected_executable_env(claude_executable),
            shell=False,
            check=False,
        )
    except OSError as exc:
        wall_time = int((_datetime.datetime.now() - start).total_seconds())
        print(f"{COLORS.red}ERROR{COLORS.reset} ({type(exc).__name__}: {exc})")
        writer.append(agent, model, 0, wall_time, 0, 127)
        return
    wall_time = int((_datetime.datetime.now() - start).total_seconds())

    if completed.returncode != 0:
        print(f"{COLORS.red}ERROR{COLORS.reset} (exit {completed.returncode})")
        if completed.stderr:
            print("    claude stderr:")
            for line in completed.stderr.splitlines():
                print(f"      {line}")
        writer.append(agent, model, 0, wall_time, 0, completed.returncode)
        return

    token_summary, _parsed = TOKEN_COUNTER.parse_token_text(completed.stdout)
    total_tokens = int(token_summary.get("total_tokens", 0))
    overall: float | int = -1
    if expected_file.is_file():
        actual_text = ""
        try:
            payload = json.loads(completed.stdout)
            result = payload.get("result", "")
            actual_text = result if isinstance(result, str) else str(result)
        except json.JSONDecodeError:
            actual_text = ""
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as actual:
            actual.write(actual_text)
            actual_path = Path(actual.name)
        try:
            overall = quality_overall(actual_path, expected_file)
        finally:
            actual_path.unlink(missing_ok=True)

    writer.append(agent, model, total_tokens, wall_time, overall, 0)
    print_outcome(overall, wall_time, total_tokens)


def codex_total_tokens(jsonl_file: Path) -> int:
    total = 0
    for line in jsonl_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed":
            usage = event.get("usage", {}) or {}
            total = int(usage.get("input_tokens", 0) or 0)
            total += int(usage.get("cached_input_tokens", 0) or 0)
            total += int(usage.get("output_tokens", 0) or 0)
            total += int(usage.get("reasoning_output_tokens", 0) or 0)
    return total


def run_benchmark_codex(
    agent: str,
    effort: str,
    fixtures_dir: Path,
    writer: ResultWriter,
    codex_executable: Path,
) -> None:
    fixture_dir = fixtures_dir / agent
    input_file = fixture_dir / "input-prompt.md"
    expected_file = fixture_dir / "expected-output.md"

    if not input_file.is_file():
        print(f"  {COLORS.yellow}SKIP{COLORS.reset} {agent} (no input-prompt.md)")
        return

    prompt = codex_prompt(agent, input_file.read_text(encoding="utf-8"))
    label = f"{agent} (effort={effort})" if effort else agent
    print(f"  Running {COLORS.bold}{label}{COLORS.reset} ... ", end="", flush=True)

    jsonl_file = tempfile.NamedTemporaryFile(delete=False)
    stderr_file = tempfile.NamedTemporaryFile(delete=False)
    last_message_file = tempfile.NamedTemporaryFile(delete=False)
    jsonl_path = Path(jsonl_file.name)
    stderr_path = Path(stderr_file.name)
    last_message_path = Path(last_message_file.name)
    jsonl_file.close()
    stderr_file.close()
    last_message_file.close()

    argv = ["codex", "exec"]
    if effort:
        argv.extend(["-c", f"model_reasoning_effort={effort}"])
    argv.extend(["--json", "-o", str(last_message_path), "-"])

    model_label = f"effort={effort}"
    try:
        start = _datetime.datetime.now()
        try:
            with jsonl_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
                completed = subprocess.run(
                    argv,
                    input=prompt,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stdout=stdout,
                    stderr=stderr,
                    env=selected_executable_env(codex_executable),
                    shell=False,
                    check=False,
                )
        except OSError as exc:
            wall_time = int((_datetime.datetime.now() - start).total_seconds())
            print(f"{COLORS.red}ERROR{COLORS.reset} ({type(exc).__name__}: {exc})")
            writer.append(agent, model_label, 0, wall_time, 0, 127)
            return
        wall_time = int((_datetime.datetime.now() - start).total_seconds())

        if completed.returncode != 0:
            print(f"{COLORS.red}ERROR{COLORS.reset} (exit {completed.returncode})")
            stderr_text = stderr_path.read_text(encoding="utf-8")
            if stderr_text:
                print("    codex stderr:")
                for line in stderr_text.splitlines():
                    print(f"      {line}")
            writer.append(agent, model_label, 0, wall_time, 0, completed.returncode)
            return

        total_tokens = codex_total_tokens(jsonl_path)
        overall: float | int = -1
        if expected_file.is_file() and last_message_path.is_file() and last_message_path.stat().st_size > 0:
            overall = quality_overall(last_message_path, expected_file)
        writer.append(agent, model_label, total_tokens, wall_time, overall, 0)
        print_outcome(overall, wall_time, total_tokens)
    finally:
        jsonl_path.unlink(missing_ok=True)
        stderr_path.unlink(missing_ok=True)
        last_message_path.unlink(missing_ok=True)


def run(config: Config) -> int:
    fixtures_dir, results_dir = resolve_dirs(config.runtime)
    runtime_executable = resolve_runtime_executable(config)
    if runtime_executable is None:
        return 1

    result_file = results_dir / f"{timestamp()}.json"
    writer = ResultWriter(result_file)
    writer.write()
    agents = collect_agents(fixtures_dir, config.target_agent)

    if not agents:
        print(f"No agent fixtures found in {fixtures_dir}/")
        print("Create fixtures/<agent-name>/input-prompt.md to get started.")
        writer.write()
        return 0

    print(f"\n{COLORS.bold}{COLORS.cyan}Layer 6: Agent Efficiency Benchmarks (runtime={config.runtime}){COLORS.reset}")
    print("--------------------------------------------")

    if config.runtime == RUNTIME_CLAUDE:
        if config.sweep_mode and config.target_agent:
            print(f"Sweep mode: testing {config.target_agent} across {len(SWEEP_CONFIGS)} model configurations\n")
            for model in SWEEP_CONFIGS:
                run_benchmark(config.target_agent, model, fixtures_dir, writer, runtime_executable)
        elif config.sweep_mode:
            print("ERROR: --sweep requires --agent <name>")
            writer.write()
            return 2
        else:
            for agent in agents:
                run_benchmark(agent, "", fixtures_dir, writer, runtime_executable)
    else:
        if config.sweep_mode and config.target_agent:
            print(f"Sweep mode: testing {config.target_agent} across {len(CODEX_SWEEP_CONFIGS)} effort levels\n")
            for effort in CODEX_SWEEP_CONFIGS:
                run_benchmark_codex(config.target_agent, effort, fixtures_dir, writer, runtime_executable)
        elif config.sweep_mode:
            print("ERROR: --sweep requires --agent <name>")
            writer.write()
            return 2
        else:
            for agent in agents:
                run_benchmark_codex(agent, "", fixtures_dir, writer, runtime_executable)

    writer.write()
    print(f"\nResults saved to: {result_file}")
    return 0


def main(argv: list[str]) -> int:
    try:
        config = parse_args(argv)
    except MissingValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ValueError as exc:
        return usage_error(str(exc))
    return run(config)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
