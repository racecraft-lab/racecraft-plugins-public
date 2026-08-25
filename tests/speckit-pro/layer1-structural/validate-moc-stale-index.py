#!/usr/bin/env python3
"""Version-gated stale-index lint for MOC markers (port of validate-moc-stale-index.sh).

XPLAT-010 count-parity port (T041, US2). Python 3.11+ standard library only.
Every former ``set_test``/``_pass``/``_fail`` execution maps to one counted
``subTest`` unit with the bash check name reproduced verbatim.

Baseline: ``tests/speckit-pro/parity/bash-to-python/validate-moc-stale-index-baseline.txt``
(TOTAL: 11).
"""

from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "moc"
LINK_RE = re.compile(r"\[[^\][]*\]\(([^()]*)\)")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")


def _read_text(path: Path) -> str | None:
    if not path.is_file() or not os.access(path, os.R_OK):
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _frontmatter_block(path: Path) -> list[str]:
    text = _read_text(path)
    if text is None:
        return []
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return []
    block: list[str] = []
    for line in lines[1:]:
        if line == "---":
            break
        block.append(line)
    return block


def _strip_inline_comment(value: str) -> str:
    return re.sub(r"\s+#.*$", "", value).strip()


def moc_frontmatter_field(path: Path, field: str) -> str | None:
    for line in _frontmatter_block(path):
        if re.match(rf"^\s*{re.escape(field)}:", line):
            value = line.split(":", 1)[1]
            value = _strip_inline_comment(value)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            return value
    return None


def moc_is_gated(marker: Path) -> bool:
    if not marker.is_file() or not os.access(marker, os.R_OK):
        return False
    version = moc_frontmatter_field(marker, "structureVersion")
    if version is None or not version.isdigit():
        return False

    raw_token: str | None = None
    for line in _frontmatter_block(marker):
        if re.match(r"^\s*structureVersion:", line):
            raw_token = _strip_inline_comment(line.split(":", 1)[1])
            break
    if raw_token is None or not raw_token.isdigit():
        return False
    return int(version) >= 1


def stale_body(marker: Path) -> str:
    text = _read_text(marker)
    if text is None:
        return ""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return text

    body: list[str] = []
    in_frontmatter = True
    for line in lines[1:]:
        if in_frontmatter and line == "---":
            in_frontmatter = False
            continue
        if in_frontmatter:
            continue
        body.append(line)
    return "\n".join(body)


def stale_link_targets(marker: Path) -> list[str]:
    if not marker.is_file() or not os.access(marker, os.R_OK):
        return []
    targets: list[str] = []
    up_value = moc_frontmatter_field(marker, "up") or ""
    targets.extend(LINK_RE.findall(up_value))
    targets.extend(LINK_RE.findall(stale_body(marker)))
    return targets


def stale_is_relative_ref(target: str) -> bool:
    if not target:
        return False
    if target.startswith("#"):
        return False
    if target.startswith("/"):
        return False
    if SCHEME_RE.match(target):
        return False
    if target.startswith("mailto:"):
        return False
    return True


def stale_target_resolves(marker_dir: Path, target: str) -> bool:
    target = target.split("#", 1)[0]
    target = target.split("?", 1)[0]
    if not target:
        return False
    path = marker_dir / target
    return path.is_file() and os.access(path, os.R_OK)


def moc_links_resolve(marker: Path) -> bool:
    text = _read_text(marker)
    if text is None:
        return False
    if "[[" in text:
        return False
    marker_dir = marker.parent
    for target in stale_link_targets(marker):
        if not stale_is_relative_ref(target):
            continue
        if not stale_target_resolves(marker_dir, target):
            return False
    return True


def scan_root(root: Path, *, emit: bool = False) -> list[str]:
    if not root.is_dir():
        return []

    violations: list[str] = []
    for spec_dir in sorted((path for path in root.iterdir() if path.is_dir()), key=lambda path: path.as_posix()):
        if spec_dir.name == ".process" or ".process" in spec_dir.parts:
            continue
        marker = spec_dir / "SPEC-MOC.md"

        if marker.exists() and not os.access(marker, os.R_OK):
            print(
                f"WARNING: validate-moc-stale-index.py: skipping unreadable marker {marker}",
                file=sys.stderr,
            )
            continue
        if not moc_is_gated(marker):
            continue

        text = _read_text(marker) or ""
        if "[[" in text:
            violations.append(
                f"VIOLATION [stale-index/wikilink]: {marker} — contains a [[wikilink]] "
                "(wikilinks are not allowed in a gated MOC)"
            )

        for target in stale_link_targets(marker):
            if not stale_is_relative_ref(target):
                continue
            if not stale_target_resolves(marker.parent, target):
                violations.append(
                    f"VIOLATION [stale-index/link]: {marker} — relative link target does not "
                    f"resolve to a regular readable file: {target}"
                )

    if emit:
        for violation in violations:
            print(violation)
    return violations


