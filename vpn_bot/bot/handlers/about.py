"""About section: rules, refund, tariffs (read-only)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from .. import locations, texts
from ..callbacks import Nav
from ..keyboards import inline
from ..plans import PLANS, discount_percent
from ..utils import edit_screen

router = Router(name="about")


@router.callback_query(Nav.filter(F.to == "rules"))
async def rules(call: CallbackQuery) -> None:
    await edit_screen(call, texts.RULES, inline.about_sub_menu())
    await call.answer()


@router.callback_query(Nav.filter(F.to == "locations_view"))
async def locations_view(call: CallbackQuery) -> None:
    await edit_screen(call, locations.full_list_text(), inline.about_sub_menu())
    await call.answer()


@router.callback_query(Nav.filter(F.to == "refund"))
async def refund(call: CallbackQuery) -> None:
    await edit_screen(call, texts.REFUND, inline.about_sub_menu())
    await call.answer()


@router.callback_query(Nav.filter(F.to == "tariffs_view"))
async def tariffs_view(call: CallbackQuery) -> None:
    lines = [texts.TARIFFS_VIEW_HEADER, ""]
    for plan in PLANS:
        disc = discount_percent(plan)
        badge = f" (−{disc}%)" if disc > 0 else ""
        lines.append(
            f"• {plan.title} — {plan.price} ₽{badge} · {plan.traffic_gb} ГБ/мес"
        )
    await edit_screen(call, "\n".join(lines), inline.plans_view_menu(PLANS))
    await call.answer()
