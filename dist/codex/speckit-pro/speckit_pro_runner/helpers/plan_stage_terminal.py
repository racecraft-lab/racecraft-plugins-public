"""The runner owns the plan stage's terminal sequence (ADR 0026).

One mutation helper fills the artifact pages, takes the stage-boundary commit, builds and commits the
draft packet, pushes, creates or refreshes the draft pull request, records it, and writes
`plan/completed` (state `stage: plan`, `status: completed`). A model writes only the page prose,
through one artifact-author dispatch between the `pages` call and the finishing call (ADR 0019).
A step that cannot finish stops the sequence with the stop label the prose table used to hold.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable

from .. import artifact_review, cli_probe, stop_policy
from ..atomic_write import write_bytes_atomic
from ..envelope import RunnerRequest, diagnostic, response
from ..trusted_io import resolve_repo_root, trusted_bytes
from ..workflow_stage import AUTOPILOT_BASIC_INFO_HEADING, HTML_COMMENT_RE, workflow_stage_signals, workflow_table_rows
from . import artifact_publication, artifact_selection
from .read_only import corroborate_draft_pr, observation_pull_requests, workflow_draft_pr_row
from .readiness_record import preview_surface

Dispatch = Callable[[Any], dict[str, Any]]
TIMEOUT_SECONDS = 120
PACKET_ID = "draft"
BOUNDARY = "close the plan stage boundary"
PLANNING = ("plan_file", "spec_file", "tasks_file")
INPUTS = frozenset({"repo_root", "host", "workflow_file", "execution_mode", "until", "base_branch",
                    "unratified_defaults", *PLANNING})
RESUME = {"claude": "/speckit-pro:speckit-autopilot", "codex": "$speckit-pro:speckit-autopilot"}
OPEN = "open"
CONTENT = re.compile(r"<(?:p|dd|li|h2)\b[^>]*>(.*?)</(?:p|dd|li|h2)>", re.DOTALL)
TAG = re.compile(r"<[^>]+>")
SECTION = re.compile(r"(?ms)^## Artifact Review Handoff\n.*?(?=^## |\Z)")


class Stop(Exception):
    """The sequence ends here; `reason` is a stop-policy reason and `report` names the step and the state left."""

    def __init__(self, reason: str, report: str) -> None:
        super().__init__(report)
        self.reason, self.report = reason, report


def cli(root: Path, argv: list[str]) -> dict[str, Any]:
    """The one place this helper runs git or gh."""
    return cli_probe.probe(root, argv, allowed=("git", "gh"), timeout=TIMEOUT_SECONDS)


def run(root: Path, argv: list[str], failure: str, reason: str = "plan_stage_boundary") -> str:
    result = cli(root, argv)
    if result["exit_status"] != 0:
        raise Stop(reason, f"{failure}: {result['stderr_tail'][-200:] or 'the command did not run'}")
    return str(result["stdout_tail"])


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
        if lines[index].startswith("|"):
            last = index
            cells = [cell.strip("*` ").casefold() for cell in lines[index].strip("| ").split("|")]
            if cells and cells[0] == key.casefold():
                lines[index] = row
                return "\n".join(lines) + "\n"
        elif index > start + 1 and lines[index].strip():
            break
    lines.insert(last + 1, row)
    return "\n".join(lines) + "\n"


def sentence(text: str) -> str:
    return re.split(r"(?<=[.!?])\s", " ".join(text.split()), maxsplit=1)[0]


def title_of(info: dict[str, str]) -> dict[str, str]:
    return {"title_type": "feat", "title_scope": re.sub(r"[^a-z0-9]+", "-", info["spec id"].lower()).strip("-"),
            "title_description": f"plan {info['name']}"}


def draft_body(title: str, feature: str, gallery: dict[str, dict[str, Any]], pages: dict[str, Any], inputs: dict[str, Any]) -> str:
    rows = [f"| {gallery[page_id]['title']} | {sentence(gallery[page_id]['when_to_use'])} | `open {feature}/artifacts/{page_id}.html` |"
            for page_id in pages["generated"]]
    rows += [f"| {gallery[gap['id']]['title'] if gap['id'] in gallery else 'All artifacts'} | Gap: {gap['reason']} | none |"
             for gap in pages["gaps"]]
    flag = inputs.get("unratified_defaults")
    resume = f"{RESUME[inputs['host']]} {inputs['workflow_file']} --stage implement"
    return "\n".join([f"# {title}", "", "## Artifacts", "", "| Artifact | Purpose | Open |", "| --- | --- | --- |", *rows, "",
                      *([flag, ""] if flag else []), "## Resume", "",
                      "Stage: plan. Stopped at the plan-stage boundary for review.", f"Resume with: `{resume}`", ""])


def check_inputs(inputs: dict[str, Any]) -> None:
    if set(inputs) - INPUTS:
        raise ValueError("finish-plan-stage received unknown inputs")
    if inputs.get("host") not in RESUME or inputs.get("execution_mode", "interactive") not in ("interactive", "headless"):
        raise ValueError("host must be claude or codex and execution_mode interactive or headless")
    if inputs.get("until", "pages") != "pages":
        raise ValueError("until accepts only pages")
    for field in ("workflow_file", "plan_file", "spec_file", "tasks_file"):
        if not isinstance(inputs.get(field), str):
            raise ValueError(f"{field} is required")


class Sequence:
    """One run of the terminal sequence over a repository; each method is one step of it."""

    def __init__(self, root: Path, inputs: dict[str, Any], dispatch: Dispatch, request: RunnerRequest) -> None:
        self.root, self.inputs, self.dispatch, self.request = root, inputs, dispatch, request
        self.workflow = inputs["workflow_file"]
        self.state = str(Path(self.workflow).with_name("autopilot-state.json"))
        self.feature = str(Path(inputs["plan_file"]).parent)
        self.info = basic_information(self.read_workflow())
        if not {"spec id", "name"} <= self.info.keys():
            raise ValueError("the workflow file's Basic Information needs Spec ID and Name rows")
        self.concept = f"docs/ai/specs/.process/{self.info['spec id']}-design-concept.md"
        optional = {"research_file": f"{self.feature}/research.md", "design_concept_file": self.concept}
        self.planning = {**{field: inputs[field] for field in PLANNING},
                         **{field: path for field, path in optional.items() if sha256(root, path)}}
        self.branch = ""
        self.commits: list[str] = []
        manifest = trusted_bytes(artifact_review.GALLERY / "manifest.json", artifact_review.GALLERY)
        if manifest is None:
            raise ValueError("gallery manifest is unreadable")
        self.manifest_sha = hashlib.sha256(manifest).hexdigest()
        self.gallery = {entry["id"]: entry for entry in artifact_selection.draft_gallery_entries(manifest)}

    def call(self, helper_id: str, mode: str, inputs: dict[str, Any]) -> dict[str, Any]:
        return self.dispatch(RunnerRequest(self.request.request_id, helper_id, helper_id, mode, inputs))

    def commit(self, paths: list[str], subject: str) -> None:
        run(self.root, ["git", "add", "--", *paths], f"staging for '{subject}' failed")
        if cli(self.root, ["git", "diff", "--cached", "--quiet"])["exit_status"] != 0:
            run(self.root, ["git", "commit", "-q", "-m", subject], f"the commit '{subject}' failed")
            self.commits.append(subject)

    def read_workflow(self) -> str:
        return text_of(self.root, self.workflow)

    def reusable(self) -> bool:
        """True when the recorded pages still match the planning inputs, so the author's prose is kept."""
        try:
            return bool(artifact_review.review_handoff(self.read_workflow(), self.root, trusted_bytes)["reuse_artifacts"])
        except ValueError:
            return False

    def discard(self, path: Path) -> None:
        try:
            path.unlink()
        except OSError as error:
            raise Stop("integrity_failure", f"an unowned artifact file could not be removed: {path.name}") from error

    def pages(self, fresh: bool) -> dict[str, Any]:
        """Fill the selected pages nothing has written yet; delete any page that is no generated page of this run.

        `fresh` starts a run: pages left by a run whose inputs have since changed are deleted and refilled.
        Otherwise a page on disk is kept, because the author has written its prose.
        """
        directory = self.root / self.feature / "artifacts"
        files = list(directory.iterdir()) if directory.is_dir() else []
        if fresh and not self.reusable():
            for stale in files:
                if stale.stem in self.gallery:
                    self.discard(stale)
        selection = self.call("select-artifact-pages", "read_only",
                              {field: self.planning[field] for field in artifact_publication.SELECTION_INPUTS if field in self.planning})
        selected = selection["data"].get("selected_pages", [])
        gaps = [] if selection["status"] == "ok" else [{"id": "all", "reason": selection["diagnostics"][0]["message"]}]
        for page_id in selected:
            path = directory / f"{page_id}.html"
            if not path.exists():
                filled = self.call("fill-artifact-page", "apply", {**self.planning, "entry_id": page_id})
                if filled["status"] != "ok":
                    gaps.append({"id": page_id, "reason": filled["diagnostics"][0]["message"]})
                    continue
            template = trusted_bytes(artifact_review.GALLERY / f"templates/{page_id}.html", artifact_review.GALLERY)
            if path.read_bytes() == template or any(banner.encode() in path.read_bytes() for banner in artifact_publication.BANNERS):
                self.discard(path)
                gaps.append({"id": page_id, "reason": "the page is still the sample template"})
        owned = [page_id for page_id in selected if page_id not in {gap["id"] for gap in gaps}]
        for stale in directory.iterdir() if directory.is_dir() else []:
            if (stale.name.startswith(".artifact-author-") and stale.suffix == ".tmp") or (
                    stale.suffix == ".html" and stale.stem in self.gallery and stale.stem not in owned):
                self.discard(stale)
        return {"generated": owned, "gaps": gaps, "selected": selected}

    def record(self, pages: dict[str, Any]) -> str:
        """Write the Artifact Review Handoff record, the sole store for generation and preview evidence."""
        inputs = {f"{self.feature}/{name}.md": sha256(self.root, f"{self.feature}/{name}.md") for name in ("spec", "plan", "tasks")}
        inputs[self.concept] = sha256(self.root, self.concept)
        entries = []
        for page_id in pages["generated"]:
            path = f"{self.feature}/artifacts/{page_id}.html"
            html = text_of(self.root, path)
            title = " ".join(TAG.sub("", (re.search(r"<title>(.*?)</title>", html, re.DOTALL) or [None, page_id])[1]).split())
            body = next((" ".join(TAG.sub("", c).split()) for c in CONTENT.findall(html) if len(" ".join(TAG.sub("", c).split())) >= 12
                         and " ".join(TAG.sub("", c).split()) not in title), "")
            if not body:
                raise Stop("integrity_failure", f"the page {page_id} carries no feature content to observe")
            entries.append({"id": page_id, "generation": "generated", "path": path, "sha256": sha256(self.root, path),
                            "expected_title": title, "expected_content": body,
                            "preview": {"status": "pending", "blocker": "Not observed yet", "observation": None}})
        entries += [{"id": gap["id"], "generation": "gap", "reason": gap["reason"]} for gap in pages["gaps"] if gap["id"] != "all"]
        whole = next((gap["reason"] for gap in pages["gaps"] if gap["id"] == "all"), None)
        record = {"schema_version": "1.0", "feature_dir": self.feature, "input_hashes": inputs, "manifest_sha256": self.manifest_sha,
                  "template_hashes": {e["id"]: sha256(artifact_review.GALLERY, f"templates/{e['id']}.html") for e in entries},
                  "generation_error": whole, "pages": entries}
        section = "## Artifact Review Handoff\n\n```json\n" + json.dumps(record, indent=2) + "\n```\n"
        text = self.read_workflow()
        text = SECTION.sub(lambda found: section + found.group(0)[len(found.group(0).rstrip("\n")) + 1:], text, count=1) \
            if SECTION.search(text) else text.rstrip("\n") + "\n\n" + section
        write(self.root, self.workflow, text)
        return text

    def packet(self, pages: dict[str, Any]) -> tuple[str, dict[str, str]]:
        info = self.info
        title = title_of(info)
        remote = cli(self.root, ["git", "symbolic-ref", "--short", f"refs/remotes/{self.remote()}/HEAD"])
        base = self.inputs.get("base_branch") or (str(remote["stdout_tail"]).split("/", 1)[-1] if remote["exit_status"] == 0 else "main")
        subject = f"{title['title_type']}({title['title_scope']}): {title['title_description']}"
        request = {"packet_path": f"{self.feature}/.process/pr-packets/{PACKET_ID}.json", "source_feature_dir": self.feature,
                   "target": {"base_branch": base, "head_branch": self.branch}, "mode": "draft", **title,
                   "changed_files": [], "verification_evidence": [],
                   "body": draft_body(subject, self.feature, self.gallery, pages, self.inputs),
                   **({"unratified_defaults": self.inputs["unratified_defaults"]} if self.inputs.get("unratified_defaults") else {})}
        for mode in ("dry_run", "apply"):
            made = self.call("pr-packet-output", mode, request)
            if made["status"] != "ok":
                raise Stop("plan_stage_boundary", f"packet generation refused: {made['diagnostics'][0]['message']}")
        checked = self.call("validate-pr-packet-read-only", "read_only", {"packet_path": request["packet_path"]})
        verdict = (checked.get("data") or {}).get("stdout_json") or {}
        if verdict.get("status") != "passed" or verdict.get("pr_blocked"):
            raise Stop("plan_stage_boundary", "packet validation did not pass; the packet is local and uncommitted")
        self.commit([made["data"]["body_file"], request["packet_path"]], f"chore({info['spec id']}): add the draft pull request packet")
        return subject, {"body_file": made["data"]["body_file"], "base_branch": base}

    def remote(self) -> str:
        remotes = run(self.root, ["git", "remote"], "no remote could be read").split()
        if "origin" in remotes or len(remotes) == 1:
            return "origin" if "origin" in remotes else remotes[0]
        raise Stop("plan_stage_boundary", "the remote could not be chosen: name one remote origin")

    def push(self) -> None:
        result = cli(self.root, ["git", "push", "-q", "-u", self.remote(), self.branch])
        if result["exit_status"] != 0:
            protected = "protected" in result["stderr_tail"].lower()
            raise Stop("protected_push" if protected else "plan_stage_boundary",
                       f"the branch push failed and no pull request was opened: {result['stderr_tail'][-200:]}")

    def pull_request(self, title: str, packet: dict[str, str]) -> dict[str, Any]:
        """Create or refresh the one draft pull request, by the two-way existence test."""
        listing = cli(self.root, ["gh", "pr", "list", "--head", self.branch, "--state", "all", "--json", "number,url,state,title"])
        observation: dict[str, Any] = {"ok": False}
        if listing["exit_status"] == 0:
            try:
                observation = {"ok": True, "pull_requests": json.loads(listing["stdout_tail"])}
            except ValueError:
                pass
        entries = observation_pull_requests(observation)
        row = workflow_draft_pr_row(HTML_COMMENT_RE.sub("", self.read_workflow()).splitlines())
        corroboration = corroborate_draft_pr(row, observation)
        status = corroboration["status"]
        recorded = corroboration["recorded"]
        if status == "pr_closed":
            raise Stop("reopen_closed_pr", f"the recorded pull request #{recorded['number']} is closed; the operator reopens it, then re-runs")
        if status == "pr_missing" or (status == "identity_mismatch" and not corroboration["repair"]):
            raise Stop("ambiguous_pr_record", "the recorded and live pull requests disagree; the row was left as found")
        if entries is None and recorded is None:
            raise Stop("tool_unavailable", "the pull request query could not answer, so nothing was created")
        target = corroboration["repair"] or recorded
        opened = [entry for entry in entries or [] if entry["state"].casefold() == OPEN]
        if target is None and len(opened) > 1:
            raise Stop("ambiguous_pr_record", "several open pull requests answer for the branch")
        if target is None and opened:
            target = {"number": opened[0]["number"], "url": opened[0]["url"]}
        if target is not None:
            known = next((entry for entry in entries or [] if entry["number"] == target["number"]), {})
            edit = ["gh", "pr", "edit", str(target["number"]), "--body-file", packet["body_file"]]
            run(self.root, edit + (["--title", title] if known.get("title") != title else []),
                "the pull request refresh failed; the artifacts and boundary commit are already pushed")
            return target
        url = run(self.root, ["gh", "pr", "create", "--draft", "--base", packet["base_branch"], "--head", self.branch,
                              "--title", title, "--body-file", packet["body_file"]],
                  "the pull request could not be opened; the artifacts and boundary commit are already pushed").splitlines()[-1]
        number = re.search(r"/pull/(\d+)$", url)
        if number is None:
            raise Stop("plan_stage_boundary", "the pull request was created but its URL could not be read")
        return {"number": int(number[1]), "url": url}


