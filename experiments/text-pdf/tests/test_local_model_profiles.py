"""Verify the provisioner receives exactly the allowlisted runtime profile."""

import pytest

from soulkiller_text.local_model_profiles import PROFILES, main


@pytest.mark.parametrize("name", ["qwen3-1.7b", "qwen3-4b"])
def test_provision_metadata_matches_runtime_profile(
    name: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Emit filename, size, hash and pinned URL from the selected immutable profile."""
    # Arrange
    profile = PROFILES[name]
    # Act
    status = main([name])
    stdout = capsys.readouterr().out
    # Assert
    assert status == 0
    assert stdout.splitlines() == [
        f"{profile.filename}\t{profile.size}\t{profile.sha256}\t{profile.url}"
    ]
    assert f"/resolve/{profile.revision}/" in profile.url


@pytest.mark.parametrize("arguments", [[], ["latest"], ["qwen3-1.7b", "qwen3-4b"]])
def test_unknown_provision_profile_fails_without_metadata(
    arguments: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """Refuse unreviewed selectors and leave stdout empty for the shell caller."""
    # Act
    status = main(arguments)
    # Assert
    assert status == 2
    assert capsys.readouterr().out == ""
