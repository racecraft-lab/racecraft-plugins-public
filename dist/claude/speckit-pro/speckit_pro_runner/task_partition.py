"""Phase 7 task-line parsing and the research, implement and verify partition of a tasks file."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .trusted_io import (
    json_text,
    make_result,
    request_path_display,
    resolve_input_path,
    trusted_file_exists,
    trusted_lines,
    trusted_text,
)


PHASE7_DEFAULT_WAVE_SIZE = 4
PHASE7_IMPLEMENT_AGENT = "speckit-pro:implement-executor"
PHASE7_RESEARCH_AGENT = "speckit-pro:domain-researcher"
PHASE7_VERIFY_AGENT = "orchestrator-direct"
PHASE7_TEST_KEYWORDS = ("contract test", "unit test", "integration", "test")
PHASE7_RESEARCH_KEYWORDS = ("research", "investigate", "explore api")
# The one list of check-only task verbs. The Tasks guidance and both hosts'
# routing prose name exactly these words; a contract test holds them together.
PHASE7_VERIFY_KEYWORDS = ("verify", "run", "check", "build", "lint", "confirm", "recheck")
PHASE7_CODE_SPAN = re.compile(r"`[^`]*`")
PHASE7_LEADING_VERB = re.compile(r"^[\s*_]*([A-Za-z]+)")


def phase7_keyword_matches(title: str, keyword: str) -> bool:
    """Match one routing keyword as a whole word, case-insensitively.

    Whole-word matching is what keeps ``test`` off ``latest`` while still
    matching it inside ``src/parser.test.ts``. Non-alphanumeric characters
    bound a word, so a keyword still matches inside a bare hyphenated name or
    a bare path.
    Names the task writes as inline code are not description words at all, so
    ``phase7_route`` removes those spans before calling this.
    """
    pattern = r"(?<![0-9A-Za-z])" + re.escape(keyword.strip()) + r"(?![0-9A-Za-z])"
    return re.search(pattern, title, re.IGNORECASE) is not None


def phase7_leading_verb(title: str) -> str:
    """Return the description's opening word, lowercased, or an empty string.

    Markdown emphasis around the verb is punctuation rather than a word, so a
    bolded ``**Verify**`` still reports ``verify``. Any other opening character
    means the description does not start with a verb, and the caller reads the
    empty string as "no verification head".
    """
    match = PHASE7_LEADING_VERB.match(title)
    return match.group(1).lower() if match else ""


def phase7_route(title: str, project_agent: str | None, project_keywords: list[str]) -> str:
    """Route one task description to an agent, first match wins.

    The five branches are the documented Phase 7 routing table: the project
    implementation agent, the TDD executor for test work, the researcher for
    investigation, the orchestrator itself for verification commands, and the
    TDD executor again as the fallback.

    Inline code spans are removed first. A task list names helpers, files, and
    commands in backticks, and those names are identifiers rather than words
    about the work: matching them routed ``Port and register
    `check-prerequisites` behavior`` to ``orchestrator-direct``, which
    dispatches no agent at all. Only the prose around the spans decides.

    Branches (a) through (c) match their keywords anywhere in the description.
    The verification branch does not: it reads the leading verb alone, because
    the documented branch is verification-only work and ``run``, ``check`` and
    ``build`` are ordinary words everywhere else in a task list. Matching them
    anywhere sent "Add the required validate-release-note check" and "Register
    the helper and check the manifest" to ``orchestrator-direct``, which
    dispatches no agent and injects no TDD protocol. ``build`` at the head is
    the one word that still reads both ways, and verification wins it.
    """
    title = PHASE7_CODE_SPAN.sub(" ", title)
    if project_agent and any(phase7_keyword_matches(title, word) for word in project_keywords):
        return project_agent
    if any(phase7_keyword_matches(title, word) for word in PHASE7_TEST_KEYWORDS):
        return PHASE7_IMPLEMENT_AGENT
    if any(phase7_keyword_matches(title, word) for word in PHASE7_RESEARCH_KEYWORDS):
        return PHASE7_RESEARCH_AGENT
    if phase7_leading_verb(title) in PHASE7_VERIFY_KEYWORDS:
        return PHASE7_VERIFY_AGENT
    return PHASE7_IMPLEMENT_AGENT


def phase7_waves(task_ids: list[str], wave_size: int) -> list[list[str]]:
    return [task_ids[start : start + wave_size] for start in range(0, len(task_ids), wave_size)]


def phase7_flush(
    pending: list[dict[str, Any]],
    wave_size: int,
    runs: list[dict[str, Any]],
) -> None:
    """Close the open parallel run, degrading a one-task run to a singleton."""
    if not pending:
        return
    if len(pending) < 2:
        runs.append(phase7_singleton(pending[0]))
    else:
        task_ids = [task["id"] for task in pending]
        runs.append(
            {
                "kind": "parallel",
                "agent": pending[0]["agent"],
                "group": pending[0]["group"],
                "tasks": task_ids,
                "waves": phase7_waves(task_ids, wave_size),
            }
        )
    pending.clear()


def phase7_singleton(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "singleton",
        "agent": task["agent"],
        "group": task["group"],
        "tasks": [task["id"]],
    }


def phase7_error(message: str) -> dict[str, Any]:
    return make_result(
        json_text({"tool": "partition-phase7-tasks", "contract_version": 1, "error": message}),
        f"partition-phase7-tasks: input_error: {message}\n",
        2,
    )


def partition_phase7_tasks(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    """Partition a tasks.md file into ordered Phase 7 dispatch runs.

    The orchestrator used to run these rules in its own context. They are
    deterministic, so the runner owns them: consecutive ``[P]`` tasks that route
    to the same agent become one parallel run, a task without ``[P]`` becomes a
    singleton, a ``[P]`` task that routes elsewhere closes the open run and
    opens a new one, a parallel run of one degrades to a singleton, and each
    parallel run is split into order-preserving waves no larger than
    ``wave_size``.
    """
    raw = inputs.get("tasks_file")
    if not isinstance(raw, str) or not raw:
        return phase7_error("tasks_file is required")
    tasks_rel = request_path_display(raw, repo_root)
    tasks_file = resolve_input_path(tasks_rel, repo_root)
    if not trusted_file_exists(tasks_file, repo_root):
        return phase7_error(f"tasks_file not found or unreadable: {tasks_rel}")

    wave_raw = inputs.get("wave_size", PHASE7_DEFAULT_WAVE_SIZE)
    if isinstance(wave_raw, bool) or not isinstance(wave_raw, int) or wave_raw < 1:
        return phase7_error("wave_size must be a positive integer")
    wave_size = wave_raw

    project_agent = inputs.get("project_agent_name")
    if project_agent is not None and (not isinstance(project_agent, str) or not project_agent.strip()):
        return phase7_error("project_agent_name must be a non-empty string")
    keywords_raw = inputs.get("project_agent_keywords", [])
    if not isinstance(keywords_raw, list) or not all(
        isinstance(word, str) and word.strip() for word in keywords_raw
    ):
        return phase7_error("project_agent_keywords must be an array of non-empty strings")
    project_keywords = [word for word in keywords_raw if word.strip()]

    lines = trusted_lines(tasks_file, repo_root)
    records: list[dict[str, Any]] = []
    phase_instance = 0
    task_sources: dict[str, dict[str, Any]] = {}
    warnings: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []
    group: str | None = None
    task_count = 0

    for line_no, line in enumerate(lines, start=1):
        if line.startswith("## ") and not line.startswith("###"):
            # A phase group is a dispatch boundary: the orchestrator opens and
            # closes one task entry per group, so no run may straddle two.
            phase7_flush(pending, wave_size, runs)
            group = line[3:].strip()
            phase_instance += 1
            continue
        task = parse_task_line(
            line,
            line_no,
            tasks_rel,
            repo_root,
            "phase7",
            "partition",
            task_sources,
            warnings,
            errors,
        )
        if task is None:
            continue
        task_count += 1
        agent = phase7_route(task["title"], project_agent, project_keywords)
        records.append({**task, "agent": agent, "group": group, "phase_instance": phase_instance})
        record = {"id": task["id"], "agent": agent, "group": group}
        if task["parallel"] and pending and pending[0]["agent"] == agent:
            pending.append(record)
            continue
        phase7_flush(pending, wave_size, runs)
        if task["parallel"]:
            pending.append(record)
        else:
            runs.append(phase7_singleton(record))
    phase7_flush(pending, wave_size, runs)

    payload = {
        "tool": "partition-phase7-tasks",
        "contract_version": 1,
        "tasks_file": tasks_rel,
        "wave_size": wave_size,
        "task_count": task_count,
        "runs": runs,
        "errors": errors,
    }
    if errors:
        return make_result(
            json_text(payload),
            f"partition-phase7-tasks: invalid_tasks: {len(errors)} error(s)\n",
            1,
        )
    required = inputs.get("task_execution_required", False)
    if not isinstance(required, bool):
        return phase7_error("task_execution_required must be a Boolean")
    metadata_path = tasks_file.parent / ".process" / "task-execution.json"
    action = inputs.get("_task_execution_action")
    if required or action or metadata_path.exists() or metadata_path.is_symlink():
        return phase7_metadata_partition(inputs, repo_root, tasks_file, records, payload)
    return make_result(json_text(payload))


def phase7_metadata_partition(inputs: dict[str, Any], repo_root: Path, tasks_file: Path,
                              records: list[dict[str, Any]], payload: dict[str, Any]) -> dict[str, Any]:
    """Validate the sidecar before handing native orchestration a batch plan."""
    from .task_execution import TaskExecutionError, batch_waves, fingerprints, make_batches, validate_metadata

    texts = [trusted_text(path, repo_root) for path in (
        tasks_file.parent / "spec.md", tasks_file.parent / "plan.md", tasks_file
    )]
    if any(text is None for text in texts):
        return phase7_error("metadata requires readable, contained spec.md, plan.md, and tasks.md")
    expected = fingerprints(*texts)
    if inputs.get("_task_execution_action") == "fingerprints":
        return make_result(json_text({"tool": "validate-task-execution", "contract_version": 1,
                                      "fingerprints": expected, "task_ids": [r["id"] for r in records]}))
    metadata_text = trusted_text(tasks_file.parent / ".process" / "task-execution.json", repo_root)
    if metadata_text is None:
        return phase7_error("task-execution metadata missing or unreadable; parent reconciliation required")
    try:
        entries = validate_metadata(metadata_text, records, repo_root, expected, inputs.get("completed_tasks", []))
        batches = make_batches(records, entries)
    except TaskExecutionError as exc:
        return phase7_error(str(exc))
    result = {key: value for key, value in payload.items() if key != "runs"}
    result.update({"contract_version": 2, "fingerprints": expected, "batches": batches,
                   "waves": batch_waves(batches, payload["wave_size"]), "dispatch_count": len(batches),
                   "completed_tasks": [r["id"] for r in records if r["status"] == "done"]})
    for batch in batches:
        batch.pop("_filesystem_ids")
    return make_result(json_text(result))


def plan_layers_source(path: str, line: int | None, heading: str | None = None) -> dict[str, Any]:
    source: dict[str, Any] = {"path": path, "line": line}
    if heading is not None:
        source["heading"] = heading
    return source


def plan_layers_diagnostic(
    code: str,
    severity: str,
    message: str,
    tasks_rel: str,
    line_no: int | None,
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "source": plan_layers_source(tasks_rel, line_no),
        "details": details,
    }


def parse_task_line(
    line: str,
    line_no: int,
    tasks_rel: str,
    repo_root: Path,
    increment_id: str,
    increment_kind: str,
    task_sources: dict[str, dict[str, Any]],
    warnings: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> dict[str, Any] | None:
    match = re.match(r"^\s*-\s+\[([ xX])\]\s+(T[0-9]{3,})(.*)$", line)
    if match is None:
        if re.match(r"^\s*-\s+\[[^]]+\]\s+T[0-9]{3,}", line):
            errors.append(
                plan_layers_diagnostic(
                    "malformed_task",
                    "error",
                    "Task-like checkbox line uses unsupported syntax.",
                    tasks_rel,
                    line_no,
                    {"line_text": line.strip()},
                )
            )
        return None
    marker, task_id, rest = match.groups()
    rest = rest.lstrip()
    parallel = False
    story: str | None = None
    while True:
        if rest.startswith("[P]"):
            parallel = True
            rest = rest[3:].lstrip()
            continue
        story_match = re.match(r"^\[US([1-9][0-9]*)\]\s*(.*)$", rest)
        if story_match is not None:
            story = f"us{story_match.group(1)}"
            rest = story_match.group(2)
            continue
        break
    if increment_kind == "story" and story is None:
        story = increment_id

    files, tests, reference_warnings = extract_refs(
        rest,
        task_id,
        increment_id,
        line_no,
        tasks_rel,
        repo_root,
    )
    warnings.extend(reference_warnings)
    source = plan_layers_source(tasks_rel, line_no)
    if task_id in task_sources:
        errors.append(
            plan_layers_diagnostic(
                "duplicate_task_id",
                "error",
                f"Task ID {task_id} is duplicated.",
                tasks_rel,
                line_no,
                {
                    "task_id": task_id,
                    "first_source": task_sources[task_id],
                    "duplicate_source": source,
                },
            )
        )
    else:
        task_sources[task_id] = source
    return {
        "id": task_id,
        "title": rest,
        "story": story,
        "increment_id": increment_id,
        "status": "done" if marker in {"x", "X"} else "todo",
        "parallel": parallel,
        "source": source,
        "files": files,
        "tests": tests,
    }


def extract_refs(
    title: str,
    task_id: str,
    increment_id: str,
    line_no: int,
    tasks_rel: str,
    repo_root: Path,
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    files: list[str] = []
    tests: list[str] = []
    warnings: list[dict[str, Any]] = []
    for word in title.split():
        token = clean_token(word)
        if not re.search(r"^(\./|\.\./|/|[A-Za-z0-9_.-]+/)", token) or not re.search(r"\.[A-Za-z0-9]+$", token):
            continue
        normalized, inside_root = normalize_reference_info(token, repo_root)
        comparable = normalized.removeprefix("./")
        kind = (
            "test"
            if comparable.startswith("tests/")
            or "/tests/" in comparable
            or re.search(r"(^|/)test-[^/]+\.sh$", comparable)
            else "file"
        )
        if not inside_root:
            warnings.append(
                plan_layers_diagnostic(
                    "reference_not_found",
                    "warning",
                    f"{kind} reference is outside the worktree: {token}",
                    tasks_rel,
                    line_no,
                    {"kind": kind, "reference": token, "task_id": task_id},
                )
            )
            continue
        if not (repo_root / normalized).exists():
            warnings.append(
                plan_layers_diagnostic(
                    "reference_not_found",
                    "warning",
                    f"{kind} reference not found: {normalized}",
                    tasks_rel,
                    line_no,
                    {"kind": kind, "reference": normalized, "task_id": task_id},
                )
            )
        target = tests if kind == "test" else files
        if normalized not in target:
            target.append(normalized)
    if not files and not tests:
        warnings.append(
            plan_layers_diagnostic(
                "task_without_references",
                "warning",
                f"Task {task_id} has no file or test references.",
                tasks_rel,
                line_no,
                {"task_id": task_id, "increment_id": increment_id},
            )
        )
    return sorted(files), sorted(tests), warnings


def clean_token(token: str) -> str:
    token = token.replace("`", "")
    for prefix, suffix in (("\"", "\""), ("'", "'"), ("(", ")"), ("[", "]"), ("<", ">")):
        if token.startswith(prefix):
            token = token[len(prefix):]
        if token.endswith(suffix):
            token = token[:-len(suffix)]
    for suffix in (",", ";", ":", "."):
        if token.endswith(suffix):
            token = token[:-1]
    return token


def normalize_reference_info(raw: str, repo_root: Path) -> tuple[str, bool]:
    if not raw.startswith("/") and ".." not in raw and "/./" not in raw:
        return raw.removeprefix("./"), True
    path = Path(raw)
    if not path.is_absolute():
        path = repo_root / path
    try:
        return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix(), True
    except ValueError:
        return raw, False
