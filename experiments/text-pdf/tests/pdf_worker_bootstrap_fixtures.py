"""Safe standalone bootstrap doubles leave pytest's own limits untouched."""

import sys
from types import SimpleNamespace

import pytest

LIMIT = 64 * 1024**2


def install_guard_doubles(
    monkeypatch: pytest.MonkeyPatch,
    events: list[str],
    *,
    memory_supported: bool = True,
    network_supported: bool = True,
) -> None:
    """Observe guard order through independent standalone collaborators."""

    def memory_guard(limit: int) -> bool:
        events.append("memory")
        return memory_supported

    def network_guard() -> bool:
        events.append("network")
        return network_supported

    monkeypatch.setitem(
        sys.modules,
        "worker_bootstrap",
        SimpleNamespace(
            MIN_ADDRESS_SPACE_BYTES=LIMIT,
            MAX_ADDRESS_SPACE_BYTES=2 * 1024**3,
            UNSUPPORTED_EXIT=3,
            MEMORY_FAILURE_EXIT=4,
            _configure_address_space=memory_guard,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "worker_network_guard",
        SimpleNamespace(
            has_offline_topology=network_guard,
        ),
    )
