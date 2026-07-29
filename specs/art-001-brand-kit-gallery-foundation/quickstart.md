# Quickstart: Validating ART-001

**Feature**: ART-001 | Run from the repository root. All paths are
repository-relative.

Check details live in `contracts/gallery-validation-contract.md`; entity shapes
live in `data-model.md`. This file is the run guide.

## Prerequisites

- Python 3.11+ on `PATH`. The repository suite needs no bootstrap.
- Node 22.12+ and `pnpm` **only** for the docs-site reference step. A fresh
  worktree needs `pnpm --dir docs-site install --frozen-lockfile` once before any
  docs command.
- A browser, for the manual scenarios the automated suite cannot cover.

## 1. Fast loop — the feature's own test

```bash
python3 tests/speckit-pro/unit/test-artifact-gallery.py
```

Expected final line, exit code 0:

```
test-artifact-gallery: <N>/<N> passed
```

This is the loop to iterate on. It is a plain subprocess entry point — Layer 4
never receives `--live`, so it takes no arguments.

## 2. Layer 4 — unit coverage

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

## 3. Layer 1 — structural validation of the new shipped directory

```bash
python3 tests/speckit-pro/run-all.py --layer 1
```

## 4. Regenerate the shipped payload and its proofs

`speckit-pro/artifact-gallery/` is shipped plugin source, so the
generated-artifact contract applies. **Run this after the allowlist edit lands,
not before** — before the edit it produces no gallery output, which is exactly the
silent failure FR-018 exists to catch.

```bash
python3 tests/speckit-pro/check-toolchain.py --mode tests
PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py
```

One idempotent command performs six steps: runner trust metadata, both payload
builds, marketplace version sync, installed-cache fixture sync, proof tree
hashes, and the XPLAT-009 evidence files. A second run on unchanged source makes
no further changes.

Confirm the gallery actually reached both payloads:

```bash
ls dist/claude/speckit-pro/artifact-gallery/
ls dist/codex/speckit-pro/artifact-gallery/
```

Both must list the gallery files. An empty or missing directory means the
allowlist edit in `speckit-pro/speckit_pro_runner/gates/payloads.py` did not land
— and note that **the build still exits 0 in that state**, which is precisely why
check group F exists.

## 5. Regenerate the docs-site test reference

The docs-site reference generator enumerates every `.md`/`.py`/`.sh` under
`tests/speckit-pro`, so adding the new unit test staleness-fails the committed
reference page. This passes locally and fails clean CI if skipped.

```bash
pnpm --dir docs-site install --frozen-lockfile   # once per worktree
pnpm --dir docs-site reference:generate
```

Commit the resulting `docs-site/src/content/docs/reference/tests.md` diff.

## 6. Full verification

```bash
python3 tests/speckit-pro/run-all.py
python3 tests/speckit-pro/check-toolchain.py --mode docs
pnpm --dir docs-site reference:check
```

