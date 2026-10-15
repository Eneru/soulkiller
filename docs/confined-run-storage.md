# Confined run-storage foundation

The [eighth extraction tranche](../openspec/changes/implement-confined-run-storage/proposal.md)
adds the filesystem boundary required before saving comparison reports. It
stores **opaque bytes**, independently of the [in-memory runner](bounded-corpus-run.md).
There is no automatic runner persistence, report schema or CLI yet.

## Create, write and reopen

Inside the devcontainer, from Soulkiller's root:

```sh
PYTHONPATH=experiments/text-pdf/src python - <<'PY'
from pathlib import Path
from soulkiller_text import create_run_store, open_run_store

workspace = Path.cwd()
corpus = "experiments/text-pdf/corpus"
with create_run_store(workspace, corpus, "run-example-001") as store:
    store.write_record("example", b'{"note":"synthetic storage example"}')

with open_run_store(workspace, corpus, "run-example-001") as store:
    print(store.read_record("example").decode("utf-8"))
PY
```

Choose an unused run ID: repeating creation fails rather than reusing the folder.
The fixed location is `.soulkiller-local/evaluation/<run-id>/`, already ignored
by Git. Neither API accepts another output root. Opening an existing store is
read-only and creates nothing. There is no append, replacement, deletion,
automatic cleanup, catalog or directory scan.

Run IDs and record names are lowercase ASCII components, 1–64 characters:
`[a-z0-9][a-z0-9_-]{0,63}`. Paths, dots, uppercase letters, drive syntax,
NUL and surrogate code points are rejected. Payloads must be exact immutable
`bytes`; the store does not interpret JSON or Python objects.
Each handle has one owner; call its operations sequentially. Always use the
returned context manager or close the handle explicitly.

## Boundaries and records

The source directory is checked before output creation. Source/output trees
must be disjoint in both directions, including directory identity aliases on a
case-insensitive backing filesystem. This checks directory confinement, not
manifest validity or source acceptance; no worker starts through these APIs.

Workspace/output traversal and file operations use Linux directory descriptors
and no-follow flags. Existing run leaves are refused, whether directories,
files or links. Existing record names are never replaced. Unsupported platform
runtime capabilities fail before writes; filesystem-specific link/sync failures
can arise during an operation and preserve created state. Requested directory/file modes are restrictive;
Windows ACL confidentiality is not established by Linux mode bits.

Each stored record has a 48-byte header: magic `SKRUN01\n`, network-order payload
length and SHA-256 digest, followed by unchanged payload bytes. Inspection checks
the complete frame, digest, bounded stable reads and a single-link regular inode
before returning bytes. The digest detects corruption/completeness failures;
it does not authenticate origin, source truth or a comparison result.

Storage guards count **encoded frame bytes**, including that header:

| Guard | Ceiling |
| --- | --- |
| One framed record | 10 MiB |
| All committed records plus an in-flight frame | 50 MiB |
| Committed record count | 34 (32 fixtures plus two metadata records) |
| In-flight scratch files | One per writable handle |

Empty payloads are valid and consume header/count capacity. These storage bounds
are distinct from the runner's actual pipe-byte observations; a future report
serializer must account for its own framing and metadata overhead.

## Publication, interruption and errors

A write fills an exclusive random scratch file, handles short writes, requests
file synchronization and publishes the completed inode through an exclusive
hard link. It then removes only that owned scratch link and requests directory
synchronization. Ordinary rename/replace is not used.

If writing, synchronization, publication or scratch removal fails, the call does
not claim success and the handle refuses subsequent writes. Earlier committed
records remain readable. Any remaining scratch state is retained for inspection;
completed publication steps are not undone. Scratch names cannot be requested
as committed records. An interrupted publication may leave a multiply linked final inode, which reads reject.

`RunStoreError` exposes a fixed category without supplied paths, payloads or
raw operating-system diagnostics. Operator cancellation propagates after
transient descriptors close; the directory descriptor closes on context exit.
No failure removes existing runs or user-owned files.

Descriptor anchoring assumes a trusted workspace: it does not protect against
a hostile same-UID/privileged operator moving already acquired directories or
mounts. Synchronization is requested and failures are reported; power-loss,
SIGKILL recovery and storage-stack durability are not claimed.

## Checks and next step

```sh
bash tools/checks/check.sh all
```

The existing bounded offline Python invocation also exercises these synthetic
filesystem tests with container-internal temporary folders. All maintained
storage source participates in the >=70% executable-line coverage gate, Ruff,
strict mypy and full Bandit. Gitleaks/Hadolint and advisory audits remain active.
The storage modules use the existing Python runtime, native editor integration
and eligible CI. A curl package-pin repair requires rebuilding the devcontainer;
Python, pypdf, editor extensions and workflow configuration remain unchanged.

Next: versioned typed result records and automatic runner checkpoints before a
CLI, scoring, Docling and the reviewed comparison. This foundation does not yet
save a `CorpusRunResult` automatically or make interrupted runs durable.
