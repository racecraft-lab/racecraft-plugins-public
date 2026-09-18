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

Fifteen of the twenty upstream files are byte-for-byte copies and are labelled
`verbatim` in [`provenance.json`](provenance.json). For each one the recorded
SHA-256 is both the upstream hash and the hash of the local copy.

Five files are labelled `adapted`, plus one file in `quint-modeling/examples/`.
Each adaption is mechanical and is recorded per file in `provenance.json`
together with the original upstream SHA-256:

- A code-fence info string was normalized to the portable shell tag the plugin
  allows. Only the info string moved; every sample command inside the fence is
  unchanged.
- One helper filename named in prose lost its script extension.

The normalization exists because the repository's plugin shell-confinement
guard blocks shell-dialect tokens and script filenames anywhere under
`speckit-pro/` and the generated payloads; `provenance.json` names the exact
contract. Adapted files are still upstream text carrying upstream attribution;
they are not SpecKit-authored guidance.

## Not active skills

Neither tree is an active skill inside SpecKit Pro. They are references to be
supplied by the parent when a Quint model is explicitly selected. SpecKit Pro
still owns selection, approved requirements, phase order, output paths, gate
decisions, and formal-check execution. Availability of these references or
Quint/Apalache tools never enrolls a feature.
