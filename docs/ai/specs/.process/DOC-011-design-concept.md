---
topic: "DOC-011 GitHub Pages build-and-deploy pipeline"
slug: "DOC-011-design-concept"
date: "2026-06-22"
mode: "setup"
spec_id: "DOC-011"
source_input:
  type: "file"
  ref: "docs/ai/specs/interactive-documentation-technical-roadmap.md"
question_count: 9
stop_reason: "natural"
---

# Design Concept: DOC-011 GitHub Pages Build-and-Deploy Pipeline

> **Source:** docs/ai/specs/interactive-documentation-technical-roadmap.md
> **Date:** 2026-06-22
> **Questions asked:** 9
> **Stop reason:** natural

## Goals

- Deliver DOC-011 as a deploy-ready GitHub Pages slice: deploy workflow, staging noindex guard, and runbook notes.
- Deploy continuously from `main` and allow manual maintainer dispatch.
- Use GitHub Actions Pages deployment with least-privilege permissions, a `github-pages` environment, and deploy concurrency.
- Gate Pages deployment on the existing `pnpm --dir docs-site validate` path.
- Protect the staging github.io URL from search indexing with both `robots.txt` disallow and a global noindex/nofollow meta guard.
- Create the missing CI/CD verification runbook that the roadmap and `CLAUDE.md` reference, then add the Pages deployment setting and rollback notes there.
- Keep DOC-011 as one vertical slice. The estimator returned `{"estimated_loc":245,"suggested_slices":1,"status":"ok"}` for four user stories, about six files/surfaces, ten functional requirements, and modify-mode work.

## Non-goals

- Custom domain, DNS, base-path migration, or removal of the noindex guard - owned by DOC-012 (Q4).
- Branding, SEO metadata, social cards, analytics, Lighthouse CI, or launch hygiene - owned by DOC-013, DOC-014, DOC-017, and DOC-018 (Q1, Q4).
- Automating GitHub repository Pages settings through API or CLI - rejected in Q3.
- Live plugin install tests or plugin behavior changes - not part of DOC-011 (Q5).
- Narrow path filtering that risks missing docs-impacting source changes - rejected by the user's Q6 answer.
- Splitting deploy workflow and runbook work into separate specs - rejected in Q9.

## Design Tree (Q&A log)

### Q1. For DOC-011, what should the scaffold treat as the primary deliverable?

**Branch:** Scope envelope

**Recommended answer:** Workflow plus guard (Recommended)
> The roadmap says DOC-011 should make docs reachable at a live GitHub Pages URL while preserving the public-exposure policy. Keeping deploy workflow, noindex guard, and runbook notes together gives one coherent staging capability.

**Alternatives offered:**
- Workflow only: Keep DOC-011 narrower, but defer noindex/runbook work and risk an unsafe public staging URL.
- Docs-only runbook: Avoid CI changes for now, but DOC-011 would not actually make the docs reachable.

**User's answer:** Workflow plus guard (Recommended)

---

### Q2. How should the GitHub Pages deploy workflow be triggered for DOC-011?

**Branch:** Deployment trigger

**Recommended answer:** Main paths plus manual (Recommended)
> Continuous deploy from `main` matches the roadmap goal, and `workflow_dispatch` gives maintainers an explicit recovery/retry path. Path filtering keeps the workflow from running on irrelevant changes unless later narrowed or broadened by Q6.

**Alternatives offered:**
- Every main push: Simpler YAML, but deploys even on unrelated plugin-only changes.
- Manual only: Lower automation risk, but does not give continuous docs deployment.

**User's answer:** Main paths plus manual (Recommended)

---

### Q3. How should DOC-011 handle GitHub Pages enablement?

**Branch:** Repository settings boundary

**Recommended answer:** Workflow plus runbook (Recommended)
> GitHub Pages source/environment settings may require repository admin permission. The spec should implement the workflow and document the one-time "source = GitHub Actions" setting rather than trying to mutate repo settings during implementation.

**Alternatives offered:**
- Automate repo setting: Try to configure Pages via GitHub API/CLI, but this may require admin permissions and adds a brittle setup dependency.
- Assume enabled: Simpler spec, but leaves a hidden blocker if Pages source is not set to GitHub Actions.

**User's answer:** Workflow plus runbook (Recommended)

---

### Q4. What should DOC-011 require for staging-site search visibility?

**Branch:** Public exposure and safety

**Recommended answer:** Global noindex guard (Recommended)
> The roadmap explicitly says the staging github.io URL is previewable but not indexed or discoverable until DOC-012. A global Starlight head meta guard plus `robots.txt` disallow makes that launch boundary visible and testable.

**Alternatives offered:**
- Robots only: Less config churn, but weaker because page-level indexing directives are absent.
- No guard: Simpler deploy, but violates the roadmap's public-exposure policy.

**User's answer:** Global noindex guard (Recommended)

---

### Q5. What validation should gate the deploy job before uploading the Pages artifact?

**Branch:** Deployment validation

