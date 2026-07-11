#!/usr/bin/env python3
"""Version-gated orphan lint for MOC markers (port of validate-moc-orphan.sh).

XPLAT-010 count-parity port (T040, US2). Python 3.11+ standard library only.
No-arg mode runs the committed fixture self-tests plus real-tree scan with every
former ``assert_*``/``_pass``/``_fail`` execution mapped to one counted
``subTest`` unit. Explicit scan-root mode scans only that root and preserves the
predecessor's no-summary exit-code contract.

Baselines:
* ``tests/speckit-pro/parity/bash-to-python/validate-moc-orphan-baseline.txt``
  (TOTAL: 29)
* ``tests/speckit-pro/parity/bash-to-python/validate-moc-orphan-scan-root-baseline.txt``
  (TOTAL: 0)
"""

from __future__ import annotations

import io
import os
import re
import sys
import unittest
from pathlib import Path
from typing import TextIO

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "moc"
GATE_VERSION = 1


def _moc_fm_block(file: Path) -> list[str]:
    if not file.is_file() or not os.access(file, os.R_OK):
        return []
    try:
        lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    if not lines or lines[0] != "---":
        return []
    block: list[str] = []
    for line in lines[1:]:
        if line == "---":
            break
        block.append(line)
    return block


def _strip_frontmatter_value(value: str) -> str:
    value = value.lstrip()
    value = re.sub(r"\s+#.*$", "", value)
    value = value.rstrip()
    if value.startswith('"'):
        value = value[1:]
        if value.endswith('"'):
            value = value[:-1]
    elif value.startswith("'"):
        value = value[1:]
        if value.endswith("'"):
            value = value[:-1]
    return value


def moc_frontmatter_field(file: Path, field: str) -> str | None:
    prefix = re.compile(rf"^\s*{re.escape(field)}:")
    for line in _moc_fm_block(file):
        if prefix.match(line):
            return _strip_frontmatter_value(line.split(":", 1)[1])
    return None


def _raw_frontmatter_field(file: Path, field: str) -> str | None:
    prefix = re.compile(rf"^\s*{re.escape(field)}:")
    for line in _moc_fm_block(file):
        if prefix.match(line):
            raw = line.split(":", 1)[1]
            raw = raw.lstrip()
            raw = re.sub(r"\s+#.*$", "", raw)
            return raw.rstrip()
    return None


def moc_is_gated(file: Path) -> bool:
    version = moc_frontmatter_field(file, "structureVersion")
    if version is None or not re.fullmatch(r"[0-9]+", version):
        return False
    raw_token = _raw_frontmatter_field(file, "structureVersion")
    if raw_token is None or not re.fullmatch(r"[0-9]+", raw_token):
        return False
    return int(version) >= GATE_VERSION


def moc_normalize(value: str) -> tuple[str, str]:
    parts = value.lower().split("-")
    first = parts[0] if parts else ""
    if re.fullmatch(r"[a-z]+", first):
        namespace = first
        number_suffix = parts[1] if len(parts) > 1 else ""
    else:
        namespace = "spec"
        number_suffix = first
    return namespace, number_suffix


def moc_id_match(left: str, right: str) -> bool:
    return moc_normalize(left) == moc_normalize(right)


def moc_up_well_formed(file: Path) -> bool:
    up = moc_frontmatter_field(file, "up")
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
    if "://" in target or target.startswith("//") or target.startswith("/") or target.startswith("#"):
        return False

    before_slash = target.split("/", 1)[0]
    return ":" not in before_slash


def moc_specid_matches_dir(file: Path, dir_name: str) -> bool:
    spec_id = moc_frontmatter_field(file, "spec_id")
    return bool(spec_id) and moc_id_match(spec_id, dir_name)


def _iter_spec_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted((child for child in root.iterdir() if child.is_dir()), key=lambda path: path.name)


