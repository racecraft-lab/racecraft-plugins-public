"""Python AST analyzer that detects shell-backed subprocess execution."""

from __future__ import annotations

import ast
import re
import shlex

from .common import (
    OS_SHELL_FUNCTION_NAMES,
    PROHIBITED_COMMAND_NAMES,
    PartialStaticAssignment,
    SHELL_COMMAND_NAMES,
    SHELL_RUNTIME_COMMAND_NAMES,
    SUBPROCESS_ARGV_FUNCTION_NAMES,
    SUBPROCESS_SHELL_FUNCTION_NAMES,
    StaticAssignment,
    executable_basename,
    has_prohibited_script_suffix,
)


def python_static_command_assignments(tree: ast.AST) -> dict[str, list[StaticAssignment]]:
    assignments: dict[str, list[StaticAssignment]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = static_command_value(node.value)
            if value is None:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(
                        StaticAssignment(value=value, line=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0))
                    )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            value = static_command_value(node.value)
            if value is not None:
                assignments.setdefault(node.target.id, []).append(
                    StaticAssignment(value=value, line=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0))
                )
    return assignments


def python_static_bool_assignments(tree: ast.AST) -> dict[str, list[StaticAssignment]]:
    assignments: dict[str, list[StaticAssignment]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = static_bool_value(node.value)
            if value is None:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(
                        StaticAssignment(value=value, line=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0))
                    )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            value = static_bool_value(node.value)
            if value is not None:
                assignments.setdefault(node.target.id, []).append(
                    StaticAssignment(value=value, line=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0))
                )
    return assignments


def python_partial_command_assignments(
    tree: ast.AST,
    static_assignments: dict[str, list[StaticAssignment]],
) -> dict[str, list[PartialStaticAssignment]]:
    assignments: dict[str, list[PartialStaticAssignment]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = partial_static_string_argv(node.value, static_assignments, node)
            if value is None:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments.setdefault(target.id, []).append(
                        PartialStaticAssignment(value=value, line=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0))
                    )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            value = partial_static_string_argv(node.value, static_assignments, node)
            if value is not None:
                assignments.setdefault(node.target.id, []).append(
                    PartialStaticAssignment(value=value, line=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0))
                )
    return assignments


