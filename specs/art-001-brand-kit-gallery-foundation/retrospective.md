---
feature: ART-001 — Artifact Brand Kit & Gallery Foundation
branch: art-001-brand-kit-gallery-foundation
date: 2026-07-29
completion_rate: 94
spec_adherence: 88
requirements_total: 39
requirements_implemented: 30
requirements_partial: 9
requirements_not_implemented: 0
requirements_modified: 0
requirements_unspecified: 0
findings_critical: 0
findings_significant: 3
findings_minor: 2
findings_positive: 4
constitution_violations: 0
---

# ART-001 Retrospective

## Executive summary

The feature shipped what it promised and nothing it did not: six foundation files,
one Layer 4 validation module, and a two-line payload-builder edit. 32 of 34 tasks
completed (94%); the two open ones are genuinely manual browser scenarios, not
skipped work. Spec adherence is 88%, and the 12% gap has a single structural cause
worth stating plainly rather than burying: **ART-001 ships zero artifacts, so every
requirement worded as an obligation on "gallery artifacts" is satisfied as an
*enforced rule* rather than an *observed behaviour*.** That is the intended design —
the four port specs consume this foundation — but it means roughly half the
validation surface runs against synthetic fixtures, and the spec says so per row
instead of letting a green suite imply live coverage.

The most valuable output of the run was not the code. It was seven defects found by
verification *after* the code was written, each of which would have shipped green.
The single highest-impact one was a fail-silent gap in the payload builder: without
the two-line fix the entire gallery directory would have been absent from every
installed plugin while the build stayed green. Copilot's review independently
identified that same edit as "the minimal payload-builder allowlist change required
to actually ship the new directory," which is corroboration from an independent
reader rather than self-assessment.

## Proposed spec changes

**None.** No spec modification is proposed or required, so the Human Gate in step 13
does not apply and `spec.md` was not touched by this retrospective. The size overrun
that would ordinarily prompt a spec revision was already written into `spec.md`
during the run as an explicit disclosure rather than left to be reconciled here.

Three questions do need a **human decision**, but they are brand-owner and licensing
calls, not spec defects — they are carried as known gaps on the PR and repeated under
Follow-up actions below.

## Requirement coverage matrix

Total requirements: 39 (27 FR + 12 SC + 0 NFR). Unspecified: 0.

| Status | Count | IDs |
| --- | --- | --- |
| Implemented | 30 | FR-001, FR-002, FR-003, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-023, FR-025, FR-026, FR-027; SC-002, SC-003, SC-007, SC-008, SC-009, SC-012 |
| Partial | 9 | FR-004, FR-022, FR-024; SC-001, SC-004, SC-005, SC-006, SC-010, SC-011 |
| Not implemented | 0 | — |
| Modified | 0 | — |
| Unspecified | 0 | — |

Every one of the nine partials is partial for the *same* reason, and none is partial
because work was left undone:

- **FR-004, FR-022, FR-024, SC-001, SC-005, SC-006, SC-010, SC-011** — the mechanism
  is shipped and was driven in a real browser through an authored harness, but the
  requirement is worded as an observation about a *shipped artifact*, and no artifact
  ships in this slice. The residual is tasks T026/T027: a real `file://` load and
  keyboard-only operation.
- **SC-004** ("porting a template requires no edit to any shared foundation file") is
  unobservable by construction until the first port exists. ART-002 is its proof.

Adherence = ((30 + 0 + (9 × 0.5)) / 39) × 100 = **88%**.

## Success criteria assessment

