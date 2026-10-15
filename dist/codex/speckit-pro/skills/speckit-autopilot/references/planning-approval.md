# Recorded planning approval helper

Use the installed runner transport with `helper_id=planning-approval` and
`operation=planning-approval`. Both hosts share this interface and record.

Inputs always include repository-relative `feature_dir` and `workflow_file`.
`action=manifest` and `action=verify` require `mode=read_only`.
`action=record` requires `mode=dry_run` or `apply` and an `approval` object:

- `repository`, `planning_run`, `repair_runs` (list), `source_commit` (reviewed commit).
- `canary_issued=false`, `supersedes` (prior record path or null),
  `superseded_by=null`, `withdrawn_by=null`.
- `reviewed_evidence`: nonempty unique file references to the reviewed artifact
  manifest, draft PR/source snapshot, decisions, blocked gates and confidence findings.
- `confirmation`: `reference`, `manifest_digest`, `decision=approve`, `approver`,
  `time` (ISO timestamp with timezone). The referenced JSON holds those same
  fields except `reference`. Keep private transcripts outside public records.
- `findings`: map of every finding ID to `requests` (exact instruction strings),
  `correction`, and `check` with `status=passed`, `manifest_digest`, `reference`.
  The feature's `planning-findings.json` is the authoritative map of IDs to
  request arrays; an empty map represents a clean plan, never a missing file.

The runner inventories feature files, workflow, task dispatch metadata, project
planning configuration and declared formal inputs. It normalizes task completion
and declared workflow execution sections; runtime outputs and approval records
are excluded. New or removed planning files change the digest. Required spec,
plan and tasks must be readable. `data.manifest` states the versioned inventory.

`apply` writes `data.record_path` under the feature's `plan-approvals/` directory;
commit that file with the feature. Existing decisions cannot be overwritten.
`verify` rebuilds the manifest and evidence bindings and refuses a missing,
changed, withdrawn, superseded or canary-issued record. Assurance is `recorded`:
the record does not defend against an agent with the operator's file access.
This helper supplies no protected human-presence proof, security consent or
implementation dispatch. Review orchestration and admission are separate work.
