#!/usr/bin/env python3
"""Layer-4 validation for the fill regions a gallery template ships.

`speckit-pro/artifact-gallery/manifest.json` says which templates exist and
`test-artifact-gallery.py` holds everything about the artifact itself. This
module holds one thing neither of those can see: the interface between a shipped
template and the authoring agent that fills it. The agent reads the template's
own inventory comment to learn what it must fill; nothing else tells it. The
checks below are what keep that inventory true.

**Every check function takes the gallery root as a parameter**, for the reason
the gallery scanner records at length: a check that reads ``GALLERY_ROOT`` for
itself can only ever run against the source tree. That mattered acutely while
this module landed, when the tree shipped no template at all and every
per-template check would have passed by vacuity; it still matters now that
templates ship, because any entry a later slice has not yet flipped still reads
``planned``. Taking the root as an argument is what lets the fixture cases
exercise the same functions against synthetic galleries built in a temporary
directory, where every template they describe exists.

**The R1-R7 per-template checks are gated on the catalog's ``status``, never on
file presence.** The contract binds the two in both directions — a file exists if and
only if its entry reads ``shipped`` — so ``status`` is the sufficient and cheaper
signal, and the gallery scanner already owns the direction this one relies on.
Keying on file presence instead would pass in the one state the contract calls a
failure: an artifact present without its flip. A ``shipped`` entry whose file is
missing is therefore *reported* here rather than skipped.

**The universe of per-template checks is the templates the floor names**, not
every entry in the catalog. The floor and the list-slot literal are pinned from
the roadmap, which names those and no others; a later template flipping to
``shipped`` belongs to the specification that ships it, and that specification is
what adds its rows below. Binding it here ahead of that would hold it to a
contract its own design never read.

**Marker-shaped text inside a ``script`` element is not a marker.** Comments are
collected through ``html.parser``, which reads a script element's content as raw
character data and never emits ``handle_comment`` for anything inside one. A
template's own export routine builds text, and a routine that happened to embed
a marker in a string literal must not be able to declare a region the body does
not delimit. Reading markers as parsed comments closes that by construction
rather than by a rule someone has to remember.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import tomllib
import unittest
from collections import Counter
from collections.abc import Callable, Iterable
from html.parser import HTMLParser
from pathlib import Path
from typing import NamedTuple


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
GALLERY_ROOT = PLUGIN_ROOT / "artifact-gallery"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


MANIFEST_FILE = "manifest.json"
TEMPLATES_DIR = "templates"
PLANNED = "planned"
SHIPPED = "shipped"

CLAUDE_ARTIFACT_AUTHOR = PLUGIN_ROOT / "agents" / "artifact-author.md"
CODEX_ARTIFACT_AUTHOR = PLUGIN_ROOT / "codex-agents" / "artifact-author.toml"
CLAUDE_PHASE_EXECUTION = (
    PLUGIN_ROOT / "skills" / "speckit-autopilot" / "references" / "phase-execution.md"
)
CODEX_PHASE_EXECUTION = (
    PLUGIN_ROOT
    / "codex-skills"
    / "speckit-autopilot"
    / "references"
    / "phase-execution-codex.md"
)


class ArtifactAuthorPublishLastContractTests(unittest.TestCase):
    """The author must never expose unfinished sample pages at final paths."""

    REQUIRED_INSTRUCTIONS = (
        "finish one page before reading or writing the next template",
        "Never pre-copy raw templates to their final artifact paths",
        "replacement map whose keys equal the template's declared slot inventory exactly",
        ".artifact-author-<entry-id>.<nonce>.tmp",
        "atomically replace the final `.html`",
        "Never publish by writing directly to the final path",
        "`sample-notice`, `notice`, or `note`",
        "every declared `FILL` marker pair still appears exactly once and in order",
        "every marked region matches the replacement map",
    )

    REQUIRED_RECONCILIATION = (
        "Reconcile current-run ownership before trusting any artifact file",
        "only the IDs it reports as `generated`",
        "lacks a complete current-run `generated` outcome",
        "delete every sibling `.artifact-author-*.tmp` file",
        "re-read the artifact directory",
        "every remaining draft-stage final ID is owned",
        "no `.artifact-author-*.tmp` file remains",
        "STOP before staging, the boundary commit, push",
        "fail-open cannot safely preserve an unowned file",
        "After every verification-driven deletion, re-read that path",
        "Demoting the outcome remains fail-open only when the invalid file is verifiably gone",
        "a surviving invalid file is the same artifact-integrity failure",
    )

    REQUIRED_CODEX_WAIT_LIFECYCLE = (
        "Bounded describes each wait call, not the lifetime of the worker",
        "`wait_agent` timeout is one bounded mailbox poll",
        "not an artifact-generation deadline",
        "declares no aggregate wall-clock deadline or poll-count limit",
        "Never synthesize loop exhaustion from an improvised number of polls or elapsed-time cutoff",
        "never interrupt the worker for crossing one",
        "A running worker whose latest bounded poll timed out is explicitly not in this set",
    )

    def test_claude_and_codex_agents_publish_only_finished_pages(self) -> None:
        claude_instructions = CLAUDE_ARTIFACT_AUTHOR.read_text(encoding="utf-8")
        codex_instructions = tomllib.loads(
            CODEX_ARTIFACT_AUTHOR.read_text(encoding="utf-8")
        )["developer_instructions"]

        for runtime, instructions in (
            ("Claude", claude_instructions),
            ("Codex", codex_instructions),
        ):
            with self.subTest(runtime=runtime):
                normalized = " ".join(instructions.split())
                for required in self.REQUIRED_INSTRUCTIONS:
                    self.assertIn(required, normalized)

    def test_orchestrators_remove_every_artifact_not_owned_by_this_run(self) -> None:
        for runtime, path in (
            ("Claude", CLAUDE_PHASE_EXECUTION),
            ("Codex", CODEX_PHASE_EXECUTION),
        ):
            instructions = path.read_text(encoding="utf-8")
            with self.subTest(runtime=runtime):
                normalized = " ".join(instructions.split())
                for required in self.REQUIRED_RECONCILIATION:
                    self.assertIn(required, normalized)

    def test_codex_orchestrator_does_not_turn_poll_timeouts_into_artifact_gaps(self) -> None:
        instructions = CODEX_PHASE_EXECUTION.read_text(encoding="utf-8")
        normalized = " ".join(instructions.split())

        for required in self.REQUIRED_CODEX_WAIT_LIFECYCLE:
            self.assertIn(required, normalized)


# ---------------------------------------------------------------------------
# The two pinned literals
# ---------------------------------------------------------------------------

# Both are held here and neither is read back out of a template. A set derived
# from the file under validation asserts only that the file equals itself.

# The floor traces to the roadmap's scope for the template sets that have shipped,
# and to nothing else, so a reader can tell why each entry is there. It is a **floor,
# not an equality**: a template may carry more slots than the roadmap names, and
# the both-ways agreement of R2 and R3 is what binds the remainder.
READ_ONLY_PORT_FLOOR: dict[str, tuple[str, ...]] = {
    "design-system": ("feature-header", "color", "typography", "spacing", "shape", "components"),
    "animation-prototype": (
        "feature-header",
        "completion-stage",
        "easing-controls",
        "keyframes",
        "css-snippet",
    ),
    "interaction-prototype": ("feature-header", "views", "interaction-notes", "open-questions"),
    "svg-illustrations": ("feature-header", "illustrations", "palette-rules"),
}

DECISION_PORT_FLOOR: dict[str, tuple[str, ...]] = {
    "visual-designs": ("feature-header", "design-brief", "background-toggle", "directions"),
    "component-variants": ("feature-header", "variant-controls", "variants", "snippet-preview"),
}

FLOOR: dict[str, tuple[str, ...]] = {
    "implementation-plan": (
        "document-title",
        "phases",
        "data-flow",
        "mockups",
        "risk-register",
        "task-inventory",
    ),
    "spec-explainer": (
        "document-title",
        "tldr",
        "goals",
        "non-goals",
        "acceptance-criteria",
        "clarification-faq",
    ),
    "code-approaches": ("document-title", "approaches"),
    "module-map": ("document-title", "module-graph"),
    "pr-writeup": ("motivation", "before-after", "file-by-file", "implementation-notes"),
    "annotated-diff": ("hunks",),
    "flowchart": ("flow-diagram",),
    "slide-deck": ("deck-title", "slides", "speaker-notes"),
    "concept-explainer": ("concept-title", "principles", "worked-example", "simulation-scenarios"),
    "status-report": ("summary", "landed", "in-flight", "blocked", "next-actions"),
    "incident-report": ("summary", "timeline", "impact", "root-cause", "follow-ups"),
    "triage-board": ("triage-items", "column-labels"),
    "feature-flags": ("flags", "environment-notes"),
    "prompt-tuner": ("prompt-variants", "evaluation-notes"),
    **READ_ONLY_PORT_FLOOR,
    **DECISION_PORT_FLOOR,
}

# The slots whose items an objection or a selection attaches to, and which
# therefore need their items individually addressable. ``modules`` is here and
# **not** in the floor above, which is the one row that looks inconsistent and is
# not: floor membership would prove only that a region of that name exists, never
# that its items are addressable, so the floor cannot verify this requirement even
# in principle. It gets R5 instead. Keeping the floor sourced from one document is
# also what keeps that literal auditable.
LIST_SLOTS: dict[str, tuple[str, ...]] = {
    "implementation-plan": ("phases",),
    "code-approaches": ("approaches",),
    "module-map": ("modules",),
    "pr-writeup": ("file-by-file",),
    "annotated-diff": ("hunks",),
    "flowchart": ("nodes",),
    "slide-deck": ("slides",),
    "concept-explainer": ("simulation-scenarios",),
    "status-report": ("landed", "in-flight", "blocked", "next-actions"),
    "incident-report": ("timeline", "follow-ups"),
    "triage-board": ("triage-items",),
    "feature-flags": ("flags",),
    "prompt-tuner": ("prompt-variants",),
    "interaction-prototype": ("views",),
    "visual-designs": ("directions",),
    "component-variants": ("variants",),
}

# One anchored item shows nothing about how a repeated list renders. Most slots
# need two; reorderable views retain three under their approved compaction floor.
DEFAULT_LIST_SLOT_ITEM_MINIMUM = 2
LIST_SLOT_ITEM_MINIMUMS: dict[tuple[str, str], int] = {
    ("interaction-prototype", "views"): 3,
}


def _list_slot_item_minimum(identifier: str, slot: str) -> int:
    return LIST_SLOT_ITEM_MINIMUMS.get((identifier, slot), DEFAULT_LIST_SLOT_ITEM_MINIMUM)


# ---------------------------------------------------------------------------
# The grammar the contract fixes
# ---------------------------------------------------------------------------

# Filename-safe kebab-case, the same character rules the catalog applies to its
# identifiers. Everything the contract bans falls out of it: a path separator, a
# parent-directory segment, a dot, whitespace, and a leading, trailing, or
# repeated hyphen all fail to match.
KEBAB = r"[a-z0-9]+(?:-[a-z0-9]+)*"
_KEBAB_RE = re.compile(KEBAB)

# The slot part is deliberately permissive — anything up to the next colon — so a
# malformed name is *collected* and then reported by name, rather than read as no
# marker at all and reported as a region that simply does not exist.
_MARKER_RE = re.compile(r"\s*FILL:(?P<slot>[^:\s]+):(?P<boundary>START|END)\s*")

START = "START"
END = "END"

SLOT_LABEL = "Slot:"
FILLS_LABEL = "Fills:"
SOURCE_LABEL = "Source:"
INVENTORY_LABELS: tuple[str, ...] = (SLOT_LABEL, FILLS_LABEL, SOURCE_LABEL)

# Closed vocabulary. A slot drawing on two names both, separated by a comma.
# Most members are files under the feature directory. ``git-diff`` is not one: it
# names the change's own diff, so a reader does not go looking for a file of that
# name.
SOURCE_ARTIFACTS: tuple[str, ...] = (
    "spec.md",
    "plan.md",
    "tasks.md",
    "research.md",
    "design-concept.md",
    "implementation-notes.md",
    "git-diff",
)

# The attribution header's own labels and literals, mirrored from the gallery
# scanner's group G, which owns the header itself. They are pinned again here
# rather than imported because that module's filename is not an importable
# identifier, and reaching it through ``importlib`` would couple two Layer 4
# modules for eight short strings. R4 uses them in one direction only — the
# inventory must carry **none** of them — so drift here can make R4 stricter or
# laxer about what an inventory may say, and can never change what a header must
# contain.
REPOSITORY_LABEL = "Upstream repository:"
UPSTREAM_FILE_LABEL = "Upstream file:"
LICENSE_LABEL = "License:"
LICENSE_TEXT_LABEL = "License text:"
DERIVATIVE_LABEL = "Modified derivative:"
UPSTREAM_REPOSITORY = "anthropics/html-effectiveness"
UPSTREAM_COPYRIGHT = "Copyright (c) 2026 Anthropic PBC"
UPSTREAM_LICENSE_REFERENCE = "UPSTREAM-NOTICE.md"

# The licence-text reference is the eighth literal the contract names and the
# one most easily left out, because it is a bare filename rather than a labelled
# field. It belongs here for the same reason as the rest: an inventory mentioning
# it would be read as the attribution header, and the artifact would then fail
# its provenance check for a reason naming the wrong region of the file.
ATTRIBUTION_MARKERS: tuple[str, ...] = (
    REPOSITORY_LABEL,
    UPSTREAM_FILE_LABEL,
    LICENSE_LABEL,
    LICENSE_TEXT_LABEL,
    DERIVATIVE_LABEL,
    UPSTREAM_REPOSITORY,
    UPSTREAM_COPYRIGHT,
    UPSTREAM_LICENSE_REFERENCE,
)

# Void elements take no end tag, so one is never pushed onto the region's tag
# stack. Pushing one would reparent everything after it, and every element
# following an ``<img>`` inside a list region would read as nested rather than as
# an item of that region — which is exactly the position R5 asks about.
VOID_ELEMENTS: frozenset[str] = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)


# ---------------------------------------------------------------------------
# The parser
# ---------------------------------------------------------------------------


class _RegionElement(NamedTuple):
    """One element opened at a fill region's own top level."""

    tag: str
    identifier: str | None


