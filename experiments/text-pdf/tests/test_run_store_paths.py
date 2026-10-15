"""Creation and reopening reject unsafe output namespaces before writes."""

import os
import sys
from pathlib import Path
from typing import cast

import pytest

from soulkiller_text import run_store_paths
from soulkiller_text.run_store import create_run_store, open_run_store
from soulkiller_text.run_store_error import RunStoreError

from .run_store_fixtures import RUN_ID, directory_entries, run_directory, workspace_with_source


@pytest.mark.parametrize("run_id", ["a", "a0_-", "a" * 64])
def test_safe_run_names_create_only_the_fixed_output_tree(tmp_path: Path, run_id: str) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    # Act
    with create_run_store(workspace, "corpus", run_id):
        entries = directory_entries(workspace)
    # Assert
    assert entries == {"corpus", ".soulkiller-local"}
    assert run_directory(workspace, run_id).is_dir()
    assert directory_entries(run_directory(workspace, run_id)) == set()
    assert (workspace / "corpus" / "source.txt").read_bytes() == b"Synthetic source."


@pytest.mark.parametrize(
    "run_id",
    ["", ".", "..", "a.b", "a/b", "a\\b", "A", "é", "a:b", "a\x00", "a\ud800", "a" * 65, None],
)
def test_invalid_run_names_fail_before_any_output(tmp_path: Path, run_id: object) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    # Act
    with pytest.raises(RunStoreError) as failure:
        create_run_store(workspace, "corpus", cast(str, run_id))
    # Assert
    assert failure.value.category == "invalid_name"
    assert failure.value.args == ("invalid_name",)
    assert directory_entries(workspace) == {"corpus"}


@pytest.mark.parametrize("kind", ["directory", "file", "fifo", "symlink"])
def test_existing_run_is_preserved_without_reuse(tmp_path: Path, kind: str) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    run = run_directory(workspace)
    run.parent.mkdir(parents=True)
    if kind == "directory":
        run.mkdir()
        (run / "keep").write_bytes(b"Keep existing run.")
    elif kind == "file":
        run.write_bytes(b"Keep existing file.")
    elif kind == "fifo":
        os.mkfifo(run)
    else:
        run.symlink_to(workspace / "corpus", target_is_directory=True)
    before = run.lstat()
    # Act
    with pytest.raises(RunStoreError) as failure:
        create_run_store(workspace, "corpus", RUN_ID)
    # Assert
    assert failure.value.category == "run_exists"
    assert run.lstat() == before
    assert directory_entries(run.parent) == {RUN_ID}


@pytest.mark.parametrize("boundary", ["workspace", "corpus", "local", "evaluation"])
def test_directory_symlinks_are_not_followed(tmp_path: Path, boundary: str) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    run_directory(workspace).parent.mkdir(parents=True)
    target = {
        "workspace": workspace,
        "corpus": workspace / "corpus",
        "local": workspace / ".soulkiller-local",
        "evaluation": run_directory(workspace).parent,
    }[boundary]
    original = target.with_name(target.name + "-original")
    target.rename(original)
    target.symlink_to(original, target_is_directory=True)
    # Act
    with pytest.raises(RunStoreError) as failure:
        create_run_store(workspace, "corpus", RUN_ID)
    # Assert
    assert failure.value.category == "unsafe_path"
    assert not (original / RUN_ID).exists()
    assert target.is_symlink()


@pytest.mark.parametrize(
    "capability", ["platform", "O_NOFOLLOW", "O_DIRECTORY", "O_NONBLOCK", "O_CLOEXEC", "dir-fd"]
)
def test_missing_enforcement_fails_before_creating_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capability: str
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    if capability == "platform":
        monkeypatch.setattr(sys, "platform", "win32")
    elif capability == "dir-fd":
        monkeypatch.setattr(os, "supports_dir_fd", set())
    else:
        monkeypatch.delattr(os, capability)
    # Act
    with pytest.raises(RunStoreError) as failure:
        create_run_store(workspace, "corpus", RUN_ID)
    # Assert
    assert failure.value.category == "unsupported_platform"
    assert directory_entries(workspace) == {"corpus"}


@pytest.mark.parametrize("anchor", [Path("relative"), Path("/workspaces/../outside")])
def test_ambiguous_workspace_anchor_is_rejected(anchor: Path) -> None:
    # Arrange
    source = "corpus"
    # Act
    with pytest.raises(RunStoreError) as failure:
        create_run_store(anchor, source, RUN_ID)
    # Assert
    assert failure.value.category == "invalid_path"


@pytest.mark.parametrize("source", ["missing", "corpus/source.txt"])
def test_non_directory_sources_do_not_create_output(tmp_path: Path, source: str) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    # Act
    with pytest.raises(RunStoreError):
        create_run_store(workspace, source, RUN_ID)
    # Assert
    assert directory_entries(workspace) == {"corpus"}


