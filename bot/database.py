import os
import asyncpg
from dotenv import load_dotenv
import logging

load_dotenv()

class Database:
    def __init__(self):
        self.pool = None
        logging.info("Database instance created")

    async def connect(self):
        logging.info("Attempting to connect to database...")
        try:
            self.pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))
            logging.info("Database connection established successfully")
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            raise

    async def create_tables(self):
        logging.info("Creating tables...")
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    name TEXT NOT NULL,
                    height INTEGER NOT NULL,
                    weight INTEGER NOT NULL,
                    age INTEGER NOT NULL,
                    activity_level TEXT NOT NULL,
                    workouts_per_week INTEGER NOT NULL,
                    preferences TEXT,
                    language TEXT DEFAULT 'ru',
                    goal TEXT DEFAULT 'gain_mass',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS payments (
                    user_id BIGINT PRIMARY KEY,
                    payment_id TEXT,
                    trial_used BOOLEAN DEFAULT FALSE,
                    subscription_end TIMESTAMP
                );
            """)
            logging.info("Tables created successfully")

    async def add_user(self, user_id, name, height, weight, age, activity, workouts, preferences="", language="ru", goal="gain_mass"):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, name, height, weight, age, activity_level, workouts_per_week, preferences, language, goal)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (user_id) DO UPDATE SET 
                    name = EXCLUDED.name,
                    height = EXCLUDED.height,
                    weight = EXCLUDED.weight,
                    age = EXCLUDED.age,
                    activity_level = EXCLUDED.activity_level,
                    workouts_per_week = EXCLUDED.workouts_per_week,
                    preferences = EXCLUDED.preferences,
                    language = EXCLUDED.language,
                    goal = EXCLUDED.goal,
                    created_at = CURRENT_TIMESTAMP
            """, user_id, name, height, weight, age, activity, workouts, preferences, language, goal)
            logging.info(f"User {user_id} added or updated")
            await self.reset_trial(user_id)  # Сбрасываем триал для нового или обновлённого пользователя

    async def set_trial_used(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO payments (user_id, trial_used)
                VALUES ($1, TRUE)
                ON CONFLICT (user_id) DO UPDATE SET trial_used = TRUE
            """, user_id)
            logging.info(f"Trial status for user {user_id} set to True")

    async def set_subscription(self, user_id, subscription_end):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO payments (user_id, subscription_end, trial_used)
                VALUES ($1, $2, FALSE)
                ON CONFLICT (user_id) DO UPDATE SET subscription_end = $2, trial_used = FALSE
            """, user_id, subscription_end)
            logging.info(f"Subscription set for user {user_id} until {subscription_end}")

    async def get_subscription(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT trial_used, subscription_end FROM payments WHERE user_id = $1", user_id)

    async def reset_subscription(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE payments SET trial_used = FALSE, subscription_end = NULL, payment_id = NULL WHERE user_id = $1
            """, user_id)
            logging.info(f"Subscription reset for user {user_id}")

    async def reset_trial(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO payments (user_id, trial_used)
                VALUES ($1, FALSE)
                ON CONFLICT (user_id) DO UPDATE SET trial_used = FALSE
            """, user_id)
            logging.info(f"Trial reset for user {user_id}")

    async def get_user(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)

    async def update_user_language(self, user_id, language):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE users SET language = $2 WHERE user_id = $1
            """, user_id, language)
            logging.info(f"Language updated to {language} for user {user_id}")
