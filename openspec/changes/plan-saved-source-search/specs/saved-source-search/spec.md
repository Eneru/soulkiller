# Search saved source passages

**Status: proposed behavior, pending maintainer review and implementation.**
This is a read-only experimental source-finding step, not a generated answer.

## ADDED Requirements

### Requirement: Search one saved run without side effects

The proposed search command SHALL search only retained extracted text in one
explicitly selected saved synthetic run, using saved metadata and existing strict
integrity checks. It SHALL NOT read original source files, use reference
annotations as evidence, start extraction, write files or make network/model calls.

#### Scenario: Find a saved French phrase
- **WHEN** the operator searches the saved demo for "lampe bleue"
- **THEN** the result quotes retained French PDF evidence and identifies source page 1 without running extraction

#### Scenario: Original files are no longer available
- **WHEN** a saved run is valid and its corpus directory still satisfies existing store checks but the original source files are absent
- **THEN** search still uses the saved evidence without recreating the sources

### Requirement: Exact literal matching with explicit limitations

Matching SHALL use the complete query as a case-sensitive literal code-point
substring, preserving accents and whitespace. It SHALL NOT interpret query syntax
or claim semantic, translated or natural-language-question retrieval.
A query SHALL contain 1..200 code points and at least one non-whitespace character;
invalid queries SHALL fail as usage errors before opening the run.

#### Scenario: Find English evidence across formats
- **WHEN** the operator searches the current saved demo for "paper stars"
- **THEN** the English TXT and PDF passages are both eligible with separate source references

#### Scenario: No matching expression
- **WHEN** the query does not occur literally in retained text
- **THEN** the report says no matching passage was found without inventing an answer or claiming exhaustive knowledge

### Requirement: Resolving quotations and bounded presentation

Each match SHALL retain source ID/path/revision hash, format, declared language,
author/subject labels and an optional one-based PDF page. The match and context
excerpt SHALL have separate zero-based, end-exclusive code-point ranges resolving
exactly in the saved TXT or page text. Context SHALL contain up to 80 code points
on each side. Documents/pages SHALL NOT be joined to fabricate a match.

#### Scenario: Inspect the returned PDF quotation
- **WHEN** the operator slices the saved page text at the reported excerpt and match ranges
- **THEN** the exact displayed excerpt and literal query are reproduced without treating labels as verified identity

### Requirement: Stable limited results with visible coverage

Results SHALL enumerate non-overlapping occurrences in manifest, physical-page
and start-offset order. The default limit SHALL be 3, with accepted integers
1..20. The report SHALL disclose when additional matches exist without claiming
an unmeasured exact total or relevance/truth ranking.
It SHALL expose saved run status, per-document observed outcomes and unavailable,
unfinished or known missing-page coverage, including partial PDFs.

#### Scenario: A partial PDF contains a match
- **WHEN** a retained page matches but other pages are missing
- **THEN** the passage is returned with the partial outcome and known missing-page coverage visible

#### Scenario: More passages exist than requested
- **WHEN** at least one additional match exists beyond the requested limit
- **THEN** output contains no more than the limit and visibly indicates truncation

### Requirement: Safe observable command outcomes

Search SHALL provide terminal-safe readable output and exact escaped JSON.
It SHALL fail on missing/corrupt saved data rather than silently trusting some
rows. A complete run SHALL return exit 0 even with no matches; incomplete or
failure states SHALL return 1, saved cancellation 130 and invalid arguments 2.
Available matches SHALL NOT hide a non-complete run status.

#### Scenario: Inspect incomplete saved progress
- **WHEN** retained evidence has a hit but the saved run is incomplete
- **THEN** output retains the hit, labels incomplete coverage and returns exit 1

#### Scenario: A record fails integrity validation
- **WHEN** a saved record is corrupt
- **THEN** search fails visibly without returning trusted search results or modifying the run
