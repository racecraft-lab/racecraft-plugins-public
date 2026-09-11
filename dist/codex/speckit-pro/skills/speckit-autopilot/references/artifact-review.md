# Artifact Review Handoff

This is the shared Claude/Codex plan-stage delivery contract. The parent owns
preview delivery; artifact-author still owns generation. Publication, generation,
rendered delivery, human approval, and UAT are separate facts.

## Durable record

After validating generation and before the boundary commit, write one top-level
`## Artifact Review Handoff` section with one `json` fence in the workflow file.
It is the sole store: no state-file mirror and no second copy of the `Draft PR`
identity. The scaffold does not write an empty placeholder. Use this exact shape:

```json
{
  "schema_version": "1.0",
  "feature_dir": "specs/<feature>",
  "input_hashes": {
    "specs/<feature>/spec.md": "<sha256>",
    "specs/<feature>/plan.md": "<sha256>",
    "specs/<feature>/tasks.md": "<sha256>",
    "docs/ai/specs/.process/<SPEC-ID>-design-concept.md": null
  },
  "manifest_sha256": "<sha256 of the author-used gallery manifest>",
  "template_hashes": {"implementation-plan": "<sha256>"},
  "generation_error": null,
  "pages": [{
    "id": "implementation-plan",
    "generation": "generated",
    "path": "specs/<feature>/artifacts/implementation-plan.html",
    "sha256": "<sha256 of the validated final file>",
    "expected_title": "<actual page title>",
    "expected_content": "<feature-specific body passage distinct from the title>",
    "preview": {"status": "pending", "blocker": "Not observed yet", "observation": null}
  }]
}
```

Expand `pages` to the complete selected outcome list, including always-selected
entries. A gap has only `id`, `generation: "gap"`, and `reason`; it has no
preview. Every selected ID has a `template_hashes` entry; `null` means that
template was absent, never that its hash was not checked. A whole-set author
failure has empty `pages` and `template_hashes` and a nonempty `generation_error`.
Keep planned/missing-template gaps separate from preview failures.

Compute hashes from bytes; never invent receipts. Include the design-concept
path supplied to the author even when absent (`null`), so its later creation
invalidates reuse. Omit that entry only when no design-concept input was supplied.
Do not fingerprint workflow bookkeeping or output evidence as generation inputs.
Record project paths relative to canonical `WORKFLOW_ROOT`; gallery hashes refer
to the active runner's shipped gallery, which must be the one the author used.
Derive expected content from the actual validated page and check it against the
feature's planning record. A title repeated as body content is insufficient.

Run `resolve-autopilot-stage` to validate the record. Its optional
`artifact_review` result reports `status`, `resume_action`, `reuse_artifacts`,
counts, per-page dispositions, and generation gaps. The existing phase-coverage
validator gates malformed evidence through `artifact_review_errors`. Neither
helper opens a browser or proves that an observation really occurred: the
parent must retain the actual rendered observation referenced by the record.

## Delivery after publication

Only after the draft PR identity bookkeeping commit and push succeed:

1. Revalidate the canonical workflow binding and resolve every artifact beneath
   its feature's `artifacts/` directory. Determine the current task from the
   runtime. Keep that task as the destination; never silently open in another
   task or infer task identity from a similarly named worktree. An unresolved
   binding or destination leaves delivery pending with its blocker.
2. Discover available preview **and observation** capabilities using the shared
   capability-discovery directive. Prefer supported native HTML preview when it
   can be observed. A browser preview must use an initially permitted local route
   and the installed browser capability's current instructions. Do not assume
   that agent-driven `file://` navigation is permitted. If a local server is the
   selected permitted route, serve only the artifact directory on loopback and
   keep it running while its review tabs are needed.
3. Open each generated page and inspect its rendered state. Match the expected
   title **and feature-specific rendered body content** to that page. Keep one
   review surface per page available; do not close successful previews. File
   existence, HTTP success, a tab URL, generic open success, and `queued` are
   never rendered evidence. Use the observer's bounded wait when needed; an
   inconclusive observation ends this attempt as pending, not an endless poll.
