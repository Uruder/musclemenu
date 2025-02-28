import logging
import os
import random
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
from database import Database
from datetime import datetime, timedelta
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import asyncio

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))
GROK_API_KEY = os.getenv("GROK_API_KEY")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logging.info(f"Bot starting with token: {BOT_TOKEN[:10]}...")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.info("Bot and Dispatcher initialized")

# База данных
db = Database()
logging.info("Database object created")

# База рецептов
RECIPES = [
    {"name": "Овсянка с бананом", "calories": 400, "protein": 10, "fat": 5, "carbs": 70, "recipe": "🥣 100г овсянки, 🍌 1 банан. Залей кипятком, дай настояться 5 мин."},
    {"name": "Курица с рисом", "calories": 600, "protein": 50, "fat": 10, "carbs": 60, "recipe": "🍗 150г куриной грудки, 🍚 80г риса. Отвари курицу и рис."},
    {"name": "Творог с яблоком", "calories": 350, "protein": 30, "fat": 5, "carbs": 40, "recipe": "🧀 150г творога 5%, 🍎 1 яблоко. Нарежь яблоко, смешай с творогом."},
    {"name": "Яичница с картофелем", "calories": 500, "protein": 20, "fat": 25, "carbs": 50, "recipe": "🥚 3 яйца, 🥔 200г картофеля. Обжарь яйца с вареным картофелем."},
]

# Мотивационные цитаты
QUOTES = {
    "ru": ["💪 Сила в дисциплине!"],
    "en": ["💪 Strength lies in discipline!"],
    "uk": ["💪 Сила в дисципліні!"]
}

# Тексты на разных языках
TEXTS = {
    "ru": {
        "welcome": "💪 *Привет! Я MuscleMenu!* Помогу тебе набрать массу.\nДавай зарегистрируем тебя. Как тебя зовут?",
        "name": "Как тебя зовут?",
        "height": "Какой у тебя рост (в см)?",
        "weight": "Какой у тебя вес (в кг)?",
        "age": "Сколько тебе лет?",
        "activity": "Какой у тебя уровень активности (низкая/средняя/высокая)?",
        "workouts": "Сколько у тебя тренировок в неделю?",
        "preferences": "Какие продукты ты любишь? (Например: 🍗 курица, 🥚 яйца, 🍚 рис)\nОставь пустым, если нет предпочтений.",
        "saved": "✅ *Данные сохранены!* Что дальше?",
        "daily_plan": "🍽 *Дневной рацион* 🍽",
        "payment_success": "🎉 Спасибо за покупку!",
        "subscription_end": "⏰ Твоя подписка заканчивается через {days} дней! Продли за 500 UAH или 50 XTR.",
        "subscription_expired": "⚠️ Твоя подписка закончилась. Доступ к дневному рациону ограничен.",
        "register_first": "Сначала зарегистрируйтесь!",
        "back_to_main": "💪 *MuscleMenu* — твой помощник в наборе массы!\nЧто дальше?"
    },
    "en": {
        "welcome": "💪 *Hello! I’m MuscleMenu!* I’ll help you gain mass.\nLet’s get you registered. What’s your name?",
        "name": "What’s your name?",
        "height": "What’s your height (in cm)?",
        "weight": "What’s your weight (in kg)?",
        "age": "How old are you?",
        "activity": "What’s your activity level (low/medium/high)?",
        "workouts": "How many workouts do you have per week?",
        "preferences": "What foods do you like? (E.g., 🍗 chicken, 🥚 eggs, 🍚 rice)\nLeave empty if no preferences.",
        "saved": "✅ *Data saved!* What’s next?",
        "daily_plan": "🍽 *Daily Meal Plan* 🍽",
        "payment_success": "🎉 Thank you for your purchase!",
        "subscription_end": "⏰ Your subscription ends in {days} days! Renew for 500 UAH or 50 XTR.",
        "subscription_expired": "⚠️ Your subscription has expired. Access to daily meal plans is restricted.",
        "register_first": "Register first!",
        "back_to_main": "💪 *MuscleMenu* — your mass-gaining assistant!\nWhat’s next?"
    },
    "uk": {
        "welcome": "💪 *Привіт! Я MuscleMenu!* Допоможу тобі набрати масу.\nДавай зареєструємо тебе. Як тебе звати?",
        "name": "Як тебе звати?",
        "height": "Який у тебе зріст (в см)?",
        "weight": "Яка у тебе вага (в кг)?",
        "age": "Скільки тобі років?",
        "activity": "Який у тебе рівень активності (низький/середній/високий)?",
        "workouts": "Скільки у тебе тренувань на тиждень?",
        "preferences": "Які продукти ти любиш? (Например: 🍗 курка, 🥚 яйця, 🍚 рис)\nЗалиш порожнім, якщо немає вподобань.",
        "saved": "✅ *Дані збережено!* Що далі?",
        "daily_plan": "🍽 *Денний раціон* 🍽",
        "payment_success": "🎉 Дякую за покупку!",
        "subscription_end": "⏰ Твоя підписка закінчується через {days} днів! Продовж за 500 UAH або 50 XTR.",
        "subscription_expired": "⚠️ Твоя підписка закінчилася. Доступ до денного раціону обмежено.",
        "register_first": "Спочатку зареєструйтесь!",
        "back_to_main": "💪 *MuscleMenu* — твій помічник у наборі маси!\nЩо далі?"
    }
}

