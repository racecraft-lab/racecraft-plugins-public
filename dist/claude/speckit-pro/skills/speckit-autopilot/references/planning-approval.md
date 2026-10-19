# Recorded planning approval helper

Use the installed runner transport with `helper_id=planning-approval` and
`operation=planning-approval`. Both hosts share this interface and record.

Inputs always include repository-relative `feature_dir` and `workflow_file`.
`action=manifest`, `action=verify` and `action=admit` require `mode=read_only`.
`admit` is the implement entry check: it returns `admitted` or refuses with
`planning approval field <name>` for a missing record (`record`), a checkout whose
`origin` does not name the record's repository (`repository`), a changed bundle
(`manifest_digest`), `canary_issued`, `withdrawn_by`, `superseded_by`, a finding
(`findings.<id>`) or changed evidence (`reviewed_evidence`). `resolve-autopilot-stage`
runs it for every implement entry.
`action=record` requires `mode=dry_run` or `apply` and an `approval` object:

- `repository` (the GitHub `owner/name` exactly as spelled in this checkout's
  `origin` URL, without `.git`), `planning_run`, `repair_runs` (list),
  `source_commit` (reviewed commit). Record refuses with `planning approval field
  repository` when `origin` does not name it, the same check `admit` runs.
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
  `finish-plan-stage` writes it: `{}` for a clean plan, and on a strict confidence
  shortfall one `confidence-<criterion>` ID per criterion below the threshold
  (`confidence-composite` when none is), each with an empty request array. It
  keeps recorded entries. An empty array refuses `record` until plan review fills it:
  `plan-review-prompt` in `apply` mode records each finding's active request
  instructions in review order and adds a finding the file did not list. It never
  drops a recorded request unless the review withdraws it, and it refuses two active
  requests with the same instruction. A rerun replaces a withdrawn instruction with
  its replacement.

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
The complete PRS block stays approval-bound, including ordinary PR updates;
only bounded runtime BACKLINKS can be progress. Regenerate and obtain a fresh
approval after changing PRS content.
The spec-index generator encodes contributor-controlled PR fields and backlink
labels as literal text and percent-encodes backlink destinations, preventing
runtime names and PR metadata from introducing Markdown structure or external
links. A complete canonical runtime table header and delimiter form one typed
Implement write. Partial scaffolds and separator column or alignment changes
remain bound; other workflow separators are retained.
URL-shaped and email-shaped metadata is refused rather than auto-linked.
Backlink labels may contain those characters inside their quoted relative links.

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
`apply` and `verify` also return `data.implement_prompt`: `prompt`, the copyable text that
invokes `speckit-autopilot` with `--stage implement` for this workflow, revision and record,
plus `sends=false` and `starts_work=false`. It is text only. Approval never starts implement;
the human pastes the prompt into a session, and the implement entry check runs then.
`dry_run` returns no prompt. A missing or invalid record returns none.
This helper supplies no protected human-presence proof, security consent or
implementation dispatch. The `speckit-plan-review` skill drives the interview that ends in `record`.
