# Coherence audit branch

`audit/coherence-2026-09` holds the read-only coherence and cohesion audit of
speckit-pro: the coverage ledger, lanes, ripwire evidence pack and findings.
The branch is pushed after each wave and never merged. It is deleted after
triage. Design: `docs/ai/specs/speckit-pro-coherence-audit-design-concept.md`.

## Regenerate the ledger

```bash
git fetch origin
python3 audit/scope.py          # writes audit/ledger.json and audit/lanes.json
python3 audit/build_evidence.py # runs the ripwire scans, writes audit/evidence/
```

`scope.py` reads the file list from `origin/main`, applies the scope rules in
the script, assigns each file to one lane by the ordered rule table, and tags
files changed by open PR branches (`in_flight`). It is deterministic for a given
`origin/main` and set of open PRs. Lanes over 100 files are split into numbered
parts. Ripwire scans run against the checked-out worktree, which matches
`origin/main` apart from the ripwire config files and the design concept.

## Check coverage

```bash
python3 audit/coverage_check.py
```

Exit 0 only when every ledger row has a verdict (`clean` or finding IDs) and a
`verdict_lane` equal to its owning `lane`. Exit 1 lists the missing or mis-owned
rows. Exit 2 means the ledger or lanes file is missing or unparseable.

Finding format: `audit/finding-schema.md`.
