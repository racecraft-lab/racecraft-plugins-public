# gate-no-fence — SKIP

This marker has NO `---` frontmatter fence at all, so there is no parseable
frontmatter and no readable `structureVersion`. Treated as absent -> skipped.

structureVersion: 1
up: "[parent](../../gate.md)"
spec_id: "gate-no-fence"

(The lines above are body text, not frontmatter: with no opening `---` fence on
line 1, a total/safe gate read must NOT mistake them for gated frontmatter.)
