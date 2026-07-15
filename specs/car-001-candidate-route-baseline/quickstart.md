# Quickstart: Validate the CAR-001 Baseline Deliverables

**Date**: 2026-07-14 | **Branch**: `car-001-candidate-route-baseline`

This is a validation/run guide for the two CAR-001 deliverables. It proves the
spike's success criteria (SC-001…SC-008) end-to-end. Field-level details live in
[`data-model.md`](./data-model.md); the machine contract is
[`contracts/agent-route-candidate-manifest.schema.json`](./contracts/agent-route-candidate-manifest.schema.json).
Run every command from the repository root. Do not embed absolute filesystem
paths in any deliverable — the privacy scan below enforces this.

## Prerequisites

- Python 3.11+ (standard library only; no third-party packages required).
- The two deliverables exist:
  - `docs/ai/research/claude-agent-route-candidates.md` (the record)
  - `docs/ai/research/claude-agent-route-candidate-manifest.json` (the manifest)
- Read-only inventory sources present and unmodified: `speckit-pro/agents/*.md`,
  `speckit-pro/codex-agents/autopilot-fast-helper.toml`,
  `tests/speckit-pro/layer6-efficiency/fixtures/`.

## Validation scenarios

### V1 — Repository default suite still passes untouched (SC-006)

```bash
python3 tests/speckit-pro/run-all.py
```

Expected: zero failures. The spike changes no shipped byte, so Layers 1/4/5 pass
exactly as on `main`.

### V2 — Manifest is valid JSON (SC-001 precondition)

```bash
python3 -m json.tool docs/ai/research/claude-agent-route-candidate-manifest.json > /dev/null && echo "manifest JSON: VALID"
```

Expected: `manifest JSON: VALID`.

### V3 — Manifest conforms to the machine contract (SC-008, data-model §7)

Validate the manifest against the JSON Schema. If `jsonschema` is available it
gives the richest output; otherwise a stdlib structural check covers the
load-bearing rules (twelve-agent coverage, alias closure, absence integrity,
eligibility/availability split). Expected outcome either way: no violations.

```bash
python3 - <<'PY'
import json
man = json.load(open("docs/ai/research/claude-agent-route-candidate-manifest.json"))
schema = json.load(open("specs/car-001-candidate-route-baseline/contracts/agent-route-candidate-manifest.schema.json"))
try:
    import jsonschema
    jsonschema.validate(man, schema)
    print("contract: VALID (jsonschema)")
except ModuleNotFoundError:
    agents = man["agents"]
    assert len(agents) == 12, f"expected 12 agents, got {len(agents)}"
    absent = [n for n, e in agents.items() if e["production_route_recorded_absence"]]
    assert absent == ["autopilot-fast-helper"], f"absence integrity: {absent}"
    for n, e in agents.items():
        for t in e["candidate_routes"]:
            assert t["alias"] in {"opus", "sonnet", "haiku", "fable"}, (n, t["alias"])
            assert t["environment_time_availability"]["status"] == "probe_required", n
    print("contract: VALID (stdlib structural check)")
PY
```

### V4 — Twelve-agent coverage, every required field present (SC-001)

```bash
python3 - <<'PY'
import json
man = json.load(open("docs/ai/research/claude-agent-route-candidate-manifest.json"))
required = ["agent_name","agent_contract_id","role_contract","immutable_production_route",
           "production_route_recorded_absence","agent_file_hashes","candidate_routes",
           "required_capabilities","candidate_rationale","known_incompatibilities",
           "required_qualification_artifacts","invalidation_triggers","fixture_backlog_ref"]
expected = {"analyze-executor","checklist-executor","clarify-executor","codebase-analyst",
            "consensus-synthesizer","domain-researcher","gate-validator","implement-executor",
            "phase-executor","spec-context-analyst","uat-runbook-author","autopilot-fast-helper"}
agents = man["agents"]
assert set(agents) == expected, set(agents) ^ expected
for n, e in agents.items():
    missing = [f for f in required if f not in e]
    assert not missing, f"{n} missing {missing}"
    assert e["candidate_routes"], f"{n} has no candidate tuple"
print("coverage: 12/12 agents, all required fields present")
PY
```

### V5 — Instruction identity survives a pure frontmatter route change (SC-007)

Recompute the frontmatter-stripped-body sha256 for a current agent **from the
pinned comparator tag** (`git show speckit-pro-v2.19.1:…`, matching FR-011 and
T027 — never the working-tree copy) and confirm it matches the manifest; then
confirm that swapping only a frontmatter route value (model/effort) does not
change it. Uses the Python standard library only (FR-025).

