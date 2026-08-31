"""Fetch custom_emoji_id values for a Telegram emoji set.

Run this on a machine that can reach Telegram (NOT the cloud sandbox — there
api.telegram.org is blocked). Standard library only, no dependencies.

    # Linux / macOS
    BOT_TOKEN=123:abc python tools/fetch_emoji_ids.py pictograms_adaptive

    # Windows (PowerShell)
    $env:BOT_TOKEN="123:abc"; python tools/fetch_emoji_ids.py pictograms_adaptive

The set name is the part after t.me/addemoji/ in the link. The script prints
every emoji in the set with its id, plus a ready-to-paste CUSTOM_EMOJI_IDS
line where our button slots are matched to ids by their base emoji.

getStickerSet is a public read — no Telegram Premium needed just to read ids
(Premium is only required for the icons to actually render on buttons).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

# Button slot -> base emoji used as the plain fallback in keyboards.
# Keep in sync with bot/keyboards/inline.py.
SLOT_FALLBACK: dict[str, str] = {
    "menu.cabinet": "👤",
    "menu.referral": "👥",
    "menu.help": "🎧",
    "menu.about": "ℹ️",
    "cabinet.subscription": "⚡",
    "cabinet.key": "🔗",
    "buy": "✨",
    "help.setup": "⚙️",
    "help.faq": "❓",
    "help.support": "💬",
    "about.rules": "📄",
    "about.refund": "📄",
    "about.locations": "📍",
    "about.tariffs": "🏷️",
    "nav.back": "🔙",
}


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        sys.exit("Set the BOT_TOKEN environment variable first.")
    name = sys.argv[1] if len(sys.argv) > 1 else "pictograms_adaptive"

    url = f"https://api.telegram.org/bot{token}/getStickerSet?name={name}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.load(resp)
    except Exception as exc:  # noqa: BLE001
        sys.exit(f"Request failed: {exc}")

    if not data.get("ok"):
        sys.exit(f"Telegram error: {data}")

    stickers = data["result"]["stickers"]
    print(f"set: {name} — {len(stickers)} emoji\n")

    by_emoji: dict[str, str] = {}
    for s in stickers:
        emo = s.get("emoji", "")
        cid = s.get("custom_emoji_id", "")
        print(f"{emo}\t{cid}")
        by_emoji.setdefault(emo, cid)

    suggestion = {
        slot: by_emoji[base]
        for slot, base in SLOT_FALLBACK.items()
        if base in by_emoji
    }
    print("\n--- Paste this line into .env ---")
    print("CUSTOM_EMOJI_IDS=" + json.dumps(suggestion, ensure_ascii=False))

    missing = [s for s in SLOT_FALLBACK if s not in suggestion]
    if missing:
        print(
            "\nNo base-emoji match in this set for: "
            + ", ".join(missing)
            + "\nPick ids for these manually from the list above."
        )


if __name__ == "__main__":
    main()
