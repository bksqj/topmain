"""/start, main menu, and generic navigation to top-level screens."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from .. import texts
from ..callbacks import Nav
from ..config import get_settings
from ..db import repo
from ..keyboards import inline
from ..utils import edit_screen

router = Router(name="start")
_settings = get_settings()


def _parse_start_payload(command: CommandObject | None) -> int | None:
    """Extract a referrer telegram_id from a `ref_<id>` deep-link payload."""
    if command is None or not command.args:
        return None
    arg = command.args.strip()
    if arg.startswith("ref_"):
        rest = arg[4:]
        if rest.isdigit():
            return int(rest)
    return None


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await state.clear()
    referred_by = _parse_start_payload(command)
    await repo.get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        referred_by=referred_by,
    )
    await message.answer(texts.MAIN_MENU, reply_markup=inline.main_menu())


@router.callback_query(Nav.filter(F.to == "main"))
async def to_main(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await edit_screen(call, texts.MAIN_MENU, inline.main_menu())
    await call.answer()


@router.callback_query(Nav.filter(F.to == "help"))
async def to_help(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await edit_screen(call, texts.HELP, inline.help_menu())
    await call.answer()


@router.callback_query(Nav.filter(F.to == "about"))
async def to_about(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await edit_screen(call, texts.ABOUT, inline.about_menu())
    await call.answer()
