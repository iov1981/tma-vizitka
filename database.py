import aiosqlite

DB_NAME = "database.db"


async def init_db():
    """Создание таблиц пользователей и статистики"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def add_user(user_id: int, username: str, first_name: str):
    """Добавление пользователя, если его ещё нет"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, username, first_name)
            VALUES (?, ?, ?)
        """, (user_id, username, first_name))
        await db.commit()


async def log_event(user_id: int, event_type: str):
    """Логирование события (resume_download, lead_submit и т.д.)"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT INTO events (user_id, event_type)
            VALUES (?, ?)
        """, (user_id, event_type))
        await db.commit()


async def get_stats() -> dict:
    """Получение сводной статистики для администратора"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM events WHERE event_type = 'resume_download'") as cursor:
            resume_downloads = (await cursor.fetchone())[0]

        async with db.execute("SELECT COUNT(*) FROM events WHERE event_type = 'lead_submit'") as cursor:
            leads_count = (await cursor.fetchone())[0]

        return {
            "total_users": total_users,
            "resume_downloads": resume_downloads,
            "leads_count": leads_count
        }


async def get_all_user_ids() -> list:
    """Получение списка всех ID пользователей для рассылки"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]