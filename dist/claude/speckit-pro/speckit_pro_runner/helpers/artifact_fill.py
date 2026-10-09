"""The runner fills draft artifact pages from the planning files (ADR 0019).

Structured regions come straight from the planning files. Each prose slot holds
text lifted from them, so a page is complete before any model writes. The one
narrative dispatch may replace a slot with short plain text, which the runner
escapes and wraps in markup. Publication stays with artifact_publication.
"""

from __future__ import annotations

import dataclasses
import re
from collections.abc import Callable, Iterable
from html import escape
from pathlib import Path
from typing import Any

from ..envelope import diagnostic, response
from ..strict_input import require_text
from ..trusted_io import resolve_repo_root, trusted_bytes
from . import artifact_publication, artifact_selection
from .read_only import declared_file_entries

INPUTS = frozenset({*artifact_publication.SELECTION_INPUTS, "entry_id", "spec_file", "tasks_file", "narrative"})
PLANNING = {"plan": ("plan_file", True), "spec": ("spec_file", True), "tasks": ("tasks_file", True),
            "research": ("research_file", False), "design": ("design_concept_file", False)}
NARRATIVE_LIMIT = 1200
LIFT_LIMIT = 600
NOT_RECORDED = "Not recorded in the planning files."
PROSE_START = re.compile(r"(?![-*+]\s)[A-Za-z0-9`\"(*_]")
TASK = re.compile(r"^\s*[-*] \[[ xX]\] (T\d+)\s+(?:\[[^\]]*\]\s*)*(.+)$")
QUESTION = re.compile(r"^Q:\s*(.+?)\s*(?:→|->)\s*A:\s*(.+)$")
CRITERION = re.compile(r"^\*\*(SC-\d+)\*\*:?\s*(.*)$", re.DOTALL)
LEAD = re.compile(r"^\*\*(.+?)\*\*:?\s*(.*)$", re.DOTALL)
STORY = re.compile(r"^User Story \d+\s*[-—]\s*(.+?)(?:\s*\(Priority.*)?$")
SLOT = re.compile(r"Slot:\s*([a-z0-9-]+)\s*\|\s*Fills:\s*([^|]+?)\s*\|")
SIZE = re.compile(r"Projected reviewable LOC\W{0,12}(\d+)", re.IGNORECASE)


def plain(text: str) -> str:
    """Planning Markdown as one line of text; the caller escapes it."""
    return " ".join(re.sub(r"[*`]", "", text).split())


def clip(text: str) -> str:
    return text if len(text) <= LIFT_LIMIT else text[:LIFT_LIMIT].rsplit(" ", 1)[0] + " …"


def sections(text: str, depth: int = 6) -> list[tuple[str, list[str]]]:
    """Split planning lines at headings no deeper than `depth`; deeper headings stay in the body."""
    found: list[tuple[str, list[str]]] = [("", [])]
    for line in artifact_selection.planning_lines(text):
        heading = artifact_selection.HEADING.match(line)
        if heading and len(heading.group(1)) <= depth:
            found.append((plain(heading.group(2)), []))
        else:
            found[-1][1].append(line)
    return found


def section(text: str, title: str) -> list[str]:
    """The body of the first heading starting with `title`, through its subsections."""
    level, found = 0, []
    for line in artifact_selection.planning_lines(text):
        heading = artifact_selection.HEADING.match(line)
        if heading and level and len(heading[1]) <= level:
            break
        if level:
            found.append(line)
        elif heading and plain(heading[2]).lower().startswith(title.lower()):
            level = len(heading[1])
    return found


def paragraphs(lines: Iterable[str]) -> list[str]:
    """Prose blocks only: list items, tables, quotes, and indented blocks are not lifted."""
    blocks = re.split(r"\n\s*\n", "\n".join(lines))
    return [plain(block) for block in blocks if PROSE_START.match(block.lstrip("\n"))]


def bullets(lines: Iterable[str]) -> list[str]:
    """Top-level list items with their wrapped continuation lines, Markdown kept."""
    items: list[str] = []
    for line in lines:
        marker = re.match(r"(?:[-*+]|\d+\.)\s", line)
        if marker:
            items.append(line[marker.end():].strip())
        elif items and line.startswith(" ") and line.strip():
            items[-1] += " " + line.strip()
    return items


