import asyncio
import io
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)
from aiohttp import web
import database
from dotenv import load_dotenv
import qrcode

# 1. Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
WEB_APP_URL = "https://iov1981.github.io/tma-vizitka/"

if not BOT_TOKEN:
    raise ValueError(
        "Токен бота не найден! Убедись, что BOT_TOKEN указан в файле .env."
    )

if not ADMIN_ID:
    raise ValueError(
        "ADMIN_ID не найден! Добавь свой цифровой Telegram ID в файл .env."
    )

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# 2. Состояния FSM (Обратная связь и Отзывы)
class FeedbackState(StatesGroup):
    waiting_for_message = State()


class ReviewState(StatesGroup):
    waiting_for_rating = State()
    waiting_for_text = State()


# 3. Клавиатуры
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📱 Открыть визитку (Web App)",
                web_app=WebAppInfo(url=WEB_APP_URL),
            )
        ],
        [KeyboardButton(text="👤 Обо мне"), KeyboardButton(text="🛠 Навыки")],
        [KeyboardButton(text="📁 Мои проекты"), KeyboardButton(text="📞 Контакты")],
        [
            KeyboardButton(text="📄 Скачать резюме"),
            KeyboardButton(text="📲 QR-код визитки"),
        ],
        [
            KeyboardButton(text="⭐ Оставить отзыв"),
            KeyboardButton(text="✉️ Написать автору"),
        ],
        [KeyboardButton(text="🏠 Главное меню")],
    ],
    resize_keyboard=True,
)

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]], resize_keyboard=True
)

contacts_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📱 Открыть Mini App", web_app=WebAppInfo(url=WEB_APP_URL)
            )
        ],
        [
            InlineKeyboardButton(
                text="🔗 GitHub", url="https://github.com/iov1981"
            ),
            InlineKeyboardButton(
                text="✈️ Telegram",
                url="https://t.me/iov1981?text=Привет!%20Пишу%20из%20бота-визитки",
            ),
        ],
    ]
)

rating_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐ 1", callback_data="rate_1"),
            InlineKeyboardButton(text="⭐⭐ 2", callback_data="rate_2"),
            InlineKeyboardButton(text="⭐⭐⭐ 3", callback_data="rate_3"),
            InlineKeyboardButton(text="⭐⭐⭐⭐ 4", callback_data="rate_4"),
            InlineKeyboardButton(text="⭐⭐⭐⭐⭐ 5", callback_data="rate_5"),
        ],
        [InlineKeyboardButton(text="Отмена", callback_data="rate_cancel")],
    ]
)


# 4. Команда /start и кнопка "🏠 Главное меню"
@dp.message(CommandStart())
@dp.message(F.text == "🏠 Главное меню")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await database.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
    )
    text = (
        f"Здравствуйте, {message.from_user.first_name}!\n\n"
        "Это цифровая бот-визитка Алексея Хрипунова.\n"
        "Здесь можно просмотреть проекты, скачать резюме в PDF, получить QR-код или открыть Mini App 👇"
    )
    await message.answer(text, reply_markup=main_menu)


# 5. Генерация QR-кода визитки на лету
@dp.message(F.text == "📲 QR-код визитки")
async def send_qr(message: Message):
    # Генерируем QR-код со ссылкой на визитку
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=2,
    )
    qr.add_data(WEB_APP_URL)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1A365D", back_color="white")

    # Сохранение в буфер памяти
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    photo_file = BufferedInputFile(buf.getvalue(), filename="qr_vizitka.png")
    caption_text = (
        "📲 <b>Ваш QR-код визитки!</b>\n\n"
        f"Ведет на веб-приложение: <code>{WEB_APP_URL}</code>\n"
        "Покажите его с экрана смартфона для быстрого сканирования камерой."
    )
    await message.answer_photo(
        photo=photo_file, caption=caption_text, parse_mode="HTML"
    )


# 6. Отправка резюме в PDF
@dp.message(F.text == "📄 Скачать резюме")
async def send_resume(message: Message):
    resume_path = "resume.pdf"
    if os.path.exists(resume_path):
        pdf_file = FSInputFile(
            resume_path, filename="Резюме_Алексей_Хрипунов.pdf"
        )
        await message.answer_document(
            document=pdf_file,
            caption="📄 Актуальное резюме Алексея Хрипунова (QA Engineer / Python).",
        )
    else:
        await message.answer(
            "Файл резюме сейчас формируется. Напишите напрямую автору: @iov1981"
        )


