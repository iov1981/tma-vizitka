import os
import sys
import json
import asyncio
import aiohttp
from aiohttp import web
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    WebAppInfo,
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault
)
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

import database as db

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
PORT = int(os.getenv("PORT", 8080))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://tma-vizitka.onrender.com")

GOOGLE_SHEETS_WEBHOOK_URL = os.getenv(
    "GOOGLE_SHEETS_WEBHOOK_URL",
    "https://script.google.com/macros/s/AKfycbziYuslONyFHUgrBswRgQaQardwdA9mkZWsCNayPE6ri6wvZVGXXU_leZw3hf7intSh/exec"
)

if not BOT_TOKEN:
    print("Ошибка: BOT_TOKEN не задан!")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class BroadcastState(StatesGroup):
    waiting_for_message = State()


async def setup_bot_commands():
    try:
        default_commands = [BotCommand(command="start", description="Перезапустить бота / Меню")]
        await bot.set_my_commands(default_commands, scope=BotCommandScopeDefault())

        if ADMIN_ID:
            admin_commands = [
                BotCommand(command="start", description="Перезапустить бота"),
                BotCommand(command="stats", description="📊 Статистика просмотров и заявок"),
                BotCommand(command="broadcast", description="📢 Отправить рассылку пользователям")
            ]
            await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=int(ADMIN_ID)))
    except Exception as e:
        print(f"Ошибка команд: {e}")


async def send_to_google_sheets(payload: dict):
    if not GOOGLE_SHEETS_WEBHOOK_URL:
        return
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                GOOGLE_SHEETS_WEBHOOK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                print(f"[Sheets] Ответ от скрипта: {response.status}")
    except Exception as e:
        print(f"[Sheets Error]: {e}")


async def process_lead(name: str, contact: str, message_text: str, user_id=None, username=None):
    print(f"[Lead] Получена заявка: {name} | {contact} | {message_text}")
    if user_id:
        try:
            await db.log_event(int(user_id), "lead_submit")
        except Exception:
            pass

    # Отправка в Google Таблицу
    sheet_payload = {
        "name": name,
        "contact": contact,
        "message": message_text,
        "username": username or "",
        "user_id": str(user_id or "")
    }
    asyncio.create_task(send_to_google_sheets(sheet_payload))

    # Отправка админу
    admin_text = (
        f"🔥 <b>Новая заявка из Mini App!</b>\n\n"
        f"👤 <b>Имя:</b> {name}\n"
        f"📞 <b>Контакт:</b> {contact}\n"
        f"📝 <b>Задача:</b>\n{message_text}\n\n"
        f"ℹ️ <b>Отправитель:</b> @{username or 'нет'} (ID: <code>{user_id or '—'}</code>)"
    )

    if ADMIN_ID:
        try:
            await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="HTML")
            print("[Lead] Сообщение админу успешно отправлено в TG.")
        except Exception as e:
            print(f"[Lead Error] Не удалось отправить админу: {e}")


# ================= ВЕБ-СЕРВЕР И CORS =================
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

async def handle_ping(request):
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html", headers=CORS_HEADERS)
    return web.Response(text="Bot is running!", content_type="text/plain", headers=CORS_HEADERS)

async def handle_avatar(request):
    if os.path.exists("avatar.jpg"):
        return web.FileResponse("avatar.jpg", headers=CORS_HEADERS)
    return web.Response(status=404, text="Avatar not found", headers=CORS_HEADERS)

async def handle_api_options(request):
    return web.Response(headers=CORS_HEADERS)

async def handle_api_lead(request):
    try:
        data = await request.json()
        name = data.get("name", "Не указано")
        contact = data.get("contact", "Не указано")
        msg = data.get("message", "Без описания")
        uid = data.get("user_id")
        uname = data.get("username")

        await process_lead(name, contact, msg, user_id=uid, username=uname)
        return web.json_response({"status": "ok"}, headers=CORS_HEADERS)
    except Exception as e:
        print(f"Ошибка API /api/lead: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=400, headers=CORS_HEADERS)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/avatar.jpg", handle_avatar)
    app.router.add_options("/api/lead", handle_api_options)
    app.router.add_post("/api/lead", handle_api_lead)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Веб-сервер запущен на порту {PORT}")


def get_main_keyboard(is_admin: bool = False):
    web_app_url = f"{RENDER_EXTERNAL_URL}?admin=true" if is_admin else RENDER_EXTERNAL_URL
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Открыть визитку", web_app=WebAppInfo(url=web_app_url))],
            [KeyboardButton(text="📄 Скачать резюме (PDF)"), KeyboardButton(text="ℹ️ Обо мне")]
        ],
        resize_keyboard=True
    )

def get_inline_links():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🐙 GitHub репозиторий", url="https://github.com/iov1981/tma-vizitka")]]
    )

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    is_admin = bool(ADMIN_ID and str(user.id) == str(ADMIN_ID))
    await db.add_user(user.id, user.username, user.first_name)
    welcome_text = (
        f"Здравствуйте, {user.first_name}!\n\n"
        "Добро пожаловать в бота-визитку.\n"
        "Здесь вы можете посмотреть мои проекты, узнать о направлениях работы с ИИ, "
        "скачать PDF-резюме или открыть интерактивное приложение."
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(is_admin=is_admin))

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    if not ADMIN_ID or str(message.from_user.id) != str(ADMIN_ID):
        return
    stats = await db.get_stats()
    text = (
        "📊 <b>Статистика бота-визитки:</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"📥 Скачиваний резюме: <b>{stats['resume_downloads']}</b>\n"
        f"✉️ Заявок: <b>{stats['leads_count']}</b>"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "📄 Скачать резюме (PDF)")
async def send_resume(message: Message):
    await db.log_event(message.from_user.id, "resume_download")
    if os.path.exists("resume.pdf"):
        doc = FSInputFile("resume.pdf", filename="CV_Developer.pdf")
        await message.answer_document(document=doc, caption="Ваше резюме готово к просмотру!")
    else:
        await message.answer("⚠️ Файл резюме пока не сформирован.")

@dp.message(F.text == "ℹ️ Обо мне")
async def about_me(message: Message):
    text = (
        "💼 <b>Специализация:</b> Разработка Telegram-ботов, Mini Apps, интеграция ИИ и автоматизация процессов.\n\n"
        "🛠 <b>Стек:</b> Python, aiogram 3, aiosqlite, ReportLab, HTML/CSS/JS, LLM APIs."
    )
    await message.answer(text, reply_markup=get_inline_links(), parse_mode="HTML")

@dp.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        if data.get("type") == "lead":
            name = data.get("name", "Не указано")
            contact = data.get("contact", "Не указано")
            user_msg = data.get("message", "Без описания")
            user = message.from_user
            await process_lead(name, contact, user_msg, user_id=user.id, username=user.username)
            await message.answer("✅ <b>Спасибо за обращение!</b> Заявка получена.", parse_mode="HTML")
    except Exception as e:
        print(f"Ошибка web_app_data: {e}")

async def main():
    await db.init_db()
    await setup_bot_commands()
    await start_web_server()
    print("Бот запущен и ожидает сообщений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")