def python_shell_aliases(tree: ast.AST) -> dict[str, set[str]]:
    aliases = {
        "os_modules": {"os"},
        "os_system_functions": set[str](),
        "subprocess_modules": {"subprocess"},
        "subprocess_functions": set[str](),
        "subprocess_shell_functions": set[str](),
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                bound = alias.asname or alias.name
                if alias.name == "os":
                    aliases["os_modules"].add(bound)
                elif alias.name == "subprocess":
                    aliases["subprocess_modules"].add(bound)
        elif isinstance(node, ast.ImportFrom):
            if node.module == "os":
                for alias in node.names:
                    if alias.name in OS_SHELL_FUNCTION_NAMES:
                        aliases["os_system_functions"].add(alias.asname or alias.name)
            elif node.module == "subprocess":
                for alias in node.names:
                    if alias.name in SUBPROCESS_ARGV_FUNCTION_NAMES:
                        aliases["subprocess_functions"].add(alias.asname or alias.name)
                    elif alias.name in SUBPROCESS_SHELL_FUNCTION_NAMES:
                        aliases["subprocess_shell_functions"].add(alias.asname or alias.name)
    return aliases


def is_os_system_call(func: ast.expr, aliases: dict[str, set[str]]) -> bool:
    if isinstance(func, ast.Attribute) and func.attr in OS_SHELL_FUNCTION_NAMES and isinstance(func.value, ast.Name):
        return func.value.id in aliases["os_modules"]
    return isinstance(func, ast.Name) and func.id in aliases["os_system_functions"]


def os_shell_call_pattern(func: ast.expr) -> str:
    if isinstance(func, ast.Attribute):
        return f"os.{func.attr}("
    if isinstance(func, ast.Name):
        return f"{func.id}("
    return "os shell execution"


def is_shell_backed_subprocess_call(func: ast.expr, aliases: dict[str, set[str]]) -> bool:
    if isinstance(func, ast.Attribute) and func.attr in SUBPROCESS_SHELL_FUNCTION_NAMES and isinstance(func.value, ast.Name):
        return func.value.id in aliases["subprocess_modules"]
    return isinstance(func, ast.Name) and func.id in aliases["subprocess_shell_functions"]


def subprocess_call_pattern(func: ast.expr) -> str:
    if isinstance(func, ast.Attribute):
        return f"subprocess.{func.attr}("
    if isinstance(func, ast.Name):
        return f"{func.id}("
    return "subprocess shell execution"


def is_subprocess_call(func: ast.expr, aliases: dict[str, set[str]]) -> bool:
    if isinstance(func, ast.Attribute) and func.attr in SUBPROCESS_ARGV_FUNCTION_NAMES and isinstance(func.value, ast.Name):
        return func.value.id in aliases["subprocess_modules"]
    return isinstance(func, ast.Name) and func.id in aliases["subprocess_functions"]


def call_has_shell_enabled(node: ast.Call, assignments: dict[str, list[StaticAssignment]] | None = None) -> bool:
    for keyword in node.keywords:
        if keyword.arg != "shell":
            continue
        if shell_keyword_is_statically_false(keyword.value, assignments or {}, node):
            return False
        return True
    return False


def shell_keyword_pattern(node: ast.Call, assignments: dict[str, list[StaticAssignment]] | None = None) -> str:
    for keyword in node.keywords:
        if keyword.arg != "shell":
            continue
        if isinstance(keyword.value, ast.Name):
            assignment = latest_static_assignment(keyword.value.id, assignments or {}, node)
            if assignment is not None:
                return f"shell={keyword.value.id} ({assignment.value})"
            return f"shell={keyword.value.id}"
        if isinstance(keyword.value, ast.Constant):
            return f"shell={keyword.value.value!r}"
        return "shell=<dynamic>"
    return "shell=True"


def shell_keyword_is_statically_false(
    value: ast.AST,
    assignments: dict[str, list[StaticAssignment]],
    node: ast.AST,
) -> bool:
    bool_value = static_bool_value(value)
    if bool_value is False:
        return True
    if not isinstance(value, ast.Name):
        return False
    assignment = latest_static_assignment(value.id, assignments, node)
    return assignment is not None and assignment.value is False


def static_bool_value(node: ast.AST | None) -> bool | None:
    if isinstance(node, ast.Constant):
        if node.value is True:
            return True
        if node.value is False or node.value == 0:
            return False
    return None


def call_has_command_string(node: ast.Call, assignments: dict[str, list[StaticAssignment]] | None = None) -> bool:
    return isinstance(static_subprocess_arg_value(node, assignments or {}), str)


def command_argv_subprocess_pattern(
    node: ast.Call,
    assignments: dict[str, list[StaticAssignment]] | None = None,
    partial_assignments: dict[str, list[PartialStaticAssignment]] | None = None,
) -> str | None:
    args_node = subprocess_args_node(node)
    if isinstance(args_node, ast.Name):
        prior_pattern = prior_forbidden_argv_assignment_pattern(
            args_node.id,
            assignments or {},
            partial_assignments or {},
            node,
        )
        if prior_pattern is not None:
            return prior_pattern
    value = static_subprocess_arg_value(node, assignments or {})
    if not isinstance(value, list):
        partial_argv = partial_static_subprocess_argv(node, partial_assignments or {}, assignments or {})
        if partial_argv is None or not partial_command_argv_contains_forbidden(partial_argv):
            return None
        return " ".join(item if item is not None else "<dynamic>" for item in partial_argv)[:120]
    argv = value
    if command_argv_contains_forbidden(argv):
        return " ".join(argv)[:120]
    if executable_basename(argv[0]) == "env":
        for delegated_argv in env_delegated_argvs(argv):
            if command_argv_contains_forbidden(delegated_argv):
                return " ".join(argv)[:120]
    return None


def prior_forbidden_argv_assignment_pattern(
    name: str,
    assignments: dict[str, list[StaticAssignment]],
    partial_assignments: dict[str, list[PartialStaticAssignment]],
    node: ast.AST,
) -> str | None:
    call_position = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
    for assignment in assignments.get(name, []):
        if (assignment.line, assignment.column) > call_position or not isinstance(assignment.value, list):
            continue
        if command_argv_contains_forbidden(assignment.value):
            return " ".join(assignment.value)[:120]
    for assignment in partial_assignments.get(name, []):
        if (assignment.line, assignment.column) > call_position:
            continue
        if partial_command_argv_contains_forbidden(assignment.value):
            return " ".join(item if item is not None else "<dynamic>" for item in assignment.value)[:120]
    return None


def static_subprocess_arg_value(node: ast.Call, assignments: dict[str, list[StaticAssignment]]) -> list[str] | str | None:
    args_node = subprocess_args_node(node)
    if isinstance(args_node, ast.Name):
        assignment = latest_static_assignment(args_node.id, assignments, node)
        return assignment.value if assignment is not None else None
    return static_command_value(args_node)


def partial_static_subprocess_argv(
    node: ast.Call,
    assignments: dict[str, list[PartialStaticAssignment]],
    static_assignments: dict[str, list[StaticAssignment]],
) -> list[str | None] | None:
    args_node = subprocess_args_node(node)
    if isinstance(args_node, ast.Name):
        assignment = latest_partial_static_assignment(args_node.id, assignments, node)
        return assignment.value if assignment is not None else None
    return partial_static_string_argv(args_node, static_assignments, node)


def latest_partial_static_assignment(
    name: str,
    assignments: dict[str, list[PartialStaticAssignment]],
    node: ast.AST,
) -> PartialStaticAssignment | None:
    call_position = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
    candidates = [
        assignment
        for assignment in assignments.get(name, [])
        if (assignment.line, assignment.column) <= call_position
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda assignment: (assignment.line, assignment.column))


def latest_static_assignment(name: str, assignments: dict[str, list[StaticAssignment]], node: ast.AST) -> StaticAssignment | None:
    call_position = (getattr(node, "lineno", 0), getattr(node, "col_offset", 0))
    candidates = [
        assignment
        for assignment in assignments.get(name, [])
        if (assignment.line, assignment.column) <= call_position
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda assignment: (assignment.line, assignment.column))


def subprocess_args_node(node: ast.Call) -> ast.AST | None:
    if node.args:
        return node.args[0]
    for keyword in node.keywords:
        if keyword.arg == "args":
            return keyword.value
    return None


def command_argv_contains_forbidden(argv: list[str], *, depth: int = 0) -> bool:
    if not argv:
        return False
    if executable_basename(argv[0]) in PROHIBITED_COMMAND_NAMES | SHELL_RUNTIME_COMMAND_NAMES:
        return True
    if any(has_prohibited_script_suffix(item) for item in argv):
        return True
    if shell_c_payload_has_forbidden_command(argv):
        return True
    if executable_basename(argv[0]) == "env" and depth < 4:
        for delegated_argv in env_delegated_argvs(argv):
            if command_argv_contains_forbidden(delegated_argv, depth=depth + 1):
                return True
    joined = " ".join(item.lower() for item in argv)
    if "git bash" in joined:
        return True
    return False


def partial_command_argv_contains_forbidden(argv: list[str | None], *, depth: int = 0) -> bool:
    if not argv:
        return False
    executable = argv[0]
    if executable is not None and executable_basename(executable) in PROHIBITED_COMMAND_NAMES | SHELL_RUNTIME_COMMAND_NAMES:
        return True
    if any(item is not None and has_prohibited_script_suffix(item) for item in argv):
        return True
    if executable is not None and executable_basename(executable) in SHELL_COMMAND_NAMES:
        return any(item is not None and shell_command_payload_flag(item) for item in argv[1:])
    if executable is not None and executable_basename(executable) == "env" and depth < 4:
        return partial_env_delegation_contains_forbidden(argv, depth=depth)
    return False


def static_command_value(node: ast.AST | None) -> list[str] | str | None:
    argv = static_string_argv(node)
    if argv is not None:
        return argv
    return static_command_string(node)


def static_string_argv(node: ast.AST | None) -> list[str] | None:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return None
    argv: list[str] = []
    for element in node.elts:
        value = static_string_literal(element)
        if value is None:
            return None
        argv.append(value)
    return argv or None


def partial_static_string_argv(
    node: ast.AST | None,
    assignments: dict[str, list[StaticAssignment]] | None = None,
    context_node: ast.AST | None = None,
) -> list[str | None] | None:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return None
    argv = [partial_static_string_value(element, assignments or {}, context_node or node) for element in node.elts]
    return argv if any(item is not None for item in argv) else None


def partial_static_string_value(
    node: ast.AST,
    assignments: dict[str, list[StaticAssignment]],
    context_node: ast.AST,
) -> str | None:
    value = static_string_literal(node)
    if value is not None:
        return value
    if not isinstance(node, ast.Name):
        return None
    candidates = [
        assignment
        for assignment in assignments.get(node.id, [])
        if isinstance(assignment.value, str)
        and (assignment.line, assignment.column) <= (getattr(context_node, "lineno", 0), getattr(context_node, "col_offset", 0))
    ]
    if not candidates:
        return None
    unsafe_values = [assignment.value for assignment in candidates if scalar_static_value_can_hide_forbidden_argv(assignment.value)]
    if unsafe_values:
        return unsafe_values[0]
    if len(candidates) == 1:
        return candidates[0].value
    return None


def static_command_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.JoinedStr):
        return static_string_literal(node) or "f-string subprocess command"
    return static_string_literal(node)


