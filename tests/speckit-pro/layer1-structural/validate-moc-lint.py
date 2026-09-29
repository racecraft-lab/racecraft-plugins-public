#!/usr/bin/env python3
"""MOC lint: orphan and stale-index checks over SPEC-MOC.md markers.

The lint reads frontmatter through the runner's own spec-index helpers, so the
gate, the scalar quoting rules, and spec-ID normalization cannot drift from the
generator that writes the same files. Two CLI modes lint one directory:
``--moc-orphan DIR`` and ``--moc-stale DIR``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, TextIO
import io
import os
import re
import shutil
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for _import_root in (LIB_DIR, PLUGIN_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from speckit_pro_runner.helpers.read_only import (
    _spec_index_id_match,
    _spec_index_is_gated,
    _spec_index_scalar,
)
from test_result import run_counted

LABEL = "validate-moc-lint"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "moc"
LINK_RE = re.compile(r"\[[^\][]*\]\(([^()]*)\)")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")


def _read_text(path: Path) -> str | None:
    if not path.is_file() or not os.access(path, os.R_OK):
        return None
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def moc_is_gated(marker: Path) -> bool:
    text = _read_text(marker)
    return text is not None and _spec_index_is_gated(text)


def moc_field(marker: Path, field: str) -> str | None:
    """The frontmatter scalar as the generator reads it, or None when absent."""
    text = _read_text(marker)
    if text is None:
        return None
    found, value = _spec_index_scalar(text, field)
    return value if found else None


def moc_up_well_formed(marker: Path) -> bool:
    up = moc_field(marker, "up")
    if not up:
        return False
    if "[[" in up:
        return False
    before, sep, after = up.partition("](")
    if not sep or "[" not in before or ")" not in after:
        return False
    target = after.split(")", 1)[0].strip()
    if not target:
        return False
    if "://" in target or target.startswith(("//", "/", "#")):
        return False
    return ":" not in target.split("/", 1)[0]


def moc_specid_matches_dir(marker: Path, dir_name: str) -> bool:
    spec_id = moc_field(marker, "spec_id")
    return bool(spec_id) and _spec_index_id_match(spec_id, dir_name)


def _spec_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted((child for child in root.iterdir() if child.is_dir()), key=lambda path: path.as_posix())


def _lintable_markers(root: Path, mode: str, stderr: TextIO) -> list[Path]:
    """Gated, readable SPEC-MOC.md markers directly under ``root``'s spec dirs."""
    markers: list[Path] = []
    for spec_dir in _spec_dirs(root):
        if ".process" in spec_dir.parts:
            continue
        marker = spec_dir / "SPEC-MOC.md"
        if marker.exists() and not os.access(marker, os.R_OK):
            print(f"WARNING: {LABEL} {mode}: skipping unreadable marker {marker.as_posix()}", file=stderr)
            continue
        if moc_is_gated(marker):
            markers.append(marker)
    return markers


def scan_moc_orphans(root: Path, *, stdout: TextIO = sys.stdout, stderr: TextIO = sys.stderr) -> int:
    violation_count = 0
    for marker in _lintable_markers(root, "--moc-orphan", stderr):
        dir_name = marker.parent.name
        if not moc_up_well_formed(marker):
            print(f"VIOLATION [orphan]: {marker.as_posix()} \u2014 up: missing, empty, or ill-formed (not a well-formed relative [](...) link)", file=stdout)
            violation_count += 1
        if not moc_specid_matches_dir(marker, dir_name):
            print(f'VIOLATION [spec_id]: {marker.as_posix()} \u2014 spec_id absent/empty or does not namespace-match directory "{dir_name}"', file=stdout)
            violation_count += 1
    return violation_count


def stale_body(marker: Path) -> str:
    text = _read_text(marker)
    if text is None:
        return ""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return text
    closing = next((index for index, line in enumerate(lines[1:], start=1) if line == "---"), None)
    return "" if closing is None else "\n".join(lines[closing + 1 :])


def stale_link_targets(marker: Path) -> list[str]:
    if _read_text(marker) is None:
        return []
    targets = LINK_RE.findall(moc_field(marker, "up") or "")
    targets.extend(LINK_RE.findall(stale_body(marker)))
    return targets


def stale_is_relative_ref(target: str) -> bool:
    if not target or target.startswith(("#", "/", "mailto:")):
        return False
    return SCHEME_RE.match(target) is None


