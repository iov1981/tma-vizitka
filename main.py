import os
import sys
import json
import asyncio
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


# ================= FSM СОСТОЯНИЯ =================
class BroadcastState(StatesGroup):
    waiting_for_message = State()


# ================= НАСТРОЙКА ПЕРСОНАЛЬНЫХ КОМАНД МЕНЮ =================
async def setup_bot_commands():
    """Команды меню для гостей и персонально для администратора"""
    try:
        # Для всех пользователей
        default_commands = [
            BotCommand(command="start", description="Перезапустить бота / Меню")
        ]
        await bot.set_my_commands(default_commands, scope=BotCommandScopeDefault())

        # Для администратора
        if ADMIN_ID:
            admin_commands = [
                BotCommand(command="start", description="Перезапустить бота"),
                BotCommand(command="stats", description="📊 Статистика просмотров и заявок"),
                BotCommand(command="broadcast", description="📢 Отправить рассылку пользователям")
            ]
            await bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=int(ADMIN_ID))
            )
            print(f"Персональное меню команд для администратора (ID: {ADMIN_ID}) установлено.")
    except Exception as e:
        print(f"Ошибка при установке команд меню: {e}")


# ================= ВЕБ-СЕРВЕР KEEP-ALIVE И РАЗДАЧА INDEX.HTML =================
async def handle_ping(request):
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type="text/html")
    return web.Response(text="Bot is running!", content_type="text/plain")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Веб-сервер успешно запущен на порту {PORT}")


# ================= КЛАВИАТУРЫ =================
def get_main_keyboard(is_admin: bool = False):
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
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🐙 GitHub репозиторий", url="https://github.com/iov1981/tma-vizitka")
            ]
        ]
    )


# ================= ХЕНДЛЕРЫ БОТА =================
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    is_admin = bool(ADMIN_ID and str(user.id) == str(ADMIN_ID))

    await db.add_user(user.id, user.username, user.first_name)

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


# --- РАССЫЛКА ПОЛЬЗОВАТЕЛЯМ (/broadcast) ---
@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    """Инициация рассылки (только для администратора)"""
    user_id = message.from_user.id
    if not ADMIN_ID or str(user_id) != str(ADMIN_ID):
        return

    await state.set_state(BroadcastState.waiting_for_message)
    await message.answer(
        "📢 <b>Режим рассылки сообщений</b>\n\n"
        "Отправьте сообщение (текст, фото или документ), которое хотите разослать всем пользователям бота.\n\n"
        "Для отмены отправьте /cancel",
        parse_mode="HTML"
    )


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего действия FSM"""
    await state.clear()
    await message.answer("Действие отменено.")


@dp.message(BroadcastState.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Выполнение рассылки всем пользователям из базы SQLite"""
    await state.clear()

    user_ids = await db.get_all_user_ids()
    if not user_ids:
        await message.answer("База пользователей пуста. Некому отправлять.")
        return

    status_msg = await message.answer(f"⏳ Запуск рассылки на {len(user_ids)} получателей...")

    success = 0
    blocked = 0

    for uid in user_ids:
        try:
            # Копируем сообщение в исходном виде
            await message.copy_to(chat_id=uid)
            success += 1
            # Небольшая пауза, чтобы не превысить лимиты Telegram API
            await asyncio.sleep(0.05)
        except TelegramForbiddenError:
            # Пользователь заблокировал бота
            blocked += 1
        except TelegramBadRequest:
            blocked += 1
        except Exception:
            blocked += 1

    report_text = (
        "✅ <b>Рассылка завершена!</b>\n\n"
        f"📤 Всего в базе: <b>{len(user_ids)}</b>\n"
        f"📬 Успешно доставлено: <b>{success}</b>\n"
        f"🚫 Не доставлено (заблокировали бота): <b>{blocked}</b>"
    )
    await status_msg.edit_text(report_text, parse_mode="HTML")


@dp.message(F.text == "📄 Скачать резюме (PDF)")
async def send_resume(message: Message):
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
    try:
        data = json.loads(message.web_app_data.data)
        if data.get("type") == "lead":
            name = data.get("name")
            contact = data.get("contact")
            user_msg = data.get("message")
            user = message.from_user

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