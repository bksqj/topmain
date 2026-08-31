"""Referral program: stats + personal deep-link generation."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from .. import texts
from ..callbacks import Nav
from ..config import get_settings
from ..db import repo
from ..keyboards import inline
from ..utils import edit_screen

router = Router(name="referral")
_settings = get_settings()


@router.callback_query(Nav.filter(F.to == "referral"))
async def to_referral(call: CallbackQuery, session: AsyncSession) -> None:
    user, _ = await repo.get_or_create_user(
        session, call.from_user.id, call.from_user.username
    )
    stat = user.referral_stat
    text = texts.referral_stats(
        invited=stat.invited_count if stat else 0,
        paid_count=stat.total_paid_count if stat else 0,
        paid_amount=stat.total_paid_amount if stat else 0.0,
    )
    await edit_screen(call, text, inline.referral_menu())
    await call.answer()


@router.callback_query(Nav.filter(F.to == "ref_create"))
async def create_code(call: CallbackQuery) -> None:
    link = f"https://t.me/{_settings.bot_username}?start=ref_{call.from_user.id}"
    await edit_screen(call, texts.referral_code(link), inline.referral_code_menu(link))
    await call.answer()
