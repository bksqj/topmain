"""Help section: setup wizard (FSM), FAQ (paginated), tech support."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from .. import texts
from ..callbacks import FaqCB, Nav, PageNav, SetupCB
from ..config import get_settings
from ..content import DEVICE_TYPES, FAQ_BY_KEY, FAQ_ITEMS, get_app
from ..keyboards import inline
from ..keyboards.pagination import paginate
from ..states import SetupWizard, SupportFlow
from ..utils import edit_screen

router = Router(name="help")
logger = logging.getLogger(__name__)
_settings = get_settings()


# ---- Setup wizard --------------------------------------------------------

@router.callback_query(Nav.filter(F.to == "setup"))
async def setup_start(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SetupWizard.device)
    await edit_screen(call, texts.SETUP_DEVICE, inline.setup_device_menu())
    await call.answer()


@router.callback_query(SetupCB.filter(F.step == "device"))
async def setup_pick_device(
    call: CallbackQuery, callback_data: SetupCB, state: FSMContext
) -> None:
    device = callback_data.value
    if device not in DEVICE_TYPES:
        await call.answer(texts.ERROR_GENERIC, show_alert=True)
        return
    await state.update_data(device=device)
    await state.set_state(SetupWizard.app)
    await edit_screen(call, texts.SETUP_APP, inline.setup_app_menu(device))
    await call.answer()


@router.callback_query(SetupCB.filter(F.step == "app"))
async def setup_pick_app(
    call: CallbackQuery, callback_data: SetupCB, state: FSMContext
) -> None:
    data = await state.get_data()
    device = data.get("device", "phone")
    app = get_app(device, callback_data.value)
    if app is None:
        await call.answer(texts.ERROR_GENERIC, show_alert=True)
        return
    await state.update_data(app=app.key)
    await state.set_state(SetupWizard.install)
    await edit_screen(
        call,
        texts.setup_install(app.name, app.links),
        inline.setup_install_menu(),
    )
    await call.answer()


@router.callback_query(SetupCB.filter(F.step == "next"))
async def setup_next(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    device = data.get("device", "phone")
    app = get_app(device, data.get("app", ""))
    if app is None:
        await setup_start(call, state)
        return
    await state.set_state(SetupWizard.import_key)
    await edit_screen(
        call,
        texts.setup_import(app.name, app.import_instructions),
        inline.setup_import_menu(),
    )
    await call.answer()


# ---- FAQ -----------------------------------------------------------------

@router.callback_query(PageNav.filter(F.list == "faq"))
async def faq_page(call: CallbackQuery, callback_data: PageNav) -> None:
    page = paginate(FAQ_ITEMS, callback_data.page)
    header = (
        "<b>❓ Ответы на вопросы</b>\n\nВыберите категорию:"
    )
    await edit_screen(call, header, inline.faq_menu(page))
    await call.answer()


@router.callback_query(FaqCB.filter())
async def faq_item(call: CallbackQuery, callback_data: FaqCB) -> None:
    item = FAQ_BY_KEY.get(callback_data.key)
    if item is None:
        await call.answer(texts.ERROR_GENERIC, show_alert=True)
        return
    await edit_screen(call, item.answer, inline.faq_item_menu())
    await call.answer()


# ---- Support -------------------------------------------------------------

@router.callback_query(Nav.filter(F.to == "support"))
async def support(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    text = texts.SUPPORT.format(support=_settings.support_username)
    await edit_screen(call, text, inline.support_menu())
    await call.answer()


@router.callback_query(Nav.filter(F.to == "support_write"))
async def support_write(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SupportFlow.waiting_message)
    await edit_screen(call, texts.SUPPORT_ASK, inline.support_menu())
    await call.answer()


@router.message(SupportFlow.waiting_message, F.text)
async def support_receive(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    await state.clear()
    # forward to all admins
    for admin_id in _settings.admin_ids:
        try:
            await message.bot.send_message(
                admin_id,
                f"💬 <b>Сообщение в поддержку</b>\n"
                f"От: @{message.from_user.username or '—'} "
                f"(id <code>{message.from_user.id}</code>)\n\n"
                f"{message.text}",
            )
        except Exception:  # pragma: no cover
            logger.warning("failed to deliver support msg to admin %s", admin_id)
    await message.answer(texts.SUPPORT_SENT, reply_markup=inline.help_menu())