def stale_target_resolves(marker_dir: Path, target: str) -> bool:
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return False
    path = marker_dir / target
    return path.is_file() and os.access(path, os.R_OK)


def moc_links_resolve(marker: Path) -> bool:
    text = _read_text(marker)
    if text is None or "[[" in text:
        return False
    return all(
        stale_target_resolves(marker.parent, target)
        for target in stale_link_targets(marker)
        if stale_is_relative_ref(target)
    )


def scan_stale_moc_links(root: Path, *, emit: bool = False) -> list[str]:
    violations: list[str] = []
    for marker in _lintable_markers(root, "--moc-stale", sys.stderr):
        if "[[" in (_read_text(marker) or ""):
            violations.append(f"VIOLATION [stale-index/wikilink]: {marker} \u2014 contains a [[wikilink]] (wikilinks are not allowed in a gated MOC)")
        for target in stale_link_targets(marker):
            if stale_is_relative_ref(target) and not stale_target_resolves(marker.parent, target):
                violations.append(f"VIOLATION [stale-index/link]: {marker} \u2014 relative link target does not resolve to a regular readable file: {target}")
    if emit:
        for violation in violations:
            print(violation)
    return violations


class ValidateMocOrphan(unittest.TestCase):
    UP_CASES = (
        ('valid relative up: passes', 'orphan-valid', True),
        ('missing up: is a violation', 'orphan-missing-up', False),
        ('empty up: is a violation', 'orphan-empty-up', False),
        ('wikilink up: is a violation (ill-formed for orphan)', 'orphan-wikilink-up', False),
        ('absolute-URL up: is a violation (not a relative target)', 'orphan-absolute-url-up', False),
        ('root-absolute up: is a violation (not a relative target)', 'orphan-root-absolute-up', False),
        ('protocol-relative up: is a violation (not a relative target)', 'orphan-protocol-relative-up', False),
        ('anchor-only up: is a violation (not a relative target)', 'orphan-anchor-only-up', False),
        ('root-absolute up: with a LEADING SPACE is still a violation (trimmed)', 'orphan-leading-space-up', False),
        ('schemed up: (mailto:/tel:) is a violation (not a relative target)', 'orphan-scheme-up', False),
    )
    GATE_CASES = (
        ('no structureVersion -> SKIP (not gated)', 'gate-no-version', False),
        ('structureVersion 0 (< 1) -> SKIP', 'gate-version-zero', False),
        ('quoted "1" -> SKIP (non-bare-integer)', 'gate-version-quoted', False),
        ('decimal 1.0 -> SKIP (non-bare-integer)', 'gate-version-decimal', False),
        ('non-numeric text -> SKIP (non-bare-integer)', 'gate-version-text', False),
        ('no --- fence -> SKIP (unparseable frontmatter)', 'gate-no-fence', False),
        ('bare integer 1 WITH inline # comment -> GATED (guards inline-comment false-skip)', 'gate-version-commented', True),
    )
    SPEC_ID_CASES = (
        ('spec_id namespace-matches dir (prsg,002) -> PASS', 'prsg-002-something', True),
        ('spec_id namespace-matches dir (spec,006a) -> PASS', '006a-uat-skeleton', True),
        ('spec_id (spec,002) vs dir (prsg,002) collision -> VIOLATION', 'prsg-002-collision', False),
        ('spec_id 013a1 vs dir 013a near-miss -> VIOLATION', '013a', False),
        ('absent spec_id in gated marker -> VIOLATION', 'specid-absent', False),
        ('empty spec_id in gated marker -> VIOLATION', 'specid-empty', False),
    )

    def test_moc_orphan_lint(self) -> None:
        for message, case, expected in self.UP_CASES:
            with self.subTest(msg=message):
                self.assertEqual(expected, moc_up_well_formed(FIXTURES / 'orphan' / case / 'SPEC-MOC.md'))
        for message, case, expected in self.GATE_CASES:
            with self.subTest(msg=message):
                self.assertEqual(expected, moc_is_gated(FIXTURES / 'gate' / case / 'SPEC-MOC.md'))
        for message, case, expected in self.SPEC_ID_CASES:
            with self.subTest(msg=message):
                self.assertEqual(expected, moc_specid_matches_dir(FIXTURES / 'specid' / case / 'SPEC-MOC.md', case))

    def test_moc_orphan_scans(self) -> None:
        clean_scans = (
            ('non-MOC docs in a gated spec are not required to carry up: (scan clean)', FIXTURES / 'scan-clean'),
            ('no SPEC-MOC.md in dir -> SKIP (scan clean, no marker globbed)', FIXTURES / 'gate'),
            ('real-tree scan of docs/ai/specs/ is clean (legacy skipped)', REPO_ROOT / 'docs' / 'ai' / 'specs'),
            ('real-tree scan of specs/ is clean (active markers pass, legacy skipped)', REPO_ROOT / 'specs'),
        )
        for message, root in clean_scans:
            with self.subTest(msg=message):
                self.assertEqual(0, scan_moc_orphans(root, stdout=io.StringIO()))
        dogfood_marker = FIXTURES / 'specid' / 'prsg-002-something' / 'SPEC-MOC.md'
        with self.subTest(msg='Dogfood PRSG marker is version-gated (observable, not inferred from exit 0)'):
            self.assertTrue(moc_is_gated(dogfood_marker), 'fixture SPEC-MOC.md is NOT gated')
        with self.subTest(msg='Dogfood PRSG marker spec_id namespace-matches its directory'):
            self.assertTrue(moc_specid_matches_dir(dogfood_marker, 'prsg-002-something'))


