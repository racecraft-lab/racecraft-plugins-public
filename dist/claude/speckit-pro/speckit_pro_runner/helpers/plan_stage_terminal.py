"""The runner owns the plan stage's terminal sequence (ADR 0026).

One mutation helper fills the artifact pages, takes the stage-boundary commit, builds and commits the
draft packet, pushes, creates or refreshes the draft pull request, records it, and writes
`plan/completed` (state `stage: plan`, `status: completed`). A model writes only the page prose,
through one artifact-author dispatch between the `pages` call and the finishing call (ADR 0019).
A step that cannot finish stops the sequence with the stop label the prose table used to hold.
"""

from __future__ import annotations

import functools
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .. import artifact_review, cli_probe, stop_policy
from ..atomic_write import write_bytes_atomic
from ..envelope import RunnerRequest, diagnostic, response
from ..trusted_io import resolve_repo_root, trusted_bytes
from ..workflow_stage import AUTOPILOT_BASIC_INFO_HEADING, HTML_COMMENT_RE, workflow_stage_signals, workflow_table_rows
from . import artifact_fill, artifact_publication, artifact_selection
from .read_only import corroborate_draft_pr, observation_pull_requests, workflow_draft_pr_row
from .readiness_record import preview_surface

Dispatch = Callable[[Any], dict[str, Any]]
PACKET_ID = "draft"
BOUNDARY = "close the plan stage boundary"
PLANNING = ("plan_file", "spec_file", "tasks_file")
INPUTS = frozenset({"repo_root", "host", "workflow_file", "execution_mode", "until", "base_branch",
                    "unratified_defaults", *PLANNING})
RESUME = {"claude": "/speckit-pro:speckit-autopilot", "codex": "$speckit-pro:speckit-autopilot"}
TITLE = re.compile(r"<title>(.*?)</title>", re.DOTALL)
SECTION = re.compile(r"(?ms)^## Artifact Review Handoff\n.*?(?=^## |\Z)")
# One git or gh command in the repository; tests replace this name with a fake.
cli = functools.partial(cli_probe.probe, allowed=("git", "gh"), timeout=120)


@dataclass(eq=False)
class Stop(Exception):
    """The sequence ends here; `reason` is a stop-policy reason and `report` names the step and the state left."""

    reason: str
    report: str


@dataclass
class Run:
    """The inputs and the facts one terminal sequence reads from the workflow file and the repository."""

    root: Path
    inputs: dict[str, Any]
    dispatch: Dispatch
    request: RunnerRequest
    workflow: str = ""
    state: str = ""
    feature: str = ""
    info: dict[str, str] = field(default_factory=dict)
    concept: str = ""
    planning: dict[str, str] = field(default_factory=dict)
    gallery: dict[str, dict[str, Any]] = field(default_factory=dict)
    manifest_sha: str = ""
    branch: str = ""
    commits: list[str] = field(default_factory=list)


def text_of(root: Path, relative: str) -> str:
    content = trusted_bytes(root / relative, root)
    if content is None:
        raise ValueError(f"{relative} is not readable inside the repository")
    return content.decode("utf-8")


def write(root: Path, relative: str, text: str) -> None:
    write_bytes_atomic(root / relative, text.encode("utf-8"), trust_root=root)


def sha256(root: Path, relative: str) -> str | None:
    content = trusted_bytes(root / relative, root)
    return hashlib.sha256(content).hexdigest() if content is not None else None


def command(run: Run, argv: list[str], failure: str, reason: str = "plan_stage_boundary") -> str:
    result = cli(run.root, argv)
    if result["exit_status"] != 0:
        raise Stop(reason, f"{failure}: {result['stderr_tail'][-200:] or 'the command did not run'}")
    return str(result["stdout_tail"])


def call(run: Run, helper_id: str, mode: str, inputs: dict[str, Any]) -> dict[str, Any]:
    return run.dispatch(RunnerRequest(run.request.request_id, helper_id, helper_id, mode, inputs))


def workflow_text(run: Run) -> str:
    return text_of(run.root, run.workflow)


def basic_information(text: str) -> dict[str, str]:
    rows = workflow_table_rows(HTML_COMMENT_RE.sub("", text).splitlines(), AUTOPILOT_BASIC_INFO_HEADING)
    return {cells[0].strip("*` ").casefold(): cells[1].strip("*` ") for cells in rows if len(cells) >= 2}


