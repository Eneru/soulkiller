"""One independent reference quote and its observed resolving location."""

from dataclasses import dataclass

Location = tuple[int | None, int | None, int | None]


@dataclass(frozen=True)
class FactScore:
    """Locations are (page, start, end); absent expected offsets mean page-only checks."""

    quote: str
    expected_location: Location
    observed_location: Location | None
    location_matched: bool
