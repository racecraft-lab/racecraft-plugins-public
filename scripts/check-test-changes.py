#!/usr/bin/env python3
"""Require disclosure of removed tests and of lost or changed assertions.

Run from the repository root with BASE_REF, HEAD_REF (default HEAD), and PR_BODY.
Reads committed blobs at merge-base(BASE_REF, HEAD_REF) and HEAD_REF. Python
is read as a syntax tree (ast) and Go as a token stream from a small lexer
here. No source is executed, and only Python's standard library and git are
needed. A file that cannot be read at either ref fails the check.

Assertions are compared per function: a top-level function, a class method
(`Class.method`), a Go receiver method (`Receiver.Method`), or a file's module
scope. A function found at head in the same directory, in any file, is the same
function. An assertion is one assert statement or one assertion call, however
many lines it spans. It is compared by its code alone: literal contents are
exact, and comments and layout are ignored. Each base assertion that the head
function lacks is lost (the count fell) or changed, and needs a disclosure line
naming the function and its base path.

A Go assertion is a failure call on a test value named t, b, f or tb, or a
testify `require.` or `assert.` call. Redundant parentheses, a pointer
indirection and a method expression are read as the same call: `(t).Error(1)`,
`(t.Error)(1)`, `(*t).Error(1)` and `(*testing.T).Error(t, 1)`. A call reached
another way (another name, a conversion, a type assertion, a stored method
value) is not counted.
"""

from __future__ import annotations

import argparse
import ast
import itertools
import json
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_note_policy import FenceOpening, is_closing_fence, opening_fence  # noqa: E402

GO_KEYWORDS = frozenset(
    "break case chan const continue default defer else fallthrough for func go goto if import interface map "
    "package range return select struct switch type var".split()
)
# One Go lexeme: skipped whitespace or a comment, or a token. An unterminated comment or literal matches nothing.
GO_LEXEME = re.compile(
    r"(?P<skip>\s+|//[^\n]*|/\*.*?\*/)|(?P<token>"
    r"`[^`]*`|\"(?:\\[^\n]|[^\"\\\n])*\"|'(?:\\[^\n]|[^'\\\n])+'"  # raw string, string, rune
    r"|0[xX][0-9a-fA-F_]*(?:\.[0-9a-fA-F_]*)?(?:[pP][-+]?[0-9_]+)?i?|0[bBoO][0-9_]+i?"
    r"|(?:[0-9][0-9_]*(?:\.[0-9_]*)?|\.[0-9][0-9_]*)(?:[eE][-+]?[0-9_]+)?i?"
    r"|[^\W\d]\w*"  # a name or keyword
    r"|<<=|>>=|&\^=|\.\.\.|&&|\|\||<-|\+\+|--|<<|>>|&\^|[-+*%&|^<>=!:]=|/(?!\*)=?|[-+*%&|^<>=!~()\[\]{},;.:])",
    re.S,
)
GO_TEST_NAME = re.compile(r"(?:(?:Test|Benchmark|Fuzz)(?![a-z])\w*|Example\w*)\Z")
# Failure calls on the conventional testing.T, B, F and TB names, and the testify packages.
GO_TESTING_NAMES = frozenset({"t", "b", "f", "tb"})
GO_TESTING_TYPES = frozenset({"T", "B", "F", "TB"})
GO_FAILURE_CALLS = frozenset({"Fatal", "Fatalf", "Error", "Errorf", "FailNow", "Fail"})
GO_TESTIFY = frozenset({"require", "assert"})
PY_FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
# Assertion scope for code outside every function; module scopes never move between files.
MODULE = ""


@dataclass(frozen=True)
class TestFile:
    names: tuple[str, ...]
    # Function key (`name`, `Class.method`, `Receiver.Method`, or MODULE) -> each assertion in canonical form.
    assertions: dict[str, tuple[str, ...]]


EMPTY = TestFile((), {})


@dataclass(frozen=True)
class Disclosure:
    tokens: tuple[str, ...]  # (path, name) for a function, (path,) for a module scope
    description: str
    kind: str  # "removed" test name, "vanished" function, or "changed" function present at head


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


def is_go_name(token: str) -> bool:
    return (token[:1] == "_" or token[:1].isalpha()) and token not in GO_KEYWORDS


def go_ends_statement(token: str) -> bool:
    """Go's rule for a line's last token: a name, a literal, one of four keywords or a closer ends the statement."""
    if token in GO_KEYWORDS:
        return token in ("break", "continue", "fallthrough", "return")
    is_number = token[0].isdigit() or (token[0] == "." and token[1:2].isdigit())
    return token in ("++", "--", ")", "]", "}") or token[0] in "\"'`" or is_number or is_go_name(token)


