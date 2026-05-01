# SPEC-FIXTURE-MINIMAL — Trivial feature for L7 e2e smoke

> This is an L7 integration-test fixture spec, not a real SpecKit
> feature spec. It is intentionally tiny so the autopilot can complete
> phases G0–G3 within the live-mode budget cap. Do not derive product
> requirements from this file.

## Feature

Add a `--greeting` flag to a hypothetical CLI tool that prints a short
greeting and exits. Default greeting: `"hello"`. The flag accepts any
non-empty string.

## Goals

- Single flag, single behavior, single output line.
- No external dependencies.

## Non-goals

- Localization
- Configuration files
- Multi-line output

## Acceptance criteria

- `tool --greeting hi` prints `hi\n` and exits 0.
- `tool --greeting ""` exits non-zero with an error message.
- `tool` (no flag) prints `hello\n` and exits 0.
