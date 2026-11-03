import datetime
import aiosqlite

DB_NAME = "database.db"


async def init_db():
    """Инициализация таблиц пользователей и отзывов."""
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица пользователей для статистики
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                first_seen DATE
            )
        """
        )
        # Таблица отзывов от посетителей
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                full_name TEXT,
                username TEXT,
                rating INTEGER,
                review_text TEXT,
                created_at DATE
            )
        """
        )
        await db.commit()


async def add_user(user_id: int, username: str | None, full_name: str):
    """Фиксация нового пользователя при старте бота."""
    today = datetime.date.today().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users (user_id, username, full_name, first_seen)
            VALUES (?, ?, ?, ?)
        """,
            (user_id, username, full_name, today),
        )
        await db.commit()


async def get_stats() -> dict:
    """Получение статистики посетителей."""
    today = datetime.date.today().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]

        async with db.execute(
            "SELECT COUNT(*) FROM users WHERE first_seen = ?", (today,)
        ) as cursor:
            today_users = (await cursor.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM reviews") as cursor:
            total_reviews = (await cursor.fetchone())[0]

        return {
            "total": total_users,
            "today": today_users,
            "reviews": total_reviews,
        }


async def save_review(
    user_id: int,
    full_name: str,
    username: str | None,
    rating: int,
    review_text: str,
):
    """Сохранение отзыва в базу данных."""
    today = datetime.date.today().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO reviews (user_id, full_name, username, rating, review_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (user_id, full_name, username, rating, review_text, today),
        )
        await db.commit()