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
- `clear_halt` checks the token against the digest with `hmac.compare_digest`
  and removes the record under the same publication lock that recording uses.
  A wrong, empty, non-string or missing token, a record without a digest, and
  a clear with no standing halt are refused. A used token cannot match the next
  halt's fresh digest.
- A `dry_run` clear returns `would_clear` and `clear_refusal` and changes
  nothing; it does not spend the token.
- Helper answers report `record` without the digest, and a halt answer reports
  `clear_token: shown_on_owner_terminal | not_delivered`. Refusal text never
  repeats the token.
- `SPECKIT_HARM_HALT_TERMINAL=off` only withholds the token. The suite child
  environment sets it so a test halt never prints on a developer's terminal.

## Known limits

- **Same-login agents.** The token protects the runner command, not the files.
  An agent with the operator's shell can delete `halt.json` by hand. This
  matches the `recorded` assurance level of ADR 0017.
- **Nested agent terminals.** When an agent's own PTY is the outermost terminal
  (for example `claude -p` started inside a Codex PTY with piped stdio, or a
  detached tmux pane an agent started), that agent can read the token. The
  standard-stream guard does not catch it, and no process-tree check can tell
  an agent's PTY from a human's. Reaching it needs a halt recorded under that
  dispatch shape; a halt already shown to the owner cannot be re-shown.
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