# Определение состояний FSM
class UserForm(StatesGroup):
    name = State()
    height = State()
    weight = State()
    age = State()
    activity = State()
    workouts = State()
    preferences = State()

# Главное меню
def get_main_menu(language="ru"):
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🍽", callback_data="daily_plan")],
        [types.InlineKeyboardButton(text="🌐 Язык" if language == "ru" else "🌐 Language" if language == "en" else "🌐 Мова", callback_data="switch_language")]
    ])

# Меню с кнопкой "Назад" и "Поделиться"
def get_back_menu(text_to_share="", language="ru"):
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="⬅️ Назад" if language == "ru" else "⬅️ Back" if language == "en" else "⬅️ Назад", callback_data="back_to_main")]
    ])
    if text_to_share:
        markup.inline_keyboard.append([types.InlineKeyboardButton(text="📤 Поделиться" if language == "ru" else "📤 Share" if language == "en" else "📤 Поділитися", url=f"https://t.me/share/url?url={text_to_share.replace(' ', '%20')}")])
    return markup

async def create_stripe_link(user_id):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "uah",
                "product_data": {"name": "Monthly Meal Plan Subscription"},
                "unit_amount": 50000,  # 500 UAH
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{WEBHOOK_HOST}/success",
        cancel_url=f"{WEBHOOK_HOST}/cancel",
        metadata={"user_id": str(user_id)}
    )
    return session.url

async def generate_daily_recipe(user_data):
    return "Пример дневного рациона"

@dp.message(Command(commands=['start']))
async def start(message: types.Message, state: FSMContext):
    logging.info(f"Received /start from user {message.from_user.id}")
    try:
        await message.reply("💪 *Привет! Я MuscleMenu!* Помогу тебе набрать массу.\nДавай зарегистрируем тебя. Как тебя зовут?", parse_mode="Markdown")
        await state.set_state(UserForm.name)
        logging.info(f"Sent welcome message and set state for user {message.from_user.id}")
    except Exception as e:
        logging.error(f"Error in start handler for user {message.from_user.id}: {e}")