class _FillRegionCollector(HTMLParser):
    """Comments, marker pairs, and region-top-level elements, in one parse.

    ``HTMLParser`` delivers comments and start tags through the same instance in
    document order, so one subclass serves both needs the checks have:
    ``handle_comment`` toggles which slot is currently open and
    ``handle_starttag`` records the elements opened inside it.

    ``_stack`` is the region's depth counter, holding tag names rather than a
    bare integer. An element sits at the region's own top level exactly when the
    stack is empty. Holding the names is what makes a mismatched end tag
    harmless: ``<div><span></div>`` pops both, where a counter would decrement
    once and leave every later element in the region reading as nested.

    Regions are flat by contract — no pair may enclose another — and a nested
    ``START`` is therefore not a state this parser has to represent. It resolves
    one anyway rather than leaving the behaviour undefined: the inner region
    becomes the open one, and the outer keeps only the elements it had already
    collected.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.comments: list[str] = []
        self.markers: list[tuple[str, str]] = []
        self.regions: dict[str, list[_RegionElement]] = {}
        self.identifiers: list[str] = []
        self.unbalanced: dict[str, str] = {}
        self._open: str | None = None
        self._stack: list[str] = []

    def handle_comment(self, data: str) -> None:
        self.comments.append(data)
        match = _MARKER_RE.fullmatch(data)
        if match is None:
            return
        slot, boundary = match.group("slot"), match.group("boundary")
        self.markers.append((slot, boundary))
        if boundary == START:
            self._open = slot
            self._stack = []
            self.regions.setdefault(slot, [])
        elif self._open == slot:
            # Anything still open here was opened inside the region and closes
            # outside it, so the pair does not delimit a whole subtree. R7 reads
            # this; the depth counter it walks over the markers alone cannot see
            # it, because the markers themselves are perfectly paired.
            #
            # ``html.parser`` performs no implicit closing, so a region that
            # omitted an optional end tag — ``</li>``, ``</p>``, ``</td>`` —
            # would read as one leaving an element open. Every gallery template
            # writes its end tags, and the failure is loud rather than silent, so
            # the stricter reading is the one worth holding.
            if self._stack:
                self.unbalanced.setdefault(slot, self._stack[0])
            self._open = None
            self._stack = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record(tag, attrs)
        if self._open is not None and tag not in VOID_ELEMENTS:
            self._stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # A self-closing tag opens and closes at once, so it is recorded and
        # never pushed.
        self._record(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if self._open is None:
            return
        if tag in self._stack:
            while self._stack and self._stack.pop() != tag:
                continue
        elif tag not in VOID_ELEMENTS:
            # The other direction of the same defect: this end tag closes an
            # element the region never opened, so the element began outside the
            # START marker and ends inside the pair. Recorded rather than
            # ignored, because a fill that replaces the region deletes this end
            # tag and leaves its start tag unclosed.
            self.unbalanced.setdefault(self._open, tag)

    def _record(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.lower(): (value if value is not None else "") for name, value in attrs}
        identifier = attributes.get("id")
        if identifier is not None:
            self.identifiers.append(identifier)
        if self._open is not None and not self._stack:
            self.regions[self._open].append(_RegionElement(tag=tag, identifier=identifier))


class _Template(NamedTuple):
    """One shipped template and the single parse every check reads it through."""

    identifier: str
    relative: str
    collector: _FillRegionCollector


# ---------------------------------------------------------------------------
# Reading the gallery
# ---------------------------------------------------------------------------


def _read_or_none(path: Path) -> str | None:
    """A file's text with newline translation off, or ``None`` when it is not UTF-8.

    An unhandled decode error would propagate out of a check and stop the module
    before it reached the templates that are fine, so the condition is reported
    by the caller instead of raised.
    """
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            return handle.read()
    except UnicodeDecodeError:
        return None


def _catalog(gallery_root: Path) -> dict | None:
    """The parsed catalog, or ``None`` when it cannot be read.

    Absence is not a pass: R6 reports it. Every other check defers, so one
    unreadable catalog produces one message rather than six.
    """
    path = gallery_root / MANIFEST_FILE
    if not path.is_file():
        return None
    text = _read_or_none(path)
    if text is None:
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _entries(gallery_root: Path) -> list | None:
    catalog = _catalog(gallery_root)
    if catalog is None:
        return None
    entries = catalog.get("templates")
    return entries if isinstance(entries, list) else None


def _catalog_ids(gallery_root: Path) -> set[str] | None:
    entries = _entries(gallery_root)
    if entries is None:
        return None
    return {
        entry["id"] for entry in entries if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }


def _shipped_floor_ids(gallery_root: Path) -> list[str]:
    """The floor's templates whose catalog entry reads ``shipped``, in name order."""
    entries = _entries(gallery_root)
    if entries is None:
        return []
    return sorted(
        entry["id"]
        for entry in entries
        if isinstance(entry, dict) and entry.get("id") in FLOOR and entry.get("status") == SHIPPED
    )


