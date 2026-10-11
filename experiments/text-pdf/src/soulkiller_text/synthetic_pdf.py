"""Deterministic tiny PDF fixtures, independent of candidate parser output."""

FONT_OBJECT = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
PAGE_RESOURCES = b"<< /Font << /F1 3 0 R >> >>"


def _stream(content: bytes, attributes: bytes = b"") -> bytes:
    length = str(len(content)).encode("ascii")
    return b"<< /Length " + length + attributes + b" >>\nstream\n" + content + b"\nendstream"


def _text_commands(text: str) -> bytes:
    if not text:
        return b""
    lines = [b"BT /F1 12 Tf 16 TL 72 720 Td"]
    for index, line in enumerate(text.split("\n")):
        encoded = line.encode("cp1252")
        escaped = encoded.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")
        if index:
            lines.append(b"T*")
        lines.append(b"(" + escaped + b") Tj")
    lines.append(b"ET")
    return b"\n".join(lines)


def _page(content_number: int, resources: bytes = PAGE_RESOURCES) -> bytes:
    return (
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources "
        + resources
        + b" /Contents "
        + str(content_number).encode("ascii")
        + b" 0 R >>"
    )


def _document(objects: list[bytes]) -> bytes:
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for number, value in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode("ascii"))
        output.extend(value + b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(output)


def build_text_pdf(pages: tuple[str, ...]) -> bytes:
    """Write trusted WinAnsi text pages; an empty string creates a blank page."""
    if not pages:
        raise ValueError("synthetic_pdf_requires_pages")
    kids = " ".join(f"{4 + 2 * index} 0 R" for index in range(len(pages)))
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode("ascii"),
        FONT_OBJECT,
    ]
    for index, text in enumerate(pages):
        objects.extend((_page(5 + 2 * index), _stream(_text_commands(text))))
    return _document(objects)


def build_image_pdf() -> bytes:
    """Write one image-only page containing an invented, uncompressed RGB pixel."""
    image_resources = b"<< /XObject << /Im0 6 0 R >> >>"
    image_attributes = (
        b" /Type /XObject /Subtype /Image /Width 1 /Height 1"
        b" /ColorSpace /DeviceRGB /BitsPerComponent 8"
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [4 0 R] /Count 1 >>",
        FONT_OBJECT,
        _page(5, image_resources),
        _stream(b"q 100 0 0 100 72 600 cm /Im0 Do Q"),
        _stream(b"\x80\xb0\xd0", image_attributes),
    ]
    return _document(objects)
