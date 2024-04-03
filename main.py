import logging
import asyncio
import sys
from aiogram.fsm.storage.redis import RedisStorage

from CouplePurchases.CouplesMain import CoupleMain
from handlers import add_order, del_order, status, ClearQueue
import nest_asyncio
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.strategy import FSMStrategy
from settings import TOKEN

from aiogram import Bot, types, Router, Dispatcher, F
from aiogram.filters import Command
from statistic import stat_couple, stat_graph

from keyboard.keyboard_main import markup_adf

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="%(asctime)s - %(module)s - %(levelname)s - %(funcName)s: %(lineno)d - %(message)s",
                    datefmt='%H:%M:%S')

logger = logging.getLogger()

bot = Bot(token=TOKEN, parse_mode="HTML")
router = Router()


@router.message(Command(commands=["start"]))
async def cmd_start(message: types.Message):
    await message.answer(f'Приветствую тебя {message.from_user.username}!', reply_markup=markup_adf)


async def main():

    dp = Dispatcher(storage=MemoryStorage(), fsm_strategy=FSMStrategy.CHAT)
    dp.message.filter(F.chat.type == "private")

    dp.include_router(add_order.router)
    dp.include_router(del_order.router)
    dp.include_router(status.router)
    dp.include_router(stat_couple.router)
    dp.include_router(stat_graph.router)
    dp.include_router(ClearQueue.router)
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == '__main__':

    CoupleMain().start()
    nest_asyncio.apply()
    asyncio.run(main())
