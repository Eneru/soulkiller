# Design: confined immutable run-storage foundation

## Context and scope
PR #20 merge was confirmed at 6deea6c33cb1f91f86bf64f093f91e3e1688bb58.
The approved evaluate-text-pdf-extraction plan fixes the output root at
.soulkiller-local/evaluation/<run-id>/. This tranche stores opaque bounded bytes;
typed result serialization and automatic incremental persistence follow later.

## Public API
create_run_store(workspace_root: Path, corpus_path: str, run_id: str) returns a
context-managed RunStore for a new run. open_run_store has the same arguments
and returns a read-only context-managed store without creating anything.
The trusted workspace must be absolute and free of parent traversal.

RunStore.write_record(name: str, payload: bytes) publishes a new immutable
record; read_record(name: str) returns a known record's original payload.
Handles have one owner and sequential operations, matching the approved
single-worker execution model. No generic directory scan/catalog, arbitrary output path, append, replacement,
delete, resume or record interpretation is exposed. Always close/use the context.

Run IDs and record names are lowercase ASCII single components matching
[a-z0-9][a-z0-9_-]{0,63}; no separators, dots, drive syntax, NUL or surrogates.
All validation errors use a separate safe RunStoreError with fixed categories,
without supplied paths, payloads or raw OS diagnostics. Missing runtime
capabilities fail before any write; filesystem-specific link/sync failures may
be discovered only during the operation and preserve created state. Invalid names/payload/budgets do not create a scratch file.

## Descriptor confinement and separation
Reuse reviewed directory-walk/read primitives where practical; do not weaken
existing input confinement. Require Linux O_DIRECTORY/O_NOFOLLOW/O_NONBLOCK/
O_CLOEXEC, dir_fd-capable open/mkdir/link/unlink and available fsync operations.
Filesystem-specific support is checked by executing those operations, not inferred
from flag availability.
Walk absolute workspace and relative source components without following links.
Validate the source directory before creating output state; this is directory
validation, not manifest/corpus acceptance and never launches a worker.

Reject source/output subtree overlap in both directions before any mkdir.
Compare path components and acquired directory identities to catch case aliases
on WSL/Windows backing filesystems. Never write inside selected source or local
credential folders. Walk existing .soulkiller-local/evaluation parents without
following symlinks; create missing parents with restrictive requested modes.
Create the run with exclusive mkdir: every pre-existing leaf, including a link,
file or directory, is refused without reuse/overwrite/cleanup.
Read-only open requires the already existing confined run directory.

All file operations stay anchored to the acquired run descriptor. Replacements
before acquisition must not be followed. This does not defend against hostile
same-UID/privileged operators relocating already acquired directories or mounts.
Assume a trusted workspace and no hostile concurrent namespace mutation.
Requested Linux modes do not establish a Windows ACL confidentiality guarantee.

## Bounded complete records
Use a fixed binary frame: eight-byte magic SKRUN01\n,
then network-order uint64 payload length and 32-byte SHA-256 digest, then the
unchanged bytes. Header size is 48 bytes; its digest checks corruption/completeness,
not authenticity. Readers never deserialize executable data.

Ceilings count encoded frame bytes: 10 MiB/record and 50 MiB/store, reusing the
approved experimental output bounds. At most MAX_FIXTURES+2 (34) committed records
allow one per fixture and two metadata records; at most one in-flight scratch.
These are storage guards, not throughput/product limits. Empty payloads are legal
but consume the header/count budget. The writer rejects excess before creating
a scratch file. This storage-byte metric is separate from worker pipe observations.

Write a randomly named exclusive regular scratch file using no-follow/nonblocking
flags, handling short writes and rejecting zero progress. Request fsync on its
completed frame, atomically link to the final name with no replacement, unlink
only that owned scratch after publication, then request directory fsync.
Never use rename/replace because they may overwrite. Verify the scratch remains
the acquired single-link regular inode before publication. Existing final files,
links, FIFOs and directories remain untouched.

On any exception after scratch creation, including cancellation, preserve remaining
created state without undoing completed publication steps, close transient scratch descriptors and prohibit further writes
from that handle. Its acquired directory descriptor remains available for reads
until context exit/close.
Earlier committed records remain readable. A failed fsync/publication/cleanup
is never reported as success. Scratch names cannot be requested through the
public record-name grammar, so partial scratch cannot be read as a committed record.
A crash between link and scratch unlink may leave a multiply linked final inode;
inspection rejects it rather than accepting uncertain publication.
No automatic cleanup, SIGKILL recovery, power-loss or storage-stack durability
guarantee is claimed.

Read through the reviewed bounded descriptor reader: regular single-link files,
exact size/revision stability and a finite encoded-size cap. Verify magic,
declared length, full frame and digest before exposing bytes. Missing, malformed,
truncated, oversized, mutated, linked and special-file records fail safely.
Reopening never grants write access or appends to old runs.

## Quality and delivery
Independent AAA tests cover exact byte/count bounds, empty/binary/Unicode
payloads, reopen, existing-path preservation, every symlink boundary, source
overlap/case-alias identities, unsupported capabilities, short/zero/failed writes,
interruption, frame corruption and deterministic descriptor replacement faults.
Exercise frame/fsync/link failures without personal data or paid/network calls.
Retain all worker/corpus regressions in connected and fresh bounded offline lanes.
All maintained source enters existing >=70% executable-line coverage, Ruff,
strict mypy, full Bandit, Gitleaks/Hadolint and dependency checks.
The storage API needs no new dependency, editor setting or workflow trigger.
The separate curl package-pin repair below requires rebuilding the image.
Document limits and incomplete runner/report integration, update CHANGELOG and
parent progress, publish one verified App-bot ready PR, await human review/manual merge.

## Hosted rebuild correction
After initial publication, hosted run 38781103668 failed before tests: Ubuntu APT
selected libcurl4t64 8.5.0-2ubuntu10.16 while curl and libcurl4-openssl-dev still
required 8.5.0-2ubuntu10.15. Align the three direct curl-family pins to .16 in
builder/runtime stages, confirm repository availability and rebuild/test the
image. Preserve all Python/Node/candidate/editor pins and workflow triggers.
This repairs fresh image construction; the existing cached image had passed
all foundation and storage checks. Do not report the failed hosted run as passed.
