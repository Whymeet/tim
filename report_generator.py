from docx import Document
from docx.shared import Inches
import os

def generate_report(posts, output_file="Отчет.docx"):
    doc = Document()
    doc.add_heading("Отчет по рекламным постам", level=0)
    for i, post in enumerate(posts, 1):
        title = post.get("Название поста") or f"Пост {i}"
        url = post.get("Ссылка")
        screenshot = post.get("Скриншот")
        group_stats = post.get("Групповая статистика")

        doc.add_heading(title, level=2)
        doc.add_paragraph(url)
        if screenshot and os.path.exists(screenshot):
            doc.add_picture(screenshot, width=Inches(5))
        if group_stats and os.path.exists(group_stats):
            doc.add_paragraph("Статистика рекламной группы VK Ads:")
            doc.add_picture(group_stats, width=Inches(5))
        doc.add_paragraph("-" * 40)
    doc.save(output_file)
    print(f"Отчет сохранён как {output_file}")
