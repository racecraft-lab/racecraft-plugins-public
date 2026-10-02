# Simple remediation choices for plan review

Date: 2026-10-02. Scope: the throwaway review prototype. This records design evidence, not a shipped contract or accessibility certification.

## Operator requirement

Make reviewing plan issues and constructing the repair handoff as simple as possible. Explain each issue and its impact quickly. Offer a recommended remedy, a meaningful alternative and space for the operator's own remedy. Choosing a remedy must not claim that the issue is fixed.

## Accessible interaction guidance

| Design rule | Primary evidence | Application |
| --- | --- | --- |
| Group related choices under one question. | [W3C: grouping form controls](https://www.w3.org/WAI/tutorials/forms/grouping/) | One native fieldset and legend per issue; associated labels and separate radio-group names. |
| Offer one mutually exclusive answer and clear hint text. | [GOV.UK: radios](https://design-system.service.gov.uk/components/radios/) | Mark the recommendation in its label, explain the tradeoff and leave choices initially unanswered. |
| Reveal only a simple related custom question. | [GOV.UK: conditional radio questions](https://design-system.service.gov.uk/components/radios/#conditionally-revealing-a-related-question), [W3C: on input](https://www.w3.org/WAI/WCAG22/Understanding/on-input.html) | The custom option reveals one labeled textarea. Selection does not submit or navigate. Keep focus on the radio; Tab reaches the revealed field. Hide it from navigation otherwise, but preserve its draft. |
| Explain errors and retain answers. | [GOV.UK: error summary](https://design-system.service.gov.uk/components/error-summary/), [error message](https://design-system.service.gov.uk/components/error-message/) | Keep Build handoff prompt available. Missing choices or custom text produce a focused summary, matching inline errors and links to the affected controls. |
| Give controls comfortable click targets and visible focus. | [W3C: minimum target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum/), [GOV.UK: radios](https://design-system.service.gov.uk/components/radios/) | Large clickable option labels, visible keyboard focus and a Browser check of native radio/textarea navigation. The target-size criterion has exceptions; measurements alone do not establish conformance. |
| Communicate what happened and what happens next. | [W3C: status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages/) | Prompt ready, copy/paste destination and an edit-choices action. Avoid duplicate announcements when focus moves to the new heading. |

GOV.UK documents accessibility concerns with conditional questions. Using the pattern alone is insufficient proof. The local checks cover markup, keyboard interaction and layout; full assistive-technology evaluation remains human work.

The copy button must await the Clipboard API result before reporting success. [MDN: Clipboard.writeText](https://developer.mozilla.org/en-US/docs/Web/API/Clipboard/writeText) documents its resolved Promise, secure-context requirement and possible permission rejection. On failure or unavailable access, select the prompt and explain how to copy it with the keyboard. Tavily extraction retrieved this API guidance and GOV.UK radio guidance during the refinement.

## Repository-grounded options

[ADR 0012](../../adr/0012-blocked-for-uat.md) requires one runner-owned blocked-work record, consistent rendering, retained original history and explicit authority for a linked repair run. The alternative remedies below change the implementation approach or timing while preserving that contract.

| Issue | Option | Planning instruction and required check |
| --- | --- | --- |
| Independent document lists | Recommended: use one shared snapshot. | Both renderers consume the same frozen record revision. Preserve every entry, status, evidence reference, ordering and count. Check both input contracts and the absence of independent lists. |
| Independent document lists | Alternative: generate one shared report. | Generate one immutable report from a specified canonical record revision and feed it to both renderers. Treat it as a derived view, prohibit independent edits, and check source freshness, preserved content and both renderer contracts. |
| Resume clears history | Recommended: prepare repairs at handoff. | Preserve blocks, spent attempts and evidence. Prepare only an inert repair-request draft linked to original entries at handoff. Check preservation, linkage and separate authorization before any new run. |
| Resume clears history | Alternative: prepare repairs when requested. | Preserve the same history. Add a separate reviewer request before preparing the inert linked repair draft. Check that ordinary resume does not retry blocked work or automatically start a repair. |

The options are proposals, not newly accepted repository decisions. A derived report must never become a second authority. The repair timing choices must never weaken preservation or authorization.

## Simulation and verification boundary

The request must preserve each selected option and exact free text. The revised example plan/tasks/contracts and planning report must bind to the selected built-in strategy. A custom instruction cannot receive a canned checked result, even if it resembles a catalog option. A matching real response and check evidence remain necessary.

All displayed defects, replies and planning results are fictional samples grounded in a real repository decision. Building or selecting a prompt sends nothing, starts no work and creates no protected approval. Runtime behavior, human comprehension, formal ASD-STE100 conformance and full accessibility conformance are not established by this research.

## Local verification

The implemented form starts with six unchecked options in two named native groups. The Browser walkthrough verified focused error summaries and their links, arrow-key radio selection, focus remaining on the custom radio before Tab reaches its textarea, retained free text after changing options, and preserved choices after editing. Repair and implementation clipboard contents matched their read-only prompts exactly. Both themes rendered, and narrow-screen controls remained usable without horizontal page overflow.

The model/DOM smoke exercised all four built-in combinations, distinct returned strategies and matched planning checks. Custom text, omitted requested remedies and pending new requests cannot reuse earlier passing checks. Independent audit reproduced and verified fixes for a secondary action that replaced alternatives and a prepared-request approval bypass. No human comprehension or assistive-technology certification is claimed.
