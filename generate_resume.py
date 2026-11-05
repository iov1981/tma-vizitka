import os
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def generate_vcard_qr(filename="vcard_qr.png"):
    """Генерация QR-кода с карточкой контакта vCard"""
    vcard_data = (
        "BEGIN:VCARD\n"
        "VERSION:3.0\n"
        "N:Хрипунов;Алексей;;;\n"
        "FN:Алексей Хрипунов\n"
        "TITLE:AI & Telegram Bot Developer\n"
        "URL:https://t.me/aleksey_qa_vizitka_bot\n"
        "NOTE:Разработка ботов, автоматизация и внедрение ИИ\n"
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


def setup_cyrillic_font():
    """Регистрация шрифта с гарантированной поддержкой кириллицы"""
    font_name = "Helvetica"
    font_files = [
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:\\Windows\\Fonts\\arial.ttf"
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

    # Стили с поддержкой зарегистрированного кириллического шрифта
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
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=8,
        spaceAfter=4
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

    # 1. Шапка резюме с QR-кодом
    qr_path = generate_vcard_qr()

    header_text = [
        Paragraph("<b>Алексей Хрипунов</b>", name_style),
        Spacer(1, 4),
        Paragraph("<b>Инженер по тестированию (QA Engineer) / Python-разработчик</b>", title_style),
        Spacer(1, 4),
        Paragraph("Telegram: @iov1981 | GitHub: github.com/iov1981", body_style),
    ]

    header_table = Table([[header_text, Image(qr_path, width=70, height=70)]], colWidths=[450, 90])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
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
        "чек-листов и тест-кейсов. Разработка прикладных решений на Python, создание и тестирование Telegram-ботов."
    )
    story.append(Paragraph(about_text, body_style))
    story.append(Spacer(1, 6))

    # 3. Навыки
    story.append(Paragraph("<b>КЛЮЧЕВЫЕ НАВЫКИ</b>", heading_style))
    skills_text = (
        "• <b>Тестирование:</b> Функциональное, регрессионное, интеграционное, UI/UX, кроссбраузерное.<br/>"
        "• <b>Тестирование API:</b> Postman, Chrome DevTools, валидация JSON-ответов.<br/>"
        "• <b>Базы данных:</b> SQL (SELECT, JOIN, агрегация), SQLite / aiosqlite.<br/>"
        "• <b>Стек и инструменты:</b> Python, Git, GitHub, PyCharm, Jira, Confluence, DevTools, aiogram 3."
    )
    story.append(Paragraph(skills_text, body_style))
    story.append(Spacer(1, 6))

    # 4. Проекты и опыт
    story.append(Paragraph("<b>ПРОЕКТЫ И ПРАКТИЧЕСКИЙ ОПЫТ</b>", heading_style))
    projects_text = (
        "• <b>TubeSaver-Pro:</b> Десктопное приложение для загрузки мультимедиа (Python, CustomTkinter, yt-dlp).<br/>"
        "• <b>Taxi Region Bot:</b> Telegram-бот для автоматизации заказов поездок (aiogram 3, aiosqlite, Render).<br/>"
        "• <b>Web-визитка & Telegram Mini App:</b> Интерактивное веб-приложение на Python с генерацией PDF и сбором лидов."
    )
    story.append(Paragraph(projects_text, body_style))
    story.append(Spacer(1, 6))

    # 5. Образование
    story.append(Paragraph("<b>ОБРАЗОВАНИЕ И КУРСЫ</b>", heading_style))
    edu_text = (
        "• Курс «Инженер по тестированию» (Skillbox).<br/>"
        "• Тестирование веб-приложений и Android-приложений (клиент-сервер, REST-архитектура, чек-листы)."
    )
    story.append(Paragraph(edu_text, body_style))

    doc.build(story)

    if os.path.exists(qr_path):
        os.remove(qr_path)
    print(f"Резюме успешно сгенерировано: {output_filename}")


if __name__ == "__main__":
    create_resume()