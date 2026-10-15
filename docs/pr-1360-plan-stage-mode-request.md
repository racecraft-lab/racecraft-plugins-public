# Plan-stage mode request

Issue #1359: a Codex host that can nest always ran the plan stage nested, so
the canary could not produce the flat Codex run that ADR 0026's Gate 8 needs.

## Rule

`resolve-nesting-mode` takes an optional `requested_mode`. When the request
omits it, the helper reads `SPECKIT_PLAN_STAGE_MODE` unchanged from the
environment the runner inherits. The orchestrator runs no command to read it,
so Claude's run-start allow rules still cover the whole step.

- `flat` returns `mode=flat` with `reason=operator_requested_flat`, even when
  the probe is `allowed`.
- `nested` never overrides a `refused` or `not_run` probe.
- An empty or invalid value returns `mode=flat` with `reason=probe_invalid`.
- With no request, the decision is unchanged; the answer adds
  `requested_mode: null`.

## Known limits

- **Canary acceptance is not proven here.** The canary harness and its
  `mode.not_scheduled` check live outside this repository. The next scheduled
  flat Codex leg must set `SPECKIT_PLAN_STAGE_MODE=flat`. The local receipt
  test only shows a flat answer is a valid receipt mode.
- **`configured_depth` stays `null` on Codex.** The orchestrator cannot read an
  effective `-c agents.max_depth` override, so the skill omits the value. The
  ticket proposed no fix, and depth never decides the mode.
- **Invalid request reports `probe_invalid`.** A bad
  `SPECKIT_PLAN_STAGE_MODE` value is reported with the same reason as a bad
  probe, and a refused probe then shows no prerequisite hint. It always falls
  back to flat, the safe side.
- **Precedence is described in operator docs.** `prerequisites.md` and
  `GLOSSARY.md` state the precedence for operators. The runner alone decides;
  the skill and agents no longer restate it.
