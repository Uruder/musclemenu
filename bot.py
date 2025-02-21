import logging
import asyncio
from aiogram import Bot, Dispatcher, types

API_TOKEN = "7513479457:AAE8De_nENdfXtDcMxVP79lONSIdd1W3AwM"

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем экземпляры бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Давай начнем! Как тебя зовут?")

async def main():
    """Функция запуска бота"""
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
