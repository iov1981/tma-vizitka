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
    ReplyKeyboardRemove,
    WebAppInfo,
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault
)
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

import database as db
from generate_resume import create_resume
from ai_assistant import ask_gemini

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID", "770948445")
PORT = int(os.getenv("PORT", 8080))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://tma-vizitka.onrender.com")

# Google Apps Script Webhook URL
GOOGLE_SHEETS_WEBHOOK_URL = os.getenv(
    "GOOGLE_SHEETS_WEBHOOK_URL",
    "https://script.google.com/macros/s/AKfycbziYuslONyFHUgrBswRgQaQardwdA9mkZWsCNayPE6ri6wvZVGXXU_leZw3hf7intSh/exec"
)

if not BOT_TOKEN:
    print("Ошибка: BOT_TOKEN не задан в переменных окружения или .env файле!")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ================= FSM СОСТОЯНИЯ =================
class BroadcastState(StatesGroup):
    waiting_for_message = State()


class OfferState(StatesGroup):
    waiting_for_company = State()
    waiting_for_conditions = State()
    waiting_for_contact = State()


class AIAssistantState(StatesGroup):
    chatting = State()


# ================= НАСТРОЙКА МЕНЮ =================
async def setup_bot_commands():
    try:
        default_commands = [
            BotCommand(command="start", description="Перезапустить бота / Меню"),
            BotCommand(command="ask", description="🤖 Задать вопрос AI-ассистенту"),
            BotCommand(command="cancel", description="Отменить текущее действие")
        ]
        await bot.set_my_commands(default_commands, scope=BotCommandScopeDefault())

        if ADMIN_ID:
            admin_commands = [
                BotCommand(command="start", description="Перезапустить бота"),
                BotCommand(command="stats", description="📊 Статистика просмотров и заявок"),
                BotCommand(command="broadcast", description="📢 Отправить рассылку пользователям"),
                BotCommand(command="ask", description="🤖 Задать вопрос AI-ассистенту"),
                BotCommand(command="cancel", description="Отменить текущее действие")
            ]
            await bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=int(ADMIN_ID))
            )
            print(f"Персональное меню команд для администратора (ID: {ADMIN_ID}) установлено.")
    except Exception as e:
        print(f"Ошибка при установке команд меню: {e}")


# ================= ОТПРАВКА ДАННЫХ В GOOGLE ТАБЛИЦУ =================
async def send_to_google_sheets(payload: dict):
    if not GOOGLE_SHEETS_WEBHOOK_URL:
        print("[Sheets] URL скрипта не задан.")
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
                print(f"[Sheets] Данные переданы скрипту, статус HTTP: {response.status}")
    except Exception as e:
        print(f"[Sheets Error] Исключение при отправке в Google Sheets: {e}")


# ================= ОБЩАЯ ФУНКЦИЯ ОБРАБОТКИ ЛИДА =================
async def process_lead(name: str, contact: str, message_text: str, user_id=None, username=None):
    print(f"[Lead] Обработка заявки: Имя='{name}', Контакт='{contact}', Задача='{message_text}', UID='{user_id}'")

    if user_id:
        try:
            await db.log_event(int(user_id), "lead_submit")
        except Exception:
            pass

    sheet_payload = {
        "name": name,
        "contact": contact,
        "message": message_text,
        "username": username or "",
        "user_id": str(user_id or "")
    }
    asyncio.create_task(send_to_google_sheets(sheet_payload))

    admin_text = (
        f"🔥 <b>Новая заявка из Mini App!</b>\n\n"
        f"👤 <b>Имя:</b> {name}\n"
        f"📞 <b>Контакт:</b> {contact}\n"
        f"📝 <b>Задача / Расчет:</b>\n{message_text}\n\n"
        f"ℹ️ <b>Отправитель в TG:</b> @{username or 'нет'} (ID: <code>{user_id or '—'}</code>)\n"
        f"📊 <i>Запись передана в Google Таблицу.</i>"
    )

    if ADMIN_ID:
        try:
            await bot.send_message(chat_id=int(ADMIN_ID), text=admin_text, parse_mode="HTML")
            print(f"[Lead] Уведомление успешно доставлено администратору {ADMIN_ID}.")
        except Exception as e:
            print(f"[Lead Error] Ошибка отправки уведомления администратору в Telegram: {e}")


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
    elif os.path.exists("avatar.png"):
        return web.FileResponse("avatar.png", headers=CORS_HEADERS)
    return web.Response(status=404, text="Avatar not found", headers=CORS_HEADERS)

async def handle_api_options(request):
    return web.Response(headers=CORS_HEADERS)