def set_basic_row(text: str, key: str, value: str) -> str:
    """Rewrite the `Basic Information` row whole, or add it below the table's last row."""
    lines = text.splitlines()
    row = f"| **{key}** | {value} |"
    start = lines.index(AUTOPILOT_BASIC_INFO_HEADING)
    last = start
    for index in range(start + 1, len(lines)):
        if not lines[index].startswith("|"):
            if index > start + 1 and lines[index].strip():
                break
            continue
        last = index
        if lines[index].strip("| ").split("|")[0].strip("*` ").casefold() == key.casefold():
            lines[index] = row
            return "\n".join(lines) + "\n"
    lines.insert(last + 1, row)
    return "\n".join(lines) + "\n"


def prepare(run: Run, inputs: dict[str, Any]) -> None:
    """Read the facts the sequence needs, and refuse before any write when one is missing."""
    run.workflow = inputs["workflow_file"]
    run.state = str(Path(run.workflow).with_name("autopilot-state.json"))
    run.feature = str(Path(inputs["plan_file"]).parent)
    run.info = basic_information(workflow_text(run))
    if not {"spec id", "name"} <= run.info.keys() or sha256(run.root, run.state) is None:
        raise ValueError("the workflow file needs Spec ID and Name rows and sits beside autopilot-state.json")
    run.concept = f"docs/ai/specs/.process/{run.info['spec id']}-design-concept.md"
    optional = {"research_file": f"{run.feature}/research.md", "design_concept_file": run.concept}
    run.planning = {**{name: inputs[name] for name in PLANNING},
                    **{name: path for name, path in optional.items() if sha256(run.root, path)}}
    manifest = trusted_bytes(artifact_review.GALLERY / "manifest.json", artifact_review.GALLERY)
    if manifest is None:
        raise ValueError("gallery manifest is unreadable")
    run.manifest_sha = hashlib.sha256(manifest).hexdigest()
    run.gallery = {entry["id"]: entry for entry in artifact_selection.draft_gallery_entries(manifest)}
    signals = workflow_stage_signals(workflow_text(run))
    if not signals["parsed"]:
        raise ValueError("the workflow file has no parseable Workflow Overview table")
    if "blocked" in str(signals["confidence_gate_status"]).casefold():
        raise Stop("strict_confidence_opt_in", "the confidence gate blocked in strict mode; no pull request was opened")
    if not signals["planning_complete"] or signals["confidence_gate_status"] is None:
        raise Stop("plan_stage_boundary", "planning phases and the confidence gate must finish before publication")
    rows = workflow_table_rows(HTML_COMMENT_RE.sub("", workflow_text(run)).splitlines(), "## Phase 6.5: Confidence Gate")
    gate = {cells[0].strip("*` ").casefold(): cells[1].strip("*` ") for cells in rows if len(cells) >= 2}
    verdict = call(run, "confidence-gate", "read_only", {"workflow_file": run.workflow, "mode_name": gate.get("mode", "")})
    action = verdict.get("data", {}).get("stdout_json", {}).get("recommended_action")
    if verdict["status"] != "ok" or action not in {"proceed", "continue_with_warning"}:
        raise Stop("plan_stage_boundary", "the confidence gate must explicitly pass or warn before publication")
    run.branch = command(run, ["git", "branch", "--show-current"], "the branch could not be read")


def commit(run: Run, paths: list[str], subject: str) -> None:
    command(run, ["git", "add", "--", *paths], f"staging for '{subject}' failed")
    if cli(run.root, ["git", "diff", "--cached", "--quiet"])["exit_status"] != 0:
        command(run, ["git", "commit", "-q", "-m", subject], f"the commit '{subject}' failed")
        run.commits.append(subject)


def remote(run: Run) -> str:
    remotes = command(run, ["git", "remote"], "no remote could be read").split()
    if "origin" in remotes or len(remotes) == 1:
        return "origin" if "origin" in remotes else remotes[0]
    raise Stop("plan_stage_boundary", "the remote could not be chosen: name one remote origin")


def push(run: Run) -> None:
    result = cli(run.root, ["git", "push", "-q", "-u", remote(run), run.branch])
    if result["exit_status"] != 0:
        reason = "protected_push" if "protected" in result["stderr_tail"].lower() else "plan_stage_boundary"
        raise Stop(reason, f"the branch push failed and no pull request was opened: {result['stderr_tail'][-200:]}")


