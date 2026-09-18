#!/usr/bin/env python3
"""Attribution and provenance contracts for extracted Quint references."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
REF_ROOT = (
    REPO_ROOT
    / "speckit-pro"
    / "skills"
    / "speckit-coach"
    / "references"
    / "quint"
)
GUIDE_ROOT = (
    REPO_ROOT
    / "speckit-pro"
    / "skills"
    / "speckit-coach"
    / "references"
)
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402

EXPECTED_COMMIT = "cc75369f741af7d490936f82002c2d28e3b3d78d"
EXPECTED_REPOSITORY = "quint-co/quint-llm-kit"
EXPECTED_AUTHOR = "Informal Systems Inc."
EXPECTED_PROJECT = "Quint LLM Kit"
VERBATIM_TREES = ("quint-lang", "quint-modeling")
DERIVED_FILE = "witness-and-trace.md"
ROOT_ARTEFACTS = {"README.md", "UPSTREAM-NOTICE.md", "provenance.json"}
UPSTREAM_PATHS = {
    name: f"quint-llm-kit-plugin/skills/{name}" for name in VERBATIM_TREES
}
# The plan extracts authoring references only. These upstream layers stay out:
# the Docker-native agentic pipeline, the MCP server install, the Rust
# model-based-testing agents, and the Go/Node LSP bridge.
UNADOPTED_NAMES = {
    "quint-execute-spec",
    "mcp-servers",
    "claudecode.dockerfile",
    "entrypoint.sh",
    "setup-mcp.sh",
    "quint_connect",
    "test_generation",
    "mbt-validator.md",
}
UNADOPTED_SUFFIXES = {".rs", ".dockerfile", ".sh", ".bash", ".ps1"}
# The plugin-bash-confinement zero-Bash guard blocks these tokens anywhere under
# speckit-pro/ and the generated payloads, so no extracted file may carry them.
ZERO_BASH_TOKENS = (re.compile(r"\bbash\b", re.IGNORECASE), re.compile(r"\.(?:sh|bash|zsh|ps1|bat|cmd)\b", re.IGNORECASE))

# Authoritative literal record of the mechanical normalization applied to the
# adapted upstream files. This test tree is outside the guard's scan roots, so the
# literal tokens live here rather than in the shipped metadata.
ADAPTATION_TOKEN_MAP = (
    ("```bash", "```sh"),  # code-fence info string
    ("test_witness.sh", "test_witness"),  # helper filename named in prose
)
ADAPTATION_TRANSFORM_KINDS = {
    "fence-info-string-normalized": ("```bash", "```sh"),
    "script-filename-extension-dropped": ("test_witness.sh", "test_witness"),
    "entry-document-renamed": ("SKILL.md", "OVERVIEW.md"),
}
EXPECTED_ADAPTED_FILE_COUNT = 8


def _manifest() -> dict:
    return json.loads((REF_ROOT / "provenance.json").read_text(encoding="utf-8"))


def _entry_by_name(manifest: dict, name: str) -> dict:
    return next(entry for entry in manifest["entries"] if entry["name"] == name)


def _relative_files(name: str) -> set[str]:
    return {
        path.relative_to(REF_ROOT).as_posix()
        for path in (REF_ROOT / name).rglob("*")
        if path.is_file()
    }


class QuintReferenceAttributionTests(unittest.TestCase):
    def test_notice_and_manifest_are_present(self) -> None:
        for name in ("UPSTREAM-NOTICE.md", "README.md", "provenance.json"):
            with self.subTest(artefact=name):
                self.assertTrue((REF_ROOT / name).is_file(), f"missing {name}")
        notice = (REF_ROOT / "UPSTREAM-NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("Copyright 2026 Informal Systems Inc.", notice)

    def test_notice_records_the_exact_upstream_facts(self) -> None:
        notice = (REF_ROOT / "UPSTREAM-NOTICE.md").read_text(encoding="utf-8")
        for fact in (EXPECTED_PROJECT, EXPECTED_AUTHOR, EXPECTED_REPOSITORY, EXPECTED_COMMIT):
            with self.subTest(fact=fact):
                self.assertIn(fact, notice)
        self.assertIn("Apache-2.0", notice)
        for name, upstream in UPSTREAM_PATHS.items():
            with self.subTest(upstream_path=upstream):
                self.assertIn(upstream, notice)

    def test_readme_names_author_repository_commit_and_license(self) -> None:
        readme = (REF_ROOT / "README.md").read_text(encoding="utf-8")
        for fact in (EXPECTED_AUTHOR, EXPECTED_REPOSITORY, EXPECTED_COMMIT, "Apache-2.0"):
            with self.subTest(fact=fact):
                self.assertIn(fact, readme)
        self.assertIn("UPSTREAM-NOTICE.md", readme)
        self.assertIn("verbatim", readme.lower())
        self.assertIn("adapted", readme.lower())

    def test_provenance_pins_the_expected_upstream(self) -> None:
        manifest = _manifest()
        self.assertEqual(manifest["upstream"]["repository"], EXPECTED_REPOSITORY)
        self.assertEqual(manifest["upstream"]["commit"], EXPECTED_COMMIT)
        self.assertEqual(manifest["upstream"]["author"], EXPECTED_AUTHOR)
        self.assertEqual(manifest["upstream"]["license"], "Apache-2.0")
        self.assertEqual(manifest["upstream"]["project"], EXPECTED_PROJECT)

    def test_adaptation_is_recorded_and_justified(self) -> None:
        manifest = _manifest()
        adaptation = manifest["adaptation"]
        self.assertIn("plugin-bash-confinement", adaptation["contract"])
        self.assertTrue(adaptation["reason"].strip())
        declared = {item["kind"] for item in adaptation["transform_kinds"]}
        self.assertEqual(declared, set(ADAPTATION_TRANSFORM_KINDS))
        self.assertIn("test-quint-reference-attribution.py", adaptation["exact_token_mapping_recorded_in"])
        seen = 0
        for entry in manifest["entries"]:
            for item in entry["files"]:
                for transform in item.get("transforms", []):
                    seen += 1
                    with self.subTest(path=item["path"], kind=transform["kind"]):
                        self.assertIn(transform["kind"], declared, "an adapted file uses an undeclared transform")
                        self.assertGreater(transform["occurrences"], 0)
        self.assertGreater(seen, 0, "no adapted file records its transform")

    def test_adapted_files_match_the_recorded_transform(self) -> None:
        manifest = _manifest()
        for entry in manifest["entries"]:
            for item in entry["files"]:
                if item["kind"] != "adapted":
                    continue
                path = REF_ROOT / item["path"]
                content = path.read_text(encoding="utf-8")
                for transform in item["transforms"]:
                    source, target = ADAPTATION_TRANSFORM_KINDS[transform["kind"]]
                    with self.subTest(path=item["path"], kind=transform["kind"]):
                        if transform["kind"] == "entry-document-renamed":
                            self.assertTrue(
                                item["path"].endswith(target),
                                "a renamed entry document must ship under its new name",
                            )
                            self.assertEqual(item.get("upstream_path", "").endswith(source), True)
                            continue
                        self.assertNotIn(source, content, "the normalized token is still present")
                        self.assertIn(target, content, "the normalized token is missing")
                        if transform["kind"] == "fence-info-string-normalized":
                            self.assertEqual(
                                transform["occurrences"],
                                content.count(target),
                                "recorded fence normalization count drifted",
                            )

    def test_every_extracted_file_carries_provenance_metadata(self) -> None:
        manifest = _manifest()
        recorded = {
            item["path"]
            for entry in manifest["entries"]
            for item in entry["files"]
        }
        on_disk = {
            path.relative_to(REF_ROOT).as_posix()
            for path in REF_ROOT.rglob("*")
            if path.is_file() and path.relative_to(REF_ROOT).as_posix() not in ROOT_ARTEFACTS
        }
        self.assertEqual(on_disk, recorded, "extracted files and provenance entries diverged")

    def test_extracted_trees_are_completely_provenanced(self) -> None:
        manifest = _manifest()
        for name in VERBATIM_TREES:
            with self.subTest(name=name):
                entry = _entry_by_name(manifest, name)
                self.assertIn(entry["kind"], {"verbatim", "adapted"})
                self.assertEqual(entry["upstream_path"], UPSTREAM_PATHS[name])
                self.assertEqual(
                    entry["local_path"],
                    f"speckit-pro/skills/speckit-coach/references/quint/{name}",
                )
                self.assertTrue((REPO_ROOT / entry["local_path"]).is_dir())
                listed = {item["path"] for item in entry["files"]}
                self.assertEqual(listed, _relative_files(name))
                adapted = [item for item in entry["files"] if item["kind"] == "adapted"]
                self.assertEqual(entry["kind"], "adapted" if adapted else "verbatim")
                self.assertEqual(entry.get("adapted_file_count"), len(adapted))
                self.assertEqual(
                    {item["kind"] for item in entry["files"]},
                    {"verbatim"} | ({"adapted"} if adapted else set()),
                    f"{name} records an unknown per-file kind",
                )
                for item in entry["files"]:
                    actual = hashlib.sha256((REF_ROOT / item["path"]).read_bytes()).hexdigest()
                    self.assertEqual(
                        actual,
                        item["sha256"],
                        f"{item['path']} changed without a provenance update",
                    )

    def test_verbatim_files_record_the_upstream_hash(self) -> None:
        manifest = _manifest()
        seen = 0
        for entry in manifest["entries"]:
            for item in entry["files"]:
                if item["kind"] != "verbatim":
                    continue
                seen += 1
                with self.subTest(path=item["path"]):
                    self.assertEqual(
                        item["sha256"],
                        item.get("upstream_sha256", item["sha256"]),
                        "a verbatim file must hash identically to its upstream source",
                    )
                    self.assertNotIn("transforms", item)
        self.assertGreater(seen, 0, "no verbatim file is recorded; refusing to pass vacuously")

    def test_adapted_files_record_the_upstream_hash_and_transform(self) -> None:
        manifest = _manifest()
        seen = 0
        for entry in manifest["entries"]:
            for item in entry["files"]:
                if item["kind"] != "adapted":
                    continue
                seen += 1
                with self.subTest(path=item["path"]):
                    self.assertRegex(item.get("upstream_sha256", ""), r"^[0-9a-f]{64}$")
                    self.assertTrue(item.get("transforms"), "an adapted file must name its transform")
                    kinds = {transform["kind"] for transform in item["transforms"]}
                    self.assertLessEqual(
                        kinds,
                        set(ADAPTATION_TRANSFORM_KINDS),
                        "an adapted file uses an undeclared transform kind",
                    )
                    if "entry-document-renamed" not in kinds:
                        self.assertNotEqual(
                            item["upstream_sha256"],
                            item["sha256"],
                            "content adaptation must change the file hash",
                        )
        self.assertEqual(seen, EXPECTED_ADAPTED_FILE_COUNT, "the recorded adaptation set changed")

    def test_extracted_upstream_content_is_free_of_zero_bash_tokens(self) -> None:
        # Only the copied upstream text is checked here. SpecKit-authored metadata
        # files describe the guard itself, and the suite's own release-readiness
        # tests verify the guard end to end across the whole tree.
        subjects = [
            path
            for tree in VERBATIM_TREES
            for path in sorted((REF_ROOT / tree).rglob("*"))
            if path.is_file()
        ]
        subjects.append(REF_ROOT / DERIVED_FILE)
        offenders = []
        for path in subjects:
            content = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in ZERO_BASH_TOKENS:
                if pattern.search(content):
                    offenders.append(f"{path.relative_to(REF_ROOT).as_posix()}: {pattern.pattern}")
        self.assertEqual(offenders, [], "extracted content would block the plugin zero-Bash guard")

    def test_fidelity_prose_matches_the_manifest(self) -> None:
        manifest = _manifest()
        counts = {}
        for entry in manifest["entries"]:
            for item in entry["files"]:
                counts[item["kind"]] = counts.get(item["kind"], 0) + 1
        self.assertEqual(counts.get("verbatim"), 12)
        self.assertEqual(counts.get("adapted"), EXPECTED_ADAPTED_FILE_COUNT)
        readme = (REF_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "Twelve of the twenty",
            readme,
            "README copy-fidelity totals drifted from provenance.json; update both together",
        )
        self.assertIn(
            "Eight files are labelled `adapted`",
            readme,
            "README adapted-file total drifted from provenance.json; update both together",
        )
        notice = (REF_ROOT / "UPSTREAM-NOTICE.md").read_text(encoding="utf-8")
        self.assertIn(
            "Twelve files are byte-for-byte **verbatim**; eight carry",
            notice,
            "UPSTREAM-NOTICE totals drifted from provenance.json; update both together",
        )

    def test_derived_guide_names_its_upstream_sources(self) -> None:
        manifest = _manifest()
        entry = _entry_by_name(manifest, "witness-and-trace")
        self.assertEqual(entry["kind"], "derived")
        self.assertEqual(entry["upstream_path"], "agentic")
        text = (REF_ROOT / DERIVED_FILE).read_text(encoding="utf-8")
        self.assertIn(EXPECTED_COMMIT, text)
        for upstream in (
            "agentic/agents/verifier.md",
            "agentic/commands/verify/generate-witness.md",
            "agentic/commands/verify/explain-trace.md",
            "agentic/commands/verify/debug-witness.md",
        ):
            with self.subTest(upstream=upstream):
                self.assertIn(upstream, text)
        self.assertIn("not a verbatim upstream copy", text)

    def test_unadopted_upstream_layers_are_absent(self) -> None:
        present = {path.name for path in REF_ROOT.rglob("*")}
        self.assertEqual(present & UNADOPTED_NAMES, set(), "unadopted upstream layer extracted")
        bad_suffixes = sorted(
            path.relative_to(REF_ROOT).as_posix()
            for path in REF_ROOT.rglob("*")
            if path.is_file() and path.suffix.lower() in UNADOPTED_SUFFIXES
        )
        self.assertEqual(bad_suffixes, [], "Docker/MCP/LSP artefacts extracted")

    def test_guide_links_local_references_only(self) -> None:
        guide = (GUIDE_ROOT / "quint-guide.md").read_text(encoding="utf-8")
        for expected in (
            "quint/quint-lang/OVERVIEW.md",
            "quint/quint-modeling/OVERVIEW.md",
            "quint/witness-and-trace.md",
            "quint/UPSTREAM-NOTICE.md",
            "quint/provenance.json",
        ):
            with self.subTest(link=expected):
                self.assertIn(expected, guide)
        for forbidden in ("quint-execute-spec", "Docker", "MCP", "LSP"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(f"quint/{forbidden}", guide)
        self.assertIn("authoring", guide.lower())
        self.assertIn("smallest relevant", guide)

    def test_model_author_uses_local_references_and_keeps_gates_in_speckit(self) -> None:
        surfaces = (
            REPO_ROOT / "speckit-pro" / "agents" / "formal-model-author.md",
            REPO_ROOT / "speckit-pro" / "codex-agents" / "formal-model-author.toml",
        )
        for surface in surfaces:
            with self.subTest(surface=surface.name):
                text = surface.read_text(encoding="utf-8")
                self.assertIn("references/quint/quint-lang/OVERVIEW.md", text)
                self.assertIn("references/quint/quint-modeling/OVERVIEW.md", text)
                self.assertIn("references/quint/witness-and-trace.md", text)
                self.assertIn("formal-check", text)
                self.assertIn("gate decisions", text)
                for forbidden in ("quint-execute-spec", "Docker", "MCP server", "LSP"):
                    self.assertNotIn(forbidden, text)


class QuintProgressiveDisclosureTests(unittest.TestCase):
    """The extracted references must be reachable at level 3 on both platforms."""

    SKILL_ROOT = REPO_ROOT / "speckit-pro" / "skills" / "speckit-coach"
    LINK_RE = re.compile(r"\[[^\]]*\]\((?P<target>[^)\s]+)\)")

    def _links(self, path: Path) -> list[str]:
        found = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("```"):
                continue
            found.extend(match.group("target") for match in self.LINK_RE.finditer(line))
        return found

    def _resolve(self, source: Path, target: str) -> Path:
        target = target.split("#", 1)[0]
        return (source.parent / target).resolve()

    def test_no_nested_skill_entrypoint_is_extracted(self) -> None:
        nested = sorted(
            path.relative_to(REF_ROOT).as_posix()
            for path in REF_ROOT.rglob("SKILL.md")
        )
        self.assertEqual(
            nested,
            [],
            "a nested SKILL.md is stripped from the Codex payload and would dangle links",
        )
        for tree in VERBATIM_TREES:
            with self.subTest(tree=tree):
                self.assertTrue(
                    (REF_ROOT / tree / "OVERVIEW.md").is_file(),
                    f"{tree} must ship its renamed entry document",
                )

    def test_quint_guide_disclosure_links_resolve(self) -> None:
        guide = GUIDE_ROOT / "quint-guide.md"
        targets = [t for t in self._links(guide) if not t.startswith(("http://", "https://"))]
        self.assertTrue(targets, "the guide must link its bundled references")
        for target in targets:
            with self.subTest(target=target):
                self.assertTrue(self._resolve(guide, target).is_file(), f"dangling link {target}")

    def test_reference_readme_links_resolve(self) -> None:
        readme = REF_ROOT / "README.md"
        for target in self._links(readme):
            if target.startswith(("http://", "https://")):
                continue
            with self.subTest(target=target):
                self.assertTrue(self._resolve(readme, target).is_file(), f"dangling link {target}")

    def test_both_coach_surfaces_route_to_the_quint_guide(self) -> None:
        surfaces = {
            REPO_ROOT / "speckit-pro" / "skills" / "speckit-coach" / "SKILL.md":
                "./references/quint-guide.md",
            REPO_ROOT / "speckit-pro" / "codex-skills" / "speckit-coach" / "SKILL.md":
                "../../skills/speckit-coach/references/quint-guide.md",
        }
        for surface, expected in surfaces.items():
            with self.subTest(surface=surface.name):
                text = surface.read_text(encoding="utf-8")
                self.assertIn(expected, text, "the coach must route to the Quint guidance")
                self.assertTrue(
                    self._resolve(surface, expected).is_file(),
                    f"{surface.name} routes to a missing file",
                )
                self.assertLess(
                    len(text.split()),
                    5000,
                    "the guide caps a skill entrypoint at 5,000 words",
                )

    def test_model_author_reference_paths_exist(self) -> None:
        for surface in (
            REPO_ROOT / "speckit-pro" / "agents" / "formal-model-author.md",
            REPO_ROOT / "speckit-pro" / "codex-agents" / "formal-model-author.toml",
        ):
            text = surface.read_text(encoding="utf-8")
            for target in sorted(set(re.findall(r"references/quint[a-z0-9/._-]*?\.(?:md|json)", text))):
                with self.subTest(surface=surface.name, target=target):
                    self.assertTrue(
                        (self.SKILL_ROOT / target).is_file(),
                        f"{surface.name} names a missing reference {target}",
                    )


if __name__ == "__main__":
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite(
        (
            loader.loadTestsFromTestCase(QuintReferenceAttributionTests),
            loader.loadTestsFromTestCase(QuintProgressiveDisclosureTests),
        )
    )
    raise SystemExit(run_counted(suite, label="test-quint-reference-attribution"))
