"""Data-access helpers. Thin async functions over SQLAlchemy sessions."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import get_settings
from .models import Payment, ReferralStat, Subscription, User

_settings = get_settings()


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    stmt = (
        select(User)
        .where(User.telegram_id == telegram_id)
        .options(
            selectinload(User.subscription),
            selectinload(User.referral_stat),
        )
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    referred_by: int | None = None,
) -> tuple[User, bool]:
    """Return (user, created). Sets up trial subscription + referral stat row."""
    user = await get_user(session, telegram_id)
    if user is not None:
        # keep username fresh
        if username and user.username != username:
            user.username = username
            await session.commit()
        return user, False

    user = User(
        telegram_id=telegram_id,
        username=username,
        referred_by=referred_by if referred_by != telegram_id else None,
    )
    session.add(user)
    await session.flush()

    trial = Subscription(
        user_id=user.id,
        plan="trial",
        traffic_limit_gb=float(_settings.trial_traffic_gb),
        traffic_used_gb=0.0,
        expires_at=datetime.utcnow() + timedelta(days=_settings.trial_days),
    )
    session.add(trial)
    session.add(ReferralStat(user_id=user.id))
    await session.flush()

    # credit the referrer's invited_count
    if user.referred_by:
        await _bump_referrer_invited(session, user.referred_by)

    await session.commit()
    await session.refresh(user, ["subscription", "referral_stat"])
    return user, True


async def _bump_referrer_invited(session: AsyncSession, referrer_tg_id: int) -> None:
    referrer = await get_user(session, referrer_tg_id)
    if referrer is None:
        return
    stat = referrer.referral_stat
    if stat is None:
        stat = ReferralStat(user_id=referrer.id)
        session.add(stat)
        await session.flush()
    stat.invited_count += 1


async def get_user_by_pk(session: AsyncSession, user_pk: int) -> User | None:
    stmt = (
        select(User)
        .where(User.id == user_pk)
        .options(
            selectinload(User.subscription),
            selectinload(User.referral_stat),
        )
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_subscription(
    session: AsyncSession, telegram_id: int
) -> Subscription | None:
    user = await get_user(session, telegram_id)
    return user.subscription if user else None


async def create_payment(
    session: AsyncSession,
    user: User,
    amount: float,
    plan_key: str,
    months: int,
    provider: str = "yookassa",
    provider_payment_id: str | None = None,
) -> Payment:
    payment = Payment(
        user_id=user.id,
        amount=amount,
        provider=provider,
        provider_payment_id=provider_payment_id,
        plan_key=plan_key,
        months=months,
        status="pending",
    )
    session.add(payment)
    await session.commit()
    await session.refresh(payment)
    return payment


async def get_payment_by_provider_id(
    session: AsyncSession, provider_payment_id: str
) -> Payment | None:
    stmt = select(Payment).where(
        Payment.provider_payment_id == provider_payment_id
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def mark_payment_status(
    session: AsyncSession, payment: Payment, status: str
) -> None:
    payment.status = status
    await session.commit()


async def credit_referrer_payment(
    session: AsyncSession, buyer: User, amount: float
) -> User | None:
    """When `buyer` pays, credit their referrer's stats. Returns the referrer."""
    if not buyer.referred_by:
        return None
    referrer = await get_user(session, buyer.referred_by)
    if referrer is None:
        return None
    stat = referrer.referral_stat
    if stat is None:
        stat = ReferralStat(user_id=referrer.id)
        session.add(stat)
        await session.flush()
    stat.total_paid_count += 1
    stat.total_paid_amount += amount
    await session.commit()
    return referrer


# ---- admin helpers -------------------------------------------------------

async def count_users(session: AsyncSession) -> int:
    from sqlalchemy import func as sa_func

    return (
        await session.execute(select(sa_func.count(User.id)))
    ).scalar_one()


async def sum_payments(session: AsyncSession) -> float:
    from sqlalchemy import func as sa_func

    total = (
        await session.execute(
            select(sa_func.coalesce(sa_func.sum(Payment.amount), 0.0)).where(
                Payment.status == "succeeded"
            )
        )
    ).scalar_one()
    return float(total or 0.0)


async def all_user_telegram_ids(session: AsyncSession) -> list[int]:
    rows = (await session.execute(select(User.telegram_id))).scalars().all()
    return list(rows)