def discard(run: Run, names: list[str]) -> None:
    try:
        artifact_publication.remove_pages(run.root, Path(run.feature), names)
    except OSError as error:
        raise Stop("integrity_failure", "artifact cleanup refused an unsafe directory or page") from error


def recorded_pages_current(run: Run) -> bool:
    """True when the recorded pages still match the planning inputs, so the author's prose is kept."""
    try:
        return artifact_review.generation_inputs_current(workflow_text(run), run.root, trusted_bytes)
    except ValueError:
        return False


def is_sample(page_id: str, content: bytes) -> bool:
    template = trusted_bytes(artifact_review.GALLERY / f"templates/{page_id}.html", artifact_review.GALLERY)
    return content == template or any(banner.encode() in content for banner in artifact_publication.BANNERS)


def fill_page(run: Run, page_id: str, directory: Path) -> str | None:
    """Fill a page nothing has written yet, then reject it when it is still a sample; the gap reason, or None."""
    path = directory / f"{page_id}.html"
    if not path.exists():
        filled = call(run, "fill-artifact-page", "apply", {**run.planning, "entry_id": page_id})
        if filled["status"] != "ok":
            return str(filled["diagnostics"][0]["message"])
    content = trusted_bytes(path, run.root)
    if content is None or path.stat().st_nlink != 1:
        raise Stop("integrity_failure", f"the page {page_id} is not a confined regular file")
    if is_sample(page_id, content):
        discard(run, [path.name])
        return "the page is still the sample template"
    return None


def fill_pages(run: Run, fresh: bool) -> dict[str, Any]:
    """Select before touching pages; every removal belongs to the confined publication owner."""
    selection = call(run, "select-artifact-pages", "read_only",
                     {name: path for name, path in run.planning.items() if name in artifact_publication.SELECTION_INPUTS})
    if selection["status"] != "ok":
        raise Stop("integrity_failure", str(selection["diagnostics"][0]["message"]))
    if not fresh and artifact_review.record_from_workflow(workflow_text(run)) is not None and not recorded_pages_current(run):
        raise Stop("integrity_failure", "planning inputs changed; regenerate the pages before finishing the stage")
    selected = selection["data"]["selected_pages"]
    directory = run.root / run.feature / "artifacts"
    if fresh and artifact_review.record_from_workflow(workflow_text(run)) is not None and not recorded_pages_current(run) and directory.exists():
        discard(run, [f"{page_id}.html" for page_id in run.gallery])
    gaps = []
    for page_id in selected:
        reason = fill_page(run, page_id, directory)
        if reason is not None:
            gaps.append({"id": page_id, "reason": reason})
    owned = [page_id for page_id in selected if page_id not in {gap["id"] for gap in gaps}]
    if directory.exists():
        discard(run, [f"{page_id}.html" for page_id in run.gallery if page_id not in owned])
    return {"generated": owned, "gaps": gaps, "selected": selected}


def page_entry(run: Run, page_id: str) -> dict[str, Any]:
    """The generated-page record: its digest, its title and one body passage distinct from the title."""
    path = f"{run.feature}/artifacts/{page_id}.html"
    html = text_of(run.root, path)
    filled = call(run, "fill-artifact-page", "dry_run", {**run.planning, "entry_id": page_id})
    if filled["status"] != "ok":
        raise Stop("integrity_failure", f"the planning evidence for {page_id} could not be rendered")
    title, body = (filled["data"][key] for key in ("expected_title", "expected_content"))
    found = TITLE.search(html)
    if not body or found is None or artifact_fill.html_text(found[1]) != title or body not in artifact_fill.html_text(html):
        raise Stop("integrity_failure", f"the page {page_id} does not match its planning title and feature content")
    return {"id": page_id, "generation": "generated", "path": path, "sha256": sha256(run.root, path),
            "expected_title": title, "expected_content": body,
            "preview": {"status": "pending", "blocker": "Not observed yet", "observation": None}}


