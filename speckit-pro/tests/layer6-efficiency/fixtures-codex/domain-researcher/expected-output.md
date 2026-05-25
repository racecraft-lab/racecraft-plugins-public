## Answer

The widely adopted convention is that the server returns `next_cursor:
null` (or omits the field entirely) when the current page is the last
page, and may additionally return a `has_more: false` boolean for
explicit clarity. Both forms are documented across major REST API
providers — clients should treat either `null`/missing `next_cursor`
*or* `has_more: false` as the terminal signal.

The recommended canonical references to point readers at are:

- The Stripe API "Pagination" guide, which is the most widely-cited
  cursor-pagination reference in REST API design.
- The Google API Improvement Proposal AIP-158 ("Pagination"), which
  prescribes the equivalent semantics for Google-style APIs.
- The GitHub REST API documentation on "Using pagination in the REST
  API", which documents the same convention for the `Link` header form.

The spec should reference at least one of these (Stripe is the most
operational; AIP-158 is the most formal) so that integrators have a
non-project source of truth for the convention.

## References

- Stripe API documentation — "Pagination":
  Cursor-based pagination spec. Authoritative for the convention that
  the server signals end-of-list by setting `has_more: false`; widely
  cited as a de-facto industry reference.

- Google AIP-158 — "Pagination":
  Google API Improvement Proposal for paginated list methods. Prescribes
  `next_page_token` returning the empty string on the last page, with
  equivalent semantics to `next_cursor: null`.

- GitHub REST API documentation — "Using pagination in the REST API":
  Documents the `Link` header convention for cursor-style pagination
  (`rel="next"` omitted on the final page).

- RFC 5988 — "Web Linking":
  Underpins the `Link` header form used by GitHub-style pagination.
  Useful only if the spec intends to use the `Link` header rather than
  body fields.

## Confidence

high

**Rationale**: The convention is consistent across multiple top-tier API
providers (Stripe, Google, GitHub), each with formal public
documentation. The only variation is the surface — body field
(`next_cursor`/`has_more`) vs. header (`Link`) — and the semantics are
identical. Confidence is high because the question is about an
established external convention, not a novel design choice.
