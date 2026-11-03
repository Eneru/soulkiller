## Decision proposed for this experiment

Search the already validated saved evidence directly using literal string search.
This gives a useful source-finding action without an index lifecycle or another
runtime. The baseline is experimental, not the E4 SQLite/dense/hybrid comparison.

Case sensitivity is intentional: preserve exact code-point locations without a
normalized-text mapping. Accents, whitespace and case must match; substring
matches are allowed. There is no query language, regular expression, stemming,
translation or semantic ranking. Explain these limits in CLI help and the guide.
Language choice for generated answers remains undecided.

## Source references and bounded context

Reuse read_saved_evaluation, including the saved metadata for missing rows.
Search successful TXT text and every retained PDF page, including partial PDF
evidence. Never concatenate pages or documents. Reference quotes and outcome
annotations are not search inputs: only actual retained candidate text is searched.

Enumerate non-overlapping occurrences by manifest order, physical page order and
match start. Advance past the full matched expression, never split its code-point
span. Results have source ID/path/hash, format, declared language/author/subject,
optional one-based PDF page, match start/end, excerpt start/end and exact excerpt.
Offsets are zero-based, end-exclusive code points in the saved TXT or PDF page.
Declared labels are metadata, not verified identity or established truth.

Show up to 80 code points before/after each match, preserving exact text and
clipping at unit boundaries. The match and excerpt ranges are separate. One more
match beyond the requested limit proves truncation; do not claim an exact total.
Stable order is for reproducibility, not a confidence or truth ranking.

## Experimental bounds and command semantics

Propose --limit default 3, accepted integer range 1..20, and --query length 1..200
code points with at least one non-whitespace character. Reject invalid arguments
before opening the store. Do not trim an accepted query or interpret shell syntax.
These are small fixture-experiment output guards, not household-PC capacity,
latency targets or production search limits. Maximum excerpt size is 360 code
points per match; existing bounded saved-record validation still applies.

Use --corpus and --run-id like show, plus --json. Connected-container inspection
is allowed: this command makes no network calls and starts no workers.
Expose saved run status, per-document observed outcomes, unavailable/unfinished
rows and known missing PDF pages. Read all rows through existing integrity checks
before searching; corruption must not yield a trusted partial result.
No new files, query logs, caches or record-format migration are needed.
Retain existing source-directory/disjointness requirements; original files are
not reopened. Searching a historical saved run does not implement source deletion
or persona retention semantics.

Reuse terminal-safe text and escaped exact JSON. Exit 0 for complete saved runs,
including zero hits; 1 for incomplete/failure states, missing/corrupt runs; 130 for
saved cancellation; 2 for invalid arguments. Hits may be shown with incomplete
status and a nonzero exit. No-hit text says only no literal passage was found;
it cannot prove the persona does not know the answer.

## Delivery and checks after review

Implement the whole search journey in one small PR, without splitting out new
storage/worker foundations. Keep functions documented and cohesive. Reuse current
Python/editor integration, all-source >=70% executable-line coverage and canonical
Gitleaks/Hadolint/Ruff/mypy/Bandit/audit/CLI/CI gates. No image/editor/workflow
change is anticipated; revisit if implementation needs a new tool.

Tests use independent synthetic sources and exact slicing assertions: TXT/PDF,
French/English, repeated matches, context clipping, ordering/limits, absent and
case/accent-sensitive queries, partial/missing/cancelled evidence, corruption and
terminal controls. Include actual module execution in a new connected container,
saved-input removal and unchanged stored-file hashes. Run canonical checks and
the bounded offline suite. Windows performance and retrieval-quality benchmarks
remain unexecuted; no new numerical quality threshold is proposed.
