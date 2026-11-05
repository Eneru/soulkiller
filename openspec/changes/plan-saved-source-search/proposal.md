## Why

Extraction is now manually usable and its reference facts can be checked.
The next useful action is finding a passage without reading every saved document.
Propose one small search journey before introducing generated answers.

**Status: approved in merged PR #25; implementation proceeds under this contract.**
PR #24 and PR #25 merges are confirmed. The maintainer explicitly requested the
implementation after reviewing this packet.

## What the maintainer will be able to try

After an ordinary saved synthetic run, the proposed command is:

~~~sh
python -m soulkiller_text search --run-id demo-001 --query "lampe bleue"
~~~

It would show the French PDF passage, document identity, revision hash and page 1.
Searching "paper stars" would show both the English TXT and English PDF sources.
Searching an absent phrase would say no matching passage was found.
The result is quoted evidence, not a generated persona answer.

## Proposed scope to approve

- Literal, case-sensitive expression search in one explicitly selected saved run.
- Read-only text and JSON results, with resolvable source references and context.
- Visible extraction failures/incomplete coverage, bounded results and stable order.
- One implementation PR with CLI tests, manual examples and existing quality gates.
- Python standard library and the existing saved reader; no dependency or service.

This deliberately narrow reference can later be compared with lexical indexing
or semantic retrieval. It does not adopt SQLite, an embedding model, a production
language or a final retrieval strategy.

## Boundaries and following milestone

Synthetic inputs remain the only permitted corpus. No source scan, new extraction,
index/cache, LLM, provider, data transfer, persona memory, GUI or Windows claim.
A complete Docling/benchmark comparison is not a prerequisite for this independent
read-only journey.

After this implementation, prepare the local/remote inference comparison and
grounded-dialogue contract. Real model downloads, endpoints and spending still
need reviewed assets, data boundaries and budgets. This packet authorizes none
of those, nor any automatic follow-up implementation.
