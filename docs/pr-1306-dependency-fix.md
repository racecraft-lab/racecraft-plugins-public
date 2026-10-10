# Docs dependency repair

PR #1306 removes Astro's unused optional Sharp dependency and keeps the
source-map-js and postcss-selector-parser security updates.

The dependency-review failure was caused by the updated Sharp/libvips binary
packages matching the existing LGPL license deny-list. The site already uses
Astro's passthrough image service, and its Open Graph cards use CanvasKit.
Removing the unused dependency fixes the failure without an exemption or a
change to the license and vulnerability gates.

## Known limits

- The Sharp removal depends on the existing passthrough image service in
  `docs-site/astro.config.mjs`. A future switch to Sharp image processing must
  restore its dependency. That configuration is absent from this PR, so a
  missing-Sharp error is unreachable in the current image-service path.
- Full browser validation runs in GitHub CI. The local VM suite allow-list has
  no docs validation entry; local frozen installation, Astro checks, static
  build, link validation, and Open Graph PNG generation are separate evidence.
- Linux VM plugin CI cannot cover macOS plugin behavior or the two real-sandbox
  cases `test_pr_test_code_cannot_touch_the_host_under_the_real_sandbox` and
  `test_pr_test_code_cannot_create_or_modify_any_file_in_the_clone`. The
  orchestrator runs those before merge.

Sources: [Astro passthrough service](https://docs.astro.build/en/reference/errors/missing-sharp/)
and [pnpm 10 dependency removal](https://pnpm.io/10.x/settings#overrides).
