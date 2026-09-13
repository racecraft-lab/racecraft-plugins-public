"""Provider-free, fail-closed corpus accounting and native launch selection."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from trigger_evidence import case_id

SCHEMA_VERSION = "trigger-inventory/v1"
SELECTION_POLICY = "trigger-pr-selection/v1"
PROTECTED_POSITIONS = {
    "speckit-autopilot": (18,), "speckit-coach": (23,), "speckit-install": (13,),
    "speckit-prd": (10, 12), "speckit-scaffold-spec": (19, 20),
}


class InventoryError(ValueError):
    """An inventory cannot account for its frozen inputs and current corpus."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise InventoryError(message)


def load_inventory(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), "inventory must be an object")
    return value


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def query_shape(row: dict) -> dict:
    require(isinstance(row.get("query"), str) and bool(row["query"].strip()), "query must be non-empty text")
    require(type(row.get("should_trigger")) is bool, "should_trigger must be boolean")
    return {"query": row["query"], "should_trigger": row["should_trigger"]}


def boundary_shape(row: dict) -> None:
    boundaries = row["boundaries"]
    require(isinstance(boundaries, list) and bool(boundaries), "boundaries must be a non-empty list")
    require(all(isinstance(value, str) and bool(value) for value in boundaries), "boundaries must contain text")


def roster_row(row: dict) -> dict:
    return {key: row[key] for key in ("case_id", "host", "skill", "query", "should_trigger")}


def frozen_originals(inventory: dict) -> dict:
    frozen = {}
    corpora = set()
    for source in inventory["source_corpora"]:
        host, skill = source["host"], source["skill"]
        require(host in {"claude", "codex"}, "unknown host")
        require((host, skill) not in corpora, "duplicate source corpus")
        corpora.add((host, skill))
        expected_path = f"{'evals' if host == 'claude' else 'codex-evals'}/{skill}-trigger.json"
        require(source["path"] == expected_path and PurePosixPath(skill).name == skill, "invalid source path")
        content = source["original_utf8"]
        require(hashlib.sha256(content.encode()).hexdigest() == source["sha256"], "source bytes do not match digest")
        for position, entry in enumerate(json.loads(content), 1):
            require(set(entry) == {"query", "should_trigger"}, "frozen corpus schema changed")
            query_shape(entry)
            frozen[(host, skill, position)] = {**entry, "case_id": case_id(host, skill, entry)}
    require(len(corpora) == 23 and len(frozen) == 438, "original corpus accounting must retain 23 corpora and 438 occurrences")
    return frozen


def validate_active(inventory: dict, layer_root: Path) -> dict:
    active = {}
    per_corpus = defaultdict(list)
    repeats = defaultdict(list)
    for row in inventory["active"]:
        entry = query_shape(row)
        boundary_shape(row)
        identity = case_id(row["host"], row["skill"], entry)
        require(identity == row["case_id"] and identity not in active, "forged or duplicate active identity")
        require(row["category"] in {"explicit", "natural", "negative"}, "unknown active category")
        require((row["category"] == "negative") == (row["should_trigger"] is False), "category and label disagree")
        require(bool(row["rationale"].strip()) and bool(row["intent"].strip()) and bool(row["boundaries"]), "missing active rationale or boundary")
        if row["category"] == "explicit":
            marker = ("/speckit-pro:" if row["host"] == "claude" else "$") + row["skill"]
            require(row["query"].startswith(marker + " "), "explicit smoke must use textual host invocation")
        active[identity] = row
        per_corpus[(row["host"], row["skill"])].append(row)
        repeats[(row["host"], row["query"])].append(row)
    expected_corpora = {(row["host"], row["skill"]) for row in inventory["source_corpora"]}
    require(set(per_corpus) == expected_corpora, "missing or extra active host/skill corpus")
    for source in inventory["source_corpora"]:
        rows = per_corpus[(source["host"], source["skill"])]
        counts = Counter(row["category"] for row in rows)
        require(counts["explicit"] >= 1 and counts["natural"] >= 3 and counts["negative"] >= 3, "each corpus needs distinct explicit, three natural positives and three negatives")
        actual = json.loads((layer_root / source["path"]).read_text(encoding="utf-8"))
        require(actual == [query_shape(row) for row in rows], "active inventory and on-disk corpus disagree")
    for rows in repeats.values():
        if len(rows) > 1:
            require(all(row["skill"] in row.get("repeat_rationale", "") for row in rows), "repeated cross-skill prompt needs target-specific rationale")
    return active


