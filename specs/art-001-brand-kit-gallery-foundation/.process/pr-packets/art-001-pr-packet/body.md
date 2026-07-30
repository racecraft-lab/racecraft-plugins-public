# feat(speckit-pro): Add the artifact gallery brand kit, routing catalog, and validation

## Summary

<!-- speckit-pro-editable:summary:start -->
Ships the platform-neutral foundation every HTML artifact in the SpecKit-Pro gallery consumes: brand tokens, a canonical head block, a 21-row routing catalog, the single-file authoring contract, a brand-voice subset, an upstream notice, and one Layer 4 validation module. Ships zero templates by design — those are ART-002 through ART-005.
<!-- speckit-pro-editable:summary:end -->

## What Changed

<!-- speckit-pro-editable:what_changed:start -->
- brand-kit.css — the Racecraft token set, marker-delimited for verbatim embedding, with an audited contrast table above the marker that ships to no artifact.
- theme-toggle.html — the canonical head region: security policy declaration, font request, pre-first-paint theme application, the theme control, and the opt-in brand mark.
- manifest.json — all 21 planned templates seeded, with the closed five-signal routing vocabulary.
- SPA-CONTRACT.md — the author-facing single-file contract, including the five exact attribution labels and the typeface-token table.
- brand-voice.md — the artifact-relevant voice subset, citing the private brand source by repository, path, and commit rather than copying its prose.
- UPSTREAM-NOTICE.md — the verbatim upstream MIT licence, hash-verified.
- tests/speckit-pro/unit/test-artifact-gallery.py — 73 checks in groups A through K, every one mutation-proved.
- Two lines in the payload builder so the gallery directory actually reaches both platform payloads.
<!-- speckit-pro-editable:what_changed:end -->

## Why It Matters

<!-- speckit-pro-editable:why_it_matters:start -->
The payload edit is the blocking part. Without it the gallery directory is absent from every installed plugin and the whole feature ships nothing while the build stays green — the copy helper falls through silently when a name is neither a directory nor a file. Everything else is the shared vocabulary the four template-port specs depend on, so getting it wrong once is a cost paid twenty-one times.
<!-- speckit-pro-editable:why_it_matters:end -->

## How To Review

- Start with the payload builder edit — it is two lines and it is what makes the feature real.
- Read the contrast table above the brand-kit marker; every pairing is measured, and four failures were corrected during verification.
- Check the head block stays inside head-legal metadata content — the toggle and mark are script-created because a button there would close the head and void the policy declaration for every artifact.
- Spot-check the routing catalog's closure in both directions: every signal used is declared, every declared signal is used.
- The validation module is large; the group A through K contract table in contracts/gallery-validation-contract.md is the index.

## How To UAT

Open speckit-pro/artifact-gallery/.process/acceptance-harness.html from disk over file:// in a browser. Confirm: the page paints in your operating system theme with no flash of the wrong one; the theme control in the top right flips the theme and its pressed state; the choice survives a reload; the Racecraft mark is visible and legible in both themes while the opt-out container beside it stays empty; headings one and two render in Space Grotesk and heading three in Geist; and the browser console reports no errors. Two scenarios remain genuinely manual and are called out as open: first paint over file:// and keyboard-only operation of the theme control.

## UAT Runbook

Open speckit-pro/artifact-gallery/.process/acceptance-harness.html from disk over file:// in a browser. Confirm: the page paints in your operating system theme with no flash of the wrong one; the theme control in the top right flips the theme and its pressed state; the choice survives a reload; the Racecraft mark is visible and legible in both themes while the opt-out container beside it stays empty; headings one and two render in Space Grotesk and heading three in Geist; and the browser console reports no errors. Two scenarios remain genuinely manual and are called out as open: first paint over file:// and keyboard-only operation of the theme control.

## Verification

- Full repository suite 5777/5777 — Layer 1 1428, Layer 4 4163, Layer 5 186.
- Every one of the 73 checks mutation-proved: neutralized to return nothing and required to fail. None vacuous.
- Browser-verified in Chrome in both themes: the mark mounts and tracks the theme, the opt-out container stays empty, h1/h2 render Space Grotesk and h3 Geist 600, all nine font faces load with display swap, the policy declaration is a direct child of head, and the namespaced storage key round-trips.
- Roughly half the checks are vacuous against the real gallery by design — this feature ships zero artifacts — so they run against synthetic fixtures, asserted explicitly rather than left implied.

## Scope

- speckit-pro/artifact-gallery/ — six new shipped files.
- speckit-pro/speckit_pro_runner/gates/payloads.py — two lines.
- tests/speckit-pro/unit/test-artifact-gallery.py plus its suite-manifest registration.
- specs/art-001-brand-kit-gallery-foundation/ — spec, plan, tasks, contracts, and process artifacts.
- Regenerated payloads and installed-cache proofs.

## Known Gaps

- Two manual scenarios remain open (T026/T027) — first paint with no flash over file://, and keyboard-only operation. A harness was built and reviewed in-browser; what remains is a real file:// load, which the browser tooling cannot navigate to.
- MIT attribution needs a human decision before ART-002 lands ports. Whether these re-skins clear the licence's undefined substantial-portion bar is unresolved by any authoritative source; the header wording deliberately over-attributes.
- Three brand-owner questions: may brand red be tuned per theme; is the danger red acceptable as the dark-theme emphasis colour; may the muted surface be lightened — the cheapest structural fix, which would restore contrast headroom for every boundary token at once.
- In-document policy enforcement over file:// is confirmed against browser-engine source, not executed in a browser. One manual check, owned by the first port spec.
- Authored volume overran its estimate substantially and the overrun is disclosed in the spec rather than absorbed: 7,838 authored lines across nine files, 6,322 of them the validation module, which is roughly fourteen times its ~450-line estimate.
