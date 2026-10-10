#!/usr/bin/env python3
"""Docs that cite a tests/speckit-pro/layerN-* path must cite one that exists."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted

CITED_PATH = re.compile(r"tests/speckit-pro/layer\d+-[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)*/?")


def tracked_files(repo_root: Path) -> list[str]:
    """Every path in the git index; raises when git cannot answer."""
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z"],
        capture_output=True,
        check=True,
    )
    return [name for name in proc.stdout.decode("utf-8").split("\0") if name]


def is_cited_doc(path: str) -> bool:
    return path.endswith("AGENTS.md") or (path.startswith("docs/adr/") and path.endswith(".md"))


def cited_paths(text: str) -> list[str]:
    """Layer paths named in ``text``, minus trailing sentence punctuation."""
    return [match.rstrip("./") for match in CITED_PATH.findall(text)]


def path_exists(cited: str, tracked: list[str]) -> bool:
    return cited in tracked or any(name.startswith(cited + "/") for name in tracked)


def collect_errors(repo_root: Path, tracked: list[str]) -> list[str]:
    errors: list[str] = []
    for doc in sorted(name for name in tracked if is_cited_doc(name)):
        doc_path = repo_root / doc
        if not doc_path.is_file():
            continue
        text = doc_path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            for cited in cited_paths(line):
                if not path_exists(cited, tracked):
                    errors.append(f"{doc}:{number} cites {cited}, which is not a tracked path")
    return errors


class ValidateDocTestLayerPaths(unittest.TestCase):

    def test_retired_layer_path_is_reported(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "adr").mkdir(parents=True)
            (root / "docs" / "adr" / "0001-x.md").write_text(
                "Run `tests/speckit-pro/layer7-integration/`.\n"
                "Also `tests/speckit-pro/layer6-integration/canary.json`.\n",
                encoding="utf-8",
            )
            tracked = ["docs/adr/0001-x.md", "tests/speckit-pro/layer6-integration/canary.json"]
            errors = collect_errors(root, tracked)
        self.assertEqual(
            errors,
            ["docs/adr/0001-x.md:1 cites tests/speckit-pro/layer7-integration, which is not a tracked path"],
        )

    def test_directory_and_file_citations_resolve(self) -> None:
        tracked = ["tests/speckit-pro/layer6-integration/a.json"]
        self.assertTrue(path_exists("tests/speckit-pro/layer6-integration", tracked))
        self.assertTrue(path_exists("tests/speckit-pro/layer6-integration/a.json", tracked))
        self.assertFalse(path_exists("tests/speckit-pro/layer6-integ", tracked))

    def test_trailing_punctuation_is_not_part_of_the_path(self) -> None:
        self.assertEqual(
            cited_paths("see tests/speckit-pro/layer1-structural/, and tests/speckit-pro/layer2-trigger."),
            ["tests/speckit-pro/layer1-structural", "tests/speckit-pro/layer2-trigger"],
        )

    def test_repository_docs_cite_only_existing_layer_paths(self) -> None:
        tracked = tracked_files(REPO_ROOT)
        self.assertTrue(any(is_cited_doc(name) for name in tracked), "no cited docs found")
        errors = collect_errors(REPO_ROOT, tracked)
        with self.subTest(msg="every cited layer path exists"):
            self.assertFalse(errors, "\n".join(errors))


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    return run_counted(suite, label="validate-doc-test-layer-paths")


if __name__ == "__main__":
    raise SystemExit(main())
