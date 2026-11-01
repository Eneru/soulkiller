# Design

## Scope and trust boundary
Use encode_fixture_record(row) -> bytes and
decode_fixture_record(payload, specification) -> FixtureRun. The caller supplies
an already accepted CorpusFixture/PdfCorpusFixture; the decoded row reuses it.
Check its exact class, fixture ID, format, lowercase SHA-256 and PDF page ceiling,
but do not claim that a permissive dataclass proves manifest/source acceptance.
Annotations, labels and source paths are not serialized or reopened. Observed
outcomes need not equal reference expectations; mismatches remain findings.

This is one persisted row for the current fixed UTF-8/pypdf workers, not the
parent contract's complete reproducibility report. Run identity, aggregate
accounting, candidate/configuration/environment inventory, comparison metrics and
automatic checkpoints remain later tranches. Digests/bindings do not authenticate
data or establish source truth.

## Exact version-1 representation
The envelope has exactly schema_version, fixture_id, format, source_sha256,
result, output_bytes and unfinished_reason. schema_version is exact integer 1.
TXT result is null or exactly {outcome, text}; PDF result is null or exactly
{outcome, pages, total_pages, missing_pages}. Pages contain exactly page_number
and text. Encode deterministic compact ASCII JSON without text normalization.

Both encode and decode validate semantics. Reject unknown/missing/duplicate
fields, wrong/boolean numeric types, unknown versions/enums, malformed Unicode,
nonfinite JSON constants, malformed/deep framing, incorrect identity/revision
and mismatched TXT/PDF result classes. Reject before returning a typed row.
FixtureRecordError exposes fixed categories without input, paths or diagnostics.
The child-response decoders remain stricter about candidate-reported outcomes.

## Observation rules
Completed rows have an exact matching WorkerResult/PdfWorkerResult, matching
source hash, no unfinished reason and an exact integer observed count in
0..MAX_OUTPUT_BYTES+1. The extra byte is the supervisor's observed overflow probe.
TXT success preserves nonempty scalar Unicode exactly; other outcomes have no
text. PDF candidate evidence uses the existing strict page/partition validation;
supervisor-only failures require empty evidence and unavailable total.
Unfinished rows have no result, a non-COMPLETE RunStatus and count zero, or
unavailable count only for CANCELLED/CLEANUP_FAILURE. Run-wide ordering and totals
are not inferred by a per-row codec.

## Bounds and storage
Bound exact input bytes and successful encoded JSON to
MAX_RECORD_BYTES - HEADER_BYTES (10 MiB minus the 48-byte store frame). JSON
escaping/metadata count against this cap. Never truncate evidence to fit.
The codec does no file I/O. Callers explicitly pass bytes to the existing
create-only RunStore; storage failures retain their existing semantics.
Temporary JSON encoding is not a hard process-memory sandbox.

## Structure and documentation
Use separate public codec, strict fields, nested result helpers, constants and
one error-class file, with explicit collaborators. Keep functions <=50 lines.
Every new/changed function, including private/dunder/test helpers, has a useful
docstring describing its role, constraints and relevant errors. Low-level code
must explain OS-specific concepts, descriptor ownership and cleanup when present;
do not add boilerplate that merely repeats a function name.

## Verification
Independent literal JSON tests prove both directions without roundtrip-only
oracles. Cover all outcome kinds, Unicode/CRLF, partial/missing PDF pages,
unknown/zero observations, forged objects, wire errors, exact byte ceilings and
real RunStore close/reopen/no-overwrite. Include an offline real-worker-to-record
smoke in the complete existing regression lane.
Run canonical static/security/audit/tests, all-source executable line coverage
>=70%, complete fresh bounded offline Python suite, strict OpenSpec, links,
documentation/size audits, whitespace and unchanged LICENSE checks. Existing
Python image/editor and PR-main/SemVer CI apply; no rebuild or trigger is needed.
