# Suite checkout lock review notes

## Review fixes

- Lock errors refuse execution. A supported checkout refuses both quick and CI
  wrapper execution with exit 75 if opening or acquiring its lock fails. An
  unwritable lock file does not imply that the staging tree is read-only or
  isolated. Entry-point tests cover permission errors and filesystem errors
  from `flock` without starting children.
- The raw CI runner request takes the lock. The lock module now lives in the
  runner core (`speckit-pro/speckit_pro_runner/suite_checkout_lock.py`), and
  the suite gate holds it around every command set. The raw command CI and
  container preflight send is refused while another suite holds the checkout:
  `missing_prerequisite` (exit 3) with a `suite_lock_held` diagnostic, before
  any command starts.
- The lock lives as long as the suite's main dispatch chain. Each dispatcher
  (`run-ci-suite.py`, `run-all.py`, the suite gate, `run-layer-scripts.py`)
  passes the locked descriptor to its children, so the kernel lock stays held
  until the last of them exits. Killing the process that took the lock no
  longer admits a second suite while a child still runs.

## Known limits

- Windows without `fcntl` remains outside this ticket's supported platforms.
  That fallback cannot occur on the supported Linux and macOS hosts.
- A source tree without git metadata runs unguarded. It is not a supported git
  checkout; isolated archive copies used by the test runner reach this path.
  The CLI entry points print a warning; the suite gate and the layer dispatcher
  stay silent, because the runner's stderr is a JSON channel. The fallback must
  not be treated as concurrency protection.
- A process whose `SPECKIT_SUITE_LOCK` names the checkout's lock file counts as
  part of the running suite and does not lock again. Only a lock holder sets
  it, for its own children, so a second session never has it. A shell that
  exports it by hand disables the guard for that checkout.
- Only the suite's own dispatch chain receives the descriptor. A grandchild a
  test starts with a plain `subprocess` call runs inside the suite but does not
  extend the lock. If every descriptor holder dies while such a grandchild
  still runs, a second suite can start; test grandchildren are short-lived and
  owned by a test process that holds the descriptor.
- The runner reports a refusal as exit 3, not 75: the runner envelope fixes its
  exit codes. The wrappers still exit 75 before they start the runner.
- Every suite-gate operation takes the lock, including
  `run-toolchain-preflight`, so a standalone toolchain preflight is refused
  while another suite runs in the same checkout.
- Lock-file paths trust local checkout metadata (F1302-585b6aa9). Symlinks
  or hard links can cause truncation of their writable target; replacing the
  lock inode, replacing the Git directory, or retargeting a linked worktree
  can admit a second holder. These forms require local write access that
  already permits modifying the affected target or checkout state. They are
  the prior review's Low limits, not protection against a local code executor.
- The inherited environment marker is not proof of a held descriptor
  (F1302-cd7b5944). A marker without a descriptor, with a missing or mismatched
  descriptor, with an unlocked same-inode descriptor, or retained by a stale
  descendant can bypass acquisition. These forms require a contributor-controlled
  process or the suite's descendant environment; ordinary independent suite
  launches do not receive the marker.
- Quick-suite toolchain preflight does not pass the lock descriptor through
  `run_runner` (F1302-b8c5916a). Killing the wrapper during preflight can leave
  its checker running after the lock is released. That checker does not write
  shared staging state, so the reviewed path demonstrated no corrupting overlap.

## Test review clarifications

- The acquisition after `assertRaises(RuntimeError)` is reachable: the assertion
  context catches the deliberate suite exception before execution continues.
  A temporary failing assertion at that point failed exactly the exceptional
  release test; removing the probe restored all 21 passing checks.
- The lock test imports `unittest` and its mock submodule with consistent
  `import` syntax; its existing assertions and mock behavior are preserved.
