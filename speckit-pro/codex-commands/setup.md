# /setup

Prepare a spec from the technical roadmap for autonomous execution.
Creates the worktree, branch, and workflow file — ready for `$speckit-autopilot`.

## Arguments

- `spec_id` (required): The SPEC-ID from your technical roadmap (e.g., SPEC-009)

## Workflow

1. **Find the Technical Roadmap** — search for `*technical*roadmap*` or `docs/ai/*roadmap*.md`.
   If not found, stop: "No technical roadmap found. Ask `$speckit-coach` for help creating one."

2. **Find the Spec** — read the roadmap section for the requested SPEC-ID. Extract: spec name,
   short name (for branch), spec number, tool count/names, priority, dependencies, scope
   description, status. Must be ⏳ Pending.

3. **Create Git Worktree** — never commit to main. All work happens in the worktree:
   ```bash
   git remote -v                                       # detect remote name
   git worktree add .worktrees/<NNN>-<short-name> -b <NNN>-<short-name>
   cd .worktrees/<NNN>-<short-name>
   git push -u <remote> <NNN>-<short-name>
   git rev-parse --abbrev-ref HEAD                     # verify branch
   ```

4. **Copy & Populate Workflow Template** — read the template from
   `skills/speckit-coach/templates/workflow-template.md` (shared asset), write it to
   `.worktrees/<NNN>-<short-name>/docs/ai/specs/SPEC-<ID>-workflow.md`, and replace all
   placeholders (`SPEC_ID`, `SPEC_NAME`, `BRANCH_NAME`, `TOOL_COUNT`, `TOOL_NAMES`).
   Populate phase prompts from the roadmap scope description.

5. **Commit and Verify** — stage, commit, and push from the worktree branch (never main):
   ```bash
   cd .worktrees/<NNN>-<short-name>
   git add docs/ai/specs/SPEC-<ID>-workflow.md
   git commit -m "chore(SPEC-XXX): set up workflow for autopilot"
   git push
   ```

6. **Update Technical Roadmap** — mark the spec as 🔄 In Progress in the worktree copy.
   Commit and push.

## Output

Report the spec name, branch, worktree path, workflow file path, and the command to run next:
`$speckit-autopilot docs/ai/specs/SPEC-<ID>-workflow.md`
