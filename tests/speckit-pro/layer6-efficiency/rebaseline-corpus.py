#!/usr/bin/env python3
"""Rebaseline the Layer 6 governed role corpus against live agent source bytes.

The corpus binds a sha256 chain over the shipped agent definitions, so editing
any agent restales it and the qualification tests fail with "source digest does
not match role source bytes". This script is that regeneration step.

Default mode rewrites, for every role in ``GOVERNED_ROLE_ORDER``:

* ``fixtures-codex/<role>/fixture.json`` with the role's live source digest and
  freshly derived route digests;
* ``fixtures-codex/corpus-manifest.json`` with those fixtures and a corpus
  digest recomputed over the written fixture bytes;
* ``fixtures/claude-agent-roster-rebaseline-v2.json`` with each shipped Claude
  agent's source digest and the catalog digest that covers the record.

``fixture_binding.fixture_digest`` is an identity digest over the fixture ID
rather than a content digest, so it is carried through untouched. The immutable
``fixtures/car-003-role-corpus.json`` is never written.

The digest and canonical-JSON helpers come from ``lib/qualification_corpus.py``
so this script and the validator can never disagree about the preimage.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
import tomllib
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
LIB_DIR = SCRIPT_DIR / "lib"
REPO_ROOT = SCRIPT_DIR.parents[2]

if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from qualification_corpus import (  # noqa: E402
    EXECUTABLE_CORE_ROLES,
    GOVERNED_ROLE_ORDER,
    NON_EXECUTABLE_CORE_ROLES,
    OPTIONAL_HELPER_ROLES,
    REQUIRED_CORE_ROLES,
    canonical_bytes,
    digest,
)


LAYER6_REL = "tests/speckit-pro/layer6-efficiency"
MODULE_REL = f"{LAYER6_REL}/lib/qualification_corpus.py"
FIXTURE_ROOT_REL = f"{LAYER6_REL}/fixtures-codex"
MANIFEST_REL = f"{FIXTURE_ROOT_REL}/corpus-manifest.json"
ROSTER_REL = f"{LAYER6_REL}/fixtures/claude-agent-roster-rebaseline-v2.json"
SCHEMA_RELS = (
    f"{LAYER6_REL}/contracts/role-corpus.schema.json",
    f"{LAYER6_REL}/contracts-claude/role-corpus.schema.json",
    f"{LAYER6_REL}/contracts-codex-specification/role-corpus.schema.json",
)
AGENT_DIR_REL = "speckit-pro/agents"
CODEX_AGENT_DIR_REL = "speckit-pro/codex-agents"

SOURCE_KINDS = ("codex_toml", "governed_markdown_contract")
CALIBRATION_TIME = "2026-07-24T00:00:00Z"
REVIEWER_PREIMAGE = {"reviewer": "independent-corpus-reviewer"}

_ENUM_RE = re.compile(
    r'("role_id"\s*:\s*\{\s*\n[ \t]*"enum"\s*:\s*\[\n)(?P<body>.*?)(\n[ \t]*\])',
    re.DOTALL,
)
# The bounds sit in the same object as the roles array itself. Excluding braces
# from the span keeps the match inside that object, and the trailing comma after
# each number stays outside the match so the rewrite is width-independent.
_ROLE_COUNT_RE = re.compile(
    r'("roles"\s*:\s*\{[^{}]*?"minItems"\s*:\s*)\d+([^{}]*?"maxItems"\s*:\s*)\d+'
)


class RebaselineError(Exception):
    """A condition the caller must resolve before the corpus can be rewritten."""


def fixture_relative_path(role_id: str) -> str:
    return f"{FIXTURE_ROOT_REL}/{role_id}/fixture.json"


def source_kind_for(role_id: str) -> str:
    """Return the source kind the governed role membership implies."""
    if role_id in NON_EXECUTABLE_CORE_ROLES:
        return "governed_markdown_contract"
    return "codex_toml"


def source_relative_path(role_id: str, kind: str) -> str:
    if kind == "governed_markdown_contract":
        return f"{AGENT_DIR_REL}/{role_id}.md"
    return f"{CODEX_AGENT_DIR_REL}/{role_id}.toml"


def read_bytes(root: Path, relative: str) -> bytes:
    path = root / relative
    if not path.is_file():
        raise RebaselineError(f"missing source file: {relative}")
    return path.read_bytes()


def read_json(root: Path, relative: str) -> dict:
    try:
        return json.loads(read_bytes(root, relative).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RebaselineError(f"{relative} is not readable JSON") from exc


def route_digest_payload(binding: dict) -> dict:
    return {
        "agent_contract_id": binding["agent_contract_id"],
        "candidate_freeze_id": binding["candidate_freeze_id"],
        "role_id": binding["role_id"],
        "route_id": binding["route_id"],
    }


def rebound_route_binding(binding: dict) -> dict:
    rebound = copy.deepcopy(binding)
    rebound["route_digest"] = digest(route_digest_payload(rebound))
    return rebound


def rebound_source_binding(root: Path, role_id: str, kind: str) -> dict:
    source_rel = source_relative_path(role_id, kind)
    return {
        "source_path": source_rel,
        "source_kind": kind,
        "source_digest": digest(read_bytes(root, source_rel)),
    }


def rebaselined_fixture(root: Path, fixture: dict) -> dict:
    """Return the fixture with its source digest and route digests rebound."""
    role_id = fixture["role_id"]
    rebound = copy.deepcopy(fixture)
    rebound["source_binding"] = rebound_source_binding(root, role_id, source_kind_for(role_id))
    rebound["route_bindings"] = [
        rebound_route_binding(binding) for binding in rebound["route_bindings"]
    ]
    return rebound


def sandbox_mode_for(root: Path, role_id: str, kind: str) -> str:
    """Read the sandbox mode a new role's source declares."""
    if kind == "governed_markdown_contract":
        return "read-only"
    source_rel = source_relative_path(role_id, kind)
    try:
        source = tomllib.loads(read_bytes(root, source_rel).decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise RebaselineError(f"{source_rel} is not parseable TOML") from exc
    mode = source.get("sandbox_mode")
    if mode not in ("read-only", "workspace-write"):
        raise RebaselineError(f"{source_rel} declares no usable sandbox_mode")
    return mode


def generated_fixture(
    root: Path,
    role_id: str,
    kind: str,
    *,
    partition_binding: dict,
    freeze_id: str,
) -> dict:
    """Derive a new role fixture from the role's source and governed membership.

    The corpus carries two authored conventions for the identity digests and the
    permitted-tool list. This follows the one that covers eight of the twelve
    committed roles, including both non-executable ones.
    """
    executable = role_id in EXECUTABLE_CORE_ROLES or role_id in OPTIONAL_HELPER_ROLES
    mode = sandbox_mode_for(root, role_id, kind)
    read_only = mode == "read-only"
    route_binding = {
        "role_id": role_id,
        "route_id": f"g56r-003-route-{role_id}",
        "candidate_freeze_id": freeze_id,
        "agent_contract_id": f"g56r-003-agent-contract-{role_id}",
        "admission_status": "admitted",
    }
    route_binding["route_digest"] = digest(route_digest_payload(route_binding))
    return {
        "role_id": role_id,
        "required_core": role_id in REQUIRED_CORE_ROLES,
        "optional_helper": role_id in OPTIONAL_HELPER_ROLES,
        "executable": executable,
        "source_binding": rebound_source_binding(root, role_id, kind),
        "fixture_binding": {
            "fixture_id": f"g56r-003-fixture-{role_id}",
            "fixture_version": "1.0.0",
            "fixture_digest": digest({"fixture": role_id, "version": "1.0.0"}),
            "fixture_state": "valid",
            "current": True,
            "invalidated_at": None,
            "invalidation_reason": None,
        },
        "objective_binding": {
            "objective_id": f"g56r-003-objective-{role_id}",
            "objective_digest": digest({"objective": role_id, "partition": "calibration"}),
        },
        "partition_binding": copy.deepcopy(partition_binding),
        "permitted_tools": ["filesystem.read"] if read_only else ["filesystem.read", "shell.exec"],
        "sandbox": {
            "mode": mode,
            "network": "restricted",
            "mutation": "read_only" if read_only else "workspace_write",
        },
        "expected_artifacts": [
            {
                "artifact_contract_id": f"g56r-003-artifact-{role_id}-summary",
                "artifact_type": "markdown_summary",
                "artifact_digest": digest({"artifact": role_id, "type": "markdown_summary"}),
            }
        ],
        "acceptance_oracle": {
            "oracle_id": f"g56r-003-oracle-{role_id}",
            "oracle_version": "1.0.0",
            "oracle_digest": digest({"oracle": role_id, "version": "1.0.0"}),
        },
        "independent_review": {
            "review_id": f"g56r-003-review-{role_id}",
            "reviewer_digest": digest(REVIEWER_PREIMAGE),
            "review_digest": digest({"review": role_id, "result": "passed"}),
            "review_state": "passed",
            "reviewed_at": CALIBRATION_TIME,
        },
        "route_bindings": [route_binding] if executable else [],
    }


def corpus_freeze_id(manifest: dict) -> str:
    """Return the candidate freeze the committed corpus already binds."""
    freeze_ids = {
        binding["candidate_freeze_id"]
        for role in manifest["roles"]
        for binding in role["route_bindings"]
    }
    if len(freeze_ids) != 1:
        raise RebaselineError("corpus route bindings do not share one candidate freeze ID")
    return freeze_ids.pop()


def assert_governed_membership(role_ids: list[str]) -> None:
    """Fail unless the resulting corpus is exactly the governed role set."""
    if len(set(role_ids)) != len(role_ids):
        raise RebaselineError("corpus membership contains a duplicate role")
    if len(role_ids) != len(GOVERNED_ROLE_ORDER) or set(role_ids) != set(GOVERNED_ROLE_ORDER):
        missing = sorted(set(GOVERNED_ROLE_ORDER) - set(role_ids))
        unexpected = sorted(set(role_ids) - set(GOVERNED_ROLE_ORDER))
        raise RebaselineError(
            "resulting corpus membership does not match GOVERNED_ROLE_ORDER "
            f"(absent from the corpus: {missing}; absent from GOVERNED_ROLE_ORDER: "
            f"{unexpected}). Update GOVERNED_ROLE_ORDER and its companion tuples in "
            f"{MODULE_REL} in the same change."
        )


def planned_role_count_text(text: str, count: int, relative: str) -> str:
    """Return the schema text with the roles array bounds set to ``count``.

    The bounds move with the enum or the schema stops admitting its own corpus:
    an enum of eleven permitted ids under ``minItems`` 12 is unsatisfiable,
    because ``uniqueItems`` forbids repeating one to reach the floor.
    """
    updated, replaced = _ROLE_COUNT_RE.subn(
        lambda match: f"{match.group(1)}{count}{match.group(2)}{count}", text
    )
    if replaced != 1:
        raise RebaselineError(f"{relative} has no roles item bounds to update")
    return updated


def planned_schema_text(text: str, role_ids: list[str], relative: str) -> str:
    """Return the schema text with its role_id enum and role count set to ``role_ids``."""
    match = _ENUM_RE.search(text)
    if match is None:
        raise RebaselineError(f"{relative} has no role_id enum to update")
    body = match.group("body")
    first_line = body.splitlines()[0]
    entry_indent = first_line[: len(first_line) - len(first_line.lstrip())]
    replacement = ",\n".join(f'{entry_indent}"{role_id}"' for role_id in role_ids)
    with_enum = text[: match.start("body")] + replacement + text[match.end("body") :]
    return planned_role_count_text(with_enum, len(role_ids), relative)


def planned_roster_bytes(root: Path) -> bytes:
    """Return the Claude roster rebound to the live agent bytes."""
    roster = read_json(root, ROSTER_REL)
    for role in roster["shipped_roles"]:
        role_id = role["role_id"]
        role["source_digest"] = digest(read_bytes(root, f"{AGENT_DIR_REL}/{role_id}.md"))
    preimage = {key: value for key, value in roster.items() if key != "catalog_digest"}
    roster["catalog_digest"] = digest(preimage)
    return (json.dumps(roster, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build_plan(
    root: Path,
    *,
    add_role: str | None = None,
    add_kind: str | None = None,
    remove_role: str | None = None,
) -> tuple[dict[str, bytes], list[str]]:
    """Return the desired bytes for every owned file, plus fixture files to drop.

    A removal drops the role's ``fixture.json`` and nothing else. The corpus
    shares ``fixtures-codex/<role>/`` with the Layer 6 Codex benchmark, which
    owns ``input-prompt.md`` and ``expected-output.md`` beside it and discovers
    agents by listing that tree. Dropping a role from the governed corpus does
    not retire the Codex agent, so those files outlive the fixture.
    """
    manifest = read_json(root, MANIFEST_REL)
    role_ids = [role["role_id"] for role in manifest["roles"]]
    removed_files: list[str] = []

    if remove_role is not None:
        if remove_role not in role_ids:
            raise RebaselineError(f"{remove_role} is not bound by the corpus manifest")
        role_ids = [role_id for role_id in role_ids if role_id != remove_role]
        removed_files.append(fixture_relative_path(remove_role))
    if add_role is not None:
        if add_role in role_ids:
            raise RebaselineError(f"{add_role} is already bound by the corpus manifest")
        expected_kind = source_kind_for(add_role)
        if add_kind != expected_kind:
            raise RebaselineError(
                f"--kind {add_kind} contradicts the governed membership of {add_role}, "
                f"which implies {expected_kind}. Update NON_EXECUTABLE_CORE_ROLES in "
                f"{MODULE_REL} first if the classification is meant to change."
            )
        role_ids.append(add_role)

    assert_governed_membership(role_ids)
    order = {role_id: index for index, role_id in enumerate(GOVERNED_ROLE_ORDER)}
    role_ids.sort(key=lambda role_id: order[role_id])

    fixtures: dict[str, dict] = {}
    for role_id in role_ids:
        if role_id == add_role:
            fixtures[role_id] = generated_fixture(
                root,
                role_id,
                add_kind or source_kind_for(role_id),
                partition_binding=manifest["partition_binding"],
                freeze_id=corpus_freeze_id(manifest),
            )
            continue
        fixture_rel = fixture_relative_path(role_id)
        if not (root / fixture_rel).is_file():
            raise RebaselineError(
                f"missing role fixture: {fixture_rel}. Use --add-role {role_id} --kind "
                f"{source_kind_for(role_id)} to author it."
            )
        fixtures[role_id] = rebaselined_fixture(root, read_json(root, fixture_rel))

    planned: dict[str, bytes] = {}
    for role_id in role_ids:
        planned[fixture_relative_path(role_id)] = canonical_bytes(fixtures[role_id]) + b"\n"

    manifest["roles"] = [fixtures[role_id] for role_id in role_ids]
    manifest["corpus_digest"] = digest(
        {
            "corpus_id": manifest["corpus_id"],
            "corpus_version": manifest["corpus_version"],
            "fixture_byte_digests": [
                {
                    "fixture_digest": digest(planned[fixture_relative_path(role_id)]),
                    "fixture_path": fixture_relative_path(role_id),
                    "role_id": role_id,
                }
                for role_id in role_ids
            ],
            "partition_binding": manifest["partition_binding"],
        }
    )
    planned[MANIFEST_REL] = canonical_bytes(manifest) + b"\n"
    planned[ROSTER_REL] = planned_roster_bytes(root)

    if add_role is not None or remove_role is not None:
        for relative in SCHEMA_RELS:
            text = read_bytes(root, relative).decode("utf-8")
            planned[relative] = planned_schema_text(text, role_ids, relative).encode("utf-8")

    return planned, removed_files


def report_drift(root: Path, planned: dict[str, bytes]) -> list[str]:
    drifted = []
    for relative in sorted(planned):
        path = root / relative
        if not path.is_file() or path.read_bytes() != planned[relative]:
            drifted.append(relative)
    return drifted


def apply_plan(root: Path, planned: dict[str, bytes], removed_files: list[str]) -> list[str]:
    written = []
    for relative in sorted(planned):
        path = root / relative
        if path.is_file() and path.read_bytes() == planned[relative]:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(planned[relative])
        written.append(relative)
    for relative in removed_files:
        path = root / relative
        if path.is_file():
            path.unlink()
            written.append(f"{relative} (removed)")
        parent = path.parent
        # Only the now-empty leftover goes. A directory that still holds the
        # benchmark's input-prompt.md or expected-output.md stays put.
        if parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            written.append(f"{parent.relative_to(root).as_posix()}/ (removed)")
    return written


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebaseline the Layer 6 governed role corpus against live agent bytes.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift without writing; exit 1 when the corpus is stale",
    )
    parser.add_argument(
        "--add-role",
        metavar="ROLE_ID",
        help="author a fixture for a new governed role and add it to the schemas",
    )
    parser.add_argument(
        "--kind",
        choices=SOURCE_KINDS,
        help="source kind of the added role; required with --add-role",
    )
    parser.add_argument(
        "--remove-role",
        metavar="ROLE_ID",
        help="drop a governed role from the corpus, its fixture.json, and the schemas",
    )
    args = parser.parse_args(argv)
    if args.check and (args.add_role or args.remove_role):
        parser.error("--check cannot be combined with --add-role or --remove-role")
    if args.add_role and not args.kind:
        parser.error("--add-role requires --kind")
    if args.kind and not args.add_role:
        parser.error("--kind is only meaningful with --add-role")
    if args.add_role and args.add_role == args.remove_role:
        parser.error("--add-role and --remove-role name the same role")
    return args


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        planned, removed_files = build_plan(
            REPO_ROOT,
            add_role=args.add_role,
            add_kind=args.kind,
            remove_role=args.remove_role,
        )
    except RebaselineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.check:
        drifted = report_drift(REPO_ROOT, planned)
        for relative in drifted:
            print(f"drift: {relative}")
        if drifted:
            print(f"{len(drifted)} corpus file(s) no longer match live source bytes")
            return 1
        print("corpus matches live source bytes")
        return 0

    written = apply_plan(REPO_ROOT, planned, removed_files)
    for relative in written:
        print(f"updated: {relative}")
    if not written:
        print("corpus already matches live source bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
