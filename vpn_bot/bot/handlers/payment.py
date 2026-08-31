"""Purchase flow.

buy → выбор тарифа → карточка тарифа + способ оплаты → email для чека
(54-ФЗ, можно пропустить) → счёт → оплата → провижининг через вебхук.
"""
from __future__ import annotations

import logging
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession

from .. import texts
from ..callbacks import Nav, PayCheckCB, PlanCB, PurchaseCB
from ..db import repo
from ..keyboards import inline
from ..plans import PLANS, PLANS_BY_KEY, discount_percent
from ..services import payments
from ..services.orders import finalize_payment
from ..states import PurchaseFlow
from ..utils import edit_screen

router = Router(name="payment")
logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@router.callback_query(Nav.filter(F.to == "buy"))
async def choose_plan(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await edit_screen(call, texts.CHOOSE_PLAN, inline.plans_menu(PLANS))
    await call.answer()


@router.callback_query(PlanCB.filter(F.action == "choose"))
async def plan_details(
    call: CallbackQuery, callback_data: PlanCB, state: FSMContext
) -> None:
    await state.clear()
    plan = PLANS_BY_KEY.get(callback_data.key)
    if plan is None:
        await call.answer(texts.ERROR_GENERIC, show_alert=True)
        return
    text = texts.plan_details(
        title=plan.title,
        months=plan.months,
        price=plan.price,
        per_month=plan.base_monthly,
        traffic_gb=plan.traffic_gb,
        discount=discount_percent(plan),
    )
    await edit_screen(call, text, inline.payment_methods_menu(plan.key))
    await call.answer()


@router.callback_query(PlanCB.filter(F.action == "pay"))
async def ask_email(
    call: CallbackQuery, callback_data: PlanCB, state: FSMContext
) -> None:
    plan = PLANS_BY_KEY.get(callback_data.key)
    if plan is None:
        await call.answer(texts.ERROR_GENERIC, show_alert=True)
        return
    await state.set_state(PurchaseFlow.email)
    await state.update_data(plan_key=plan.key, method=callback_data.method)
    await edit_screen(call, texts.EMAIL_ASK, inline.email_menu(plan.key))
    await call.answer()


@router.message(PurchaseFlow.email, F.text)
async def email_received(
    message: Message, state: FSMContext, session: AsyncSession
) -> None:
    email = message.text.strip()
    if not _EMAIL_RE.match(email):
        await message.answer(texts.EMAIL_INVALID)
        return
    data = await state.get_data()
    await state.clear()
    result = await _make_payment(
        session, message.from_user, data.get("plan_key"), data.get("method"), email
    )
    if result is None:
        await message.answer(texts.ERROR_GENERIC)
        return
    text, kb = result
    await message.answer(text, reply_markup=kb)


@router.callback_query(PurchaseCB.filter(F.action == "email_skip"))
async def email_skip(
    call: CallbackQuery, state: FSMContext, session: AsyncSession
) -> None:
    data = await state.get_data()
    await state.clear()
    result = await _make_payment(
        session, call.from_user, data.get("plan_key"), data.get("method"), None
    )
    if result is None:
        await call.answer(texts.ERROR_GENERIC, show_alert=True)
        return
    text, kb = result
    await edit_screen(call, text, kb)
    await call.answer()


async def _make_payment(
    session: AsyncSession,
    tg_user: TgUser,
    plan_key: str | None,
    method: str | None,
    email: str | None,
) -> tuple[str, InlineKeyboardMarkup] | None:
    """Create the YooKassa payment + DB record; return (text, keyboard)."""
    plan = PLANS_BY_KEY.get(plan_key or "")
    if plan is None:
        return None
    user, _ = await repo.get_or_create_user(session, tg_user.id, tg_user.username)
    try:
        result = await payments.create_payment(
            amount_rub=plan.price,
            description=f"Подписка на доступ к онлайн-платформам (Nekit): {plan.title}",
            metadata={"telegram_id": user.telegram_id, "plan_key": plan.key},
            method=method or "yookassa",
            receipt_email=email,
        )
    except Exception:  # pragma: no cover - network/SDK failure
        logger.exception("failed to create payment")
        return None

    payment = await repo.create_payment(
        session,
        user=user,
        amount=float(plan.price),
        plan_key=plan.key,
        months=plan.months,
        provider_payment_id=result.provider_id,
    )
    return (
        texts.payment_created(plan.price, email),
        inline.payment_link_menu(result.confirmation_url, payment.id),
    )


@router.callback_query(PayCheckCB.filter())
async def check_payment(
    call: CallbackQuery, callback_data: PayCheckCB, session: AsyncSession
) -> None:
    """Manual 'I paid' button: poll YooKassa and provision on success."""
    from ..db.models import Payment

    payment = await session.get(Payment, callback_data.payment_id)
    if payment is None:
        await call.answer(texts.ERROR_GENERIC, show_alert=True)
        return

    if payment.status != "succeeded":
        remote = await payments.fetch_payment(payment.provider_payment_id or "")
        if remote.get("status") == "succeeded":
            await finalize_payment(session, payment)
        else:
            await call.answer(texts.PAYMENT_PENDING, show_alert=True)
            return

    user = await repo.get_user(session, call.from_user.id)
    sub = user.subscription if user else None
    url = sub.subscription_url if sub else ""
    await edit_screen(
        call, texts.PAYMENT_SUCCESS + f"\n\n<code>{url}</code>", inline.key_menu()
    )
    await call.answer("✅ Оплата подтверждена")
