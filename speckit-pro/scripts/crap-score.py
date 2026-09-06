#!/usr/bin/env python3
"""CRAP score gate: join per-function complexity with per-function coverage.

CRAP(f) = cc(f)^2 * (1 - cov(f))^3 + cc(f), where cov is the fraction of the
function's measured lines (Python) or statements (TypeScript) that ran.

Python joins ``radon cc --json`` with a ``coverage json`` report. TypeScript
joins ESLint's ``complexity`` rule (``--format json``, max 0 so every function
reports) with an Istanbul ``coverage-final.json``. Each source can be supplied
pre-generated (``--radon-json``, ``--coverage-json``, ``--eslint-json``) so the
join runs without the tools installed; otherwise radon, ESLint, and
``coverage json`` run here with fixed argument lists. The test run that
produces coverage data is never launched from this script: the discovery
table's slot command runs it first, so no operator-supplied executable is
ever spawned from plugin Python.

Exit 0 when every checked function is within both ceilings, 1 on any
violation, 2 when a tool is missing or its output cannot be parsed. An empty
path list checks nothing and exits 0.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ESLINT_COMPLEXITY_RE = re.compile(r"^(?P<name>.+?) has a complexity of (?P<cc>\d+)\.")
DEFAULT_TS_COVERAGE_JSON = "coverage/coverage-final.json"


class ToolError(Exception):
    """A tool is missing or produced output this script cannot read."""


def crap(cc: int, coverage: float) -> float:
    return cc * cc * (1.0 - coverage) ** 3 + cc


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise ToolError(f"tool not found on PATH: {name}")


def load_json(source: Path | str) -> Any:
    try:
        text = Path(source).read_text(encoding="utf-8") if isinstance(source, Path) else source
        return json.loads(text)
    except (OSError, ValueError) as exc:
        raise ToolError(f"cannot parse JSON: {exc}") from exc


def same_file(key: str, path: Path, cwd: Path) -> bool:
    candidate = Path(key)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    try:
        return candidate.resolve() == path.resolve()
    except OSError:
        return False


def file_entry(report: dict[str, Any], path: Path, cwd: Path) -> Any:
    for key, value in report.items():
        if same_file(key, path, cwd):
            return value
    return None


# --- Python -----------------------------------------------------------------


def radon_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for block in blocks:
        if block.get("type") == "class":
            flat.extend(radon_blocks(block.get("methods", [])))
            continue
        flat.append(block)
        flat.extend(radon_blocks(block.get("closures", [])))
    return flat


def python_functions(args: argparse.Namespace, paths: list[Path], cwd: Path) -> list[dict[str, Any]]:
    if args.radon_json:
        radon = load_json(Path(args.radon_json))
    else:
        require_tool("radon")
        result = subprocess.run(
            ["radon", "cc", "--json", "--", *map(str, paths)],
            cwd=cwd, capture_output=True, text=True, shell=False, check=False,
        )
        if result.returncode != 0:
            raise ToolError(f"radon failed: {result.stderr.strip()}")
        radon = load_json(result.stdout)
    if args.coverage_json:
        coverage = load_json(Path(args.coverage_json))
    else:
        # Reads the .coverage data the slot command's `coverage run` produced.
        require_tool("coverage")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "coverage.json"
            result = subprocess.run(
                ["coverage", "json", "-q", "-o", str(out)],
                cwd=cwd, capture_output=True, text=True, shell=False, check=False,
            )
            if result.returncode != 0:
                raise ToolError(f"coverage json failed: {result.stderr.strip()}")
            coverage = load_json(out)
    files = coverage.get("files", {}) if isinstance(coverage, dict) else {}
    functions: list[dict[str, Any]] = []
    for path in paths:
        blocks = file_entry(radon, path, cwd) or []
        entry = file_entry(files, path, cwd) or {}
        executed = set(entry.get("executed_lines", []))
        missing = set(entry.get("missing_lines", []))
        for block in radon_blocks(blocks):
            lines = range(int(block["lineno"]), int(block["endline"]) + 1)
            hit = sum(1 for line in lines if line in executed)
            measured = hit + sum(1 for line in lines if line in missing)
            functions.append(
                {
                    "file": str(path),
                    "name": block.get("name", "?"),
                    "line": int(block["lineno"]),
                    "complexity": int(block["complexity"]),
                    "coverage": (hit / measured) if measured else 0.0,
                }
            )
    return functions


# --- TypeScript --------------------------------------------------------------


def typescript_functions(args: argparse.Namespace, paths: list[Path], cwd: Path) -> list[dict[str, Any]]:
    if args.eslint_json:
        eslint = load_json(Path(args.eslint_json))
    else:
        require_tool("eslint")
        result = subprocess.run(
            ["eslint", "--format", "json", "--rule", "complexity: [warn, {max: 0}]", "--", *map(str, paths)],
            cwd=cwd, capture_output=True, text=True, shell=False, check=False,
        )
        if result.returncode > 1:
            raise ToolError(f"eslint failed: {result.stderr.strip()[-2000:]}")
        eslint = load_json(result.stdout)
    # Reads the report the slot command's coverage run produced.
    coverage = load_json(Path(args.coverage_json) if args.coverage_json else cwd / DEFAULT_TS_COVERAGE_JSON)
    functions: list[dict[str, Any]] = []
    for path in paths:
        entry = file_entry(coverage, path, cwd) if isinstance(coverage, dict) else None
        entry = entry or {}
        fn_map = entry.get("fnMap", {})
        statements = entry.get("statementMap", {})
        hits = entry.get("s", {})
        for report in eslint if isinstance(eslint, list) else []:
            if not same_file(report.get("filePath", ""), path, cwd):
                continue
            for message in report.get("messages", []):
                if message.get("ruleId") != "complexity":
                    continue
                match = ESLINT_COMPLEXITY_RE.match(message.get("message", ""))
                if not match:
                    raise ToolError(f"unrecognised eslint complexity message: {message.get('message')!r}")
                line = int(message.get("line", 0))
                span = next(
                    (
                        (fn["loc"]["start"]["line"], fn["loc"]["end"]["line"])
                        for fn in fn_map.values()
                        if fn.get("decl", fn.get("loc", {})).get("start", {}).get("line") == line
                    ),
                    None,
                )
                if span is None:
                    cov = 0.0
                else:
                    ids = [sid for sid, loc in statements.items() if span[0] <= loc["start"]["line"] <= span[1]]
                    covered = sum(1 for sid in ids if int(hits.get(sid, 0)) > 0)
                    cov = (covered / len(ids)) if ids else 0.0
                functions.append(
                    {
                        "file": str(path),
                        "name": match.group("name"),
                        "line": line,
                        "complexity": int(match.group("cc")),
                        "coverage": cov,
                    }
                )
    return functions


# --- CLI ----------------------------------------------------------------------


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--language", choices=("python", "typescript"), required=True)
    parser.add_argument("--ceiling", type=float, required=True, help="maximum CRAP score per function")
    parser.add_argument("--complexity-ceiling", type=int, required=True, help="maximum cyclomatic complexity per function")
    parser.add_argument("--radon-json", help="pre-generated `radon cc --json` output")
    parser.add_argument("--eslint-json", help="pre-generated `eslint --format json` output")
    parser.add_argument("--coverage-json", help="coverage report to read (coverage.py JSON; Istanbul coverage-final.json, default coverage/coverage-final.json)")
    parser.add_argument("--report", help="write the full JSON report to this file")
    parser.add_argument("paths", nargs="*", help="changed source files; empty checks nothing and passes")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    cwd = Path.cwd()
    paths = [Path(p) for p in args.paths if p.strip()]
    report: dict[str, Any] = {
        "language": args.language,
        "ceiling": args.ceiling,
        "complexity_ceiling": args.complexity_ceiling,
        "checked": 0,
        "violations": [],
        "functions": [],
    }
    if paths:
        try:
            functions = python_functions(args, paths, cwd) if args.language == "python" else typescript_functions(args, paths, cwd)
        except ToolError as exc:
            print(f"crap-score: {exc}", file=sys.stderr)
            return 2
        for fn in functions:
            fn["crap"] = round(crap(fn["complexity"], fn["coverage"]), 2)
            fn["coverage"] = round(fn["coverage"], 4)
            reasons = []
            if fn["complexity"] > args.complexity_ceiling:
                reasons.append(f"complexity {fn['complexity']} > {args.complexity_ceiling}")
            if fn["crap"] > args.ceiling:
                reasons.append(f"CRAP {fn['crap']} > {args.ceiling:g}")
            if reasons:
                report["violations"].append({**fn, "reasons": reasons})
        report["functions"] = functions
        report["checked"] = len(functions)
    else:
        report["note"] = "no paths given; nothing checked"
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        Path(args.report).write_text(text + "\n", encoding="utf-8")
    print(text)
    for violation in report["violations"]:
        print(f"crap-score: {violation['file']}:{violation['line']} {violation['name']}: " + "; ".join(violation["reasons"]), file=sys.stderr)
    return 1 if report["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
