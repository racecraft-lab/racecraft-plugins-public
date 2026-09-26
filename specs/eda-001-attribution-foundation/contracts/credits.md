# Contract: Derivative File Credits

**Consumers**: Later EDA authors and attribution tests. **Requirements**: FR-009–FR-012, FR-017–FR-018.

## File selection

A landed file destination selects that authored file. A directory destination recursively selects authored `.md`, `.toml`, and `.py` files in sorted repository-relative order; the eligible selection must be nonempty. Generated files, vendored files, test fixtures, and attribution notices are excluded. Exclusions use explicit repository-owned path categories (generated payload/reference outputs, fixed vendored content boundaries, fixture directories, and UPSTREAM-NOTICE.md files); an authored references directory is not excluded merely because its name is references. Keep exclusions local to this test, grounded in the existing repository boundaries, with fixture proofs for empty-after-exclusion selection.

Fixtures are materialized as synthetic authored destinations under a temporary repository-shaped root. The test must not exclude all synthetic cases merely because their source text was loaded from fixtures. Each positive landed case asserts at least one selected file. The actual initial ledger may have zero landed rows; a positive fixture supplies file-coverage evidence instead.

For a file selected by multiple landed rows, aggregate those rows' upstream paths, deduplicate and sort them, and require one matching header. Each selected file is checked individually; another file's credit does not substitute. Later owners must credit every derivative they author and choose destinations whose authored contents satisfy this rule; EDA-001 does not create those contents.

## Exact ordered header lines

1. `Upstream repository: mattpocock/skills`
2. One `Upstream skill: <upstream_path>` line per represented source, sorted lexicographically, with no missing/extra/duplicate identifiers.
3. `Pinned commit: c55ee46073ed923f86ce59a5eb3b6d895095d1b7`
4. `Modified derivative: yes`
5. `License notice: speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/UPSTREAM-NOTICE.md`

The expected source set comes from the selected landed rows, not from trusting the header being tested. Do not use section-level markers.

## Syntax and placement

| File | Header syntax | Permitted prefix |
| --- | --- | --- |
| Markdown | One HTML comment containing the exact lines, with delimiters on their own lines | YAML frontmatter at the start, if present; blank lines |
| TOML | Each exact line prefixed with `# ` | Blank lines |
| Python | Each exact line prefixed with `# ` | Shebang and encoding declaration as allowed by the requirement; blank lines |

The header is the first nonblank body block after the permitted prefix/frontmatter. Reject body text or another unrelated block before it, malformed/unclosed frontmatter, wrong comment form, duplicate provenance blocks, wrong line order, wrong commit/repository/modified state/notice, or a different source set. Preserve any loader frontmatter as the first content; no existing skill validator is changed.

## SKILL.md metadata

A derivative SKILL.md also has a metadata mapping in its frontmatter and exactly one credits field with one quoted YAML string value. The decoded value is built from the same sorted source set:

`mattpocock/skills@c55ee46073ed923f86ce59a5eb3b6d895095d1b7:<upstream_path>`

Join multiple identifiers with exactly `; `. Single-quoted and double-quoted string forms are supported; the recognizer must interpret the designated quoted scalar correctly and compare its value, rather than claim general YAML parsing. Reject a missing/duplicate metadata or credits declaration, non-string collections/numeric values, unquoted or block forms, invalid quoting, different identifiers/order/separators, or disagreement with the header. Host interpretation/presentation is not part of this contract. Include positive cases for both quoted styles and a shared-source case; use isolated negatives to prove header/metadata mismatch rejection.

## Required proof cases

- Valid zero-landed 38-row ledger.
- Landed Markdown without frontmatter; Markdown after frontmatter; SKILL.md with metadata; TOML; Python with and without permitted prefixes.
- Directory selection with one or more eligible files, plus a shared-file multi-source case.
- Missing destination; empty directory; only excluded files; missing or misplaced header; wrong syntax; each mismatched ordered field; empty or extra source set.
- Missing metadata; mismatched value; wrong scalar type/quote form; duplicate metadata/credits declarations.

Failure names the landed upstream path and destination or selected file, plus the failed credit field. No arbitrary failure elsewhere counts as proof of a negative case.
