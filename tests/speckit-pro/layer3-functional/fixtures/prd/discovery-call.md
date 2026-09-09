<!-- fixture-kind: deterministic-synthetic-testdata; this is authored setup input, not a real discovery call or live evidence. -->

# Discovery Call: Customer Feedback Operations

This synthetic discovery call is the immutable setup input for the PRD
evaluation. Section labels are stable anchors; statements under “Decided” are
validated input, while “Open” items are deliberately unresolved gaps.

## [FEEDBACK-WIDGET]

**Decided:** Customers can submit a short message from the product and may
optionally include the page they were viewing. The first release should accept
feedback without requiring a screenshot or a rating.

**Open:** The call did not decide whether anonymous submissions are allowed or
what confirmation the customer sees after submitting.

## [MODERATION-QUEUE]

**Decided:** Support staff need a queue for reviewing submissions, with a
status that distinguishes new, in-review, and resolved feedback. Resolved
items remain available for reporting.

**Open:** The call did not decide which staff roles may resolve an item or how
long an unreviewed item may remain before escalation.

## [WEEKLY-DIGEST]

**Decided:** Product and support leads want a weekly email summarizing new and
resolved feedback. The digest should link back to the moderation queue rather
than include full message text.

**Open:** The call did not decide the delivery weekday, recipient management,
or whether an empty digest should be sent.

## [SCOPE-BOUNDARY]

The three candidate features are the customer-feedback widget, the admin
moderation queue, and the weekly digest email. The call did not authorize
implementation choices, vendor selection, or a broader customer-support
platform.