def lead(lines: Iterable[str], index: int = 0) -> str:
    """The `index`-th prose paragraph, or nothing; a missing paragraph is never borrowed from another."""
    found = paragraphs(lines)
    return clip(found[index]) if index < len(found) else ""


def counted(number: int, noun: str) -> str:
    return f"{number} {noun}" + ("" if number == 1 else "s")


@dataclasses.dataclass
class Page:
    feature: str
    name: str
    texts: dict[str, str]
    narrative: dict[str, str]
    kind: str = "Artifact"
    slots: dict[str, str] = dataclasses.field(default_factory=dict)
    guidance: dict[str, str] = dataclasses.field(default_factory=dict)
    anchors: set[str] = dataclasses.field(default_factory=set)

    def prose(self, slot: str, fallback: str, css: str = "") -> str:
        """One prose slot: the narrative text when written, else the lifted fallback."""
        self.slots[slot] = fallback or NOT_RECORDED
        attribute = f' class="{css}"' if css else ""
        return f"<p{attribute}>{escaped(self.narrative.get(slot, self.slots[slot]))}</p>"

    def anchor(self, prefix: str, label: str) -> str:
        base = f"{prefix}-{re.sub(r'[^a-z0-9]+', '-', label.lower()).strip('-') or 'item'}"
        candidate, number = base, 2
        while candidate in self.anchors:
            candidate, number = f"{base}-{number}", number + 1
        self.anchors.add(candidate)
        return candidate

    def phases(self) -> list[tuple[str, list[tuple[str, str]]]]:
        return [(title, [(match[1], plain(match[2])) for match in map(TASK.match, lines) if match])
                for title, lines in sections(self.texts["tasks"], 2) if title.lower().startswith("phase")]

    def modules(self) -> dict[str, list[tuple[str, str]]]:
        groups: dict[str, list[tuple[str, str]]] = {}
        for status, path in declared_file_entries(self.texts["plan"]):
            groups.setdefault(Path(path).parent.as_posix(), []).append((status, path))
        return groups


def escaped(value: str) -> str:
    return escape(value, quote=True)


def listing(items: list[str], opening: str, closing: str) -> str:
    return f"{opening}{''.join(items)}{closing}" if items else f"<p>{NOT_RECORDED}</p>"


def header(page: Page) -> str:
    return (f'<p class="eyebrow"><span id="feature-id">{escaped(page.feature)}</span> · draft pull request</p>'
            f'<h1 id="feature-name">{escaped(page.name)}</h1>'
            + page.prose("feature-header", lead(section(page.texts["plan"], "Summary")), "lede"))


def plan_stats(page: Page) -> str:
    size = SIZE.search(page.texts["spec"] + page.texts["plan"])
    rows = (("Phases", len(page.phases())), ("Files touched", len(declared_file_entries(page.texts["plan"]))),
            ("Projected size", f"{size[1]} lines" if size else "not recorded"), ("Behind flag", "none recorded"))
    return listing([f'<div class="stat"><dt>{label}</dt><dd>{escaped(str(value))}</dd></div>' for label, value in rows],
                   '<dl class="stats">', "</dl>")


def phases(page: Page) -> str:
    return "".join(f'<div class="milestone" id="{page.anchor("phases", title)}"><h3>{escaped(title)}</h3>'
                   f'<p class="what">{counted(len(tasks), "task")}</p></div>' for title, tasks in page.phases()) or listing([], "", "")


def task_inventory(page: Page) -> str:
    panels = [f'<div class="task-panel"><h3>{escaped(title)}</h3><p class="task-count">{counted(len(tasks), "task")}</p>'
              + listing([f'<li><span class="task-id">{escaped(task)}</span>{escaped(clip(body))}</li>' for task, body in tasks],
                        '<ul class="task-list">', "</ul>") + "</div>" for title, tasks in page.phases()]
    return listing(panels, '<div class="task-grid">', "</div>")


def risk_register(page: Page) -> str:
    rows = []
    for item in bullets(section(page.texts["spec"], "Edge Cases")):
        match = LEAD.match(item)
        risk, handling = (match[1], match[2]) if match else (item, "")
        rows.append(f'<tr><th scope="row">{escaped(clip(plain(risk)))}</th><td>Not rated</td>'
                    f"<td>{escaped(clip(plain(handling)) or NOT_RECORDED)}</td></tr>")
    return listing(rows, '<table class="risks"><thead><tr><th scope="col">Risk</th><th scope="col">Severity</th>'
                   '<th scope="col">Mitigation</th></tr></thead><tbody>', "</tbody></table>")


