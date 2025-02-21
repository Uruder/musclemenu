import logging
import asyncio
from aiogram import Bot, Dispatcher, types

API_TOKEN = "7513479457:AAE8De_nENdfXtDcMxVP79lONSIdd1W3AwM"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Давай начнем! Как тебя зовут?")

async def main():
    """Удаляем вебхук и запускаем polling"""
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
