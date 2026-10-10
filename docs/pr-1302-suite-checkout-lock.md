# Suite checkout lock review notes

## Review fix

A supported checkout now refuses both quick and CI wrapper execution with exit
75 if opening or acquiring its lock fails. An unwritable lock file does not
imply that the staging tree is read-only or isolated. Entry-point tests cover
permission errors and filesystem errors from `flock` without starting children.

## Known limits

- Windows without `fcntl` remains outside this ticket's supported platforms.
  That fallback cannot occur on the supported Linux and macOS hosts.
- A source tree without git metadata still warns and runs unguarded. It is not
  a supported git checkout; isolated archive copies used by the test runner
  reach this path. The fallback must not be treated as concurrency protection.

## Unresolved review findings

- The documented raw CI runner request bypasses the wrapper lock. This is a
  reachable path used by repository CI and container preflight, not an accepted
  limit of the requested checkout protection.
- Terminating only the CI wrapper releases the lock while its child can remain
  alive. A second suite can then acquire the lock against the same staging tree.
  The lock lifetime needs to cover the actual suite, not just its wrapper.