def goals(page: Page) -> str:
    stories = [match[1] for name, _ in sections(page.texts["spec"]) if (match := STORY.match(name))]
    return listing([f"<li>{escaped(story)}</li>" for story in stories], '<ul class="points">', "</ul>")


def non_goals(page: Page) -> str:
    items = bullets(section(page.texts["spec"], "Out of Scope")) or bullets(section(page.texts["design"], "Non-goals"))
    return listing([f"<li>{escaped(clip(plain(item)))}</li>" for item in items], '<ul class="points">', "</ul>")


def acceptance(page: Page) -> str:
    criteria = [match for item in bullets(section(page.texts["spec"], "Success Criteria")) if (match := CRITERION.match(item))]
    return listing([f'<details><summary>{escaped(match[1])}</summary><div class="body"><p>{escaped(clip(plain(match[2])))}'
                    "</p></div></details>" for match in criteria], "", "")


def faq(page: Page) -> str:
    pairs = [match for item in bullets(section(page.texts["spec"], "Clarifications")) if (match := QUESTION.match(plain(item)))]
    return listing([f"<dt>{escaped(match[1])}</dt><dd>{escaped(clip(match[2]))}</dd>" for match in pairs],
                   '<dl class="faq">', "</dl>")


def decisions(page: Page) -> list[tuple[str, str, list[str]]]:
    """Each research or design section that records alternatives: its title, decision, and alternatives."""
    found = []
    for title, lines in sections(page.texts["research"] + "\n" + page.texts["design"], 2):
        start = next((index for index, line in enumerate(lines) if "alternatives" in line.lower()), None)
        if start is not None and artifact_selection.records_alternatives("\n".join(lines)):
            chosen = next((block[9:].strip() for block in paragraphs(lines) if block.startswith("Decision:")), "")
            found.append((title, chosen, [plain(item) for item in bullets(lines[start + 1:])]))
    return found


def approaches(page: Page) -> str:
    return "".join(f'<article class="approach" id="{page.anchor("approaches", title)}"><header class="approach-head">'
                   f"<h3>{escaped(title)}</h3><p>{escaped(clip(chosen) or NOT_RECORDED)}</p></header>"
                   + listing([f'<li class="chip">{escaped(clip(item))}</li>' for item in options], '<ul class="chips">', "</ul>")
                   + "</article>" for title, chosen, options in decisions(page)) or listing([], "", "")


def recommendation(page: Page) -> str:
    return page.prose("recommendation", next((clip(chosen) for _, chosen, _ in decisions(page) if chosen), ""))


def module_graph(page: Page) -> str:
    groups = page.modules()
    rows = [f"<li>{escaped(directory)}: {counted(len(files), 'file')}</li>" for directory, files in groups.items()]
    caption = f"The change touches {counted(len(groups), 'module')}, one per directory below." if groups else ""
    return ('<figure class="graph"><figcaption>' + page.prose("module-graph", caption)
            + "</figcaption>" + listing(rows, "<ul>", "</ul>") + "</figure>")


def modules(page: Page) -> str:
    return "".join(f'<div class="module" id="{page.anchor("modules", directory)}"><div class="module-body">'
                   f'<p class="module-loc">{escaped(directory)}</p><h3>{escaped(directory)}</h3><p class="what">'
                   + escaped(", ".join(f"{status.lower()} {Path(path).name}" for status, path in files)) + "</p></div></div>"
                   for directory, files in page.modules().items()) or listing([], "", "")


def key_files(page: Page) -> str:
    files = sorted(declared_file_entries(page.texts["plan"]), key=lambda entry: entry[0] != "MODIFIED")
    return listing([f'<li><span class="path">{escaped(path)}</span><span class="desc">{status.capitalize()} file</span></li>'
                    for status, path in files], '<div class="panel"><ul class="key-files">', "</ul></div>")


