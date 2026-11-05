import os
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def generate_vcard_qr(filename="vcard_qr.png"):
    """
    Генерирует QR-код с контактом формата vCard.
    При наведении камеры смартфон предлагает сразу сохранить контакт в телефонную книгу.
    """
    vcard_data = (
        "BEGIN:VCARD\n"
        "VERSION:3.0\n"
        "N:Хрипунов;Алексей;;;\n"
        "FN:Алексей Хрипунов\n"
        "TITLE:AI & Telegram Bot Developer\n"
        "URL:https://t.me/aleksey_qa_vizitka_bot\n"
        "NOTE:Разработка ботов, автоматизация и внедрение искусственного интеллекта\n"
        "END:VCARD"
    )
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=1,
    )
    qr.add_data(vcard_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    return filename


def create_resume(output_filename="resume.pdf"):
    # Регистрация кириллического шрифта (используем стандартный DejaVuSans из системы или Arial)
    # Если шрифт не найден, библиотека может использовать базовый Helvetica
    font_name = "Helvetica"
    try:
        # Проверяем типовые пути к шрифтам с кириллицей в Linux / Windows
        possible_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "DejaVuSans.ttf"
        ]
        for path in possible_fonts:
            if os.path.exists(path):
                pdfmetrics.registerFont(TTFont("CustomFont", path))
                font_name = "CustomFont"
                break
    except Exception as e:
        print(f"Предупреждение по шрифтам: {e}")

    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Пользовательские стили
    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b")
    )

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2563eb")
    )

    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )

    story = []

    # 1. Шапка: Имя, должность и vCard QR-код справа
    qr_path = generate_vcard_qr()

    header_text = [
        Paragraph("<b>Алексей Хрипунов</b>", name_style),
        Spacer(1, 4),
        Paragraph("<b>Разработчик Telegram-ботов | Интегратор ИИ | QA Automation</b>", title_style),
        Spacer(1, 6),
        Paragraph("Telegram: @aleksey_qa_vizitka_bot | Специализация: Python, AI, Bots", body_style),
    ]

    header_table_data = [
        [header_text, Image(qr_path, width=70, height=70)]
    ]
    header_table = Table(header_table_data, colWidths=[450, 90])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # Разделитель
    line_table = Table([['']], colWidths=[540], rowHeights=[2])
    line_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor("#2563eb")),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 8))

    # 2. Ключевые компетенции
    story.append(Paragraph("<b>КЛЮЧЕВЫЕ КОМПЕТЕНЦИИ</b>", heading_style))
    skills_text = (
        "• <b>Telegram & Bots:</b> aiogram 3, Telegram Mini Apps (TMA), Webhook/Polling, создание ботов под ключ.<br/>"
        "• <b>Искусственный Интеллект:</b> интеграция LLM (OpenAI API, Claude, DeepSeek), AI-агенты, Prompt Engineering, автоматизация рутины.<br/>"
        "• <b>Backend & БД:</b> Python, aiohttp, SQLite (aiosqlite), архитектурные паттерны, асинхронное программирование.<br/>"
        "• <b>QA & Качество:</b> ручное и автоматизированное тестирование API и логики ботов, валидация сценариев.<br/>"
        "• <b>Деплой & Хостинг:</b> развертывание 24/7 (Render, Linux), настройка Keep-Alive демонов, Git/GitHub."
    )
    story.append(Paragraph(skills_text, body_style))
    story.append(Spacer(1, 8))

    # 3. Реализованные проекты и опыт
    story.append(Paragraph("<b>РЕАЛИЗОВАННЫЕ ПРОЕКТЫ И ОПЫТ</b>", heading_style))

    projects_text = (
        "<b>1. Telegram Mini App «Визитка» & Портфолио</b><br/>"
        "Разработка full-stack визитки с веб-приложением внутри Telegram, динамической генерацией PDF-резюме "
        "с персональным vCard QR-кодом, сбором заявок клиентов и скрытой административной аналитикой.<br/>"
        "<i>Стек: Python, aiogram 3, aiosqlite, ReportLab, HTML5/CSS3.</i><br/><br/>"

        "<b>2. Бот для автоматизации сервиса заказа такси</b><br/>"
        "Реализация комплексного Telegram-сервиса с обработкой геопозиции пользователей, тарификацией поездок "
        "и непрерывной облачной работой 24/7.<br/>"
        "<i>Стек: Python, aiogram, Render Cloud Hosting.</i><br/><br/>"

        "<b>3. Направление: Внедрение и развитие инструментов ИИ</b><br/>"
        "Настройка и внедрение прикладных решений на базе нейросетей, интеграция языковых моделей в бизнес-процессы "
        "для генерации ответов, анализа данных и оптимизации времени специалистов."
    )
    story.append(Paragraph(projects_text, body_style))
    story.append(Spacer(1, 8))

    # 4. Преимущества работы
    story.append(Paragraph("<b>ПОДХОД К РАБОТЕ</b>", heading_style))
    approach_text = (
        "Внимание к деталям, упор на отказоустойчивость решений (24/7 работа без простоев), "
        "чистая архитектура кода и понятный интерфейс для конечного пользователя. "
        "Отсканируйте QR-код в правом верхнем углу документа для связи в Telegram."
    )
    story.append(Paragraph(approach_text, body_style))

    doc.build(story)

    # Удаляем временную картинку QR после сборки PDF
    if os.path.exists(qr_path):
        os.remove(qr_path)
    print(f"Резюме успешно сгенерировано: {output_filename}")


if __name__ == "__main__":
    create_resume()