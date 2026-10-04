"""The decisions list: every judgment a run made instead of asking, in one runner-owned file.

The runner is the only writer. Entries sort spec-affecting first, then authority
skips, then notes; one malformed entry refuses the whole batch. The terminal
message is the count and a link, nothing else (ADR 0010).
"""

from __future__ import annotations

import json
from contextlib import nullcontext
from typing import Any

from ..envelope import diagnostic, response
from ..execution_control import confined_path, durable_json, exclusive_ledger, workflow_process_directory
from ..strict_input import SelectionError, require_fields, require_text, unique_object
from ..trusted_io import resolve_repo_root

SCHEMA_VERSION = "decisions-list/v1"
MAX_TEXT = 1000
TEXT_FIELDS = ("option_chosen", "rejected_alternative", "evidence", "affected_unit")
SPEC_AFFECTING, AUTHORITY_SKIP, NOTE = 0, 1, 2
# The closed set of kinds, each with its sort class.
KINDS = {
    "scope_answer": SPEC_AFFECTING,
    "split_recommendation": SPEC_AFFECTING,
    "unratified_default": SPEC_AFFECTING,
    "authority_action_skipped": AUTHORITY_SKIP,
    "readiness_stale": NOTE,
    "pr_record_problem": NOTE,
    "unregistered_stop": NOTE,
}


def checked_entry(value: Any) -> dict[str, str]:
    """One entry exactly as the contract states it; anything else raises."""
    fields = require_fields(value, {"kind", *TEXT_FIELDS}, "entry")
    if not isinstance(fields["kind"], str) or fields["kind"] not in KINDS:
        raise SelectionError(f"entry: kind must be one of {sorted(KINDS)}")
    if any(len(fields[name]) > MAX_TEXT for name in TEXT_FIELDS if isinstance(fields[name], str)):
        raise SelectionError(f"entry: text fields are limited to {MAX_TEXT} characters")
    return {"kind": fields["kind"], **{name: require_text(fields[name], name) for name in TEXT_FIELDS}}


def ordered(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(entries, key=lambda item: (KINDS[item["kind"]], item["seq"]))


def terminal_message(count: int, link: str) -> str:
    return f"{count} decisions recorded: {link}"


def _stored(path: Any) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    document = require_fields(json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object),
                              {"schema_version", "entries"}, "decisions list")
    if document["schema_version"] != SCHEMA_VERSION or not isinstance(document["entries"], list):
        raise SelectionError(f"decisions list must be {SCHEMA_VERSION} with an entries list")
    stored = []
    for index, item in enumerate(document["entries"], start=1):
        seq = require_fields(item, {"seq", "kind", *TEXT_FIELDS}, "stored entry").get("seq")
        if type(seq) is not int or seq != index:
            raise SelectionError("stored entries must be numbered 1..n in order")
        stored.append({"seq": seq, **checked_entry({key: item[key] for key in item if key != "seq"})})
    return stored


def decisions_list(root: Any, inputs: dict[str, Any], mode: str) -> dict[str, Any]:
    """Read the list, or append a batch (planned in dry_run, written in apply)."""
    fields = {"workflow_file"} if mode == "read_only" else {"workflow_file", "entries"}
    request = require_fields({key: value for key, value in inputs.items() if key != "repo_root"}, fields, "inputs")
    workflow = require_text(request["workflow_file"], "workflow_file")
    if not confined_path(root, workflow).is_file():
        raise SelectionError("workflow_file must be an existing contained file")
    link = workflow_process_directory(workflow).joinpath("decisions-list", "decisions.json").as_posix()
    path = confined_path(root, link)
    batch = request.get("entries", [])
    if not isinstance(batch, list) or (mode != "read_only" and not batch):
        raise SelectionError("entries must be a non-empty list")
    new = [checked_entry(item) for item in batch]
    with exclusive_ledger(path) if mode == "apply" else nullcontext():
        stored = _stored(path)
        entries = stored + [{"seq": len(stored) + index, **item} for index, item in enumerate(new, start=1)]
        if mode == "apply":
            durable_json(path, {"schema_version": SCHEMA_VERSION, "entries": entries})
    return {"entries": ordered(entries), "count": len(entries), "link": link,
            "message": terminal_message(len(entries), link), "writes_state": mode == "apply"}


def run_decisions_list_helper(entry: Any, request: Any) -> dict[str, Any]:
    try:
        root = resolve_repo_root(request.inputs)
        if isinstance(root, dict):
            return response("input_error", request_id=request.request_id, diagnostics=[root])
        data = decisions_list(root, request.inputs, request.mode)
    except (ValueError, OSError) as error:
        refusal = diagnostic(
            "invalid_decisions_list_request",
            str(error),
            remediation_summary="Send the workflow file and, to record, a non-empty list of well-formed entries.",
            remediation_actions=["Correct the named field.", "Rerun decisions-list; nothing was written."],
        )
        return response("input_error", request_id=request.request_id, diagnostics=[refusal])
    identity = {"helper_id": entry.helper_id, "operation": entry.operation, "mode": request.mode}
    return response("ok", request_id=request.request_id, data={**data, **identity})