def _template_path(identifier: str) -> str:
    return f"{TEMPLATES_DIR}/{identifier}.html"


def _templates(gallery_root: Path) -> tuple[list[_Template], list[str]]:
    """Every shipped floor template, parsed, plus the failures **R1 owns**.

    A shipped entry whose file is missing or undecodable is reported rather than
    skipped — skipping is the vacuity this module exists to avoid. R1 carries
    that message and R2 through R5 defer to it, so one defect produces one
    message rather than five.
    """
    parsed: list[_Template] = []
    failures: list[str] = []
    for identifier in _shipped_floor_ids(gallery_root):
        relative = _template_path(identifier)
        path = gallery_root / relative
        if not path.is_file():
            failures.append(
                f"{relative}: the catalog entry reads '{SHIPPED}' and no template exists at that path, "
                "so none of its fill regions can be checked"
            )
            continue
        text = _read_or_none(path)
        if text is None:
            failures.append(
                f"{relative}: is not decodable as UTF-8, so none of its fill regions can be read"
            )
            continue
        collector = _FillRegionCollector()
        collector.feed(text)
        collector.close()
        parsed.append(_Template(identifier=identifier, relative=relative, collector=collector))
    return parsed, failures


# ---------------------------------------------------------------------------
# Reading one template
# ---------------------------------------------------------------------------


def _boundaries(template: _Template) -> dict[str, list[str]]:
    """Each slot the body marks, with its boundaries in document order."""
    found: dict[str, list[str]] = {}
    for slot, boundary in template.collector.markers:
        found.setdefault(slot, []).append(boundary)
    return found


def _paired(template: _Template) -> set[str]:
    """The slots delimited by exactly one pair, start before end."""
    return {slot for slot, sequence in _boundaries(template).items() if sequence == [START, END]}


def _marked(template: _Template) -> set[str]:
    """Every slot the body names in a marker, however it is paired.

    R3 reads this rather than ``_paired``: an undocumented region is content the
    agent never replaces whether or not its markers are well formed, and pointing
    at the pairing instead would name R2's defect.
    """
    return {slot for slot, _ in template.collector.markers}


def _attribution_index(template: _Template) -> int | None:
    """Where the attribution header sits among the parser-recognized comments.

    The header is the **first** comment carrying any of its own labels or
    literals — the same rule the gallery scanner applies when it locates one.
    That is why R4 also forbids the inventory from carrying those literals: an
    inventory placed before a header and mentioning a licence would be read as
    the header, and the artifact would fail its provenance check for a reason
    naming the wrong region of the file.
    """
    for index, comment in enumerate(template.collector.comments):
        if any(marker in comment for marker in ATTRIBUTION_MARKERS):
            return index
    return None


def _inventory_comment(template: _Template) -> str | None:
    """The comment immediately after the attribution header, or ``None``."""
    index = _attribution_index(template)
    comments = template.collector.comments
    if index is None or index + 1 >= len(comments):
        return None
    return comments[index + 1]


def _inventory_lines(comment: str) -> list[tuple[int, str, list[str]]]:
    """Each non-blank inventory line: its number, its text, and its pipe-split fields."""
    return [
        (number, line.strip(), [field.strip() for field in line.split("|")])
        for number, line in enumerate(comment.splitlines(), start=1)
        if line.strip()
    ]


def _documented(template: _Template) -> list[str]:
    """The slot names the inventory carries, in document order.

    Read from the first field alone, so a line malformed further along still
    contributes its name. R2 and R3 then report the agreement defect and R4
    reports the format one, rather than one line's format defect suppressing both.
    """
    comment = _inventory_comment(template)
    if comment is None:
        return []
    names = []
    for _, _, fields in _inventory_lines(comment):
        if fields and fields[0].startswith(SLOT_LABEL):
            names.append(fields[0][len(SLOT_LABEL) :].strip())
    return names