def validate_dispositions(inventory: dict, frozen: dict, active: dict) -> None:
    seen = set()
    sources = defaultdict(set)
    for row in inventory["originals"]:
        boundary_shape(row)
        require(type(row["original_position"]) is int, "original position must be integer, not boolean")
        key = (row["host"], row["skill"], row["original_position"])
        require(key in frozen and key not in seen, "missing, extra or duplicate original occurrence")
        seen.add(key)
        require({**query_shape(row), "case_id": row["case_id"]} == frozen[key], "original identity or bytes changed")
        require(row["disposition"] in {"retained", "consolidated", "rewritten", "retired"}, "unknown disposition")
        require(bool(row["rationale"].strip()) and bool(row["intent"].strip()), "disposition needs intent and rationale")
        covered_by = row["covered_by"]
        require(isinstance(covered_by, list) and bool(covered_by) and len(set(covered_by)) == len(covered_by), "every disposition needs explicit unique coverage mapping")
        require(all(identity in active for identity in covered_by), "coverage mapping targets missing active case")
        representatives = [active[identity] for identity in covered_by]
        for identity in covered_by:
            sources[identity].add(row["case_id"])
        require(all(item["host"] == row["host"] and item["skill"] == row["skill"] and item["should_trigger"] == row["should_trigger"] for item in representatives), "coverage cannot silently cross host, target or label")
        boundaries = {boundary for item in representatives for boundary in item["boundaries"]}
        require(bool(row["boundaries"]) and set(row["boundaries"]) <= boundaries, "original routing boundary has no active coverage")
        if row["disposition"] == "retained":
            require(covered_by == [row["case_id"]], "retained original must keep exact identity")
    require(seen == set(frozen), "not every original occurrence has a disposition")
    for identity, row in active.items():
        require(isinstance(row["source_case_ids"], list) and len(row["source_case_ids"]) == len(set(row["source_case_ids"])), "source identities must be a unique list")
        require(set(row["source_case_ids"]) == sources[identity], "active source membership disagrees with dispositions")
        require(bool(sources[identity]) or row["category"] == "explicit", "new non-smoke case requires an explicit rewritten original mapping")


def validate_inventory(inventory: dict, layer_root: Path) -> dict:
    """Structural coverage is necessary, not evidence of semantic/native acceptance."""
    try:
        require(inventory["schema_version"] == SCHEMA_VERSION, "unsupported inventory version")
        frozen = frozen_originals(inventory)
        active = validate_active(inventory, layer_root)
        validate_dispositions(inventory, frozen, active)
        protected = {row["case_id"] for (host, skill, position), row in frozen.items() if position in PROTECTED_POSITIONS.get(skill, ())}
        require(len(protected) == 14 and set(inventory["protected_case_ids"]) == protected and len(inventory["protected_case_ids"]) == 14, "protected sentinel set changed")
        require(protected <= set(active), "protected original identity removed")
        pilot = inventory["pilot_case_ids"]
        require(len(pilot) == len(set(pilot)) == 8 and set(pilot) <= set(active), "pilot must select eight distinct active identities")
        for host in ("claude", "codex"):
            selected = [active[identity] for identity in pilot if active[identity]["host"] == host]
            require(len(selected) == 4, "pilot needs four cases per host")
            require(any(row["category"] == "natural" for row in selected), "pilot missing natural discovery")
            require(any(row["case_id"] in protected and not row["should_trigger"] for row in selected), "pilot missing protected negative")
            require(any("no-speckit" in boundary for row in selected for boundary in row["boundaries"]), "pilot missing no-op negative")
            require(any(":reject:install" in boundary for row in selected for boundary in row["boundaries"]), "pilot missing host/catalog boundary")
        return {"original_cases": len(frozen), "active_cases": len(active), "corpora": len(inventory["source_corpora"]), "protected_cases": len(protected), "original_launches": len(frozen) * 6, "full_launches": len(active) * 6, "target_200_met": len(active) <= 200, "minimum_reduction_met": len(active) <= 219, "review_status": inventory["review_status"]}
    except (KeyError, TypeError, AttributeError, json.JSONDecodeError, OSError) as error:
        raise InventoryError(f"malformed inventory: {error}") from error


