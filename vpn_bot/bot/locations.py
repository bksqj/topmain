"""Static fallback catalog of VPN locations.

In production the list is usually fetched from Marzban (available inbounds /
nodes). This module provides a typed structure and a fallback list so the UI
works out of the box.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    tag: str  # unique node/inbound tag used in Marzban
    flag: str  # flag emoji
    country: str
    city: str
    extra: str | None = None  # e.g. "HY2"

    def label(self) -> str:
        parts = [f"{self.flag} {self.country}", self.city]
        if self.extra:
            parts.append(self.extra)
        return " | ".join(parts)


FALLBACK_LOCATIONS: list[Location] = [
    Location("pl-waw-1", "🇵🇱", "Poland", "Warsaw"),
    Location("pl-waw-hy2", "🇵🇱", "Poland", "Warsaw", "HY2"),
    Location("nl-ams-1", "🇳🇱", "Netherlands", "Amsterdam"),
    Location("de-fra-1", "🇩🇪", "Germany", "Frankfurt"),
    Location("fi-hel-1", "🇫🇮", "Finland", "Helsinki"),
    Location("se-sto-1", "🇸🇪", "Sweden", "Stockholm"),
    Location("us-nyc-1", "🇺🇸", "USA", "New York"),
    Location("tr-ist-1", "🇹🇷", "Turkey", "Istanbul"),
]

LOCATIONS_BY_TAG: dict[str, Location] = {loc.tag: loc for loc in FALLBACK_LOCATIONS}
