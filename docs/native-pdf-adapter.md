# Native PDF adapter foundation

The [fourth extraction tranche](../openspec/changes/implement-pypdf-adapter/proposal.md)
adds an internal native-page adapter and independently authored synthetic
fixtures. The [parent evaluation](../openspec/changes/evaluate-text-pdf-extraction/design.md)
was approved in PR #13; TXT worker supervision was reviewed and merged in PR #16.

This seam handles trusted synthetic bytes for adapter tests. It is not a PDF
ingestion command or a complete evaluation runner. The
[PDF corpus extension](pdf-corpus-input.md) adds parser-free manifest/snapshot
validation. Supervised PDF protocol, the full offline execution boundary, scoring, persisted
page evidence and Docling comparison remain subsequent short PRs.

## Runtime and native editor

Rebuild the devcontainer to provision base pypdf **6.20.0** in
`/opt/python-tools`, with the exact wheel hash in the existing Python lock.
The plan's 6.19.0 metadata snapshot is updated because
[6.20.0 adds stream-decoding security guards](https://github.com/py-pdf/pypdf/releases/tag/6.20.0).
No optional crypto/image/font/Brotli extras, model or provider is installed.
See [the artifact/license inventory](python-toolchain.md#native-pdf-candidate)
and [native editor setup](python-editor.md).

The existing image interpreter, Pylance navigation, strict mypy/Ruff diagnostics
and pytest discovery cover these modules. CLI and image verification do not
claim that a human editor UI has been exercised.

## Internal byte adapter

`soulkiller_text.native_pdf.extract_native_pdf(source, max_pages=20)` accepts
immutable bytes only. It deliberately is not exported as a new package-level
ingestion helper. Source bytes are capped at 5 MiB; the integer page ceiling
must be from 1 to 20, with booleans rejected. Invalid source type raises
`TypeError("invalid_pdf_source")`; excessive bytes or an invalid page bound
raise `ValueError("pdf_input_too_large")` or `ValueError("invalid_pdf_page_limit")`
before parser execution.

The frozen `PdfResult` contains:

| Field | Meaning |
| --- | --- |
| `outcome` | Named `PdfOutcome` enum |
| `source_sha256` | SHA-256 of the exact original bytes |
| `pages` | Tuple of covered `PdfPage(page_number, text)` records |
| `total_pages` | Actual count when known, otherwise `None` |
| `missing_pages` | One-based pages whose extraction was attempted and failed |

Covered page text remains unchanged. Page numbers are physical one-based
indices, not PDF display labels. String slices use zero-based, end-exclusive
Unicode code points; they do not represent original-file byte offsets or visual
coordinates. The records are value containers, not child-protocol validators,
proof of authorship or persona memory.

| Outcome | Interpretation |
| --- | --- |
| `success` | All pages covered and at least one has meaningful native text |
| `no_text` | All pages covered but text is empty/whitespace-only; empty pages retained |
| `encrypted_pdf` | Detected protection, including an empty-password protected file |
| `malformed_input` | Reader/page-tree failure, or uniformly malformed pages with no covered page |
| `page_limit` | Count exceeds the accepted cap; no text extraction attempted |
| `unsupported_dependency` | Dependency unavailable, including uniformly failed pages with no covered page |
| `partial` | Some pages covered and some missing; never complete success |
| `candidate_failure` | Unexpected failure or mixed failure kinds with no covered page |

A rejected page-limit result records its count with empty covered/missing tuples;
it does not allocate a tuple proportional to an arbitrarily large rejected count.
A later independent fixture remains eligible after a failure.
`MemoryError` and cancellation propagate so future supervision can enforce its
own result boundary; they are not converted into partial success.

## Parser behavior and limits

pypdf imports lazily, so importing the internal adapter does not load the parser.
Before reader construction, its public configuration disables external JBIG2
helpers and legacy handling; parser logging is suppressed to avoid exposing
input diagnostics. These settings are process-local and suit sequential
evaluation workers.

Reading is non-strict and extraction uses plain native text. There are no
attachment/action/image-export/layout-debug operations, OCR or fallback.
The caller supplies no password; pypdf may try an empty password internally.
Detected protection is still rejected before page access. Some AES revisions
can raise a dependency error during construction; this remains a dependency
blocker rather than invented proof of encryption.

No native text does not prove that a PDF is a scan. Plain extraction does not
guarantee visible reading order, accurate pre-existing OCR or table semantics.
Counting pages can flatten a page tree; decompression/extraction can allocate
before returning. The adapter itself does not enforce time, memory or network
isolation. The separately reviewed PDF worker integration must establish those
guards before a user-file run interface is delivered.

## Synthetic fixtures and checks

The maintained stdlib writer in
[synthetic_pdf.py](../experiments/text-pdf/src/soulkiller_text/synthetic_pdf.py)
generates deterministic PDF objects/xref, explicit Helvetica/WinAnsi text,
blank pages and an image-only sentinel. French/English facts and physical pages
are authored in reusable test fixtures independently of extraction output.
A protected sentinel is encrypted only in tests using base pypdf's RC4 support;
it does not add an optional crypto dependency.

From the root inside the rebuilt devcontainer:

```sh
python -c 'import pypdf; assert pypdf.__version__ == "6.20.0"'
bash tools/checks/python.sh static
bash tools/checks/python.sh tests
bash tools/checks/python.sh audit
bash tools/checks/check.sh all
```

All maintained adapter/models/writer source is included in the existing
**70% executable line-coverage** gate. Tests cover real small fixtures and
meaningful public-boundary doubles; private readability helpers require no
direct structure tests. No source exclusions or timed benchmarks are added.
See [quality execution points](quality-checks.md#experimental-python-checks).

For the explicit offline suite, launch from a host terminal opened in Soulkiller:

```sh
docker run --rm --init --network none --memory 3g --cpus 2 \
  --mount "type=bind,source=${PWD},target=/workspaces/soulkiller,readonly" \
  --workdir /workspaces/soulkiller soulkiller-dev \
  bash tools/checks/python.sh tests
```

Only the Docker launch runs on the host; tests run in the container without
credentials/downloads, with only Soulkiller mounted. Dependency advisory audits
are separate explicit network checks. These tests do not measure Windows
performance, establish household-PC capacity or complete the approved parser
comparison. Results actually executed belong in the delivery PR.
