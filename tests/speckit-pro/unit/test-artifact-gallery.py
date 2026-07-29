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


# --- Group A fixtures ------------------------------------------------------

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


class MarkerBlockDriftFixtureTests(unittest.TestCase):
    """Group A against synthetic galleries built in a temporary directory.

    Nothing here is written into the repository tree: a fixture artifact under
    ``speckit-pro/artifact-gallery/templates/`` would be a D4 failure and would
    be required in both payloads by F1/F2.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="artifact-gallery-")
        self.gallery = Path(self._tmp.name).resolve() / "artifact-gallery"
        self.gallery.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # -- fixture builders --

    def write(self, relative: str, text: str) -> Path:
        path = self.gallery / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return path

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

    def assertReports(self, failures: list[str], *fragments: str) -> None:
        """One failure naming every fragment — FR-006's message obligation."""
        self.assertTrue(failures, "expected a failure, got none")
        self.assertTrue(
            any(all(fragment in failure for fragment in fragments) for failure in failures),
            f"no failure named all of {fragments}: {failures}",
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