def write_record(run: Run, pages: dict[str, Any]) -> None:
    """Write the Artifact Review Handoff record, the sole store for generation and preview evidence."""
    inputs = {f"{run.feature}/{name}.md": sha256(run.root, f"{run.feature}/{name}.md") for name in ("spec", "plan", "tasks")}
    inputs[f"{run.feature}/research.md"] = sha256(run.root, f"{run.feature}/research.md")
    inputs[run.concept] = sha256(run.root, run.concept)
    text = workflow_text(run)
    previous = artifact_review.record_from_workflow(text)
    reusable = artifact_review.review_handoff(text, run.root, trusted_bytes)["reuse_artifacts"]
    old_pages = {page["id"]: page for page in previous["pages"]} if previous is not None else {}
    entries = [page_entry(run, page_id) for page_id in pages["generated"]]
    for entry in entries:
        old = old_pages.get(entry["id"], {})
        preview = old.get("preview", {})
        if preview.get("status") == "denied" or (reusable and old.get("sha256") == entry["sha256"]):
            entry["preview"] = preview
    entries += [{"id": gap["id"], "generation": "gap", "reason": gap["reason"]} for gap in pages["gaps"] if gap["id"] != "all"]
    record = {"schema_version": "1.0", "feature_dir": run.feature, "input_hashes": inputs, "manifest_sha256": run.manifest_sha,
              "template_hashes": {e["id"]: sha256(artifact_review.GALLERY, f"templates/{e['id']}.html") for e in entries},
              "generation_error": next((gap["reason"] for gap in pages["gaps"] if gap["id"] == "all"), None), "pages": entries}
    section = "## Artifact Review Handoff\n\n```json\n" + json.dumps(record, indent=2) + "\n```\n"
    text = workflow_text(run)
    found = SECTION.search(text)
    if found is None:
        write(run.root, run.workflow, text.rstrip("\n") + "\n\n" + section)
        return
    blank_tail = found[0][len(found[0].rstrip("\n")) + 1:]
    write(run.root, run.workflow, text[:found.start()] + section + blank_tail + text[found.end():])


def sentence(text: str) -> str:
    return re.split(r"(?<=[.!?])\s", " ".join(text.split()), maxsplit=1)[0]


def draft_body(run: Run, title: str, pages: dict[str, Any]) -> str:
    """The two-section draft description: the artifacts index with gap rows, and the resume command."""
    rows = [f"| {run.gallery[page_id]['title']} | {sentence(run.gallery[page_id]['when_to_use'])} | "
            f"`open {run.feature}/artifacts/{page_id}.html` |" for page_id in pages["generated"]]
    rows += [f"| {run.gallery[gap['id']]['title'] if gap['id'] in run.gallery else 'All artifacts'} | Gap: {gap['reason']} | none |"
             for gap in pages["gaps"]]
    flag = run.inputs.get("unratified_defaults")
    resume = f"{RESUME[run.inputs['host']]} {run.workflow} --stage implement"
    return "\n".join([f"# {title}", "", "## Artifacts", "", "| Artifact | Purpose | Open |", "| --- | --- | --- |", *rows, "",
                      *([flag, ""] if flag else []), "## Resume", "",
                      "Stage: plan. Stopped at the plan-stage boundary for review.", f"Resume with: `{resume}`", ""])


def base_branch(run: Run) -> str:
    if run.inputs.get("base_branch"):
        return str(run.inputs["base_branch"])
    head = cli(run.root, ["git", "symbolic-ref", "--short", f"refs/remotes/{remote(run)}/HEAD"])
    return str(head["stdout_tail"]).split("/", 1)[-1] if head["exit_status"] == 0 else "main"


def build_packet(run: Run, pages: dict[str, Any]) -> dict[str, str]:
    """Generate, validate and commit the draft packet; the title comes from the workflow's Spec ID and Name."""
    scope = re.sub(r"[^a-z0-9]+", "-", run.info["spec id"].lower()).strip("-")
    title = {"title_type": "feat", "title_scope": scope, "title_description": f"plan {run.info['name']}"}
    subject = f"feat({scope}): {title['title_description']}"
    base = base_branch(run)
    request = {"packet_path": f"{run.feature}/.process/pr-packets/{PACKET_ID}.json", "source_feature_dir": run.feature,
               "target": {"base_branch": base, "head_branch": run.branch}, "mode": "draft", **title,
               "changed_files": [], "verification_evidence": [], "body": draft_body(run, subject, pages),
               **({"unratified_defaults": run.inputs["unratified_defaults"]} if run.inputs.get("unratified_defaults") else {})}
    for mode in ("dry_run", "apply"):
        made = call(run, "pr-packet-output", mode, request)
        if made["status"] != "ok":
            raise Stop("plan_stage_boundary", f"packet generation refused: {made['diagnostics'][0]['message']}")
    checked = call(run, "validate-pr-packet-read-only", "read_only", {"packet_path": request["packet_path"]})
    verdict = (checked.get("data") or {}).get("stdout_json") or {}
    if verdict.get("status") != "passed" or verdict.get("pr_blocked"):
        raise Stop("plan_stage_boundary", "packet validation did not pass; the packet is local and uncommitted")
    body_file = made["data"]["body_file"]
    commit(run, [body_file, request["packet_path"]], f"chore({run.info['spec id']}): add the draft pull request packet")
    return {"title": subject, "body_file": body_file, "base_branch": base}


