# 📱 Telegram Mini App & Bot «Визитка разработчика»

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Aiogram 3](https://img.shields.io/badge/Aiogram-3.x-2481cc.svg)](https://docs.aiogram.dev/)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7.svg)](https://render.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Многофункциональный Telegram-бот и встроенное веб-приложение (Telegram Mini App), выполняющие роль интерактивного портфолио, инструмента для автоматического сбора лидов (CRM-интеграция) и генератора резюме в формате PDF с динамическими QR-кодами.

---

## 🚀 Ключевые возможности

- **Интерактивный интерфейс Telegram Mini App (TMA):**
  - Адаптивный дизайн под светлую и тёмную темы Telegram.
  - Карточки проектов с технологическими стеками и ссылками на репозитории.
  - Интерактивный калькулятор стоимости разработки с автоматическим формированием брифа в форму заявки.
  - FAQ-аккордеон с ответами на частые вопросы и виброоткликом (HapticFeedback).
  - Нативная функция шаринга («Поделиться визиткой») в любой чат Telegram в один клик.
  - Кликабельные контакты (Telegram, Instagram, Email, GitHub) без блокировок во встроенном браузере WebView.

- **Двухканальная лидогенерация (Telegram + Google Sheets):**
  - Мгновенная отправка данных заявки в личный чат администратора с подробностями выбранных услуг.
  - Автоматическая синхронизация через Webhook в Google Таблицу (дата, имя, контакт, бриф/бюджет, TG ID, username).
  - Поддержка отправки как через Telegram `sendData`, так и через прямой HTTP API эндпоинт с защитой CORS.

- **Генерация PDF-резюме на лету (ReportLab):**
  - Формирование структурированного резюме в формате PDF по запросу пользователя.
  - Генерация динамического QR-кода со стабильной ссылкой на запуск Mini App визитки.
  - Поддержка кириллических шрифтов (DejaVu / Arial).

- **Панель управления и аналитика:**
  - Автоматический трекинг посетителей, скачиваний резюме и отправленных заявок в базе данных SQLite.
  - Команда `/stats` для просмотра статистики просмотров и конверсий (доступна только администратору).
  - Команда `/broadcast` для безопасной рассылки сообщений пользователям бота.
  - Специальный режим владельца: при входе администратора форма заявки автоматически скрывается.

---

## 🛠 Технологический стек

- **Backend:** Python 3, `aiogram 3` (асинхронный фреймворк для Telegram Bot API), `aiohttp` (встроенный HTTP веб-сервер и обработка API), `asyncio`.
- **Frontend (Mini App):** HTML5, Modern CSS3 (CSS Variables, Telegram Theme Params), JavaScript (Vanilla JS, Telegram WebApp SDK).
- **База данных:** SQLite, `aiosqlite` (асинхронные транзакции).
- **Документооборот:** `ReportLab` (генерация PDF), `qrcode`, `Pillow`.
- **Интеграции:** Google Sheets API (через Google Apps Script Webhook).
- **Хостинг & Инфраструктура:** Облачный сервис Render (развёртывание веб-сервиса с 24/7 Keep-Alive мониторингом).

---

## 📂 Структура проекта

```text
├── database.py             # Асинхронные методы работы с базой данных SQLite
├── generate_resume.py      # Модуль генерации PDF-резюме и QR-кода
├── index.html              # Frontend-код Telegram Mini App (TMA)
├── main.py                 # Точка входа: Telegram-бот, веб-сервер и роутинг API
├── Procfile                # Инструкция запуска для облачных PaaS-платформ
├── requirements.txt        # Список зависимостей Python
├── resume.pdf              # Автоматически генерируемый файл резюме
└── .env                    # Конфигурационные токены и переменные окружения
git clone [https://github.com/iov1981/tma-vizitka.git](https://github.com/iov1981/tma-vizitka.git)
cd tma-vizitka


# Для Windows:
python -m venv .venv
.venv\Scripts\activate

# Для Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate


pip install -r requirements.txt


BOT_TOKEN=your_telegram_bot_token_from_botfather
ADMIN_ID=your_telegram_numeric_id
PORT=8080
RENDER_EXTERNAL_URL=[https://your-app-domain.onrender.com](https://your-app-domain.onrender.com)
GOOGLE_SHEETS_WEBHOOK_URL=[https://script.google.com/macros/s/your_script_id/exec](https://script.google.com/macros/s/your_script_id/exec)


python main.py


Развёртывание на Render
Создайте новый Web Service на Render.com.

Подключите ваш GitHub-репозиторий tma-vizitka.

Задайте параметры сервиса:

Environment: Python 3

Build Command: pip install -r requirements.txt

Start Command: python main.py

В разделе Environment Variables добавьте переменные:

BOT_TOKEN

ADMIN_ID

PORT: 8080

RENDER_EXTERNAL_URL: публичный URL вашего сервиса

GOOGLE_SHEETS_WEBHOOK_URL: ссылка на развёрнутый вебхук Google Apps Script.


👨‍💻 Автор
Алексей Хрипунов

Telegram: @iov1981

Instagram: @iov1981

Email: hripunov60@gmail.com

GitHub: iov1981