#!/usr/bin/env python3
"""Require disclosure of removed tests and of lost or changed assertions.

Run from the repository root with BASE_REF, HEAD_REF (default HEAD), and PR_BODY.
Reads committed blobs at merge-base(BASE_REF, HEAD_REF) and HEAD_REF. Python
uses ast; Go declarations use a masked lexical scan. No source is executed,
and only Python's standard library and git are needed.

Assertions are compared per function: a top-level function, a class method
(`Class.method`), a Go receiver method (`Receiver.Method`), or a file's module
scope. A function found at head in the same directory, in any file, is the same
function. Each base assertion statement, compared without comments or
whitespace, that the head function lacks is lost (the count fell) or changed,
and needs a disclosure line naming the function and its base path.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import subprocess
import sys
import tokenize
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_note_policy import FenceOpening, is_closing_fence, opening_fence  # noqa: E402

GO_LITERALS = re.compile(r'//[^\n]*|/\*.*?\*/|`[^`]*`|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S)
# A depth-0 match opens a scope: a receiver method, a function, or a var/const/type/import block.
GO_TOKEN = re.compile(
    r"\bfunc\s*\(([^(){}]*)\)\s*(\w+)\s*\(|\bfunc\s+(\w+)\s*[(\[]"
    r"|\b(?:var|const|type|import)\b|[()[\]{}]"
)
GO_RECEIVER_TYPE = re.compile(r"(\w+)\s*(?:\[[^\]]*\])?\s*\Z")
GO_TEST_NAME = re.compile(r"(?:(?:Test|Benchmark|Fuzz)(?![a-z])\w*|Example\w*)\Z")
GO_ASSERTION = re.compile(r"\b(?:t\.(?:Fatalf?|Errorf?)\s*\(|(?:require|assert)\.)")
PY_ASSERTION = re.compile(r"\bassert\s+|\bself\.assert\w*\s*\(|\bpytest\.raises\s*\(")
PY_STRING_OPENERS = {getattr(tokenize, name, None) for name in ("FSTRING_START", "TSTRING_START")} - {None}
PY_STRING_CLOSERS = {getattr(tokenize, name, None) for name in ("FSTRING_END", "TSTRING_END")} - {None}
# Assertion scope for code outside every function; module scopes never move between files.
MODULE = ""


@dataclass(frozen=True)
class TestFile:
    names: tuple[str, ...]
    # Function key (`name`, `Class.method`, `Receiver.Method`, or MODULE) -> normalized assertion statements.
    assertions: dict[str, tuple[str, ...]]


EMPTY = TestFile((), {})


@dataclass(frozen=True)
class Disclosure:
    tokens: tuple[str, ...]  # (path, name) for a function, (path,) for a module scope
    description: str
    kind: str  # "removed" test name, "vanished" function, or "changed" function present at head


@dataclass(frozen=True)
class Layout:
    names: tuple[str, ...]
    owners: list[str]
    keys: frozenset[str]


def command(arguments: list[str]) -> bytes:
    result = subprocess.run(
        ["git", *arguments], capture_output=True, check=False, shell=False,
    )
    return command_output(result, "git")


def command_output(result: subprocess.CompletedProcess[bytes], executable: str) -> bytes:
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"{executable} failed (exit {result.returncode}): {detail}")
    return result.stdout


def commit_ref(ref: str) -> str:
    if not ref:
        raise ValueError("BASE_REF and HEAD_REF must be non-empty")
    return command(["rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"]).decode().strip()


def is_test_file(path: str, registered: set[str]) -> bool:
    file = PurePosixPath(path)
    if path.endswith("_test.go"):
        return True
    if file.suffix != ".py":
        return False
    if path in registered:
        return True
    if not path.startswith("tests/"):
        return False
    return (
        file.name.startswith("test_") or file.name.endswith("_test.py")
        or (path.startswith("tests/speckit-pro/") and file.name.startswith("test-"))
    )


def source_rows(text: str) -> list[str]:
    return io.StringIO(text).readlines()


def blank(text: str) -> str:
    return re.sub(r"[^\r\n]", " ", text)


def blank_span(rows: list[list[str]], start: tuple[int, int], end: tuple[int, int]) -> None:
    for index in range(start[0] - 1, end[0]):
        row = rows[index]
        first = start[1] if index == start[0] - 1 else 0
        last = end[1] if index == end[0] - 1 else len(row)
        for column in range(first, min(last, len(row))):
            if row[column] not in "\r\n":
                row[column] = " "


def python_views(text: str) -> tuple[list[str], list[str]]:
    """Return rows with comments and literals blanked, and rows with only comments blanked."""
    code = [list(row) for row in source_rows(text)]
    readable = [list(row) for row in source_rows(text)]
    opened: list[tuple[int, int]] = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type in PY_STRING_OPENERS:
            opened.append(token.start)
        elif token.type in PY_STRING_CLOSERS:
            # Blank the whole outermost f-string or t-string, interpolations included.
            start = opened.pop()
            if not opened:
                blank_span(code, start, token.end)
        elif token.type == tokenize.STRING and not opened:
            blank_span(code, token.start, token.end)
        if token.type == tokenize.COMMENT:
            blank_span(code, token.start, token.end)
            blank_span(readable, token.start, token.end)
    return ["".join(row) for row in code], ["".join(row) for row in readable]


def python_functions(tree: ast.Module) -> list[tuple[str, int, int, bool]]:
    """Functions and classes outside every function, as (key, first row, last row, is_function), outer first."""
    found: list[tuple[str, int, int, bool]] = []

    def walk(nodes: list[ast.AST], prefix: str) -> None:
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                key = prefix + node.name
                first = min([decorator.lineno for decorator in node.decorator_list] + [node.lineno])
                is_function = not isinstance(node, ast.ClassDef)
                found.append((key, first, node.end_lineno or node.lineno, is_function))
                if not is_function:
                    walk(list(node.body), key + ".")
            else:
                walk(list(ast.iter_child_nodes(node)), prefix)

    walk(list(tree.body), "")
    return found


def python_layout(tree: ast.Module, rows: int) -> Layout:
    functions = python_functions(tree)
    owners = [MODULE] * rows
    for key, first, last, _ in functions:
        owners[first - 1:last] = [key] * (last - first + 1)
    names = tuple(
        key.rsplit(".", 1)[-1] for key, _, _, is_function in functions
        if is_function and key.rsplit(".", 1)[-1].startswith("test_")
    )
    return Layout(names, owners, frozenset(key for key, *_ in functions))


def go_scope(token: re.Match[str]) -> str | None:
    if token[3]:
        return token[3]
    if token[2]:
        receiver = GO_RECEIVER_TYPE.search(token[1].strip())
        if receiver is None:
            raise ValueError(f"Go method {token[2]} has an unreadable receiver")
        return f"{receiver[1]}.{token[2]}"
    return MODULE if token[0][-1].isalpha() else None


def go_top_level_tokens(masked: str) -> list[re.Match[str]]:
    """GO_TOKEN matches outside every bracket; unbalanced brackets fail."""
    found = []
    stack: list[str] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for token in GO_TOKEN.finditer(masked):
        if not stack:
            found.append(token)
        delimiter = token[0][-1]
        if delimiter in "([{":
            stack.append(delimiter)
        elif delimiter in pairs and (not stack or stack.pop() != pairs[delimiter]):
            raise ValueError("Go file has mismatched delimiters")
    if stack:
        raise ValueError("Go file has unclosed delimiters")
    return found


def go_layout(masked: str) -> Layout:
    if not re.match(r"\s*package\s+\w+", masked):
        raise ValueError("Go file has no package declaration")
    names = []
    starts: list[tuple[int, str]] = []
    for token in go_top_level_tokens(masked):
        scope = go_scope(token)
        if scope is not None:
            starts.append((masked.count("\n", 0, token.start()), scope))
            if token[3] and token[0][-1] == "(" and GO_TEST_NAME.fullmatch(token[3]):
                names.append(token[3])
    owners = [MODULE] * len(source_rows(masked))
    for row, scope in starts:
        owners[row:] = [scope] * (len(owners) - row)
    return Layout(tuple(names), owners, frozenset(scope for _, scope in starts))


def statement_end(code: list[str], row: int, column: int) -> int:
    """Last row of the statement starting at (row, column): brackets still open, or a backslash, continue it."""
    depth, segment = 0, code[row][column:]
    while True:
        depth += sum(map(segment.count, "([{")) - sum(map(segment.count, ")]}"))
        if (depth <= 0 and not segment.rstrip().endswith("\\")) or row + 1 == len(code):
            return row
        row += 1
        segment = code[row]


def parse_test_file(path: str, source: bytes) -> TestFile:
    text = source.decode("utf-8")
    if path.endswith(".go"):
        code = source_rows(GO_LITERALS.sub(lambda match: blank(match[0]), text))
        readable = source_rows(GO_LITERALS.sub(
            lambda match: blank(match[0]) if match[0][:2] in ("//", "/*") else match[0], text,
        ))
        layout, pattern = go_layout("".join(code)), GO_ASSERTION
    else:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        tree = ast.parse(text)
        code, readable = python_views(text)
        layout, pattern = python_layout(tree, len(code)), PY_ASSERTION
    assertions: dict[str, list[str]] = {key: [] for key in layout.keys | {MODULE}}
    for row, line in enumerate(code):
        if match := pattern.search(line):
            last = statement_end(code, row, match.start())
            assertions[layout.owners[row]].append(" ".join(" ".join(readable[row:last + 1]).split()))
    return TestFile(layout.names, {key: tuple(lines) for key, lines in assertions.items()})


def registered_tests(ref: str) -> set[str]:
    path = "tests/speckit-pro/suite-manifest.json"
    try:
        manifest = json.loads(command(["show", f"{ref}:{path}"]))
        layers = manifest["layers"]
        if not isinstance(layers, list):
            raise ValueError("layers must be a list")
        paths = set()
        for layer in layers:
            scripts = layer["scripts"]
            if not isinstance(scripts, list):
                raise ValueError("scripts must be a list")
            for script in scripts:
                name = script["path"]
                if not isinstance(name, str) or not name:
                    raise ValueError("script path must be non-empty text")
                paths.add(name)
        return paths
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"unreadable or unparseable {path} at {ref}: {exc}") from exc


def inventory(ref: str, registered: set[str]) -> dict[str, TestFile]:
    paths = command(["ls-tree", "-r", "--name-only", "-z", ref]).decode("utf-8").split("\0")
    files = {}
    for path in paths:
        if not is_test_file(path, registered):
            continue
        source = command(["show", f"{ref}:{path}"])
        try:
            files[path] = parse_test_file(path, source)
        except (SyntaxError, UnicodeError, ValueError, tokenize.TokenError) as exc:
            raise ValueError(f"unparseable test file {path} at {ref}: {exc}") from exc
    return files


def move_scope(path: str) -> str:
    return str(PurePosixPath(path).parent)


def removed_tests(before: dict[str, TestFile], after: dict[str, TestFile]) -> list[tuple[str, str]]:
    # Match unchanged identities first, then consume newly located functions
    # once each. A pre-existing namesake must not hide a removal.
    removed: list[tuple[str, str]] = []
    added: Counter[tuple[str, str]] = Counter()
    for path in sorted(before.keys() | after.keys()):
        old = Counter(before.get(path, EMPTY).names)
        new = Counter(after.get(path, EMPTY).names)
        removed.extend((path, name) for name in (old - new).elements())
        added.update((move_scope(path), name) for name in (new - old).elements())
    missing = []
    for path, name in removed:
        key = (move_scope(path), name)
        if added[key]:
            added[key] -= 1
        else:
            missing.append((path, name))
    return missing


def disclosure_section(body: str) -> str:
    body = re.sub(r"<!--.*?(?:-->|\Z)", "", body, flags=re.S)
    section = []
    active = False
    fence: FenceOpening | None = None
    for line in body.splitlines():
        if fence is not None:
            if is_closing_fence(line, fence):
                fence = None
        elif (opening := opening_fence(line)) is not None:
            fence = opening
        else:
            heading = re.match(r"^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$", line)
            if heading and len(heading[1]) <= 2:
                active = heading[1] == "##" and heading[2] == "Test changes"
                continue
        if active:
            section.append(line)
    return "\n".join(section)


def scoped_assertions(files: dict[str, TestFile]) -> dict[tuple[str, str], dict[str, tuple[str, ...]]]:
    """Key each function by (directory, function key); a module scope stays keyed by its own path."""
    keyed: dict[tuple[str, str], dict[str, tuple[str, ...]]] = {}
    for path, file in files.items():
        for key, statements in file.assertions.items():
            scope = path if key == MODULE else move_scope(path)
            keyed.setdefault((scope, key), {})[path] = statements
    return keyed


def paired_paths(old: set[str], new: set[str]) -> list[tuple[str, str | None]]:
    """Pair each base path with a head path: the same path first, then moved copies in sorted order."""
    moved_to = sorted(new - old)
    moved_from = sorted(old - new)
    return [(path, path) for path in sorted(old & new)] + [
        (path, moved_to[index] if index < len(moved_to) else None) for index, path in enumerate(moved_from)
    ]


def plural(count: int) -> str:
    return "line" if count == 1 else "lines"


def assertion_disclosure(path: str, key: str, old: tuple[str, ...], new: tuple[str, ...] | None) -> Disclosure | None:
    head = new or ()
    missing = sum((Counter(old) - Counter(head)).values())
    if not missing:
        return None
    lost = max(0, len(old) - len(head))
    counts = [f"{lost} net assertion {plural(lost)} lost"] if lost else []
    if missing > lost:
        counts.append(f"{missing - lost} assertion {plural(missing - lost)} changed")
    owner, _, name = key.rpartition(".")
    where = f"in `{name}`" + (f" of `{owner}`" if owner else "") if name else "at module level"
    return Disclosure(
        (path, name) if name else (path,),
        f"- {'Lost' if lost else 'Changed'} assertions: `{path}` ({', '.join(counts)}) {where}.",
        "vanished" if new is None else "changed",
    )


def assertion_disclosures(before: dict[str, TestFile], after: dict[str, TestFile]) -> list[Disclosure]:
    # A function found at head in the same directory, in any file, is the same
    # function; every base assertion statement missing from it needs disclosure.
    base, head = scoped_assertions(before), scoped_assertions(after)
    found = []
    for scope_key, olds in base.items():
        news = head.get(scope_key, {})
        for path, target in paired_paths(set(olds), set(news)):
            entry = assertion_disclosure(path, scope_key[1], olds[path], None if target is None else news[target])
            if entry is not None:
                found.append(entry)
    return sorted(found, key=lambda entry: (entry.tokens[0], entry.description))


def disclosures(before: dict[str, TestFile], after: dict[str, TestFile]) -> list[Disclosure]:
    removals = [
        Disclosure((path, name), f"- Removed or renamed `{name}` (`{path}`).", "removed")
        for path, name in removed_tests(before, after)
    ]
    return removals + assertion_disclosures(before, after)


def required_mentions(group: list[Disclosure]) -> int:
    kinds = Counter(entry.kind for entry in group)
    # A removed test and the assertions that left with it share one line.
    return sum(kinds.values()) - min(kinds["removed"], kinds["vanished"])


def missing_disclosures(entries: list[Disclosure], section: str) -> list[str]:
    patterns = {
        token: re.compile(rf"(?<![\w./-]){re.escape(token)}(?![\w./-])")
        for entry in entries for token in entry.tokens
    }
    lines = [
        Counter({token: len(pattern.findall(line)) for token, pattern in patterns.items()})
        for line in section.splitlines()
    ]
    groups: dict[tuple[str, ...], list[Disclosure]] = {}
    for entry in entries:
        groups.setdefault(entry.tokens, []).append(entry)
    missing: list[str] = []
    for tokens, group in groups.items():
        for _ in range(required_mentions(group)):
            mentions = next((line for line in lines if all(line[token] for token in tokens)), None)
            if mentions is None:
                missing.extend(entry.description for entry in group)
                break
            if len(tokens) > 1:
                mentions[tokens[1]] -= 1
    return missing


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        base = commit_ref(os.environ.get("BASE_REF", ""))
        head = commit_ref(os.environ.get("HEAD_REF", "HEAD"))
        merge_base = command(["merge-base", base, head]).decode().strip()
        registered = registered_tests(merge_base) | registered_tests(head)
        entries = disclosures(inventory(merge_base, registered), inventory(head, registered))
        missing = missing_disclosures(entries, disclosure_section(os.environ.get("PR_BODY", "")))
    except (OSError, ValueError, UnicodeError) as exc:
        print("::error::Test changes check failed.", file=sys.stderr)
        print(f"Reason: {str(exc)!r}", file=sys.stderr)
        return 1
    if missing:
        print("::error::Test changes require disclosure in a ## Test changes section.", file=sys.stderr)
        print("Missing disclosures (paste into the PR body):\n## Test changes", file=sys.stderr)
        print("\n".join(missing), file=sys.stderr)
        return 1
    print("Test changes: " + ("all changes disclosed." if entries else "no removed tests or lost or changed assertions."))
    for entry in entries:
        print(entry.description)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