@dp.message(UserForm.name)
async def process_name(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Received message '{message.text}' from user {message.from_user.id} with state {current_state}")
    try:
        await state.update_data(name=message.text)
        await message.reply("Какой у тебя рост (в см)?")
        await state.set_state(UserForm.height)
        logging.info(f"Processed name and set height state for user {message.from_user.id}")
    except Exception as e:
        logging.error(f"Error in process_name for user {message.from_user.id}: {e}")

@dp.message(UserForm.height)
async def process_height(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Received message '{message.text}' from user {message.from_user.id} with state {current_state}")
    try:
        height = int(message.text)
        await state.update_data(height=height)
        await message.reply("Какой у тебя вес (в кг)?")
        await state.set_state(UserForm.weight)
        logging.info(f"Processed height and set weight state for user {message.from_user.id}")
    except ValueError:
        await message.reply("Пожалуйста, укажи число. Какой у тебя рост (в см)?")
    except Exception as e:
        logging.error(f"Error in process_height for user {message.from_user.id}: {e}")

@dp.message(UserForm.weight)
async def process_weight(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Received message '{message.text}' from user {message.from_user.id} with state {current_state}")
    try:
        weight = int(message.text)
        await state.update_data(weight=weight)
        await message.reply("Сколько тебе лет?")
        await state.set_state(UserForm.age)
        logging.info(f"Processed weight and set age state for user {message.from_user.id}")
    except ValueError:
        await message.reply("Пожалуйста, укажи число. Какой у тебя вес (в кг)?")
    except Exception as e:
        logging.error(f"Error in process_weight for user {message.from_user.id}: {e}")

@dp.message(UserForm.age)
async def process_age(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Received message '{message.text}' from user {message.from_user.id} with state {current_state}")
    try:
        age = int(message.text)
        await state.update_data(age=age)
        await message.reply("Какой у тебя уровень активности (низкая/средняя/высокая)?")
        await state.set_state(UserForm.activity)
        logging.info(f"Processed age and set activity state for user {message.from_user.id}")
    except ValueError:
        await message.reply("Пожалуйста, укажи число. Сколько тебе лет?")
    except Exception as e:
        logging.error(f"Error in process_age for user {message.from_user.id}: {e}")

@dp.message(UserForm.activity)
async def process_activity(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Received message '{message.text}' from user {message.from_user.id} with state {current_state}")
    activity = message.text.lower()
    if activity not in ["низкая", "средняя", "высокая", "low", "medium", "high", "низький", "середній", "високий"]:
        await message.reply("Укажи: низкая/средняя/высокая (или low/medium/high, низький/середній/високий). Какой у тебя уровень активности?")
        return
    try:
        await state.update_data(activity=activity)
        await message.reply("Сколько у тебя тренировок в неделю?")
        await state.set_state(UserForm.workouts)
        logging.info(f"Processed activity and set workouts state for user {message.from_user.id}")
    except Exception as e:
        logging.error(f"Error in process_activity for user {message.from_user.id}: {e}")

@dp.message(UserForm.workouts)
async def process_workouts(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Received message '{message.text}' from user {message.from_user.id} with state {current_state}")
    try:
        workouts = int(message.text)
        await state.update_data(workouts=workouts)
        await message.reply("Какие продукты ты любишь? (Например: 🍗 курица, 🥚 яйца, 🍚 рис)\nОставь пустым, если нет предпочтений.")
        await state.set_state(UserForm.preferences)
        logging.info(f"Processed workouts and set preferences state for user {message.from_user.id}")
    except ValueError:
        await message.reply("Пожалуйста, укажи число. Сколько у тебя тренировок в неделю?")
    except Exception as e:
        logging.error(f"Error in process_workouts for user {message.from_user.id}: {e}")

@dp.message(UserForm.preferences)
async def process_preferences(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Received message '{message.text}' from user {message.from_user.id} with state {current_state}")
    try:
        preferences = message.text.strip()
        data = await state.get_data()
        logging.info(f"Data from state: {data}")
        await db.add_user(
            message.from_user.id, data["name"], data["height"], data["weight"],
            data["age"], data["activity"], data["workouts"], preferences, "ru"
        )
        await message.reply("✅ *Данные сохранены!* Что дальше?", reply_markup=get_main_menu("ru"), parse_mode="Markdown")
        await state.clear()  # Используем clear() вместо finish()
        logging.info(f"Processed preferences and cleared state for user {message.from_user.id}")
    except Exception as e:
        logging.error(f"Error in process_preferences for user {message.from_user.id}: {e}")
        await message.reply("Произошла ошибка при сохранении данных. Попробуйте позже.")

@dp.callback_query(lambda c: c.data == "daily_plan")
async def daily_plan(callback: types.CallbackQuery):
    logging.info(f"Received callback 'daily_plan' from user {callback.from_user.id}")
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.message.reply("Сначала зарегистрируйтесь!", reply_markup=get_main_menu("ru"))
        return
    language = user["language"]
    subscription = await db.get_subscription(callback.from_user.id)
    now = datetime.now()
    logging.info(f"Subscription status for user {callback.from_user.id}: {subscription}")

    # Проверяем, есть ли пользователь в базе и предоставляем пробный доступ, если триал не использован
    if not subscription:
        await db.set_trial_used(callback.from_user.id)  # Устанавливаем trial_used=True для нового пользователя
        ration = await generate_daily_recipe(user)
        await callback.message.reply(ration, reply_markup=get_back_menu(ration, language), parse_mode="Markdown")
        logging.info(f"Provided trial daily plan for user {callback.from_user.id}")
    elif subscription and not subscription.get("trial_used", False):
        await db.set_trial_used(callback.from_user.id)  # Устанавливаем trial_used=True
        ration = await generate_daily_recipe(user)
        await callback.message.reply(ration, reply_markup=get_back_menu(ration, language), parse_mode="Markdown")
        logging.info(f"Provided trial daily plan for user {callback.from_user.id}")
    elif subscription and subscription["subscription_end"] and subscription["subscription_end"] > now:
        ration = await generate_daily_recipe(user)
        await callback.message.reply(ration, reply_markup=get_back_menu(ration, language), parse_mode="Markdown")
        logging.info(f"Provided subscribed daily plan for user {callback.from_user.id}")
    elif subscription and subscription["trial_used"]:
        markup = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="💫 Stars (50 XTR)", callback_data="pay_stars"),
             types.InlineKeyboardButton(text="💳 Карта (500 UAH)", callback_data="pay_stripe")],
            [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
        ])
        await callback.message.reply(
            "Подписка на 30 дней доступа к дневному рациону:",
            reply_markup=markup
        )
        logging.info(f"Offered subscription for user {callback.from_user.id}")
    else:
        await callback.message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu(language))

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    logging.info(f"Received callback 'back_to_main' from user {callback.from_user.id}")
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.message.reply("Сначала зарегистрируйтесь!", reply_markup=get_main_menu("ru"))
        return
    language = user["language"]
    await callback.message.reply(TEXTS[language]["back_to_main"], reply_markup=get_main_menu(language), parse_mode="Markdown")
    logging.info(f"Returned to main menu for user {callback.from_user.id}")

@dp.callback_query(lambda c: c.data == "switch_language")
async def switch_language(callback: types.CallbackQuery):
    logging.info(f"Received callback 'switch_language' from user {callback.from_user.id}")
    user = await db.get_user(callback.from_user.id)
    if not user:
        await callback.message.reply("Сначала зарегистрируйтесь!", reply_markup=get_main_menu("ru"))
        return

    current_language = user["language"]
    languages = ["ru", "en", "uk"]
    current_index = languages.index(current_language)
    new_language = languages[(current_index + 1) % 3]  # Переключаем на следующий язык

    # Обновляем язык в базе данных
    await db.update_user_language(callback.from_user.id, new_language)
    await callback.message.reply(TEXTS[new_language]["back_to_main"], reply_markup=get_main_menu(new_language), parse_mode="Markdown")
    logging.info(f"Switched language to {new_language} for user {callback.from_user.id}")

@dp.callback_query(lambda c: c.data == "pay_stars")
async def pay_stars(callback: types.CallbackQuery):
    logging.info(f"Received callback 'pay_stars' from user {callback.from_user.id}")
    user = await db.get_user(callback.from_user.id)
    language = user["language"]
    await bot.send_invoice(
        callback.from_user.id,
        title="Подписка на 30 дней",
        description="Доступ к дневному рациону на 30 дней",
        provider_token="",
        currency="XTR",
        prices=[types.LabeledPrice(label="Подписка", amount=50)],
        payload="subscription_stars"
    )

@dp.callback_query(lambda c: c.data == "pay_stripe")
async def pay_stripe(callback: types.CallbackQuery):
    logging.info(f"Received callback 'pay_stripe' from user {callback.from_user.id}")
    user = await db.get_user(callback.from_user.id)
    language = user["language"]
    payment_url = await create_stripe_link(callback.from_user.id)
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Оплатить", url=payment_url)]
    ])
    await callback.message.reply(
        "Перейди по ссылке для оплаты (500 UAH):",
        reply_markup=markup
    )

@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    logging.info(f"Received pre_checkout_query from user {pre_checkout_query.from_user.id}")
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message()
async def successful_payment(message: types.Message):
    logging.info(f"Received message with content_type: {message.content_type} from user {message.from_user.id}")
    if message.content_type != types.ContentType.SUCCESSFUL_PAYMENT:
        return
    user = await db.get_user(message.from_user.id)
    language = user["language"]
    subscription_end = datetime.now() + timedelta(days=30)
    await db.set_subscription(message.from_user.id, subscription_end)
    ration = await generate_daily_recipe(user)
    await message.reply(ration + f"\n\n{TEXTS[language]['payment_success']}", reply_markup=get_back_menu(ration, language), parse_mode="Markdown")
    logging.info(f"Payment processed for user {message.from_user.id}")

async def send_reminders():
    logging.info("Starting reminders task")
    while True:
        await asyncio.sleep(24 * 60 * 60)
        async with db.pool.acquire() as conn:
            users = await conn.fetch("SELECT user_id, language FROM users")
            now = datetime.now()
            for user in users:
                language = user["language"]
                quote = random.choice(QUOTES[language])
                subscription = await db.get_subscription(user["user_id"])
                msg = f"⏰ {quote}"
                if subscription and subscription["subscription_end"]:
                    days_left = (subscription["subscription_end"] - now).days
                    if days_left <= 3 and days_left > 0:
                        msg += f"\n\n{TEXTS[language]['subscription_end'].format(days=days_left)}"
                    elif days_left <= 0:
                        await db.reset_subscription(user["user_id"])
                        msg += f"\n\n{TEXTS[language]['subscription_expired']}"
                await bot.send_message(user["user_id"], msg, reply_markup=get_main_menu(language))

async def on_startup(_):
    logging.info("Entering on_startup function")
    try:
        await db.connect()
        logging.info("Database connected")
        await db.create_tables()
        logging.info("Tables created")
        await bot.set_webhook(WEBHOOK_URL)
        logging.info(f"Webhook set to {WEBHOOK_URL}")
        asyncio.create_task(send_reminders())
        logging.info("Reminders task created")
    except Exception as e:
        logging.error(f"Startup failed: {e}")
        raise

async def on_shutdown(_):
    logging.info("Shutting down bot...")
    await bot.delete_webhook()
    await db.pool.close()
    logging.info("Webhook stopped and DB closed")

# Создание приложения и запуск
app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
request_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
request_handler.register(app, path=WEBHOOK_PATH)
setup_application(app, dp, bot=bot)

if __name__ == "__main__":
    logging.info("Preparing to run bot...")
    logging.info("Web app setup complete")
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
