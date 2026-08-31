"""Admin router: whitelist-gated stats, manual grant, broadcast."""
from __future__ import annotations

import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from .. import texts
from ..callbacks import AdminCB
from ..config import get_settings
from ..db import repo
from ..keyboards import inline
from ..services.provisioning import provision_manual
from ..states import AdminFlow
from ..utils import edit_screen

logger = logging.getLogger(__name__)
_settings = get_settings()


class IsAdmin(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return event.from_user is not None and event.from_user.id in _settings.admin_ids


router = Router(name="admin")
# every handler in this router requires admin membership
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(Command("admin"))
async def admin_entry(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.ADMIN_MENU, reply_markup=inline.admin_menu())


@router.callback_query(AdminCB.filter(F.action == "menu"))
async def admin_menu(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await edit_screen(call, texts.ADMIN_MENU, inline.admin_menu())
    await call.answer()


@router.callback_query(AdminCB.filter(F.action == "stats"))
async def admin_stats(call: CallbackQuery, session: AsyncSession) -> None:
    users = await repo.count_users(session)
    total = await repo.sum_payments(session)
    await edit_screen(
        call, texts.admin_stats(users, total), inline.admin_back_menu()
    )
    await call.answer()


# ---- Manual grant --------------------------------------------------------

@router.callback_query(AdminCB.filter(F.action == "grant"))
async def admin_grant_ask(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFlow.grant)
    await edit_screen(call, texts.ADMIN_GRANT_ASK, inline.admin_back_menu())
    await call.answer()


@router.message(AdminFlow.grant, F.text)
async def admin_grant_do(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    parts = message.text.split()
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        await message.answer(texts.ADMIN_GRANT_BAD)
        return
    tg_id, months = int(parts[0]), int(parts[1])
    await state.clear()
    user, _ = await repo.get_or_create_user(session, telegram_id=tg_id)
    await provision_manual(session, user, months=months)
    await message.answer(
        texts.ADMIN_GRANT_DONE.format(tg_id=tg_id, months=months),
        reply_markup=inline.admin_menu(),
    )


# ---- Broadcast -----------------------------------------------------------

@router.callback_query(AdminCB.filter(F.action == "broadcast"))
async def admin_broadcast_ask(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminFlow.broadcast)
    await edit_screen(call, texts.ADMIN_BROADCAST_ASK, inline.admin_back_menu())
    await call.answer()


@router.message(AdminFlow.broadcast, F.text)
async def admin_broadcast_do(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await state.clear()
    ids = await repo.all_user_telegram_ids(session)
    sent = failed = 0
    for tg_id in ids:
        try:
            await message.bot.send_message(tg_id, message.text)
            sent += 1
        except Exception:  # pragma: no cover
            failed += 1
        await asyncio.sleep(0.05)  # gentle rate-limit
    await message.answer(
        texts.admin_broadcast_done(sent, failed), reply_markup=inline.admin_menu()
    )