def observe_branch(run: Run) -> dict[str, Any]:
    """The one read-only query for every pull request on the head branch, in the corroboration's shape."""
    listing = cli(run.root, ["gh", "pr", "list", "--head", run.branch, "--state", "all", "--json", "number,url,state,title"])
    try:
        pulls = json.loads(listing["stdout_tail"]) if listing["exit_status"] == 0 else None
    except ValueError:
        pulls = None
    return {"ok": isinstance(pulls, list), "pull_requests": pulls}


def existing_pull_request(run: Run, observation: dict[str, Any]) -> dict[str, Any] | None:
    """The pull request to refresh, or None to create; a discrepancy or an unanswered query stops the sequence."""
    row = workflow_draft_pr_row(HTML_COMMENT_RE.sub("", workflow_text(run)).splitlines())
    corroboration = corroborate_draft_pr(row, observation)
    recorded = corroboration["recorded"]
    if corroboration["status"] == "pr_closed":
        raise Stop("reopen_closed_pr", f"the recorded pull request #{recorded['number']} is closed; the operator reopens it, then re-runs")
    if corroboration["status"] == "pr_missing" or (corroboration["status"] == "identity_mismatch" and not corroboration["repair"]):
        raise Stop("ambiguous_pr_record", "the recorded and live pull requests disagree; the row was left as found")
    entries = observation_pull_requests(observation)
    if entries is None and recorded is None:
        raise Stop("tool_unavailable", "the pull request query could not answer, so nothing was created")
    opened = [entry for entry in entries or [] if entry["state"].casefold() == "open"]
    if len(opened) > 1 and recorded is None:
        raise Stop("ambiguous_pr_record", "several open pull requests answer for the branch")
    return corroboration["repair"] or recorded or ({"number": opened[0]["number"], "url": opened[0]["url"]} if opened else None)


def create_or_refresh(run: Run, packet: dict[str, str]) -> dict[str, Any]:
    """Create or refresh the one draft pull request by the two-way existence test: the recorded row and one live query."""
    observation = observe_branch(run)
    target = existing_pull_request(run, observation)
    pushed = "the artifacts and boundary commit are already pushed"
    if target is not None:
        known: dict[str, Any] = next((e for e in observation["pull_requests"] or [] if e["number"] == target["number"]), {})
        edit = ["gh", "pr", "edit", str(target["number"]), "--body-file", packet["body_file"]]
        command(run, edit + (["--title", packet["title"]] if known.get("title") != packet["title"] else []),
                f"the pull request refresh failed; {pushed}")
        return target
    created = command(run, ["gh", "pr", "create", "--draft", "--base", packet["base_branch"], "--head", run.branch,
                            "--title", packet["title"], "--body-file", packet["body_file"]],
                      f"the pull request could not be opened; {pushed}").splitlines()[-1]
    number = re.search(r"/pull/(\d+)$", created)
    if number is None:
        raise Stop("plan_stage_boundary", "the pull request was created but its URL could not be read")
    return {"number": int(number[1]), "url": created}


def record_pull_request(run: Run, found: dict[str, Any], pages: dict[str, Any]) -> None:
    """Write the `Draft PR` row whole and `plan/completed`, in the separate bookkeeping commit."""
    total = len(pages["selected"]) or len(pages["gaps"])
    note = f" — {len(pages['gaps'])} of {total} artifacts missing" if pages["gaps"] else ""
    write(run.root, run.workflow, set_basic_row(workflow_text(run), "Draft PR", f"[#{found['number']}]({found['url']}){note}"))
    state = json.loads(text_of(run.root, run.state))
    write(run.root, run.state, json.dumps({**state, "stage": "plan", "status": "completed"}, indent=2) + "\n")
    commit(run, [run.workflow, run.state], f"chore({run.info['spec id']}): record the draft pull request")
    push(run)


