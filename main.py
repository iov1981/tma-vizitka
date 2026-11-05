import os
import sys
import json
import asyncio
from aiohttp import web
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo
)

import database as db

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
PORT = int(os.getenv("PORT", 8080))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://tma-vizitka.onrender.com")

if not BOT_TOKEN:
    print("Ошибка: BOT_TOKEN не задан в переменных окружения или .env файле!")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ================= ВЕБ-СЕРВЕР KEEP-ALIVE И РАЗДАЧА INDEX.HTML =================
async def handle_ping(request):
    """Эндпоинт для cron-job проверки и раздачи Mini App"""
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    return web.Response(text="Bot is running!", content_type="text/plain")


async def start_web_server():
    """Запуск фонового aiohttp сервера на порту 8080"""
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Веб-сервер успешно запущен на порту {PORT}")


# ================= КЛАВИАТУРЫ =================
def get_main_keyboard(is_admin: bool = False):
    """Главная клавиатура бота: для админа скрывает форму связи в TMA"""
    web_app_url = f"{RENDER_EXTERNAL_URL}?admin=true" if is_admin else RENDER_EXTERNAL_URL

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📱 Открыть визитку", web_app=WebAppInfo(url=web_app_url))
            ],
            [
                KeyboardButton(text="📄 Скачать резюме (PDF)"),
                KeyboardButton(text="ℹ️ Обо мне")
            ]
        ],
        resize_keyboard=True
    )


def get_inline_links():
    """Инлайн-кнопки со ссылками на репозиторий"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🐙 GitHub репозиторий", url="https://github.com/iov1981/tma-vizitka")
            ]
        ]
    )


# ================= ХЕНДЛЕРЫ БОТА =================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    is_admin = bool(ADMIN_ID and str(user.id) == str(ADMIN_ID))

    # Сохраняем пользователя в SQLite
    await db.add_user(user.id, user.username, user.first_name)

    # Оповещение администратора только если зашел сторонний клиент
    if ADMIN_ID and not is_admin:
        try:
            await bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🔔 Пользователь @{user.username or 'нет'} (ID: {user.id}) нажал /start"
            )
        except Exception:
            pass

    welcome_text = (
        f"Здравствуйте, {user.first_name}!\n\n"
        "Добро пожаловать в бота-визитку.\n"
        "Здесь вы можете посмотреть мои проекты, узнать о направлениях работы с ИИ, "
        "скачать PDF-резюме или открыть интерактивное приложение."
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(is_admin=is_admin))


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Команда просмотра статистики (только для администратора)"""
    user_id = message.from_user.id
    if not ADMIN_ID or str(user_id) != str(ADMIN_ID):
        return

    stats = await db.get_stats()
    text = (
        "📊 <b>Статистика бота-визитки:</b>\n\n"
        f"👥 Всего уникальных пользователей: <b>{stats['total_users']}</b>\n"
        f"📥 Скачиваний резюме (PDF): <b>{stats['resume_downloads']}</b>\n"
        f"✉️ Отправлено заявок через Mini App: <b>{stats['leads_count']}</b>"
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "📄 Скачать резюме (PDF)")
async def send_resume(message: Message):
    # Логируем скачивание
    await db.log_event(message.from_user.id, "resume_download")

    pdf_path = "resume.pdf"
    if os.path.exists(pdf_path):
        doc = FSInputFile(pdf_path, filename="CV_Developer.pdf")
        await message.answer_document(document=doc, caption="Ваше резюме готово к просмотру!")
    else:
        await message.answer("⚠️ Файл резюме сейчас генерируется. Пожалуйста, попробуйте чуть позже.")


@dp.message(F.text == "ℹ️ Обо мне")
async def about_me(message: Message):
    text = (
        "💼 <b>Специализация:</b> Разработка Telegram-ботов, Mini Apps, интеграция ИИ и автоматизация процессов.\n\n"
        "🛠 <b>Стек:</b> Python, aiogram 3, aiosqlite, ReportLab, HTML/CSS/JS, LLM APIs.\n\n"
        "Нажмите <b>«📱 Открыть визитку»</b>, чтобы посмотреть интерактивное портфолио."
    )
    await message.answer(text, reply_markup=get_inline_links(), parse_mode="HTML")


@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    """Обработка данных формы обратной связи из Mini App"""
    try:
        data = json.loads(message.web_app_data.data)
        if data.get("type") == "lead":
            name = data.get("name")
            contact = data.get("contact")
            user_msg = data.get("message")
            user = message.from_user

            # Логируем заявку в статистику
            await db.log_event(user.id, "lead_submit")

            admin_text = (
                f"🔥 <b>Новая заявка из Mini App!</b>\n\n"
                f"👤 <b>Имя:</b> {name}\n"
                f"📞 <b>Контакт:</b> {contact}\n"
                f"📝 <b>Задача:</b> {user_msg}\n\n"
                f"ℹ️ <b>Отправитель в TG:</b> @{user.username or 'нет'} (ID: <code>{user.id}</code>)"
            )

            if ADMIN_ID:
                await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")

            await message.answer(
                "✅ <b>Спасибо за обращение!</b>\nВаша заявка успешно передана, я свяжусь с вами в ближайшее время.",
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"Ошибка при обработке web_app_data: {e}")


# ================= ТОЧКА ВХОДА =================
async def main():
    # Инициализация базы данных
    await db.init_db()

    # Запуск фонового веб-сервера Keep-Alive
    await start_web_server()

    print("Бот запущен и ожидает сообщений...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")