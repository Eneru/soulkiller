# Decision-recording design

## Context

The study in PR #4 is reviewed and merged; issue #3 is completed. The maintainer's
2026-10-03 answers confirm first inputs/languages, a small planning corpus and
automatic persona memory. Local versus remote operation must still be compared.
See [proposal.md](proposal.md) and the
[first-increment framing](../../../docs/research/soulkiller-first-increment-framing.md).

## Decisions

1. Keep the existing decision register as the handoff entry point. Add one focused
   framing document for inference options, comparison controls and memory questions.
   Preserve the study report's 2026-10-02 evidence snapshot and point to later answers.
2. Record automatic saving, immediate use with conversational origin and
   same-persona sharing as confirmed intent. Content, attribution/access, conflicts,
   retention and deletion semantics remain open. Do not add a human confirmation
   requirement or per-interlocutor isolation contrary to these answers.
3. Treat the approximate corpus size as a planning input and French/English as
   first source-language priorities. No capacity, response-language or cross-language
   performance claim follows from these answers.
4. Keep local extraction required; local retrieval/storage in the comparison is
   a proposed control, not an adopted architecture. Describe complete local,
   owned-server and hosted options without selecting a provider or permitting
   a data transfer.
5. Publish a narrowly scoped framing issue and use a closing keyword in the
   draft PR. Its closure completes this documentation task, not all of R1/F1.
   Record native-link capability limitations; a branch name is not a native link.
6. Document automatic branch deletion as an owner-controlled repository setting.
   Keep repository settings unchanged and merges manual.

## Validation

Run strict OpenSpec validation and Git whitespace checks in the devcontainer.
Check local Markdown links, scope, common secret patterns and LICENSE against
the main baseline. A read-only review checks that confirmed answers are not
converted into stack adoption or completed experiments. No container rebuild
or application tests apply to this documentation-only change.