CI additionally runs the drift gate, which must be clean:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/refresh-release-artifacts.py --check
```

## 7. Proving the drift check actually catches drift (SC-002)

Story 1's Independent Test. Do this in a scratch copy, never on a tracked file:

1. Copy a gallery HTML artifact to a scratch path.
2. Change one character inside its `BRAND-KIT:START`/`END` region.
3. Run the test. It must fail and name **both** the artifact and the block.
4. Restore the character. It must pass.

While ART-001 ships no artifact, exercise this against a fixture rather than a
real gallery file — the check must be proven, not assumed.

## 8. Manual scenarios the automated suite cannot cover

The suite drives no browser. These are acceptance evidence for the PR
(SC-001, SC-005, SC-006) and are recorded there, not asserted in Python.

| # | Scenario | Expected |
|---|----------|----------|
| M1 | Open a gallery artifact from `file://` with the OS set to **dark** | Dark theme on **first paint**, no flash of light, no console errors |
| M2 | Open the same artifact with the OS set to **light** | Light theme, no console errors |
| M3 | Activate the theme control | Theme switches immediately; on reopen the choice persists where the browser permits storage |
| M4 | Activate the control in a browser that refuses `localStorage` for local files | Theme still switches for the session; **no error surfaced** |
| M5 | Disable the network, reopen | All content, layout, and behavior work; the only difference is typeface substitution |
| M6 | Follow a provenance or attribution link | Navigates normally — these are not resource loads and must not have been stripped |
| M7 | Reach the theme control using **only** the keyboard, then activate it without a pointer | Control is reachable in normal focus order, shows a visible focus indicator, and activates; theme switches (FR-022, FR-023, SC-010) |
| M8 | Inspect the control's reported name and state in an accessibility inspector, in **both** theme positions | A stable human-readable name in both; the active theme is reported as state, and the reported state **changes** between positions (FR-022, SC-010) |
| M9 | Set the OS to reduce motion, reopen, and switch themes | No cross-theme animation or transition; nothing animates or smooth-scrolls (FR-023) |
| M10 | On a **dark** OS, force the **light** theme, then inspect a form control and the scrollbar | Both render light, matching the chosen theme rather than the OS (FR-004). This is the check that fails when only `color-scheme: light dark` is declared |
| M11 | Throttle or block the font host, reload, and watch the first paint | Text is visible in the fallback face immediately; at no point is text rendered invisibly (FR-024, SC-011) |
| M12 | With fonts unavailable, compare a heading against body copy | The two remain distinguishable — by level, size, and weight even if the substituted faces are similar (FR-024, SC-011) |

ART-001 ships no artifact, so M1–M6 run against the canonical
`theme-toggle.html` plus `brand-kit.css` composed into a scratch harness page.
The first port spec re-runs them against a real artifact.

## Requirement coverage map

| Requirement | Verified by |
|---|---|
| FR-001, FR-005, SC-007 | Audited contrast table in `data-model.md`, restated in `brand-kit.css` |
| FR-002, FR-003, FR-006, SC-002 | Check group A; step 7 |
| FR-004, SC-005 | M1, M3, M4, M10; check I3 |
| FR-021 | `SPA-CONTRACT.md` review — the use-of-color rule stated separately from the punctuation rule |
| FR-022, SC-010 | M7, M8; check I4 |
| FR-023 | M7, M9; checks I1, I2; focus-ring ratios in the audited table |
| FR-024, SC-011 | Check E4 (the request); M11, M12 (the rendering) |
| FR-025 | `brand-kit.css` review — a functional token is re-valued when it misses its floor; a brand primitive is not, and its unservable need is routed to a named functional sibling defined alongside it. Grounded in the audited table in `data-model.md` |
| FR-007, FR-019, SC-003 | Check group B |
| FR-026 | Checks B1 and B2 — exactly the three documented top-level keys in order, `schema_version` at the literal this spec fixes |
| FR-008, FR-015, FR-016, FR-017 | Check group C |
| FR-009 | Check group D |
| FR-010, FR-013 | `SPA-CONTRACT.md` and `brand-voice.md` review |
| FR-011, SC-008 | Check group E, including the E2/E3 negative controls |
| FR-012 | Provenance header review |
| FR-014 | Check H1; steps 2 and 6 |
| FR-018 | Check group F; step 4 |
| FR-020 | Check group G |
| FR-027 | Check group J (J1–J10) against synthetic fixtures; the security obligations section of `SPA-CONTRACT.md`. J6 proves the declaration is present and well-formed — that a browser **enforces** it over `file://` is the manual item the first port spec discharges |
| SC-001, SC-006 | M1, M2, M5 |
| SC-004 | Contract review — a port changes exactly one `status` value |
| SC-009 | ART-002 can begin using only ART-001's outputs |
| SC-012 | `SPA-CONTRACT.md` review — the untrusted-input rule for **generated** artifacts, naming the four contexts an interpolated value may never enter, stated in the same place as the explicit limit that FR-011's external-reference guarantee does not reach them |