REGIONS: dict[str, Callable[[Page], str]] = {
    "document-title": lambda page: f"<title>{escaped(page.kind)} — {escaped(page.feature)} {escaped(page.name)}</title>",
    "feature-header": header, "plan-stats": plan_stats, "phases": phases, "task-inventory": task_inventory,
    "data-flow": lambda page: ('<figure class="flow"><figcaption>'
                               + page.prose("data-flow", lead(section(page.texts["plan"], "Summary"), 1))
                               + "</figcaption></figure>"),
    "mockups": lambda page: page.prose("mockups", lead(section(page.texts["design"], "Interface"))
                                       or "The planning files record no interface sketch."),
    "risk-register": risk_register,
    "tldr": lambda page: '<div class="tldr">' + page.prose("tldr", lead(section(page.texts["spec"], "User Story"))) + "</div>",
    "goals": goals, "non-goals": non_goals, "acceptance-criteria": acceptance, "clarification-faq": faq,
    "approaches": approaches, "recommendation": recommendation,
    "module-summary": lambda page: page.prose("module-summary", lead(section(page.texts["plan"], "Summary"), 1),
                                              "summary"),
    "module-graph": module_graph, "modules": modules, "key-files": key_files,
}


def narrative_input(inputs: dict[str, Any]) -> dict[str, str]:
    value = inputs.get("narrative", {})
    if not isinstance(value, dict) or not all(isinstance(prose, str) and prose.strip() and len(prose) <= NARRATIVE_LIMIT
                                              for prose in value.values()):
        raise ValueError(f"narrative must map prose slots to plain text of 1 to {NARRATIVE_LIMIT} characters")
    return {slot: " ".join(prose.split()) for slot, prose in value.items()}


def render(page: Page, entry_id: str) -> str:
    """Fill every region of the shipped template; any region without a builder is an error."""
    template = trusted_bytes(artifact_selection.GALLERY / "templates" / f"{entry_id}.html", artifact_selection.GALLERY)
    if template is None:
        raise ValueError("the shipped template is unreadable")
    source = template.decode("utf-8")
    kind = re.search(r"<title>([^<]*?) —", source)
    page.kind = kind[1] if kind else page.kind
    page.guidance = {slot: " ".join(fills.split()) for slot, fills in SLOT.findall(source)}
    missing = {name for name, _ in artifact_publication.REGION.findall(source)} - set(REGIONS)
    if missing:
        raise ValueError(f"the runner has no filler for template regions: {', '.join(sorted(missing))}")
    filled = artifact_publication.REGION.sub(
        lambda match: f"<!-- FILL:{match[1]}:START -->\n{REGIONS[match[1]](page)}\n<!-- FILL:{match[1]}:END -->", source)
    if set(page.narrative) - set(page.slots):
        raise ValueError("narrative names a prose slot this page does not have")
    return filled


def run_artifact_fill_helper(entry: Any, request: Any) -> dict[str, Any]:
    root = resolve_repo_root(request.inputs)
    if isinstance(root, dict):
        return response("input_error", request_id=request.request_id, diagnostics=[root])
    inputs = request.inputs
    try:
        if set(inputs) - INPUTS:
            raise ValueError("fill-artifact-page received unknown inputs")
        entry_id = require_text(inputs.get("entry_id"), "entry_id")
        selection = {field: inputs[field] for field in artifact_publication.SELECTION_INPUTS if field in inputs}
        if entry_id not in artifact_selection.select_artifact_pages(selection, root)["selected_pages"]:
            raise ValueError("entry_id is not a page the runner selected for these planning inputs")
        texts = {key: artifact_selection.planning_text(inputs, field, root, required=required)
                 for key, (field, required) in PLANNING.items()}
        title = re.search(r"^#\s+[^:\n]*:\s*(.+)$", texts["spec"], re.MULTILINE)
        feature = Path(inputs["plan_file"]).parent.name
        page = Page(feature, plain(title[1]) if title else feature, texts, narrative_input(inputs))
        content = render(page, entry_id)
    except artifact_selection.INPUT_ERRORS as error:
        return response("input_error", request_id=request.request_id, diagnostics=[diagnostic(
            "artifact_fill_invalid", str(error),
            remediation_summary="Keep the page already published, or report it as a gap; the pull request still opens.",
            remediation_actions=["Correct the planning inputs or the narrative text.", "Retry the fill."],
        )])
    published = artifact_publication.run_artifact_publication_helper(entry, dataclasses.replace(
        request, inputs={**selection, "entry_id": entry_id, "content": content}))
    if published["data"]:
        published["data"]["narrative_slots"] = [{"slot": slot, "guidance": page.guidance.get(slot, ""),
                                                 "fallback": fallback} for slot, fallback in page.slots.items()]
    return published
