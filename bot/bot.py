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
    {
        "name": {
            "ru": "Овсянка с бананом",
            "en": "Oatmeal with Banana",
            "uk": "Вівсянка з бананом"
        },
        "calories": 400,
        "protein": 10,
        "fat": 5,
        "carbs": 70,
        "recipe": {
            "ru": "🥣 100г овсянки, 🍌 1 банан. Залей кипятком, дай настояться 5 мин.",
            "en": "🥣 100g oatmeal, 🍌 1 banana. Pour boiling water, let it steep for 5 min.",
            "uk": "🥣 100г вівсянки, 🍌 1 банан. Залий окропом, дай настоятися 5 хв."
        }
    },
    {
        "name": {
            "ru": "Курица с рисом",
            "en": "Chicken with Rice",
            "uk": "Курка з рисом"
        },
        "calories": 600,
        "protein": 50,
        "fat": 10,
        "carbs": 60,
        "recipe": {
            "ru": "🍗 150г куриной грудки, 🍚 80г риса. Отвари курицу и рис.",
            "en": "🍗 150g chicken breast, 🍚 80g rice. Boil chicken and rice.",
            "uk": "🍗 150г курячої грудки, 🍚 80г рису. Відвари курку та рис."
        }
    },
    {
        "name": {
            "ru": "Творог с яблоком",
            "en": "Cottage Cheese with Apple",
            "uk": "Творог з яблуком"
        },
        "calories": 350,
        "protein": 30,
        "fat": 5,
        "carbs": 40,
        "recipe": {
            "ru": "🧀 150г творога 5%, 🍎 1 яблоко. Нарежь яблоко, смешай с творогом.",
            "en": "🧀 150g 5% cottage cheese, 🍎 1 apple. Chop the apple, mix with cottage cheese.",
            "uk": "🧀 150г творогу 5%, 🍎 1 яблуко. Наріж яблуко, змішай з творогом."
        }
    },
    {
        "name": {
            "ru": "Яичница с картофелем",
            "en": "Scrambled Eggs with Potatoes",
            "uk": "Яєчня з картоплею"
        },
        "calories": 500,
        "protein": 20,
        "fat": 25,
        "carbs": 50,
        "recipe": {
            "ru": "🥚 3 яйца, 🥔 200г картофеля. Обжарь яйца с вареным картофелем.",
            "en": "🥚 3 eggs, 🥔 200g potatoes. Fry eggs with boiled potatoes.",
            "uk": "🥚 3 яйця, 🥔 200г картоплі. Обсмаж яйця з вареною картоплею."
        }
    },
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
        "goal": "Какая твоя цель? (набор массы/снижение веса/поддержание веса)",
        "preferences": "Какие продукты ты любиш? (Например: 🍗 курица, 🥚 яйца, 🍚 рис)\nОставь пустым, если нет предпочтений.",
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
        "goal": "What’s your goal? (weight gain/weight loss/weight maintenance)",
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
        "goal": "Яка твоя мета? (набір маси/схуднення/підтримка ваги)",
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
    goal = State()  # Добавляем состояние для цели
    preferences = State()

# Главное меню
def get_main_menu(language="ru"):
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🍽", callback_data="daily_plan")],
        [types.InlineKeyboardButton(text="🌐 Язык" if language == "ru" else "🌐 Language" if language == "en" else "🌐 Мова", callback_data="switch_language")]
    ])

