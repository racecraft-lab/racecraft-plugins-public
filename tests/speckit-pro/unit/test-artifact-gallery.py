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
"""

from __future__ import annotations

import inspect
import json
import re
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GALLERY_ROOT = REPO_ROOT / "speckit-pro" / "artifact-gallery"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


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
    text = _read_exact(path)
    return _region(text, block) if _embeds(text, block) else None


def _canonical_pair_failures(gallery_root: Path, block: str) -> list[str]:
    name = CANONICAL_FILES[block]
    path = gallery_root / name
    if not path.is_file():
        return [f"{name}: block {block}: canonical file is missing, so no artifact can embed the block"]
    return _pair_failures(name, block, _read_exact(path))


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
        text = _read_exact(path)
        label = _label(gallery_root, path)
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
        text = _read_exact(path)
        label = _label(gallery_root, path)
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
    """A5 — every ``shipped`` entry's artifact embeds the brand block.

    Absence is never a pass: a shipped entry whose artifact is missing, or whose
    artifact carries no ``BRAND-KIT`` pair, fails here rather than falling
    through A4, which can only compare a region that exists.
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
            failures.append(
                f"{label}: block {BRAND_BLOCK}: shipped entry '{identifier}' has no artifact, "
                "so the block is embedded nowhere"
            )
        elif not _embeds(_read_exact(artifact), BRAND_BLOCK):
            failures.append(f"{label}: block {BRAND_BLOCK}: shipped entry '{identifier}' does not embed the block")
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
CATALOG_KEYS = ("schema_version", "signals", "templates")

# The eight documented keys, in FR-007's declaration order. Only the *set* is
# asserted: JSON object key order carries no meaning to any consumer, so a rule
# about ordering would be one no check ever applies.
ENTRY_KEYS = ("id", "category", "title", "when_to_use", "stage", "trigger", "source", "status")

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
    """B4 — each entry carries exactly the eight documented keys."""
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
                    f"expected an object carrying the eight documented keys, found {type(entry).__name__}",
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
                f"key '{key}': unexpected — an entry carries exactly the eight documented keys and no "
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
        """One conforming entry: the eight keys, in FR-007's declaration order."""
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
        }
        entry.update(overrides)
        return entry

    def catalog(self, **overrides: object) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "signals": list(FIXTURE_SIGNALS),
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

    def test_b1_accepts_exactly_the_three_top_level_keys(self) -> None:
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

    # -- B4: the eight keys --

    def test_b4_accepts_exactly_the_eight_documented_keys(self) -> None:
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

        self.assertReports(check_b4(self.gallery), self.position_of(FIXTURE_ENTRY_ID), "eight")

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
    validated shape. B4 reports the same key as missing from the eight; this row
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
    section = _section(_read_exact(path), SIGNAL_SECTION_HEADING)
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
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for test_case in CHECK_GROUPS:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test_case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-artifact-gallery")


if __name__ == "__main__":
    raise SystemExit(main())
