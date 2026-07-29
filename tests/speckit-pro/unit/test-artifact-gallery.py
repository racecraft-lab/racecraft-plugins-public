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