# Быстрое меню
def get_quick_menu(language="ru"):
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Daily Plan" if language == "en" else "Дневной рацион" if language == "ru" else "Денний раціон")],
            [types.KeyboardButton(text="🌐 Language" if language == "en" else "🌐 Язык" if language == "ru" else "🌐 Мова")],
            [types.KeyboardButton(text="Back" if language == "en" else "Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

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
    """
    Генерирует дневной рацион на основе данных пользователя.
    Учитывает возраст, вес, рост, активность, тренировки, предпочтения и цель.
    """
    height = user_data["height"]
    weight = user_data["weight"]
    age = user_data["age"]
    activity_level = user_data["activity_level"].lower()
    workouts_per_week = user_data["workouts_per_week"]
    preferences = user_data.get("preferences", "").lower().split(", ") if user_data.get("preferences") else []
    goal = user_data.get("goal", "gain_mass")
    language = user_data.get("language", "ru")  # Получаем язык пользователя

    # Расчёт базового уровня метаболизма (BMR) по формуле Миффлина-Сан Жеора
    bmr = 10 * weight + 6.25 * height - 5 * age + 5  # Для мужчин, для женщин: + (-161)
    activity_multipliers = {
        "низкая": 1.2,
        "средняя": 1.55,
        "высокая": 1.9,
        "low": 1.2,
        "medium": 1.55,
        "high": 1.9,
        "низький": 1.2,
        "середній": 1.55,
        "високий": 1.9
    }
    total_calories = bmr * activity_multipliers[activity_level] + (workouts_per_week * 300)  # Добавляем калории для тренировок

    # Корректируем калории в зависимости от цели
    if goal == "gain_mass":
        total_calories *= 1.15  # Набор массы — +15%
    elif goal == "lose_weight":
        total_calories *= 0.85  # Снижение веса — -15%
    elif goal == "maintain_weight":
        total_calories *= 1.0  # Поддержание веса — без изменений

    # Распределяем калории на макронутриенты (пример: 40% углеводы, 30% белки, 30% жиры)
    carbs_cal = total_calories * 0.4 / 4  # Углеводы (4 ккал/г)
    protein_cal = total_calories * 0.3 / 4  # Белки (4 ккал/г)
    fat_cal = total_calories * 0.3 / 9  # Жиры (9 ккал/г)

    # Фильтруем рецепты по предпочтениям, если они указаны
    available_recipes = RECIPES
    if preferences:
        available_recipes = [recipe for recipe in RECIPES if any(pref in recipe["recipe"]["ru"].lower() for pref in preferences)]

    if not available_recipes:
        available_recipes = RECIPES  # Если предпочтения не подходят, используем все рецепты

    # Разбиваем общий каллораж на 4 приёма пищи (например, завтрак, обед, ужин, перекус)
    meals_per_day = 4
    calories_per_meal = total_calories / meals_per_day

    # Выбираем случайные рецепты для каждого приёма пищи, чтобы покрыть дневную норму калорий
    selected_recipes = []
    total_cal = 0
    for _ in range(meals_per_day):
        meal_recipes = []
        meal_cal = 0
        for recipe in available_recipes:
            if meal_cal < calories_per_meal * 0.9:  # Оставляем 10% для гибкости в каждом приёме
                meal_recipes.append(recipe)
                meal_cal += recipe["calories"]
            if len(meal_recipes) >= 1:  # Ограничиваем до 1 блюда на приём пищи
                break
        selected_recipes.append(meal_recipes[0] if meal_recipes else random.choice(available_recipes))
        total_cal += meal_cal

    # Формируем текст рациона
    meal_names = {
        "ru": ["Завтрак", "Обед", "Ужин", "Перекус"],
        "en": ["Breakfast", "Lunch", "Dinner", "Snack"],
        "uk": ["Сніданок", "Обід", "Вечеря", "Перекус"]
    }
    goal_text = {
        "ru": f"Цель: {goal.replace('_', ' ').title()}",
        "en": f"Goal: {goal.replace('_', ' ').title()}",
        "uk": f"Мета: {goal.replace('_', ' ').title()}"
    }
    ration_text = f"🍽 *{'Дневной рацион' if language == 'ru' else 'Daily Meal Plan' if language == 'en' else 'Денний раціон'}*\n\n{goal_text[language]}\n\n"
    for i, recipe in enumerate(selected_recipes):
        ration_text += f"- {meal_names[language][i]}: {recipe['name'][language]} ({recipe['calories']} ккал, белки: {recipe['protein']}г, жиры: {recipe['fat']}г, углеводы: {recipe['carbs']}г)\n  {recipe['recipe'][language]}\n\n"
    ration_text += f"Общая калорийность: {total_cal:.0f} ккал (примерно {total_calories:.0f} ккал необходимо для {goal.replace('_', ' ').title()})."

    return ration_text

@dp.message(Command(commands=['start']))
async def start(message: types.Message, state: FSMContext):
    logging.info(f"Received /start from user {message.from_user.id}")
    try:
        # Проверяем, существует ли пользователь в базе
        user = await db.get_user(message.from_user.id)
        if user:
            language = user["language"]
            subscription = await db.get_subscription(message.from_user.id)
            now = datetime.now()
            logging.info(f"User {message.from_user.id} already exists. Subscription status: {subscription}")

            # Если есть активная подписка или триал не использован, предлагаем меню
            if subscription and subscription["subscription_end"] and subscription["subscription_end"] > now:
                await message.reply(TEXTS[language]["back_to_main"], reply_markup=get_quick_menu(language), parse_mode="Markdown")
                logging.info(f"User {message.from_user.id} has active subscription, showing main menu with quick keyboard")
                return
            elif not subscription or not subscription["trial_used"]:
                await db.reset_trial(message.from_user.id)  # Сбрасываем триал для нового доступа
                await message.reply(TEXTS[language]["back_to_main"], reply_markup=get_quick_menu(language), parse_mode="Markdown")
                logging.info(f"User {message.from_user.id} has no trial used, showing main menu with quick keyboard with trial reset")
                return

            # Если триал использован, предлагаем подписку
            markup = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="💫 Stars (50 XTR)", callback_data="pay_stars"),
                 types.InlineKeyboardButton(text="💳 Карта (500 UAH)", callback_data="pay_stripe")],
                [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
            ])
            await message.reply(
                TEXTS[language]["daily_plan"] if language in TEXTS and "daily_plan" in TEXTS[language] else "Подписка на 30 дней доступа к дневному рациону:",
                reply_markup=markup
            )
            logging.info(f"Offered subscription for user {message.from_user.id} because trial_used=True")
            return

        # Если пользователь не найден, начинаем регистрацию
        await message.reply("💪 *Привет! Я MuscleMenu!* Помогу тебе набрать массу.\nДавай зарегистрируем тебя. Как тебя зовут?", reply_markup=get_quick_menu("ru"), parse_mode="Markdown")
        await state.set_state(UserForm.name)
        logging.info(f"Sent welcome message and set state for user {message.from_user.id} with quick keyboard")
    except Exception as e:
        logging.error(f"Error in start handler for user {message.from_user.id}: {e}")
        await message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_quick_menu("ru"), parse_mode="Markdown")

