# UAT Runbook: prsg-002-moc-templates

| Field | Value |
|-------|-------|
| Spec | prsg-002-moc-templates |
| Branch | prsg-002-moc-templates |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-06T18:42:12Z |



## Env Setup

No build, typecheck, or lint step is needed. This is a shell + Markdown change with no compiled output.

From the repo root, run the full test suite with:

```bash
cd speckit-pro && bash tests/run-all.sh
```

This runs the deterministic layers (structural file checks, script unit tests, and agent tool-scope checks). A passing run prints zero failures and exits 0. Expect all checks to be green before and after every step below.


## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Templates + scaffold-time skeleton (Priority: P1)

This story delivers two reusable template files for building navigation maps, and ensures that every newly scaffolded spec automatically gets a minimal marker file that links it to its parent roadmap.

1. From the repo root, confirm both template files exist:

   ```bash
   ls speckit-pro/skills/speckit-coach/templates/roadmap-moc-template.md \
      speckit-pro/skills/speckit-coach/templates/spec-moc-template.md
   ```

   **Expected:** Both file names are listed. No "No such file" error.

2. Open `speckit-pro/skills/speckit-coach/templates/spec-moc-template.md` in any text editor or with `cat`. Scroll to the top frontmatter block (between the `---` lines).

   **Expected:** All six fields are present: `up`, `related`, `status`, `rank`, `spec_id`, and `structureVersion`. The `structureVersion` value is the literal `1`. The `up` and `spec_id` fields contain `{{TOKEN}}` placeholders that the scaffold skill fills in for each new spec.

3. Open `speckit-pro/skills/speckit-coach/templates/roadmap-moc-template.md` and check its frontmatter the same way.

   **Expected:** The same six fields are present. The `structureVersion` value is the literal `1`.

4. Confirm the marker file for this spec itself exists and is correctly filled in:

   ```bash
   cat specs/prsg-002-moc-templates/SPEC-MOC.md
   ```

   **Expected:** The frontmatter contains:
   - `up:` — a `[text](path)` style link (not a `[[wikilink]]`) containing the relative path `../../docs/ai/specs/pr-size-governance-technical-roadmap.md`.
   - `structureVersion: 1`
   - `spec_id: "PRSG-002"`

5. Confirm that link in `up:` actually resolves. From the repo root:

   ```bash
   ls docs/ai/specs/pr-size-governance-technical-roadmap.md
   ```

   **Expected:** The file is listed. No "No such file" error.

- [ ] All five steps above passed as described.

---

<a id="us-2"></a>
### User Story 2 - Version-gated lints + namespace-aware ID normalization (Priority: P2)

This story delivers two automated checks. One flags a navigation map that has no valid parent link. The other flags a map that contains a broken link or a wiki-style link (which is not allowed). Both checks run automatically in CI for every newly created spec, while all pre-existing specs are left untouched.

**Run the two checks standalone**

1. From the repo root, run the orphan check (confirms every navigation map in a version-marked spec has a valid parent link):

   ```bash
   bash speckit-pro/tests/layer1-structural/validate-moc-orphan.sh; echo "exit=$?"
   ```

   **Expected:** Output ends with `exit=0`. No files are reported as violations. This confirms the orphan check passes against all real spec trees in this repo.

2. From the repo root, run the stale-index check (confirms every link in a version-marked navigation map resolves to a real file and contains no wiki-style links):

   ```bash
   bash speckit-pro/tests/layer1-structural/validate-moc-stale-index.sh; echo "exit=$?"
   ```

   **Expected:** Output ends with `exit=0`. No files are reported as violations.

3. From the repo root, run the exit-code unit tests, which verify that a map with a broken link causes a failure exit and that an internal script error is reported separately from a content violation:

   ```bash
   bash speckit-pro/tests/layer4-scripts/test-moc-lint-exit-codes.sh
   ```

   **Expected:** All assertions pass. The final line shows 0 failures.

**Confirm pre-existing specs are not affected**

