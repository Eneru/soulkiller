# Design: supervised native PDF worker

## Context
PR #18 merge was confirmed on 2026-10-11. This sixth tranche connects immutable
bytes to the reviewed native adapter under the existing process supervisor.
Declared manifest pages/facts remain independent reference metadata.

## Decisions
### Fixed byte API and records
Expose `run_pdf_worker(source: bytes, limits=None, max_pages=20)` alongside TXT.
Reuse exact `WorkerLimits` validation and source-byte bounds. Reject non-exact
bytes, excessive input, invalid limit objects and nonboolean integer page bounds
outside 1..20 before launch. No path, password, alternate command or parser is
accepted. A separate frozen `PdfWorkerResult` contains typed outcome, original
hash, covered `PdfPage` records, total_pages and missing_pages. A separate
`PdfWorkerOutcome` enum includes adapter values and supervisor failures. Value
constructors are not the protocol boundary.

### Early externally provided offline/resource boundary
Run the pinned interpreter with `-I -B`, a fixed reviewed bootstrap and sanitized
environment. Bootstrap validates arguments, sets/reads back RLIMIT_AS and
strictly/boundedly checks `/proc/self/net/dev` for exactly loopback before
importing the package/candidate/pypdf. Unknown/malformed/unreadable topology or
a connected namespace returns unsupported_environment without parsing. Reuse
the reviewed standalone memory guard; avoid duplicate policy definitions.

Docker `--network none` supplies the external boundary. The topology check does
not create a namespace or turn an ordinary devcontainer offline. Loopback remains
available. Assume the trusted non-root image, no added privileges, only Soulkiller
mounted, no socket or external services and stable namespace during execution.
This is not a general hostile-parser sandbox or protection against a privileged
operator changing interfaces.
Primary sources: [Docker none networking](https://docs.docker.com/engine/network/drivers/none/)
and [kernel proc network tables](https://docs.kernel.org/filesystems/proc.html#networking-info-in-proc-net).

The parent deadline covers launch, input transfer, guard setup, parsing and exit.
Address space is not RSS; the approved worker and output ceilings remain intact.
Missing enforcement uses reserved exit 3; explicit MemoryError uses exit 4;
unexplained crashes remain candidate failures. Keep those early-import fallback
exits as named constants in the standalone PDF entry: obtaining them from the
package or guard helper would make failure handling depend on the import that
failed. Preserve cancellation and cleanup.

### Reuse process lifecycle
Keep the single subprocess import and exact Popen call/options in
`supervise.run_command`. Add an explicit typed completion callback with TXT as
the compatible default; PDF supplies its own completion classifier. Use precise
overloads/generic annotations rather than spreading format switches through IO
or cleanup. Adapt the narrow Bandit function-owner check only as needed to
recognize declaration-only overloads while still requiring exactly one concrete
owner and the exact reviewed call/import. Add regression tests against weakened
ownership and retain every other finding; no second launch exception.

Continue using nonblocking bounded pipes, combined stdout/stderr cap, waitid
WNOWAIT, one deadline and mandatory group termination/reaping on all paths.
The PDF completion classifier uses the same exit/cap precedence and independently
decodes the response; no response becomes success merely because text exists.

### Separate PDF protocol
PDF response uses exact fields `version: 2`, `outcome`, `source_sha256`, `pages`,
`total_pages`, `missing_pages`. Each page has exactly `page_number` and `text`.
Reject duplicate keys, invalid UTF-8/JSON/constants/depth, extra fields,
boolean/noninteger counts, surrogate text and wrong hashes. Covered/missing
numbers must be sorted, unique, disjoint and partition 1..total for bounded known
counts. Preserve exact candidate page text. Empty covered page strings are legal.

Complete meaningful coverage yields success; complete empty/whitespace coverage
yields no_text; partial requires both covered and missing pages. Unknown
constructor/protection errors carry no count/pages; known all-page failures may
retain total and all missing pages with malformed/dependency/candidate outcomes.
page_limit accepts an actual count above the requested cap with empty tuples,
without allocating missing pages proportional to that count. Any count above
the cap in other outcomes is invalid. Permit only adapter outcomes across the
candidate wire; supervisor timeout/resource/output/protocol/environment failures
derive from observation/reserved exits, not arbitrary wire claims.

The bootstrap catches MemoryError before a complete response and exits 4.
Sensitive parser diagnostics/stderr remain capped and excluded from public data.

### Tests and existing tools
Use independently authored protocol records and tiny bilingual PDF fixtures.
Test real connected refusal and real offline success/protection/malformed/empty
cases, page bounds, output overflow, partial/invalid responses, guard ordering,
missing enforcement, explicit allocation failure, timeout/cancellation/cleanup
and TXT regressions. Deterministic fault seams may use trusted test commands,
but public worker always selects the fixed bootstrap.

Execute canonical connected-container gates and the same complete Python suite
in a fresh `--network none --memory 3g --cpus 2` container. Offline success cases
must assert actual page/text results; connected refusal is not their substitute.
No extra dependency/image/editor setting is necessary. Existing native Python
integrations, all-source executable line coverage >=70%, full Bandit policy,
pinned audits and eligible CI remain active.

## Limits and delivery
No corpus scheduler, full-run budgets/metrics, output persistence, evidence
scoring, Docling or Windows benchmark is delivered. The worker guards one trusted
native candidate; input/output ownership and report semantics remain follow-ups.
Update documentation/CHANGELOG and parent progress, mark PR #18 merge confirmed,
publish one ready App-bot PR with executed checks/limitations and await review.
