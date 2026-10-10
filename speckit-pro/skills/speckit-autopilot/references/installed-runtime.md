# Installed runner transport

Resolve Python 3.11+ and the root of the plugin loaded in this session before
the first runner request, including workflow binding and scaffold checks.

<!-- host:claude: Claude exposes the root of the loaded plugin -->
Use the absolute `${CLAUDE_PLUGIN_ROOT}` value as `<plugin-root>`.
<!-- /host -->
<!-- host:codex: Codex derives the root from the installed skill location -->
Use the absolute path of this session's loaded `SKILL.md`: its layout is
`<plugin-root>/skills/<skill-name>/SKILL.md`. The parent of `skills/` is
`<plugin-root>`. Resolve that path from the skill location, rather than the
feature checkout or a guessed cache location.
<!-- /host -->

Invoke `[resolved_python, "<plugin-root>/scripts/run-speckit-pro.py"]` with
the placeholder replaced by that absolute plugin root. Keep the current
working directory at the caller's project or bound workflow worktree. Send
one JSON request on stdin, parse one JSON response on stdout, and retain
stderr and the exit code. Pass the same resolved argv and worktree to every
agent that calls a runner helper.

The launcher adds its adjacent plugin root to `sys.path` before executing
`speckit_pro_runner.__main__`. It preserves the runner's request handling,
diagnostics, exit codes and working directory. It needs no `PYTHONPATH`
setting or package installation.

If a legacy bare module call reports `No module named speckit_pro_runner`,
use the resolved launcher argv above from the same worktree. If the launcher
or adjacent `speckit_pro_runner/` is absent in the loaded plugin, report the
incomplete installation and repair it before resuming.
