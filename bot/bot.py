import logging
import os
import random
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from database import Database
from datetime import datetime, timedelta

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

# Инициализация бота и базы данных
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = Database()

# Ограничение запросов к API
API_REQUESTS_PER_DAY = 50
api_requests_today = 0
last_reset = datetime.now()

# База рецептов
RECIPES = [
    {"name": "Овсянка с бананом", "calories": 400, "protein": 10, "fat": 5, "carbs": 70, "recipe": "🥣 100г овсянки, 🍌 1 банан. Залей кипятком, дай настояться 5 мин."},
    {"name": "Курица с рисом", "calories": 600, "protein": 50, "fat": 10, "carbs": 60, "recipe": "🍗 150г куриной грудки, 🍚 80г риса. Отвари курицу и рис."},
    {"name": "Творог с яблоком", "calories": 350, "protein": 30, "fat": 5, "carbs": 40, "recipe": "🧀 150г творога 5%, 🍎 1 яблоко. Нарежь яблоко, смешай с творогом."},
    {"name": "Яичница с картофелем", "calories": 500, "protein": 20, "fat": 25, "carbs": 50, "recipe": "🥚 3 яйца, 🥔 200г картофеля. Обжарь яйца с вареным картофелем."},
]

# Мотивационные цитаты
QUOTES = {
    "ru": [
        "💪 Сила в дисциплине, а не в мотивации!",
        "🏋️‍♂️ Каждый шаг приближает тебя к цели!",
        "🍗 Ешь, чтобы расти!",
        "🏋️ Ты сильнее, чем думаешь!"
    ],
    "en": [
        "💪 Strength lies in discipline, not motivation!",
        "🏋️‍♂️ Every step brings you closer to your goal!",
        "🍗 Eat to grow!",
        "🏋️ You’re stronger than you think!"
    ],
    "uk": [
        "💪 Сила в дисципліні, а не в мотивації!",
        "🏋️‍♂️ Кожен крок наближає тебе до мети!",
        "🍗 Їж, щоб рости!",
        "🏋️ Ти сильніший, ніж думаєш!"
    ]
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
        "profile": "👤 *Личный кабинет*",
        "weekly_plan": "📅 *Твой недельный план питания* 💪",
        "daily_plan": "🍽 *Дневной рацион* 🍽",
        "update_weight": "⚖️ Укажи свой текущий вес (в кг):",
        "weight_updated": "✅ Вес обновлен! Проверь прогресс в личном кабинете.",
        "guess_game": "🎲 *Угадай калорийность!*",
        "guess_prompt": "Сколько калорий? Укажи число!",
        "guess_correct": "🎉 Отлично! Ты угадал почти точно!\nПравильный ответ: `{actual} ккал`\nТвой ответ: `{guess} ккал`",
        "guess_wrong": "🤔 Неплохо, но не совсем! Правильный ответ: `{actual} ккал`\nТвой ответ: `{guess} ккал`",
        "payment_success": "🎉 Спасибо за покупку!",
        "register_first": "Сначала зарегистрируйся!",
        "back_to_main": "💪 *MuscleMenu* — твой помощник в наборе массы!\nЧто дальше?",
        "my_day": "📊 *Мой день*",
        "random_tip": "💡 *Случайный совет*",
        "subscription_end": "⏰ Твоя подписка заканчивается через {days} дней! Продли за 500 UAH или 50 XTR.",
        "subscription_expired": "⚠️ Твоя подписка закончилась. Доступ к дневному рациону ограничен."
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
        "profile": "👤 *Profile*",
        "weekly_plan": "📅 *Your Weekly Nutrition Plan* 💪",
        "daily_plan": "🍽 *Daily Meal Plan* 🍽",
        "update_weight": "⚖️ Enter your current weight (in kg):",
        "weight_updated": "✅ Weight updated! Check your progress in your profile.",
        "guess_game": "🎲 *Guess the Calories!*",
        "guess_prompt": "How many calories? Enter a number!",
        "guess_correct": "🎉 Great job! Almost spot on!\nCorrect answer: `{actual} kcal`\nYour guess: `{guess} kcal`",
        "guess_wrong": "🤔 Not bad, but not quite! Correct answer: `{actual} kcal`\nYour guess: `{guess} kcal`",
        "payment_success": "🎉 Thank you for your purchase!",
        "register_first": "Register first!",
        "back_to_main": "💪 *MuscleMenu* — your mass-gaining assistant!\nWhat’s next?",
        "my_day": "📊 *My Day*",
        "random_tip": "💡 *Random Tip*",
        "subscription_end": "⏰ Your subscription ends in {days} days! Renew for 500 UAH or 50 XTR.",
        "subscription_expired": "⚠️ Your subscription has expired. Access to daily meal plans is restricted."
    },
    "uk": {
        "welcome": "💪 *Привіт! Я MuscleMenu!* Допоможу тобі набрати масу.\nДавай зареєструємо тебе. Як тебе звати?",
        "name": "Як тебе звати?",
        "height": "Який у тебе зріст (в см)?",
        "weight": "Яка у тебе вага (в кг)?",
        "age": "Скільки тобі років?",
        "activity": "Який у тебе рівень активності (низький/середній/високий)?",
        "workouts": "Скільки у тебе тренувань на тиждень?",
        "preferences": "Які продукти ти любиш? (Наприклад: 🍗 курка, 🥚 яйця, 🍚 рис)\nЗалиш порожнім, якщо немає вподобань.",
        "saved": "✅ *Дані збережено!* Що далі?",
        "profile": "👤 *Особистий кабінет*",
        "weekly_plan": "📅 *Твій тижневий план харчування* 💪",
        "daily_plan": "🍽 *Денний раціон* 🍽",
        "update_weight": "⚖️ Вкажи свою поточну вагу (в кг):",
        "weight_updated": "✅ Вага оновлена! Перевір прогрес у особистому кабінеті.",
        "guess_game": "🎲 *Вгадай калорійність!*",
        "guess_prompt": "Скільки калорій? Вкажи число!",
        "guess_correct": "🎉 Чудово! Ти вгадав майже точно!\nПравильна відповідь: `{actual} ккал`\nТвоя відповідь: `{guess} ккал`",
        "guess_wrong": "🤔 Непогано, але не зовсім! Правильна відповідь: `{actual} ккал`\nТвоя відповідь: `{guess} ккал`",
        "payment_success": "🎉 Дякую за покупку!",
        "register_first": "Спочатку зареєструйся!",
        "back_to_main": "💪 *MuscleMenu* — твій помічник у наборі маси!\nЩо далі?",
        "my_day": "📊 *Мій день*",
        "random_tip": "💡 *Випадкова порада*",
        "subscription_end": "⏰ Твоя підписка закінчується через {days} днів! Продовж за 500 UAH або 50 XTR.",
        "subscription_expired": "⚠️ Твоя підписка закінчилася. Доступ до денного раціону обмежено."
    }
}

