"""Assemble all routers into a single router for inclusion in the Dispatcher."""
from __future__ import annotations

from aiogram import Router

from . import about, admin, cabinet, help as help_module, payment, referral, start


def build_router() -> Router:
    root = Router(name="root")
    # order matters: specific/admin routers first, catch-all start last
    root.include_router(admin.router)
    root.include_router(start.router)
    root.include_router(cabinet.router)
    root.include_router(payment.router)
    root.include_router(referral.router)
    root.include_router(help_module.router)
    root.include_router(about.router)
    return root
