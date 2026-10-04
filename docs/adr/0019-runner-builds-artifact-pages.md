# The runner builds artifact pages; a model writes only their prose

Status: accepted

Decision ticket: [Artifact pages: cheaper authoring while staying on the plan stage](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1153), part of [Wayfinder: speckit-pro planning performance](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1144).

The HTML review artifacts stay ready when the plan stage ends (the promise is fixed), but the runner now builds them. The runner:
- selects the pages by rule: a module map when Declared File Operations has any `MODIFIED` entry, and a code-approaches page when the research or design concept records alternatives;
- fills every region it can derive from the planning files;
- emits the skeleton and a lifted-text fallback for regions that mix structure and prose;
- validates and publishes each page atomically.

One model dispatch writes only short prose slots for the narrative regions, and may polish the mixed ones. Authoring stays fail-open. When the readiness record shows the host has no preview surface, the run records one "preview unavailable" note instead of spawning a preview observer per page.

The measured cost drove this. The author took 23 minutes (baseline) and 38 minutes (2.40.0 smoke), about a quarter to a third of the plan stage. It wrote whole pages as scripts, about 5 to 9 times more code than visible prose, and re-wrote a validator for every page. Of 25 marked regions, 8 are derivable in code, 10 are a skeleton plus short prose, and 7 need narrative. The model's page selection varied between runs on the same kind of input. Every headless observer returned `unavailable`.

## Considered Options

- **Move pages after the draft PR.** Ruled out: the promise is fixed for this map.
- **Fewer pages only.** Rejected: the author would still write pages as scripts.
- **Move only selection and validation into code.** Rejected: most of the time is in writing pages, not choosing them.
- **Keep one observer per page when headless.** Rejected: the observers add no rendered evidence without a preview surface.

## Consequences

- The 2.40.0 rule that every generated page gets its own brokered observation (#1139) applies only when the host has a preview surface.
- A lifted-text fallback reads worse than condensed prose. The narrative dispatch may polish it, but a page with fallbacks is still a complete page.
- The author agent shrinks to a narrative writer, and the artifact-gallery templates gain short text slots that the runner wraps in markup.
