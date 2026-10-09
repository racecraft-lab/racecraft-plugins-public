#!/usr/bin/env python3
"""Draft page selection through the runner helper seam (ADR 0019)."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests/speckit-pro/lib"))
from test_result import run_counted  # noqa: E402


class SelectionFixture(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.gallery: Path | None = None
        self.timeout = 30
        (self.root / ".specify").mkdir()
        (self.root / "plan.md").write_text("## Declared File Operations\n\n- NEW src/new.py\n", encoding="utf-8")

    def select(self, *, status: str = "ok", plugin: str = "speckit-pro", **inputs: object) -> dict:
        request = {"schema_version": "1.0", "request_id": "artifact-selection-test",
                   "helper_id": "select-artifact-pages", "operation": "select-artifact-pages",
                   "mode": "read_only", "inputs": {"plan_file": "plan.md", **inputs}}
        done = subprocess.run([
            sys.executable, "-c", "\n".join([
                "import runpy, sys",
                "from pathlib import Path",
                "from speckit_pro_runner.helpers import artifact_selection",
                "artifact_selection.GALLERY = Path(sys.argv[1]) if sys.argv[1] != 'None' else artifact_selection.GALLERY",
                "sys.argv = sys.argv[:1]",
                "runpy.run_module('speckit_pro_runner', run_name='__main__')",
            ]), str(self.gallery),
        ], input=json.dumps(request), text=True, capture_output=True, check=False,
            cwd=self.root, env={**os.environ, "PYTHONPATH": str(ROOT / plugin)}, timeout=self.timeout)
        result = json.loads(done.stdout.splitlines()[-1])
        self.assertEqual(done.returncode, 0 if status == "ok" else 2, result)
        self.assertEqual(result["status"], status, result)
        if self.gallery is not None and status != "ok":
            self.assertIn("gallery manifest", result["diagnostics"][0]["message"])
        return result["data"]


class ManifestSecurityTests(SelectionFixture):
    def test_structurally_malformed_manifests_are_explicit_errors(self) -> None:
        gallery = self.root / "gallery"
        gallery.mkdir()
        self.gallery = gallery
        shipped = json.loads((ROOT / "speckit-pro/artifact-gallery/manifest.json").read_text(encoding="utf-8"))
        cases = [("missing contract", {"templates": []}), ("null", None), ("array", [])]
        for label, field, value in (("empty templates", "templates", []), ("invalid entries", "templates", [None]),
                                    ("invalid version", "schema_version", "2.0"), ("invalid signals", "signals", {})):
            manifest = copy.deepcopy(shipped)
            manifest[field] = value
            cases.append((label, manifest))
        for trigger in ({}, {"always": False}, {"always": 1}, {"any_of": []}, {"any_of": "brownfield_change"},
                        {"any_of": ["unknown"]}, {"always": True, "any_of": ["brownfield_change"]}):
            manifest = copy.deepcopy(shipped)
            manifest["templates"][0]["trigger"] = trigger
            cases.append((str(trigger), manifest))
        duplicate = copy.deepcopy(shipped)
        duplicate["templates"].append(duplicate["templates"][0])
        cases.append(("duplicate ids", duplicate))
        no_mandatory = copy.deepcopy(shipped)
        for entry in no_mandatory["templates"]:
            if entry["stage"] == "draft-pr":
                entry["trigger"] = {"any_of": ["brownfield_change"]}
        cases.append(("missing mandatory draft pages", no_mandatory))
        for label, manifest in cases:
            with self.subTest(case=label):
                (gallery / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                self.assertEqual(self.select(status="input_error"), {})

    def test_manifest_ids_cannot_escape_the_artifact_directory(self) -> None:
        gallery = self.root / "gallery"
        gallery.mkdir()
        self.gallery = gallery
        manifest = json.loads((ROOT / "speckit-pro/artifact-gallery/manifest.json").read_text(encoding="utf-8"))
        for identifier in ("../../escape", "/absolute-target", "sub/page", "..", "C:\\escape", "\\escape"):
            with self.subTest(identifier=identifier):
                manifest["templates"][0]["id"] = identifier
                (gallery / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                self.assertEqual(self.select(status="input_error"), {})


class OutputSecurityTests(SelectionFixture):
    def test_selection_no_longer_hands_out_pathname_checks(self) -> None:
        (self.root / "artifacts").mkdir()
        final = "artifacts/implementation-plan.html"
        for inputs in ({"candidate_paths": [final]}, {"verify_written_paths": True},
                       {"candidate_paths": [final], "verify_written_paths": True}):
            with self.subTest(inputs=inputs):
                self.assertEqual(self.select(status="input_error", **inputs), {})
        result = self.select()
        self.assertNotIn("checked_paths", result)
        self.assertNotIn("verified_paths", result)

    def test_symlinked_artifact_components_reject_selection(self) -> None:
        artifacts = self.root / "artifacts"
        outside = self.root / "outside"
        outside.mkdir()
        for target in (outside, outside / "missing"):
            with self.subTest(target=target.name):
                artifacts.symlink_to(target)
                self.assertEqual(self.select(status="input_error"), {})
                artifacts.unlink()
        artifacts.mkdir()
        final = artifacts / "implementation-plan.html"
        for target in (outside / "escape.html", artifacts / "another.html"):
            with self.subTest(target=target.name):
                final.symlink_to(target)
                self.assertEqual(self.select(status="input_error"), {})
                final.unlink()


# Runs the runner with one-shot hooks that race the artifact directory at a named point:
# "open:<name>#<n>" (before the nth descriptor-relative open of <name>), "mkdir" (after
# the feature directory is held, before artifacts/ is opened), "create" (before the
# temporary is created), "written" (after the temporary is written, before its entry is
# re-checked), "publish" (inside the last window, just before the rename), and "readback"
# (before the final page is reopened). Unfired hooks are written out so a test can prove its race ran.
RACE_ACTIONS = """
import atexit, json, os, runpy, sys
from pathlib import Path
from speckit_pro_runner import atomic_write
plan = json.loads(sys.argv[1])
sys.argv = sys.argv[:1]
atexit.register(lambda: Path('race-unfired.json').write_text(json.dumps(plan), encoding='utf-8'))
real_open, real_rename, real_replace, real_mkdir = os.open, os.rename, os.replace, os.mkdir
state = {'published': False}
opened = {}
def act(point, name):
    for action in plan.pop(point, []):
        entry = Path('artifacts', name)
        if action == 'fail':
            raise OSError('injected publication failure')
        elif action == 'owned-open':
            os.fstat(state['owned_fd'])
        elif action == 'swap':
            Path('artifacts').rename('held-artifacts')
            Path('artifacts').symlink_to('outside', target_is_directory=True)
        elif action == 'restore':
            Path('artifacts').unlink()
            Path('held-artifacts').rename('artifacts')
        elif action == 'swap-feature':
            Path('specs/feat').rename('held-feat')
            Path('specs/feat').symlink_to(Path('outside-feat').resolve(), target_is_directory=True)
        elif action == 'move':
            Path('artifacts').rename('moved-artifacts')
            Path('artifacts').mkdir()
        elif action == 'leaf-symlink':
            entry.unlink()
            entry.symlink_to(Path('outside/victim.html').resolve())
        elif action == 'leaf-hardlink':
            os.link(entry, Path('outside/linked.html'))
        elif action == 'leaf-overwrite':
            with entry.open('a', encoding='utf-8') as stream:
                stream.write('<script>injected</script>')
        elif action == 'leaf-replace':
            entry.unlink()
            entry.write_text('foreign page', encoding='utf-8')
        elif action == 'replace-final':
            final = Path('artifacts/implementation-plan.html')
            final.unlink()
            final.write_text('foreign page', encoding='utf-8')
