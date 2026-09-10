# Optional stack manager

Keep packet-owned titles, bodies, release-readiness checks and PR creation.
Select a manager before stack mutations, using the existing runner helper
`detect-stack-manager-plan` in `dry_run` mode. Selection does not require formal
methods and never installs tools or executes a PR mutation.

Supply `repo_root: WORKFLOW_ROOT`, `repository: owner/repo`, an explicit `remote`,
and the available gh-stack skill's actual `SKILL.md` path as `skill_path`. Do not
search credentials or substitute a skill merely mentioned in repository prose.
Use `preference: explicit-gh` when the operator chose current PR management;
otherwise use `auto`. Include `previous_decision` whenever an emission decision
already exists, using its process-evidence path relative to WORKFLOW_ROOT.

The `topology` array comes from the owned layer/marker plan, in bottom-to-top
order. Each row has `review_order`, `slice_id`, `branch`, `base_branch`, and,
when created, its verified full `pr_url`. Example:

```json
{
  "schema_version": "1.0",
  "helper_id": "detect-stack-manager-plan",
  "operation": "detect-stack-manager-plan",
  "mode": "dry_run",
  "inputs": {
    "repo_root": "<WORKFLOW_ROOT>",
    "repository": "owner/repo",
    "remote": "origin",
    "skill_path": "<installed-gh-stack>/SKILL.md",
    "preference": "auto",
    "topology": [
      {"review_order": 1, "slice_id": "foundation", "branch": "feature/foundation", "base_branch": "main"},
      {"review_order": 2, "slice_id": "behavior", "branch": "feature/behavior", "base_branch": "feature/foundation"}
    ]
  }
}
```

The qualified profile is gh-stack 0.1.1 on GitHub.com, a non-fork repository
with push permission, a successful read-only Stacks API response, and a linear
chain of owned local branches. Existing PRs must match repository, open state,
head commit, head branch and base branch. Other versions, missing CLI or skill,
unsupported repositories, and incompatible topology select `explicit-gh` before
mutation. Keep the returned reason; never relabel unavailable evidence as support.

Persist `data.decision` using the existing
`stack-manager-decision.schema.json`, and reference that path in the emission
state, command log, workflow and PRS record. It contains capability evidence,
skill path/hash, owned branch topology, planned commands and mutation boundary.
The helper is read-only: the parent owns those normal bookkeeping writes.

For either manager, create or refresh each PR using its validated packet and
exact final title, preserving `--title`, `--body-file`, `--base` and `--head`.
Look up an existing PR by its owned head/base before creating one. Persist the
actual PR URL/number and head SHA immediately. Rerun detection with those URLs
after all packet validations pass. A selected `gh-stack` decision then returns
one documented `gh stack link --remote ... --base ... <full-PR-URL>...` command.
It uses existing PRs only. Do not use bare branch arguments or `--open`.

Before linking, read the installed skill and persist `mutation_boundary.status:
attempted` with the command ID, start time, argv, pre-mutation topology and
validated packet references. Execute the returned command, capture its exit and
bounded output, then read remote PR and stack membership to record the observed
topology. Preserve packet metadata and draft status. A zero command exit without
the expected remote topology is incomplete.

After any attempted or partial mutation, resume through the selected manager.
Detection returns a blocking recovery record, preserving prior PR identities and
observed topology. Use the installed skill and read-only remote evidence to
reconcile the exact outcome before retrying the existing-PR command. Never
automatically switch managers, recreate PRs, or erase the attempted boundary.
Only a reconciled successful result may supersede the blocked event. Subsequent
supported stack operations follow the installed skill; this helper does not
promote the separate deferred `restack` or live emission executors.

Sources: [existing-PR link contract](https://github.com/github/gh-stack#gh-stack-link),
[read-only Stacks API](https://github.com/github/gh-stack/blob/2bd699a544a09cb5c45a013d03416e0894b0454e/internal/github/github.go#L488).
