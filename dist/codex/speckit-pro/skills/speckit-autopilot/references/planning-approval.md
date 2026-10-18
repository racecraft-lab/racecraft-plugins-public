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
and the typed progress fields in the [Implement write contract](workflow-file-protocol.md#implement-write-contract);
runtime outputs and approval records are excluded. New or removed planning files
change the digest. Required spec, plan and tasks must be readable.
`data.manifest` states the versioned inventory.

The progress table in `helpers/planning_approval.py` owns the allowed regions and
value shapes. Status spellings come from `workflow_stage.py`, shared with the
readers. Known progress values, measured counts and execution-evidence references
preserve the revision; arbitrary prose remains bound even inside a status cell,
checklist, lesson, summary, or generated navigation block. A writer appends typed
summaries while retaining existing planning notes. Success Criteria text is
planning and its tick state is progress. Other workflow planning-choice
checkboxes bind checked/unchecked state; `x` and `X` are equivalent spellings.
Fences remain literal planning content. Canonical SPEC-MOC navigation is compared
with its generator's output rather than discarded as a whole region.

Older projection digests may require a new approval after this change. Do not
rewrite a prior approval record to adopt the new digest.

Prepare reviewed evidence and create the confirmation path (for example,
`artifacts/confirmation.json` with placeholder JSON) before the final manifest.
Regenerate feature navigation, obtain the manifest digest, then fill that same
confirmation path with the decision. After adding another evidence or
confirmation file, regenerate navigation and check the manifest again.
Recording in `dry_run` or `apply` requires canonical generated navigation;
stale or edited generated maps are refused with a regeneration instruction.
Manifests continue to bind their noncanonical bytes.

`apply` writes `data.record_path` under the feature's `plan-approvals/` directory;
commit that file with the feature. Existing decisions cannot be overwritten.
When the feature map is already canonical, the same write refreshes its generated
backlinks to include the new record. Commit the refreshed map with the record.
`dry_run` and a preflight refusal change neither file.
`verify` rebuilds the manifest and evidence bindings and refuses a missing,
changed, withdrawn, superseded or canary-issued record. Assurance is `recorded`:
the record does not defend against an agent with the operator's file access.
This helper supplies no protected human-presence proof, security consent or
implementation dispatch. Review orchestration and admission are separate work.
