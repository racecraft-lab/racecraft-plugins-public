# Simplified language for plan review

Research date: 2026-10-02. Retrieval: Tavily search and full-document extraction from primary publishers. The official ASD PDF extraction succeeded with no failed results. Page references below are the standard’s printed page labels, not PDF viewer numbers.

## Verified STE evidence

ASD-STE100 Issue 9 is dated 2025-01-15. It governs technical documentation through writing rules and a dictionary. Issue 9 replaces the earlier term “technical name” with “technical noun.” [Official Issue 9 standard](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf), Highlights HI-2; introduction i.

| Rules | Verified requirement, paraphrased | Printed pages |
| --- | --- | --- |
| 1.1–1.4 | Check vocabulary permission, grammatical role, intended meaning, and permitted forms. | 1-1-2–1-1-4 |
| 1.5; 1.8–1.11 | Domain nouns need an applicable category; use approved, short, consistent terminology without jargon. | 1-1-5; 1-1-11–1-1-13 |
| 3.6 | Prefer active voice; descriptive passive voice has a limited exception for an unknown actor. | 1-3-5 |
| 5.1–5.3 | Procedures: at most 20 words per sentence; one instruction except simultaneous actions; command form. | 1-5-1–1-5-3 |
| 5.4 | Put a necessary condition before its instruction. | 1-5-4 |
| 6.3 | Descriptions: at most 25 words per sentence. | 1-6-4 |
| 8.6; 9.4 | Special counting rules apply; maintain consistent wording. | 1-8-5–1-8-8; 1-9-8 |

All rows refer to the [official standard](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf). A basic whitespace counter is not its complete counting method.

The dictionary does not generally approve the verb *approve* (2-1-A17), verb *confirm* (2-1-C16), noun *finding* (2-1-F6), or noun *review* (2-1-R15). Its approved *agent* meaning concerns materials (2-1-A10), not AI workers. This demonstrates why mechanical substitutions can change product meaning. [Issue 9 dictionary](https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf)

## Interface guidance

GOV.UK recommends users’ language, short direct copy, one idea per sentence, important words first, and sentence case. It advises improving an interface that needs lengthy explanations. [Writing for user interfaces](https://www.gov.uk/service-manual/design/writing-for-user-interfaces)

GOV.UK button guidance asks labels to describe their actions and distinguishes continuation from saving. Multiple primary actions make the next step harder to identify. [Button guidance](https://design-system.service.gov.uk/components/button/)

Digital.gov recommends active voice to identify responsibility, direct verbs, short sections, and tense choices that preserve accuracy. It recommends testing early, revising, and testing again; paraphrase and usability testing answer different comprehension questions. [Writing for understanding](https://digital.gov/guides/plain-language/writing), [Test for understanding](https://digital.gov/guides/plain-language/test)

## Implementable rubric

Treat the following as **STE-inspired interface copy**, combined with plain-language guidance:

1. Address the reviewer as “you.” Name the system when it performs an action.
2. Aim for no more than 20 words in an instruction and 25 in an explanation. Count conservatively for copy review; record exceptions.
3. Give one action per instruction. Put its prerequisite first. Keep consequence text beside the choice.
4. Use consistent domain terms: **plan**, **finding**, **decision**, **approval**, **implementation**, and **simulation**. Explain a finding as an issue that needs your decision. These are a proposed project vocabulary, not a verified STE-approved glossary.
5. Use concrete labels: “Read the plan,” “Decide this finding,” “Confirm approval,” and “Start implementation simulation.” Keep simulation wording visible where a modeled action could be mistaken for a real one.
6. Reserve **approval** for the final decision. An accepted finding, reading completion, or navigation action must not imply approval. Approval must not imply implementation has started.
7. Replace system terms in the reviewer view with their consequence: for example, explain an admission failure as why implementation cannot start. Preserve exact codes in optional technical details.
8. Check every replacement against actual behavior. Avoid “saved” when a decision exists only in transient page state. Never change an approval rule to fit simpler wording.

Before acceptance, ask the intended reviewer to paraphrase each decision’s meaning and predict what its button does. Check especially the difference between accepting a finding, confirming approval, and starting implementation. No human comprehension result has been measured by this research.

## Limits

The current prototype has not undergone a complete dictionary, grammar, domain-vocabulary, or word-count audit. This research establishes neither formal STE conformance nor readability certification. Interface adaptation is a design recommendation; the retrieved standard does not validate this specific review UI. Sentence length and agent review do not prove comprehension or valid consent.