def changed_skill_from_path(path: str, known: set) -> str | None:
    parts = PurePosixPath(path).parts
    if len(parts) >= 4 and parts[:2] in (("speckit-pro", "skills"), ("speckit-pro", "codex-skills")):
        return parts[2] if parts[2] in known else None
    if len(parts) == 5 and parts[:3] == ("tests", "speckit-pro", "layer2-trigger") and parts[3] in {"evals", "codex-evals"}:
        name = parts[4].removesuffix("-trigger.json")
        return name if name in known else None
    return None


def plan_inventory(inventory: dict, layer_root: Path, scope: str, *, changed_skills: list[str] | None = None, changed_paths: list[str] | None = None, inventory_path: Path | None = None) -> dict:
    report = validate_inventory(inventory, layer_root)
    inventory_bytes = (inventory_path or layer_root / "case-inventory.json").read_bytes()
    require(json.loads(inventory_bytes) == inventory, "inventory changed after loading; rerun planning")
    require(scope in {"full", "pr-core", "pilot"}, "unknown qualification scope")
    known = {row["skill"] for row in inventory["active"]}
    changed = set(changed_skills or [])
    paths = [changed_skill_from_path(path, known) for path in changed_paths or []]
    expanded = scope == "pr-core" and (not changed and not paths or not changed <= known or None in paths)
    changed.update(skill for skill in paths if skill)
    actual_scope = "full" if expanded else scope
    active = inventory["active"]
    if actual_scope == "pilot":
        identities = set(inventory["pilot_case_ids"])
        active = [row for row in active if row["case_id"] in identities]
    elif actual_scope == "pr-core":
        protected = set(inventory["protected_case_ids"])
        active = [row for row in active if row["skill"] in changed or row["case_id"] in protected or any(set(boundary.split(":")) & changed for boundary in row["boundaries"])]
    arms = ["candidate"] if actual_scope == "pilot" else ["baseline", "candidate"]
    schedules = ["serial", "two-worker"] if actual_scope == "pilot" else ["serial"]
    roster = [roster_row(row) for row in active]
    return {
        "schema_version": "trigger-selection/v1", "selection_policy": SELECTION_POLICY,
        "requested_scope": scope, "qualification_scope": actual_scope,
        "expanded_to_full": expanded, "changed_skills": sorted(changed), "roster": roster,
        "trials": 3, "threshold": 0.5, "arms": arms, "schedules": schedules,
        "launch_count": len(active) * 3 * len(arms) * len(schedules),
        "corpus_sha256": canonical_sha256(roster),
        "inventory_sha256": hashlib.sha256(inventory_bytes).hexdigest(),
        "qualification_established": False, "launch_authorized": False,
        "required_before_launch": [
            "independent semantic inventory review",
            "reviewed trigger-experiment/v1 with exact model, CLI, observer, catalog, fixture and controlled-difference pins",
            "explicit campaign approval and launch budget",
        ],
        "inventory_report": report,
    }
