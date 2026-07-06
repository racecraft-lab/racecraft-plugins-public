"""Payload and install-verification gate operations for XPLAT-007 US2."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from .. import RUNNER_VERSION
from ..envelope import diagnostic, response

PROMOTION_RECORD = "tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/promotion-records.json"
FIXTURE_BOUNDARY = Path("tests") / "speckit-pro" / "layer4-scripts" / "fixtures" / "xplat-007-gates"
DEFAULT_PAYLOAD_CASES = FIXTURE_BOUNDARY / "payload-evidence-cases.json"
DEFAULT_INSTALL_CASES = FIXTURE_BOUNDARY / "install-verification-cases.json"
INSTALL_INVENTORY = Path("speckit-pro") / "speckit_pro_runner" / "install_inventory.json"
XPLAT_008_FIXTURE_BOUNDARY = Path("tests") / "speckit-pro" / "layer4-scripts" / "fixtures" / "xplat-008-release"
DEFAULT_XPLAT_008_PAYLOAD_CASES = XPLAT_008_FIXTURE_BOUNDARY / "payload-completeness-cases.json"
XPLAT_008_PROMOTION_RECORD = XPLAT_008_FIXTURE_BOUNDARY / "promotion-records.json"

__all__ = ("run_payload_gate",)


def run_payload_gate(entry: Any, request: Any) -> dict[str, Any]:
    repo_root = find_repo_root(Path.cwd())
    if repo_root is None:
        diag = diagnostic(
            "missing_prerequisite",
            "could not locate repository root for payload/install gate request",
            remediation_summary="Run the gate from a SpecKit Pro source checkout.",
            remediation_actions=["Change to the repository root.", "Retry the same runner request."],
        )
        return response("missing_prerequisite", request_id=request.request_id, data=base_data(entry, request.operation, "missing_prerequisite"), diagnostics=[diag])

    if request.operation == "build-test-payload-evidence":
        return build_test_payload_evidence(entry, request, repo_root)
    if request.operation == "payload-completeness":
        return payload_completeness_xplat008(entry, request, repo_root)
    if request.operation == "refresh-local-plugin-fixture":
        return install_verification(entry, request, repo_root, refresh=True)
    if request.operation == "verify-install":
        return install_verification(entry, request, repo_root, refresh=False)

    diag = diagnostic(
        "unknown_gate_operation",
        "payload/install gate operation is not implemented by the payload module",
        details={"operation": request.operation},
    )
    return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])


def payload_completeness_xplat008(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    case_result = load_case(repo_root, request.inputs, default_case_file=DEFAULT_XPLAT_008_PAYLOAD_CASES)
    if is_diagnostic(case_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[case_result])
    case = case_result

    surfaces_result = xplat008_payload_surfaces(case)
    if is_diagnostic(surfaces_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[surfaces_result])
    surfaces = surfaces_result

    target_result = xplat008_build_target(request, repo_root)
    if is_diagnostic(target_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[target_result])

    temp_context: tempfile.TemporaryDirectory[str] | None = None
    try:
        if target_result is None:
            temp_context = tempfile.TemporaryDirectory(prefix="xplat-008-payload-")
            build_dist_root = Path(temp_context.name) / "dist"
        else:
            build_dist_root = target_result

        try:
            build_xplat008_payloads(repo_root, build_dist_root)
            compare_dist_root = build_dist_root if request.mode == "apply" else repo_root / "dist"
            results = xplat008_payload_results(repo_root, build_dist_root, compare_dist_root, case, surfaces)
        except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
            diag = diagnostic(
                "payload_completeness_evidence_invalid",
                "XPLAT-008 payload completeness could not build or read generated payload evidence",
                details={"case_id": case.get("case_id"), "error": type(exc).__name__},
                remediation_summary="Refresh source manifests and generated payload metadata before retrying.",
                remediation_actions=["Run the payload build from a complete source checkout.", "Retry the read-only payload completeness gate."],
            )
            return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])
    finally:
        if temp_context is not None:
            temp_context.cleanup()

    blocking = [result for result in results if result["status"] != "pass"]
    status = "expected_failure" if blocking else "ok"
    data = base_data(entry, request.operation, status)
    data["gate"]["comparison_ids"] = ["xplat-008-payload-completeness"]
    data["gate"]["promotion_record"] = XPLAT_008_PROMOTION_RECORD.as_posix()
    data["artifacts"] = [
        {"path": XPLAT_008_PROMOTION_RECORD.as_posix(), "kind": "promotion_record"},
        {"path": DEFAULT_XPLAT_008_PAYLOAD_CASES.as_posix(), "kind": "fixture"},
    ]
    data["payload_completeness"] = results
    data["artifacts"].extend(
        {"path": result["generated_root"], "kind": "generated_payload"}
        for result in results
        if isinstance(result.get("generated_root"), str) and not Path(result["generated_root"]).is_absolute()
    )
    if status == "ok":
        return response("ok", request_id=request.request_id, data=data)

    data["gate"]["gate_status"] = "fail"
    data["gate"]["blocking"] = True
    diag = diagnostic(
        "payload_completeness_blocked",
        "XPLAT-008 payload completeness found blocking generated payload drift",
        details={
            "case_id": case.get("case_id"),
            "blocking_surfaces": [item["payload_surface"] for item in blocking],
        },
        remediation_summary="Rebuild generated Claude and Codex payloads from source through the runner apply request.",
        remediation_actions=["Run payload-completeness in apply mode.", "Retry the read-only payload completeness gate."],
    )
    return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])


def build_test_payload_evidence(entry: Any, request: Any, repo_root: Path) -> dict[str, Any]:
    if request.inputs.get("release_payload_cutover") is not False:
        diag = diagnostic(
            "release_payload_cutover_refused",
            "XPLAT-007 payload evidence must not select or cut over release payloads",
            details={"release_payload_cutover": request.inputs.get("release_payload_cutover")},
            remediation_summary="Keep test payload evidence isolated from release payload selection.",
            remediation_actions=["Set release_payload_cutover to false.", "Defer generated release payload cutover to XPLAT-008."],
            deferred_to="XPLAT-008",
        )
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])

    case_result = load_case(repo_root, request.inputs, default_case_file=DEFAULT_PAYLOAD_CASES)
    if is_diagnostic(case_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[case_result])
    case = case_result

    output_result = output_root_from_inputs(request.inputs, repo_root)
    if is_diagnostic(output_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[output_result])
    output_root = output_result
    output_root_rel = repo_relative(output_root, repo_root) if is_relative_to(output_root, repo_root) else output_root.as_posix()

    evidence = [
        payload_evidence_record(payload, request.mode, case, output_root_rel)
        for payload in case.get("payloads", [])
        if isinstance(payload, dict)
    ]
    if not evidence:
        diag = diagnostic(
            "invalid_payload_case",
            "payload evidence case must contain at least one payload record",
            details={"case_id": case.get("case_id")},
            remediation_summary="Use a payload evidence fixture with payload records.",
            remediation_actions=["Inspect payload-evidence-cases.json.", "Retry with a valid case_id."],
        )
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])

    data = base_data(entry, request.operation, "ok")
    data["payload_evidence"] = evidence
    data["artifacts"].extend(payload_artifacts(evidence, output_root, repo_root, include_written=request.mode == "apply"))

    stale = [item for item in case.get("stale_generated_files", []) if isinstance(item, str)]
    if stale:
        for item in evidence:
            item["status"] = "expected_failure"
        data["gate"]["gate_status"] = "fail"
        data["gate"]["blocking"] = True
        diag = diagnostic(
            "stale_generated_payload_evidence",
            "payload evidence fixture contains stale generated release payload references",
            details={"case_id": case.get("case_id"), "stale_generated_files": stale},
            remediation_summary="Refresh test payload evidence without touching release payload cutover files.",
            remediation_actions=["Remove stale generated release payload evidence.", "Re-run build-test-payload-evidence in fixture or temp output roots."],
        )
        return response("expected_failure", request_id=request.request_id, data=data, diagnostics=[diag])

    if request.mode == "apply":
        write_payload_evidence(evidence, output_root)

    return response("ok", request_id=request.request_id, data=data)


def install_verification(entry: Any, request: Any, repo_root: Path, *, refresh: bool) -> dict[str, Any]:
    case_result = load_case(repo_root, request.inputs, default_case_file=DEFAULT_INSTALL_CASES)
    if is_diagnostic(case_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[case_result])
    case = case_result

    fake_home = request.inputs.get("fake_home", case.get("fake_home")) is True
    if not fake_home:
        diag = diagnostic(
            "real_home_refused",
            "US2 install verification accepts fake-home fixture roots only",
            details={"case_id": case.get("case_id")},
            remediation_summary="Use fake_home true with a fixture install root.",
            remediation_actions=["Set fake_home to true.", "Defer real installed-cache verification to XPLAT-008."],
            deferred_to="XPLAT-008",
        )
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[diag])

    install_root_result = install_root_from_case(case, repo_root)
    if is_diagnostic(install_root_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[install_root_result])
    install_root = install_root_result

    inventory_result = load_install_inventory(repo_root, case)
    if is_diagnostic(inventory_result):
        return response("input_error", request_id=request.request_id, data=base_data(entry, request.operation, "input_error"), diagnostics=[inventory_result])
    inventory = inventory_result

    missing = sorted(path for path in case.get("missing_paths", []) if isinstance(path, str))
    mismatches = sorted(path for path in case.get("checksum_mismatches", []) if isinstance(path, str))
    expected_files = [record["path"] for record in inventory]
    status = "complete"
    if missing or mismatches:
        status = "safe_repair" if fake_home else "blocked"
    if case.get("expected_status") in {"complete", "safe_repair", "blocked"}:
        status = str(case["expected_status"])

    install = {
        "schema_version": "1.0",
        "verification_id": str(case.get("verification_id") or f"us2-install-{case.get('case_id', 'fixture')}"),
        "status": status,
        "install_root": repo_relative(install_root, repo_root),
        "fake_home": True,
        "stubbed_cli": request.inputs.get("stubbed_cli", case.get("stubbed_cli", True)) is True,
        "bundled_agent_count": bundled_agent_count(inventory),
        "expected_files": expected_files,
        "missing_files": missing,
        "checksum_mismatches": mismatches,
        "command_plans": command_plans(request.operation, missing + mismatches),
        "safe_repairs": missing + mismatches if status == "safe_repair" else [],
        "unsafe_manual_remediations": [] if fake_home else missing + mismatches,
        "native_uat_claimed": False,
    }

    if refresh and request.mode == "read_only":
        install["command_plans"] = command_plans(request.operation, expected_files[:1])

    data = base_data(entry, request.operation, "ok")
    data["install_verification"] = install
    return response("ok", request_id=request.request_id, data=data)


def xplat008_build_target(request: Any, repo_root: Path) -> Path | None | dict[str, Any]:
    if request.mode in {"read_only", "dry_run"}:
        return None

    raw_output = request.inputs.get("output_root")
    if isinstance(raw_output, str) and raw_output:
        output_root = resolve_path(raw_output, repo_root)
        resolved = output_root.resolve(strict=False)
        fixture_root = (repo_root / XPLAT_008_FIXTURE_BOUNDARY).resolve(strict=False)
        temp_root = Path(tempfile.gettempdir()).resolve(strict=False)
        if is_relative_to(resolved, fixture_root) or is_relative_to(resolved, temp_root):
            return output_root
        return diagnostic(
            "payload_output_root_refused",
            "XPLAT-008 payload output_root must stay inside fixture or temporary roots",
            details={"output_root": raw_output, "fixture_root": repo_relative(fixture_root, repo_root)},
            remediation_summary="Use a fixture or OS temp output root for dry-run/apply tests.",
            remediation_actions=["Set output_root under tests/speckit-pro/layer4-scripts/fixtures/xplat-008-release.", "Or use an OS temp directory."],
        )

    if request.mode == "apply" and request.inputs.get("apply_dist") is True:
        return repo_root / "dist"

    return diagnostic(
        "payload_output_root_refused",
        "XPLAT-008 payload dry_run/apply requires output_root unless apply_dist is true",
        remediation_summary="Use a fixture/temp output root or explicitly target committed dist in apply mode.",
        remediation_actions=["Set output_root for test writes.", "Set apply_dist to true only when rebuilding committed dist output."],
    )


def build_xplat008_payloads(repo_root: Path, dist_root: Path) -> None:
    source = repo_root / "speckit-pro"
    claude = dist_root / "claude" / "speckit-pro"
    codex = dist_root / "codex" / "speckit-pro"
    if not source.is_dir():
        raise FileNotFoundError(f"source plugin directory not found: {source}")

    reset_payload_dir(claude, dist_root)
    for name in [
        ".claude-plugin",
        "agents",
        "commands",
        "hooks",
        "skills",
        "scripts",
        "speckit_pro_runner",
        "README.md",
        "CHANGELOG.md",
    ]:
        copy_optional_xplat008(source / name, claude / name)
    copy_optional_xplat008(repo_root / "LICENSE", claude / "LICENSE")
    for skill_file in claude.glob("skills/*/SKILL.md"):
        strip_codex_guard(skill_file)

    reset_payload_dir(codex, dist_root)
    for name in [
        ".codex-plugin",
        "codex-agents",
        "codex-hooks.json",
        "scripts",
        "speckit_pro_runner",
        "README.md",
        "CHANGELOG.md",
    ]:
        copy_optional_xplat008(source / name, codex / name)
    copy_optional_xplat008(repo_root / "LICENSE", codex / "LICENSE")
    copy_required_xplat008(source / "skills", codex / "skills")
    copy_required_xplat008(source / "codex-skills", codex / "skills")
    rewrite_codex_manifest_xplat008(codex)
    for text_file in codex.rglob("*"):
        if text_file.is_file():
            rewrite_payload_skill_paths_xplat008(codex, text_file)


def reset_payload_dir(path: Path, allowed_root: Path) -> None:
    resolved_path = path.resolve(strict=False)
    resolved_allowed = allowed_root.resolve(strict=False)
    if not is_relative_to(resolved_path, resolved_allowed):
        raise ValueError(f"refusing to reset path outside payload root: {path}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_required_xplat008(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"required source path missing: {src}")
    copy_optional_xplat008(src, dst)


def copy_optional_xplat008(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(
            src,
            dst,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    elif src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def strip_codex_guard(skill_file: Path) -> None:
    text = skill_file.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].rstrip("\n") == "## Codex Skill-Selection Guard":
            i += 1
            while i < len(lines) and not lines[i].startswith("## "):
                i += 1
            continue
        output.append(lines[i])
        i += 1
    skill_file.write_text("".join(output), encoding="utf-8")


def rewrite_codex_manifest_xplat008(codex_root: Path) -> None:
    manifest = codex_root / ".codex-plugin" / "plugin.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["skills"] = "./skills/"
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


REL_SKILL_PATH_XPLAT008 = re.compile(r"(?P<prefix>(?:\.\./)+(?:skills|codex-skills)/)(?P<rest>[^\s`)\"']+)")


def rewrite_payload_skill_paths_xplat008(codex_root: Path, path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return

    current_dir = path.parent

    def replace(match: re.Match[str]) -> str:
        rest = match.group("rest")
        suffix = ""
        while rest and rest[-1] in ".,;:":
            suffix = rest[-1] + suffix
            rest = rest[:-1]
        anchor = ""
        if "#" in rest:
            rest, anchor = rest.split("#", 1)
            anchor = "#" + anchor
        trailing_slash = rest.endswith("/")
        target = codex_root / "skills" / rest
        rel = os.path.relpath(target, current_dir).replace(os.sep, "/")
        if trailing_slash and not rel.endswith("/"):
            rel += "/"
        return rel + anchor + suffix

    rewritten = REL_SKILL_PATH_XPLAT008.sub(replace, text)
    if rewritten != text:
        path.write_text(rewritten, encoding="utf-8")


def xplat008_payload_surfaces(case: dict[str, Any]) -> list[str] | dict[str, Any]:
    raw_surfaces = case.get("surfaces", ["claude", "codex"])
    if not isinstance(raw_surfaces, list):
        return diagnostic(
            "invalid_payload_surface_selection",
            "XPLAT-008 payload completeness requires explicit Claude and Codex surfaces",
            details={"case_id": case.get("case_id"), "surfaces_type": type(raw_surfaces).__name__},
            remediation_summary="Select exactly the Claude and Codex generated payload surfaces.",
            remediation_actions=["Set surfaces to [\"claude\", \"codex\"].", "Retry the payload completeness request."],
        )
    surfaces = [item for item in raw_surfaces if isinstance(item, str) and item in {"claude", "codex"}]
    invalid = [str(item) for item in raw_surfaces if not isinstance(item, str) or item not in {"claude", "codex"}]
    if set(surfaces) != {"claude", "codex"} or len(surfaces) != 2 or invalid:
        return diagnostic(
            "invalid_payload_surface_selection",
            "XPLAT-008 payload completeness must compare exactly the Claude and Codex generated payloads",
            details={"case_id": case.get("case_id"), "surfaces": raw_surfaces, "invalid_surfaces": invalid},
            remediation_summary="Do not allow a payload completeness gate to pass without both generated payload surfaces.",
            remediation_actions=["Set surfaces to [\"claude\", \"codex\"].", "Retry the payload completeness request."],
        )
    return surfaces


def xplat008_payload_results(
    repo_root: Path,
    expected_dist_root: Path,
    actual_dist_root: Path,
    case: dict[str, Any],
    surfaces: list[str],
) -> list[dict[str, Any]]:
    mutations = case.get("mutations") if isinstance(case.get("mutations"), dict) else {}
    return [
        xplat008_payload_result(
            repo_root,
            surface,
            expected_dist_root / surface / "speckit-pro",
            actual_dist_root / surface / "speckit-pro",
            mutations.get(surface, {}) if isinstance(mutations, dict) else {},
        )
        for surface in surfaces
    ]


def xplat008_payload_result(
    repo_root: Path,
    surface: str,
    expected_root: Path,
    actual_root: Path,
    mutation: dict[str, Any],
) -> dict[str, Any]:
    plugin_version = plugin_version_for_surface(repo_root, surface)
    expected_files = scan_payload_files(expected_root, source_root=repo_root / "speckit-pro", surface=surface)
    actual_files = scan_payload_files(actual_root, source_root=repo_root / "speckit-pro", surface=surface)
    actual_files = apply_payload_mutation(actual_files, mutation)

    expected_by_path = {item["path"]: item for item in expected_files}
    actual_by_path = {item["path"]: item for item in actual_files}
    missing = sorted(set(expected_by_path) - set(actual_by_path))
    extra = sorted(set(actual_by_path) - set(expected_by_path))
    mismatched = sorted(
        path for path in set(expected_by_path) & set(actual_by_path)
        if expected_by_path[path]["sha256"] != actual_by_path[path]["sha256"]
    )
    trust_metadata_mismatches = payload_trust_metadata_mismatches(actual_root)
    mismatched = sorted(set(mismatched) | set(trust_metadata_mismatches))
    path_leaks = sorted(
        set(path for path in actual_by_path if payload_path_leaks(path))
        | set(str(item) for item in mutation.get("path_leaks", []) if isinstance(item, str))
    )
    status = "pass" if not missing and not extra and not mismatched and not path_leaks else "fail"

    return {
        "schema_version": "1.0",
        "payload_surface": surface,
        "source_root": "speckit-pro",
        "generated_root": repo_relative(actual_root, repo_root) if is_relative_to(actual_root.resolve(strict=False), repo_root.resolve(strict=False)) else actual_root.as_posix(),
        "plugin_version": plugin_version,
        "runner_version": RUNNER_VERSION,
        "expected_files": expected_files,
        "actual_files": actual_files,
        "missing_paths": missing,
        "extra_paths": extra,
        "mismatched_paths": mismatched,
        "path_leaks": path_leaks,
        "file_tree_hash": payload_tree_hash(actual_files),
        "status": status,
    }


def plugin_version_for_surface(repo_root: Path, surface: str) -> str:
    manifest_name = ".claude-plugin/plugin.json" if surface == "claude" else ".codex-plugin/plugin.json"
    manifest = json.loads((repo_root / "speckit-pro" / manifest_name).read_text(encoding="utf-8"))
    version = manifest.get("version")
    return version if isinstance(version, str) and version else "0.0.0"


def payload_trust_metadata_mismatches(payload_root: Path) -> list[str]:
    runner_root = payload_root / "speckit_pro_runner"
    manifest_path = runner_root / "speckit-pro-runner.manifest.json"
    checksum_path = runner_root / "speckit-pro-runner.sha256"
    manifest_rel = "speckit_pro_runner/speckit-pro-runner.manifest.json"
    checksum_rel = "speckit_pro_runner/speckit-pro-runner.sha256"
    runner_files = sorted(
        path
        for path in runner_root.rglob("*.py")
        if path.is_file() and "__pycache__" not in path.parts and not path.name.endswith(".pyc")
    )
    if not runner_files:
        return []

    actual = {path.relative_to(payload_root).as_posix(): sha256_file(path) for path in runner_files}
    mismatches: set[str] = set()

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        records = manifest.get("runner_files")
        if not isinstance(records, list):
            mismatches.add(manifest_rel)
        else:
            manifest_hashes: dict[str, str] = {}
            for record in records:
                if not isinstance(record, dict):
                    mismatches.add(manifest_rel)
                    continue
                path_record = record.get("path")
                value = path_record.get("value") if isinstance(path_record, dict) else None
                digest = record.get("sha256")
                if not isinstance(value, str) or not isinstance(digest, str):
                    mismatches.add(manifest_rel)
                    continue
                manifest_hashes[value] = digest
            if manifest_hashes != actual:
                mismatches.add(manifest_rel)
    except (OSError, json.JSONDecodeError):
        mismatches.add(manifest_rel)

    try:
        checksum_hashes = parse_payload_checksum(checksum_path)
        if checksum_hashes != actual:
            mismatches.add(checksum_rel)
    except OSError:
        mismatches.add(checksum_rel)

    return sorted(mismatches)


def parse_payload_checksum(path: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, separator, rel = line.partition("  ")
        if not separator or len(digest) != 64 or not rel:
            return {}
        records[rel] = digest
    return records


def scan_payload_files(root: Path, *, source_root: Path, surface: str) -> list[dict[str, Any]]:
    if not root.is_dir():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and "__pycache__" not in item.parts and not item.name.endswith(".pyc")):
        rel = path.relative_to(root).as_posix()
        source_path = infer_payload_source_path(rel, source_root, surface)
        records.append(
            {
                "path": rel,
                "source_path": source_path,
                "kind": payload_file_kind(rel),
                "transform": payload_transform(rel, source_path),
                "sha256": sha256_file(path),
                "byte_count": path.stat().st_size,
                "required": True,
            }
        )
    return records


def infer_payload_source_path(rel: str, source_root: Path, surface: str) -> str:
    if rel == ".claude-plugin/plugin.json":
        return "speckit-pro/.claude-plugin/plugin.json"
    if rel == ".codex-plugin/plugin.json":
        return "speckit-pro/.codex-plugin/plugin.json"
    if rel == "codex-hooks.json":
        return "speckit-pro/codex-hooks.json"
    if rel.startswith("codex-agents/"):
        return f"speckit-pro/{rel}"
    if rel.startswith("skills/"):
        candidate = source_root / rel
        codex_candidate = source_root / "codex-skills" / rel.removeprefix("skills/")
        if surface == "codex" and codex_candidate.exists():
            return f"speckit-pro/codex-skills/{rel.removeprefix('skills/')}"
        if candidate.exists():
            return f"speckit-pro/{rel}"
    if rel == "LICENSE":
        return "LICENSE"
    return f"speckit-pro/{rel}"


def payload_file_kind(path: str) -> str:
    parts = PurePosixPath(path).parts
    if path.endswith("plugin.json"):
        return "manifest"
    if parts and parts[0] in {"agents", "codex-agents"}:
        return "agent"
    if parts and parts[0] in {"hooks"} or path == "codex-hooks.json":
        return "hook"
    if parts and parts[0] == "skills":
        return "skill"
    if parts and parts[0] == "speckit_pro_runner":
        if path.endswith(".sha256"):
            return "checksum"
        if path.endswith(".manifest.json") or path.endswith("install_inventory.json"):
            return "trust_metadata"
        return "runner"
    if path in {"README.md", "CHANGELOG.md", "LICENSE"}:
        return "install_guidance" if path == "README.md" else "version_metadata"
    return "docs"


def payload_transform(path: str, source_path: str) -> str:
    if path == ".codex-plugin/plugin.json":
        return "manifest_rewrite"
    if "/SKILL.md" in path and "codex-skills" in source_path:
        return "codex_overlay"
    if "/SKILL.md" in path:
        return "claude_guard_strip"
    if source_path != f"speckit-pro/{path}" and path.startswith("skills/"):
        return "path_normalization"
    return "none"


def apply_payload_mutation(files: list[dict[str, Any]], mutation: dict[str, Any]) -> list[dict[str, Any]]:
    mutated = [dict(item) for item in files]
    remove_paths = {item for item in mutation.get("remove_paths", []) if isinstance(item, str)}
    if remove_paths:
        mutated = [item for item in mutated if item["path"] not in remove_paths]
    mismatch_paths = {item for item in mutation.get("mismatch_paths", []) if isinstance(item, str)}
    for item in mutated:
        if item["path"] in mismatch_paths:
            item["sha256"] = "0" * 64
    for extra in mutation.get("extra_files", []):
        if not isinstance(extra, dict):
            continue
        path = str(extra.get("path", "extra.txt"))
        if payload_path_leaks(path):
            continue
        content = str(extra.get("content", "extra"))
        mutated.append(
            {
                "path": path,
                "source_path": str(extra.get("source_path", "")),
                "kind": str(extra.get("kind", "docs")),
                "transform": str(extra.get("transform", "none")),
                "sha256": sha256_text(content),
                "byte_count": len(content.encode("utf-8")),
                "required": bool(extra.get("required", True)),
            }
        )
    return sorted(mutated, key=lambda item: item["path"])


def payload_path_leaks(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return path.startswith("/") or bool(re.match(r"^[A-Za-z]:", path)) or ".." in parts


def payload_tree_hash(files: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        [{"path": item["path"], "sha256": item["sha256"]} for item in sorted(files, key=lambda item: item["path"])],
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256_text(payload)


def payload_evidence_record(payload: dict[str, Any], mode: str, case: dict[str, Any], output_root: str) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for item in payload.get("files", []):
        if not isinstance(item, dict):
            continue
        path = normalize_posix_path(str(item.get("path", "")))
        content = str(item.get("content", ""))
        files.append({"path": path, "sha256": sha256_text(content), "byte_count": len(content.encode("utf-8"))})
    tree_payload = json.dumps(files, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": "1.0",
        "evidence_id": str(payload.get("evidence_id")),
        "payload_surface": str(payload.get("payload_surface")),
        "mode": mode,
        "input_root": f"{DEFAULT_PAYLOAD_CASES.as_posix()}#{case.get('case_id')}",
        "output_root": output_root,
        "file_tree_hash": sha256_text(tree_payload),
        "files": files,
        "release_payload_cutover": False,
        "status": "ok",
    }


def payload_artifacts(evidence: list[dict[str, Any]], output_root: Path, repo_root: Path, *, include_written: bool) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    if not include_written:
        return artifacts
    for item in evidence:
        path = output_root / payload_evidence_filename(item["payload_surface"])
        artifacts.append({"path": repo_relative(path, repo_root), "kind": "evidence"})
    return artifacts


def write_payload_evidence(evidence: list[dict[str, Any]], output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    for item in evidence:
        target = output_root / payload_evidence_filename(item["payload_surface"])
        target.write_text(json.dumps(item, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def payload_evidence_filename(surface: str) -> str:
    raw = str(surface).strip().replace("\\", "/")
    parts = [part for part in raw.split("/") if part not in {"", ".", ".."}]
    stem = parts[-1] if parts else "payload"
    safe = "".join(ch if ch.isalnum() or ch in ".-" else "-" for ch in stem.replace("_", "-"))
    while ".." in safe:
        safe = safe.replace("..", ".")
    safe = safe.strip(".-") or "payload"
    return f"{safe}-payload-evidence.json"


def command_plans(operation: str, repair_paths: list[str]) -> list[dict[str, Any]]:
    plans = [
        {
            "operation_id": operation,
            "argv": [sys.executable, "-m", "speckit_pro_runner"],
        }
    ]
    for path in repair_paths:
        plans.append(
            {
                "operation_id": f"repair:{path}",
                "argv": [sys.executable, "-m", "speckit_pro_runner"],
            }
        )
    return plans


def load_case(repo_root: Path, inputs: dict[str, Any], *, default_case_file: Path) -> dict[str, Any]:
    raw = inputs.get("case_file", default_case_file.as_posix())
    path_result = fixture_file_path(raw, repo_root)
    if is_diagnostic(path_result):
        return path_result
    try:
        document = json.loads(path_result.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return diagnostic(
            "invalid_case_file",
            "case fixture could not be loaded",
            details={"case_file": str(raw), "error": type(exc).__name__},
            remediation_summary="Use a valid JSON fixture case file.",
            remediation_actions=["Inspect the case fixture.", "Retry with a valid case_file path."],
        )
    cases = document.get("cases")
    if not isinstance(cases, list):
        return diagnostic("invalid_case_file", "case fixture must contain a cases array")
    case_id = inputs.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        case_id = str(cases[0].get("case_id")) if cases and isinstance(cases[0], dict) else ""
    for case in cases:
        if isinstance(case, dict) and case.get("case_id") == case_id:
            merged = dict(case)
            merged["_case_file"] = repo_relative(path_result, repo_root)
            return merged
    return diagnostic(
        "unknown_fixture_case",
        "requested fixture case was not found",
        details={"case_id": case_id, "case_file": repo_relative(path_result, repo_root)},
        remediation_summary="Use a case_id declared by the fixture file.",
        remediation_actions=["Inspect the case fixture.", "Retry with a known case_id."],
    )


def fixture_file_path(raw: Any, repo_root: Path) -> Path | dict[str, Any]:
    if not isinstance(raw, str) or not raw:
        return diagnostic("invalid_case_file", "case_file must be a non-empty string")
    path = resolve_path(raw, repo_root)
    if not is_relative_to(path.resolve(strict=False), repo_root.resolve(strict=False)):
        return diagnostic("invalid_case_file", "case_file must stay inside the repository")
    if not path.is_file():
        return diagnostic("invalid_case_file", "case_file does not exist", details={"case_file": raw})
    return path


def output_root_from_inputs(inputs: dict[str, Any], repo_root: Path) -> Path | dict[str, Any]:
    raw = inputs.get("output_root")
    if not isinstance(raw, str) or not raw:
        return diagnostic(
            "fixture_output_root_refused",
            "output_root is required for test payload evidence",
            remediation_summary="Use a fixture or temporary output root.",
            remediation_actions=["Set output_root under the XPLAT-007 fixture tree or a temp directory."],
        )
    output_root = resolve_path(raw, repo_root)
    resolved = output_root.resolve(strict=False)
    fixture_root = (repo_root / FIXTURE_BOUNDARY).resolve(strict=False)
    temp_root = Path(tempfile.gettempdir()).resolve(strict=False)
    if is_relative_to(resolved, fixture_root) or is_relative_to(resolved, temp_root):
        return output_root
    return diagnostic(
        "fixture_output_root_refused",
        "payload evidence output_root must be fixture or temporary scoped",
        details={"output_root": raw, "fixture_root": repo_relative(fixture_root, repo_root)},
        remediation_summary="Keep payload evidence writes in fixture or temp roots only.",
        remediation_actions=["Use tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates/.", "Or use an OS temp directory."],
    )


def install_root_from_case(case: dict[str, Any], repo_root: Path) -> Path | dict[str, Any]:
    raw = case.get("install_root")
    if not isinstance(raw, str) or not raw:
        return diagnostic("fixture_install_root_refused", "install_root is required")
    install_root = resolve_path(raw, repo_root)
    resolved = install_root.resolve(strict=False)
    boundary = (repo_root / FIXTURE_BOUNDARY).resolve(strict=False)
    if is_relative_to(resolved, boundary):
        return install_root
    return diagnostic(
        "fixture_install_root_refused",
        "install verification refuses roots outside the XPLAT-007 fixture boundary",
        details={"install_root": normalize_path_text(raw), "fixture_root": repo_relative(boundary, repo_root)},
        remediation_summary="Use a fake-home install root under the XPLAT-007 fixture tree.",
        remediation_actions=["Move install_root under tests/speckit-pro/layer4-scripts/fixtures/xplat-007-gates.", "Retry verify-install."],
        deferred_to="XPLAT-008",
    )


def load_install_inventory(repo_root: Path, case: dict[str, Any]) -> list[dict[str, str]]:
    inventory_path = repo_root / INSTALL_INVENTORY
    try:
        document = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return diagnostic(
            "malformed_inventory",
            "install inventory could not be loaded",
            details={"path": INSTALL_INVENTORY.as_posix(), "error": type(exc).__name__},
        )
    files = document.get("files")
    if not isinstance(files, list):
        return diagnostic("malformed_inventory", "install inventory files must be an array")
    normalized: list[dict[str, str]] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        path = normalize_posix_path(str(item.get("path", "")))
        content = str(item.get("content", ""))
        digest = str(item.get("sha256", "skip"))
        normalized.append({"path": path, "content": normalized_content(content, case), "sha256": digest})
    return normalized


def normalized_content(content: str, case: dict[str, Any]) -> str:
    if case.get("installed_files") == "from_inventory_crlf":
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        return normalized.replace("\n", "\r\n")
    return content


def bundled_agent_count(inventory: list[dict[str, str]]) -> int:
    return sum(1 for record in inventory if "agent" in PurePosixPath(record["path"]).parts or record["path"].startswith("agents/"))


def base_data(entry: Any, operation: str, status: str) -> dict[str, Any]:
    gate_status = "pass"
    if status in {"expected_failure", "subprocess_failure"}:
        gate_status = "fail"
    elif status == "missing_prerequisite":
        gate_status = "skipped"
    elif status == "input_error":
        gate_status = "input_error"
    return {
        "gate": {
            "gate_id": entry.helper_id,
            "operation": operation,
            "gate_status": gate_status,
            "promoted": status != "input_error",
            "blocking": status != "ok",
            "comparison_ids": [f"us2-{operation}"],
            "promotion_record": PROMOTION_RECORD,
        },
        "artifacts": [{"path": PROMOTION_RECORD, "kind": "fixture"}],
    }


def find_repo_root(start: Path) -> Path | None:
    candidates = [start, *start.parents] if start.is_dir() else [start.parent, *start.parent.parents]
    for candidate in candidates:
        if (candidate / "speckit-pro" / "speckit_pro_runner").is_dir() and (candidate / "tests" / "speckit-pro").is_dir():
            return candidate.resolve(strict=False)
    return None


def resolve_path(raw: str, repo_root: Path) -> Path:
    value = normalize_path_text(raw)
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def normalize_path_text(raw: str) -> str:
    return raw.replace("\\", "/")


def normalize_posix_path(raw: str) -> str:
    value = normalize_path_text(raw)
    parts = PurePosixPath(value).parts
    if value.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        return value.strip("/")
    return PurePosixPath(value).as_posix()


def repo_relative(path: Path, repo_root: Path) -> str:
    return path.resolve(strict=False).relative_to(repo_root.resolve(strict=False)).as_posix()


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_diagnostic(value: Any) -> bool:
    return isinstance(value, dict) and value.get("source") == "runner" and "code" in value
