#!/usr/bin/env python3
"""Docs that cite a tests/speckit-pro/layerN-* path must cite one that exists."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted

CITED_PATH = re.compile(r"tests/speckit-pro/layer\d+-")
CITATION_TOKEN = re.compile(
    r"(?<!`)(?P<ticks>`+)(?!`)(?P<code>.*?)(?<!`)(?P=ticks)(?!`)"
    r"|\]\((?:<(?P<angle>[^>\n]*)>|(?P<link>[^\s)]*))\)"
    r"|(?P<bare>tests/speckit-pro/layer\d+-[^\s`]+)",
    re.DOTALL,
)


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


def citations(text: str) -> list[tuple[int, str]]:
    """Locate complete literal citations; only bare prose has punctuation."""
    result: list[tuple[int, str]] = []
    for token in CITATION_TOKEN.finditer(text):
        group = next(name for name in ("code", "angle", "link", "bare") if token[name] is not None)
        body = token[group]
        start = CITED_PATH.search(body)
        if start is None:
            continue
        cited = body[start.start():]
        if token["bare"] is not None:
            cited = cited.removesuffix(",")
            if not cited.endswith(".."):
                cited = cited.removesuffix(".")
        number = text.count("\n", 0, token.start(group) + start.start()) + 1
        result.append((number, cited))
    return result


def cited_paths(text: str) -> list[str]:
    """Layer paths named in ``text``, preserving literal filename bytes."""
    return [cited for _, cited in citations(text)]


def path_exists(cited: str, tracked: list[str]) -> bool:
    if cited.endswith("/"):
        return any(name.startswith(cited) for name in tracked)
    return cited in tracked or any(name.startswith(cited + "/") for name in tracked)


def collect_errors(repo_root: Path, tracked: list[str]) -> list[str]:
    errors: list[str] = []
    for doc in sorted(name for name in tracked if is_cited_doc(name)):
        doc_path = repo_root / doc
        if not doc_path.is_file():
            continue
        text = doc_path.read_text(encoding="utf-8")
        for number, cited in citations(text):
            if not path_exists(cited, tracked):
                errors.append(f"{doc}:{number} cites {cited}, which is not a tracked path")
    return errors


def citation_errors(text: str, tracked_paths: list[str]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "docs" / "adr").mkdir(parents=True)
        doc = "docs/adr/0001-x.md"
        (root / doc).write_text(text, encoding="utf-8")
        return collect_errors(root, [doc, *tracked_paths])


def assert_missing_citations(case: unittest.TestCase, paths: list[str], markup: str = "code") -> None:
    for cited in paths:
        with case.subTest(cited=cited, markup=markup):
            delimiter = "``" if "`" in cited else "`"
            rendered = {
                "code": f"{delimiter}{cited}{delimiter}",
                "link": f"[test](<{cited}>)",
                "plain_link": f"[test]({cited})",
                "bare": cited,
            }[markup]
            errors = citation_errors(f"Run {rendered}.\n", ["tests/speckit-pro/layer1-structural/exists.py"])
            case.assertEqual(errors, [f"docs/adr/0001-x.md:1 cites {cited}, which is not a tracked path"])


class LiteralCitationParsing(unittest.TestCase):

    def test_child_component_characters_cannot_pass_as_parent(self) -> None:
        assert_missing_citations(self, [f"tests/speckit-pro/layer1-structural/{char}missing.py" for char in ("+", "@", "é")])

    def test_basename_characters_cannot_pass_as_tracked_file(self) -> None:
        assert_missing_citations(self, [f"tests/speckit-pro/layer1-structural/exists.py{char}extra" for char in (" ", "+")])

    def test_other_legal_characters_never_truncate_literal_paths(self) -> None:
        characters = "!\"#$%&'()*+,;:<=>?@[\\]^`{|}~\t" + "中🙂\u00a0"
        bases = ("tests/speckit-pro/layer1-structural/", "tests/speckit-pro/layer1-structural/exists.py")
        assert_missing_citations(self, [f"{base}{char}extra" for char in characters for base in bases])

    def test_terminal_filename_characters_are_not_punctuation_in_code(self) -> None:
        suffixes = (" ", "\t", "\u00a0", "+", "@", "é", ",", ";", ":", "!", "?", ")", "]", ">")
        assert_missing_citations(self, [f"tests/speckit-pro/layer1-structural/exists.py{suffix}" for suffix in suffixes])

    def test_plain_links_and_bare_tokens_do_not_truncate_components(self) -> None:
        paths = [
            base + suffix
            for base in ("tests/speckit-pro/layer1-structural/", "tests/speckit-pro/layer1-structural/exists.py")
            for suffix in ("+extra", "@extra", "éextra", "$extra", "#extra", "[extra]")
        ]
        assert_missing_citations(self, paths, "plain_link")
        assert_missing_citations(self, paths, "bare")

    def test_multiline_code_span_cannot_pass_as_existing_prefix(self) -> None:
        assert_missing_citations(self, ["tests/speckit-pro/layer1-structural/exists.py\nextra"])

    def test_multiline_spans_report_the_citation_line(self) -> None:
        path = "tests/speckit-pro/layer1-structural/+missing.py"
        errors = citation_errors(f"First line.\n``example\n{path}``", ["tests/speckit-pro/layer1-structural/exists.py"])
        self.assertEqual(errors, [f"docs/adr/0001-x.md:3 cites {path}, which is not a tracked path"])

    def test_adjacent_spans_and_backtick_filename_keep_their_boundaries(self) -> None:
        first = "tests/speckit-pro/layer1-structural/exists.py+extra"
        second = "tests/speckit-pro/layer1-structural/`missing.py"
        self.assertEqual(cited_paths(f"`{first}` and ``{second}``"), [first, second])


class LiteralPathExistence(unittest.TestCase):

    def test_literal_trailing_dot_is_not_stripped(self) -> None:
        assert_missing_citations(self, ["tests/speckit-pro/layer1-structural/exists.py."])

    def test_regular_file_with_trailing_slash_is_not_a_directory(self) -> None:
        assert_missing_citations(self, ["tests/speckit-pro/layer1-structural/exists.py/"])

    def test_repeated_dots_and_slash_dot_forms_are_not_stripped(self) -> None:
        suffixes = ("..", "...", "/.", "/..", "/./", "/../", "./", "//", "//.")
        assert_missing_citations(self, [f"tests/speckit-pro/layer1-structural/exists.py{suffix}" for suffix in suffixes])

    def test_literal_directory_slash_remains_accepted(self) -> None:
        path = "tests/speckit-pro/layer1-structural/"
        self.assertEqual(cited_paths(f"`{path}`"), [path])
        self.assertTrue(path_exists(cited_paths(f"`{path}`")[0], [path + "exists.py"]))

    def test_sentence_final_dot_outside_code_remains_punctuation(self) -> None:
        path = "tests/speckit-pro/layer1-structural/exists.py"
        self.assertEqual(cited_paths(f"See {path}."), [path])
        self.assertEqual(cited_paths(f"See `{path}.`."), [path + "."])

    def test_link_destinations_preserve_literal_characters_and_suffixes(self) -> None:
        suffixes = ("+extra", " extra", ".", "/", "..", "/.")
        assert_missing_citations(self, [f"tests/speckit-pro/layer1-structural/exists.py{suffix}" for suffix in suffixes], "link")

    def test_existing_literal_names_are_checked_exactly(self) -> None:
        suffixes = ("+extra", "@extra", "éextra", " extra", ".", "..", ",", "\t", "\u00a0")
        for suffix in suffixes:
            path = f"tests/speckit-pro/layer1-structural/exists.py{suffix}"
            with self.subTest(path=path):
                self.assertEqual(citation_errors(f"See `{path}`.\n", [path]), [])
                self.assertEqual(citation_errors(f"See `{path}/`.\n", [path + "/child.py"]), [])


class ValidateDocTestLayerPaths(unittest.TestCase):

    def test_retired_layer_path_is_reported(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "adr").mkdir(parents=True)
            (root / "docs" / "adr" / "0001-x.md").write_text(
                "Run `tests/speckit-pro/layer7-integration/`.\n"
                "Also `tests/speckit-pro/layer6-integration/canary.json` and `tests/speckit-pro/layer6-integration/`.\n"
                "Prefix `tests/speckit-pro/layer6-integ/` is not a directory.\n",
                encoding="utf-8",
            )
            tracked = ["docs/adr/0001-x.md", "tests/speckit-pro/layer6-integration/canary.json"]
            errors = collect_errors(root, tracked)
        self.assertEqual(
            errors,
            [
                "docs/adr/0001-x.md:1 cites tests/speckit-pro/layer7-integration/, which is not a tracked path",
                "docs/adr/0001-x.md:3 cites tests/speckit-pro/layer6-integ/, which is not a tracked path",
            ],
        )

    def test_trailing_punctuation_is_not_part_of_the_path(self) -> None:
        self.assertEqual(
            cited_paths("see tests/speckit-pro/layer1-structural/, and tests/speckit-pro/layer2-trigger."),
            ["tests/speckit-pro/layer1-structural/", "tests/speckit-pro/layer2-trigger"],
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
