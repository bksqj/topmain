"""Finalize a paid order: provision VPN, credit referrer, notify buyer.

Shared by the YooKassa webhook and the manual 'I paid' check button so the
logic stays identical and idempotent.
"""
from __future__ import annotations

import logging

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from .. import texts
from ..db import repo
from ..db.models import Payment, User
from ..keyboards import inline
from ..plans import PLANS_BY_KEY
from .provisioning import provision_plan

logger = logging.getLogger(__name__)


async def finalize_payment(
    session: AsyncSession, payment: Payment, bot: Bot | None = None
) -> tuple[User | None, bool]:
    """Provision the subscription for a succeeded payment.

    Returns (user, newly_finalized). Safe to call twice: a payment already
    marked succeeded short-circuits without re-provisioning.
    """
    if payment.status == "succeeded":
        user = await repo.get_user_by_pk(session, payment.user_id)
        return user, False

    await repo.mark_payment_status(session, payment, "succeeded")
    user = await repo.get_user_by_pk(session, payment.user_id)
    if user is None:
        return None, False

    plan = PLANS_BY_KEY.get(payment.plan_key or "")
    if plan is not None:
        await provision_plan(session, user, plan)
    await repo.credit_referrer_payment(session, user, payment.amount)

    if bot is not None:
        await _notify_buyer(bot, user)
    return user, True


async def _notify_buyer(bot: Bot, user: User) -> None:
    sub = user.subscription
    url = sub.subscription_url if sub else ""
    text = texts.PAYMENT_SUCCESS + f"\n\n<code>{url}</code>"
    try:
        await bot.send_message(user.telegram_id, text, reply_markup=inline.key_menu())
    except Exception:  # pragma: no cover - user blocked the bot etc.
        logger.warning("could not notify buyer %s", user.telegram_id)