| SC | Verdict | Evidence |
| --- | --- | --- |
| SC-001 | Partial | Harness opened and driven in Chrome; real `file://` load open (T026) |
| SC-002 | Met | Byte-for-byte marker-region comparison, mutation-proved |
| SC-003 | Met | Two-step routing resolvable from one catalog read; closure validated both directions |
| SC-004 | Deferred | Provable only by ART-002; no shared-file edit is required by design |
| SC-005 | Partial | Verified in-browser in both themes; real `file://` load open (T026) |
| SC-006 | Partial | Offline behaviour verified in-browser; typeface substitution the only difference |
| SC-007 | Met | Every permitted pairing measured; four failures found and corrected |
| SC-008 | Met | Scanner plus executed evasions, including the case-folding bypass |
| SC-009 | Met | Foundation complete; the four port specs are unblocked |
| SC-010 | Partial | Keyboard operation is T027, open |
| SC-011 | Partial | `display=swap` shipped; the no-invisible-text observation is T027 |
| SC-012 | Met | Untrusted-input obligation stated in the author-facing contract |

## Architecture drift

| Planned | As shipped | Drift? |
| --- | --- | --- |
| Marker-delimited CSS token set | `brand-kit.css`, `BRAND-KIT:START/END` | No |
| Theme-toggle snippet | `theme-toggle.html`, marker renamed `GALLERY-HEAD` | Minor, intentional — the region grew beyond a toggle to the canonical head block, so the old name misdescribed it |
| Routing manifest | `manifest.json`, 21 rows, 5-signal closed vocabulary | No |
| Single-file contract doc | `SPA-CONTRACT.md` | No |
| Brand-voice cheat sheet | `brand-voice.md`, subset only, private source cited not copied | No |
| — | `UPSTREAM-NOTICE.md` | **Added.** Not in the plan; required once the MIT attribution obligation was identified |
| Python stdlib unit test | `tests/speckit-pro/unit/test-artifact-gallery.py` | No, in kind — see the volume finding below |
| — | 2 lines in `speckit_pro_runner/gates/payloads.py` | **Added.** Written into the spec as FR-018 rather than smuggled in |

No architectural approach changed. Both additions are scope the plan missed, not
scope that replaced planned work.

## Significant deviations

**SIGNIFICANT — the validation module is ~14× its estimate.** 6,322 authored lines
against a ~450-line estimate; total authored volume 7,838 lines across nine files
against a plan that projected far less. This is disclosed in `spec.md` rather than
absorbed. Two things keep it from being a simple overrun: the declared gate figures
(62 LOC / 2 production files / 24 total) are *correct* against the binding metric,
which counts production code only, so the reviewability gate was never misled; and
every one of the 73 checks is mutation-proved non-vacuous, so the volume is not
padding. Root cause: the estimate was made against "a test file for a CSS token set"
before the security surface (external-reference scanning with executed evasions) and
the accessibility surface (per-pairing contrast measurement) were understood to be
in scope.

**SIGNIFICANT — roughly half the validation cannot exercise the real subject.**
Because zero artifacts ship, about half the checks run against synthetic fixtures.
This is correct for a foundation slice, and it is asserted per row rather than
implied. But it means the suite's green state proves *the checkers work*, not *the
gallery is clean* — a distinction a reviewer could easily miss, which is why it is
stated in the PR body as well as the contract table.

**SIGNIFICANT — the PR was opened before its own packet was emitted.** The skill's
order is packet → validate → open. The actual order was inverted, and the cost was
real: the hand-written body omitted the `release-note` fence that `feat` PRs require,
so `validate-release-note` failed on the opened PR. Fixed by adding one fence and
verifying against the real validator locally before pushing. Notably, following the
packet path would *not* have prevented this — the packet's generated body carries no
fenced block at all, which is now raised as a gap against speckit-pro.

## Minor deviations

**MINOR — the theme-toggle marker was renamed mid-run** (`THEME-TOGGLE` →
`GALLERY-HEAD`). Correct, and cheap now because no artifact embeds it yet; it would
have been a 21-file migration after ART-002.

**MINOR — the brand kit's heading rule was split after checking the brand source.**
The display face had been applied to all six heading levels; only the first two take
it. Two required weights were also unrequested, which browsers would have
synthesized.

## Innovations and best practices

**POSITIVE — mutation proof as the bar for "is this check real."** Every check was
neutralized to return nothing and required to fail. 73/73 non-vacuous. Highly
reusable and cheap; it is the difference between "checks written" and "checks that
would notice." **Constitution candidate.**