class ValidateMocStaleIndex(unittest.TestCase):

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix='moc-stale-fixtures-')
        self.addCleanup(temporary.cleanup)
        self.fixtures = Path(temporary.name) / 'moc'
        shutil.copytree(FIXTURES, self.fixtures, symlinks=True)
        (self.fixtures / 'stale/stale-broken-symlink/broken-link.md').symlink_to('this-target-does-not-exist.md')

    def test_stale_index_lint(self) -> None:
        with self.subTest(msg='all relative targets resolve (up: + body link) -> PASS'):
            self.assertTrue(moc_links_resolve(self.fixtures / 'stale/stale-valid/SPEC-MOC.md'))
        with self.subTest(msg='an absent relative body-link target -> VIOLATION'):
            self.assertFalse(moc_links_resolve(self.fixtures / 'stale/stale-absent-link/SPEC-MOC.md'))
        with self.subTest(msg='a relative target that is a DIRECTORY (not a regular file) -> VIOLATION'):
            self.assertFalse(moc_links_resolve(self.fixtures / 'stale/stale-dir-target/SPEC-MOC.md'))
        with self.subTest(msg='a relative target that is a BROKEN SYMLINK -> VIOLATION (distinct from absent)'):
            self.assertFalse(self.fixtures.is_relative_to(REPO_ROOT))
            self.assertTrue((self.fixtures / 'stale/stale-broken-symlink/broken-link.md').is_symlink())
            self.assertFalse(moc_links_resolve(self.fixtures / 'stale/stale-broken-symlink/SPEC-MOC.md'))
        with self.subTest(msg='a [[wikilink]] anywhere in a gated MOC -> VIOLATION'):
            self.assertFalse(moc_links_resolve(self.fixtures / 'stale/stale-wikilink/SPEC-MOC.md'))
        with self.subTest(msg='a non-gated marker with a dangling link is skipped (exempt-before-content)'):
            self.assertEqual(0, len(scan_stale_moc_links(self.fixtures / 'stale-exempt')))
        with self.subTest(msg='scan of the stale fixture tree counts the negative cases as violations'):
            self.assertEqual(4, len(scan_stale_moc_links(self.fixtures / 'stale')))
        dogfood_marker = self.fixtures / 'stale/stale-valid/SPEC-MOC.md'
        with self.subTest(msg='Dogfood MOC marker is version-gated (observable, not inferred)'):
            self.assertTrue(moc_is_gated(dogfood_marker))
        with self.subTest(msg='Dogfood MOC marker links all resolve (up: and body links)'):
            self.assertTrue(moc_links_resolve(dogfood_marker))
        with self.subTest(msg='real-tree scan of docs/ai/specs/ is clean (legacy skipped)'):
            self.assertEqual(0, len(scan_stale_moc_links(REPO_ROOT / 'docs/ai/specs')))
        with self.subTest(msg='real-tree scan of specs/ is clean (active markers pass, legacy skipped)'):
            self.assertEqual(0, len(scan_stale_moc_links(REPO_ROOT / 'specs')))


