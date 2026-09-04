#!/usr/bin/env python3
"""Validate generated payload conformance."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402

CLAUDE_ROOT = REPO_ROOT / "dist" / "claude" / "speckit-pro"
CODEX_ROOT = REPO_ROOT / "dist" / "codex" / "speckit-pro"

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
BLOCK_SCALAR_RE = re.compile(r"^[>|][-+]?[0-9]*$")
POINTER_KEYS = ("skills", "hooks", "mcpServers", "apps", "agents", "commands", "lsp")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _first_line(path: Path) -> str:
    text = _read_text(path)
    return text.splitlines()[0] if text.splitlines() else ""


def repo_rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_or_none(path: Path) -> Any | None:
    try:
        return _load_json(path)
    except (OSError, json.JSONDecodeError):
        return None


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def fm_value(path: Path, key: str) -> str:
    """Return a leading-frontmatter top-level scalar, mirroring the bash awk helper."""
    lines = _read_text(path).splitlines()
    if not lines or lines[0] != "---":
        return ""
    for line in lines[1:]:
        if line == "---":
            return ""
        if line.startswith(f"{key}:"):
            value = line[len(key) + 1 :].strip()
            if BLOCK_SCALAR_RE.fullmatch(value):
                return "__BLOCK__"
            return value
    return ""


def fm_has_key(path: Path, key: str) -> bool:
    """Return true iff leading frontmatter declares a top-level ``key:`` line."""
    lines = _read_text(path).splitlines()
    if not lines or lines[0] != "---":
        return False
    for line in lines[1:]:
        if line == "---":
            return False
        if line.startswith(f"{key}:"):
            return True
    return False


class ValidatePayloadConformance(unittest.TestCase):
    def assert_md_frontmatter(self, label: str, item: str, path: Path) -> None:
        with self.subTest(msg=f"[{label}/{item}] opens with a '---' frontmatter fence"):
            self.assertEqual("---", _first_line(path), f"{path} does not begin with a YAML frontmatter fence")
        if _first_line(path) != "---":
            return

        name = _strip_quotes(fm_value(path, "name"))
        with self.subTest(msg=f"[{label}/{item}] frontmatter has a non-empty 'name' (required)"):
            self.assertTrue(name, f"{path} frontmatter is missing 'name'")

        with self.subTest(msg=f"[{label}/{item}] frontmatter 'name' is kebab-case ('{name}')"):
            self.assertRegex(name, NAME_RE, f"{path} 'name' ('{name}') is not lowercase kebab-case")

        desc = fm_value(path, "description")
        with self.subTest(msg=f"[{label}/{item}] frontmatter has a non-empty 'description' (required)"):
            self.assertTrue(desc, f"{path} frontmatter is missing 'description'")

    def assert_no_forbidden_agent_fields(self, label: str, item: str, path: Path) -> None:
        for key in ("permissionMode", "hooks", "mcpServers"):
            with self.subTest(msg=f"[{label}/{item}] does NOT declare plugin-unsupported '{key}' (plugins-reference)"):
                self.assertFalse(
                    fm_has_key(path, key),
                    f"{path} declares '{key}' - not supported for plugin-shipped agents per official docs",
                )

    def assert_toml_agent(self, label: str, path: Path) -> None:
        item = path.stem
        text = _read_text(path)
        with self.subTest(msg=f"[{label}/{item}] built agent .toml has a 'name =' key"):
            self.assertRegex(text, re.compile(r"^name\s*=", re.MULTILINE), f"{path} is missing a top-level 'name =' key")
        with self.subTest(msg=f"[{label}/{item}] built agent .toml has a 'description =' key"):
            self.assertRegex(
                text,
                re.compile(r"^description\s*=", re.MULTILINE),
                f"{path} is missing a top-level 'description =' key",
            )

    def assert_hooks_json(self, label: str, path: Path) -> None:
        with self.subTest(msg=f"[{label}] hooks file exists ({repo_rel(path)})"):
            self.assertTrue(path.is_file(), f"missing hooks file: {path}")
        if not path.is_file():
            return

        data: Any | None = None
        with self.subTest(msg=f"[{label}] hooks file is valid JSON"):
            try:
                data = _load_json(path)
            except json.JSONDecodeError as exc:
                self.fail(f"invalid JSON: {path}: {exc}")
        if data is None:
            return

        with self.subTest(msg=f"[{label}] hooks file has a top-level 'hooks' object"):
            self.assertTrue(
                isinstance(data, dict) and isinstance(data.get("hooks"), dict),
                f"{path} has no top-level 'hooks' object",
            )

    def assert_pointers_resolve(self, label: str, manifest: Path, root: Path) -> None:
        data = _json_or_none(manifest)
        for key in POINTER_KEYS:
            value = data.get(key) if isinstance(data, dict) else None
            if not isinstance(value, str) or not value:
                continue
            rel = value.removeprefix("./").removesuffix("/")
            with self.subTest(msg=f"[{label}] manifest '{key}' pointer resolves in payload ('{value}')"):
                self.assertTrue((root / rel).exists(), f"manifest '{key}' ('{value}') does not resolve to a path under the payload")

    def test_payload_conformance(self) -> None:
        self.validate_claude_payload()
        self.validate_codex_payload()

    def validate_claude_payload(self) -> None:
        with self.subTest(msg=f"[claude] built payload root exists ({repo_rel(CLAUDE_ROOT)})"):
            self.assertTrue(CLAUDE_ROOT.is_dir(), "Claude payload missing - run python3 scripts/build-plugin-payloads.py")
        if not CLAUDE_ROOT.is_dir():
            return

        manifest = CLAUDE_ROOT / ".claude-plugin" / "plugin.json"
        with self.subTest(msg="[claude] manifest exists at .claude-plugin/plugin.json"):
            self.assertTrue(manifest.is_file(), f"missing {manifest}")

        manifest_data: Any | None = None
        with self.subTest(msg="[claude] manifest is valid JSON"):
            try:
                manifest_data = _load_json(manifest)
            except (OSError, json.JSONDecodeError) as exc:
                self.fail(f"invalid JSON: {manifest}: {exc}")

        with self.subTest(msg="[claude] manifest has the required 'name' (string, non-empty)"):
            cname = manifest_data.get("name") if isinstance(manifest_data, dict) else None
            self.assertTrue(isinstance(cname, str) and cname, "manifest 'name' missing or not a string")

        with self.subTest(msg="[claude] manifest 'version', if present, is a string"):
            ok = isinstance(manifest_data, dict) and (
                "version" not in manifest_data or isinstance(manifest_data.get("version"), str)
            )
            self.assertTrue(ok, "manifest 'version' present but not a string")

        self.assert_pointers_resolve("claude", manifest, CLAUDE_ROOT)

        skills_dir = CLAUDE_ROOT / "skills"
        with self.subTest(msg="[claude] skills/ directory exists in the payload"):
            self.assertTrue(skills_dir.is_dir(), f"missing {skills_dir}")
        claude_skills = sorted((p for p in skills_dir.glob("*/SKILL.md") if p.is_file()), key=lambda p: p.as_posix())
        with self.subTest(msg="[claude] at least one skills/*/SKILL.md is present"):
            self.assertTrue(claude_skills, f"no SKILL.md under {skills_dir}/*/ - refusing to pass vacuously")
        if not claude_skills:
            return
        for path in claude_skills:
            self.assert_md_frontmatter("claude-skill", path.parent.name, path)

        agents_dir = CLAUDE_ROOT / "agents"
        with self.subTest(msg="[claude] agents/ directory exists in the payload"):
            self.assertTrue(agents_dir.is_dir(), f"missing {agents_dir}")
        claude_agents = sorted((p for p in agents_dir.glob("*.md") if p.is_file()), key=lambda p: p.as_posix())
        with self.subTest(msg="[claude] at least one agents/*.md is present"):
            self.assertTrue(claude_agents, f"no agents/*.md under {agents_dir} - refusing to pass vacuously")
        if not claude_agents:
            return
        for path in claude_agents:
            item = path.stem
            self.assert_md_frontmatter("claude-agent", item, path)
            self.assert_no_forbidden_agent_fields("claude-agent", item, path)

        self.assert_hooks_json("claude", CLAUDE_ROOT / "hooks" / "hooks.json")

    def validate_codex_payload(self) -> None:
        with self.subTest(msg=f"[codex] built payload root exists ({repo_rel(CODEX_ROOT)})"):
            self.assertTrue(CODEX_ROOT.is_dir(), "Codex payload missing - run python3 scripts/build-plugin-payloads.py")
        if not CODEX_ROOT.is_dir():
            return

        manifest = CODEX_ROOT / ".codex-plugin" / "plugin.json"
        with self.subTest(msg="[codex] manifest exists at .codex-plugin/plugin.json"):
            self.assertTrue(manifest.is_file(), f"missing {manifest}")

        manifest_data: Any | None = None
        with self.subTest(msg="[codex] manifest is valid JSON"):
            try:
                manifest_data = _load_json(manifest)
            except (OSError, json.JSONDecodeError) as exc:
                self.fail(f"invalid JSON: {manifest}: {exc}")

        xname = manifest_data.get("name") if isinstance(manifest_data, dict) and isinstance(manifest_data.get("name"), str) else ""
        with self.subTest(msg="[codex] manifest 'name' is present, a string, and kebab-case"):
            self.assertTrue(xname and NAME_RE.fullmatch(xname), f"manifest 'name' missing/not-a-string/not-kebab-case ('{xname}')")

        xver = manifest_data.get("version") if isinstance(manifest_data, dict) and isinstance(manifest_data.get("version"), str) else ""
        with self.subTest(msg="[codex] manifest 'version' is present and non-empty (semver)"):
            self.assertTrue(xver, "manifest 'version' missing or not a string")

        xdesc = manifest_data.get("description") if isinstance(manifest_data, dict) and isinstance(manifest_data.get("description"), str) else ""
        with self.subTest(msg="[codex] manifest 'description' is present and non-empty"):
            self.assertTrue(xdesc, "manifest 'description' missing or empty")

        codex_plugin_dir = CODEX_ROOT / ".codex-plugin"
        expected_plugin_files = {"plugin.json", "sweep-mcp.json"}
        actual_plugin_files = (
            {path.name for path in codex_plugin_dir.iterdir() if path.is_file()}
            if codex_plugin_dir.is_dir()
            else set()
        )
        with self.subTest(msg="[codex] .codex-plugin/ contains only the manifest and sweep broker MCP config"):
            self.assertEqual(
                expected_plugin_files,
                actual_plugin_files,
                ".codex-plugin/ must contain exactly plugin.json and sweep-mcp.json",
            )

        self.assert_pointers_resolve("codex", manifest, CODEX_ROOT)

        skills_dir = CODEX_ROOT / "skills"
        with self.subTest(msg="[codex] skills/ directory exists at the plugin root"):
            self.assertTrue(skills_dir.is_dir(), f"missing {skills_dir}")
        codex_skills = sorted((p for p in skills_dir.glob("*/SKILL.md") if p.is_file()), key=lambda p: p.as_posix())
        with self.subTest(msg="[codex] at least one skills/*/SKILL.md is present"):
            self.assertTrue(codex_skills, f"no SKILL.md under {skills_dir}/*/ - refusing to pass vacuously")
        if not codex_skills:
            return
        for path in codex_skills:
            self.assert_md_frontmatter("codex-skill", path.parent.name, path)

        agents_dir = CODEX_ROOT / "codex-agents"
        with self.subTest(msg="[codex] codex-agents/ directory exists at the plugin root"):
            self.assertTrue(agents_dir.is_dir(), f"missing {agents_dir}")
        codex_agents = sorted((p for p in agents_dir.glob("*.toml") if p.is_file()), key=lambda p: p.as_posix())
        with self.subTest(msg="[codex] at least one codex-agents/*.toml is present"):
            self.assertTrue(codex_agents, f"no codex-agents/*.toml under {agents_dir} - refusing to pass vacuously")
        if not codex_agents:
            return
        for path in codex_agents:
            self.assert_toml_agent("codex-agent", path)

        self.assert_hooks_json("codex", CODEX_ROOT / "codex-hooks.json")


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidatePayloadConformance)


def main() -> int:
    return run_counted(build_suite(), label="validate-payload-conformance")


if __name__ == "__main__":
    raise SystemExit(main())
