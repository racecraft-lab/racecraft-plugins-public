# PR for #1378: human-authenticated harm-halt clear

This PR stacks on the harm-halt PR (#1370). It replaces that PR's
refuse-every-clear stub with a token-gated clear. Where this doc and the
"Human recovery" or dry-run notes in `docs/pr-1370-harm-halts.md` disagree,
this doc describes the current behavior.

## Shape

`helpers/harm_halt.py` stays the one owner of the halt domain:

- `record_halt` mints `secrets.token_urlsafe(32)`, writes only its SHA-256
  digest (`clear_token_sha256`) in the same durable record write, and then
  calls `show_on_owner_terminal`. Every caller (the helper, the plan-stage
  terminal, the sweep isolation failure) gets the same token path.
- `show_on_owner_terminal` writes the token to the outermost terminal in the
  process ancestry, read with `/bin/ps`. It refuses a device that the runner's
  standard streams or controlling terminal use. Any doubt (no terminal, `ps`
  refused, not a character device, write failure) withholds the token. It
  never falls back to stdout, stderr, the environment or a file.
  Short writes retry the unwritten suffix until the entire terminal frame is
  delivered; a zero-byte return or `OSError` reports `not_delivered`.
- `clear_halt` checks the token against the digest with `hmac.compare_digest`
  and removes the record under the same publication lock that recording uses.
  A wrong, empty, non-string or missing token, a record without a digest, and
  a clear with no standing halt are refused. A used token cannot match the next
  halt's fresh digest.
- A `dry_run` clear returns `would_clear` and `clear_refusal` and changes
  nothing; it does not spend the token. Like apply, it checks the lock before
  the token: a held publication lock beside a standing record reports `would_clear: false` with
  the same "ledger locked" text apply refuses with (review R1380-fb74189c).
- A second trigger refused because a halt already stands changed nothing, so
  it releases the publication lock; the owner's token still clears the first
  halt. An aborted publication still keeps its lock (fail closed).
- Helper answers report `record` without the digest. Every answer that records
  a halt reports `clear_token: shown_on_owner_terminal | not_delivered`: the
  `harm-halt` halt action, a plan-stage stop with `halt_record_status:
  recorded`, and the sweep isolation failure (review R1380-74e6ebf8). A
  `blocked` or `unavailable` answer minted no token and carries none. Refusal
  text never repeats the token.
- `SPECKIT_HARM_HALT_TERMINAL=off` only withholds the token. The suite child
  environment sets it so a test halt never prints on a developer's terminal.

## Known limits

- **Same-login agents.** The token stops a clear that only follows
  instructions, not an agent that works around the runner. An agent with the
  operator's shell can delete `halt.json`, or rewrite its digest to one of its
  own tokens, by hand; neither gives more than deleting the file. This matches
  the `recorded` assurance level of ADR 0017. The owner's terminal can also be
  read back through tmux, screen or terminal scripting until the token is used.
- **Agent-steered terminals.** The agent chooses how it launches the runner.
  A planted instruction can ask it to wrap runner calls in a PTY it reads and
  detach that PTY from the owner's terminal (a detached `script` or tmux
  session, or `claude -p` inside a Codex PTY). A halt recorded in that launch
  then shows the token to that agent. The standard-stream guard does not catch
  it, and no process-tree check can tell an agent's PTY from a human's. A halt
  already shown to the owner is never re-shown, and an ancestry deeper than the
  64-process walk withholds the token (review finding, fixed red-first).
  **Accepted by the owner on 2026-10-18** as a known limit of this PR; it is
  reachable when an agent launches the runner in an agent-readable detached
  terminal. Follow-up #1382 tracks an out-of-band owner channel. This PR does
  not close that gap.
- **Codex sandbox.** The Codex macOS sandbox is reported to refuse `ps`. Then
  the token is withheld: the halt records and blocks, and only manual human
  recovery clears it. Not exercised live; the probe was refused in this session.
- **Live terminal write.** The write to a real Claude Code or Codex owner
  terminal was not exercised (auto mode refused opening the owner's terminal).
  Tests cover the path with `os.openpty` pairs. A full-screen interface may
  redraw over the line; the token is framed by blank lines so scrollback keeps
  it.
- **Desktop apps and CI.** With no terminal in the ancestry (desktop apps,
  GitHub Actions), the token is withheld and manual recovery applies.
- **Rollback text covers refused clears only (review R1380-abc624ca, Info).**
  The registry rollback sentence for `harm-halt` (`registry.py`) says a refused
  clear preserves any standing halt; it does not describe a refused `halt`
  trigger. After the R1380-fb74189c fix, a refused trigger keeps a lock only
  when its own publication aborts or the standing record cannot be read, which
  fails closed by design, and `REFUSAL`
  in `harm_halt.py` already tells the caller a human must inspect a kept lock.
  Not a reachable wrong result, so the sentence stays as is.
- **Dry run skips the ignore-marker check (cross-host review of `cfca10bf`,
  Low).** Apply enters `exclusive_ledger`, which refuses when
  `.specify/harm-halt/.gitignore` is a directory; `planned_clear` checks that
  marker only when no record stands. With a halt standing and the marker
  replaced by a directory, a dry run reports `would_clear: true` and apply
  refuses. Reaching it needs someone to tamper with runner-owned storage after
  the halt, and the result fails closed: the halt stands and the refusal names
  the marker. The guidance therefore names only the checks a dry run makes.