# ---------------------------------------------------------------------------
# The checks
# ---------------------------------------------------------------------------


def check_r1(gallery_root: Path) -> list[str]:
    """R1 — every slot the roadmap names is present as a marker pair.

    A **subset** check. The floor is a floor: a template may carry more slots
    than the roadmap names, and R2 and R3 are what bind the remainder. It also
    carries the missing-template message, which is why it reports the failures
    ``_templates`` collects.
    """
    templates, failures = _templates(gallery_root)
    for template in templates:
        paired = _paired(template)
        failures.extend(
            f"{template.relative}: the roadmap names '{slot}' for this template and the body delimits no "
            f"matched FILL:{slot}:START … FILL:{slot}:END pair for it"
            for slot in FLOOR[template.identifier]
            if slot not in paired
        )
    return failures


def check_r2(gallery_root: Path) -> list[str]:
    """R2 — every documented slot has exactly one marker pair, start before end.

    One direction of the both-ways agreement. A documented slot with no region is
    a fill that silently does nothing, which is why this is kept apart from R3:
    a single check reporting both directions would name the wrong defect half the
    time.
    """
    templates, _ = _templates(gallery_root)
    failures: list[str] = []
    for template in templates:
        boundaries = _boundaries(template)
        for slot in _documented(template):
            sequence = boundaries.get(slot, [])
            if sequence == [START, END]:
                continue
            if not sequence:
                failures.append(
                    f"{template.relative}: the inventory names '{slot}' and the body delimits no region "
                    "for it, so filling that slot silently does nothing"
                )
            else:
                failures.append(
                    f"{template.relative}: the inventory names '{slot}' and its body markers read "
                    f"{sequence} rather than one {START} before one {END}, so the region it delimits is "
                    "not one an agent can replace"
                )
    return failures


def check_r3(gallery_root: Path) -> list[str]:
    """R3 — every marker pair in the body is named in the inventory.

    The other direction. An undocumented region is content the agent never
    replaces, left showing fictional sample data in a filled artifact — a defect
    R2 cannot see, and the reason these are two checks.
    """
    templates, _ = _templates(gallery_root)
    failures: list[str] = []
    for template in templates:
        undocumented = _marked(template).difference(_documented(template))
        failures.extend(
            f"{template.relative}: the body delimits '{slot}' and the inventory does not name it, so the "
            "agent never replaces that region and its sample content survives the fill"
            for slot in sorted(undocumented)
        )
    return failures


def check_r4(gallery_root: Path) -> list[str]:
    """R4 — the inventory's placement, format, and vocabulary.

    One parser-recognized comment immediately after the attribution header,
    carrying none of that header's own labels or literals; one slot per line
    reading ``Slot: … | Fills: … | Source: …`` in that order with no pipe inside
    a value; names filename-safe and unique within the template; every source
    drawn from the closed set.
    """
    templates, _ = _templates(gallery_root)
    failures: list[str] = []
    for template in templates:
        comment = _inventory_comment(template)
        if comment is None:
            failures.append(
                f"{template.relative}: no comment carries an attribution element, so the inventory has no "
                "header to be placed after and its placement cannot be checked"
                if _attribution_index(template) is None
                else f"{template.relative}: no comment follows the attribution header, so the template "
                "documents no slot inventory and an authoring agent has nothing to read"
            )
            continue
        failures.extend(
            f"{template.relative}: the inventory carries '{marker}', one of the attribution header's own "
            "labels or literals, so the gallery scanner would read the inventory as the header"
            for marker in ATTRIBUTION_MARKERS
            if marker in comment
        )
        lines = _inventory_lines(comment)
        if not lines:
            failures.append(
                f"{template.relative}: the comment after the attribution header names no slot, so it "
                "documents no inventory"
            )
            continue
        seen: set[str] = set()
        for number, line, fields in lines:
            failures.extend(_line_failures(template.relative, number, line, fields, seen))
    return failures


def _line_failures(relative: str, number: int, line: str, fields: list[str], seen: set[str]) -> list[str]:
    """One inventory line's format and vocabulary failures.

    ``seen`` accumulates the names already read from this template, which is what
    makes uniqueness a property of the template rather than of the line.
    """
    where = f"{relative}: inventory line {number}"
    if len(fields) != len(INVENTORY_LABELS):
        if len(fields) > len(INVENTORY_LABELS):
            return [
                f"{where}: reads {len(fields)} fields rather than three, so a value carries the pipe that "
                f"separates them: {line!r}"
            ]
        missing = ", ".join(label for label in INVENTORY_LABELS if label not in line)
        return [
            f"{where}: reads {len(fields)} field(s) rather than three, missing {missing}: {line!r}"
        ]

    failures: list[str] = []
    values: list[str] = []
    for label, field in zip(INVENTORY_LABELS, fields):
        if not field.startswith(label):
            return failures + [
                f"{where}: reads {field!r} where '{label} …' is required, so its three labels are not "
                f"{', '.join(INVENTORY_LABELS)} in that order: {line!r}"
            ]
        values.append(field[len(label) :].strip())

    name, fills, source = values
    if not _KEBAB_RE.fullmatch(name):
        failures.append(
            f"{where}: the slot name {name!r} is not filename-safe kebab-case, so it is not safe in a "
            "filename, in a document fragment, or in a comment marker"
        )
    elif name in seen:
        failures.append(
            f"{where}: the slot name {name!r} is already documented in this template, and a repeated name "
            "leaves an agent no way to tell which region a line describes"
        )
    else:
        seen.add(name)
    if not fills:
        failures.append(
            f"{where}: {FILLS_LABEL} carries no value, so the inventory names a slot without saying what "
            "fills it"
        )
    for artifact in (part.strip() for part in source.split(",")):
        if artifact not in SOURCE_ARTIFACTS:
            failures.append(
                f"{where}: {SOURCE_LABEL} names {artifact!r}, which is outside the closed set "
                f"{', '.join(SOURCE_ARTIFACTS)}"
            )
    return failures


def check_r5(gallery_root: Path) -> list[str]:
    """R5 — every repeated item in a list slot carries its stable anchor.

    **Its own assertion, not an entry in the floor.** Floor membership would
    prove only that a region of that name exists, never that its items are
    individually addressable, so the floor cannot verify this even in principle;
    and every floor entry traces to the roadmap, so an entry sourced from a
    different requirement would make that literal unauditable.

    The anchor is read at the region's **own top level**, which is where the
    contract puts each repeated item: a list's grouping element encloses the
    region rather than sitting inside it, because a fill replaces a whole region
    and the container has to survive one.
    """
    templates, _ = _templates(gallery_root)
    failures: list[str] = []
    for template in templates:
        counts = Counter(template.collector.identifiers)
        for slot in LIST_SLOTS.get(template.identifier, ()):
            minimum = _list_slot_item_minimum(template.identifier, slot)
            pattern = re.compile(rf"{re.escape(slot)}-{KEBAB}")
            elements = template.collector.regions.get(slot)
            if elements is None:
                failures.append(
                    f"{template.relative}: '{slot}' holds a repeated list and the body delimits no region "
                    "for it, so it carries no addressable item at all"
                )
                continue
            anchored: list[str] = []
            for element in elements:
                if element.identifier is None:
                    failures.append(
                        f"{template.relative}: '{slot}' holds a <{element.tag}> at the region's own top "
                        "level carrying no id, so an objection or a selection has nothing to attach to"
                    )
                elif not pattern.fullmatch(element.identifier):
                    failures.append(
                        f"{template.relative}: '{slot}' holds a <{element.tag}> whose id "
                        f"{element.identifier!r} is not '{slot}-<item-slug>' in kebab-case"
                    )
                else:
                    anchored.append(element.identifier)
            failures.extend(
                f"{template.relative}: '{slot}' carries the anchor {identifier!r} "
                f"{counts[identifier]} times in the document, and a fragment resolving to two items "
                "resolves to neither"
                for identifier in sorted({value for value in anchored if counts[value] > 1})
            )
            if len(anchored) < minimum:
                failures.append(
                    f"{template.relative}: '{slot}' holds {len(anchored)} anchored item(s), fewer than the "
                    f"{minimum} this repeated list needs to show a reader how a filled list renders"
                )
    return failures


