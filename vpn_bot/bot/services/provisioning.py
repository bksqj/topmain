"""Provision / extend a user's subscription in Remnawave and persist state.

Shared by the payment webhook and the admin manual-grant flow. Falls back to
a DB-only update when Remnawave is not configured, so the bot stays usable in
demo mode.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..db.models import Subscription, User
from ..plans import Plan
from .remnawave import RemnawaveError, get_remnawave

_settings = get_settings()

# rough UUID matcher, to tell a real squad uuid from a demo location slug
_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)


def panel_username_for(user: User) -> str:
    return f"tg_{user.telegram_id}"


async def provision_plan(
    session: AsyncSession, user: User, plan: Plan
) -> Subscription:
    return await _provision(
        session, user, plan_key=plan.key, months=plan.months,
        traffic_gb=float(plan.traffic_gb),
    )


async def provision_manual(
    session: AsyncSession, user: User, months: int, traffic_gb: float = 100.0
) -> Subscription:
    return await _provision(
        session, user, plan_key=f"manual_{months}m", months=months,
        traffic_gb=traffic_gb,
    )


async def _provision(
    session: AsyncSession,
    user: User,
    plan_key: str,
    months: int,
    traffic_gb: float,
) -> Subscription:
    panel = get_remnawave()
    add_days = months * 30

    sub = user.subscription
    if sub is None:
        sub = Subscription(user_id=user.id)
        session.add(sub)

    now = datetime.utcnow()
    base = max(sub.expires_at or now, now)
    new_expiry = base + timedelta(days=add_days)

    if panel.configured:
        try:
            if sub.remnawave_uuid:
                payload = await panel.extend_user(
                    sub.remnawave_uuid, new_expiry, traffic_gb=traffic_gb
                )
            else:
                payload = await panel.create_user(
                    username=panel_username_for(user),
                    expire_at=new_expiry,
                    traffic_gb=traffic_gb,
                    squads=_settings.remnawave_default_squads,
                    telegram_id=user.telegram_id,
                )
            sub.remnawave_uuid = payload.get("uuid") or sub.remnawave_uuid
            sub.remnawave_short_uuid = (
                payload.get("shortUuid") or sub.remnawave_short_uuid
            )
            url = panel.subscription_url(payload)
            if url:
                sub.subscription_url = url
        except RemnawaveError:
            # keep DB consistent even if the panel call failed
            pass

    sub.plan = plan_key
    sub.traffic_limit_gb = traffic_gb
    sub.expires_at = new_expiry
    await session.commit()
    await session.refresh(sub)
    return sub


async def sync_traffic(session: AsyncSession, sub: Subscription) -> Subscription:
    panel = get_remnawave()
    if panel.configured and sub.remnawave_uuid:
        try:
            payload = await panel.get_user(sub.remnawave_uuid)
            sub.traffic_used_gb = panel.used_traffic_gb(payload)
            url = panel.subscription_url(payload)
            if url:
                sub.subscription_url = url
            await session.commit()
            await session.refresh(sub)
        except RemnawaveError:
            pass
    return sub


async def reissue_key(session: AsyncSession, sub: Subscription) -> Subscription:
    panel = get_remnawave()
    if panel.configured and sub.remnawave_uuid:
        try:
            payload = await panel.revoke_subscription(sub.remnawave_uuid)
            url = panel.subscription_url(payload)
            if url:
                sub.subscription_url = url
            sub.remnawave_short_uuid = (
                payload.get("shortUuid") or sub.remnawave_short_uuid
            )
            await session.commit()
            await session.refresh(sub)
        except RemnawaveError:
            pass
    return sub


async def switch_location(
    session: AsyncSession, sub: Subscription, node_tag: str
) -> Subscription:
    """Switch the user's squad. `node_tag` should be a squad UUID in production;
    demo location slugs are stored for UI only."""
    panel = get_remnawave()
    if panel.configured and sub.remnawave_uuid and _UUID_RE.match(node_tag):
        try:
            await panel.set_squads(sub.remnawave_uuid, [node_tag])
        except RemnawaveError:
            pass
    sub.node_tag = node_tag
    await session.commit()
    await session.refresh(sub)
    return sub