4. After each page, persist its disposition in the workflow file. `verified`
   requires `blocker: null` and this observation object:

   ```json
   {"kind":"rendered","title":"<observed title>","body_text":"<observed visible body text>","route":"<selected preview route>","reference":"<actual observation locator>","observed_at":"<ISO-8601 time with timezone>"}
   ```

   Capture visible body text, not HTML source, hidden DOM data, or the document
   title alone. Wrong, blank, error, or title-only pages stay `pending`. Their
   rendered observation may be retained with a precise blocker. Use
   `unavailable` when no usable preview/observer exists and `denied` for a policy
   denial. Both remain unverified. Other unverified states also require a
   nonempty blocker; an open request alone has `observation: null`.
5. A denial stops that route. Do not change permissions, proxies, origins, or
   tools to circumvent it. On resume, retain the denial unless new authorization
   evidence exists. Missing capabilities may be rediscovered; absence does not
   establish denial. Successful files, previews, and the draft PR remain intact.
6. Validate the updated record, then commit and push the workflow file alone
   using a conventional `chore` message. A nothing-to-commit result is a no-op.
   If persistence fails, report exactly which evidence remained local or
   uncommitted; do not claim the handoff record reached the remote.

## Resume and reporting

Default resume returns to the plan terminal step while recorded preview delivery
is unfinished and implementation has not started. An explicit `--stage implement`
or `--stage full` still wins; print the unresolved preview warning and preserve
all existing gates. `planning_complete` continues to describe planning phases,
not preview delivery. Do not rerun completed phases or G6.5 solely for previews.

| `resume_action` | Parent action at the terminal step |
| --- | --- |
| `preview` | Reuse validated outcomes and files. Bypass author dispatch and its current-run cleanup. Corroborate the existing PR and verify the artifact/identity commits reached its branch; skip already-completed publication steps and continue delivery. |
| `generate` | Inputs or file bytes changed, a file is missing, or a gap has an unexpected final file. Re-enter generation validation and refresh through the existing protocol. Never regenerate merely because a preview is pending. |
| `reconcile` | A legacy active plan draft lacks a record. Recover the complete generation outcomes from durable receipts; re-read files against the existing generation checks and current planning inputs. If receipts are unavailable, establish that evidence by reviewing the complete selected set on disk. Record verified generation outcomes or precise gaps before publication recovery; do not delete or regenerate valid pages just to obtain a preview record. |
| `none` | No preview work is outstanding in this record. Preserve review surfaces; absence of a record alone never asserts delivery. |

The normal PR identity checks still apply, including closed/missing/mismatched
identities and interrupted pushes. Repair only outstanding publication work; do
not recreate or unnecessarily refresh a valid PR for a preview retry. Persisted
page hashes and input fingerprints permit reuse after interruption. A changed
page invalidates its own preview evidence; changed generation inputs invalidate
all affected evidence. A published gap still stays a generation gap.

Absent records are legal in legacy/archived workflows. A recorded plan-stage
draft whose implementation has not begun is reported `unrecorded` and routed to
reconciliation; already-started implementation is never routed backward.

The stop report carries the PR link, generation gaps, verified/generated preview
counts, each outstanding page's disposition and exact blocker, and direct local
file links with canonical absolute paths for manual review. CLI/headless runs
report unavailability rather than success. Zero generated pages means
`not_applicable` for previews, never successful artifact generation. Only all
generated pages with current rendered evidence justify verified preview delivery.
Human approval and UAT completion require their own evidence.

## Documentation boundary

[Work with files](https://learn.chatgpt.com/docs/artifacts-viewer) makes HTML
preview availability surface-dependent. The [browser preview workflow](https://learn.chatgpt.com/docs/browser#preview-a-page)
requires inspecting rendered state. [Browser permissions](https://learn.chatgpt.com/docs/config-file/config-reference#requirementstoml)
separate user-operated `in_app_browser` from agent-operated `browser_use`.
These sources do not define a queued request as delivery. The record format,
resume rules, and verification criteria above are SpecKit design choices.
