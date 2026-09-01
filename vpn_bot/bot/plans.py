"""Static catalog of tariff plans and helper lookups.

Prices are in RUB. `months` drives the panel expiry extension. `discount`
is the percent saved versus paying the 1-month price each month, shown in UI.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    key: str
    title: str
    months: int
    price: int  # total price in RUB
    traffic_gb: int  # monthly traffic limit

    @property
    def base_monthly(self) -> float:
        return self.price / self.months


# Base monthly reference price used to compute the "% economy" badge.
_BASE_MONTHLY = 199

PLANS: list[Plan] = [
    Plan(key="m1", title="1 месяц", months=1, price=199, traffic_gb=100),
    Plan(key="m3", title="3 месяца", months=3, price=499, traffic_gb=100),
    Plan(key="m6", title="6 месяцев", months=6, price=899, traffic_gb=100),
    Plan(key="m12", title="12 месяцев", months=12, price=1599, traffic_gb=100),
]

PLANS_BY_KEY: dict[str, Plan] = {p.key: p for p in PLANS}


def discount_percent(plan: Plan) -> int:
    """Percent saved versus paying the base monthly price every month."""
    full = _BASE_MONTHLY * plan.months
    if full <= 0:
        return 0
    saved = (full - plan.price) / full * 100
    return max(0, round(saved))