def static_string_literal(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if not isinstance(node, ast.JoinedStr):
        return None
    parts: list[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
            continue
        if isinstance(value, ast.FormattedValue) and isinstance(value.value, ast.Constant):
            parts.append(str(value.value.value))
            continue
        return None
    return "".join(parts)


def shell_c_payload_has_forbidden_command(argv: list[str]) -> bool:
    if executable_basename(argv[0]) not in SHELL_COMMAND_NAMES:
        return False
    for index, item in enumerate(argv[1:], start=1):
        if not shell_command_payload_flag(item) or index + 1 >= len(argv):
            continue
        return True
    return False


def shell_command_payload_flag(item: str) -> bool:
    return bool(re.fullmatch(r"-[A-Za-z]*c[A-Za-z]*", item))


def scalar_static_value_can_hide_forbidden_argv(value: str) -> bool:
    if executable_basename(value) in PROHIBITED_COMMAND_NAMES | SHELL_RUNTIME_COMMAND_NAMES or has_prohibited_script_suffix(value):
        return True
    if "git bash" in value.lower():
        return True
    return any(command_argv_contains_forbidden(delegated_argv) for delegated_argv in env_split_string_argvs(value))


def partial_env_delegation_contains_forbidden(argv: list[str | None], *, depth: int = 0) -> bool:
    index = 1
    while index < len(argv):
        item = argv[index]
        if item is None:
            return True
        if item in {"-S", "--split-string"}:
            if index + 1 >= len(argv):
                return False
            payload = argv[index + 1]
            if payload is None:
                return True
            return any(command_argv_contains_forbidden(delegated_argv) for delegated_argv in env_split_string_argvs(payload))
        if item.startswith("-S") and item != "-S":
            return any(command_argv_contains_forbidden(delegated_argv) for delegated_argv in env_split_string_argvs(item[2:].strip()))
        if item.startswith("--split-string="):
            return any(command_argv_contains_forbidden(delegated_argv) for delegated_argv in env_split_string_argvs(item.split("=", 1)[1]))
        if item in {"-u", "--unset", "-C", "--chdir"}:
            index += 2
            continue
        if item.startswith("--unset=") or item.startswith("--chdir="):
            index += 1
            continue
        if item.startswith("-"):
            index += 1
            continue
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", item):
            index += 1
            continue
        return partial_command_argv_contains_forbidden(argv[index:], depth=depth + 1)
    return False


def env_delegated_argvs(argv: list[str]) -> list[list[str]]:
    delegated: list[list[str]] = []
    index = 1
    while index < len(argv):
        item = argv[index]
        if item in {"-S", "--split-string"}:
            if index + 1 < len(argv):
                delegated.extend(env_split_string_argvs(argv[index + 1]))
            index += 2
            continue
        if item.startswith("-S") and item != "-S":
            delegated.extend(env_split_string_argvs(item[2:].strip()))
            index += 1
            continue
        if item.startswith("--split-string="):
            delegated.extend(env_split_string_argvs(item.split("=", 1)[1]))
            index += 1
            continue
        if item in {"-u", "--unset", "-C", "--chdir"}:
            index += 2
            continue
        if item.startswith("--unset=") or item.startswith("--chdir="):
            index += 1
            continue
        if item.startswith("-"):
            index += 1
            continue
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", item):
            index += 1
            continue
        delegated.append(argv[index:])
        break
    return delegated


def env_split_string_argvs(payload: str) -> list[list[str]]:
    try:
        tokens = shlex.split(payload)
    except ValueError:
        tokens = payload.split()
    if not tokens:
        return []
    return env_delegated_argvs(["env", *tokens])
