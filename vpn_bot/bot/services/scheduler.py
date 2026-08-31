"""APScheduler jobs: notify users 3 days and 1 day before expiry."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from .. import texts
from ..callbacks import Nav
from ..db.engine import async_session_factory
from ..db.models import Subscription, User

logger = logging.getLogger(__name__)


def _renew_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="✨ Продлить", callback_data=Nav(to="buy"))
    kb.adjust(1)
    return kb.as_markup()


async def _notify_window(bot: Bot, days: int) -> None:
    """Notify users whose subscription expires in ~`days` days (24h window)."""
    now = datetime.utcnow()
    window_start = now + timedelta(days=days)
    window_end = window_start + timedelta(days=1)
    async with async_session_factory() as session:
        stmt = (
            select(Subscription, User)
            .join(User, User.id == Subscription.user_id)
            .where(
                Subscription.expires_at >= window_start,
                Subscription.expires_at < window_end,
            )
        )
        rows = (await session.execute(stmt)).all()
    for sub, user in rows:
        try:
            await bot.send_message(
                user.telegram_id,
                texts.EXPIRY_REMINDER.format(days=days),
                reply_markup=_renew_keyboard(),
            )
        except Exception:  # pragma: no cover
            logger.warning("expiry reminder failed for %s", user.telegram_id)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    # run daily at 10:00 UTC
    scheduler.add_job(_notify_window, "cron", hour=10, minute=0, args=[bot, 3])
    scheduler.add_job(_notify_window, "cron", hour=10, minute=5, args=[bot, 1])
    return scheduler