**POSITIVE — executing evasions instead of reasoning about them.** Every scanner
evasion was run as a fixture. This is how the `casefold()` bypass surfaced — U+017F
folds to `s`, so a host spelled `fontſ.gstatic.com` compared equal to the allowlisted
one. No amount of re-reading the requirement would have found it. **Constitution
candidate.**

**POSITIVE — negative controls for design claims.** The head-block design was proved
by building the *forbidden* variant and observing the marker relocate into the body,
rather than by asserting the rule.

**POSITIVE — recording why a defensive clause exists, inside a test.** The ASCII
repertoire restriction is asserted *together with* proof that the other two checks
alone admit the attack, so a later reader cannot delete it as redundant tidying.

## Constitution compliance

| Article | Verdict | Evidence |
| --- | --- | --- |
| I. Plugin Structure Compliance | PASS | Layer 1 1428/1428, including payload completeness and conformance |
| II. Cross-Platform Runtime & Script Safety | PASS | Python 3.11+ stdlib only; no new Bash or `jq` dependency; both Claude and Codex payloads updated |
| III. Semantic Versioning | PASS | No hand-edited versions; `artifact-consistency` green |
| IV. Test Coverage Before Merge | PASS | 73 checks registered in `suite-manifest.json`; full suite 5777/5777 |
| V. Conventional Commits | PASS | `validate-pr-title` green; all commits conventional |
| VI. KISS, Simplicity & YAGNI | PASS, with the volume finding above | See assessment |

**Violations: none.**

Article VI deserves its reasoning shown rather than a bare PASS, because the 14×
overrun is the obvious place to suspect one. The article prohibits *speculative
features*, *abstractions for one-time operations*, and *wrapper layers* — the module
contains none: it is flat `check_*` functions with a mechanically-enforced uniform
signature and no abstraction layer. The checks are not speculative features; they
enforce requirements the spec states and that bind on ART-002 onward. The article's
own quality gate is "master plan review + code review," and code review returned no
blocking findings while Copilot returned "0 important, 0 nits." So the gate as
defined is satisfied. The honest caveat: "a reviewer cannot understand it in 30
seconds" applies to the 6,322-line aggregate even though it does not apply to any
individual check, which is precisely why the group A–K contract table exists as an
index. Recorded as SIGNIFICANT, not as a violation.

## Unspecified implementations

Two things shipped that no requirement had asked for at the time they were written.
Both were converted into requirements rather than left unspecified:

- The payload-builder edit became **FR-018** once the fail-silent gap was found.
- The MIT attribution obligation became **FR-020** and `UPSTREAM-NOTICE.md`.

Net unspecified implementations at close: **zero.**

## Task execution analysis

- 34 tasks; 32 complete (94%); 0 dropped; 0 phantom completions (verified by the
  phantom-check pass).
- 2 open: **T026** and **T027**, both manual browser scenarios. An acceptance harness
  was authored and driven in-browser as substitute evidence; what remains is a real
  `file://` load and keyboard-only operation, neither of which the browser tooling
  can perform.
- Task count grew during the run as verification found real scope (FR-018 and the
  attribution work). Growth from discovered defects is healthy; it is the opposite of
  scope creep.

## Lessons learned and recommendations

1. **Run the gate; do not reason about it.** Three times a threshold was compared
   against the wrong instrument — a production-file count of 9 against a block
   threshold of 8, an estimator's 795 against an 800 belonging to a different tool,
   and a plan justifying a third file against the wrong dimension. Every one
   dissolved on execution. *Priority: HIGH.*
2. **Verify subagent claims instead of banking them.** Two reports contained real
   errors, including a claimed signature harness that did not exist and was later
   built for real. A claim about work done is evidence only when it cites something
   checkable. *Priority: HIGH.*
3. **State an obligation where it will be read, not where it was decided.**
   Repeatedly the real defect was placement — a rule living in a planning artifact no
   port author opens. *Priority: MEDIUM.*
