#!/usr/bin/env python3
"""Layer 8 parity fixture runner.

Validates Layer 8 parity fixtures in dry-run mode by default. Live mode runs
the same workflow twice with teams and fallback environment contracts, then
compares configured artifacts with deterministic local tolerances.
"""

from __future__ import annotations

import difflib
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / "lib"
ENV_SCHEMA = "speckit.layer8.env.v1"
EXPECTED_SCHEMA = "speckit.layer8.expected-equivalence.v1"
TOLERANCE_SCHEMA = "speckit.layer8.tolerance.v1"
ALLOWED_TOLERANCES = frozenset({"byte-identical", "exact", "tolerance-1", "semantic-equivalent"})
DEFAULT_BUDGET_USD = "20"
CLAUDE_EXECUTABLE_NAMES = frozenset({"claude", "claude.exe", "claude.cmd", "claude.bat"})
RULE = "────────────────────────────────────────"
SUMMARY_RULE = "════════════════════════════════════════"
MAX_DIFF_LINES = 50
MAX_PREVIEW_CHARS = 4_096

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import extractors  # noqa: E402
import judge  # noqa: E402


@dataclass
class Config:
    mode: str = "dry-run"
    fixture_filter: str = ""
    budget_usd: str = os.environ.get("L8_FIXTURE_BUDGET_USD", DEFAULT_BUDGET_USD)
    claude_bin: str = os.environ.get("CLAUDE_BIN", "claude")


class Counts:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self._color = sys.stdout.isatty()

    def _style(self, color: str, text: str) -> str:
        if not self._color:
            return text
        colors = {"red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m"}
        return f"{colors[color]}{text}\033[0m"

    def pass_(self, label: str) -> None:
        self.passed += 1
        print(f"  {self._style('green', 'PASS')} {label}")

    def fail(self, label: str, detail: str = "") -> None:
        self.failed += 1
        print(f"  {self._style('red', 'FAIL')} {label}")
        if detail:
            print(f"    {self._style('red', detail)}")

    def skip(self, label: str, detail: str = "") -> None:
        self.skipped += 1
        print(f"  {self._style('yellow', 'SKIP')} {label}")
        if detail:
            print(f"    {self._style('yellow', detail)}")


def print_usage() -> None:
    print(
        "\n".join(
            [
                "Layer 8 - Parity Fixtures Runner",
                "",
                "Usage:",
                "  python3 tests/speckit-pro/layer8-parity/run-parity-fixtures.py [--dry-run|--live]",
                "                                                               [--fixture <name>]",
                "                                                               [--budget-usd <N>]",
                "",
                "Environment:",
                "  L8_FIXTURE_BUDGET_USD  Per-fixture-pair budget cap (default: 20)",
                "  CLAUDE_BIN             claude executable (default: claude)",
                "  L8_OUT                 live-mode output root (default: platform temp directory)",
            ]
        )
    )


def parse_args(argv: list[str]) -> tuple[Config | None, int]:
    config = Config()
    index = 0
    while index < len(argv):
        arg = argv[index]
        if arg == "--dry-run":
            config.mode = "dry-run"
            index += 1
        elif arg == "--live":
            config.mode = "live"
            index += 1
        elif arg == "--fixture":
            if index + 1 >= len(argv):
                print("Missing value for --fixture", file=sys.stderr)
                return None, 2
            config.fixture_filter = argv[index + 1]
            index += 2
        elif arg == "--budget-usd":
            if index + 1 >= len(argv):
                print("Missing value for --budget-usd", file=sys.stderr)
                return None, 2
            config.budget_usd = argv[index + 1]
            index += 2
        elif arg in {"-h", "--help"}:
            print_usage()
            return None, 0
        else:
            print(f"Unknown flag: {arg}", file=sys.stderr)
            return None, 2
    return config, 0


def required_files() -> tuple[str, ...]:
    return (
        "README.md",
        "workflow.md",
        "env-fallback.json",
        "env-teams.json",
        "tolerance.json",
        "expected-equivalence.json",
    )


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return data