def check_r6(gallery_root: Path) -> list[str]:
    """R6 — every template the floor names is one the catalog carries.

    Without it, renaming a catalog identifier would leave the floor naming a
    template that can never ship, and every per-template check above would go
    quietly vacuous rather than fail.
    """
    identifiers = _catalog_ids(gallery_root)
    if identifiers is None:
        return [
            f"{MANIFEST_FILE}: the catalog is missing or unreadable, so no template the floor names can be "
            "found and every per-template check below it is vacuous"
        ]
    return [
        f"{MANIFEST_FILE}: the floor names '{identifier}', which is not an identifier the catalog carries, "
        "so the floor names a template that can never ship"
        for identifier in sorted(set(FLOOR).difference(identifiers))
    ]


def check_r7(gallery_root: Path) -> list[str]:
    """R7 — regions are flat: no marker pair encloses another.

    Its own check because **no other one can see this defect**. A nested pair is
    still exactly one START and one END with START before END, so R2 accepts it,
    and its slot is still named in the inventory, so R3 accepts it too. Both
    directions of the agreement hold on a document that violates the contract.

    The harm is the one this whole convention exists to prevent, and it is
    silent. A fill replaces a whole region, so filling the outer slot deletes the
    inner one entirely — its content, its anchors, and its marker pair — while
    the inventory goes on naming it. The next fill of the inner slot then finds
    no region to replace and does nothing, and no check reports either event.

    Walked as a depth counter over the markers in document order rather than by
    comparing offsets, so an END arriving before its own START is reported as the
    disorder it is instead of reading as a negative-width region.

    **Flatness against the element tree as well as against the markers.** A pair
    can be well formed and still not delimit a whole subtree: put one boundary
    inside an element and the other outside it, and the region overlaps that
    element rather than nesting within it. Every other check accepts such a
    document — the markers read one START before one END, the slot is named in
    the inventory, and the depth counter never leaves zero — yet replacing the
    region deletes an unmatched tag and the fill emits malformed markup. Both
    orientations count, and the parser already knows about each: an element
    opened inside the region leaves the region's tag stack non-empty at its END,
    and one opened before the START arrives as an end tag the stack never held.
    """
    templates, _ = _templates(gallery_root)
    failures: list[str] = []
    for template in templates:
        failures.extend(
            f"{template.relative}: the region '{slot}' and a <{tag}> element overlap rather than nest — "
            "one boundary of the pair falls inside that element and the other falls outside it, so "
            "replacing the region deletes an unmatched tag and leaves the document malformed"
            for slot, tag in sorted(template.collector.unbalanced.items())
        )
        depth = 0
        open_slots: list[str] = []
        for slot, boundary in template.collector.markers:
            if boundary == START:
                if depth > 0:
                    failures.append(
                        f"{template.relative}: FILL:{slot}:START opens inside '{open_slots[-1]}', but regions "
                        "are flat — filling the enclosing slot would delete this one, its anchors, and its "
                        "own markers, while the inventory went on naming it"
                    )
                depth += 1
                open_slots.append(slot)
            else:
                if depth == 0:
                    failures.append(
                        f"{template.relative}: FILL:{slot}:END closes a region that is not open, so the "
                        "body's markers do not nest consistently"
                    )
                    continue
                depth -= 1
                open_slots.pop()
    return failures


def check_r8(gallery_root: Path) -> list[str]:
    """R8 — approved read-only floor targets are shipped and present.

    R1-R7 intentionally defer a planned entry. These four ports are no longer a
    future catalog universe: their implementation slice is active, so leaving
    them planned or fileless must keep this RED task non-vacuous.
    """
    entries = _entries(gallery_root)
    if entries is None:
        return []  # R6 owns an unreadable catalog

    failures: list[str] = []
    for identifier in READ_ONLY_PORT_FLOOR:
        matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("id") == identifier]
        if not matches:
            continue  # R6 owns a floor identifier absent from the catalog
        status = matches[0].get("status")
        if status != SHIPPED:
            failures.append(
                f"{MANIFEST_FILE}: read-only fill-region target '{identifier}' remains {status!r} rather "
                f"than '{SHIPPED}', so its floor is not active"
            )
        path = gallery_root / _template_path(identifier)
        if not path.is_file():
            failures.append(
                f"{_template_path(identifier)}: read-only fill-region target is missing, so its floor and "
                "list slots cannot be checked"
            )
    return failures


def check_r9(gallery_root: Path) -> list[str]:
    """R9 — approved decision-port floor targets are shipped and present.

    R1-R7 intentionally defer a planned entry. The two decision ports now have
    approved fill-region/list-slot floors, so leaving them planned or fileless
    must keep this RED task non-vacuous.
    """
    entries = _entries(gallery_root)
    if entries is None:
        return []  # R6 owns an unreadable catalog

    failures: list[str] = []
    for identifier in DECISION_PORT_FLOOR:
        matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("id") == identifier]
        if not matches:
            continue  # R6 owns a floor identifier absent from the catalog
        status = matches[0].get("status")
        if status != SHIPPED:
            failures.append(
                f"{MANIFEST_FILE}: decision-port fill-region target '{identifier}' remains {status!r} rather "
                f"than '{SHIPPED}', so its floor is not active"
            )
        path = gallery_root / _template_path(identifier)
        if not path.is_file():
            failures.append(
                f"{_template_path(identifier)}: decision-port fill-region target is missing, so its floor "
                "and list slots cannot be checked"
            )
    return failures


FILL_REGION_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("R1", check_r1),
    ("R2", check_r2),
    ("R3", check_r3),
    ("R4", check_r4),
    ("R5", check_r5),
    ("R6", check_r6),
    ("R7", check_r7),
    ("R8", check_r8),
    ("R9", check_r9),
)


# ---------------------------------------------------------------------------
# The real gallery
# ---------------------------------------------------------------------------


