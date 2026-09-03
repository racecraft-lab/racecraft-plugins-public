#!/usr/bin/env python3
"""Behavior contracts for the Layer 6 governed role-corpus rebaseline script.

The corpus binds a sha256 chain over live agent source bytes, so editing any
agent definition stales it. ``rebaseline-corpus.py`` is the regeneration step.
Every case here runs the real script against a throwaway copy of the tracked
tree, so no assertion depends on the digests the working tree happens to carry.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_ROOT = REPO_ROOT / "tests" / "speckit-pro"
LIB_DIR = TEST_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from test_result import run_counted  # noqa: E402


LAYER6_REL = "tests/speckit-pro/layer6-efficiency"
SCRIPT_REL = f"{LAYER6_REL}/rebaseline-corpus.py"
MODULE_REL = f"{LAYER6_REL}/lib/qualification_corpus.py"
FIXTURE_ROOT_REL = f"{LAYER6_REL}/fixtures-codex"
MANIFEST_REL = f"{FIXTURE_ROOT_REL}/corpus-manifest.json"
ROSTER_REL = f"{LAYER6_REL}/fixtures/claude-agent-roster-rebaseline-v2.json"
HISTORICAL_CORPUS_REL = f"{LAYER6_REL}/fixtures/car-003-role-corpus.json"
SCHEMA_RELS = (
    f"{LAYER6_REL}/contracts/role-corpus.schema.json",
    f"{LAYER6_REL}/contracts-claude/role-corpus.schema.json",
    f"{LAYER6_REL}/contracts-codex-specification/role-corpus.schema.json",
)
AGENT_DIR_REL = "speckit-pro/agents"
CODEX_AGENT_DIR_REL = "speckit-pro/codex-agents"

SCRIPT_PATH = REPO_ROOT / SCRIPT_REL
ROUND_TRIP_ROLE = "uat-runbook-author"
# A role the governed order does not carry, used to drive the growth direction
# of the membership flags inside the throwaway tree.
ADDED_ROLE = "sandbox-thirteenth-role"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def digest_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def digest_value(value: object) -> str:
    return digest_bytes(canonical_bytes(value))


def load_module(path: Path):
    name = f"_rebaseline_corpus_module_{uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class RebaselineScriptTestCase(unittest.TestCase):
    """Shared throwaway-tree scaffolding for the rebaseline script."""

    maxDiff = None

    def setUp(self) -> None:
        self.assertTrue(
            SCRIPT_PATH.is_file(),
            f"missing implementation: {SCRIPT_REL}",
        )
        self.sandbox = Path(tempfile.mkdtemp(prefix="rebaseline-corpus-")).resolve()
        self.addCleanup(shutil.rmtree, self.sandbox, ignore_errors=True)
        self._populate()

    def _copy_file(self, relative: str) -> None:
        destination = self.sandbox / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)

    def _copy_tree(self, relative: str) -> None:
        shutil.copytree(REPO_ROOT / relative, self.sandbox / relative)

    def _populate(self) -> None:
        (self.sandbox / AGENT_DIR_REL).mkdir(parents=True, exist_ok=True)
        for source in sorted((REPO_ROOT / AGENT_DIR_REL).glob("*.md")):
            shutil.copy2(source, self.sandbox / AGENT_DIR_REL / source.name)
        self._copy_tree(CODEX_AGENT_DIR_REL)
        self._copy_tree(FIXTURE_ROOT_REL)
        for relative in (SCRIPT_REL, MODULE_REL, ROSTER_REL, HISTORICAL_CORPUS_REL, *SCHEMA_RELS):
            self._copy_file(relative)

    def run_script(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.sandbox / SCRIPT_REL), *args],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(self.sandbox),
        )

    def read_bytes(self, relative: str) -> bytes:
        return (self.sandbox / relative).read_bytes()

    def read_json(self, relative: str) -> dict:
        return json.loads(self.read_bytes(relative).decode("utf-8"))

    def snapshot(self) -> dict[str, str]:
        """Map every tracked sandbox file to its content digest.

        Digests rather than bytes keep a failing comparison readable, and
        ``__pycache__`` is skipped because importing the corpus module writes it.
        """
        tracked: dict[str, str] = {}
        for path in sorted(self.sandbox.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            tracked[str(path.relative_to(self.sandbox))] = digest_bytes(path.read_bytes())
        return tracked

    def drop_role_from_module(self, role_id: str) -> None:
        module_path = self.sandbox / MODULE_REL
        kept = [
            line
            for line in module_path.read_text(encoding="utf-8").splitlines(keepends=True)
            if line.strip() != f'"{role_id}",'
        ]
        module_path.write_text("".join(kept), encoding="utf-8")

    def add_role_to_module(self, role_id: str) -> None:
        module_path = self.sandbox / MODULE_REL
        opener = "GOVERNED_ROLE_ORDER = (\n"
        source = module_path.read_text(encoding="utf-8")
        self.assertIn(opener, source)
        module_path.write_text(
            source.replace(opener, f'{opener}    "{role_id}",\n', 1), encoding="utf-8"
        )

    def source_relative_path(self, role_id: str) -> str:
        module = load_module(self.sandbox / MODULE_REL)
        if role_id in module.NON_EXECUTABLE_CORE_ROLES:
            return f"{AGENT_DIR_REL}/{role_id}.md"
        return f"{CODEX_AGENT_DIR_REL}/{role_id}.toml"


class RebaselineWriteTests(RebaselineScriptTestCase):
    """Default mode rebinds the digest chain to the live source bytes."""

    def test_rebaseline_binds_every_governed_role_to_live_source_bytes(self) -> None:
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        module = load_module(self.sandbox / MODULE_REL)
        manifest = self.read_json(MANIFEST_REL)
        self.assertEqual(
            [role["role_id"] for role in manifest["roles"]],
            list(module.GOVERNED_ROLE_ORDER),
        )
        for role in manifest["roles"]:
            role_id = role["role_id"]
            with self.subTest(role=role_id):
                source_rel = self.source_relative_path(role_id)
                self.assertEqual(role["source_binding"]["source_path"], source_rel)
                self.assertEqual(
                    role["source_binding"]["source_digest"],
                    digest_bytes(self.read_bytes(source_rel)),
                )

    def test_rebaseline_writes_fixtures_the_manifest_reproduces(self) -> None:
        self.assertEqual(self.run_script().returncode, 0)
        manifest = self.read_json(MANIFEST_REL)
        for role in manifest["roles"]:
            role_id = role["role_id"]
            with self.subTest(role=role_id):
                fixture_rel = f"{FIXTURE_ROOT_REL}/{role_id}/fixture.json"
                raw = self.read_bytes(fixture_rel)
                self.assertEqual(raw, canonical_bytes(json.loads(raw)) + b"\n")
                self.assertEqual(json.loads(raw), role)

    def test_rebaselined_corpus_passes_the_governed_validator(self) -> None:
        self.assertEqual(self.run_script().returncode, 0)
        module = load_module(self.sandbox / MODULE_REL)
        validated = module.validate_role_corpus(
            self.read_json(MANIFEST_REL), repo_root=self.sandbox
        )
        self.assertEqual(
            [role["role_id"] for role in validated["roles"]],
            list(module.GOVERNED_ROLE_ORDER),
        )

    def test_rebaseline_preserves_the_identity_fixture_digests(self) -> None:
        # fixture_binding.fixture_digest is an identity digest over the fixture
        # ID, not a content digest, so a source rebaseline must not disturb it.
        before = {
            role["role_id"]: role["fixture_binding"]["fixture_digest"]
            for role in self.read_json(MANIFEST_REL)["roles"]
        }
        self.assertEqual(self.run_script().returncode, 0)
        after = {
            role["role_id"]: role["fixture_binding"]["fixture_digest"]
            for role in self.read_json(MANIFEST_REL)["roles"]
        }
        self.assertEqual(after, before)

    def test_rebaseline_rebinds_the_claude_roster_and_its_catalog_digest(self) -> None:
        self.assertEqual(self.run_script().returncode, 0)
        roster = self.read_json(ROSTER_REL)
        for role in roster["shipped_roles"]:
            with self.subTest(role=role["role_id"]):
                self.assertEqual(
                    role["source_digest"],
                    digest_bytes(self.read_bytes(f"{AGENT_DIR_REL}/{role['role_id']}.md")),
                )
        preimage = {key: value for key, value in roster.items() if key != "catalog_digest"}
        self.assertEqual(roster["catalog_digest"], digest_value(preimage))

    def test_rebaseline_leaves_the_immutable_historical_corpus_alone(self) -> None:
        before = self.read_bytes(HISTORICAL_CORPUS_REL)
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual(self.read_bytes(HISTORICAL_CORPUS_REL), before)

    def test_a_second_rebaseline_is_a_byte_identical_no_op(self) -> None:
        self.assertEqual(self.run_script().returncode, 0)
        first = self.snapshot()
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual(self.snapshot(), first)


class RebaselineCheckTests(RebaselineScriptTestCase):
    """``--check`` reports drift without writing."""

    def test_check_passes_on_a_freshly_rebaselined_tree(self) -> None:
        self.assertEqual(self.run_script().returncode, 0)
        result = self.run_script("--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_check_fails_and_names_the_drift_after_a_one_byte_agent_change(self) -> None:
        self.assertEqual(self.run_script().returncode, 0)
        agent_rel = f"{AGENT_DIR_REL}/gate-validator.md"
        agent_path = self.sandbox / agent_rel
        agent_path.write_bytes(agent_path.read_bytes() + b"\n")
        result = self.run_script("--check")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = result.stdout + result.stderr
        self.assertIn("gate-validator", report)
        self.assertIn(MANIFEST_REL, report)

    def test_check_never_writes(self) -> None:
        self.assertEqual(self.run_script().returncode, 0)
        agent_rel = f"{AGENT_DIR_REL}/gate-validator.md"
        agent_path = self.sandbox / agent_rel
        agent_path.write_bytes(agent_path.read_bytes() + b"\n")
        before = self.snapshot()
        self.assertEqual(self.run_script("--check").returncode, 1)
        self.assertEqual(self.snapshot(), before)


class RebaselineMembershipTests(RebaselineScriptTestCase):
    """``--remove-role`` and ``--add-role`` keep membership and schemas in step."""

    def enum_ids(self, relative: str) -> list[str]:
        """Return the role_id enum, whichever role definition the schema names."""
        definitions = self.read_json(relative)["$defs"]
        for name in ("roleContract", "role"):
            role_schema = definitions.get(name)
            if role_schema and "enum" in role_schema.get("properties", {}).get("role_id", {}):
                return list(role_schema["properties"]["role_id"]["enum"])
        raise AssertionError(f"no role_id enum in {relative}")

    def role_count_bounds(self, relative: str) -> tuple[int, int]:
        """Return the ``roles`` array bounds the schema publishes."""
        roles_schema = self.read_json(relative)["properties"]["roles"]
        return roles_schema["minItems"], roles_schema["maxItems"]

    def test_remove_role_drops_the_id_from_every_schema_enum(self) -> None:
        self.assertEqual(self.run_script().returncode, 0)
        self.drop_role_from_module(ROUND_TRIP_ROLE)
        result = self.run_script("--remove-role", ROUND_TRIP_ROLE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for relative in SCHEMA_RELS:
            with self.subTest(schema=relative):
                self.assertNotIn(ROUND_TRIP_ROLE, self.enum_ids(relative))
                self.assertEqual(len(self.enum_ids(relative)), 11)
        manifest = self.read_json(MANIFEST_REL)
        self.assertNotIn(
            ROUND_TRIP_ROLE, [role["role_id"] for role in manifest["roles"]]
        )
        self.assertFalse((self.sandbox / FIXTURE_ROOT_REL / ROUND_TRIP_ROLE).exists())

    def test_remove_role_spares_the_benchmark_fixtures_beside_the_corpus_file(self) -> None:
        # fixtures-codex/<role>/ is shared: the corpus owns fixture.json, and the
        # L6 Codex benchmark owns input-prompt.md and expected-output.md beside
        # it. Dropping a role from the corpus does not retire the Codex agent, so
        # the benchmark files have to survive the removal.
        self.assertEqual(self.run_script().returncode, 0)
        self.drop_role_from_module(ROUND_TRIP_ROLE)
        role_dir = self.sandbox / FIXTURE_ROOT_REL / ROUND_TRIP_ROLE
        sibling = role_dir / "input-prompt.md"
        sibling_bytes = b"# Benchmark input owned by run-efficiency-benchmarks.py\n"
        sibling.write_bytes(sibling_bytes)
        result = self.run_script("--remove-role", ROUND_TRIP_ROLE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((role_dir / "fixture.json").exists())
        self.assertTrue(role_dir.is_dir(), "the shared fixture directory must survive")
        self.assertEqual(sibling.read_bytes(), sibling_bytes)

    def test_remove_role_refuses_while_the_governed_order_still_lists_it(self) -> None:
        self.assertEqual(self.run_script().returncode, 0)
        before = self.snapshot()
        result = self.run_script("--remove-role", ROUND_TRIP_ROLE)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("GOVERNED_ROLE_ORDER", result.stdout + result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_remove_then_add_round_trips_to_the_same_fixture_bytes(self) -> None:
        self.assertEqual(self.run_script().returncode, 0)
        baseline = self.snapshot()
        module_bytes = self.read_bytes(MODULE_REL)
        self.drop_role_from_module(ROUND_TRIP_ROLE)
        self.assertEqual(self.run_script("--remove-role", ROUND_TRIP_ROLE).returncode, 0)
        (self.sandbox / MODULE_REL).write_bytes(module_bytes)
        result = self.run_script("--add-role", ROUND_TRIP_ROLE, "--kind", "codex_toml")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.snapshot(), baseline)

    def test_remove_role_retunes_the_role_count_in_every_schema(self) -> None:
        # The enum and the array bounds have to move together. Eleven permitted
        # ids under minItems 12 is unsatisfiable, so the schema would reject the
        # corpus the same run wrote.
        self.assertEqual(self.run_script().returncode, 0)
        self.drop_role_from_module(ROUND_TRIP_ROLE)
        result = self.run_script("--remove-role", ROUND_TRIP_ROLE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(self.read_json(MANIFEST_REL)["roles"]), 11)
        for relative in SCHEMA_RELS:
            with self.subTest(schema=relative):
                self.assertEqual(self.role_count_bounds(relative), (11, 11))
                self.assertEqual(len(self.enum_ids(relative)), 11)

    def test_add_role_retunes_the_role_count_in_every_schema(self) -> None:
        # The growth direction fails the same way: thirteen roles under
        # maxItems 12 is a schema that rejects its own corpus.
        self.assertEqual(self.run_script().returncode, 0)
        self.add_role_to_module(ADDED_ROLE)
        source = self.sandbox / CODEX_AGENT_DIR_REL / f"{ADDED_ROLE}.toml"
        source.write_text(
            f'name = "{ADDED_ROLE}"\nsandbox_mode = "read-only"\n', encoding="utf-8"
        )
        result = self.run_script("--add-role", ADDED_ROLE, "--kind", "codex_toml")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(self.read_json(MANIFEST_REL)["roles"]), 13)
        for relative in SCHEMA_RELS:
            with self.subTest(schema=relative):
                self.assertEqual(self.role_count_bounds(relative), (13, 13))
                self.assertEqual(len(self.enum_ids(relative)), 13)

    def test_add_role_refuses_a_kind_the_governed_order_contradicts(self) -> None:
        self.assertEqual(self.run_script().returncode, 0)
        module_bytes = self.read_bytes(MODULE_REL)
        self.drop_role_from_module(ROUND_TRIP_ROLE)
        self.assertEqual(self.run_script("--remove-role", ROUND_TRIP_ROLE).returncode, 0)
        (self.sandbox / MODULE_REL).write_bytes(module_bytes)
        before = self.snapshot()
        result = self.run_script(
            "--add-role", ROUND_TRIP_ROLE, "--kind", "governed_markdown_contract"
        )
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(self.snapshot(), before)


class RebaselineScriptShapeTests(unittest.TestCase):
    """The script ships as a runnable sibling of the other Layer 6 entry points."""

    def test_script_is_executable_with_a_python3_shebang(self) -> None:
        self.assertTrue(SCRIPT_PATH.is_file(), f"missing implementation: {SCRIPT_REL}")
        first_line = SCRIPT_PATH.read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(first_line, "#!/usr/bin/env python3")
        self.assertTrue(SCRIPT_PATH.stat().st_mode & 0o111, "script must be executable")

    def test_script_is_registered_in_the_suite_manifest(self) -> None:
        manifest = json.loads(
            (TEST_ROOT / "suite-manifest.json").read_text(encoding="utf-8")
        )
        unit_layer = next(layer for layer in manifest["layers"] if layer["id"] == "4")
        paths = {script["path"] for script in unit_layer["scripts"]}
        self.assertIn("tests/speckit-pro/unit/test-rebaseline-corpus.py", paths)


TEST_CASES = (
    RebaselineWriteTests,
    RebaselineCheckTests,
    RebaselineMembershipTests,
    RebaselineScriptShapeTests,
)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in TEST_CASES:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


if __name__ == "__main__":
    raise SystemExit(run_counted(build_suite(), label="test-rebaseline-corpus"))
