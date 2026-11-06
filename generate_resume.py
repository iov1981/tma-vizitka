import os
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def generate_bot_qr(filename="bot_qr.png"):
    """Генерация QR-кода с прямой ссылкой на запуск Mini App визитки"""
    miniapp_url = "https://t.me/aleksey_qa_vizitka_bot?startapp=open"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=1,
    )
    qr.add_data(miniapp_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#2563eb", back_color="white")
    img.save(filename)
    return filename


def setup_cyrillic_font():
    """Регистрация шрифта с поддержкой кириллицы (Windows / Linux)"""
    font_name = "Helvetica"
    font_files = [
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\calibri.ttf"
    ]
    for font_path in font_files:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont("DejaVuCyr", font_path))
                font_name = "DejaVuCyr"
                break
            except Exception as e:
                print(f"Ошибка подключения шрифта {font_path}: {e}")
    return font_name


def create_resume(output_filename="resume.pdf"):
    font_name = setup_cyrillic_font()

    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1e293b")
    )

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2563eb")
    )

    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=7,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#334155")
    )

    story = []

    # 1. Шапка резюме с контактами и QR-кодом Mini App
    qr_path = generate_bot_qr()

    header_text = [
        Paragraph("<b>Алексей Хрипунов</b>", name_style),
        Spacer(1, 3),
        Paragraph("<b>Инженер по тестированию (QA Engineer) / Python-разработчик</b>", title_style),
        Spacer(1, 4),
        Paragraph("<b>Telegram:</b> @iov1981 | <b>Email:</b> hripunov60@gmail.com", body_style),
        Paragraph("<b>Instagram:</b> @iov1981 | <b>GitHub:</b> github.com/iov1981", body_style),
        Paragraph("<i>QR-код справа открывает Mini App визитку: @aleksey_qa_vizitka_bot</i>", body_style)
    ]

    header_table = Table([[header_text, Image(qr_path, width=72, height=72)]], colWidths=[445, 95])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # Разделительная полоса
    line_table = Table([['']], colWidths=[540], rowHeights=[2])
    line_table.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, colors.HexColor("#2563eb")),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 6))

    # 2. О себе
    story.append(Paragraph("<b>О СЕБЕ</b>", heading_style))
    about_text = (
        "QA-инженер с опытом ручного и базового автоматизированного тестирования. "
        "Глубокое понимание процессов разработки ПО (SDLC, STLC), составления тест-планов, "
        "чек-листов и тест-кейсов. Разработка прикладных решений на Python, создание и тестирование Telegram-ботов "
        "с интеграцией искусственного интеллекта и баз данных."
    )
    story.append(Paragraph(about_text, body_style))
    story.append(Spacer(1, 5))

    # 3. Навыки
    story.append(Paragraph("<b>КЛЮЧЕВЫЕ НАВЫКИ</b>", heading_style))
    skills_text = (
        "• <b>Тестирование:</b> Функциональное, регрессионное, интеграционное, UI/UX, кроссбраузерное, нагрузочное.<br/>"
        "• <b>Тестирование API & Сети:</b> Postman, Chrome DevTools, REST API, валидация JSON-ответов.<br/>"
        "• <b>Базы данных:</b> SQL (SELECT, JOIN, агрегация), SQLite / aiosqlite, Google Sheets API.<br/>"
        "• <b>Стек и инструменты:</b> Python, Git, GitHub, Pytest, PyCharm, Jira, Confluence, aiogram 3, ReportLab."
    )
    story.append(Paragraph(skills_text, body_style))
    story.append(Spacer(1, 5))

    # 4. Проекты и опыт
    story.append(Paragraph("<b>ПРОЕКТЫ И ПРАКТИЧЕСКИЙ ОПЫТ</b>", heading_style))
    projects_text = (
        "• <b>Web-визитка & Telegram Mini App:</b> Интерактивное веб-приложение на Python (aiogram 3, aiohttp) "
        "с динамическим калькулятором стоимости, генерацией PDF на лету, базой данных SQLite и синхронизацией лидов.<br/>"
        "• <b>TubeSaver-Pro:</b> Десктопное приложение для загрузки мультимедиа (Python, CustomTkinter, yt-dlp).<br/>"
        "• <b>Taxi Region Bot:</b> Telegram-бот для автоматизации заказов поездок (aiogram 3, aiosqlite, Render 24/7)."
    )
    story.append(Paragraph(projects_text, body_style))
    story.append(Spacer(1, 5))

    # 5. Образование
    story.append(Paragraph("<b>ОБРАЗОВАНИЕ И КУРСЫ</b>", heading_style))
    edu_text = (
        "• Курс «Инженер по тестированию» (Skillbox).<br/>"
        "• Тестирование веб-приложений и Android-приложений (клиент-сервер, REST-архитектура, чек-листы, тест-кейсы)."
    )
    story.append(Paragraph(edu_text, body_style))

    doc.build(story)

    if os.path.exists(qr_path):
        os.remove(qr_path)
    print(f"Резюме успешно сгенерировано: {output_filename}")


if __name__ == "__main__":
    create_resume()