"""Small private synthetic corpora for independent input-boundary scenarios."""

import hashlib
import json
from pathlib import Path

DEFAULT_SOURCE = b"A\xc3\xa9 e\xcc\x81\xf0\x9f\x8c\x9fZ\r\n"
SOURCE_PATH = "nested/notes.txt"


def write_corpus(
    workspace: Path,
    source: bytes = DEFAULT_SOURCE,
    changes: dict[str, object] | None = None,
) -> Path:
    corpus = workspace / "corpus"
    (corpus / "nested").mkdir(parents=True)
    (corpus / SOURCE_PATH).write_bytes(source)
    fixture: dict[str, object] = {
        "id": "t01",
        "path": SOURCE_PATH,
        "sha256": hashlib.sha256(source).hexdigest(),
        "format": "txt",
        "language": "fr",
        "author_label": "Inez (invented author)",
        "subject_label": "Corin (invented subject)",
        "outcome": "success",
        "annotations": [],
    }
    fixture.update(changes or {})
    manifest = {"schema_version": 1, "fixtures": [fixture]}
    (corpus / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return corpus
