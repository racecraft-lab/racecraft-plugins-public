#!/usr/bin/env python3
"""Focused contracts for release-note extraction, sanitization, and validation."""

from __future__ import annotations

import ast
import functools
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
POLICY_FILE = REPO_ROOT / "scripts" / "release_note_policy.py"
SCRIPTS_DIR = str(POLICY_FILE.parent)
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
for import_path in (SCRIPTS_DIR, str(LIB_DIR)):
    if import_path not in sys.path:
        sys.path.insert(0, import_path)

import release_note_policy as POLICY  # noqa: E402
from test_result import run_counted  # noqa: E402


def top_level_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    return imports


def inventory_check(test):  # type: ignore[no-untyped-def]
    """Give a non-loop unittest method one stable parity-inventory name."""
    @functools.wraps(test)
    def wrapped(self):  # type: ignore[no-untyped-def]
        name = test.__name__.removeprefix("test_").replace("_", " ")
        with self.subTest(msg=name):
            test(self)

    return wrapped


class ReleaseNotePolicyTests(unittest.TestCase):
    @inventory_check
    def test_fence_extraction_is_anchored_exact_and_nesting_aware(self) -> None:
        nested = """> Context
> ````release-note
> First line
> ```
> Last line
> `````
"""
        self.assertEqual(POLICY.extract_release_note(nested), "First line\n```\nLast line")

        ambiguous = """```release-note
One
```

~~~release-note
Two
~~~
"""
        self.assertIsNone(POLICY.extract_release_note(ambiguous))
        self.assertIsNone(POLICY.extract_release_note("```release-note\n   \n```"))
        self.assertIsNone(POLICY.extract_release_note("````release-note\nShort close\n```"))
        self.assertIsNone(POLICY.extract_release_note("```release-note extra\nNo exact info string\n```"))
        self.assertIsNone(POLICY.extract_release_note("```release-note\nFour-space close\n    ```"))

        nested_list = """- ```release-note
  Nested list note.
  ```
"""
        self.assertEqual(POLICY.extract_release_note(nested_list), "Nested list note.")

    def test_fence_extraction_rejects_release_note_inside_any_outer_fence(self) -> None:
        bodies = (
            """````markdown
```release-note
This is example text, not a release note.
```
````
""",
            """~~~text
```release-note
This is still fenced example text.
```
~~~
""",
            """> ````markdown
> ```release-note
> Quoted fenced example text.
> ```
> ````
""",
        )
        for index, body in enumerate(bodies, start=1):
            with self.subTest(msg=f"outer fence case {index}"):
                self.assertIsNone(POLICY.extract_release_note(body))

    @inventory_check
    def test_sanitization_strips_html_images_and_neutralizes_structure(self) -> None:
        note = """<strong>Visible</strong> ![secret](https://example.test/leak.png)
- list item
* star item
# injected heading
[plain link](https://example.test) remains
"""
        sanitized = POLICY.sanitize_release_note(note)
        self.assertIn("Visible", sanitized)
        self.assertNotIn("<strong>", sanitized)
        self.assertNotIn("secret", sanitized)
        self.assertNotIn("leak.png", sanitized)
        self.assertIn("\\- list item", sanitized)
        self.assertIn("\\* star item", sanitized)
        self.assertIn("\\# injected heading", sanitized)
        self.assertIn("[plain link](https://example.test)", sanitized)

    @inventory_check
    def test_sanitization_enforces_the_inline_markdown_allowlist(self) -> None:
        note = """> quoted text
1. ordered dot
2) ordered parenthesis
+ plus list
```python
fenced code
```
~~~text
tilde fenced code
~~~
Use `inline code` here.
Setext title
===
Dash setext title
-
Second dash setext title
--
left | right
:--- | ---:
***
_ _ _
[script](javascript:alert(1))
[encoded](java&#x73;cript:alert(1))
[relative](/admin)
[safe](https://example.test/docs_(v2)?q=ok#read)
[also-safe](HTTP://EXAMPLE.TEST/path)
Keep *emphasis*, **strong emphasis**, _underscores_, and __strong underscores__.
"""

        sanitized = POLICY.sanitize_release_note(note)

        self.assertIn("\\> quoted text", sanitized)
        self.assertIn("1\\. ordered dot", sanitized)
        self.assertIn("2\\) ordered parenthesis", sanitized)
        self.assertIn("\\+ plus list", sanitized)
        self.assertIn("\\`\\`\\`python", sanitized)
        self.assertIn("\\~\\~\\~text", sanitized)
        self.assertIn("Use \\`inline code\\` here.", sanitized)
        self.assertIn("\\=\\=\\=", sanitized)
        self.assertIn("Dash setext title\n\\-", sanitized)
        self.assertIn("Second dash setext title\n\\-\\-", sanitized)
        self.assertIn("left \\| right", sanitized)
        self.assertIn(":--- \\| ---:", sanitized)
        self.assertIn("\\*\\*\\*", sanitized)
        self.assertIn("\\_ \\_ \\_", sanitized)
        self.assertNotIn("javascript:", sanitized.lower())
        self.assertNotIn("[relative](/admin)", sanitized)
        self.assertIn("script", sanitized)
        self.assertIn("encoded", sanitized)
        self.assertIn("relative", sanitized)
        self.assertIn("[safe](https://example.test/docs_(v2)?q=ok#read)", sanitized)
        self.assertIn("[also-safe](HTTP://EXAMPLE.TEST/path)", sanitized)
        self.assertIn(
            "Keep *emphasis*, **strong emphasis**, _underscores_, and __strong underscores__.",
            sanitized,
        )

    def test_sanitization_preserves_only_validated_http_https_inline_links(self) -> None:
        unsafe_destinations = (
            "javascript:alert(1)",
            "JaVaScRiPt:alert(1)",
            "data:text/html,unsafe",
            "vbscript:msgbox(1)",
            "mailto:release-notes",
            "/relative/path",
            "//example.test/protocol-relative",
            "#fragment",
            "https://",
            "https://example.test/contains space",
            "https:\\example.test\\backslash",
        )
        for destination in unsafe_destinations:
            with self.subTest(msg=f"reject inline link destination {destination}"):
                self.assertEqual(
                    POLICY.sanitize_release_note(f"[label]({destination})"),
                    "label",
                )

        for destination in (
            "http://example.test",
            "https://example.test/path_(v2)?q=release%20notes#read",
            "HTTPS://EXAMPLE.TEST/path",
        ):
            with self.subTest(msg=f"preserve inline link destination {destination}"):
                link = f"[label]({destination})"
                self.assertEqual(POLICY.sanitize_release_note(link), link)

    @inventory_check
    def test_sanitization_removes_complete_nested_image_destinations(self) -> None:
        note = "Before ![secret](https://example.test/chart_(draft_(2)).png) after"

        self.assertEqual(POLICY.sanitize_release_note(note), "Before  after")

    @inventory_check
    def test_sanitization_removes_images_with_nested_alt_brackets(self) -> None:
        note = "Before ![outer [inner]](https://example.test/pixel.png) after"

        self.assertEqual(POLICY.sanitize_release_note(note), "Before  after")

    @inventory_check
    def test_sanitization_neutralizes_unterminated_image_with_nested_alt_brackets(self) -> None:
        note = "Before ![outer [inner]](https://example.test/pixel.png after"

        self.assertEqual(
            POLICY.sanitize_release_note(note),
            "Before !\\[outer \\[inner\\]\\](https://example.test/pixel.png after",
        )

    @inventory_check
    def test_sanitization_neutralizes_unterminated_nested_image_and_strips_html(self) -> None:
        note = "<strong>Before</strong> ![broken](https://example.test/chart_(draft).png after"

        self.assertEqual(
            POLICY.sanitize_release_note(note),
            "Before !\\[broken\\](https://example.test/chart_(draft).png after",
        )

    @inventory_check
    def test_sanitization_entities_and_transform_order_cannot_recreate_markup(self) -> None:
        note = """<strong>Visible</strong>
&lt;img src=x onerror=alert(1)&gt;
!&#91;secret&#93;(https://example.test/entity.png)
!<span>[joined]</span>(https://example.test/joined.png)
&amp;#33;&amp;#91;nested&amp;#93;(https://example.test/nested.png)
"""

        sanitized = POLICY.sanitize_release_note(note)

        self.assertIn("Visible", sanitized)
        self.assertNotIn("<img", sanitized.lower())
        self.assertNotIn("![", sanitized)
        self.assertNotIn("secret", sanitized)
        self.assertNotIn("joined.png", sanitized)
        self.assertNotIn("nested.png", sanitized)

    @inventory_check
    def test_sanitization_caps_at_2000_characters_with_marker(self) -> None:
        sanitized = POLICY.sanitize_release_note("x" * 2100)
        self.assertEqual(len(sanitized), 2000)
        self.assertTrue(sanitized.endswith(POLICY.TRUNCATION_MARKER))

    @inventory_check
    def test_sanitized_empty_block_fails_validation(self) -> None:
        body = """```release-note
&lt;img src=x&gt; !&#91;tracking&#93;(https://example.test/pixel.png)
```
"""
        valid, reason = POLICY.validate_release_note(
            "feat: Add release notes",
            body,
            set(),
            draft=False,
        )
        self.assertFalse(valid)
        self.assertIn("sanitization", reason)

    @inventory_check
    def test_title_normalization_rejects_marker_only_conventional_subjects(self) -> None:
        title = "feat: (#123)"
        body = """```release-note
Valid consumer note.
```
"""

        self.assertEqual(
            POLICY.deprefix_title("feat(core): useful title (#321)"),
            "useful title",
        )
        self.assertEqual(POLICY.deprefix_title(title), "")
        valid, reason = POLICY.validate_release_note(title, body, set(), draft=False)
        self.assertFalse(valid)
        self.assertEqual(reason, "feat/fix pull request title is empty after normalization")

    @inventory_check
    def test_policy_dependencies_stay_stdlib_only(self) -> None:
        self.assertLessEqual(top_level_imports(POLICY_FILE), sys.stdlib_module_names)

    @inventory_check
    def test_suite_imports_only_the_policy_production_module(self) -> None:
        self.assertEqual(
            top_level_imports(Path(__file__))
            - sys.stdlib_module_names
            - {"test_result"},
            {"release_note_policy"},
        )


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ReleaseNotePolicyTests)


def main() -> int:
    return run_counted(build_suite(), label="test-release-note-policy")


if __name__ == "__main__":
    raise SystemExit(main())
