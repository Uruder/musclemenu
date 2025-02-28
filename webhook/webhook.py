import logging
import os
from flask import Flask, request
from dotenv import load_dotenv
import stripe
from datetime import datetime, timedelta
import asyncio
from aiogram import Bot
import aiohttp

load_dotenv()
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8081))

stripe.api_key = STRIPE_API_KEY
bot = Bot(token=BOT_TOKEN)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

DATABASE_URL = os.getenv("DATABASE_URL")

async def set_subscription(user_id, subscription_end):
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO payments (user_id, subscription_end)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET subscription_end = $2, trial_used = FALSE
        """, user_id, subscription_end)
    await pool.close()

async def generate_daily_recipe(user):
    return "Пример дневного рациона"

@app.route('/stripe_webhook', methods=['POST'])
async def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        if event['type'] == 'checkout.session.completed':
            user_id = int(event['data']['object']['metadata']['user_id'])
            subscription_end = datetime.now() + timedelta(days=30)
            await set_subscription(user_id, subscription_end)
            ration = await generate_daily_recipe({"language": "ru"})  # Предполагаем язык ru для простоты
            await bot.send_message(user_id, ration + "\n\n🎉 Спасибо за покупку!", parse_mode="Markdown")
    except ValueError as e:
        logging.error(f"Webhook error: {e}")
    return '', 200

if __name__ == "__main__":
    app.run(host=WEBAPP_HOST, port=WEBAPP_PORT)
