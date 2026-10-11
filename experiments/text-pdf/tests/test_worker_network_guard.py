"""Bounded kernel interface inspection fails closed without contacting a network."""

import io

import pytest

from soulkiller_text.worker_network_guard import has_offline_topology

from .pdf_worker_fixtures import CONNECTED_DEVICE, LOOPBACK_DEVICE, NETWORK_HEADERS


def test_loopback_only_kernel_topology_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    requested: list[tuple[object, ...]] = []

    def kernel_table(*args: object) -> io.BytesIO:
        requested.append(args)
        return io.BytesIO((NETWORK_HEADERS + LOOPBACK_DEVICE).encode("ascii"))

    monkeypatch.setattr("builtins.open", kernel_table)
    # Act
    supported = has_offline_topology()
    # Assert
    assert supported
    assert requested == [("/proc/self/net/dev", "rb")]


@pytest.mark.parametrize(
    "table",
    [
        NETWORK_HEADERS + LOOPBACK_DEVICE + CONNECTED_DEVICE,
        NETWORK_HEADERS + CONNECTED_DEVICE,
        NETWORK_HEADERS,
        NETWORK_HEADERS + LOOPBACK_DEVICE + LOOPBACK_DEVICE,
        NETWORK_HEADERS + "lo: " + " ".join(["0"] * 15) + "\n",
        NETWORK_HEADERS + "lo: " + " ".join(["0"] * 17) + "\n",
        NETWORK_HEADERS + "lo: -1 " + " ".join(["0"] * 15) + "\n",
        NETWORK_HEADERS + "lo: 1.0 " + " ".join(["0"] * 15) + "\n",
        NETWORK_HEADERS + "lo " + " ".join(["0"] * 16) + "\n",
        "unrecognized header\n" + NETWORK_HEADERS.splitlines()[1] + "\n" + LOOPBACK_DEVICE,
        NETWORK_HEADERS.splitlines()[0] + "\nunrecognized fields\n" + LOOPBACK_DEVICE,
        "x" * 4097,
    ],
)
def test_connected_unrecognized_or_oversized_topology_is_rejected(
    table: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    monkeypatch.setattr("builtins.open", lambda *args: io.BytesIO(table.encode("ascii")))
    # Act
    supported = has_offline_topology()
    # Assert
    assert not supported


def test_nonascii_kernel_table_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    monkeypatch.setattr("builtins.open", lambda *args: io.BytesIO(b"\xff"))
    # Act
    supported = has_offline_topology()
    # Assert
    assert not supported


def test_missing_kernel_view_is_explicitly_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    def unavailable(*args: object) -> io.BytesIO:
        raise OSError("private synthetic kernel diagnostic")

    monkeypatch.setattr("builtins.open", unavailable)
    # Act
    supported = has_offline_topology()
    # Assert
    assert not supported
