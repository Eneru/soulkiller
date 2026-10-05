# Design

## Authority and boundary

The approved parent is [evaluate-text-pdf-extraction](../evaluate-text-pdf-extraction/design.md).
PR #14 merge and the continuation request authorize this small implementation.
Python remains an evaluation tool. The caller supplies a trusted workspace Path
and a relative corpus path; neither anchor is chosen by manifest data. Tests use
container-internal temporary synthetic workspaces. A future CLI must use the
Soulkiller workspace anchor; this tranche creates no CLI or directory scanner.

## Manifest and models

Read fixed manifest.json with a 128 KiB byte ceiling. Strict UTF-8 JSON rejects
duplicate object keys, nonfinite constants, malformed/deep inputs, unknown fields
and incorrect types (including booleans as integers). schema_version is integer 1;
fixtures is a nonempty list of at most 32. Each fixture has exactly id, path,
sha256, format, language, author_label, subject_label, outcome and annotations.
IDs are short ASCII identifiers; paths must already be canonical relative slash paths,
without empty/dot/parent segments, backslashes, colons, absolute roots or NUL.
Reject duplicate IDs/paths and a fixture referring to manifest.json.

Only format txt and language fr/en are accepted now. SHA-256 is 64 lowercase hex
digits. Labels are explicit nonempty bounded synthetic metadata, not inferred
authorship/identity. outcome is success/no_text/invalid_encoding. At most 32
annotations per fixture contain exactly start/end/quote: nonboolean integer
code-point offsets, nonempty strings, valid nonempty spans. Failed/empty outcomes
have no annotations. All schema validation precedes fixture reads.

Separate frozen TextAnnotation, CorpusFixture and LoadedFixture classes, one per
file; keep constants/path checks/JSON validation distinct from descriptor reads
and orchestration. Public load_corpus(workspace_root, corpus_path) returns a tuple
of LoadedFixture(specification, source bytes). Data containers do not authenticate
forged instances; use the loader. Errors use a dedicated CorpusError with stable
categories, without personal paths/source content in messages.

## Confined bounded snapshots

Linux only, fail closed on unsupported platforms. Walk workspace ancestors from
/ and then corpus/path parents component by component using directory-relative
os.open with O_DIRECTORY/O_NOFOLLOW/O_CLOEXEC. Open leaves O_RDONLY/O_NOFOLLOW/
O_NONBLOCK/O_CLOEXEC, reject nonregular files or nlink!=1 before reading. Keep
anchors as descriptors while traversing; never use resolve-then-open. Close every
opened descriptor on success/error. Exclude traversal and links before target reads.

Read each source in bounded chunks up to 5 MiB plus one overflow byte; compare
size/mtime/ctime/device/inode/link metadata before/after and reject mutation or
size disagreement. Hash the returned bytes, compare the declared revision, reuse
extract_utf8 and validate outcome and exact annotation slices. Return those bytes
so later extraction never reopens the validated path. No write/delete operation.
The retained raw corpus is at most 160 MiB; these approved experiment guards are
not product limits or Windows performance evidence. Expected text is manually
authored independently of the extractor; hash computation only freezes source
revision. Literal assets require no generator dependency. Scoped -text Git
attributes preserve exact corpus TXT bytes when checkout would otherwise convert
line endings; verify this in an isolated autocrlf=true synthetic repository.

This is a Linux input boundary, not a parser sandbox or a native Windows adapter.
It does not prevent privileged mount changes or prove immutable physical storage;
hash verification binds the returned snapshot to the annotated revision. No worker,
output-write confinement, total runtime guard or actual PDF page limit is claimed.

## Quality and environment

Existing source-inclusive >=70% Python executable line coverage, separate branch
reporting, Ruff, strict mypy, Bandit and advisory gates apply to every new module.
Use independent AAA schema/read/error tests and reusable temp synthetic fixtures,
including symlink parents/leaves/root, hardlinks/FIFO, oversize inputs, directory
replacement, changing descriptors, stale expected data and valid subsequent reads.
Canonical CLI/hooks/native editor/eligible PR-to-main or SemVer-tag CI already
cover the same src/tests tree. No new Python package or runtime is needed; existing
image tools/native editor configuration remain suitable and must be verified.
No additional Actions lane or benchmark runs.

Document English Conventional Commits 1.0.0 for new authored messages with a
lowercase type and optional scope; preserve existing history and GitHub-generated
merge commits. No new commitlint dependency or CI event is necessary for this
contribution rule. Record actual tests/limits in the ready bot PR.

Primary API references: [descriptor-based reads](https://docs.python.org/3.13/library/os.html#os.open),
[JSON interoperability](https://docs.python.org/3.13/library/json.html#standard-compliance-and-interoperability).
Regular-file I/O can still block; the byte guards do not implement a wall-clock
limit or prevent filesystem stalls. Worker supervision remains a later tranche.