async def handle_api_lead(request):
    try:
        raw_text = await request.text()
        print(f"[DEBUG Lead Raw]: {raw_text}")
        data = json.loads(raw_text)

        name = data.get("name", "Не указано")
        contact = data.get("contact", "Не указано")
        msg = data.get("message", "Без описания")
        uid = data.get("user_id")
        uname = data.get("username")

        await process_lead(name, contact, msg, user_id=uid, username=uname)
        return web.json_response({"status": "ok"}, headers=CORS_HEADERS)
    except Exception as e:
        print(f"[DEBUG Lead Error]: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=400, headers=CORS_HEADERS)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/avatar.jpg", handle_avatar)
    app.router.add_get("/avatar.png", handle_avatar)
    app.router.add_options("/api/lead", handle_api_options)
    app.router.add_post("/api/lead", handle_api_lead)

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
                KeyboardButton(text="🤖 Спросить AI-ассистента"),
                KeyboardButton(text="💼 Предложить проект / оффер")
            ],
            [
                KeyboardButton(text="📄 Скачать резюме (PDF)"),
                KeyboardButton(text="ℹ️ Обо мне")
            ]
        ],
        resize_keyboard=True
    )

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Выйти из режима AI")]],
        resize_keyboard=True
    )

def get_offer_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def get_inline_links():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✈️ Telegram", url="https://t.me/iov1981"),
                InlineKeyboardButton(text="🐙 GitHub", url="https://github.com/iov1981")
            ],
            [
                InlineKeyboardButton(text="📸 Instagram", url="https://www.instagram.com/iov1981"),
                InlineKeyboardButton(
                    text="✉️ Написать на Email",
                    url="https://mail.google.com/mail/?view=cm&fs=1&to=hripunov60@gmail.com"
                )
            ]
        ]
    )


# ================= ОБРАБОТКА ОТМЕНЫ =================
@dp.message(Command("cancel"))
@dp.message(F.text.in_({"❌ Отмена", "❌ Выйти из режима AI"}))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    is_admin = bool(ADMIN_ID and str(message.from_user.id) == str(ADMIN_ID))
    await message.answer("Вы вернулись в главное меню.", reply_markup=get_main_keyboard(is_admin=is_admin))


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    is_admin = bool(ADMIN_ID and str(user.id) == str(ADMIN_ID))

    await db.add_user(user.id, user.username, user.first_name)

    if ADMIN_ID and not is_admin:
        try:
            await bot.send_message(
                chat_id=int(ADMIN_ID),
                text=f"🔔 Пользователь @{user.username or 'нет'} (ID: {user.id}) нажал /start"
            )
        except Exception:
            pass

    welcome_text = (
        f"Здравствуйте, {user.first_name}!\n\n"
        "Добро пожаловать в бота-визитку Алексея Хрипунова.\n\n"
        "• Нажмите <b>«📱 Открыть визитку»</b> для интерактивного портфолио.\n"
        "• Нажмите <b>«🤖 Спросить AI-ассистента»</b>, чтобы задать любой вопрос нейросети о навыках и опыте Алексея.\n"
        "• Нажмите <b>«💼 Предложить проект / оффер»</b> для передачи вакансии или заказа.\n"
        "• Нажмите <b>«📄 Скачать резюме»</b> для получения актуального PDF."
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(is_admin=is_admin), parse_mode="HTML")


# ================= AI-АССИСТЕНТ (GEMINI) =================
@dp.message(Command("ask"))
@dp.message(F.text == "🤖 Спросить AI-ассистента")
async def start_ai_chat(message: Message, state: FSMContext):
    await state.set_state(AIAssistantState.chatting)
    text = (
        "🤖 <b>AI-ассистент готов к диалогу!</b>\n\n"
        "Вы можете спросить меня о чем угодно, что касается опыта Алексея:\n"
        "— <i>«Какой опыт у Алексея в Postman и тестировании API?»</i>\n"
        "— <i>«Пишет ли Алексей автотесты на Python?»</i>\n"
        "— <i>«Готов ли Алексей к удаленному формату работы?»</i>\n"
        "— <i>«Какие проекты он создавал на aiogram?»</i>\n\n"
        "Напишите ваш вопрос ниже 👇\n"
        "<i>(Для возврата в меню нажмите «❌ Выйти из режима AI»)</i>"
    )
    await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")


@dp.message(AIAssistantState.chatting)
async def process_ai_message(message: Message, state: FSMContext):
    user_text = message.text.strip()
    if not user_text:
        return

    # Индикатор набора сообщения в Telegram
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    ai_reply = await ask_gemini(user_text)
    await message.answer(ai_reply, reply_markup=get_cancel_keyboard())


# ================= СЦЕНАРИЙ ДЛЯ РЕКРУТЕРОВ (FSM) =================
@dp.message(F.text == "💼 Предложить проект / оффер")
async def start_offer_dialog(message: Message, state: FSMContext):
    await state.set_state(OfferState.waiting_for_company)
    text = (
        "🤝 <b>Отлично! Рад новым предложениям.</b>\n\n"
        "<b>Шаг 1 из 3:</b> Укажите название вашей компании или краткую суть проекта:"
    )
    await message.answer(text, reply_markup=get_offer_cancel_keyboard(), parse_mode="HTML")