def go_tokens(text: str) -> list[str]:
    """Go tokens in source order: comments dropped, and a `;` added where Go ends a statement at a line break.

    A literal keeps its quotes, so it never equals a name. A raw string drops its carriage returns, as in Go.
    """
    tokens: list[str] = []
    position = 0
    while position < len(text):
        lexeme = GO_LEXEME.match(text, position)
        if lexeme is None:
            raise ValueError(f"Go file has an unreadable token on line {text.count(chr(10), 0, position) + 1}")
        token = lexeme["token"]
        if token:
            tokens.append(token.replace("\r", "") if token[0] == "`" else token)
        elif "\n" in lexeme[0] and tokens and go_ends_statement(tokens[-1]):
            tokens.append(";")
        position = lexeme.end()
    if tokens and go_ends_statement(tokens[-1]):
        tokens.append(";")
    return tokens


def go_chain(tokens: list[str]) -> list[str] | None:
    """The `name.name` chain of an operand that is only names, dots and leading `*`; None for anything else."""
    chain = list(itertools.dropwhile(lambda token: token == "*", tokens))
    is_chain = len(chain) % 2 == 1 and all(map(is_go_name, chain[::2])) and all(dot == "." for dot in chain[1::2])
    return chain if is_chain else None


def go_groups_after(before: str) -> bool:
    """Whether a `(` after `before` groups an expression, not call arguments, a type assertion or a signature."""
    return not (before in (")", "]", "}", ".", "func") or is_go_name(before))


def go_unwrapped(content: list[str], before: str, after: list[str]) -> list[str] | None:
    """What `(content)` reads as without its parentheses, or None when it needs them."""
    chain = go_chain(content)
    if chain is None or not go_groups_after(before):
        return None
    selects = after[:1] == ["."] and is_go_name("".join(after[1:2]))
    # A bare chain needs no parentheses anywhere; `(*x)` needs none before a selected name.
    return chain if content == chain or selects else None


def go_plain(tokens: list[str], closers: dict[int, int], start: int, stop: int) -> list[str]:
    """The tokens from `start` to `stop` without redundant parentheses, so one call has one spelling.

    `(t).Error(1)`, `(t.Error)(1)`, `((t)).Error(1)` and `(*t).Error(1)` all read as `t.Error(1)`: a selector
    reaches through a pointer, so the `*` is redundant there too. Only a pair that groups one operand goes.
    """
    plain: list[str] = []
    index = start
    while index < stop:
        if tokens[index] != "(":
            plain.append(tokens[index])
            index += 1
            continue
        first, last = index + 1, closers[index]
        while tokens[first:first + 1] == ["("] and closers[first] == last - 1:
            first, last = first + 1, last - 1  # `((x))` is `(x)`
        content = go_plain(tokens, closers, first, last)
        index = closers[index] + 1
        operand = go_unwrapped(content, plain[-1] if plain else "", tokens[index:index + 2])
        plain += ["(", *content, ")"] if operand is None else operand
    return plain


def go_closers(tokens: list[str]) -> dict[int, int]:
    """Index of each opening delimiter -> index of its closing delimiter; unbalanced delimiters fail."""
    pairs = {")": "(", "]": "[", "}": "{"}
    closers = {}
    opened: list[int] = []
    for index, token in enumerate(tokens):
        if token in pairs.values():
            opened.append(index)
        elif token in pairs:
            if not opened or tokens[opened[-1]] != pairs[token]:
                raise ValueError("Go file has mismatched delimiters")
            closers[opened.pop()] = index
    if opened:
        raise ValueError("Go file has unclosed delimiters")
    return closers


def go_receiver_type(receiver: list[str], method: str) -> str:
    """The receiver's type name: the last name before any type parameters, closing punctuation aside."""
    typed = receiver[:receiver.index("[")] if "[" in receiver else receiver
    named = [token for token in typed if token not in (")", ",")]
    if not named or not is_go_name(named[-1]):
        raise ValueError(f"Go method {method} has an unreadable receiver")
    return named[-1]


def go_scope(tokens: list[str], index: int, closers: dict[int, int]) -> str | None:
    """The scope a top-level token opens: a receiver method, a function, or a var/const/type/import block."""
    if tokens[index] in ("var", "const", "type", "import"):
        return MODULE
    if tokens[index] != "func":
        return None
    has_receiver = tokens[index + 1:index + 2] == ["("]
    start = closers[index + 1] + 1 if has_receiver else index + 1
    name, opener = (tokens[start:start + 2] + ["", ""])[:2]
    # A method takes `(` after its name; a function may take `[` for type parameters instead.
    openers = ("(",) if has_receiver else ("(", "[")
    if not is_go_name(name) or opener not in openers:
        return None
    return f"{go_receiver_type(tokens[index + 2:start - 1], name)}.{name}" if has_receiver else name