# Состояния для опроса
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
    return InlineKeyboardMarkup().row(
        InlineKeyboardButton("📅", callback_data="weekly_plan"),
        InlineKeyboardButton("🍽", callback_data="daily_plan")
    ).row(
        InlineKeyboardButton("👤", callback_data="profile"),
        InlineKeyboardButton("⚖️", callback_data="update_weight")
    ).row(
        InlineKeyboardButton("🎲", callback_data="guess_game"),
        InlineKeyboardButton("📊", callback_data="my_day")
    ).row(
        InlineKeyboardButton("💡", callback_data="random_tip"),
        InlineKeyboardButton("🌐 Язык" if language == "ru" else "🌐 Language" if language == "en" else "🌐 Мова", callback_data="switch_language")
    )

# Меню с кнопкой "Назад" и "Поделиться"
def get_back_menu(text_to_share="", language="ru"):
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("⬅️ Назад" if language == "ru" else "⬅️ Back" if language == "en" else "⬅️ Назад", callback_data="back_to_main"))
    if text_to_share:
        markup.add(InlineKeyboardButton("📤 Поделиться" if language == "ru" else "📤 Share" if language == "en" else "📤 Поділитися", url=f"https://t.me/share/url?url={text_to_share.replace(' ', '%20')}"))
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

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user = await db.get_user(message.from_user.id)
    language = user["language"] if user else "ru"
    await message.reply(TEXTS[language]["welcome"], parse_mode="Markdown")
    await UserForm.name.set()