def stop_label(reason: str) -> str:
    stop_policy.stop_class(reason)
    return f"stop_reason:{reason}"


def pages_ready(pages: dict[str, Any]) -> dict[str, Any]:
    action = (f"Dispatch artifact-author once for pages {pages['generated']}, then call finish-plan-stage again without until."
              if pages["generated"] else "Call finish-plan-stage again without until.")
    return {"outcome": "pages_ready", "next_action": action}


def terminal_sequence(run: Run, pages: dict[str, Any]) -> dict[str, Any]:
    surface = "unavailable" if run.inputs.get("execution_mode") == "headless" else preview_surface(run.root, run.inputs["host"])
    write_record(run, pages)
    try:
        artifact_review.review_handoff(workflow_text(run), run.root, trusted_bytes, surface)
    except ValueError as error:
        raise Stop("integrity_failure", f"a generated page failed its fill check: {error}") from error
    commit(run, ["specs/", run.workflow, run.state], f"chore({run.info['spec id']}): {BOUNDARY}")
    packet = build_packet(run, pages)
    push(run)
    found = create_or_refresh(run, packet)
    record_pull_request(run, found, pages)
    review = artifact_review.review_handoff(workflow_text(run), run.root, trusted_bytes, surface)
    pending = review["observer_dispatches"]
    done = {"pull_request": found, "commits": run.commits,
            "preview": {"status": review["status"], "note": review.get("preview_note"), "observer_dispatches": pending}}
    label = stop_label("plan_stage_boundary")
    if review["status"] == "pending":
        return {**done, "outcome": "preview_pending", "stop_label": None,
                "next_action": f"Observe pages {pending} through the runner, commit the preview evidence, then print {label}."}
    return {**done, "outcome": "completed", "stop_label": label,
            "next_action": f"Print the stop report, then {label} as the last line, and stop."}


def check_inputs(inputs: dict[str, Any]) -> None:
    if set(inputs) - INPUTS:
        raise ValueError("finish-plan-stage received unknown inputs")
    if inputs.get("host") not in RESUME or inputs.get("execution_mode", "interactive") not in ("interactive", "headless"):
        raise ValueError("host must be claude or codex and execution_mode interactive or headless")
    if inputs.get("until", "pages") != "pages":
        raise ValueError("until accepts only pages")
    for name in ("workflow_file", *PLANNING):
        if not isinstance(inputs.get(name), str):
            raise ValueError(f"{name} is required")


def finish(run: Run, apply: bool) -> dict[str, Any]:
    prepare(run, run.inputs)
    if not apply:
        return {"outcome": "dry_run", "next_action": "Apply the finish-plan-stage request to run the terminal sequence.",
                "writes_state": False}
    pages = fill_pages(run, fresh=run.inputs.get("until") == "pages")
    summary = {"pages": {"generated": pages["generated"], "gaps": pages["gaps"]}, "writes_state": True}
    if run.inputs.get("until") == "pages":
        write_record(run, pages)
        return {**summary, **pages_ready(pages)}
    return {**summary, **terminal_sequence(run, pages)}


def run_plan_stage_terminal_helper(entry: Any, request: Any, dispatch: Dispatch) -> dict[str, Any]:
    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    try:
        check_inputs(request.inputs)
        data = finish(Run(root, request.inputs, dispatch, request), request.mode == "apply")
    except Stop as stop:
        label = stop_label(stop.reason)
        return response("expected_failure", request_id=request.request_id, data={
            "helper_id": entry.helper_id, "outcome": "stopped", "stop_label": label, "report": stop.report,
            "next_action": f"Print the stop report, then {label} as the last line, and stop."},
            diagnostics=[diagnostic("plan_stage_stopped", stop.report, remediation_summary="Follow the stop report's resume path.")])
    except (ValueError, KeyError, OSError) as error:
        return response("input_error", request_id=request.request_id, diagnostics=[diagnostic(
            "plan_stage_invalid", str(error), remediation_summary="Correct the request or the workflow file, then retry.")])
    return response("ok", request_id=request.request_id, data={"helper_id": entry.helper_id, **data})
