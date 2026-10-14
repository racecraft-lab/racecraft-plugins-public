# Feature-offer evidence: PR #1329

The readiness record owns evaluation and offer evidence for Claude and Codex.
A Step 6.5 apply attempt naming a supported host retires the prior receipt without deleting its
observations. Retired records have a null `evaluation_id`, so neither the old
digest nor a reconstructed digest can authorize offers. A successful evaluation
has a unique identifier and returns the digest of the bytes actually published.

Step 6.6 requires that digest, rechecks file fingerprints, and conditionally
publishes against the captured record inode, content, mode and parent identity.
The checked reader also rechecks file inputs. A publication that reached disk
but cannot be confirmed returns `expected_failure` with `writes_state: true`;
it supplies no successful coverage result.

Scaffold Step 8 flips the SPEC row in the roadmap's Progress Tracking table to In
Progress after Step 6.5 fingerprinted that roadmap. File fingerprints therefore
ignore the Status column of that table, and every other roadmap edit still
changes the digest and fails the checked reader closed.

## Known limits

- Offer fingerprint rechecks use G0's 1 MiB file-read bound, while the initial
  evaluation fingerprints files without that bound. An observation naming a
  larger file can be recorded but cannot authorize an offer. It fails closed
  and reports a coverage gap, matching G0's existing stale-input behavior.
  No current Step 6.5 input reaches this size; reaching the limit requires an
  observation naming a readiness input over 1 MiB.
- File and runtime evidence is a snapshot. Runtime observations belong to the
  successful Step 6.5 evaluation; they are not continuous health monitoring.
  Later runtime changes require another evaluation. This is outside the
  changed helper's observation boundary, rather than an implicit reuse of an
  earlier evaluation after a failed apply attempt.
- A consumer that copies raw JSON bypasses `feature_offers()` freshness
  checks. The repository canary integration test uses the checked reader;
  deployment of an external canary fixture remains separate work. A mutation
  after the last snapshot cannot be detected by an earlier raw copy. This is
  outside the helper/reader contract; raw file presence is not fresh evidence.
- The existing conditional atomic writer preserves a competing entry in a
  recovery file if both its checked swap and rollback fail. The helper reports
  failure, and recovery requires inspecting that preserved entry. This double
  I/O-fault case is an existing primitive limit. The response reports failure;
  the canonical record may still read as offered for the evaluation current
  at snapshot time. This is not a successful update of the competing evaluation
  or deletion of its observations.
- Filesystems without a checked atomic exchange refuse offer updates and
  retirement of prior evidence. If retirement cannot be published, the helper
  stops before evaluating new inputs and issues no fresh receipt. Older
  observations may remain on disk; a failed response is not current evidence.
  The helper reports the coverage gap and does not fall back to an unchecked
  replacement. Resolve the write prerequisite before retrying. Linux VM
  results do not establish native macOS coverage.
- Interactive question tools and a live scaffold session were not exercised.
  The tests execute the documented request and both rendered host views.

These limits do not waive current-head review or merge gates.