# 7. Блок отзывов
@dp.message(F.text == "⭐ Оставить отзыв")
async def review_start(message: Message, state: FSMContext):
    await state.set_state(ReviewState.waiting_for_rating)
    await message.answer(
        "Пожалуйста, выберите оценку визитки или проектов от 1 до 5 звёзд:",
        reply_markup=rating_keyboard,
    )


@dp.callback_query(ReviewState.waiting_for_rating, F.data == "rate_cancel")
async def review_cancel_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Оценка отменена.")
    await callback.answer()


@dp.callback_query(ReviewState.waiting_for_rating, F.data.startswith("rate_"))
async def review_rating_chosen(callback: CallbackQuery, state: FSMContext):
    rating = int(callback.data.split("_")[1])
    await state.update_data(rating=rating)
    await state.set_state(ReviewState.waiting_for_text)
    await callback.message.edit_text(
        f"Вы выбрали оценку: {'⭐' * rating}\n\n"
        "Напишите ваш краткий отзыв или пожелание в ответном сообщении:"
    )
    await callback.answer()


@dp.message(ReviewState.waiting_for_text)
async def review_text_received(message: Message, state: FSMContext):
    data = await state.get_data()
    rating = data.get("rating", 5)
    review_text = message.text or "Без текста"

    # Сохраняем отзыв в БД
    await database.save_review(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
        rating=rating,
        review_text=review_text,
    )
    await state.clear()

    # Оповещение администратору
    admin_alert = (
        "🌟 <b>Получен новый отзыв!</b>\n\n"
        f"👤 <b>От:</b> {message.from_user.full_name} (@{message.from_user.username})\n"
        f"⭐️ <b>Оценка:</b> {'⭐' * rating}\n"
        f"📝 <b>Текст отзыва:</b>\n{review_text}"
    )
    try:
        await bot.send_message(
            chat_id=int(ADMIN_ID), text=admin_alert, parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка отправки уведомления админу: {e}")

    await message.answer(
        "Большое спасибо! Ваш отзыв успешно сохранён.", reply_markup=main_menu
    )


# 8. Информационные разделы
@dp.message(F.text == "👤 Обо мне")
async def show_about(message: Message):
    text = (
        "<b>Обо мне:</b>\n\n"
        "Меня зовут Алексей. Я QA инженер и Python-разработчик.\n\n"
        "Специализируюсь на ручном тестировании веб-приложений, API и разработке "
        "прикладных инструментов, парсеров и ботов на Python."
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "🛠 Навыки")
async def show_skills(message: Message):
    text = (
        "<b>Мой стек и навыки:</b>\n\n"
        "• <b>Тестирование:</b> Web, API (Postman), Chrome DevTools, баг-репорты (Jira), тест-кейсы.\n"
        "• <b>Разработка:</b> Python, aiogram 3, aiohttp, SQLite / aiosqlite.\n"
        "• <b>Инструменты:</b> Git, GitHub, PyCharm."
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "📁 Мои проекты")
async def show_projects(message: Message):
    text = (
        "<b>Мои проекты:</b>\n\n"
        "1. <b>TubeSaver-Pro</b> — десктопное приложение для скачивания медиа с YouTube (CustomTkinter, yt-dlp).\n"
        "2. <b>Taxi Region Bot</b> — бот для координации поездок на aiogram 3.\n"
        "3. <b>Бот-визитка & Mini App</b> — интерактивная визитка с базой данных и отзывами."
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text == "📞 Контакты")
async def show_contacts(message: Message):
    text = (
        "<b>Контакты для связи:</b>\n\n"
        "• Telegram: @iov1981\n"
        "• GitHub: github.com/iov1981\n\n"
        "Нажмите на кнопку ниже для быстрого перехода:"
    )
    await message.answer(text, reply_markup=contacts_keyboard, parse_mode="HTML")


# 9. Форма обратной связи
@dp.message(F.text == "✉️ Написать автору")
async def feedback_start(message: Message, state: FSMContext):
    await state.set_state(FeedbackState.waiting_for_message)
    await message.answer(
        "Напишите ваше сообщение в ответ.\n"
        "Если передумали — нажмите «❌ Отмена».",
        reply_markup=cancel_keyboard,
    )


@dp.message(FeedbackState.waiting_for_message, F.text == "❌ Отмена")
async def feedback_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отправка отменена.", reply_markup=main_menu)


@dp.message(FeedbackState.waiting_for_message)
async def feedback_received(message: Message, state: FSMContext):
    await state.clear()
    sender_name = message.from_user.full_name
    sender_username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "не указан"
    )
    sender_id = message.from_user.id
    user_text = message.text or "[Вложение или медиафайл]"

    admin_notification = (
        "📬 <b>Новое сообщение из бота-визитки!</b>\n\n"
        f"👤 <b>Отправитель:</b> {sender_name}\n"
        f"🔹 <b>Username:</b> {sender_username}\n"
        f"🆔 <b>ID пользователя:</b> <code>{sender_id}</code>\n\n"
        f"💬 <b>Текст:</b>\n{user_text}\n\n"
        "<i>(Чтобы ответить, свайпните это сообщение и напишите ответ)</i>\n"
        f"#ID_{sender_id}"
    )

    try:
        await bot.send_message(
            chat_id=int(ADMIN_ID), text=admin_notification, parse_mode="HTML"
        )
        await message.answer(
            "Спасибо! Ваше сообщение передано. Алексей ответит вам здесь же.",
            reply_markup=main_menu,
        )
    except Exception as e:
        await message.answer(
            "Произошла ошибка при отправке сообщения. Напишите напрямую: @iov1981",
            reply_markup=main_menu,
        )
        print(f"Ошибка отправки: {e}")


