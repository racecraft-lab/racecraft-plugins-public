#!/usr/bin/env python3
"""Layer-4 regression tests for Claude/Codex eval runner skill selection.

Port of ``test-eval-runner-skill-selection.sh`` (XPLAT-010 PR9 T084). The
predecessor executes 13 assertions; the count-parity baseline is pinned at
``tests/speckit-pro/parity/bash-to-python/test-eval-runner-skill-selection-baseline.txt``
(TOTAL: 13).
"""

from __future__ import annotations

import contextlib
import inspect
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
TESTS_ROOT = REPO_ROOT / "tests" / "speckit-pro"
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
LAYER3_FUNCTIONAL_ROOT = TESTS_ROOT / "layer3-functional"
FUNCTIONAL_SCRIPT = TESTS_ROOT / "layer3-functional" / "run-functional-evals.py"
TRIGGER_SCRIPT = TESTS_ROOT / "layer2-trigger" / "run-trigger-evals.py"
CODEX_FUNCTIONAL_SCRIPT = TESTS_ROOT / "layer3-functional" / "run-functional-evals-codex.py"
CODEX_TRIGGER_SCRIPT = TESTS_ROOT / "layer2-trigger" / "run-trigger-evals-codex.py"
BASELINE = TESTS_ROOT / "parity" / "bash-to-python" / "test-eval-runner-skill-selection-baseline.txt"
CODEX_SKILLS = ("speckit-scaffold-spec", "speckit-status", "speckit-resolve-pr", "install")
LAYER3_CONTRACT_ROOTS = (
    TESTS_ROOT / "layer3-functional" / "evals",
    TESTS_ROOT / "layer3-functional" / "codex-evals",
)
LAYER8_ROOT = TESTS_ROOT / "layer8-parity"

if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))
if str(LAYER3_FUNCTIONAL_ROOT) not in sys.path:
    sys.path.insert(0, str(LAYER3_FUNCTIONAL_ROOT))
from preview_helpers import eval_count, print_eval_prompts  # noqa: E402
from speckit_pro_runner.helpers.pr_emission import generate_pr_body  # noqa: E402
from speckit_pro_runner.helpers.registry import HELPERS, MUTATION_HELPERS  # noqa: E402

SHIPPED_RUNTIME_CONTRACTS = (
    PLUGIN_ROOT / "skills" / "speckit-upgrade" / "SKILL.md",
    PLUGIN_ROOT / "codex-skills" / "speckit-upgrade" / "SKILL.md",
    PLUGIN_ROOT / "skills" / "speckit-scaffold-spec" / "SKILL.md",
    PLUGIN_ROOT / "codex-skills" / "speckit-scaffold-spec" / "SKILL.md",
    PLUGIN_ROOT / "skills" / "speckit-autopilot" / "SKILL.md",
    PLUGIN_ROOT / "codex-skills" / "speckit-autopilot" / "SKILL.md",
    PLUGIN_ROOT / "skills" / "speckit-autopilot" / "references" / "phase-execution.md",
    PLUGIN_ROOT / "codex-skills" / "speckit-autopilot" / "references" / "phase-execution-codex.md",
    PLUGIN_ROOT / "skills" / "speckit-autopilot" / "references" / "post-implementation.md",
    PLUGIN_ROOT / "codex-skills" / "speckit-autopilot" / "references" / "post-implementation-codex.md",
    PLUGIN_ROOT / "skills" / "speckit-autopilot" / "templates" / "pr-description-template.md",
)
EXPECTED_DEFERRED_HELPERS = frozenset(
    {
        "ensure-reviewability-preset",
        "migrate-structure",
        "relocate-process-artifacts",
        "restack",
    }
)
EXPECTED_ACTIVE_PACKET_HELPERS = frozenset({"pr-packet-output", "validate-pr-packet-write"})
PACKET_PATH_CONTRACT = "specs/<feature>/.process/pr-packets/<packet-id>.json"
SAFE_NEGATION_MARKERS = (
    "do not",
    "does not",
    "must not",
    "never",
    "no runner command",
    "not active",
    "unavailable",
    "out of scope",
    "is deferred",
    "are deferred",
    "registered as deferred",
    "registered but deferred",
    "without claiming",
)

