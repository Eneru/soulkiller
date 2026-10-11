"""Verify the offline topology supplied externally, without importing the package."""

MAX_NETWORK_TABLE_BYTES = 4096
_HEADERS = (
    "Inter-|Receive|Transmit",
    "face|bytespacketserrsdropfifoframecompressedmulticast|"
    "bytespacketserrsdropfifocollscarriercompressed",
)


def _loopback_table(raw: bytes) -> bool:
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeDecodeError:
        return False
    if len(lines) != 3:
        return False
    if tuple("".join(line.split()) for line in lines[:2]) != _HEADERS:
        return False
    row = lines[2].split(":")
    if len(row) != 2 or row[0].strip() != "lo":
        return False
    counters = row[1].split()
    return len(counters) == 16 and all(counter.isdecimal() for counter in counters)


def has_offline_topology() -> bool:
    """Fail closed unless bounded kernel inspection reports exactly loopback."""
    try:
        with open("/proc/self/net/dev", "rb") as stream:
            raw = stream.read(MAX_NETWORK_TABLE_BYTES + 1)
    except OSError:
        return False
    return len(raw) <= MAX_NETWORK_TABLE_BYTES and _loopback_table(raw)