@pytest.mark.parametrize(
    "source",
    [
        ".soulkiller-local",
        ".soulkiller-local/evaluation",
        ".soulkiller-local/evaluation/synthetic-run",
        ".soulkiller-local/evaluation/synthetic-run/inside",
    ],
)
def test_source_output_overlap_is_rejected_in_both_directions(tmp_path: Path, source: str) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    selected = workspace / source
    selected.mkdir(parents=True)
    (selected / "keep").write_bytes(b"Unchanged source.")
    before = {str(path.relative_to(workspace)) for path in workspace.rglob("*")}
    # Act
    with pytest.raises(RunStoreError) as failure:
        create_run_store(workspace, source, RUN_ID)
    # Assert
    assert failure.value.category == "source_overlap"
    assert {str(path.relative_to(workspace)) for path in workspace.rglob("*")} == before
    assert (selected / "keep").read_bytes() == b"Unchanged source."


def test_read_only_reopen_does_not_create_missing_output(tmp_path: Path) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    # Act
    with pytest.raises(RunStoreError):
        open_run_store(workspace, "corpus", RUN_ID)
    # Assert
    assert directory_entries(workspace) == {"corpus"}


def test_read_only_reopen_refuses_a_symlink_run(tmp_path: Path) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    run = run_directory(workspace)
    run.parent.mkdir(parents=True)
    run.symlink_to(workspace / "corpus", target_is_directory=True)
    # Act
    with pytest.raises(RunStoreError) as failure:
        open_run_store(workspace, "corpus", RUN_ID)
    # Assert
    assert failure.value.category == "unsafe_path"
    assert directory_entries(workspace / "corpus") == {"source.txt"}


@pytest.mark.parametrize(
    "direction", ["source-aliases-local", "evaluation-aliases-source-ancestor"]
)
def test_descriptor_identity_aliases_reject_overlap_before_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, direction: str
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    evaluation = run_directory(workspace).parent
    evaluation.mkdir(parents=True)
    source = workspace / "corpus"
    if direction == "source-aliases-local":
        alias = source
        replacement = evaluation.parent.stat()
        selected = "corpus"
    else:
        (source / "nested").mkdir()
        alias = evaluation
        replacement = source.stat()
        selected = "corpus/nested"
    original_fstat = os.fstat
    before = {str(path.relative_to(workspace)) for path in workspace.rglob("*")}

    def aliased_fstat(descriptor: int) -> os.stat_result:
        if os.readlink(f"/proc/self/fd/{descriptor}") == str(alias):
            return replacement
        return original_fstat(descriptor)

    monkeypatch.setattr(os, "fstat", aliased_fstat)
    # Act
    with pytest.raises(RunStoreError) as failure:
        create_run_store(workspace, selected, RUN_ID)
    # Assert
    assert failure.value.category == "source_overlap"
    assert {str(path.relative_to(workspace)) for path in workspace.rglob("*")} == before


@pytest.mark.parametrize("capability", ["follow-link", "follow-stat", "fsync"])
def test_missing_sync_or_no_follow_semantics_do_not_create_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capability: str
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    if capability == "fsync":
        monkeypatch.setattr(os, "fsync", None)
    else:
        unsupported = os.link if capability == "follow-link" else os.stat
        monkeypatch.setattr(
            os, "supports_follow_symlinks", os.supports_follow_symlinks - {unsupported}
        )
    # Act
    with pytest.raises(RunStoreError) as failure:
        create_run_store(workspace, "corpus", RUN_ID)
    # Assert
    assert failure.value.category == "unsupported_platform"
    assert directory_entries(workspace) == {"corpus"}


@pytest.mark.parametrize("operation", ["open", "mkdir", "link", "unlink", "stat"])
def test_each_required_descriptor_operation_is_checked_before_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    unsupported = getattr(os, operation)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd - {unsupported})
    # Act
    with pytest.raises(RunStoreError) as failure:
        create_run_store(workspace, "corpus", RUN_ID)
    # Assert
    assert failure.value.category == "unsupported_platform"
    assert directory_entries(workspace) == {"corpus"}


def test_run_replaced_by_symlink_before_reopen_is_not_followed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("original", b"Original synthetic bytes.")
    run = run_directory(workspace)
    original_acquire = run_store_paths._acquire_leaf

    def replaced_acquire(parent: int, name: str, *, create: bool) -> int:
        run.rename(run.with_name("original-run"))
        run.symlink_to(workspace / "corpus", target_is_directory=True)
        return original_acquire(parent, name, create=create)

    monkeypatch.setattr(run_store_paths, "_acquire_leaf", replaced_acquire)
    # Act
    with pytest.raises(RunStoreError) as failure:
        open_run_store(workspace, "corpus", RUN_ID)
    # Assert
    assert failure.value.category == "unsafe_path"
    assert directory_entries(workspace / "corpus") == {"source.txt"}
    assert (run.with_name("original-run") / "original").is_file()
