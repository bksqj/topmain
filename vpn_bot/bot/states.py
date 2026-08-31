"""FSM state groups."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class SetupWizard(StatesGroup):
    device = State()
    app = State()
    install = State()
    import_key = State()


class PurchaseFlow(StatesGroup):
    email = State()


class SupportFlow(StatesGroup):
    waiting_message = State()


class AdminFlow(StatesGroup):
    broadcast = State()
    grant = State()
