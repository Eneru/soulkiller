"""Real Linux filesystem boundaries with deterministic replacement/error probes."""

import errno
import os
import sys
from pathlib import Path

import pytest

from soulkiller_text import confined_files
from soulkiller_text.confined_files import corpus_descriptor, read_confined
from soulkiller_text.corpus_error import CorpusError
from soulkiller_text.load_corpus import load_corpus

from .filesystem_fixtures import DEFAULT_SOURCE, SOURCE_PATH, write_corpus


@pytest.mark.parametrize("position", ["workspace", "corpus", "parent", "leaf", "manifest"])
def test_symlinks_at_every_input_boundary_are_rejected(tmp_path: Path, position: str) -> None:
    # Arrange
    workspace = tmp_path / "workspace"
    corpus = write_corpus(workspace)
    selected = {
        "workspace": workspace,
        "corpus": corpus,
        "parent": corpus / "nested",
        "leaf": corpus / SOURCE_PATH,
        "manifest": corpus / "manifest.json",
    }[position]
    original = selected.with_name(selected.name + "-original")
    selected.rename(original)
    selected.symlink_to(original, target_is_directory=original.is_dir())
    # Act
    with pytest.raises(CorpusError) as failure:
        load_corpus(workspace, "corpus")
    # Assert
    assert failure.value.category == "unsafe_file"


@pytest.mark.parametrize("kind", ["directory", "fifo", "hardlink"])
def test_nonregular_or_multiply_linked_sources_are_rejected_before_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    # Arrange
    corpus = write_corpus(tmp_path)
    path = corpus / SOURCE_PATH
    if kind == "hardlink":
        os.link(path, corpus / "second-link")
    else:
        path.unlink()
        if kind == "directory":
            path.mkdir()
        else:
            os.mkfifo(path)
    reads: list[int] = []

    def forbidden_read(descriptor: int, count: int) -> bytes:
        reads.append(descriptor)
        raise AssertionError("Unsafe content must not be read.")

    # Act
    with corpus_descriptor(tmp_path, "corpus") as root:
        monkeypatch.setattr(os, "read", forbidden_read)
        with pytest.raises(CorpusError) as failure:
            read_confined(root, SOURCE_PATH, 100)
    # Assert
    assert failure.value.category == "unsafe_file"
    assert reads == []


@pytest.mark.parametrize("source,accepted", [(b"abcd", True), (b"abcde", False)])
def test_byte_limit_accepts_exact_boundary_and_rejects_one_more(
    tmp_path: Path, source: bytes, accepted: bool
) -> None:
    # Arrange
    write_corpus(tmp_path, source)
    # Act
    with corpus_descriptor(tmp_path, "corpus") as root:
        if accepted:
            actual = read_confined(root, SOURCE_PATH, 4)
        else:
            with pytest.raises(CorpusError) as failure:
                read_confined(root, SOURCE_PATH, 4)
    # Assert
    if accepted:
        assert actual == b"abcd"
    else:
        assert failure.value.category == "input_too_large"


@pytest.mark.parametrize(
    "before_open", [True, False], ids=["before-acquisition", "after-acquisition"]
)
def test_replaced_leaf_never_reads_symlink_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, before_open: bool
) -> None:
    # Arrange
    corpus = write_corpus(tmp_path)
    path = corpus / SOURCE_PATH
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"Replacement must not be read.")
    original_open = confined_files._open_leaf

    def replaced_open(parent: int, name: str) -> int:
        if name != "notes.txt":
            return original_open(parent, name)
        descriptor = None if before_open else original_open(parent, name)
        path.rename(corpus / "original.txt")
        path.symlink_to(outside)
        return original_open(parent, name) if descriptor is None else descriptor

    monkeypatch.setattr(confined_files, "_open_leaf", replaced_open)
    # Act
    if before_open:
        with pytest.raises(CorpusError) as failure:
            load_corpus(tmp_path, "corpus")
    else:
        loaded = load_corpus(tmp_path, "corpus")
    # Assert
    if before_open:
        assert failure.value.category == "unsafe_file"
    else:
        assert loaded[0].source == DEFAULT_SOURCE
    assert outside.read_bytes() == b"Replacement must not be read."


@pytest.mark.parametrize(
    "before_open", [True, False], ids=["before-acquisition", "after-acquisition"]
)
def test_replaced_parent_never_traverses_replacement_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, before_open: bool
) -> None:
    # Arrange
    corpus = write_corpus(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "notes.txt").write_bytes(b"Replacement must not be read.")
    original_open = confined_files._open_directory

    def replaced_open(parent: int, name: str) -> int:
        if name != "nested":
            return original_open(parent, name)
        descriptor = None if before_open else original_open(parent, name)
        (corpus / "nested").rename(corpus / "original-directory")
        (corpus / "nested").symlink_to(outside, target_is_directory=True)
        return original_open(parent, name) if descriptor is None else descriptor

    monkeypatch.setattr(confined_files, "_open_directory", replaced_open)
    # Act
    if before_open:
        with pytest.raises(CorpusError) as failure:
            load_corpus(tmp_path, "corpus")
    else:
        loaded = load_corpus(tmp_path, "corpus")
    # Assert
    if before_open:
        assert failure.value.category == "unsafe_file"
    else:
        assert loaded[0].source == DEFAULT_SOURCE