def go_scopes(tokens: list[str], closers: dict[int, int]) -> dict[int, str]:
    """Index of each scope-opening token outside every delimiter -> its scope."""
    scopes = {}
    index = 0
    while index < len(tokens):
        scope = go_scope(tokens, index, closers)
        if scope is not None:
            scopes[index] = scope
        index = closers.get(index, index) + 1
    return scopes


def go_assertion_end(tokens: list[str], index: int, closers: dict[int, int]) -> int | None:
    """Index past the assertion that starts at `index`, or None when no assertion starts there."""
    receiver, dot, method, opener = (tokens[index:index + 4] + [""] * 3)[:4]
    # `testing.T.Error(t, 1)`, a method expression, is another spelling of `t.Error(1)`.
    is_method_expression = receiver in GO_TESTING_TYPES and tokens[max(index - 2, 0):index] == ["testing", "."]
    on_test = receiver in GO_TESTING_NAMES or is_method_expression
    is_failure_call = on_test and method in GO_FAILURE_CALLS and opener == "("
    if dot != "." or not (is_failure_call or receiver in GO_TESTIFY):
        return None
    end = index + 3
    # Take the call and every chained selector, index or call, as in `assert.New(t).Equal(1, 2)`.
    while tokens[end:end + 1] in (["("], ["["], ["."]):
        end = end + 2 if tokens[end] == "." else closers[end] + 1
    return end


def go_statement(tokens: list[str]) -> str:
    """Tokens joined by spaces: literal contents exact, layout absent, no `,` or `;` before a closing delimiter."""
    following = tokens[1:] + [""]
    return " ".join(
        token for token, after in zip(tokens, following, strict=True)
        if not (token in (",", ";") and after in (")", "]", "}"))
    )


def read_go(text: str) -> TestFile:
    spelled = go_tokens(text)
    tokens = go_plain(spelled, go_closers(spelled), 0, len(spelled))
    if tokens[:1] != ["package"] or not is_go_name("".join(tokens[1:2])):
        raise ValueError("Go file has no package declaration")
    closers = go_closers(tokens)
    scopes = go_scopes(tokens, closers)
    names = tuple(
        scope for index, scope in scopes.items()
        if tokens[index + 1:index + 3] == [scope, "("] and GO_TEST_NAME.fullmatch(scope)
    )
    assertions: dict[str, list[str]] = {scope: [] for scope in (MODULE, *scopes.values())}
    scope = MODULE
    for index in range(len(tokens)):
        scope = scopes.get(index, scope)
        end = go_assertion_end(tokens, index, closers)
        if end is not None:
            assertions[scope].append(go_statement(tokens[index:end]))
    return TestFile(names, {key: tuple(found) for key, found in assertions.items()})


def is_python_assertion(node: ast.AST) -> bool:
    """An assert statement, a unittest call on `self`, or `pytest.raises` or `pytest.fail`."""
    if isinstance(node, ast.Assert):
        return True
    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
        return False
    receiver, method = node.func.value, node.func.attr
    if not isinstance(receiver, ast.Name):
        return False
    if receiver.id == "pytest":
        return method in ("raises", "fail")
    # Exact fail names: a `fail` prefix also matches fixture helpers such as `self.failing_write()`.
    return receiver.id == "self" and (method.startswith("assert") or method in ("fail", "failureException"))


def python_scope(node: ast.AST, key: str, in_function: bool) -> str:
    """The scope that owns `node`: a function or class outside every function opens its own under `key`."""
    if in_function or not isinstance(node, (*PY_FUNCTIONS, ast.ClassDef)):
        return key
    return f"{key}.{node.name}" if key else node.name


def read_python(text: str) -> TestFile:
    names: list[str] = []
    assertions: dict[str, list[str]] = {MODULE: []}
    # An explicit stack, so deeply nested code cannot exhaust the interpreter's recursion limit here.
    pending: list[tuple[ast.AST, str, bool]] = [(ast.parse(text), MODULE, False)]
    while pending:
        parent, key, in_function = pending.pop()
        for node in ast.iter_child_nodes(parent):
            scope = python_scope(node, key, in_function)
            found = assertions.setdefault(scope, [])
            if is_python_assertion(node):
                # The dump holds the code alone: literal values exact, formatting and comments absent.
                found.append(ast.dump(node))
            if scope != key and isinstance(node, PY_FUNCTIONS) and node.name.startswith("test_"):
                names.append(node.name)
            pending.append((node, scope, in_function or isinstance(node, PY_FUNCTIONS)))
    return TestFile(tuple(names), {key: tuple(found) for key, found in assertions.items()})


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
        read = read_go if path.endswith(".go") else read_python
        try:
            files[path] = read(source.decode("utf-8"))
        except (SyntaxError, UnicodeError, ValueError, RecursionError) as exc:
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