4. **Sequence payload/proof regeneration deliberately.** Touching any runner file
   reds the same eight tests; regeneration was pulled forward so later failures
   stayed diagnosable. *Priority: MEDIUM.*
5. **Estimate the surface, not the artifact.** The ~450-line estimate was made
   against "a test for a CSS file" and missed that security and accessibility
   verification were in scope. Estimating from the *requirement classes* to be
   verified would have been closer. *Priority: MEDIUM.*
6. **A process list that marks nothing cannot catch a skipped step.** Eleven of the
   twelve post-implementation entries ran while all twelve stayed unmarked, and two
   never ran at all — surfaced only because the operator read the task list.
   *Priority: HIGH, and raised against speckit-pro rather than owned here.*

## Follow-up actions

**Requires a human decision (blocking ART-002, not this PR):**

1. **MIT "substantial portion."** Whether these re-skins clear the licence's
   undefined bar is unresolved by any authoritative source; the header currently
   over-attributes deliberately.
2. **Three brand-owner questions.** May brand red be tuned per theme; is the danger
   red acceptable as the dark-theme emphasis colour; may the muted surface be
   lightened — the last is the cheapest structural fix and would restore contrast
   headroom for every boundary token at once.

**Owned by the first port spec (ART-002):**

3. Execute T026/T027 against a real shipped artifact over `file://`.
4. Confirm in-document policy enforcement over `file://` in a browser — currently
   verified against browser-engine source, not executed.
5. Demonstrate SC-004 by porting without editing any shared foundation file.

**Raised against speckit-pro (recorded in the workflow file, not ART-001 scope):**

6. The PR packet's generated body and this repository's release-note gate are
   mutually unsatisfiable as written.
7. `validate-pr-packet-write`'s apply mode is unreachable where packets are untracked.
8. No post-implementation entry is self-verifying.
9. The autopilot loop permits a correct-but-halted turn.
10. A subagent can create an agent team and leave a teammate running.
11. The gap-counting helper matches `[Gap]` literally and under-reports `[Gap, <ref>]`.

**No constitution amendment is proposed.** Two candidates (mutation proof, executed
evasions) are recorded above for a future `/speckit.constitution` pass, which is a
separate human-gated action.

## Self-assessment checklist

| Item | Result |
| --- | --- |
| Evidence completeness — every major deviation cites file, task, or behaviour | PASS |
| Coverage integrity — all 39 requirement IDs classified, none missing | PASS |
| Metrics sanity — completion 32/34 = 94%; adherence ((30 + 4.5)/39) = 88% | PASS |
| Severity consistency — labels match stated impact | PASS |
| Constitution review — all six articles assessed, "none" stated explicitly | PASS |
| Human Gate readiness — no spec changes proposed, so not applicable | PASS (N/A) |
| Actionability — recommendations prioritized and tied to findings | PASS |

No blocking item failed. Report finalized.

## File traceability appendix

| Requirement group | Files |
| --- | --- |
| FR-001, FR-002, FR-005, FR-012, FR-021, FR-023, FR-025 | `speckit-pro/artifact-gallery/brand-kit.css` |
| FR-003, FR-004, FR-022, FR-024, FR-027 | `speckit-pro/artifact-gallery/theme-toggle.html` |
| FR-007, FR-008, FR-009, FR-015, FR-016, FR-017, FR-019, FR-026 | `speckit-pro/artifact-gallery/manifest.json` |
| FR-010, FR-020, SC-012 | `speckit-pro/artifact-gallery/SPA-CONTRACT.md` |
| FR-013 | `speckit-pro/artifact-gallery/brand-voice.md` |
| FR-020 | `speckit-pro/artifact-gallery/UPSTREAM-NOTICE.md` |
| FR-006, FR-011, FR-014, FR-019, FR-026, SC-002, SC-008 | `tests/speckit-pro/unit/test-artifact-gallery.py` |
| FR-018 | `speckit-pro/speckit_pro_runner/gates/payloads.py` |
| Check contract index (groups A–K) | `specs/art-001-brand-kit-gallery-foundation/contracts/gallery-validation-contract.md` |