RETIRED_REPOSITORY_HELPERS = frozenset(
    {
        "aggregate-crl.sh",
        "atomicity-route.sh",
        "check-prerequisites.sh",
        "confidence-gate.sh",
        "count-markers.sh",
        "create-new-feature.sh",
        "detect-commands.sh",
        "detect-presets.sh",
        "detect-stack-manager.sh",
        "estimate-reviewable-loc.sh",
        "estimate-spec-size.sh",
        "final-reviewability-backstop.sh",
        "generate-pr-body.sh",
        "generate-spec-index.sh",
        "generate-uat-skeleton.sh",
        "install-curated-set.sh",
        "migrate-structure.sh",
        "multi-pr-emission.sh",
        "o5-topology.sh",
        "parse-consensus-categories.sh",
        "plan-layers.sh",
        "project-fixup.sh",
        "relocate-process-artifacts.sh",
        "resolve-confidence-mode.sh",
        "restack.sh",
        "reviewability-gate.sh",
        "validate-agent-install.sh",
        "validate-gate.sh",
        "validate-pr-packet.sh",
        "validate-pr-workflow-contract.sh",
        "validate-uat-runbook.sh",
    }
)
RETIRED_HELPER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_-])(" + "|".join(re.escape(name) for name in sorted(RETIRED_REPOSITORY_HELPERS)) + r")(?![A-Za-z0-9_-])"
)

# These evals intentionally describe legacy PROCESS relocation. Retired paths
# are allowed only as negative assertions in expected contract fields.
LAYER3_NEGATIVE_CONTEXTS = {
    ("tests/speckit-pro/layer3-functional/evals/speckit-scaffold-spec-evals.json", 1): {"relocate-process-artifacts.sh"},
    ("tests/speckit-pro/layer3-functional/codex-evals/speckit-scaffold-spec-evals.json", 8): {"relocate-process-artifacts.sh"},
    ("tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json", 23): {"relocate-process-artifacts.sh"},
    ("tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json", 29): {"relocate-process-artifacts.sh"},
}

# Layer 8 Markdown is scanned only in contract files. Each retained retired
# path must live in one explicitly classified section.
LAYER8_MARKDOWN_CONTEXTS = {
    (
        "tests/speckit-pro/layer8-parity/02-repository-migration-guidance/README.md",
        "Test scenario",
        "relocate-process-artifacts.sh",
    ): "negative",
    (
        "tests/speckit-pro/layer8-parity/02-repository-migration-guidance/workflow.md",
        "Legacy Input Scenario",
        "migrate-structure.sh",
    ): "legacy_input",
    (
        "tests/speckit-pro/layer8-parity/02-repository-migration-guidance/workflow.md",
        "Legacy Input Scenario",
        "relocate-process-artifacts.sh",
    ): "legacy_input",
    (
        "tests/speckit-pro/layer8-parity/02-repository-migration-guidance/workflow.md",
        "No Auto-Run Guard",
        "relocate-process-artifacts.sh",
    ): "negative",
}

NEGATIVE_MARKERS = ("must not", "does not", "never", "reject", "forbidden", "not invoke")
LEGACY_SECTION_MARKERS = ("fixture input", "historical provenance", "neither may be recommended or invoked")

CURRENT_INVENTORY = [
    "Functional runner uses Claude skill for speckit-coach",
    "Trigger runner uses Claude skill for speckit-coach",
    "Trigger runner uses Claude skill for speckit-coach",
    "Codex functional runner uses codex skill for speckit-coach",
    "Codex trigger runner uses codex skill for speckit-coach",
    "Codex functional runner uses codex skill for speckit-scaffold-spec",
    "Codex trigger runner uses codex skill for speckit-scaffold-spec",
    "Codex functional runner uses codex skill for speckit-status",
    "Codex trigger runner uses codex skill for speckit-status",
    "Codex functional runner uses codex skill for speckit-resolve-pr",
    "Codex trigger runner uses codex skill for speckit-resolve-pr",
    "Codex functional runner uses codex skill for install",
    "Codex trigger runner uses codex skill for install",
]