def scan_root(root: Path, *, stdout: TextIO = sys.stdout, stderr: TextIO = sys.stderr) -> int:
    violation_count = 0
    for spec_dir in _iter_spec_dirs(root):
        if ".process" in spec_dir.parts:
            continue
        marker = spec_dir / "SPEC-MOC.md"

        if marker.exists() and not os.access(marker, os.R_OK):
            print(f"WARNING: validate-moc-orphan.py: skipping unreadable marker {marker.as_posix()}", file=stderr)
            continue

        if not moc_is_gated(marker):
            continue

        dir_name = spec_dir.name
        marker_text = marker.as_posix()
        if not moc_up_well_formed(marker):
            print(
                "VIOLATION [orphan]: "
                f"{marker_text} — up: missing, empty, or ill-formed "
                "(not a well-formed relative [](...) link)",
                file=stdout,
            )
            violation_count += 1

        if not moc_specid_matches_dir(marker, dir_name):
            print(
                "VIOLATION [spec_id]: "
                f'{marker_text} — spec_id absent/empty or does not namespace-match directory "{dir_name}"',
                file=stdout,
            )
            violation_count += 1
    return violation_count


class ValidateMocOrphan(unittest.TestCase):
    def test_moc_orphan_lint(self) -> None:
        with self.subTest(msg="valid relative up: passes"):
            self.assertTrue(moc_up_well_formed(FIX / "orphan" / "orphan-valid" / "SPEC-MOC.md"))

        with self.subTest(msg="missing up: is a violation"):
            self.assertFalse(moc_up_well_formed(FIX / "orphan" / "orphan-missing-up" / "SPEC-MOC.md"))

        with self.subTest(msg="empty up: is a violation"):
            self.assertFalse(moc_up_well_formed(FIX / "orphan" / "orphan-empty-up" / "SPEC-MOC.md"))

        with self.subTest(msg="wikilink up: is a violation (ill-formed for orphan)"):
            self.assertFalse(moc_up_well_formed(FIX / "orphan" / "orphan-wikilink-up" / "SPEC-MOC.md"))

        with self.subTest(msg="absolute-URL up: is a violation (not a relative target)"):
            self.assertFalse(moc_up_well_formed(FIX / "orphan" / "orphan-absolute-url-up" / "SPEC-MOC.md"))

        with self.subTest(msg="root-absolute up: is a violation (not a relative target)"):
            self.assertFalse(moc_up_well_formed(FIX / "orphan" / "orphan-root-absolute-up" / "SPEC-MOC.md"))

        with self.subTest(msg="protocol-relative up: is a violation (not a relative target)"):
            self.assertFalse(moc_up_well_formed(FIX / "orphan" / "orphan-protocol-relative-up" / "SPEC-MOC.md"))

        with self.subTest(msg="anchor-only up: is a violation (not a relative target)"):
            self.assertFalse(moc_up_well_formed(FIX / "orphan" / "orphan-anchor-only-up" / "SPEC-MOC.md"))

        with self.subTest(msg="root-absolute up: with a LEADING SPACE is still a violation (trimmed)"):
            self.assertFalse(moc_up_well_formed(FIX / "orphan" / "orphan-leading-space-up" / "SPEC-MOC.md"))

        with self.subTest(msg="schemed up: (mailto:/tel:) is a violation (not a relative target)"):
            self.assertFalse(moc_up_well_formed(FIX / "orphan" / "orphan-scheme-up" / "SPEC-MOC.md"))

        with self.subTest(msg="non-MOC docs in a gated spec are not required to carry up: (scan clean)"):
            self.assertEqual(0, scan_root(FIX / "scan-clean", stdout=io.StringIO()))

        with self.subTest(msg="no structureVersion -> SKIP (not gated)"):
            self.assertFalse(moc_is_gated(FIX / "gate" / "gate-no-version" / "SPEC-MOC.md"))

        with self.subTest(msg="structureVersion 0 (< 1) -> SKIP"):
            self.assertFalse(moc_is_gated(FIX / "gate" / "gate-version-zero" / "SPEC-MOC.md"))

        with self.subTest(msg='quoted "1" -> SKIP (non-bare-integer)'):
            self.assertFalse(moc_is_gated(FIX / "gate" / "gate-version-quoted" / "SPEC-MOC.md"))

        with self.subTest(msg="decimal 1.0 -> SKIP (non-bare-integer)"):
            self.assertFalse(moc_is_gated(FIX / "gate" / "gate-version-decimal" / "SPEC-MOC.md"))

        with self.subTest(msg="non-numeric text -> SKIP (non-bare-integer)"):
            self.assertFalse(moc_is_gated(FIX / "gate" / "gate-version-text" / "SPEC-MOC.md"))

        with self.subTest(msg="no --- fence -> SKIP (unparseable frontmatter)"):
            self.assertFalse(moc_is_gated(FIX / "gate" / "gate-no-fence" / "SPEC-MOC.md"))

        with self.subTest(msg="no SPEC-MOC.md in dir -> SKIP (scan clean, no marker globbed)"):
            self.assertEqual(0, scan_root(FIX / "gate", stdout=io.StringIO()))

        with self.subTest(msg="bare integer 1 WITH inline # comment -> GATED (guards inline-comment false-skip)"):
            self.assertTrue(moc_is_gated(FIX / "gate" / "gate-version-commented" / "SPEC-MOC.md"))

        with self.subTest(msg="spec_id namespace-matches dir (prsg,002) -> PASS"):
            self.assertTrue(
                moc_specid_matches_dir(
                    FIX / "specid" / "prsg-002-something" / "SPEC-MOC.md",
                    "prsg-002-something",
                )
            )

        with self.subTest(msg="spec_id namespace-matches dir (spec,006a) -> PASS"):
            self.assertTrue(
                moc_specid_matches_dir(
                    FIX / "specid" / "006a-uat-skeleton" / "SPEC-MOC.md",
                    "006a-uat-skeleton",
                )
            )

        with self.subTest(msg="spec_id (spec,002) vs dir (prsg,002) collision -> VIOLATION"):
            self.assertFalse(
                moc_specid_matches_dir(
                    FIX / "specid" / "prsg-002-collision" / "SPEC-MOC.md",
                    "prsg-002-collision",
                )
            )

        with self.subTest(msg="spec_id 013a1 vs dir 013a near-miss -> VIOLATION"):
            self.assertFalse(moc_specid_matches_dir(FIX / "specid" / "013a" / "SPEC-MOC.md", "013a"))

        with self.subTest(msg="absent spec_id in gated marker -> VIOLATION"):
            self.assertFalse(
                moc_specid_matches_dir(FIX / "specid" / "specid-absent" / "SPEC-MOC.md", "specid-absent")
            )

        with self.subTest(msg="empty spec_id in gated marker -> VIOLATION"):
            self.assertFalse(
                moc_specid_matches_dir(FIX / "specid" / "specid-empty" / "SPEC-MOC.md", "specid-empty")
            )

        dogfood_marker = FIX / "specid" / "prsg-002-something" / "SPEC-MOC.md"
        with self.subTest(msg="Dogfood PRSG marker is version-gated (observable, not inferred from exit 0)"):
            self.assertTrue(moc_is_gated(dogfood_marker), "fixture SPEC-MOC.md is NOT gated")

        with self.subTest(msg="Dogfood PRSG marker spec_id namespace-matches its directory"):
            self.assertTrue(moc_specid_matches_dir(dogfood_marker, "prsg-002-something"))

        with self.subTest(msg="real-tree scan of docs/ai/specs/ is clean (legacy skipped)"):
            self.assertEqual(0, scan_root(REPO_ROOT / "docs" / "ai" / "specs", stdout=io.StringIO()))

        with self.subTest(msg="real-tree scan of specs/ is clean (active markers pass, legacy skipped)"):
            self.assertEqual(0, scan_root(REPO_ROOT / "specs", stdout=io.StringIO()))


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateMocOrphan)


def main(argv: list[str]) -> int:
    if len(argv) >= 1:
        try:
            violations = scan_root(Path(argv[0]))
        except Exception as exc:  # pragma: no cover - defensive parity with shell trap.
            print(f"ERROR: validate-moc-orphan.py: internal failure ({exc.__class__.__name__}: {exc})", file=sys.stderr)
            return 2
        return 1 if violations > 0 else 0
    return run_counted(build_suite(), label="validate-moc-orphan")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
