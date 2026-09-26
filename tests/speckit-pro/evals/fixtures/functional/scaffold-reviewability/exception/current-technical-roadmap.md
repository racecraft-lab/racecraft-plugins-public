# Technical Roadmap: Token Platform

## Reviewability Budget Policy

- Warn above 400 reviewable production LOC, 6 production files, or 15 total
  files.
- Block above 800 reviewable production LOC, 8 production files, or 25 total
  files, unless the entry records a typed exception pragma.

---

## Progress Tracking

| Spec | Name | Status | Workflow File | Next Phase |
|------|------|--------|---------------|------------|
| SPEC-841 | Token Store Migration | ⏳ Pending | [SPEC-841-workflow.md](.process/SPEC-841-workflow.md) | Specify |
| SPEC-842 | Token Audit Export | ⏳ Pending | [SPEC-842-workflow.md](.process/SPEC-842-workflow.md) | Specify |

---

## Specification Sections

### SPEC-841: Token Store Migration

**Priority:** P1 | **Depends On:** None | **Enables:** SPEC-842

**Goal:** Move refresh-token storage from the session table to a dedicated token store.

**Reviewability Budget:** Primary surface: schema/migration |
Projected reviewable LOC: 1180 |
Production files: 9 |
Total files: 22 |
Budget result: recorded at setup
Reviewability-Exception: infra

**Scope:**
- Create the token store schema and migrate existing refresh tokens.
- Route token reads and writes through the new store.

**Key Files:**
- `src/tokens/store.py` — Token store access layer

---

### SPEC-842: Token Audit Export

**Priority:** P2 | **Depends On:** SPEC-841 | **Enables:** None

**Goal:** Export token lifecycle events as JSON Lines for audit.

**Reviewability Budget:** Primary surface: API |
Projected reviewable LOC: 260 |
Production files: 3 |
Total files: 7 |
Budget result: recorded at setup

**Scope:**
- Add an audit export endpoint for token lifecycle events.

**Key Files:**
- `src/tokens/audit_export.py` — Audit export endpoint
