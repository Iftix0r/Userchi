import asyncio
import logging

from database import init_db
from userbot import userbot
from admin_bot import bot, dp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    await init_db()
    logger.info("Database ready")

    async with userbot:
        logger.info("Userbot started as: %s", await userbot.get_me())
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())