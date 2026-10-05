# Confined synthetic TXT corpus

## Why

PR #14 is approved and merged; the maintainer confirms native editor operation
and authorizes the next short implementation tranche of the reviewed extraction
plan. Turn its pure TXT seam into a reader for an explicitly selected synthetic
corpus before introducing PDF parsers or workers. Restore consistent new commit
messages using Conventional Commits, as requested.

## What Changes

- Validate a bounded version-1 synthetic TXT manifest and independent code-point annotations.
- Read only selected files beneath a trusted workspace/corpus anchor through Linux directory descriptors, without following symlinks.
- Reject invalid schema, paths, duplicate identifiers, stale hashes/expectations, nonregular/hardlinked files, changed files and input-budget failures.
- Return immutable metadata and the exact verified source bytes, with no later pathname reopen.
- Add literal bilingual synthetic fixture bytes/annotations and independent boundary tests.
- Preserve corpus source bytes through scoped Git attributes, including CRLF and malformed UTF-8.
- Document Conventional Commits for new authored commits, preserving existing history.

## Capabilities

### New Capabilities

- text-corpus-input: explicit synthetic TXT selection and bounded confined reads.

### Modified Capabilities

None. Partial implementation of evaluate-text-pdf-extraction; PDF selection will
be added with its first bounded worker. The existing TXT decoder is reused.

## Impact

Only experimental Python source/tests/fixture data, scoped Git attributes, OpenSpec
and documentation.
No new dependency, interpreter/editor version, workflow/event, PDF parser, CLI,
worker, output directory, benchmark, LLM/provider or application behavior.
Refs #7; human review/manual merge remain required.
