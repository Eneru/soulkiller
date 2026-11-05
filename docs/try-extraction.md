# Try the extraction program

This is the first manually usable extraction milestone. It reads the invented
TXT/PDF example, saves progress and lets you read it later. The default demo includes two PDFs and an invalid-encoding case. No model, account,
paid call or personal-directory scan is involved. It does not chat yet.

## 1. Open the offline environment

In a **host WSL terminal opened in Soulkiller**, build and launch:

```sh
docker build -t soulkiller-dev .devcontainer
docker run --rm -it --init --network none --memory 3g --cpus 2 \
  --mount "type=bind,source=${PWD},target=/workspaces/soulkiller" \
  --workdir /workspaces/soulkiller soulkiller-dev bash
```

These are the only host commands. All following commands run **inside that
container**. The ordinary connected editor devcontainer can inspect results,
but extraction deliberately requires this offline launch.

## 2. Run the example

```sh
export PYTHONPATH="$PWD/experiments/text-pdf/src"
python -m soulkiller_text run --run-id demo-001
```

Choose a different ID if demo-001 already exists. Expect a run status, one
outcome per selected example document, TXT text, PDF page headings and a saved
location: `.soulkiller-local/evaluation/demo-001/`.
A complete schedule can include document errors; it does not mean every
extraction succeeded. The example is synthetic, with French/English text.

## 3. Read it again

```sh
python -m soulkiller_text show --run-id demo-001
python -m soulkiller_text show --run-id demo-001 --json
```

The first command is the readable report. The second is machine-readable JSON
preserving exact evidence. Neither starts extraction again. Stored files use
integrity framing: use show rather than opening them as ordinary text files.
The folder and saved results persist when you exit and relaunch the container
with the same Soulkiller mount. Repeat the export after opening a new terminal.

## 4. Check the reference facts

~~~sh
python -m soulkiller_text score --run-id demo-001
python -m soulkiller_text score --run-id demo-001 --json
~~~

For a newly extracted current example, expect **6/6 exact quotes**, **6/6 correct
reference locations** and **5/5 expected outcomes**, including invalid encoding.
These are observations for six invented reference facts, not a general quality
score or an approved acceptance threshold. No worker runs and no files change.
The command also works in the ordinary connected editor container.

Each fact shows its quote, expected location and one observed resolving location.
Locations are (page, start, end): TXT has no page, while PDF references one-based
pages. Offsets are zero-based, end-exclusive Unicode code points within saved TXT
or the saved PDF page text. No normalization is applied; case, accents and
whitespace matter. Recovery on a wrong page or at wrong TXT offsets is visible
separately from location correctness.

Failures and missing rows retain their expected facts in the totals. Outcome
agreement is separate from quote recovery. Unannotated documents are counted;
zero reference facts means 0/0, never a perfect score. Partial/incomplete runs
remain visibly partial/incomplete. Score uses saved annotations: older runs may
contain fewer reference facts, even after the current manifest changes. Extract
under a new run ID to try the current six-fact example.

## 5. Find a source passage

In either the offline container or the ordinary connected editor devcontainer:

~~~sh
python -m soulkiller_text search --run-id demo-001 --query "lampe bleue"
python -m soulkiller_text search --run-id demo-001 --query "paper stars"
python -m soulkiller_text search --run-id demo-001 --query "paper stars" --limit 1 --json
python -m soulkiller_text search --run-id demo-001 --query "absent phrase"
~~~

Expect one French PDF match on page 1 for "lampe bleue", two English matches
(TXT and PDF) for "paper stars", and an explicit no-match message for the absent
phrase. With limit 1, the JSON marks additional matches rather than claiming an
exact total. The command reads saved results without extracting again or writing
an index, cache or query log.

Search is **case-sensitive literal substring matching**: accents and whitespace
must match too. It does not interpret regular expressions or answer a question.
A missing expression only means that literal passage was not found in retained
text. Source order is stable (manifest, physical PDF page, offset), not a relevance
or truth ranking. Pages and documents are never joined to create a match.

Each hit includes the declared source labels, revision hash, exact quotation
and up to 80 context code points on each side. Match and excerpt ranges are
separate, zero-based and end-exclusive in saved TXT or the named PDF page.
The JSON quote and excerpt resolve by slicing those exact ranges; page numbers
are one-based. Declared labels do not verify identity or authorship.

Document coverage stays visible even for failed, partial, missing or unfinished
extractions. A complete schedule can still have invalid files. Missing-page
coverage is unknown when the PDF total is unavailable; a partial page hit does
not make the other pages searchable. All saved records must pass integrity
validation before any trusted results are printed.

Default output is 3 matches; --limit accepts 1..20. --query accepts 1..200 code
points with nonblank text. These are experimental output guards, not validated
PC capacity. Invalid arguments fail before opening the run. Text display escapes
terminal controls; JSON retains exact evidence.

## 6. Try the errors

- Repeat run with demo-001: it refuses to replace the earlier result.
- Show an unknown ID: it fails without creating a run.
- Run in the ordinary connected editor container: it explains the offline launch.
- Ctrl+C during work: completed checkpoints remain; caught interruption records
  unfinished documents. Very small examples may finish before you press it.

Exit 0 means the schedule completed (inspect individual errors); exit 1 means
failure/incomplete state; exit 2 means incorrect arguments; exit 130 means
cancellation. Search uses these same status-based exits: a complete run with no
matches exits 0, while incomplete or cancelled saved progress keeps its nonzero
status even if hits are available. Score also uses status-based exits: a quality mismatch is
reported without making a complete run fail an unapproved quality gate.
Unexpected stop/storage failure can leave an incomplete folder:
show labels missing observations unknown instead of claiming completion.

## Boundaries

Only an explicitly validated synthetic corpus is accepted; --corpus selects
another prepared relative corpus, not a folder to scan. Do not use personal data.
Source files are not needed for later reading, but the selected source directory
must still exist for the store's separation check.
Existing bounds and no-overwrite rules remain active. No crash/power-loss
durability, native Windows performance, semantic/reading-order evaluation, parser ranking or full benchmark report
is claimed. Plain display escapes terminal controls; JSON retains exact text.

Next milestone: compare local/remote inference and specify the first sourced dialogue. The current tool has no RAG or persona memory.
