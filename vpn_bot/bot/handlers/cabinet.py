"""Personal cabinet: subscription card, key screen, locations."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from .. import texts
from ..callbacks import KeyActionCB, LocationCB, Nav, PageNav
from ..config import get_settings
from ..db import repo
from ..keyboards import inline
from ..keyboards.pagination import paginate
from ..locations import LOCATIONS_BY_TAG, FALLBACK_LOCATIONS
from ..plans import PLANS
from ..services.provisioning import reissue_key, switch_location, sync_traffic
from ..services.qr import make_qr_png
from ..utils import edit_screen, time_remaining

router = Router(name="cabinet")
_settings = get_settings()


def _plan_title(plan_key: str) -> str:
    from ..plans import PLANS_BY_KEY

    if plan_key in ("trial", "free"):
        return _settings.trial_plan_name
    plan = PLANS_BY_KEY.get(plan_key)
    if plan:
        return plan.title
    if plan_key.startswith("manual_"):
        return "Ручная выдача"
    return plan_key


@router.callback_query(Nav.filter(F.to == "cabinet"))
async def to_cabinet(call: CallbackQuery) -> None:
    await edit_screen(call, texts.CABINET, inline.cabinet_menu())
    await call.answer()


@router.callback_query(Nav.filter(F.to == "subscription"))
async def to_subscription(call: CallbackQuery, session: AsyncSession) -> None:
    user = await repo.get_or_create_user(
        session, call.from_user.id, call.from_user.username
    )
    sub = user[0].subscription
    if sub is not None:
        sub = await sync_traffic(session, sub)
    days, hours, minutes = time_remaining(sub.expires_at if sub else None)
    text = texts.subscription_card(
        plan_title=_plan_title(sub.plan) if sub else _settings.trial_plan_name,
        limit_gb=sub.traffic_limit_gb if sub else 0,
        used_gb=sub.traffic_used_gb if sub else 0,
        days=days,
        hours=hours,
        minutes=minutes,
    )
    is_trial = sub.is_trial if sub else True
    await edit_screen(call, text, inline.subscription_menu(is_trial))
    await call.answer()


# ---- Key -----------------------------------------------------------------

@router.callback_query(Nav.filter(F.to == "key"))
async def to_key(call: CallbackQuery, session: AsyncSession) -> None:
    user, _ = await repo.get_or_create_user(
        session, call.from_user.id, call.from_user.username
    )
    sub = user.subscription
    if not sub or not sub.subscription_url:
        await edit_screen(call, texts.NO_KEY_YET, inline.key_no_sub_menu())
        await call.answer()
        return
    await edit_screen(call, texts.key_card(sub.subscription_url), inline.key_menu())
    await call.answer()


@router.callback_query(KeyActionCB.filter(F.action == "copy"))
async def key_copy(call: CallbackQuery) -> None:
    # Telegram highlights <code> for tap-to-copy; just acknowledge.
    await call.answer(texts.KEY_COPIED, show_alert=False)


@router.callback_query(KeyActionCB.filter(F.action == "qr"))
async def key_qr(call: CallbackQuery, session: AsyncSession) -> None:
    sub = await repo.get_subscription(session, call.from_user.id)
    if not sub or not sub.subscription_url:
        await call.answer(texts.ERROR_GENERIC, show_alert=True)
        return
    png = make_qr_png(sub.subscription_url)
    photo = BufferedInputFile(png, filename="key.png")
    await call.message.answer_photo(photo, caption="🔳 QR-код вашего ключа")
    await call.answer()


@router.callback_query(KeyActionCB.filter(F.action == "reissue"))
async def key_reissue_ask(call: CallbackQuery) -> None:
    await edit_screen(call, texts.REISSUE_CONFIRM, inline.reissue_confirm_menu())
    await call.answer()


@router.callback_query(KeyActionCB.filter(F.action == "reissue_confirm"))
async def key_reissue_confirm(call: CallbackQuery, session: AsyncSession) -> None:
    sub = await repo.get_subscription(session, call.from_user.id)
    if not sub:
        await call.answer(texts.ERROR_GENERIC, show_alert=True)
        return
    sub = await reissue_key(session, sub)
    await call.answer(texts.REISSUE_DONE, show_alert=True)
    url = sub.subscription_url or ""
    await edit_screen(call, texts.key_card(url), inline.key_menu())


# ---- Locations -----------------------------------------------------------

def _render_locations(page_num: int) -> tuple[str, object, object]:
    locations = FALLBACK_LOCATIONS
    page = paginate(locations, page_num)
    lines = [texts.LOCATIONS_HEADER, ""]
    for offset, loc in enumerate(page.items):
        lines.append(f"{page.start_index + offset}. {loc.label()}")
    return "\n".join(lines), page, locations


@router.callback_query(PageNav.filter(F.list == "locations"))
async def locations_page(call: CallbackQuery, callback_data: PageNav) -> None:
    text, page, _ = _render_locations(callback_data.page)
    await edit_screen(call, text, inline.locations_menu(page))
    await call.answer()


@router.callback_query(LocationCB.filter())
async def choose_location(
    call: CallbackQuery, callback_data: LocationCB, session: AsyncSession
) -> None:
    loc = LOCATIONS_BY_TAG.get(callback_data.tag)
    if loc is None:
        await call.answer(texts.ERROR_GENERIC, show_alert=True)
        return
    sub = await repo.get_subscription(session, call.from_user.id)
    if sub is None:
        await call.answer("Сначала оформите подписку", show_alert=True)
        return
    # inbounds mapping is Marzban-config specific; pass the tag through
    await switch_location(
        session, sub, node_tag=loc.tag, inbounds={"vless": [loc.tag]}
    )
    await call.answer(texts.LOCATION_SWITCHED.format(label=loc.label()), show_alert=True)
