import os
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def create_pdf(filename="resume.pdf"):
    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    font_bold_path = "C:\\Windows\\Fonts\\arialbd.ttf"

    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("Arial", font_path))
        main_font = "Arial"
    else:
        main_font = "Helvetica"

    if os.path.exists(font_bold_path):
        pdfmetrics.registerFont(TTFont("Arial-Bold", font_bold_path))
        bold_font = "Arial-Bold"
    else:
        bold_font = main_font

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Normal"],
        fontName=bold_font,
        fontSize=20,
        leading=24,
        textColor=HexColor("#1A365D"),
    )

    subtitle_style = ParagraphStyle(
        "SubTitleStyle",
        parent=styles["Normal"],
        fontName=main_font,
        fontSize=13,
        leading=16,
        textColor=HexColor("#2B6CB0"),
    )

    contact_style = ParagraphStyle(
        "ContactStyle",
        parent=styles["Normal"],
        fontName=main_font,
        fontSize=9,
        leading=13,
        textColor=HexColor("#4A5568"),
    )

    h2_style = ParagraphStyle(
        "H2Style",
        parent=styles["Normal"],
        fontName=bold_font,
        fontSize=12,
        leading=16,
        textColor=HexColor("#2C5282"),
        spaceBefore=10,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName=main_font,
        fontSize=9.5,
        leading=13,
        textColor=HexColor("#2D3748"),
    )

    story = []

    # Шапка
    story.append(Paragraph("Алексей Хрипунов", title_style))
    story.append(
        Paragraph("Инженер по тестированию (QA Engineer) / Python", subtitle_style)
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "Telegram: @iov1981 | GitHub: github.com/iov1981 | Локация: Пенза / Удаленно",
            contact_style,
        )
    )
    story.append(Spacer(1, 10))

    # Разделы
    story.append(Paragraph("О СЕБЕ", h2_style))
    story.append(
        Paragraph(
            "QA-инженер с практическим опытом ручного и базового автоматизированного тестирования. "
            "Понимаю жизненный цикл разработки ПО (SDLC, STLC), методики тест-дизайна, клиент-серверную архитектуру. "
            "Разрабатываю прикладные инструменты, парсеры и ботов на Python для оптимизации рабочих задач.",
            body_style,
        )
    )

    story.append(Paragraph("КЛЮЧЕВЫЕ НАВЫКИ", h2_style))
    story.append(
        Paragraph(
            "• <b>Тестирование:</b> Функциональное, регрессионное, интеграционное, UI/UX, смоук-тестирование.<br/>"
            "• <b>Работа с API:</b> Postman (коллекции, переменные, автотесты), Chrome DevTools.<br/>"
            "• <b>Базы данных:</b> SQL (SELECT, JOIN, фильтрация, агрегация), SQLite / aiosqlite.<br/>"
            "• <b>Языки и инструменты:</b> Python, Git, GitHub, PyCharm, Jira, Confluence, DevTools.",
            body_style,
        )
    )

    story.append(Paragraph("ПРОЕКТЫ И ПРАКТИЧЕСКИЙ ОПЫТ", h2_style))
    story.append(
        Paragraph(
            "• <b>TubeSaver-Pro:</b> Десктопное приложение для загрузки мультимедиа (Python, CustomTkinter, yt-dlp).<br/>"
            "• <b>Taxi Region Bot:</b> Telegram-бот для координации поездок (aiogram 3, aiosqlite, Render).<br/>"
            "• <b>Web-визитка & Telegram Mini App:</b> Интерактивное приложение со сбором статистики и FSM.",
            body_style,
        )
    )

    story.append(Paragraph("ОБРАЗОВАНИЕ И КУРСЫ", h2_style))
    story.append(
        Paragraph(
            "• Курс «Профессия Инженер по тестированию» (Skillbox).<br/>"
            "• Практика тестирования веб-приложений и Android-приложений (составление чек-листов, тест-кейсов, баг-репортов).",
            body_style,
        )
    )

    doc.build(story)
    print(f"Файл {filename} успешно сгенерирован!")


if __name__ == "__main__":
    create_pdf()