def _with_broken_symlink() -> None:
    broken_link = FIXTURES / "stale/stale-broken-symlink/broken-link.md"
    try:
        if broken_link.exists() or broken_link.is_symlink():
            broken_link.unlink()
        broken_link.symlink_to("this-target-does-not-exist.md")
    except (NotImplementedError, OSError):
        # Windows runners may not permit symlink creation; an absent target still
        # exercises the same non-resolving regular-file predicate.
        if broken_link.exists() or broken_link.is_symlink():
            broken_link.unlink(missing_ok=True)


def _cleanup_broken_symlink() -> None:
    broken_link = FIXTURES / "stale/stale-broken-symlink/broken-link.md"
    if broken_link.exists() or broken_link.is_symlink():
        broken_link.unlink()


class ValidateMocStaleIndex(unittest.TestCase):
    def test_stale_index_lint(self) -> None:
        with self.subTest(msg="all relative targets resolve (up: + body link) -> PASS"):
            self.assertTrue(moc_links_resolve(FIXTURES / "stale/stale-valid/SPEC-MOC.md"))

        with self.subTest(msg="an absent relative body-link target -> VIOLATION"):
            self.assertFalse(moc_links_resolve(FIXTURES / "stale/stale-absent-link/SPEC-MOC.md"))

        with self.subTest(msg="a relative target that is a DIRECTORY (not a regular file) -> VIOLATION"):
            self.assertFalse(moc_links_resolve(FIXTURES / "stale/stale-dir-target/SPEC-MOC.md"))

        with self.subTest(msg="a relative target that is a BROKEN SYMLINK -> VIOLATION (distinct from absent)"):
            self.assertFalse(moc_links_resolve(FIXTURES / "stale/stale-broken-symlink/SPEC-MOC.md"))

        with self.subTest(msg="a [[wikilink]] anywhere in a gated MOC -> VIOLATION"):
            self.assertFalse(moc_links_resolve(FIXTURES / "stale/stale-wikilink/SPEC-MOC.md"))

        with self.subTest(msg="a non-gated marker with a dangling link is skipped (exempt-before-content)"):
            self.assertEqual(0, len(scan_root(FIXTURES / "stale-exempt")))

        with self.subTest(msg="scan of the stale fixture tree counts the negative cases as violations"):
            self.assertEqual(4, len(scan_root(FIXTURES / "stale")))

        dogfood_marker = FIXTURES / "stale/stale-valid/SPEC-MOC.md"
        with self.subTest(msg="Dogfood MOC marker is version-gated (observable, not inferred)"):
            self.assertTrue(moc_is_gated(dogfood_marker))

        with self.subTest(msg="Dogfood MOC marker links all resolve (up: and body links)"):
            self.assertTrue(moc_links_resolve(dogfood_marker))

        with self.subTest(msg="real-tree scan of docs/ai/specs/ is clean (legacy skipped)"):
            self.assertEqual(0, len(scan_root(REPO_ROOT / "docs/ai/specs")))

        with self.subTest(msg="real-tree scan of specs/ is clean (active markers pass, legacy skipped)"):
            self.assertEqual(0, len(scan_root(REPO_ROOT / "specs")))


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateMocStaleIndex)


def main() -> int:
    if len(sys.argv) >= 2:
        try:
            violations = scan_root(Path(sys.argv[1]), emit=True)
        except Exception as exc:  # pragma: no cover - defensive CLI contract
            print(f"ERROR: validate-moc-stale-index.py: internal failure ({exc})", file=sys.stderr)
            return 2
        return 1 if violations else 0

    _with_broken_symlink()
    try:
        try:
            # Walking the live `specs/` tree is this validator's job, and it is
            # archive-safe: an absent feature folder scans clean.
            return run_counted(
                build_suite(),
                label="validate-moc-stale-index",
                allow_live_specs=True,
            )
        except Exception as exc:  # pragma: no cover - defensive CLI contract
            print(f"ERROR: validate-moc-stale-index.py: internal failure ({exc})", file=sys.stderr)
            return 2
    finally:
        _cleanup_broken_symlink()


if __name__ == "__main__":
    raise SystemExit(main())