```bash
python3 - <<'PY'
import hashlib, json, re, subprocess
def strip_frontmatter(text):
    m = re.match(r"^---\n.*?\n---\n", text, re.DOTALL)
    return text[m.end():] if m else text
man = json.load(open("docs/ai/research/claude-agent-route-candidate-manifest.json"))
name = "phase-executor"
tag = "speckit-pro-v2.19.1"
# Read the agent bytes AS PUBLISHED AT THE PINNED TAG (FR-011: "not the working-tree
# copy"), via the same git-show provenance T008/T027 use — never the working tree.
raw = subprocess.run(["git", "show", "%s:speckit-pro/agents/%s.md" % (tag, name)],
                     capture_output=True, check=True).stdout.decode("utf-8")
live = hashlib.sha256(strip_frontmatter(raw).encode("utf-8")).hexdigest()
recorded = man["agents"][name]["agent_file_hashes"]["instruction_sha256"]
assert live == recorded, f"instruction hash drift for {name}: {live} != {recorded}"
# Simulate a pure frontmatter route change: alter only the frontmatter, re-strip, re-hash.
mutated = re.sub(r"(?m)^model:.*$", "model: sonnet", raw, count=1)
assert hashlib.sha256(strip_frontmatter(mutated).encode("utf-8")).hexdigest() == live, \
    "frontmatter route change must not alter instruction identity"
print("SC-007: instruction identity stable under pure frontmatter route change")
PY
```

### V6 — No absolute filesystem paths leak into deliverables (privacy scan)

```bash
python3 - <<'PY'
import re, pathlib
pat = re.compile(r"/(Users|home)/")
bad = []
for f in ["docs/ai/research/claude-agent-route-candidates.md",
          "docs/ai/research/claude-agent-route-candidate-manifest.json"]:
    for i, line in enumerate(pathlib.Path(f).read_text(encoding="utf-8").splitlines(), 1):
        if pat.search(line):
            bad.append(f"{f}:{i}")
assert not bad, "absolute paths found: " + ", ".join(bad)
print("privacy scan: no absolute filesystem paths in deliverables")
PY
```

### V7 — Zero shipped-byte change (SC-006, FR-024)

No shipped plugin byte changes. Check the shipped payload surfaces against `main`:

```bash
git diff --stat main -- speckit-pro dist
```

Expected: empty output. Nothing under `speckit-pro/` or `dist/` (the shipped
Claude/Codex plugin payload) is added, modified, or removed by the spike, so
**0 production-code LOC** change.

The one intentional edit under `tests/` is the docs-surface guard allowlist in
`tests/speckit-pro/unit/test-speckit-pro-runner.py` (+9 lines), which admits the
two `docs/ai/research/` deliverables as a conscious review checkpoint. It is
repository test configuration, **not** a shipped payload byte, so SC-006 holds:

```bash
git diff --stat main -- tests
```

Expected: only `tests/speckit-pro/unit/test-speckit-pro-runner.py` changed. The
whole-branch surface is 19 files — the two deliverables, the spec-driven-
development artifacts under `specs/car-001-candidate-route-baseline/`, two
`docs/ai/specs/` roadmap/index updates, and this one test-guard edit.

### V8 — Every platform fact is cited; statements are labeled (SC-002, SC-003)

Manual review of the record: confirm every row in the primary-source fact table
carries a source URL, an access date, and a short verbatim quote (SC-002), and
that every statement is visibly labeled fact / inference / proposed policy /
assumption (SC-003). Confirm the capability-question section uses stable
`CAP-Qn` IDs and that the go/no-go handoff is the record's final section, is
self-contained, and lists no dependency on CAR-002 results (SC-004, FR-022).

### V9 — Semantic rules the JSON Schema cannot express (data-model §7 rules 9, 10)

The schema enforces shape; the load-bearing cross-reference and coverage rules
are review/quickstart-enforced (data-model §7 rules 9 and 10, and the §5
helper-only `platform_field_mapping` rule). This check makes that enforcement
real: it confirms `agent_name` matches its map key, every `CAP-Qn` a tuple
references resolves to a declared capability question, `platform_field_mapping`
and recorded absence occur only on the helper, every candidate `effort` is a
documented level (record `EFF-1`), every distinct candidate alias has an
invalidation trigger naming it, the helper's `platform_field_mapping` is
non-empty and represents every field of the pinned Codex source toml
(source-completeness, data-model §5), both the capability-question IDs and
the twelve `agent_contract_id`s are unique, the comparator is pinned to the
exact `speckit-pro-v2.19.1` tag and commit, every `fixture_backlog_ref` anchor
resolves to a record heading and each capability-question ID has a dedicated
record entry, and each agent carries both per-alias re-pointing and
comparator-drift invalidation triggers.

