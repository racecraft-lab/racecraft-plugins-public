"""Stage and qualify provider-native trigger-selection evidence.

The transport adapter owns provider processes and raw capture.  This module
owns the narrower trigger contract: a complete controlled skill catalog and a
qualified canonical activation derived from native evidence rather than prose.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import sys
from typing import Any, Mapping

from trigger_evidence import description_override


SCHEMA_VERSION = "native-trigger-stage/v1"
QUALIFICATION_SCHEMA_VERSION = "native-trigger-qualification/v1"
_NO_SKILL_NAME = "no-speckit-skill"
_SKILL_NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
_PLUGIN_NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
_HELPERS: dict[str, object] = {}


class TriggerEvidenceError(ValueError):
    """Trigger staging or evidence cannot establish an unambiguous outcome."""


@dataclass(frozen=True)
class TriggerStage:
    """Exact controlled catalog and attempt-bound evidence inputs."""

    host: str
    target_skill: str
    native_target: str
    namespace: str | None
    stage_root: Path
    sibling_skills: tuple[str, ...]
    skill_markers: dict[str, str]
    witnesses: dict[str, dict[str, str]]
    source_identities: dict[str, dict[str, object]]
    staged_identities: dict[str, dict[str, object]]
    controlled_description_identity: dict[str, object]
    trial_id_sha256: str
    catalog_sha256: str
    attempt_sha256: str

    def as_dict(self) -> dict[str, object]:
        """Return a serializable copy suitable for runtime evidence."""
        return {
            "schema_version": SCHEMA_VERSION,
            "host": self.host,
            "target_skill": self.target_skill,
            "native_target": self.native_target,
            "namespace": self.namespace,
            "stage_root": str(self.stage_root),
            "sibling_skills": list(self.sibling_skills),
            "skill_markers": dict(self.skill_markers),
            "witnesses": {name: dict(value) for name, value in self.witnesses.items()},
            "source_identities": {name: dict(value) for name, value in self.source_identities.items()},
            "staged_identities": {name: dict(value) for name, value in self.staged_identities.items()},
            "controlled_description_identity": dict(self.controlled_description_identity),
            "trial_id_sha256": self.trial_id_sha256,
            "catalog_sha256": self.catalog_sha256,
            "attempt_sha256": self.attempt_sha256,
        }


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TriggerEvidenceError(message)


def _digest(value: object) -> str:
    digest = hashlib.sha256()
    encoder = json.JSONEncoder(
        sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    )
    for chunk in encoder.iterencode(value):
        digest.update(chunk.encode("utf-8"))
    return digest.hexdigest()


def _helpers(host: str) -> object:
    cached = _HELPERS.get(host)
    if cached is not None:
        return cached
    filename = "run-trigger-evals.py" if host == "claude" else "run_codex_evals.py"
    path = Path(__file__).resolve().parents[1] / "layer2-trigger" / filename
    name = f"native_eval_trigger_{host}_helpers"
    spec = importlib.util.spec_from_file_location(name, path)
    _require(spec is not None and spec.loader is not None, f"{host} trigger helpers are unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    _HELPERS[host] = module
    return module


def _skill_name(value: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), "target skill is empty")
    name = value.rsplit(":", 1)[-1].removeprefix("$")
    _require(_SKILL_NAME.fullmatch(name) is not None, "target skill name is malformed")
    return name


def _file_identity(path: Path, relative: str) -> dict[str, object]:
    try:
        status = path.lstat()
        payload = path.read_bytes()
    except OSError as exc:
        raise TriggerEvidenceError(f"skill source is unavailable: {relative}") from exc
    _require(stat.S_ISREG(status.st_mode) and not stat.S_ISLNK(status.st_mode),
             f"skill source must be a regular non-symlink file: {relative}")
    return {"path": relative, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def _source_catalog(
    root: Path, target: str, helpers: object,
) -> tuple[dict[str, Path], dict[str, dict[str, object]]]:
    try:
        root_status = root.lstat()
        root.resolve(strict=True)
        entries = sorted(root.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise TriggerEvidenceError("skill source root is unavailable") from exc
    _require(stat.S_ISDIR(root_status.st_mode) and not stat.S_ISLNK(root_status.st_mode),
             "skill source root must be a real directory")
    sources: dict[str, Path] = {}
    for entry in entries:
        try:
            status = entry.lstat()
        except OSError as exc:
            raise TriggerEvidenceError(f"could not inspect source catalog entry: {entry.name}") from exc
        _require(not stat.S_ISLNK(status.st_mode), f"skill source catalog entry is a symlink: {entry.name}")
        if not stat.S_ISDIR(status.st_mode):
            continue
        _require(_SKILL_NAME.fullmatch(entry.name) is not None, f"skill source name is malformed: {entry.name}")
        skill_file = entry / "SKILL.md"
        _file_identity(skill_file, f"{entry.name}/SKILL.md")
        sources[entry.name] = skill_file
    _require(target in sources, f"target skill is absent from source catalog: {target}")
    legacy_siblings = {path.name for path in helpers.sibling_skill_dirs(sources[target])}
    _require(legacy_siblings == set(sources) - {target}, "legacy sibling discovery did not cover the full catalog")
    identities = {
        name: _file_identity(path, f"{name}/SKILL.md") for name, path in sorted(sources.items())
    }
    return sources, identities


def _controlled_description(path: str | Path | None, default: str) -> tuple[str, dict[str, object]]:
    try:
        value = description_override(str(path) if path is not None else None, default)
    except (OSError, UnicodeError, ValueError) as exc:
        raise TriggerEvidenceError("controlled description override is invalid") from exc
    identity: dict[str, object] = {
        "source": "default" if path is None else "override",
        "value_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
    }
    if path is not None:
        source = Path(path)
        try:
            status = source.lstat()
            payload = source.read_bytes()
        except OSError as exc:
            raise TriggerEvidenceError("controlled description override is unavailable") from exc
        _require(stat.S_ISREG(status.st_mode) and not stat.S_ISLNK(status.st_mode),
                 "controlled description override must be a regular non-symlink file")
        identity.update(path=str(source.resolve()), bytes=len(payload),
                        source_sha256=hashlib.sha256(payload).hexdigest())
    return value, identity


def _replace_no_op_description(skill_file: Path, old: str, new: str) -> None:
    text = skill_file.read_text(encoding="utf-8")
    needle = f"description: {old}"
    _require(text.count(needle) == 1, "staged no-op description was not uniquely identifiable")
    skill_file.write_text(text.replace(needle, f"description: {new}", 1), encoding="utf-8")


def _staged_identities(root: Path, relative_root: str, names: set[str]) -> dict[str, dict[str, object]]:
    return {
        name: _file_identity(root / relative_root / name / "SKILL.md", f"{relative_root}/{name}/SKILL.md")
        for name in sorted(names)
    }


def _witness_identities(witnesses: Mapping[str, Mapping[str, str]]) -> dict[str, dict[str, str]]:
    """Relocate attempt-local absolute paths while retaining exact witness bytes."""
    return {
        name: {
            "marker": witness["marker"],
            "relative_path": witness["relative_path"],
            "sha256": witness["sha256"],
            "body_sha256": hashlib.sha256(witness["body"].encode("utf-8")).hexdigest(),
        }
        for name, witness in sorted(witnesses.items())
    }


def _attempt_digest(
    catalog_sha256: str,
    trial_id_sha256: str,
    markers: Mapping[str, str],
    staged_identities: Mapping[str, Mapping[str, object]],
    witnesses: Mapping[str, Mapping[str, str]],
) -> str:
    return _digest([
        catalog_sha256, trial_id_sha256, markers, staged_identities,
        _witness_identities(witnesses),
    ])


def _stage_claude(
    helpers: object, sources: dict[str, Path], stage: Path, target: str,
    plugin_name: str, token: str, no_op_description: str,
) -> tuple[str, dict[str, str], dict[str, dict[str, str]], dict[str, dict[str, object]]]:
    _require(not any(stage.iterdir()), "Claude trigger plugin root must be empty")
    siblings = {name: path for name, path in sources.items() if name != target}
    _skill_dir, native_target = helpers.stage_measurement_plugin(
        sources[target], stage, plugin_name, target, f"CLAUDE_TRIGGER_TRIAL:{token}", siblings,
    )
    no_op = helpers.NO_SPECKIT_SKILL_NAME
    _replace_no_op_description(
        stage / "skills" / no_op / "SKILL.md", helpers.NO_SPECKIT_SKILL_DESCRIPTION, no_op_description,
    )
    names = {*sources, no_op}
    _require({path.parent.name for path in (stage / "skills").glob("*/SKILL.md")} == names,
             "Claude staged catalog is incomplete or ambiguous")
    for name, source in sources.items():
        staged = stage / "skills" / name / "SKILL.md"
        _require(helpers.source_description_lines(staged) == helpers.source_description_lines(source),
                 f"Claude staged description differs from source: {name}")
    return native_target, {}, {}, _staged_identities(stage, "skills", names)


def _stage_codex(
    helpers: object, sources: dict[str, Path], stage: Path, target: str,
    token: str, no_op_description: str,
) -> tuple[str, dict[str, str], dict[str, dict[str, str]], dict[str, dict[str, object]]]:
    skill_root = stage / ".agents" / "skills"
    _require(not skill_root.exists(), "Codex staged skill catalog already exists")
    target_marker = helpers.selection_marker(target, token)
    helpers.stage_repository_skill(sources[target], stage, target, target_marker)
    _descriptions, sibling_markers = helpers.stage_sibling_skills(sources[target], stage, token)
    no_op = helpers.NO_SPECKIT_SKILL_NAME
    _replace_no_op_description(
        skill_root / no_op / "SKILL.md", helpers.NO_SPECKIT_SKILL_DESCRIPTION, no_op_description,
    )
    names = {*sources, no_op}
    _require({path.parent.name for path in skill_root.glob("*/SKILL.md")} == names,
             "Codex staged catalog is incomplete or ambiguous")
    for name, source in sources.items():
        _require(helpers.source_skill_description(skill_root / name / "SKILL.md")
                 == helpers.source_skill_description(source),
                 f"Codex staged description differs from source: {name}")
    by_skill = {target: target_marker, **sibling_markers}
    witnesses = helpers.skill_witnesses(stage, by_skill)
    marker_to_skill = {marker: name for name, marker in by_skill.items()}
    _require(len(marker_to_skill) == len(names), "Codex staged markers are duplicated")
    return target, marker_to_skill, witnesses, _staged_identities(stage, ".agents/skills", names)


def stage_trigger_catalog(
    host: str,
    source_root: str | Path,
    stage_root: str | Path,
    target_skill: str,
    trial_id: str,
    *,
    plugin_name: str = "speckit-pro-trigger",
    no_op_description_path: str | Path | None = None,
) -> TriggerStage:
    """Stage a complete controlled trigger catalog without launching a provider.

    ``trial_id`` identifies a logical trial and must remain stable when that
    same trial is resumed.  A different logical trial must use a different id.
    The attempt hash includes the resulting exact marker-bearing staged bytes.
    """
    _require(host in {"claude", "codex"}, f"unsupported trigger host: {host}")
    target = _skill_name(target_skill)
    _require(isinstance(trial_id, str) and bool(trial_id.strip()), "trial_id is empty")
    _require(isinstance(plugin_name, str) and _PLUGIN_NAME.fullmatch(plugin_name) is not None,
             "trigger plugin name is malformed")
    expected_root = "skills" if host == "claude" else "codex-skills"
    source_path = Path(source_root)
    _require(source_path.name == expected_root, f"{host} trigger source root must be named {expected_root}")
    stage = Path(stage_root)
    try:
        if stage.exists():
            status = stage.lstat()
            _require(stat.S_ISDIR(status.st_mode) and not stat.S_ISLNK(status.st_mode),
                     "trigger stage root must be a real directory")
        else:
            stage.mkdir(parents=False, mode=0o700)
        stage = stage.resolve(strict=True)
    except OSError as exc:
        raise TriggerEvidenceError("trigger stage root is unavailable") from exc
    helpers = _helpers(host)
    sources, source_identities = _source_catalog(source_path, target, helpers)
    default_description = helpers.NO_SPECKIT_SKILL_DESCRIPTION
    no_op_description, description_identity = _controlled_description(
        no_op_description_path, default_description,
    )
    token = hashlib.sha256(trial_id.encode("utf-8")).hexdigest()[:32]
    if host == "claude":
        native_target, markers, witnesses, staged_identities = _stage_claude(
            helpers, sources, stage, target, plugin_name, token, no_op_description,
        )
        namespace: str | None = plugin_name
    else:
        native_target, markers, witnesses, staged_identities = _stage_codex(
            helpers, sources, stage, target, token, no_op_description,
        )
        namespace = None
    _require(
        source_identities
        == {name: _file_identity(path, f"{name}/SKILL.md") for name, path in sorted(sources.items())},
        "source skill bytes changed during trigger staging",
    )
    sibling_skills = tuple(sorted(({*sources, helpers.NO_SPECKIT_SKILL_NAME}) - {target}))
    catalog_input = {
        "schema_version": SCHEMA_VERSION,
        "host": host,
        "target_skill": target,
        "namespace": namespace,
        "siblings": sibling_skills,
        "source_identities": source_identities,
        "controlled_description_identity": description_identity,
        "marker_template": "CODEX_SKILL_SELECTED:{skill}-{sha256(trial_id)[:32]}"
        if host == "codex" else "CLAUDE_TRIGGER_TRIAL:{sha256(trial_id)[:32]}",
    }
    catalog_sha256 = _digest(catalog_input)
    trial_id_sha256 = hashlib.sha256(trial_id.encode("utf-8")).hexdigest()
    attempt_sha256 = _attempt_digest(
        catalog_sha256, trial_id_sha256, markers, staged_identities, witnesses,
    )
    return TriggerStage(
        host, target, native_target, namespace, stage, sibling_skills, markers, witnesses,
        source_identities, staged_identities, description_identity, trial_id_sha256,
        catalog_sha256, attempt_sha256,
    )


def _observation(value: Mapping[str, object]) -> tuple[list[str], list[Mapping[str, object]]]:
    _require(isinstance(value, Mapping), "normalized trigger observation must be an object")
    _require(value.get("completed") is True and value.get("error") is None,
             "trigger observation is incomplete or failed")
    _require(isinstance(value.get("final_text"), str), "trigger final_text is malformed")
    activations = value.get("activations")
    calls = value.get("tool_calls")
    _require(isinstance(activations, list)
             and all(isinstance(item, str) and item for item in activations),
             "trigger activations are malformed")
    _require(isinstance(calls, list) and all(isinstance(call, Mapping) for call in calls),
             "trigger tool_calls are malformed")
    _require(isinstance(value.get("artifacts"), dict) and isinstance(value.get("usage"), dict),
             "trigger observation omitted artifacts or usage")
    metadata = value.get("native_metadata")
    _require(metadata is None or isinstance(metadata, dict), "trigger native_metadata is malformed")
    return list(activations), list(calls)


def _call(call: Mapping[str, object]) -> tuple[str, Mapping[str, object], bool, object]:
    name, inputs, success = call.get("name"), call.get("input"), call.get("success")
    _require(isinstance(name, str) and bool(name) and isinstance(inputs, Mapping)
             and type(success) is bool and "output" in call,
             "trigger tool call is malformed or truncated")
    return name, inputs, success, call["output"]


def _canonical_claude_skill(stage: TriggerStage, native: str) -> str:
    roster = {stage.target_skill, *stage.sibling_skills}
    if native in roster:
        return native
    prefix = str(stage.namespace) + ":"
    _require(native.startswith(prefix) and native[len(prefix):] in roster,
             f"Claude selected an unstaged skill: {native}")
    return native[len(prefix):]


def _qualify_claude(stage: TriggerStage, calls: list[Mapping[str, object]]) -> tuple[list[str], list[str]]:
    selected: list[str] = []
    for call in calls:
        name, inputs, success, _output = _call(call)
        _require(name == "Skill", f"Claude used an undeclared trigger tool: {name}")
        _require(success, "Claude Skill invocation failed")
        native = inputs.get("skill")
        _require(isinstance(native, str) and bool(native), "Claude Skill invocation omitted its target")
        selected.append(_canonical_claude_skill(stage, native))
    _require(len(selected) <= 1, "Claude trigger evidence has multiple or conflicting Skill activations")
    return selected, []


def _codex_markers(stage: TriggerStage, text: str, helpers: object) -> tuple[str | None, str | None]:
    emitted = helpers.MARKER_PATTERN.findall(text)
    unknown = sorted(set(emitted) - set(stage.skill_markers))
    _require(not unknown, "Codex returned an unknown or stale trial marker")
    _require(len(emitted) <= 1, "Codex returned repeated or conflicting trial markers")
    if not emitted:
        return None, None
    marker = emitted[0]
    first = next((line.strip() for line in text.splitlines() if line.strip()), None)
    _require(first == marker, "Codex trial marker was not first in the completed response")
    return marker, stage.skill_markers[marker]


def _qualify_codex(
    stage: TriggerStage, text: str, calls: list[Mapping[str, object]], helpers: object,
) -> tuple[list[str], list[str]]:
    reads: list[str] = []
    for call in calls:
        name, inputs, success, output = _call(call)
        _require(name == "command_execution", f"Codex used an undeclared trigger tool: {name}")
        _require(success, "Codex trigger command failed")
        command = inputs.get("command")
        _require(isinstance(command, str) and bool(command) and isinstance(output, str),
                 "Codex skill read is malformed or truncated")
        match = helpers._codex_body_read_match(command, output, stage.witnesses)
        _require(match is not None, "Codex command was not an exact staged skill-file read")
        reads.append(match[0])
    _require(len(reads) <= 1, "Codex read multiple or conflicting staged skill files")
    _marker, marked_skill = _codex_markers(stage, text, helpers)
    if marked_skill is None:
        _require(not reads, "Codex skill-file read was not paired with a fresh trial marker")
        return [], []
    _require(len(reads) == 1, "Codex marker was not corroborated by a successful staged skill-file read")
    _require(reads[0] == marked_skill, "Codex marker conflicts with the staged skill-file read")
    return [marked_skill], reads


def qualify_trigger_observation(stage: TriggerStage, observation: Mapping[str, object]) -> dict[str, Any]:
    """Return canonical qualified activations or reject unverifiable evidence.

    A completed wrong selection and a completed no-selection remain valid
    behavioral outcomes.  Only malformed, incomplete, conflicting, or
    uncorroborated evidence raises ``TriggerEvidenceError``.
    """
    _require(isinstance(stage, TriggerStage), "trigger stage contract is malformed")
    relative_root = "skills" if stage.host == "claude" else ".agents/skills"
    expected_names = {stage.target_skill, *stage.sibling_skills}
    current_identities = _staged_identities(stage.stage_root, relative_root, expected_names)
    _require(current_identities == stage.staged_identities,
             "staged trigger skill bytes changed after staging")
    try:
        current_attempt = _attempt_digest(
            stage.catalog_sha256, stage.trial_id_sha256, stage.skill_markers,
            current_identities, stage.witnesses,
        )
    except (KeyError, TypeError) as exc:
        raise TriggerEvidenceError("trigger stage witness contract is malformed") from exc
    _require(current_attempt == stage.attempt_sha256, "trigger stage attempt identity changed")
    captured, calls = _observation(observation)
    if stage.host == "claude":
        qualified, consulted = _qualify_claude(stage, calls)
        method = "completed-native-skill-call"
    else:
        qualified, consulted = _qualify_codex(
            stage, str(observation["final_text"]), calls, _helpers("codex"),
        )
        method = "successful-skill-file-read-plus-trial-marker"
    _require(captured == qualified, "captured activations disagree with qualified native trigger evidence")
    canonical = [name for name in qualified if name != _NO_SKILL_NAME]
    result = dict(observation)
    result["activations"] = canonical
    metadata = dict(result.get("native_metadata") or {})
    metadata["trigger_qualification"] = {
        "schema_version": QUALIFICATION_SCHEMA_VERSION,
        "method": method,
        "stage_attempt_sha256": stage.attempt_sha256,
        "actual_activations": list(qualified),
        "canonical_activations": list(canonical),
        "consulted_skills": list(consulted),
    }
    result["native_metadata"] = metadata
    return result


__all__ = ["TriggerEvidenceError", "TriggerStage", "qualify_trigger_observation", "stage_trigger_catalog"]
