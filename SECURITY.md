# Security Policy

This repository publishes Claude Code and Codex plugins that other people
install and run. A defect here executes on someone else's machine with their
credentials, so treat plugin content as a distribution channel, not just
documentation.

## Reporting a vulnerability

Use GitHub's private reporting: open the **Security** tab of this repository and
choose **Report a vulnerability**. That opens a private advisory visible only to
the maintainers.

If private advisories are unavailable to you, contact a maintainer through their
GitHub profile and ask for a private channel. Do not include vulnerability
details in that first message.

Do not open a public issue, and do not describe the problem in a PR title,
branch name, or commit message before a fix ships.

Include the affected path, what an attacker or a misbehaving agent could reach,
and steps to reproduce. A proof-of-concept diff helps but is not required.

Expect an acknowledgement within seven days. There is no bug bounty for this
repository.

## Supported versions

Only the latest published version of each plugin receives security fixes. Fixes
ship forward through the normal release path rather than as backports.

## What counts as a security issue here

The shipped surface is largely instructions, so the relevant failure modes are
not the usual application-security list:

- **Instructions that cause data exfiltration.** A skill or agent that directs a
  consumer's agent to send file contents, credentials, or workspace data to an
  external endpoint.
- **Over-broad tool grants.** Agent `tools` fields are explicit allowlists.
  Granting more than the agent's job requires — particularly write or execute
  tools — is a finding.
- **Prompt injection reaching a write or execute tool.** Skills read untrusted
  content from the web, issues, and files. Any path where that content can
  steer a tool call is in scope.
- **Command injection in repository tooling.** Unquoted interpolation in shell,
  or untrusted input reaching a subprocess in Python validation.
- **CI supply chain.** An unpinned third-party action, a workflow that runs
  untrusted PR content with elevated permissions, or a secret exposed to a fork
  PR.
- **Marketplace integrity.** A manifest change that would cause consumers to
  install content other than what this repository reviewed.

## Scope

In scope: `speckit-pro/`, `scripts/`, `tests/`, `docs-site/` source, and
`.github/workflows/`.

Out of scope: third-party MCP servers and services the plugins call, the
upstream SpecKit CLI, vendored upstream content, and archived spec artifacts
under `specs/`. Report those to their respective maintainers.

## Disclosure

Report privately, and give the maintainers a chance to ship a fix before
publishing. Once a fix is released, credit is offered to the reporter unless
anonymity is requested.
