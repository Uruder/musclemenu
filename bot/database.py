import asyncpg
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"))

    async def create_tables(self):
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS payments (
                    user_id BIGINT PRIMARY KEY,
                    payment_id TEXT,
                    trial_used BOOLEAN DEFAULT FALSE,
                    subscription_end TIMESTAMP
                );
            """)

    async def add_user(self, user_id, name, height, weight, age, activity, workouts, preferences="", language="ru"):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, name, height, weight, age, activity_level, workouts_per_week, preferences, language)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (user_id) DO NOTHING
            """, user_id, name, height, weight, age, activity, workouts, preferences, language)

    async def set_trial_used(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO payments (user_id, trial_used)
                VALUES ($1, TRUE)
                ON CONFLICT (user_id) DO UPDATE SET trial_used = TRUE
            """, user_id)

    async def set_subscription(self, user_id, subscription_end):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO payments (user_id, subscription_end)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO UPDATE SET subscription_end = $2, trial_used = FALSE
            """, user_id, subscription_end)

    async def get_subscription(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT trial_used, subscription_end FROM payments WHERE user_id = $1", user_id)

    async def reset_subscription(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE payments SET trial_used = TRUE, subscription_end = NULL WHERE user_id = $1", user_id)

    async def get_user(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
