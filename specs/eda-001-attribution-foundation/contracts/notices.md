# Contract: Holder-Specific Notices

**Consumers**: Redistributors and attribution validation. **Requirements**: FR-001, FR-014–FR-016, FR-018–FR-019.

## Matt Pocock notice

Location: `speckit-pro/skills/speckit-coach/references/upstream/mattpocock-skills/UPSTREAM-NOTICE.md`.

Required source identity: upstream `https://github.com/mattpocock/skills`, provenance fork `https://github.com/racecraft-lab/skills`, tag `speckit-pro-baseline`, commit `c55ee46073ed923f86ce59a5eb3b6d895095d1b7`, MIT license and Copyright (c) 2026 Matt Pocock. Explain that files identified as landed by the sibling ledger are modified derivatives; point directly to `ledger.json`. The fork is an anchor only and is not edited.

The raw license comes from the fork's pinned LICENSE and is frozen in `mattpocock-LICENSE.txt` before notice content is authored. It is not reconstructed from another holder's MIT notice. The README acknowledgment names Matt Pocock and links directly to this authored notice.

## HumanLayer notice, slice 2

Location: `speckit-pro/skills/speckit-coach/references/upstream/humanlayer-show-me/UPSTREAM-NOTICE.md`.

Required identity: `humanlayer/skills`, commit `bba9d13ab34f0a87f1cc33df4dd196372393ddfc`, copied source `plugins/show-me/skills/show-me/SKILL.md`, MIT, Copyright (c) 2026 HumanLayer. The notice MUST include the public pinned copied-source URL `https://github.com/humanlayer/skills/blob/bba9d13ab34f0a87f1cc33df4dd196372393ddfc/plugins/show-me/skills/show-me/SKILL.md`. Freeze that commit's raw LICENSE as `humanlayer-LICENSE.txt`. The pr ledger row links to this separate notice with the exact six-field source record.

Historical Apache/head references are superseded and must not be used as the source or license for this work. Both notices are delivered in EDA-001; the second belongs to its second vertical slice.

## License extraction and bytes

Each notice has exactly one heading line `## License`. Within that section there is exactly one fenced block opened by a line containing exactly three backticks and `text`, and closed by a line containing exactly three backticks. The license content starts after the opening fence newline and ends immediately before the closing fence, retaining its own final newline. Other fenced blocks or duplicated License headings/blocks cannot hide a malformed required block.

Read the notice and fixture as bytes. Compare the enclosed byte span to the nonempty fixture directly, with no stripping, newline conversion, Unicode normalization, or substring matching. Extra blank lines inside the block alter the bytes and fail. Surrounding prose is outside the byte equality check, but must retain the required identity/links. Negative cases cover a missing required notice file, missing section, missing block, duplicate section/block, changed holder/content byte, and missing/changed final newline. The missing-file case starts from otherwise valid slice-appropriate inputs and asserts the notice filename and missing-file defect, so an unrelated ledger or credit failure cannot satisfy it.

## Packaging and failure

Regeneration must carry the Matt notice and ledger into both `dist/claude/speckit-pro/` and `dist/codex/speckit-pro/`; after slice 2 both include the HumanLayer notice too. Check actual generated copies and byte equality through the validation guide. Do not modify payload builders or generated files by hand to achieve this.

A missing notice or wrong source identity/pin produces a nonzero test result naming the notice/linked row. A license mismatch names the holder fixture and notice. These checks run regardless of real landed-row count. Notices contain only public source names, URLs, commits, and attribution prose, with no machine-specific paths or shell execution instructions.
