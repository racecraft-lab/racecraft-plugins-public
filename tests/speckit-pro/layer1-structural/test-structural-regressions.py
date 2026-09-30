#!/usr/bin/env python3
"""Focused failure-path tests for consolidated structural validators."""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
LAYER1_DIR = REPO_ROOT / "tests" / "speckit-pro" / "layer1-structural"
for path in (LIB_DIR, LAYER1_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
import agent_roster  # noqa: E402
from host_skill_views import host_skill_root  # noqa: E402
from script_loader import load_script  # noqa: E402
import structural_helpers  # noqa: E402
from test_result import run_counted  # noqa: E402


def load_module(name: str, filename: str):
    path = LAYER1_DIR / filename
    return load_script(name, path)


ci_release = load_module("validate_ci_release_contracts", "validate-ci-release-contracts.py")
payloads = load_module("validate_payload_contracts", "validate-payload-contracts.py")
agents = load_module("validate_agent_contracts", "validate-agent-contracts.py")
instructions = load_module("validate_instruction_files", "validate-instruction-files.py")
skills = load_module("validate_skill_contracts", "validate-skill-contracts.py")
metadata = load_module("validate_plugin_metadata", "validate-plugin-metadata.py")


def run_with_override(module, attribute: str, value: Path, case: type[unittest.TestCase], method: str) -> unittest.TestResult:
    """Run one validator test with a module-level path pointed at ``value``."""
    original = getattr(module, attribute)
    setattr(module, attribute, value)
    try:
        result = unittest.TestResult()
        case(method).run(result)
        return result
    finally:
        setattr(module, attribute, original)


def run_codex_agent_validator(codex_agents_dir: Path) -> unittest.TestResult:
    return run_with_override(agents, "CODEX_AGENTS_DIR", codex_agents_dir, agents.ValidateCodexAgents, "test_codex_agents")


def write_valid_agent_instruction_tree(root: Path) -> None:
    for directory in instructions.EXPECTED_AGENT_DIRS:
        target = root / directory
        target.mkdir(parents=True, exist_ok=True)
        (target / "AGENTS.md").write_text("# Rules\n\nKeep this short.\n", encoding="utf-8")
        (target / "GEMINI.md").write_text(instructions.GEMINI_WRAPPER, encoding="utf-8")
    copilot = root / ".github" / "copilot-instructions.md"
    copilot.parent.mkdir(parents=True, exist_ok=True)
    copilot.write_text(instructions.COPILOT_POINTER, encoding="utf-8")


class StructuralRegressionTests(unittest.TestCase):
    def test_release_workflow_rejects_tab_only_indentation(self) -> None:
        text = "name: Invalid\njobs:\n\tbuild:\n\t  runs-on: ubuntu-latest\n"
        self.assertFalse(ci_release.yaml_syntax_sane(text))

    def test_plugin_payload_reports_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "broken.json"
            path.write_text('{"plugins":[}\n', encoding="utf-8")
            with self.assertRaisesRegex(AssertionError, "malformed JSON.*broken.json"):
                payloads.load_json_file(path)

    def test_plugin_payload_reports_missing_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "missing.json"
            with self.assertRaisesRegex(AssertionError, "unable to read.*missing.json"):
                payloads.load_json_file(path)

    def test_agent_instruction_validator_accepts_wrapper_only_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_valid_agent_instruction_tree(root)
            self.assertEqual([], instructions.collect_errors(root))

    def test_agent_instruction_validator_rejects_claude_drift(self) -> None:
        for directory in instructions.EXPECTED_AGENT_DIRS:
            with self.subTest(directory=directory.as_posix()), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                write_valid_agent_instruction_tree(root)
                (root / directory / "CLAUDE.md").write_text("@./AGENTS.md\n", encoding="utf-8")
                errors = "\n".join(instructions.collect_errors(root))
                self.assertIn(f"{(directory / 'CLAUDE.md').as_posix()} must not exist", errors)

    def test_agent_instruction_validator_rejects_unexpected_agent_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_valid_agent_instruction_tree(root)
            extra = root / "docs" / "AGENTS.md"
            extra.parent.mkdir(parents=True)
            extra.write_text("# Extra\n", encoding="utf-8")
            errors = instructions.collect_errors(root)
            self.assertIn("docs/AGENTS.md", "\n".join(errors))

    def test_agent_instruction_validator_ignores_only_root_native_eval_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_valid_agent_instruction_tree(root)
            retained = root / ".native-eval-output" / "attempts" / "staging" / "plugin"
            retained.mkdir(parents=True)
            for name in instructions.INSTRUCTION_NAMES:
                (retained / name).write_text("retained native evidence\n", encoding="utf-8")
            self.assertEqual([], instructions.collect_errors(root))

            authored = root / "authored" / ".native-eval-output" / "AGENTS.md"
            authored.parent.mkdir(parents=True)
            authored.write_text("# Unexpected authored scope\n", encoding="utf-8")
            errors = instructions.collect_errors(root)
            self.assertIn("authored/.native-eval-output/AGENTS.md", "\n".join(errors))


class CodexAgentRegressionTests(unittest.TestCase):
    def test_codex_agent_validator_rejects_missing_native_command_lifecycle_clause(self) -> None:
        for role in agents.CODEX_AGENT_PROFILES:
            if role in agents.NATIVE_COMMAND_LIFECYCLE_EXEMPT_ROLES:
                continue
            with self.subTest(role=role), tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary) / "codex-agents"
                shutil.copytree(agents.CODEX_AGENTS_DIR, target)
                path = target / f"{role}.toml"
                text = path.read_text(encoding="utf-8")
                path.write_text(
                    text.replace(
                        '`write_stdin`',
                        '`discarded_stdin`',
                        1,
                    ),
                    encoding="utf-8",
                )

                result = run_codex_agent_validator(target)
                self.assertFalse(result.wasSuccessful(), f"{role} lifecycle corruption passed validation")
                self.assertEqual([], result.errors, f"{role} corruption raised instead of asserting")
                failures = "\n".join(
                    f"{test}\n{traceback}" for test, traceback in result.failures
                )
                self.assertIn(role, failures)
                self.assertIn("native command lifecycle clauses missing", failures)

    def test_codex_agent_validator_rejects_lifecycle_clause_in_no_command_roles(self) -> None:
        donor = (agents.CODEX_AGENTS_DIR / "phase-executor.toml").read_text(encoding="utf-8")
        paragraph = next(
            line for line in donor.splitlines() if line.startswith("**Native command lifecycle:**")
        )
        closing = '"""\n'
        for role in sorted(agents.NATIVE_COMMAND_LIFECYCLE_EXEMPT_ROLES):
            with self.subTest(role=role), tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary) / "codex-agents"
                shutil.copytree(agents.CODEX_AGENTS_DIR, target)
                path = target / f"{role}.toml"
                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.endswith("\n" + closing), f"{role} must end with its instructions block")
                path.write_text(text[: -len(closing)] + "\n" + paragraph + "\n" + closing, encoding="utf-8")

                result = run_codex_agent_validator(target)
                self.assertFalse(result.wasSuccessful(), f"{role} lifecycle injection passed validation")
                self.assertEqual([], result.errors, f"{role} injection raised instead of asserting")
                failures = "\n".join(
                    f"{test}\n{traceback}" for test, traceback in result.failures
                )
                self.assertIn(role, failures)
                self.assertIn("native command lifecycle clauses present", failures)

    def test_codex_agent_validator_rejects_newly_covered_role_corruption(self) -> None:
        mutations = (
            ("artifact-author", 'sandbox_mode = "workspace-write"', 'sandbox_mode = "read-only"'),
            ("uat-runbook-author", 'name = "uat-runbook-author"', 'name = "wrong-role"'),
        )
        for role, original, replacement in mutations:
            with self.subTest(role=role), tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary) / "codex-agents"
                shutil.copytree(agents.CODEX_AGENTS_DIR, target)
                path = target / f"{role}.toml"
                path.write_text(path.read_text(encoding="utf-8").replace(original, replacement), encoding="utf-8")

                result = run_codex_agent_validator(target)
                self.assertFalse(result.wasSuccessful(), f"{role} corruption passed validation")
                self.assertEqual([], result.errors, f"{role} corruption raised instead of producing an assertion failure")
                failures = "\n".join(f"{test}\n{traceback}" for test, traceback in result.failures)
                self.assertIn(role, failures)

    def test_codex_agent_validator_rejects_missing_directory_and_unknown_role(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "missing-codex-agents"
            result = run_codex_agent_validator(missing)
            self.assertFalse(result.wasSuccessful())
            self.assertEqual([], result.errors, "missing directory must fail closed without an unhandled error")

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "codex-agents"
            shutil.copytree(agents.CODEX_AGENTS_DIR, target)
            (target / "unknown-role.toml").write_text('name = "unknown-role"\n', encoding="utf-8")
            result = run_codex_agent_validator(target)
            self.assertFalse(result.wasSuccessful(), "unknown Codex role passed exact-roster validation")
            self.assertEqual([], result.errors)


class RosterDerivationTests(unittest.TestCase):
    """Rosters come from the skill directories and the agent inventory, never a hand list."""

    def test_skill_rosters_equal_the_discovered_directories(self) -> None:
        plugin = REPO_ROOT / "speckit-pro"
        claude = sorted(p.parent.name for p in (plugin / "skills").glob("*/SKILL.md"))
        codex = sorted(p.parent.name for p in host_skill_root("codex").glob("*/SKILL.md"))
        self.assertTrue(claude and codex)
        self.assertEqual(claude, sorted(skills.validate_skills_SKILLS))
        self.assertEqual(codex, sorted(skills.validate_codex_skills_SKILLS))
        self.assertEqual(codex, sorted(metadata.REQUIRED_SKILLS))
        self.assertEqual([], metadata.codex_skill_gaps(plugin))

    def test_discovery_finds_a_new_skill_without_editing_a_list(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("alpha", "beta"):
                (root / name).mkdir()
                (root / name / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
            (root / "not-a-skill").mkdir()
            self.assertEqual(["alpha", "beta"], structural_helpers.discover_skill_names(root))
            (root / "gamma").mkdir()
            (root / "gamma" / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
            self.assertEqual(["alpha", "beta", "gamma"], structural_helpers.discover_skill_names(root))

    def test_agent_facts_follow_a_new_inventory_role(self) -> None:
        shapes = (
            ("shared-role", "plugin_agent", "custom_agent", "workspace-write"),
            ("claude-only-role", "plugin_agent", "isolated_prompt_role", "isolated-launcher"),
            ("codex-only-role", "none", "custom_agent", "read-only"),
        )
        inventory = {"roles": [
            {"name": name, "claude_code": {"implementation": cc}, "codex": {"implementation": cx, "sandbox": sandbox}}
            for name, cc, cx, sandbox in shapes
        ]}
        self.assertEqual(
            {"shared-role": "workspace-write", "codex-only-role": "read-only"},
            agent_roster.codex_sandbox_policy(inventory),
        )
        self.assertEqual(frozenset({"claude-only-role"}), agent_roster.claude_only_roles(inventory))
        self.assertEqual(frozenset({"codex-only-role"}), agent_roster.codex_only_roles(inventory))
        self.assertIn("claude-only-role", agent_roster.capability_exempt_roles("claude", inventory))
        self.assertNotIn("codex-only-role", agent_roster.capability_exempt_roles("claude", inventory))
        self.assertIn("codex-only-role", agent_roster.capability_exempt_roles("codex", inventory))
        self.assertNotIn("shared-role", agent_roster.capability_exempt_roles("codex", inventory))

    def test_shipped_agent_facts_match_the_shipped_inventory(self) -> None:
        self.assertEqual(
            {"artifact-preview-observer", "sweep-analyst", "sweep-classifier"},
            set(agent_roster.claude_only_roles()),
        )
        self.assertEqual({"autopilot-fast-helper"}, set(agent_roster.codex_only_roles()))
        self.assertEqual(
            sorted(agent_roster.codex_sandbox_policy()),
            sorted(path.stem for path in (REPO_ROOT / "speckit-pro" / "codex-agents").glob("*.toml")),
        )


class CodexSkillRosterTests(unittest.TestCase):
    """The Codex skill roster is read from skills/, so a dropped Codex skill is a gap."""

    def test_a_dropped_codex_skill_is_a_gap_in_a_copy_of_the_plugin(self) -> None:
        plugin = REPO_ROOT / "speckit-pro"
        with tempfile.TemporaryDirectory() as temporary:
            copy = Path(temporary)
            for tree in ("skills", "codex-skills"):
                shutil.copytree(plugin / tree, copy / tree, ignore=shutil.ignore_patterns("references", "agents", "scripts"))
            self.assertEqual([], metadata.codex_skill_gaps(copy))
            shutil.rmtree(copy / "codex-skills" / "install")
            self.assertEqual(["Codex skill install/SKILL.md is missing"], metadata.codex_skill_gaps(copy))
            shutil.rmtree(copy / "skills" / "speckit-upgrade")
            (copy / "codex-skills" / "stray").mkdir()
            (copy / "codex-skills" / "stray" / "SKILL.md").write_text("---\nname: stray\n---\n", encoding="utf-8")
            self.assertEqual(
                ["Codex skill install/SKILL.md is missing", "Codex skill speckit-upgrade/ is not a required skill", "Codex skill stray/ is not a required skill"],
                metadata.codex_skill_gaps(copy),
            )


class TomlFieldTests(unittest.TestCase):
    """One reader serves the layer 1 and layer 5 agent checks; no layer keeps its own."""

    def test_reads_a_top_level_string_in_any_valid_spacing(self) -> None:
        for line in ('model = "gpt-6-sol"', 'model="gpt-6-sol"', '  model  =  "gpt-6-sol"  '):
            with self.subTest(line=line):
                self.assertEqual("gpt-6-sol", structural_helpers.toml_string_field(line + "\n", "model"))

    def test_absent_non_string_and_table_scoped_fields_read_as_empty(self) -> None:
        text = 'name = "a"\nmodel = 5\n[profile]\nsandbox_mode = "read-only"\n'
        self.assertEqual("a", structural_helpers.toml_string_field(text, "name"))
        for field in ("model", "sandbox_mode", "missing"):
            with self.subTest(field=field):
                self.assertEqual("", structural_helpers.toml_string_field(text, field))

    def test_malformed_toml_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            structural_helpers.toml_string_field('name = "a\nmodel = ', "name")

    def test_no_layer_script_defines_its_own_toml_string_extractor(self) -> None:
        layer5 = REPO_ROOT / "tests" / "speckit-pro" / "layer5-tool-scoping" / "validate-tool-scoping.py"
        texts = {path.name: path.read_text(encoding="utf-8")
                 for path in (LAYER1_DIR / "validate-agent-contracts.py", layer5)}
        own = [name for name, text in texts.items()
               if "def _extract_toml_string" in text or "def _toml_field" in text]
        self.assertEqual([], own)
        self.assertTrue(all("toml_string_field" in text for text in texts.values()))


class PayloadValidatorTests(unittest.TestCase):
    """The payload contract validator passes a sound plugin and fails a broken one."""

    def run_validator(self, source: Path) -> unittest.TestResult:
        return run_with_override(payloads, "SOURCE_ROOT", source, payloads.ValidatePluginPayload, "test_payload")

    def test_a_nested_skill_entrypoint_fails_the_payload_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "speckit-pro"
            shutil.copytree(payloads.SOURCE_ROOT, source, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            self.assertTrue(self.run_validator(source).wasSuccessful())
            nested = source / "skills" / "speckit-coach" / "nested"
            nested.mkdir()
            (nested / "SKILL.md").write_text("---\nname: nested\n---\n", encoding="utf-8")
            broken = self.run_validator(source)
        self.assertFalse(broken.wasSuccessful())
        self.assertIn("nested Codex SKILL.md count", "".join(message for _, message in broken.failures))


class RetiredPayloadBuilderTests(unittest.TestCase):
    """The full release refresh is the one payload build path; its former standalone script is gone."""

    RETIRED = "build-plugin-payloads"
    # Dated records of past work that name the script as it was then.
    HISTORICAL = (
        "docs/", ".specify/memory/",
        "tests/speckit-pro/layer6-integration/performance-fixtures/",
        "tests/speckit-pro/evals/audit/unit-remaining-support-audit.json",
        "tests/speckit-pro/unit/fixtures/plan-layers/repository-bash-confinement-plan/",
    )
    # specs/ is archived feature material that tests must never open (tests/speckit-pro/AGENTS.md).
    SKIPPED_DIRECTORIES = {".git", ".worktrees", "node_modules", "__pycache__", ".astro", ".mypy_cache", "specs"}

    def test_the_standalone_builder_is_deleted_and_unreferenced(self) -> None:
        self.assertFalse(list((REPO_ROOT / "scripts").glob(f"{self.RETIRED}*")))
        live = []
        for root, directories, files in os.walk(REPO_ROOT):
            directories[:] = [name for name in directories if name not in self.SKIPPED_DIRECTORIES]
            for name in files:
                path = Path(root) / name
                relative = path.relative_to(REPO_ROOT).as_posix()
                if relative.startswith(self.HISTORICAL) or relative == Path(__file__).relative_to(REPO_ROOT).as_posix():
                    continue
                if self.RETIRED in path.read_text(encoding="utf-8", errors="ignore"):
                    live.append(relative)
        self.assertEqual([], live)


def main() -> int:
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(StructuralRegressionTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(CodexAgentRegressionTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(RosterDerivationTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(CodexSkillRosterTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(TomlFieldTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(PayloadValidatorTests))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(RetiredPayloadBuilderTests))
    return run_counted(suite, label="test-structural-regressions")


if __name__ == "__main__":
    raise SystemExit(main())
