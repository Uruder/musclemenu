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
    
import os
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

def run_flask():
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    from aiogram import executor
    from bot import dp

    # Запускаем Flask сервер в отдельном потоке
    Thread(target=run_flask, daemon=True).start()

    # Запускаем Telegram-бота
    executor.start_polling(dp, skip_updates=True)
