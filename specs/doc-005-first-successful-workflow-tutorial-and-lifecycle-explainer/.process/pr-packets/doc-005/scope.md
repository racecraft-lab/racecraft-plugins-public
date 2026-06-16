# DOC-005 Scope Review

## Expected Implementation Scope

- `docs-site/src/content/docs/first-run.md`
- `docs-site/src/content/docs/spec-kit-lifecycle.mdx`
- `docs-site/src/components/LifecycleFlow.astro`
- DOC-005 spec/process artifacts and PR-packet evidence

## Out Of Scope

- Plugin runtime behavior
- Generated install payloads
- Marketplace catalogs
- Installer scripts
- Release automation
- Exhaustive reference, selector, troubleshooting, or trust content

## Decision

Scope remains docs-site and DOC-005 process evidence only. The implementation
uses the existing install pages and `speckit-pro/README.md` as source evidence
without editing those read-only evidence surfaces.
