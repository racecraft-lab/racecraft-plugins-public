# Tasks: Pin the runtime to a new major

This change bumps a global runtime version, which touches every consumer at once,
so it must land atomically despite the additive surfaces alongside it. The bump
names a concrete target version, not a placeholder.

- [ ] T001 [P] Bump the Node runtime to v20 in `.nvmrc` and pin the engines field
  in `package.json` so the whole repo moves together.
- [ ] T002 [P] Add a new compatibility shim module in `src/compat/node20.ts`
  (a fresh additive surface).
- [ ] T003 [P] Add a new diagnostics panel in `src/components/RuntimeInfo.tsx`
  that displays the pinned runtime version.
