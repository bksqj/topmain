"""Custom emoji icons for inline buttons (Bot API 9.4 `icon_custom_emoji_id`).

Icons render only if the bot OWNER has an active Telegram Premium subscription
(or the bot purchased usernames on Fragment). Without that — or with an empty
id — buttons fall back to a plain leading emoji, so the bot works everywhere.

How to fill the ids:
  • send the custom emoji in a chat, then read the message's `custom_emoji`
    entity (field `custom_emoji_id`), or use a helper bot such as
    @Getcustomemojibot / @idstickerbot;
  • put them here in DEFAULT_ICONS, or supply the CUSTOM_EMOJI_IDS env var as
    JSON, e.g. CUSTOM_EMOJI_IDS={"menu.cabinet":"5368324170671202286"}.
Env values override the defaults below.
"""
from __future__ import annotations

from .config import get_settings

# Semantic key -> custom_emoji_id (digits as string). Empty = plain fallback.
DEFAULT_ICONS: dict[str, str] = {
    "menu.cabinet": "",
    "menu.referral": "",
    "menu.help": "",
    "menu.about": "",
    "cabinet.subscription": "",
    "cabinet.key": "",
    "buy": "",
    "help.setup": "",
    "help.faq": "",
    "help.support": "",
    "about.rules": "",
    "about.refund": "",
    "about.locations": "",
    "about.tariffs": "",
    "nav.back": "",
}


def _load() -> dict[str, str]:
    icons = dict(DEFAULT_ICONS)
    icons.update(get_settings().custom_emoji_ids)
    return icons


_ICONS = _load()


def icon(key: str) -> str | None:
    """Return the custom_emoji_id for a slot, or None to use the text fallback."""
    return _ICONS.get(key) or None