@dp.message_handler(state=UserForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    user = await db.get_user(message.from_user.id)
    language = user["language"] if user else "ru"
    await message.reply(TEXTS[language]["height"])
    await UserForm.height.set()

@dp.message_handler(state=UserForm.height)
async def process_height(message: types.Message, state: FSMContext):
    try:
        height = int(message.text)
        await state.update_data(height=height)
        user = await db.get_user(message.from_user.id)
        language = user["language"] if user else "ru"
        await message.reply(TEXTS[language]["weight"])
        await UserForm.weight.set()
    except ValueError:
        user = await db.get_user(message.from_user.id)
        language = user["language"] if user else "ru"
        await message.reply(f"Пожалуйста, укажи число. {TEXTS[language]['height']}")

@dp.message_handler(state=UserForm.weight)
async def process_weight(message: types.Message, state: FSMContext):
    try:
        weight = int(message.text)
        await state.update_data(weight=weight)
        user = await db.get_user(message.from_user.id)
        language = user["language"] if user else "ru"
        await message.reply(TEXTS[language]["age"])
        await UserForm.age.set()
    except ValueError:
        user = await db.get_user(message.from_user.id)
        language = user["language"] if user else "ru"
        await message.reply(f"Пожалуйста, укажи число. {TEXTS[language]['weight']}")

@dp.message_handler(state=UserForm.age)
async def process_age(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
        await state.update_data(age=age)
        user = await db.get_user(message.from_user.id)
        language = user["language"] if user else "ru"
        await message.reply(TEXTS[language]["activity"])
        await UserForm.activity.set()
    except ValueError:
        user = await db.get_user(message.from_user.id)
        language = user["language"] if user else "ru"
        await message.reply(f"Пожалуйста, укажи число. {TEXTS[language]['age']}")

@dp.message_handler(state=UserForm.activity)
async def process_activity(message: types.Message, state: FSMContext):
    activity = message.text.lower()
    if activity not in ["низкая", "средняя", "высокая", "low", "medium", "high", "низький", "середній", "високий"]:
        user = await db.get_user(message.from_user.id)
        language = user["language"] if user else "ru"
        await message.reply(f"Укажи: низкая/средняя/высокая (или low/medium/high, низький/середній/високий). {TEXTS[language]['activity']}")
        return
    await state.update_data(activity=activity)
    user = await db.get_user(message.from_user.id)
    language = user["language"] if user else "ru"
    await message.reply(TEXTS[language]["workouts"])
    await UserForm.workouts.set()

@dp.message_handler(state=UserForm.workouts)
async def process_workouts(message: types.Message, state: FSMContext):
    try:
        workouts = int(message.text)
        await state.update_data(workouts=workouts)
        user = await db.get_user(message.from_user.id)
        language = user["language"] if user else "ru"
        await message.reply(TEXTS[language]["preferences"])
        await UserForm.preferences.set()
    except ValueError:
        user = await db.get_user(message.from_user.id)
        language = user["language"] if user else "ru"
        await message.reply(f"Пожалуйста, укажи число. {TEXTS[language]['workouts']}")

@dp.message_handler(state=UserForm.preferences)
async def process_preferences(message: types.Message, state: FSMContext):
    preferences = message.text.strip()
    data = await state.get_data()
    user = await db.get_user(message.from_user.id)
    language = user["language"] if user else "ru"
    await db.add_user(
        message.from_user.id, data["name"], data["height"], data["weight"],
        data["age"], data["activity"], data["workouts"], preferences, language
    )
    await message.reply(TEXTS[language]["saved"], reply_markup=get_main_menu(language), parse_mode="Markdown")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == "daily_plan")
async def daily_plan(callback: types.CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    if not user:
        language = "ru"
        await callback.message.reply(TEXTS[language]["register_first"], reply_markup=get_main_menu(language))
        return
    language = user["language"]
    subscription = await db.get_subscription(callback.from_user.id)
    now = datetime.now()

    if subscription and subscription["subscription_end"] and subscription["subscription_end"] > now:
        ration = await generate_daily_recipe(user)
        await callback.message.reply(ration, reply_markup=get_back_menu(ration, language), parse_mode="Markdown")
    elif subscription and subscription["trial_used"]:
        markup = InlineKeyboardMarkup().row(
            InlineKeyboardButton("💫 Stars (50 XTR)", callback_data="pay_stars"),
            InlineKeyboardButton("💳 Карта (500 UAH)", callback_data="pay_stripe")
        ).add(InlineKeyboardButton("⬅️ Назад" if language == "ru" else "⬅️ Back" if language == "en" else "⬅️ Назад", callback_data="back_to_main"))
        await callback.message.reply(
            "Подписка на 30 дней доступа к дневному рациону:" if language == "ru" else
            "Subscription for 30 days of daily meal plans:" if language == "en" else
            "Підписка на 30 днів доступу до денного раціону:",
            reply_markup=markup
        )
    else:
        await db.set_trial_used(callback.from_user.id)
        ration = await generate_daily_recipe(user)
        await callback.message.reply(ration, reply_markup=get_back_menu(ration, language), parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data == "pay_stars")
async def pay_stars(callback: types.CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    language = user["language"]
    await bot.send_invoice(
        callback.from_user.id,
        title="Подписка на 30 дней" if language == "ru" else "30-Day Subscription" if language == "en" else "Підписка на 30 днів",
        description="Доступ к дневному рациону на 30 дней" if language == "ru" else "Access to daily meal plans for 30 days" if language == "en" else "Доступ до денного раціону на 30 днів",
        provider_token="",
        currency="XTR",
        prices=[types.LabeledPrice(label="Подписка" if language == "ru" else "Subscription" if language == "en" else "Підписка", amount=50)],
        payload="subscription_stars"
    )

@dp.callback_query_handler(lambda c: c.data == "pay_stripe")
async def pay_stripe(callback: types.CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    language = user["language"]
    payment_url = await create_stripe_link(callback.from_user.id)
    markup = InlineKeyboardMarkup().add(InlineKeyboardButton("Оплатить" if language == "ru" else "Pay" if language == "en" else "Сплатити", url=payment_url))
    await callback.message.reply(
        "Перейди по ссылке для оплаты (500 UAH):" if language == "ru" else
        "Follow the link to pay (500 UAH):" if language == "en" else
        "Перейди за посиланням для оплати (500 UAH):",
        reply_markup=markup
    )

@dp.pre_checkout_query_handler()
async def pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    user = await db.get_user(message.from_user.id)
    language = user["language"]
    subscription_end = datetime.now() + timedelta(days=30)
    await db.set_subscription(message.from_user.id, subscription_end)
    ration = await generate_daily_recipe(user)
    await message.reply(ration + f"\n\n{TEXTS[language]['payment_success']}", reply_markup=get_back_menu(ration, language), parse_mode="Markdown")

async def send_reminders():
    while True:
        await asyncio.sleep(24 * 60 * 60)  # Каждые 24 часа
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
    await db.connect()
    await db.create_tables()
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(send_reminders())
    logging.info(f"Webhook установлен на {WEBHOOK_URL}")

async def on_shutdown(_):
    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()
    await db.pool.close()
    logging.info("Webhook остановлен")

if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
