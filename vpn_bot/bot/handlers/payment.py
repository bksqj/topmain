"""Purchase flow: tariff selection → payment method → invoice → provisioning."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from .. import texts
from ..callbacks import Nav, PayCheckCB, PlanCB
from ..db import repo
from ..keyboards import inline
from ..plans import PLANS, PLANS_BY_KEY
from ..services import payments
from ..services.orders import finalize_payment
from ..utils import edit_screen

router = Router(name="payment")
logger = logging.getLogger(__name__)


@router.callback_query(Nav.filter(F.to == "buy"))
async def choose_plan(call: CallbackQuery) -> None:
    await edit_screen(call, texts.CHOOSE_PLAN, inline.plans_menu(PLANS))
    await call.answer()


@router.callback_query(PlanCB.filter(F.action == "choose"))
async def choose_method(call: CallbackQuery, callback_data: PlanCB) -> None:
    plan = PLANS_BY_KEY.get(callback_data.key)
    if plan is None:
        await call.answer(texts.ERROR_GENERIC, show_alert=True)
        return
    text = texts.CHOOSE_PAYMENT.format(plan_title=plan.title, price=plan.price)
    await edit_screen(call, text, inline.payment_methods_menu(plan.key))
    await call.answer()


@router.callback_query(PlanCB.filter(F.action == "pay"))
async def create_invoice(
    call: CallbackQuery, callback_data: PlanCB, session: AsyncSession
) -> None:
    plan = PLANS_BY_KEY.get(callback_data.key)
    if plan is None:
        await call.answer(texts.ERROR_GENERIC, show_alert=True)
        return
    user, _ = await repo.get_or_create_user(
        session, call.from_user.id, call.from_user.username
    )
    try:
        result = await payments.create_payment(
            amount_rub=plan.price,
            description=f"Подписка (Nekit): {plan.title}",
            metadata={"telegram_id": user.telegram_id, "plan_key": plan.key},
            method=callback_data.method,
        )
    except Exception:  # pragma: no cover - network/SDK failure
        logger.exception("failed to create payment")
        await call.answer(texts.ERROR_GENERIC, show_alert=True)
        return

    payment = await repo.create_payment(
        session,
        user=user,
        amount=float(plan.price),
        plan_key=plan.key,
        months=plan.months,
        provider_payment_id=result.provider_id,
    )
    await edit_screen(
        call,
        texts.payment_created(plan.price),
        inline.payment_link_menu(result.confirmation_url, payment.id),
    )
    await call.answer()


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
