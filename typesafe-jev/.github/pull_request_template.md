## What and why

<!-- What changed, and the reasoning someone will need in a year. The diff
already shows what; this should say why, and what you rejected. -->

## Behaviour changes

<!-- Anything that behaves differently than before, including for someone
upgrading. Write "none" if there are none. -->

## Provider contract

<!-- If this changes what is sent to or accepted from a provider, cite the
source in docs/provider-contracts.md with a fetch date. Say whether a new rule
is the provider's requirement or this fork's policy. Delete if not applicable. -->

## What you ran

<!-- Actual commands and results. Mark anything you could not run as NOT RUN
with the reason, rather than leaving it implied. -->

- [ ] `task check` (gofmt, vet, tests with `-race`)
- [ ] Tests added or updated for the changed behaviour
- [ ] Docs updated if behaviour or configuration changed

## Credentials

- [ ] No key, token, or real provider response is included in this change