@dp.message(OfferState.waiting_for_company)
async def process_offer_company(message: Message, state: FSMContext):
    company = message.text.strip()
    await state.update_data(company=company)
    await state.set_state(OfferState.waiting_for_conditions)

    text = (
        "<b>Шаг 2 из 3:</b> Опишите условия работы или вилку:\n"
        "<i>(Например: Полная удаленка, QA Auto / Python, вилка от 120 000 ₽ или проектная задача)</i>"
    )
    await message.answer(text, reply_markup=get_offer_cancel_keyboard(), parse_mode="HTML")


@dp.message(OfferState.waiting_for_conditions)
async def process_offer_conditions(message: Message, state: FSMContext):
    conditions = message.text.strip()
    await state.update_data(conditions=conditions)
    await state.set_state(OfferState.waiting_for_contact)

    text = (
        "<b>Шаг 3 из 3:</b> Укажите контакт для обратной связи:\n"
        "<i>(Ваш @username в Telegram, номер телефона или рабочий Email)</i>"
    )
    await message.answer(text, reply_markup=get_offer_cancel_keyboard(), parse_mode="HTML")


@dp.message(OfferState.waiting_for_contact)
async def process_offer_contact(message: Message, state: FSMContext):
    contact = message.text.strip()
    data = await state.get_data()
    await state.clear()

    company = data.get("company", "Не указано")
    conditions = data.get("conditions", "Не указано")
    user = message.from_user
    is_admin = bool(ADMIN_ID and str(user.id) == str(ADMIN_ID))

    summary_task = f"ОФФЕР / ВАКАНСИЯ\nКомпания/Проект: {company}\nУсловия: {conditions}"

    await process_lead(
        name=f"Оффер от {user.first_name or 'Рекрутера'}",
        contact=contact,
        message_text=summary_task,
        user_id=user.id,
        username=user.username
    )

    success_text = (
        "✅ <b>Спасибо! Ваше предложение успешно передано Алексею.</b>\n\n"
        "Я ознакомлюсь с деталями и свяжусь с вами в ближайшее время."
    )
    await message.answer(success_text, reply_markup=get_main_keyboard(is_admin=is_admin), parse_mode="HTML")


# ================= КОМАНДЫ АДМИНИСТРАТОРА =================
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
        f"✉️ Отправлено заявок и офферов: <b>{stats['leads_count']}</b>"
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not ADMIN_ID or str(user_id) != str(ADMIN_ID):
        return

    await state.set_state(BroadcastState.waiting_for_message)
    await message.answer(
        "📢 <b>Режим рассылки сообщений</b>\n\n"
        "Отправьте сообщение, которое хотите разослать всем пользователям бота.\n\n"
        "Для отмены отправьте /cancel",
        parse_mode="HTML"
    )


@dp.message(BroadcastState.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
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
            await message.copy_to(chat_id=uid)
            success += 1
            await asyncio.sleep(0.05)
        except (TelegramForbiddenError, TelegramBadRequest):
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


# ================= ДРУГИЕ КНОПКИ =================
@dp.message(F.text == "📄 Скачать резюме (PDF)")
async def send_resume(message: Message):
    await db.log_event(message.from_user.id, "resume_download")

    pdf_path = "resume.pdf"
    try:
        create_resume(pdf_path)
    except Exception as e:
        print(f"Ошибка при создании PDF: {e}")

    if os.path.exists(pdf_path):
        doc = FSInputFile(pdf_path, filename="CV_Alexey_Khripunov.pdf")
        await message.answer_document(
            document=doc,
            caption="📄 Ваше резюме готово!\nВнутри вы найдете ключевой стек, проекты и QR-код со ссылкой на бота для визиток."
        )
    else:
        await message.answer("⚠️ Файл резюме сейчас формируется. Пожалуйста, попробуйте чуть позже.")


@dp.message(F.text == "ℹ️ Обо мне")
async def about_me(message: Message):
    text = (
        "💼 <b>Специализация:</b> Инженер по тестированию (QA) & Python-разработчик.\n\n"
        "🛠 <b>Стек:</b> Python, aiogram 3, aiosqlite, Pytest, ReportLab, HTML/CSS/JS, LLM APIs.\n\n"
        "Связаться со мной можно напрямую в соцсетях или по почте:"
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
            await message.answer(
                "✅ <b>Спасибо за обращение!</b>\nВаша заявка успешно передана, я свяжусь с вами в ближайшее время.",
                parse_mode="HTML"
            )
    except Exception as e:
        print(f"Ошибка при обработке web_app_data: {e}")


# ================= ПЕРЕХВАТ НЕРАСПОЗНАННЫХ ТЕКСТОВ =================
@dp.message(F.text)
async def fallback_text_to_ai(message: Message, state: FSMContext):
    """Если пользователь просто написал текстовый вопрос без нажатия кнопок — отвечает AI"""
    current_state = await state.get_state()
    if current_state is not None:
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    ai_reply = await ask_gemini(message.text.strip())
    is_admin = bool(ADMIN_ID and str(message.from_user.id) == str(ADMIN_ID))
    await message.answer(ai_reply, reply_markup=get_main_keyboard(is_admin=is_admin))


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