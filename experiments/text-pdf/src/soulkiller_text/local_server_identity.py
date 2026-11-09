"""Confirm the loopback listener belongs to the pinned server's direct child."""

import os
import socket
import sys
from pathlib import Path

from .dialogue_error import DialogueError
from .local_model_constants import SERVER_HOST, SERVER_PORT

MAX_TCP_TABLE_BYTES = 64 * 1024


def require_owned_listener(pid: int) -> None:
    """Match the Linux TCP listener inode to a descriptor held by the owned child.

    /proc/net/tcp exposes IPv4 addresses in native byte order and state 0A
    for LISTEN. Read only this container's namespace, before sending evidence.
    """
    try:
        with Path("/proc/net/tcp").open("rb") as table:
            raw = table.read(MAX_TCP_TABLE_BYTES + 1)
        if len(raw) > MAX_TCP_TABLE_BYTES:
            raise DialogueError("local_model_endpoint_unavailable")
        address = int.from_bytes(socket.inet_aton(SERVER_HOST), byteorder=sys.byteorder)
        endpoint = f"{address:08X}:{SERVER_PORT:04X}".encode("ascii")
        rows = [line.split() for line in raw.splitlines()[1:]]
        matches = [
            row[9] for row in rows if len(row) >= 10 and row[1] == endpoint and row[3] == b"0A"
        ]
        if len(matches) == 1:
            expected = f"socket:[{int(matches[0])}]"
            for descriptor in Path(f"/proc/{pid}/fd").iterdir():
                try:
                    if os.readlink(descriptor) == expected:
                        return
                except FileNotFoundError:
                    continue
    except (OSError, ValueError):
        raise DialogueError("local_model_endpoint_unavailable") from None
    raise DialogueError("local_model_endpoint_unavailable")