"""
RACE_IO = """
def hooked_open(path, flags, *args, **kwargs):
    name = str(path)
    if kwargs.get('dir_fd') is not None:
        opened[name] = opened.get(name, 0) + 1
        act(f'open:{name}#{opened[name]}', name)
        if flags & os.O_CREAT and name.startswith('.artifact-author-'):
            act('create', name)
            state['temporary'] = name
        elif state['published'] and name.endswith('.html') and not flags & os.O_CREAT:
            act('readback', name)
        elif state['published'] and name == 'artifacts':
            act('bound', name)
    fd = real_open(path, flags, *args, **kwargs)
    if flags & os.O_CREAT and name.startswith('.artifact-author-'):
        state['owned_fd'] = fd
    return fd
def hooked(real):
    def move(src, dst, *args, **kwargs):
        act('restore' if state['published'] else 'publish', str(src))
        result = real(src, dst, *args, **kwargs)
        state['published'] = True
        return result
    return move
real_fsync = os.fsync
def hooked_fsync(fd):
    act('sync', state.get('temporary', ''))
    result = real_fsync(fd)
    if 'temporary' in state:
        act('written', state['temporary'])
    return result
os.fsync = hooked_fsync
def hooked_mkdir(path, *args, **kwargs):
    if str(path) == 'artifacts' and kwargs.get('dir_fd') is not None:
        act('mkdir', str(path))
    return real_mkdir(path, *args, **kwargs)
