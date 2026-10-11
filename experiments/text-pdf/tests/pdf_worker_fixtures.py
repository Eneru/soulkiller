"""Independent version-2 records and observed container network topology."""

import json
from io import BytesIO
from pathlib import Path
from typing import Any

from pypdf import PdfWriter

from .synthetic_sources import BILINGUAL_SHA256

PDF_TEXT = "Invented copper telescope.\r\nÉté: e\u0301 \U0001f31f."
NETWORK_HEADERS = (
    "Inter-|   Receive                                                |  Transmit\n"
    " face |bytes    packets errs drop fifo frame compressed multicast|"
    "bytes    packets errs drop fifo colls carrier compressed\n"
)
LOOPBACK_DEVICE = "    lo: " + " ".join(["0"] * 16) + "\n"
CONNECTED_DEVICE = "  eth0: " + " ".join(["0"] * 16) + "\n"


def pdf_record(
    outcome: str = "success",
    *,
    pages: object = None,
    total_pages: int | None = 1,
    missing_pages: list[int] | None = None,
    source_sha256: str = BILINGUAL_SHA256,
) -> dict[str, Any]:
    """Declare expected facts independently from the production encoder."""
    return {
        "version": 2,
        "outcome": outcome,
        "source_sha256": source_sha256,
        "pages": [{"page_number": 1, "text": PDF_TEXT}] if pages is None else pages,
        "total_pages": total_pages,
        "missing_pages": [] if missing_pages is None else missing_pages,
    }


def pdf_payload(**kwargs: Any) -> bytes:
    return json.dumps(pdf_record(**kwargs), ensure_ascii=True).encode("ascii")


def externally_offline() -> bool:
    """Observe the test container, independently of the production guard."""
    rows = Path("/proc/self/net/dev").read_text(encoding="ascii").splitlines()[2:]
    return {row.split(":", 1)[0].strip() for row in rows} == {"lo"}


def empty_pdf() -> bytes:
    """Use the independent fixture writer for a legal zero-page document."""
    output = BytesIO()
    PdfWriter().write(output)
    return output.getvalue()
