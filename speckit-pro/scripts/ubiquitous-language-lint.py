#!/usr/bin/env python3
"""Advisory lint: flag declared identifiers in a diff that map to no domain term.

Reads the terms document (default ``docs/ai/specs/ubiquitous-language.md``),
whose tables carry ``Term | Meaning here | Identifiers`` rows, and the
identifiers a diff declares (``def``/``class`` in Python; ``function``,
``class``, ``interface``, ``type``, ``enum``, ``const``, ``let``, ``var`` in
TypeScript and JavaScript). An identifier maps to a term when the term's
Identifiers column names it, or when one of the term's words (three letters
or more) appears among the identifier's words after splitting camelCase and
snake_case. Everything else is reported.

This lint is advisory only: it always exits 0 (2 for a usage error), prints
a JSON report, and writes it to ``--report`` when asked. It never blocks a
gate; the orchestrator mirrors the summary into the Self-Review findings.
A missing terms document lints nothing and says so.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_TERMS = "docs/ai/specs/ubiquitous-language.md"
DECLARATION_RES = (
    re.compile(r"^\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)"),
    re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?(?:function\*?|class|interface|type|enum)\s+([A-Za-z_$]\w*)"),
    re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$]\w*)"),
)
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
WORD_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+")
MIN_WORD = 3


def words(text: str) -> set[str]:
    return {w.lower() for w in WORD_RE.findall(text) if len(w) >= MIN_WORD}


def parse_terms(text: str) -> list[dict[str, Any]]:
    """Every table row under a header whose first cell is Term."""
    terms: list[dict[str, Any]] = []
    columns: list[str] | None = None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            columns = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if columns is None:
            if cells and cells[0].lower() == "term":
                columns = [c.lower() for c in cells]
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        row = dict(zip(columns, cells))
        term = row.get("term", "").strip("`* ")
        if not term:
            continue
        identifiers = {i.strip("` ") for i in re.split(r"[,\s]+", row.get("identifiers", "")) if i.strip("` ")}
        terms.append({"term": term, "meaning": row.get("meaning here", row.get("meaning", "")), "identifiers": identifiers, "words": words(term) | {w for i in identifiers for w in words(i)}})
    return terms


def declared_identifiers(diff: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    path = ""
    line_no = 0
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            path = raw[4:].strip()
            path = path[2:] if path.startswith("b/") else path
            continue
        if raw.startswith("@@"):
            match = re.search(r"\+(\d+)", raw)
            line_no = int(match.group(1)) - 1 if match else 0
            continue
        if raw.startswith("-") or raw.startswith("\\"):
            continue
        line_no += 1
        if not raw.startswith("+") or Path(path).suffix not in SOURCE_SUFFIXES:
            continue
        body = raw[1:]
        for pattern in DECLARATION_RES:
            match = pattern.match(body)
            if match:
                found.append({"file": path, "line": line_no, "identifier": match.group(1)})
                break
    return found


def mapped_term(identifier: str, terms: list[dict[str, Any]]) -> str | None:
    id_words = words(identifier)
    for term in terms:
        if identifier in term["identifiers"] or (term["words"] and term["words"] & id_words):
            return term["term"]
    return None


def git_diff(base: str, paths: list[str]) -> str:
    result = subprocess.run(
        ["git", "diff", "--unified=0", "--no-color", f"{base}...HEAD", "--", *paths],
        capture_output=True, text=True, shell=False, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git diff failed")
    return result.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--terms", default=DEFAULT_TERMS, help="terms document (Markdown tables: Term | Meaning here | Identifiers)")
    parser.add_argument("--base", default="origin/main", help="diff base; identifiers come from <base>...HEAD")
    parser.add_argument("--diff", help="read a unified diff from this file instead of running git")
    parser.add_argument("--report", help="write the JSON report here as well as to stdout")
    parser.add_argument("paths", nargs="*", help="restrict the diff to these paths")
    args = parser.parse_args(argv)
    report: dict[str, Any] = {"advisory": True, "terms_document": args.terms, "terms": 0, "declared": 0, "unmapped": [], "note": ""}
    terms_path = Path(args.terms)
    if not terms_path.is_file():
        report["note"] = "no terms document; nothing linted"
    else:
        terms = parse_terms(terms_path.read_text(encoding="utf-8"))
        report["terms"] = len(terms)
        try:
            diff = Path(args.diff).read_text(encoding="utf-8") if args.diff else git_diff(args.base, args.paths)
        except (OSError, RuntimeError) as exc:
            report["note"] = f"diff unavailable: {exc}"
            diff = ""
        declared = declared_identifiers(diff)
        report["declared"] = len(declared)
        for item in declared:
            if mapped_term(item["identifier"], terms) is None:
                report["unmapped"].append(item)
        if not report["note"]:
            report["note"] = (
                f"{len(report['unmapped'])} of {len(declared)} declared identifiers map to no term"
                if report["unmapped"] else f"all {len(declared)} declared identifiers map to a term"
            )
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        Path(args.report).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
