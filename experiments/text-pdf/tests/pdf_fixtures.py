"""Invented PDF source text and annotations authored before candidate extraction."""

from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock

from pypdf import PdfWriter

FRENCH_PAGES = (
    "Camille construit une serre sur la lune.\nElle cultive trois tomates dorées.",
    "Le robot Émile joue du violon le mardi.\nSa mélodie préférée évoque la forêt.",
)
ENGLISH_PAGES = (
    "Morgan paints violet clouds above the invented town.\nThe clock has seven hands.",
    "Avery keeps a copper telescope near the lake.\nThe observatory opens on Friday.",
)
FRENCH_FACT_PAGES = (
    ("trois tomates dorées", 1),
    ("Émile joue du violon", 2),
    ("mélodie préférée", 2),
)
ENGLISH_FACT_PAGES = (
    ("seven hands", 1),
    ("copper telescope", 2),
    ("opens on Friday", 2),
)
MALFORMED_PDF_SOURCES = (
    b"",
    b"not a PDF",
    b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 9 0 R >>\nendobj\n%%EOF",
)


def protected_pdf(source: bytes, password: str) -> bytes:
    """Protect an independently authored fixture using base pypdf's RC4 path."""
    writer = PdfWriter(clone_from=BytesIO(source))
    writer.encrypt(password, algorithm="RC4-128")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def page_double(text: object = "", *, error: BaseException | None = None) -> Mock:
    """Provide one page with independently declared text or a requested fault."""
    return Mock(extract_text=Mock(return_value=text, side_effect=error))


def reader_double(*pages: Mock) -> SimpleNamespace:
    """Provide physical pages without requiring parser-specific malformed streams."""
    return SimpleNamespace(is_encrypted=False, pages=list(pages))
