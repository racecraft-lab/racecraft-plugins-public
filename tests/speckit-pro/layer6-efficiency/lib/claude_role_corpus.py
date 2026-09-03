#!/usr/bin/env python3
"""CAR-003 governed role corpus: composition, admission, and fixture digests.

The corpus is one governed set of **twelve** role contracts — the eleven
required-core roles, plus ``autopilot-fast-helper``, which has no Claude agent
definition and is therefore contract-only until a later spec authors it
(FR-011). The corpus fixture is frozen, so a role retired from the live roster
stays bound here and is named in ``RETIRED_ROLES``;
``SHIPPED_REQUIRED_CORE_ROLES`` is the subset that still names a definition
under ``speckit-pro/agents/``.

``required_core`` and ``executable`` are **independent** booleans. A role can be
required by the cohort design and still be unrunnable today, so every contract
field binds either way; only ``candidate_route_bindings`` is withheld, because a
role with no shipped definition has no route to bind. A non-executable role
produces no score bundle and is **never counted as attrition** — it did not fail,
it was never assigned (FR-012).

Digest discipline is FR-033: every fixture and corpus digest is SHA-256 over the
canonical JSON serialization (sorted keys, minimal separators, UTF-8, no NaN) of
the record **excluding its own digest field**, emitted as ``sha256:<64 hex>``,
recomputed at bundle acceptance and at replay. A mismatch fails the fixture
**before** any candidate scores against it.

The digest helper is imported from ``claude_successor_freeze`` rather than
restated, so one preimage rule governs every CAR-003 digest.

**Declared, not live, source digests.** ``source_digest`` and
``acceptance_oracle_digest`` record the digests collected when the corpus was
frozen. They are deliberately not recomputed from live shipped bytes: the shipped
agent definitions change on their own release cadence, and binding the corpus to
them would make an unrelated agent edit fail this suite while telling a reviewer
nothing about the corpus. Verifying a declared source digest against live bytes
is an operator step at campaign time.

This module is repository-only harness code and makes **no live model calls**.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

if __package__:  # pragma: no cover - the lib is imported flat by the suite
    from .claude_successor_freeze import record_digest
else:
    from claude_successor_freeze import record_digest


REPO_ROOT = Path(__file__).resolve().parents[4]
CORPUS_FIXTURE_PATH = (
    REPO_ROOT / "tests" / "speckit-pro" / "layer6-efficiency" / "fixtures" / "car-003-role-corpus.json"
)

SCHEMA_VERSION = "1.0.0"
CORPUS_SIZE = 12

# FR-011: the eleven required-core roles the frozen CAR-003 corpus binds. The
# corpus is immutable, so this tuple never shrinks; a role retired from the live
# roster is named in RETIRED_ROLES instead.
REQUIRED_CORE_ROLES = (
    "analyze-executor",
    "checklist-executor",
    "clarify-executor",
    "codebase-analyst",
    "consensus-synthesizer",
    "domain-researcher",
    "gate-validator",
    "implement-executor",
    "phase-executor",
    "spec-context-analyst",
    "uat-runbook-author",
)

# FR-011, FR-012: required by the cohort design, contract-only for now.
CONTRACT_ONLY_ROLES = ("autopilot-fast-helper",)

# Required-core roles the frozen corpus still binds that no longer ship a Claude
# agent definition. `gate-validator` retired once the autopilot orchestrator
# began calling the `validate-gate` runner helper directly.
RETIRED_ROLES = ("gate-validator",)

# The required-core roles that still name a definition under speckit-pro/agents/.
SHIPPED_REQUIRED_CORE_ROLES = tuple(
    role for role in REQUIRED_CORE_ROLES if role not in RETIRED_ROLES
)

GOVERNED_ROLE_IDS = tuple(sorted(REQUIRED_CORE_ROLES + CONTRACT_ONLY_ROLES))

# FR-012: bound on every entry, including the non-executable one.
ALWAYS_BOUND_CONTRACT_FIELDS = (
    "role_id",
    "required_core",
    "executable",
    "source_digest",
    "fixture_digest",
    "objective_binding",
    "permitted_tools",
    "mutation_contract",
    "expected_artifacts",
    "acceptance_oracle_digest",
    "independent_review_binding",
)

ROUTE_BINDING_FIELD = "candidate_route_bindings"

# FR-033: the fixture check runs before any candidate scores against it.
FIXTURE_CHECK_STAGE = "before_candidate_scoring"

__all__ = [
    "ALWAYS_BOUND_CONTRACT_FIELDS",
    "CONTRACT_ONLY_ROLES",
    "CORPUS_FIXTURE_PATH",
    "FIXTURE_CHECK_STAGE",
    "GOVERNED_ROLE_IDS",
    "REQUIRED_CORE_ROLES",
    "RETIRED_ROLES",
    "SHIPPED_REQUIRED_CORE_ROLES",
    "FixtureVerdict",
    "RoleCorpusError",
    "analysis_partition",
    "counts_as_attrition",
    "declared_route_ids",
    "emits_score_bundle",
    "load_corpus",
    "record_digest",
    "role_index",
    "runnable_roles",
    "seal_corpus",
    "seal_fixture",
    "unbound_contract_fields",
    "validate_corpus",
    "verify_corpus_digest",
    "verify_fixture",
]


class RoleCorpusError(AssertionError):
    """Fail-closed error for a refused corpus, role entry, or fixture."""


def load_corpus(path: Path | None = None) -> dict[str, Any]:
    """Read the committed corpus fixture."""
    target = CORPUS_FIXTURE_PATH if path is None else path
    return json.loads(target.read_text(encoding="utf-8"))


def role_index(corpus: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    """Map ``role_id`` to its contract, refusing a duplicated identifier."""
    index: dict[str, Mapping[str, Any]] = {}
    for role in corpus.get("roles", ()):
        role_id = role.get("role_id")
        if role_id in index:
            raise RoleCorpusError(f"duplicate role contract for {role_id!r}")
        index[role_id] = role
    return index


def unbound_contract_fields(role: Mapping[str, Any]) -> tuple[str, ...]:
    """Name every always-bound contract field left absent, null, or empty (FR-012).

    An empty list counts as unbound deliberately. These fields hold bindings,
    and a field carrying zero bindings has bound nothing — treating ``[]`` as
    satisfied would let a role declare a binding list and supply none, which is
    the shape FR-012 exists to refuse.
    """
    return tuple(
        field
        for field in ALWAYS_BOUND_CONTRACT_FIELDS
        if role.get(field) is None or role.get(field) == []
    )


def emits_score_bundle(role: Mapping[str, Any]) -> bool:
    """FR-012: a non-executable role produces no score bundle."""
    return bool(role.get("executable"))


def counts_as_attrition(role: Mapping[str, Any]) -> bool:
    """FR-012: a non-executable role was never assigned, so it never attrited."""
    return bool(role.get("executable"))


def analysis_partition(corpus: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    """FR-012: the contract-only role is analysed apart from primary statistics."""
    index = role_index(corpus)
    separately = tuple(sorted(role_id for role_id in index if role_id in CONTRACT_ONLY_ROLES))
    primary = tuple(
        sorted(
            role_id
            for role_id, role in index.items()
            if role.get("required_core") and role_id not in CONTRACT_ONLY_ROLES
        )
    )
    return {"required_core_primary": primary, "analysed_separately": separately}


def declared_route_ids(corpus: Mapping[str, Any]) -> tuple[str, ...]:
    """Every candidate route identifier the corpus declares, deduplicated."""
    routes: set[str] = set()
    for role in role_index(corpus).values():
        for binding in role.get(ROUTE_BINDING_FIELD, ()):
            routes.add(binding["id"])
    return tuple(sorted(routes))


def runnable_roles(corpus: Mapping[str, Any], admitted_route_ids: Iterable[str]) -> tuple[str, ...]:
    """FR-012: only roles whose every declared route is admitted may run."""
    admitted = frozenset(admitted_route_ids)
    runnable = []
    for role_id, role in role_index(corpus).items():
        if not role.get("executable"):
            continue
        bindings = role.get(ROUTE_BINDING_FIELD, ())
        if bindings and all(binding["id"] in admitted for binding in bindings):
            runnable.append(role_id)
    return tuple(sorted(runnable))


@dataclass(frozen=True)
class FixtureVerdict:
    """Outcome of recomputing one fixture digest (FR-033)."""

    role_id: str
    ok: bool
    failure_plane: str
    failure_code: str
    stage: str = FIXTURE_CHECK_STAGE


def seal_fixture(role: Mapping[str, Any]) -> dict[str, Any]:
    """Return the role contract with its FR-033 fixture digest bound."""
    sealed = {key: value for key, value in role.items() if key != "fixture_digest"}
    sealed["fixture_digest"] = record_digest(sealed, digest_field="fixture_digest")
    return sealed


def verify_fixture(role: Mapping[str, Any]) -> FixtureVerdict:
    """Recompute the fixture digest, failing the fixture before any scoring."""
    role_id = str(role.get("role_id"))
    recorded = role.get("fixture_digest")
    if not isinstance(recorded, str):
        return FixtureVerdict(role_id, False, "fixture", "fixture_invalid")
    if recorded != record_digest(role, digest_field="fixture_digest"):
        return FixtureVerdict(role_id, False, "fixture", "fixture_invalid")
    return FixtureVerdict(role_id, True, "none", "none")


def seal_corpus(corpus: Mapping[str, Any]) -> dict[str, Any]:
    """Return the corpus with its FR-033 corpus digest bound."""
    sealed = {key: value for key, value in corpus.items() if key != "corpus_digest"}
    sealed["corpus_digest"] = record_digest(sealed, digest_field="corpus_digest")
    return sealed


def verify_corpus_digest(corpus: Mapping[str, Any]) -> bool:
    recorded = corpus.get("corpus_digest")
    return isinstance(recorded, str) and recorded == record_digest(corpus, digest_field="corpus_digest")


def validate_corpus(corpus: Mapping[str, Any]) -> tuple[str, ...]:
    """Every governance finding against one corpus; empty means clean."""
    findings: list[str] = []
    if corpus.get("schema_version") != SCHEMA_VERSION:
        findings.append(f"schema_version must be {SCHEMA_VERSION}")

    roles: Sequence[Mapping[str, Any]] = corpus.get("roles", ())
    if len(roles) != CORPUS_SIZE:
        findings.append(f"the corpus must bind exactly twelve role contracts, found {len(roles)}")

    seen: list[str] = [str(role.get("role_id")) for role in roles]
    if len(set(seen)) != len(seen):
        findings.append("role_id must be unique across the corpus")
    if tuple(sorted(set(seen))) != GOVERNED_ROLE_IDS:
        findings.append("the corpus must bind exactly the governed role set")

    for role in roles:
        role_id = str(role.get("role_id"))
        for field in unbound_contract_fields(role):
            findings.append(f"{role_id}: contract field {field} is unbound")
        executable = bool(role.get("executable"))
        has_routes = ROUTE_BINDING_FIELD in role
        if executable and not role.get(ROUTE_BINDING_FIELD):
            findings.append(f"{role_id}: an executable role must bind {ROUTE_BINDING_FIELD}")
        if not executable and has_routes:
            findings.append(
                f"{role_id}: {ROUTE_BINDING_FIELD} must be absent for a non-executable role"
            )
        if role.get("required_core") and role_id not in GOVERNED_ROLE_IDS:
            findings.append(f"{role_id}: required_core is claimed by an ungoverned role")
        verdict = verify_fixture(role)
        if not verdict.ok:
            findings.append(f"{role_id}: fixture_digest mismatch ({verdict.failure_code})")

    if not verify_corpus_digest(corpus):
        findings.append("corpus_digest does not match its canonical preimage")
    return tuple(findings)
