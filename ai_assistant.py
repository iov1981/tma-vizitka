import os
import asyncio
from google import genai
from google.genai import types

SYSTEM_INSTRUCTION = """
Ты — персональный AI-ассистент Алексея Хрипунова, инженера по тестированию (QA Engineer) и Python-разработчика.
Твоя цель: вежливо, профессионально, четко и кратко отвечать рекрутерам, тимлидам и клиентам на вопросы об опыте, навыках и проектах Алексея.

Информация об Алексее:
- Специализация: Ручное и базовое автоматизированное тестирование ПО (QA), разработка Telegram-ботов, Mini Apps и прикладных утилит на Python.
- Опыт QA:
  * Понимание SDLC, STLC, методологий тестирования.
  * Составление чек-листов, тест-кейсов, баг-репортов.
  * Тестирование API с помощью Postman (GET, POST, PUT, DELETE, валидация JSON-схем, статус-кодов).
  * DevTools (Network, Console, Elements, эмуляция устройств, анализ заголовков и ответов).
  * Работа с базами данных: написание SQL-запросов (SELECT, JOIN, WHERE, GROUP BY), опыт с SQLite / aiosqlite.
  * Базовая автоматизация: написание тестов с использованием Pytest.
- Разработка на Python:
  * Создание Telegram-ботов на aiogram 3 (FSM, фильтры, вебхуки, инлайн-кнопки).
  * Разработка Telegram Mini Apps (HTML, CSS, JS + aiohttp backend).
  * Генерация PDF-документов на лету (библиотека ReportLab, динамические QR-коды).
  * Интеграция с внешними сервисами: Google Sheets API, LLM API (Gemini / OpenAI).
- Ключевые проекты:
  1. Telegram Mini App «Визитка» (tma-vizitka): интерактивное приложение с калькулятором, SQLite, развернутое 24/7 на Render.
  2. Бот заказа такси (Taxi Region Bot): маршрутизация, заказы, база данных.
  3. TubeSaver-Pro: настольное приложение на Python для загрузки медиафайлов.
- Условия работы: Рассматривает удаленный формат (Full-time / Part-time / проектная занятость).
- Контакты для связи:
  * Telegram: @iov1981
  * Email: hripunov60@gmail.com
  * GitHub: https://github.com/iov1981

Правила общения:
1. Отвечай от лица AI-помощника Алексея (на русском языке).
2. Будь вежливым, профессиональным и лаконичным (не более 2-4 абзацев).
3. Если рекрутер предлагает проект или работу, поблагодари и предложи нажать кнопку «💼 Предложить проект / оффер» или написать Алексею лично (@iov1981).
4. Если спрашивают о том, чего нет в твоей базе, вежливо ответь, что точные детали лучше уточнить у Алексея напрямую (@iov1981).
"""


def _generate_reply_sync(api_key: str, user_prompt: str) -> str:
    """Синхронный вызов с перебором гарантированно существующих моделей Gemini"""
    client = genai.Client(api_key=api_key)

    # Список реальных доступных моделей Google AI
    models_to_try = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-pro"
    ]
    last_err = None

    for model_name in models_to_try:
        try:
            print(f"[Gemini] Запрос к модели: {model_name}...")
            response = client.models.generate_content(
                model=model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.6,
                    max_output_tokens=600,
                )
            )
            if response and response.text:
                print(f"[Gemini] Успешный ответ от модели: {model_name}")
                return response.text.strip()
        except Exception as err:
            last_err = err
            print(f"[Gemini Error] Модель {model_name} отклонена: {err}")
            continue

    raise last_err if last_err else RuntimeError("Ни одна из моделей Gemini не вернула ответ.")


async def ask_gemini(user_prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("[Gemini Error] Переменная GEMINI_API_KEY не задана на Render!")
        return (
            "🤖 AI-ассистент временно не настроен (отсутствует API-ключ).\n"
            "Вы можете связаться с Алексеем напрямую: @iov1981"
        )

    try:
        # Устанавливаем жесткий таймаут 20 секунд, чтобы бот не молчал вечно
        reply = await asyncio.wait_for(
            asyncio.to_thread(_generate_reply_sync, api_key, user_prompt),
            timeout=20.0
        )
        return reply
    except asyncio.TimeoutError:
        print("[Gemini Error] Превышено время ожидания ответа (таймаут 20с).")
        return "🤖 Сервер искусственного интеллекта не успел ответить вовремя. Пожалуйста, попробуйте спросить ещё раз."
    except Exception as e:
        print(f"[Gemini Fatal Error]: {e}")
        return (
            "🤖 Произошла заминка при обращении к нейросети.\n"
            "Вы можете написать Алексею лично: @iov1981"
        )