class FillRegionTests(unittest.TestCase):
    """Every check against the shipped gallery.

    R1-R7 bind from the moment a template's catalog entry flips. R8 and R9 close
    active slices by rejecting their targets while they remain planned or
    fileless.
    """

    def test_every_check_passes_against_the_shipped_gallery(self) -> None:
        for name, check in FILL_REGION_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])

    def test_each_floor_template_is_asserted_about_once_its_entry_reads_shipped(self) -> None:
        """Non-vacuity: the gate is the catalog's ``status``, and it is readable."""
        identifiers = _catalog_ids(GALLERY_ROOT)
        self.assertIsNotNone(identifiers, f"{MANIFEST_FILE} is unreadable, so no case here can bind")
        for identifier in sorted(FLOOR):
            with self.subTest(msg=identifier):
                self.assertIn(identifier, identifiers or set())

    def test_draft_feature_templates_fill_one_static_document_title_in_head(self) -> None:
        for identifier in (
            "implementation-plan",
            "spec-explainer",
            "code-approaches",
            "module-map",
        ):
            with self.subTest(msg=identifier):
                relative = _template_path(identifier)
                template = (GALLERY_ROOT / relative).read_text(encoding="utf-8")
                start = "<!-- FILL:document-title:START -->"
                end = "<!-- FILL:document-title:END -->"
                self.assertEqual(template.count(start), 1, f"{relative}: expected one title start marker")
                self.assertEqual(template.count(end), 1, f"{relative}: expected one title end marker")
                region = template.split(start, 1)[1].split(end, 1)[0]
                self.assertRegex(region, r"\A\s*<title>[^<]+</title>\s*\Z")
                self.assertLess(template.index("<head>"), template.index(start))
                self.assertLess(template.index(end), template.index("</head>"))

    def test_slide_deck_fill_inventory_template_exists(self) -> None:
        relative = _template_path("slide-deck")
        path = GALLERY_ROOT / relative
        self.assertTrue(path.is_file(), f"{relative}: missing slide-deck fill-inventory template")
        template = path.read_text(encoding="utf-8")
        for slot in FLOOR["slide-deck"]:
            with self.subTest(msg=slot):
                self.assertIn(
                    f"Slot: {slot} |",
                    template,
                    f"{relative}: missing {slot!r} fill-inventory slot",
                )

    def test_concept_explainer_fill_inventory_template_exists(self) -> None:
        self.assertTrue((path := GALLERY_ROOT / _template_path("concept-explainer")).is_file() and all(f"Slot: {slot} |" in path.read_text(encoding="utf-8") for slot in FLOOR["concept-explainer"]), f"{_template_path('concept-explainer')}: missing concept-explainer fill-inventory template")
    def test_status_report_fill_inventory_template_exists(self) -> None:
        self.assertTrue((path := GALLERY_ROOT / _template_path("status-report")).is_file() and all(f"Slot: {slot} |" in path.read_text(encoding="utf-8") for slot in FLOOR["status-report"]), f"{_template_path('status-report')}: missing status-report fill-inventory template")
    def test_incident_report_fill_inventory_template_exists(self) -> None:
        self.assertTrue((path := GALLERY_ROOT / _template_path("incident-report")).is_file() and all(f"Slot: {slot} |" in path.read_text(encoding="utf-8") for slot in FLOOR["incident-report"]), f"{_template_path('incident-report')}: missing incident-report fill-inventory template")
    def test_triage_board_fill_inventory_template_exists(self) -> None:
        self.assertTrue((path := GALLERY_ROOT / _template_path("triage-board")).is_file() and all(f"Slot: {slot} |" in path.read_text(encoding="utf-8") for slot in FLOOR["triage-board"]), f"{_template_path('triage-board')}: missing triage-board fill-inventory template")
    def test_feature_flags_fill_inventory_template_exists(self) -> None:
        self.assertTrue((path := GALLERY_ROOT / _template_path("feature-flags")).is_file() and all(f"Slot: {slot} |" in path.read_text(encoding="utf-8") for slot in FLOOR["feature-flags"]), f"{_template_path('feature-flags')}: missing feature-flags fill-inventory template")
    def test_prompt_tuner_fill_inventory_template_exists(self) -> None:
        self.assertTrue((path := GALLERY_ROOT / _template_path("prompt-tuner")).is_file() and all(f"Slot: {slot} |" in path.read_text(encoding="utf-8") for slot in FLOOR["prompt-tuner"]), f"{_template_path('prompt-tuner')}: missing prompt-tuner fill-inventory template")


# ---------------------------------------------------------------------------
# Fixture construction
# ---------------------------------------------------------------------------


def _attribution_header() -> str:
    """A conforming attribution header, built from the pinned literals."""
    return "\n".join(
        (
            f"  {REPOSITORY_LABEL} {UPSTREAM_REPOSITORY}",
            f"  {UPSTREAM_FILE_LABEL} 16-implementation-plan.html",
            f"  {LICENSE_LABEL} MIT",
            f"  {LICENSE_TEXT_LABEL} UPSTREAM-NOTICE.md",
            f"  {DERIVATIVE_LABEL} yes",
            f"  {UPSTREAM_COPYRIGHT}",
        )
    )


def _inventory_line(slot: str, *, source: str = "plan.md") -> str:
    return f"  {SLOT_LABEL} {slot} | {FILLS_LABEL} the sample feature's {slot} | {SOURCE_LABEL} {source}"


def _inventory(slots: Iterable[str]) -> str:
    return "\n".join(_inventory_line(slot) for slot in slots)


def _region(slot: str, body: str) -> str:
    return f"<!-- FILL:{slot}:START -->\n{body}\n<!-- FILL:{slot}:END -->"


def _prose_region(slot: str) -> str:
    return _region(slot, f"<p>Sample {slot} content awaiting a fill.</p>")


def _list_region(slot: str, slugs: Iterable[str | None]) -> str:
    """A list slot, with the grouping element **enclosing** the region.

    That placement is the contract's, not a fixture convenience. A fill replaces
    a whole region, so the list container has to sit outside the pair to survive
    one — which is exactly what puts each repeated item at the region's own top
    level, where R5 looks for its anchor.
    """
    items = "\n".join(
        f'  <li id="{slot}-{slug}">Sample item.</li>' if slug is not None else "  <li>Sample item.</li>"
        for slug in slugs
    )
    return f'<ul class="items">\n{_region(slot, items)}\n</ul>'


def _template_slots(identifier: str) -> tuple[str, ...]:
    """The slots a conforming fixture template carries: its floor plus its list slots."""
    return tuple(dict.fromkeys(FLOOR.get(identifier, ()) + LIST_SLOTS.get(identifier, ())))


def _document(header: str, inventory: str, body: str) -> str:
    """A template document: the attribution header, then the inventory, then the body."""
    return (
        "<!doctype html>\n"
        f"<!--\n{header}\n-->\n"
        f"<!--\n{inventory}\n-->\n"
        '<html lang="en">\n'
        '<head>\n<meta charset="utf-8">\n<title>Sample</title>\n</head>\n'
        f"<body>\n{body}\n</body>\n"
        "</html>\n"
    )