```bash
python3 - <<'PY'
import json, re, subprocess, tomllib
man = json.load(open("docs/ai/research/claude-agent-route-candidate-manifest.json"))
agents = man["agents"]
q_ids = [q["id"] for q in man["capability_questions"]]
declared_q = set(q_ids)
errs = []
if len(q_ids) != len(declared_q):
    errs.append(f"duplicate capability_question ids: {q_ids}")
contract_ids = [e["agent_contract_id"] for e in agents.values()]
if len(contract_ids) != len(set(contract_ids)):
    errs.append(f"duplicate agent_contract_id: {contract_ids}")
comp = man["immutable_production_comparator"]
if (comp["release_tag"] != "speckit-pro-v2.19.1"
        or comp["commit_sha"] != "e343aa2e4ebcb2d48c501f285d7072cfd55722da"):
    errs.append(f"comparator pin drift: {comp['release_tag']} / {comp['commit_sha']}")
for name, e in agents.items():
    if e["agent_name"] != name:
        errs.append(f"{name}: agent_name {e['agent_name']!r} != key")
    absent = e["production_route_recorded_absence"]
    has_map = "platform_field_mapping" in e
    if absent != (name == "autopilot-fast-helper"):
        errs.append(f"{name}: unexpected recorded-absence {absent}")
    if has_map != (name == "autopilot-fast-helper"):
        errs.append(f"{name}: platform_field_mapping presence {has_map} (helper-only)")
    aliases = set()
    for t in e["candidate_routes"]:
        aliases.add(t["alias"])
        for ref in ("probe_question_ref", "binding_question_ref"):
            qid = t["environment_time_availability"][ref]
            if qid not in declared_q:
                errs.append(f"{name}: {ref} {qid} not in capability_questions")
        if t["effort"] not in {"low", "medium", "high", "xhigh", "max"}:
            errs.append(f"{name}: undocumented effort {t['effort']!r}")
    trigger_text = " ".join(e["invalidation_triggers"]).lower()
    for a in aliases:
        if a not in trigger_text:
            errs.append(f"{name}: no re-pointing invalidation trigger for alias {a!r}")
    if not any(re.search(r"drift", t, re.I) and re.search(r"hash|sha256", t, re.I)
               for t in e["invalidation_triggers"]):
        errs.append(f"{name}: no comparator-drift invalidation trigger")
# Helper platform_field_mapping is non-empty and source-complete vs the pinned Codex toml (data-model §5).
helper = agents["autopilot-fast-helper"]
pfm = helper.get("platform_field_mapping", [])
if not pfm:
    errs.append("autopilot-fast-helper: platform_field_mapping is empty")
else:
    toml_bytes = subprocess.run(
        ["git", "show", "speckit-pro-v2.19.1:speckit-pro/codex-agents/autopilot-fast-helper.toml"],
        capture_output=True, check=True).stdout
    mapped = [r["codex_field"] for r in pfm]
    for f in tomllib.loads(toml_bytes.decode("utf-8")):
        if not any(m == f or m.startswith(f + " ") or m.startswith(f + "=") for m in mapped):
            errs.append(f"autopilot-fast-helper: source field {f!r} not represented in platform_field_mapping")
# Rule 9: every fixture_backlog_ref anchor and every CAP-Qn resolves into the record.
record_path = "docs/ai/research/claude-agent-route-candidates.md"
record_text = open(record_path, encoding="utf-8").read()
def _slug(h):
    return re.sub(r"[^\w\s-]", "", h.lower()).strip().replace(" ", "-")
heading_slugs = {_slug(m.group(1)) for m in re.finditer(r"(?m)^#+\s+(.+?)\s*$", record_text)}
for name, e in agents.items():
    path, _, anchor = e["fixture_backlog_ref"].partition("#")
    if not anchor or path != record_path or anchor not in heading_slugs:
        errs.append(f"{name}: fixture_backlog_ref {e['fixture_backlog_ref']!r} does not resolve to a record heading")
for qid in declared_q:
    if not re.search(r"(?m)^[|\-]\s*\*\*`" + re.escape(qid) + r"`", record_text):
        errs.append(f"{qid}: no dedicated capability-question entry in the record")
assert not errs, "semantic violations:\n  " + "\n  ".join(errs)
print("semantic rules: cross-refs + record anchors resolve, coverage + source-completeness verified (data-model §5, §7 rules 9, 10)")
PY
```

## Success criteria mapping

| Check | Proves |
|-------|--------|
| V1, V7 | SC-006 — zero shipped-byte change; default suite green |
| V2, V4 | SC-001 — twelve-agent coverage, contract-valid manifest |
| V3 | SC-008 — manifest conforms to the `agent-route-candidate-manifest.schema.json` contract |
| V5 | SC-007 — instruction identity stable under route change |
| V6 | Privacy constraint — no absolute paths in deliverables |
| V8 | SC-002, SC-003, SC-004 — citation, labeling, self-contained handoff |
| V9 | Data-model §7 rules 9, 10 — cross-reference integrity and per-alias invalidation-trigger coverage (the semantic rules JSON Schema cannot express) |
