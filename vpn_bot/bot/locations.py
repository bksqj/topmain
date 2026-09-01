"""Catalog of VPN locations.

In production this can be fetched from Remnawave (internal squads); here it is
a static list that mirrors the panel. `tag` is a unique internal slug — in
production set it to the squad UUID so `services.provisioning.switch_location`
can assign it to the user.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    tag: str  # unique internal slug
    flag: str  # flag emoji
    name: str  # full label after the flag, e.g. "Poland | Warsaw | HY2"

    def label(self) -> str:
        return f"{self.flag} {self.name}"


# (flag, name) pairs in display order — mirrors the Remnawave panel.
_RAW: list[tuple[str, str]] = [
    ("🇵🇱", "Poland | Warsaw"),
    ("🇵🇱", "Poland | Warsaw | HY2"),
    ("🇳🇱", "Netherlands | Amsterdam"),
    ("🇳🇱", "Netherlands | Amsterdam | HY2"),
    ("🇩🇪", "Germany | Frankfurt"),
    ("🇩🇪", "Germany | Frankfurt | HY2"),
    ("🇦🇹", "Austria | Vienna"),
    ("🇦🇹", "Austria | Vienna | HY2"),
    ("🇫🇮", "Finland | Helsinki"),
    ("🇫🇮", "Finland | Helsinki | HY2"),
    ("🇹🇷", "Turkey | Istanbul"),
    ("🇹🇷", "Turkey | Istanbul | HY2"),
    ("🇷🇺", "Russia | Moscow"),
    ("🇷🇺", "Russia | Moscow | HY2"),
    ("🇷🇺", "Russia | Moscow-2"),
    ("🇷🇺", "Russia | Moscow-2 | HY2"),
    ("🇺🇸", "USA | Manassas"),
    ("🇺🇸", "USA | Manassas | HY2"),
    ("🇺🇸", "USA | Chicago"),
    ("🇺🇸", "USA | Chicago | HY2"),
    ("🇷🇺", "Russia-2 | WL | x5 | HY2"),
    ("🇷🇺", "Russia-3 | WL | x5"),
    ("🇷🇺", "Russia-4 | WL | x20"),
    ("🇷🇺", "Russia-5 | WL | x20"),
    ("🇷🇺", "Russia-6 | WL | x20"),
    ("🇩🇪", "Germany-2 | WL | x5 | HY2"),
    ("🇩🇪", "Germany-3 | WL | x5"),
    ("🇩🇪", "Germany-4 | WL | x20"),
    ("🇩🇪", "Germany-5 | WL | x20"),
    ("🇩🇪", "Germany-6 | WL | x20"),
    ("🇺🇸", "USA-2 | WL | x5 | HY2"),
    ("🇺🇸", "USA-3 | WL | x5"),
    ("🇺🇸", "USA-4 | WL | x20"),
    ("🇺🇸", "USA-5 | WL | x20"),
    ("🇺🇸", "USA-6 | WL | x20"),
]


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


FALLBACK_LOCATIONS: list[Location] = [
    Location(tag=_slug(name), flag=flag, name=name) for flag, name in _RAW
]

LOCATIONS_BY_TAG: dict[str, Location] = {loc.tag: loc for loc in FALLBACK_LOCATIONS}


def full_list_text() -> str:
    """Read-only block for «О нас → Локации» with tree glyphs and footnotes."""
    lines = ["<b>🌍 Локации:</b>", ""]
    last = len(FALLBACK_LOCATIONS) - 1
    for i, loc in enumerate(FALLBACK_LOCATIONS):
        glyph = "└" if i == last else "├"
        lines.append(f"{glyph} {loc.label()}")
    lines.append("")
    lines.append(
        "<i>*Все локации доступны на любом тарифе.\n"
        "**Локации могут меняться.</i>"
    )
    return "\n".join(lines)
