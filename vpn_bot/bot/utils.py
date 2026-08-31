"""Small shared helpers."""
from __future__ import annotations

from datetime import datetime

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup


def time_remaining(expires_at: datetime | None) -> tuple[int, int, int]:
    """Return (days, hours, minutes) until `expires_at`, clamped at zero."""
    if expires_at is None:
        return 0, 0, 0
    delta = expires_at - datetime.utcnow()
    total_seconds = int(delta.total_seconds())
    if total_seconds <= 0:
        return 0, 0, 0
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    return days, hours, minutes


async def edit_screen(
    call: CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Edit the message in place, tolerating 'message is not modified'.

    If the current message is a photo (no text to edit), send fresh text
    instead so navigation still works after a QR photo was shown.
    """
    message = call.message
    if message is None:
        return
    try:
        if message.text is None and message.caption is not None:
            # message carries media; can't edit_text — send a new screen
            await message.answer(text, reply_markup=reply_markup)
            return
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc):
            return
        # e.g. can't edit media message as text -> fall back to a new message
        await message.answer(text, reply_markup=reply_markup)