LIB_DIR = TESTS_ROOT / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from test_result import run_counted  # noqa: E402


def baseline_inventory(path: Path) -> list[str]:
    if not path.is_file():
        return []
    names: list[str] = []
    total: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("TOTAL: "):
            total = int(line.removeprefix("TOTAL: "))
            continue
        _ordinal, name = line.split(" ", 1)
        names.append(name)
    if total != len(names):
        raise AssertionError(f"baseline TOTAL {total} does not match {len(names)} names")
    return names


def merged_output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def json_strings(value: object, path: tuple[object, ...] = ()) -> list[tuple[tuple[object, ...], str]]:
    strings: list[tuple[tuple[object, ...], str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            strings.extend(json_strings(child, (*path, key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            strings.extend(json_strings(child, (*path, index)))
    elif isinstance(value, str):
        strings.append((path, value))
    return strings


def json_path_display(path: tuple[object, ...]) -> str:
    result = ""
    for part in path:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += ("." if result else "") + str(part)
    return result


def is_vendored_speckit_reference(value: str, match: re.Match[str]) -> bool:
    start = value.rfind(".specify/", 0, match.start())
    if start < 0:
        return False
    between = value[start : match.start()]
    return re.search(r"[\s`\"'()<>{}\[\],]", between) is None


def layer3_reference_allowed(relative: str, eval_id: object, field_path: tuple[object, ...], value: str, helper: str) -> bool:
    allowed = LAYER3_NEGATIVE_CONTEXTS.get((relative, eval_id), set())
    if helper not in allowed or not field_path or field_path[0] not in {"expected_output", "expectations"}:
        return False
    lowered = value.casefold()
    return "retired" in lowered and any(marker in lowered for marker in NEGATIVE_MARKERS)


def layer8_contract_files() -> tuple[list[Path], list[Path]]:
    markdown = [LAYER8_ROOT / "README.md"]
    structured: list[Path] = []
    for fixture_dir in sorted(path for path in LAYER8_ROOT.iterdir() if path.is_dir() and path.name[:1].isdigit()):
        markdown.extend(fixture_dir / name for name in ("README.md", "workflow.md"))
        structured.extend(fixture_dir / name for name in ("expected-equivalence.json", "tolerance.json"))
    return [path for path in markdown if path.is_file()], [path for path in structured if path.is_file()]


def runtime_contract_files() -> list[Path]:
    markdown, structured = layer8_contract_files()
    layer3 = [path for root in LAYER3_CONTRACT_ROOTS for path in sorted(root.glob("*.json"))]
    return sorted({*SHIPPED_RUNTIME_CONTRACTS, *layer3, *markdown, *structured})


def contract_units(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return [value for _field_path, value in json_strings(json.loads(text))]
    paragraphs = [" ".join(block.split()) for block in re.split(r"\n\s*\n", text) if block.strip()]
    table_rows = [line.strip() for line in text.splitlines() if line.lstrip().startswith("|")]
    return [*paragraphs, *table_rows]


def has_safe_negation(text: str) -> bool:
    lowered = text.casefold()
    return any(marker in lowered for marker in SAFE_NEGATION_MARKERS)


def runtime_registry_violations() -> list[str]:
    violations: list[str] = []
    for helper_id in sorted(EXPECTED_DEFERRED_HELPERS):
        entry = MUTATION_HELPERS.get(helper_id)
        if entry is None:
            violations.append(f"registry: missing expected helper {helper_id}")
            continue
        if entry.promotion_status != "deferred":
            violations.append(f"registry: {helper_id} status={entry.promotion_status}, expected deferred")
        if entry.authoritative_command:
            violations.append(f"registry: deferred helper {helper_id} exposes an authoritative request")

    for helper_id in sorted(EXPECTED_ACTIVE_PACKET_HELPERS):
        entry = MUTATION_HELPERS.get(helper_id)
        if entry is None:
            violations.append(f"registry: missing active packet helper {helper_id}")
            continue
        if entry.promotion_status != "golden_only":
            violations.append(f"registry: {helper_id} status={entry.promotion_status}, expected golden_only")
        if not entry.authoritative_command:
            violations.append(f"registry: active packet helper {helper_id} has no authoritative request")

    generate_entry = MUTATION_HELPERS.get("generate-pr-body")
    if generate_entry is None or generate_entry.promotion_status != "golden_only":
        status = None if generate_entry is None else generate_entry.promotion_status
        violations.append(f"registry: generate-pr-body status={status}, expected golden_only")
    source = inspect.getsource(generate_pr_body)
    input_fields = set(re.findall(r'request\.inputs\.get\("([^"]+)"', source))
    if input_fields != {"output_path", "title", "sections"}:
        violations.append(f"implementation: generate-pr-body fields={sorted(input_fields)}")

    validate_entry = HELPERS.get("validate-pr-packet-read-only")
    if validate_entry is None or validate_entry.promotion_status != "python_authoritative":
        status = None if validate_entry is None else validate_entry.promotion_status
        violations.append(f"registry: validate-pr-packet-read-only status={status}")
    elif "persistence" in validate_entry.out_of_scope_modes:
        violations.append("registry: packet validator still marks promoted persistence out of scope")
    elif validate_entry.mutation_operation != "validate-pr-packet-write":
        violations.append("registry: packet validator does not route persistence to validate-pr-packet-write")
    elif validate_entry.mutation_operation_deferred:
        violations.append("registry: packet validator still marks validate-pr-packet-write as deferred")
    return violations


def runtime_contract_violations() -> list[str]:
    violations: list[str] = []
    unavailable = {
        helper_id
        for helper_id, entry in MUTATION_HELPERS.items()
        if entry.promotion_status in {"deferred", "out_of_scope"}
    }
    unsupported_body_claims = (
        "packet/body generation via runner helper generate-pr-body",
        "generate-pr-body metadata",
        "generate-pr-body appends",
        "generate-pr-body creates",
        "generate-pr-body emits",
        "generate-pr-body uses the host",
        "generate-pr-body writes packet",
        "generator emits",
        "generator writes packet",
    )
    persistence_safe = (
        "writes_state=false",
        "does not persist",
        "never writes",
        "no validation file",
        "without claiming",
        "do not claim",
        "must not",
    )

    for path in runtime_contract_files():
        relative = path.relative_to(REPO_ROOT).as_posix()
        for unit in contract_units(path):
            lowered = unit.casefold()
            if ".git/" in lowered:
                violations.append(f"{relative}: uses invalid linked-worktree .git child path")
            if "--packet-output" in lowered or "packet_output" in lowered:
                violations.append(f"{relative}: claims unsupported generate-pr-body packet output")
            if any(claim in lowered for claim in unsupported_body_claims) and not has_safe_negation(unit):
                violations.append(f"{relative}: claims unsupported generate-pr-body behavior")

            for helper_id in unavailable:
                if helper_id not in lowered:
                    continue
                helper = re.escape(helper_id)
                invocation = re.search(
                    rf"(?:runner helper\s+`?{helper}`?|\b(?:run|invoke|execute|call|retry|use)\b.{{0,160}}\b{helper}\b|\b{helper}\b.{{0,80}}(?:--dry-run|--apply|mode[ =](?:dry_run|apply)))",
                    lowered,
                )
                if invocation and not has_safe_negation(unit):
                    violations.append(f"{relative}: actively invokes unavailable helper {helper_id}")

            persistence_claim = any(
                term in lowered for term in ("validation.json", "validation_result_path", "validation file")
            ) or re.search(r"validate-pr-packet.{0,100}\b(?:writes|persists|persisted|written)\b", lowered)
            if "validate-pr-packet" in lowered and persistence_claim:
                if not any(marker in lowered for marker in persistence_safe):
                    violations.append(f"{relative}: claims read-only packet validation persists state")
    return sorted(set(violations))


def runtime_contract_parity_violations() -> list[str]:
    violations: list[str] = []
    pairs = (
        (
            "upgrade",
            PLUGIN_ROOT / "skills" / "speckit-upgrade" / "SKILL.md",
            PLUGIN_ROOT / "codex-skills" / "speckit-upgrade" / "SKILL.md",
            ("migrate-structure", "relocate-process-artifacts", "promotion_status=deferred", "no authoritative request"),
        ),
        (
            "scaffold",
            PLUGIN_ROOT / "skills" / "speckit-scaffold-spec" / "SKILL.md",
            PLUGIN_ROOT / "codex-skills" / "speckit-scaffold-spec" / "SKILL.md",
            ("relocate-process-artifacts", "ensure-reviewability-preset", "deferred", "unavailable"),
        ),
        (
            "autopilot",
            PLUGIN_ROOT / "skills" / "speckit-autopilot" / "SKILL.md",
            PLUGIN_ROOT / "codex-skills" / "speckit-autopilot" / "SKILL.md",
            (PACKET_PATH_CONTRACT, "pr-packet-output", "data.stdout_json", "writes_state=false", "output_path", "sections"),
        ),
        (
            "phase execution",
            PLUGIN_ROOT / "skills" / "speckit-autopilot" / "references" / "phase-execution.md",
            PLUGIN_ROOT / "codex-skills" / "speckit-autopilot" / "references" / "phase-execution-codex.md",
            (PACKET_PATH_CONTRACT, "relocate-process-artifacts", "data.stdout_json", "writes_state=false", "output_path", "sections"),
        ),
        (
            "post implementation",
            PLUGIN_ROOT / "skills" / "speckit-autopilot" / "references" / "post-implementation.md",
            PLUGIN_ROOT / "codex-skills" / "speckit-autopilot" / "references" / "post-implementation-codex.md",
            (),
        ),
    )
    for label, claude_path, codex_path, required in pairs:
        bodies = {
            "Claude": re.sub(r"\s+", " ", claude_path.read_text(encoding="utf-8").casefold()),
            "Codex": re.sub(r"\s+", " ", codex_path.read_text(encoding="utf-8").casefold()),
        }
        for surface, body in bodies.items():
            for token in required:
                if token.casefold() not in body:
                    violations.append(f"{label}: {surface} missing parity token {token}")
    post_paths = pairs[-1][1:3]
    violations.extend(
        post_implementation_outcome_violations(
            {
                "Claude": post_paths[0].read_text(encoding="utf-8"),
                "Codex": post_paths[1].read_text(encoding="utf-8"),
            }
        )
    )
    return violations


def post_implementation_outcome_violations(bodies: dict[str, str]) -> list[str]:
    required_fragments = {
        "deferred UAT invocation prohibition": (
            "the runner helper `generate-uat-skeleton` is registered as deferred",
            "never invoke it as an active helper",
        ),
        "missing UAT fail-open fallback": (
            "mark the uat row skipped with that evidence, and continue to pr-body generation and pr creation",
            "missing deferred output alone never marks the row failed and never blocks pr side effects",
        ),
        "registered-validator-only blocker": (
            "never invoke `validate-uat-runbook`: that helper is not registered",
            "if no actual registered uat-validation path exists",
            "if and only if that just-run validator reports the existing runbook invalid",
        ),
        "stack-manager invocation prohibition and fallback": (
            "`detect-stack-manager-plan` is out of scope and must not be invoked",
            "use explicit packet-owned `gh pr create --base --head --title --body-file` commands",
        ),
        "source-directory and branch-prefix split": (
            "`--feature-branch` is the emitted branch prefix",
            "`--source-feature-dir specs/<feature>`",
            "evidence, scoped evidence, prs, and moc files stay under the source feature directory while emitted head/base refs use the safe branch prefix",
        ),
    }
    required_patterns = {
        "missing packet blocker": r"if any (?:required )?packet is absent or invalid,(?:.|\n){0,120}stop",
        "post-mutation manager block": r"(?:prior|partial) `gh-stack` mutation(?: already occurred)?,?(?:.|\n){0,120}block(?:.|\n){0,120}(?:rather than|instead of) mixing managers",
        "golden-only live-mutation prohibition": r"`multi-pr-emission`(?:.|\n){0,120}`golden_only`(?:.|\n){0,160}does not emit packets or execute live pr mutations",
    }
    forbidden_patterns = {
        "missing UAT output must not stop": r"(?:skeleton generation fails|output file is missing)(?:.|\n){0,160}(?:stop|blocks?)",
        "unregistered UAT helper must not be called": r"runner helper validate-uat-runbook",
        "post-mutation fallback must not run": r"after (?:a |any )?partial `gh-stack` mutation(?:.|\n){0,100}(?:fall back|fallback) to `?gh pr",
    }

    violations: list[str] = []
    for surface, raw_body in bodies.items():
        body = re.sub(r"\s+", " ", raw_body.casefold())
        for outcome, fragments in required_fragments.items():
            if any(fragment not in body for fragment in fragments):
                violations.append(f"post implementation: {surface} missing outcome: {outcome}")
        for outcome, pattern in required_patterns.items():
            if re.search(pattern, body) is None:
                violations.append(f"post implementation: {surface} missing outcome: {outcome}")
        for outcome, pattern in forbidden_patterns.items():
            if re.search(pattern, body):
                violations.append(f"post implementation: {surface} contradictory outcome: {outcome}")
    return violations


def markdown_section_map(text: str) -> tuple[list[str], dict[str, str]]:
    current = "<preamble>"
    line_sections: list[str] = []
    section_lines: dict[str, list[str]] = {current: []}
    for line in text.splitlines():
        heading = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1)
            section_lines.setdefault(current, [])
        line_sections.append(current)
        section_lines[current].append(line)
    return line_sections, {section: "\n".join(lines).casefold() for section, lines in section_lines.items()}


def layer8_markdown_reference_allowed(relative: str, section: str, line: str, section_text: str, helper: str) -> bool:
    classification = LAYER8_MARKDOWN_CONTEXTS.get((relative, section, helper))
    lowered = line.casefold()
    if classification == "negative":
        return "retired" in lowered and any(marker in lowered for marker in NEGATIVE_MARKERS)
    if classification == "legacy_input":
        return all(marker in section_text for marker in LEGACY_SECTION_MARKERS)
    return False


def retired_contract_violations() -> list[str]:
    violations: list[str] = []

    for root in LAYER3_CONTRACT_ROOTS:
        for path in sorted(root.glob("*.json")):
            relative = path.relative_to(REPO_ROOT).as_posix()
            data = json.loads(path.read_text(encoding="utf-8"))
            for eval_case in data.get("evals", []):
                eval_id = eval_case.get("id")
                for field_path, value in json_strings(eval_case):
                    for match in RETIRED_HELPER_PATTERN.finditer(value):
                        helper = match.group(1)
                        if is_vendored_speckit_reference(value, match):
                            continue
                        if layer3_reference_allowed(relative, eval_id, field_path, value, helper):
                            continue
                        violations.append(f"{relative}:eval[{eval_id}].{json_path_display(field_path)} prescribes {helper}")

    markdown_paths, structured_paths = layer8_contract_files()
    for path in structured_paths:
        relative = path.relative_to(REPO_ROOT).as_posix()
        data = json.loads(path.read_text(encoding="utf-8"))
        for field_path, value in json_strings(data):
            for match in RETIRED_HELPER_PATTERN.finditer(value):
                if is_vendored_speckit_reference(value, match):
                    continue
                violations.append(f"{relative}:{json_path_display(field_path)} prescribes {match.group(1)}")

    for path in markdown_paths:
        relative = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        line_sections, section_texts = markdown_section_map(text)
        for line_number, line in enumerate(text.splitlines(), start=1):
            section = line_sections[line_number - 1]
            for match in RETIRED_HELPER_PATTERN.finditer(line):
                helper = match.group(1)
                if is_vendored_speckit_reference(line, match):
                    continue
                if layer8_markdown_reference_allowed(relative, section, line, section_texts[section], helper):
                    continue
                violations.append(f"{relative}:{line_number} [{section}] prescribes {helper}")

    return violations


def run_script(script: Path, *args: str, env_overrides: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        env=env,
        shell=False,
        check=False,
    )


def write_fake_skill_creator(root: Path) -> Path:
    skill_creator = root / "skill-creator"
    scripts = skill_creator / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "__init__.py").write_text("", encoding="utf-8")
    (scripts / "run_eval.py").write_text(
        textwrap.dedent(
            """\
            import sys

            print("fake run_eval invoked")
            print("args:", " ".join(sys.argv[1:]))
            """
        ),
        encoding="utf-8",
    )
    return skill_creator


class EvalRunnerSkillSelectionTests(unittest.TestCase):
    def test_functional_preview_helpers_handle_invalid_eval_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            invalid_json = root / "invalid.json"
            invalid_json.write_text("{", encoding="utf-8")

            self.assertEqual(eval_count(invalid_json), "?")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                print_eval_prompts(invalid_json)
            self.assertIn("ERROR: Unable to read eval file", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())

            invalid_entries = root / "invalid-entries.json"
            invalid_entries.write_text(
                json.dumps(
                    {
                        "evals": [
                            {"id": 1, "prompt": "preview me", "expectations": ["first expectation"]},
                            {"id": "missing-prompt", "expectations": ["no prompt"]},
                            "not an object",
                            {"id": "bad-expectation", "prompt": "skip bad expectation", "expectations": [5]},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(eval_count(invalid_entries), "4")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                print_eval_prompts(invalid_entries)
            self.assertIn("[1] preview me...", stdout.getvalue())
            self.assertIn("- first expectation", stdout.getvalue())
            self.assertIn("ERROR: Skipping eval entry 2", stderr.getvalue())
            self.assertIn("ERROR: Skipping eval entry 3", stderr.getvalue())
            self.assertIn("ERROR: Skipping eval entry 4 expectation", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_codex_archive_sweep_execution_contract(self) -> None:
        prerequisites = (
            PLUGIN_ROOT / "codex-skills/speckit-autopilot/references/prerequisites-codex.md"
        ).read_text(encoding="utf-8")
        normalized = " ".join(prerequisites.split())

        self.assertIn("use its project-local command contract as the Codex invocation path", normalized)
        self.assertIn("Do not require a generated `$speckit-archive-run` skill", normalized)
        self.assertIn("Treat integration-specific frontmatter entries and manifest requirements", normalized)
        self.assertIn("Do not resolve or execute those entries from the Codex plugin", normalized)
        self.assertIn("`prerequisite_mode=codex_native_worktree_binding`", normalized)
        self.assertIn("Do not substitute a manual `specs/` inventory", normalized)
        self.assertIn("STOP before Phase 0", normalized)
        self.assertIn("`status=no_candidates`", normalized)
        self.assertIn("It is not a fallback for a broken or unexecuted command path", normalized)

    def test_codex_autopilot_worktree_handoff_contract(self) -> None:
        scaffold = (PLUGIN_ROOT / "codex-skills/speckit-scaffold-spec/SKILL.md").read_text(encoding="utf-8")
        autopilot = (PLUGIN_ROOT / "codex-skills/speckit-autopilot/SKILL.md").read_text(encoding="utf-8")
        prerequisites = (
            PLUGIN_ROOT / "codex-skills/speckit-autopilot/references/prerequisites-codex.md"
        ).read_text(encoding="utf-8")

        self.assertIn("start a new Codex task rooted at that worktree", scaffold)
        self.assertIn("Never hand off only the inner workflow path from the parent checkout", scaffold)
        self.assertIn("bind the workflow to the current worktree", autopilot)
        self.assertIn("git worktree list\n   --porcelain", prerequisites)
        self.assertIn("STOP: Workflow file is not in the current checkout", prerequisites)
        self.assertIn("Never copy, move, check out, rebase, or reconstruct the workflow", prerequisites)

    def test_post_implementation_outcome_negative_canaries(self) -> None:
        claude = (PLUGIN_ROOT / "skills/speckit-autopilot/references/post-implementation.md").read_text(encoding="utf-8")
        codex = (PLUGIN_ROOT / "codex-skills/speckit-autopilot/references/post-implementation-codex.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(post_implementation_outcome_violations({"Claude": claude, "Codex": codex}), [])

        canaries = {
            "missing deferred output stop": claude + "\nIf the output file is missing, STOP before PR creation.\n",
            "active unregistered validator": claude + "\nRun runner helper validate-uat-runbook now.\n",
            "post-mutation fallback": claude + "\nAfter a partial `gh-stack` mutation, fall back to `gh pr create`.\n",
            "source and branch reversal": claude.replace(
                "evidence, scoped evidence, PRS, and MOC files stay under\n   the source feature directory while emitted head/base refs use the safe branch\n   prefix",
                "evidence, scoped evidence, PRS, and MOC files move to the safe branch prefix",
            ),
        }
        for name, mutated in canaries.items():
            with self.subTest(msg=name):
                self.assertTrue(post_implementation_outcome_violations({"Claude": mutated, "Codex": codex}))

    def test_eval_runner_skill_selection_contract(self) -> None:
        self.assertEqual(baseline_inventory(BASELINE), CURRENT_INVENTORY)
        self.assertEqual(retired_contract_violations(), [])
        self.assertEqual(runtime_registry_violations(), [])
        self.assertEqual(runtime_contract_violations(), [])
        self.assertEqual(runtime_contract_parity_violations(), [])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_skill_creator = write_fake_skill_creator(root)
            fake_home = root / "home"
            fake_home.mkdir()

            name = CURRENT_INVENTORY[0]
            result = run_script(FUNCTIONAL_SCRIPT, "speckit-coach")
            with self.subTest(msg=name):
                output = merged_output(result)
                self.assertTrue(
                    result.returncode == 0
                    and f"Skill path: {PLUGIN_ROOT / 'skills' / 'speckit-coach'}" in output,
                    output,
                )

            name = CURRENT_INVENTORY[1]
            result = run_script(
                TRIGGER_SCRIPT,
                "speckit-coach",
                env_overrides={"SKILL_CREATOR_ROOT": str(fake_skill_creator), "HOME": str(fake_home)},
            )
            with self.subTest(msg=name):
                self.assertEqual(result.returncode, 0, merged_output(result))

            name = CURRENT_INVENTORY[2]
            with self.subTest(msg=name):
                self.assertIn(f"Skill path: {PLUGIN_ROOT / 'skills' / 'speckit-coach'}", merged_output(result))

            name = CURRENT_INVENTORY[3]
            result = run_script(CODEX_FUNCTIONAL_SCRIPT, "speckit-coach")
            with self.subTest(msg=name):
                output = merged_output(result)
                self.assertTrue(
                    result.returncode == 0
                    and f"Skill path: {PLUGIN_ROOT / 'codex-skills' / 'speckit-coach'}" in output,
                    output,
                )

            name = CURRENT_INVENTORY[4]
            result = run_script(CODEX_TRIGGER_SCRIPT, "speckit-coach")
            with self.subTest(msg=name):
                output = merged_output(result)
                self.assertTrue(
                    result.returncode == 0
                    and f"Skill path: {PLUGIN_ROOT / 'codex-skills' / 'speckit-coach'}" in output,
                    output,
                )

            inventory_index = 5
            for skill in CODEX_SKILLS:
                name = CURRENT_INVENTORY[inventory_index]
                result = run_script(CODEX_FUNCTIONAL_SCRIPT, skill)
                with self.subTest(msg=name):
                    output = merged_output(result)
                    self.assertTrue(
                        result.returncode == 0
                        and f"Skill path: {PLUGIN_ROOT / 'codex-skills' / skill}" in output,
                        output,
                    )
                inventory_index += 1

                name = CURRENT_INVENTORY[inventory_index]
                result = run_script(CODEX_TRIGGER_SCRIPT, skill)
                with self.subTest(msg=name):
                    output = merged_output(result)
                    self.assertTrue(
                        result.returncode == 0
                        and f"Skill path: {PLUGIN_ROOT / 'codex-skills' / skill}" in output,
                        output,
                    )
                inventory_index += 1


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EvalRunnerSkillSelectionTests)
    return run_counted(suite, label="test-eval-runner-skill-selection")


if __name__ == "__main__":
    raise SystemExit(main())
