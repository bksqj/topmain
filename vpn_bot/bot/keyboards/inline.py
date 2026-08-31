"""Inline keyboard builders. Every screen is edited in place (see handlers)."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..callbacks import (
    AdminCB,
    FaqCB,
    KeyActionCB,
    LocationCB,
    Nav,
    PageNav,
    PayCheckCB,
    PlanCB,
    SetupCB,
)
from .. import emojis
from ..content import DEVICE_TYPES, SETUP_APPS
from ..locations import Location
from ..plans import Plan, discount_percent
from .pagination import Page

BACK = "🔙 Назад"


def _icon_btn(emoji: str, label: str, callback, icon_key: str) -> InlineKeyboardButton:
    """A button with a custom-emoji icon when configured, else a plain emoji.

    `callback` is a CallbackData instance (packed here).
    """
    icon_id = emojis.icon(icon_key)
    if icon_id:
        return InlineKeyboardButton(
            text=label, callback_data=callback.pack(), icon_custom_emoji_id=icon_id
        )
    return InlineKeyboardButton(text=f"{emoji} {label}", callback_data=callback.pack())


def _back_button(to: str) -> InlineKeyboardButton:
    icon_id = emojis.icon("nav.back")
    if icon_id:
        return InlineKeyboardButton(
            text="Назад", callback_data=Nav(to=to).pack(), icon_custom_emoji_id=icon_id
        )
    return InlineKeyboardButton(text=BACK, callback_data=Nav(to=to).pack())


# ---- Main menu -----------------------------------------------------------

def main_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(_icon_btn("👤", "Личный кабинет", Nav(to="cabinet"), "menu.cabinet"))
    kb.row(_icon_btn("👥", "Реферальная программа", Nav(to="referral"), "menu.referral"))
    kb.row(_icon_btn("🎧", "Помощь", Nav(to="help"), "menu.help"))
    kb.row(_icon_btn("ℹ️", "О нас", Nav(to="about"), "menu.about"))
    return kb.as_markup()


# ---- Cabinet -------------------------------------------------------------

def cabinet_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(_icon_btn("⚡", "Подписка", Nav(to="subscription"), "cabinet.subscription"))
    kb.row(_icon_btn("🔗", "Ключ", Nav(to="key"), "cabinet.key"))
    kb.row(_back_button("main"))
    return kb.as_markup()


def subscription_menu(is_trial: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if is_trial:
        kb.row(_icon_btn("✨", "Купить подписку", Nav(to="buy"), "buy"))
    else:
        kb.row(_icon_btn("🔄", "Продлить подписку", Nav(to="buy"), "buy"))
    kb.row(_back_button("cabinet"))
    return kb.as_markup()


def key_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📋 Скопировать ключ", callback_data=KeyActionCB(action="copy"))
    kb.button(text="🔳 QR-код", callback_data=KeyActionCB(action="qr"))
    kb.button(text="🔄 Перевыпустить ключ", callback_data=KeyActionCB(action="reissue"))
    kb.button(text="🌍 Локации", callback_data=PageNav(list="locations", page=1))
    kb.adjust(2, 1, 1)
    kb.row(_back_button("cabinet"))
    return kb.as_markup()


def key_no_sub_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✨ Купить подписку", callback_data=Nav(to="buy"))
    kb.adjust(1)
    kb.row(_back_button("cabinet"))
    return kb.as_markup()


def reissue_confirm_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="✅ Да, перевыпустить",
        callback_data=KeyActionCB(action="reissue_confirm"),
    )
    kb.button(text=BACK, callback_data=Nav(to="key"))
    kb.adjust(1)
    return kb.as_markup()


# ---- Locations (paginated) ----------------------------------------------

def locations_menu(page: Page) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    number_row: list[InlineKeyboardButton] = []
    for offset, loc in enumerate(page.items):
        assert isinstance(loc, Location)
        number = page.start_index + offset
        number_row.append(
            InlineKeyboardButton(
                text=str(number), callback_data=LocationCB(tag=loc.tag).pack()
            )
        )
    if number_row:
        kb.row(*number_row)
    kb.row(*_pager_row("locations", page))
    kb.row(_back_button("key"))
    return kb.as_markup()


# ---- Buy flow ------------------------------------------------------------

def plans_menu(plans: list[Plan], with_pay: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for plan in plans:
        disc = discount_percent(plan)
        badge = f" · −{disc}%" if disc > 0 else ""
        kb.button(
            text=f"{plan.title} — {plan.price} ₽{badge}",
            callback_data=PlanCB(action="choose", key=plan.key),
        )
    kb.adjust(1)
    kb.row(_back_button("subscription"))
    return kb.as_markup()


def plans_view_menu(plans: list[Plan]) -> InlineKeyboardMarkup:
    """Read-only tariff list (О нас → Тарифы): no pay buttons."""
    kb = InlineKeyboardBuilder()
    kb.row(_back_button("about"))
    return kb.as_markup()


def payment_methods_menu(plan_key: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="💳 Банковская карта",
        callback_data=PlanCB(action="pay", key=plan_key, method="yookassa"),
    )
    kb.button(
        text="⚡ СБП",
        callback_data=PlanCB(action="pay", key=plan_key, method="sbp"),
    )
    kb.adjust(1)
    kb.row(_back_button("buy"))
    return kb.as_markup()


def payment_link_menu(url: str, payment_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💳 Перейти к оплате", url=url)
    kb.button(
        text="🔄 Я оплатил — проверить",
        callback_data=PayCheckCB(payment_id=payment_id),
    )
    kb.adjust(1)
    kb.row(_back_button("subscription"))
    return kb.as_markup()


# ---- Referral ------------------------------------------------------------

def referral_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Создать код", callback_data=Nav(to="ref_create"))
    kb.adjust(1)
    kb.row(_back_button("main"))
    return kb.as_markup()


def referral_code_menu(link: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📤 Поделиться", url=f"https://t.me/share/url?url={link}")
    kb.adjust(1)
    kb.row(_back_button("referral"))
    return kb.as_markup()


# ---- Help ----------------------------------------------------------------

def help_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(_icon_btn("⚙️", "Установка и настройка", Nav(to="setup"), "help.setup"))
    kb.row(
        _icon_btn("❓", "Ответы на вопросы", PageNav(list="faq", page=1), "help.faq")
    )
    kb.row(_icon_btn("💬", "Техподдержка", Nav(to="support"), "help.support"))
    kb.row(_back_button("main"))
    return kb.as_markup()


def support_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✍️ Написать в поддержку", callback_data=Nav(to="support_write"))
    kb.adjust(1)
    kb.row(_back_button("help"))
    return kb.as_markup()


# ---- Setup wizard --------------------------------------------------------

def setup_device_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, title in DEVICE_TYPES.items():
        kb.button(text=title, callback_data=SetupCB(step="device", value=key))
    kb.adjust(1)
    kb.row(_back_button("help"))
    return kb.as_markup()


def setup_app_menu(device: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for app in SETUP_APPS.get(device, []):
        kb.button(
            text=f"{app.emoji} {app.name}",
            callback_data=SetupCB(step="app", value=app.key),
        )
    kb.adjust(1)
    kb.row(_back_button("setup"))
    return kb.as_markup()


def setup_install_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Далее", callback_data=SetupCB(step="next"))
    kb.button(text="🆘 Что-то пошло не так", callback_data=Nav(to="support"))
    kb.adjust(1)
    kb.row(InlineKeyboardButton(text=BACK, callback_data=Nav(to="setup").pack()))
    return kb.as_markup()


def setup_import_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🆘 Что-то пошло не так", callback_data=Nav(to="support"))
    kb.adjust(1)
    kb.row(_back_button("help"))
    return kb.as_markup()


# ---- FAQ (paginated) -----------------------------------------------------

def faq_menu(page: Page) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for item in page.items:
        kb.button(text=item.title, callback_data=FaqCB(key=item.key))
    kb.adjust(1)
    kb.row(*_pager_row("faq", page))
    kb.row(_back_button("help"))
    return kb.as_markup()


def faq_item_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text=BACK, callback_data=PageNav(list="faq", page=1).pack()
        )
    )
    return kb.as_markup()


# ---- About ---------------------------------------------------------------

def about_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(_icon_btn("📄", "Правила пользования сервисом", Nav(to="rules"), "about.rules"))
    kb.row(_icon_btn("📄", "Условия возврата", Nav(to="refund"), "about.refund"))
    kb.row(_icon_btn("📍", "Локации", Nav(to="locations_view"), "about.locations"))
    kb.row(_icon_btn("🏷️", "Тарифы", Nav(to="tariffs_view"), "about.tariffs"))
    kb.row(_back_button("main"))
    return kb.as_markup()


def about_sub_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(_back_button("about"))
    return kb.as_markup()




# ---- Admin ---------------------------------------------------------------

def admin_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Статистика", callback_data=AdminCB(action="stats"))
    kb.button(text="🎁 Ручная выдача", callback_data=AdminCB(action="grant"))
    kb.button(text="📣 Рассылка", callback_data=AdminCB(action="broadcast"))
    kb.adjust(1)
    return kb.as_markup()


def admin_back_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=BACK, callback_data=AdminCB(action="menu"))
    kb.adjust(1)
    return kb.as_markup()


# ---- shared --------------------------------------------------------------

def _pager_row(list_name: str, page: Page) -> list[InlineKeyboardButton]:
    """Build the «« ‹ N/M › »» navigation row."""
    first = 1
    last = page.total_pages
    prev_page = max(first, page.page - 1)
    next_page = min(last, page.page + 1)
    return [
        InlineKeyboardButton(
            text="««", callback_data=PageNav(list=list_name, page=first).pack()
        ),
        InlineKeyboardButton(
            text="‹", callback_data=PageNav(list=list_name, page=prev_page).pack()
        ),
        InlineKeyboardButton(
            text=f"{page.page}/{page.total_pages}",
            callback_data=PageNav(list=list_name, page=page.page).pack(),
        ),
        InlineKeyboardButton(
            text="›", callback_data=PageNav(list=list_name, page=next_page).pack()
        ),
        InlineKeyboardButton(
            text="»»", callback_data=PageNav(list=list_name, page=last).pack()
        ),
    ]
