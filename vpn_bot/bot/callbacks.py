"""Typed callback-data factories (aiogram CallbackData)."""
from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class Nav(CallbackData, prefix="nav"):
    """Generic navigation between named screens."""

    to: str  # screen key, e.g. "main", "cabinet", "help", "about", "referral"


class PageNav(CallbackData, prefix="pg"):
    """Pagination: which list and which page."""

    list: str  # "locations" | "faq"
    page: int


class PlanCB(CallbackData, prefix="plan"):
    action: str  # "choose" | "pay"
    key: str  # plan key
    method: str = "-"  # payment method for "pay" action


class PurchaseCB(CallbackData, prefix="buyflow"):
    action: str  # "email_skip"


class PayCheckCB(CallbackData, prefix="paycheck"):
    payment_id: int


class LocationCB(CallbackData, prefix="loc"):
    tag: str


class KeyActionCB(CallbackData, prefix="key"):
    action: str  # "copy" | "qr" | "reissue" | "reissue_confirm"


class FaqCB(CallbackData, prefix="faq"):
    key: str


class SetupCB(CallbackData, prefix="setup"):
    step: str  # "device" | "app" | "install" | "import" | "next"
    value: str = "-"


class AdminCB(CallbackData, prefix="admin"):
    action: str  # "stats" | "broadcast" | "grant" | "menu"