class ValidateMocLintRunnerAgreement(unittest.TestCase):
    """The lint and the generator read one marker the same way.

    Each case is a marker on which the two former hand-copied readers disagreed
    with the runner: a superscript or Arabic-Indic digit passed ``str.isdigit``
    (one crashed ``int()``, the other gated the marker), and an unbalanced quote
    was half-stripped so a malformed ``spec_id`` matched its directory.
    """

    GATE_TOKENS = ("1", '"1"', "1.0", "²", "١", "1 # note", "01", "0", "")

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="moc-lint-agreement-"))
        self.addCleanup(shutil.rmtree, self.root)

    def marker(self, frontmatter: str, directory: str = "prsg-001-foo") -> Path:
        (self.root / directory).mkdir(exist_ok=True)
        return _write(self.root / directory / "SPEC-MOC.md", f"---\n{frontmatter}---\n\nbody\n")

    def test_gate_matches_the_runner_for_every_token(self) -> None:
        for token in self.GATE_TOKENS:
            with self.subTest(token=token):
                marker = self.marker(f"structureVersion: {token}\n")
                self.assertEqual(_spec_index_is_gated(marker.read_text(encoding="utf-8")), moc_is_gated(marker))

    def test_both_scans_skip_a_marker_the_runner_does_not_gate(self) -> None:
        for token in ("²", "١"):
            with self.subTest(token=token):
                self.marker(f'up: "[home](missing.md)"\nspec_id: "OTHER-9"\nstructureVersion: {token}\n')
                self.assertEqual(0, scan_moc_orphans(self.root, stdout=io.StringIO()))
                self.assertEqual([], scan_stale_moc_links(self.root))

    def test_a_gated_marker_is_still_linted_by_both_scans(self) -> None:
        self.marker('up: "[home](missing.md)"\nspec_id: "OTHER-9"\nstructureVersion: 1\n')
        self.assertEqual(1, scan_moc_orphans(self.root, stdout=io.StringIO()), "the mismatched spec_id is the one orphan violation")
        self.assertEqual(1, len(scan_stale_moc_links(self.root)))

    def test_spec_id_quotes_follow_the_runner(self) -> None:
        for raw in ('"PRSG-001', "PRSG-001'", '"PRSG-001"', "'PRSG-001'", "PRSG-001"):
            with self.subTest(raw=raw):
                marker = self.marker(f"spec_id: {raw}\nstructureVersion: 1\n")
                found, value = _spec_index_scalar(marker.read_text(encoding="utf-8"), "spec_id")
                self.assertTrue(found)
                self.assertEqual(_spec_index_id_match(value, "prsg-001-foo"), moc_specid_matches_dir(marker, "prsg-001-foo"))
        with self.subTest(msg="an unbalanced quote does not match its directory"):
            self.assertFalse(moc_specid_matches_dir(self.marker('spec_id: "PRSG-001\nstructureVersion: 1\n'), "prsg-001-foo"))


def _lint(mode: str, argv: list[str], scan: Callable[[Path], int | list[str]], case: type[unittest.TestCase]) -> int:
    """Lint the directory in ``argv[0]``, or with no argument run one lint's own tests.

    Exit 0 is clean, 1 is a content violation, 2 is an internal failure.
    """
    try:
        if argv:
            return 1 if scan(Path(argv[0])) else 0
        return run_counted(unittest.defaultTestLoader.loadTestsFromTestCase(case), label=LABEL, allow_live_specs=True)
    except Exception as exc:  # noqa: BLE001 - boundary: any failure becomes an explicit error
        print(f"ERROR: {LABEL} {mode}: internal failure ({exc.__class__.__name__}: {exc})", file=sys.stderr)
        return 2


def run_moc_orphan(argv: list[str]) -> int:
    return _lint("--moc-orphan", argv, lambda root: scan_moc_orphans(root), ValidateMocOrphan)


def run_moc_stale(argv: list[str]) -> int:
    return _lint("--moc-stale", argv, lambda root: scan_stale_moc_links(root, emit=True), ValidateMocStaleIndex)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "--moc-orphan":
        return run_moc_orphan(args[1:])
    if args and args[0] == "--moc-stale":
        return run_moc_stale(args[1:])
    if args:
        print(f"ERROR: unknown MOC lint mode: {args[0]}", file=sys.stderr)
        return 2
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label=LABEL, allow_live_specs=True)


if __name__ == "__main__":
    raise SystemExit(main())