os.open, os.rename, os.replace, os.mkdir = hooked_open, hooked(real_rename), hooked(real_replace), hooked_mkdir
"""
RACE_FAILURES = """
real_write, real_read, real_close, real_unlink = os.write, os.read, os.close, os.unlink
def hooked_write(fd, data):
    if fd == state.get('owned_fd'):
        act('write', state['temporary'])
    return real_write(fd, data)
def hooked_read(fd, size):
    if state['published']:
        act('read', '')
    return real_read(fd, size)
def hooked_close(fd):
    if fd == state.get('owned_fd'):
        act('close', state['temporary'])
    return real_close(fd)
def hooked_unlink(path, *args, **kwargs):
    if state['published'] and str(path) == state.get('temporary'):
        act('cleanup', str(path))
    return real_unlink(path, *args, **kwargs)
os.write, os.read, os.close, os.unlink = hooked_write, hooked_read, hooked_close, hooked_unlink
real_swap = atomic_write.swap_entries
def hooked_swap(directory, src, dst):
    act('restore' if state['published'] else 'publish', src)
    result = real_swap(directory, src, dst)
    state['published'] = result
    return result
atomic_write.swap_entries = hooked_swap
runpy.run_module('speckit_pro_runner', run_name='__main__')
"""
RACE_RUNNER = "\n".join((RACE_ACTIONS, RACE_IO, RACE_FAILURES))
PLUGINS = ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro")
FILL = re.compile(r"(<!-- FILL:([a-z0-9-]+):START -->)(.*?)(<!-- FILL:\2:END -->)", re.DOTALL)


def rendered_page(entry_id: str) -> str:
    template = (ROOT / f"speckit-pro/artifact-gallery/templates/{entry_id}.html").read_text(encoding="utf-8")
    return FILL.sub(lambda match: f"{match.group(1)}<p>Real {match.group(2)}.</p>{match.group(4)}", template)


class PublicationFixture(SelectionFixture):
    def setUp(self) -> None:
        super().setUp()
        (self.root / "artifacts").mkdir()
        (self.root / "outside").mkdir()
        (self.root / "artifacts/implementation-plan.html").write_text("old page", encoding="utf-8")
        (self.root / "outside/victim.html").write_text("outside page", encoding="utf-8")
        self.page = rendered_page("implementation-plan")

    def publish(self, *, status: str = "ok", race: dict | None = None, plugin: str = "speckit-pro",
                mode: str = "apply", helper: str = "publish-artifact-page", **inputs: object) -> dict:
        content = {"content": self.page} if helper == "publish-artifact-page" else {}
        request = {"schema_version": "1.0", "request_id": "artifact-publication-test",
                   "helper_id": helper, "operation": helper, "mode": mode,
                   "inputs": {"plan_file": "plan.md", "entry_id": "implementation-plan", **content,
                              **inputs}}
        done = subprocess.run([sys.executable, "-c", RACE_RUNNER, json.dumps(race or {})],
                              input=json.dumps(request), text=True, capture_output=True, check=False,
                              cwd=self.root, env={**os.environ, "PYTHONPATH": str(ROOT / plugin)}, timeout=30)
        self.assertTrue(done.stdout, done.stderr)
        result = json.loads(done.stdout.splitlines()[-1])
        self.assertEqual(result["status"], status, result)
        unfired = json.loads((self.root / "race-unfired.json").read_text(encoding="utf-8"))
        self.assertEqual(unfired, {}, "every scripted race step must actually run")
        return result

    def tree(self) -> dict[str, str]:
        return {path.relative_to(self.root).as_posix(): ("-> link" if path.is_symlink() else path.read_text(encoding="utf-8"))
                for path in sorted(self.root.rglob("*")) if path.is_symlink() or path.is_file()
                if path.suffix in {".html", ".tmp"}}

    def assert_outside_untouched(self) -> None:
        self.assertEqual({name: text for name, text in self.tree().items() if name.startswith("outside/")},
                         {"outside/victim.html": "outside page"})


class PublicationRecoveryTests(PublicationFixture):
    def test_failed_readback_keeps_the_previous_page_byte_for_byte(self) -> None:
        result = self.publish(status="expected_failure", race={"readback": ["fail"]})
        self.assertEqual(self.tree(), {"artifacts/implementation-plan.html": "old page",
                                      "outside/victim.html": "outside page"})
        self.assertEqual(result["data"].get("retained_page"),
                         {"sha256": hashlib.sha256(b"old page").hexdigest(), "bytes": 8})

    def test_failure_at_each_publication_step_keeps_the_previous_bytes_on_both_hosts(self) -> None:
        previous = b"previous page\r\n\x00with exact bytes\n"
        steps = ("create", "write", "sync", "written", "publish", "readback", "read", "bound", "close", "cleanup")
        for plugin in PLUGINS:
            for step in steps:
                with self.subTest(plugin=plugin, step=step):
                    self.setUp()
                    page = self.root / "artifacts/implementation-plan.html"
                    page.write_bytes(previous)
                    self.publish(status="expected_failure", plugin=plugin, race={step: ["fail"]})
                    self.assertEqual(page.read_bytes(), previous)
                    self.assert_outside_untouched()

    def test_restore_does_not_overwrite_a_page_replaced_in_the_last_window(self) -> None:
        self.publish(status="expected_failure", race={"readback": ["fail"], "restore": ["replace-final"]})
        self.assertEqual((self.root / "artifacts/implementation-plan.html").read_bytes(), b"foreign page")
        self.assertEqual([path.read_bytes() for path in (self.root / "artifacts").glob("*.tmp")], [b"old page"])

    def test_failed_narrative_fill_forwards_the_verified_retained_page_on_both_hosts(self) -> None:
        for plugin in PLUGINS:
            with self.subTest(plugin=plugin):
                self.setUp()
                (self.root / "spec.md").write_text("# Feature: previous page\n", encoding="utf-8")
                (self.root / "tasks.md").write_text("- [ ] T001 implement the page\n", encoding="utf-8")
                result = self.publish(status="expected_failure", plugin=plugin, helper="fill-artifact-page",
                                      spec_file="spec.md", tasks_file="tasks.md", race={"readback": ["fail"]})
                self.assertEqual((self.root / "artifacts/implementation-plan.html").read_bytes(), b"old page")
                self.assertEqual(result["data"]["retained_page"],
                                 {"sha256": hashlib.sha256(b"old page").hexdigest(), "bytes": 8})


class PublicationSecurityTests(PublicationFixture):
    """F1249-f4c3e846: no pathname check is ever followed by a separate native operation."""

    def test_publication_writes_through_the_held_directory_and_reads_back_the_same_object(self) -> None:
        for plugin in PLUGINS:
            with self.subTest(plugin=plugin):
                data = self.publish(plugin=plugin, race={"publish": ["owned-open"],
                                                        "readback": ["owned-open"]})["data"]
                self.assertTrue(data["writes_state"])
                self.assertEqual(data["output_path"], "artifacts/implementation-plan.html")
                self.assertEqual(self.tree(), {"artifacts/implementation-plan.html": self.page,
                                               "outside/victim.html": "outside page"})
                self.assertEqual(data["sha256"], __import__("hashlib").sha256(self.page.encode()).hexdigest())

    def test_parent_swap_before_temporary_create_or_write_never_redirects(self) -> None:
        for plugin in PLUGINS:
            with self.subTest(plugin=plugin):
                self.setUp()
                self.publish(status="expected_failure", plugin=plugin, race={"create": ["swap"]})
                self.assert_outside_untouched()
                self.assertNotIn(self.page, self.tree().values())

    def test_parent_swap_between_temporary_verification_and_publish_never_redirects(self) -> None:
        for plugin in PLUGINS:
            with self.subTest(plugin=plugin):
                self.setUp()
                self.publish(status="expected_failure", plugin=plugin, race={"publish": ["swap"]})
                self.assert_outside_untouched()
                self.assertNotIn(self.page, self.tree().values())

    def test_parent_swap_between_publish_and_final_read_withdraws_only_the_owned_page(self) -> None:
        (self.root / "outside/implementation-plan.html").write_text("outside final", encoding="utf-8")
        self.publish(status="expected_failure", race={"readback": ["swap"]})
        tree = self.tree()
        self.assertEqual(tree["outside/implementation-plan.html"], "outside final")
        self.assertEqual(tree["outside/victim.html"], "outside page")
        self.assertNotIn(self.page, tree.values())

    def test_swap_and_restore_cannot_approve_an_old_page_or_leave_a_redirected_one(self) -> None:
        for plugin in PLUGINS:
            with self.subTest(plugin=plugin):
                self.setUp()
                self.publish(plugin=plugin, race={"create": ["swap"], "readback": ["restore"]})
                self.assertEqual(self.tree(), {"artifacts/implementation-plan.html": self.page,
                                               "outside/victim.html": "outside page"})

    def test_directory_moved_after_snapshot_is_detected_and_the_page_withdrawn(self) -> None:
        self.publish(status="expected_failure", race={"readback": ["move"]})
        self.assertNotIn(self.page, self.tree().values())
        self.assert_outside_untouched()

    def test_leaf_substitution_and_hard_links_break_the_object_binding(self) -> None:
        cases = (("symlinked temporary", {"written": ["leaf-symlink"]}),
                 ("hard-linked temporary", {"written": ["leaf-hardlink"]}),
                 ("temporary symlinked inside the rename window", {"publish": ["leaf-symlink"]}),
                 ("temporary hard-linked inside the rename window", {"publish": ["leaf-hardlink"]}),
                 ("replaced final page", {"readback": ["leaf-replace"]}),
                 ("final page rewritten in place", {"readback": ["leaf-overwrite"]}),
                 ("symlinked final page", {"readback": ["leaf-symlink"]}))
        for label, race in cases:
            with self.subTest(case=label):
                self.setUp()
                self.publish(status="expected_failure", race=race)
                tree = self.tree()
                self.assertEqual(tree["outside/victim.html"], "outside page")
                self.assertNotIn(self.page, [text for name, text in tree.items() if name.startswith("artifacts/")])
                self.assertFalse([name for name in tree if name.endswith(".tmp") and tree[name] == self.page])
                if "written" in race:
                    self.assertEqual(tree["artifacts/implementation-plan.html"], "old page",
                                     "a substituted temporary must never be renamed over the final page")

    def test_cleanup_never_unlinks_an_entry_it_did_not_create(self) -> None:
        self.publish(status="expected_failure", race={"readback": ["leaf-replace"]})
        self.assertEqual(self.tree()["artifacts/implementation-plan.html"], "foreign page")
        self.setUp()
        self.publish(status="expected_failure", race={"publish": ["leaf-symlink"]})
        self.assertTrue([path for path in (self.root / "artifacts").iterdir() if path.is_symlink()])
        self.assert_outside_untouched()

    def test_parent_swap_after_selection_before_the_directory_open_is_refused(self) -> None:
        for plugin in PLUGINS:
            with self.subTest(plugin=plugin):
                self.setUp()
                self.publish(status="expected_failure", plugin=plugin, race={"mkdir": ["swap"]})
                self.assert_outside_untouched()

    def test_feature_directory_swap_before_the_descriptor_walk_is_refused(self) -> None:
        feature = self.root / "specs/feat"
        feature.mkdir(parents=True)
        (self.root / "plan.md").rename(feature / "plan.md")
        (self.root / "outside-feat").mkdir()
        (self.root / "outside-feat/plan.md").write_text((feature / "plan.md").read_text(encoding="utf-8"),
                                                       encoding="utf-8")
        self.publish(status="expected_failure", plan_file="specs/feat/plan.md", race={"open:feat#2": ["swap-feature"]})
        self.assertEqual(sorted(path.name for path in (self.root / "outside-feat").iterdir()), ["plan.md"])
        self.assertNotIn(self.page, self.tree().values())

    def test_symlinked_artifact_directory_is_refused_before_any_write(self) -> None:
        (self.root / "artifacts/implementation-plan.html").unlink()
        (self.root / "artifacts").rmdir()
        (self.root / "artifacts").symlink_to(self.root / "outside", target_is_directory=True)
        self.publish(status="input_error")
        self.assert_outside_untouched()


class PublicationContentTests(PublicationFixture):
    def test_unselected_template_identical_and_partial_pages_are_refused(self) -> None:
        template = (ROOT / "speckit-pro/artifact-gallery/templates/implementation-plan.html").read_text(encoding="utf-8")
        first_region = FILL.search(template)
        assert first_region is not None
        partial = self.page.replace(f"<p>Real {first_region.group(2)}.</p>", first_region.group(3), 1)
        cases = ({"entry_id": "module-map", "content": rendered_page("module-map")}, {"entry_id": "../escape"},
                 {"content": template}, {"content": partial}, {"content": self.page + '<p class="note">x</p>'},
                 {"content": self.page.replace("<!-- FILL:phases:END -->", "", 1)}, {"content": ""},
                 {"unknown": True})
        for inputs in cases:
            with self.subTest(inputs=sorted(inputs)):
                self.publish(status="input_error", **inputs)
                self.assertEqual(self.tree()["artifacts/implementation-plan.html"], "old page")

    def test_dry_run_validates_without_writing(self) -> None:
        data = self.publish(mode="dry_run")["data"]
        self.assertFalse(data["writes_state"])
        self.assertEqual(self.tree()["artifacts/implementation-plan.html"], "old page")


class ArtifactSelectionTests(SelectionFixture):
    def test_new_files_select_only_the_always_selected_draft_pages(self) -> None:
        result = self.select()
        self.assertEqual(result["selected_pages"], ["implementation-plan", "spec-explainer"])
        self.assertEqual(result["signals"], [])
        self.assertFalse(result["writes_state"])

    def test_modified_operation_selects_module_map_in_manifest_order(self) -> None:
        (self.root / "plan.md").write_text("## Declared File Operations\n\n- NEW src/new.py\n"
                                           "- MODIFIED src/existing.py\n", encoding="utf-8")
        result = self.select()
        self.assertEqual(result["selected_pages"], ["implementation-plan", "spec-explainer", "module-map"])
        self.assertEqual(result["signals"], ["brownfield_change"])

    def test_each_signal_follows_its_planning_record(self) -> None:
        cases = (
            ("plan_file", "plan.md", "- MODIFIED outside.py\n## Declared File Operations\n"
             "- NEW src/new.py\n## Notes\n- MODIFIED also-outside.py\n", [],
             ["implementation-plan", "spec-explainer"]),
            ("plan_file", "plan.md", "## Declared File Operations\n- NEW src/new.py\n"
             "```markdown\n- MODIFIED src/example.py\n```\n", [], ["implementation-plan", "spec-explainer"]),
            ("plan_file", "plan.md", "## Declared File Operations\n- NEW src/new.py\n<!--\n  - MODIFIED <path>\n-->\n"
             "<!-- - MODIFIED src/inline.py -->\n", [], ["implementation-plan", "spec-explainer"]),
            ("research_file", "research.md", "**Alternatives considered**: a separate schema.\n",
             ["competing_approaches"], ["implementation-plan", "spec-explainer", "code-approaches"]),
            ("design_concept_file", "design.md", "**Alternatives offered:**\n- Keep the old schema.\n",
             ["competing_approaches"], ["implementation-plan", "spec-explainer", "code-approaches"]),
        )
        for field, filename, text, signals, pages in cases:
            with self.subTest(field=field, text=text):
                (self.root / filename).write_text(text, encoding="utf-8")
                result = self.select(**{field: filename})
                self.assertEqual((result["signals"], result["selected_pages"]), (signals, pages))

    def test_links_and_subheadings_record_real_alternatives(self) -> None:
        for text in ("**Alternatives considered**:\n- [Separate schema](https://example.com/schema)\n",
                     "## Alternatives considered\n### Separate schema\nKeep a dedicated schema.\n",
                     "- Decision: reuse\n- Alternatives considered: a separate schema.\n",
                     "- **Alternatives considered**: a separate schema.\n", "Alternatives considered: a separate schema.\n"):
            with self.subTest(text=text):
                (self.root / "research.md").write_text(text, encoding="utf-8")
                self.assertEqual(self.select(research_file="research.md")["signals"], ["competing_approaches"])

    def test_empty_negative_placeholder_and_incidental_alternatives_do_not_select(self) -> None:
        for text in ("", "We may research alternatives later.\n", "## Alternatives were not considered\n",
                     "## Alternatives considered\n\n## Decision\nKeep it.\n",
                     "**Alternatives considered**: None.\n", "**Alternatives offered:**\n- N/A\n",
                     "**Alternatives considered**: None.\nCompatibility requires the existing approach.\n",
                     "## Alternatives considered\nNone.\nCompatibility requires the existing approach.\n",
                     "## Alternatives\n[TODO]\n", "- Alternatives considered: None\n",
                     "Alternatives were weighed in review.\n", "```markdown\n**Alternatives considered**: Example.\n```\n"):
            with self.subTest(text=text):
                (self.root / "research.md").write_text(text, encoding="utf-8")
                (self.root / "design.md").write_text(text, encoding="utf-8")
                self.assertEqual(self.select(research_file="research.md", design_concept_file="design.md")["signals"], [])

    def test_both_rules_select_all_shipped_draft_pages_but_no_planned_or_final_pages(self) -> None:
        (self.root / "plan.md").write_text("## Declared File Operations\n- MODIFIED src/old.py\n", encoding="utf-8")
        (self.root / "research.md").write_text("## Alternatives considered\n- Add a new adapter.\n", encoding="utf-8")
        for plugin in ("speckit-pro", "dist/claude/speckit-pro", "dist/codex/speckit-pro"):
            with self.subTest(plugin=plugin):
                self.assertEqual(self.select(plugin=plugin, research_file="research.md")["selected_pages"],
                                 ["implementation-plan", "spec-explainer", "code-approaches", "module-map"])

    def test_unreadable_invalid_and_escaping_inputs_are_explicit_selection_errors(self) -> None:
        for inputs in ({"plan_file": "missing.md"}, {"research_file": "missing.md"},
                       {"design_concept_file": "../outside.md"}, {"plan_file": 1}, {"unknown": True}):
            with self.subTest(inputs=inputs):
                self.assertEqual(self.select(status="input_error", **inputs), {})
        (self.root / "outside-link.md").symlink_to(ROOT / "README.md")
        self.assertEqual(self.select(status="input_error", research_file="outside-link.md"), {})


class ArtifactHostSelectionTests(SelectionFixture):
    def test_packaged_hosts_enforce_manifest_and_output_confinement(self) -> None:
        gallery = self.root / "gallery"
        gallery.mkdir()
        shipped = json.loads((ROOT / "speckit-pro/artifact-gallery/manifest.json").read_text(encoding="utf-8"))
        for host in ("claude", "codex"):
            plugin = f"dist/{host}/speckit-pro"
            with self.subTest(host=host):
                self.assertEqual(self.select(plugin=plugin)["output_paths"], {
                    "implementation-plan": "artifacts/implementation-plan.html",
                    "spec-explainer": "artifacts/spec-explainer.html",
                })
                self.gallery = gallery
                for identifier in ("../../escape", "/absolute-target"):
                    manifest = copy.deepcopy(shipped)
                    manifest["templates"][0]["id"] = identifier
                    (gallery / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
                    self.assertEqual(self.select(status="input_error", plugin=plugin), {})
                malformed = copy.deepcopy(shipped)
                malformed["templates"][0]["trigger"] = {}
                (gallery / "manifest.json").write_text(json.dumps(malformed), encoding="utf-8")
                self.assertEqual(self.select(status="input_error", plugin=plugin), {})
                self.gallery = None
                (self.root / "artifacts").symlink_to(self.root / "redirected")
                self.assertEqual(self.select(status="input_error", plugin=plugin), {})
                (self.root / "artifacts").unlink()

    def test_both_host_dispatches_and_author_roles_consume_runner_selection(self) -> None:
        for host, agent in (("claude", "agents/artifact-author.md"), ("codex", "codex-agents/artifact-author.toml")):
            with self.subTest(host=host):
                plugin = ROOT / f"dist/{host}/speckit-pro"
                for relative in ("skills/speckit-autopilot/SKILL.md", agent):
                    text = (plugin / relative).read_text(encoding="utf-8")
                    self.assertIn("select-artifact-pages", text)
                    self.assertIn("selected_pages", text)
                self.assertNotIn("Apply each surviving entry's `trigger`", (plugin / agent).read_text(encoding="utf-8"))

    def test_both_author_roles_route_every_artifact_operation_through_the_runner(self) -> None:
        for host, agent in (("claude", "agents/artifact-author.md"), ("codex", "codex-agents/artifact-author.toml")):
            for root in (ROOT / "speckit-pro", ROOT / f"dist/{host}/speckit-pro"):
                with self.subTest(host=host, root=root.relative_to(ROOT).as_posix()):
                    author = " ".join((root / agent).read_text(encoding="utf-8").split())
                    self.assertIn("publish-artifact-page", author)
                    self.assertIn("Never create, write, rename, read, or delete anything in the `artifacts/`", author)
                    for retired in ("candidate_paths", "checked_paths", "verify_written_paths", "verified_paths",
                                    ".artifact-author-<entry-id>", "Native tool writes retain a check/use race"):
                        self.assertNotIn(retired, author)

if __name__ == "__main__":
    raise SystemExit(run_counted(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]),
                                 label="test-artifact-selection"))