@pytest.mark.parametrize("mutation", ["append", "same-size", "hardlink"])
def test_descriptor_changes_during_reads_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    # Arrange
    corpus = write_corpus(tmp_path, b"abcd")
    path = corpus / SOURCE_PATH
    original_read = os.read
    changed = False

    def mutating_read(descriptor: int, count: int) -> bytes:
        nonlocal changed
        if not changed:
            changed = True
            if mutation == "append":
                with path.open("ab") as stream:
                    stream.write(b"ef")
            elif mutation == "same-size":
                path.write_bytes(b"wxyz")
            else:
                os.link(path, corpus / "new-link")
        return original_read(descriptor, count)

    # Act
    with corpus_descriptor(tmp_path, "corpus") as root:
        monkeypatch.setattr(os, "read", mutating_read)
        with pytest.raises(CorpusError) as failure:
            read_confined(root, SOURCE_PATH, 4)
    # Assert
    expected = "input_too_large" if mutation == "append" else "source_changed"
    assert failure.value.category == expected


def test_short_reads_are_accumulated_without_assuming_full_chunks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    write_corpus(tmp_path)
    original_read = os.read

    def short_read(descriptor: int, count: int) -> bytes:
        return original_read(descriptor, min(count, 1))

    # Act
    with corpus_descriptor(tmp_path, "corpus") as root:
        monkeypatch.setattr(os, "read", short_read)
        source = read_confined(root, SOURCE_PATH, 100)
    # Assert
    assert source == DEFAULT_SOURCE


def test_read_failure_closes_acquired_descriptors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    write_corpus(tmp_path)
    acquired: list[int] = []
    original_open = confined_files._open_leaf

    def tracked_open(parent: int, name: str) -> int:
        descriptor = original_open(parent, name)
        acquired.append(descriptor)
        return descriptor

    def failed_read(descriptor: int, count: int) -> bytes:
        raise OSError(errno.EIO, "synthetic read failure")

    monkeypatch.setattr(confined_files, "_open_leaf", tracked_open)
    # Act
    with corpus_descriptor(tmp_path, "corpus") as root:
        monkeypatch.setattr(os, "read", failed_read)
        with pytest.raises(CorpusError) as failure:
            read_confined(root, SOURCE_PATH, 100)
    # Assert
    assert failure.value.category == "source_unavailable"
    assert len(acquired) == 1
    with pytest.raises(OSError) as closed:
        os.fstat(acquired[0])
    assert closed.value.errno == errno.EBADF


def test_interrupted_parent_close_does_not_leak_acquired_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    write_corpus(tmp_path)
    acquired: list[int] = []
    original_open = confined_files._open_directory
    original_close = os.close
    interrupted = False

    def tracked_open(parent: int, name: str) -> int:
        descriptor = original_open(parent, name)
        acquired.append(descriptor)
        return descriptor

    def interrupted_close(descriptor: int) -> None:
        nonlocal interrupted
        original_close(descriptor)
        if not interrupted:
            interrupted = True
            raise OSError(errno.EINTR, "synthetic close interruption")

    monkeypatch.setattr(confined_files, "_open_directory", tracked_open)
    monkeypatch.setattr(os, "close", interrupted_close)
    # Act
    with pytest.raises(CorpusError) as failure:
        load_corpus(tmp_path, "corpus")
    # Assert
    assert failure.value.category == "source_unavailable"
    assert acquired
    for descriptor in acquired:
        with pytest.raises(OSError) as closed:
            os.fstat(descriptor)
        assert closed.value.errno == errno.EBADF


@pytest.mark.parametrize("capability", ["platform", "flags", "dir-fd"])
def test_missing_descriptor_capabilities_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capability: str
) -> None:
    # Arrange
    write_corpus(tmp_path)
    if capability == "platform":
        monkeypatch.setattr(sys, "platform", "win32")
    elif capability == "flags":
        monkeypatch.delattr(os, "O_NOFOLLOW")
    else:
        monkeypatch.setattr(os, "supports_dir_fd", set())
    # Act
    with pytest.raises(CorpusError) as failure:
        load_corpus(tmp_path, "corpus")
    # Assert
    assert failure.value.category == "unsupported_platform"


@pytest.mark.parametrize("anchor", [Path("relative"), Path("/workspaces/../outside")])
def test_invalid_workspace_anchors_are_rejected(anchor: Path) -> None:
    # Arrange
    corpus_path = "corpus"
    # Act
    with pytest.raises(CorpusError) as failure:
        load_corpus(anchor, corpus_path)
    # Assert
    assert failure.value.category == "invalid_path"


def test_initial_oversize_is_rejected_without_content_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    write_corpus(tmp_path, b"abcde")
    reads: list[int] = []

    def forbidden_read(descriptor: int, count: int) -> bytes:
        reads.append(descriptor)
        raise AssertionError("An already oversized file must not be read.")

    # Act
    with corpus_descriptor(tmp_path, "corpus") as root:
        monkeypatch.setattr(os, "read", forbidden_read)
        with pytest.raises(CorpusError) as failure:
            read_confined(root, SOURCE_PATH, 4)
    # Assert
    assert failure.value.category == "input_too_large"
    assert reads == []


def test_unexpected_early_eof_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    write_corpus(tmp_path)
    # Act
    with corpus_descriptor(tmp_path, "corpus") as root:
        monkeypatch.setattr(os, "read", lambda descriptor, count: b"")
        with pytest.raises(CorpusError) as failure:
            read_confined(root, SOURCE_PATH, 100)
    # Assert
    assert failure.value.category == "source_changed"
