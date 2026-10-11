"""Independent metadata and tiny filesystem corpora for PDF input tests."""

import hashlib
from pathlib import Path

from soulkiller_text.synthetic_pdf import build_text_pdf

from .corpus_helpers import encode_manifest, fixture_document

PDF_SENTINEL = b"Invented PDF revision; intentionally not a parseable document.\xff"
FRENCH_PAGES = ("Une archive inventée.", "Inez garde une lampe bleue.")
ENGLISH_PAGES = ("Corin collects paper stars.",)


def pdf_document(
    fixture_id: str = "pdf-fr",
    path: str = "pdfs/archive.pdf",
    source: bytes = PDF_SENTINEL,
) -> dict[str, object]:
    """Return independently declared metadata, without inspecting PDF contents."""
    return {
        "id": fixture_id,
        "path": path,
        "sha256": hashlib.sha256(source).hexdigest(),
        "format": "pdf",
        "language": "fr",
        "author_label": "  Inez (invented author)  ",
        "subject_label": "Corin (invented subject)",
        "page_count": 2,
        "outcome": "success",
        "annotations": [{"page_number": 2, "quote": "Inez garde une lampe bleue."}],
    }


def evaluation_document(
    fixtures: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Return a fresh version-2 manifest with an explicitly selected PDF."""
    return {"schema_version": 2, "fixtures": [pdf_document()] if fixtures is None else fixtures}


def write_evaluation_corpus(
    workspace: Path,
    fixtures: list[dict[str, object]] | None = None,
    sources: dict[str, bytes] | None = None,
) -> Path:
    """Write only invented fixture bytes and their explicit metadata."""
    corpus = workspace / "corpus"
    corpus.mkdir(parents=True)
    selected = {"pdfs/archive.pdf": PDF_SENTINEL} if sources is None else sources
    for relative, source in selected.items():
        path = corpus / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(source)
    (corpus / "manifest.json").write_bytes(encode_manifest(evaluation_document(fixtures)))
    return corpus


def bilingual_corpus(workspace: Path) -> Path:
    """Create mixed formats with literal independent fact/page expectations."""
    french = build_text_pdf(FRENCH_PAGES)
    english = build_text_pdf(ENGLISH_PAGES)
    txt = fixture_document("txt-en", "notes.txt")
    first = pdf_document(source=french)
    second = pdf_document("pdf-en", "pdfs/english.pdf", english)
    second.update(
        {
            "language": "en",
            "page_count": 1,
            "annotations": [{"page_number": 1, "quote": "Corin collects paper stars."}],
        }
    )
    return write_evaluation_corpus(
        workspace,
        [txt, first, second],
        {"notes.txt": b"abc", "pdfs/archive.pdf": french, "pdfs/english.pdf": english},
    )
