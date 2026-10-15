# CLI probe operator installs

Issue #1355: the plan-stage pull request query ran `gh` through
`cli_probe.probe`, which rejected every regular file the current user owns. A
standard Homebrew install on Apple silicon is owned by the operator, so
`/opt/homebrew/bin` was dropped and the plan-stage terminal stopped at
`tool_unavailable`.

## Rule

`cli_probe.OPERATOR_CLIS` names `git` and `gh`. For these two CLIs only, a
regular file in a retained PATH directory, or a symlink target from one,
passes `validate_probe_directory` when all of these hold
(`operator_installed`):

- the effective user owns it;
- its mode grants no group or other write;
- no worktree name reaches it or any path its lookup visits. The lookup chain
  holds the PATH directory, its ancestors, the entry, and every link hop and
  hop ancestor. `worktree_reach` counts two kinds of worktree names: a regular
  file with a second hardlink, and the target of any worktree symlink (file
  or directory). Identity is compared by device and inode, so case aliases
  and symlinked hops still match.

The walk skips only a dangling link and a link loop, which reach nothing
now. Every other failure raises and drops the directory (fail closed): an
unreadable directory, and a directory or name that vanishes mid-walk, since a
rename could hide an alias (`test_worktree_walk_errors_fail_closed`).

Every other rule is unchanged, for every CLI. Cwd-relative and empty PATH
entries are skipped. A PATH directory inside the worktree, or any symlink hop
or target inside it, rejects the directory. A file another identity owns but
the runner can write is rejected. Docker keeps the strict file rule. The
`claude` and `codex` host probes keep the strict file rule and the protected
directory rule, and still take only `--version`. `reject_mutable_probe_alias`
keeps its main-branch signature and body, and the operator check runs only
when `probe_search_path` passes a reach callable, which it does only for
`git` and `gh` (`test_operator_owned_helper_still_rejects_docker_and_host_directories`).

## Threat model

The guarded threat is hostile worktree content: files checked out or written
inside the worktree, including checked-out symlinks. That content cannot
reach an accepted file:

- A worktree path, a link hop into the worktree, or a link target in it
  rejects the directory (existing traversal tests).
- A hardlink between the worktree and an accepted file or helper rejects the
  directory (`test_worktree_hardlink_alias_cannot_supply_any_cli`,
  `test_other_cli_probes_reject_worktree_linked_helpers`,
  `test_every_retained_name_rejects_worktree_content_that_reaches_it`).
  Git does not store hardlinks, so a checkout cannot create one.
- A worktree symlink to the PATH entry, the install file, the PATH
  directory, the install directory or a hop directory rejects the directory
  (`test_worktree_symlink_reaching_the_lookup_chain_is_rejected`). An
  in-place write through such a link could otherwise change or replace an
  accepted file.
- A file another identity can write, or one with a group or other write bit,
  is still rejected, including in the relink race tests.

## Known limits

- **Relink or rewrite after validation.** A process running as the operator
  can hardlink an accepted file into the worktree, or rewrite or swap it,
  between validation and launch. For `git` and `gh` the probe no longer
  stops that. Worktree content cannot do it: it needs code running as the
  operator, and that code can rewrite the same file before validation, where
  no check can see it. Closing the window needs the strict ownership rule,
  which rejects every Homebrew install. The host agent, the operator's shell
  and the runner's own direct `git` calls (`helpers/read_only.py`,
  `helpers/mutation.py`, `gates/active_path_guard/`) already run these
  binaries from the ambient PATH with no check. The relink race tests keep
  this protection for Docker and both hosts, and pin the foreign-writable and
  shared-writable forms for `git` and `gh`.
- **Directory swaps.** Non-host PATH directories were never checked for
  ownership (`test_other_cli_path_directory_stays_outside_the_directory_rule`).
  A writer to `/opt/homebrew/bin` (the operator, or the `admin` group on a
  default install) can swap names there. #1355 does not change this.
- **ACLs.** The rule reads mode bits, not ACLs. An ACL that grants another
  user write on an operator-owned file is not seen. The main-branch rule
  never read ACLs either, for files owned by another identity.
- **Helpers outside PATH.** Git's exec-path helpers and shared libraries are
  not PATH entries, so the probe does not inspect them for any CLI. For a
  Homebrew Git they are operator-owned. A worktree symlink or hardlink to one
  is not checked, because it is outside the lookup chain. Changing one still
  needs an operator tool to write through that worktree name, and the host
  agent's own Git loads the same files. `gh` is a single Go binary with no
  Homebrew libraries, but it can start Git from its search path.
- **Names outside the worktree.** A hardlink or symlink in a sibling clone or
  in the shared `.git` directory of a linked worktree is not counted. Making
  one needs write access outside the worktree.
- **Indirect worktree alias.** A worktree symlink to a pre-existing external
  alias directory can reach an accepted `git` or `gh` executable or adjacent
  helper through a hardlink or symlink inside that directory. The probe records
  the external directory's inode but does not walk its children, so it accepts
  the install despite that indirect worktree name. This needs an external alias
  directory that already points at the install, created outside the worktree
  by the operator; worktree content alone cannot create it. Writing through
  that alias also needs operator-level access. This is a Low known limit.
- **Cost.** Each `git` or `gh` lookup that meets an operator-owned file walks
  the worktree once. On the build machine a `gh` lookup took about 0.8 s,
  with a 0.2 s walk of a 3,300-file clone and a 1,286-entry Homebrew
  directory. The result is not cached across probes, so it never outlives the
  check it supports.
- **Fail-closed false negatives.** An unreadable worktree directory, or one
  that changes during the walk, drops operator directories for `git` and
  `gh`. So does a worktree link to any file a PATH directory serves: a
  virtual environment inside the worktree built from Homebrew Python links to
  the same file as `/opt/homebrew/bin/python3`, so `/opt/homebrew/bin` is
  dropped and `gh` there stops at `tool_unavailable`. Each case fails closed
  and names no trusted path.
- Whether the Claude Code and Codex sandboxes let sandboxed code hardlink a
  file outside their writable roots into the worktree was not confirmed. If
  they do, the same trick reaches any operator-owned file (shell profiles,
  Git config), so the probe cannot be the boundary for it.