# 10. Ответ администратора на сообщение через Reply
@dp.message(F.chat.id == int(ADMIN_ID), F.reply_to_message)
async def reply_to_user(message: Message):
    reply_text = message.reply_to_message.text or ""
    if "#ID_" not in reply_text:
        return

    try:
        target_user_id = int(reply_text.split("#ID_")[-1].strip().split()[0])
        user_message = f"💬 <b>Ответ от Алексея:</b>\n\n{message.text}"
        await bot.send_message(
            chat_id=target_user_id, text=user_message, parse_mode="HTML"
        )
        await message.reply("✅ Ответ успешно доставлен пользователю!")
    except Exception as e:
        await message.reply(f"❌ Ошибка отправки: {e}")


# 11. Статистика (только для админа)
@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return
    stats = await database.get_stats()
    text = (
        "📊 <b>Статистика бота-визитки:</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total']}</b>\n"
        f"⚡️ Новых за сегодня: <b>{stats['today']}</b>\n"
        f"⭐ Получено отзывов: <b>{stats['reviews']}</b>"
    )
    await message.answer(text, parse_mode="HTML")


# 12. Инлайн-режим (Inline Mode: @имя_бота в любом чате)
@dp.inline_query()
async def inline_share_card(inline_query: InlineQuery):
    article = InlineQueryResultArticle(
        id="card_alexey",
        title="Визитка: Алексей Хрипунов",
        description="QA Engineer & Python Developer | Резюме, проекты, контакты",
        input_message_content=InputTextMessageContent(
            message_text=(
                "💼 <b>Цифровая визитка: Алексей Хрипунов</b>\n\n"
                "• Специализация: QA инженер & Python-разработчик\n"
                "• Тестирование API, Web, разработка ботов и утилит\n\n"
                "Ознакомьтесь с проектами или откройте Mini App по кнопке ниже 👇"
            ),
            parse_mode="HTML",
        ),
        reply_markup=contacts_keyboard,
    )
    await inline_query.answer([article], cache_time=60)


# 13. Веб-сервер Keep-Alive для Render
async def handle_ping(request):
    return web.Response(text="Bot is running!")


async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


# 14. Точка входа
async def main():
    await database.init_db()
    # Запуск фонового веб-сервера для Keep-Alive
    try:
        await start_web_server()
        print("Веб-сервер Keep-Alive запущен.")
    except Exception as e:
        print(f"Сервер не запущен (локальный запуск): {e}")

    print("Бот успешно запущен со всеми новыми функциями!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())