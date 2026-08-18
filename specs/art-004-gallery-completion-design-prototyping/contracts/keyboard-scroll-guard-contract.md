# Contract: Keyboard-Scroll Guard

## Scope

This contract applies to every shipped gallery artifact swept from `speckit-pro/artifact-gallery/manifest.json`.

## Markup Contract

Every intentional horizontal overflow region must carry:

```html
data-rc-keyboard-scroll="horizontal"
tabindex="0"
role="group"
aria-label="<specific non-empty artifact label>"
```

Declared regions must appear in the same sequential focus order as their source
order and must not rely on positive `tabindex`. The accessible name must identify
the artifact-specific content, not a generic phrase such as "scroll area".

## Guard Contract

- The Layer 4 guard uses the existing standard-library `html.parser` collector.
- The guard does not parse CSS selectors to infer the contract.
- The guard rejects a declared horizontal-scroll region missing `tabindex="0"`.
- The guard rejects a declared horizontal-scroll region missing `role="group"`.
- The guard rejects a declared horizontal-scroll region with an absent, empty, or generic `aria-label`.
- The guard rejects positive `tabindex` values in shipped gallery artifacts.
- The guard report records each declared region's artifact ID, source-order
  index, and accessible name for manual focus-order review.
- A bounded raw-source check rejects horizontal overflow styling when an artifact declares no keyboard-scroll regions.
- The guard proves the six new ART-004 IDs plus `code-approaches`, `implementation-plan`, and `module-map` are swept after the status flips.
- The guard proves the five known existing affected regions are declared and compliant.

## Negative Fixture

The red fixture is an in-memory `GalleryFixtureCase` with one shipped synthetic artifact. Its declared horizontal region has `data-rc-keyboard-scroll="horizontal"`, `role="group"`, and a valid `aria-label`, but omits `tabindex`.

The durable test name is:

`test_rejects_declared_scroll_region_without_keyboard_route`

## Manual UAT Contract

For each target region:

1. Open the artifact over `file://`.
2. Focus the declared horizontal region by keyboard in source order.
3. Verify the accessible name remains exposed.
4. Verify the visible focus indicator is present.
5. Send the horizontal arrow key supported by the browser.
6. Confirm horizontal scroll position changes without pointer input.
7. Confirm focus can leave the region by keyboard without a trap.

Safari UAT states whether Tab or Option-Tab was used to reach each focusable
scroll region, matching the active Safari keyboard-navigation setting.

ART-004 records separate UAT results and does not overwrite ART-003 harness outputs.
