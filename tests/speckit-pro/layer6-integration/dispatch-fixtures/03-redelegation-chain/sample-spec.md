# SPEC-FIXTURE-003 — User password storage

> L7 redelegation-chain test fixture spec. Intentionally surfaces a
> security-domain ambiguity so the Clarify phase generates an
> unresolved consensus item, exercising the orchestrator → clarify →
> analysts → synthesizer chain.

## Feature

Add a password-storage layer to a hypothetical web application. Users
sign up with an email + password; the password must be hashed before
persistence.

## Requirements

- Hashing must be one-way (no plaintext recovery).
- Verification on login compares the input password against the stored
  hash.
- The chosen algorithm must be configurable behind a single function
  boundary so future migrations are not invasive.

## Open question (intentional, for the fixture)

The spec does not specify whether to use **bcrypt** (the existing
pattern in the codebase) or **argon2id** (the current OWASP-preferred
default for new applications). This is the exact ambiguity that the
Clarify phase should surface and tag with `[codebase, domain]` so the
consensus protocol fans out to both analysts.

## Non-goals

- Multi-factor authentication
- Password-strength policy
- Account-recovery flows