def validate_env_contract(path: Path, expected_mode: str) -> None:
    data = load_json(path)
    if data.get("schema") != ENV_SCHEMA:
        raise ValueError(f"{path.name} schema must be {ENV_SCHEMA}")
    if data.get("mode") != expected_mode:
        raise ValueError(f"{path.name} mode must be {expected_mode}")
    environment = data.get("environment")
    if not isinstance(environment, dict):
        raise ValueError(f"{path.name} environment must be an object")
    set_values = environment.get("set", {})
    unset_values = environment.get("unset", [])
    if not isinstance(set_values, dict):
        raise ValueError(f"{path.name} environment.set must be an object")
    if not isinstance(unset_values, list) or not all(isinstance(value, str) for value in unset_values):
        raise ValueError(f"{path.name} environment.unset must be a string list")
    for key, value in set_values.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError(f"{path.name} environment.set must map strings to strings")


def validate_relative_source(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value.startswith(("/", "\\")):
        raise ValueError(f"{label} must be a non-empty relative path")
    if "\\" in value or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError(f"{label} must be a normalized repository-relative path")
    return value


def validate_fixture_contracts(fixture_dir: Path, expected: dict[str, Any], tolerance: dict[str, Any]) -> None:
    fixture_id = fixture_dir.name
    if expected.get("schema") != EXPECTED_SCHEMA:
        raise ValueError(f"expected-equivalence.json schema must be {EXPECTED_SCHEMA}")
    if tolerance.get("schema") != TOLERANCE_SCHEMA:
        raise ValueError(f"tolerance.json schema must be {TOLERANCE_SCHEMA}")
    if expected.get("fixture_id") != fixture_id or tolerance.get("fixture_id") != fixture_id:
        raise ValueError("fixture_id must match the fixture directory in both contracts")

    fields = tolerance.get("fields")
    if not isinstance(fields, dict) or not fields:
        raise ValueError("tolerance.json fields must be a non-empty object")
    for key, entry in fields.items():
        if not isinstance(key, str) or not key or not isinstance(entry, dict):
            raise ValueError("tolerance.json fields must map non-empty strings to objects")
        if entry.get("tolerance") not in ALLOWED_TOLERANCES:
            raise ValueError(f"tolerance key '{key}' has an unsupported tolerance")
        if not isinstance(entry.get("rationale"), str) or not entry["rationale"].strip():
            raise ValueError(f"tolerance key '{key}' must provide a rationale")

    compare = expected.get("compare")
    if not isinstance(compare, list) or not compare:
        raise ValueError("expected-equivalence.json compare must be a non-empty array")
    compare_fields: set[str] = set()
    tolerance_keys: set[str] = set()
    compare_sources: set[str] = set()
    for index, entry in enumerate(compare):
        if not isinstance(entry, dict):
            raise ValueError(f"compare[{index}] must be an object")
        field = entry.get("field")
        tolerance_key = entry.get("tolerance_key")
        if not isinstance(field, str) or not field or field in compare_fields:
            raise ValueError(f"compare[{index}].field must be a unique non-empty string")
        if not isinstance(tolerance_key, str) or tolerance_key not in fields:
            raise ValueError(f"compare[{index}].tolerance_key must reference tolerance.json fields")
        compare_fields.add(field)
        tolerance_keys.add(tolerance_key)
        compare_sources.add(validate_relative_source(entry.get("source"), f"compare[{index}].source"))
        section = entry.get("section_selector")
        extractor = entry.get("extractor")
        if (section is None) != (extractor is None):
            raise ValueError(f"compare[{index}] must provide section_selector and extractor together")
        if section is not None and (not isinstance(section, str) or not section.startswith("## ")):
            raise ValueError(f"compare[{index}].section_selector must name an H2 section")
        if extractor is not None and not (
            extractor == "table_row_count" or isinstance(extractor, str) and extractor.startswith("table_column:")
        ):
            raise ValueError(f"compare[{index}].extractor is unsupported")
    if tolerance_keys != set(fields):
        missing = sorted(set(fields) - tolerance_keys)
        raise ValueError(f"tolerance.json contains unreferenced fields: {missing}")

    invariants = expected.get("required_invariants")
    invariant_source = expected.get("required_invariants_source")
    if invariants is None:
        if invariant_source is not None:
            raise ValueError("required_invariants_source requires required_invariants")
        return
    if not isinstance(invariants, dict) or not invariants:
        raise ValueError("required_invariants must be a non-empty object")
    for key, value in invariants.items():
        if not isinstance(key, str) or not key:
            raise ValueError("required_invariants keys must be non-empty strings")
        if isinstance(value, list):
            if not value or not all(isinstance(item, str) and item for item in value):
                raise ValueError(f"required_invariants.{key} must be a non-empty string list")
        elif not isinstance(value, (str, bool)) or isinstance(value, str) and not value:
            raise ValueError(f"required_invariants.{key} must be a non-empty string, boolean, or string list")
    if not isinstance(invariant_source, dict):
        raise ValueError("required_invariants_source must be an object")
    if set(invariant_source) != {"source", "section_selector", "key_column", "value_column"}:
        raise ValueError("required_invariants_source has an invalid shape")
    source = validate_relative_source(invariant_source.get("source"), "required_invariants_source.source")
    if source not in compare_sources:
        raise ValueError("required_invariants_source.source must also be a compared output")
    for key in ("section_selector", "key_column", "value_column"):
        value = invariant_source.get(key)
        if not isinstance(value, str) or not value:
            raise ValueError(f"required_invariants_source.{key} must be a non-empty string")
    if not invariant_source["section_selector"].startswith("## "):
        raise ValueError("required_invariants_source.section_selector must name an H2 section")


def invariant_value(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def enforce_required_invariants(
    output_root: Path,
    expected: dict[str, Any],
    counts: Counts,
    label: str,
) -> bool:
    invariants = expected.get("required_invariants")
    if not isinstance(invariants, dict):
        return True
    source = expected["required_invariants_source"]
    artifact = output_root / source["source"]
    section = strip_h2_prefix(source["section_selector"])
    try:
        keys = extractors.extract_table_column(artifact, section, source["key_column"]).splitlines()
        values = extractors.extract_table_column(artifact, section, source["value_column"]).splitlines()
    except (OSError, extractors.ExtractorError) as exc:
        counts.fail(f"{label}: required invariants", f"cannot read invariant evidence: {exc}")
        return False
    if len(keys) != len(values) or len(keys) != len(set(keys)):
        counts.fail(f"{label}: required invariants", "invariant evidence must contain unique key/value rows")
        return False
    observed = dict(zip(keys, values, strict=True))
    failures = [
        f"{key}: expected {invariant_value(value)!r}, observed {observed.get(key)!r}"
        for key, value in invariants.items()
        if observed.get(key) != invariant_value(value)
    ]
    if failures:
        counts.fail(f"{label}: required invariants", "; ".join(failures))
        return False
    return True


def validate_fixture_structure(fixture_dir: Path, counts: Counts) -> bool:
    fixture_id = fixture_dir.name
    ok = True
    for required in required_files():
        if not (fixture_dir / required).is_file():
            counts.fail(f"{fixture_id}: missing {required}", f"every parity fixture must provide {required}")
            ok = False

    env_checks = (
        ("env-fallback.json", "fallback"),
        ("env-teams.json", "teams"),
    )
    for file_name, expected_mode in env_checks:
        path = fixture_dir / file_name
        if not path.is_file():
            continue
        try:
            validate_env_contract(path, expected_mode)
        except (json.JSONDecodeError, ValueError) as exc:
            counts.fail(f"{fixture_id}: {file_name} invalid env contract", str(exc))
            ok = False

    if ok:
        counts.pass_(f"{fixture_id}: fixture structure complete")

    contracts: dict[str, dict[str, Any]] = {}
    for file_name in ("tolerance.json", "expected-equivalence.json"):
        path = fixture_dir / file_name
        if not path.is_file():
            continue
        try:
            contracts[file_name] = load_json(path)
        except (json.JSONDecodeError, ValueError) as exc:
            counts.fail(f"{fixture_id}: {file_name} invalid JSON", str(exc))
            ok = False
        else:
            counts.pass_(f"{fixture_id}: {file_name} parses")
    if set(contracts) == {"tolerance.json", "expected-equivalence.json"}:
        try:
            validate_fixture_contracts(
                fixture_dir,
                contracts["expected-equivalence.json"],
                contracts["tolerance.json"],
            )
        except ValueError as exc:
            counts.fail(f"{fixture_id}: fixture contract invalid", str(exc))
            ok = False
        else:
            ok &= enforce_required_invariants(
                fixture_dir,
                contracts["expected-equivalence.json"],
                counts,
                fixture_id,
            )
    return ok


def discover_fixtures(config: Config) -> list[Path]:
    fixtures = [
        path
        for path in sorted(SCRIPT_DIR.iterdir())
        if path.is_dir() and (path / "README.md").is_file()
    ]
    if config.fixture_filter:
        fixtures = [path for path in fixtures if path.name == config.fixture_filter]
    return fixtures


def resolve_executable(command: str) -> str | None:
    if os.sep in command or (os.altsep and os.altsep in command):
        path = Path(command)
        executable = str(path.absolute()) if path.is_file() and (os.name == "nt" or os.access(path, os.X_OK)) else None
    else:
        executable = shutil.which(command)
    if executable is None or Path(executable).name.casefold() not in CLAUDE_EXECUTABLE_NAMES:
        return None
    return executable


def claude_bin_missing_reason(command: str) -> str:
    if os.sep in command or (os.altsep and os.altsep in command):
        path = Path(command)
        if not path.exists():
            return f"configured CLAUDE_BIN path does not exist: {command}"
        if not path.is_file():
            return f"configured CLAUDE_BIN path is not a file: {command}"
        if os.name != "nt" and not os.access(path, os.X_OK):
            return f"configured CLAUDE_BIN path is not executable: {command}"
        return f"configured CLAUDE_BIN path is not a supported Claude executable: {command}"
    return f"{command} not on PATH"


def env_from_contract(contract_path: Path) -> dict[str, str]:
    data = load_json(contract_path)
    environment = data["environment"]
    child_env = os.environ.copy()
    for key in environment.get("unset", []):
        child_env.pop(key, None)
    for key, value in environment.get("set", {}).items():
        child_env[key] = value
    return child_env


def run_path(fixture_dir: Path, env_contract: Path, out_dir: Path, config: Config, claude_executable: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(fixture_dir / "workflow.md", out_dir / "workflow.md")
    stdout_path = out_dir / ".claude-stdout.log"
    stderr_path = out_dir / ".claude-stderr.log"
    exit_path = out_dir / ".claude-exit-code"
    argv = [
        "claude",
        "-p",
        "--max-budget-usd",
        config.budget_usd,
        "/speckit-pro:autopilot workflow.md",
    ]
    child_env = env_from_contract(env_contract)
    selected_dir = str(Path(claude_executable).parent)
    current_path = child_env.get("PATH", "")
    child_env["PATH"] = selected_dir if not current_path else f"{selected_dir}{os.pathsep}{current_path}"
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        completed = subprocess.run(
            argv,
            cwd=out_dir,
            text=True,
            stdout=stdout,
            stderr=stderr,
            env=child_env,
            shell=False,
            check=False,
        )
    exit_path.write_text(f"{completed.returncode}\n", encoding="utf-8")


def strip_h2_prefix(section: str) -> str:
    return section[3:] if section.startswith("## ") else section


def extract_value(file_path: Path, section: str, extractor_name: str) -> str:
    if extractor_name == "table_row_count":
        return extractors.extract_table_row_count(file_path, section)
    if extractor_name.startswith("table_column:"):
        column = extractor_name.split(":", 1)[1]
        return extractors.extract_table_column(file_path, section, column)
    raise ValueError(f"unknown extractor '{extractor_name}'")


def read_text_lossy(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)


def _write_bounded_diff(report: Any, diff: Any) -> None:
    iterator = iter(diff)
    for line in itertools.islice(iterator, MAX_DIFF_LINES):
        report.write(line)
    if next(iterator, None) is not None:
        report.write(f"... diff truncated after {MAX_DIFF_LINES} lines\n")


def _bounded_preview(text: str) -> str:
    if len(text) <= MAX_PREVIEW_CHARS:
        return text
    remaining = len(text) - MAX_PREVIEW_CHARS
    return f"{text[:MAX_PREVIEW_CHARS]}\n...[truncated {remaining} chars]\n"


def append_file_diff(report_path: Path, file_a: Path, file_b: Path) -> None:
    diff = difflib.unified_diff(
        read_text_lossy(file_a),
        read_text_lossy(file_b),
        fromfile=file_a.as_posix(),
        tofile=file_b.as_posix(),
    )
    with report_path.open("a", encoding="utf-8") as report:
        _write_bounded_diff(report, diff)


def append_value_diff(report_path: Path, field_name: str, extractor_name: str, value_a: str, value_b: str) -> None:
    diff = difflib.unified_diff(
        [f"{line}\n" for line in value_a.splitlines()],
        [f"{line}\n" for line in value_b.splitlines()],
        fromfile="pathA",
        tofile="pathB",
    )
    with report_path.open("a", encoding="utf-8") as report:
        report.write(f"\n--- {field_name} (extractor={extractor_name}) ---\n")
        _write_bounded_diff(report, diff)


def append_semantic_skip(report_path: Path, field_name: str, value_a: str, value_b: str, reason: str) -> None:
    with report_path.open("a", encoding="utf-8") as report:
        report.write(f"\n--- {field_name} (semantic-equivalent skipped) ---\n")
        report.write(f"WARNING: {reason}\n")
        report.write("VALUE A:\n")
        report.write(_bounded_preview(value_a))
        report.write("\nVALUE B:\n")
        report.write(_bounded_preview(value_b))
        report.write("\n")


def result_detail(result: Any) -> dict[str, Any]:
    detail = getattr(result, "detail", None)
    return detail if isinstance(detail, dict) else {}


def emit_judge_result(
    counts: Counts,
    fixture_id: str,
    field_name: str,
    tolerance_type: str,
    result: Any,
    report_path: Path,
    file_a: Path | None = None,
    file_b: Path | None = None,
    extractor_name: str = "",
    value_a: str = "",
    value_b: str = "",
) -> str:
    status = getattr(result, "status", "fail")
    reason = getattr(result, "reason", "comparison failed")
    if status == "pass":
        if tolerance_type == "byte-identical":
            counts.pass_(f"{fixture_id}:{field_name} (byte-identical)")
        elif tolerance_type == "tolerance-1":
            detail = result_detail(result)
            diff = detail.get("difference", 0)
            left = detail.get("value_a", value_a)
            right = detail.get("value_b", value_b)
            counts.pass_(f"{fixture_id}:{field_name} (tolerance-1, |{left} - {right}|={diff})")
        elif extractor_name:
            counts.pass_(f"{fixture_id}:{field_name} ({tolerance_type}, extractor={extractor_name})")
        else:
            counts.pass_(f"{fixture_id}:{field_name} ({tolerance_type}, whole-file)")
        return "pass"

    if status == "skip":
        counts.skip(f"{fixture_id}:{field_name}", f"WARNING: {reason}")
        append_semantic_skip(report_path, field_name, value_a, value_b, reason)
        return "skip"

    if tolerance_type == "byte-identical" and file_a is not None and file_b is not None:
        counts.fail(f"{fixture_id}:{field_name}", "byte-identical tolerance failed - see diff in report")
        append_file_diff(report_path, file_a, file_b)
    elif extractor_name:
        counts.fail(f"{fixture_id}:{field_name}", reason)
        append_value_diff(report_path, field_name, extractor_name, value_a, value_b)
    else:
        counts.fail(f"{fixture_id}:{field_name}", reason)
        if file_a is not None and file_b is not None:
            append_file_diff(report_path, file_a, file_b)
    return "fail"


def compare_whole_file_bytes(
    fixture_id: str,
    field_name: str,
    tolerance_type: str,
    file_a: Path,
    file_b: Path,
    report_path: Path,
    counts: Counts,
) -> str:
    if file_a.read_bytes() == file_b.read_bytes():
        counts.pass_(f"{fixture_id}:{field_name} ({tolerance_type}, whole-file)")
        return "pass"
    counts.fail(f"{fixture_id}:{field_name}", f"{tolerance_type} tolerance failed (whole-file byte diff)")
    append_file_diff(report_path, file_a, file_b)
    return "fail"


def compare_field(
    fixture_id: str,
    path_a: Path,
    path_b: Path,
    field_json: dict[str, Any],
    tolerance_json: dict[str, Any],
    counts: Counts,
) -> str:
    field_name = str(field_json.get("field", "field"))
    source_path = str(field_json.get("source", ""))
    tolerance_key = str(field_json.get("tolerance_key", ""))
    report_path = path_a.parent / "diff-report.txt"

    tolerance_entry = tolerance_json.get("fields", {}).get(tolerance_key, {})
    tolerance_type = tolerance_entry.get("tolerance", "unknown")
    if not isinstance(tolerance_type, str) or tolerance_type == "unknown":
        counts.fail(f"{fixture_id}:{field_name}", f"unknown tolerance key '{tolerance_key}'")
        return "fail"

    file_a = path_a / source_path
    file_b = path_b / source_path
    if not file_a.is_file() or not file_b.is_file():
        counts.fail(f"{fixture_id}:{field_name}", f"missing artifact on one or both paths ({source_path})")
        return "fail"

    # Byte identity is a file contract and must be evaluated before optional
    # section/extractor configuration can change the comparison surface.
    if tolerance_type == "byte-identical":
        return compare_whole_file_bytes(fixture_id, field_name, tolerance_type, file_a, file_b, report_path, counts)

    section = strip_h2_prefix(str(field_json.get("section_selector", "")))
    extractor_name = str(field_json.get("extractor", ""))
    if section and extractor_name:
        try:
            value_a = extract_value(file_a, section, extractor_name)
            value_b = extract_value(file_b, section, extractor_name)
        except (extractors.ExtractorError, ValueError) as exc:
            counts.fail(
                f"{fixture_id}:{field_name}",
                f"extractor '{extractor_name}' failed for section '## {section}' on one or both paths: {exc}",
            )
            return "fail"
        if tolerance_type == "semantic-equivalent" and value_a.encode("utf-8") == value_b.encode("utf-8"):
            counts.pass_(f"{fixture_id}:{field_name} (semantic-equivalent, bytes match - judge skipped)")
            return "pass"
        try:
            result = judge.judge_values(value_a, value_b, tolerance_type, field=field_name)
        except ValueError as exc:
            counts.fail(f"{fixture_id}:{field_name}", str(exc))
            return "fail"
        return emit_judge_result(
            counts,
            fixture_id,
            field_name,
            tolerance_type,
            result,
            report_path,
            extractor_name=extractor_name,
            value_a=value_a,
            value_b=value_b,
        )

    if tolerance_type == "semantic-equivalent":
        counts.fail(
            f"{fixture_id}:{field_name}",
            "semantic-equivalent requires section_selector + extractor in expected-equivalence.json",
        )
        return "fail"

    if tolerance_type in {"exact", "tolerance-1"}:
        return compare_whole_file_bytes(fixture_id, field_name, tolerance_type, file_a, file_b, report_path, counts)

    try:
        result = judge.judge_files(file_a, file_b, tolerance_type, field=field_name)
    except ValueError as exc:
        counts.fail(f"{fixture_id}:{field_name}", str(exc))
        return "fail"

    return emit_judge_result(
        counts,
        fixture_id,
        field_name,
        tolerance_type,
        result,
        report_path,
        file_a=file_a,
        file_b=file_b,
    )


def run_fixture_live(fixture_dir: Path, config: Config, counts: Counts) -> None:
    fixture_id = fixture_dir.name
    claude_executable = resolve_executable(config.claude_bin)
    if claude_executable is None:
        counts.skip(f"{fixture_id}: live mode", claude_bin_missing_reason(config.claude_bin))
        return

    default_out = Path(tempfile.gettempdir()) / f"l8-parity-{os.getpid()}"
    out_root = Path(os.environ.get("L8_OUT", str(default_out))) / fixture_id
    path_a = out_root / "pathA"
    path_b = out_root / "pathB"
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / "diff-report.txt").write_text("", encoding="utf-8")

    live_label = "LIVE"
    print(f"  {live_label} {fixture_id}: running Path A (env-teams.json)")
    run_path(fixture_dir, fixture_dir / "env-teams.json", path_a, config, claude_executable)
    rc_a = (path_a / ".claude-exit-code").read_text(encoding="utf-8").strip()
    print(f"  {live_label} {fixture_id}: running Path B (env-fallback.json)")
    run_path(fixture_dir, fixture_dir / "env-fallback.json", path_b, config, claude_executable)
    rc_b = (path_b / ".claude-exit-code").read_text(encoding="utf-8").strip()

    if rc_a != "0" or rc_b != "0":
        counts.fail(
            f"{fixture_id}: claude -p",
            f"Path A exit={rc_a} / Path B exit={rc_b}. See {out_root}/{{pathA,pathB}}/.claude-stderr.log",
        )
        return

    expected = load_json(fixture_dir / "expected-equivalence.json")
    tolerance = load_json(fixture_dir / "tolerance.json")
    invariants_ok = enforce_required_invariants(path_a, expected, counts, f"{fixture_id}:Path A")
    invariants_ok &= enforce_required_invariants(path_b, expected, counts, f"{fixture_id}:Path B")
    if not invariants_ok:
        return
    fail_fast = bool(expected.get("fail_fast", False))
    compare_entries = expected.get("compare", [])
    if not isinstance(compare_entries, list):
        counts.fail(f"{fixture_id}: expected-equivalence.json", "compare must be an array")
        return

    for entry in compare_entries:
        if not isinstance(entry, dict):
            counts.fail(f"{fixture_id}: expected-equivalence.json", "compare entries must be objects")
            if fail_fast:
                return
            continue
        status = compare_field(fixture_id, path_a, path_b, entry, tolerance, counts)
        if status == "fail" and fail_fast:
            return

    print(f"  LIVE {fixture_id}: results in {out_root}")


def main(argv: list[str] | None = None) -> int:
    config, parse_exit = parse_args(sys.argv[1:] if argv is None else argv)
    if config is None:
        return parse_exit

    counts = Counts()
    print(f"Layer 8: Parity Fixtures (mode={config.mode})")
    print(RULE)

    for fixture_dir in discover_fixtures(config):
        print()
        print(fixture_dir.name)
        fixture_valid = validate_fixture_structure(fixture_dir, counts)
        if config.mode == "live" and fixture_valid:
            run_fixture_live(fixture_dir, config, counts)

    print()
    print(SUMMARY_RULE)
    print(f"Layer 8 (parity): {counts.passed} passed, {counts.failed} failed, {counts.skipped} skipped")
    print(f"run-parity-fixtures: {counts.passed}/{counts.passed + counts.failed} passed")
    return 1 if counts.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