@dp.message(UserForm.name)
async def process_name(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Received message '{message.text}' from user {message.from_user.id} with state {current_state}")
    try:
        await state.update_data(name=message.text)
        await message.reply("Какой у тебя рост (в см)?", reply_markup=get_quick_menu("ru"))
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
        await message.reply("Какой у тебя вес (в кг)?", reply_markup=get_quick_menu("ru"))
        await state.set_state(UserForm.weight)
        logging.info(f"Processed height and set weight state for user {message.from_user.id}")
    except ValueError:
        await message.reply("Пожалуйста, укажи число. Какой у тебя рост (в см)?", reply_markup=get_quick_menu("ru"))
    except Exception as e:
        logging.error(f"Error in process_height for user {message.from_user.id}: {e}")

@dp.message(UserForm.weight)
async def process_weight(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Received message '{message.text}' from user {message.from_user.id} with state {current_state}")
    try:
        weight = int(message.text)
        await state.update_data(weight=weight)
        await message.reply("Сколько тебе лет?", reply_markup=get_quick_menu("ru"))
        await state.set_state(UserForm.age)
        logging.info(f"Processed weight and set age state for user {message.from_user.id}")
    except ValueError:
        await message.reply("Пожалуйста, укажи число. Какой у тебя вес (в кг)?", reply_markup=get_quick_menu("ru"))
    except Exception as e:
        logging.error(f"Error in process_weight for user {message.from_user.id}: {e}")

@dp.message(UserForm.age)
async def process_age(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Received message '{message.text}' from user {message.from_user.id} with state {current_state}")
    try:
        age = int(message.text)
        await state.update_data(age=age)
        await message.reply("Какой у тебя уровень активности (низкая/средняя/высокая)?", reply_markup=get_quick_menu("ru"))
        await state.set_state(UserForm.activity)
        logging.info(f"Processed age and set activity state for user {message.from_user.id}")
    except ValueError:
        await message.reply("Пожалуйста, укажи число. Сколько тебе лет?", reply_markup=get_quick_menu("ru"))
    except Exception as e:
        logging.error(f"Error in process_age for user {message.from_user.id}: {e}")

@dp.message(UserForm.activity)
async def process_activity(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Received message '{message.text}' from user {message.from_user.id} with state {current_state}")
    activity_level = message.text.lower()
    if activity_level not in ["низкая", "средняя", "высокая", "low", "medium", "high", "низький", "середній", "високий"]:
        await message.reply("Укажи: низкая/средняя/высокая (или low/medium/high, низький/середній/високий). Какой у тебя уровень активности?", reply_markup=get_quick_menu("ru"))
        return
    try:
        await state.update_data(activity_level=activity_level)
        await message.reply("Сколько у тебя тренировок в неделю?", reply_markup=get_quick_menu("ru"))
        await state.set_state(UserForm.workouts)
        logging.info(f"Processed activity_level and set workouts state for user {message.from_user.id}")
    except Exception as e:
        logging.error(f"Error in process_activity for user {message.from_user.id}: {e}")

@dp.message(UserForm.workouts)
async def process_workouts(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Received message '{message.text}' from user {message.from_user.id} with state {current_state}")
    try:
        workouts_per_week = int(message.text)
        await state.update_data(workouts_per_week=workouts_per_week)
        await message.reply("Какая твоя цель? (набор массы/снижение веса/поддержание веса)\nУкажи на русском, английском или украинском (например: набор массы, weight loss, набір маси).", reply_markup=get_quick_menu("ru"))
        await state.set_state(UserForm.goal)
        logging.info(f"Processed workouts_per_week and set goal state for user {message.from_user.id}")
    except ValueError:
        await message.reply("Пожалуйста, укажи число. Сколько у тебя тренировок в неделю?", reply_markup=get_quick_menu("ru"))
    except Exception as e:
        logging.error(f"Error in process_workouts for user {message.from_user.id}: {e}")

@dp.message(UserForm.goal)
async def process_goal(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    logging.info(f"Received message '{message.text}' from user {message.from_user.id} with state {current_state}")
    goal = message.text.lower()
    valid_goals = {
        "набор массы": "gain_mass",
        "снижение веса": "lose_weight",
        "поддержание веса": "maintain_weight",
        "weight gain": "gain_mass",
        "weight loss": "lose_weight",
        "weight maintenance": "maintain_weight",
        "набір маси": "gain_mass",
        "схуднення": "lose_weight",
        "підтримка ваги": "maintain_weight"
    }
    if goal not in valid_goals:
        await message.reply("Пожалуйста, укажи правильную цель: набор массы/снижение веса/поддержание веса (или аналог на английском/украинском).", reply_markup=get_quick_menu("ru"))
        return
    try:
        await state.update_data(goal=valid_goals[goal])
        await message.reply("Какие продукты ты любиш? (Например: 🍗 курица, 🥚 яйца, 🍚 рис)\nОставь пустым, если нет предпочтений.", reply_markup=get_quick_menu("ru"))
        await state.set_state(UserForm.preferences)
        logging.info(f"Processed goal and set preferences state for user {message.from_user.id}")
    except Exception as e:
        logging.error(f"Error in process_goal for user {message.from_user.id}: {e}")

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
            data["age"], data["activity_level"], data["workouts_per_week"], preferences, "ru", data.get("goal", "gain_mass")
        )
        await message.reply("✅ *Данные сохранены!* Что дальше?", reply_markup=get_quick_menu("ru"), parse_mode="Markdown")
        await state.clear()
        logging.info(f"Processed preferences and cleared state for user {message.from_user.id}")
    except Exception as e:
        logging.error(f"Error in process_preferences for user {message.from_user.id}: {e}")
        await message.reply("Произошла ошибка при сохранении данных. Попробуйте позже.", reply_markup=get_quick_menu("ru"))

@dp.callback_query(lambda c: c.data == "daily_plan")
async def daily_plan(callback: types.CallbackQuery):
    logging.info(f"Received callback 'daily_plan' from user {callback.from_user.id}")
    try:
        user = await db.get_user(callback.from_user.id)
        if not user:
            await callback.message.reply("Сначала зарегистрируйтесь!", reply_markup=get_main_menu("ru"))
            return
        language = user["language"]
        subscription = await db.get_subscription(callback.from_user.id)
        now = datetime.now()
        logging.info(f"Subscription status for user {callback.from_user.id}: {subscription}")

        # Временная логика для тестирования: предоставляем бесплатный доступ для user_id 898243089
        if callback.from_user.id == 898243089:
            # Устанавливаем неограниченный доступ (например, до 2030 года)
            if not subscription or not subscription["subscription_end"] or subscription["subscription_end"] < now:
                await db.set_subscription(callback.from_user.id, datetime(2030, 1, 1, 0, 0))  # Установим подписку до 2030 года
                subscription = await db.get_subscription(callback.from_user.id)  # Обновляем данные
            ration = await generate_daily_recipe(user)
            await callback.message.reply(ration, reply_markup=get_back_menu(ration, language), parse_mode="Markdown")
            logging.info(f"Provided free trial daily plan for user {callback.from_user.id} (testing mode)")
            return

        # Обычная логика для других пользователей
        if not subscription or (subscription and not subscription["trial_used"]):
            await db.set_trial_used(callback.from_user.id)  # Устанавливаем, что триал использован
            ration = await generate_daily_recipe(user)
            await callback.message.reply(ration, reply_markup=get_back_menu(ration, language), parse_mode="Markdown")
            logging.info(f"Provided trial daily plan for user {callback.from_user.id}")
        elif subscription and subscription["subscription_end"] and subscription["subscription_end"] > now:
            ration = await generate_daily_recipe(user)
            await callback.message.reply(ration, reply_markup=get_back_menu(ration, language), parse_mode="Markdown")
            logging.info(f"Provided subscribed daily plan for user {callback.from_user.id}")
        else:
            markup = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="💫 Stars (50 XTR)", callback_data="pay_stars"),
                 types.InlineKeyboardButton(text="💳 Карта (500 UAH)", callback_data="pay_stripe")],
                [types.InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main")]
            ])
            await callback.message.reply(
                TEXTS[language]["daily_plan"] if language in TEXTS and "daily_plan" in TEXTS[language] else "Подписка на 30 дней доступа к дневному рациону:",
                reply_markup=markup
            )
            logging.info(f"Offered subscription for user {callback.from_user.id}")
    except Exception as e:
        logging.error(f"Error in daily_plan for user {callback.from_user.id}: {e}")
        await callback.message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_main_menu("ru"))

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    logging.info(f"Received callback 'back_to_main' from user {callback.from_user.id}")
    try:
        user = await db.get_user(callback.from_user.id)
        if not user:
            await callback.message.reply("Сначала зарегистрируйтесь!", reply_markup=get_main_menu("ru"))
            return
        language = user["language"]
        await callback.message.reply(TEXTS[language]["back_to_main"], reply_markup=get_quick_menu(language), parse_mode="Markdown")
        logging.info(f"Returned to main menu for user {callback.from_user.id}")
    except Exception as e:
        logging.error(f"Error in back_to_main for user {callback.from_user.id}: {e}")
        await callback.message.reply("Произошла ошибка. Попробуйте позже.", reply_markup=get_quick_menu("ru"))

@dp.callback_query(lambda c: c.data == "switch_language")
async def switch_language(callback: types.CallbackQuery):
    logging.info(f"Received callback 'switch_language' from user {callback.from_user.id}")
    try:
        user = await db.get_user(callback.from_user.id)
        if not user:
            await callback.message
