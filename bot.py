import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

API_TOKEN = '7513479457:AAE8De_nENdfXtDcMxVP79lONSIdd1W3AwM'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Давай начнем! Как тебя зовут?")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
