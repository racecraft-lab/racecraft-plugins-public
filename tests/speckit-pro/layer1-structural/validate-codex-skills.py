#!/usr/bin/env python3
"""Structural validation for Codex skill directories (port of validate-codex-skills.sh).

XPLAT-010 count-parity port (T042, US2). Python 3.11+ standard library only.
Checks the expected ``speckit-pro/codex-skills/<name>/SKILL.md`` files for
frontmatter shape, metadata limits, body length, Codex-specific regression
guards, sidecar policy metadata, and source-artifact mappings. Every former
``assert_*``/``_pass``/``_fail`` execution maps to one counted ``subTest`` unit;
names reproduced verbatim via ``subTest(msg=...)`` for a 1:1 baseline match.

Baseline: ``tests/speckit-pro/parity/bash-to-python/validate-codex-skills-baseline.txt``
(TOTAL: 161).
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LIB_DIR = REPO_ROOT / "tests" / "speckit-pro" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))
from test_result import run_counted  # noqa: E402
from speckit_pro_runner.helpers.registry import MUTATION_HELPERS  # noqa: E402

CODEX_SKILLS_DIR = PLUGIN_ROOT / "codex-skills"

# Canonical skill list. Keep in sync with the source-artifact mapping below.
SKILLS = (
    "speckit-archive-cleanup",
    "speckit-autopilot",
    "speckit-coach",
    "speckit-scaffold-spec",
    "speckit-status",
    "speckit-resolve-pr",
    "install",
    "speckit-install",
    "speckit-upgrade",
    "grill-me",
    "speckit-prd",
)
COLLISION_GUARD_SKILLS = (
    "speckit-archive-cleanup",
    "speckit-autopilot",
    "speckit-coach",
    "grill-me",
    "speckit-prd",
)

CC_ONLY_KEYS = ("user-invocable", "disable-model-invocation", "license", "argument-hint")
CLAUDE_ONLY_RUNTIME_RE = re.compile(
    r"TaskCreate|TaskUpdate|Agent\(|Bash\(|Opus-class|Opus 4\.6|/model opus|"
    r"/effort max|/speckit[.:]|run /<command>|general-purpose agent"
)
ALLOW_IMPLICIT_RE = re.compile(r"^[ \t]*allow_implicit_invocation:[ \t]*(true|false)[ \t]*$")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _frontmatter(lines: list[str]) -> str:
    out: list[str] = []
    fences = 0
    for line in lines:
        if line == "---":
            fences += 1
            if fences == 1:
                continue
            if fences == 2:
                break
        elif fences == 1:
            out.append(line)
    return "\n".join(out)


def _body(lines: list[str]) -> str:
    out: list[str] = []
    fences = 0
    found = False
    for line in lines:
        if line == "---":
            fences += 1
            if fences == 2:
                found = True
                continue
        if found:
            out.append(line)
    return "\n".join(out)


def _allow_implicit_values(yaml_content: str) -> list[str]:
    values: list[str] = []
    for line in yaml_content.splitlines():
        match = ALLOW_IMPLICIT_RE.match(line)
        if match:
            values.append(match.group(1))
    return values


def _source_artifact_exists(skill: str) -> bool:
    if skill == "install":
        return True
    return (PLUGIN_ROOT / "skills" / skill / "SKILL.md").is_file()


class ValidateCodexSkills(unittest.TestCase):
    def test_codex_skill_selection_collision_guards(self) -> None:
        for skill in COLLISION_GUARD_SKILLS:
            shared_skill_file = PLUGIN_ROOT / "skills" / skill / "SKILL.md"
            codex_skill_file = CODEX_SKILLS_DIR / skill / "SKILL.md"

            both_exist = shared_skill_file.is_file() and codex_skill_file.is_file()
            with self.subTest(msg=f"{skill}: shared and Codex variants both exist"):
                self.assertTrue(
                    both_exist,
                    f"expected both {shared_skill_file} and {codex_skill_file}",
                )
            if not both_exist:
                continue

            shared_content = shared_skill_file.read_text(encoding="utf-8")

            with self.subTest(msg=f"{skill}: shared variant redirects when selected by Codex"):
                self.assertIn("Codex Skill-Selection Guard", shared_content)

            with self.subTest(msg=f"{skill}: shared guard names the Codex variant path"):
                self.assertIn(f"../../codex-skills/{skill}/SKILL.md", shared_content)

            with self.subTest(msg=f"{skill}: shared guard forbids Claude instructions in Codex"):
                self.assertIn("Do not follow the Claude-oriented instructions below in Codex", shared_content)

    def test_codex_skills(self) -> None:
        for skill in SKILLS:
            skill_dir = CODEX_SKILLS_DIR / skill
            skill_file = skill_dir / "SKILL.md"

            with self.subTest(msg=f"{skill}: SKILL.md exists"):
                self.assertTrue(skill_file.is_file(), f"file not found: {skill_file}")
            if not skill_file.is_file():
                continue

            content = skill_file.read_text(encoding="utf-8")
            lines = content.splitlines()
            first_line = lines[0] if lines else ""

            with self.subTest(msg=f"{skill}: YAML frontmatter present (starts with ---)"):
                self.assertEqual("---", first_line, "first line must be ---")

            with self.subTest(msg=f"{skill}: has closing ---"):
                fence_count = sum(1 for line in lines if line == "---")
                self.assertGreaterEqual(fence_count, 2, f"expected at least 2 '---' lines, found {fence_count}")

            frontmatter = _frontmatter(lines)

            with self.subTest(msg=f"{skill}: has name: field"):
                self.assertIn("name:", frontmatter)

            with self.subTest(msg=f"{skill}: has description: field"):
                self.assertIn("description:", frontmatter)

            with self.subTest(msg=f"{skill}: no Claude Code-only frontmatter keys"):
                bad_keys = [key for key in CC_ONLY_KEYS if re.search(rf"^{re.escape(key)}:", frontmatter, re.MULTILINE)]
                self.assertEqual([], bad_keys, "Claude Code-only keys found:" + "".join(f" {key}" for key in bad_keys))

            with self.subTest(msg=f"{skill}: agents/openai.yaml sidecar exists"):
                self.assertTrue((skill_dir / "agents" / "openai.yaml").is_file(), f"file not found: {skill_dir / 'agents' / 'openai.yaml'}")

            if skill == "speckit-scaffold-spec":
                sidecar_content = _read(skill_dir / "agents" / "openai.yaml")

                with self.subTest(msg="speckit-scaffold-spec: Codex picker metadata uses scaffold naming"):
                    self.assertTrue(
                        'display_name: "SpecKit Scaffold Spec"' in sidecar_content
                        and 'default_prompt: "Scaffold a SPEC-ID from the technical roadmap for SpecKit autopilot"'
                        in sidecar_content
                        and "SpecKit Setup" not in sidecar_content
                        and "Set up a SPEC-ID" not in sidecar_content,
                        "expected scaffold naming in codex-skills/speckit-scaffold-spec/agents/openai.yaml",
                    )

                with self.subTest(msg="speckit-scaffold-spec: Codex skill heading uses scaffold naming"):
                    self.assertTrue(
                        re.search(r"^# SpecKit Scaffold Spec$", content, re.MULTILINE) is not None
                        and re.search(r"^# SpecKit Setup$", content, re.MULTILINE) is None,
                        "expected '# SpecKit Scaffold Spec' heading in codex-skills/speckit-scaffold-spec/SKILL.md",
                    )

            body = _body(lines)
            with self.subTest(msg=f"{skill}: body word count between 500 and 8000"):
                word_count = len(body.split())
                self.assertGreaterEqual(word_count, 500, f"body is {word_count} words (need 500-8000)")
                self.assertLessEqual(word_count, 8000, f"body is {word_count} words (need 500-8000)")

            if skill == "speckit-scaffold-spec":
                with self.subTest(msg="speckit-scaffold-spec: Codex Grill Me requires native picker config"):
                    self.assertTrue(
                        "picker-first HITL guard" in body
                        and "request_user_input" in body
                        and "default_mode_request_user_input" in body
                        and "Do not ask the Grill Me question as a normal assistant" in body
                        and "If `request_user_input` is absent" in body
                        and "unavailable, stop setup" in body
                        and "codex features enable default_mode_request_user_input" in body,
                        "expected scaffold to require native request_user_input config and forbid Markdown fallback",
                    )

            if skill == "grill-me":
                protocol_content = _read(skill_dir / "references" / "interview-protocol.md")

                with self.subTest(msg="grill-me: Codex picker-first guard requires default-mode request_user_input"):
                    self.assertTrue(
                        "Codex picker-first HITL guard" in body
                        and "Use `request_user_input` whenever it is present in the active tool" in body
                        and "default_mode_request_user_input" in body
                        and "Do not ask a" in body
                        and "Grill Me question as a normal assistant message" in body
                        and "stop instead of asking in Markdown/free-text" in body
                        and "Never end a turn with a Markdown question" in protocol_content,
                        "expected grill-me to require default-mode request_user_input and forbid Markdown fallback",
                    )

            if skill == "speckit-autopilot":
                self._check_autopilot_skill(skill_dir, body)

            self._check_allow_implicit_invocation_policy(skill, skill_dir)

            with self.subTest(msg=f"{skill}: corresponding source artifact exists"):
                self.assertTrue(
                    _source_artifact_exists(skill),
                    f"corresponding Claude skill not found at skills/{skill}/SKILL.md",
                )

            if skill == "speckit-scaffold-spec":
                with self.subTest(
                    msg="speckit-scaffold-spec: referenced workflow template exists (skills/speckit-coach/templates/workflow-template.md)"
                ):
                    self.assertTrue(
                        (PLUGIN_ROOT / "skills" / "speckit-coach" / "templates" / "workflow-template.md").is_file(),
                        f"file not found: {PLUGIN_ROOT / 'skills' / 'speckit-coach' / 'templates' / 'workflow-template.md'}",
                    )

            if skill == "install":
                with self.subTest(msg="install: installer helper is documented"):
                    entry = MUTATION_HELPERS["install-codex-agents"]
                    self.assertTrue(
                        "install-codex-agents" in body
                        and "dry_run" in body
                        and "apply" in body
                        and "verified" in body
                        and entry.promotion_status == "golden_only"
                        and bool(entry.authoritative_command),
                        "expected a promoted, fixture-backed install-codex-agents dry-run/apply contract",
                    )

    def _check_autopilot_skill(self, skill_dir: Path, body: str) -> None:
        runtime_doc = body
        for ref_file in (
            skill_dir / "references" / "phase-execution-codex.md",
            skill_dir / "references" / "post-implementation-codex.md",
            skill_dir / "references" / "error-recovery-codex.md",
        ):
            if ref_file.is_file():
                runtime_doc = f"{runtime_doc}\n{ref_file.read_text(encoding='utf-8')}"

        with self.subTest(msg="speckit-autopilot: requires update_plan as the progress contract"):
            self.assertIn("update_plan", runtime_doc)

        with self.subTest(msg="speckit-autopilot: requires durable autopilot-state.json persistence"):
            self.assertIn("autopilot-state.json", runtime_doc)

        with self.subTest(msg="speckit-autopilot: names Codex-native delegation tools"):
            self.assertTrue(
                "spawn_agent" in runtime_doc and "wait_agent" in runtime_doc,
                "expected both spawn_agent and wait_agent in the Codex autopilot skill",
            )

        with self.subTest(msg="speckit-autopilot: maps hosted and local Codex follow-up tools"):
            self.assertTrue(
                "followup_task" in runtime_doc
                and "send_message" in runtime_doc
                and "resume_agent" in runtime_doc
                and "send_input" in runtime_doc,
                "expected hosted followup_task/send_message plus local send_input and resume-then-send_input handling",
            )

        with self.subTest(msg="speckit-autopilot: adapts agent cleanup to the exposed Codex surface"):
            self.assertTrue(
                "absence of `close_agent` is NOT" in runtime_doc
                and "prerequisite failure" in runtime_doc
                and "only when `close_agent` is exposed" in runtime_doc
                and "interrupt_agent" in runtime_doc
                and "list_agents" in runtime_doc
                and "terminal status is corroboration or recovery evidence only" in runtime_doc
                and "A `wait_agent` timeout is one bounded mailbox poll" in runtime_doc
                and "`close_agent` is REQUIRED" not in runtime_doc,
                "expected capability-aware hosted/local lifecycle handling without a close_agent hard requirement",
            )

        with self.subTest(msg="speckit-autopilot: validates a single in_progress item before phase execution"):
            self.assertIn("Exactly one plan item is `in_progress`", body)

        with self.subTest(msg="speckit-autopilot: requires all canonical phase families before execution"):
            self.assertTrue(
                "phase family coverage is mandatory" in runtime_doc
                and "Phase 7: Implement - Pending task decomposition" in runtime_doc
                and "Post: Doctor Extension Check" in runtime_doc
                and "Post: Retrospective" in runtime_doc,
                "expected all-phase coverage, Phase 7 placeholder, and the canonical Post item list "
                "(Doctor Extension Check -> Retrospective) in the Codex autopilot skill",
            )

        with self.subTest(msg="speckit-autopilot: documents canonical PHASES order"):
            self.assertIn("PHASES = [specify, clarify, plan, checklist, tasks, analyze, implement]", runtime_doc)

        with self.subTest(msg="speckit-autopilot: prevents from-phase from dropping later phases"):
            self.assertIn("`--from-phase` changes only the starting index", runtime_doc)

        with self.subTest(msg="speckit-autopilot: requires concrete Phase 7 tasks after G5"):
            self.assertTrue(
                "After the Tasks phase and G5 pass" in runtime_doc
                and "the placeholder no longer exists" in runtime_doc
                and "each concrete Phase 7 item names task IDs" in runtime_doc,
                "expected G5 Phase 7 placeholder replacement guardrails",
            )

        with self.subTest(msg="speckit-autopilot: resumes into Post before reporting complete"):
            self.assertTrue(
                "all seven SDD phases are complete" in runtime_doc
                and "items are missing, pending, or in progress" in runtime_doc
                and "execute Step 3" in runtime_doc,
                "expected all-phases-complete resume to continue into Post",
            )

        with self.subTest(msg="speckit-autopilot: blocks final answers while Post items remain incomplete"):
            self.assertTrue(
                "Pre-final completion audit" in runtime_doc
                and "MUST NOT send a final response" in runtime_doc
                and "any Post item is pending, in_progress, or missing" in runtime_doc
                and "Post: Retrospective" in runtime_doc,
                "expected a pre-final guard that prevents stopping after implementation while post items remain incomplete",
            )

        with self.subTest(msg="speckit-autopilot: documents skill-local agents/openai.yaml metadata"):
            self.assertIn("agents/openai.yaml", body)

        with self.subTest(msg="speckit-autopilot: validates installed Codex subagent paths"):
            self.assertTrue(
                ".codex/agents/" in body and "~/.codex/agents/" in body,
                "expected both project and user Codex subagent paths in the autopilot skill",
            )

        with self.subTest(msg="speckit-autopilot: fails closed to the install skill when subagents are missing"):
            prerequisites = _read(skill_dir / "references" / "prerequisites-codex.md")
            self.assertTrue(
                "$install" in body
                and "$install" in prerequisites
                and "install-codex-agents" in prerequisites
                and "dry_run" in prerequisites
                and "validate-agent-install" not in prerequisites
                and "--autoheal" not in prerequisites,
                "expected read-only installer dry-run preflight and install/restart fail-closed guidance",
            )

        with self.subTest(msg="speckit-autopilot: documents the optional Spark helper"):
            self.assertIn("autopilot-fast-helper", body)

        with self.subTest(msg="speckit-autopilot: keeps the Spark helper advisory and parent-only"):
            self.assertTrue(
                "Only the parent orchestrator may call this helper" in body
                and "latency optimization, not a dependency" in body,
                "expected parent-only and optional guardrails for autopilot-fast-helper",
            )

        with self.subTest(msg="speckit-autopilot: does not bundle skill-local TOML subagents"):
            agents_dir = skill_dir / "agents"
            bundled_count = len(list(agents_dir.glob("*.toml"))) if agents_dir.is_dir() else 0
            self.assertEqual("0", str(bundled_count), "expected no bundled custom-agent templates in speckit-autopilot/agents")

        with self.subTest(msg="speckit-autopilot: excludes Claude-only runtime primitives"):
            self.assertIsNone(
                CLAUDE_ONLY_RUNTIME_RE.search(runtime_doc),
                "found Claude-only primitive or runtime guidance in Codex autopilot skill",
            )

        with self.subTest(msg="speckit-autopilot: Codex-specific references exist"):
            self.assertTrue((skill_dir / "references" / "phase-execution-codex.md").is_file())

        with self.subTest(msg="speckit-autopilot: Codex post-implementation reference exists"):
            self.assertTrue((skill_dir / "references" / "post-implementation-codex.md").is_file())

        with self.subTest(msg="speckit-autopilot: Codex SKILL.md names the plan-phase estimator helper"):
            self.assertIn("estimate-reviewable-loc", body)

        with self.subTest(msg="speckit-autopilot: Codex SKILL.md carries the three-value status vocab"):
            self.assertIn("`pass` / `over_budget` / `not_estimated`", body)

        phase_exec = _read(skill_dir / "references" / "phase-execution-codex.md")

        with self.subTest(msg="speckit-autopilot: phase-execution-codex.md names the plan-phase estimator helper"):
            self.assertIn("estimate-reviewable-loc", phase_exec)

        with self.subTest(msg="speckit-autopilot: phase-execution-codex.md documents the over_budget status"):
            self.assertIn("over_budget", phase_exec)

        with self.subTest(msg="speckit-autopilot: phase-execution-codex.md documents the not_estimated status"):
            self.assertIn("not_estimated", phase_exec)

    def _check_allow_implicit_invocation_policy(self, skill: str, skill_dir: Path) -> None:
        sidecar = skill_dir / "agents" / "openai.yaml"
        with self.subTest(msg=f"{skill}: agents/openai.yaml allow_implicit_invocation policy"):
            if not sidecar.is_file():
                self.fail("agents/openai.yaml not found; skipping policy check")

            values = _allow_implicit_values(sidecar.read_text(encoding="utf-8"))
            if len(values) != 1:
                self.fail("agents/openai.yaml must declare exactly one anchored allow_implicit_invocation policy")
            policy_value = values[0]

            if skill == "speckit-scaffold-spec":
                self.assertEqual(
                    "true",
                    policy_value,
                    "scaffold skill must have allow_implicit_invocation: true for Codex discovery",
                )
            elif skill in (
                "speckit-archive-cleanup",
                "speckit-autopilot",
                "speckit-resolve-pr",
                "install",
                "speckit-install",
                "speckit-upgrade",
                "grill-me",
                "speckit-prd",
            ):
                self.assertEqual("false", policy_value, "mutation-heavy skill must have allow_implicit_invocation: false")
            elif skill in ("speckit-coach", "speckit-status"):
                self.assertEqual("true", policy_value, "read-only skill must have allow_implicit_invocation: true")
            else:
                self.fail(f"no implicit-invocation policy expectation defined for '{skill}'; update validate-codex-skills.sh")


def build_suite() -> unittest.TestSuite:
    return unittest.defaultTestLoader.loadTestsFromTestCase(ValidateCodexSkills)


def main() -> int:
    return run_counted(build_suite(), label="validate-codex-skills")


if __name__ == "__main__":
    raise SystemExit(main())