**Recommended answer:** Existing docs validate (Recommended)
> `docs-site/package.json` already defines `validate` as the complete local docs quality path: reference freshness, Astro checks/build, links, safe aids, quality checks, and Playwright smoke. Reusing it keeps DOC-011 simple and consistent with DOC-010.

**Alternatives offered:**
- Build only: Faster deploy job, but skips DOC-010's docs quality and smoke gates.
- Reference and build: Middle ground, but still omits accessibility/quality/smoke coverage already wired into validation.

**User's answer:** Existing docs validate (Recommended)

---

### Q6. Which changed paths should trigger the DOC-011 deploy workflow on `main`?

**Branch:** Trigger path filter

**Recommended answer:** Docs inputs only (Recommended)
> A tight filter around `docs-site/**` plus generated-reference source inputs avoids unrelated plugin-only deploys while still catching docs changes. This was the initial recommendation, but the user chose a broader trigger to reduce missed-deploy risk.

**Alternatives offered:**
- Docs-site only: Cleanest filter, but release payload/source changes that alter generated reference pages may not deploy docs.
- Broad repo paths: Harder to miss docs changes, but may deploy on unrelated plugin implementation work.

**User's answer:** Broad repo paths

**Notes:** Plan should define the exact broad filter. It should still avoid obviously irrelevant paths if safe, but the chosen bias is "do not miss docs-impacting changes" over "minimize deploy frequency."

---

### Q7. How should DOC-011 handle the missing CI/CD verification runbook that the roadmap and CLAUDE.md reference?

**Branch:** Runbook and recovery evidence

**Recommended answer:** Create runbook now (Recommended)
> The roadmap names `docs/ai/specs/cicd-release-pipeline-verification.md`, and `CLAUDE.md` already references that path, but the file is absent. Creating the runbook in DOC-011 turns a stale pointer into durable deployment evidence and a place for Pages setup/recovery steps.

**Alternatives offered:**
- CLAUDE note only: Keep the slice smaller, but leave the referenced runbook path missing.
- Defer runbook: Treat runbook creation as future work, but DOC-011 loses an explicit setup/rollback record.

**User's answer:** Create runbook now (Recommended)

---

### Q8. What permissions and concurrency model should DOC-011 require for `deploy-docs.yml`?

**Branch:** Workflow security and reliability

**Recommended answer:** Least privilege deploy (Recommended)
> GitHub Pages deploys need `contents: read`, `pages: write`, and `id-token: write`, plus a `github-pages` environment. A Pages concurrency group prevents overlapping deploys when multiple main pushes land quickly.

**Alternatives offered:**
- Broad write token: Simpler to troubleshoot but grants more token scope than Pages deploy needs.
- No concurrency: Less YAML, but overlapping deploys can race when multiple main pushes land quickly.

**User's answer:** Least privilege deploy (Recommended)

---

### Q9. Should DOC-011 stay as one scaffolded vertical slice?

**Branch:** Slice sizing

**Recommended answer:** One slice (Recommended)
> The forward estimator returned `ok`, and the work is a coherent vertical slice: deploy workflow, validation gate, noindex guard, and runbook evidence all support one observable capability.

**Alternatives offered:**
- Split deploy/docs: Separates workflow from documentation, but leaves noindex/runbook sequencing more fragile.
- Defer decision: Record split sizing as open and let Clarify/Plan decide before implementation.

**User's answer:** One slice (Recommended)

## Open Questions

- **What:** Exact broad `paths:` filter for `deploy-docs.yml`.
  **Why deferred:** The user chose broad repo paths in Q6; Plan should translate that into maintainable YAML after reviewing which source paths can affect generated reference pages and docs output.
  **Suggested next step:** Start from `docs-site/**`, docs content/source files, generated-reference inputs, plugin manifests, release/payload sync sources, and workflow files. Keep unrelated archive/test fixture paths out if that does not risk missed docs deploys.
- **What:** Whether `pnpm --dir docs-site validate` in Pages deploy should install Playwright browsers explicitly or reuse an existing CI-compatible setup pattern.
  **Why deferred:** The existing validation command includes Playwright smoke; Plan should inspect current CI behavior and choose the smallest stable setup.
  **Suggested next step:** Prefer a clear `pnpm --dir docs-site install --frozen-lockfile` plus the minimum browser install command required for `validate:smoke:preview`.
- **What:** Exact wording for the one-time Pages repository setting.
  **Why deferred:** It depends on current GitHub UI/API labels at implementation time.
  **Suggested next step:** Document "Settings -> Pages -> Source: GitHub Actions" and the `github-pages` environment expectation, then verify against GitHub's current UI during implementation if needed.

## Recommended Next Step

Continue setup by generating `docs/ai/specs/.process/DOC-011-workflow.md`, writing `specs/doc-011-github-pages-build-and-deploy-pipeline/SPEC-MOC.md`, committing the scaffold artifacts, and then running:

```text
$speckit-autopilot docs/ai/specs/.process/DOC-011-workflow.md
```

This design concept is the source of truth for scoping decisions captured during setup. Any drift in downstream artifacts (`spec.md`, `plan.md`, `tasks.md`) from the decisions above is a defect unless there is an explicit revision note.
