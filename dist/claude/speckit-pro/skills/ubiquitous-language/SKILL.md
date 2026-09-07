---
name: ubiquitous-language
description: "Build or refresh the repository's ubiquitous-language terms document, a committed Markdown table of domain terms (term, meaning here, identifiers) that humans and agents read before designing. Use when the user asks to define domain terms, create or update a glossary or ubiquitous language, pin what a term means in this codebase, reconcile names between the spec and the code, or invokes /speckit-pro:ubiquitous-language. Also runs the advisory identifier lint on a diff. Not for scoping interviews, PRD authoring, or general SDD coaching."
argument-hint: "optional: a domain area, a spec path, or 'lint <base>'"
user-invocable: true
license: MIT
---

# Ubiquitous Language

Write and maintain `docs/ai/specs/ubiquitous-language.md`: one table of the
domain terms this repository uses, what each means here, and the code
identifiers that carry it. Grill Me and PRD authoring read it when present, so
a term is pinned once and reused instead of re-derived in every interview.

## Ground recommendations

Inspect the tools and skills actually available. Follow the shared
[capability-discovery](${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/capability-discovery.md)
and [grounding](${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/grounding.md) contracts.
A term's meaning comes from the code and documents that use it; disclose
uncertainty and do not invent a definition.

## Workflow

1. **Read what exists.** If `docs/ai/specs/ubiquitous-language.md` exists,
   read it first and treat its rows as settled unless the user reopens one.
   Read `.specify/memory/constitution.md`, the technical roadmaps under
   `docs/ai/specs/`, and any PRD under `docs/` for terms already in use.
2. **Scan the repository.** Collect candidate terms from module and package
   names, exported classes and functions, database tables and columns, API
   routes, and README or docs headings. Group names that split the same
   concept (`Invoice`, `bill`, `statement`) and names that overload one word
   for two concepts.
3. **Propose the table.** For each term, write one row: the term, its meaning
   in this repository in one sentence, and the identifiers that carry it.
   Where the codebase disagrees with itself, propose one term and list the
   other spellings under Identifiers so the lint maps them. Ask the user about
   a genuinely ambiguous term with `AskUserQuestion`, one term at a time, with
   your recommendation first; do not ask about terms the evidence settles.
4. **Write the document** only after the user confirms the proposal. Keep the
   format exactly:

   ```markdown
   # Ubiquitous Language

   | Term | Meaning here | Identifiers |
   |---|---|---|
   | Invoice | A billable statement issued to one customer for one period. | `Invoice`, `invoice_ledger` |
   ```

   Preserve existing rows and their order on an update; append new terms;
   never delete a row without saying which identifiers lose their mapping.
5. **Lint, advisory only.** Run
   `${CLAUDE_PLUGIN_ROOT}/scripts/ubiquitous-language-lint.py --base <base>`
   (default base `origin/main`). It prints a JSON report of declared
   identifiers in the diff that map to no term. Report the summary and the
   unmapped identifiers to the user; suggest a term or a rename for each. The
   lint always exits 0 and never blocks a gate.

## Output contract

- `docs/ai/specs/ubiquitous-language.md`: the terms table above, committed.
- A short report: terms added, changed, or kept; unmapped identifiers from
  the lint with a suggestion each.

This skill does not conduct a scoping interview (`/speckit-pro:grill-me`),
author a PRD (`/speckit-pro:speckit-prd`), or explain SDD
(`/speckit-pro:speckit-coach`).