def finish(root: Path, inputs: dict[str, Any], sequence: Sequence, apply: bool) -> dict[str, Any]:
    signals = workflow_stage_signals(sequence.read_workflow())
    if not signals["parsed"]:
        raise ValueError("the workflow file has no parseable Workflow Overview table")
    if "blocked" in str(signals["confidence_gate_status"]).casefold():
        raise Stop("strict_confidence_opt_in", "the confidence gate blocked in strict mode; no pull request was opened")
    sequence.branch = run(root, ["git", "branch", "--show-current"], "the branch could not be read")
    if not apply:
        return {"outcome": "dry_run", "next_action": "Apply the finish-plan-stage request to run the terminal sequence.", "writes_state": False}
    pages = sequence.pages(fresh=inputs.get("until") == "pages")
    base = {"pages": {"generated": pages["generated"], "gaps": pages["gaps"]}, "writes_state": True}
    if inputs.get("until") == "pages":
        action = (f"Dispatch artifact-author once for pages {pages['generated']}, then call finish-plan-stage again without until."
                  if pages["generated"] else "Call finish-plan-stage again without until.")
        return {**base, "outcome": "pages_ready", "next_action": action}
    spec = sequence.info["spec id"]
    sequence.record(pages)
    surface = "unavailable" if inputs.get("execution_mode") == "headless" else preview_surface(root, inputs["host"])
    try:
        artifact_review.review_handoff(sequence.read_workflow(), root, trusted_bytes, surface)
    except ValueError as error:
        raise Stop("integrity_failure", f"a generated page failed its fill check: {error}") from error
    sequence.commit(["specs/", sequence.workflow, sequence.state], f"chore({spec}): {BOUNDARY}")
    title, packet = sequence.packet(pages)
    sequence.push()
    found = sequence.pull_request(title, packet)
    gap = f" — {len(pages['gaps'])} of {len(pages['selected']) or len(pages['gaps'])} artifacts missing" if pages["gaps"] else ""
    write(root, sequence.workflow, set_basic_row(sequence.read_workflow(), "Draft PR", f"[#{found['number']}]({found['url']}){gap}"))
    state = json.loads(text_of(root, sequence.state))
    write(root, sequence.state, json.dumps({**state, "stage": "plan", "status": "completed"}, indent=2) + "\n")
    sequence.commit([sequence.workflow, sequence.state], f"chore({spec}): record the draft pull request")
    sequence.push()
    review = artifact_review.review_handoff(sequence.read_workflow(), root, trusted_bytes, surface)
    pending = review["observer_dispatches"]
    done = {**base, "pull_request": found, "commits": sequence.commits, "writes_state": True,
            "preview": {"status": review["status"], "note": review.get("preview_note"), "observer_dispatches": pending}}
    if pending:
        return {**done, "outcome": "preview_pending", "stop_label": None,
                "next_action": f"Observe pages {pending} through the runner, commit the preview evidence, then print {stop_label('plan_stage_boundary')}."}
    return {**done, "outcome": "completed", "stop_label": stop_label("plan_stage_boundary"),
            "next_action": f"Print the stop report, then {stop_label('plan_stage_boundary')} as the last line, and stop."}


def stop_label(reason: str) -> str:
    stop_policy.stop_class(reason)
    return f"stop_reason:{reason}"


def run_plan_stage_terminal_helper(entry: Any, request: Any, dispatch: Dispatch) -> dict[str, Any]:
    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    try:
        check_inputs(request.inputs)
        sequence = Sequence(root, request.inputs, dispatch, request)
        data = finish(root, request.inputs, sequence, request.mode == "apply")
    except Stop as stop:
        return response("expected_failure", request_id=request.request_id, data={
            "helper_id": entry.helper_id, "outcome": "stopped", "stop_label": stop_label(stop.reason), "report": stop.report,
            "next_action": f"Print the stop report, then {stop_label(stop.reason)} as the last line, and stop."},
            diagnostics=[diagnostic("plan_stage_stopped", stop.report, remediation_summary="Follow the stop report's resume path.")])
    except (ValueError, KeyError, OSError) as error:
        return response("input_error", request_id=request.request_id, diagnostics=[diagnostic(
            "plan_stage_invalid", str(error), remediation_summary="Correct the request or the workflow file, then retry.")])
    return response("ok", request_id=request.request_id, data={"helper_id": entry.helper_id, **data})
