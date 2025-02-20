from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from flask import Flask, request
import logging

API_TOKEN = '7513479457:AAE8De_nENdfXtDcMxVP79lONSIdd1W3AwM'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

app = Flask(__name__)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Давай начнем! Как тебя зовут?")

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = types.Update(**request.json)
    await dp.process_update(update)
    return 'ok', 200

if __name__ == '__main__':
    # Встановлюємо вебхук
    from aiogram.utils.executor import start_webhook

    async def on_startup(dp):
        await bot.set_webhook("https://your-render-url.onrender.com/webhook")

    async def on_shutdown(dp):
        await bot.delete_webhook()

    start_webhook(
        dispatcher=dp,
        webhook_path='/webhook',
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host='0.0.0.0',
        port=10000,
    )
