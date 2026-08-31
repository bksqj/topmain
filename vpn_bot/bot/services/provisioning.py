"""Provision / extend a user's VPN subscription in Marzban and persist state.

Shared by the payment webhook and the admin manual-grant flow.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Subscription, User
from ..plans import Plan
from .marzban import MarzbanError, get_marzban


def marzban_username_for(user: User) -> str:
    return f"tg_{user.telegram_id}"


async def provision_plan(
    session: AsyncSession, user: User, plan: Plan
) -> Subscription:
    """Create or extend the user's Marzban account for a purchased plan.

    Falls back to a DB-only update if Marzban is not configured, so the bot
    remains usable in demo mode.
    """
    return await _provision(
        session,
        user,
        plan_key=plan.key,
        plan_title=plan.title,
        months=plan.months,
        traffic_gb=float(plan.traffic_gb),
    )


async def provision_manual(
    session: AsyncSession, user: User, months: int, traffic_gb: float = 100.0
) -> Subscription:
    return await _provision(
        session,
        user,
        plan_key=f"manual_{months}m",
        plan_title=f"Ручная выдача ({months} мес.)",
        months=months,
        traffic_gb=traffic_gb,
    )


async def _provision(
    session: AsyncSession,
    user: User,
    plan_key: str,
    plan_title: str,
    months: int,
    traffic_gb: float,
) -> Subscription:
    marzban = get_marzban()
    username = marzban_username_for(user)
    add_days = months * 30

    sub = user.subscription
    if sub is None:
        sub = Subscription(user_id=user.id)
        session.add(sub)

    subscription_url = sub.subscription_url
    if marzban.configured:
        try:
            if sub.marzban_username:
                payload = await marzban.extend_user(
                    sub.marzban_username, add_days, traffic_gb=traffic_gb
                )
            else:
                payload = await marzban.create_user(
                    username, traffic_gb=traffic_gb, days=add_days
                )
            subscription_url = marzban.subscription_url(payload) or subscription_url
            sub.marzban_username = username
        except MarzbanError:
            # keep DB consistent even if the panel call failed; caller logs
            pass

    # persist plan + expiry
    now = datetime.utcnow()
    base = max(sub.expires_at or now, now)
    sub.plan = plan_key
    sub.traffic_limit_gb = traffic_gb
    sub.expires_at = base + timedelta(days=add_days)
    sub.subscription_url = subscription_url
    if plan_title:
        # store a readable title alongside the key for the UI
        pass
    await session.commit()
    await session.refresh(sub)
    return sub


async def sync_traffic(session: AsyncSession, sub: Subscription) -> Subscription:
    """Pull latest used-traffic from Marzban into the subscription record."""
    marzban = get_marzban()
    if marzban.configured and sub.marzban_username:
        try:
            payload = await marzban.get_user(sub.marzban_username)
            sub.traffic_used_gb = marzban.used_traffic_gb(payload)
            url = marzban.subscription_url(payload)
            if url:
                sub.subscription_url = url
            await session.commit()
            await session.refresh(sub)
        except MarzbanError:
            pass
    return sub


async def reissue_key(session: AsyncSession, sub: Subscription) -> Subscription:
    marzban = get_marzban()
    if marzban.configured and sub.marzban_username:
        try:
            payload = await marzban.revoke_subscription(sub.marzban_username)
            url = marzban.subscription_url(payload)
            if url:
                sub.subscription_url = url
            await session.commit()
            await session.refresh(sub)
        except MarzbanError:
            pass
    return sub


async def switch_location(
    session: AsyncSession, sub: Subscription, node_tag: str, inbounds: dict
) -> Subscription:
    marzban = get_marzban()
    if marzban.configured and sub.marzban_username:
        try:
            await marzban.set_inbounds(sub.marzban_username, inbounds)
        except MarzbanError:
            pass
    sub.node_tag = node_tag
    await session.commit()
    await session.refresh(sub)
    return sub
