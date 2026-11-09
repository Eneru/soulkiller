"""The ignored model store verifies bytes without accepting path redirection."""

import hashlib
import os
from pathlib import Path

import pytest

from soulkiller_text import local_model_asset
from soulkiller_text.dialogue_error import DialogueError
from soulkiller_text.local_model_constants import MODEL_DIRECTORY, MODEL_FILENAME


@pytest.mark.parametrize("kind", ["valid", "wrong", "symlink", "linked", "absent"])
def test_verified_model_checks_exact_bytes_and_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    """Verify only the pinned file, without opening a substitute or leaking its path."""
    # Arrange
    pinned = b"synthetic model"
    monkeypatch.setattr(local_model_asset, "MODEL_SIZE", len(pinned))
    monkeypatch.setattr(local_model_asset, "MODEL_SHA256", hashlib.sha256(pinned).hexdigest())
    model = tmp_path / MODEL_DIRECTORY / MODEL_FILENAME
    model.parent.mkdir(parents=True)
    other = tmp_path / "unapproved"
    other.write_bytes(pinned)
    if kind == "symlink":
        model.symlink_to(other)
    elif kind == "linked":
        os.link(other, model)
    elif kind != "absent":
        model.write_bytes(pinned if kind == "valid" else b"forged model!!!")

    # Act / Assert
    if kind == "valid":
        with local_model_asset.verified_model(tmp_path) as descriptor:
            assert os.pread(descriptor, len(pinned), 0) == pinned
    else:
        with pytest.raises(DialogueError, match="local_model_asset"):
            with local_model_asset.verified_model(tmp_path):
                pytest.fail("invalid asset was yielded")
