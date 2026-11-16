#!/usr/bin/env python3
"""Require disclosure of removed tests and net assertion losses.

Run from the repository root with BASE_REF, HEAD_REF (default HEAD), and PR_BODY.
Reads committed blobs at merge-base(BASE_REF, HEAD_REF) and HEAD_REF. Python
uses ast; Go declarations use a masked lexical scan. No source is executed,
and only Python's standard library and git are needed.

Assertion losses compare shared paths individually. Vanished paths consume
assertion credit from appeared paths in the same directory, once each; any
remaining loss is attributed to the old path in sorted order.
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
GO_TOKEN = re.compile(r"\bfunc\s+(\w+)\s*\(|[()[\]{}]")
GO_TEST_NAME = re.compile(r"(?:(?:Test|Benchmark|Fuzz)(?![a-z])\w*|Example\w*)\Z")
GO_ASSERTION = re.compile(r"\b(?:t\.(?:Fatalf?|Errorf?)\s*\(|(?:require|assert)\.)")
PY_ASSERTION = re.compile(r"\bassert\s+|\bself\.assert\w*\s*\(|\bpytest\.raises\s*\(")


@dataclass(frozen=True)
class TestFile:
    names: tuple[str, ...]
    assertions: int


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


def python_names(source: bytes) -> tuple[str, ...]:
    tree = ast.parse(source)
    # Only module-level tests and class methods, not nested helper functions.
    nodes: list[ast.AST] = list(tree.body)
    names = []
    while nodes:
        node = nodes.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                names.append(node.name)
        else:
            nodes.extend(ast.iter_child_nodes(node))
    return tuple(names)


def mask_non_code(source: bytes, *, go: bool) -> str:
    text = source.decode("utf-8")
    if go:
        return GO_LITERALS.sub(lambda match: re.sub(r"[^\n]", " ", match[0]), text)
    literal_tokens = (
        tokenize.COMMENT, tokenize.STRING,
        *(getattr(tokenize, name, None) for name in (
            "FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END",
            "TSTRING_START", "TSTRING_MIDDLE", "TSTRING_END",
        )),
    )
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    return tokenize.untokenize(
        token._replace(string=re.sub(r"[^\n]", " ", token.string))
        if token.type in literal_tokens else token
        for token in tokens
    )


def go_names(source: bytes) -> tuple[str, ...]:
    masked = mask_non_code(source, go=True)
    if not re.match(r"\s*package\s+\w+", masked):
        raise ValueError("Go file has no package declaration")
    names = []
    stack: list[str] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for token in GO_TOKEN.finditer(masked):
        name = token[1]
        if name and not stack and GO_TEST_NAME.fullmatch(name):
            names.append(name)
        delimiter = token[0][-1]
        if delimiter in "([{":
            stack.append(delimiter)
        elif not stack or stack.pop() != pairs[delimiter]:
            raise ValueError("Go file has mismatched delimiters")
    if stack:
        raise ValueError("Go file has unclosed delimiters")
    return tuple(names)


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
            names = go_names(source) if path.endswith(".go") else python_names(source)
            pattern = GO_ASSERTION if path.endswith(".go") else PY_ASSERTION
            masked = mask_non_code(source, go=path.endswith(".go"))
            count = sum(bool(pattern.search(line)) for line in masked.splitlines())
        except (SyntaxError, UnicodeError, ValueError) as exc:
            raise ValueError(f"unparseable test file {path} at {ref}: {exc}") from exc
        files[path] = TestFile(names, count)
    return files


def move_scope(path: str) -> str:
    return str(PurePosixPath(path).parent)


def removed_tests(before: dict[str, TestFile], after: dict[str, TestFile]) -> list[tuple[str, str]]:
    # Match unchanged identities first, then consume newly located functions
    # once each. A pre-existing namesake must not hide a removal.
    removed: list[tuple[str, str]] = []
    added: Counter[tuple[str, str]] = Counter()
    for path in sorted(before.keys() | after.keys()):
        old = Counter(before.get(path, TestFile((), 0)).names)
        new = Counter(after.get(path, TestFile((), 0)).names)
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


def assertion_losses(before: dict[str, TestFile], after: dict[str, TestFile]) -> dict[str, int]:
    losses = {
        path: before[path].assertions - after[path].assertions
        for path in before.keys() & after.keys()
    }
    added: Counter[str] = Counter()
    for path in after.keys() - before.keys():
        added[move_scope(path)] += after[path].assertions
    for path in sorted(before.keys() - after.keys()):
        scope = move_scope(path)
        credit = min(before[path].assertions, added[scope])
        added[scope] -= credit
        losses[path] = before[path].assertions - credit
    return losses


def disclosures(before: dict[str, TestFile], after: dict[str, TestFile]) -> list[tuple[tuple[str, ...], str]]:
    entries: list[tuple[tuple[str, ...], str]] = [
        ((path, name), f"- Removed or renamed `{name}` (`{path}`).")
        for path, name in removed_tests(before, after)
    ]
    for path, lost in sorted(assertion_losses(before, after).items()):
        if lost > 0:
            noun = "line" if lost == 1 else "lines"
            entries.append(((path,), f"- Lost assertions: `{path}` ({lost} net assertion {noun} lost)."))
    return entries


def missing_disclosures(entries: list[tuple[tuple[str, ...], str]], section: str) -> list[str]:
    missing = []
    patterns = {
        token: re.compile(rf"(?<![\w./-]){re.escape(token)}(?![\w./-])")
        for tokens, _ in entries for token in tokens
    }
    lines = [
        Counter({token: len(pattern.findall(line)) for token, pattern in patterns.items()})
        for line in section.splitlines()
    ]
    for tokens, description in entries:
        for mentions in lines:
            if all(mentions[token] for token in tokens):
                if len(tokens) > 1:
                    mentions[tokens[1]] -= 1
                break
        else:
            missing.append(description)
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
    print("Test changes: " + ("all changes disclosed." if entries else "no removals or assertion losses."))
    for _, description in entries:
        print(description)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
