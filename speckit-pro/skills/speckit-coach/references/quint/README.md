# Quint references

This directory contains attributed upstream guidance used only for model
authoring. It does not install tools or activate formal checking.

- Upstream trees: `quint-lang/` and `quint-modeling/`
- SpecKit-derived witness and trace guidance: `witness-and-trace.md`
- Upstream notice: [`UPSTREAM-NOTICE.md`](UPSTREAM-NOTICE.md)
- Machine-readable provenance: [`provenance.json`](provenance.json)

Original project: **Quint LLM Kit**, by **Informal Systems Inc.**
Upstream repository: `quint-co/quint-llm-kit`
Pinned upstream commit: `cc75369f741af7d490936f82002c2d28e3b3d78d`
License: **Apache-2.0**

## Copy fidelity

Twelve of the twenty copied upstream files are byte-for-byte copies and are
labelled `verbatim` in [`provenance.json`](provenance.json). For each one the
recorded `sha256` and `upstream_sha256` are both present and equal, so the
local copy and its upstream source hash identically.

Eight files are labelled `adapted`. Each adaptation is mechanical and is
recorded per file in `provenance.json` together with the original upstream
SHA-256 and the transform that produced it:

- Five files under `quint-lang/guidelines/` had a code-fence info string
  normalized to the portable shell tag the plugin allows. Only the info string
  moved; every sample command inside the fence is unchanged.
- One helper filename named in prose in `quint-modeling/examples/README.md` lost
  its script extension.
- `quint-lang/SKILL.md` and `quint-modeling/SKILL.md` ship as `OVERVIEW.md`.
  Their bytes are unchanged; only the path moved, so neither platform treats the
  upstream entry document as a skill entrypoint.

The normalization exists because the repository's plugin shell-confinement
guard blocks shell-dialect tokens and script filenames anywhere under
`speckit-pro/` and the generated payloads; `provenance.json` names the exact
contract. Adapted files are still upstream text carrying upstream attribution;
they are not SpecKit-authored guidance.

## Reading the upstream prose

The upstream text is unedited, so it still refers to its own layout. Two
rules cover every such pointer:

- `SKILL.md` in upstream prose means the sibling `OVERVIEW.md` in the same
  tree. `../SKILL.md` from `quint-modeling/guidelines/` means
  `quint-modeling/OVERVIEW.md`, and `quint-modeling/SKILL.md` means the same
  file.
- `quint-execute-spec`, `mcp-servers/`, the Docker image, and the LSP bridge
  are not adopted here. Upstream prose that points at them describes the full
  upstream kit, not anything SpecKit Pro ships or expects you to install.

## Not active skills

Neither tree is an active skill inside SpecKit Pro. They are references to be
supplied by the parent when a Quint model is explicitly selected. SpecKit Pro
still owns selection, approved requirements, phase order, output paths, gate
decisions, and formal-check execution. Availability of these references or
Quint/Apalache tools never enrolls a feature.
