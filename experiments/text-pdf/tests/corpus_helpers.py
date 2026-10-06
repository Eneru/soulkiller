"""Independent synthetic manifest builders for schema and filesystem tests."""

import json


def annotation_document() -> dict[str, object]:
    """Return a literal expectation for the invented three-byte source abc."""
    return {"start": 0, "end": 3, "quote": "abc"}


def fixture_document(
    fixture_id: str = "sample", path: str = "texts/sample.txt"
) -> dict[str, object]:
    """Return fresh metadata with a fixed independently known source revision."""
    return {
        "id": fixture_id,
        "path": path,
        "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        "format": "txt",
        "language": "en",
        "author_label": "Synthetic author",
        "subject_label": "Synthetic subject",
        "outcome": "success",
        "annotations": [annotation_document()],
    }


def manifest_document(
    fixtures: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """Return a fresh version-1 manifest without accessing source files."""
    return {"schema_version": 1, "fixtures": [fixture_document()] if fixtures is None else fixtures}


def encode_manifest(document: object) -> bytes:
    """Encode test JSON, including intentionally invalid schema values."""
    return json.dumps(document, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
