"""Entry point: runs aiogram polling, the FastAPI webhook, and the scheduler.

    python -m bot.main
"""
from __future__ import annotations

import asyncio
import logging

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import get_settings
from .db.engine import init_db
from .handlers import build_router
from .middlewares import DbSessionMiddleware
from .services.scheduler import setup_scheduler
from .webhook.app import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("vpn_bot")


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DbSessionMiddleware())
    dp.include_router(build_router())
    return dp


async def _run_webhook(bot: Bot) -> None:
    settings = get_settings()
    app = create_app(bot)
    config = uvicorn.Config(
        app,
        host=settings.webhook_host,
        port=settings.webhook_port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    settings = get_settings()
    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()

    scheduler = setup_scheduler(bot)
    scheduler.start()

    logger.info("Starting bot polling + webhook server on %s:%s",
                settings.webhook_host, settings.webhook_port)

    try:
        await asyncio.gather(
            dp.start_polling(bot),
            _run_webhook(bot),
        )
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down.")