4. From the repo root, list the `specs/` directory:

   ```bash
   ls specs/
   ```

   Pick any folder from the listing that is NOT `prsg-002-moc-templates`, then check whether it contains a marker file:

   ```bash
   ls specs/<that-folder-name>/SPEC-MOC.md 2>/dev/null || echo "no marker — correct"
   ```

   **Expected:** "no marker — correct" is printed. Pre-PRSG-002 spec folders carry no `SPEC-MOC.md`, so the checks skip them entirely.

5. Run the full test suite and confirm it stays green:

   ```bash
   cd speckit-pro && bash tests/run-all.sh
   ```

   **Expected:** Zero failures. The run exits 0.

**Confirm ID matching does not confuse similar-looking IDs**

6. Observe that the marker for this spec uses `spec_id: PRSG-002` and its folder is named `prsg-002-moc-templates`. The checks treat these as a match because both share the prefix `prsg` and the number `002`. Confirm the checks pass (step 1 and 2 above already verified this). The important thing: `PRSG-002` does NOT match a folder like `002-pr-checks-workflow` (different prefix), and `013a` does NOT match `013a1` (different number). These distinctions are tested by the unit tests in step 3.

- [ ] All six steps above passed as described.



## FR Coverage Matrix

| Behavior the PR promises | Where it is proven above |
|--------------------------|--------------------------|
| Every new spec is born with a parent link on creation — no manual step | Story 1, step 4 (SPEC-MOC.md exists with `up:`) + step 5 (link resolves) |
| Two reusable template shapes carry the full six-field frontmatter contract | Story 1, steps 1–3 |
| Adopting this feature on the existing repo produces zero new check failures | Story 2, steps 1, 2, 5 (all checks exit 0 against real spec trees) |
| A broken or wiki-style link in a navigation map is caught before merge | Story 2, step 3 (exit-code test verifies violation exits nonzero) |
| `PRSG-002` and `SPEC-002` are never confused; `013a` and `013a1` are never confused | Story 2, steps 3 and 6 (unit tests exercise these exact pairs) |
| Pre-existing specs without a marker are silently skipped — they never cause a failure | Story 2, step 4 (no marker in legacy dirs) + step 5 (suite stays green) |


## Negative-Path Tests

Try these to confirm the checks behave safely on bad or unexpected input. Each is a "try this → expect this safe outcome" exercise.

- **No marker file present**: A spec folder that has no `SPEC-MOC.md` is completely ignored by both checks. Neither check reports a failure for it. You can confirm this by looking at any pre-PRSG-002 spec folder (Story 2, step 4) — the suite stays green.

- **Marker file has no `structureVersion` field, or the value is not a plain integer** (for example `"1"` in quotes, or `1.0`): The check reads the field, finds it is absent or not a bare integer, and silently skips that spec. It does not report a failure.

- **Marker file is present but `spec_id` is missing or empty**: The check treats a missing join key as a violation and reports the offending file. A navigation map that cannot be identified cannot be linked correctly.

- **`spec_id` does not match the folder name**: For example, a marker inside `prsg-002-moc-templates/` with `spec_id: PRSG-999`. The check reports a violation naming the file and the mismatch.

- **Link in a map points to a folder rather than a file, or to a broken symlink**: Both are treated as "does not resolve" — a violation is reported. Only links to real, readable files are accepted.

- **A `[[wikilink]]` appears anywhere in a navigation map**: The stale-index check flags it as a violation regardless of whether a file with that name happens to exist. Only relative `[text](path.md)` style links are allowed.

- **One of the spec tree folders (`docs/ai/specs/` or `specs/`) does not exist in a consumer project**: The check skips the missing tree without error. A project that has only one tree still gets full coverage of the tree it has.

- **The check finds zero navigation maps that have a version marker** (for example, a brand-new empty repo): Both checks exit 0. An empty checkable set is a passing run.

- **A content violation (broken link) vs. an operational error (check cannot read a required file)**: These are reported differently. A content problem names the file and the rule that failed. An operational error is reported to a separate output channel and gets a different exit code, so you can tell the two apart.


## Self-Review Findings

**Self-Review:** <not available — workflow file not provided>

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations
