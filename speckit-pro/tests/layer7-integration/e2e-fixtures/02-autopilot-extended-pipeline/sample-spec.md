# SPEC-FIXTURE-EXTENDED — Trivial feature for L7 extended-pipeline e2e

> L7 fixture spec for the extended-pipeline e2e test (G0 → G6).
> Intentionally tiny so the autopilot can complete more phases within
> the live-mode budget cap. Do not derive product requirements from
> this file.

## Feature

A pure-function `is_palindrome(s: str) -> bool` that returns whether a
string is a palindrome. Case-insensitive, ignoring whitespace.

## Goals

- Single function, single behavior, single return type.
- No I/O.

## Non-goals

- Unicode normalization beyond Python defaults
- Performance optimization
- CLI integration

## Acceptance criteria

- `is_palindrome("racecar")` returns True
- `is_palindrome("hello")` returns False
- `is_palindrome("A man a plan a canal Panama")` returns True
- `is_palindrome("")` returns True (vacuously)
