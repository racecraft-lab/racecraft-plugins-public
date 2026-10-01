"""Feedback-sweep runner helpers: comment intake, isolation session, parse, target check and redaction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..sweep_export import (
    SWEEP_LOG_HEADING,
    SWEEP_LOG_KEY_COLUMN,
    SWEEP_NAMED_SURFACES,
    SWEEP_PARSE_SURFACE,
    SWEEP_REDACT_LEGS,
    SWEEP_SELF_REPLY_PREFIX,
    SWEEP_TRUSTED_ASSOCIATIONS,
    sweep_analyst_payload,
    sweep_comment_error,
    sweep_error,
    sweep_export_record,
    sweep_logged_comment_ids,
    sweep_normalize_line_endings,
    sweep_redact_outbound,
    sweep_result,
)
from ..trusted_io import (
    json_text,
    make_result,
    repo_relative,
    request_path_display,
    resolve_input_path,
    trusted_dir_exists,
    trusted_text,
)


def sweep_pr_feedback(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    """Route one request to the named surface it asks for.

    Reports; never decides. The helper assigns no class: `amended` is what routes
    an item into consensus, so that judgment stays with the orchestrator reading
    this envelope. It runs no `gh`, reaches no network, and writes no file. The
    orchestrator takes the one read-only observation and passes it in as data,
    which is what leaves the parse deterministic and offline-testable.

    An explicit JSON null reads as absence and routes to the parse, because a
    caller assembling the object programmatically writes the key with a null
    value where a caller writing it by hand omits the key. The empty string is a
    value outside the three and is an input error, so the test is `is None`
    rather than truthiness.
    """
    named_surface = inputs.get("named_surface")
    if named_surface is None:
        named_surface = SWEEP_PARSE_SURFACE
    if named_surface not in SWEEP_NAMED_SURFACES:
        return sweep_error(f"unknown named_surface: {named_surface}")
    if named_surface == "redact":
        return sweep_redact(inputs)
    if named_surface == "check_target":
        return sweep_check_target(inputs, repo_root)
    return sweep_parse(inputs, repo_root)


def sweep_isolation_session(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    """Operate the private feedback-sweep boundary without returning prose."""
    from ..sweep_isolation import (
        CaptureViolation,
        IsolationViolation,
        ReceiptViolation,
        SchemaViolation,
        SweepSession,
        capture_github_session,
    )
    from ..sweep_launcher import (
        LauncherViolation,
        run_claude_sweep,
        run_codex_sweep,
        verify_claude_boundary,
        verify_codex_boundary,
    )

    named_surface = inputs.get("named_surface")
    allowed = {
        "capture",
        "accept",
        "launch_claude",
        "launch_codex",
        "attest_claude",
        "close",
    }
    if named_surface not in allowed:
        return make_result(json_text({"status": "invalid_request"}), "isolation request rejected\n", 2)

    plugin_root = Path(__file__).resolve().parents[2]
    try:
        if named_surface == "attest_claude":
            if set(inputs) != {"named_surface"}:
                raise SchemaViolation("attestation fields do not match")
            verify_claude_boundary(repo_root, plugin_root)
            payload = {"surface": "claude", "status": "attested"}
        elif named_surface == "close":
            if set(inputs) != {"named_surface", "session_id"}:
                raise SchemaViolation("close fields do not match")
            session = SweepSession.open(inputs["session_id"])
            session.invalidate()
            payload = {"session_id": inputs["session_id"], "status": "closed"}
        elif named_surface == "capture":
            if set(inputs) != {"named_surface", "surface", "repository", "pr_number", "workflow_file"}:
                raise SchemaViolation("capture fields do not match")
            surface = inputs["surface"]
            if surface == "claude":
                verify_claude_boundary(repo_root, plugin_root)
            elif surface == "codex":
                verify_codex_boundary(plugin_root)
            else:
                raise SchemaViolation("surface is unknown")
            payload = capture_github_session(
                repo_root,
                repository=inputs["repository"],
                pr_number=inputs["pr_number"],
                workflow_file=inputs["workflow_file"],
            )
            payload["surface"] = surface
        elif named_surface == "accept":
            if set(inputs) != {"named_surface", "session_id", "receipt", "stage"}:
                raise SchemaViolation("accept fields do not match")
            stage = inputs["stage"]
            if stage not in {"classifier", "perspective"}:
                raise SchemaViolation("only non-synthesis receipts may be accepted directly")
            session = SweepSession.open(inputs["session_id"])
            payload = session.accept_receipt(inputs["receipt"], expected_stage=stage)
        elif named_surface in {"launch_claude", "launch_codex"}:
            expected = {"named_surface", "session_id", "comment_id", "stage"}
            if inputs.get("stage") == "perspective":
                expected.add("perspective")
            if set(inputs) != expected:
                raise SchemaViolation("isolated launch fields do not match")
            launcher = run_claude_sweep if named_surface == "launch_claude" else run_codex_sweep
            payload = launcher(
                plugin_root=plugin_root,
                repo_root=repo_root,
                session_id=inputs["session_id"],
                comment_id=inputs["comment_id"],
                stage=inputs["stage"],
                perspective=inputs.get("perspective"),
            )
        else:
            raise SchemaViolation("isolation surface is unreachable")
    except (CaptureViolation, IsolationViolation, LauncherViolation, ReceiptViolation, SchemaViolation) as violation:
        # A capture failure names its own closed reason, so the orchestrator can
        # tell an absent tool or credential from a spent retry schedule.
        reason = getattr(violation, "reason", "isolation_boundary_unavailable")
        return make_result(json_text({"status": "blocked", "reason": reason}), f"feedback sweep blocked: {reason}\n", 3)
    return make_result(json_text(payload))


def sweep_parse(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    """Report the sweepable comments of one supplied pull-request observation."""
    self_login = inputs.get("self_login")
    if not isinstance(self_login, str) or not self_login.strip():
        # Presence is as far as a deterministic parse can go: the contract forbids
        # it from reaching the network, so it has no second value to compare
        # against, and confirming the account stays the orchestrator's job through
        # provenance.
        return sweep_error("self_login is required and must not be blank")
    workflow_file = inputs.get("workflow_file")
    if not isinstance(workflow_file, str) or not workflow_file:
        return sweep_error("workflow_file is required")
    workflow_display = request_path_display(workflow_file, repo_root)
    workflow_text = trusted_text(resolve_input_path(workflow_display, repo_root), repo_root)
    if workflow_text is None:
        return sweep_error(f"workflow file cannot be read: {workflow_display}")
    observation = inputs.get("pr_observation")
    if not isinstance(observation, dict):
        return sweep_error("pr_observation is required")
    if observation.get("ok") is not True:
        # A truthy non-`true` value is not a successful read, following the
        # precedent in `observation_pull_requests`.
        return sweep_error("pr_observation.ok must be the literal true")
    comments = observation.get("comments")
    if not isinstance(comments, list):
        return sweep_error("pr_observation.comments must be an array")
    for entry in comments:
        problem = sweep_comment_error(entry)
        if problem is not None:
            return sweep_error(problem)
    logged, unreadable_row = sweep_logged_comment_ids(workflow_text)
    if unreadable_row is not None:
        return sweep_error(
            f"{SWEEP_LOG_HEADING} row {unreadable_row} has no readable"
            f" {SWEEP_LOG_KEY_COLUMN} cell: {workflow_display}"
        )

    candidates: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for entry in comments:
        comment_id = entry["id"]
        record = {"id": comment_id, "surface": entry["surface"]}
        # The trust filter runs ahead of everything else, so an untrusted
        # comment's text is never parsed and never recognized. Every exclusion is
        # reported, so a marker collision drops a candidate visibly.
        if entry["author_association"] not in SWEEP_TRUSTED_ASSOCIATIONS:
            excluded.append({**record, "reason": "untrusted_author"})
            continue
        body = sweep_normalize_line_endings(entry["body"])
        # Both halves are required. An empty account would match no real author,
        # which is why the empty value is rejected above rather than narrowed to
        # the marker half.
        if body.startswith(SWEEP_SELF_REPLY_PREFIX) and entry.get("author") == self_login:
            excluded.append({**record, "reason": "self_reply"})
            continue
        if comment_id in logged:
            excluded.append({**record, "reason": "already_logged"})
            continue
        if entry.get("thread_resolved") is True:
            excluded.append({**record, "reason": "thread_resolved"})
            continue
        # No `body` key, on either list and on every path: an untrusted comment's
        # text is absent from this output by construction rather than by a caller
        # remembering to drop it. A null `author` is carried through, because a
        # deleted account is reported as one and never as a blank.
        candidates.append({
            "id": comment_id,
            "surface": entry["surface"],
            "author": entry.get("author"),
            "author_association": entry["author_association"],
            "truncated": entry.get("truncated"),
            "export": sweep_export_record(body),
        })
    return sweep_result(({
        "tool": "sweep-pr-feedback",
        # Both surfaces are read as one all-or-nothing observation, so
        # this reports what the observation covered rather than which of the two
        # happened to carry a comment.
        "surfaces_read": ["review_thread", "pr_conversation"],
        # `observed` is counted from the observation rather than from the two
        # lists, which is what keeps `observed == candidates + excluded`
        # falsifiable: a comment a later filter drops shows up as a mismatch
        # instead of agreeing with itself.
        "counts": {
            "observed": len(comments),
            "candidates": len(candidates),
            "excluded": len(excluded),
        },
        "candidates": candidates,
        "excluded": excluded,
    }))


# The three artifacts an amendment may write. The set is closed here
# because it is the whole of the check: a fourth name is a contract change.
SWEEP_EDIT_ALLOWLIST = ("spec.md", "plan.md", "tasks.md")


def sweep_check_target(inputs: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    """Check the resolved write target in code before any write.

    The test is the surface's and the stop is the orchestrator's, the same division
    the parse keeps when it reports candidates and assigns no class. `allowed: false`
    is a successful read with an answer in it rather than a diagnostic, so a refusal
    returns a verdict and the halt stays with the caller.
    """
    feature_dir = inputs.get("feature_dir")
    if not isinstance(feature_dir, str) or not feature_dir:
        return sweep_error("feature_dir is required")
    target = inputs.get("target")
    if not isinstance(target, str) or not target:
        return sweep_error("target is required")
    if "\x00" in feature_dir or "\x00" in target:
        # Defence in depth, and unreachable through registered dispatch.
        # `target` is not a `path_keys_by_helper` entry, but it IS in PATH_KEYS,
        # so validate_bounded_inputs NUL-checks and boundary-checks it before
        # this helper is entered. Kept because a direct caller has no such
        # guarantee, and a NUL reaching Path.resolve raises instead of
        # returning the diagnostic the contract reserves for a bad request.
        # malformed request is `invalid_input`, never a traceback and never a
        # verdict: the check has to be able to run before it can refuse anything.
        return sweep_error("feature_dir and target must not carry a NUL byte")
    comment_id = inputs.get("comment_id")
    if not isinstance(comment_id, str) or not comment_id.strip():
        return sweep_error("comment_id is required and must not be blank")
    feature_path = resolve_input_path(feature_dir, repo_root)
    if not trusted_dir_exists(feature_path, repo_root):
        return sweep_error(
            "feature_dir does not resolve to a directory:"
            f" {request_path_display(feature_dir, repo_root)}"
        )
    # The candidate is kept both ways on purpose. The comparison reads the resolved
    # path, and the two link tests read the unresolved one, because resolving is
    # what destroys the information those tests are looking for.
    candidate = resolve_input_path(target, repo_root)
    allowed_paths = {
        (feature_path / name).resolve(strict=False) for name in SWEEP_EDIT_ALLOWLIST
    }
    # The allowlist by NAME, unresolved. This is the half that makes the set
    # actually be the three artifacts. `allowed_paths` above resolves each name,
    # so on its own it means "whatever those three names happen to point at": a
    # symlink at `spec.md` aimed at `evil.md` puts `evil.md` into the allowed set,
    # and a request naming `evil.md` directly would then be approved while the
    # indirect route through `spec.md` is refused as `symlink_target`. Both tests
    # must pass, so a link can neither launder a fourth file in nor be followed.
    allowed_names = {feature_path / name for name in SWEEP_EDIT_ALLOWLIST}
    reason: str | None = None
    if candidate not in allowed_names or candidate.resolve(strict=False) not in allowed_paths:
        # Exact membership over resolved paths, never containment. A
        # containment or prefix test would admit everything beneath the feature
        # directory, its checklists and its contracts included, and comparing
        # prefixes against an unresolved path is a traversal defect of its own.
        reason = "outside_set"
    elif candidate.is_symlink():
        reason = "symlink_target"
    elif sweep_symlinked_parent(candidate, feature_path):
        reason = "symlink_parent"
    return sweep_result(({
        "tool": "sweep-pr-feedback",
        "named_surface": "check_target",
        "comment_id": comment_id,
        "allowed": reason is None,
        # The path the check actually compared, never the one the caller sent.
        "resolved": repo_relative(candidate, repo_root),
        "reason": reason,
    }))


def sweep_symlinked_parent(candidate: Path, feature_path: Path) -> bool:
    """True when any directory from the target's parent up to `feature_dir` is a link.

    Each directory is tested before the walk asks whether it is the one to stop at,
    and the feature directory is therefore tested too. Both follow from the same
    case: a link inside the feature directory pointing back at it resolves onto an
    allowed path, so a walk that stopped before testing where it stopped would let
    that link through as an ordinary parent.
    """
    stop = feature_path.resolve(strict=False)
    parent = candidate.parent
    while True:
        if parent.is_symlink():
            return True
        if parent.resolve(strict=False) == stop or parent == parent.parent:
            return False
        parent = parent.parent


def sweep_redact(inputs: dict[str, Any]) -> dict[str, Any]:
    """The redaction surface: one surface, four legs, and the set is closed at four.

    The deny-set never runs on `analyst_payload`, and the shaping never runs on an
    outbound leg, so the leg is the whole of the branch.
    """
    leg = inputs.get("leg")
    if leg not in SWEEP_REDACT_LEGS:
        return sweep_error(f"unknown redaction leg: {leg}")
    comment_id = inputs.get("comment_id")
    if not isinstance(comment_id, str) or not comment_id.strip():
        return sweep_error("comment_id is required and must not be blank")
    if leg == "analyst_payload":
        return sweep_analyst_payload(inputs, comment_id)
    lines = inputs.get("lines")
    if not isinstance(lines, list) or any(not isinstance(entry, str) for entry in lines):
        return sweep_error(
            f"lines must be an array of strings on the {leg} leg for comment {comment_id}"
        )
    # One physical line per entry, enforced rather than assumed. Every rule below
    # tests a whole entry: the key-header rule uses fullmatch with no MULTILINE,
    # and the value rules never split. So an entry carrying an embedded newline
    # is scanned as one opaque string and matches nothing, and a whole private
    # key packed into a single entry would pass all six rules untouched. The
    # caller convention alone cannot be the control here, because these bytes
    # reach a public remote before any human checkpoint.
    if any("\n" in entry or "\r" in entry for entry in lines):
        return sweep_error(
            f"lines entries carry one physical line each; an entry on the {leg} leg "
            f"for comment {comment_id} contains a line break"
        )
    for field in ("text", "truncated", "matched_lines"):
        if inputs.get(field) is not None:
            # The leg fixes the request shape in both directions, so a request
            # carrying both shapes is a malformed caller rather than an ambiguity.
            return sweep_error(f"{field} is an analyst_payload field and not the {leg} leg's")
    return sweep_redact_outbound(leg, comment_id, lines)