class FillRegionFixtureCase(unittest.TestCase):
    """A synthetic gallery in a temporary directory, shared by every check.

    Nothing here is written into the repository tree: a fixture template under
    ``speckit-pro/artifact-gallery/templates/`` would be an orphaned artifact the
    gallery scanner fails on, and it would be required in both shipped payloads.
    ``gallery_root`` always resolves to the temporary root rather than the source
    tree.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="artifact-fill-regions-")
        self.gallery = Path(self._tmp.name).resolve() / "artifact-gallery"
        self.gallery.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, relative: str, text: str) -> Path:
        path = self.gallery / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return path

    def assertReports(self, failures: list[str], *fragments: str) -> None:
        """One failure naming every fragment, so a message points at one defect."""
        self.assertTrue(failures, "expected a failure, got none")
        self.assertTrue(
            any(all(fragment in failure for fragment in fragments) for failure in failures),
            f"no failure named all of {fragments}: {failures}",
        )

    def write_catalog(self, *entries: dict[str, object]) -> Path:
        return self.write(
            MANIFEST_FILE,
            json.dumps(
                {"schema_version": "1.0", "signals": [], "export_kinds": [], "templates": list(entries)},
                indent=2,
            ),
        )

    def write_template(
        self,
        identifier: str,
        *,
        slots: tuple[str, ...] | None = None,
        documented: tuple[str, ...] | None = None,
        anchors: dict[str, tuple[str | None, ...]] | None = None,
        inventory: str | None = None,
        header: str | None = None,
        trailing: str = "",
    ) -> Path:
        """One template file.

        ``slots`` is what the body delimits and ``documented`` is what the
        inventory names; both default to the same conforming set, so a fixture
        perturbing one direction states only that perturbation.
        """
        carried = _template_slots(identifier) if slots is None else slots
        named = carried if documented is None else documented
        lists = LIST_SLOTS.get(identifier, ())
        chosen = {} if anchors is None else anchors
        body = "\n".join(
            _list_region(
                slot,
                chosen.get(
                    slot, ("schema-migration", "api-cutover", "rollback")[:_list_slot_item_minimum(identifier, slot)]
                ),
            )
            if slot in lists
            else _prose_region(slot)
            for slot in carried
        )
        return self.write(
            f"{TEMPLATES_DIR}/{identifier}.html",
            _document(
                _attribution_header() if header is None else header,
                _inventory(named) if inventory is None else inventory,
                body + trailing,
            ),
        )

    def build(self, identifier: str | None = None, **template: object) -> None:
        """A shipped catalog and its four templates, one of them perturbed.

        Called with no argument it builds a wholly conforming gallery, which is
        what the accept cases assert about: a fixture set that only ever proves
        detection cannot tell a working check from one that reports on everything.
        """
        self.write_catalog(*({"id": name, "status": SHIPPED} for name in sorted(FLOOR)))
        for name in sorted(FLOOR):
            if name == identifier:
                self.write_template(name, **template)  # type: ignore[arg-type]
            else:
                self.write_template(name)


# ---------------------------------------------------------------------------
# Fixture cases — each check detects its own defect, and accepts a clean gallery
# ---------------------------------------------------------------------------


class FillRegionFixtureTests(FillRegionFixtureCase):
    """Every check against a synthetic gallery carrying exactly one defect.

    These were written while the real gallery shipped no template at all, when a
    check exercised only against the real tree would have passed by vacuity and
    there would have been no way to make this module genuinely fail. Templates
    ship now, so the real-gallery cases do bind — but the fixtures stay the only
    place a *defect* is exercised, because the shipped templates are
    required to be correct and a suite that only ever sees correct input cannot
    tell a working check from one that reports nothing.
    """

    # -- the accept path --

    def test_every_check_accepts_a_conforming_gallery(self) -> None:
        self.build()

        for name, check in FILL_REGION_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(self.gallery), [])

    def test_per_template_checks_defer_while_every_entry_reads_planned(self) -> None:
        """R1-R7 defer planned entries; R8 and R9 keep active slices RED."""
        self.write_catalog(*({"id": name, "status": PLANNED} for name in sorted(FLOOR)))

        for name, check in FILL_REGION_CHECKS:
            if check in (check_r8, check_r9):
                continue
            with self.subTest(msg=name):
                self.assertEqual(check(self.gallery), [])
        self.assertReports(check_r8(self.gallery), "design-system", PLANNED)
        self.assertReports(check_r9(self.gallery), "visual-designs", PLANNED)

    # -- R1 --

    def test_r1_detects_a_floor_slot_with_no_region(self) -> None:
        carried = tuple(slot for slot in _template_slots("implementation-plan") if slot != "mockups")
        self.build("implementation-plan", slots=carried)

        self.assertReports(check_r1(self.gallery), "implementation-plan", "mockups")

    def test_r1_detects_a_missing_read_only_floor_region(self) -> None:
        carried = tuple(slot for slot in _template_slots("design-system") if slot != "shape")
        self.build("design-system", slots=carried)

        self.assertReports(check_r1(self.gallery), "design-system", "shape")

    def test_r1_detects_a_missing_decision_floor_region(self) -> None:
        carried = tuple(slot for slot in _template_slots("visual-designs") if slot != "background-toggle")
        self.build("visual-designs", slots=carried)

        self.assertReports(check_r1(self.gallery), "visual-designs", "background-toggle")

    def test_r1_accepts_a_template_carrying_more_slots_than_the_floor_names(self) -> None:
        """The floor is a floor, not an equality."""
        carried = _template_slots("implementation-plan") + ("plan-stats", "feature-header")
        self.build("implementation-plan", slots=carried)

        self.assertEqual(check_r1(self.gallery), [])

    def test_r1_detects_a_shipped_entry_with_no_template(self) -> None:
        self.write_catalog({"id": "module-map", "status": SHIPPED})

        self.assertReports(check_r1(self.gallery), "module-map", SHIPPED)

    # -- R2 and R3, the two directions --

    def test_r2_detects_an_inventory_slot_with_no_region(self) -> None:
        carried = tuple(slot for slot in _template_slots("implementation-plan") if slot != "data-flow")
        self.build("implementation-plan", slots=carried, documented=_template_slots("implementation-plan"))

        self.assertReports(check_r2(self.gallery), "implementation-plan", "data-flow")

    def test_r2_detects_a_region_whose_end_precedes_its_start(self) -> None:
        reversed_pair = "<!-- FILL:tldr:END -->\n<p>Sample.</p>\n<!-- FILL:tldr:START -->"
        carried = tuple(slot for slot in _template_slots("spec-explainer") if slot != "tldr")
        self.build(
            "spec-explainer",
            slots=carried,
            documented=_template_slots("spec-explainer"),
            trailing="\n" + reversed_pair,
        )

        self.assertReports(check_r2(self.gallery), "spec-explainer", "tldr")

    def test_r3_detects_a_region_the_inventory_does_not_name(self) -> None:
        carried = _template_slots("implementation-plan") + ("plan-stats",)
        self.build("implementation-plan", slots=carried, documented=_template_slots("implementation-plan"))

        self.assertReports(check_r3(self.gallery), "implementation-plan", "plan-stats")

    def test_r3_reads_a_marker_inside_a_script_as_no_slot_at_all(self) -> None:
        """Raw character data is not a comment, so it declares no region.

        The complement of the case above: the same marker text, in a position the
        parser never reports as a comment, must register as nothing. A template's
        export routine builds text, and one embedding a marker in a string literal
        must not be able to declare a region the body does not delimit.
        """
        script = '\n<script>\n  const marker = "<!-- FILL:plan-stats:START -->";\n</script>'
        self.build("implementation-plan", trailing=script)

        self.assertEqual(check_r3(self.gallery), [])

    # -- R4 --

    def test_r4_detects_a_malformed_inventory_line(self) -> None:
        malformed = f"  {SLOT_LABEL} phases | {SOURCE_LABEL} plan.md"
        self.build("implementation-plan", inventory=malformed)

        self.assertReports(check_r4(self.gallery), "implementation-plan", FILLS_LABEL)

    def test_r4_detects_a_pipe_inside_a_value(self) -> None:
        piped = f"  {SLOT_LABEL} phases | {FILLS_LABEL} the phases | and their order | {SOURCE_LABEL} plan.md"
        self.build("implementation-plan", inventory=piped)

        self.assertReports(check_r4(self.gallery), "implementation-plan", "pipe")

    def test_r4_detects_a_source_outside_the_closed_set(self) -> None:
        outside = f"  {SLOT_LABEL} phases | {FILLS_LABEL} the phases | {SOURCE_LABEL} roadmap.md"
        self.build("implementation-plan", inventory=outside)

        self.assertReports(check_r4(self.gallery), "implementation-plan", "roadmap.md")

    def test_r4_accepts_a_slot_drawing_on_two_sources(self) -> None:
        both = _inventory_line("risk-register", source="plan.md, research.md")
        self.build("implementation-plan", slots=("risk-register",), inventory=both)

        self.assertEqual(check_r4(self.gallery), [])

    def test_r4_detects_a_slot_name_that_is_not_kebab_case(self) -> None:
        self.build("implementation-plan", slots=("Task_Inventory",))

        self.assertReports(check_r4(self.gallery), "implementation-plan", "Task_Inventory")

    def test_r4_detects_a_repeated_slot_name(self) -> None:
        repeated = "\n".join((_inventory_line("phases"), _inventory_line("phases")))
        self.build("implementation-plan", inventory=repeated)

        self.assertReports(check_r4(self.gallery), "implementation-plan", "phases")

    def test_r4_detects_an_inventory_carrying_the_headers_own_literals(self) -> None:
        borrowed = f"  {LICENSE_LABEL} MIT\n" + _inventory(_template_slots("implementation-plan"))
        self.build("implementation-plan", inventory=borrowed)

        self.assertReports(check_r4(self.gallery), "implementation-plan", LICENSE_LABEL)

    def test_r4_detects_an_inventory_with_no_header_to_follow(self) -> None:
        """No header means no anchor for the placement rule, and R4 names that.

        The gallery scanner's attribution group owns the missing header itself.
        R4 reports only what it can see — that placement is unverifiable — rather
        than reporting the inventory malformed, which would name the wrong file
        region.
        """
        self.build("implementation-plan", header="  A comment carrying no attribution element.")

        self.assertReports(check_r4(self.gallery), "implementation-plan", "attribution element")

    # -- R5 --

    def test_r5_detects_a_repeated_item_with_no_anchor(self) -> None:
        self.build("implementation-plan", anchors={"phases": ("schema-migration", None)})

        self.assertReports(check_r5(self.gallery), "implementation-plan", "phases")

    def test_r5_detects_a_duplicated_anchor(self) -> None:
        self.build("implementation-plan", anchors={"phases": ("schema-migration", "schema-migration")})

        self.assertReports(check_r5(self.gallery), "implementation-plan", "phases-schema-migration")

    def test_r5_detects_a_single_item_list(self) -> None:
        self.build("module-map", anchors={"modules": ("router",)})

        self.assertReports(check_r5(self.gallery), "module-map", "modules")

    def test_r5_requires_three_anchored_interaction_views(self) -> None:
        self.build("interaction-prototype", anchors={"views": ("inbox", "today")})
        self.assertReports(check_r5(self.gallery), "interaction-prototype", "views", "2 anchored", "the 3")

        self.build("interaction-prototype", anchors={"views": ("inbox", "today", "upcoming")})
        self.assertEqual(check_r5(self.gallery), [])

    def test_r5_detects_an_anchor_that_does_not_open_with_its_slot(self) -> None:
        self.build("code-approaches", anchors={"approaches": ("worker-pool", None)})
        path = self.gallery / _template_path("code-approaches")
        self.write(
            _template_path("code-approaches"),
            path.read_text(encoding="utf-8").replace("<li>Sample item.</li>", '<li id="option-two">Sample item.</li>'),
        )

        self.assertReports(check_r5(self.gallery), "code-approaches", "option-two")

    def test_r5_detects_a_list_slot_with_no_region(self) -> None:
        """``modules`` is a list slot and not a floor entry, so only R5 sees this."""
        self.build("module-map", slots=("module-graph",), documented=("module-graph",))

        self.assertReports(check_r5(self.gallery), "module-map", "modules")

    def test_r5_detects_an_unanchored_read_only_list_item(self) -> None:
        self.build("interaction-prototype", anchors={"views": ("editor", None)})

        self.assertReports(check_r5(self.gallery), "interaction-prototype", "views")

    def test_r5_detects_an_unanchored_decision_direction_item(self) -> None:
        self.build("visual-designs", anchors={"directions": ("technical-depth", None)})

        self.assertReports(check_r5(self.gallery), "visual-designs", "directions")

    def test_r5_requires_two_anchored_component_variants(self) -> None:
        self.build("component-variants", anchors={"variants": ("default",)})

        self.assertReports(check_r5(self.gallery), "component-variants", "variants", "1 anchored", "the 2")

    # -- R6 --

    def test_r6_detects_a_floor_template_the_catalog_does_not_carry(self) -> None:
        self.write_catalog(
            *({"id": name, "status": PLANNED} for name in sorted(FLOOR) if name != "module-map")
        )

        self.assertReports(check_r6(self.gallery), "module-map")

    def test_r6_detects_an_unreadable_catalog(self) -> None:
        self.write(MANIFEST_FILE, "{ not valid json")

        self.assertReports(check_r6(self.gallery), MANIFEST_FILE)

    # -- R9 --

    def test_r9_reports_planned_and_missing_decision_ports(self) -> None:
        self.write_catalog(*({"id": name, "status": PLANNED} for name in sorted(FLOOR)))

        failures = check_r9(self.gallery)
        self.assertReports(failures, "visual-designs", PLANNED)
        self.assertReports(failures, "templates/visual-designs.html", "missing")
        self.assertReports(failures, "component-variants", PLANNED)
        self.assertReports(failures, "templates/component-variants.html", "missing")

    # -- R7 --

    def test_r7_detects_a_region_nested_inside_another(self) -> None:
        """The defect R2 and R3 both accept, which is why R7 exists.

        Asserted here as well as detected: the same document that fails R7 must
        pass R2 and R3, or the claim that no other check sees this is untrue and
        R7 is redundant.
        """
        self.build()
        path = self.gallery / _template_path("implementation-plan")
        text = path.read_text(encoding="utf-8")
        moved = _prose_region("risk-register")
        # Move a **documented** region inside another rather than inventing an
        # undocumented one: an undocumented region is R3's defect, and nesting it
        # would prove only that R3 works.
        nested = text.replace(moved + "\n", "", 1).replace(
            "<p>Sample mockups content awaiting a fill.</p>",
            "<p>Sample mockups content awaiting a fill.</p>\n" + moved,
            1,
        )
        self.assertNotEqual(nested, text, "fixture did not perturb the template")
        self.write(_template_path("implementation-plan"), nested)

        self.assertReports(check_r7(self.gallery), "implementation-plan", "risk-register")
        self.assertEqual(check_r2(self.gallery), [])
        self.assertEqual(check_r3(self.gallery), [])

    def test_r7_detects_a_pair_that_does_not_delimit_a_whole_subtree(self) -> None:
        """The second defect only R7 sees, and the marker walk alone cannot.

        The pair is well formed and well ordered, so the depth counter never
        leaves zero. What is wrong is the element tree: the ``<div>`` opens
        before the START marker and closes before the END one, so the region
        carries an end tag for an element it never opened and replacing the
        region leaves that ``<div>`` unclosed. Asserted alongside the other
        checks passing, for the same reason the nesting case is.
        """
        self.build()
        path = self.gallery / _template_path("implementation-plan")
        text = path.read_text(encoding="utf-8")
        crossing = text.replace(
            _prose_region("mockups"),
            '<div class="panel">\n'
            "<!-- FILL:mockups:START -->\n"
            "<p>Sample mockups content awaiting a fill.</p>\n"
            "</div>\n"
            "<!-- FILL:mockups:END -->",
            1,
        )
        self.assertNotEqual(crossing, text, "fixture did not perturb the template")
        self.write(_template_path("implementation-plan"), crossing)

        self.assertReports(check_r7(self.gallery), "implementation-plan", "mockups", "div")
        self.assertEqual(check_r2(self.gallery), [])
        self.assertEqual(check_r3(self.gallery), [])

    def test_r7_detects_an_end_marker_that_closes_nothing(self) -> None:
        self.build()
        path = self.gallery / _template_path("spec-explainer")
        stray = path.read_text(encoding="utf-8").replace(
            "<!-- FILL:tldr:START -->", "<!-- FILL:tldr:END -->\n<!-- FILL:tldr:START -->", 1
        )
        self.write(_template_path("spec-explainer"), stray)

        self.assertReports(check_r7(self.gallery), "spec-explainer", "tldr")


# Registered cases, in check order. A case not named here is a case the suite
# never runs.
CHECK_GROUPS: tuple[type[unittest.TestCase], ...] = (
    ArtifactAuthorPublishLastContractTests,
    FillRegionTests,
    FillRegionFixtureTests,
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for test_case in CHECK_GROUPS:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-artifact-fill-regions")


if __name__ == "__main__":
    raise SystemExit(main())
