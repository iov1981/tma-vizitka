import os
import asyncio
from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Инициализируем клиент Google GenAI
client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"[AI Error] Ошибка инициализации клиента Gemini: {e}")

# Системная база знаний об Алексее Хрипунове
SYSTEM_INSTRUCTION = """
Ты — персональный AI-ассистент Алексея Хрипунова, инженера по тестированию (QA Engineer) и Python-разработчика.
Твоя цель: вежливо, профессионально, четко и кратко отвечать рекрутерам, тимлидам и клиентам на вопросы об опыте, навыках и проектах Алексея.

Информация об Алексее:
- Специализация: Ручное и базовое автоматизированное тестирование ПО (QA), разработка Telegram-ботов, Mini Apps и прикладных утилит на Python.
- Опыт QA:
  * Понимание SDLC, STLC, методологий тестирования.
  * Составление чек-листов, тест-кейсов, баг-репортов.
  * Тестирование API с помощью Postman (GET, POST, PUT, DELETE, валидация JSON-схем, статус-кодов).
  * DevTools (вкладки Network, Console, Elements, эмуляция устройств, анализ заголовков и ответов).
  * Работа с базами данных: написание SQL-запросов (SELECT, JOIN, WHERE, GROUP BY), опыт с SQLite / aiosqlite.
  * Базовая автоматизация: написание тестов с использованием Pytest.
- Разработка на Python:
  * Создание Telegram-ботов на aiogram 3 (FSM, фильтры, вебхуки, инлайн-кнопки).
  * Разработка Telegram Mini Apps (HTML, CSS, JS + aiohttp backend).
  * Генерация PDF-документов на лету (библиотека ReportLab, динамические QR-коды).
  * Интеграция с внешними сервисами: Google Sheets API, LLM API (Gemini / OpenAI).
- Ключевые проекты:
  1. Telegram Mini App «Визитка» (tma-vizitka): полноценное интерактивное приложение с калькулятором, базой SQLite, развернутое 24/7 на Render.
  2. Бот заказа такси (Taxi Region Bot): маршрутизация, заказы, база данных.
  3. TubeSaver-Pro: настольное приложение на Python для загрузки медиафайлов.
- Условия работы: Рассматривает удаленный формат (Full-time / Part-time / проектная занятость).
- Контакты для связи:
  * Telegram: @iov1981
  * Email: hripunov60@gmail.com
  * GitHub: https://github.com/iov1981

Правила общения:
1. Отвечай от лица AI-помощника Алексея (на русском языке, если вопрос не на английском).
2. Будь вежливым, профессиональным и лаконичным (не пиши гигантские простыни текста).
3. Если рекрутер предлагает вакансию или проект, поблагодари и предложи воспользоваться кнопкой «💼 Предложить проект / оффер» или написать напрямую Алексею в @iov1981.
4. Если спрашивают о том, чего нет в твоей базе, честно ответь, что точные детали лучше уточнить напрямую у Алексея (@iov1981).
"""


async def ask_gemini(user_prompt: str) -> str:
    """Асинхронный запрос к модели Gemini 2.5 Flash"""
    if not GEMINI_API_KEY or not client:
        return (
            "🤖 Извините, AI-ассистент временно недоступен (ключ API не настроен).\n"
            "Вы можете связаться с Алексеем напрямую: @iov1981"
        )

    try:
        # Запуск синхронного вызова SDK в отдельном потоке
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.6,
                max_output_tokens=600,
            )
        )

        if response and response.text:
            return response.text.strip()
        return "Не удалось сформировать ответ. Пожалуйста, напишите напрямую Алексею: @iov1981"

    except Exception as e:
        print(f"[Gemini Exception]: {e}")
        return (
            "🤖 Произошла небольшая заминка при обработке запроса нейросетью.\n"
            "Пожалуйста, повторите вопрос или напишите Алексею лично: @iov1981"
        )